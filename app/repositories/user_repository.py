from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def get_by_email(self, db: Session, *, email: str) -> User | None:
        return db.query(User).filter(User.email == email).first()

    def email_exists(self, db: Session, *, email: str) -> bool:
        return db.query(User.id).filter(User.email == email).first() is not None


user_repository = UserRepository(User)
