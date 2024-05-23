from datetime import datetime

from pydantic import BaseModel

from company.schemas import CompanySchema
from db.models.doctors.company_doctor import CompanyDoctor


class NoteHistorySchema(BaseModel):
    id: int
    title: str
    description: str
    note_type: str
    note_format: str
    created_at: datetime
    updated_at: datetime


class CreateNoteSchema(BaseModel):
    title: str = "Note title"
    description: str | None = None
    note_type: str
    note_format: str
    user_id: int


class UpdateNote(BaseModel):
    title: str | None = None
    description: str | None = None


