import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base, get_db
from app.main import app
from app.models import Document, Topic, User
from app.security import current_user


class UploadWithoutAITests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        self.engine = create_engine(
            f"sqlite:///{root / 'upload-test.db'}",
            connect_args={"check_same_thread": False},
        )
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.db = self.session_factory()
        self.user = User(
            id=1,
            email="upload-test@example.com",
            name="Upload Test",
            password_hash="not-used",
        )
        self.db.add(self.user)
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
        self.upload_path = root / "uploads"

    def tearDown(self):
        app.dependency_overrides.clear()
        self.db.close()
        self.engine.dispose()
        self.temp_dir.cleanup()

    def test_syllabus_upload_indexes_and_extracts_topics_without_groq(self):
        syllabus = b"""Biology Syllabus
Chapter 1: Cell Biology
1.1 Cell structure
1.2 Cell membranes
Chapter 2: Photosynthesis
"""
        with (
            patch("app.main.settings.groq_api_key", ""),
            patch("app.main.settings.upload_path", str(self.upload_path)),
            patch("app.main.index_chunks") as index_chunks,
        ):
            response = self.client.post(
                "/api/documents/upload",
                data={"kind": "syllabus"},
                files={"file": ("syllabus.txt", syllabus, "text/plain")},
            )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["chunks"], 1)
        index_chunks.assert_called_once()
        topic_names = {
            topic.name for topic in self.db.query(Topic).filter_by(user_id=self.user.id).all()
        }
        self.assertIn("Cell Biology", topic_names)
        self.assertIn("Photosynthesis", topic_names)
        self.assertEqual(
            self.db.query(Document).filter_by(user_id=self.user.id).count(),
            1,
        )

    def test_notes_upload_does_not_require_groq(self):
        with (
            patch("app.main.settings.groq_api_key", ""),
            patch("app.main.settings.upload_path", str(self.upload_path)),
            patch("app.main.index_chunks"),
        ):
            response = self.client.post(
                "/api/documents/upload",
                data={"kind": "notes"},
                files={"file": ("notes.txt", b"Cell membranes regulate transport.", "text/plain")},
            )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["kind"], "notes")


if __name__ == "__main__":
    unittest.main()
