document.addEventListener("DOMContentLoaded", () => {
  const detector = new InfoLeakDetector();

  // 탭 전환
  const tabBtns = document.querySelectorAll(".tab-btn");
  const tabContents = document.querySelectorAll(".tab-content");

  tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      tabBtns.forEach((b) => b.classList.remove("active"));
      tabContents.forEach((c) => c.classList.remove("active"));

      btn.classList.add("active");
      document.getElementById(`${btn.dataset.tab}-tab`).classList.add("active");
    });
  });

  // 직접 입력 분석
  document.getElementById("analyze-btn").addEventListener("click", () => {
    const text = document.getElementById("input-text").value;
    const result = detector.analyze(text);
    displayResult(result);
  });

  // 페이지 스캔
  document.getElementById("scan-page-btn").addEventListener("click", () => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      chrome.tabs.sendMessage(
        tabs[0].id,
        { action: "scanPage" },
        (response) => {
          if (response && response.text) {
            const result = detector.analyze(response.text);
            displayResult(result);
          }
        }
      );
    });
  });

  // 선택 영역 스캔
  document
    .getElementById("scan-selection-btn")
    .addEventListener("click", () => {
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        chrome.tabs.sendMessage(
          tabs[0].id,
          { action: "scanSelection" },
          (response) => {
            if (response && response.text) {
              const result = detector.analyze(response.text);
              displayResult(result);
            } else {
              alert("텍스트를 선택해주세요.");
            }
          }
        );
      });
    });

  // 결과 표시
  function displayResult(result) {
    const resultArea = document.getElementById("result-area");
    resultArea.classList.remove("hidden");

    // 위험도 배지
    const riskBadge = document.getElementById("risk-badge");
    riskBadge.textContent = result.riskLevel.label;
    riskBadge.style.backgroundColor = result.riskLevel.color;

    // 점수 바
    const scoreFill = document.getElementById("score-fill");
    scoreFill.style.width = `${result.riskScore}%`;
    scoreFill.style.backgroundColor = result.riskLevel.color;
    document.getElementById(
      "score-text"
    ).textContent = `${result.riskScore}/100`;

    // 패턴
    const patternsSection = document.getElementById("patterns-section");
    const patternsList = document.getElementById("patterns-list");
    patternsList.innerHTML = "";

    if (Object.keys(result.patterns).length > 0) {
      patternsSection.classList.remove("hidden");
      for (const [type, data] of Object.entries(result.patterns)) {
        const li = document.createElement("li");
        li.innerHTML = `<strong>${type}</strong>: ${data.count}건 
            <span class="sample">(예: ${data.samples.join(", ")})</span>`;
        patternsList.appendChild(li);
      }
    } else {
      patternsSection.classList.add("hidden");
    }

    // 키워드
    const keywordsSection = document.getElementById("keywords-section");
    const keywordsList = document.getElementById("keywords-list");
    keywordsList.innerHTML = "";

    if (Object.keys(result.keywords).length > 0) {
      keywordsSection.classList.remove("hidden");
      for (const [category, words] of Object.entries(result.keywords)) {
        const li = document.createElement("li");
        li.innerHTML = `<strong>${category}</strong>: ${words.join(", ")}`;
        keywordsList.appendChild(li);
      }
    } else {
      keywordsSection.classList.add("hidden");
    }

    // 요약
    document.getElementById("summary-text").textContent = result.summary;
  }
});
