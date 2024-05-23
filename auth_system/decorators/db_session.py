
from functools import wraps
from db.postgres import async_session
from sqlalchemy.exc import SQLAlchemyError


def db_session(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # If 'session' is already passed as an argument, use it.
        if 'session' in kwargs:
            modified_kwargs = kwargs.copy()
            del modified_kwargs['session']
            return await func(kwargs['session'], *args, **modified_kwargs)

        # Otherwise, create a new session and use it.
        async with async_session() as session:
            try:
                return await func(session, *args, **kwargs)

            except SQLAlchemyError as e:
                await session.rollback()
                raise e

    return wrapper
