from price_monitor.providers.airbnb import extract_price_breakdown_from_html


def test_extract_price_breakdown_simple():
    html = (
        '<div>"productPriceBreakdown": '
        '{"priceBreakdown": {"total": {"total": '
        '{"amountMicros": 123456000000, "amountFormatted": "$123"}}, '
        '"priceItems": []}}</div>'
    )
    data = extract_price_breakdown_from_html(html)
    assert data is not None
    assert (data.get("total") or {}).get("total") is not None
