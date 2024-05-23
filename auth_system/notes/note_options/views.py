from fastapi import APIRouter, Depends, status

from db.models.notes.note_options import NoteOptionStore
from notes.note_options.schemas import CreateNoteOptionSchema, UpdateNoteOptionSchema

router = APIRouter(
    prefix="/notes",
    tags=["Notes"],
)



@router.get('')
async def get_note_options():
    return await NoteOptionStore.get_note_options()


@router.post('', status_code=status.HTTP_201_CREATED)
async def create_note_options(note_options: CreateNoteOptionSchema):
    note = note_options.model_dump()
    return await NoteOptionStore.create_note_option(data=note)

@router.patch('/{note_options_id}')
async def update_note_options(note_options_id: int, note_options: UpdateNoteOptionSchema):
    return await NoteOptionStore.update_note_option(note_option_id=note_options_id, data=note_options)


@router.delete('/{note_options_id}', status_code=status.HTTP_204_NO_CONTENT)
async def update_note_options(note_options_id: int):
    return await NoteOptionStore.delete_note_option(note_option_id=note_options_id,)