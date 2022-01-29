import db
import logging as log
import os
import requests
import time
import urllib
from flask import Blueprint, request


CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = "http://localhost:36789/truelayer/callback"

bp = Blueprint('truelayer', __name__, url_prefix='/truelayer')


def handle_auth_callback(code):
    body = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT_URI,
    }
    res = requests.post('https://auth.truelayer.com/connect/token', data=body)
    data = res.json()

    log.info('Obtained tokens from TrueLayer, storing locally')
    db.save('truelayer', data['access_token'], data['refresh_token'], time.time() + data['expires_in'])


def get_balance(account_id, access_token) -> object:
    auth_header = {'Authorization': f'Bearer {access_token}'}
    res = requests.get(f'https://api.truelayer.com/data/v1/cards/{account_id}/balance', headers=auth_header)
    res.raise_for_status()
    balance = res.json()['results'][0]

    return balance['current']


def get_accounts(access_token) -> object:
    auth_header = {'Authorization': f'Bearer {access_token}'}
    res = requests.get('https://api.truelayer.com/data/v1/cards', headers=auth_header)
    res.raise_for_status()

    total = 0
    for account in res.json()['results']:
        acc_id = account['account_id']
        balance = get_balance(acc_id, access_token)
        accounts[acc_id] = {
            'balance': balance,
            'name': acc_name,
        }

    return total


def get_total_balance():
    tokens = db.get_tokens('truelayer')
    if len(tokens) == 0:
        log.error('No token available to use for TrueLayer')
        raise Exception('No token available to use for TrueLayer')

    access_token = tokens['access_token']

    auth_header = {'Authorization': f'Bearer {access_token}'}
    res = requests.get('https://api.truelayer.com/data/v1/cards', headers=auth_header)
    res.raise_for_status()

    total = 0
    for account in res.json()['results']:
        acc_id = account['account_id']
        total += get_balance(acc_id, access_token)

    return total


@bp.route('/signin', methods=['GET'])
def sign_in():
    query = urllib.parse.urlencode({
        'response_type': 'code',
        'response_mode': 'form_post',
        'client_id': CLIENT_ID,
        'scope': 'accounts cards balance offline_access',
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
