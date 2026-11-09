import json
import logging
import re
import uuid
from pathlib import Path
from typing import Literal

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.config import settings
from app.db import Base, SessionLocal, engine, get_db
from app.grading import grade_answer
from app.models import Document, GapReport, Question, QuizAnswer, QuizAttempt, SourceChunk, Topic, User
from app.rag import (
    extract_pages,
    index_chunks,
    llm_json,
    remove_document_vectors,
    render_citation,
    retrieve,
    split_pages,
)
from app.security import check_password, create_token, current_user, hash_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gapfinder")
app = FastAPI(title="GapFinder AI", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Credentials(BaseModel):
    email: str
    password: str = Field(min_length=1, max_length=128)
    name: str = ""


class QuizRequest(BaseModel):
    num_questions: Literal[5, 10, 15, 20] = 10
    topic_ids: list[int] = []
    question_types: list[str] = ["mcq", "short_answer"]


class QuizSubmission(BaseModel):
    answers: list[dict]


class PlanRequest(BaseModel):
    days: int = Field(ge=1, le=60)
    hours_per_day: float = Field(gt=0, le=12)


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    history: list[ChatTurn] = Field(default_factory=list, max_length=8)


def groq_http_error(exc: Exception, api_key: str | None = None):
    if getattr(exc, "status_code", None) == 429:
        response = getattr(exc, "response", None)
        retry = response.headers.get("retry-after") if response else None
        detail = "The AI provider rate-limited this key/account. Check provider quota and retry window."
        body = getattr(exc, "body", None)
        provider_error = body.get("error") if isinstance(body, dict) else None
        provider_message = (
            provider_error.get("message")
            if isinstance(provider_error, dict)
            else None
        )
        if isinstance(provider_message, str) and provider_message.strip():
            safe_message = provider_message.strip()[:500]
            if api_key:
                safe_message = safe_message.replace(api_key, "[redacted]")
            detail = f"Groq rate limit: {safe_message}"
        if retry:
            detail += f" Retry after {retry}."
        raise HTTPException(429, detail=detail, headers={"Retry-After": str(retry)} if retry else None) from exc
    if getattr(exc, "status_code", None) == 401:
        raise HTTPException(
            401,
            "Groq rejected this API key. Check the key in Settings and save a valid key.",
        ) from exc
    if getattr(exc, "status_code", None) == 403:
        raise HTTPException(
            403,
            "Groq denied access for this API key. Check its permissions and account access.",
        ) from exc
    if not (api_key or settings.groq_api_key):
        raise HTTPException(503, "AI features require a Groq API key. Enter one in Settings.") from exc
    logger.exception("AI provider request failed")
    raise HTTPException(502, "The AI provider request failed.") from exc


def first_text(value, keys: tuple[str, ...]) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, dict):
        for key in keys:
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
    return None


@app.on_event("startup")
def startup():
    settings.validate_production()
    Base.metadata.create_all(bind=engine)
    if settings.seed_demo and settings.demo_password:
        with SessionLocal() as db:
            demo = db.query(User).filter(User.email == settings.demo_email.lower()).first()
            if not demo:
                demo = User(
                    email=settings.demo_email.lower(),
                    name="Demo Student",
                    password_hash=hash_password(settings.demo_password),
                )
                db.add(demo)
            else:
                demo.name = "Demo Student"
                demo.password_hash = hash_password(settings.demo_password)
            db.commit()


@app.get("/api/health")
def health():
    return {"status": "healthy", "service": "GapFinder AI"}


@app.post("/api/auth/register")
def register(payload: Credentials, db: Session = Depends(get_db)):
    if len(payload.password.encode("utf-8")) < 8:
        raise HTTPException(422, "Password must be at least 8 bytes.")
    if len(payload.password.encode("utf-8")) > 128:
        raise HTTPException(422, "Password must not exceed 128 bytes.")
    email = payload.email.strip().lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(409, "An account with this email already exists.")
    user = User(email=email, name=payload.name.strip(), password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"token": create_token(user.id), "user": {"id": user.id, "email": user.email, "name": user.name}}


@app.post("/api/auth/login")
def login(payload: Credentials, db: Session = Depends(get_db)):
    if len(payload.password.encode("utf-8")) > 128:
        raise HTTPException(422, "Password must not exceed 128 bytes.")
    user = db.query(User).filter(User.email == payload.email.strip().lower()).first()
    if not user or not check_password(payload.password, user.password_hash):
        raise HTTPException(401, "Email or password is incorrect.")
    return {"token": create_token(user.id), "user": {"id": user.id, "email": user.email, "name": user.name}}


@app.get("/api/auth/me")
def me(user: User = Depends(current_user)):
    return {"id": user.id, "email": user.email, "name": user.name}


@app.post("/api/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    kind: str = Form(...),
    api_key: str | None = Header(default=None, alias="X-Groq-API-Key"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    filename = Path((file.filename or "").replace("\\", "/")).name
    if Path(filename).suffix.lower() not in {".pdf", ".txt"}:
        raise HTTPException(400, "Only PDF and TXT files are supported.")
    if kind not in {"syllabus", "notes", "past_paper"}:
        raise HTTPException(400, "kind must be syllabus, notes, or past_paper.")
    content = await file.read(20 * 1024 * 1024 + 1)
    if not content or len(content) > 20 * 1024 * 1024:
        raise HTTPException(413, "File must be non-empty and no larger than 20 MB.")
    user_dir = Path(settings.upload_path) / str(user.id)
    user_dir.mkdir(parents=True, exist_ok=True)
    path = user_dir / f"{uuid.uuid4().hex}_{filename}"
    path.write_bytes(content)
    doc = Document(user_id=user.id, filename=filename, kind=kind)
    db.add(doc)
    db.flush()
    chunks = []
    try:
        chunks = split_pages(extract_pages(path))
        if not chunks:
            raise HTTPException(400, "No readable text was found in the document.")
        index_chunks(user.id, doc.id, filename, chunks, db)
        if kind == "syllabus":
            syllabus_text = "\n".join(page_text for _, page_text in extract_pages(path))
            if api_key or settings.groq_api_key:
                topic_data = llm_json(
                    "Extract a concise hierarchy of study topics from this syllabus. Return JSON array "
                    "of {name, children:[{name,children:[]}]} objects. Do not invent topics.\n"
                    + syllabus_text,
                    api_key,
                )
                if not isinstance(topic_data, list):
                    raise ValueError("Syllabus model output must be a JSON array.")
            else:
                topic_data = _extract_topics_locally(syllabus_text)
            _save_topics(db, user.id, topic_data)
        elif kind == "past_paper":
            if api_key or settings.groq_api_key:
                _weight_topics(db, user.id, chunks, api_key)
            else:
                _weight_topics_locally(db, user.id, chunks)
        db.commit()
    except Exception as exc:
        db.rollback()
        remove_document_vectors(user.id, [chunk["id"] for chunk in chunks])
        path.unlink(missing_ok=True)
        if isinstance(exc, HTTPException):
            raise
        if getattr(exc, "status_code", None) == 429 or not (api_key or settings.groq_api_key):
            groq_http_error(exc, api_key)
        logger.exception("Document processing failed")
        raise HTTPException(500, "Document processing failed; no document was saved.") from exc
    return {"id": doc.id, "filename": filename, "kind": kind, "chunks": len(chunks)}


def _save_topics(db: Session, user_id: int, topics: list, parent_id: int | None = None):
    for item in topics:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            continue
        name = item["name"].strip()
        if not name:
            continue
        topic = db.query(Topic).filter_by(user_id=user_id, name=name, parent_id=parent_id).first()
        if topic is None:
            topic = Topic(user_id=user_id, name=name, parent_id=parent_id, exam_weight=0.0)
            db.add(topic)
            db.flush()
        _save_topics(db, user_id, item.get("children", []), topic.id)


def _extract_topics_locally(text: str) -> list[dict]:
    topics: list[dict] = []
    current: dict | None = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        heading = re.match(
            r"^(?:(?:chapter|unit|module|part)\s+[\w.-]+[\s:.-]*)?(.{3,100})$",
            line,
            re.IGNORECASE,
        )
        numbered = re.match(r"^\d+(?:\.\d+)*[.)]?\s+(.{2,100})$", line)
        bullet = re.match(r"^[-*•]\s+(.{2,100})$", line)
        if numbered or bullet:
            name = (numbered or bullet).group(1).strip(" .:-")
            depth = len(re.match(r"^\d+(?:\.\d+)*", line).group(0).split(".")) if numbered else 1
            if depth > 1 and current is not None:
                current["children"].append({"name": name, "children": []})
            else:
                current = {"name": name, "children": []}
                topics.append(current)
        elif heading and len(line.split()) <= 12 and not line.endswith((".", "?", "!")):
            name = heading.group(1).strip(" #:-")
            if name and name.casefold() not in {"syllabus", "contents", "table of contents"}:
                current = {"name": name, "children": []}
                topics.append(current)
    if not topics:
        sentences = re.split(r"[\n;]+|(?<=[.!?])\s+", text)
        names = [
            sentence.strip(" -#.:")
            for sentence in sentences
            if 1 < len(sentence.split()) <= 10
            and len(sentence.strip()) <= 100
            and not sentence.strip().isdigit()
        ]
        topics = [{"name": name, "children": []} for name in dict.fromkeys(names[:30])]
    if not topics:
        raise HTTPException(422, "No topics could be extracted. Add headings or numbered topics to the syllabus.")
    return topics


def _weight_topics(db: Session, user_id: int, chunks: list[dict], api_key: str | None = None):
    topics = db.query(Topic).filter_by(user_id=user_id).all()
    if not topics:
        return
    prompt = (
        "Return JSON array of {topic, frequency} for the topics evidenced in this exam paper. "
        "Use integer frequency counts; include only provided topic names.\nTopics: "
        + json.dumps([topic.name for topic in topics])
        + "\nPaper:\n"
        + "\n".join(c["text"] for c in chunks[:10])
    )
    counts = llm_json(prompt, api_key)
    totals = {topic.name.casefold(): 0 for topic in topics}
    for item in counts:
        name = str(item.get("topic", "")).casefold()
        if name in totals:
            totals[name] += max(0, int(item.get("frequency", 0)))
    denominator = sum(totals.values()) or 1
    for topic in topics:
        topic.exam_weight = totals[topic.name.casefold()] / denominator


def _weight_topics_locally(db: Session, user_id: int, chunks: list[dict]):
    topics = db.query(Topic).filter_by(user_id=user_id).all()
    if not topics:
        return
    paper = " ".join(chunk["text"].casefold() for chunk in chunks)
    counts = {
        topic.id: len(re.findall(rf"(?<!\w){re.escape(topic.name.casefold())}(?!\w)", paper))
        for topic in topics
    }
    denominator = sum(counts.values())
    if denominator:
        for topic in topics:
            topic.exam_weight = counts[topic.id] / denominator


@app.get("/api/documents")
def documents(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return [
        {"id": doc.id, "filename": doc.filename, "kind": doc.kind, "created_at": doc.created_at}
        for doc in db.query(Document).filter_by(user_id=user.id).order_by(Document.id.desc()).all()
    ]


@app.get("/api/topics")
def topics(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return [
        {"id": topic.id, "name": topic.name, "parent_id": topic.parent_id, "exam_weight": topic.exam_weight}
        for topic in db.query(Topic).filter_by(user_id=user.id).order_by(Topic.id).all()
    ]


@app.post("/api/quiz/generate")
def generate_quiz(
    payload: QuizRequest,
    api_key: str | None = Header(default=None, alias="X-Groq-API-Key"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    api_key = api_key or settings.groq_api_key
    if not api_key:
        raise HTTPException(503, "AI quiz generation requires a Groq API key. Enter one in Settings.")
    if not payload.question_types or any(q not in {"mcq", "short_answer"} for q in payload.question_types):
        raise HTTPException(422, "Choose at least one supported question type.")
    topic_query = db.query(Topic).filter_by(user_id=user.id)
    if payload.topic_ids:
        topic_query = topic_query.filter(Topic.id.in_(payload.topic_ids))
    topic_list = topic_query.all()
    if not topic_list:
        raise HTTPException(400, "Upload a syllabus and create topics before generating a quiz.")
    chunks = retrieve(user.id, " ".join(topic.name for topic in topic_list), count=12)
    if not chunks:
        raise HTTPException(400, "No relevant uploaded source material was found for these topics.")
    evidence = {chunk["id"]: chunk for chunk in chunks}
    source_context = "\n".join(
        f"ID={c['id']} {render_citation(c)}\n{c['text']}" for c in chunks
    )
    allowed_source_ids = list(evidence)
    generated_questions = []
    batch_size = 5
    for batch_start in range(0, payload.num_questions, batch_size):
        batch_count = min(batch_size, payload.num_questions - batch_start)
        prompt = (
            "Generate exactly the requested number of concise diagnostic questions using only the source context. "
            "Return only a compact JSON array. Every item must have topic (exactly one supplied topic name), "
            "kind (mcq or short_answer), prompt, options (array or []), answer, concise explanation "
            "(one sentence), and source_chunk_ids (array containing exact IDs from the allowed ID list). "
            "Copy source IDs exactly; do not return citation labels instead of IDs. "
            "Do not use outside knowledge. Ensure the JSON is complete.\n"
            f"Count: {batch_count}; allowed types: {payload.question_types}; "
            f"topics: {[t.name for t in topic_list]}\n"
            f"Allowed source IDs: {json.dumps(allowed_source_ids)}\nSources:\n{source_context}"
        )
        try:
            batch = llm_json(prompt, api_key)
        except Exception as exc:
            db.rollback()
            if isinstance(exc, ValueError):
                raise HTTPException(
                    502,
                    "The AI provider returned an incomplete quiz response. Try a smaller quiz, or wait briefly and retry.",
                ) from exc
            groq_http_error(exc, api_key)
        if not isinstance(batch, list) or len(batch) != batch_count:
            db.rollback()
            raise HTTPException(
                502,
                f"The AI provider returned an incomplete batch ({len(batch) if isinstance(batch, list) else 0} of {batch_count} questions). Try a smaller quiz.",
            )
        generated_questions.extend(batch)
    result = []
    rejected = {"invalid_fields": 0, "invalid_topic": 0, "invalid_kind": 0, "invalid_citations": 0}
    missing_fields: dict[str, int] = {}
    for item in generated_questions:
        if not isinstance(item, dict):
            rejected["invalid_fields"] += 1
            missing_fields["question object"] = missing_fields.get("question object", 0) + 1
            continue
        topic_name = first_text(item.get("topic") or item.get("topic_name"), ("name", "title", "text"))
        prompt_text = first_text(
            item.get("prompt") or item.get("question") or item.get("question_text") or item.get("statement"),
            ("text", "content", "value"),
        )
        answer_text = first_text(
            item.get("answer") or item.get("correct_answer") or item.get("correct_option") or item.get("answer_key"),
            ("text", "value", "label", "option"),
        )
        explanation_text = first_text(
            item.get("explanation") or item.get("rationale") or item.get("reasoning") or item.get("solution"),
            ("text", "content", "value"),
        ) or "Review the cited source material for the supporting explanation."
        absent = [
            field for field, value in (("topic", topic_name), ("question", prompt_text), ("answer", answer_text))
            if not value
        ]
        if absent:
            rejected["invalid_fields"] += 1
            for field in absent:
                missing_fields[field] = missing_fields.get(field, 0) + 1
            continue
        topic = next((t for t in topic_list if t.name.casefold() == topic_name.casefold()), None)
        if not topic:
            rejected["invalid_topic"] += 1
            continue
        raw_kind = first_text(item.get("kind") or item.get("question_type") or item.get("type"), ("name", "value", "label"))
        kind = (raw_kind or "").casefold().replace("-", "_").replace(" ", "_")
        if kind in {"multiple_choice", "multiplechoice", "mcq_question"}:
            kind = "mcq"
        elif kind in {"shortanswer", "open_ended", "open_response", "free_response"}:
            kind = "short_answer"
        if kind not in payload.question_types:
            rejected["invalid_kind"] += 1
            continue
        raw_citations = (
            item.get("source_chunk_ids")
            or item.get("source_ids")
            or item.get("citations")
            or item.get("sources")
            or []
        )
        if isinstance(raw_citations, str):
            raw_citations = [raw_citations]
        cited = []
        if isinstance(raw_citations, list):
            for citation in raw_citations:
                citation_text = first_text(citation, ("id", "source_id", "chunk_id", "text", "citation"))
                if not citation_text:
                    continue
                normalized_citation = citation_text.casefold()
                cited.extend(
                    source_id for source_id in evidence
                    if source_id.casefold() in normalized_citation
                )
        cited = list(dict.fromkeys(cited))
        if not cited:
            rejected["invalid_citations"] += 1
            continue
        raw_options = item.get("options") or item.get("choices") or []
        if isinstance(raw_options, dict):
            raw_options = list(raw_options.values())
        options = [
            option_text
            for option in raw_options if isinstance(raw_options, list)
            if (option_text := first_text(option, ("text", "label", "value", "option")))
        ]
        question = Question(
            topic_id=topic.id,
            prompt=prompt_text,
            kind=kind,
            options_json=json.dumps(options),
            answer=answer_text,
            explanation=explanation_text,
            source_chunk_ids_json=json.dumps(cited),
        )
        db.add(question)
        db.flush()
        result.append({
            "id": question.id, "topic": topic.name, "kind": question.kind,
            "prompt": question.prompt, "options": json.loads(question.options_json),
            "citations": [render_citation(evidence[cid]) for cid in cited],
        })
    if len(result) != payload.num_questions:
        db.rollback()
        missing_summary = (
            f" Missing required fields: {', '.join(f'{name} ({count})' for name, count in missing_fields.items())}."
            if missing_fields else ""
        )
        raise HTTPException(
            502,
            f"The AI provider returned {len(result)} of {payload.num_questions} usable questions "
            f"(invalid fields: {rejected['invalid_fields']}, topics: {rejected['invalid_topic']}, "
            f"question types: {rejected['invalid_kind']}, citations: {rejected['invalid_citations']}). "
            f"{missing_summary} Try a smaller quiz.",
        )
    db.commit()
    return {"questions": result}


@app.post("/api/quiz/submit")
def submit_quiz(payload: QuizSubmission, user: User = Depends(current_user), db: Session = Depends(get_db)):
    submitted_questions = []
    for entry in payload.answers:
        question = (
            db.query(Question).join(Topic, Question.topic_id == Topic.id)
            .filter(Question.id == entry.get("question_id"), Topic.user_id == user.id).first()
        )
        if not question:
            raise HTTPException(404, "One or more quiz questions were not found.")
        submitted_questions.append((entry, question))
    attempt = QuizAttempt(user_id=user.id, total=len(payload.answers))
    db.add(attempt)
    db.flush()
    topic_results: dict[int, dict] = {}
    results = []
    for entry, question in submitted_questions:
        answer = str(entry.get("answer", "")).strip()
        correct = grade_answer(
            question.kind,
            question.answer,
            answer,
            json.loads(question.options_json),
        )
        db.add(QuizAnswer(attempt_id=attempt.id, question_id=question.id, answer=answer, correct=correct))
        attempt.score += int(correct)
        aggregate = topic_results.setdefault(question.topic_id, {"correct": 0, "total": 0, "missed": []})
        aggregate["total"] += 1
        aggregate["correct"] += int(correct)
        if not correct:
            aggregate["missed"].append(question.prompt[:120])
        chunk_ids = json.loads(question.source_chunk_ids_json)
        source_chunks = db.query(SourceChunk).filter(SourceChunk.id.in_(chunk_ids)).all() if chunk_ids else []
        results.append({
            "question_id": question.id,
            "question": question.prompt,
            "submitted_answer": answer,
            "correct": correct,
            "points_earned": 10 if correct else 0,
            "points_possible": 10,
            "correct_answer": question.answer,
            "explanation": question.explanation,
            "citations": [
                f"Source: {db.get(Document, chunk.document_id).filename}, Page {chunk.page}"
                for chunk in source_chunks
            ],
        })
    for topic_id, score in topic_results.items():
        topic = db.get(Topic, topic_id)
        pct = score["correct"] / score["total"] * 100
        level = "weak" if pct < 50 else "medium" if pct < 80 else "strong"
        evidence = f"Answered {score['correct']}/{score['total']} correctly on {topic.name}."
        if score["missed"]:
            evidence += " Missed: " + "; ".join(score["missed"][:3])
        db.add(GapReport(attempt_id=attempt.id, topic_id=topic_id, score_pct=pct, level=level, evidence=evidence))
    db.commit()
    return {
        "attempt_id": attempt.id,
        "correct_count": attempt.score,
        "total": attempt.total,
        "score_points": attempt.score * 10,
        "max_points": attempt.total * 10,
        "score_pct": round(attempt.score / attempt.total * 100, 1) if attempt.total else 0,
        "results": results,
    }


@app.get("/api/gap-report/{attempt_id}")
def gap_report(attempt_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    attempt = db.query(QuizAttempt).filter_by(id=attempt_id, user_id=user.id).first()
    if not attempt:
        raise HTTPException(404, "Quiz attempt not found.")
    rows = db.query(GapReport, Topic).join(Topic, GapReport.topic_id == Topic.id).filter(
        GapReport.attempt_id == attempt_id
    ).all()
    answer_rows = (
        db.query(QuizAnswer, Question)
        .join(Question, QuizAnswer.question_id == Question.id)
        .filter(QuizAnswer.attempt_id == attempt_id)
        .all()
    )
    answer_details = []
    for saved_answer, question in answer_rows:
        chunk_ids = json.loads(question.source_chunk_ids_json)
        source_chunks = db.query(SourceChunk).filter(SourceChunk.id.in_(chunk_ids)).all() if chunk_ids else []
        answer_details.append({
            "question": question.prompt,
            "submitted_answer": saved_answer.answer,
            "correct": saved_answer.correct,
            "points_earned": 10 if saved_answer.correct else 0,
            "points_possible": 10,
            "correct_answer": question.answer,
            "explanation": question.explanation,
            "citations": [
                f"Source: {db.get(Document, chunk.document_id).filename}, Page {chunk.page}"
                for chunk in source_chunks
            ],
        })
    return {
        "attempt_id": attempt.id,
        "correct_count": attempt.score,
        "total": attempt.total,
        "score_points": attempt.score * 10,
        "max_points": attempt.total * 10,
        "score_pct": round(attempt.score / attempt.total * 100, 1) if attempt.total else 0,
        "answers": answer_details,
        "topics": [
            {"topic": topic.name, "score_pct": report.score_pct, "level": report.level, "evidence": report.evidence}
            for report, topic in rows
        ],
    }


@app.get("/api/dashboard/progress")
def progress(user: User = Depends(current_user), db: Session = Depends(get_db)):
    attempts = db.query(QuizAttempt).filter_by(user_id=user.id).order_by(desc(QuizAttempt.id)).limit(20).all()
    return {
        "attempts": [
            {
                "id": a.id,
                "correct_count": a.score,
                "total": a.total,
                "score_points": a.score * 10,
                "max_points": a.total * 10,
                "score_pct": round(a.score / a.total * 100, 1) if a.total else 0,
                "created_at": a.created_at,
            }
            for a in attempts
        ]
    }


@app.post("/api/study-plan/generate")
def study_plan(payload: PlanRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    latest = db.query(QuizAttempt).filter_by(user_id=user.id).order_by(desc(QuizAttempt.id)).first()
    if not latest:
        raise HTTPException(400, "Take a diagnostic quiz before generating a plan.")
    rows = db.query(Topic, GapReport).join(GapReport, GapReport.topic_id == Topic.id).filter(
        Topic.user_id == user.id, GapReport.attempt_id == latest.id
    ).all()
    priorities = [
        (topic, report, topic.exam_weight * (1 - report.score_pct / 100))
        for topic, report in rows
    ]
    if sum(item[2] for item in priorities) <= 0:
        priorities = [(topic, report, 1 - report.score_pct / 100) for topic, report, _ in priorities]
    if sum(item[2] for item in priorities) <= 0:
        priorities = [(topic, report, 1.0) for topic, report, _ in priorities]
    priorities.sort(key=lambda item: item[2], reverse=True)
    if not priorities:
        raise HTTPException(400, "The latest quiz did not assess any topics.")
    budget = payload.days * payload.hours_per_day
    total_priority = sum(item[2] for item in priorities)
    plan = []
    for topic, report, priority in priorities:
        hours = budget * priority / total_priority
        plan.append({
            "topic": topic.name,
            "level": report.level,
            "hours": round(hours, 2),
            "priority": round(priority, 4),
            "days": max(1, round(hours / payload.hours_per_day)),
            "suggestion": f"Review your uploaded material for {topic.name}, then retest this topic.",
        })
    schedule = []
    day = 1
    available = payload.hours_per_day
    for item in plan:
        remaining = item["hours"]
        while remaining > 1e-8:
            allocated = min(remaining, available)
            schedule.append({"day": day, "topic": item["topic"], "hours": round(allocated, 2)})
            remaining -= allocated
            available -= allocated
            if available <= 1e-8 and day < payload.days:
                day += 1
                available = payload.hours_per_day
    return {"days": payload.days, "hours_per_day": payload.hours_per_day, "items": plan, "schedule": schedule}


@app.post("/api/chat")
def chat(
    payload: ChatRequest,
    api_key: str | None = Header(default=None, alias="X-Groq-API-Key"),
    user: User = Depends(current_user),
):
    recent_user_context = " ".join(
        turn.content for turn in payload.history[-6:] if turn.role == "user"
    )
    chunks_by_id = {
        chunk["id"]: chunk
        for chunk in retrieve(user.id, payload.message)
    }
    if recent_user_context:
        contextual_query = f"{recent_user_context} {payload.message}"
        for chunk in retrieve(user.id, contextual_query):
            existing = chunks_by_id.get(chunk["id"])
            if existing is None or chunk["score"] > existing["score"]:
                chunks_by_id[chunk["id"]] = chunk
    chunks = sorted(chunks_by_id.values(), key=lambda chunk: chunk["score"], reverse=True)[:6]
    if not chunks:
        return {"reply": "I couldn't find supporting information in your uploaded study materials.", "citations": []}
    conversation = "\n".join(
        f"{'Student' if turn.role == 'user' else 'Study assistant'}: {turn.content}"
        for turn in payload.history
    )
    prompt = (
        "Continue the study conversation. Use the conversation only to understand references and follow-ups; "
        "answer the latest student question using only the source context. If it does not support an answer, "
        "say so. Do not invent citations; keep the answer concise.\n"
        + (f"Conversation so far:\n{conversation}\n" if conversation else "")
        + "Source context:\n"
        + "\n".join(f"ID={c['id']} {render_citation(c)}\n{c['text']}" for c in chunks)
        + "\nLatest student question: " + payload.message
    )
    try:
        from app.rag import llm

        response = llm(api_key).invoke(prompt)
    except Exception as exc:
        groq_http_error(exc, api_key)
    citations = list(dict.fromkeys(render_citation(chunk) for chunk in chunks))
    return {"reply": f"{response.content.strip()}\n\n" + "\n".join(citations), "citations": citations}
