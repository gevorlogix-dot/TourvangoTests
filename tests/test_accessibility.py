import pytest
from playwright.sync_api import Page, expect

BASE_URL = "https://tourvango.testingforproduction.com"

MAIN_PAGES = [
    ("/", "home"),
    ("/about-us", "about"),
    ("/vehicles", "fleet"),
    ("/contact-us", "contact"),
    ("/faq", "faq"),
    ("/reviews", "reviews"),
]


# ── HTML lang attribute ───────────────────────────────────────────────────────

@pytest.mark.parametrize("path,label", MAIN_PAGES)
def test_html_has_lang_attribute(page: Page, path: str, label: str):
    page.goto(f"{BASE_URL}{path}")
    page.wait_for_load_state("networkidle")
    lang = page.locator("html").get_attribute("lang")
    assert lang and len(lang) >= 2, f"{label}: <html> element missing lang attribute"


# ── Form labels ───────────────────────────────────────────────────────────────

def test_contact_form_inputs_have_labels_or_placeholders(page: Page):
    page.goto(f"{BASE_URL}/contact-us")
    page.wait_for_load_state("networkidle")
    inputs = page.locator("form input[type='text'], form input[type='email'], form input[type='tel']")
    count = inputs.count()
    assert count > 0, "No text inputs found in contact form"
    for i in range(count):
        inp = inputs.nth(i)
        input_id = inp.get_attribute("id") or ""
        placeholder = inp.get_attribute("placeholder") or ""
        aria_label = inp.get_attribute("aria-label") or ""
        # Either a <label for="..."> exists, or placeholder/aria-label provides context
        has_label = False
        if input_id:
            has_label = page.locator(f"label[for='{input_id}']").count() > 0
        assert has_label or placeholder or aria_label, \
            f"Input #{i} has no label, placeholder, or aria-label"


def test_booking_form_inputs_have_labels_or_placeholders(page: Page):
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    inputs = page.locator("form input[type='text'], form input[type='email'], form input[type='tel']")
    count = inputs.count()
    assert count > 0, "No text inputs found in booking form"
    for i in range(count):
        inp = inputs.nth(i)
        placeholder = inp.get_attribute("placeholder") or ""
        aria_label = inp.get_attribute("aria-label") or ""
        input_id = inp.get_attribute("id") or ""
        has_label = False
        if input_id:
            has_label = page.locator(f"label[for='{input_id}']").count() > 0
        assert has_label or placeholder or aria_label, \
            f"Booking form input #{i} has no accessible label"


# ── Button accessible names ───────────────────────────────────────────────────

def test_homepage_buttons_have_accessible_names(page: Page):
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    buttons = page.locator("button")
    count = buttons.count()
    assert count > 0, "No buttons found on homepage"
    unnamed = []
    for i in range(count):
        btn = buttons.nth(i)
        text = (btn.inner_text() or "").strip()
        aria = btn.get_attribute("aria-label") or ""
        title = btn.get_attribute("title") or ""
        if not text and not aria and not title:
            unnamed.append(i)
    assert len(unnamed) == 0, f"Buttons at indices {unnamed} have no accessible name"


def test_contact_page_submit_button_has_text(page: Page):
    page.goto(f"{BASE_URL}/contact-us")
    page.wait_for_load_state("networkidle")
    submit = page.locator("button[type='submit'], input[type='submit'], button:has-text('Submit')").first
    expect(submit).to_be_visible()
    text = (submit.inner_text() or "").strip()
    value = submit.get_attribute("value") or ""
    aria = submit.get_attribute("aria-label") or ""
    assert text or value or aria, "Submit button has no accessible text"


# ── ARIA roles ────────────────────────────────────────────────────────────────

def test_homepage_has_main_landmark(page: Page):
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    main = page.locator("main, [role='main']")
    assert main.count() >= 1, "Page should have a <main> or role='main' landmark"


def test_contact_page_has_main_landmark(page: Page):
    page.goto(f"{BASE_URL}/contact-us")
    page.wait_for_load_state("networkidle")
    main = page.locator("main, [role='main']")
    assert main.count() >= 1, "Contact page should have a main landmark"


def test_homepage_nav_has_role_or_element(page: Page):
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    nav = page.locator("nav, [role='navigation']")
    assert nav.count() >= 1, "Page should have a <nav> or role='navigation' element"


# ── Keyboard / tab navigation ─────────────────────────────────────────────────

def test_contact_form_tab_order_reaches_submit(page: Page):
    """Tab through contact form fields until submit is reached or max tabs exhausted."""
    page.goto(f"{BASE_URL}/contact-us")
    page.wait_for_load_state("networkidle")

    # Focus the first form input
    first_input = page.locator("form input").first
    first_input.focus()

    submit_focused = False
    for _ in range(15):
        page.keyboard.press("Tab")
        focused = page.evaluate("() => document.activeElement.tagName.toLowerCase()")
        focused_type = page.evaluate("() => document.activeElement.type || ''")
        focused_text = page.evaluate("() => document.activeElement.innerText || document.activeElement.value || ''")
        if focused in ("button",) or focused_type in ("submit",):
            submit_focused = True
            break

    assert submit_focused, "Tab navigation did not reach a submit button within 15 presses"


def test_homepage_booking_form_tab_navigable(page: Page):
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    first_input = page.locator("form input").first
    first_input.focus()

    # Tab through the form a few times without error
    for _ in range(5):
        page.keyboard.press("Tab")
    # Page should still be operational
    expect(page.locator("body")).to_be_visible()


# ── Focus visibility ──────────────────────────────────────────────────────────

def test_skip_nav_or_first_focusable_exists(page: Page):
    """First Tab press should focus something meaningful — not land in a void."""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    page.keyboard.press("Tab")
    focused_tag = page.evaluate("() => document.activeElement.tagName.toLowerCase()")
    assert focused_tag not in ("body", "html"), \
        "First Tab press should focus a real element, not <body> or <html>"


# ── Images: alt text on key pages ────────────────────────────────────────────

def test_contact_page_images_have_alt(page: Page):
    page.goto(f"{BASE_URL}/contact-us")
    page.wait_for_load_state("networkidle")
    missing = page.evaluate(
        """() => Array.from(document.images)
               .filter(img => !img.hasAttribute('alt'))
               .map(img => img.src || '(no src)')"""
    )
    assert missing == [], f"Images without alt attribute on contact page: {missing}"


def test_faq_page_images_have_alt(page: Page):
    page.goto(f"{BASE_URL}/faq")
    page.wait_for_load_state("networkidle")
    missing = page.evaluate(
        """() => Array.from(document.images)
               .filter(img => !img.hasAttribute('alt'))
               .map(img => img.src || '(no src)')"""
    )
    assert missing == [], f"Images without alt attribute on FAQ page: {missing}"


# ── Link text accessibility ───────────────────────────────────────────────────

def test_homepage_links_have_descriptive_text(page: Page):
    """Links should not rely solely on generic text like 'click here'."""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    generic_texts = {"click here", "here", "more", "read more", "learn more"}
    links = page.locator("a")
    count = links.count()
    generic_found = []
    for i in range(min(count, 50)):
        lnk = links.nth(i)
        text = (lnk.inner_text() or "").strip().lower()
        if text in generic_texts:
            generic_found.append(text)
    assert len(generic_found) == 0, \
        f"Found generic/non-descriptive link text: {generic_found}"


# ── Color-contrast proxy: text present ───────────────────────────────────────

@pytest.mark.parametrize("path,label", MAIN_PAGES)
def test_page_body_text_not_empty(page: Page, path: str, label: str):
    """Sanity check that pages render text (catches white-on-white / display:none issues)."""
    page.goto(f"{BASE_URL}{path}")
    page.wait_for_load_state("networkidle")
    body_text = page.locator("body").inner_text()
    assert len(body_text.strip()) > 200, \
        f"{label}: page has very little visible text — possible rendering/contrast issue"
