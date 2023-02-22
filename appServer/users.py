import json

import sqlalchemy as sa
import datetime
from sqlalchemy.ext.declarative import declarative_base

from enum import Enum


class Roles(Enum):
    ADMIN = 1
    CLIENT = 2


Base = declarative_base()


class User(Base):
    __tablename__ = 'Users'

    id = sa.Column('Id', sa.Integer, primary_key=True, autoincrement=True)
    email = sa.Column('Email', sa.String, nullable=False, unique=True)
    last_name = sa.Column('LastName', sa.String, nullable=False)
    first_name = sa.Column('FirstName', sa.String, nullable=False)
    role = sa.Column('Role', sa.Enum(Roles), nullable=False)
    created_date = sa.Column(sa.DateTime, default=datetime.datetime.now)

    def __str__(self):
        return f'<User {self.id} ({self.email} {self.first_name} {self.last_name}) {self.role} {self.created_date}>'

    def as_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'last_name': self.last_name,
            'first_name': self.first_name,
            'role': self.role.name,
            'created_date': str(self.created_date),
        }


def json_to_user(json_object):
    role_num = 0
    if json_object['role'] == 'CLIENT':
        role_num = 2
    else:
        role_num = 1
    return User(id=json_object['id'],
                email=json_object['email'],
                last_name=json_object['last_name'],
                first_name=json_object['first_name'],
                role=Roles(Roles(role_num)),
                created_date=(json_object['created_date']))
