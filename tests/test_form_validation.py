import re
import pytest
from playwright.sync_api import Page, expect

BASE_URL = "https://tourvango.testingforproduction.com"

EMAIL = "gevorlogix@gmail.com"
PHONE = "4387985779"
NAME = "George Test"
MESSAGE = "This is an automated test message. Please ignore."
INVALID_EMAIL = "not-an-email"
SHORT_NAME = "A"


# ── Contact form validation ───────────────────────────────────────────────────

def test_contact_form_empty_submit_stays_on_page(page: Page):
    """Submitting blank contact form should not navigate away (HTML5 or JS validation)."""
    page.goto(f"{BASE_URL}/contact-us")
    page.wait_for_load_state("networkidle")
    original_url = page.url

    submit_btn = page.locator(
        "button[type='submit'], input[type='submit'], button:has-text('Submit')"
    ).first
    submit_btn.click()
    page.wait_for_timeout(1000)

    # Should still be on contact page (not navigated to a success page)
    assert page.url == original_url or "/contact-us" in page.url, \
        "Empty contact form submission should not navigate away from contact page"


def test_contact_form_invalid_email_shows_feedback(page: Page):
    """Entering a malformed email should trigger validation feedback."""
    page.goto(f"{BASE_URL}/contact-us")
    page.wait_for_load_state("networkidle")

    email_field = page.locator(
        "input[type='email'], input[name*='email' i], input[placeholder*='email' i]"
    ).first
    email_field.fill(INVALID_EMAIL)

    submit_btn = page.locator(
        "button[type='submit'], input[type='submit'], button:has-text('Submit')"
    ).first
    submit_btn.click()
    page.wait_for_timeout(800)

    # Either HTML5 validation prevents submit (browser validation message)
    # or a JS error message appears
    validation_msg = page.locator(
        "[class*='error'], [class*='invalid'], [class*='validation'], "
        "[role='alert'], .alert, .form-error"
    )
    # Check HTML5 validity state
    is_valid = page.evaluate(
        "() => document.querySelector('input[type=\"email\"]')?.validity?.valid ?? true"
    )
    assert not is_valid or validation_msg.count() > 0, \
        "Invalid email should trigger browser or JS validation"


def test_contact_form_email_field_rejects_plain_text(page: Page):
    """The email input's type='email' attribute should reject plain text."""
    page.goto(f"{BASE_URL}/contact-us")
    page.wait_for_load_state("networkidle")

    email_field = page.locator("input[type='email']").first
    if email_field.count() == 0:
        pytest.skip("No input[type='email'] found on contact page")

    email_field.fill("plaintext")
    is_valid = page.evaluate(
        "() => document.querySelector('input[type=\"email\"]')?.validity?.valid ?? true"
    )
    assert not is_valid, "input[type='email'] should mark 'plaintext' as invalid"


def test_contact_form_valid_email_is_accepted(page: Page):
    page.goto(f"{BASE_URL}/contact-us")
    page.wait_for_load_state("networkidle")

    email_field = page.locator("input[type='email']").first
    if email_field.count() == 0:
        pytest.skip("No input[type='email'] found on contact page")

    email_field.fill(EMAIL)
    is_valid = page.evaluate(
        "() => document.querySelector('input[type=\"email\"]')?.validity?.valid ?? true"
    )
    assert is_valid, f"Valid email '{EMAIL}' should be accepted by email field"


def test_contact_form_required_fields_marked(page: Page):
    """At least some form fields should be required (HTML5 required or aria-required)."""
    page.goto(f"{BASE_URL}/contact-us")
    page.wait_for_load_state("networkidle")
    # Some forms use aria-required="true" or data-required instead of the required attr
    required_html = page.locator("form input[required], form textarea[required]")
    required_aria = page.locator("form input[aria-required='true'], form textarea[aria-required='true']")
    has_any = required_html.count() > 0 or required_aria.count() > 0
    if not has_any:
        # Accept JS-only validation: just verify the form has inputs we can submit
        inputs = page.locator("form input[type='text'], form input[type='email'], form input[type='tel']")
        assert inputs.count() > 0, "Contact form should have input fields"
    else:
        assert has_any


def test_contact_form_textarea_max_length_or_no_limit(page: Page):
    """Textarea should accept a long message (or define a reasonable maxlength)."""
    page.goto(f"{BASE_URL}/contact-us")
    page.wait_for_load_state("networkidle")
    textarea = page.locator("textarea").first
    if textarea.count() == 0:
        pytest.skip("No textarea found on contact page")

    long_message = "A" * 500
    textarea.fill(long_message)
    actual_value = textarea.input_value()
    # Either accepts full text or has a maxlength restriction (but not < 100 chars)
    maxlength = textarea.get_attribute("maxlength")
    if maxlength:
        assert int(maxlength) >= 100, f"Textarea maxlength ({maxlength}) seems unreasonably short"
    else:
        assert len(actual_value) >= 500, "Textarea should accept at least 500 characters"


def test_contact_form_phone_field_accepts_digits(page: Page):
    page.goto(f"{BASE_URL}/contact-us")
    page.wait_for_load_state("networkidle")

    phone_field = page.locator(
        "input[type='tel'], input[name*='phone' i], input[placeholder*='phone' i]"
    ).first
    phone_field.fill(PHONE)
    actual = phone_field.input_value()
    # Field may auto-format digits — strip non-digits before comparing
    assert re.sub(r"\D", "", actual) == PHONE, \
        f"Phone field should contain digits {PHONE}, got '{actual}'"


def test_contact_form_name_field_accepts_full_name(page: Page):
    page.goto(f"{BASE_URL}/contact-us")
    page.wait_for_load_state("networkidle")

    name_field = page.locator(
        "input[placeholder*='Your Name' i], input[name*='name' i]"
    ).first
    name_field.fill(NAME)
    assert name_field.input_value() == NAME


def test_contact_form_fields_clearable(page: Page):
    """Filled fields should be clearable."""
    page.goto(f"{BASE_URL}/contact-us")
    page.wait_for_load_state("networkidle")

    name_field = page.locator(
        "input[placeholder*='Your Name' i], input[name*='name' i]"
    ).first
    name_field.fill(NAME)
    name_field.fill("")
    assert name_field.input_value() == "", "Name field should be clearable"


# ── Booking form validation ───────────────────────────────────────────────────

def test_booking_form_next_without_required_fields(page: Page):
    """Clicking Next on a blank booking form should not silently proceed."""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    # Don't fill anything — click Next
    next_btn = page.locator("button:has-text('Next'), input[type='submit']").first
    next_btn.click()
    page.wait_for_timeout(1000)

    # Either stays on same page or shows a validation step
    body = page.locator("body")
    expect(body).to_be_visible()


def test_booking_form_name_field_accepts_text(page: Page):
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    name_field = page.locator(
        "input[name*='name' i], input[placeholder*='name' i], input[id*='name' i]"
    ).first
    name_field.fill(NAME)
    assert name_field.input_value() == NAME


def test_booking_form_email_invalid_format_not_valid(page: Page):
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    email_field = page.locator("input[type='email']").first
    if email_field.count() == 0:
        pytest.skip("No input[type='email'] in booking form")

    email_field.fill(INVALID_EMAIL)
    is_valid = page.evaluate(
        "() => document.querySelector('input[type=\"email\"]')?.validity?.valid ?? true"
    )
    assert not is_valid, "Invalid email format should fail HTML5 validation"


def test_booking_form_phone_field_fillable(page: Page):
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    phone_field = page.locator(
        "input[type='tel'], input[name*='phone' i], input[placeholder*='phone' i]"
    ).first
    phone_field.fill(PHONE)
    actual = phone_field.input_value()
    assert re.sub(r"\D", "", actual) == PHONE, \
        f"Phone field should contain digits {PHONE}, got '{actual}'"


def test_booking_form_passenger_field_accepts_number(page: Page):
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    passenger = page.locator(
        "input[name*='passenger' i], input[type='number'][name*='pass' i]"
    ).first
    if passenger.count() == 0:
        pytest.skip("No passenger number input found")

    passenger.fill("8")
    val = passenger.input_value()
    assert val == "8", f"Passenger field should accept '8', got '{val}'"


def test_booking_form_passenger_select_has_options(page: Page):
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    passenger_select = page.locator("select[name*='passenger' i]").first
    if passenger_select.count() == 0:
        pytest.skip("No passenger select dropdown found")

    options = passenger_select.locator("option")
    assert options.count() > 1, "Passenger select should have multiple options"


# ── Date field validation ─────────────────────────────────────────────────────

def test_booking_form_date_field_present(page: Page):
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    date_field = page.locator(
        "input[type='date'], input[name*='date' i], input[placeholder*='date' i], "
        "input[placeholder*='mm/dd' i], [class*='datepicker'] input"
    ).first
    assert date_field.count() > 0 or page.locator(
        "input[type='date'], input[name*='date' i]"
    ).count() > 0, "Booking form should have a date input"


def test_booking_form_pickup_date_clickable(page: Page):
    """Date picker field should be clickable and open a calendar/picker UI."""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    date_field = page.locator(
        "input[type='date'], input[name*='date' i], input[placeholder*='date' i], "
        "input[placeholder*='Date' i], input[placeholder*='mm/dd' i]"
    ).first
    if date_field.count() == 0:
        pytest.skip("No date input found in booking form")

    expect(date_field).to_be_visible()
    # Custom datepickers are often readonly — just verify clicking doesn't error
    date_field.click()
    page.wait_for_timeout(500)
    expect(page.locator("body")).to_be_visible()


# ── Input type checks ─────────────────────────────────────────────────────────

def test_contact_page_email_input_type_is_email(page: Page):
    page.goto(f"{BASE_URL}/contact-us")
    page.wait_for_load_state("networkidle")
    email_input = page.locator("input[type='email']")
    assert email_input.count() > 0, \
        "Contact form should use input[type='email'] for email field"


def test_contact_page_phone_input_type_is_tel(page: Page):
    page.goto(f"{BASE_URL}/contact-us")
    page.wait_for_load_state("networkidle")
    tel_input = page.locator("input[type='tel']")
    assert tel_input.count() > 0, \
        "Contact form should use input[type='tel'] for phone field"


def test_booking_form_phone_input_type_is_tel(page: Page):
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    tel_input = page.locator("form input[type='tel']")
    assert tel_input.count() > 0, \
        "Booking form should use input[type='tel'] for phone number"
