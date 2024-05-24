import datetime
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Query, Request, Response, HTTPException
from starlette import status
from auth import utils as auth_utils
from auth.jwt_helper import generate_tokens_and_set_cookies
from company.schemas import CompanyDoctorsSchemaWithAmount
from core.mailer import send_email_with_credentials
from db.models.doctors.company_doctor import CompanyDoctorStore
from doctor.schemas import CreateDoctorByCompany, CompanyDoctorUpdatePartial, CompanyDoctorSchema, DoctorSchema

router = APIRouter(
    prefix="/company/user",
    tags=["Company user"],
)


@router.post(
    "",
    response_model=CompanyDoctorSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_doctor(
        doctor_income: CreateDoctorByCompany,
        background_tasks: BackgroundTasks,
        response: Response,
):
    doctor = doctor_income.model_dump()

    # Generate the password
    password = auth_utils.generate_strong_password()  # Assuming you have this function
    print("password", password)
    # Hash the password before adding to the doctor data
    doctor["password"] = auth_utils.hash_password(password)
    # Call CompanyDoctorStore.create() function
    doctor = await CompanyDoctorStore.create(data=doctor)
    if doctor:
        username = f'{doctor.firstName} {doctor.lastName}'
        # Add the email sending task with email and password as parameters
        background_tasks.add_task(send_email_with_credentials,
                                  email_to=doctor.email,
                                  username=username,
                                  login=doctor.email,
                                  password=password)
        # await generate_tokens_and_set_cookies(doctor, "user", response)
        # DoctorTokenSchema(access_token=access_token,
        #                   refresh_token=refresh_token,
        #                   doctor_id=user.id,
        #                   role=user_type)
    return doctor



# @router.get("/{pagination}/{page}/", response_model=list[CompanyDoctorSchema])
# async def get_all_doctors(pagination: int, page: int):
#     return await CompanyDoctorStore.get_all_doctor(pagination=pagination, page=page)


# @router.get("/{doctor_id}/", response_model=CompanyDoctorSchema)
# async def get_doctor_by_id(
#     doctor_id: int
# ):
#     return await CompanyDoctorStore.get_doctor_by_id(doctor_id=doctor_id)

@router.patch("/{user_id}", response_model=CompanyDoctorUpdatePartial)
async def update_product_partial(
        user_id: int,
        doctor_update: CompanyDoctorUpdatePartial,
        background_tasks: BackgroundTasks,
):
    if doctor_update.email or doctor_update.oldPassword:
        user = await CompanyDoctorStore.get_doctor_by_id(doctor_id=user_id)

        if doctor_update.oldPassword and doctor_update.newPassword:
            if not auth_utils.validate_password(
                    password=doctor_update.oldPassword,
                    hashed_password=user.password,
            ):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect password")
        new_user = await CompanyDoctorStore.update_doctor(
            doctor_id=user_id,
            data=doctor_update)
        if new_user:
            background_tasks.add_task(send_email_with_credentials,
                                      email_to=user.email,
                                      username=user.name,
                                      login=doctor_update.email if doctor_update.email else user.email,
                                      password=doctor_update.newPassword if doctor_update.newPassword else "********")
        return new_user
    return await CompanyDoctorStore.update_doctor(
        doctor_id=user_id,
        data=doctor_update)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_doctor(
        user_id: int,
):
    await CompanyDoctorStore.delete_doctor(doctor_id=user_id)


@router.get("/{company_id}", response_model=CompanyDoctorsSchemaWithAmount)
async def get_company_doctors_filtered(company_id: int,
                                       page: int = Query(1, ge=1),
                                       search_info: str | None = None):
    return await CompanyDoctorStore.search_company_with_doctors(page=page,
                                                                company_id=company_id,
                                                                search_info=search_info)
