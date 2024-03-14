import pytz
import logging

# Initialize the logger
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

URL_MAPPING = {19: "https://www.unibet.com/betting/sports/event/{bookmaker_event_link}"}

MIN_ODDS_FACTOR = 0.874
FREQUENCY_SECONDS = 100


TIME_ZONE = pytz.timezone("Europe/Stockholm")

BASE_MESSAGE = """
Nytt Spel!

⚽️ {event_name}
🎲 Bets
{bets}


{league_name}
🔐 Lägsta spelbara odds {min_odds}
🕰️  {match_time}
🌐 {bet_url}
"""
