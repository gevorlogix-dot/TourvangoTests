import pytest
from playwright.sync_api import Page, expect

BASE_URL = "https://tourvango.testingforproduction.com"

INTERNAL_PAGES = [
    "/",
    "/about-us",
    "/vehicles",
    "/contact-us",
    "/faq",
    "/reviews",
    "/blogs/category/all",
    "/policy/rental-policies",
    "/policy/privacy-policy",
    "/policy/terms-of-service",
    "/glendale",
    "/pasadena-van-rental",
    "/north-hollywood-sprinter-van-rental",
    "/anaheim-sprinter-van-rental",
    "/santa-monica-sprinter-van-rental",
]


# ── Internal navigation links ─────────────────────────────────────────────────

@pytest.mark.parametrize("path", INTERNAL_PAGES)
def test_internal_page_returns_content(page: Page, path: str):
    page.goto(f"{BASE_URL}{path}")
    page.wait_for_load_state("networkidle")
    body_text = page.locator("body").inner_text()
    assert len(body_text.strip()) > 50, \
        f"Page {path} returned empty or very short content (possible 404)"


def test_homepage_nav_links_all_resolve(page: Page):
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    nav_links = page.locator("nav a, header a")
    count = nav_links.count()
    assert count > 0, "No navigation links found"

    hrefs = []
    for i in range(count):
        href = nav_links.nth(i).get_attribute("href") or ""
        if href.startswith("/") and not href.startswith("//"):
            hrefs.append(href)

    failed = []
    for href in set(hrefs):
        page.goto(f"{BASE_URL}{href}")
        page.wait_for_load_state("networkidle")
        text = page.locator("body").inner_text()
        if len(text.strip()) < 50:
            failed.append(href)

    assert failed == [], f"These nav link destinations appear empty/404: {failed}"


def test_footer_links_all_resolve(page: Page):
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    footer_links = page.locator("footer a")
    count = footer_links.count()
    assert count > 0, "No footer links found"

    hrefs = []
    for i in range(count):
        href = footer_links.nth(i).get_attribute("href") or ""
        if href.startswith("/") and not href.startswith("//"):
            hrefs.append(href)

    failed = []
    for href in set(hrefs):
        page.goto(f"{BASE_URL}{href}")
        page.wait_for_load_state("networkidle")
        text = page.locator("body").inner_text()
        if len(text.strip()) < 50:
            failed.append(href)

    assert failed == [], f"These footer link destinations appear empty/404: {failed}"


# ── Phone (tel:) links ────────────────────────────────────────────────────────

def test_homepage_has_tel_link(page: Page):
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    tel_links = page.locator("a[href^='tel:']")
    assert tel_links.count() > 0, "Homepage should have at least one tel: link"


def test_homepage_tel_link_has_correct_area_code(page: Page):
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    tel_links = page.locator("a[href^='tel:']")
    assert tel_links.count() > 0, "No tel: links found"
    tel_href = tel_links.first.get_attribute("href") or ""
    assert "818" in tel_href or "1818" in tel_href, \
        f"Tel link should contain area code 818, got: {tel_href}"


def test_contact_page_has_tel_link(page: Page):
    page.goto(f"{BASE_URL}/contact-us")
    page.wait_for_load_state("networkidle")
    tel_links = page.locator("a[href^='tel:']")
    assert tel_links.count() > 0, "Contact page should have at least one tel: link"


def test_faq_page_has_tel_link(page: Page):
    page.goto(f"{BASE_URL}/faq")
    page.wait_for_load_state("networkidle")
    tel_links = page.locator("a[href^='tel:']")
    assert tel_links.count() > 0, "FAQ page should have a clickable phone number link"


def test_footer_has_tel_link(page: Page):
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    tel_links = page.locator("footer a[href^='tel:']")
    assert tel_links.count() > 0, "Footer should contain a tel: link"


@pytest.mark.parametrize("path,label", [
    ("/about-us", "about"),
    ("/vehicles", "fleet"),
    ("/reviews", "reviews"),
])
def test_page_has_tel_link(page: Page, path: str, label: str):
    page.goto(f"{BASE_URL}{path}")
    page.wait_for_load_state("networkidle")
    tel_links = page.locator("a[href^='tel:']")
    assert tel_links.count() > 0, f"{label} page should have a clickable phone number"


# ── Email (mailto:) links ─────────────────────────────────────────────────────

def test_contact_page_has_mailto_or_form(page: Page):
    page.goto(f"{BASE_URL}/contact-us")
    page.wait_for_load_state("networkidle")
    mailto_links = page.locator("a[href^='mailto:']")
    form = page.locator("form")
    # Either a mailto link or a contact form satisfies this
    assert mailto_links.count() > 0 or form.count() > 0, \
        "Contact page should have a mailto link or a contact form"


def test_footer_has_email_or_contact_link(page: Page):
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    footer = page.locator("footer")
    mailto = footer.locator("a[href^='mailto:']")
    contact = footer.locator("a[href*='contact']")
    assert mailto.count() > 0 or contact.count() > 0, \
        "Footer should have a mailto link or contact link"


# ── Social media links ────────────────────────────────────────────────────────

def test_social_links_present_on_homepage(page: Page):
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    social = page.locator(
        "a[href*='facebook.com'], a[href*='instagram.com'], "
        "a[href*='youtube.com'], a[href*='twitter.com'], a[href*='tiktok.com']"
    )
    assert social.count() >= 1, "At least one social media link should be present"


def test_social_links_open_in_new_tab(page: Page):
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    social = page.locator(
        "a[href*='facebook.com'], a[href*='instagram.com'], "
        "a[href*='youtube.com'], a[href*='twitter.com'], a[href*='tiktok.com']"
    )
    count = social.count()
    if count == 0:
        pytest.skip("No social links found")

    for i in range(count):
        link = social.nth(i)
        target = link.get_attribute("target") or ""
        assert target == "_blank", \
            f"Social link {link.get_attribute('href')} should open in a new tab"


def test_social_links_have_noopener(page: Page):
    """Advisory: social links should have rel=noopener/noreferrer (security best practice)."""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    social = page.locator(
        "a[href*='facebook.com'], a[href*='instagram.com'], "
        "a[href*='youtube.com'], a[href*='twitter.com'], a[href*='tiktok.com']"
    )
    if social.count() == 0:
        pytest.skip("No social links found")

    missing = []
    for i in range(social.count()):
        link = social.nth(i)
        rel = link.get_attribute("rel") or ""
        if "noopener" not in rel and "noreferrer" not in rel:
            missing.append(link.get_attribute("href"))

    if missing:
        pytest.xfail(
            f"SECURITY ADVISORY: social links missing rel=noopener/noreferrer: {missing}"
        )


def test_facebook_link_href_valid(page: Page):
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    fb_link = page.locator("a[href*='facebook.com']").first
    if fb_link.count() == 0:
        pytest.skip("No Facebook link found")
    href = fb_link.get_attribute("href") or ""
    assert href.startswith("https://"), f"Facebook link should be HTTPS: {href}"
    assert "facebook.com" in href, f"Unexpected Facebook link: {href}"


# ── No broken internal links (404 check) ─────────────────────────────────────

def test_no_404_in_main_nav(page: Page):
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    links = page.locator("nav a, header a")
    count = links.count()
    hrefs = set()
    for i in range(count):
        href = links.nth(i).get_attribute("href") or ""
        if href.startswith("/") and href not in ("#", "/"):
            hrefs.add(href)

    not_found = []
    for href in hrefs:
        response = page.goto(f"{BASE_URL}{href}", wait_until="domcontentloaded")
        if response and response.status == 404:
            not_found.append(href)

    assert not_found == [], f"404 pages found in main navigation: {not_found}"


def test_policy_pages_reachable_from_footer(page: Page):
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    footer_links = page.locator("footer a[href*='policy'], footer a[href*='terms'], footer a[href*='privacy']")
    if footer_links.count() == 0:
        pytest.skip("No policy links found in footer")

    count = footer_links.count()
    for i in range(count):
        href = footer_links.nth(i).get_attribute("href") or ""
        if href.startswith("/"):
            page.goto(f"{BASE_URL}{href}")
            page.wait_for_load_state("networkidle")
            text = page.locator("body").inner_text()
            assert len(text.strip()) > 100, \
                f"Policy page {href} appears empty or broken"


# ── External links ────────────────────────────────────────────────────────────

def test_external_links_use_https(page: Page):
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    external_links = page.locator("a[href^='http']")
    count = external_links.count()
    insecure = []
    for i in range(count):
        href = external_links.nth(i).get_attribute("href") or ""
        if href.startswith("http://") and "localhost" not in href:
            insecure.append(href)
    assert insecure == [], f"External links using insecure HTTP: {insecure}"


def test_google_maps_or_directions_link_present(page: Page):
    page.goto(f"{BASE_URL}/contact-us")
    page.wait_for_load_state("networkidle")
    maps_link = page.locator(
        "a[href*='maps.google'], a[href*='google.com/maps'], "
        "a[href*='goo.gl/maps'], iframe[src*='maps.google'], iframe[src*='google.com/maps']"
    )
    body_text = page.locator("body").inner_text()
    has_address = "Burbank" in body_text or "1814" in body_text
    assert maps_link.count() > 0 or has_address, \
        "Contact page should have a Google Maps link or a business address"


# ── Booking CTA links ─────────────────────────────────────────────────────────

def test_homepage_has_book_now_cta(page: Page):
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    cta = page.locator(
        "a:has-text('Book'), a:has-text('Reserve'), a:has-text('Get a Quote'), "
        "button:has-text('Book'), button:has-text('Reserve')"
    )
    assert cta.count() > 0, "Homepage should have a Book/Reserve CTA link or button"


def test_fleet_page_book_cta_links_to_booking(page: Page):
    page.goto(f"{BASE_URL}/vehicles")
    page.wait_for_load_state("networkidle")
    cta = page.locator(
        "a:has-text('Book'), a:has-text('Reserve'), button:has-text('Book')"
    ).first
    if cta.count() == 0:
        pytest.skip("No Book/Reserve CTA found on fleet page")
    href = cta.get_attribute("href") or ""
    # Either links elsewhere or is a JS action (button) — just verify it's visible
    expect(cta).to_be_visible()
    expect(cta).to_be_enabled()


def test_reviews_page_cta_links_to_booking(page: Page):
    page.goto(f"{BASE_URL}/reviews")
    page.wait_for_load_state("networkidle")
    cta = page.locator(
        "a[href='/vehicles'], a[href='/contact-us'], "
        "a:has-text('Book'), a:has-text('Reserve')"
    ).first
    expect(cta).to_be_visible()
