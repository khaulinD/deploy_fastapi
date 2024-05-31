import asyncio
import time

import stripe
import uvicorn
from fastapi import FastAPI, HTTPException, status, Request, Response
from fastapi.responses import JSONResponse

from auth.middleware import token_middleware
from company.views import router as company_router
from auth.jwt_auth_view import router as jwt_auth_router
from core.config import settings
from db.create_tables import recreate_tables, create_defaults
from doctor.company_doctor_view import router as company_doctor_router
from notes.note_generate.views import router as notes_generate_view
from tariff_plan.middleware import check_tariff_middleware
from tariff_plan.view import router as tariff_plan_router
from user_helper.view import router as email_verification_router
from notes.note_options.views import router as note_options_router
from auth.google_auth import router as google_auth_router
from tariff_plan.user_tariff_views import router as tariff_plan_user_router
from payment.views import router as payment_router
from notes.note_history.views import router as note_history_router
from fastapi.middleware.cors import CORSMiddleware
from auth.jwt_helper import get_current_token_payload
import aioredis
app = FastAPI()

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
stripe.api_key = settings.payments.private_key


@app.middleware("http")
async def tariff_middleware(request: Request, call_next):
    print("222222222222")
    response = Response()
    response = await check_tariff_middleware(request, response, call_next)
    return response

#info
@app.middleware("http")
async def jwt_middleware(request: Request, call_next):
    print("111111111111")
    response = Response()
    res = await token_middleware(request, response, call_next)
    return res


# Apply CORS middleware first
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],

)


app.include_router(company_router)
app.include_router(jwt_auth_router)
app.include_router(company_doctor_router)
app.include_router(tariff_plan_router)
app.include_router(email_verification_router)
app.include_router(note_options_router)
app.include_router(google_auth_router)
app.include_router(tariff_plan_user_router)
app.include_router(payment_router)
app.include_router(note_history_router)
app.include_router(notes_generate_view)




@app.on_event("startup")
async def startup():
    # await recreate_tables()
    await create_defaults()
#
# @app.on_event("shutdown")
# async def shutdown():
#     pass
#
# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)
