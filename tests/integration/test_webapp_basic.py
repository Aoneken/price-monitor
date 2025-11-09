from datetime import date


def test_workspace_and_season_crud(test_client):
    # Create workspace
    r = test_client.post("/api/workspaces", json={"name": "TestWS"})
    assert r.status_code == 200
    ws_id = r.json()["id"]

    # List workspaces
    r = test_client.get("/api/workspaces")
    assert any(w["id"] == ws_id for w in r.json())

    # Create season
    payload = {"name": "Temp", "start_date": "2025-12-01", "end_date": "2025-12-05"}
    r = test_client.post(f"/api/workspaces/{ws_id}/seasons", json=payload)
    assert r.status_code == 200
    season_id = r.json()["id"]

    r = test_client.get(f"/api/workspaces/{ws_id}/seasons")
    assert any(s["id"] == season_id for s in r.json())


def test_listing_and_scrape_job(test_client):
    # Ensure default workspace exists by triggering startup endpoint usage
    r = test_client.post(
        "/api/listings",
        json={
            "listing_id": "dummy123",
            "name": "Dummy Listing",
            "url": "https://www.airbnb.com.ar/rooms/dummy123",
            "provider": "airbnb",
        },
    )
    assert r.status_code == 200, r.text
    listing_id = r.json()["id"]

    # Create a scrape job with short date range
    job_payload = {
        "listing_id": listing_id,
        "start_date": str(date.today()),
        "end_date": str(date.today()),
        "guests": 2,
        "provider": "airbnb",
        "params": {
            "currency": "USD",
            "locale": "en",
            "delay": 0.2,
            "retries": 1,
            "concurrency": 2,
        },
    }
    r = test_client.post("/api/scrape", json=job_payload)
    assert r.status_code == 200, r.text
    job_id = r.json()["id"]

    # Poll job status until completed/failed (simple loop, small timeout)
    for _ in range(25):
        status_resp = test_client.get(f"/api/jobs/{job_id}")
        assert status_resp.status_code == 200
        status = status_resp.json()["status"]
        if status in ("completed", "failed"):
            break
    else:
        raise AssertionError("Job did not finish in time")

    # Fetch prices
    price_url = (
        f"/api/prices/{listing_id}?start_date={date.today()}&end_date="
        f"{date.today()}"
    )
    price_resp = test_client.get(price_url)
    assert price_resp.status_code == 200
    prices = price_resp.json()
    # We don't assert >0 because remote call may fail; just ensure structure
    assert isinstance(prices, list)
    if prices:
        sample = prices[0]
        assert "date" in sample and "currency" in sample


def test_export_snapshots_empty(test_client):
    # Basic call with season id that may not exist yet just to hit endpoint
    r = test_client.get(
        "/api/seasons/0/snapshots?date_from=2025-12-01&date_to=2025-12-02"
    )
    # Should return CSV (200) even if empty
    assert r.status_code == 200
    assert r.text.startswith("date,available,")
