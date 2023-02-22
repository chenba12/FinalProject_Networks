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
