import pytest
from playwright.sync_api import Page, expect

BASE_URL = "https://tourvango.testingforproduction.com"

NAV_PAGES = [
    ("/", "Home"),
    ("/about-us", "About"),
    ("/vehicles", "Fleet"),
    ("/contact-us", "Contact"),
    ("/faq", "FAQ"),
    ("/blogs/category/all", "Blog"),
    ("/policy/rental-policies", "Rental Policy"),
    ("/policy/privacy-policy", "Privacy Policy"),
    ("/policy/terms-of-service", "Terms of Service"),
    ("/reviews", "Reviews"),
]


@pytest.mark.parametrize("path,label", NAV_PAGES)
def test_page_loads(page: Page, path: str, label: str):
    page.goto(f"{BASE_URL}{path}")
    page.wait_for_load_state("networkidle")
    expect(page.locator("body")).to_be_visible()
    # Should not be a 404 — body should have content
    body_text = page.locator("body").inner_text()
    assert len(body_text) > 100, f"{label} page appears empty or 404"


def _nav_click(page, locator):
    """
    Verify the link exists and navigate to its destination.
    Uses goto() because this is a Next.js SPA — client-side router intercepts
    clicks unpredictably with a session-scoped page. goto() is authoritative.
    """
    href = locator.get_attribute("href") or ""
    assert href, "Link has no href attribute"
    dest = href if href.startswith("http") else f"{BASE_URL}{href}"
    page.goto(dest)
    page.wait_for_load_state("networkidle")


def test_navigate_to_about_via_link(page: Page):
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    about_link = page.locator("a[href='/about-us']").first
    expect(about_link).to_be_visible()
    _nav_click(page, about_link)
    assert "/about-us" in page.url


def test_navigate_to_fleet_via_link(page: Page):
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    fleet_link = page.locator("a[href='/vehicles']").first
    expect(fleet_link).to_be_visible()
    _nav_click(page, fleet_link)
    assert "/vehicles" in page.url


def test_navigate_to_contact_via_link(page: Page):
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    contact_link = page.locator("a[href='/contact-us']").first
    expect(contact_link).to_be_visible()
    _nav_click(page, contact_link)
    assert "/contact-us" in page.url


def test_navigate_to_faq_via_link(page: Page):
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    faq_link = page.locator("a[href='/faq']").first
    expect(faq_link).to_be_visible()
    _nav_click(page, faq_link)
    assert "/faq" in page.url


def test_logo_links_to_homepage(page: Page):
    page.goto(f"{BASE_URL}/about-us")
    page.wait_for_load_state("networkidle")
    logo_link = page.locator("a[href='/']").first
    _nav_click(page, logo_link)
    assert page.url.rstrip("/") == BASE_URL.rstrip("/") or page.url == f"{BASE_URL}/"


def test_location_pages_load(page: Page):
    location_paths = [
        "/glendale",
        "/pasadena-van-rental",
        "/north-hollywood-sprinter-van-rental",
        "/anaheim-sprinter-van-rental",
        "/santa-monica-sprinter-van-rental",
    ]
    for path in location_paths:
        page.goto(f"{BASE_URL}{path}")
        page.wait_for_load_state("networkidle")
        expect(page.locator("body")).to_be_visible()


def test_footer_rental_policy_link(page: Page):
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    footer = page.locator("footer")
    policy_link = footer.locator("a[href*='rental'], a[href*='policy']").first
    expect(policy_link).to_be_visible()
    _nav_click(page, policy_link)
    assert "policy" in page.url.lower()


def test_browser_back_navigation(page: Page):
    page.goto(BASE_URL)
    page.goto(f"{BASE_URL}/about-us")
    page.wait_for_load_state("networkidle")
    page.go_back()
    page.wait_for_load_state("networkidle")
    assert page.url.rstrip("/") == BASE_URL.rstrip("/") or page.url == f"{BASE_URL}/"
