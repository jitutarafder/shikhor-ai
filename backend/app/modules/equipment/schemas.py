"""Pydantic v2 schemas for Equipment listings and ranked discovery."""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.modules.equipment.models import EquipmentType, PriceUnit


class EquipmentCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, populate_by_name=True)

    name: str = Field(..., min_length=2, max_length=100)
    equipmentType: EquipmentType = Field(alias="equipment_type")
    description: Optional[str] = Field(None, max_length=1000)
    priceAmount: int = Field(alias="price_amount", ge=10, description="Price in BDT")
    priceUnit: PriceUnit = Field(alias="price_unit")
    district: str = Field(..., min_length=2, max_length=100)
    upazila: str = Field(..., min_length=2, max_length=100)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    serviceRadiusKm: float = Field(default=15.0, alias="service_radius_km", ge=1.0, le=100.0)


class EquipmentUpdateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, populate_by_name=True)

    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    priceAmount: Optional[int] = Field(None, alias="price_amount", ge=10)
    serviceRadiusKm: Optional[float] = Field(None, alias="service_radius_km", ge=1.0, le=100.0)
    isAvailable: Optional[bool] = Field(None, alias="is_available")
    isPaused: Optional[bool] = Field(None, alias="is_paused")


class RankingBreakdownSchema(BaseModel):
    priceScore: float
    distanceScore: float
    rankingScore: float
    distanceKm: float


class EquipmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: str
    owner_id: str = Field(serialization_alias="ownerId")
    name: str
    equipment_type: EquipmentType = Field(serialization_alias="equipmentType")
    description: Optional[str] = None
    price_amount: int = Field(serialization_alias="priceAmount")
    price_unit: PriceUnit = Field(serialization_alias="priceUnit")
    district: str
    upazila: str
    service_radius_km: float = Field(serialization_alias="serviceRadiusKm")
    is_available: bool = Field(serialization_alias="isAvailable")
    is_paused: bool = Field(serialization_alias="isPaused")
    approximate_lat: float = Field(serialization_alias="approximateLat")
    approximate_lon: float = Field(serialization_alias="approximateLon")
    owner_name: Optional[str] = Field(default=None, serialization_alias="ownerName")
    is_owner_verified: bool = Field(default=False, serialization_alias="isOwnerVerified")
    average_rating: Optional[float] = Field(default=None, serialization_alias="averageRating")
    review_count: int = Field(default=0, serialization_alias="reviewCount")
    created_at: datetime = Field(serialization_alias="createdAt")

    # Optional ranking metrics if queried through search
    ranking: Optional[RankingBreakdownSchema] = None


class EquipmentReviewCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, populate_by_name=True)

    rentalRequestId: str = Field(..., alias="rental_request_id")
    rating: int = Field(..., ge=1, le=5, description="Star rating 1 to 5")
    comment: Optional[str] = Field(None, max_length=500, description="Optional feedback in Bangla or English")


class EquipmentReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    equipment_id: str = Field(serialization_alias="equipmentId")
    renter_id: str = Field(serialization_alias="renterId")
    renter_name: str = Field(serialization_alias="renterName")
    rental_request_id: str = Field(serialization_alias="rentalRequestId")
    rating: int
    comment: Optional[str] = None
    created_at: datetime = Field(serialization_alias="createdAt")


class BookedDateItem(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    rental_date: date = Field(serialization_alias="rentalDate")
    date: str = ""
    duration_units: int = Field(default=1, serialization_alias="durationUnits")
    status: str = "booked"


class EquipmentAvailabilityResponse(BaseModel):
    equipment_id: str = Field(serialization_alias="equipmentId")
    booked_dates: list[BookedDateItem] = Field(default_factory=list, serialization_alias="bookedDates")
