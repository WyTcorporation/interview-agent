async function recordAndSend() {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mediaRecorder = new MediaRecorder(stream);
    const chunks = [];
    mediaRecorder.ondataavailable = e => chunks.push(e.data);
    mediaRecorder.onstop = async () => {
        const blob = new Blob(chunks, { type: 'audio/wav' });
        const formData = new FormData();
        formData.append('file', blob, 'recording.wav');
        const response = await fetch('/ask', {
            method: 'POST',
            body: formData
        });
        const result = await response.json();
        document.getElementById("question").textContent = result.question;
        document.getElementById("answer").textContent = result.answer;
        addToHistory(result.question, result.answer);
    };
    mediaRecorder.start();
    setTimeout(() => mediaRecorder.stop(), 3000);
}


function addToHistory(q, a) {
    const log = document.getElementById("chatlog");
    const div = document.createElement("div");
    div.className = "block";
    div.innerHTML = `<div class="q">Q: ${q}</div><div class="a">A: ${a}</div>`;
    log.prepend(div);
}

async function resetContext() {
    await fetch('/reset', { method: 'POST' });
    document.getElementById("chatlog").innerHTML = "";
}

async function loadHistory() {
    const res = await fetch('/history');
    const data = await res.json();
    const log = document.getElementById('log');
    log.innerHTML = '';
    data.forEach(entry => {
        const li = document.createElement('li');
        li.innerHTML = `<b>Q:</b> ${entry.question}<br><b>A:</b> ${entry.answer}`;
        log.appendChild(li);
    });
}
setInterval(loadHistory, 2000);