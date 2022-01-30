import logging as log
import os
import requests
import time
from . import db
from urllib import parse
from flask import Blueprint, request

CLIENT_ID = os.getenv('MONZO_CLIENT_ID')
CLIENT_SECRET = os.getenv('MONZO_CLIENT_SECRET')
REDIRECT_URI = "http://localhost:36789/monzo/callback"
DEDUPE_ID = 0

bp = Blueprint('monzo', __name__, url_prefix='/monzo')


def handle_auth_callback(code):
    log.info('Received auth callback for Monzo, fetching tokens')
    body = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT_URI
    }
    res = requests.post('https://api.monzo.com/oauth2/token', data=body)
    data = res.json()

    log.info('Obtained tokens from Monzo, storing locally')
    db.save('monzo', data['access_token'], data['refresh_token'], time.time() + data['expires_in'])


def refresh_access_token():
    log.info('Refreshing access token for Monzo')
    refresh_token = db.get_tokens('monzo')['refresh_token']

    body = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }
    res = requests.post('https://api.monzo.com/oauth2/token', data=body)
    data = res.json()

    log.info('Refreshed access token, storing locally')
    db.save('monzo', data['access_token'], data['refresh_token'], time.time() + data['expires_in'])
    return db.get_tokens('monzo')


def get_auth_header() -> object:
    tokens = db.get_tokens('monzo')
    if len(tokens) == 0:
        log.error('No token available to use for Monzo')
        raise Exception('No token available to use for Monzo')

    if tokens['expires'] < time.time():
        tokens = refresh_access_token()

    return {'Authorization': f'Bearer {tokens["access_token"]}'}


def get_account() -> object:
    log.info('Getting account info from Monzo')
    res = requests.get(f'https://api.monzo.com/accounts', headers=get_auth_header())
    res.raise_for_status()

    return res.json()['accounts'][0]


def find_amex_pot(account_id) -> object:
    log.info('Finding Amex pot')
    query = parse.urlencode({
        'current_account_id': account_id
    })
    res = requests.get(f'https://api.monzo.com/pots?{query}', headers=get_auth_header())
    res.raise_for_status()

    pots = res.json()['pots']
    amex_pots = list(filter(lambda x: (x['name'] == 'Amex' and not x['deleted']), pots))

    if len(amex_pots) == 0:
        log.error('No pot named Amex found')
        raise Exception('No pot named Amex found')

    return amex_pots[0]


def get_account_and_pot():
    log.info('Getting account and pot info from Monzo')
    account = get_account()
    return account, find_amex_pot(account['id'])


def add_to_pot(account_id, pot_id, amount):
    log.info('Adding £%s to pot %s', amount / 100.0, pot_id)
    data = {
        'source_account_id': account_id,
        'amount': amount,
        'dedupe_id': int(time.time())
    }
    res = requests.put(f'https://api.monzo.com/pots/{pot_id}/deposit', data=data, headers=get_auth_header())
    res.raise_for_status()


def withdraw_from_pot(account_id, pot_id, amount):
    log.info('Withdrawing £%s from pot %s', amount / 100.0, pot_id)
    data = {
        'destination_account_id': account_id,
        'amount': amount,
        'dedupe_id': time.time()
    }
    res = requests.put(f'https://api.monzo.com/pots/{pot_id}/withdraw', data=data, headers=get_auth_header())
    res.raise_for_status()


def send_notification(account_id, title, message):
    log.info('Sending notification to Monzo')
    body = {
      "account_id": account_id,
      "type": "basic",
      "params[image_url]": "https://www.nyan.cat/cats/original.gif",
      "params[title]": title,
      "params[body]": message
    }
    res = requests.post('https://api.monzo.com/feed', data=body, headers=get_auth_header())
    res.raise_for_status()


@bp.route('/signin', methods=['GET'])
def sign_in():
    query = parse.urlencode({
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'state': int(time.time()),
        'redirect_uri': REDIRECT_URI
    })
    auth_uri = f'https://auth.monzo.com/?{query}'
    return f'Please sign in <a href="{auth_uri}" target="_blank">here.</a>'


@bp.route('/callback', methods=['GET'])
def callback():
    code = request.args.get('code')
    handle_auth_callback(code)
    return {}, 200
