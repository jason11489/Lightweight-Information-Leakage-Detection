# 🔍 Chrome 확장 프로그램 디버깅 가이드

## 문제 증상
모든 웹페이지에서 "이 페이지에서는 스캔할 수 없습니다" 메시지만 표시됨

---

## 🚨 즉시 확인할 사항

### 1단계: Content Script가 로드되는지 확인

#### 방법 A: 개발자 도구에서 확인
```
1. 아무 웹페이지 접속 (예: https://example.com)
2. F12 키 (또는 우클릭 → 검사)
3. Console 탭 선택
4. 다음 메시지가 보이는지 확인:
   - "✅ ML 키워드 30개 로드됨" (detector.js가 정상 로드)
   - 또는 "ℹ️ 기본 설정 사용 (외부 설정 없음)"
5. Errors (빨간색) 가 있는지 확인
```

**예상 결과:**
- ✅ 정상: "✅ ML 키워드 30개 로드됨" 또는 "ℹ️ 기본 설정 사용"
- ❌ 문제: 에러 메시지 또는 아무것도 안 뜸

#### 방법 B: Content Scripts 직접 확인
```
1. 아무 웹페이지 접속
2. F12 (개발자 도구)
3. Console 탭에서 다음 입력:
   
   chrome.runtime.onMessage
   
4. 결과가 undefined가 아니면 content script가 로드됨
```

---

### 2단계: 확장 프로그램 에러 확인

```
1. chrome://extensions/ 접속
2. "정보 유출 탐지기" 찾기
3. "오류" 버튼이 있는지 확인
4. 있으면 클릭해서 에러 내용 확인
```

---

### 3단계: 수동으로 메시지 테스트

```
1. https://example.com 접속
2. F12 (개발자 도구)
3. Console에 다음 입력:

chrome.runtime.sendMessage({action: "test"}, (response) => {
  console.log("Response:", response);
  console.log("LastError:", chrome.runtime.lastError);
});

4. 결과 확인:
   - "Response: undefined" + "LastError: undefined" → content script 로드됨
   - "LastError: Could not establish connection" → content script 로드 안 됨
```

---

## 🔧 가능한 원인과 해결책

### 원인 1: detector.js의 fetch 에러

**증상**: Console에 에러 메시지
```
Failed to fetch chrome-extension://...config/hybrid_detector_config.json
```

**원인**: `detector.js`가 config 파일을 fetch하려다 실패

**해결책**: detector.js의 _loadConfig를 수정해서 에러가 content script 로딩을 막지 않도록 함

---

### 원인 2: Content Script 권한 문제

**증상**: chrome://extensions/ 에서 경고 표시

**해결책**: manifest.json의 permissions 확인
```json
{
  "permissions": ["activeTab", "storage", "contextMenus"],
  "host_permissions": ["<all_urls>"]  // 이게 필요할 수도!
}
```

---

### 원인 3: 확장 프로그램이 제대로 새로고침 안 됨

**해결책**:
```
1. chrome://extensions/
2. "정보 유출 탐지기" 찾기
3. 🔄 "새로고침" 버튼 클릭
4. 또는 확장 프로그램 "제거" 후 다시 설치
```

---

### 원인 4: detector.js 로드 순서 문제

**증상**: detector.js 에러로 content.js가 실행 안 됨

**임시 해결책**: manifest.json에서 순서 변경
```json
"js": ["content.js", "detector.js"]  // content.js를 먼저!
```

---

## 🧪 긴급 테스트: Content Script만 따로 테스트

### 최소 버전으로 테스트

임시로 `manifest.json` 수정:
```json
"content_scripts": [
  {
    "matches": ["<all_urls>"],
    "js": ["content.js"]  // detector.js 제거!
  }
]
```

이렇게 수정 후:
1. 확장 프로그램 새로고침
2. 웹페이지에서 "페이지 스캔" 클릭
3. 에러 메시지가 여전히 나오는지 확인

**결과 분석:**
- 여전히 에러 → content.js 자체 문제 또는 권한 문제
- 에러 사라짐 → detector.js가 문제!

---

## 📋 체크리스트

디버깅 전에 확인할 것들:

- [ ] Chrome 브라우저 최신 버전인가? (chrome://version/)
- [ ] 확장 프로그램이 활성화되어 있는가?
- [ ] 일반 웹페이지(http://, https://)에서 테스트하는가?
- [ ] chrome://extensions/ 에서 새로고침 했는가?
- [ ] F12 개발자 도구 Console에 에러가 있는가?
- [ ] config/hybrid_detector_config.json 파일이 존재하는가?

---

## 🆘 여전히 안 될 때

다음 정보를 수집해주세요:

1. **Chrome 버전**: chrome://version/ 에서 확인
2. **Console 에러 메시지**: F12 → Console 탭의 모든 에러
3. **확장 프로그램 에러**: chrome://extensions/ → "오류" 버튼
4. **테스트한 URL**: 어떤 페이지에서 테스트했는지
5. **위의 1-3단계 결과**: 각 단계에서 무엇이 나타났는지

---

## 🎯 빠른 해결 (90% 확률)

대부분의 경우 이것만 하면 됩니다:

```
1. chrome://extensions/ 접속
2. "정보 유출 탐지기" 찾기
3. "제거" 버튼 클릭
4. 다시 "압축해제된 확장 프로그램을 로드합니다" 클릭
5. info-leak-detector 폴더 선택
6. 웹페이지 새로고침 (F5)
7. 다시 테스트
```

---

## 💡 확실한 확인 방법

Console에서 직접 입력:
```javascript
// 1. Content script가 로드되었는지 확인
document.body.innerText ? "✅ DOM 접근 가능" : "❌ DOM 접근 불가"

// 2. Chrome API가 작동하는지 확인
typeof chrome !== 'undefined' ? "✅ Chrome API 존재" : "❌ Chrome API 없음"

// 3. 메시지 리스너가 등록되었는지 (content script에서만)
chrome.runtime.onMessage.hasListeners() ? "✅ 리스너 존재" : "❌ 리스너 없음"
```

이 명령들을 웹페이지 Console에서 실행하고 결과를 알려주세요!
