from functools import wraps

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Enum, Integer, String, create_engine, func, ForeignKey, select, delete, update
from decorators.db_session import db_session
from db.postgres import Base
from decorators.as_dict import AsDictMixin
from datetime import datetime
from db.models.role import Role
from core.const import PERMISSION
from sqlalchemy.orm import relationship
from starlette import status
from starlette.requests import Request
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class MPermission(BaseModel):
    record_type: str
    type: int
    condition: int
    filter: str
    role_id: int


class Permission(Base, AsDictMixin):
    __tablename__ = 'permission'
    id = Column(Integer, primary_key=True, autoincrement=True)
    record_type = Column(String)
    type = Column(Integer, nullable=False)
    condition = Column(Integer, nullable=False)
    role_id = Column(Integer, ForeignKey('role.id', ondelete='CASCADE'))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    role = relationship("Role", back_populates="permissions")


    def as_dict(self):
        return {
            'record_type': self.record_type,
            'type': self.type,
            'condition': self.condition,
            'filter': self.filter,
            'role_id': self.role_id,
        }


class PermissionStore:
    @staticmethod
    @db_session
    async def create(session, data: MPermission):
        permission = Permission(**data.model_dump())
        session.add(permission)
        await session.commit()
        return permission

    @staticmethod
    @db_session
    async def get_by_id(session, permission_id: int):
        permission = await session.execute(
            select(Permission).filter_by(id=permission_id)
        )
        return permission.scalar_one_or_none()

    @staticmethod
    @db_session
    async def get_all(session):
        permissions = await session.execute(
            select(Permission).order_by(Permission.created_at)
        )
        return permissions.scalars().all()

    @staticmethod
    @db_session
    async def update(session, permission_id: int, data: dict):
        permission = (await session.execute(select(Permission).filter_by(id=permission_id))).scalar()

        if permission is None:
            return None

        for field, value in data.items():
            setattr(permission, field, value)

        await session.commit()
        return permission

    @staticmethod
    @db_session
    async def delete_by_id(session, permission_id: int):
        permission = await PermissionStore.get_by_id(permission_id)

        if permission is None:
            return None
        await session.delete(permission)
        await session.commit()
        return True

    @staticmethod
    @db_session
    async def get_by_role(session, role_id: int):
        permissions = await session.execute(
            select(Permission).filter_by(role_id=role_id)
        )
        return permissions.scalars().all()

    @staticmethod
    @db_session
    async def delete_by_role(session, role_id: int):
        await session.execute(
            delete(Permission).where(Permission.role_id == role_id)
        )
        await session.commit()
        return True

class AccessControl:

    @staticmethod
    async def check_role_in_enum(role_name: str):
        if role_name in [e for e in PERMISSION.keys()]:
            return True
        return False

    @staticmethod
    async def get_permission_by_role(role_name: str):
        if await AccessControl.check_role_in_enum(role_name=role_name):
            return PERMISSION.get(role_name, None)
        else:
            return False

    @staticmethod
    async def check_for_access(action: str, role_name: str, record_type: str):
        try:
            permissions = await AccessControl.get_permission_by_role(role_name=role_name)
            permission = [perm for perm in permissions if perm['record_type'] == record_type
                          and perm['condition'] == True]
            for perm in permission:
                if action == perm['type']:
                    return True
            return False
        except Exception as err:
            return False
