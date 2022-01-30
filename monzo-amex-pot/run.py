import logging as log
from flask import abort, Blueprint
import truelayer
import monzo

bp = Blueprint('run', __name__, url_prefix='/')


@bp.route('/run', methods=['GET'])
def run():
    try:
        monzo_account, monzo_pot = monzo.get_account_and_pot()
        pot_balance = monzo_pot['balance']
    except Exception as e:
        log.exception('Failed to get pot balance from Monzo: %s', e)
        abort(500)

    try:
        amex_balance = truelayer.get_total_balance()
    except Exception as e:
        log.exception('Failed to get Amex balance from TrueLayer, sending Monzo notification: %s', e)
        monzo.send_notification(monzo_account['id'], 'Authentication with Amex has expired', 'Uh oh')
        abort(500)

    balance_diff = (amex_balance * 100) - pot_balance

    if balance_diff > 0:
        log.info('Adding £%s to Amex pot to cover difference', balance_diff / 100.0)
        monzo.add_to_pot(monzo_account['id'], monzo_pot['id'], balance_diff)
    elif balance_diff < 0:
        log.info('Withdrawing £%s from Amex pot', +balance_diff / 100.0)
        monzo.withrdaw_from_pot(monzo_account['id'], monzo_pot['id'], balance_diff)
    else:
        log.info('No balance difference, doing nothing')

    return {}, 200
