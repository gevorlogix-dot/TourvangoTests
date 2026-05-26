import pytest
from collections.abc import Iterator
from playwright.sync_api import Browser, BrowserContext, Page

BASE_URL = "https://tourvango.testingforproduction.com"

TEST_USER = {
    "email": "gevorlogix@gmail.com",
    "phone": "4387985779",
    "name": "George Test",
    "message": "This is an automated test message. Please ignore.",
}

PICKUP_DATE = "06/15/2026"
DROPOFF_DATE = "06/20/2026"
PICKUP_LOCATION = "Los Angeles, CA"
DROPOFF_LOCATION = "Santa Monica, CA"


@pytest.fixture(scope="session")
def test_user():
    return TEST_USER


# ── Single browser tab reused across all tests ────────────────────────────────

@pytest.fixture(scope="session")
def context(browser: Browser) -> Iterator[BrowserContext]:
    ctx = browser.new_context(viewport={"width": 1280, "height": 800})
    yield ctx
    ctx.close()


@pytest.fixture(scope="session")
def page(context: BrowserContext) -> Iterator[Page]:
    p = context.new_page()
    yield p
    p.close()


# Keep this for any test that explicitly re-uses browser_context_args
@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 800},
    }
