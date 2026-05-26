from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_active_user, get_current_superuser
from app.models.user import User
from app.schemas.hospital import HospitalCreate, HospitalResponse, HospitalUpdate
from app.services.hospital_service import hospital_service

router = APIRouter()


@router.get("", response_model=list[HospitalResponse])
def list_hospitals(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    return hospital_service.get_all(db, skip=skip, limit=limit)


@router.get("/active", response_model=list[HospitalResponse])
def list_active_hospitals(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    return hospital_service.get_active(db, skip=skip, limit=limit)


@router.post("", response_model=HospitalResponse, status_code=status.HTTP_201_CREATED)
def create_hospital(
    hospital_in: HospitalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
):
    return hospital_service.create(db, hospital_in, created_by=current_user.id)


@router.get("/{hospital_id}", response_model=HospitalResponse)
def get_hospital(
    hospital_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    return hospital_service.get_by_id(db, hospital_id)


@router.patch("/{hospital_id}", response_model=HospitalResponse)
def update_hospital(
    hospital_id: int,
    hospital_in: HospitalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
):
    return hospital_service.update(db, hospital_id, hospital_in, updated_by=current_user.id)


@router.delete("/{hospital_id}", response_model=HospitalResponse)
def delete_hospital(
    hospital_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
):
    return hospital_service.delete(db, hospital_id)
