from enum import Enum
from typing import Optional

from fastapi import Depends, HTTPException, APIRouter, Response, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer
import requests
from auth import utils as auth_utils
from auth.jwt_helper import generate_tokens_and_set_cookies
from company.schemas import CreateCompanyByGoogle
from core.config import settings
from db.models.company import CompanyStore
from db.models.doctors.doctor import DoctorStore
from doctor.schemas import CreateDoctorByGoogle
from company.schemas import TokenSchema as CompanyTokenSchema
from doctor.schemas import TokenSchema as DoctorTokenSchema
from user_helper.utils import get_user_by_email
from core.config import settings


# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class ModelName(str, Enum):
    company = "company"
    user = "user"
    anonym = "anonym"


# Replace these with your own values from the Google Developer Console
GOOGLE_CLIENT_ID = settings.google_keys.client_id
GOOGLE_CLIENT_SECRET = settings.google_keys.client_secret
GOOGLE_REDIRECT_URI = f"{settings.base_url}/auth/google"

router = APIRouter(tags=["Google authentication system"])


@router.get("/login/google")
async def login_google(user_type: str):
    global GOOGLE_REDIRECT_URI
    if user_type == "company":

        GOOGLE_REDIRECT_URI = f"{settings.base_url}/auth/google?user_type={user_type}"
        return {
            "url": f"https://accounts.google.com/o/oauth2/auth?response_type=code&client_id={GOOGLE_CLIENT_ID}&redirect_uri={GOOGLE_REDIRECT_URI}&scope=openid%20profile%20email&access_type=offline&prompt=select_account"
        }
    else:
        GOOGLE_REDIRECT_URI = f"{settings.base_url}/auth/google?user_type={user_type}"
        return {
            "url": f"https://accounts.google.com/o/oauth2/auth?response_type=code&client_id={GOOGLE_CLIENT_ID}&redirect_uri={GOOGLE_REDIRECT_URI}&scope=openid%20profile%20email&access_type=offline"
        }


@router.get("/auth/google")
async def auth_google(code: str, user_type: str):
    token_url = "https://accounts.google.com/o/oauth2/token"
    print(code)
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    res = requests.post(token_url, data=data)
    access_token = res.json().get("access_token")

    # user_info = requests.get("https://www.googleapis.com/oauth2/v1/userinfo",
    #                          headers={"Authorization": f"Bearer {access_token}"})
    # print(user_info)
    return RedirectResponse(f"http://localhost:5173/auth/?code={access_token}&user_type={user_type}")
    # Extract user information from Google's response
    # user_data = user_info.json()


@router.post("/auth/google/account", response_model=CompanyTokenSchema | DoctorTokenSchema)
async def operate_user_data(data: dict, response: Response, user_type: ModelName | None = None):
    email = data.get("email")

    if not user_type or user_type == "anonym":
        company, companydoctor = await get_user_by_email(email)

        if company:
            return await generate_tokens_and_set_cookies(company, "company", response)

        else:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User not found")

    elif user_type == "company":
        user = await CompanyStore.get_company_by_email(email=email)
        if not user:
            user = await CompanyStore.create(CreateCompanyByGoogle(email=data["email"],
                                                                   is_verified=data["verified_email"],
                                                                   name=data["name"]).model_dump())

        return await generate_tokens_and_set_cookies(user, user_type, response)

    # elif user_type == "user":
    #     user = await DoctorStore.get_doctor_by_email(email=email)
    #     if not user:
    #         user = await DoctorStore.create(CreateDoctorByGoogle(email=data["email"],
    #                                                              is_verified=data["verified_email"],
    #                                                              name=data["name"],
    #                                                              firstName=data["given_name"],
    #                                                              lastName=data["family_name"]).model_dump())
    #
        # return await generate_tokens_and_set_cookies(user, user_type, response)

    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error while authenticating")
