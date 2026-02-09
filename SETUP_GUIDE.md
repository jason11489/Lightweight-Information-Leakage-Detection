# 🔒 Chrome 확장 프로그램 설정 가이드

## 문제 상황

Python으로 작성된 ML 모델(`project.py`)을 Chrome 확장 프로그램에서 사용하고 싶지만, Chrome 확장은 JavaScript만 실행 가능합니다.

## 해결 방법: Python → JavaScript 브릿지

```
Python (ML 모델)  →  JSON 설정 파일  →  JavaScript (Chrome 확장)
```

### 작동 원리

1. **Python에서 ML 모델 학습**
   - TF-IDF + Logistic Regression으로 텍스트 분류
   - 중요 특성(features) 추출
   
2. **JSON으로 내보내기**
   - ML이 학습한 중요 키워드 + 가중치
   - 규칙 기반 패턴 (정규표현식)
   - 민감 키워드 목록

3. **JavaScript에서 JSON 로드**
   - Chrome 확장이 JSON 설정 읽기
   - ML 키워드 가중치로 점수 계산
   - 규칙 기반 + ML 기반 하이브리드 탐지

---

## 📋 설치 단계

### 1. Python 환경 설정

```bash
cd /Users/ksw/AIscientist/NLP/실습자료/nlp_project

# 가상환경 활성화
source .venv/bin/activate

# 필수 라이브러리 설치
pip install scikit-learn
```

### 2. ML 모델 학습 및 내보내기

```bash
python project.py
```

**생성되는 파일:**
- `hybrid_detector.pkl` - 하이브리드 모델
- `hybrid_detector_ml.pkl` - ML 모델 
- `hybrid_detector_config.json` - **Chrome 확장용 설정 (중요!)**

### 3. JSON을 Chrome 확장 폴더로 복사

```bash
cp hybrid_detector_config.json info-leak-detector/config/
```

### 4. Chrome 확장 프로그램 설치

1. Chrome에서 `chrome://extensions/` 접속
2. 오른쪽 상단 **"개발자 모드"** 활성화
3. **"압축해제된 확장 프로그램을 로드합니다"** 클릭
4. `info-leak-detector` 폴더 선택
5. 완료! 🎉

---

## 🧪 테스트

### 방법 1: 직접 텍스트 입력
1. Chrome 확장 아이콘 클릭
2. "직접 입력" 탭 선택
3. 텍스트 입력 후 "분석하기"

### 방법 2: 웹 페이지 스캔
1. 아무 웹 페이지 방문
2. 확장 아이콘 클릭 → "페이지 스캔"
3. "전체 페이지 스캔" 클릭

### 방법 3: 텍스트 선택 스캔
1. 웹 페이지에서 텍스트 드래그
2. 확장 아이콘 클릭
3. "선택 영역 스캔" 클릭

---

## 📊 테스트 예시

### ✅ 안전한 텍스트 (정상)
```
오늘 회의는 3시에 진행됩니다.
프로젝트 일정을 확인해 주세요.
코드 리뷰 부탁드립니다.
```

### 🚨 위험한 텍스트 (유출 위험)
```
고객 주민번호 901234-1234567 확인요청
서버 비밀번호: admin123!
API 키: sk-1234567890abcdef
카드번호 1234-5678-9012-3456
```

---

## 🔍 JSON 설정 파일 내용

`hybrid_detector_config.json`에 포함된 내용:

### 1. 정규식 패턴
```json
{
  "patterns": {
    "주민등록번호": "\\d{6}[-\\s]?\\d{7}",
    "신용카드": "\\d{4}[-\\s]?\\d{4}[-\\s]?\\d{4}[-\\s]?\\d{4}",
    "전화번호": "(01[016789][-\\s]?\\d{3,4}[-\\s]?\\d{4})",
    ...
  }
}
```

### 2. 민감 키워드
```json
{
  "sensitiveKeywords": {
    "개인정보": ["주민번호", "주민등록", "생년월일", "신분증"],
    "금융정보": ["계좌", "카드번호", "비밀번호", "인증번호"],
    "기업기밀": ["기밀", "대외비", "영업비밀", "내부정보"],
    ...
  }
}
```

### 3. ML 학습 키워드 (가중치 포함)
```json
{
  "mlFeatures": {
    "topLeakKeywords": [
      ["010", 0.3626],
      ["비밀번호", 0.3311],
      ["admin", 0.2603],
      ["key", 0.2621],
      ["서버", 0.2332],
      ...
    ]
  }
}
```

---

## 🎯 핵심 포인트

1. **Python 코드는 Chrome에서 실행 불가**
   - 하지만 JSON 파일은 읽을 수 있음!

2. **ML 모델의 "지식"을 JSON으로 변환**
   - 모델이 학습한 중요 키워드와 가중치
   - JavaScript에서 이 정보로 점수 계산

3. **하이브리드 탐지**
   - 규칙 기반 (정규식 패턴 매칭)
   - ML 기반 (학습된 키워드 가중치)
   - 두 방법을 결합하여 정확도 향상

4. **모델 업데이트 시**
   ```bash
   python project.py  # 재학습
   cp hybrid_detector_config.json info-leak-detector/config/  # 재복사
   chrome://extensions/ 에서 새로고침
   ```

---

## 📁 프로젝트 구조

```
nlp_project/
├── project.py                           # Python ML 모델
├── hybrid_detector.pkl                  # 저장된 모델
├── hybrid_detector_ml.pkl               # ML 모델
├── hybrid_detector_config.json          # ✨ Chrome 확장용 설정
├── detector.py                          # 추가 탐지 로직
├── README.md
└── info-leak-detector/                  # Chrome 확장 프로그램
    ├── manifest.json
    ├── detector.js                      # ✨ JSON 로드 + 분석 로직
    ├── popup.js
    ├── popup.html
    ├── content.js
    ├── background.js
    ├── styles.css
    ├── content-styles.css
    ├── config/
    │   └── hybrid_detector_config.json  # ✨ Python에서 복사한 설정
    └── icons/
        ├── icon16.png
        ├── icon48.png
        └── icon128.png
```

---

## 🐛 문제 해결

### JSON이 로드되지 않을 때
```bash
# 파일 경로 확인
ls -la info-leak-detector/config/hybrid_detector_config.json

# Chrome 확장 프로그램 새로고침
chrome://extensions/ → "새로고침" 버튼 클릭
```

### 모델 성능 개선하기
```python
# project.py의 SAMPLE_DATA에 더 많은 예시 추가
SAMPLE_DATA = [
    ("새로운 정상 텍스트 예시", 0),
    ("새로운 유출 텍스트 예시", 1),
    ...
]

# 재학습 및 재배포
python project.py
cp hybrid_detector_config.json info-leak-detector/config/
```

---

## 🎓 배운 점

1. **Python과 JavaScript를 JSON으로 연결**
   - 서로 다른 언어 간 데이터 교환

2. **ML 모델의 지식을 경량화**
   - 전체 모델 대신 핵심 특성만 추출
   - Chrome 확장에 적합한 경량 구조

3. **하이브리드 접근법**
   - 규칙 기반: 빠르고 정확 (패턴 명확)
   - ML 기반: 유연하고 학습 가능 (새로운 패턴)

---

## 📚 참고 자료

- [Chrome Extension Documentation](https://developer.chrome.com/docs/extensions/)
- [scikit-learn TF-IDF](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html)
- [Logistic Regression](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html)

---

**작성일**: 2026-02-09  
**프로젝트**: 정보 유출 탐지 시스템
