"""Pydantic v2 schemas for Rental Requests and state transitions."""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.modules.rentals.models import RentalStatus


class RentalRequestCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, populate_by_name=True)

    equipmentId: str = Field(alias="equipment_id")
    rentalDate: date = Field(alias="rental_date")
    durationUnits: int = Field(default=1, ge=1, alias="duration_units")
    selectedDates: Optional[list[date]] = Field(default=None, alias="selected_dates")
    note: Optional[str] = Field(None, max_length=500)
    # Rule 21: Idempotency key for offline sync
    idempotencyKey: Optional[str] = Field(None, alias="idempotency_key", max_length=64)


class RentalStatusUpdateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, populate_by_name=True)
    targetStatus: RentalStatus = Field(alias="target_status")


class RentalRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: str
    equipment_id: str = Field(serialization_alias="equipmentId")
    renter_id: str = Field(serialization_alias="renterId")
    rental_date: date = Field(serialization_alias="rentalDate")
    selected_dates: Optional[str] = Field(default=None, serialization_alias="selectedDates")
    duration_units: int = Field(serialization_alias="durationUnits")
    total_estimated_price: int = Field(serialization_alias="totalEstimatedPrice")
    status: RentalStatus
    note: Optional[str] = None
    idempotency_key: Optional[str] = Field(None, serialization_alias="idempotencyKey")
    created_at: datetime = Field(serialization_alias="createdAt")
