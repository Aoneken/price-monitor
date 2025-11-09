import os

import pytest
from playwright.sync_api import sync_playwright


@pytest.mark.integration
@pytest.mark.slow
def test_homepage_loads_and_has_core_ui(tmp_path):
    """
    E2E básico: levanta la webapp (debe estar ya corriendo en :8000 via task),
    navega a la home, toma screenshot y valida elementos clave.
    Requiere que la task 'webapp: Start' esté activa.
    """
    base_url = os.environ.get("PM_BASE_URL", "http://localhost:8000/")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        page.goto(base_url, wait_until="domcontentloaded")

        # Validar título y elementos clave
        assert "Price Monitor" in page.title()
        assert page.locator(".app-title").is_visible()
        assert page.get_by_role("tab", name="Configuración").is_visible()
        assert page.get_by_role("tab", name="Scraping").is_visible()
        assert page.get_by_role("tab", name="Jobs").is_visible()
        assert page.get_by_role("tab", name="Base de Datos").is_visible()
        assert page.get_by_role("tab", name="Análisis").is_visible()

        # Screenshot
        screenshots_dir = tmp_path / "screenshots"
        screenshots_dir.mkdir(parents=True, exist_ok=True)
        path = screenshots_dir / "homepage.png"
        page.screenshot(path=path.as_posix(), full_page=True)

        # Afirmación mínima de tamaño (>0 bytes)
        assert path.exists() and path.stat().st_size > 10_000

        context.close()
        browser.close()
