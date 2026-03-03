import sqlite3


def create_database(db_name="bot_database.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Enable Foreign Key support (SQLite disables this by default!)
    cursor.execute('PRAGMA foreign_keys = ON;')

    # 1. farkle_roll_records
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS farkle_roll_records (
        record_id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        match_id INTEGER NOT NULL,
        roll_amount INTEGER,
        score INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 2. farkle_finished_matches
    # Added AUTOINCREMENT to match_id
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS farkle_finished_matches (
        match_id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER NOT NULL,
        max_score INTEGER,
        finished_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 3. farkle_match_participants
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS farkle_match_participants (
        match_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        score INTEGER,
        placement INTEGER,
        PRIMARY KEY (match_id, user_id),
        FOREIGN KEY (match_id) REFERENCES farkle_finished_matches(match_id) ON DELETE CASCADE
    )
    ''')

    # 4. farkle_guild_config
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS farkle_guild_config (
        guild_id INTEGER PRIMARY KEY,
        category_id INTEGER
    )
    ''')

    # 5. bot_admins
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bot_admins (
        admin_id INTEGER PRIMARY KEY
    )
    ''')

    # 6. PERFORMANCE INDEXES for get_player_high_scores()
    # Speeds up: "WHERE user_id = ? ORDER BY score DESC"
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_records_global
    ON farkle_roll_records (user_id, score DESC);
    ''')

    # Speeds up: "WHERE user_id = ? AND guild_id = ? ORDER BY score DESC"
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_records_guild
    ON farkle_roll_records (user_id, guild_id, score DESC);
    ''')

    conn.commit()
    conn.close()
    print(f"Database '{db_name}' created successfully with auto-incrementing match IDs.")


if __name__ == "__main__":
    create_database()
