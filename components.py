import streamlit.components.v1 as components

def render_speed_test_ui(L):
    # 使用 Python replace 避開 {} 衝突，並加入畫布繪圖腳本
    html_template = """
    <div style="background: #161B22; padding: 15px; border-radius: 10px; border: 1px solid #30363D; color: white; font-family: sans-serif;">
        <div id="res" style="color: #00f2ff; font-family: monospace; font-size: 20px; text-align: center; padding: 10px; background: #0d1117; border-radius: 8px; margin-bottom: 12px; border: 1px solid #30363D; box-shadow: inset 0 0 10px rgba(0,242,255,0.1);">
            WAIT_TEXT
        </div>
        
        <canvas id="liveChart" height="100" style="width: 100%; background: #0d1117; border-radius: 5px; margin-bottom: 12px;"></canvas>
        
        <button id="btn" onclick="run()" style="width: 100%; padding: 12px; background: #00f2ff; color: black; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; transition: 0.3s;">
            BTN_TEXT
        </button>
    </div>

    <script>
    // --- 即時波形繪製邏輯 (永不閃爍) ---
    const canvas = document.getElementById('liveChart');
    const ctx = canvas.getContext('2d');
    let points = Array(60).fill(30); // 初始點數

    function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // 繪製背景網格
        ctx.strokeStyle = '#1b222b';
        ctx.lineWidth = 1;
        for(let i=0; i<canvas.height; i+=20) {
            ctx.beginPath(); ctx.moveTo(0, i); ctx.lineTo(canvas.width, i); ctx.stroke();
        }

        // 繪製波形
        ctx.beginPath();
        ctx.strokeStyle = '#00f2ff';
        ctx.lineWidth = 2;
        ctx.lineJoin = 'round';
        
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
        const grad = ctx.createLinearGradient(0, 0, 0, canvas.height);
        grad.addColorStop(0, 'rgba(0, 242, 255, 0.2)');
        grad.addColorStop(1, 'rgba(0, 242, 255, 0)');
        ctx.fillStyle = grad;
        ctx.fill();

        // 模擬動態數據更新
        points.shift();
        let lastVal = points[points.length-1];
        let newVal = lastVal + (Math.random() * 10 - 5);
        if(newVal < 10) newVal = 10; if(newVal > 90) newVal = 90;
        points.push(newVal);

        requestAnimationFrame(draw);
    }
    draw(); // 啟動動畫

    // --- 原有測速邏輯 ---
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
    
    return components.html(ready_html, height=280) # 增加高度以容納畫布
