# This file have all the methods related to the Message class
# Used to send message between the SQL server and the client over TCP/RUDP connection

class Message:
    func = ""
    body = ""

    def __init__(self, func, body):
        self.func = func
        self.body = body

    def to_json(self):
        return {
            'func': self.func,
            'body': self.body
        }

    def __str__(self):
        return f"<Message fun:{self.func} body:{self.body}>"


def json_to_message(json_object) -> Message:
    return Message(func=json_object['func'],
                   body=json_object['body'])


def str_to_message(string) -> Message:
    prefix1 = "fun:"
    prefix2 = "body:"
    prefix3 = "body:"
    prefix4 = ">"
    # Get substring between prefix1 and prefix2
    func = string.split(prefix1)[1].split(prefix2)[0].strip()
    body = string.split(prefix3)[1].split(prefix4)[0].strip()
    print(func)
    print(body)
    return Message(func, body)


def get_all_message() -> Message:
    return Message("getAll", "")


def add_game_message(name: str, platform: str, category: str, price: float, score: float, release_year: int) -> Message:
    return Message("addGame", {
        'id': 0,
        'name': name,
        'platform': platform,
        'category': category,
        'price': price,
        'score': score,
        'release_year': release_year
    })


def update_game_message(game_id: int, name: str, platform: str, category: str, price: float, score: float,
                        release_year: int) -> Message:
    return Message("updateGame", {
        'id': game_id,
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


def get_game_by_score_message(score: float) -> Message:
    return Message("getGameByScore", {
        'score': score
    })


def get_game_by_year_message(release_year: int) -> Message:
    return Message("getGameByYear", {
        'release_year': release_year
    })


def get_game_by_price_message(price: float) -> Message:
    return Message("getGameByPrice", {
        'price': price
    })


def get_game_by_price_between_message(start: float, end: float) -> Message:
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
