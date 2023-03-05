def json_to_message(json_object):
    return Message(func=json_object['func'],
                   body=json_object['body'])


class Message:
    func = ""
    body = ""

    def __init__(self, func, body):
        self.func = func
        self.body = body

    def as_dict(self):
        return {
            'func': self.func,
            'body': self.body
        }


def get_all_message():
    return Message("getAll", "")


def add_game_message(name: str, platform: str, category: str, price: float, score: float, release_year: int) -> Message:
    return Message("addGame", {
        'name': name,
        'platform': platform,
        'category': category,
        'price': price,
        'score': score,
        'release_year': release_year
    })


def get_game_by_id_message(game_id: int) -> Message:
    return Message("getGameByID", {
        'id': game_id
    })


def get_game_by_name_message(name: str) -> Message:
    return Message("getGameByName", {
        'name': name
    })


def get_game_by_platform_message(platform: str) -> Message:
    return Message("getGameByPlatform", {
        'platform': platform
    })


def get_game_by_category_message(category: str) -> Message:
    return Message("getGameByCategory", {
        'category': category
    })


def delete_game_message(game_id: int) -> Message:
    return Message("deleteGame", {
        'id': game_id
    })


def get_game_by_score_message(score: int) -> Message:
    return Message("getGameByScore", {
        'score': score
    })


def get_game_by_year_message(release_year: int) -> Message:
    return Message("getGameByYear", {
        'release_year': release_year
    })


def get_game_by_price_message(price: int) -> Message:
    return Message("getGameByPrice", {
        'price': price
    })


def get_game_by_price_between_message(start: int, end: int) -> Message:
    return Message("getGameByPriceBetween", {
        'start': start,
        'end': end
    })


def result_message(result) -> Message:
    return Message("result", result)


def error_message(message: str) -> Message:
    return Message("error", {
        "value": message
    })
