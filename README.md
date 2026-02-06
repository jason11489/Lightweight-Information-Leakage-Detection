# 🔒 정보 유출 탐지 시스템

텍스트 기반 정보 유출을 탐지하는 하이브리드 NLP 시스템입니다. 규칙 기반 탐지와 머신러닝 분류를 결합하여 개인정보, 금융정보, 기업기밀 등의 민감한 정보 유출을 실시간으로 감지합니다.

## 📋 프로젝트 구조

```
nlp_project/
├── project.py                 # 메인 탐지 모델
├── hybrid_detector.pkl        # 학습된 모델 (생성됨)
├── hybrid_detector_ml.pkl     # ML 모델 (생성됨)
├── hybrid_detector_config.json # Chrome 확장 프로그램용 설정 (생성됨)
├── README.md
└── info-leak-detector/        # Chrome 확장 프로그램
    ├── manifest.json
    ├── background.js
    ├── content.js
    ├── detector.js
    ├── popup.html
    ├── popup.js
    ├── styles.css
    ├── content-styles.css
    ├── config/
    │   └── hybrid_detector_config.json
    └── icons/
```

## 🚀 주요 기능

### 1. 규칙 기반 탐지 (RuleBasedDetector)

정규표현식 패턴을 사용한 민감정보 탐지:

- **주민등록번호**: `XXXXXX-XXXXXXX` 형식
- **전화번호**: `010-XXXX-XXXX` 형식
- **이메일**: 이메일 주소 패턴
- **신용카드**: 16자리 카드번호
- **계좌번호**: 은행 계좌번호 패턴
- **IP 주소**: IPv4 주소
- **비밀번호 패턴**: password, 비밀번호 등 키워드 포함

### 2. ML 기반 탐지 (TfidfClassifier)

TF-IDF 벡터화 + 전통 ML 모델:

- **Logistic Regression**: 기본 분류기
- **Naive Bayes**: 텍스트 분류에 효과적

### 3. 하이브리드 탐지 (HybridDetector)

규칙 기반 + ML 기반 결합으로 정확도 향상

## 💻 설치 및 실행

### 요구사항

```bash
pip install scikit-learn
```

### 모델 학습 및 저장

```bash
python project.py
```

### 사용 예시

```python
from project import HybridDetector

# 저장된 모델 로드
detector = HybridDetector.load('hybrid_detector.pkl')

# 텍스트 분석
result = detector.analyze("고객 주민번호 901234-1234567 확인요청")
print(result)
# {'final': {'is_leak': True, 'confidence': 0.95}, ...}
```

## 📊 모델 성능

| 모델                | Accuracy | F1 Score | Precision | Recall |
| ------------------- | -------- | -------- | --------- | ------ |
| Logistic Regression | ~0.90+   | ~0.90+   | ~0.90+    | ~0.90+ |
| Naive Bayes         | ~0.85+   | ~0.85+   | ~0.85+    | ~0.85+ |

> 성능은 학습 데이터에 따라 달라질 수 있습니다.

## 🌐 Chrome 확장 프로그램

`info-leak-detector/` 폴더에 브라우저 확장 프로그램이 포함되어 있습니다.

### 설치 방법

1. Chrome에서 `chrome://extensions/` 접속
2. "개발자 모드" 활성화
3. "압축해제된 확장 프로그램을 로드합니다" 클릭
4. `info-leak-detector` 폴더 선택

### 기능

- 웹 페이지 내 민감정보 실시간 탐지
- 입력 필드 모니터링
- 유출 위험 경고 알림

## 📁 탐지 대상 정보 유형

| 카테고리 | 탐지 항목                            |
| -------- | ------------------------------------ |
| 개인정보 | 주민번호, 주민등록, 생년월일, 신분증 |
| 금융정보 | 계좌, 카드번호, 비밀번호, 인증번호   |
| 기업기밀 | 기밀, 대외비, 영업비밀, 내부정보     |
| 접근권한 | admin, root, API키, secret, token    |

## 🔧 커스터마이징

### 패턴 추가

```python
detector = HybridDetector()
detector.rule_detector.patterns['새패턴'] = r'정규표현식'
```

### 키워드 추가

```python
detector.rule_detector.sensitive_keywords['새카테고리'] = ['키워드1', '키워드2']
```

## 📝 라이선스

MIT License

## 🤝 기여

이슈 및 PR 환영합니다!
