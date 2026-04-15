# database.py
import sqlite3
import hashlib
import pandas as pd
from datetime import datetime, timezone, timedelta

def init_db():
    conn = sqlite3.connect('ksr_network.db')
    c = conn.cursor()
    # 建立使用者表
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT, role TEXT)''')
    
    # 🔥 重要：確保測速紀錄表在初始化時就建立
    c.execute('''CREATE TABLE IF NOT EXISTS test_records
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT, 
                  timestamp TEXT, 
                  rtt REAL, 
                  jitter REAL, 
                  status TEXT)''')
    
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

# 🔥 儲存紀錄 (已修正 datetime 錯誤)
def add_record(username, rtt, jitter, status):
    conn = sqlite3.connect('ksr_network.db')
    c = conn.cursor()
    # 獲取台北時間
    now = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO test_records (username, timestamp, rtt, jitter, status) VALUES (?, ?, ?, ?, ?)",
              (username, now, rtt, jitter, status))
    conn.commit()
    conn.close()

# 🔥 讀取紀錄 (已修正 Table 不存在導致的 DatabaseError)
def get_records(username=None):
    conn = sqlite3.connect('ksr_network.db')
    try:
        if username and username != "Admin":
            query = "SELECT timestamp, rtt, jitter, status FROM test_records WHERE username=?"
            df = pd.read_sql_query(query, conn, params=(username,))
        else:
            # Admin 可以看到是哪個帳號測速的
            query = "SELECT username, timestamp, rtt, jitter, status FROM test_records"
            df = pd.read_sql_query(query, conn)
    except Exception as e:
        # 如果表不存在，手動建立一個空的 DataFrame 回傳，防止前端崩潰
        cols = ["username", "timestamp", "rtt", "jitter", "status"]
        df = pd.DataFrame(columns=cols)
    finally:
        conn.close()
    return df

# 🔥 清理紀錄 (僅限 Admin)
def clear_all_records():
    conn = sqlite3.connect('ksr_network.db')
    c = conn.cursor()
    c.execute("DELETE FROM test_records")
    conn.commit()
    conn.close()
