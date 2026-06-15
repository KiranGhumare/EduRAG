import os
import shutil
import uuid
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db, SessionLocal
from app.models.models import Course, Material
from app.schemas.schemas import MaterialOut
from app.services.ingestion import ingest_pdf

router = APIRouter(prefix="/courses/{course_id}/materials", tags=["materials"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_TYPES = {
    "application/pdf": "pdf",
    "image/png": "diagram",
    "image/jpeg": "diagram",
    "image/jpg": "diagram",
    "video/mp4": "video",
    "video/quicktime": "video",
}


def process_material(material_id: str, file_path: str, source_type: str,
                       course_id: str, filename: str):
    """Background task with its own DB session — independent of the request's session."""
    db = SessionLocal()
    try:
        material = db.query(Material).filter(Material.id == material_id).first()
        if not material:
            return

        material.status = "processing"
        db.commit()

        if source_type == "pdf":
            chunk_count = ingest_pdf(
                file_path=file_path,
                material_id=material_id,
                course_id=course_id,
                filename=filename,
            )
        else:
            chunk_count = 0

        material.status = "ready" if chunk_count > 0 else "no_text_found"
        material.chunk_count = chunk_count
        db.commit()
    except Exception:
        material.status = "error"
        db.commit()
    finally:
        db.close()


@router.post("/", response_model=MaterialOut, status_code=202)
async def upload_material(
    course_id: UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    content_type = file.content_type or ""
    source_type = ALLOWED_TYPES.get(content_type)
    if not source_type:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {content_type}. Allowed: PDF, PNG, JPEG, MP4",
        )

    material_id = str(uuid.uuid4())
    ext = Path(file.filename).suffix
    storage_path = str(UPLOAD_DIR / f"{material_id}{ext}")

    with open(storage_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    material = Material(
        id=material_id,
        course_id=course_id,
        filename=file.filename,
        source_type=source_type,
        storage_path=storage_path,
        status="pending",
    )
    db.add(material)
    db.commit()
    db.refresh(material)

    background_tasks.add_task(
        process_material,
        material_id=material_id,
        file_path=storage_path,
        source_type=source_type,
        course_id=str(course_id),
        filename=file.filename,
    )

    return material


@router.get("/", response_model=list[MaterialOut])
def list_materials(course_id: UUID, db: Session = Depends(get_db)):
    return (
        db.query(Material)
        .filter(Material.course_id == course_id)
        .order_by(Material.created_at.desc())
        .all()
    )


@router.delete("/{material_id}", status_code=204)
def delete_material(course_id: UUID, material_id: UUID, db: Session = Depends(get_db)):
    material = db.query(Material).filter(
        Material.id == material_id,
        Material.course_id == course_id,
    ).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    if os.path.exists(material.storage_path):
        os.remove(material.storage_path)

    db.delete(material)
    db.commit()