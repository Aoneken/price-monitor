"""E2E UI Audit - Captura screenshots y detecta funcionalidades faltantes."""

import json
from pathlib import Path

from playwright.sync_api import sync_playwright


def run_ui_audit():
    """Run comprehensive UI audit with screenshots and functionality checks."""
    base_url = "http://127.0.0.1:8000"
    screenshots_dir = Path("tests/e2e_screenshots")
    screenshots_dir.mkdir(exist_ok=True, parents=True)

    audit_results = {"missing_features": [], "ui_issues": [], "screenshots": []}

    with sync_playwright() as p:
        # Use chromium in headless mode (avoid dependencies warning)
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        try:
            # Test 1: Homepage / Initial state
            print("📸 Capturando homepage...")
            page.goto(base_url, wait_until="networkidle", timeout=10000)
            page.screenshot(path=str(screenshots_dir / "01_homepage.png"))
            audit_results["screenshots"].append("01_homepage.png")

            # Check for critical elements
            if not page.query_selector("#focus-select"):
                audit_results["missing_features"].append("Focus selector not found")

            if not page.query_selector("#season-select"):
                audit_results["missing_features"].append("Season selector not found")

            # Check for "Nuevo Focus" button
            new_focus_btn = page.query_selector('button:has-text("Nuevo Focus")')
            if not new_focus_btn:
                audit_results["missing_features"].append("'Nuevo Focus' button missing")

            # Test 2: Try to create a workspace
            print("📸 Probando creación de workspace...")
            if new_focus_btn:
                new_focus_btn.click()
                page.wait_for_timeout(500)
                page.screenshot(path=str(screenshots_dir / "02_new_focus_modal.png"))
                audit_results["screenshots"].append("02_new_focus_modal.png")

                # Fill and submit
                name_input = page.query_selector("#workspace-name")
                if name_input:
                    name_input.fill("Test Workspace E2E")
                    page.screenshot(
                        path=str(screenshots_dir / "03_focus_form_filled.png")
                    )
                    audit_results["screenshots"].append("03_focus_form_filled.png")

                    submit_btn = page.query_selector(
                        'button[type="submit"]:has-text("Crear Focus")'
                    )
                    if submit_btn:
                        submit_btn.click()
                        page.wait_for_timeout(1000)
                        page.screenshot(
                            path=str(screenshots_dir / "04_after_focus_created.png")
                        )
                        audit_results["screenshots"].append(
                            "04_after_focus_created.png"
                        )

            # Test 3: Check configuration tabs
            print("📸 Probando pestañas de configuración...")
            config_tab = page.query_selector('button.tab:has-text("Configuración")')
            if config_tab:
                config_tab.click()
                page.wait_for_timeout(300)

                # Check for subtabs
                subtabs = ["Ajustes", "Temporadas", "Establecimientos"]
                for subtab_name in subtabs:
                    subtab = page.query_selector(f'button:has-text("{subtab_name}")')
                    if not subtab:
                        audit_results["missing_features"].append(
                            f"'{subtab_name}' subtab missing"
                        )
                    else:
                        subtab.click()
                        page.wait_for_timeout(300)
                        screenshot_name = f"05_subtab_{subtab_name.lower()}.png"
                        page.screenshot(path=str(screenshots_dir / screenshot_name))
                        audit_results["screenshots"].append(screenshot_name)
            else:
                audit_results["missing_features"].append("Configuration tab not found")

            # Test 4: Check for season creation form
            print("📸 Verificando formulario de temporadas...")
            seasons_btn = page.query_selector('button:has-text("Temporadas")')
            if seasons_btn:
                seasons_btn.click()
                page.wait_for_timeout(300)

                season_form = page.query_selector("#new-season-form")
                if not season_form:
                    audit_results["missing_features"].append(
                        "Season creation form missing"
                    )
                else:
                    page.screenshot(path=str(screenshots_dir / "06_seasons_form.png"))
                    audit_results["screenshots"].append("06_seasons_form.png")

                    # Try to create a season
                    name_field = page.query_selector("#season-name")
                    start_field = page.query_selector("#season-start")
                    end_field = page.query_selector("#season-end")

                    if name_field and start_field and end_field:
                        name_field.fill("Temporada Alta 2025")
                        start_field.fill("2025-12-01")
                        end_field.fill("2025-12-31")
                        page.screenshot(
                            path=str(screenshots_dir / "07_season_form_filled.png")
                        )
                        audit_results["screenshots"].append("07_season_form_filled.png")

                        season_submit = page.query_selector(
                            "#new-season-form button[type='submit']"
                        )
                        if season_submit:
                            season_submit.click()
                            page.wait_for_timeout(1000)
                            page.screenshot(
                                path=str(
                                    screenshots_dir / "08_after_season_created.png"
                                )
                            )
                            audit_results["screenshots"].append(
                                "08_after_season_created.png"
                            )

            # Test 5: Check listings/establishments
            print("📸 Verificando establecimientos...")
            listings_btn = page.query_selector('button:has-text("Establecimientos")')
            if listings_btn:
                listings_btn.click()
                page.wait_for_timeout(300)
                page.screenshot(path=str(screenshots_dir / "09_listings_view.png"))
                audit_results["screenshots"].append("09_listings_view.png")

                listing_form = page.query_selector("#new-listing-form")
                if not listing_form:
                    audit_results["missing_features"].append(
                        "Listing creation form missing"
                    )
                else:
                    # Check for scrape buttons
                    scrape_buttons = page.query_selector_all(
                        'button:has-text("Scrape")'
                    )
                    if len(scrape_buttons) == 0:
                        audit_results["ui_issues"].append(
                            "No 'Scrape' buttons visible in listings table"
                        )

            # Test 6: Check for scrape modal
            print("📸 Verificando modal de scrape...")
            scrape_modal = page.query_selector("#scrape-modal")
            if not scrape_modal:
                audit_results["missing_features"].append(
                    "Scrape modal (#scrape-modal) not found in DOM"
                )

            # Test 7: Check for additional missing tabs/features from spec
            print("📸 Verificando tabs adicionales...")

            # According to spec, should have tabs for:
            # - Scraping (to launch jobs)
            # - Jobs (to see history)
            # - Reports/Analytics

            tabs_expected = ["Configuración"]  # At minimum
            tabs_found = page.query_selector_all(".tab")
            if len(tabs_found) < 2:
                audit_results["ui_issues"].append(
                    f"Only {len(tabs_found)} main tab(s) found. Expected more (Scraping, Jobs, etc.)"
                )

            # Test 8: Check for progress bar and WebSocket readiness
            progress_bar = page.query_selector(".progress-bar")
            if not progress_bar:
                audit_results["ui_issues"].append("Progress bar component missing")

            # Test 9: Check for toast container
            toast_container = page.query_selector("#toast-container")
            if not toast_container:
                audit_results["ui_issues"].append(
                    "Toast notification container missing"
                )

            # Test 10: Check mobile responsiveness by changing viewport
            print("📸 Probando vista mobile...")
            page.set_viewport_size({"width": 375, "height": 667})
            page.wait_for_timeout(300)
            page.screenshot(path=str(screenshots_dir / "10_mobile_view.png"))
            audit_results["screenshots"].append("10_mobile_view.png")

            # Check if header stacks properly
            header = page.query_selector(".app-header")
            if header:
                header_height = header.bounding_box()["height"]
                if header_height < 150:
                    audit_results["ui_issues"].append(
                        "Header might not be responsive (too short on mobile)"
                    )

            # Test 11: Desktop view with full features
            print("📸 Vista desktop completa...")
            page.set_viewport_size({"width": 1920, "height": 1080})
            page.wait_for_timeout(300)
            page.screenshot(
                path=str(screenshots_dir / "11_desktop_full.png"), full_page=True
            )
            audit_results["screenshots"].append("11_desktop_full.png")

            # Test 12: Check color scheme and professional appearance
            print("📸 Analizando estilos...")
            body_bg = page.evaluate("window.getComputedStyle(document.body).background")
            if "linear-gradient" not in body_bg.lower():
                audit_results["ui_issues"].append(
                    "Background gradient might be missing"
                )

            # Final screenshot
            page.screenshot(path=str(screenshots_dir / "12_final_state.png"))
            audit_results["screenshots"].append("12_final_state.png")

        except Exception as e:
            audit_results["ui_issues"].append(f"Test execution error: {str(e)}")
            page.screenshot(path=str(screenshots_dir / "error_state.png"))
            audit_results["screenshots"].append("error_state.png")

        finally:
            browser.close()

    # Save audit report
    report_path = screenshots_dir / "audit_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(audit_results, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Audit complete. Report saved to {report_path}")
    print(f"📸 {len(audit_results['screenshots'])} screenshots captured")
    print(f"⚠️  {len(audit_results['missing_features'])} missing features detected")
    print(f"🔍 {len(audit_results['ui_issues'])} UI issues detected")

    if audit_results["missing_features"]:
        print("\n❌ MISSING FEATURES:")
        for feature in audit_results["missing_features"]:
            print(f"   - {feature}")

    if audit_results["ui_issues"]:
        print("\n⚠️  UI ISSUES:")
        for issue in audit_results["ui_issues"]:
            print(f"   - {issue}")

    return audit_results


if __name__ == "__main__":
    run_ui_audit()
