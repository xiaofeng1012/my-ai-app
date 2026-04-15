# database.py
import sqlite3
import pandas as pd
from datetime import datetime, timezone, timedelta

def init_db():
    conn = sqlite3.connect('ksr_network.db')
    c = conn.cursor()
    # 使用者表
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)')
    # 🔥 關鍵：測速紀錄表，增加 id 作為唯一標記
    c.execute('''CREATE TABLE IF NOT EXISTS speed_logs 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  user TEXT, 
                  time TEXT, 
                  speed REAL, 
                  status TEXT)''')
    conn.commit()
    conn.close()

def add_speed_record(user, speed):
    conn = sqlite3.connect('ksr_network.db')
    c = conn.cursor()
    now = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO speed_logs (user, time, speed, status) VALUES (?, ?, ?, ?)",
              (user, now, speed, "Success ✅"))
    conn.commit()
    conn.close()

def get_user_logs(user):
    conn = sqlite3.connect('ksr_network.db')
    # 這裡過濾使用者，確保資料分開
    df = pd.read_sql_query("SELECT time as Timestamp, speed as 'Mbps (RTT)', status as Status FROM speed_logs WHERE user = ? ORDER BY id DESC", 
                           conn, params=(user,))
    conn.close()
    return df
