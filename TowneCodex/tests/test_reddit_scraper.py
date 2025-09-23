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
        "Name": "Bulletin Buckler",
        "Link": "https://www.reddit.com/r/TheGriffonsSaddlebag/comments/1f792nd/the_griffons_saddlebag_bulletin_buckler_armor/",
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
]


@pytest.mark.parametrize("row", CSV_SAMPLE_ROWS)
def test_fetch_post_data_live(row):
    """Integration test: hits Reddit live and parses."""
    data = RedditScraper.fetch_post_data(row["Link"])
    assert data["title"]  # should have a title
    assert isinstance(data["rarity"], str)
    assert isinstance(data["attunement"], str)
    # description and image may be None if post format varies, so just check type
    assert "description" in data
    assert "image_url" in data
