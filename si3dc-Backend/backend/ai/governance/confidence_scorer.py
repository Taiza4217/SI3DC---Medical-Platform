"""SI3DC — Confidence Scorer.

Classifies AI output confidence as HIGH, MEDIUM, LOW, or UNRELIABLE.
"""

from __future__ import annotations

from typing import Any


def classify_confidence(
    hallucination_count: int,
    data_completeness: float,
    response_length: int,
) -> dict[str, Any]:
    """
    Calculate and classify the confidence of an AI clinical output.

    Args:
        hallucination_count: Number of hallucination flags detected.
        data_completeness: Score from 0.0 to 1.0 indicating data availability.
        response_length: Length of the AI response text.

    Returns:
        Dictionary with score (0.0 - 1.0) and label (HIGH/MEDIUM/LOW/UNRELIABLE).
    """
    score = 1.0

    # Penalize hallucinations heavily
    score -= hallucination_count * 0.25

    # Reward data completeness
    score *= (0.3 + 0.7 * data_completeness)

    # Penalize very short responses (possibly incomplete)
    if response_length < 100:
        score *= 0.5
    elif response_length < 300:
        score *= 0.8

    # Clamp to [0, 1]
    score = max(0.0, min(1.0, score))

    # Label
    if score >= 0.8:
        label = "HIGH"
    elif score >= 0.6:
        label = "MEDIUM"
    elif score >= 0.3:
        label = "LOW"
    else:
        label = "UNRELIABLE"

    return {
        "score": round(score, 3),
        "label": label,
        "factors": {
            "hallucination_penalty": hallucination_count * 0.25,
            "data_completeness": round(data_completeness, 3),
            "response_length_factor": "adequate" if response_length >= 300 else "short",
        },
    }
