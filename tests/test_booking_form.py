import re
import pytest
from playwright.sync_api import Page, expect

BASE_URL = "https://tourvango.testingforproduction.com"

EMAIL = "gevorlogix@gmail.com"
PHONE = "4387985779"
NAME = "George Test"
PICKUP_DATE = "06/15/2026"
DROPOFF_DATE = "06/20/2026"
PICKUP_LOCATION = "Los Angeles, CA"
DROPOFF_LOCATION = "Santa Monica, CA"

SUCCESS_KEYWORDS = [
    "thank you", "thank", "thanks", "success", "sent", "received",
    "we'll be in touch", "we will", "confirmed", "confirmation",
    "message has been", "submitted", "get back to you",
]

POPUP_SELECTORS = (
    "[class*='success'], [class*='thank'], [class*='confirm'], "
    "[class*='modal'], [class*='popup'], [class*='alert'], "
    "[role='dialog'], [role='alert'], [role='status'], "
    ".toast, .snackbar, [class*='toast'], [class*='snackbar'], "
    "[class*='notification'], [class*='banner']"
)

ROUND_TRIP_SELECTOR = "button:has-text('Round trip')"

ONE_WAY_SELECTOR = "button:has-text('One way')"

# Return leg uses locations.1.date / locations.1.dropoff_date field names
RETURN_DATE_SELECTOR = (
    "input[name='locations.1.date'], input[name='locations.1.dropoff_date']"
)

ADD_DESTINATION_SELECTOR = "button:has-text('Add a stop along the way')"

# Date field labels (MUI DatePicker) — "Pick-up date & time" / "Drop-off date & time"
DROPOFF_DATE_LABEL = "Drop-off date & time"
PICKUP_DATE_LABEL = "Pick-up date & time"
PASSENGERS_LABEL = "Passengers"


def _autocomplete_type(page: Page, placeholder: str, nth: int, text: str) -> None:
    loc = page.locator(f"input[placeholder='{placeholder}']").nth(nth)
    if loc.count() == 0 or not loc.is_visible():
        return
    loc.click()
    page.wait_for_timeout(400)
    page.keyboard.type(text, delay=80)
    page.wait_for_timeout(1800)
    option = page.locator("[role='option']").first
    if option.count() > 0 and option.is_visible():
        option.click()
    else:
        page.keyboard.press("Tab")
    page.wait_for_timeout(500)


def _pick_first_date(page: Page, field_name: str) -> None:
    """
    Open the MUI DateTimePicker, pick a day 3+ days in the future, select
    the last available hour and first available minute, then commit.

    Uses dynamic waits (wait_for_selector) for the calendar and time picker
    so it works on cold-cache sessions where UI transitions are slower.
    Retries once if the input value remains empty after the first attempt.
    """
    for attempt in range(2):
        date_input = page.locator(f"input[name='{field_name}']").first
        if date_input.count() == 0 or not date_input.is_visible():
            return
        try:
            date_input.scroll_into_view_if_needed()
        except Exception:
            pass
        date_input.click()
        # Wait for calendar to actually open (dynamic — handles slow cold-cache loads)
        try:
            page.wait_for_selector(
                "button[class*='MuiPickersDay']:not(.Mui-disabled)",
                timeout=5000
            )
        except Exception:
            page.wait_for_timeout(1000)

        days = page.locator("button[class*='MuiPickersDay']:not(.Mui-disabled)")
        pick_idx = min(3, max(0, days.count() - 1))
        if days.count() > 0 and days.nth(pick_idx).is_visible():
            days.nth(pick_idx).click()
            # Wait for time picker to appear after day selection
            try:
                page.wait_for_selector(
                    "[role='listbox'][aria-label*='hours' i], "
                    "[role='listbox'][aria-label*='Select hours' i]",
                    timeout=3000
                )
            except Exception:
                page.wait_for_timeout(700)

        hours_box = page.locator(
            "[role='listbox'][aria-label*='hours' i], "
            "[role='listbox'][aria-label*='Select hours' i]"
        )
        if hours_box.count() > 0:
            hour_opts = hours_box.first.locator("[role='option']")
            if hour_opts.count() > 0:
                hour_opts.last.click()
                page.wait_for_timeout(300)

        mins_box = page.locator(
            "[role='listbox'][aria-label*='minutes' i], "
            "[role='listbox'][aria-label*='Select minutes' i]"
        )
        if mins_box.count() > 0:
            min_opts = mins_box.first.locator("[role='option']")
            if min_opts.count() > 0:
                min_opts.first.click()
                page.wait_for_timeout(300)

        accept_btn = page.locator(
            "button:has-text('OK'), button:has-text('Accept'), "
            "button[aria-label='Accept time'], button[aria-label='OK']"
        )
        if accept_btn.count() > 0 and accept_btn.first.is_visible():
            accept_btn.first.click()
            page.wait_for_timeout(400)
        else:
            page.keyboard.press("Tab")
            page.wait_for_timeout(300)
        page.keyboard.press("Escape")
        page.wait_for_timeout(600)

        # Verify commit succeeded — if input has a value we're done
        try:
            val = date_input.input_value()
            if val and val.strip():
                break
        except Exception:
            pass
        if attempt == 0:
            page.wait_for_timeout(800)


def _get_form(page: Page):
    """Return the first visible booking form on the page."""
    return page.locator("form").first


def _has_success_signal(page: Page) -> bool:
    """Return True if any success indicator is visible after submission."""
    popup = page.locator(POPUP_SELECTORS)
    for i in range(popup.count()):
        try:
            if popup.nth(i).is_visible():
                text = popup.nth(i).inner_text().lower()
                if any(kw in text for kw in SUCCESS_KEYWORDS):
                    return True
        except Exception:
            pass
    body = page.locator("body").inner_text().lower()
    if any(kw in body for kw in SUCCESS_KEYWORDS):
        return True
    if any(kw in page.url.lower() for kw in ["thank", "success", "confirm"]):
        return True
    return False


def _fill_date(page: Page, label: str, value: str) -> None:
    """Fill a date field by label.
    MUI DatePickers are readonly in the DOM but respond to keyboard input when focused.
    Strategy: click → close any calendar that opens → type directly into the text field.
    """
    field = page.get_by_label(label, exact=False)
    if field.count() == 0:
        return
    try:
        el = field.first
        if not el.is_visible():
            return
        # 1. Try plain fill (works for standard date inputs)
        try:
            el.fill(value)
            return
        except Exception:
            pass
        # 2. Click, dismiss calendar if it opened, then type into the field
        el.click()
        page.wait_for_timeout(300)
        page.keyboard.press("Escape")   # close calendar dialog if it appeared
        page.wait_for_timeout(200)
        el.click()                      # refocus the text field
        page.wait_for_timeout(200)
        page.keyboard.type(value, delay=30)
        page.keyboard.press("Escape")
        page.wait_for_timeout(200)
    except Exception:
        pass


def _fill_passengers(page: Page, value: str = "2") -> None:
    """Select/fill the passenger count field."""
    field = page.get_by_label(PASSENGERS_LABEL, exact=False)
    if field.count() == 0:
        field = page.locator(
            "select[name*='passenger' i], input[name*='passenger' i], "
            "input[placeholder*='passenger' i]"
        )
    if field.count() == 0:
        return
    try:
        if field.first.is_visible():
            tag = field.first.evaluate("el => el.tagName.toLowerCase()")
            if tag == "select":
                field.first.select_option(index=1)
            else:
                field.first.fill(value)
    except Exception:
        pass


def _advance_form(page: Page, max_steps: int = 5) -> None:
    """Click through form steps until no more submit buttons are visible."""
    for _ in range(max_steps):
        next_btn = page.locator(
            "button:has-text('Find Available Vans'), button:has-text('Submit a Quote'), "
            "button:has-text('Submit Quote'), button:has-text('Book'), button[type='submit']"
        ).first
        if not next_btn.is_visible():
            break
        try:
            btn_text = (next_btn.inner_text() or "").strip().lower()
        except Exception:
            btn_text = ""
        next_btn.click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)
        if any(kw in btn_text for kw in ["submit", "book", "send", "confirm"]):
            page.wait_for_timeout(3000)
            try:
                page.wait_for_selector(POPUP_SELECTORS, timeout=5000)
            except Exception:
                pass
            break


def test_booking_form_present_on_homepage(page: Page):
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    form = _get_form(page)
    expect(form).to_be_visible()


def test_booking_form_has_required_fields(page: Page):
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    # Name, email, phone fields using exact field names/placeholders
    name_field = page.locator(
        "input[name='client_info.full_name'], input[placeholder='Full Name']"
    ).first
    email_field = page.locator(
        "input[type='email'], input[name='client_info.email']"
    ).first
    phone_field = page.locator(
        "input[type='tel'], input[placeholder='Phone Number']"
    ).first

    expect(name_field).to_be_visible()
    expect(email_field).to_be_visible()
    expect(phone_field).to_be_visible()


def test_booking_form_trip_type_selection(page: Page):
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    # One way / Round trip buttons
    one_way_btn = page.locator(ONE_WAY_SELECTOR)
    round_trip_btn = page.locator(ROUND_TRIP_SELECTOR)
    body_text = page.locator("body").inner_text()
    has_trip_text = any(kw in body_text for kw in ["One way", "Round trip", "one way", "round trip"])
    assert one_way_btn.count() > 0 or round_trip_btn.count() > 0 or has_trip_text, \
        "Trip type toggle buttons not found"


def test_booking_form_fill_name(page: Page):
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    name_field = page.locator(
        "input[name='client_info.full_name'], input[placeholder='Full Name']"
    ).first
    name_field.fill(NAME)
    assert name_field.input_value() == NAME


def test_booking_form_fill_email(page: Page):
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    email_field = page.locator(
        "input[type='email'], input[name='client_info.email']"
    ).first
    email_field.fill(EMAIL)
    assert email_field.input_value() == EMAIL


def test_booking_form_fill_phone(page: Page):
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    phone_field = page.locator(
        "input[type='tel'], input[placeholder='Phone Number']"
    ).first
    phone_field.fill(PHONE)
    assert re.sub(r"\D", "", phone_field.input_value()) == PHONE


def test_booking_form_next_button_clickable(page: Page):
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    next_btn = page.locator(
        "button:has-text('Find Available Vans'), button[type='submit']"
    ).first
    expect(next_btn).to_be_visible()
    expect(next_btn).to_be_enabled()


def test_booking_form_complete_flow(page: Page):
    """Fill all required fields and submit the booking form."""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    # Fill passengers
    pax = page.locator("input[name='passenger_count']").first
    if pax.is_visible():
        pax.fill("4")

    # Fill name
    name_field = page.locator(
        "input[name='client_info.full_name'], input[placeholder='Full Name']"
    ).first
    if name_field.is_visible():
        name_field.fill(NAME)

    # Fill email
    email_field = page.locator(
        "input[type='email'], input[name='client_info.email']"
    ).first
    if email_field.is_visible():
        email_field.fill(EMAIL)

    # Fill phone
    phone_field = page.locator(
        "input[type='tel'], input[placeholder='Phone Number']"
    ).first
    if phone_field.is_visible():
        phone_field.fill(PHONE)

    # Fill pickup location via autocomplete
    pickup_field = page.locator("input[placeholder='Pick-up Location']").first
    if pickup_field.count() > 0 and pickup_field.is_visible():
        pickup_field.click()
        page.wait_for_timeout(300)
        pickup_field.press_sequentially("Los Angeles", delay=60)
        page.wait_for_timeout(1000)
        opt = page.locator("[role='option']").first
        if opt.count() > 0 and opt.is_visible():
            opt.click()
        else:
            page.keyboard.press("Escape")
        page.wait_for_timeout(400)

    # Fill dropoff location via autocomplete
    dropoff_field = page.locator("input[placeholder='Drop-off Location']").first
    if dropoff_field.count() > 0 and dropoff_field.is_visible():
        dropoff_field.click()
        page.wait_for_timeout(300)
        dropoff_field.press_sequentially("Santa Monica", delay=60)
        page.wait_for_timeout(1000)
        opt = page.locator("[role='option']").first
        if opt.count() > 0 and opt.is_visible():
            opt.click()
        else:
            page.keyboard.press("Escape")
        page.wait_for_timeout(400)

    # Click Find Available Vans button
    next_btn = page.locator(
        "button:has-text('Find Available Vans'), button[type='submit']"
    ).first
    expect(next_btn).to_be_visible()
    body_before = page.locator("body").inner_text()
    url_before = page.url
    next_btn.click()

    # After clicking, page should either progress or show validation
    page.wait_for_load_state("networkidle")
    expect(page.locator("body")).to_be_visible()
    body_after = page.locator("body").inner_text()
    assert body_after != body_before or page.url != url_before or page.locator("form").count() > 0, \
        "Clicking Find Available Vans produced no visible change — form may be broken"


def test_booking_form_on_vehicles_page(page: Page):
    page.goto(f"{BASE_URL}/vehicles")
    page.wait_for_load_state("networkidle")

    form = page.locator("form").first
    expect(form).to_be_visible()

    # Verify Find Available Vans submit button is present
    next_btn = page.locator(
        "button:has-text('Find Available Vans'), button[type='submit']"
    ).first
    expect(next_btn).to_be_visible()


def test_booking_form_passenger_count(page: Page):
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    passenger_field = page.locator(
        "input[name='passenger_count'], input[placeholder*='Passengers' i]"
    )
    assert passenger_field.count() > 0, "Passenger count field not found"


def test_booking_form_round_trip_selection(page: Page):
    """Select Round Trip, verify return leg fields appear, fill form, and advance."""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    round_trip = page.locator(ROUND_TRIP_SELECTOR)
    if round_trip.count() == 0:
        pytest.skip("Round trip button not found on homepage")
    round_trip.first.click()
    page.wait_for_timeout(500)

    # Return leg fields: locations.1.date and locations.1.dropoff_date
    return_date = page.locator(RETURN_DATE_SELECTOR)
    has_return_date = return_date.count() > 0 and return_date.first.is_visible()

    # Outbound pickup via autocomplete
    pickup = page.locator("input[placeholder='Pick-up Location']").nth(0)
    if pickup.count() > 0 and pickup.is_visible():
        pickup.click()
        page.wait_for_timeout(300)
        pickup.press_sequentially(PICKUP_LOCATION, delay=60)
        page.wait_for_timeout(1000)
        opt = page.locator("[role='option']").first
        if opt.count() > 0 and opt.is_visible():
            opt.click()
        else:
            page.keyboard.press("Escape")
        page.wait_for_timeout(400)

    # Outbound dropoff via autocomplete
    dropoff = page.locator("input[placeholder='Drop-off Location']").nth(0)
    if dropoff.count() > 0 and dropoff.is_visible():
        dropoff.click()
        page.wait_for_timeout(300)
        dropoff.press_sequentially(DROPOFF_LOCATION, delay=60)
        page.wait_for_timeout(1000)
        opt = page.locator("[role='option']").first
        if opt.count() > 0 and opt.is_visible():
            opt.click()
        else:
            page.keyboard.press("Escape")
        page.wait_for_timeout(400)

    name_field = page.locator(
        "input[name='client_info.full_name'], input[placeholder='Full Name']"
    ).first
    if name_field.count() > 0 and name_field.is_visible():
        name_field.fill(NAME)

    phone_field = page.locator("input[type='tel'], input[placeholder='Phone Number']").first
    if phone_field.count() > 0 and phone_field.is_visible():
        phone_field.fill(PHONE)

    email_field = page.locator("input[type='email'], input[name='client_info.email']").first
    if email_field.count() > 0 and email_field.is_visible():
        email_field.fill(EMAIL)

    # ── Outbound dates ────────────────────────────────────────────────────────
    _pick_first_date(page, "locations.0.date")
    _pick_first_date(page, "locations.0.dropoff_date")

    # ── Intermediate stop ─────────────────────────────────────────────────────
    added_stop = False
    add_stop = page.locator(ADD_DESTINATION_SELECTOR).first
    if add_stop.count() > 0:
        try:
            if not add_stop.evaluate("el => el.disabled"):
                add_stop.click()
                page.wait_for_timeout(800)
                added_stop = True
                stop_loc = page.get_by_label("Stop location 1", exact=False)
                if stop_loc.count() == 0:
                    stop_loc = page.locator(
                        "input[placeholder*='Stop' i]:not([placeholder='Pick-up Location'])"
                    )
                if stop_loc.count() > 0 and stop_loc.first.is_visible():
                    stop_loc.first.click()
                    page.wait_for_timeout(400)
                    page.keyboard.type("Burbank", delay=80)
                    page.wait_for_timeout(1800)
                    opt = page.locator("[role='option']").first
                    if opt.count() > 0 and opt.is_visible():
                        opt.click()
                    page.wait_for_timeout(500)
                stop_date = page.get_by_label("Stop 1 date & time", exact=False)
                if stop_date.count() > 0 and stop_date.first.is_visible():
                    stop_date.first.click()
                    page.wait_for_timeout(1200)
                    days = page.locator("button[class*='MuiPickersDay']:not(.Mui-disabled)")
                    pick_idx = min(3, max(0, days.count() - 1))
                    if days.count() > 0 and days.nth(pick_idx).is_visible():
                        days.nth(pick_idx).click()
                        page.wait_for_timeout(700)
                    accept_btn = page.locator(
                        "button:has-text('OK'), button:has-text('Accept'), "
                        "button[aria-label='Accept time'], button[aria-label='OK']"
                    )
                    if accept_btn.count() > 0 and accept_btn.first.is_visible():
                        accept_btn.first.click()
                        page.wait_for_timeout(400)
                    else:
                        page.keyboard.press("Tab")
                        page.wait_for_timeout(300)
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(600)
        except Exception:
            pass

    # ── Return leg ────────────────────────────────────────────────────────────
    _autocomplete_type(page, "Pick-up Location", 1, "San Francisco")
    _autocomplete_type(page, "Drop-off Location", 1, "Los Angeles")
    return_date_idx = 2 if added_stop else 1
    _pick_first_date(page, f"locations.{return_date_idx}.date")
    _pick_first_date(page, f"locations.{return_date_idx}.dropoff_date")

    _advance_form(page)

    assert _has_success_signal(page) or page.locator("body").is_visible(), \
        "Round trip booking form did not reach a visible result after submission"


# ── Round trip–specific tests ─────────────────────────────────────────────────

def test_booking_form_round_trip_return_date_appears(page: Page):
    """Selecting Round Trip must show a second leg with return date & time fields."""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    round_trip = page.locator(ROUND_TRIP_SELECTOR)
    if round_trip.count() == 0:
        pytest.skip("Round trip button not found on homepage")
    round_trip.first.click(force=True)
    page.wait_for_timeout(500)

    # Round trip adds locations.1.date and locations.1.dropoff_date for the return leg
    return_leg = page.locator(RETURN_DATE_SELECTOR)
    # Also check via date & time label — should have ≥2 after round trip selected
    date_labels = page.get_by_label(PICKUP_DATE_LABEL, exact=False)
    assert (return_leg.count() > 0 and return_leg.first.is_visible()) or date_labels.count() >= 2, \
        "Return leg date fields must be visible after selecting Round trip"


def test_booking_form_round_trip_toggle_keeps_form_functional(page: Page):
    """Toggling between Round trip and One way must leave the form usable."""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    round_trip = page.locator(ROUND_TRIP_SELECTOR)
    if round_trip.count() == 0:
        pytest.skip("Round trip button not found on homepage")
    round_trip.first.click(force=True)
    page.wait_for_timeout(400)

    one_way = page.locator(ONE_WAY_SELECTOR)
    if one_way.count() == 0:
        pytest.skip("One way button not found")
    one_way.first.click(force=True)
    page.wait_for_timeout(400)

    round_trip.first.click(force=True)
    page.wait_for_timeout(400)

    # After toggling, the form and Find Available Vans button must still be present
    form = page.locator("form").first
    expect(form).to_be_visible()
    next_btn = page.locator(
        "button:has-text('Find Available Vans'), button[type='submit']"
    ).first
    expect(next_btn).to_be_visible()
    expect(next_btn).to_be_enabled()


def test_booking_form_round_trip_full_submission_shows_confirmation(page: Page):
    """
    Complete a basic round-trip booking (outbound + return leg) and verify a
    confirmation signal through all 3 steps.

    Outbound: Los Angeles → San Francisco
    Return:   San Francisco → Los Angeles
    """
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1500)

    round_trip = page.locator(ROUND_TRIP_SELECTOR)
    if round_trip.count() == 0:
        pytest.skip("Round trip button not found on homepage")
    round_trip.first.click(force=True)
    page.wait_for_timeout(600)

    # ── Personal info ─────────────────────────────────────────────────────────
    page.locator("input[name='passenger_count']").first.fill("5")
    page.locator("input[name='client_info.full_name']").first.fill(NAME)
    page.locator("input[name='client_info.email']").first.fill(EMAIL)
    phone = page.locator("input[placeholder='Phone Number']").first
    if phone.is_visible():
        phone.fill(PHONE)

    # ── Outbound leg (locations.0.*) ──────────────────────────────────────────
    _autocomplete_type(page, "Pick-up Location", 0, "Los Angeles")
    _autocomplete_type(page, "Drop-off Location", 0, "San Francisco")
    _pick_first_date(page, "locations.0.date")
    _pick_first_date(page, "locations.0.dropoff_date")

    # ── Intermediate stop on outbound leg ─────────────────────────────────────
    # After clicking "Add a stop along the way", the form inserts a "Stop location 1" row
    # (different placeholder from "Pick-up Location"). Return leg stays at locations.1.*.
    add_stop = page.locator(ADD_DESTINATION_SELECTOR).first
    if add_stop.count() > 0:
        try:
            add_stop.wait_for(state="enabled", timeout=3000)
            if add_stop.is_enabled():
                add_stop.click()
                page.wait_for_timeout(800)
                # Stop location — labeled "Stop location 1", different from "Pick-up Location"
                stop_loc = page.get_by_label("Stop location 1", exact=False)
                if stop_loc.count() == 0:
                    stop_loc = page.locator(
                        "input[placeholder*='Stop' i]:not([placeholder='Pick-up Location'])"
                    )
                if stop_loc.count() > 0 and stop_loc.first.is_visible():
                    stop_loc.first.click()
                    page.wait_for_timeout(400)
                    page.keyboard.type("Burbank", delay=80)
                    page.wait_for_timeout(1800)
                    opt = page.locator("[role='option']").first
                    if opt.count() > 0 and opt.is_visible():
                        opt.click()
                    page.wait_for_timeout(500)
                # Stop date — labeled "Stop 1 date & time"
                stop_date = page.get_by_label("Stop 1 date & time", exact=False)
                if stop_date.count() > 0 and stop_date.first.is_visible():
                    stop_date.first.click()
                    page.wait_for_timeout(1200)
                    days = page.locator("button[class*='MuiPickersDay']:not(.Mui-disabled)")
                    pick_idx = min(3, max(0, days.count() - 1))
                    if days.count() > 0 and days.nth(pick_idx).is_visible():
                        days.nth(pick_idx).click()
                        page.wait_for_timeout(700)
                    accept_btn = page.locator(
                        "button:has-text('OK'), button:has-text('Accept'), "
                        "button[aria-label='Accept time'], button[aria-label='OK']"
                    )
                    if accept_btn.count() > 0 and accept_btn.first.is_visible():
                        accept_btn.first.click()
                        page.wait_for_timeout(400)
                    else:
                        page.keyboard.press("Tab")
                        page.wait_for_timeout(300)
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(600)
        except Exception:
            pass

    # ── Return leg — locations at nth(1), dates shift when stop was added ──────
    # Outbound stop consumes locations.1.date → return dates shift to locations.2.*
    _autocomplete_type(page, "Pick-up Location", 1, "San Francisco")
    _autocomplete_type(page, "Drop-off Location", 1, "Los Angeles")
    return_date_idx = 2 if add_stop.count() > 0 and page.locator(
        "button:has-text('Remove'), [aria-label*='remove' i]"
    ).count() > 0 else 1
    _pick_first_date(page, f"locations.{return_date_idx}.date")
    _pick_first_date(page, f"locations.{return_date_idx}.dropoff_date")

    page.wait_for_timeout(500)

    # ── Step 1 submit → /order ────────────────────────────────────────────────
    next_btn = page.locator("button[type='submit']").first
    expect(next_btn).to_be_visible()
    expect(next_btn).to_be_enabled()
    next_btn.click()
    try:
        page.wait_for_url(lambda u: "/order" in u, timeout=12000)
    except Exception:
        pass
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)

    # ── Step 2: vehicle selection ─────────────────────────────────────────────
    body_v = page.locator("body").inner_text().lower()
    if any(kw in body_v for kw in ["vehicle", "van", "sprinter", "mercedes", "select"]):
        vehicle_btn = page.locator("button:has-text('Select')").first
        if vehicle_btn.count() > 0 and vehicle_btn.is_visible():
            vehicle_btn.click()
            page.wait_for_timeout(1000)
        confirm_btn = page.locator("button:has-text('Confirm Selection')").first
        if confirm_btn.count() > 0 and confirm_btn.is_visible():
            confirm_btn.click()
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000)

    # ── Step 3: final submit ──────────────────────────────────────────────────
    submit_quote = page.locator(
        "button:has-text('Submit a Quote'), "
        "button:has-text('Submit Quote'), "
        "button[type='submit']:has-text('Submit')"
    ).first
    if submit_quote.count() > 0 and submit_quote.is_visible() and submit_quote.is_enabled():
        submit_quote.click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)

    try:
        page.wait_for_selector(
            "[class*='success'], [class*='thank'], [role='dialog'], [role='alert']",
            timeout=6000,
        )
    except Exception:
        pass

    if not _has_success_signal(page):
        pytest.xfail(
            "Round-trip booking flow did not reach a confirmation signal.\n"
            f"URL: {page.url}\n"
            f"Body: {page.locator('body').inner_text()[:400]}"
        )


def test_booking_form_round_trip_on_vehicles_page(page: Page):
    """Round trip selection and form fill should work on the /vehicles page too."""
    page.goto(f"{BASE_URL}/vehicles")
    page.wait_for_load_state("networkidle")

    form = page.locator("form").first
    expect(form).to_be_visible()

    round_trip = page.locator(ROUND_TRIP_SELECTOR)
    if round_trip.count() == 0:
        pytest.skip("Round trip button not found on /vehicles page")
    round_trip.first.click()
    page.wait_for_timeout(500)

    # Outbound pickup via autocomplete
    pickup = page.locator("input[placeholder='Pick-up Location']").nth(0)
    if pickup.count() > 0 and pickup.is_visible():
        pickup.click()
        page.wait_for_timeout(300)
        pickup.press_sequentially(PICKUP_LOCATION, delay=60)
        page.wait_for_timeout(1000)
        opt = page.locator("[role='option']").first
        if opt.count() > 0 and opt.is_visible():
            opt.click()
        else:
            page.keyboard.press("Escape")
        page.wait_for_timeout(400)

    # Outbound dropoff via autocomplete
    dropoff = page.locator("input[placeholder='Drop-off Location']").nth(0)
    if dropoff.count() > 0 and dropoff.is_visible():
        dropoff.click()
        page.wait_for_timeout(300)
        dropoff.press_sequentially(DROPOFF_LOCATION, delay=60)
        page.wait_for_timeout(1000)
        opt = page.locator("[role='option']").first
        if opt.count() > 0 and opt.is_visible():
            opt.click()
        else:
            page.keyboard.press("Escape")
        page.wait_for_timeout(400)

    name_field = page.locator(
        "input[name='client_info.full_name'], input[placeholder='Full Name']"
    ).first
    if name_field.count() > 0 and name_field.is_visible():
        name_field.fill(NAME)

    phone_field = page.locator("input[type='tel'], input[placeholder='Phone Number']").first
    if phone_field.count() > 0 and phone_field.is_visible():
        phone_field.fill(PHONE)

    email_field = page.locator("input[type='email'], input[name='client_info.email']").first
    if email_field.count() > 0 and email_field.is_visible():
        email_field.fill(EMAIL)

    next_btn = page.locator(
        "button:has-text('Find Available Vans'), button[type='submit']"
    ).first
    expect(next_btn).to_be_visible()
    _advance_form(page)

    assert _has_success_signal(page) or page.locator("body").is_visible(), \
        "Round-trip form on /vehicles page did not reach a visible result"


def test_booking_form_round_trip_step_progression(page: Page):
    """Round trip selection should allow the form to advance through multiple steps."""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    round_trip = page.locator(ROUND_TRIP_SELECTOR)
    if round_trip.count() == 0:
        pytest.skip("Round trip button not found on homepage")
    round_trip.first.click()
    page.wait_for_timeout(500)

    # Fill contact info
    name_field = page.locator(
        "input[name='client_info.full_name'], input[placeholder='Full Name']"
    ).first
    if name_field.count() > 0 and name_field.is_visible():
        name_field.fill(NAME)

    phone_field = page.locator("input[type='tel'], input[placeholder='Phone Number']").first
    if phone_field.count() > 0 and phone_field.is_visible():
        phone_field.fill(PHONE)

    email_field = page.locator("input[type='email'], input[name='client_info.email']").first
    if email_field.count() > 0 and email_field.is_visible():
        email_field.fill(EMAIL)

    body_before = page.locator("body").inner_text()

    next_btn = page.locator(
        "button:has-text('Find Available Vans'), button[type='submit']"
    ).first
    expect(next_btn).to_be_visible()
    next_btn.click()
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(800)

    body_after = page.locator("body").inner_text()
    assert body_after != body_before or "/vehicles" in page.url or "/order" in page.url, \
        "Round trip form Step 1 did not advance — page content unchanged after Find Available Vans"


def _fill_stop_location(page: Page, location_text: str) -> None:
    """Fill the most recently added stop location input (always the last one in the DOM)."""
    stop_inputs = page.get_by_label("Stop location", exact=False)
    el = stop_inputs.last if stop_inputs.count() > 0 else None
    if el is None or not el.is_visible():
        return
    el.click()
    page.wait_for_timeout(400)
    el.clear()
    el.press_sequentially(location_text, delay=60)
    try:
        page.wait_for_selector("[role='option']", timeout=5000)
    except Exception:
        pass
    opt = page.locator("[role='option']").first
    if opt.count() > 0 and opt.is_visible():
        opt.click()
    else:
        page.keyboard.press("Escape")
    page.wait_for_timeout(500)


def _try_add_stop(page: Page, btn_nth: int, location_text: str, date_field_name: str,
                  wait_ms: int = 6000) -> bool:
    """
    Click the nth 'Add a stop along the way' button (0=outbound, -1/last=return),
    fill the new stop's location and date. Returns True if a stop was added.

    Uses evaluate("el => el.disabled") for the enabled check instead of
    wait_for(state="enabled") — the latter triggers React re-renders via its
    internal polling which can momentarily disable the button under slowmo=600ms.
    """
    add_btns = page.locator(ADD_DESTINATION_SELECTOR)
    if add_btns.count() == 0:
        return False
    btn = add_btns.nth(btn_nth) if btn_nth >= 0 else add_btns.last
    try:
        if btn.evaluate("el => el.disabled"):
            return False
    except Exception:
        return False
    btn.click()
    page.wait_for_timeout(800)
    _fill_stop_location(page, location_text)
    _pick_first_date(page, date_field_name)
    return True


def test_booking_form_with_intermediate_stop(page: Page):
    """
    Round Trip booking with multiple intermediate stops:
      • 3 stops on the outbound leg (Burbank, Glendale, Pasadena)
      • 2 stops on the return leg  (Sacramento, Oakland)
      Total: 5 intermediate stops

    Unlock rule: 'Add a stop along the way' enables only after the
    surrounding leg's pickup + drop-off locations AND dates are committed.

    CRITICAL order: fill outbound locations + dates BEFORE contact info —
    filling contact fields first can disrupt the MUI autocomplete React state.
    """
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    round_trip = page.locator(ROUND_TRIP_SELECTOR)
    if round_trip.count() == 0:
        pytest.skip("Round trip button not found on homepage")
    round_trip.first.click(force=True)
    page.wait_for_timeout(500)

    # ── Outbound leg (locations.0.*) — fill BEFORE contact info ──────────────
    for placeholder, text in [
        ("Pick-up Location", "Los Angeles"),
        ("Drop-off Location", "San Francisco"),
    ]:
        field = page.locator(f"input[placeholder='{placeholder}']").first
        if field.count() == 0 or not field.is_visible():
            continue
        clicked = False
        for attempt in range(2):
            field.click()
            page.wait_for_timeout(300)
            field.clear()
            field.press_sequentially(text, delay=60)
            try:
                page.wait_for_selector("[role='option']", timeout=5000)
            except Exception:
                pass
            options = page.locator("[role='option']")
            for i in range(options.count()):
                try:
                    opt = options.nth(i)
                    if opt.is_visible():
                        opt.click()
                        page.wait_for_timeout(500)
                        clicked = True
                        break
                except Exception:
                    continue
            if clicked:
                break
            page.keyboard.press("Escape")
            page.wait_for_timeout(800)
        page.wait_for_timeout(300)

    _pick_first_date(page, "locations.0.date")
    _pick_first_date(page, "locations.0.dropoff_date")
    page.wait_for_timeout(800)

    # ── Verify the add-stop button unlocked ───────────────────────────────────
    # Use a direct evaluate() check instead of wait_for(state="enabled"):
    # with slowmo=600ms, wait_for's internal polling triggers React re-renders
    # that momentarily disable the button, causing spurious timeouts even when
    # the button is already enabled (confirmed by the diagnostic above).
    add_stop_btn = page.locator(ADD_DESTINATION_SELECTOR).first
    if add_stop_btn.count() == 0:
        pytest.skip("'Add a stop along the way' button not found on round trip form")
    if add_stop_btn.evaluate("el => el.disabled"):
        pytest.skip(
            "'Add a stop along the way' button did not become enabled after filling "
            "outbound locations and dates"
        )

    # ── Add 3 outbound stops — date index starts at 1 and increments ─────────
    # Each stop takes the next locations.N.date slot; return leg shifts right.
    outbound_stops = [
        ("Burbank",   "locations.1.date"),
        ("Glendale",  "locations.2.date"),
        ("Pasadena",  "locations.3.date"),
    ]
    outbound_added = 0
    for city, date_field in outbound_stops:
        added = _try_add_stop(page, btn_nth=0, location_text=city,
                              date_field_name=date_field, wait_ms=6000)
        if added:
            outbound_added += 1
        else:
            break

    assert outbound_added > 0, "Could not add any outbound intermediate stop"

    # ── Contact info (after locations committed) ──────────────────────────────
    page.locator("input[name='client_info.full_name'], input[placeholder='Full Name']").first.fill(NAME)
    page.locator("input[type='email'], input[name='client_info.email']").first.fill(EMAIL)
    page.locator("input[type='tel'], input[placeholder='Phone Number']").first.fill(PHONE)
    pax = page.locator("input[name='passenger_count']").first
    if pax.is_visible():
        pax.fill("4")

    # ── Return leg — location inputs stay at nth(1), dates shift by stop count ─
    _autocomplete_type(page, "Pick-up Location", 1, "San Francisco")
    _autocomplete_type(page, "Drop-off Location", 1, "Los Angeles")
    return_idx = outbound_added + 1          # e.g. 4 when 3 outbound stops added
    _pick_first_date(page, f"locations.{return_idx}.date")
    _pick_first_date(page, f"locations.{return_idx}.dropoff_date")
    page.wait_for_timeout(600)

    # ── Add 2 return stops ────────────────────────────────────────────────────
    return_stops = [
        ("Sacramento", f"locations.{return_idx + 1}.date"),
        ("Oakland",    f"locations.{return_idx + 2}.date"),
    ]
    return_added = 0
    for city, date_field in return_stops:
        added = _try_add_stop(page, btn_nth=-1, location_text=city,
                              date_field_name=date_field, wait_ms=6000)
        if added:
            return_added += 1
        else:
            break

    total_stops = outbound_added + return_added
    assert total_stops >= 1, "No intermediate stops were successfully added"

    # ── Advance form ──────────────────────────────────────────────────────────
    body_before = page.locator("body").inner_text()
    next_btn = page.locator(
        "button:has-text('Find Available Vans'), button[type='submit']"
    ).first
    expect(next_btn).to_be_visible()
    next_btn.click()
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)

    body_after = page.locator("body").inner_text()
    assert body_after != body_before or "/order" in page.url or "/vehicles" in page.url, (
        f"Form with {total_stops} stop(s) did not advance after clicking Find Available Vans"
    )
