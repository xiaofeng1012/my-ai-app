import streamlit.components.v1 as components

def render_speed_test_ui(L):
    # 使用 Python replace 避開 {} 衝突
    html_template = """
    <div style="background: #161B22; padding: 15px; border-radius: 10px; border: 1px solid #30363D; color: white; font-family: sans-serif;">
        <div id="res" style="color: #00f2ff; font-family: monospace; font-size: 20px; text-align: center; padding: 10px; background: #0d1117; border-radius: 8px; margin-bottom: 12px; border: 1px solid #30363D;">
            WAIT_TEXT
        </div>
        
        <canvas id="liveChart" height="100" style="width: 100%; background: #0d1117; border-radius: 5px; margin-bottom: 12px; border: 1px solid #1b222b;"></canvas>
        
        <button id="btn" onclick="run()" style="width: 100%; padding: 12px; background: #00f2ff; color: black; border: none; border-radius: 5px; font-weight: bold; cursor: pointer;">
            BTN_TEXT
        </button>
    </div>

    <script>
    // --- JavaScript 即時繪圖 (完全獨立於 Python 刷新之外) ---
    const canvas = document.getElementById('liveChart');
    const ctx = canvas.getContext('2d');
    let points = Array(50).fill(40); 

    function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // 畫波形
        ctx.beginPath();
        ctx.strokeStyle = '#00f2ff';
        ctx.lineWidth = 2;
        let xStep = canvas.width / (points.length - 1);
        for(let i=0; i<points.length; i++) {
            let x = i * xStep;
            let y = canvas.height - (points[i] / 100 * canvas.height);
            if(i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        ctx.stroke();

        // 漸層填充
        ctx.lineTo(canvas.width, canvas.height);
        ctx.lineTo(0, canvas.height);
        ctx.fillStyle = 'rgba(0, 242, 255, 0.1)';
        ctx.fill();

        // 模擬數據微幅跳動
        points.shift();
        let newVal = points[points.length-1] + (Math.random() * 8 - 4);
        if(newVal < 20) newVal = 20; if(newVal > 80) newVal = 80;
        points.push(newVal);

        requestAnimationFrame(draw);
    }
    draw();

    // --- 測速通訊邏輯 ---
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
            window.parent.postMessage({
                isStreamlitMessage: true,
                type: "streamlit:setComponentValue",
                value: JSON.stringify({ "mbps": mbps, "ts": new Date().getTime() })
            }, "*");
            btn.disabled = false;
        } catch (e) { res.innerText = "ERROR"; btn.disabled = false; }
    }
    </script>
    """
    ready_html = html_template.replace("WAIT_TEXT", L['speed_wait'])\
                               .replace("BTN_TEXT", L['speed_btn'])\
                               .replace("TESTING_TEXT", L['speed_testing'])
    return components.html(ready_html, height=280)
