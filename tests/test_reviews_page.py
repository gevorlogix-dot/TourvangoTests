import pytest
from playwright.sync_api import Page, expect

BASE_URL = "https://tourvango.testingforproduction.com"
REVIEWS_URL = f"{BASE_URL}/reviews"


def test_reviews_page_loads(page: Page):
    page.goto(REVIEWS_URL)
    page.wait_for_load_state("networkidle")
    expect(page.locator("body")).to_be_visible()


def test_reviews_page_has_content(page: Page):
    page.goto(REVIEWS_URL)
    page.wait_for_load_state("networkidle")
    body_text = page.locator("body").inner_text()
    assert len(body_text) > 100, "Reviews page appears empty"


def test_reviews_page_mentions_rating(page: Page):
    page.goto(REVIEWS_URL)
    page.wait_for_load_state("networkidle")
    body_text = page.locator("body").inner_text()
    assert any(kw in body_text for kw in ["5", "4.", "rating", "Rating", "star", "Star", "review"]), \
        "Reviews page should display a rating"


def test_reviews_page_shows_reviewer_names_or_count(page: Page):
    page.goto(REVIEWS_URL)
    page.wait_for_load_state("networkidle")
    body_text = page.locator("body").inner_text()
    # Either individual reviews or a total count should be present
    has_reviews = any(kw in body_text for kw in ["review", "Review", "77", "Google"])
    assert has_reviews, "Reviews page should show reviewer information or review count"


def test_reviews_page_star_elements_or_rating_text(page: Page):
    page.goto(REVIEWS_URL)
    page.wait_for_load_state("networkidle")
    # Stars can be SVGs, Unicode ★, or image-based
    star_elements = page.locator(
        "[class*='star'], [class*='rating'], svg[aria-label*='star' i], "
        "[aria-label*='rating' i], [class*='score']"
    )
    body_text = page.locator("body").inner_text()
    has_star_html = star_elements.count() > 0
    has_rating_text = any(kw in body_text for kw in ["5/5", "4.3", "★", "☆", "/5"])
    assert has_star_html or has_rating_text, \
        "Reviews page should show star elements or rating text"


def test_reviews_page_navigation_intact(page: Page):
    page.goto(REVIEWS_URL)
    page.wait_for_load_state("networkidle")
    nav = page.locator("nav, header").first
    expect(nav).to_be_visible()


def test_reviews_page_footer_intact(page: Page):
    page.goto(REVIEWS_URL)
    page.wait_for_load_state("networkidle")
    footer = page.locator("footer")
    expect(footer).to_be_visible()


def test_reviews_page_has_google_reference_or_link(page: Page):
    page.goto(REVIEWS_URL)
    page.wait_for_load_state("networkidle")
    body_text = page.locator("body").inner_text()
    google_link = page.locator("a[href*='google'], a[href*='g.page'], img[alt*='Google' i]")
    has_google_text = "Google" in body_text or "google" in body_text
    has_google_link = google_link.count() > 0
    assert has_google_text or has_google_link, \
        "Reviews page should reference Google reviews"


def test_reviews_page_individual_reviews_visible(page: Page):
    page.goto(REVIEWS_URL)
    page.wait_for_load_state("networkidle")
    review_cards = page.locator(
        "[class*='review'], [class*='testimonial'], [class*='card'], "
        "blockquote, [class*='feedback']"
    )
    body_text = page.locator("body").inner_text()
    # Either individual review cards or quoted text should exist
    if review_cards.count() == 0:
        assert len(body_text) > 500, \
            "Reviews page should have substantial review content if no card elements"


def test_reviews_page_booking_or_cta_link_present(page: Page):
    page.goto(REVIEWS_URL)
    page.wait_for_load_state("networkidle")
    cta = page.locator(
        "a:has-text('Book'), a:has-text('Reserve'), a:has-text('Contact'), "
        "a[href='/vehicles'], a[href='/contact-us'], button:has-text('Book')"
    )
    assert cta.count() > 0, \
        "Reviews page should have a call-to-action link to book or contact"


def test_reviews_page_no_broken_images(page: Page):
    page.goto(REVIEWS_URL)
    page.wait_for_load_state("networkidle")
    broken = page.evaluate(
        """() => Array.from(document.images)
               .filter(img => !img.complete || img.naturalWidth === 0)
               .map(img => img.src)"""
    )
    assert broken == [], f"Broken images on reviews page: {broken}"


def test_reviews_page_phone_number_visible(page: Page):
    page.goto(REVIEWS_URL)
    page.wait_for_load_state("networkidle")
    body_text = page.locator("body").inner_text()
    assert "818" in body_text, "Business phone number should be visible on reviews page"
