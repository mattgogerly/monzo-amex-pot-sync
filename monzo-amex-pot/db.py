from tinydb import TinyDB, Query

db = TinyDB('db.json')


def get_tokens(name):
    data = Query()
    result = db.get(data.name is name)

    if result is None:
        return {}

    return result


def save(name, access_token, refresh_token, expires):
    data = Query()
    db.upsert({'name': name, 'access_token': access_token, 'refresh_token': refresh_token, 'expires': expires},
              data.name is name)
