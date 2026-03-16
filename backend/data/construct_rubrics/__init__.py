"""Construct rubric registry — dispatches slug to domain-specific rubric functions."""

import logging
from typing import Callable, Optional

from backend.data.construct_rubrics.artisan_rubrics import ARTISAN_RUBRICS
from backend.data.construct_rubrics.khole_rubrics import KHOLE_RUBRICS
from backend.data.construct_rubrics.mibera_codex_rubrics import MIBERA_CODEX_RUBRICS

logger = logging.getLogger(__name__)

# Slug → rubrics mapping
_RUBRIC_REGISTRY: dict[str, dict[str, Callable]] = {
    "artisan": ARTISAN_RUBRICS,
    "khole": KHOLE_RUBRICS,
    "mibera-codex": MIBERA_CODEX_RUBRICS,
}


def get_rubrics(construct_slug: str) -> Optional[dict[str, Callable]]:
    """Lookup rubrics for a construct by slug.

    Returns None if no rubrics are registered for the slug.
    """
    rubrics = _RUBRIC_REGISTRY.get(construct_slug)
    if rubrics is None:
        logger.warning("No rubrics registered for construct slug '%s'", construct_slug)
    return rubrics
