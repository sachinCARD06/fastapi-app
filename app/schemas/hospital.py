from pydantic import BaseModel


class UserBrief(BaseModel):
    id: str
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
    id: str
    is_active: bool
    created_by: str | None
    updated_by: str | None
    creator: UserBrief | None
    updater: UserBrief | None

    model_config = {"from_attributes": True}
