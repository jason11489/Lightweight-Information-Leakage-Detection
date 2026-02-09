"""
가벼운 정보 유출 탐지 분류 모델
- TF-IDF + 전통 ML
- FastText
- 경량 신경망
"""

import re
import pickle
from typing import List, Dict, Tuple
import warnings
warnings.filterwarnings('ignore')


# ============== 1. 규칙 기반 탐지 (기본) ==============

class RuleBasedDetector:
    """규칙 기반 정보 유출 탐지기"""
    
    def __init__(self):
        self.patterns = {
            # '주민등록번호': r'\d{6}[-\s]?\d{7}',
            '주민등록번호' : r'\d{2}([0]\d|[1][0-2])([0][1-9]|[1-2]\d|[3][0-1])[-]*[1-4]\d{6}',
            '전화번호': r'(01[016789][-\s]?\d{3,4}[-\s]?\d{4})',
            '이메일': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            '신용카드': r'\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}',
            '계좌번호': r'\d{3,4}[-\s]?\d{2,4}[-\s]?\d{4,6}',
            'IP주소': r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',
            '비밀번호패턴': r'(password|비밀번호|pwd|passwd)[\s:=]+\S+',
        }
        
        self.sensitive_keywords = {
            '개인정보': ['주민번호', '주민등록', '생년월일', '신분증'],
            '금융정보': ['계좌', '카드번호', '비밀번호', '인증번호'],
            '기업기밀': ['기밀', '대외비', '영업비밀', '내부정보'],
            '접근권한': ['admin', 'root', 'API키', 'secret', 'token'],
        }
    
    def analyze(self, text: str) -> Dict:
        # 패턴 탐지
        patterns_found = {}
        for name, pattern in self.patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                patterns_found[name] = True
        
        # 키워드 탐지
        keywords_found = {}
        for category, keywords in self.sensitive_keywords.items():
            matched = [kw for kw in keywords if kw.lower() in text.lower()]
            if matched:
                keywords_found[category] = matched
        
        risk_score = len(patterns_found) * 30 + len(keywords_found) * 20
        risk_score = min(risk_score, 100)
        
        return {
            'is_leak': risk_score > 30,
            'risk_score': risk_score,
            'patterns': patterns_found,
            'keywords': keywords_found,
        }


# ============== 2. TF-IDF + 전통 ML (가장 가벼움) ==============

class TfidfClassifier:
    """TF-IDF + Logistic Regression / Naive Bayes"""
    
    def __init__(self, model_type: str = 'logistic'):
        """
        model_type: 'logistic', 'naive_bayes'
        """
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.naive_bayes import MultinomialNB
        
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),  # unigram + bigram
            min_df=1
        )
        
        models = {
            'logistic': LogisticRegression(max_iter=1000),
            'naive_bayes': MultinomialNB(),
        }
        self.model = models.get(model_type, LogisticRegression())
        self.model_type = model_type
        self.is_trained = False
    
    def train(self, texts: List[str], labels: List[int]):
        """학습"""
        X = self.vectorizer.fit_transform(texts)
        self.model.fit(X, labels)
        self.is_trained = True
        print(f"[TF-IDF + {self.model_type}] 학습 완료! (샘플 수: {len(texts)})")
    
    def predict(self, text: str) -> Dict:
        """예측"""
        if not self.is_trained:
            raise ValueError("모델이 학습되지 않았습니다.")
        
        X = self.vectorizer.transform([text])
        pred = self.model.predict(X)[0]
        
        # 확률값 (지원하는 모델만)
        if hasattr(self.model, 'predict_proba'):
            proba = self.model.predict_proba(X)[0]
            confidence = proba[pred]
        else:
            confidence = 0.8 if pred == 1 else 0.2
        
        return {
            'is_leak': bool(pred),
            'label': '유출위험' if pred else '정상',
            'confidence': float(confidence)
        }
    
    def save(self, path: str):
        with open(path, 'wb') as f:
            pickle.dump({'vectorizer': self.vectorizer, 'model': self.model}, f)
    
    def load(self, path: str):
        with open(path, 'rb') as f:
            data = pickle.load(f)
            self.vectorizer = data['vectorizer']
            self.model = data['model']
            self.is_trained = True


# ============== 3. 하이브리드 탐지기 ==============

class HybridDetector:
    """규칙 기반 + ML 하이브리드"""
    
    def __init__(self, ml_model=None):
        self.rule_detector = RuleBasedDetector()
        self.ml_model = ml_model
    
    def analyze(self, text: str) -> Dict:
        # 규칙 기반
        rule_result = self.rule_detector.analyze(text)
        
        result = {
            'text_preview': text[:80] + '...' if len(text) > 80 else text,
            'rule_based': rule_result,
        }
        
        # ML 기반
        ml_result = self.ml_model.predict(text)
        result['ml_based'] = ml_result
        
        # 최종 판단
        result['final'] = {
            'is_leak': rule_result['is_leak'] or ml_result['is_leak'],
            'confidence': max(rule_result['risk_score']/100, ml_result['confidence'])
        }
        
        return result
    
    def save(self, path: str):
        """모델 저장"""
        import json
        
        data = {
            'rule_detector': {
                'patterns': self.rule_detector.patterns,
                'sensitive_keywords': self.rule_detector.sensitive_keywords
            },
            'ml_model': None
        }
        
        # ML 모델이 있으면 저장
        if self.ml_model and hasattr(self.ml_model, 'is_trained') and self.ml_model.is_trained:
            ml_path = path.replace('.pkl', '_ml.pkl')
            self.ml_model.save(ml_path)
            data['ml_model_path'] = ml_path
            data['ml_model_type'] = getattr(self.ml_model, 'model_type', 'logistic')
        
        with open(path, 'wb') as f:
            pickle.dump(data, f)
        
        print(f"✅ HybridDetector 저장 완료: {path}")
        
        # Chrome 확장 프로그램용 JSON 내보내기
        self._export_for_chrome(path.replace('.pkl', '_config.json'))
    
    @classmethod
    def load(cls, path: str) -> 'HybridDetector':
        """모델 로드"""
        with open(path, 'rb') as f:
            data = pickle.load(f)
        
        # ML 모델 로드
        ml_model = None
        if data.get('ml_model_path'):
            ml_model = TfidfClassifier(model_type=data.get('ml_model_type', 'logistic'))
            ml_model.load(data['ml_model_path'])
        
        # HybridDetector 생성
        detector = cls(ml_model=ml_model)
        
        # 규칙 설정 복원
        if data.get('rule_detector'):
            detector.rule_detector.patterns = data['rule_detector']['patterns']
            detector.rule_detector.sensitive_keywords = data['rule_detector']['sensitive_keywords']
        
        print(f"✅ HybridDetector 로드 완료: {path}")
        return detector
    
    def _export_for_chrome(self, json_path: str):
        """Chrome 확장 프로그램용 설정 JSON 내보내기"""
        import json
        
        config = {
            'patterns': self.rule_detector.patterns,
            'sensitiveKeywords': self.rule_detector.sensitive_keywords,
            'version': '1.0',
            'exportedAt': str(import_datetime())
        }
        
        # ML 모델의 중요 특성 추출 (가능한 경우)
        if self.ml_model and hasattr(self.ml_model, 'vectorizer'):
            try:
                feature_names = self.ml_model.vectorizer.get_feature_names_out()
                
                # Logistic Regression의 경우 중요 특성 추출
                if hasattr(self.ml_model.model, 'coef_'):
                    coef = self.ml_model.model.coef_[0]
                    # 상위 50개 유출 관련 키워드
                    top_indices = coef.argsort()[-50:][::-1]
                    top_features = [(feature_names[i], float(coef[i])) for i in top_indices]
                    config['mlFeatures'] = {
                        'topLeakKeywords': top_features[:30],
                        'modelType': self.ml_model.model_type
                    }
            except Exception as e:
                print(f"⚠️ ML 특성 추출 실패: {e}")
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Chrome 확장 프로그램용 설정 저장: {json_path}")


def import_datetime():
    from datetime import datetime
    return datetime.now().isoformat()


# ============== 샘플 데이터 ==============

SAMPLE_DATA = [
    # ========== 정상 (0) ==========
    # 일상 업무
    ("오늘 회의는 3시에 진행됩니다.", 0),
    ("프로젝트 일정을 확인해 주세요.", 0),
    ("점심 메뉴 추천 부탁드립니다.", 0),
    ("내일 출장 일정 공유합니다.", 0),
    ("코드 리뷰 부탁드립니다.", 0),
    ("이번 주 금요일까지 보고서 제출 바랍니다.", 0),
    ("회의실 예약 완료되었습니다.", 0),
    ("새로운 기능 개발이 완료되었습니다.", 0),
    
    # 일반 소통
    ("안녕하세요, 잘 지내시죠?", 0),
    ("오늘 날씨가 정말 좋네요.", 0),
    ("주말에 뭐 하실 계획이세요?", 0),
    ("커피 한잔 하실래요?", 0),
    ("수고하셨습니다. 좋은 하루 되세요.", 0),
    ("감사합니다. 확인했습니다.", 0),
    ("네, 알겠습니다. 진행하겠습니다.", 0),
    ("질문 있으시면 편하게 연락주세요.", 0),
    
    # 업무 관련
    ("이번 분기 매출 목표 달성했습니다.", 0),
    ("신규 고객 유치 전략 회의 안내드립니다.", 0),
    ("서비스 업데이트 공지사항입니다.", 0),
    ("버그 수정 완료되어 배포 예정입니다.", 0),
    ("테스트 결과 이상 없습니다.", 0),
    ("디자인 시안 검토 부탁드립니다.", 0),
    ("마케팅 캠페인 결과 보고서입니다.", 0),
    ("다음 주 워크샵 장소가 확정되었습니다.", 0),
    
    # 기술 관련 (정상)
    ("Python 3.11 버전으로 업그레이드 했습니다.", 0),
    ("새로운 라이브러리 도입을 검토 중입니다.", 0),
    ("성능 최적화 작업이 완료되었습니다.", 0),
    ("코드 컨벤션 가이드 공유드립니다.", 0),
    ("깃허브 PR 리뷰 요청드립니다.", 0),
    ("CI/CD 파이프라인 구축 완료했습니다.", 0),
    ("API 문서 업데이트했습니다.", 0),
    ("단위 테스트 커버리지 80% 달성했습니다.", 0),
    
    # ========== 유출 위험 (1) ==========
    # 개인정보 - 주민등록번호
    ("고객 주민번호는 901234-1234567입니다.", 1),
    ("본인확인용 주민등록번호: 850101-2345678", 1),
    ("신청자 주민번호 920315-1111111 확인바랍니다.", 1),
    ("회원가입시 주민번호 뒷자리 필요합니다 880520-1234567", 1),
    
    # 개인정보 - 연락처
    ("고객 연락처 010-1234-5678 이메일 test@test.com", 1),
    ("담당자 전화번호: 010-9876-5432로 연락주세요.", 1),
    ("비상연락망 김OO 010-1111-2222 박OO 010-3333-4444", 1),
    ("고객 이메일 주소 customer@company.com 입니다.", 1),
    
    # 금융정보 - 카드/계좌
    ("고객 카드번호 1234-5678-9012-3456 확인요청", 1),
    ("결제 카드정보: 4111-1111-1111-1111 유효기간 12/25", 1),
    ("환불 계좌번호 110-123-456789 국민은행입니다.", 1),
    ("급여이체 계좌 신한 110-456-789012로 변경해주세요.", 1),
    
    # 인증정보 - 비밀번호
    ("데이터베이스 비밀번호: admin123!", 1),
    ("서버 접속정보 IP 192.168.1.100 root password123", 1),
    ("FTP 접속 비밀번호는 qwerty2024! 입니다.", 1),
    ("관리자 계정 password: P@ssw0rd!234", 1),
    ("시스템 초기 비밀번호 설정: temp1234!", 1),
    
    # 인증정보 - API 키/토큰
    ("API 키: sk-1234567890abcdef", 1),
    ("AWS secret key: AKIAIOSFODNN7EXAMPLE", 1),
    ("GitHub 토큰: ghp_xxxxxxxxxxxxxxxxxxxx", 1),
    ("Slack webhook URL: https://hooks.slack.com/services/T00/B00/xxxx", 1),
    ("Firebase API key: AIzaSyxxxxxxxxxxxxxxxxxx", 1),
    
    # 기업 기밀
    ("회사 기밀 문서입니다. 대외비로 처리해주세요.", 1),
    ("내부정보 유출 금지, 영업비밀 포함됨", 1),
    ("이 문서는 1급 기밀입니다. 외부 반출 금지.", 1),
    ("경쟁사 분석 자료 - 대외비", 1),
    ("인수합병 관련 극비 문서입니다.", 1),
    ("신제품 출시 계획 - 사내 한정 공유", 1),
    
    # 서버/인프라 정보
    ("운영서버 SSH 접속: ssh admin@10.0.0.1 -p 22", 1),
    ("DB 접속정보 host: db.internal.com user: root pwd: dbpass123", 1),
    ("Redis 서버 192.168.0.50:6379 인증키 redis_secret_key", 1),
    ("프로덕션 서버 IP 목록: 10.0.1.1, 10.0.1.2, 10.0.1.3", 1),
    
    # 복합 유출
    ("고객정보 - 홍길동 주민번호 900101-1234567 전화 010-1234-5678", 1),
    ("결제내역 카드 1234-5678-9012-3456 금액 50000원 승인", 1),
    ("긴급) admin 계정 비밀번호 초기화: admin / newpass123!", 1),
    ("AWS 계정 access_key: AKIA1234 secret: abcd1234efgh", 1),
]

# ============== 메인 실행 ==============

if __name__ == "__main__":
    print("=" * 60)
    print("🔒 가벼운 정보 유출 탐지 모델")
    print("=" * 60)
    
    
    # 데이터 준비
    texts = [d[0] for d in SAMPLE_DATA]
    labels = [d[1] for d in SAMPLE_DATA]
    
    # ============== 정량적 평가 추가 ==============
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import (
        confusion_matrix, 
        classification_report, 
        f1_score, 
        accuracy_score,
        precision_score,
        recall_score
    )
    
    # Train/Test 분리
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )
    
    print("\n" + "=" * 60)
    print("📊 정량적 평가 (Train/Test Split)")
    print("=" * 60)
    print(f"학습 데이터: {len(X_train)}개, 테스트 데이터: {len(X_test)}개\n")
    
    # 모델별 평가
    model_types = ['rule_based', 'logistic', 'naive_bayes']
    results = {}
    
    for model_type in model_types:
        print(f"\n{'='*50}")
        print(f"📌 {model_type.upper()}")
        print('='*50)
        
        if model_type == 'rule_based':
            # 규칙 기반 탐지기 평가
            detector = RuleBasedDetector()
            y_pred = [int(detector.analyze(text)['is_leak']) for text in X_test]
        else:
            # TF-IDF 기반 모델 평가
            clf = TfidfClassifier(model_type=model_type)
            clf.vectorizer.fit(X_train)
            print(f"\n🔍 Vectorizer 구성: {clf.vectorizer.get_params()}")

            X_train_vec = clf.vectorizer.transform(X_train)
            X_test_vec = clf.vectorizer.transform(X_test)
            clf.model.fit(X_train_vec, y_train)
            clf.is_trained = True
            
            # 예측
            y_pred = clf.model.predict(X_test_vec)
        
        # 메트릭 계산
        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        
        results[model_type] = {
            'accuracy': acc,
            'f1': f1,
            'precision': precision,
            'recall': recall
        }
        
        # Confusion Matrix
        cm = confusion_matrix(y_test, y_pred)
        print(f"\n🔹 Confusion Matrix:")
        print(f"              예측:정상  예측:유출")
        print(f"  실제:정상      {cm[0][0]:4d}      {cm[0][1]:4d}")
        print(f"  실제:유출      {cm[1][0]:4d}      {cm[1][1]:4d}")
        
        # Classification Report
        print(f"\n🔹 Classification Report:")
        print(classification_report(y_test, y_pred, target_names=['정상', '유출위험']))
    
    # ============== 모델 비교 요약 ==============
    print("\n" + "=" * 60)
    print("📈 모델별 성능 비교")
    print("=" * 60)
    print(f"{'모델':<20} {'Accuracy':<12} {'F1':<12} {'Precision':<12} {'Recall':<12}")
    print("-" * 68)
    for model_type, metrics in results.items():
        print(f"{model_type:<20} {metrics['accuracy']:<12.4f} {metrics['f1']:<12.4f} {metrics['precision']:<12.4f} {metrics['recall']:<12.4f}")

    # ============== 최적 모델로 HybridDetector 생성 및 저장 ==============
    print("\n" + "=" * 60)
    print("💾 HybridDetector 모델 저장")
    print("=" * 60)
    
    # 가장 좋은 성능의 모델 선택 (예: logistic)
    best_model_type = max(results, key=lambda x: results[x]['f1'])
    print(f"최적 모델: {best_model_type} (F1: {results[best_model_type]['f1']:.4f})")
    
    # 전체 데이터로 재학습 (규칙 기반은 학습 불필요)
    if best_model_type == 'rule_based':
        best_clf = None
    else:
        best_clf = TfidfClassifier(model_type=best_model_type)
        best_clf.train(texts, labels)
    
    # HybridDetector 생성 및 저장
    hybrid = HybridDetector(ml_model=best_clf)
    hybrid.save('hybrid_detector.pkl')
    
    # ============== HybridDetector 평가 ==============
    print("\n" + "=" * 60)
    print("📊 HybridDetector 평가")
    print("=" * 60)
    
    # X_test에 대한 예측
    y_pred_hybrid = [int(hybrid.analyze(text)['final']['is_leak']) for text in X_test]
    
    # 메트릭 계산
    acc_hybrid = accuracy_score(y_test, y_pred_hybrid)
    f1_hybrid = f1_score(y_test, y_pred_hybrid)
    precision_hybrid = precision_score(y_test, y_pred_hybrid)
    recall_hybrid = recall_score(y_test, y_pred_hybrid)
    
    # Confusion Matrix
    cm_hybrid = confusion_matrix(y_test, y_pred_hybrid)
    print(f"\n🔹 Confusion Matrix:")
    print(f"              예측:정상  예측:유출")
    print(f"  실제:정상      {cm_hybrid[0][0]:4d}      {cm_hybrid[0][1]:4d}")
    print(f"  실제:유출      {cm_hybrid[1][0]:4d}      {cm_hybrid[1][1]:4d}")
    
    # Classification Report
    print(f"\n🔹 Classification Report:")
    print(classification_report(y_test, y_pred_hybrid, target_names=['정상', '유출위험']))
    
    # 저장된 모델 로드 테스트
    print("\n" + "=" * 60)
    print("🔄 저장된 모델 로드 테스트")
    print("=" * 60)
    
    loaded_hybrid = HybridDetector.load('hybrid_detector.pkl')
    
    print(loaded_hybrid)
    
    # 테스트
    test_texts = [
        "오늘 회의 잘 부탁드립니다.",
        "고객 주민번호 901234-1234567 확인요청",
        "회사 기밀 문서입니다. 대외비로 처리해주세요.",
        "서버 비밀번호: admin123!",
    ]
    
    for text in test_texts:
        result = loaded_hybrid.analyze(text)
        print("\nresult = ",result)
        status = "🚨 유출위험" if result['final']['is_leak'] else "✅ 정상"
        print(f"{status} ({result['final']['confidence']:.1%}): {text[:40]}...")