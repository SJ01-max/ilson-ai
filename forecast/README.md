# forecast — 데이터 파이프라인 + 유휴 예보 (김새영)
- kma_api.py: 기상청 단기예보 호출 (.env의 KMA_API_KEY 사용)
- demand.py: 작목면적×농작업시기×기상 → 필요 인력
- idle.py: 유휴·손실 계산 → docs/interface.md 3번 JSON 출력
- gen_demo_data.py: 근로자 20명·농가 10곳 데모 데이터 생성
