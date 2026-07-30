from fastapi import APIRouter, UploadFile, File

from app.schemas.upload_schema import UploadResponse
from app.services.upload_service import (
    save_file,
    analyze_dataset
)

router = APIRouter()


@router.post(
    "/upload",
    response_model=UploadResponse
)
async def upload_dataset(file: UploadFile = File(...)):
    file_path = save_file(file)

    result = analyze_dataset(file_path)

    return UploadResponse(**result)