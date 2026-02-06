// 우클릭 컨텍스트 메뉴
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "scanSelection",
    title: "🔒 선택 텍스트 유출 검사",
    contexts: ["selection"],
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "scanSelection" && info.selectionText) {
    chrome.tabs.sendMessage(tab.id, {
      action: "showAlert",
      text: info.selectionText,
    });
  }
});
