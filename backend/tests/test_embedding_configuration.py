import unittest

from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

from app.rag import embedding_function


class EmbeddingConfigurationTests(unittest.TestCase):
    def test_uses_chromas_lightweight_default_embedding_function(self):
        self.assertIsInstance(embedding_function(), DefaultEmbeddingFunction)


if __name__ == "__main__":
    unittest.main()
