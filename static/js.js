document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("form");
  const fileInput = document.getElementById("audio");
  const result = document.getElementById("result");
  const historyContainer = document.getElementById("history");
  const resetBtn = document.getElementById("reset-context");

  // Завантажити історію при старті
  fetch("/history")
    .then((res) => res.json())
    .then((history) => {
      updateHistory(history);
    });

  // Очистити історію
  resetBtn.addEventListener("click", () => {
    fetch("/reset", { method: "POST" })
      .then((res) => res.json())
      .then(() => {
        result.innerText = "Контекст очищено.";
        updateHistory([]);
      });
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    result.innerText = "⌛ Обробка...";

    const response = await fetch("/ask", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    result.innerHTML = `
      <div><strong>Q:</strong> ${data.question}</div>
      <div><strong>A:</strong> ${data.answer}</div>
    `;

    // Додати до історії
    fetch("/history")
      .then((res) => res.json())
      .then((history) => {
        updateHistory(history);
      });
  });

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
  }
});
