/**
 * 규칙 기반 + ML 특성 기반 정보 유출 탐지기
 */

class InfoLeakDetector {
  constructor() {
    // 기본 정규식 패턴
    this.patterns = {
      주민등록번호: /\d{6}[-\s]?\d{7}/g,
      전화번호: /(01[016789][-\s]?\d{3,4}[-\s]?\d{4})/g,
      이메일: /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g,
      신용카드: /\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}/g,
      계좌번호: /\d{3,4}[-\s]?\d{2,4}[-\s]?\d{4,6}/g,
      IP주소: /\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/g,
      비밀번호패턴: /(password|비밀번호|pwd|passwd)[\s:=]+\S+/gi,
      API키: /(api[_-]?key|apikey|secret[_-]?key|access[_-]?token)[\s:=]+\S+/gi,
      AWS키: /AKIA[0-9A-Z]{16}/g,
      GitHub토큰: /ghp_[a-zA-Z0-9]{36}/g,
    };

    // 민감 키워드
    this.sensitiveKeywords = {
      개인정보: ["주민번호", "주민등록", "생년월일", "신분증", "여권번호"],
      금융정보: ["계좌", "카드번호", "비밀번호", "인증번호", "cvv", "cvc"],
      기업기밀: ["기밀", "대외비", "영업비밀", "내부정보", "극비", "1급비밀"],
      접근권한: ["admin", "root", "api키", "secret", "token", "credential"],
    };

    // ML 모델에서 학습된 중요 키워드 (Python에서 내보낸 설정으로 업데이트)
    this.mlLeakKeywords = [];

    // 위험도 가중치
    this.patternWeights = {
      주민등록번호: 50,
      신용카드: 45,
      비밀번호패턴: 40,
      API키: 40,
      AWS키: 45,
      GitHub토큰: 40,
      계좌번호: 35,
      전화번호: 20,
      이메일: 15,
      IP주소: 15,
    };

    // 설정 로드 시도
    this._loadConfig();
  }

  /**
   * Python에서 내보낸 설정 로드
   */
  async _loadConfig() {
    try {
      const response = await fetch(
        chrome.runtime.getURL("config/hybrid_detector_config.json")
      );
      if (response.ok) {
        const config = await response.json();

        // 패턴 업데이트 (문자열 → RegExp 변환)
        if (config.patterns) {
          for (const [name, pattern] of Object.entries(config.patterns)) {
            try {
              // 문자열 패턴을 RegExp로 변환 (글로벌 플래그 추가)
              this.patterns[name] = new RegExp(pattern, "gi");
              console.log(`✅ 패턴 로드: ${name}`);
            } catch (e) {
              console.warn(`⚠️ 잘못된 정규식 패턴: ${name}`, e);
            }
          }
        }

        // 키워드 업데이트
        if (config.sensitiveKeywords) {
          this.sensitiveKeywords = {
            ...this.sensitiveKeywords,
            ...config.sensitiveKeywords,
          };
        }

        // ML 학습 키워드 로드
        if (config.mlFeatures && config.mlFeatures.topLeakKeywords) {
          this.mlLeakKeywords = config.mlFeatures.topLeakKeywords;
          console.log(`✅ ML 키워드 ${this.mlLeakKeywords.length}개 로드됨`);
        }
      }
    } catch (e) {
      console.log("ℹ️ 기본 설정 사용 (외부 설정 없음)");
    }
  }

  /**
   * 텍스트 분석 (하이브리드)
   */
  analyze(text) {
    if (!text || typeof text !== "string") {
      return this._emptyResult();
    }

    const patternsFound = {};
    const matchedItems = [];
    let totalRiskScore = 0;

    // 1. 정규식 패턴 탐지
    for (const [name, pattern] of Object.entries(this.patterns)) {
      // 정규식 패턴인 경우
      if (pattern instanceof RegExp) {
        const matches = text.match(pattern);
        if (matches) {
          patternsFound[name] = {
            count: matches.length,
            samples: matches
              .slice(0, 3)
              .map((m) => this._maskSensitive(m, name)),
          };
          matchedItems.push(
            ...matches.map((m) => ({
              type: name,
              value: m,
              masked: this._maskSensitive(m, name),
            }))
          );
          totalRiskScore += (this.patternWeights[name] || 20) * matches.length;
        }
      }
    }

    // 2. 키워드 탐지
    const keywordsFound = {};
    const lowerText = text.toLowerCase();

    for (const [category, keywords] of Object.entries(this.sensitiveKeywords)) {
      const matched = keywords.filter((kw) =>
        lowerText.includes(kw.toLowerCase())
      );
      if (matched.length > 0) {
        keywordsFound[category] = matched;
        totalRiskScore += matched.length * 15;
      }
    }

    // 3. ML 학습 키워드 기반 추가 점수
    const mlScore = this._calculateMLScore(lowerText);
    totalRiskScore += mlScore;

    // 위험도 정규화 (0-100)
    const riskScore = Math.min(totalRiskScore, 100);
    const riskLevel = this._getRiskLevel(riskScore);

    return {
      isLeak: riskScore > 25,
      riskScore,
      riskLevel,
      patterns: patternsFound,
      keywords: keywordsFound,
      matchedItems,
      mlScore,
      summary: this._generateSummary(patternsFound, keywordsFound, riskLevel),
      timestamp: new Date().toISOString(),
    };
  }

  /**
   * ML 학습 키워드 기반 점수 계산
   */
  _calculateMLScore(lowerText) {
    if (!this.mlLeakKeywords || this.mlLeakKeywords.length === 0) {
      return 0;
    }

    let score = 0;
    const words = lowerText.split(/\s+/);

    for (const [keyword, weight] of this.mlLeakKeywords) {
      if (lowerText.includes(keyword.toLowerCase())) {
        // 가중치에 비례한 점수 (최대 5점씩)
        score += Math.min(weight * 2, 5);
      }
    }

    return Math.min(score, 30); // ML 점수 최대 30점
  }

  /**
   * 민감 정보 마스킹
   */
  _maskSensitive(value, type) {
    if (!value) return value;

    switch (type) {
      case "주민등록번호":
        return value.replace(/(\d{6}[-\s]?)\d{7}/, "$1*******");
      case "신용카드":
        return value.replace(
          /(\d{4}[-\s]?)\d{4}[-\s]?\d{4}[-\s]?(\d{4})/,
          "$1****-****-$2"
        );
      case "전화번호":
        return value.replace(
          /(01[016789][-\s]?)\d{3,4}([-\s]?\d{4})/,
          "$1****$2"
        );
      case "이메일":
        return value.replace(/(.{2})[^@]*(@.*)/, "$1***$2");
      case "계좌번호":
        return value.replace(/(\d{3,4}[-\s]?)\d+/, "$1********");
      default:
        if (value.length > 6) {
          return (
            value.substring(0, 3) + "***" + value.substring(value.length - 2)
          );
        }
        return "***";
    }
  }

  /**
   * 위험 등급 결정
   */
  _getRiskLevel(score) {
    if (score >= 70)
      return { level: "critical", label: "🔴 위험", color: "#e74c3c" };
    if (score >= 40)
      return { level: "high", label: "🟠 높음", color: "#e67e22" };
    if (score >= 25)
      return { level: "medium", label: "🟡 주의", color: "#f1c40f" };
    return { level: "low", label: "🟢 안전", color: "#27ae60" };
  }

  /**
   * 요약 생성
   */
  _generateSummary(patterns, keywords, riskLevel) {
    const patternTypes = Object.keys(patterns);
    const keywordCategories = Object.keys(keywords);

    if (patternTypes.length === 0 && keywordCategories.length === 0) {
      return "민감 정보가 탐지되지 않았습니다.";
    }

    let summary = `[${riskLevel.label}] `;

    if (patternTypes.length > 0) {
      summary += `탐지된 패턴: ${patternTypes.join(", ")}. `;
    }

    if (keywordCategories.length > 0) {
      summary += `관련 키워드: ${keywordCategories.join(", ")}.`;
    }

    return summary;
  }

  /**
   * 빈 결과 반환
   */
  _emptyResult() {
    return {
      isLeak: false,
      riskScore: 0,
      riskLevel: { level: "low", label: "🟢 안전", color: "#27ae60" },
      patterns: {},
      keywords: {},
      matchedItems: [],
      mlScore: 0,
      summary: "분석할 텍스트가 없습니다.",
      timestamp: new Date().toISOString(),
    };
  }
}

// 전역으로 내보내기
if (typeof window !== "undefined") {
  window.InfoLeakDetector = InfoLeakDetector;
}
