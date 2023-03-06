import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base

# This file have all the methods related to the Game class
# The class is used as an ORM (Object-relation mapping)
# Before connecting to the database with SQLlite driver the code validate some fields
# and only then it will get/insert/update/delete data
# sqlalchemy is the library used to connect to the database and transfer data
# Table "Games"
# each row in the table is built in the following way
# | id | name(str) | platform(str) | category(str) | price(float) | score(float) | release year(int) |
# The data transfer between the client and server will happen over TCP/RUDP, and we will use json as the data format
Base = declarative_base()


class Game(Base):
    __tablename__ = 'Games'

    id = sa.Column('id', sa.Integer, primary_key=True, autoincrement=True)
    name = sa.Column('name', sa.String, nullable=False, unique=True)
    platform = sa.Column('platform', sa.String, nullable=False)
    category = sa.Column('category', sa.String, nullable=False)
    price = sa.Column('price', sa.Float, nullable=False)
    score = sa.Column('score', sa.Float, nullable=False)
    release_year = sa.Column('release year', sa.Integer, default=1970)

    def __str__(self):
        return f'<{self.id} Title:{self.name} Platform:{self.platform} Category:{self.category} ' \
               f'Price:${self.price} Score:{self.score}/100 Release date:{self.release_year}>'

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'platform': self.platform,
            'category': self.category,
            'price': self.price,
            'score': self.score,
            'release_year': self.release_year,

        }


def json_to_game(json_object):
    return Game(id=int(json_object['id']),
                name=json_object['name'],
                platform=json_object['platform'],
                category=json_object['category'],
                price=json_object['price'],
                score=json_object['score'],
                release_year=(json_object['release_year']))


def validate_year(year):
    return 1970 <= year <= 2030


def validate_category(category):
    category_list = ["JRPG", "Adventure", "Shooter", "Action", "Fighting", "Platformer", "RPG", "Survival", "Sport",
                     "MMO"]
    return category in category_list


def validate_platform(platform):
    platform_list = ["Switch", "PC", "Playstation5", "Playstation4"]
    return platform in platform_list


def validate_score(score):
    return 0 <= score <= 100
