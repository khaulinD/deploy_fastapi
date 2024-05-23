from collections import defaultdict
from fastapi import status, HTTPException
from sqlalchemy.exc import IntegrityError
from auth import utils as auth_utils
from db.postgres import Base
from decorators.as_dict import AsDictMixin
from sqlalchemy import select
from sqlalchemy.orm import Mapped, mapped_column

from decorators.db_session import db_session
from notes.note_options.schemas import NoteOptionSchema, UpdateNoteOptionSchema

data = {"Detox": "level_of_care",
        "Residential Treatment": "level_of_care",
        "Day Treatment": "level_of_care",
        "Intensive Outpatient (IOP)": "level_of_care",
        "Ambulatory Detox": "level_of_care",
        "Narrative": "note_format",
        "Dap Note": "note_format",
        "SOAP Note": "note_format",
        "Treatment Planning Note": "note_format",
        "Individual Note": "note_type",
        "Group Note": "note_type",
        "Ancillary Progress Note": "note_type",
        "UR Note": "note_type",
        "Nursing Note": "note_type",
        "Physician Note": "note_type",
        "Magelan": "insurance_company",
        "Cigna and Evernorth": "insurance_company",
        "Optum and United Healthcare": "insurance_company",
        "BCBS Blue Cross Blue Shield":"insurance_company",
        "Aetna": "insurance_company",
        "Others": "insurance_company",
        }


class NoteOption(Base, AsDictMixin):
    name: Mapped[str]
    type: Mapped[str]


class NoteOptionStore:

    @staticmethod
    @db_session
    async def create_note_option(session, data: NoteOptionSchema):

        note_option = NoteOption(**data)
        session.add(note_option)
        await session.commit()

        return note_option

    @staticmethod
    @db_session
    async def get_note_options(session):
        query = await session.execute(select(NoteOption))
        results = query.all()

        note_dict = defaultdict(list)

        for item in results:
            note_option_object = item[0]

            note = note_option_object.type

            key = note_option_object.name

            if note in note_dict:
                note_dict[note].append(key)
            else:
                note_dict[note] = [key]

        return note_dict

    @staticmethod
    @db_session
    async def update_note_option(session,
                             note_option_id: int,
                             data: UpdateNoteOptionSchema):

        note_option = await session.get(NoteOption, note_option_id)

        if note_option is None:
            raise HTTPException(status_code=404, detail="Note option not found")

        for name, value in data.model_dump(exclude_unset=True).items():
            if name == "password":
                value = auth_utils.hash_password(value)
            setattr(note_option, name, value)

        await session.commit()
        return note_option

    @staticmethod
    @db_session
    async def delete_note_option(session, note_option_id: int):
        try:
            query = select(NoteOption).filter(NoteOption.id == note_option_id)
            result = await session.execute(query)
            note_option = result.scalar()
            if note_option:
                await session.delete(note_option)
                await session.commit()
            else:
                raise HTTPException(status_code=404, detail="Note option not found")
        except IntegrityError as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="error while deleting note option")