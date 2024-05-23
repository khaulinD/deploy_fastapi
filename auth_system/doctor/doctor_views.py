from fastapi import APIRouter, BackgroundTasks, Response

from starlette import status

from auth.jwt_helper import generate_tokens_and_set_cookies
from core.mailer import send_verification_email
from db.models.doctors.doctor import DoctorStore
from doctor.schemas import CreateDoctor, DoctorSchema, DoctorUpdatePartial
from user_helper.utils import generate_token

router = APIRouter(
    prefix="/user",
    tags=["User"],
)

@router.post(
    "",
    response_model=DoctorSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_doctor(
    doctor_income: CreateDoctor,
    background_tasks: BackgroundTasks,
    response: Response,
):
    doctor = doctor_income.model_dump()
    doctor = await DoctorStore.create(data=doctor)
    if doctor:
        # background_tasks.add_task(generate_token, company, "company")
        token = await generate_token(doctor, "doctor")
        background_tasks.add_task(send_verification_email, doctor.email, token)
        await generate_tokens_and_set_cookies(doctor, "user", response)

    return doctor


@router.get("/{user_id}", response_model=DoctorSchema)
async def get_doctor_by_id(
    user_id: int
):
    return await DoctorStore.get_doctor_by_id(doctor_id=user_id)


# @router.get("/{pagination}/{page}/", response_model=list[DoctorSchema])
# async def get_all_doctors(
#         pagination: int, page: int
# ):
#     return await DoctorStore.get_all_doctor(pagination=pagination, page=page)


@router.patch("/{user_id}")
async def update_product_partial(
    user_id: int,
    doctor_update: DoctorUpdatePartial,
):
    return await DoctorStore.update_doctor(
        doctor_id=user_id,
        data=doctor_update)
