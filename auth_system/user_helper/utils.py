from auth import utils as auth_utils


async def generate_token(user, user_type: str) -> str:
    # from db.models.company import CompanyStore
    # from db.models.doctors.company_doctor import CompanyDoctorStore
    # doctor = await CompanyDoctorStore.get_doctor_by_email(user.email)
    # company = await CompanyStore.get_company_by_email(user.email)

    data = {"email": user.email,
            "user_type": user_type,
            "id": user.id}

    return auth_utils.encode_jwt(data, expire_minutes=24 * 60 * 60)


async def get_user_by_email(email: str):
    from db.models.company import CompanyStore

    # Check if the email exists in any of the tables
    company = await CompanyStore.get_company_by_email(email=email)
    company_doctor = None

    # If email not found in company table, check doctor and companydoctor tables
    if not company:
        from db.models.doctors.company_doctor import CompanyDoctorStore
        company_doctor = await CompanyDoctorStore.get_doctor_by_email(email=email)
    return company, company_doctor


async def send_data_old_email(email: str, user_type: str):
    pass