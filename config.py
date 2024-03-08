import pytz
import logging

# Logging
LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

URL_MAPPING = {19: "https://www.unibet.com/betting/sports/event/{bookmaker_event_link}"}

MIN_ODDS_FACTOR = 0.874
FREQUENCY_MINUTES = 1


TIME_ZONE = pytz.timezone("Europe/Stockholm")

BASE_MESSAGE = """
⚽️ {event_name}
🎲 Bets
{bets}


{league_name}
🔐 Lägsta spelbara odds {min_odds}
🕰️  {match_time}
🌐 {bet_url}
"""
