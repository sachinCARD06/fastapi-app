from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.hospital import Hospital
from app.repositories.hospital_repository import hospital_repository
from app.schemas.hospital import HospitalCreate, HospitalUpdate


class HospitalService:
    def get_by_id(self, db: Session, hospital_id: int) -> Hospital:
        hospital = hospital_repository.get(db, hospital_id)
        if not hospital:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hospital not found")
        return hospital

    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> list[Hospital]:
        return hospital_repository.get_multi(db, skip=skip, limit=limit)

    def get_active(self, db: Session, skip: int = 0, limit: int = 100) -> list[Hospital]:
        return hospital_repository.get_active(db, skip=skip, limit=limit)

    def create(self, db: Session, hospital_in: HospitalCreate, created_by: int) -> Hospital:
        if hospital_repository.name_exists(db, name=hospital_in.name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Hospital with this name already exists",
            )
        return hospital_repository.create(
            db, obj_in={**hospital_in.model_dump(), "created_by": created_by}
        )

    def update(
        self, db: Session, hospital_id: int, hospital_in: HospitalUpdate, updated_by: int
    ) -> Hospital:
        hospital = self.get_by_id(db, hospital_id)
        update_data = hospital_in.model_dump(exclude_none=True)
        if "name" in update_data and update_data["name"] != hospital.name:
            if hospital_repository.name_exists(db, name=update_data["name"]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Hospital with this name already exists",
                )
        update_data["updated_by"] = updated_by
        return hospital_repository.update(db, db_obj=hospital, obj_in=update_data)

    def delete(self, db: Session, hospital_id: int) -> Hospital:
        hospital = hospital_repository.delete(db, id=hospital_id)
        if not hospital:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hospital not found")
        return hospital


hospital_service = HospitalService()
