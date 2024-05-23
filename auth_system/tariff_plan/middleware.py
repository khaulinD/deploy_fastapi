import datetime
import logging
import jwt
from fastapi import Request, Response, status, HTTPException
from auth import utils as auth_utils
from auth.cookies.cookies_logic import COOKIE_ACCESS_TOKEN, COOKIE_REFRESH_TOKEN
from auth.utils import deactivate_company_doctor
from core.config import settings
from db.models.doctors.company_doctor import CompanyDoctorStore

from db.models.permission import AccessControl
from core.const import get_action, get_method, get_tariff_url
from db.models.company import CompanyStore
from db.models.doctors.doctor import DoctorStore
from fastapi.responses import JSONResponse

from doctor.schemas import DoctorSchema, CompanyDoctorSchema, DoctorUpdatePartial


async def check_tariff_middleware(request: Request, response: Response, call_next):
    if await get_tariff_url(request.url.path, request.method):
        payload = request.state.payload
        if payload['user_type'] == "company":
            user = await CompanyStore.get_company_with_doctors(company_id=payload['sub'])
            if user:
                if user.tariff_plan.expired_at < datetime.datetime.now():
                    await deactivate_company_doctor(user.doctors, False)
                    return Response(status_code=status.HTTP_403_FORBIDDEN, content="Tariff expired")

            else:
                return Response(status_code=status.HTTP_403_FORBIDDEN,
                                    content="You dont have any tariff")

            if "company/user" in request.url.path and request.method == "GET":
                if int(request.url.path.split("/")[-2]) != payload["sub"]:
                    return Response(status_code=status.HTTP_403_FORBIDDEN,
                                        content="You dont have access to this company")
        elif payload['user_type'] == "companyuser":
            doctor = await CompanyDoctorStore.get_doctor_by_id(doctor_id=payload['sub'])
            if doctor.active == True or doctor:
                company = await CompanyStore.get_company_with_tariff_plan(company_id=doctor.company_id)
                if not company.user_tariff or company.user_tariff.expired_at < datetime.datetime.now():
                    await CompanyDoctorStore.update_doctor(doctor_id=doctor.id, data=DoctorUpdatePartial(active=False))
                    return Response(status_code=status.HTTP_403_FORBIDDEN, content="Tariff expired")

        response = await call_next(request)
        return response
    response = await call_next(request)
    return response
