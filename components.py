# components.py
import streamlit.components.v1 as components
import json

def render_speed_test_ui(L):
    # 使用 Python 的 replace 避開 f-string 與 JS 括號的衝突
    html_template = """
    <div style="background: #161B22; padding: 10px; border-radius: 10px; border: 1px solid #30363D; color: white;">
        <div id="res" style="color: #00f2ff; font-family: monospace; font-size: 18px; text-align: center; padding: 12px; background: #0d1117; border-radius: 8px; margin-bottom: 10px;">
            WAIT_TEXT
        </div>
        <button id="btn" onclick="run()" style="width: 100%; padding: 12px; background: #00f2ff; color: black; border: none; border-radius: 5px; font-weight: bold; cursor: pointer;">
            BTN_TEXT
        </button>
    </div>

    <script>
    async function run() {
        const res = document.getElementById('res');
        const btn = document.getElementById('btn');
        btn.disabled = true;
        res.innerText = "TESTING_TEXT";
        const start = new Date().getTime();
        try {
            const resp = await fetch('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv?n=' + start);
            const reader = resp.body.getReader();
            let received = 0;
            while(true) {
                const {done, value} = await reader.read();
                if (done) break;
                received += value.length;
            }
            const dur = (new Date().getTime() - start) / 1000;
            const mbps = ((received * 8) / dur / 1000000).toFixed(2);
            res.innerText = mbps + " Mbps";
            
            // 🔥 傳送 JSON 給 Python
            window.parent.postMessage({
                isStreamlitMessage: true,
                type: "streamlit:setComponentValue",
                value: JSON.stringify({ "val": mbps, "ts": new Date().getTime() })
            }, "*");
            btn.disabled = false;
        } catch (e) { res.innerText = "ERROR"; btn.disabled = false; }
    }
    </script>
    """
    # 手動替換語系，避開 f-string 錯誤
    ready_html = html_template.replace("WAIT_TEXT", L['speed_wait'])\
                               .replace("BTN_TEXT", L['speed_btn'])\
                               .replace("TESTING_TEXT", L['speed_testing'])
    
    return components.html(ready_html, height=160)
