import pytest
from playwright.sync_api import Page, expect

BASE_URL = "https://tourvango.testingforproduction.com"


def test_fleet_page_loads(page: Page):
    page.goto(f"{BASE_URL}/vehicles")
    assert len(page.title()) > 0, "Fleet page title should not be empty"
    expect(page.locator("body")).to_be_visible()


def test_fleet_page_has_content(page: Page):
    page.goto(f"{BASE_URL}/vehicles")
    page.wait_for_load_state("networkidle")
    body_text = page.locator("body").inner_text()
    assert len(body_text) > 100, "Fleet page appears empty"


def test_fleet_page_mentions_sprinter(page: Page):
    page.goto(f"{BASE_URL}/vehicles")
    page.wait_for_load_state("networkidle")
    body_text = page.locator("body").inner_text()
    assert any(kw in body_text for kw in ["Sprinter", "sprinter", "Van", "van", "Mercedes"]), \
        "Fleet page should mention vehicle types"


def test_fleet_page_has_booking_form(page: Page):
    page.goto(f"{BASE_URL}/vehicles")
    page.wait_for_load_state("networkidle")
    form = page.locator("form").first
    expect(form).to_be_visible()


def test_fleet_page_reserve_cta_visible(page: Page):
    page.goto(f"{BASE_URL}/vehicles")
    page.wait_for_load_state("networkidle")
    body_text = page.locator("body").inner_text()
    assert any(kw in body_text for kw in ["Reserve", "reserve", "Book", "book", "Rental"]), \
        "Fleet page should have a reservation CTA"


def test_fleet_page_no_availability_message(page: Page):
    """Site may show 'No Vans Available? Try Adjusting Your Dates!' — that's valid content."""
    page.goto(f"{BASE_URL}/vehicles")
    page.wait_for_load_state("networkidle")
    body_text = page.locator("body").inner_text()
    # Either vehicle cards or the availability message must be present
    has_vehicles = any(kw in body_text for kw in ["Sprinter", "Mercedes", "passenger"])
    has_availability_msg = "adjust" in body_text.lower() or "available" in body_text.lower()
    assert has_vehicles or has_availability_msg, \
        "Fleet page should show vehicles or availability message"


def test_fleet_page_navigation_intact(page: Page):
    page.goto(f"{BASE_URL}/vehicles")
    page.wait_for_load_state("networkidle")
    nav = page.locator("nav, header").first
    expect(nav).to_be_visible()


def test_fleet_booking_form_next_button(page: Page):
    page.goto(f"{BASE_URL}/vehicles")
    page.wait_for_load_state("networkidle")
    next_btn = page.locator("button:has-text('Find Available Vans'), button[type='submit']").first
    expect(next_btn).to_be_visible()


def test_fleet_page_passenger_range_mentioned(page: Page):
    page.goto(f"{BASE_URL}/vehicles")
    page.wait_for_load_state("networkidle")
    body_text = page.locator("body").inner_text()
    # Should mention 8-17 passengers somewhere
    assert any(kw in body_text for kw in ["8", "17", "Passenger", "passenger"]), \
        "Fleet page should indicate passenger capacity"
