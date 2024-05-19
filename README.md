# BETBURGER NOTIFICATION SERVICE

This service serves to provide prematch value bets. Bets are sent to telegram groups where each group is associated with a bookmaker.

Users can subscribe to the service, to a specific bookmaker, by paying a monthly subscription fee for each supported bookmaker.

The user is then provided with a group link to join the telegram group associated with the bookmaker they have subscribed to.

## Features

- Live prematch value bets
- Fully local service
  - SQLite database for storing user data and bets
  - NGROK for exposing the local server to the internet
  - Scheduler for running the telegram bot
  - FastAPI Stripe backend for handling subscription payments
  - Local Telegram backend for handling subscription payments
  - Currently only Unibet is supported
- Stripe subscription payments for users to access the service
- Temporary group links for users to join the telegram group associated with the bookmaker they have subscribed to

## Installation

NOTE: This project was built with `Python 3.11.4`

1. Clone the repository

```bash
git clone
```

2. Install the dependencies

```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory and add the following environment variables

```bash
# Telegram bot token
TELEGRAM_B
OT_TOKEN=your_telegram_bot_token

# Stripe secret key
STRIPE_SECRET_KEY=your_stripe_secret_key

# Database connection string
DATABASE_URL=your_database_connection_string
```

4. Run the FastAPI Stripe backend

```bash
python -m src.server.stripe_backend
```

5. Run the local Telegram backend

```bash
python -m src.server.telegram_backend
```

6. Run the telegram bot

```bash
python -m src.server.main
```

## Future Aspects:

[ ] Allow multiple filter id requests to be run at the same time (Betburger only)

[ ] Allow messages to be sent to multiple telegram groups at the same time based on the bookmaker

[ ] Add multiple APIs for retrieving bets and have a common interface (e.g bets.retrieve() will be a method that will return the bets in our own schema regardless of which API is calling it)

[ ] Have a distributed architecture for sending messages to each telegram group (e.g. use celery)

##### NOTE: This will still run locally

[ ] Use ORM for database queries (e.g SQLAlchemy) instead of raw SQL queries

[ ] Move infrastructure to cloud for 24/7 reliability and scalability

- Use VMs for telegram bot and backend

- Use cloud functions and async task queues for running the stripe backend and sending messages to telegram groups

- Use NOSQL databases for storing bets and user data
