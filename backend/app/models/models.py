import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base

class Course(Base):
    __tablename__="courses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    materials = relationship("Material", back_populates="course", cascade="all, delete-orphan")
    questions = relationship("Question", back_populates="course", cascade="all, delete-orphan")

class Material(Base):
    __tablename__ = "materials"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default = uuid.uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    source_type = Column(String(20), nullable=False)
    storage_path = Column(String(512), nullable = False)
    status = Column(String(20), default="pending")
    chunk_count = Column(Integer, default = 0)
    created_at = Column(DateTime, default = datetime.now)
    course = relationship("Course", back_populates="materials")

class Question(Base):
    __tablename__="questions"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False, default = uuid.uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False)
    question_text = Column(String(255), nullable=False)
    question_type = Column(Text, nullable=False)
    bloom_level = Column(Integer, nullable=False)
    difficulty = Column(String(10), nullable=False)
    source_material_id = Column(UUID(as_uuid=True), ForeignKey=("materials.id"), nullable=True)
    source_location = Column(String(100), nullable=False)
    source_excerpt = Column(Text, nullable=True)

    option_a = Column(Text, nullable=True)
    option_b = Column(Text, nullable=True)
    option_c = Column(Text, nullable=True)
    option_d = Column(Text, nullable=True)
    correct_answer = Column(String(1), nullable=True)
    explanation = Column(Text, nullable=True)

    created_at = Column(DateTime, default = datetime.now)
    course = relationship("Course", back_populates="questions")
    material = relationship("Material")
