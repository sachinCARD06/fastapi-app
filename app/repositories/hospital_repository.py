from sqlalchemy.orm import Session, joinedload

from app.models.hospital import Hospital
from app.repositories.base import BaseRepository


def _with_users(query):
    return query.options(
        joinedload(Hospital.creator),
        joinedload(Hospital.updater),
    )


class HospitalRepository(BaseRepository[Hospital]):
    def get(self, db: Session, id: int) -> Hospital | None:
        return (
            _with_users(db.query(Hospital))
            .filter(Hospital.id == id)
            .first()
        )

    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100) -> list[Hospital]:
        return _with_users(db.query(Hospital)).offset(skip).limit(limit).all()

    def get_by_name(self, db: Session, *, name: str) -> Hospital | None:
        return db.query(Hospital).filter(Hospital.name == name).first()

    def name_exists(self, db: Session, *, name: str) -> bool:
        return db.query(Hospital.id).filter(Hospital.name == name).first() is not None

    def get_active(self, db: Session, *, skip: int = 0, limit: int = 100) -> list[Hospital]:
        return (
            _with_users(db.query(Hospital))
            .filter(Hospital.is_active == True)  # noqa: E712
            .offset(skip)
            .limit(limit)
            .all()
        )


hospital_repository = HospitalRepository(Hospital)
