import datetime

from fastapi.responses import JSONResponse

from auth.cookies.cookies_logic import COOKIE_ACCESS_TOKEN, COOKIE_REFRESH_TOKEN
from fastapi.responses import RedirectResponse
from company.schemas import CompanySchema
from core.config import settings
from db.models.company import CompanyStore
from jwt.exceptions import InvalidTokenError
from company.schemas import TokenSchema as CompanyTokenSchema
from doctor.schemas import TokenSchema as DoctorTokenSchema
from fastapi import (
    HTTPException,
    status,
    Request,
    Response
)
from auth import utils as auth_utils
from db.models.doctors.company_doctor import CompanyDoctorStore
from db.models.doctors.doctor import DoctorStore
from db.models.token import TokenStore

from doctor.schemas import DoctorSchema, CompanyDoctorSchema, DoctorUpdatePartial

async def validate_auth_user(
        email: str,
        password: str,
        user_type: str,
        background_tasks
):
    unauthed_exc = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid email or password",
    )
    if user_type == "company":
        user: CompanySchema = await CompanyStore.get_company_by_email(email=email)
    elif user_type == "companyuser":
        user: CompanyDoctorSchema = await CompanyDoctorStore.get_doctor_by_email(email=email)
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="unknown user type",
        )

    if not user:
        raise unauthed_exc

    if not auth_utils.validate_password(
        password=password,
        hashed_password=user.password,
    ):

        raise unauthed_exc

    if user_type != "companyuser" and not user.is_verified:
        await auth_utils.send_verification_code(user=user, background_tasks=background_tasks)
        return None, None
        # raise HTTPException(
        #     status_code=status.HTTP_403_FORBIDDEN,
        #     detail="Verificate your email",
        # )
    if user_type == "companyuser":
        await CompanyDoctorStore.update_online_doctor(doctor_id=user.id)

    return user, user_type


async def get_current_token_payload(
    request: Request,
    response: Response
) -> dict:
    try:
        token: str = request.cookies.get(COOKIE_ACCESS_TOKEN, None)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"You are not authorized",
            )
        payload: dict = auth_utils.decode_jwt(
            token=token,
        )

    except InvalidTokenError as e:
        if str(e) == "Signature has expired":
            return await auth_utils.refreshing_token(response, request)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"invalid token error: {e}",
        )

    return payload


async def refresh_jwt_token(token: str):
    try:
        payload: dict = auth_utils.decode_jwt(token)
        user_type: str = payload["user_type"]
        if user_type == "company":
            user = await CompanyStore.get_company_clean_by_id(payload["sub"])
        elif user_type == "companyuser":
            user = await CompanyDoctorStore.get_doctor_by_id(payload["sub"])
            await CompanyDoctorStore.update_online_doctor(doctor_id=user.id)
            # await CompanyDoctorStore.update_online_doctor(doctor_id=user.id)
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="unknown user type",
            )
        access_payload = {
            "sub": user.id,
            "email": user.email,
            "user_type": user_type
        }
        access_token: str | bytes = auth_utils.encode_jwt(access_payload)

        await TokenStore.update_access_token(refresh_token=token, data=access_token)
        return access_token
    except InvalidTokenError as e:
        await TokenStore.delete_by_refresh_token(refresh_token=token)
        return None
        # raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="error while refreshing token")


async def generate_tokens_and_set_cookies(user, user_type, response):
    access_payload = {
        "sub": user.id,
        "email": user.email,
        "user_type": user_type
    }
    access_token = auth_utils.encode_jwt(access_payload)

    refresh_payload = {
        "sub": user.id,
        "type": "refresh",
        "user_type": user_type
    }
    refresh_token = auth_utils.encode_jwt(refresh_payload,
                                          expire_timedelta=datetime.timedelta(
                                              minutes=settings.auth_jwt.refresh_token_expire_minutes))

    token = {"access_token": access_token, "refresh_token": refresh_token}

    await TokenStore.create(data=token)
    response.set_cookie("access_token", access_token, samesite='none', secure=True, httponly=True)
    response.set_cookie("refresh_token", refresh_token, samesite='none', httponly=True, secure=True)

    if user_type == "company":
        account = await CompanyStore.get_company_clean_by_id(company_id=user.id)
        token_schema = CompanyTokenSchema(access_token=access_token,
                                          refresh_token=refresh_token,
                                          company_id=user.id,
                                          role=user_type,
                                          user_info=account.__dict__)
    else:
        account = await CompanyDoctorStore.get_doctor_by_id(doctor_id=user.id)
        token_schema = DoctorTokenSchema(access_token=access_token,
                                         refresh_token=refresh_token,
                                         doctor_id=user.id,
                                         role=user_type,
                                         user_info=account.__dict__)

    return token_schema


