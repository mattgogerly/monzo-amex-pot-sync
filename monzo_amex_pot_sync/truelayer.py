import logging as log
import os
import requests
import time
from . import db
from urllib import parse
from flask import Blueprint, request

CLIENT_ID = os.getenv('TRUE_LAYER_CLIENT_ID')
CLIENT_SECRET = os.getenv('TRUE_LAYER_CLIENT_SECRET')
REDIRECT_URI = os.getenv('TRUE_LAYER_REDIRECT_URI')

bp = Blueprint('truelayer', __name__, url_prefix='/truelayer')


def handle_auth_callback(code):
    log.info('Received auth callback for TrueLayer, fetching tokens')
    body = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT_URI,
    }
    res = requests.post('https://auth.truelayer.com/connect/token', data=body)
    if res.status_code != 401 and res.status_code != 403:
        res.raise_for_status()

    data = res.json()

    log.info('Obtained tokens from TrueLayer, storing locally')
    db.save('truelayer', data['access_token'], data['refresh_token'], time.time() + data['expires_in'])


def refresh_access_token():
    log.info('Refreshing access token for TrueLayer')
    refresh_token = db.get_tokens('truelayer')['refresh_token']
    body = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }
    res = requests.post('https://auth.truelayer.com/connect/token', data=body)
    if res.status_code != 401 and res.status_code != 403:
        res.raise_for_status()

    data = res.json()

    log.info('Refreshed access token, storing locally')
    db.save('truelayer', data['access_token'], data['refresh_token'], time.time() + data['expires_in'])
    return db.get_tokens('truelayer')


def get_auth_header() -> object:
    tokens = db.get_tokens('truelayer')
    if len(tokens) == 0:
        log.error('No token available to use for TrueLayer')
        raise Exception('No token available to use for TrueLayer')

    if tokens['expires'] < time.time():
        tokens = refresh_access_token()

    return {'Authorization': f'Bearer {tokens["access_token"]}'}


def get_card_balance(account_id) -> object:
    log.info('Fetching balance for card %s', account_id)
    res = requests.get(f'https://api.truelayer.com/data/v1/cards/{account_id}/balance', headers=get_auth_header())
    if res.status_code != 401 and res.status_code != 403:
        res.raise_for_status()

    balance = res.json()['results'][0]['current']

    res = requests.get(f'https://api.truelayer.com/data/v1/cards/{account_id}/transactions/pending',
                       headers=get_auth_header())
    transactions = res.json()['results']
    for transaction in transactions:
        balance += transaction['amount']

    return balance


def get_cards() -> list:
    log.info('Fetching cards from TrueLayer')
    res = requests.get('https://api.truelayer.com/data/v1/cards', headers=get_auth_header())
    if res.status_code != 401 and res.status_code != 403:
        res.raise_for_status()
    return res.json()['results']


def get_total_balance() -> float:
    log.info('Getting total balance of Amex cards')
    cards = get_cards()
    total = 0
    for card in cards:
        card_id = card['account_id']
        total += get_card_balance(card_id)

    return total


@bp.route('/signin', methods=['GET'])
def sign_in():
    query = parse.urlencode({
        'response_type': 'code',
        'response_mode': 'form_post',
        'client_id': CLIENT_ID,
        'scope': 'accounts cards transactions balance offline_access',
        'providers': 'uk-oauth-amex',
        'disable_providers': 'uk-ob-all',
        'nonce': int(time.time())
    })
    query = f'{query}&redirect_uri={REDIRECT_URI}'
    auth_uri = f'https://auth.truelayer.com/?{query}'

    return f'Please sign in <a href="{auth_uri}" target="_blank">here.</a>'


@bp.route('/callback', methods=['POST'])
def callback():
    code = request.form['code']
    handle_auth_callback(code)
    return {}, 200
