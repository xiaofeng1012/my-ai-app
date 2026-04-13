import requests
import random
import hashlib
from datetime import datetime

def get_location(ip_addr):
    try:
        r = requests.get(f"http://ip-api.com/json/{ip_addr}", timeout=5).json()
        return r if r['status'] == 'success' else None
    except:
        return None

def get_device_info(user_agent):
    if "Windows" in user_agent: return "💻", "Windows"
    if "iPhone" in user_agent: return "🍎", "iPhone"
    return "📱", "Mobile"