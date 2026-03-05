from legal_risk.similarity_engine import SimilarityEngine


def test_similarity_threshold_penalizes_near_matches() -> None:
    engine = SimilarityEngine(threshold=0.9, penalty_scale=10.0)

    a = [1.0, 0.0, 0.0, 0.0]
    b = [0.99, 0.01, 0.0, 0.0]
    risk = engine.evaluate_risk(a, b)

    assert risk["similarity"] >= 0.9
    assert risk["violation"] is True
    assert risk["penalty"] >= 0.0


def test_similarity_below_threshold_has_no_penalty() -> None:
    engine = SimilarityEngine(threshold=0.9, penalty_scale=10.0)

    a = [1.0, 0.0, 0.0, 0.0]
    b = [0.0, 1.0, 0.0, 0.0]
    risk = engine.evaluate_risk(a, b)

    assert risk["similarity"] < 0.9
    assert risk["violation"] is False
    assert risk["penalty"] == 0.0
