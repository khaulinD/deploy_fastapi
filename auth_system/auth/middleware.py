import datetime
import logging
import jwt
from fastapi import Request, status, HTTPException, Response
from auth import utils as auth_utils
from auth.cookies.cookies_logic import COOKIE_ACCESS_TOKEN, COOKIE_REFRESH_TOKEN
from auth.utils import deactivate_company_doctor
from core.config import settings
from db.models.doctors.company_doctor import CompanyDoctorStore
from db.models.permission import AccessControl
from core.const import get_action, get_method
from db.models.company import CompanyStore
from db.models.doctors.doctor import DoctorStore
from fastapi.responses import JSONResponse

from doctor.schemas import DoctorSchema

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


async def token_middleware(request: Request, response: Response, call_next):
    print(request.method)
    if request.method == "OPTIONS" or (request.url.path, request.method) in settings.excluded_jwt_paths:
        response = await call_next(request)
        return response

    payload = None
    token: str = request.cookies.get(COOKIE_ACCESS_TOKEN, None)
    if not token:
        return JSONResponse(status_code=401, content={"detail": "You are not authorized"})
    try:
        payload = auth_utils.decode_jwt(token=token)

    except jwt.ExpiredSignatureError:
        try:
            token = await auth_utils.refreshing_token(response, request)
            payload = auth_utils.decode_jwt(token=token)
        except HTTPException as e:
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"detail": "Token expired and refresh failed"})

    except jwt.InvalidTokenError as e:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": f"Invalid token error: {e}"},
        )

    request.state.payload = payload
    url = request.url
    method = request.method
    record_type = await get_action(url.path)
    action = await get_method(method)
    print(action, payload['user_type'], record_type)
    has_permission = await AccessControl.check_for_access(action, payload['user_type'], record_type)
    if not has_permission:
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": "Insufficient permissions"})
    logging.info('access')
    print(payload)
    if payload['user_type'] == "company":
        user = await CompanyStore.get_company_clean_by_id(company_id=payload['sub'])

    elif payload['user_type'] == "user":
        user = await DoctorStore.get_doctor_clean_by_id(payload['sub'])
    elif payload['user_type'] == "companyuser":
        response = await call_next(request)
        return response
    else:
        user = None

    if user is None:
        # User not found, handle accordingly
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"detail": "User not found"})

    if not user.is_verified:
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": "User is not verified"})

    response = await call_next(request)
    return response
