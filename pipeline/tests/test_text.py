from plumes.readmodels import fl_gloss, ja_leftovers


def test_flight_level_gloss_in_both_languages():
    assert fl_gloss(550) == {"en": "FL550 (about 16.8 km)", "ja": "FL550（約16.8 km）"}


def test_japanese_text_is_clean_of_english_dates_and_half_width_brackets():
    ja = f"東京VAACは2020年1月12日に最高{fl_gloss(550)['ja']}の火山灰を観測した。"
    assert ja_leftovers(ja) == []
    assert ja_leftovers("最高FL550 (about 16.8 km)") == ["(", "about", ")"]
    assert ja_leftovers("2020-01-12、n/a") == ["2020-01-12", "n/a"]
