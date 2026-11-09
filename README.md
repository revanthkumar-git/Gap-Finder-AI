# GapFinder AI

An AI-assisted revision tool that finds knowledge gaps in a student's own uploaded study material and plans targeted revision.

## Stack

- Frontend: React, TypeScript, Vite
- API: FastAPI, Python 3.11+
- Relational data: SQLite with SQLAlchemy (PostgreSQL can be selected with `DATABASE_URL`)
- Vector retrieval: ChromaDB with Sentence-Transformers (`all-MiniLM-L6-v2`)
- LLM: Groq through LangChain's `ChatGroq`

## RAG architecture

```text
PDF/TXT upload
      |
      v
PyMuPDF/text extraction --> page-aware, overlapping chunks
      |                           |
      |                           +--> SQLite document/chunk metadata
      v
Syllabus/past-paper topic analysis (Groq; only on these document types)
      |
      v
ChromaDB per-user collection <---- topic-filtered similarity retrieval
      |                                      |
      +--------------------+-----------------+
                           v
                context + trusted chunk IDs
                           |
              +------------+------------+
              |                         |
       Quiz/chat generation       Answer evaluation
       validate cited IDs         exact quiz sources
              |                         |
              +------------+------------+
                           v
             Scores -> GapReport -> Study plan
```

Retrieval is scoped to the authenticated user. Each chunk stores document ID, filename, page, section, and chunk ID. Prompts can cite only chunk IDs returned by retrieval; the API resolves those IDs back to stored metadata and renders citations itself. The API rejects generated quiz questions that do not cite a retrieved chunk. Chat abstains when no material passes the similarity threshold. This constrains grounding but cannot guarantee that an LLM never makes an unsupported inference.

Chunking uses up to 800 whitespace-delimited words with a 160-word overlap. PDF page numbers and detected headings are retained. Syllabus topics are parsed into a hierarchy; past-paper topics are matched to this hierarchy and their observed frequency is normalized into exam weights.

## Data model

| Entity | Important fields and relationships |
|---|---|
| User | `id`, unique `email`, `password_hash`; owns documents, topics, quizzes, and reports |
| Document | `id`, `user_id`, `filename`, `kind`, `created_at`; owns source chunks |
| SourceChunk | `id`, `document_id`, `text`, `page`, `section`; exact citation/evidence record |
| Topic | `id`, `user_id`, `parent_id`, `name`, `exam_weight`; hierarchical syllabus topic |
| Question | `id`, `topic_id`, `prompt`, `kind`, `options_json`, `answer`, `explanation`, `source_chunk_ids_json` |
| QuizAttempt | `id`, `user_id`, `created_at`, `score`, `total`; owns answers and topic scores |
| GapReport | `id`, `attempt_id`, `topic_id`, `score_pct`, `level`, `evidence`; one row per assessed topic |

SQLite is the default for local development. Set `DATABASE_URL` to a PostgreSQL SQLAlchemy URL for deployment. Chroma is a separate persistent vector index; relational chunk metadata remains the citation authority.

## Run locally (Windows PowerShell)

1. Copy `backend\.env.example` to `backend\.env` and set `GROQ_API_KEY`.
2. In `backend`: `python -m venv .venv`, `.venv\Scripts\Activate.ps1`, `pip install -r requirements.txt`, then `uvicorn app.main:app --reload --port 8000`.
3. In `frontend`: `npm install`, then `npm run dev`.
4. Open `http://localhost:5173`. API docs: `http://localhost:8000/docs`.

The first embedding-model use downloads the model. PDF/TXT uploads and syllabus topic extraction work without a Groq key; without a key, syllabus headings and past-paper topic mentions are extracted locally. AI-generated quizzes, grading explanations, and study-assistant responses require `GROQ_API_KEY`. The development demo account is seeded when `SEED_DEMO=true`.

Demo login:

- Email: `demo@gapfinder.ai`
- Password: `demo123`

Change or disable the demo credentials before exposing a deployment to the public internet.

To supply a Groq key from the website, sign in, open **Settings**, enter the key, and choose **Save key for this tab**. It is held in browser `sessionStorage` only and sent to the local API in a request header; it is not written to the backend `.env` or database. Clearing the tab/session clears it. Use HTTPS on a hosted deployment.

The default model is `openai/gpt-oss-20b`. Set `LLM_MODEL` in `backend\.env` to another model ID supported by your Groq account to change it. Model availability and quotas vary by account and model; switching models may not avoid organization-wide or account-wide limits.

## Deploy

The Vercel project should use `frontend` as its root directory, build with `npm run build`, and output `dist`. Set `VITE_API_BASE_URL` to the public Render API URL followed by `/api` (for example, `https://your-service.onrender.com/api`).

`render.yaml` defines a free Render web service for the API and seeds the demo account at startup. Set `DEMO_PASSWORD` in the Render service's Environment settings (do not commit it to the repository) to enable the documented demo login. Deploy it as a Blueprint from this repository, then set the Vercel environment variable to the created service URL and redeploy the frontend. Free Render services can sleep when idle, have ephemeral local files (so uploads and SQLite/Chroma data can be lost on restart or deploy), and have limited monthly usage. Use paid persistent storage and a production database for durable data. The free setup is for testing only.

## Core API

- `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`
- `POST /api/documents/upload`, `GET /api/documents`
- `GET /api/topics`
- `POST /api/quiz/generate`, `POST /api/quiz/submit`
- `GET /api/gap-report/{attempt_id}`, `GET /api/dashboard/progress`
- `POST /api/study-plan/generate`
- `POST /api/chat`

The study plan allocates `days × hours/day` deterministically by `exam_weight × (1 − mastery)`, scheduling the highest priority first. A new quiz attempt creates a new report, so progress and plans can adapt after retesting.

## Production notes

Set a strong unique `JWT_SECRET`, PostgreSQL `DATABASE_URL`, persistent storage for Chroma and uploads, and explicit `CORS_ORIGINS`. Use HTTPS, protect `.env`, and restrict signup or add account verification before public deployment. Configure quotas and monitor Groq usage; provider rate limits are independent of this app.
