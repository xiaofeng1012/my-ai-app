# database.py
import sqlite3
import hashlib

def init_db():
    conn = sqlite3.connect('ksr_network.db')
    c = conn.cursor()
    # 建立使用者表
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT, role TEXT)''')
    # 建立預設 Admin (密碼 2812 的 SHA256)
    admin_pw = hashlib.sha256("2812".encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO users VALUES ('Admin', ?, 'admin')", (admin_pw,))
    conn.commit()
    conn.close()

def register_user(username, password):
    try:
        conn = sqlite3.connect('ksr_network.db')
        c = conn.cursor()
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()
        c.execute("INSERT INTO users VALUES (?, ?, 'user')", (username, hashed_pw))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def login_user(username, password):
    conn = sqlite3.connect('ksr_network.db')
    c = conn.cursor()
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    c.execute("SELECT role FROM users WHERE username = ? AND password = ?", (username, hashed_pw))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None
