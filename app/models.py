from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import field_validator

class UserCreate(BaseModel):
    phone_number: str
    
    @field_validator('phone_number')
    def validate_phone(cls, v):
        import re
        if not re.match(r'^09[0-9]{9}$', v):
            raise ValueError('Phone number must start with 09 and be 11 digits')
        return v

class UserRole(str, Enum):
    PASSENGER = "passenger"
    OPERATOR = "operator"
    ADMIN = "admin"

class RouteCreate(BaseModel):
    origin: str
    destination: str
    base_price: float = Field(..., gt=0)
    distance_km: Optional[int] = None

class RouteResponse(BaseModel):
    id: int
    origin: str
    destination: str
    base_price: float
    distance_km: Optional[int]

class BusCreate(BaseModel):
    bus_number: str
    driver_name: str
    capacity: int = Field(..., ge=10, le=60)
    route_id: int
    model: Optional[str] = None

class TripCreate(BaseModel):
    bus_id: int
    route_id: int
    departure_time: datetime
    arrival_time: datetime
    price: float = Field(..., gt=0)
    
    @validator('arrival_time')
    def validate_times(cls, v, values):
        if 'departure_time' in values and v <= values['departure_time']:
            raise ValueError('arrival_time must be after departure_time')
        return v

class BookingRequest(BaseModel):
    user_id: int
    trip_id: int
    seat_number: int

class CancelRequest(BaseModel):
    booking_code: str
    user_id: int