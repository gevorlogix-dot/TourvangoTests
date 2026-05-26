import pytest
from playwright.sync_api import Page, expect


BASE_URL = "https://tourvango.testingforproduction.com"


def test_homepage_loads(page: Page):
    page.goto(BASE_URL)
    assert len(page.title()) > 0, "Homepage title should not be empty"
    expect(page.locator("body")).to_be_visible()


def test_homepage_has_hero_section(page: Page):
    page.goto(BASE_URL)
    # Booking/inquiry form should be present
    expect(page.locator("form, [class*='form'], [class*='booking']").first).to_be_visible()


def test_homepage_has_navigation(page: Page):
    page.goto(BASE_URL)
    nav = page.locator("nav, header")
    expect(nav.first).to_be_visible()


def test_homepage_nav_links_present(page: Page):
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    nav_texts = ["Home", "About", "Fleet", "Contact", "FAQ", "Blog"]
    links = page.locator("a")
    all_hrefs = [links.nth(i).get_attribute("href") for i in range(links.count())]

    important_paths = ["/about-us", "/vehicles", "/contact-us", "/faq"]
    for path in important_paths:
        assert any(path in (href or "") for href in all_hrefs), f"Nav link {path} not found"


def test_homepage_google_rating_visible(page: Page):
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    # Rating badge should be visible (5/5 or 4.3/5 with 77 reviews)
    body_text = page.locator("body").inner_text()
    assert any(rating in body_text for rating in ["5/5", "4.3", "77 reviews", "77"]), \
        "Rating information not visible on homepage"


def test_homepage_phone_number_visible(page: Page):
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    body_text = page.locator("body").inner_text()
    assert "818" in body_text or "566-0005" in body_text, "Business phone number not found"


def test_homepage_booking_form_visible(page: Page):
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    # The main booking form should have a Next/Submit button
    next_btn = page.locator("button:has-text('Next'), input[type='submit'][value*='Next']")
    expect(next_btn.first).to_be_visible()


def test_homepage_footer_links(page: Page):
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    footer = page.locator("footer")
    expect(footer).to_be_visible()
    footer_links = footer.locator("a")
    assert footer_links.count() > 0, "Footer should have links"


def test_homepage_social_media_links(page: Page):
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    links = page.locator("a[href*='facebook'], a[href*='instagram'], a[href*='youtube']")
    assert links.count() >= 1, "Social media links should be present"
