import pytz
import logging
import numpy as np

# Initialize the logger
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

URL_MAPPING = {19: "https://www.unibet.com/betting/sports/event/{bookmaker_event_link}"}

MIN_ODDS_FACTOR = 0.874
FREQUENCY_SECONDS = 100


TIME_ZONE = pytz.timezone("Europe/Stockholm")

PYTHON_TO_SQLITE_DTYPE_MAPPING = {
    np.dtype("int64"): "INTEGER",
    np.dtype("float64"): "REAL",
    np.dtype("object"): "TEXT",
    np.dtype("bool"): "INTEGER",
    np.dtype("datetime64[ns]"): "TEXT",
}

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
