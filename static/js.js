document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("upload-form");
    const fileInput = document.getElementById("audio");
    const questionEl = document.getElementById("question-text");
    const answerEl = document.getElementById("answer-text");
    const historyContainer = document.getElementById("history-list");
    const resetBtn = document.getElementById("reset-btn");
    const recordBtn = document.getElementById("record-btn");

    let mediaRecorder;
    let audioChunks = [];
    let currentHistory = [];

    function renderAnswerMarkdown(rawText) {
        const answerHtml = marked.parse(rawText || "");
        answerEl.innerHTML = `<div class="rendered-answer">${answerHtml}</div>`;
        if (typeof hljs !== "undefined") {
            answerEl.querySelectorAll("pre code").forEach((el) => {
                hljs.highlightElement(el);
            });
        }
    }

    // Завантажити історію при старті
    fetch("/history")
        .then((res) => res.json())
        .then((history) => {
            currentHistory = history;
            updateHistory(currentHistory);
        });

    resetBtn.addEventListener("click", () => {
        fetch("/reset", {method: "POST"})
            .then((res) => res.json())
            .then(() => {
                questionEl.innerText = "";
                answerEl.innerText = "";
                currentHistory = [];
                updateHistory([]);
            });
    });

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        if (!fileInput.files.length) {
            questionEl.innerText = "";
            answerEl.innerText = "⚠️ Оберіть аудіофайл!";
            return;
        }


        const formData = new FormData();
        formData.append("file", fileInput.files[0]);

        questionEl.innerText = "⌛ Обробка...";
        answerEl.innerText = "";

        const response = await fetch("/ask/file", {
            method: "POST",
            body: formData,
        });

        const data = await response.json();
        questionEl.innerText = data.question;
        renderAnswerMarkdown(data.answer);

        currentHistory.push({question: data.question, answer: data.answer});
        updateHistory(currentHistory);
    });

    // 🎤 Кнопка запису
    recordBtn.addEventListener("mousedown", startRecording);
    recordBtn.addEventListener("mouseup", stopRecording);

    function startRecording() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            answerEl.innerText = "⚠️ Браузер не підтримує мікрофон або доступ заборонено.";
            return;
        }

        navigator.mediaDevices.getUserMedia({audio: true}).then((stream) => {
            audioChunks = [];
            mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);
            mediaRecorder.onstop = sendRecording;
            mediaRecorder.start();
            recordBtn.innerText = "🎙️ Запис...";
        }).catch((err) => {
            answerEl.innerText = "❌ Доступ до мікрофона заборонено.";
            console.error("getUserMedia error:", err);
        });
    }

    function stopRecording() {
        mediaRecorder.stop();
        recordBtn.innerText = "🎤 Запис";
    }

    function sendRecording() {
        const audioBlob = new Blob(audioChunks, {type: "audio/webm"});
        const formData = new FormData();
        formData.append("file", audioBlob, "recording.webm");

        if (audioBlob.size < 1128) {
            answerEl.innerText = "⚠️ Аудіо занадто коротке або порожнє!";
            return;
        }

        questionEl.innerText = "⌛ Обробка...";
        answerEl.innerText = "";

        fetch("/ask/audio", {
            method: "POST",
            body: formData,
        })
            .then((res) => res.json())
            .then((data) => {
                questionEl.innerText = data.question;
                renderAnswerMarkdown(data.answer);
                if (ttsEnabled) speakText(data.answer);
                currentHistory.push({question: data.question, answer: data.answer});
                updateHistory(currentHistory);
            });
    }

    function updateHistory(history) {
        historyContainer.innerHTML = "";
        [...history].reverse().forEach((entry) => {
            const block = document.createElement("div");
            const answerHtml = marked.parse(entry.answer || "");
            block.classList.add("history-entry");
            block.innerHTML = `
          <div><strong>Q:</strong> ${entry.question}</div>
          <div><strong>A:</strong><div class="rendered-answer">${answerHtml}</div></div>
        `;
             if (typeof hljs !== "undefined") {
                 block.querySelectorAll("pre code").forEach((el) => {
                     hljs.highlightElement(el);
                 });
             }
            historyContainer.appendChild(block);
        });
    }


    const toggleBtn = document.getElementById("theme-toggle");

    const theme = localStorage.getItem("theme");
    if (theme === "dark") {
        document.documentElement.classList.add("dark");
        toggleBtn.textContent = "🌞";
    }

    toggleBtn.addEventListener("click", () => {
        const isDark = document.documentElement.classList.toggle("dark");
        localStorage.setItem("theme", isDark ? "dark" : "light");
        toggleBtn.textContent = isDark ? "🌞" : "🌙";
    });


    function speakTextVoices() {
        window.speechSynthesis.getVoices().forEach(v => console.log(v.lang, v.name));
    }

    let ttsEnabled = false;
    let selectedLang = "en-US";

    const langSelect = document.getElementById("voice-lang-select");
    langSelect.addEventListener("change", () => {
        selectedLang = langSelect.value;
        localStorage.setItem("ttsLang", selectedLang); // зберігаємо в локалсторедж
    });

    if (localStorage.getItem("ttsLang")) {
        selectedLang = localStorage.getItem("ttsLang");
        langSelect.value = selectedLang;
    }

    const repeatBtn = document.getElementById("repeat-tts-btn");
    let lastAnswerSpoken = "";

    const ttsBtn = document.getElementById("tts-toggle-btn");

    ttsBtn.addEventListener("click", () => {
        ttsEnabled = !ttsEnabled;
        ttsBtn.textContent = ttsEnabled ? "🔈 Не озвучувати" : "🔊 Озвучити";
        repeatBtn.style.display = ttsEnabled ? "inline-block" : "none";

        // speakTextVoices();
    });

    repeatBtn.addEventListener("click", () => {
        if (lastAnswerSpoken) speakText(lastAnswerSpoken);
    });

    async function getVoice(preferredLang) {
        return new Promise((resolve) => {
            const fallbackLang = "en-US";
            const pickVoice = () => {
                const voices = speechSynthesis.getVoices();
                let voice = voices.find(v => v.lang === preferredLang);
                if (!voice) {
                    console.warn(`⚠️ Голос ${preferredLang} не знайдено. Використовую ${fallbackLang}`);
                    alert(`⚠️ Голос ${preferredLang} не знайдено. Використовую ${fallbackLang}`);
                    voice = voices.find(v => v.lang === fallbackLang) || voices[0];
                }
                resolve(voice);
            };
            if (speechSynthesis.getVoices().length) pickVoice();
            else speechSynthesis.onvoiceschanged = pickVoice;
        });
    }

    async function speakText(text) {
        const voice = await getVoice(selectedLang);
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.voice = voice;
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        window.speechSynthesis.speak(utterance);
        lastAnswerSpoken = text;
    }

    const sendTextBtn = document.getElementById("send-text-btn");
    const manualInput = document.getElementById("manual-question");

    sendTextBtn.addEventListener("click", async () => {
        const text = manualInput.value.trim();
        if (!text) return;

        questionEl.innerText = text;
        answerEl.innerText = "⌛ Обробка...";

        const response = await fetch("/ask/text", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({text})
        });

        const data = await response.json();
        renderAnswerMarkdown(data.answer);
        if (ttsEnabled) await speakText(data.answer);

        currentHistory.push({question: text, answer: data.answer});
        updateHistory(currentHistory);

        manualInput.value = "";
    });


    const listenerBtn = document.getElementById("listener-toggle-btn");
    let listenerProcess = null;
    let isListenerRunning = false;
    let listenerHistoryInterval = null;


    function loadHistory() {
        fetch("/history")
            .then(res => res.json())
            .then((history) => {
                currentHistory = history;
                updateHistory(currentHistory);
            });
    }

    listenerBtn.addEventListener("click", async () => {
        if (!isListenerRunning) {
            // Запуск listener через бекенд
            const res = await fetch("/listener/start", {method: "POST"});
            const data = await res.json();
            if (data.status === "started") {
                isListenerRunning = true;
                listenerBtn.textContent = "🟥 Зупинити Listener";
                listenerHistoryInterval = setInterval(loadHistory, 3000);
            } else {
                alert("⚠️ Не вдалося запустити listener");
            }
        } else {
            // Зупинка listener
            const res = await fetch("/listener/stop", {method: "POST"});
            const data = await res.json();
            if (data.status === "stopped") {
                isListenerRunning = false;
                listenerBtn.textContent = "🎧 Запустити Listener";
                // 🛑 Зупиняємо інтервал
                if (listenerHistoryInterval) {
                    clearInterval(listenerHistoryInterval);
                    listenerHistoryInterval = null;
                }

                // Завантажити остаточну історію
                loadHistory();
            } else {
                alert("⚠️ Не вдалося зупинити listener");
            }
        }
    });

    const screenBtn = document.getElementById("screen-analyze-btn");

    screenBtn.addEventListener("click", async () => {
        const res = await fetch("/screen/run", {
            method: "POST"
        });

        if (res.ok) {
            // почекаємо кілька секунд, поки screen.py зробить свій запит
            setTimeout(loadHistory, 30000);
        } else {
            alert("❌ Не вдалося запустити screen.py");
        }
    });

    const modeSelect = document.getElementById("mode-select");
    modeSelect.addEventListener("change", async () => {
        const mode = modeSelect.value;

        const res = await fetch("/mode", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(mode)
        });

        if (res.ok) {
            console.log("✅ Режим змінено:", mode);
        } else {
            alert("❌ Не вдалося змінити режим");
        }
    });

    const micBtn = document.getElementById("mic-listener-toggle-btn");
    let isMicRunning = false;
    let micInterval = null;

    micBtn.addEventListener("click", async () => {
        if (!isMicRunning) {
            const res = await fetch("/mic/start", {method: "POST"});
            const data = await res.json();
            if (data.status === "started") {
                isMicRunning = true;
                micBtn.textContent = "🟥 Зупинити мікрофон";
                micInterval = setInterval(loadHistory, 3000);
            } else {
                alert("❌ Не вдалося запустити mic_listener");
            }
        } else {
            const res = await fetch("/mic/stop", {method: "POST"});
            const data = await res.json();
            if (data.status === "stopped") {
                isMicRunning = false;
                micBtn.textContent = "🎙️ Live з мікрофона";
                clearInterval(micInterval);
            } else {
                alert("❌ Не вдалося зупинити mic_listener");
            }
        }
    });

    document.getElementById("overlay-btn").addEventListener("click", async () => {
        const res = await fetch("/overlay", {method: "POST"});
        if (res.ok) {
            console.log("🪟 Overlay запущено");
        } else {
            // alert("❌ Не вдалося запустити overlay");
            console.log("❌ Не вдалося запустити overlay");
        }
    });

    document.getElementById("overlay-listener-btn").addEventListener("click", async () => {
        const res = await fetch("/overlay/listener", {method: "POST"});
        if (res.ok) {
            console.log("🪟 Overlay Listener запущено");
        } else {
            alert("❌ Не вдалося запустити overlay");
        }
    });

    setInterval(() => {
        fetch("/history")
            .then(res => res.json())
            .then((history) => {
                // Якщо нова історія відрізняється — оновити
                if (JSON.stringify(history) !== JSON.stringify(currentHistory)) {
                    currentHistory = history;
                    updateHistory(currentHistory);
                }
            });
    }, 3000); // кожні 3 секунди
});

