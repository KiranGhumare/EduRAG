from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import Course, ChatMessage
from app.schemas.schemas import ChatRequest, ChatResponse, ChatMessageOut
from app.services.chat_service import handle_chat_message

router = APIRouter(prefix="/courses/{course_id}/chat", tags=["chat"])

@router.post("/", response_model = ChatResponse, status_code=201)
def chat(course_id:UUID, payload: ChatRequest, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id==course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    user_message = ChatMessage(
        course_id = course_id,
        role="user",
        content=payload.message,
        message_type="text"
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    response = handle_chat_message(
        course_id=str(course_id),
        user_message=payload.message,
        db=db,
    )

    return response


@router.get("/", response_model=list[ChatMessageOut])
def get_chat_history(course_id: UUID, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    return course.chat_messages