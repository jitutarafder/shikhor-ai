"""MongoDB Index initialization manager.

Enforces production-ready indexes:
- 2dsphere indexes for geospatial equipment & crop queries (Rule 17).
- TTL indexes for automated expiration of refresh sessions, OTPs, and idempotency cache.
- Compound unique indexes for identity, blocks, and idempotency guarantees.
- Worker polling indexes for background jobs (Rule 25).
"""

import logging
from typing import Any, Dict, List
import pymongo
from pymongo import ASCENDING, DESCENDING, GEOSPHERE, TEXT, IndexModel
from pymongo.database import Database

logger = logging.getLogger("shikhor.db.mongo.indexes")


INDEX_SPECIFICATIONS: Dict[str, List[IndexModel]] = {
    # 1. users
    "users": [
        IndexModel([("id", ASCENDING)], unique=True, name="idx_users_id"),
        IndexModel([("phone", ASCENDING)], unique=True, name="idx_users_phone_unique"),
        IndexModel(
            [("email", ASCENDING)],
            unique=True,
            partialFilterExpression={"email": {"$type": "string"}},
            name="idx_users_email_sparse_unique",
        ),
        IndexModel(
            [("nid", ASCENDING)],
            unique=True,
            partialFilterExpression={"nid": {"$type": "string"}},
            name="idx_users_nid_sparse_unique",
        ),
        IndexModel([("role", ASCENDING)], name="idx_users_role"),
        IndexModel([("is_active", ASCENDING)], name="idx_users_is_active"),
    ],

    # 2. crop_cases
    "crop_cases": [
        IndexModel([("id", ASCENDING)], unique=True, name="idx_crop_cases_id"),
        IndexModel([("user_id", ASCENDING), ("created_at", DESCENDING)], name="idx_crop_cases_user_created"),
        IndexModel([("status", ASCENDING), ("is_reviewed_by_expert", ASCENDING)], name="idx_crop_cases_status_expert"),
        IndexModel([("crop_type", ASCENDING)], name="idx_crop_cases_crop_type"),
    ],

    # 3. equipment (Geospatial 2dsphere)
    "equipment": [
        IndexModel([("id", ASCENDING)], unique=True, name="idx_equipment_id"),
        IndexModel([("location", GEOSPHERE)], name="idx_equipment_location_2dsphere"),
        IndexModel([("owner_id", ASCENDING)], name="idx_equipment_owner_id"),
        IndexModel(
            [("equipment_type", ASCENDING), ("price_unit", ASCENDING), ("is_available", ASCENDING)],
            name="idx_equipment_ranking_filter",
        ),
        IndexModel([("district", ASCENDING), ("upazila", ASCENDING)], name="idx_equipment_location_text"),
    ],

    # 4. rental_requests
    "rental_requests": [
        IndexModel([("id", ASCENDING)], unique=True, name="idx_rental_requests_id"),
        IndexModel([("equipment_id", ASCENDING), ("status", ASCENDING)], name="idx_rental_equipment_status"),
        IndexModel([("renter_id", ASCENDING), ("status", ASCENDING)], name="idx_rental_renter_status"),
        IndexModel([("owner_id", ASCENDING), ("status", ASCENDING)], name="idx_rental_owner_status"),
        IndexModel([("idempotency_key", ASCENDING)], sparse=True, name="idx_rental_idempotency"),
    ],

    # 5. crop_listings (Geospatial 2dsphere)
    "crop_listings": [
        IndexModel([("id", ASCENDING)], unique=True, name="idx_crop_listings_id"),
        IndexModel([("approximate_location", GEOSPHERE)], name="idx_crop_listings_location_2dsphere"),
        IndexModel(
            [("category", ASCENDING), ("status", ASCENDING), ("district", ASCENDING)],
            name="idx_crop_listings_search",
        ),
        IndexModel([("farmer_id", ASCENDING), ("status", ASCENDING)], name="idx_crop_listings_farmer_status"),
    ],

    # 6. saved_buyer_searches
    "saved_buyer_searches": [
        IndexModel([("id", ASCENDING)], unique=True, name="idx_saved_searches_id"),
        IndexModel([("buyer_id", ASCENDING), ("is_active", ASCENDING)], name="idx_saved_searches_buyer_active"),
    ],

    # 7. conversations
    "conversations": [
        IndexModel([("id", ASCENDING)], unique=True, name="idx_conversations_id"),
        IndexModel([("participants", ASCENDING)], name="idx_conversations_participants"),
        IndexModel([("updated_at", DESCENDING)], name="idx_conversations_updated_at"),
    ],

    # 8. messages
    "messages": [
        IndexModel([("id", ASCENDING)], unique=True, name="idx_messages_id"),
        IndexModel([("conversation_id", ASCENDING), ("created_at", ASCENDING)], name="idx_messages_conv_created"),
        IndexModel([("sender_id", ASCENDING)], name="idx_messages_sender_id"),
    ],

    # 9. knowledge_articles
    "knowledge_articles": [
        IndexModel([("id", ASCENDING)], unique=True, name="idx_knowledge_id"),
        IndexModel([("crop_type", ASCENDING), ("category", ASCENDING)], name="idx_knowledge_crop_cat"),
        IndexModel([("title_bn", TEXT), ("summary_bn", TEXT), ("content_bn", TEXT)], name="idx_knowledge_text_search"),
    ],

    # 10. notifications
    "notifications": [
        IndexModel([("id", ASCENDING)], unique=True, name="idx_notifications_id"),
        IndexModel([("user_id", ASCENDING), ("is_read", ASCENDING), ("created_at", DESCENDING)], name="idx_notifications_user_inbox"),
    ],

    # 11. moderation_reports
    "moderation_reports": [
        IndexModel([("id", ASCENDING)], unique=True, name="idx_reports_id"),
        IndexModel([("reporter_id", ASCENDING)], name="idx_reports_reporter"),
        IndexModel([("reported_user_id", ASCENDING)], sparse=True, name="idx_reports_reported_user"),
        IndexModel([("status", ASCENDING), ("created_at", DESCENDING)], name="idx_reports_status_created"),
    ],

    # 12. user_blocks
    "user_blocks": [
        IndexModel([("id", ASCENDING)], unique=True, name="idx_blocks_id"),
        IndexModel([("blocker_id", ASCENDING), ("blocked_id", ASCENDING)], unique=True, name="idx_blocks_unique_pair"),
    ],

    # 13. pilot_feedback
    "pilot_feedback": [
        IndexModel([("id", ASCENDING)], unique=True, name="idx_pilot_id"),
        IndexModel([("user_id", ASCENDING), ("created_at", DESCENDING)], name="idx_pilot_user_created"),
        IndexModel([("task_type", ASCENDING)], name="idx_pilot_task_type"),
    ],

    # 14. audit_logs
    "audit_logs": [
        IndexModel([("id", ASCENDING)], unique=True, name="idx_audit_id"),
        IndexModel([("actor_id", ASCENDING)], sparse=True, name="idx_audit_actor"),
        IndexModel([("action", ASCENDING), ("created_at", DESCENDING)], name="idx_audit_action_created"),
        IndexModel([("resource_type", ASCENDING), ("resource_id", ASCENDING)], name="idx_audit_resource"),
    ],

    # 15. refresh_sessions (TTL Index: 0 seconds after expires_at)
    "refresh_sessions": [
        IndexModel([("id", ASCENDING)], unique=True, name="idx_sessions_id"),
        IndexModel([("expires_at", ASCENDING)], expireAfterSeconds=0, name="idx_sessions_ttl"),
        IndexModel([("user_id", ASCENDING), ("is_revoked", ASCENDING)], name="idx_sessions_user_revoked"),
        IndexModel([("token_hash", ASCENDING)], unique=True, name="idx_sessions_token_hash"),
    ],

    # 16. otps (TTL Index: 0 seconds after expires_at)
    "otps": [
        IndexModel([("id", ASCENDING)], unique=True, name="idx_otps_id"),
        IndexModel([("expires_at", ASCENDING)], expireAfterSeconds=0, name="idx_otps_ttl"),
        IndexModel([("email", ASCENDING), ("purpose", ASCENDING)], name="idx_otps_email_purpose"),
        IndexModel([("otp_hash", ASCENDING)], name="idx_otps_hash"),
    ],

    # 17. idempotency_records (Compound unique + TTL retention for 48 hours)
    "idempotency_records": [
        IndexModel([("id", ASCENDING)], unique=True, name="idx_idempotency_id"),
        IndexModel(
            [("user_id", ASCENDING), ("operation", ASCENDING), ("idempotency_key", ASCENDING)],
            unique=True,
            name="idx_idempotency_compound_unique",
        ),
        IndexModel([("created_at", ASCENDING)], expireAfterSeconds=172800, name="idx_idempotency_ttl_48h"),
    ],

    # 18. background_jobs (Worker polling compound index)
    "background_jobs": [
        IndexModel([("id", ASCENDING)], unique=True, name="idx_jobs_id"),
        IndexModel(
            [("status", ASCENDING), ("priority", DESCENDING), ("scheduled_at", ASCENDING)],
            name="idx_jobs_worker_poll",
        ),
        IndexModel([("locked_by", ASCENDING), ("locked_at", ASCENDING)], name="idx_jobs_lock"),
    ],
}


def ensure_mongo_indexes(db: Database) -> Dict[str, List[str]]:
    """Initializes all production indexes across MongoDB collections safely.

    Returns:
        Dict mapping collection names to created index names.
    """
    created_indexes_summary: Dict[str, List[str]] = {}

    for collection_name, models in INDEX_SPECIFICATIONS.items():
        coll = db[collection_name]
        created = []
        for model in models:
            try:
                res = coll.create_indexes([model])
                created.extend(res)
            except Exception:
                # If index options changed or conflict, attempt to drop obsolete index and recreate
                index_name = model.document.get("name")
                if index_name:
                    try:
                        coll.drop_index(index_name)
                        res = coll.create_indexes([model])
                        created.extend(res)
                        logger.info(f"[MongoDB Indexes] Re-created evolved index '{index_name}' on '{collection_name}'")
                    except Exception as inner_exc:
                        logger.error(f"[MongoDB Indexes] Failed creating index '{index_name}' on '{collection_name}': {inner_exc}")
        created_indexes_summary[collection_name] = created

    return created_indexes_summary
