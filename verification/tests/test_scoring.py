"""Tests for the scoring engine (PromptLoader + AnthropicScorer)."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from echelon_verify.scoring.anthropic_scorer import AnthropicScorer, PromptLoader
from echelon_verify.config import ScoringConfig


# ---------------------------------------------------------------------------
# PromptLoader
# ---------------------------------------------------------------------------


class TestPromptLoader:
    def test_load_fills_placeholders(self):
        loader = PromptLoader("v1")
        result = loader.load(
            "precision",
            title="My PR",
            description="some desc",
            diff_content="diff here",
            claims_json='["claim1"]',
        )
        assert "My PR" in result
        assert "some desc" in result
        assert "diff here" in result
        assert '["claim1"]' in result

    def test_load_caches_templates(self):
        loader = PromptLoader("v1")
        first = loader.load("recall", title="T", description="D", diff_content="X", summary="S")
        second = loader.load("recall", title="T2", description="D2", diff_content="X2", summary="S2")
        # Both should work — template is cached
        assert "T" in first
        assert "T2" in second

    def test_load_unknown_prompt_raises(self):
        loader = PromptLoader("v1")
        with pytest.raises(KeyError):
            loader.load("nonexistent")


# ---------------------------------------------------------------------------
# AnthropicScorer
# ---------------------------------------------------------------------------


def _make_scorer() -> tuple[AnthropicScorer, AsyncMock]:
    """Create scorer with mocked Anthropic client."""
    config = ScoringConfig(api_key="test-key")
    scorer = AnthropicScorer(config)

    mock_client = AsyncMock()
    scorer._client = mock_client
    return scorer, mock_client


def _mock_response(text: str) -> MagicMock:
    """Create a mock Anthropic message response."""
    content_block = MagicMock()
    content_block.text = text
    response = MagicMock()
    response.content = [content_block]
    return response


@pytest.mark.asyncio
async def test_score_precision(sample_ground_truth, sample_oracle_output):
    scorer, mock_client = _make_scorer()
    mock_client.messages.create.return_value = _mock_response(
        json.dumps({
            "claims": [
                {"claim": "Added rate limiting", "supported": True, "evidence": "diff shows limiter"},
                {"claim": "Uses token bucket", "supported": True, "evidence": "RateLimiter class"},
                {"claim": "Max 100 requests", "supported": True, "evidence": "max_requests=100"},
            ],
            "precision": 1.0,
            "total": 3,
            "supported": 3,
        })
    )

    score, total, supported, raw = await scorer.score_precision(
        sample_ground_truth, sample_oracle_output
    )
    assert score == 1.0
    assert total == 3
    assert supported == 3
    assert "claims" in raw


@pytest.mark.asyncio
async def test_score_recall(sample_ground_truth, sample_oracle_output):
    scorer, mock_client = _make_scorer()
    mock_client.messages.create.return_value = _mock_response(
        json.dumps({
            "changes": [
                {"change": "Import RateLimiter", "surfaced": True},
                {"change": "Create limiter instance", "surfaced": True},
            ],
            "recall": 1.0,
            "total": 2,
            "surfaced": 2,
        })
    )

    score, total, surfaced, raw = await scorer.score_recall(
        sample_ground_truth, sample_oracle_output
    )
    assert score == 1.0
    assert total == 2
    assert surfaced == 2


@pytest.mark.asyncio
async def test_score_reply_accuracy(sample_ground_truth, sample_oracle_output):
    scorer, mock_client = _make_scorer()
    mock_client.messages.create.return_value = _mock_response(
        json.dumps({
            "accuracy": 0.75,
            "reasoning": "Mostly grounded",
            "grounded_claims": ["rate limit exists"],
            "fabricated_claims": ["429 status code not in diff"],
        })
    )

    score, raw = await scorer.score_reply_accuracy(
        sample_ground_truth, sample_oracle_output
    )
    assert score == 0.75
    assert "reasoning" in raw


@pytest.mark.asyncio
async def test_generate_follow_up_question(sample_ground_truth):
    scorer, mock_client = _make_scorer()
    mock_client.messages.create.return_value = _mock_response(
        "What is the maximum number of requests allowed per minute?"
    )

    question = await scorer.generate_follow_up_question(sample_ground_truth)
    assert "requests" in question.lower()


@pytest.mark.asyncio
async def test_json_parse_retry(sample_ground_truth, sample_oracle_output):
    """First LLM response is invalid JSON, retry succeeds."""
    scorer, mock_client = _make_scorer()

    good_json = json.dumps({
        "accuracy": 0.5,
        "reasoning": "ok",
        "grounded_claims": [],
        "fabricated_claims": [],
    })

    # First two calls: one initial + one retry from _call_llm failure...
    # But actually: _call_llm_json calls _call_llm which succeeds,
    # then json.loads fails on the text, so it retries with stricter prompt.
    mock_client.messages.create.side_effect = [
        _mock_response("This is not JSON at all"),
        _mock_response(good_json),
    ]

    score, raw = await scorer.score_reply_accuracy(
        sample_ground_truth, sample_oracle_output
    )
    assert score == 0.5
    assert mock_client.messages.create.call_count == 2


@pytest.mark.asyncio
async def test_json_parse_retry_strips_markdown_fences(sample_ground_truth, sample_oracle_output):
    """Retry strips markdown code fences from response."""
    scorer, mock_client = _make_scorer()

    good_json = json.dumps({
        "accuracy": 0.9,
        "reasoning": "good",
        "grounded_claims": ["claim"],
        "fabricated_claims": [],
    })

    mock_client.messages.create.side_effect = [
        _mock_response("not json"),
        _mock_response(f"```json\n{good_json}\n```"),
    ]

    score, raw = await scorer.score_reply_accuracy(
        sample_ground_truth, sample_oracle_output
    )
    assert score == 0.9
