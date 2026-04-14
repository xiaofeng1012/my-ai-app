# components.py
import streamlit as st

def render_speed_test_ui(L):
    js_code = f"""
    <div style="background: #161B22; padding: 10px; border-radius: 10px; border: 1px solid #30363D; color: white; font-family: sans-serif;">
        <div id="speed-result" style="color: #00f2ff; font-family: monospace; font-size: 18px; font-weight: bold; text-align: center; padding: 12px; border: 1px solid #30363D; border-radius: 8px; background: #0d1117; margin-bottom: 10px;">
            {L['speed_wait']}
        </div>
        <button onclick="runSpeedTest()" style="width: 100%; padding: 12px; background: #00f2ff; color: black; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; font-size: 14px; display: block;">
            {L['speed_btn']}
        </button>
    </div>

    <script>
    async function runSpeedTest() {{
        const display = document.getElementById('speed-result');
        display.innerText = "{L['speed_testing']}";
        const startTime = new Date().getTime();
        try {{
            const response = await fetch('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv?n=' + startTime);
            const reader = response.body.getReader();
            let received = 0;
            while(true) {{
                const {{done, value}} = await reader.read();
                if (done) break;
                received += value.length;
            }}
            const duration = (new Date().getTime() - startTime) / 1000;
            display.innerText = ((received * 8) / duration / 1000000).toFixed(2) + " Mbps";
        }} catch (e) {{ 
            display.innerText = "ERROR"; 
        }}
    }}
    </script>
    """
    # 根據 2026 新規範，使用 st.iframe 並設定 width='stretch'
    return st.iframe(srcdoc=js_code, height=180, width='stretch')
