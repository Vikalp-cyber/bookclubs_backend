import sqlite3

from logging import getLogger
logger = getLogger("main")

logger.debug("Creating the connections")

# Create a connection to the SQLite database
conn = sqlite3.connect('site.db', check_same_thread=False)
cursor = conn.cursor()

def create_tables():
    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS data (
            id INTEGER PRIMARY KEY,
            username TEXT,
            email TEXT,
            password TEXT
        )
    '''
    )

conn.commit()
create_tables()


