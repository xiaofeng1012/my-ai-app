# database.py
import sqlite3
import hashlib
import pandas as pd

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

# 🔥 新增：儲存紀錄
def add_record(username, rtt, jitter, status):
    conn = sqlite3.connect('ksr_network.db')
    c = conn.cursor()
    now = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO test_records (username, timestamp, rtt, jitter, status) VALUES (?, ?, ?, ?, ?)",
              (username, now, rtt, jitter, status))
    conn.commit()
    conn.close()

# 🔥 新增：讀取紀錄 (User 看自己, Admin 看全部)
def get_records(username=None):
    conn = sqlite3.connect('ksr_network.db')
    if username and username != "Admin":
        df = pd.read_sql_query("SELECT timestamp, rtt, jitter, status FROM test_records WHERE username=?", conn, params=(username,))
    else:
        df = pd.read_sql_query("SELECT * FROM test_records", conn)
    conn.close()
    return df

# 🔥 新增：清理紀錄 (僅限 Admin)
def clear_all_records():
    conn = sqlite3.connect('ksr_network.db')
    c = conn.cursor()
    c.execute("DELETE FROM test_records")
    conn.commit()
    conn.close()
