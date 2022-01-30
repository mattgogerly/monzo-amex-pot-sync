import os
from tinydb import TinyDB, Query

db = TinyDB(os.path.abspath('/etc/monzo/db.json'))


def get_tokens(name):
    data = Query()
    result = db.get(data.name == name)

    if result is None:
        return {}

    return result


def save(name, access_token, refresh_token, expires):
    data = Query()
    db.upsert({'name': name, 'access_token': access_token, 'refresh_token': refresh_token, 'expires': expires},
              data.name == name)
