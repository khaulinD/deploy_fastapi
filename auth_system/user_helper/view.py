from http import HTTPStatus

from fastapi import APIRouter, Request, HTTPException, Response, BackgroundTasks, status
from fastapi.responses import HTMLResponse, JSONResponse
from auth import utils as auth_utils
from auth.jwt_helper import validate_auth_user, generate_tokens_and_set_cookies
from company.schemas import CompanySchema, CompanyUpdatePartial
from core.config import settings
from db.models.company import CompanyStore
from db.models.doctors.company_doctor import CompanyDoctorStore
from db.models.doctors.doctor import DoctorStore
from doctor.schemas import DoctorSchema, CompanyDoctorSchema, DoctorUpdatePartial
from user_helper.utils import generate_token, get_user_by_email
from core.mailer import forgot_password as send_forgot_password
import aioredis


rb = aioredis.Redis(host=settings.redis.host, port=settings.redis.port, db=1)

router = APIRouter(
    tags=["User helper"],
)


@router.post("/verification_email")
async def verify_email(token: int, response: Response):
    company_id: int = await rb.get(f"customer_verify_token_{token}")
    if company_id is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Invalid token")
    user = await CompanyStore.update_company(company_id=int(company_id), data=CompanyUpdatePartial(
        is_verified=True))  # Update the verified status in the database
    await rb.delete(f"customer_verify_token_{token}")
    res = await generate_tokens_and_set_cookies(user, "company", response)
    return res




@router.post("/forgot_password")
async def forgot_password(email: str, background_task: BackgroundTasks):
    # Check if the email exists in any of the tables
    password: str = auth_utils.generate_strong_password()
    company, company_doctor = await get_user_by_email(email)

    if company:
        # Change password for company user
        await CompanyStore.update_company(company.id, CompanyUpdatePartial(password=password))
        username = company.name
        background_task.add_task(send_forgot_password, username=username,  password=password, email=company.email)
        # await send_forgot_password(email_to=company.email, password=password)
        return {"message": "Password updated for company."}
    elif company_doctor:
        company_doctor = company_doctor
        # Change password for company doctor user
        await CompanyDoctorStore.update_doctor(company_doctor.id, DoctorUpdatePartial(password=password))
        username = f"{company_doctor.firstName} {company_doctor.lastName}"
        background_task.add_task(send_forgot_password, username=username, password=password, email=company_doctor.email)
        # await send_forgot_password(email_to=doctor.email, password=password)
        return {"message": "Password updated for user."}
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email not found.")


@router.post("/reset_password")
async def reset_password(email, password: str, new_password: str, background_task: BackgroundTasks):

    company, company_doctor = await get_user_by_email(email)

    if company:
        user, user_type = await validate_auth_user(email, password, "company")
        # Change password for company user
        await CompanyStore.update_company(user.id, CompanyUpdatePartial(password=new_password))
        return {"message": "Password updated for doctor user."}
    elif company_doctor:
        user, user_type = await validate_auth_user(email, password, "companydoctor")
        # Change password for company doctor user
        await CompanyDoctorStore.update_doctor(user.id, DoctorUpdatePartial(password=new_password))
        return {"message": "Password updated for doctor user."}
    else:
        raise HTTPException(status_code=404, detail="Email not found.")


@router.get("/checkout_auth")
async def validate_user(response: Response, request: Request):
    payload = request.state.payload
    user_type = payload["user_type"]
    if user_type == "company":
        user = await CompanyStore.get_company_clean_by_id(payload["sub"])
    else:
        user = await CompanyDoctorStore.get_doctor_by_id(payload["sub"])

    return await generate_tokens_and_set_cookies(user, user_type, response)


@router.post("/resend_verification")
async def resend_verification(company_id: int, background_task: BackgroundTasks):
    company = CompanyStore.get_company_clean_by_id(company_id=company_id)
    if company:
        await auth_utils.send_verification_code(user=company, background_tasks=background_task)
        return company
    return Response(status_code=status.HTTP_200_OK)
