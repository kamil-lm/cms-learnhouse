from enum import Enum
from typing import Optional
from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class RoleTypeEnum(str, Enum):
    ORGANIZATION = "ORGANIZATION"
    ORGANIZATION_API_TOKEN = "ORGANIZATION_API_TOKEN"
    GLOBAL = "GLOBAL"


class RoleBase(SQLModel):
    name: str 
    description: Optional[str] = ""
    rights: dict = Field(default={}, sa_column=Column(JSON))


class Role(RoleBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    org_id: int = Field(default=None, foreign_key="organization.id")
    role_type: RoleTypeEnum = RoleTypeEnum.ORGANIZATION
    role_uuid: str = ""
    creation_date: str = ""
    update_date: str = ""


class RoleCreate(RoleBase):
    org_id: int = Field(default=None, foreign_key="organization.id")


class RoleUpdate(SQLModel):
    role_id: int = Field(default=None, foreign_key="role.id")
    name: Optional[str] = ""
    description: Optional[str] = ""
    rights: Optional[dict] = Field(default={}, sa_column=Column(JSON))
