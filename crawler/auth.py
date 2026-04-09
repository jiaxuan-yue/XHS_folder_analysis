"""XHS authentication using Playwright persistent browser context.

Uses a persistent browser profile to save login sessions across runs.
On first run, opens a visible browser for QR code login.
Subsequent runs reuse the saved session automatically.
"""

import shutil
import time
from pathlib import Path
from typing import Optional

from playwright.sync_api import sync_playwright, BrowserContext, Page

from utils.logger import get_logger

logger = get_logger(__name__)

XHS_EXPLORE_URL = "https://www.xiaohongshu.com/explore"
# Selector that indicates the user is logged in (user avatar / profile link)
LOGIN_SUCCESS_SELECTOR = ".user .user-image, .side-bar .user-avatar"
# Selector for the login dialog / QR code area
LOGIN_DIALOG_SELECTOR = ".login-container, .qrcode-img"

DEFAULT_PROFILE_DIR = str(Path.home() / ".xhs" / "browser_profile")
DEFAULT_LOGIN_TIMEOUT = 120


def get_profile_dir(config: Optional[dict] = None) -> str:
    """Get the browser profile directory from config or default."""
    if config and "auth" in config:
        raw = config["auth"].get("profile_dir", DEFAULT_PROFILE_DIR)
        return str(Path(raw).expanduser())
    return DEFAULT_PROFILE_DIR


def get_login_timeout(config: Optional[dict] = None) -> int:
    """Get login timeout from config or default."""
    if config and "auth" in config:
        return config["auth"].get("login_timeout", DEFAULT_LOGIN_TIMEOUT)
    return DEFAULT_LOGIN_TIMEOUT


def create_browser_context(
    playwright,
    profile_dir: str,
    headless: bool = False,
) -> BrowserContext:
    """Create a persistent browser context with the given profile directory.

    Args:
        playwright: Playwright instance.
        profile_dir: Path to store browser profile (cookies, storage, etc.).
        headless: Whether to run headless. Forced to False during login.

    Returns:
        BrowserContext with persistent storage.
    """
    Path(profile_dir).mkdir(parents=True, exist_ok=True)

    context = playwright.chromium.launch_persistent_context(
        user_data_dir=profile_dir,
        headless=headless,
        viewport={"width": 1280, "height": 800},
        user_agent=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        locale="zh-CN",
        timezone_id="Asia/Shanghai",
    )
    return context


def check_login_status(page: Page, timeout: float = 5.0) -> bool:
    """Check if the current page shows a logged-in state.

    Args:
        page: Playwright Page object.
        timeout: Max seconds to wait for login indicator.

    Returns:
        True if logged in, False otherwise.
    """
    try:
        page.wait_for_selector(LOGIN_SUCCESS_SELECTOR, timeout=timeout * 1000)
        return True
    except Exception:
        return False


def wait_for_login(page: Page, timeout: float = DEFAULT_LOGIN_TIMEOUT) -> bool:
    """Poll the page for login success.

    Args:
        page: Playwright Page navigated to XHS.
        timeout: Max seconds to wait.

    Returns:
        True if login detected within timeout.
    """
    logger.info(f"Waiting for QR code login (timeout: {timeout}s)...")
    logger.info("Please scan the QR code with the Xiaohongshu app on your phone.")
    start = time.time()
    while time.time() - start < timeout:
        if check_login_status(page, timeout=1.0):
            logger.info("Login successful!")
            return True
        time.sleep(1.0)
    logger.warning("Login timed out.")
    return False


def ensure_logged_in(config: Optional[dict] = None) -> tuple:
    """Ensure we have an authenticated browser context.

    Returns a (playwright, context, page) tuple. The caller is responsible
    for closing the context when done.

    Flow:
    1. Open persistent context (may already have valid session).
    2. Navigate to XHS explore page.
    3. Check login status.
    4. If not logged in, switch to visible mode and wait for QR scan.

    Returns:
        Tuple of (playwright_instance, browser_context, page).
    """
    profile_dir = get_profile_dir(config)
    login_timeout = get_login_timeout(config)
    headless = config.get("crawler", {}).get("headless", True) if config else True

    pw = sync_playwright().start()

    # First try with configured headless mode
    context = create_browser_context(pw, profile_dir, headless=headless)
    page = context.pages[0] if context.pages else context.new_page()

    logger.info("Navigating to XHS explore page...")
    page.goto(XHS_EXPLORE_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(2000)

    if check_login_status(page):
        logger.info("Already logged in (session restored from profile).")
        return pw, context, page

    # Not logged in — need visible browser for QR code
    if headless:
        logger.info("Not logged in. Reopening browser in visible mode for QR login...")
        context.close()
        context = create_browser_context(pw, profile_dir, headless=False)
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(XHS_EXPLORE_URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(2000)

    # Wait for user to scan QR code
    success = wait_for_login(page, timeout=login_timeout)
    if not success:
        context.close()
        pw.stop()
        raise TimeoutError(
            f"Login timed out after {login_timeout}s. "
            "Please try again and scan the QR code promptly."
        )

    return pw, context, page


def logout(config: Optional[dict] = None) -> None:
    """Clear the browser profile to logout."""
    profile_dir = get_profile_dir(config)
    profile_path = Path(profile_dir)
    if profile_path.exists():
        shutil.rmtree(profile_path)
        logger.info(f"Browser profile cleared: {profile_dir}")
    else:
        logger.info("No browser profile found, already logged out.")
