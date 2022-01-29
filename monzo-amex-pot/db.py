from tinydb import TinyDB, Query


db = TinyDB('db.json')


def get_tokens(name):
  Type = Query()
  result = db.get(Type.name == name)

  if result is None:
    return {}

  return result


def save(name, access_token, refresh_token, expires):
  Type = Query()
  db.upsert({'name': name, 'access_token': access_token, 'refresh_token': refresh_token, 'expires': expires}, Type.name == name)