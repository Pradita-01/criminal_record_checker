from playwright.sync_api import sync_playwright, Playwright, Browser, Page
from playwright_stealth import stealth_sync
from urllib.parse import urljoin
from rich import print

def setup_browser(playwright: Playwright) -> Browser:
    """Launch browser in stealth mode."""
    browser = playwright.chromium.launch(
        headless=True,
        args=['--no-sandbox', '--disable-blink-features=AutomationControlled']
    )
    return browser

def setup_context(browser: Browser):
    """Setup browser context with custom options."""
    context = browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        locale='en-US',
        timezone_id='Europe/London',
        java_script_enabled=True
    )
    page = context.new_page()
    stealth_sync(page)

    # Extra stealth evasion
    page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        window.navigator.chrome = { runtime: {} };
        Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
    """)
    return page

def fetch_interpol(fore_name: str, family_name: str, playwright: Playwright = None):
    """Fetch interpol data for given name."""
    close_playwright = False

    if playwright is None:
        playwright = sync_playwright().start()
        close_playwright = True

    browser = setup_browser(playwright)
    page = setup_context(browser)

    base_url = 'https://www.interpol.int'
    start_url = f'{base_url}/en/How-we-work/Notices/Red-Notices/View-Red-Notices'

    print("[bold yellow]Navigating to Interpol...[/bold yellow]")
    try:
        page.goto(start_url, wait_until="domcontentloaded", timeout=30000)

        page.mouse.move(200, 200)
        page.keyboard.press("ArrowDown")
        page.wait_for_selector('input[name="name"]', timeout=15000)

        # Fill and submit search form
        page.fill('input[name="name"]', family_name)
        page.fill('input[name="forename"]', fore_name)
        page.click('button[type="submit"]')

        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)

        links = page.query_selector_all('.redNoticeItem__labelLink')

        if not links:
            print("[bold red]No results found in Interpol.[/bold red]")
            return

        results = []
        for link in links:
            name_text = link.inner_text().replace('\n', ' ').strip()
            full_url = link.get_attribute('data-singleurl')
            if full_url and family_name.lower() in name_text.lower() and fore_name.lower() in name_text.lower():
                safe_url = urljoin(base_url, full_url)
                notice_number = safe_url.split("/")[-1]
                results.append((name_text, notice_number, safe_url))

        if not results:
            print("[bold red]No matching results for the given name in interpol.[/bold red]")
            return

        # Pick the first match
        selected_name, notice_number, selected_url = results[0]
        print(f"\n[bold yellow]Found:[/bold yellow] [bold yellow]{selected_name} in interpol!![/bold yellow]")
        print(f"[bold yellow]Notice Number:[/bold yellow] {notice_number}")
        print(f"[bold yellow]Profile URL:[/bold yellow] {selected_url}")

        page.goto(selected_url, wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(2000)

        # Extract charges
        try:
            json_data = page.evaluate('() => JSON.parse(document.body.innerText)')
            arrest_warrants = json_data.get('arrest_warrants', [])
            charges = arrest_warrants[0].get('charge', 'N/A') if arrest_warrants else 'N/A'
        except Exception:
            charges = "N/A"

        print(f"[bold yellow]Charges:[/bold yellow] {charges}")

    except Exception as e:
        print(f"[bold red]Error during Interpol fetch:[/bold red] {e}")

    finally:
        browser.close()
        if close_playwright:
            playwright.stop()


if __name__ == "__main__":
    with sync_playwright() as pw:
        fore_name = input("Please enter the fore name: ").strip()
        family_name = input("Please enter the family name: ").strip()
        fetch_interpol(fore_name, family_name, pw)
