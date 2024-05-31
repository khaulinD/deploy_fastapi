from typing import List
from sqlalchemy import Column, DateTime, Integer, String, func, select, desc, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import relationship
from db.postgres import Base, async_session
from pydantic import BaseModel
from decorators.as_dict import AsDictMixin
from decorators.db_session import db_session
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from db.models.permission import Permission

class MRole(BaseModel):
    id: int
    name: str


class Role(Base, AsDictMixin):
    __tablename__ = 'role'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    permissions = relationship("Permission", back_populates="role")

    def as_dict(self):
        return {
                'id': self.id,
                'name': self.name,
            }


class RoleStore:

    @staticmethod
    @db_session
    async def get_count(session) -> int:
        count_query = select(func.count()).select_from(Role)
        result = await session.execute(count_query)
        return result.scalar_one()

    @staticmethod
    @db_session
    async def create_role(session, name: str):
        role = Role(name=name)
        session.add(role)
        await session.commit()

        return role

    @staticmethod
    @db_session
    async def get_by_name(session, name: str):
        role_result = await session.execute(select(Role).where(Role.name == name))
        role = role_result.scalar()

        return role

    @staticmethod
    @db_session
    async def get_role_by_id(session, role_id: int):
        role_result = await session.execute(select(Role).where(Role.id == role_id))
        role = role_result.scalar()

        return role

    @staticmethod
    @db_session
    async def get_all_roles(session):
        roles = await session.execute(select(Role).order_by(Role.created_at))
        return roles.scalars().all()

    @staticmethod
    @db_session
    async def delete(session, role_id: int):

        await session.execute(
            delete(Role).where(Role.id == role_id)
        )
        await session.commit()

    @staticmethod
    @db_session
    async def update(session, role_id: int, data: dict):
        role = (await session.execute(select(Role).filter_by(id=role_id))).scalar()

        if role is None:
            return None

        for field, value in data.items():
            setattr(role, field, value)

        await session.commit()
        return role