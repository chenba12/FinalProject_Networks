import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Game(Base):
    __tablename__ = 'Games'

    # name id score platform category price release date
    id = sa.Column('Id', sa.Integer, primary_key=True, autoincrement=True)
    name = sa.Column('name', sa.String, nullable=False, unique=True)
    platform = sa.Column('platform', sa.String, nullable=False)
    category = sa.Column('category', sa.String, nullable=False)
    price = sa.Column('price', sa.Float, nullable=False)
    score = sa.Column('score', sa.Float, nullable=False)
    release_year = sa.Column(sa.Integer, default=1970)

    def __str__(self):
        return f'<Game {self.id} ({self.name} {self.platform} {self.category}) {self.price} {self.score} {self.release_year}>'

    def as_dict(self):
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
    return Game(id=json_object['id'],
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
