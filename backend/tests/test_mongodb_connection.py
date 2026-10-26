"""Unit and integration tests for MongoDB Atlas connection module.

Complies with:
- AGENTS.md Rule 4: No hardcoded secrets.
- AGENTS.md Rule 11 & 26: Safe error handling without credential leakage.
- AGENTS.md Rule 28: Mandatory testing for all changed connection and security logic.
"""

import pytest
from unittest.mock import MagicMock, patch
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from app.core.config import settings
import app.db.mongodb as mongo_module
from app.db.mongodb import (
    close_mongodb_connection,
    get_mongo_client,
    get_mongo_db,
    verify_mongodb_connection,
)


@pytest.fixture(autouse=True)
def cleanup_mongo_client():
    """Ensures singleton client is cleanly reset before and after each test."""
    close_mongodb_connection()
    yield
    close_mongodb_connection()


def test_mongodb_unconfigured():
    """When MONGODB_URL is empty, client returns None and verification is false."""
    with patch.object(settings, "MONGODB_URL", ""):
        client = get_mongo_client()
        assert client is None

        db = get_mongo_db()
        assert db is None

        status = verify_mongodb_connection()
        assert status["configured"] is False
        assert status["connected"] is False
        assert "not set" in status["message"]


def test_mongodb_connection_successful_ping():
    """When MongoDB Atlas is configured and ping succeeds, returns connected: True."""
    mock_client = MagicMock()
    mock_client.admin.command.return_value = {"ok": 1.0}
    mock_client.__getitem__.return_value = MagicMock()

    with patch.object(settings, "MONGODB_URL", "mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true&w=majority"), \
         patch.object(settings, "MONGODB_DB_NAME", "Shikhor"), \
         patch("app.db.mongodb.MongoClient", return_value=mock_client):

        client = get_mongo_client()
        assert client is not None

        db = get_mongo_db()
        assert db is not None
        mock_client.__getitem__.assert_called_with("Shikhor")

        status = verify_mongodb_connection()
        assert status["configured"] is True
        assert status["connected"] is True
        assert status["database"] == "Shikhor"
        mock_client.admin.command.assert_called_with("ping")


def test_mongodb_connection_failure_safe_handling():
    """When MongoDB connection fails, handles error safely without leaking credentials."""
    mock_client = MagicMock()
    mock_client.admin.command.side_effect = ServerSelectionTimeoutError("SSL handshake failed or cluster unreachable")

    with patch.object(settings, "MONGODB_URL", "mongodb+srv://secret_user:super_secret_password@cluster.mongodb.net/?retryWrites=true&w=majority"), \
         patch.object(settings, "MONGODB_DB_NAME", "Shikhor"), \
         patch("app.db.mongodb.MongoClient", return_value=mock_client):

        status = verify_mongodb_connection()
        assert status["configured"] is True
        assert status["connected"] is False
        assert status["database"] == "Shikhor"
        # Ensure password or connection URL is never leaked in the user-facing message
        assert "super_secret_password" not in status["message"]
        assert "secret_user" not in status["message"]
