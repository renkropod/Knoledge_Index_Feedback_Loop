from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import importlib
import json

from extraction import Deduplicator
from extraction import EntityExtractor
from extraction import RelationMapper

pytest = importlib.import_module("pytest")


class MockLLMClient:
    class messages:
        @staticmethod
        async def create(**kwargs):
            class Block:
                text = '{"entities": [{"name": "Ethereum", "type": "PROTOCOL", "description": "smart contract platform"}], "relations": []}'

            class Resp:
                content = [Block()]

            return Resp()


def test_split_text_empty_text():
    extractor = EntityExtractor(llm_client=MockLLMClient())
    assert extractor._split_text("", chunk_size=100, overlap=10) == []


def test_split_text_short_text(sample_text):
    extractor = EntityExtractor(llm_client=MockLLMClient())
    short = sample_text[:30]
    result = extractor._split_text(short, chunk_size=200, overlap=20)
    assert len(result) == 1
    assert result[0] == short.strip()


def test_split_text_overlapping_chunks():
    extractor = EntityExtractor(llm_client=MockLLMClient())
    text = "abcdefghijklmnopqrstuvwxyz"
    chunks = extractor._split_text(text, chunk_size=10, overlap=2)
    assert chunks == ["abcdefghij", "ijklmnopqr", "qrstuvwxyz"]
    assert chunks[0][-2:] == chunks[1][:2]
    assert chunks[1][-2:] == chunks[2][:2]


def test_split_text_exact_chunk_boundary():
    extractor = EntityExtractor(llm_client=MockLLMClient())
    text = "1234567890"
    chunks = extractor._split_text(text, chunk_size=5, overlap=0)
    assert chunks == ["12345", "67890"]


def test_parse_json_valid_json():
    extractor = EntityExtractor(llm_client=MockLLMClient())
    payload = extractor._parse_json('{"entities": [], "relations": []}')
    assert payload == {"entities": [], "relations": []}


def test_parse_json_markdown_fence():
    extractor = EntityExtractor(llm_client=MockLLMClient())
    payload = extractor._parse_json('```json\n{"entities": [], "relations": []}\n```')
    assert payload == {"entities": [], "relations": []}


def test_parse_json_with_surrounding_text():
    extractor = EntityExtractor(llm_client=MockLLMClient())
    payload = extractor._parse_json(
        'Result follows: {"entities": [{"name": "A"}], "relations": []} done'
    )
    assert payload["entities"][0]["name"] == "A"


def test_parse_json_empty_input_raises():
    extractor = EntityExtractor(llm_client=MockLLMClient())
    with pytest.raises(json.JSONDecodeError):
        extractor._parse_json("")


def test_parse_json_invalid_json_raises():
    extractor = EntityExtractor(llm_client=MockLLMClient())
    with pytest.raises(json.JSONDecodeError):
        extractor._parse_json("{not valid}")


@pytest.mark.asyncio
async def test_extract_uses_mock_llm(sample_text):
    extractor = EntityExtractor(llm_client=MockLLMClient())
    result = await extractor.extract(sample_text[:120], chunk_size=500)
    assert result["entities"][0]["name"] == "Ethereum"
    assert result["entities"][0]["chunk_index"] == 0


def test_deduplicate_merges_aliases_normalizes_relations_and_clamps_weights(
    sample_relations,
):
    deduplicator = Deduplicator()
    entities = [
        {"name": "ETH", "type": "PROTOCOL", "description": "Ethereum base layer"},
        {"name": "Ethereum", "type": "", "description": "Decentralized chain"},
        {"name": "Bitcoin", "type": "PROTOCOL", "description": "BTC network"},
    ]
    relations = sample_relations + [
        {
            "source": "eth",
            "target": "btc",
            "relation": "influences",
            "description": "Alias relation",
            "weight": 1.8,
        },
        {
            "source": "ETH",
            "target": "BTC",
            "relation": "INFLUENCES",
            "description": "Duplicate lower confidence",
            "weight": -1,
        },
    ]

    result = deduplicator.deduplicate(entities, relations)
    names = {entity["name"] for entity in result["entities"]}
    assert names == {"Ethereum", "Bitcoin"}
    eth_entity = next(
        entity for entity in result["entities"] if entity["name"] == "Ethereum"
    )
    assert "Ethereum base layer" in eth_entity["description"]
    assert "Decentralized chain" in eth_entity["description"]

    normalized = [
        rel
        for rel in result["relations"]
        if rel["source"] == "Ethereum" and rel["target"] == "Bitcoin"
    ]
    assert len(normalized) == 1
    assert normalized[0]["relation"] == "INFLUENCES"
    assert normalized[0]["weight"] == 1.0


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        ("", "desc", "desc"),
        ("desc", "", "desc"),
        ("short", "short and more", "short and more"),
        ("left", "right", "right | left"),
    ],
)
def test_merge_description_cases(left, right, expected):
    deduplicator = Deduplicator()
    assert deduplicator._merge_description(left, right) == expected


def test_infer_co_occurrence_same_chunk_pairs():
    mapper = RelationMapper()
    entities = [
        {"name": "Ethereum", "chunk_index": 0},
        {"name": "Optimism", "chunk_index": 0},
        {"name": "DeFi", "chunk_index": 0},
    ]
    relations = mapper.infer_co_occurrence(entities)
    pairs = {(rel["source"], rel["target"]) for rel in relations}
    assert len(relations) == 3
    assert ("Ethereum", "Optimism") in pairs
    assert ("Ethereum", "DeFi") in pairs
    assert ("Optimism", "DeFi") in pairs


def test_infer_co_occurrence_cross_chunk_no_pairs():
    mapper = RelationMapper()
    entities = [
        {"name": "Ethereum", "chunk_index": 0},
        {"name": "Optimism", "chunk_index": 1},
    ]
    assert mapper.infer_co_occurrence(entities) == []


def test_infer_co_occurrence_empty_input():
    mapper = RelationMapper()
    assert mapper.infer_co_occurrence([]) == []


def test_infer_hierarchical_protocol_token_same_chunk():
    mapper = RelationMapper()
    entities = [
        {
            "name": "Ethereum",
            "type": "PROTOCOL",
            "description": "base",
            "chunk_index": 2,
        },
        {
            "name": "OP Token",
            "type": "CONCEPT",
            "description": "token used in Ethereum governance",
            "chunk_index": 2,
        },
    ]
    relations = mapper.infer_hierarchical(entities)
    assert len(relations) == 1
    assert relations[0]["source"] == "OP Token"
    assert relations[0]["target"] == "Ethereum"
    assert relations[0]["relation"] == "PART_OF"


def test_infer_hierarchical_no_match():
    mapper = RelationMapper()
    entities = [
        {
            "name": "Ethereum",
            "type": "PROTOCOL",
            "description": "base",
            "chunk_index": 0,
        },
        {
            "name": "USDC",
            "type": "CONCEPT",
            "description": "stable asset on another chain",
            "chunk_index": 1,
        },
    ]
    assert mapper.infer_hierarchical(entities) == []
