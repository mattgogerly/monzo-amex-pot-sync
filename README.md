# Monzo Amex Pot Updater
Simple Python script to automatically move money into/out of a Monzo pot named 'Amex' to match the balance of Amex cards.

## Requireents
* Docker & Docker Compose

## Usage
1. Run `docker compose up -d` to start the container.
2. Go to `http://localhost:36789/monzo/signin` and follow the OAuth flow to authenticate with Monzo.
3. Go to `http://localhost:36789/truelayer/signin` and follow the OAuth flow to authenticate with TrueLayer.
4. Enjoy!

Note that you'll need to reauthenticate by completing steps 2 and 3 every 90 days, due to Open Banking strong customer authentication requirements.
