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

        const response = await fetch("/ask", {
            method: "POST",
            body: formData,
        });

        const data = await response.json();
        questionEl.innerText = data.question;
        answerEl.innerText = data.answer;

        currentHistory.push({question: data.question, answer: data.answer});
        updateHistory(currentHistory);
    });

    // 🎤 Кнопка запису
    recordBtn.addEventListener("mousedown", startRecording);
    recordBtn.addEventListener("mouseup", stopRecording);

    function startRecording() {
        navigator.mediaDevices.getUserMedia({audio: true}).then((stream) => {
            audioChunks = [];
            mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);
            mediaRecorder.onstop = sendRecording;
            mediaRecorder.start();
            recordBtn.innerText = "🎙️ Запис...";
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

        fetch("/ask", {
            method: "POST",
            body: formData,
        })
            .then((res) => res.json())
            .then((data) => {
                questionEl.innerText = data.question;
                answerEl.innerText = data.answer;
                if (ttsEnabled) speakText(data.answer);
                currentHistory.push({question: data.question, answer: data.answer});
                updateHistory(currentHistory);
            });
    }

    function updateHistory(history) {
        historyContainer.innerHTML = "";
        [...history].reverse().forEach((entry) => {
            const block = document.createElement("div");
            block.classList.add("history-entry");
            block.innerHTML = `
        <div><strong>Q:</strong> ${entry.question}</div>
        <div><strong>A:</strong> ${entry.answer}</div>
      `;
            historyContainer.appendChild(block);
        });
        historyContainer.scrollTop = historyContainer.scrollHeight;
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

    const ttsBtn = document.getElementById("tts-toggle-btn");
    ttsBtn.addEventListener("click", () => {
        ttsEnabled = !ttsEnabled;
        ttsBtn.textContent = ttsEnabled ? "🔈 Не озвучувати" : "🔊 Озвучити";
        // speakTextVoices();
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
        console.log(voice);
        const utterance = new SpeechSynthesisUtterance(text);

        utterance.voice = voice;
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        window.speechSynthesis.speak(utterance);
    }


});

