from price_monitor.core.selection import select_listings_by_tokens

listings = [
    {"listing_id": "1", "Establecimiento": "Casa Negra", "Airbnb": "URL1"},
    {"listing_id": "2", "Establecimiento": "Viento de Glaciares", "Airbnb": "URL2"},
    {"listing_id": "3", "Establecimiento": "Cerro Eléctrico", "Airbnb": "URL3"},
]


def test_select_by_index():
    sel = select_listings_by_tokens(listings, "2")
    assert sel[0]["listing_id"] == "2"


def test_select_by_range():
    sel = select_listings_by_tokens(listings, "1-2")
    assert [l["listing_id"] for l in sel] == ["1", "2"]


def test_select_by_name_fragment():
    sel = select_listings_by_tokens(listings, "Negra")
    assert sel[0]["listing_id"] == "1"
