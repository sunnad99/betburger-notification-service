import pytz

URL_MAPPING = {19: "https://www.unibet.com/betting/sports/event/{bookmaker_event_link}"}

MIN_ODDS_FACTOR = 0.874


TIME_ZONE = pytz.timezone("Europe/Stockholm")

BASE_MESSAGE = """
    {league_name}

⚽️ {event_name}

🎲 Bets
{bets}

🔐 Lägsta spelbara odds {min_odds}

🕰️  {match_time}

🌐 {bet_url}
"""
