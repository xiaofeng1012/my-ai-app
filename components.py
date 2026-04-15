# components.py
import streamlit.components.v1 as components

def render_speed_test_ui(L):
    # 注意：在 Python 的 f-string 中，JS 需要的大括號必須寫兩次 {{ }} 才能正確輸出
    js_code = f"""
    <div style="background: #161B22; padding: 10px; border-radius: 10px; border: 1px solid #30363D; color: white; font-family: sans-serif;">
        <div id="speed-result" style="color: #00f2ff; font-family: monospace; font-size: 18px; font-weight: bold; text-align: center; padding: 12px; border: 1px solid #30363D; border-radius: 8px; background: #0d1117; margin-bottom: 10px;">
            {L['speed_wait']}
        </div>
        <button id="s-btn" onclick="runTest()" style="width: 100%; padding: 12px; background: #00f2ff; color: black; border: none; border-radius: 5px; font-weight: bold; cursor: pointer;">
            {L['speed_btn']}
        </button>
    </div>

    <script>
    async function runTest() {{
        const res = document.getElementById('speed-result');
        const btn = document.getElementById('s-btn');
        btn.disabled = true;
        res.innerText = "{L['speed_testing']}";
        const start = new Date().getTime();
        try {{
            // 透過獲取 GitHub 上的 CSV 檔案來計算下載速度
            const resp = await fetch('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv?n=' + start);
            const reader = resp.body.getReader();
            let received = 0;
            while(true) {{
                const {{done, value}} = await reader.read();
                if (done) break;
                received += value.length;
            }}
            const dur = (new Date().getTime() - start) / 1000;
            const mbps = ((received * 8) / dur / 1000000).toFixed(2);
            res.innerText = mbps + " Mbps";
            
            // 🔥 傳回 JSON 物件給 Python，包含時間戳記(ts)確保每次都是新數據
            window.parent.postMessage({{
                isStreamlitMessage: true,
                type: "streamlit:setComponentValue",
                value: JSON.stringify({{ "mbps": mbps, "ts": new Date().getTime() }})
            }}, "*");
            
            btn.disabled = false;
        }} catch (e) {{ 
            res.innerText = "ERROR"; 
            btn.disabled = false; 
        }}
    }}
    </script>
    """
    return components.html(js_code, height=160)
