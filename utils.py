# utils.py
import io
import pandas as pd
from datetime import datetime

def generate_csv_report(df, sys_hash, display_id, team_name_en):
    output = io.StringIO()
    output.write(f"--- KSR AUDIT REPORT ---\n")
    output.write(f"Issued by: {team_name_en}\n")
    output.write(f"System Hash: {sys_hash}\n")
    output.write(f"Device ID: {display_id}\n")
    output.write(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    output.write(f"------------------------\n\n")
    
    # 轉換英文表頭
    df_export = df.rename(columns={"time":"Timestamp","ms":"Latency_ms"})
    df_export.to_csv(output, index=False)
    return output.getvalue()
