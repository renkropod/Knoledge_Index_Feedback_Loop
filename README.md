# Knowledge Index 피드백 루프 시스템

Graph-Augmented Knowledge Memory System (GAKMS) 기반의 자동 리서치 파이프라인입니다. 매일 웹 리서치를 수행하고, 결과를 문서화한 뒤 엔티티/관계 추출, 그래프/벡터/시간축 저장소 업데이트, 피드백 재인덱싱, 지식 현황 리포트 생성까지 한 번에 실행합니다.

## 아키텍처 개요 (5-Layer)

```
┌─────────────────────────────────────────────────────────┐
│  Layer 1: Ingestion                                     │
│  Cron 스케줄, 웹 리서치, 사용자 요청, 파일 업로드         │
├─────────────────────────────────────────────────────────┤
│  Layer 2: Knowledge Extraction                          │
│  Entity Extraction -> Relation Mapping -> Deduplication │
├─────────────────────────────────────────────────────────┤
│  Layer 3: Hybrid Storage                                │
│  Knowledge Graph | Vector Store | Temporal Fact Store   │
├─────────────────────────────────────────────────────────┤
│  Layer 4: Retrieval                                     │
│  Dual-level 검색 + PPR 기반 랭킹 + 시간 가중치            │
├─────────────────────────────────────────────────────────┤
│  Layer 5: Generation + Feedback Loop                    │
│  출력물 재인덱싱으로 지식 베이스를 지속 강화              │
└─────────────────────────────────────────────────────────┘
```

## 빠른 시작

1. 의존성 설치

```bash
pip install -r requirements.txt
```

2. 환경변수 파일 준비

```bash
cp .env.example .env
```

`.env`에서 `ANTHROPIC_API_KEY`를 설정하세요.

3. 일일 리서치 파이프라인 실행

```bash
python scripts/daily_research.py [topics...]
```

- 토픽을 전달하지 않으면 `config/settings.yaml`의 `research.default_topics`를 사용합니다.

## 프로젝트 구조

```
research-agent/
├── config/
│   ├── settings.py
│   ├── settings.yaml
│   └── prompts/
├── ingestion/
│   ├── scheduler.py
│   ├── web_researcher.py
│   └── document_parser.py
├── extraction/
│   ├── entity_extractor.py
│   ├── relation_mapper.py
│   └── deduplicator.py
├── storage/
│   ├── graph_store.py
│   ├── vector_store.py
│   └── temporal_store.py
├── retrieval/
│   ├── dual_retriever.py
│   ├── ppr_ranker.py
│   └── context_assembler.py
├── feedback/
│   ├── output_indexer.py
│   └── quality_scorer.py
├── generation/
│   ├── llm_generator.py
│   └── provenance_tracker.py
├── scripts/
│   ├── daily_research.py
│   └── knowledge_report.py
└── knowledge_base/
    ├── documents/
    ├── graph/
    ├── vectors/
    └── temporal/
```

## 기술 스택

| 구성 요소 | 기술 | 역할 |
|---|---|---|
| Knowledge Graph | NetworkX | 엔티티/관계 그래프 저장 및 업데이트 |
| Vector Store | ChromaDB | 문서 임베딩 저장 및 유사도 검색 |
| Embedding | BGE-M3 | 다국어 문서 임베딩 생성 |
| LLM | Claude | 엔티티/관계 추출 |
| Scheduler | APScheduler | 주기 실행 오케스트레이션 |

## 핵심 기능

- Self-reinforcing loop: 생성/축적된 결과를 다시 인덱싱해 다음 리서치 품질을 강화
- Temporal-aware retrieval: 사실의 유효 기간을 관리해 시간 축 기반 질의 지원
- Provenance tracking: 각 엔티티/관계/문서의 출처를 저장
- Cross-research relation discovery: 독립 리서치 간 숨은 연관 관계 발견
- Daily knowledge report: 엔티티/관계/문서/사실 변화량을 매일 보고

## 설정 가이드 (`config/settings.yaml`)

- `llm`
  - `api_key_env`: API 키를 읽을 환경변수 이름
  - `extraction_model`: 엔티티/관계 추출 모델
  - `generation_model`: 생성 단계 모델
- `storage`
  - `graph_path`: 그래프 저장 경로
  - `vector_path`: 벡터 저장 경로
  - `temporal_path`: 시간축 사실 저장 경로
- `embedding`
  - `model_name`: 임베딩 모델 이름
  - `device`: 임베딩 실행 디바이스
- `research`
  - `default_topics`: 기본 리서치 토픽 목록
  - `max_sources`: 토픽별 최대 수집 소스 수
  - `schedule_cron`: 스케줄러 크론 표현식

## 라이선스

MIT
