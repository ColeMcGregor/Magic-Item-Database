# tests/test_scraper_integration.py
import pytest
from townecodex.scraper import RedditScraper

# The real CSV sample rows (from your data)
CSV_SAMPLE_ROWS = [
    {
        "Name": "Freerunner's Armor",
        "Link": "https://www.reddit.com/r/TheGriffonsSaddlebag/comments/fxtwtd/the_griffons_saddlebag_freerunners_armor_armor/",
    },
    {
        "Name": "Hat of Osnomnosis",
        "Link": "https://www.reddit.com/r/TheGriffonsSaddlebag/comments/q6oa1v/the_griffons_saddlebag_hat_of_osnomnosis_wondrous/",
    },
    {
        "Name": "Sun and Moon Shield",
        "Link": "https://www.reddit.com/r/TheGriffonsSaddlebag/comments/r1zss3/the_griffons_saddlebag_sun_and_moon_shield_armor/",
    },
    {
        "Name": "Bath Potion",
        "Link": "https://www.reddit.com/r/TheGriffonsSaddlebag/comments/biqp7g/the_griffons_saddlebag_bath_potion_potion/",
    },
    {
        "Name": "Bloody Marilith",
        "Link": "https://www.reddit.com/r/TheGriffonsSaddlebag/comments/ekvzyu/the_griffons_saddlebag_bloody_marilith_potion/",
    },
    {
        "Name": "Relentless Bulwark",
        "Link": "https://www.reddit.com/r/TheGriffonsSaddlebag/comments/bgwgx7/the_griffons_saddlebag_relentless_bulwark_armor/",
    },
    {
        "Name": "Fused Chimeric Hide",
        "Link": "https://www.reddit.com/r/TheGriffonsSaddlebag/comments/ft1dfs/the_griffons_saddlebag_fused_chimeric_hide_armor/",
    },
    {
        "Name": "Bloodmage Dagger",
        "Link": "https://www.reddit.com/r/TheGriffonsSaddlebag/comments/bwpp3q/the_griffons_saddlebag_bloodmage_dagger_weapon/",
    },
]


def _trunc(s: str | None, n: int = 100) -> str:
    if not s:
        return "—"
    s = s.strip().replace("\n", " ")
    return s if len(s) <= n else s[: n - 1] + "…"


@pytest.mark.parametrize("row", CSV_SAMPLE_ROWS)
def test_fetch_post_data_live(row):
    """Integration test: hits Reddit live and parses.
    Prints a structured summary of what was returned.
    """
    data = RedditScraper.fetch_post_data(row["Link"])

    # --- Console summary (shown when running with: pytest -s) ---
    print(
        "\n".join(
            [
                "",
                f"[SCRAPER] Name:        {row['Name']}",
                f"[SCRAPER] URL:         {row['Link']}",
                f"[SCRAPER] Title:       {_trunc(data.get('title'), 120)}",
                f"[SCRAPER] Rarity:      {_trunc(data.get('rarity'), 60)}",
                f"[SCRAPER] Attunement:  {_trunc(data.get('attunement'), 80)}",
                f"[SCRAPER] Desc.len:    {len(data.get('description') or '')}",
                f"[SCRAPER] Image URL:   {_trunc(data.get('image_url'), 120)}",
                "-" * 72,
            ]
        )
    )

    # --- Assertions (unchanged in spirit) ---
    assert data["title"]  # should have a title
    assert isinstance(data["rarity"], str)
    assert isinstance(data["attunement"], str)
    # description and image may be None if post format varies, so just check presence of keys
    assert "description" in data
    assert "image_url" in data
