from sqlalchemy import select
from sqlalchemy.orm import Mapped
from db.postgres import Base, async_session
from pydantic import BaseModel
from decorators.as_dict import AsDictMixin
from decorators.db_session import db_session


class Token(Base, AsDictMixin):
    access_token: Mapped[str]
    refresh_token: Mapped[str]


class TokenStore:
    @staticmethod
    @db_session
    async def create(session, data: dict):
        token = Token(**data)
        session.add(token)
        await session.commit()
        return token

    @staticmethod
    @db_session
    async def update_access_token(session, refresh_token: str, data):
        token = await session.execute(select(Token).where(Token.refresh_token == refresh_token))
        token = token.scalar_one_or_none()
        if token:
            token.access_token = data
            await session.commit()
            return token
        return None

    @staticmethod
    @db_session
    async def delete_by_refresh_token(session, refresh_token: str):
        token = await session.execute(select(Token).where(Token.refresh_token == refresh_token))
        try:
            token = token.scalar_one_or_none()
            if token:
                await session.delete(token)
                await session.commit()
        except Exception as e:
            await session.commit()
