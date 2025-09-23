import pytest
from townecodex.importer import _parse_attunement


@pytest.mark.parametrize("value,expected", [
    ("No", (False, None)),
    ("no", (False, None)),
    ("Yes", (True, None)),
    ("Yes - Dex 15", (True, "Dex 15")),
    ("missing", (False, None)),
    ("", (False, None)),
    (None, (False, None)),
    ("Dex 18 required", (True, "Dex 18 required")),  # fallback case
])
def test_parse_attunement_variants(value, expected):
    assert _parse_attunement(value) == expected
