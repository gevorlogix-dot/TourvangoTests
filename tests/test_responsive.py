import pytest
from playwright.sync_api import Page, Browser, expect

BASE_URL = "https://tourvango.testingforproduction.com"

MOBILE_VIEWPORT = {"width": 390, "height": 844}   # iPhone 14
TABLET_VIEWPORT = {"width": 768, "height": 1024}  # iPad


# ── Mobile ────────────────────────────────────────────────────────────────────

def test_homepage_loads_on_mobile(page: Page, browser: Browser):
    context = browser.new_context(viewport=MOBILE_VIEWPORT)
    mobile_page = context.new_page()
    mobile_page.goto(BASE_URL)
    mobile_page.wait_for_load_state("networkidle")
    expect(mobile_page.locator("body")).to_be_visible()
    body_text = mobile_page.locator("body").inner_text()
    assert len(body_text) > 100, "Homepage appears empty on mobile"
    context.close()


def test_mobile_has_hamburger_or_nav(page: Page, browser: Browser):
    context = browser.new_context(viewport=MOBILE_VIEWPORT)
    mobile_page = context.new_page()
    mobile_page.goto(BASE_URL)
    mobile_page.wait_for_load_state("networkidle")

    hamburger = mobile_page.locator(
        "button[aria-label*='menu' i], button[aria-label*='nav' i], "
        "[class*='hamburger'], [class*='burger'], [class*='menu-icon'], "
        "button[class*='toggle'], .navbar-toggler"
    )
    nav = mobile_page.locator("nav, header")

    has_hamburger = hamburger.count() > 0
    has_nav = nav.count() > 0
    assert has_hamburger or has_nav, "Mobile should show hamburger button or navigation"
    context.close()


def test_mobile_booking_form_visible(page: Page, browser: Browser):
    context = browser.new_context(viewport=MOBILE_VIEWPORT)
    mobile_page = context.new_page()
    mobile_page.goto(BASE_URL)
    mobile_page.wait_for_load_state("networkidle")
    form = mobile_page.locator("form").first
    expect(form).to_be_visible()
    context.close()


def test_mobile_contact_page_form_visible(page: Page, browser: Browser):
    context = browser.new_context(viewport=MOBILE_VIEWPORT)
    mobile_page = context.new_page()
    mobile_page.goto(f"{BASE_URL}/contact-us")
    mobile_page.wait_for_load_state("networkidle")
    form = mobile_page.locator("form").first
    expect(form).to_be_visible()
    context.close()


def test_mobile_fleet_page_loads(page: Page, browser: Browser):
    context = browser.new_context(viewport=MOBILE_VIEWPORT)
    mobile_page = context.new_page()
    mobile_page.goto(f"{BASE_URL}/vehicles")
    mobile_page.wait_for_load_state("networkidle")
    expect(mobile_page.locator("body")).to_be_visible()
    body_text = mobile_page.locator("body").inner_text()
    assert len(body_text) > 100
    context.close()


def test_mobile_footer_visible(page: Page, browser: Browser):
    context = browser.new_context(viewport=MOBILE_VIEWPORT)
    mobile_page = context.new_page()
    mobile_page.goto(BASE_URL)
    mobile_page.wait_for_load_state("networkidle")
    footer = mobile_page.locator("footer")
    expect(footer).to_be_visible()
    context.close()


def test_mobile_no_horizontal_scroll(page: Page, browser: Browser):
    context = browser.new_context(viewport=MOBILE_VIEWPORT)
    mobile_page = context.new_page()
    mobile_page.goto(BASE_URL)
    mobile_page.wait_for_load_state("networkidle")
    scroll_width = mobile_page.evaluate("document.documentElement.scrollWidth")
    client_width = mobile_page.evaluate("document.documentElement.clientWidth")
    assert scroll_width <= client_width + 5, \
        f"Horizontal scroll detected on mobile: scrollWidth={scroll_width}, clientWidth={client_width}"
    context.close()


def test_mobile_faq_page_loads(page: Page, browser: Browser):
    context = browser.new_context(viewport=MOBILE_VIEWPORT)
    mobile_page = context.new_page()
    mobile_page.goto(f"{BASE_URL}/faq")
    mobile_page.wait_for_load_state("networkidle")
    expect(mobile_page.locator("body")).to_be_visible()
    body_text = mobile_page.locator("body").inner_text()
    assert "?" in body_text, "FAQ questions not visible on mobile"
    context.close()


# ── Tablet ────────────────────────────────────────────────────────────────────

def test_tablet_homepage_loads(page: Page, browser: Browser):
    context = browser.new_context(viewport=TABLET_VIEWPORT)
    tablet_page = context.new_page()
    tablet_page.goto(BASE_URL)
    tablet_page.wait_for_load_state("networkidle")
    expect(tablet_page.locator("body")).to_be_visible()
    context.close()


def test_tablet_booking_form_visible(page: Page, browser: Browser):
    context = browser.new_context(viewport=TABLET_VIEWPORT)
    tablet_page = context.new_page()
    tablet_page.goto(BASE_URL)
    tablet_page.wait_for_load_state("networkidle")
    form = tablet_page.locator("form").first
    expect(form).to_be_visible()
    context.close()


def test_tablet_fleet_page_loads(page: Page, browser: Browser):
    context = browser.new_context(viewport=TABLET_VIEWPORT)
    tablet_page = context.new_page()
    tablet_page.goto(f"{BASE_URL}/vehicles")
    tablet_page.wait_for_load_state("networkidle")
    expect(tablet_page.locator("body")).to_be_visible()
    context.close()


# ── Desktop wide ──────────────────────────────────────────────────────────────

def test_desktop_wide_homepage_loads(page: Page, browser: Browser):
    context = browser.new_context(viewport={"width": 1920, "height": 1080})
    wide_page = context.new_page()
    wide_page.goto(BASE_URL)
    wide_page.wait_for_load_state("networkidle")
    expect(wide_page.locator("body")).to_be_visible()
    context.close()
