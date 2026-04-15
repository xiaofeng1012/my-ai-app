import streamlit.components.v1 as components

def render_speed_test_ui(L):
    html_template = """
    <div style="background: #161B22; padding: 15px; border-radius: 10px; border: 1px solid #30363D; color: white; font-family: sans-serif;">
        <div id="res" style="color: #00f2ff; font-family: monospace; font-size: 20px; text-align: center; padding: 15px; background: #0d1117; border-radius: 8px; margin-bottom: 12px; border: 1px solid #30363D;">
            <span id="status_text">WAIT_MSG</span>
        </div>
        
        <button id="btn" onclick="run()" style="width: 100%; padding: 12px; background: #00f2ff; color: black; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; transition: 0.3s;">
            BTN_MSG
        </button>
    </div>

    <script>
    async function run() {
        const resBox = document.getElementById('res');
        const statusText = document.getElementById('status_text');
        const btn = document.getElementById('btn');
        
        // 1. 進入讀取狀態
        btn.disabled = true;
        btn.style.opacity = "0.5";
        btn.style.cursor = "not-allowed";
        // 顯示旋轉讀取動畫 (CSS 原生實現)
        statusText.innerHTML = '<div class="loader"></div> TESTING_MSG';
        
        // 加入簡單的 Loader 樣式
        const style = document.createElement('style');
        style.innerHTML = `
            .loader {
                border: 3px solid #161b22;
                border-top: 3px solid #00f2ff;
                border-radius: 50%;
                width: 18px;
                height: 18px;
                animation: spin 1s linear infinite;
                display: inline-block;
                margin-right: 10px;
                vertical-align: middle;
            }
            @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        `;
        document.head.appendChild(style);

        const start = new Date().getTime();
        try {
            // 模擬測速下載
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
            
            // 2. 顯示結果並傳送給 Python
            statusText.innerText = mbps + " Mbps";
            
            window.parent.postMessage({
                isStreamlitMessage: true,
                type: "streamlit:setComponentValue",
                value: JSON.stringify({ "mbps": mbps, "ts": new Date().getTime(), "status": "done" })
            }, "*");

            // 保持按鈕鎖定一小段時間，等待 Python 重整
            setTimeout(() => {
                btn.disabled = false;
                btn.style.opacity = "1";
                btn.style.cursor = "pointer";
            }, 2000);

        } catch (e) { 
            statusText.innerText = "Error"; 
            btn.disabled = false; 
            btn.style.opacity = "1";
        }
    }
    </script>
    """
    return components.html(
        html_template.replace("WAIT_MSG", L['speed_wait'])
                     .replace("BTN_MSG", L['speed_btn'])
                     .replace("TESTING_MSG", L['speed_testing']), 
        height=180
    )
