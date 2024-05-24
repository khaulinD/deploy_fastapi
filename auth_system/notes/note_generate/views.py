import io
from time import sleep
from fastapi import APIRouter, Depends, status, Response, Request

from db.models.notes.note_history import NoteHistoryStore
from notes.note_generate.create_note import generate_note
from notes.note_generate.utils_v4 import handle_note_data
from notes.note_generate.utils_v2 import gen_note
from notes.note_history.schemas import CreateNoteSchema

router = APIRouter(
    prefix="/notes_generate",
    tags=["Notes generate"],
)


@router.post("", status_code=status.HTTP_200_OK)
async def create_note(data: dict, request: Request):
    payload = request.state.payload
    try:
        prompt = await handle_note_data(data=data)
        res = await generate_note(messages=prompt)
        await NoteHistoryStore.create_note(data=CreateNoteSchema(note_type=data["selectedNoteType"],
                                                                 description=res,
                                                                 note_format=data["selectedNoteFormat"],
                                                                 user_id=payload["sub"]).model_dump())
        return res
    except Exception as e:
        print(str(e))
        return Response(status_code=status.HTTP_400_BAD_REQUEST, content=f"Something went wrong: {str(e)}")


@router.post("/delay", status_code=status.HTTP_200_OK)
async def create_note(data: dict, request: Request):
    payload = request.state.payload
    try:
        sleep(5)
        # await NoteHistoryStore.create_note(data=CreateNoteSchema(note_type=data["selectedNoteType"],
        #                                                          note_format=data["selectedNoteFormat"],
        #                                                          user_id=payload["sub"]).model_dump())
        text = "Subject: Patient Progress Report - Dias Kake, MRN: 4132768\n\nDear Sir/Madam,<br/><br/>I am writing to provide a progress report on my patient, Mr. Dias Kake (Medical Record Number: 4132768), who is currently undergoing Residential Treatment under my care.\n\nMr. Kake has been experiencing Withdrawal symptoms, including Anxiety, Headaches, and Insomnia. These symptoms have been accompanied by a variety of emotional, behavioral, psychiatric, and cognitive conditions such as Grief, Depression, and Avoidance. Additionally, he has shown signs of agitation, convulsions, increased heart rate, nightmares, nervousness, and difficulty sleeping, along with a lack of focus and persistent headaches.\n\nDespite these challenges, I want to note that Mr. Kake has shown resilience in facing his condition. His motivation towards treatment, however, remains unclear at this point. Regular attendance in group therapy sessions or resistance to prompting is not yet determined.\n\nMr. Kake's past treatment history includes an instance of relapse. He does not have a supportive environment at home, which may have contributed to his relapse. He does not live with someone who is currently using or has a history of substance abuse. However, he has previously lived with his father, who frequently raised his voice and was generally harsh towards him. This environment may have contributed to Mr. Kake's current emotional state.\n\nThere have been instances where Mr. Kake has expressed anger or had confrontations with people around him. This could be a consequence of his mental health conditions or a reaction to his current life circumstances.\n\nIn conclusion, Mr. Kake is currently facing a complex set of challenges. His progress in treatment is anticipated to be gradual and will require continuous support and monitoring. \n\nThank you for your continued support in providing the necessary coverage for Mr. Kake's treatment. We will keep you updated on his progress regularly.\n\nSincerely,\n\n[Your Name]\n[Your Title]\n[Your Contact Information]"
        return text
    except Exception as e:
        print(str(e))
        return Response(status_code=status.HTTP_400_BAD_REQUEST, content=f"Something went wrong: {str(e)}")
