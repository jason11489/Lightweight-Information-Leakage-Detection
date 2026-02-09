from project import HybridDetector  # Replace with the actual module name
import ollama

loaded_hybrid = HybridDetector.load('hybrid_detector.pkl')

# ollama.pull('qwen3:latest')

# response = ollama.chat(model='qwen3:latest', messages=[
#     {'role': 'user', 'content': 'Hello, how are you?'}
# ])
# print(response['message']['content'])

print("ml model = ",loaded_hybrid.ml_model)

test_texts = [
    "오늘 회의 잘 부탁드립니다.",
    "고객 주민번호 901234-1234567 확인요청",
    "회사 기밀 문서입니다. 대외비로 처리해주세요. 계약은 ABC 회사랑 하기로 했습니다.",
    "서버 비밀번호: admin123!",
    "점심 시간에 뭐 먹을까요?",
]

def classify_with_ollama(text):
    prompt = f"다음 텍스트가 개인정보 유출 위험인지 분류하세요. '유출위험' 또는 '정상'으로 답변하세요: {text}"
    response = ollama.chat(model='qwen3:latest', messages=[
        {'role': 'user', 'content': prompt}
    ])
    return response['message']['content'].strip()

for text in test_texts:
    # HybridDetector 결과
    # result = loaded_hybrid.analyze(text)
    # hybrid_status = "🚨 유출위험" if result['final']['is_leak'] else "✅ 정상"
    # hybrid_conf = result['final']['confidence']
    
    # Ollama 분류 결과
    ollama_result = classify_with_ollama(text)
    ollama_status = "🚨 유출위험" if "유출위험" in ollama_result else "✅ 정상"
    
    print(f"Ollama: {ollama_status} | Text: {text[:40]}...")
    # print(f"Hybrid: {hybrid_status}|  Text: {text[:40]}...")