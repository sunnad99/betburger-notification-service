import sqlite3


class Database:
    def __init__(self, db_file="bets.db"):
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS data (
                id TEXT PRIMARY KEY,
                market_and_bet_type INTEGER,
                bookmaker_event_id INTEGER,
                bookmaker_id INTEGER,
                league TEXT,
                event_name TEXT,
                home TEXT,
                away TEXT,
                swap_teams INTEGER,
                started_at TEXT,
                koef_last_modified_at TEXT,
                bookmaker_event_direct_link TEXT,
                koef REAL,
                avg_koef REAL,
                percent REAL,
                min_koef REAL,
                bet_url TEXT,
                bet_info TEXT,
                receive_date TEXT
            )
        """
        )
        self.conn.commit()

    def insert_data(
        self,
        id,
        market_and_bet_type,
        bookmaker_event_id,
        bookmaker_id,
        league,
        event_name,
        home,
        away,
        swap_teams,
        started_at,
        koef_last_modified_at,
        bookmaker_event_direct_link,
        koef,
        avg_koef,
        percent,
        min_koef,
        bet_url,
        bet_info,
        receive_date,
    ):
        self.cursor.execute(
            """
            INSERT OR IGNORE INTO data (
                id, market_and_bet_type, bookmaker_event_id, bookmaker_id, league, event_name, home, away,
                swap_teams, started_at, koef_last_modified_at, bookmaker_event_direct_link, koef, avg_koef,
                percent, min_koef, bet_url, bet_info, receive_date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                id,
                market_and_bet_type,
                bookmaker_event_id,
                bookmaker_id,
                league,
                event_name,
                home,
                away,
                swap_teams,
                started_at,
                koef_last_modified_at,
                bookmaker_event_direct_link,
                koef,
                avg_koef,
                percent,
                min_koef,
                bet_url,
                bet_info,
                receive_date,
            ),
        )
        self.conn.commit()

    def update_data(self, id, koef_last_modified_at, new_data):
        self.cursor.execute(
            """
            UPDATE data
            SET koef_last_modified_at = ?,
                -- Update other columns here
            WHERE id = ?
        """,
            (koef_last_modified_at, id),
        )
        self.conn.commit()

    def delete_data(self, id):
        self.cursor.execute(
            """
            DELETE FROM data
            WHERE id = ?
        """,
            (id,),
        )
        self.conn.commit()

    def get_data(self, id):
        self.cursor.execute(
            """
            SELECT * FROM data
            WHERE id = ?
        """,
            (id,),
        )
        return self.cursor.fetchone()

    def get_all_data(self):
        self.cursor.execute(
            """
            SELECT * FROM data
        """
        )
        return self.cursor.fetchall()

    def close_connection(self):
        self.cursor.close()
        self.conn.close()
