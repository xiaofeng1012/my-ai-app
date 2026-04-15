# components.py
import streamlit.components.v1 as components

def render_speed_test_ui(L):
    js_code = f"""
    <div style="background: #161B22; padding: 10px; border-radius: 10px; border: 1px solid #30363D; color: white; font-family: sans-serif;">
        <div id="speed-result" style="color: #00f2ff; font-family: monospace; font-size: 18px; font-weight: bold; text-align: center; padding: 12px; border: 1px solid #30363D; border-radius: 8px; background: #0d1117; margin-bottom: 10px;">
            {L['speed_wait']}
        </div>
        <button id="btn" onclick="runSpeedTest()" style="width: 100%; padding: 12px; background: #00f2ff; color: black; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; font-size: 14px; display: block;">
            {L['speed_btn']}
        </button>
    </div>

    <script>
    async function runSpeedTest() {{
        const display = document.getElementById('speed-result');
        const btn = document.getElementById('btn');
        btn.disabled = true; // 防止重複點擊
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
            const mbps = ((received * 8) / duration / 1000000).toFixed(2);
            display.innerText = mbps + " Mbps";
            
            // 🔥 關鍵核心：將數據傳回 Streamlit
            // 我們把 Mbps 數值透過 URL 的 Hash 或是自定義事件傳遞是不行的
            // 最穩定的做法是用 Streamlit 提供的組件通訊協定
            window.parent.postMessage({{
                isStreamlitMessage: true,
                type: "streamlit:setComponentValue",
                value: mbps
            }}, "*");
            
            btn.disabled = false;
        }} catch (e) {{ 
            display.innerText = "ERROR"; 
            btn.disabled = false;
        }}
    }}
    </script>
    """
    # 這裡回傳組件，讓我們在 main.py 接收
    return components.html(js_code, height=160, scrolling=False)
