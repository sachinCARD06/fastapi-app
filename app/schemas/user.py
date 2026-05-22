from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = None
    password: str | None = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_superuser: bool

    model_config = {"from_attributes": True}
