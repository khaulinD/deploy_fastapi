from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import DateTime, func, String, select, desc, delete, Integer, ForeignKey
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import mapped_column, selectinload, relationship
from stdnum import ma

from db.postgres import Base
from decorators.as_dict import AsDictMixin
from decorators.db_session import db_session
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from db.models.doctors.company_doctor import CompanyDoctor


class NoteHistory(Base, AsDictMixin):

    title = mapped_column(String, default="Note title")
    description = mapped_column(String, nullable=True)
    note_type = mapped_column(String)
    note_format = mapped_column(String)

    user_id = mapped_column(Integer, ForeignKey('companydoctors.id'))
    user = relationship("CompanyDoctor", back_populates="user_notes")

    created_at = mapped_column(DateTime, default=func.now())
    updated_at = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class NoteHistoryStore:

    @staticmethod
    @db_session
    async def create_note(session, data: dict):
        note = NoteHistory(**data)
        session.add(note)
        await session.commit()
        return note


    @staticmethod
    @db_session
    async def get_all_history(session, user_id: int):
        from db.models.doctors.company_doctor import CompanyDoctor
        thirty_days_ago = datetime.now() - timedelta(days=30)
        await session.execute(delete(NoteHistory).where(NoteHistory.created_at < thirty_days_ago))
        await session.commit()

        # Retrieve all history
        result = await session.execute(select(CompanyDoctor).
                                       options(selectinload(CompanyDoctor.user_notes)).
                                       where(CompanyDoctor.id == user_id)
                                       )

        if not result:
            raise HTTPException(status_code=404, detail="No history found")

        doctor = result.scalar()
        return doctor


    @staticmethod
    @db_session
    async def update_note(session, note_id: int, data):
        try:
            note = await session.get(NoteHistory, note_id)
            if note is None:
                raise HTTPException(status_code=404, detail="Note not found")

            for name, value in data.model_dump(exclude_unset=True).items():
                setattr(note, name, value)

            await session.commit()
            return note
        except IntegrityError as e:
                raise HTTPException(status_code=400, detail=str(e))

    @staticmethod
    @db_session
    async def delete_note(session, note_id: int):
        note = await session.get(NoteHistory, note_id)
        if note is None:
            raise HTTPException(status_code=404, detail="Note not found")

        await session.delete(note)
        await session.commit()
