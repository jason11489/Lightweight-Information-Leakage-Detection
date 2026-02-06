// 메시지 리스너
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "scanPage") {
    const text = document.body.innerText;
    sendResponse({ text });
  } else if (request.action === "scanSelection") {
    const selection = window.getSelection().toString();
    sendResponse({ text: selection });
  }
  return true;
});
