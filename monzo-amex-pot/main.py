import logging as log
import os
import schedule
import threading
import time
import monzo, truelayer
from flask import abort, Flask


log.basicConfig(level=log.INFO)


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    app.register_blueprint(monzo.bp)
    app.register_blueprint(truelayer.bp)

    return app


app = create_app()


@app.route('/')
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


def setup_scheduling():
    schedule.every(15).minutes.do(run)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    api_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port='36789', debug=True, use_reloader=False))
    loop_thread = threading.Thread(target=setup_scheduling)
    api_thread.start()
    loop_thread.start()
