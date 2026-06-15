from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import Course, Material, Question
from app.schemas.schemas import GenerateQuestionsRequest, QuestionOut

router = APIRouter(prefix="/questions", tags=["questions"])


@router.get("/course/{course_id}", response_model=list[QuestionOut])
def list_questions(course_id: UUID, db: Session = Depends(get_db)):
    return (
        db.query(Question)
        .filter(Question.course_id == course_id)
        .order_by(Question.created_at.desc())
        .all()
    )


@router.delete("/{question_id}", status_code=204)
def delete_question(question_id: UUID, db: Session = Depends(get_db)):
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    db.delete(q)
    db.commit()