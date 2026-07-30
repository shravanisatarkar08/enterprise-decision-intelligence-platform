from pydantic import BaseModel


class UploadResponse(BaseModel):
    filename: str
    rows: int
    columns: int
    status: str