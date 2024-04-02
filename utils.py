import asyncio
import time
import sqlite3
import logging
import datetime
import pytz
import requests
import pandas as pd
from bs4 import BeautifulSoup

from config import URL_MAPPING, MIN_ODDS_FACTOR, PYTHON_TO_SQLITE_DTYPE_MAPPING
from flags import FLAGS


# TODO: Remove this function and instead just use normal requests library. Handle all exceptions in respective places
def make_request(url, headers=None, params=None, data=None, method="GET"):

    try:
        response = requests.request(
            method, url, headers=headers, params=params, data=data
        )
        # If the response was successful, no Exception will be raised
        response.raise_for_status()
    except requests.RequestException as e:
        # If the request failed, print the error message
        print(f"Request failed: {e}")
        return None

    return response


def get_betting_mapping():

    bet_mappings = {}
    url = "https://www.betburger.com/api/entity_ids"
    response = make_request(url)
    # Check if the request was successful (status code 200)
    if response:

        # Parse the HTML content with BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")

        # Find the h2 tag with the specified title
        target_h2 = soup.find(
            "span", {"title": "translation missing: en.bet.Variation"}
        )

        # Check if the h2 tag is found
        if target_h2:
            # Find the table element following the target h2 tag
            target_table = target_h2.find_next("table")

            # Check if the table element is found
            if target_table:
                # Find the tbody element within the table
                tbody = target_table.find("tbody")

                # Check if the tbody element is found
                if tbody:
                    # Extract all rows from the tbody
                    rows = tbody.find_all("tr")

                    # Now 'rows' contains the contents of the table body
                    for row in rows:
                        # Extract and print the data from each row
                        cells = row.find_all("td")
                        row_data = [cell.text.strip() for cell in cells]
                        id, name = int(row_data[0]), row_data[1]
                        bet_mappings[id] = name

                else:
                    print("tbody not found.")
            else:
                print("Table not found.")
        else:
            print("h2 tag not found.")
    else:
        print(f"Failed to retrieve the content. Status code: {response.status_code}")

    return bet_mappings


# Obtain the bets from BetBurger
def process_bets_with_retry(token, filter_id):
    retries = 3
    delay = 2

    for i in range(retries):
        try:
            bets = process_bets(token, filter_id)
            return bets
        except Exception as e:
            logging.error(f"Error retrieving bets: {e}")

            # Log the error in a file
            with open("error.log", "a") as f:
                f.write(f"Error retrieving bets: {e}\n")

            if i < retries - 1:
                logging.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                logging.error("Failed to retrieve bets after multiple retries")

    return pd.DataFrame()


def process_bets(token, filter, per_page=500):

    url = "https://rest-api-pr.betburger.com/api/sv1/valuebets/bot_pro_search"

    payload = f"access_token={token}&search_filter%5B%5D={filter}&per_page={per_page}"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    # If the response was successful, no Exception will be raised
    response.raise_for_status()

    response_json = response.json()
    outcomes = response_json["bets"]
    value_bets = response_json["source"]["value_bets"]

    # Check if there are any outcomes that came back in the request
    if not outcomes:
        return pd.DataFrame()

    outcomes_df = pd.DataFrame(outcomes)
    value_bets_df = pd.DataFrame(value_bets)[["bet_id", "avg_koef", "percent"]]

    # Mapping the outcome ids to the outcome names
    outcome_mapping = get_betting_mapping()

    best_bets_df = (
        outcomes_df[
            [
                "id",
                "market_and_bet_type",
                "market_and_bet_type_param",
                "bookmaker_event_id",
                "bookmaker_id",
                "league",
                "event_name",
                "home",
                "away",
                "sport_id",
                "swap_teams",
                "started_at",
                "koef_last_modified_at",
                "bookmaker_event_direct_link",
                "koef",
            ]
        ]
        .merge(value_bets_df, left_on="id", right_on="bet_id", how="left")
        .astype(
            {
                "market_and_bet_type_param": str,
                "started_at": "datetime64[s]",
                "koef_last_modified_at": "datetime64[ms]",
                "home": "str",
                "away": "str",
            }
        )
    )

    # Removing the rows with no average coefficient
    best_bets_df = best_bets_df[~best_bets_df.avg_koef.isna()]

    # Adding the minimum coefficient for the bet
    best_bets_df["min_koef"] = best_bets_df["koef"] * MIN_ODDS_FACTOR

    # Obtaining the bet information through the mapping
    best_bets_df["outcome_name"] = (
        best_bets_df["market_and_bet_type"].map(outcome_mapping).fillna("Unknown")
    )

    # Adding the bookmaker URL
    best_bets_df["bet_url"] = (
        best_bets_df["bookmaker_id"].map(URL_MAPPING).fillna("{bookmaker_event_link}")
    )
    best_bets_df["bet_url"] = best_bets_df.apply(
        lambda row: row["bet_url"].replace(
            "{bookmaker_event_link}",
            (
                row["bookmaker_event_direct_link"]
                if not pd.isna(row["bookmaker_event_direct_link"])
                else "null"
            ),
        ),
        axis=1,
    )

    # Setting the betting information
    best_bets_df["outcome_name"] = best_bets_df.apply(
        lambda row: (
            row["outcome_name"]
            .replace("Team1", row["home"])
            .replace("Team2", row["away"])
            .replace("%s", row["market_and_bet_type_param"])
            if row["swap_teams"] == False
            else row["outcome_name"]
            .replace("Team1", row["away"])
            .replace("Team2", row["home"])
            .replace("%s", row["market_and_bet_type_param"])
        ),
        axis=1,
    )

    best_bets_df["bet_info"] = best_bets_df.apply(
        lambda row: f"{row['outcome_name']} @ {round(row['koef'], 2)}", axis=1
    )

    best_bets_df = best_bets_df.drop(
        [
            "bet_id",
            "outcome_name",
            "market_and_bet_type_param",
        ],
        axis=1,
    )

    best_bets_df["receive_date"] = datetime.datetime.now(datetime.UTC)

    # Converting the columns to the correct data types to be stored in the database
    best_bets_df = best_bets_df.astype(
        {"receive_date": str, "started_at": str, "koef_last_modified_at": str}
    )

    return best_bets_df


def filter_new_bets(api_bets, db_bets):

    new_bets = []
    # Filter the records that are not in the database and insert them

    ids_to_insert = set(api_bets.id) - set(db_bets.id)
    new_bets_df = api_bets[api_bets.id.isin(ids_to_insert)]

    return new_bets_df


def load_duplicate_records(bets, db):

    ids = tuple(bets.id)
    ids_str = str(ids) if len(ids) > 1 else f"('{ids[0]}')"

    filtered_db_records = db.get_data(ids_str)
    filtered_db_df = pd.DataFrame(filtered_db_records, columns=bets.columns)

    new_bets_df = filter_new_bets(bets, filtered_db_df)

    return new_bets_df


def insert_new_bets(db, new_bets_df, new_bets):
    try:
        # Insert the new bets into the database
        db.insert_data(new_bets)
    except sqlite3.OperationalError as e:
        column_name = str(e).split(" ")[-1]
        column_dtype = new_bets_df.dtypes[column_name]
        logging.warning(
            f"There was a difficulty inserting the new bets into the database...adding column {column_name} and retrying"
        )

        sqlite_dtype = PYTHON_TO_SQLITE_DTYPE_MAPPING.get(column_dtype, "TEXT")
        # Add the missing column to the database and try to insert the new bets again
        db.add_columns(column_name, sqlite_dtype)
        db.insert_data(new_bets)


def get_flag_by_name(name):

    retrieved_flag = list(
        filter(lambda flag_data: flag_data["name"].lower() == name.lower(), FLAGS)
    )

    if retrieved_flag:
        return retrieved_flag[0]["emoji"]

    return "🇪🇺"


def format_messages(best_bets_df, base_message, time_zone, sport_emoji):
    messages_to_send = []
    for i, df in best_bets_df.groupby(["bookmaker_event_id", "market_and_bet_type"]):
        cur_msg = base_message
        bet_group = df.to_dict(orient="records")

        raw_time = pd.to_datetime(bet_group[0]["started_at"])
        event_time = (
            pytz.utc.localize(raw_time).astimezone(time_zone).strftime("%A %H:%M")
        )

        league_info = bet_group[0]["league"].split(".")
        country_name, league_name = league_info[0], league_info[-1].strip()

        # If the league name is not found, then there is no country name
        if len(league_info) < 2:
            country_name = ""

        flag = get_flag_by_name(country_name)

        messages_to_send.append(
            cur_msg.format(
                league_name=f"{flag} {league_name}",
                sport_emoji=sport_emoji,
                event_name=bet_group[0]["event_name"],
                bets="\n\t".join([f"- {bet['bet_info']} (1u)" for bet in bet_group]),
                min_odds=" & ".join(
                    [str(round(min_odd["min_koef"], 1)) for min_odd in bet_group]
                ),
                match_time=event_time,
                bet_url=bet_group[0]["bet_url"],
            )
        )

    return messages_to_send


def send_message(token, chat_id, message):

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    params = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
    response = make_request(url, params=params, method="POST")

    return response.json()


async def send_message_with_retry(
    token, chat_id, message, retry_count=3, backoff_delay=1
):
    for i in range(retry_count):
        try:
            response = send_message(token, chat_id, message)
            return response
        except Exception as e:
            print(f"Failed to send message. Retrying in {backoff_delay} seconds...")
            await asyncio.sleep(backoff_delay)
            backoff_delay *= 2
    return None


async def send_messages_with_retry(
    token, chat_id, messages, max_rate=20, rate_limit_interval=60
):
    futures = []
    count = 0
    start_time = time.time()

    for message in messages:
        if count >= max_rate:
            elapsed_time = time.time() - start_time
            if elapsed_time < rate_limit_interval:
                sleep_time = rate_limit_interval - elapsed_time
                print(f"Rate limit reached. Sleeping for {sleep_time} seconds...")
                await asyncio.sleep(sleep_time)
                count = 0
                start_time = time.time()

        future = send_message_with_retry(token, chat_id, message)
        futures.append(future)
        count += 1

    await asyncio.gather(*futures)
