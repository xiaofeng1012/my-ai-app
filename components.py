import streamlit.components.v1 as components

def render_speed_test_ui(L):
    html_template = """
    <style>
        .speed-container {
            background: #161B22; padding: 15px; border-radius: 10px; 
            border: 1px solid #30363D; color: white; font-family: sans-serif;
            text-align: center;
        }
        #res {
            color: #00f2ff; font-family: 'JetBrains Mono', monospace; font-size: 24px; 
            padding: 15px; background: #0d1117; border-radius: 8px; 
            margin-bottom: 12px; border: 1px solid #30363D; min-height: 40px;
        }
        .ksr-btn {
            width: 100%; padding: 12px; border: none; border-radius: 5px; 
            font-weight: bold; cursor: pointer; transition: 0.3s; margin-top: 5px;
        }
        #test-btn { background: #00f2ff; color: black; }
        #save-btn { background: #238636; color: white; display: none; } /* 初始隱藏 */
        .loader {
            border: 3px solid #161b22; border-top: 3px solid #00f2ff;
            border-radius: 50%; width: 18px; height: 18px;
            animation: spin 1s linear infinite; display: inline-block;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>

    <div class="speed-container">
        <div id="res"><span id="status_text">WAIT_MSG</span></div>
        <button id="test-btn" class="ksr-btn" onclick="runTest()">BTN_MSG</button>
        <button id="save-btn" class="ksr-btn" onclick="saveData()">💾 儲存測試結果</button>
    </div>

    <script>
    let currentMbps = 0;

    async function runTest() {
        const statusText = document.getElementById('status_text');
        const tBtn = document.getElementById('test-btn');
        const sBtn = document.getElementById('save-btn');
        
        tBtn.disabled = true;
        tBtn.style.opacity = "0.5";
        sBtn.style.display = "none";
        statusText.innerHTML = '<div class="loader"></div> TESTING_MSG';

        try {
            const start = new Date().getTime();
            const resp = await fetch('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv?n=' + start);
            const reader = resp.body.getReader();
            let received = 0;
            while(true) {
                const {done, value} = await reader.read();
                if (done) break;
                received += value.length;
            }
            const dur = (new Date().getTime() - start) / 1000;
            currentMbps = ((received * 8) / dur / 1000000).toFixed(2);
            
            statusText.innerText = currentMbps + " Mbps";
            tBtn.disabled = false;
            tBtn.style.opacity = "1";
            tBtn.innerText = "重新測試";
            sBtn.style.display = "block"; // 顯示儲存按鈕
        } catch (e) {
            statusText.innerText = "Error";
            tBtn.disabled = false;
        }
    }

    function saveData() {
        const sBtn = document.getElementById('save-btn');
        sBtn.disabled = true;
        sBtn.innerText = "傳送中...";
        
        // 將數據傳回 Python
        window.parent.postMessage({
            isStreamlitMessage: true,
            type: "streamlit:setComponentValue",
            value: JSON.stringify({ 
                "mbps": currentMbps, 
                "ts": new Date().getTime(), 
                "action": "save" 
            })
        }, "*");
    }
    </script>
    """
    return components.html(
        html_template.replace("WAIT_MSG", L['speed_wait'])
                     .replace("BTN_MSG", L['speed_btn'])
                     .replace("TESTING_MSG", L['speed_testing']), 
        height=220
    )
