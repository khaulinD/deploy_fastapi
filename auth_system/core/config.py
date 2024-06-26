import os
from pathlib import Path
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent

DB_USER = os.getenv("POSTGRES_USER")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")
DB_NAME = os.getenv("POSTGRES_DB")


class DbSettings(BaseModel):
    # url: str = f'postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    url: str = f'postgresql+asyncpg://postgres:12345678@my-db-1.cb6wec068qfc.eu-west-3.rds.amazonaws.com:5432/postgres'
    # url: str = "cnx = psycopg2.connect(user='test', password='password123!', host='test-datbase.postgres.database.azure.com', port=5432, database='test_db')"
    # url: str = f'postgresql+asyncpg://test:password123!@test-datbase.postgres.database.azure.com:{DB_PORT}/test_db'


    # TODO
    # echo: bool = False
    echo: bool = True


class RedisSettings(BaseModel):
    host: str = os.getenv("REDIS_HOST")
    port: int = os.getenv("REDIS_PORT")


class GoogleKeys(BaseModel):
    client_id: str = os.getenv("GOOGLE_CLIENT_ID")
    client_secret: str = os.getenv("GOOGLE_CLIENT_SECRET")


class MailSettings(BaseModel):
    HOST: str = os.getenv("MAIL_HOST")
    PORT: int = os.getenv("MAIL_PORT")
    USER: str = os.getenv("MAIL_USER")
    PASSWORD: str = os.getenv("MAIL_PASSWORD")


class AuthJWT(BaseModel):
    private_key_path: str = os.getenv("JWT_SECRET_KEY")
    public_key_path: str = os.getenv("JWT_SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_minutes: int = 180


class StripePayments(BaseModel):
    public_key: str = os.getenv("STRIPE_PUBLIC_KEY")
    private_key: str = os.getenv("STRIPE_SECRET_KEY")


class Settings(BaseSettings):
    redis: RedisSettings = RedisSettings()

    openai_api_key: str = os.getenv("OPENAI_API_KEY")

    verification_code: dict = {}

    pagination: int = 10
    db: DbSettings = DbSettings()

    payments: StripePayments = StripePayments()

    mail_data: MailSettings = MailSettings()

    auth_jwt: AuthJWT = AuthJWT()

    google_keys: GoogleKeys = GoogleKeys()

    base_url: str = "http://127.0.0.1:8000"
    frontend_url: str = "http://localhost:5173"

    # db_echo: bool = True
    excluded_jwt_paths: set[tuple[str, str]] = {
        ("/docs", "GET"),
        ("/openapi.json", "GET"),
        ("/company", "POST"),
        ("/user", "POST"),

        ("/verification_email", "POST"),
        ("/forgot_password", "POST"),
        ("/reset_password", "POST"),
        ("/resend_verification", "POST"),

        ("/jwt/login/user", "POST"),
        ("/jwt/login/company", "POST"),
        ("/jwt/login/companyuser", "POST"),
        ("/login/google", "GET"),
        ("/auth/google", "GET"),
        ("/auth/google/account", "POST"),
        # ("/auth/google/account/user", "POST"),
        # ("/auth/google/account/company", "POST"),
        ("/jwt/logout", "GET"),

        # ("/payment/checkout", "GET"),
        ("/payment/webhook", "POST"),

        ("/user_tariff", "POST"),
        ("/tariff_plan", "POST"),
        ("/tariff_plan", "GET"),
        ("/user_tariff", "GET"),
        # ("/notes_generate", "POST"),

    }
    #
    # check_tariff_url: tuple ={
    #     ("/company/doctor/", "POST"),
    #     (f"/company/doctor/{int}/", "GET"),
    #     ("/note/", "GET"),
    # }


settings = Settings()
