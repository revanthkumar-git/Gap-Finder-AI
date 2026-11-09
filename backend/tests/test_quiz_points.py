import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base, get_db
from app.main import app
from app.models import Question, Topic, User
from app.security import current_user


class QuizPointsTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.engine = create_engine(
            f"sqlite:///{Path(self.temp_dir.name) / 'quiz-points.db'}",
            connect_args={"check_same_thread": False},
        )
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.db = self.session_factory()
        self.user = User(
            id=1,
            email="points@example.com",
            name="Points Test",
            password_hash="unused",
        )
        self.db.add(self.user)
        self.topic = Topic(
            user_id=self.user.id,
            name="Photosynthesis",
            exam_weight=1.0,
        )
        self.db.add(self.topic)
        self.db.flush()
        self.questions = [
            Question(
                topic_id=self.topic.id,
                prompt=f"Question {index}",
                kind="mcq",
                options_json=json.dumps(["A) Correct", "B) Incorrect"]),
                answer="A",
                explanation="Source-supported explanation.",
                source_chunk_ids_json="[]",
            )
            for index in range(3)
        ]
        self.db.add_all(self.questions)
        self.db.commit()

        def db_override():
            session = self.session_factory()
            try:
                yield session
            finally:
                session.close()

        app.dependency_overrides[get_db] = db_override
        app.dependency_overrides[current_user] = lambda: self.user
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()
        self.db.close()
        self.engine.dispose()
        self.temp_dir.cleanup()

    def test_correct_answers_are_ten_points_and_report_percent_is_preserved(self):
        response = self.client.post(
            "/api/quiz/submit",
            json={
                "answers": [
                    {"question_id": self.questions[0].id, "answer": "A"},
                    {"question_id": self.questions[1].id, "answer": "B"},
                    {"question_id": self.questions[2].id, "answer": "A) Correct"},
                ]
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()
        self.assertEqual(result["score_points"], 20)
        self.assertEqual(result["max_points"], 30)
        self.assertEqual(result["score_pct"], 66.7)
        self.assertEqual(
            [answer["points_earned"] for answer in result["results"]],
            [10, 0, 10],
        )
        report = self.client.get(f"/api/gap-report/{result['attempt_id']}")
        self.assertEqual(report.status_code, 200, report.text)
        self.assertEqual(report.json()["score_points"], 20)
        self.assertEqual(report.json()["topics"][0]["score_pct"], 66.66666666666666)
        progress = self.client.get("/api/dashboard/progress")
        self.assertEqual(progress.json()["attempts"][0]["score_points"], 20)

    def test_quiz_lengths_are_limited_to_requested_choices(self):
        source = {
            "id": "test-source",
            "text": "Photosynthesis converts light energy into chemical energy.",
            "metadata": {"filename": "biology.txt", "page": 1, "section": "Photosynthesis"},
            "score": 0.9,
        }

        def generate_batch(prompt, api_key):
            count = int(re.search(r"Count: (\d+)", prompt).group(1))
            return [
                {
                    "topic": "Photosynthesis",
                    "kind": "mcq",
                    "prompt": f"Question {index}: What does photosynthesis convert?",
                    "options": ["A) Light energy into chemical energy", "B) Water into oxygen"],
                    "answer": "A",
                    "explanation": "The source states that light energy becomes chemical energy.",
                    "source_chunk_ids": ["test-source"],
                }
                for index in range(count)
            ]

        with (
            patch("app.main.settings.groq_api_key", "test-key"),
            patch("app.main.retrieve", return_value=[source]),
            patch("app.main.llm_json", side_effect=generate_batch) as generate,
        ):
            for count in (5, 10, 15, 20):
                with self.subTest(count=count):
                    response = self.client.post(
                        "/api/quiz/generate",
                        json={"num_questions": count},
                    )
                    self.assertEqual(response.status_code, 200, response.text)
                    self.assertEqual(len(response.json()["questions"]), count)
                    self.assertEqual(generate.call_count, count // 5)
                    self.db.query(Question).delete()
                    self.db.commit()
                    generate.reset_mock()
        response = self.client.post(
            "/api/quiz/generate",
            json={"num_questions": 8},
        )
        self.assertEqual(response.status_code, 422)

    def test_invalid_groq_key_returns_actionable_error(self):
        source = {
            "id": "test-source",
            "text": "Photosynthesis converts light energy into chemical energy.",
            "metadata": {"filename": "biology.txt", "page": 1, "section": "Photosynthesis"},
            "score": 0.9,
        }
        error = Exception("Invalid API key")
        error.status_code = 401

        with (
            patch("app.main.settings.groq_api_key", ""),
            patch("app.main.retrieve", return_value=[source]),
            patch("app.main.llm_json", side_effect=error),
        ):
            response = self.client.post(
                "/api/quiz/generate",
                headers={"X-Groq-API-Key": "invalid-test-key"},
                json={"num_questions": 5},
            )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json()["detail"],
            "Groq rejected this API key. Check the key in Settings and save a valid key.",
        )

    def test_rate_limit_returns_provider_quota_reason(self):
        source = {
            "id": "test-source",
            "text": "Photosynthesis converts light energy into chemical energy.",
            "metadata": {"filename": "biology.txt", "page": 1, "section": "Photosynthesis"},
            "score": 0.9,
        }
        error = Exception("Rate limited")
        error.status_code = 429
        error.body = {
            "error": {
                "message": "Rate limit reached for tokens per minute.",
                "type": "tokens",
                "code": "rate_limit_exceeded",
            }
        }
        error.response = type("Response", (), {"headers": {"retry-after": "120"}})()

        with (
            patch("app.main.settings.groq_api_key", ""),
            patch("app.main.retrieve", return_value=[source]),
            patch("app.main.llm_json", side_effect=error),
        ):
            response = self.client.post(
                "/api/quiz/generate",
                headers={"X-Groq-API-Key": "valid-test-key"},
                json={"num_questions": 5},
            )

        self.assertEqual(response.status_code, 429)
        self.assertEqual(
            response.json()["detail"],
            "Groq rate limit: Rate limit reached for tokens per minute. Retry after 120.",
        )
        self.assertEqual(response.headers["retry-after"], "120")

    def test_quiz_generation_accepts_decorated_citation_and_common_kind_alias(self):
        source = {
            "id": "test-source",
            "text": "Photosynthesis converts light energy into chemical energy.",
            "metadata": {"filename": "biology.txt", "page": 1, "section": "Photosynthesis"},
            "score": 0.9,
        }
        question = {
            "topic": "Photosynthesis",
            "kind": "multiple choice",
            "prompt": "What does photosynthesis convert?",
            "options": ["A) Light energy into chemical energy", "B) Chemical energy into light"],
            "answer": "A",
            "explanation": "The source describes this conversion.",
            "source_chunk_ids": ["Source ID: test-source"],
        }

        with (
            patch("app.main.settings.groq_api_key", "test-key"),
            patch("app.main.retrieve", return_value=[source]),
            patch("app.main.llm_json", return_value=[question] * 5),
        ):
            response = self.client.post(
                "/api/quiz/generate",
                json={"num_questions": 5},
            )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(len(response.json()["questions"]), 5)
        self.assertEqual(response.json()["questions"][0]["kind"], "mcq")
        self.assertTrue(response.json()["questions"][0]["citations"])

    def test_quiz_generation_normalizes_alternate_fields_and_optional_explanation(self):
        source = {
            "id": "test-source",
            "text": "Photosynthesis converts light energy into chemical energy.",
            "metadata": {"filename": "biology.txt", "page": 1, "section": "Photosynthesis"},
            "score": 0.9,
        }
        question = {
            "topic_name": "Photosynthesis",
            "question_type": "multiple-choice",
            "question_text": "What does photosynthesis convert?",
            "choices": [
                {"text": "A) Light energy into chemical energy"},
                {"text": "B) Chemical energy into light"},
            ],
            "correct_answer": {"text": "A"},
            "citations": [{"source_id": "test-source"}],
        }

        with (
            patch("app.main.settings.groq_api_key", "test-key"),
            patch("app.main.retrieve", return_value=[source]),
            patch("app.main.llm_json", return_value=[question] * 5),
        ):
            response = self.client.post(
                "/api/quiz/generate",
                json={"num_questions": 5},
            )

        self.assertEqual(response.status_code, 200, response.text)
        first = response.json()["questions"][0]
        self.assertEqual(first["prompt"], question["question_text"])
        self.assertEqual(first["kind"], "mcq")
        self.assertEqual(len(first["options"]), 2)

    def test_study_chat_includes_recent_conversation_as_follow_up_context(self):
        source = {
            "id": "test-source",
            "text": "Photosynthesis converts light energy into chemical energy.",
            "metadata": {"filename": "biology.txt", "page": 1, "section": "Photosynthesis"},
            "score": 0.9,
        }
        model = Mock()
        model.invoke.return_value.content = "It stores that energy as chemical energy."

        with (
            patch("app.main.retrieve", return_value=[source]),
            patch("app.rag.llm", return_value=model),
        ):
            response = self.client.post(
                "/api/chat",
                json={
                    "message": "What does it store it as?",
                    "history": [
                        {"role": "user", "content": "Explain photosynthesis."},
                        {"role": "assistant", "content": "It converts light energy."},
                    ],
                },
            )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertIn("Explain photosynthesis.", model.invoke.call_args.args[0])
        self.assertIn("It converts light energy.", model.invoke.call_args.args[0])
        self.assertIn("What does it store it as?", model.invoke.call_args.args[0])
        self.assertIn("Photosynthesis", model.invoke.call_args.args[0])

    def test_study_chat_combines_direct_and_conversation_context_retrieval(self):
        direct_source = {
            "id": "direct-source",
            "text": "The light-dependent reactions produce ATP and NADPH.",
            "metadata": {"filename": "biology.txt", "page": 2, "section": "Light reactions"},
            "score": 0.8,
        }
        contextual_source = {
            "id": "context-source",
            "text": "The Calvin cycle uses ATP and NADPH to fix carbon dioxide.",
            "metadata": {"filename": "biology.txt", "page": 3, "section": "Calvin cycle"},
            "score": 0.9,
        }
        model = Mock()
        model.invoke.return_value.content = "The cycle uses ATP and NADPH to fix carbon dioxide."
        retrieve_results = {
            "What does the cycle use?": [direct_source],
            "Explain photosynthesis. What does the cycle use?": [contextual_source],
        }

        with (
            patch("app.main.retrieve", side_effect=lambda user_id, query: retrieve_results[query]) as retrieve,
            patch("app.rag.llm", return_value=model),
        ):
            response = self.client.post(
                "/api/chat",
                json={
                    "message": "What does the cycle use?",
                    "history": [{"role": "user", "content": "Explain photosynthesis."}],
                },
            )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(retrieve.call_count, 2)
        prompt = model.invoke.call_args.args[0]
        self.assertIn("The light-dependent reactions produce ATP and NADPH.", prompt)
        self.assertIn("The Calvin cycle uses ATP and NADPH to fix carbon dioxide.", prompt)
        self.assertEqual(len(response.json()["citations"]), 2)


if __name__ == "__main__":
    unittest.main()
