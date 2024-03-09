import sqlite3


class Database:
    def __init__(self, db_file="bets.db"):
        self.db_file = db_file

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_file)
        self.cursor = self.conn.cursor()
        self.create_table()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cursor.close()
        self.conn.close()

    def create_table(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS bets (
                id TEXT,
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

    def insert_data(self, data):
        self.cursor.executemany(
            """
            INSERT INTO bets (
                id, market_and_bet_type, bookmaker_event_id, bookmaker_id, league, event_name, home, away,
                swap_teams, started_at, koef_last_modified_at, bookmaker_event_direct_link, koef, avg_koef,
                percent, min_koef, bet_url, bet_info, receive_date
            )
            VALUES (:id, :market_and_bet_type, :bookmaker_event_id, :bookmaker_id, :league, :event_name, :home, :away,
                :swap_teams, :started_at, :koef_last_modified_at, :bookmaker_event_direct_link, :koef, :avg_koef,
                :percent, :min_koef, :bet_url, :bet_info, :receive_date)
        """,
            data,
        )
        self.conn.commit()

    def update_data(self, id, koef_last_modified_at, new_data):
        self.cursor.execute(
            """
            UPDATE bets
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
            DELETE FROM bets
            WHERE id = ?
        """,
            (id,),
        )
        self.conn.commit()

    def get_data(self, ids):
        self.cursor.execute(
            """
            SELECT * FROM bets
            WHERE id IN {ids}

        """.format(
                ids=ids
            )
        )
        return self.cursor.fetchall()

    def get_all_data(self):
        self.cursor.execute(
            """
            SELECT * FROM bets
        """
        )
        return self.cursor.fetchall()
