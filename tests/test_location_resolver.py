import pytest

from services.location_resolver import resolve_location_to_iata


@pytest.mark.parametrize(
    ("location", "expected"),
    [
        ("Athens", "ATH"),
        ("Greece", "ATH"),
        ("ATH", "ATH"),
        ("Tokyo", "NRT"),
        ("Japan", "NRT"),
        ("Rome", "FCO"),
        ("Italy", "FCO"),
        ("my city", None),
        ("some completely unknown place", None),
    ],
)

def test_resolve_location_to_iata(
    location: str,
    expected: str | None,
) -> None:
    assert resolve_location_to_iata(location) == expected