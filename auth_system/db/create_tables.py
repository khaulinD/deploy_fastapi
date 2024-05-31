import asyncio
from sqlalchemy import text
from core.config import settings
from db.postgres import Base, engine

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy_utils import database_exists, create_database
from core.const import PERMISSION
from db.models.tariff_plan_info import TariffPlanStore, TariffPlan
from db.models.user_tariff import UserTariffPlan
from db.models.token import Token, TokenStore
from db.models.company import Company, CompanyStore
# from db.models.doctors.doctor import DoctorStore, Doctor
from db.models.doctors.company_doctor import CompanyDoctorStore, CompanyDoctor
from db.models.notes.note_history import NoteHistory, NoteHistoryStore
from db.models.role import RoleStore, Role
from db.models.permission import PermissionStore, Permission
from db.models.notes.note_options import NoteOptionStore, NoteOption, data
from notes.note_options.schemas import NoteOptionSchema

from tariff_plan.schemas import TariffPlanSchema



async def remove_all_tables():
    async with engine.begin() as connection:
        remove_all = text('''
        DO $$ DECLARE
            r RECORD;
        BEGIN
            -- if the schema you operate on is not "current", you will want to
            -- replace current_schema() in query with 'schematodeletetablesfrom'
            -- *and* update the generate 'DROP...' accordingly.
            FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = current_schema()) LOOP
                EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
            END LOOP;
        END $$;
        ''')
        await connection.execute(remove_all)


async def create_tables():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def create_db_if_not_exists():
    try:
        # Try to connect to the database
        async with engine.begin() as conn:
            pass
    except Exception as e:
        # If connection fails, create a new database
        db_url_parts = settings.db.url.split('/')[:-1]
        db_url_root = '/'.join(db_url_parts)
        engine_root = create_async_engine(db_url_root, echo=True)

        async with engine_root.begin() as conn:
            result = await conn.run_sync(database_exists, engine.url)
            if not result:
                await conn.run_sync(create_database, engine.url)
                
        await engine_root.dispose()




async def create_defaults():
    # Check if any roles exist
    if not await RoleStore.get_count():
        default_roles = {}
        for role in PERMISSION.keys():
            default_roles[role] = await RoleStore.create_role(name=role)

    # Check if any tariff plans exist
    if not await TariffPlanStore.get_count():
        await TariffPlanStore.create(TariffPlanSchema(title="Basic",
                                                      description="to 5 users available Cancel anytime",
                                                      price=497,
                                                      doctor_amount=5,
                                                      duration='1').model_dump())
        await TariffPlanStore.create(TariffPlanSchema(title="Standart",
                                                      description="to 10 users available Cancel anytime",
                                                      price=873,
                                                      doctor_amount=10,
                                                      duration='1').model_dump())
        await TariffPlanStore.create(TariffPlanSchema(title="Enterprise",
                                                      description="unlimited users to add Cancel anytime",
                                                      price=5000,
                                                      duration='1').model_dump())
        await TariffPlanStore.create(TariffPlanSchema(title="Basic",
                                                         description="to 5 users available Cancel anytime",
                                                         price=497,
                                                         doctor_amount=5,
                                                         duration='12').model_dump())
        await TariffPlanStore.create(TariffPlanSchema(title="Standart",
                                                      description="to 10 users available Cancel anytime",
                                                      price=873,
                                                      doctor_amount=10,
                                                      duration='12').model_dump())
        await TariffPlanStore.create(TariffPlanSchema(title="Enterprise",
                                                      description="unlimited users to add Cancel anytime",
                                                      price=5000,
                                                      duration='12').model_dump())

    # Check if any note options exist
    if not await NoteOptionStore.get_count():
        for role in data.keys():
            await NoteOptionStore.create_note_option(NoteOptionSchema(name=role, type=data[role]).model_dump())



async def recreate_tables():
    await create_db_if_not_exists()
    await remove_all_tables()
    await create_tables()
    await create_defaults()

print("RECREATING TABLES")
# asyncio.run(recreate_tables())
# recreate_tables()
