from fastapi import APIRouter, Depends, status, Response, Request

from db.models.notes.note_history import NoteHistoryStore
from notes.note_history.schemas import UpdateNote, NoteHistorySchema, CreateNoteSchema

router = APIRouter(
    prefix="/notes_history",
    tags=["Notes history"],
)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=CreateNoteSchema)
async def create_note(note: CreateNoteSchema):
    return await NoteHistoryStore.create_note(data=note.model_dump())


@router.get('/{user_id}')
async def get_all_history(user_id: int):
    return await NoteHistoryStore.get_all_history(user_id=user_id)


@router.patch('/{note_id}')
async def update_note(note_id: int, updated_note_data: UpdateNote):
    return await NoteHistoryStore.update_note(note_id=note_id, data=updated_note_data)


@router.delete('/{note_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(note_id: int):
    return await NoteHistoryStore.delete_note(note_id=note_id)
