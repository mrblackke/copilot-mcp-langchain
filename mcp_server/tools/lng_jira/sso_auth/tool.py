import mcp.types as types
import os
import requests
from pathlib import Path
from urllib.parse import urlparse
from dotenv import dotenv_values, set_key

# ---------------------------------------------------------------------------
# lng_jira_sso_auth
# ---------------------------------------------------------------------------
# Authenticates to Jira via Microsoft SSO using Playwright browser automation.
# Opens a Chromium browser, navigates to Jira, handles the Microsoft SSO redirect,
# fills credentials, and extracts session cookies into JIRA_SESSION in .env.
#
# **Local use (headless=false, default):**
#   Browser opens visibly → fill credentials → complete MFA manually → cookies saved.
#
# **Headless / container use:**
#   Requires totp_secret (TOTP base32 key from Microsoft Authenticator "Can't scan QR" view).
#   Install virtual display on Linux: apt-get install -y xvfb (or use headless Chromium).
#
# **Cookie lifecycle:**
#   JSESSIONID from EPAM Jira typically lasts 8 hours. Re-run this tool to refresh.
#   For CI/containers: run locally → copy JIRA_SESSION to container .env / secret.
# ---------------------------------------------------------------------------


async def tool_info() -> dict:
    """Returns information about the lng_jira_sso_auth tool."""
    return {
        "description": """Authenticates to Jira via Microsoft SSO using Playwright browser automation.

Opens a Chromium browser, navigates to your Jira instance, handles the Microsoft SSO
redirect, fills in credentials, and extracts the session cookies. The result is saved
as JIRA_SESSION in your .env file and is ready for use by other Jira tools immediately.

**How it works:**
1. Opens Chromium and navigates to jira_url
2. Clicks the "Log in with Microsoft" SSO button
3. Fills username → password on Microsoft login page
4. If totp_secret is provided: generates TOTP code and fills it automatically
5. If headless=false (default): waits for you to complete MFA manually in the browser
6. Waits until redirected back to Jira, extracts all cookies
7. Saves JIRA_SESSION=<cookies> to .env file

**Parameters:**
- `jira_url` (string, optional): Jira base URL. Default: JIRA_URL from .env
- `username` (string, optional): Microsoft SSO email. Default: JIRA_SSO_USERNAME from .env
- `password` (string, optional): Microsoft SSO password. Default: JIRA_SSO_PASSWORD from .env
- `totp_secret` (string, optional): TOTP base32 secret for automatic MFA.
    Get it from Microsoft Authenticator → your account → "Can't scan QR code?".
    Default: JIRA_TOTP_SECRET from .env
- `headless` (boolean, optional): Run browser headlessly, default false.
    Set true for containers — requires totp_secret for MFA.
- `timeout_sec` (integer, optional): Max seconds to wait for login completion. Default: 120
- `env_file` (string, optional): .env file to update. Default: .env
- `check_existing` (boolean, optional): Test existing JIRA_SESSION before re-authenticating.
    If valid, returns immediately without opening browser. Default: true

**Required .env variables:**
- `JIRA_URL`: Jira base URL (e.g. https://jiraeu.epam.com)
- `JIRA_SSO_USERNAME`: Your corporate Microsoft email
- `JIRA_SSO_PASSWORD`: Your Microsoft password
- `JIRA_TOTP_SECRET` (optional): TOTP base32 secret (only for headless MFA)

**For container deployments:**
Run this tool locally (headless=false) to get an initial JIRA_SESSION, then copy it to
your container's .env or secrets. Re-run when the session expires (~8 hours for EPAM Jira).
With a TOTP secret, the container can refresh the session automatically.

**Returns:** Success message with cookie preview and session validity.""",
        "schema": {
            "type": "object",
            "properties": {
                "jira_url": {
                    "type": "string",
                    "description": "Jira base URL (e.g. https://jiraeu.epam.com). Default: JIRA_URL from .env"
                },
                "username": {
                    "type": "string",
                    "description": "Microsoft SSO email. Default: JIRA_SSO_USERNAME from .env"
                },
                "password": {
                    "type": "string",
                    "description": "Microsoft SSO password. Default: JIRA_SSO_PASSWORD from .env"
                },
                "totp_secret": {
                    "type": "string",
                    "description": "TOTP base32 secret for automatic MFA (from Authenticator). Default: JIRA_TOTP_SECRET from .env"
                },
                "headless": {
                    "type": "boolean",
                    "description": "Run Chromium headlessly (default: false). Use true in containers + totp_secret."
                },
                "timeout_sec": {
                    "type": "integer",
                    "description": "Max seconds to wait for login completion (default: 120)"
                },
                "env_file": {
                    "type": "string",
                    "description": "Path to .env file to update (default: .env)"
                },
                "check_existing": {
                    "type": "boolean",
                    "description": "Test existing JIRA_SESSION before re-authenticating. Default: true"
                }
            },
            "required": []
        }
    }


async def run_tool(name: str, params: dict) -> list[types.TextContent]:
    # Check playwright is installed
    try:
        from playwright.async_api import async_playwright  # noqa: F401
    except ImportError:
        return [types.TextContent(type="text", text=(
            "Error: playwright is not installed.\n"
            "Run: pip install playwright && playwright install chromium"
        ))]

    env_file = params.get("env_file", ".env")
    env_path = Path(env_file)
    env_vals = dotenv_values(env_path) if env_path.exists() else {}

    jira_url = (params.get("jira_url") or env_vals.get("JIRA_URL", "")).rstrip("/")
    username = params.get("username") or env_vals.get("JIRA_SSO_USERNAME", "")
    password = params.get("password") or env_vals.get("JIRA_SSO_PASSWORD", "")
    totp_secret = params.get("totp_secret") or env_vals.get("JIRA_TOTP_SECRET", "")
    headless = params.get("headless", False)
    timeout_sec = params.get("timeout_sec", 120)
    check_existing = params.get("check_existing", True)

    if not jira_url:
        return [types.TextContent(type="text", text=(
            "Error: jira_url is required.\n"
            "Either pass it as a parameter or set JIRA_URL in .env"
        ))]

    # Optionally check if the existing session is still valid
    if check_existing:
        existing_session = env_vals.get("JIRA_SESSION", "")
        if existing_session and _is_session_valid(jira_url, existing_session):
            return [types.TextContent(type="text", text=(
                f"✅ Existing JIRA_SESSION is still valid — no re-authentication needed.\n"
                f"Cookie preview: {existing_session[:80]}{'...' if len(existing_session) > 80 else ''}"
            ))]

    if headless and not totp_secret:
        return [types.TextContent(type="text", text=(
            "Warning: headless=true without totp_secret.\n"
            "If MFA is required, the browser will stall and timeout.\n"
            "Either set headless=false (default) to handle MFA manually, "
            "or provide totp_secret for automatic TOTP MFA."
        ))]

    try:
        cookie_string = await _do_sso_login(
            jira_url=jira_url,
            username=username,
            password=password,
            totp_secret=totp_secret,
            headless=headless,
            timeout_sec=timeout_sec,
        )
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error during SSO login: {e}")]

    if not cookie_string:
        return [types.TextContent(type="text", text=(
            "Error: No cookies were extracted from Jira.\n"
            "The login may have failed or timed out. Try headless=false to see what happened."
        ))]

    # Save to .env
    if not env_path.exists():
        env_path.touch()
    set_key(str(env_path), "JIRA_SESSION", cookie_string, quote_mode="never")

    # Verify the new session works
    valid = _is_session_valid(jira_url, cookie_string)
    status = "✅ Session verified — authentication successful!" if valid else "⚠️ Session saved but verification failed — Jira API returned an error. Check credentials."

    preview = cookie_string[:80] + "..." if len(cookie_string) > 80 else cookie_string
    return [types.TextContent(type="text", text=(
        f"{status}\n"
        f"JIRA_SESSION saved to: {env_file}\n"
        f"Cookie preview: {preview}\n\n"
        f"You can now use other Jira tools (lng_jira_worklog_report, etc.) — they will pick up the session automatically."
    ))]


def _is_session_valid(jira_url: str, session_cookie: str) -> bool:
    """Quick check: call Jira /rest/api/2/myself to verify the session is active."""
    try:
        resp = requests.get(
            f"{jira_url}/rest/api/2/myself",
            headers={"Accept": "application/json", "Cookie": session_cookie},
            timeout=10,
        )
        return resp.status_code == 200
    except Exception:
        return False


async def _do_sso_login(
    jira_url: str,
    username: str,
    password: str,
    totp_secret: str,
    headless: bool,
    timeout_sec: int,
) -> str:
    """Drive Playwright through Jira + Microsoft SSO, return all Jira-domain cookies as string."""
    from playwright.async_api import async_playwright

    jira_host = urlparse(jira_url).hostname
    timeout_ms = timeout_sec * 1000

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=headless)
        ctx = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        )
        page = await ctx.new_page()

        # Navigate to Jira
        await page.goto(jira_url, wait_until="domcontentloaded", timeout=timeout_ms)

        # Try to find and click the Microsoft SSO button on Jira's login page
        await _click_sso_button_if_present(page)

        # Handle Microsoft login if we're on their page
        current_url = page.url
        if "login.microsoftonline.com" in current_url or "login.microsoft.com" in current_url:
            await _handle_microsoft_login(page, username, password, totp_secret, headless, timeout_ms)

        # Wait until we're back on Jira domain (handles any redirect chain)
        await page.wait_for_url(f"**{jira_host}**", timeout=timeout_ms)
        await page.wait_for_load_state("networkidle", timeout=30_000)

        # Extract all cookies for the Jira domain
        cookies = await ctx.cookies(jira_url)
        cookie_string = "; ".join(f"{c['name']}={c['value']}" for c in cookies if c.get("value"))

        await browser.close()
        return cookie_string


async def _click_sso_button_if_present(page) -> None:
    """
    Try to click the Microsoft / SSO login button on Jira's login page.
    Jira Data Center can have different selectors depending on auth config.
    """
    # Common selectors for "Log in with Microsoft" / "SSO" button on Jira login pages
    sso_selectors = [
        "a:has-text('Microsoft')",
        "button:has-text('Microsoft')",
        "a:has-text('SSO')",
        "a:has-text('Single Sign-On')",
        "[data-provider='microsoft']",
        ".saml-link",
        "a[href*='saml']",
        "a[href*='microsoft']",
        "a[href*='sso']",
        "#login-with-sso",
        ".login-with-sso",
    ]
    for selector in sso_selectors:
        try:
            el = page.locator(selector).first
            if await el.count() > 0 and await el.is_visible():
                await el.click()
                await page.wait_for_load_state("domcontentloaded", timeout=15_000)
                return
        except Exception:
            continue


async def _handle_microsoft_login(
    page,
    username: str,
    password: str,
    totp_secret: str,
    headless: bool,
    timeout_ms: int,
) -> None:
    """Fill Microsoft SSO login form: email → password → optional TOTP → stay-signed-in."""

    # --- Step 1: Email field ---
    if username:
        try:
            email_input = page.locator("input[type='email'], input[name='loginfmt']").first
            await email_input.wait_for(state="visible", timeout=15_000)
            await email_input.fill(username)
            await _click_next_button(page)
            await page.wait_for_load_state("domcontentloaded", timeout=15_000)
        except Exception as e:
            # Email field may already be pre-filled in some federated setups
            pass

    # --- Step 2: Password field ---
    if password:
        try:
            pwd_input = page.locator("input[type='password'], input[name='passwd']").first
            await pwd_input.wait_for(state="visible", timeout=15_000)
            await pwd_input.fill(password)
            await _click_next_button(page)
            await page.wait_for_load_state("domcontentloaded", timeout=15_000)
        except Exception:
            # Some federated setups redirect to org's own login page — skip
            pass

    # --- Step 3: MFA ---
    if totp_secret:
        await _handle_totp(page, totp_secret)
    elif not headless:
        # Non-headless: MFA prompt visible — just wait for user to complete it
        # (timeout_ms is already set for the outer wait_for_url call)
        pass

    # --- Step 4: "Stay signed in?" prompt ---
    try:
        no_btn = page.locator("#idBtn_Back, input[value='No'], button:has-text('No')").first
        if await no_btn.count() > 0 and await no_btn.is_visible():
            await no_btn.click()
            await page.wait_for_load_state("domcontentloaded", timeout=10_000)
    except Exception:
        pass


async def _handle_totp(page, totp_secret: str) -> None:
    """Fill TOTP code on Microsoft Authenticator / one-time code prompt."""
    try:
        import pyotp
    except ImportError:
        raise RuntimeError(
            "pyotp is required for automatic TOTP MFA.\n"
            "Install: pip install pyotp\n"
            "Or add JIRA_TOTP_SECRET to .env after installing pyotp."
        )

    totp = pyotp.TOTP(totp_secret)
    code = totp.now()

    # Microsoft uses different input names for TOTP
    otp_selectors = [
        "input[name='otc']",
        "input[name='totp']",
        "input[type='tel']",
        "input[aria-label*='code' i]",
        "input[placeholder*='code' i]",
    ]
    for selector in otp_selectors:
        try:
            otp_input = page.locator(selector).first
            if await otp_input.count() > 0 and await otp_input.is_visible():
                await otp_input.fill(code)
                await _click_next_button(page)
                await page.wait_for_load_state("domcontentloaded", timeout=15_000)
                return
        except Exception:
            continue


async def _click_next_button(page) -> None:
    """Click the Next / Sign in submit button on Microsoft login pages."""
    btn_selectors = [
        "input[type='submit']",
        "button[type='submit']",
        "#idSIButton9",
        "button:has-text('Next')",
        "button:has-text('Sign in')",
    ]
    for selector in btn_selectors:
        try:
            btn = page.locator(selector).first
            if await btn.count() > 0 and await btn.is_visible():
                await btn.click()
                return
        except Exception:
            continue
