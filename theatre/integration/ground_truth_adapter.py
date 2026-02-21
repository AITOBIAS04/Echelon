"""Ground Truth Adapter — converts PR records to Theatre GroundTruthEpisodes."""

from __future__ import annotations

from theatre.engine.models import GroundTruthEpisode
from theatre.integration.models import GroundTruthRecord


def convert_record_to_episode(
    record: GroundTruthRecord,
    follow_up_question: str = "",
) -> GroundTruthEpisode:
    """Convert a single GroundTruthRecord to a GroundTruthEpisode.

    Args:
        record: PR-specific ground truth record.
        follow_up_question: Pre-generated follow-up question for this PR.

    Returns:
        A GroundTruthEpisode with PR data packed into input_data.
    """
    return GroundTruthEpisode(
        episode_id=record.id,
        input_data={
            "title": record.title,
            "description": record.description,
            "diff_content": record.diff_content,
            "files_changed": record.files_changed,
            "follow_up_question": follow_up_question,
        },
        expected_output=None,
        labels={
            "author": record.author,
            "url": record.url,
            "repo": record.repo,
            "github_labels": record.labels,
        },
        metadata={
            "timestamp": record.timestamp.isoformat(),
        },
    )


def convert_records_to_episodes(
    records: list[GroundTruthRecord],
    follow_up_questions: dict[str, str],
) -> list[GroundTruthEpisode]:
    """Convert a batch of records to episodes.

    Args:
        records: PR-specific ground truth records.
        follow_up_questions: Mapping of record.id → follow-up question.

    Returns:
        List of GroundTruthEpisodes in the same order as records.
    """
    return [
        convert_record_to_episode(
            record=r,
            follow_up_question=follow_up_questions.get(r.id, ""),
        )
        for r in records
    ]


class GroundTruthAdapter:
    """Stateful adapter for converting PR records to Theatre episodes.

    Holds the follow-up questions so they can be generated once and reused.
    """

    def __init__(self) -> None:
        self._follow_up_questions: dict[str, str] = {}

    def set_follow_up_questions(self, questions: dict[str, str]) -> None:
        self._follow_up_questions = dict(questions)

    def convert(self, records: list[GroundTruthRecord]) -> list[GroundTruthEpisode]:
        return convert_records_to_episodes(records, self._follow_up_questions)
