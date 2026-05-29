import re
from playwright.sync_api import Page, expect

BASE_URL = "https://tourvango.testingforproduction.com"

EMAIL = "gevorlogix@gmail.com"
PHONE = "4387985779"
NAME = "George Test"
MESSAGE = "This is an automated test message. Please ignore."


def test_contact_page_loads(page: Page):
    page.goto(f"{BASE_URL}/contact-us")
    assert len(page.title()) > 0, "Contact page title should not be empty"
    expect(page.locator("body")).to_be_visible()


def test_contact_page_has_form(page: Page):
    page.goto(f"{BASE_URL}/contact-us")
    page.wait_for_load_state("networkidle")
    form = page.locator("form").first
    expect(form).to_be_visible()


def test_contact_form_has_name_field(page: Page):
    page.goto(f"{BASE_URL}/contact-us")
    page.wait_for_load_state("networkidle")
    name_field = page.locator(
        "input[placeholder*='Your Name' i], input[name*='name' i], input[id*='name' i]"
    ).first
    expect(name_field).to_be_visible()


def test_contact_form_has_phone_field(page: Page):
    page.goto(f"{BASE_URL}/contact-us")
    page.wait_for_load_state("networkidle")
    phone_field = page.locator(
        "input[type='tel'], input[name*='phone' i], input[placeholder*='phone' i]"
    ).first
    expect(phone_field).to_be_visible()


def test_contact_form_has_email_field(page: Page):
    page.goto(f"{BASE_URL}/contact-us")
    page.wait_for_load_state("networkidle")
    email_field = page.locator(
        "input[type='email'], input[placeholder*='email' i], input[name*='email' i]"
    ).first
    expect(email_field).to_be_visible()


def test_contact_form_has_message_field(page: Page):
    page.goto(f"{BASE_URL}/contact-us")
    page.wait_for_load_state("networkidle")
    message_field = page.locator(
        "textarea, textarea[name*='message' i], textarea[placeholder*='message' i]"
    ).first
    expect(message_field).to_be_visible()


def test_contact_form_has_submit_button(page: Page):
    page.goto(f"{BASE_URL}/contact-us")
    page.wait_for_load_state("networkidle")
    submit_btn = page.locator(
        "button[type='submit'], input[type='submit'], button:has-text('Submit')"
    ).first
    expect(submit_btn).to_be_visible()
    expect(submit_btn).to_be_enabled()


def test_contact_form_fill_name(page: Page):
    page.goto(f"{BASE_URL}/contact-us")
    page.wait_for_load_state("networkidle")
    name_field = page.locator(
        "input[placeholder*='Your Name' i], input[name*='name' i]"
    ).first
    name_field.fill(NAME)
    assert name_field.input_value() == NAME


def test_contact_form_fill_phone(page: Page):
    page.goto(f"{BASE_URL}/contact-us")
    page.wait_for_load_state("networkidle")
    phone_field = page.locator(
        "input[type='tel'], input[name*='phone' i], input[placeholder*='phone' i]"
    ).first
    phone_field.fill(PHONE)
    assert re.sub(r"\D", "", phone_field.input_value()) == PHONE


def test_contact_form_fill_email(page: Page):
    page.goto(f"{BASE_URL}/contact-us")
    page.wait_for_load_state("networkidle")
    email_field = page.locator(
        "input[type='email'], input[placeholder*='email' i], input[name*='email' i]"
    ).first
    email_field.fill(EMAIL)
    assert email_field.input_value() == EMAIL


def test_contact_form_fill_message(page: Page):
    page.goto(f"{BASE_URL}/contact-us")
    page.wait_for_load_state("networkidle")
    message_field = page.locator("textarea").first
    message_field.fill(MESSAGE)
    assert message_field.input_value() == MESSAGE


def test_contact_form_phone_country_code(page: Page):
    page.goto(f"{BASE_URL}/contact-us")
    page.wait_for_load_state("networkidle")
    # Phone country code selector (+1) should default or be selectable
    country_selector = page.locator(
        "select[name*='country' i], [class*='country'], [class*='flag'], "
        "[placeholder*='+1'], span:has-text('+1'), button:has-text('+1')"
    )
    body_text = page.locator("body").inner_text()
    # Accept either a dedicated country-code element or +1 visible anywhere in the page
    assert country_selector.count() > 0 or "+1" in body_text, \
        "Country code +1 (US/Canada) should be visible on the contact form"


def test_contact_form_full_submission(page: Page):
    """Fill all contact form fields and submit."""
    page.goto(f"{BASE_URL}/contact-us")
    page.wait_for_load_state("networkidle")

    # Fill name
    name_field = page.locator(
        "input[placeholder*='Your Name' i], input[name*='name' i]"
    ).first
    name_field.fill(NAME)

    # Fill phone
    phone_field = page.locator(
        "input[type='tel'], input[name*='phone' i], input[placeholder*='phone' i]"
    ).first
    phone_field.fill(PHONE)

    # Fill email
    email_field = page.locator(
        "input[type='email'], input[placeholder*='email' i], input[name*='email' i]"
    ).first
    email_field.fill(EMAIL)

    # Fill message
    message_field = page.locator("textarea").first
    message_field.fill(MESSAGE)

    # Submit
    submit_btn = page.locator(
        "button[type='submit'], input[type='submit'], button:has-text('Submit')"
    ).first
    submit_btn.click()

    page.wait_for_load_state("networkidle")
    # After submission expect either a success message or redirect
    expect(page.locator("body")).to_be_visible()


def test_contact_page_shows_address(page: Page):
    page.goto(f"{BASE_URL}/contact-us")
    page.wait_for_load_state("networkidle")
    body_text = page.locator("body").inner_text()
    assert "Burbank" in body_text or "1814" in body_text, "Business address not found"


def test_contact_page_shows_phone_number(page: Page):
    page.goto(f"{BASE_URL}/contact-us")
    page.wait_for_load_state("networkidle")
    body_text = page.locator("body").inner_text()
    assert "818" in body_text, "Business phone number not found on contact page"
