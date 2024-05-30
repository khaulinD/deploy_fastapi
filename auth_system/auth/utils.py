import random
import string
from datetime import datetime, timedelta

import aioredis
import bcrypt
import jwt
from auth.cookies.cookies_logic import COOKIE_REFRESH_TOKEN, COOKIE_ACCESS_TOKEN
from auth.jwt_helper import refresh_jwt_token
from core.config import settings
from fastapi import Response, Request, HTTPException, status
from fastapi.responses import JSONResponse

from core.mailer import send_verification_email
from db.models.doctors.company_doctor import CompanyDoctorStore
from doctor.schemas import DoctorUpdatePartial

# rb = aioredis.Redis(host="redistest1fastapidoctor.redis.cache.windows.net", port=6379, password="vH7yX3RWEPMUiOaxsAmZLyvFinNjCp5hwAzCaDxe9kE=", db=1)
rb = aioredis.Redis(host=f"{settings.redis.host}", port=settings.redis.port, db=0)
def encode_jwt(
    payload: dict,
    private_key: str = settings.auth_jwt.private_key_path,
    algorithm: str = settings.auth_jwt.algorithm,
    expire_minutes: int = settings.auth_jwt.access_token_expire_minutes,
    expire_timedelta: timedelta | None = None,
) -> str:
    to_encode = payload.copy()
    now = datetime.utcnow()
    if expire_timedelta:
        expire = now + expire_timedelta
    else:
        expire = now + timedelta(minutes=expire_minutes)
    to_encode.update(
        exp=expire,
        iat=now,
    )
    encoded = jwt.encode(
        to_encode,
        private_key,
        algorithm=algorithm,
    )
    return encoded


def decode_jwt(
    token: str | bytes,
    public_key: str = settings.auth_jwt.public_key_path,
    algorithm: str = settings.auth_jwt.algorithm,
) -> dict:
    decoded = jwt.decode(
        token,
        public_key,
        algorithms=[algorithm],
    )
    return decoded


def hash_password(
    password: str,
) -> bytes:
    salt = bcrypt.gensalt()
    pwd_bytes: bytes = password.encode()
    return bcrypt.hashpw(pwd_bytes, salt)


def validate_password(
    password: str,
    hashed_password: bytes,
) -> bool:
    return bcrypt.checkpw(
        password=password.encode(),
        hashed_password=hashed_password,
    )


async def refreshing_token(response: Response, request: Request):

    refresh_token = request.cookies.get(COOKIE_REFRESH_TOKEN, None)
    if refresh_token:
        access_token = await refresh_jwt_token(token=refresh_token)
        if access_token:
            response.set_cookie(COOKIE_ACCESS_TOKEN, access_token, httponly=True, samesite='none', secure=True)
            # Decode and return the new access token's payload
            # return decode_jwt(access_token)
            return access_token
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token is expired')


def generate_strong_password(length: int = 12) -> str:
    """
    Generate a strong password with the specified length.
    Parameters:
        length (int): Length of the password (default is 12).
    Returns:
        str: The generated strong password.
    """
    # Define character sets for password generation
    uppercase_letters = string.ascii_uppercase
    lowercase_letters = string.ascii_lowercase
    digits = string.digits
    special_characters = '!@#$%&_?'

    # Combine character sets
    all_characters = uppercase_letters + lowercase_letters + digits + special_characters

    # Ensure each character set is included in the password
    password = [
        random.choice(uppercase_letters),
        random.choice(lowercase_letters),
        random.choice(digits),
        random.choice(special_characters)
    ]

    # Fill the rest of the password with random characters
    password.extend(random.choices(all_characters, k=length - 4))

    # Shuffle the characters to randomize the password
    random.shuffle(password)

    # Convert the password list to a string
    return ''.join(password)


async def deactivate_company_doctor(list_of_doctors: list, status: bool):
    for doctor in list_of_doctors:
        await CompanyDoctorStore.update_doctor(doctor_id=doctor.id, data=DoctorUpdatePartial(active=status))


async def send_verification_code(user, background_tasks):
    print(rb)
    pong = await rb.ping()
    print(pong)
    # pong = await rb.ping()
    #
    # print(f"Redis PING response: {pong}")
    token = random.randint(100000000, 999999999)
    set_success = await rb.set(f"customer_verify_token_{token}", user.id, nx=True, ex=30 * 60)
    while not set_success:
        token = random.randint(100000000, 999999999)
        token_key = f"customer_verify_token_{token}"
        set_success = await rb.set(token_key, user.id, nx=True, ex=30 * 60)
    # settings.verification_code[token] = company.id
    await rb.set(f"customer_verify_token_{token}", user.id, nx=True, ex=30 * 60)
    background_tasks.add_task(send_verification_email, company=user, token=token)
