from datetime import timedelta
from enum import Enum

from starlette.responses import JSONResponse

from auth.jwt_helper import validate_auth_user, get_current_token_payload, generate_tokens_and_set_cookies
from auth.schemas import LoginCredentials
from core.config import settings
from db.models.company import CompanyStore
from db.models.doctors.doctor import DoctorStore
from db.models.token import TokenStore

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Response,
    Request,
    Form, BackgroundTasks
)

from auth.cookies.cookies_logic import COOKIE_ACCESS_TOKEN, COOKIE_REFRESH_TOKEN
from auth import utils as auth_utils
from company.schemas import CompanySchema
from company.schemas import TokenSchema as CompanyTokenSchema
from doctor.schemas import TokenSchema as DoctorTokenSchema

from doctor.schemas import DoctorSchema

router = APIRouter(prefix="/jwt", tags=["JWT"])


class ModelName(str, Enum):
    company = "company"
    user = "user"
    companyuser = "companyuser"

@router.post("/login/{user_type}", response_model=CompanyTokenSchema | DoctorTokenSchema)
async def auth_user_issue_jwt(
    user_type: ModelName,
    response: Response,
    credentials: LoginCredentials,
    background_tasks: BackgroundTasks,
):
    email = credentials.email
    password = credentials.password
    user, user_type = await validate_auth_user(email, password, user_type, background_tasks)
    if not user:
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": "Verificate your email"})

    return await generate_tokens_and_set_cookies(user, user_type, response)




@router.get("/users/me")
async def auth_user_check_self_info(
        payload: dict = Depends(get_current_token_payload),

):
    iat = payload.get("iat")
    return {
        "user_type": payload.get("user_type"),
        "email": payload.get("email"),
        "logged_in_at": iat,
    }



@router.get("/logout")
async def demo_auth_logout_cookie(
        response: Response,
        request: Request
) -> dict:
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="not authenticated",
        )
    response.delete_cookie(COOKIE_ACCESS_TOKEN)
    response.delete_cookie(COOKIE_REFRESH_TOKEN)
    await TokenStore.delete_by_refresh_token(refresh_token=token)
    return {
        "message": f"Bye!",
    }




