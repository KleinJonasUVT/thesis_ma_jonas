import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

DB_NAME = 'users.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS favorites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    course_code TEXT NOT NULL,
                    UNIQUE(user_id, course_code)
                )''')
    conn.commit()
    conn.close()


def create_user(name, email, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    password_hash = generate_password_hash(password)
    c.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?)',
              (name, email, password_hash))
    conn.commit()
    conn.close()


def get_user_by_email(email):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = c.fetchone()
    conn.close()
    return user


def get_user_by_id(user_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = c.fetchone()
    conn.close()
    return user


def authenticate_user(email, password):
    user = get_user_by_email(email)
    if user and check_password_hash(user['password'], password):
        return user
    return None


def update_user(user_id, name=None, password=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if name is not None:
        c.execute('UPDATE users SET name = ? WHERE id = ?', (name, user_id))
    if password:
        password_hash = generate_password_hash(password)
        c.execute('UPDATE users SET password = ? WHERE id = ?',
                  (password_hash, user_id))
    conn.commit()
    conn.close()


def add_favorite(user_id, course_code):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO favorites (user_id, course_code) VALUES (?, ?)',
              (user_id, course_code))
    conn.commit()
    conn.close()


def remove_favorite(user_id, course_code):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('DELETE FROM favorites WHERE user_id = ? AND course_code = ?',
              (user_id, course_code))
    conn.commit()
    conn.close()


def get_favorites(user_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT course_code FROM favorites WHERE user_id = ?', (user_id,))
    favorites = [row['course_code'] for row in c.fetchall()]
    conn.close()
    return favorites
