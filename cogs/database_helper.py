import aiosqlite

DB_NAME = "bot_database.db"


# A helper function to get a connection with optimal settings for a bot
def get_db_connection():
    # A timeout of 5-10 seconds prevents "database is locked" errors on concurrent writes
    return aiosqlite.connect(DB_NAME, timeout=5.0)


async def init_db_settings():
    """Run this once when your bot starts to enable WAL mode."""
    async with get_db_connection() as db:
        # WAL mode drastically improves concurrency performance in SQLite
        await db.execute("PRAGMA journal_mode=WAL;")
        await db.commit()


async def log_roll_record(guild_id: int, user_id: int, match_id: int, roll_amount: int, score: int):
    """Saves a notable roll to the records table."""
    async with get_db_connection() as db:
        await db.execute('''
            INSERT INTO farkle_roll_records (guild_id, user_id, match_id, roll_amount, score)
            VALUES (?, ?, ?, ?, ?)
        ''', (guild_id, user_id, match_id, roll_amount, score))
        await db.commit()


async def save_finished_match(guild_id: int, max_score: int, participants: list[tuple[int, int, int]]) -> int:
    """
    Saves a match and all its participants.
    'participants' should be a list of tuples: [(user_id, score, placement), ...]
    Returns the auto-generated match_id.
    """
    async with get_db_connection() as db:
        # 1. Insert the match itself
        cursor = await db.execute('''
            INSERT INTO farkle_finished_matches (guild_id, max_score)
            VALUES (?, ?)
        ''', (guild_id, max_score))

        match_id = cursor.lastrowid
        if match_id is None:
            raise RuntimeError("Failed to retrieve match_id after inserting finished match.")

        # 2. Prepare participant data using unpacking (safer and cleaner)
        # We expect exact unpacking: user_id, score, placement
        participant_data = [
            (match_id, user_id, score, placement)
            for user_id, score, placement in participants
        ]

        # 3. Insert all participants
        await db.executemany('''
            INSERT INTO farkle_match_participants (match_id, user_id, score, placement)
            VALUES (?, ?, ?, ?)
        ''', participant_data)

        # Commit everything as a single transaction
        await db.commit()
        return match_id


async def get_player_high_scores(user_id: int, score_type: str = "score", is_global: bool = False, amount: int = 1, guild_id: int | None = None) -> list[int]:
    """
    Returns a list of a player's highest roll scores, up to the 'amount' limit.
    If there are fewer records than the limit, it returns whatever is available.
    If is_global is True, it searches across all servers.
    If False, it searches only within the provided guild_id.
    """
    # Safety check
    if not is_global and guild_id is None:
        raise ValueError("A guild_id must be provided if is_global is False.")

    column_map = {"score": "score", "rolls": "roll_amount"}
    if score_type not in column_map:
        raise ValueError("Type must be either 'score' or 'rolls'.")

    col = column_map[score_type]

    async with get_db_connection() as db:
        if is_global:
            query = f'''
                SELECT {col} FROM farkle_roll_records
                WHERE user_id = ?
                ORDER BY {col} DESC
                LIMIT ?
            '''
            params = (user_id, amount)
        else:
            query = f'''
                SELECT {col} FROM farkle_roll_records
                WHERE user_id = ? AND guild_id = ?
                ORDER BY {col} DESC
                LIMIT ?
            '''
            params = (user_id, guild_id, amount)

        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()

            # 'rows' is a list of tuples like [(1050,), (800,), (500,)]
            # We unpack it into a clean list of integers: [1050, 800, 500]
            return [row[0] for row in rows]


async def should_store_roll_record(user_id: int, guild_id: int, roll_amount: int, new_score: int) -> bool:
    """
    Checks if a round is a personal best for EITHER the score OR the amount of rolls.
    Returns True if it breaks either personal record in this server.
    """
    async with get_db_connection() as db:
        # We ask SQLite for the absolute maximums for this user in this guild
        async with db.execute('''
            SELECT MAX(score), MAX(roll_amount)
            FROM farkle_roll_records
            WHERE user_id = ? AND guild_id = ?
        ''', (user_id, guild_id)) as cursor:
            row = await cursor.fetchone()

        # If the user has no records, MAX() returns (None, None)
        if row is None or row[0] is None:
            return True

        best_score = row[0]
        best_rolls = row[1]

        # Store it if it strictly beats their personal best score OR personal best roll amount
        return new_score > best_score or roll_amount > best_rolls


async def set_guild_config(guild_id: int, category_id: int):
    """Sets or updates a guild's games category."""
    async with get_db_connection() as db:
        await db.execute('''
            INSERT OR REPLACE INTO farkle_guild_config (guild_id, category_id)
            VALUES (?, ?)
        ''', (guild_id, category_id))
        await db.commit()


async def get_guild_config(guild_id: int) -> int | None:
    """Returns the category_id for the guild, or None if not set."""
    async with get_db_connection() as db:
        async with db.execute('''
            SELECT category_id FROM farkle_guild_config
            WHERE guild_id = ?
        ''', (guild_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None


async def add_bot_admin(admin_id: int):
    """Adds a new global bot admin."""
    async with get_db_connection() as db:
        await db.execute('''
            INSERT OR IGNORE INTO bot_admins (admin_id)
            VALUES (?)
        ''', (admin_id,))
        await db.commit()


async def get_bot_admins() -> list[int]:
    """Returns a list of all bot admin IDs."""
    async with get_db_connection() as db:
        async with db.execute('SELECT admin_id FROM bot_admins') as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
