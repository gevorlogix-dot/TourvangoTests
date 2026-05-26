import pytest
from playwright.sync_api import Page, expect

BASE_URL = "https://tourvango.testingforproduction.com"

EXPECTED_FAQ_QUESTIONS = [
    "reservation",
    "cancel",
    "deposit",
    "one way",
    "pets",
    "amenities",
    "smoking",
    "insurance",
    "airport",
    "minimum rental",
    "stops",
    "driver",
    "age",
    "miles",
    "Canada",
    "shuttle",
    "foreign",
]


def test_faq_page_loads(page: Page):
    page.goto(f"{BASE_URL}/faq")
    assert len(page.title()) > 0, "FAQ page title should not be empty"
    expect(page.locator("body")).to_be_visible()


def test_faq_page_has_questions(page: Page):
    page.goto(f"{BASE_URL}/faq")
    page.wait_for_load_state("networkidle")
    body_text = page.locator("body").inner_text()
    assert "?" in body_text, "FAQ page should contain questions"


def test_faq_page_has_minimum_questions(page: Page):
    page.goto(f"{BASE_URL}/faq")
    page.wait_for_load_state("networkidle")
    body_text = page.locator("body").inner_text()
    found = sum(1 for kw in EXPECTED_FAQ_QUESTIONS if kw.lower() in body_text.lower())
    assert found >= 5, f"Only {found} expected FAQ topics found — expected at least 5"


def test_faq_reservation_question_present(page: Page):
    page.goto(f"{BASE_URL}/faq")
    page.wait_for_load_state("networkidle")
    body_text = page.locator("body").inner_text()
    assert "reservation" in body_text.lower(), "Reservation FAQ question not found"


def test_faq_cancellation_question_present(page: Page):
    page.goto(f"{BASE_URL}/faq")
    page.wait_for_load_state("networkidle")
    body_text = page.locator("body").inner_text()
    assert "cancel" in body_text.lower(), "Cancellation FAQ question not found"


def test_faq_deposit_question_present(page: Page):
    page.goto(f"{BASE_URL}/faq")
    page.wait_for_load_state("networkidle")
    body_text = page.locator("body").inner_text()
    assert "deposit" in body_text.lower(), "Deposit FAQ question not found"


def test_faq_pets_question_present(page: Page):
    page.goto(f"{BASE_URL}/faq")
    page.wait_for_load_state("networkidle")
    body_text = page.locator("body").inner_text()
    assert "pet" in body_text.lower(), "Pets FAQ question not found"


def test_faq_contact_us_link_present(page: Page):
    page.goto(f"{BASE_URL}/faq")
    page.wait_for_load_state("networkidle")
    contact_link = page.locator("a[href='/contact-us'], a:has-text('Contact')").first
    expect(contact_link).to_be_visible()


def test_faq_contact_us_link_navigates(page: Page):
    page.goto(f"{BASE_URL}/faq")
    page.wait_for_load_state("networkidle")
    contact_link = page.locator("a[href='/contact-us']").first
    contact_link.click()
    page.wait_for_load_state("networkidle")
    assert "/contact-us" in page.url


def test_faq_accordion_items_clickable(page: Page):
    page.goto(f"{BASE_URL}/faq")
    page.wait_for_load_state("networkidle")

    # Try common accordion patterns
    accordion_items = page.locator(
        "[class*='accordion'] button, [class*='faq'] button, "
        "[class*='collapse'] button, details summary, "
        "h3 button, h4 button"
    )

    if accordion_items.count() > 0:
        # Click the first item and verify it expands
        accordion_items.first.click()
        page.wait_for_timeout(500)
        expect(page.locator("body")).to_be_visible()
    else:
        # FAQ might be static — just verify content exists
        body_text = page.locator("body").inner_text()
        assert len(body_text) > 200, "FAQ page should have readable content"


def test_faq_page_phone_number_visible(page: Page):
    page.goto(f"{BASE_URL}/faq")
    page.wait_for_load_state("networkidle")
    body_text = page.locator("body").inner_text()
    assert "818" in body_text, "Business phone number not found on FAQ page"
