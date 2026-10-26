"""Pydantic v2 schemas for Crop Marketplace.

Strictly complies with:
- AGENTS.md Rule 16: Exact quantities, units, and integer money.
- AGENTS.md Rule 17: Approximate coordinate exposure for privacy.
- Phase 6 Exit Criteria: Private contact details are not exposed in list endpoints.
"""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.modules.crop_marketplace.models import CropCategory, CropListingStatus, QuantityUnit


class CropListingCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, populate_by_name=True)

    cropName: str = Field(..., alias="crop_name", min_length=2, max_length=100)
    category: CropCategory
    quantity: float = Field(..., gt=0.0)
    quantityUnit: QuantityUnit = Field(alias="quantity_unit")
    pricePerUnit: int = Field(..., alias="price_per_unit", ge=1, description="Price in BDT")
    expectedHarvestDate: date = Field(alias="expected_harvest_date")
    district: str = Field(..., min_length=2, max_length=100)
    upazila: str = Field(..., min_length=2, max_length=100)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    description: Optional[str] = Field(None, max_length=1000)


class CropListingUpdateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, populate_by_name=True)

    cropName: Optional[str] = Field(None, alias="crop_name", min_length=2, max_length=100)
    quantity: Optional[float] = Field(None, gt=0.0)
    pricePerUnit: Optional[int] = Field(None, alias="price_per_unit", ge=1)
    expectedHarvestDate: Optional[date] = Field(None, alias="expected_harvest_date")
    status: Optional[CropListingStatus] = None
    description: Optional[str] = Field(None, max_length=1000)


class CropListingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: str
    farmerId: str = Field(serialization_alias="farmerId")
    farmerName: str = Field(serialization_alias="farmerName")
    farmerRole: str = Field(serialization_alias="farmerRole")
    cropName: str = Field(serialization_alias="cropName")
    category: CropCategory
    quantity: float
    quantityUnit: QuantityUnit = Field(serialization_alias="quantityUnit")
    pricePerUnit: int = Field(serialization_alias="pricePerUnit")
    expectedHarvestDate: date = Field(serialization_alias="expectedHarvestDate")
    district: str
    upazila: str
    # Rule 17: Approximate coordinate exposure (~1.1km grid)
    approximateLat: float = Field(serialization_alias="approximateLat")
    approximateLon: float = Field(serialization_alias="approximateLon")
    status: CropListingStatus
    isFarmerVerified: bool = Field(default=False, serialization_alias="isFarmerVerified")
    description: Optional[str] = None
    createdAt: datetime = Field(serialization_alias="createdAt")
    updatedAt: datetime = Field(serialization_alias="updatedAt")


class SavedBuyerSearchCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, populate_by_name=True)

    name: str = Field(..., min_length=2, max_length=100)
    category: Optional[CropCategory] = None
    cropName: Optional[str] = Field(None, alias="crop_name", max_length=100)
    district: Optional[str] = Field(None, max_length=100)
    maxPrice: Optional[int] = Field(None, alias="max_price", ge=1)
    minQuantity: Optional[float] = Field(None, alias="min_quantity", gt=0.0)


class SavedBuyerSearchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: str
    buyerId: str = Field(serialization_alias="buyerId")
    name: str
    category: Optional[CropCategory] = None
    cropName: Optional[str] = Field(None, serialization_alias="cropName")
    district: Optional[str] = None
    maxPrice: Optional[int] = Field(None, serialization_alias="maxPrice")
    minQuantity: Optional[float] = Field(None, serialization_alias="minQuantity")
    isActive: bool = Field(serialization_alias="isActive")
    createdAt: datetime = Field(serialization_alias="createdAt")
    updatedAt: datetime = Field(serialization_alias="updatedAt")

