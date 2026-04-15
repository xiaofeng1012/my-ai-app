# database.py
import sqlite3
import hashlib
import pandas as pd
from datetime import datetime, timezone, timedelta

def init_db():
    conn = sqlite3.connect('ksr_network.db')
    c = conn.cursor()
    # 使用者表
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT, role TEXT)''')
    # 測速紀錄表 (統一使用這個結構)
    c.execute('''CREATE TABLE IF NOT EXISTS test_records
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT, timestamp TEXT, rtt REAL, jitter REAL, status TEXT)''')
    
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

def add_record(username, rtt, jitter, status):
    conn = sqlite3.connect('ksr_network.db')
    c = conn.cursor()
    now = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO test_records (username, timestamp, rtt, jitter, status) VALUES (?, ?, ?, ?, ?)",
              (username, now, rtt, jitter, status))
    conn.commit()
    conn.close()

def get_records(username=None):
    conn = sqlite3.connect('ksr_network.db')
    try:
        if username and username != "Admin":
            # 關鍵：針對一般使用者，只抓取他個人的資料
            df = pd.read_sql_query("SELECT timestamp as '時間', rtt as 'Mbps', status as '狀態' FROM test_records WHERE username=? ORDER BY id DESC", 
                                   conn, params=(username,))
        else:
            # 管理員看全部
            df = pd.read_sql_query("SELECT username as '使用者', timestamp as '時間', rtt as 'Mbps', status as '狀態' FROM test_records ORDER BY id DESC", conn)
    except:
        df = pd.DataFrame()
    finally:
        conn.close()
    return df

def clear_all_records():
    conn = sqlite3.connect('ksr_network.db')
    c = conn.cursor()
    c.execute("DELETE FROM test_records")
    conn.commit()
    conn.close()
