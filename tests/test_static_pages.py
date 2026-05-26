import pytest
from playwright.sync_api import Page, expect

BASE_URL = "https://tourvango.testingforproduction.com"


# ── About Us ────────────────────────────────────────────────────────────────

def test_about_page_loads(page: Page):
    page.goto(f"{BASE_URL}/about-us")
    expect(page.locator("body")).to_be_visible()


def test_about_page_has_content(page: Page):
    page.goto(f"{BASE_URL}/about-us")
    page.wait_for_load_state("networkidle")
    body_text = page.locator("body").inner_text()
    assert len(body_text) > 100, "About page appears empty"


def test_about_page_mentions_company(page: Page):
    page.goto(f"{BASE_URL}/about-us")
    page.wait_for_load_state("networkidle")
    body_text = page.locator("body").inner_text()
    assert any(kw in body_text for kw in ["TourVanGo", "Tourvango", "van", "Van", "rental"]), \
        "About page should mention the company"


# ── Reviews ─────────────────────────────────────────────────────────────────

def test_reviews_page_loads(page: Page):
    page.goto(f"{BASE_URL}/reviews")
    expect(page.locator("body")).to_be_visible()


def test_reviews_page_has_rating_content(page: Page):
    page.goto(f"{BASE_URL}/reviews")
    page.wait_for_load_state("networkidle")
    body_text = page.locator("body").inner_text()
    assert any(kw in body_text for kw in ["review", "Review", "rating", "Rating", "star", "5"]), \
        "Reviews page should show rating content"


# ── Blog ────────────────────────────────────────────────────────────────────

def test_blog_page_loads(page: Page):
    page.goto(f"{BASE_URL}/blogs/category/all")
    expect(page.locator("body")).to_be_visible()


def test_blog_page_has_posts(page: Page):
    page.goto(f"{BASE_URL}/blogs/category/all")
    page.wait_for_load_state("networkidle")
    body_text = page.locator("body").inner_text()
    assert len(body_text) > 100, "Blog page appears empty"


# ── Rental Policy ────────────────────────────────────────────────────────────

def test_rental_policy_page_loads(page: Page):
    page.goto(f"{BASE_URL}/policy/rental-policies")
    expect(page.locator("body")).to_be_visible()


def test_rental_policy_has_content(page: Page):
    page.goto(f"{BASE_URL}/policy/rental-policies")
    page.wait_for_load_state("networkidle")
    body_text = page.locator("body").inner_text()
    assert any(kw in body_text for kw in ["policy", "Policy", "rental", "Rental", "cancel"]), \
        "Rental policy page should contain policy information"


# ── Privacy Policy ───────────────────────────────────────────────────────────

def test_privacy_policy_page_loads(page: Page):
    page.goto(f"{BASE_URL}/policy/privacy-policy")
    expect(page.locator("body")).to_be_visible()


def test_privacy_policy_has_content(page: Page):
    page.goto(f"{BASE_URL}/policy/privacy-policy")
    page.wait_for_load_state("networkidle")
    body_text = page.locator("body").inner_text()
    assert any(kw in body_text for kw in ["privacy", "Privacy", "data", "information"]), \
        "Privacy policy page should contain privacy information"


# ── Terms of Service ─────────────────────────────────────────────────────────

def test_terms_of_service_page_loads(page: Page):
    page.goto(f"{BASE_URL}/policy/terms-of-service")
    expect(page.locator("body")).to_be_visible()


def test_terms_of_service_has_content(page: Page):
    page.goto(f"{BASE_URL}/policy/terms-of-service")
    page.wait_for_load_state("networkidle")
    body_text = page.locator("body").inner_text()
    assert any(kw in body_text for kw in ["terms", "Terms", "service", "agreement"]), \
        "Terms of service page should contain terms content"


# ── Location Pages ───────────────────────────────────────────────────────────

@pytest.mark.parametrize("path,city", [
    ("/glendale", "Glendale"),
    ("/pasadena-van-rental", "Pasadena"),
    ("/north-hollywood-sprinter-van-rental", "North Hollywood"),
    ("/anaheim-sprinter-van-rental", "Anaheim"),
    ("/santa-monica-sprinter-van-rental", "Santa Monica"),
    ("/west-hollywood-sprinter-van-rental", "West Hollywood"),
    ("/downtown-los-angeles-sprinter-van-rental", "Los Angeles"),
])
def test_location_page_loads_and_has_city(page: Page, path: str, city: str):
    page.goto(f"{BASE_URL}{path}")
    page.wait_for_load_state("networkidle")
    expect(page.locator("body")).to_be_visible()
    body_text = page.locator("body").inner_text()
    city_word = city.split()[0]  # e.g. "North" from "North Hollywood"
    assert city_word in body_text, f"Location page {path} should mention {city}"
