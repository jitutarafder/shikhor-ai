"""API v1 router aggregator."""

from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    crop_assistant,
    crop_marketplace,
    equipment,
    health,
    messaging,
    rentals,
    weather,
    knowledge,
    sync,
    admin,
    pilot,
    users,
    expert,
    notifications,
    jobs,
    crop_disease,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(crop_disease.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(notifications.router)
api_router.include_router(crop_assistant.router)
api_router.include_router(expert.router)
api_router.include_router(equipment.router)
api_router.include_router(rentals.router)
api_router.include_router(weather.router)
api_router.include_router(crop_marketplace.router)
api_router.include_router(messaging.router)
api_router.include_router(knowledge.router)
api_router.include_router(sync.router)
api_router.include_router(admin.router)
api_router.include_router(pilot.router)
api_router.include_router(jobs.router)


