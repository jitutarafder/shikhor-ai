"""MongoDB Atlas connection manager for Shikhor AI backend.

Complies with:
- AGENTS.md Rule 4: No hardcoded secrets. Reads MONGODB_URL and MONGODB_DB_NAME from typed settings / .env.
- AGENTS.md Rule 11 & 26: Safe error handling without leaking raw connection strings or credentials.
- AGENTS.md Rule 5: Clean separation between relational (SQLite/PostgreSQL) and document storage.
"""

import logging
from typing import Any, Dict, Optional
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, ConfigurationError, PyMongoError

from app.core.config import settings

logger = logging.getLogger("shikhor.db.mongodb")

_mongo_client: Optional[MongoClient] = None


def get_mongo_client() -> Optional[MongoClient]:
    """Returns singleton PyMongo client instance if MONGODB_URL is configured."""
    global _mongo_client
    if _mongo_client is not None:
        return _mongo_client

    mongo_url = settings.MONGODB_URL.strip()
    if not mongo_url:
        logger.info("[MongoDB] MONGODB_URL is not configured. MongoDB integration is inactive.")
        return None

    try:
        import certifi
        tls_ca = certifi.where()
    except Exception:
        tls_ca = None

    try:
        # Initialise MongoClient with bounded timeout for resilience and certifi CA bundle
        client_kwargs = {
            "serverSelectionTimeoutMS": 5000,
            "connectTimeoutMS": 5000,
            "socketTimeoutMS": 10000,
            "maxPoolSize": 20,
            "minPoolSize": 1,
            "appName": "ShikhorAI",
        }
        if tls_ca:
            client_kwargs["tlsCAFile"] = tls_ca

        _mongo_client = MongoClient(mongo_url, **client_kwargs)
        return _mongo_client
    except (ConfigurationError, PyMongoError) as exc:
        logger.error(f"[MongoDB] Failed to initialize MongoClient: {exc.__class__.__name__}")
        return None


def get_mongo_db() -> Optional[Database]:
    """Returns the target MongoDB database instance (default: 'Shikhor')."""
    client = get_mongo_client()
    if client is None:
        return None

    db_name = settings.MONGODB_DB_NAME.strip() or "Shikhor"
    return client[db_name]


def verify_mongodb_connection() -> Dict[str, Any]:
    """Verifies active connectivity to MongoDB Atlas by pinging admin database.

    Returns:
        Dict with connection status, database name, and safe sanitized error message if failed.
    """
    mongo_url = settings.MONGODB_URL.strip()
    db_name = settings.MONGODB_DB_NAME.strip() or "Shikhor"

    if not mongo_url:
        return {
            "configured": False,
            "connected": False,
            "database": db_name,
            "message": "MONGODB_URL is not set in environment.",
        }

    client = get_mongo_client()
    if client is None:
        return {
            "configured": True,
            "connected": False,
            "database": db_name,
            "message": "Failed to create MongoClient instance.",
        }

    try:
        # Ping the server to verify active Atlas connection
        client.admin.command("ping")
        logger.info(f"[MongoDB] Successfully connected to MongoDB Atlas (Database: '{db_name}')")
        return {
            "configured": True,
            "connected": True,
            "database": db_name,
            "message": f"Successfully connected to MongoDB database '{db_name}'.",
        }
    except ConnectionFailure as exc:
        logger.warning(f"[MongoDB] Connection failure to MongoDB Atlas: {exc.__class__.__name__}")
        return {
            "configured": True,
            "connected": False,
            "database": db_name,
            "message": "Could not connect to MongoDB Atlas server. Check network or connection string.",
        }
    except Exception as exc:
        logger.warning(f"[MongoDB] MongoDB verification error: {exc.__class__.__name__}")
        close_mongodb_connection()
        return {
            "configured": True,
            "connected": False,
            "database": db_name,
            "message": f"MongoDB verification failed: {exc.__class__.__name__}",
        }


def close_mongodb_connection() -> None:
    """Closes the MongoDB client connection pool cleanly."""
    global _mongo_client
    if _mongo_client is not None:
        try:
            _mongo_client.close()
            logger.info("[MongoDB] Closed MongoDB client connection.")
        except Exception as exc:
            logger.warning(f"[MongoDB] Error closing connection: {exc}")
        finally:
            _mongo_client = None
