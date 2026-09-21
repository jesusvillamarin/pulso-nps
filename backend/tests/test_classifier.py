from app import classifier
from app.taxonomy import DEFAULT_TAXONOMY


def test_mock_classifier_returns_hierarchical_typed_result(monkeypatch) -> None:
    monkeypatch.setattr(classifier, "TYPESAFE_MOCK", True)
    result = classifier.classify_batch(
        [{"row_index": 1, "comment": "Me cobraron dos veces y nadie responde"}],
        DEFAULT_TAXONOMY,
    )[0]
    assert result["area"] == "Facturación"
    assert result["category"] == "Cobros"
    assert result["tone"] in {"Frustrado", "Agresivo", "Decepcionado", "Neutral", "Positivo", "Feliz", "Confundido"}
    assert 0 <= result["area_confidence"] <= 1
    assert abs(sum(result["area_probabilities"].values()) - 1) < 0.0001
