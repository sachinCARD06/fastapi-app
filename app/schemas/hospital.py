from pydantic import BaseModel


class UserBrief(BaseModel):
    id: int
    email: str
    full_name: str | None = None

    model_config = {"from_attributes": True}


class HospitalBase(BaseModel):
    name: str
    address: str
    city: str
    mobile_number: str


class HospitalCreate(HospitalBase):
    pass


class HospitalUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    city: str | None = None
    mobile_number: str | None = None
    is_active: bool | None = None


class HospitalResponse(HospitalBase):
    id: int
    is_active: bool
    created_by: int | None
    updated_by: int | None
    creator: UserBrief | None
    updater: UserBrief | None

    model_config = {"from_attributes": True}
