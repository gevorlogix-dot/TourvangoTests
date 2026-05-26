# TourVanGo Playwright Test Suite

## Project
Automated QA test suite for **https://tourvango.testingforproduction.com** — a Sprinter van rental service based in Burbank, CA.

## Stack
- **Python 3.13** + **pytest 9** + **pytest-playwright 0.7**
- Browser: Chromium (headed or headless)
- All tests in `tests/`

## Running tests

```bash
# All tests (headless)
python -m pytest tests/

# All tests headed (visible browser, 500ms slow-mo)
python -m pytest tests/ --headed --slowmo=500

# Single file headed
python -m pytest tests/test_form_submission.py --headed --slowmo=600 -v

# One specific test
python -m pytest tests/test_form_submission.py::test_contact_form_submission_shows_confirmation --headed -v
```

## Test files

| File | What it covers |
|---|---|
| `test_homepage.py` | Title, nav, hero form, phone, footer, social links |
| `test_booking_form.py` | Booking form fields, trip type, Next button, passenger count |
| `test_form_submission.py` | **Full form submissions** — contact & booking — verifies thank-you confirmation |
| `test_contact.py` | Contact page fields, full submission, address, phone |
| `test_navigation.py` | All nav links, browser back, footer policy links |
| `test_fleet.py` | /vehicles page content, form, CTA |
| `test_faq.py` | FAQ questions, accordion, contact link |
| `test_static_pages.py` | About, reviews, blog, policies, location pages |
| `test_seo.py` | Title, meta description, OG tags, canonical, H1, viewport meta |
| `test_responsive.py` | Mobile (390px), tablet (768px), desktop (1920px) |
| `test_images.py` | No broken images, alt text, logo |
| `test_blog.py` | Blog index, post open, heading, content, breadcrumb |
| `test_reviews_page.py` | Ratings, Google reference, CTA, phone |
| `test_accessibility.py` | lang attr, form labels, button names, ARIA landmarks, tab order |
| `test_form_validation.py` | HTML5 validation, email/phone types, required fields, clearing |
| `test_links.py` | Internal links, tel: links (area 818), social links, HTTPS, CTAs |

## Key constants (conftest.py)
```python
BASE_URL  = "https://tourvango.testingforproduction.com"
NAME      = "George Test"
EMAIL     = "gevorlogix@gmail.com"
PHONE     = "4387985779"   # auto-formatted to (438) 798-5779 by the site
```

## Architecture
- **Session-scoped `page` fixture** in `conftest.py` — all tests reuse **one browser tab**, no new windows per test.
- `test_responsive.py` explicitly creates its own `browser.new_context()` for mobile/tablet viewports — those tests open separate contexts intentionally.

## Known site issues (xfail / advisory)
| Test | Issue |
|---|---|
| `test_social_links_have_noopener` | Social links missing `rel="noopener"` — security advisory |
| `test_contact_form_empty_submit_shows_validation_not_success` | Site accepts blank submissions (no client-side validation) — marked xfail if triggered |

## Business info (for assertions)
- Phone: **818-566-0005** (area code 818)
- Address: **1814 ... Burbank, CA**
- Google rating: **4.3 / 5** · 77 reviews
- Vehicle capacity: **8–17 passengers** (Mercedes Sprinter vans)
