from pydantic import BaseModel


class NoteOptionSchema(BaseModel):
    name: str
    type: str


class CreateNoteOptionSchema(BaseModel):
    name: str
    type: str


class UpdateNoteOptionSchema(BaseModel):
    name: str | None = None
    type: str | None = None
