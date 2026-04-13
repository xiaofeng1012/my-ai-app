# components.py
import streamlit.components.v1 as components

def render_speed_test_ui(L):
    # 這裡處理 JS 轉義大括號問題
    js_code = f"""
    <div id="speed-result" style="color: #00f2ff; font-family: monospace; font-size: 18px; font-weight: bold; text-align: center; padding: 12px; border: 1px solid #30363D; border-radius: 8px; background: #0d1117;">
        {L['speed_wait']}
    </div>
    <button onclick="runSpeedTest()" style="width: 100%; margin-top: 8px; padding: 10px; background: #00f2ff; color: black; border: none; border-radius: 5px; font-weight: bold; cursor: pointer;">
        {L['speed_btn']}
    </button>
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
        }} catch (e) {{ display.innerText = "ERROR"; }}
    }}
    </script>
    """
    return components.html(js_code, height=140)
