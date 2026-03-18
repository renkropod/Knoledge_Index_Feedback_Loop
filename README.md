# GAKMS — Graph-Augmented Knowledge Memory System

하루 2회 자동으로 기술 뉴스를 수집 → 한국어 Knowledge Base 구축 → LLM 인텔리전스 브리핑 생성 → Discord 전송하는 시스템.

## 현황 (2026-03-17)

| 항목 | 수치 |
|---|---|
| Knowledge Graph 엔티티 | **10,044** |
| 관계 | **9,339** |
| Temporal 사실 | **10,478** |
| Vector 청크 | **5,327** |
| 커뮤니티 (Louvain) | **2,182** |
| 수집 문서 | **5,312** |
| 인텔리전스 리포트 | **7** |
| 유닛 테스트 | **31/31 pass** |
| 데이터 소스 | HN, Lobsters, Dev.to, Reddit(5), GitHub Trending, RSS(3) |

## 아키텍처

```
┌─ 데이터 수집 ──────────────────────────────────────────┐
│  HN Algolia API · Lobsters · Dev.to · Reddit · GitHub  │
│  Trending · TechCrunch/ArsTechnica/TheVerge RSS         │
├─ 1차 스캔 ─────────────────────────────────────────────┤
│  Entity/Relation Extraction (vLLM, 한국어)              │
│  Source-Grounding Filter → Deduplication                │
├─ Hybrid Storage ───────────────────────────────────────┤
│  NetworkX KG │ ChromaDB Vectors │ Temporal JSONL        │
│  Louvain Community Detection                            │
├─ Retrieval ────────────────────────────────────────────┤
│  Dual-Level (Low+High+Hybrid) + PPR Ranking             │
│  Community Boost + Temporal Boost                       │
├─ 2차 딥리드 ───────────────────────────────────────────┤
│  상위 K/R 글 원문 Fetch → 근거수준 A/B/C/D 판정        │
│  과거 리포트 3개 참조 → 반복 관측 판정                   │
├─ Intelligence Report ──────────────────────────────────┤
│  3축 점수 (T/K/R) · 확인/해석/가설 분리                 │
│  5섹션: 필독글 → 요약 → 신호 → 딥리드 → 지식노트        │
├─ 전송 ─────────────────────────────────────────────────┤
│  Discord Webhook · Obsidian Vault · MD 파일             │
├─ Feedback Loop ────────────────────────────────────────┤
│  출력물 재인덱싱 → QualityScorer → ProvenanceTracker     │
└────────────────────────────────────────────────────────┘
```

## 빠른 시작

```bash
# 1. venv 생성 + 의존성
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. 환경변수 (vLLM 로컬 모델 사용 시)
export VLLM_BASE_URL=http://localhost:8013/v1
export VLLM_MODEL="Qwen/Qwen3.5-35B-A3B-FP8"

# 3. KB 구축 (HN 한달치 + 다중 소스)
python scripts/build_kb_hn_monthly.py

# 4. 일일 파이프라인 실행
python scripts/daily_news_pipeline.py --hours 12

# 5. RAG 한국어 Q&A
python scripts/ask.py "최근 AI 에이전트 트렌드"

# 6. KB 대시보드
python scripts/dashboard.py
```

## 주요 스크립트

| 스크립트 | 용도 |
|---|---|
| `scripts/daily_news_pipeline.py` | 하루 2회 자동 실행. 수집→추출→KB→인텔리전스 리포트→Discord |
| `scripts/ask.py "질문"` | RAG 기반 한국어 Q&A (vLLM 답변 생성) |
| `scripts/build_kb_hn_monthly.py` | HN 30일치 + Lobsters + Dev.to + RSS 대규모 KB 구축 |
| `scripts/query.py "검색어"` | KB 검색 CLI (`--at-time`, `--entity-history`, `--communities`) |
| `scripts/dashboard.py` | KB 성장 메트릭 대시보드 (`--json`) |
| `scripts/benchmark.py` | 전 모듈 벤치마크 (Precision, Recall@k, MRR) |
| `scripts/run_scheduler.py` | APScheduler 기반 자동 실행 |
| `scripts/setup_cron.sh` | crontab / systemd timer 설정 (10AM/10PM KST) |

## 인텔리전스 리포트 구조

하루 2회 자동 생성되는 3층 구조 브리핑:

```
§0. 오늘 꼭 읽을 글 3개     ← K+R 최상위, 🔴정독/🟡스캔/⚪검증대기
§1. 한 화면 요약             ← 3줄, 관측형 문장
§2. 핵심 신호 5개            ← 확인/해석/미확인 분리, 근거강도 표기
§3. 장문 딥리드              ← 원문 fetch 기반, 확인/해석/확장가설 3층
§4. 지식 노트                ← 신규개념, 배경개념, 도구카드, 열린질문, 용어
§5. 체크리스트               ← 질문 7개 + 키워드 10개
```

3축 점수:
- **T**(트렌드): 커뮤니티 확산도
- **K**(지식): 배움의 밀도
- **R**(연구): 논문/시스템 이해 연결 가능성

## 프로젝트 구조

```
research-agent/
├── config/
│   ├── settings.py / settings.yaml
│   ├── llm_client.py          # vLLM/Anthropic 공용 팩토리
│   ├── notification.py        # Discord + Obsidian 연동
│   └── prompts/
├── extraction/
│   ├── entity_extractor.py    # LLM 추출 + source-grounding
│   ├── relation_mapper.py     # co-occurrence + hierarchical
│   └── deduplicator.py
├── storage/
│   ├── graph_store.py         # NetworkX + Louvain community
│   ├── vector_store.py        # ChromaDB + lazy loading + batch
│   ├── temporal_store.py      # append-only JSONL journal
│   └── knowledge_cards.py     # 누적형 지식 카드
├── retrieval/
│   ├── dual_retriever.py      # low/high/hybrid + community boost
│   ├── ppr_ranker.py          # PPR + max-normalization
│   └── context_assembler.py
├── ingestion/
│   ├── web_researcher.py      # DuckDuckGo search + fetch
│   ├── document_parser.py     # md/pdf/html/txt
│   └── scheduler.py           # APScheduler
├── generation/
│   ├── llm_generator.py       # vLLM/Anthropic 호환
│   └── provenance_tracker.py  # bounded records
├── feedback/
│   ├── output_indexer.py      # 재인덱싱 + temporal facts
│   └── quality_scorer.py
├── scripts/                   # 위 표 참조
├── tests/                     # 31 unit tests
└── knowledge_base/
    ├── documents/             # 5,312 markdown files
    ├── graph/kg.json          # 10K entities, 9K relations
    ├── vectors/               # ChromaDB
    ├── temporal/facts.jsonl   # 10K facts
    ├── cards/                 # 누적형 지식 카드
    └── reports/               # 인텔리전스 브리핑
```

## 설정

### vLLM (로컬 LLM)
```bash
export VLLM_BASE_URL=http://localhost:8013/v1
export VLLM_MODEL="Qwen/Qwen3.5-35B-A3B-FP8"
```

### Anthropic (클라우드)
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

### Discord 웹훅
```yaml
# config/settings.yaml
notification:
  discord_webhook_url: "https://discord.com/api/webhooks/..."
```

### Obsidian
```yaml
notification:
  obsidian_vault_path: "/path/to/vault"
  obsidian_folder: "Tech Trends"
```

### 자동 실행 (10AM/10PM KST)
```bash
bash scripts/setup_cron.sh
```

## 기술 스택

| 구성 요소 | 기술 |
|---|---|
| Knowledge Graph | NetworkX + Louvain community detection |
| Vector Store | ChromaDB (BGE-M3 embedding) |
| LLM | vLLM (Qwen3.5-35B-A3B-FP8) / Anthropic Claude |
| 수집 | Algolia HN API, Reddit JSON, GitHub HTML, RSS |
| 스케줄러 | APScheduler / systemd timer |
| 알림 | Discord Webhook, Obsidian Vault |

## 성능

| 지표 | 값 |
|---|---|
| Retrieval Precision@5 | **91%** |
| Retrieval Latency | **0.06s** avg |
| LLM Extraction | **~3s/doc** (Qwen3.5-35B-A3B-FP8) |
| 일일 파이프라인 | **~5분** (277건 수집+추출+리포트) |
| 벤치마크 | **39/39** (100%) Grade A |

## 개발 이력

| 날짜 | 내용 |
|---|---|
| Phase 1 | 코어 모듈 (extraction, storage, retrieval, ingestion, generation, feedback) |
| Phase 2 | 성능 최적화 (VectorStore lazy loading 2.1x, parallel extraction, append-only temporal) |
| Phase 3 | vLLM 연동, 24시간 KB 빌드, source-grounding filter (P@5 71%→91%) |
| Phase 4 | 미구현 항목 완료 (recall@k/MRR, dashboard, QualityScorer/ProvenanceTracker 통합) |
| Phase 5 | Community detection (Louvain), 한국어 KB 구축 (4,662건) |
| Phase 6 | 일일 파이프라인 + RAG Q&A + Discord/Obsidian 연동 |
| Phase 7 | 3층 인텔리전스 리포트 (T/K/R 3축, 확인/해석/가설 분리, 2-pass 딥리드) |

## 라이선스

MIT
