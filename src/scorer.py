def clamp_score(score):
    try:
        score = float(score)
    except (TypeError, ValueError):
        return 0.0

    if score < 0:
        return 0.0

    if score > 1:
        return 1.0

    return score


def combine_scores(
    person_match_score,
    employment_evidence_score,
    llm_confidence,
):
    person_match_score = clamp_score(person_match_score)
    employment_evidence_score = clamp_score(
        employment_evidence_score
    )
    llm_confidence = clamp_score(llm_confidence)

    final_score = (
        (person_match_score * 0.55)
        + (employment_evidence_score * 0.25)
        + (llm_confidence * 0.20)
    )

    return round(
        clamp_score(final_score),
        4,
    )