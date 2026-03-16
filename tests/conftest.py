from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def tmp_dir(tmp_path):
    return tmp_path


@pytest.fixture
def graph_path(tmp_path):
    return str(tmp_path / "test_kg.json")


@pytest.fixture
def temporal_path(tmp_path):
    return str(tmp_path / "test_facts.jsonl")


@pytest.fixture
def vector_path(tmp_path):
    return str(tmp_path / "test_vectors")


@pytest.fixture
def sample_entities():
    return [
        {
            "name": "Ethereum",
            "type": "PROTOCOL",
            "description": "Decentralized smart contract platform",
        },
        {
            "name": "Optimism",
            "type": "L2_SOLUTION",
            "description": "Ethereum optimistic rollup",
        },
        {
            "name": "Bitcoin",
            "type": "PROTOCOL",
            "description": "Decentralized digital currency",
        },
        {
            "name": "Solana",
            "type": "PROTOCOL",
            "description": "High-throughput blockchain",
        },
        {
            "name": "DeFi",
            "type": "CONCEPT",
            "description": "Decentralized Finance ecosystem",
        },
    ]


@pytest.fixture
def sample_relations():
    return [
        {
            "source": "Optimism",
            "target": "Ethereum",
            "relation": "LAYER2_OF",
            "description": "Optimism is L2 of Ethereum",
            "weight": 0.9,
        },
        {
            "source": "DeFi",
            "target": "Ethereum",
            "relation": "BUILT_ON",
            "description": "DeFi ecosystem built on Ethereum",
            "weight": 0.85,
        },
        {
            "source": "Bitcoin",
            "target": "DeFi",
            "relation": "INFLUENCES",
            "description": "BTC price affects DeFi",
            "weight": 0.6,
        },
    ]


@pytest.fixture
def sample_text():
    return (
        "Ethereum is the leading smart contract platform. Optimism is an optimistic rollup "
        "Layer 2 solution built on Ethereum to improve scalability. The DeFi ecosystem on "
        "Ethereum has grown significantly, with total value locked exceeding $50 billion. "
        "Bitcoin remains the dominant cryptocurrency by market cap, but Ethereum's DeFi "
        "ecosystem has created new financial primitives. Solana offers an alternative with "
        "higher throughput but different security trade-offs."
    )
