from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.repositories.user_repository import user_repository
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    def get_by_id(self, db: Session, user_id: int) -> User:
        user = user_repository.get(db, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user

    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> list[User]:
        return user_repository.get_multi(db, skip=skip, limit=limit)

    def create(self, db: Session, user_in: UserCreate) -> User:
        if user_repository.email_exists(db, email=user_in.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        return user_repository.create(
            db,
            obj_in={
                **user_in.model_dump(exclude={"password"}),
                "hashed_password": get_password_hash(user_in.password),
            },
        )

    def update(self, db: Session, user: User, user_in: UserUpdate) -> User:
        update_data = user_in.model_dump(exclude_none=True)
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
        return user_repository.update(db, db_obj=user, obj_in=update_data)

    def delete(self, db: Session, user_id: int) -> User:
        user = user_repository.delete(db, id=user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user

    def authenticate(self, db: Session, email: str, password: str) -> User | None:
        user = user_repository.get_by_email(db, email=email)
        if not user or not verify_password(password, user.hashed_password):
            return None
        return user
    

user_service = UserService()
