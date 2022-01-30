# Monzo Amex Pot Sync
Simple Python script to automatically move money into/out of a Monzo pot named 'Amex' to match the balance of Amex cards.

## Requireents
* Docker & Docker Compose

## Usage
1. Register for Monzo Developer and TrueLayer. Create clients and put the details in docker-compose.yml.
2. Run `docker compose up -d` to start the container.
3. Go to `http://localhost:36789/monzo/signin` and follow the OAuth flow to authenticate with Monzo.
4. Go to `http://localhost:36789/truelayer/signin` and follow the OAuth flow to authenticate with TrueLayer.
5. Enjoy!

Note that you'll need to reauthenticate by completing steps 2 and 3 every 90 days, due to Open Banking strong customer authentication requirements.
