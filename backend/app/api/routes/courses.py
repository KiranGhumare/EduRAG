from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import Course
from app.schemas.schemas import CourseCreate, CourseOut

router = APIRouter(prefix="/courses", tags=["courses"])

@router.post("/", response_model = CourseOut, status_code = 201)
def create_course(payload: CourseCreate, db: Session = Depends(get_db)):
    course = Course(name=payload.name, description = payload.description)
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


@router.get("/", response_model = list[CourseOut])
def list_courses(db: Session = Depends(get_db)):
    return db.query(Course).order_by(Course.created_at.desc()).all()


@router.get("/{course_id}", response_model=CourseOut)
def get_course(course_id: UUID, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.delete("/{course_id}", status_code=204)
def delete_course(course_id: UUID, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    db.delete(course)
    db.commit()