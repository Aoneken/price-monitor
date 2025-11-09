import os

import pytest
from playwright.sync_api import sync_playwright


@pytest.mark.integration
@pytest.mark.slow
def test_tabs_and_buttons_no_console_errors(tmp_path):
    base_url = os.environ.get("PM_BASE_URL", "http://localhost:8000/")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()
        console_errors = []

        def on_console(msg):
            if msg.type == "error":
                console_errors.append(msg.text)

        page.on("console", on_console)
        page.goto(base_url, wait_until="networkidle")

        # Abrir modal Nuevo Workspace y cerrarlo para no bloquear clicks
        page.get_by_role("button", name="Nuevo Workspace").click()
        modal = page.locator("#new-focus-modal")
        assert modal.is_visible()
        modal.click(position={"x": 5, "y": 5})
        modal.wait_for(state="hidden")

        # Navegar tabs y validar visibles
        tabs = [
            ("Configuración", "config-tab"),
            ("Scraping", "scraping-tab"),
            ("Jobs", "jobs-tab"),
            ("Base de Datos", "database-tab"),
            ("Análisis", "analytics-tab"),
        ]

        for name, content_id in tabs:
            page.get_by_role("tab", name=name).click()
            el = page.locator(f"#{content_id}")
            assert el.is_visible()

        # Capturas de pantallas por pestaña
        screenshots = tmp_path / "screenshots"
        screenshots.mkdir(parents=True, exist_ok=True)
        for name, _ in tabs:
            page.get_by_role("tab", name=name).click()
            shot_path = screenshots / f"tab_{name}.png"
            page.screenshot(path=shot_path.as_posix())
            assert shot_path.exists() and shot_path.stat().st_size > 10_000

        # Validar que no hubo errores de consola
        assert not console_errors, f"Console errors: {console_errors}"

        context.close()
        browser.close()
