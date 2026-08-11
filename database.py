import sqlite3
import json
from datetime import datetime

DATABASE = 'doge_empire.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            coins REAL DEFAULT 0,
            total_coins REAL DEFAULT 0,
            clicks INTEGER DEFAULT 0,
            stage INTEGER DEFAULT 1,
            multiplier REAL DEFAULT 1.0,
            auto_click_power REAL DEFAULT 0,
            crit_chance REAL DEFAULT 0,
            crit_multiplier REAL DEFAULT 2.0,
            click_power REAL DEFAULT 1.0,
            last_save TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            daily_streak INTEGER DEFAULT 0,
            last_daily_reward TIMESTAMP,
            active_skin TEXT DEFAULT 'default',
            skin_bonus REAL DEFAULT 1.0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS upgrades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            upgrade_id TEXT,
            level INTEGER DEFAULT 0,
            UNIQUE(user_id, upgrade_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            event_type TEXT,
            event_data TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS monetization_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            monetization_type TEXT,
            action TEXT,
            reward_data TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN daily_streak INTEGER DEFAULT 0')
    except:
        pass
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN last_daily_reward TIMESTAMP')
    except:
        pass
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN active_skin TEXT DEFAULT "default"')
    except:
        pass
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN skin_bonus REAL DEFAULT 1.0')
    except:
        pass
    
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
    conn.close()
    return dict(user) if user else None

def create_user(user_id):
    conn = get_db()
    conn.execute('INSERT INTO users (user_id) VALUES (?)', (user_id,))
    conn.commit()
    conn.close()
    return get_user(user_id)

def update_user(user_id, **kwargs):
    conn = get_db()
    sets = ', '.join([f'{k} = ?' for k in kwargs.keys()])
    values = list(kwargs.values()) + [user_id]
    conn.execute(f'UPDATE users SET {sets} WHERE user_id = ?', values)
    conn.commit()
    conn.close()

def get_upgrades(user_id):
    conn = get_db()
    upgrades = conn.execute('SELECT * FROM upgrades WHERE user_id = ?', (user_id,)).fetchall()
    conn.close()
    return {u['upgrade_id']: u['level'] for u in upgrades}

def set_upgrade(user_id, upgrade_id, level):
    conn = get_db()
    conn.execute('''
        INSERT OR REPLACE INTO upgrades (user_id, upgrade_id, level)
        VALUES (?, ?, ?)
    ''', (user_id, upgrade_id, level))
    conn.commit()
    conn.close()

def add_event(user_id, event_type, event_data):
    conn = get_db()
    conn.execute('INSERT INTO events_log (user_id, event_type, event_data) VALUES (?, ?, ?)',
                 (user_id, event_type, json.dumps(event_data)))
    conn.commit()
    conn.close()

def add_monetization_log(user_id, monetization_type, action, data):
    conn = get_db()
    conn.execute('INSERT INTO monetization_log (user_id, monetization_type, action, reward_data) VALUES (?, ?, ?, ?)',
                 (user_id, monetization_type, action, json.dumps(data)))
    conn.commit()
    conn.close()

def get_last_monetization(user_id, monetization_type):
    conn = get_db()
    result = conn.execute('''
        SELECT timestamp FROM monetization_log 
        WHERE user_id = ? AND monetization_type = ? 
        ORDER BY timestamp DESC LIMIT 1
    ''', (user_id, monetization_type)).fetchone()
    conn.close()
    return result['timestamp'] if result else None