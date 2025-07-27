from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
from rich import print


def stealthify(page):
    """Apply stealth measures to evade bot detection"""
    stealth_sync(page)
    page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        window.navigator.chrome = { runtime: {} };
        Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
    """)


def safe_inner_text(page, selector, default="N/A"):
    """Safely get inner text from selector, return default if missing"""
    try:
        el = page.query_selector(selector)
        return el.inner_text().strip() if el else default
    except:
        return default


def fetch_cbi_notices(query: str, base_url: str, notice_type: str, context):
    """Fetch data from given CBI notice type URL"""
    page = context.new_page()
    stealthify(page)

    print(f"[bold purple]Checking {notice_type} Notices in CBI…[/bold purple]")

    try:
        page.goto(base_url, wait_until="domcontentloaded", timeout=30000)
    except Exception:
        print(f"[bold red]Failed to load {notice_type} Notice page. Skipping.[/bold red]")
        page.close()
        return

    try:
        page.wait_for_selector("#searchterm", timeout=15000)
    except:
        print(f"[bold red]Search box not found on {notice_type} page. Layout may have changed.[/bold red]")
        page.close()
        return

    if not query.strip():
        print("[bold red]Empty search query provided. Exiting.[/bold red]")
        page.close()
        return

    page.fill("#searchterm", query.strip())
    page.keyboard.press("Enter")
    print(f"[bold purple]Searching {notice_type} for: {query}…[/bold purple]")

    page.wait_for_timeout(3000)

    try:
        page.wait_for_selector("table#clipsid tbody tr", timeout=10000)
    except:
        print(f"[bold red]No results found for {notice_type} Notices in CBI!!.[/bold red]")
        page.close()
        return

    rows = page.query_selector_all("table#clipsid tbody tr")
    if not rows:
        print(f"[bold red]No results found in {notice_type} Notices table in CBI!!.[/bold red]")
        page.close()
        return

    found_any = False

    for idx, row in enumerate(rows, start=1):
        try:
            name_el = row.query_selector("td:nth-child(2) a")
            if not name_el:
                continue

            found_any = True  

            name = safe_inner_text(row, "td:nth-child(2) a")
            link = name_el.get_attribute("href")

            print(f"\n[bold purple]{name}[/bold purple] ({notice_type} Notice)")
            print(f"Profile Link: [blue]{link}[/blue]")

            # Open detail page
            detail_page = context.new_page()
            stealthify(detail_page)
            try:
                detail_page.goto(link, wait_until="domcontentloaded", timeout=30000)
            except:
                print("[bold red]Failed to load detail page. Skipping.[/bold red]")
                detail_page.close()
                continue

            try:
                detail_page.wait_for_selector("div.wantedsingle__colright", timeout=15000)
            except:
                print("[bold red]Detail page failed to load properly.[/bold red]")
                detail_page.close()
                continue

            if notice_type == "Red":
                
                charges = safe_inner_text(detail_page, "#charge", default="No charges listed.")
                print(f"[bold purple]Charges:[/bold purple] {charges}")

            

            detail_page.close()

        except Exception as e:
            print(f"[bold red]Error processing row {idx} in {notice_type} Notices: {e}[/bold red]")

    if not found_any:
        print(f"[bold red]No results found for {notice_type} Notices in CBI!!.[/bold red]")

    page.close()


def fetch_cbi_interpol(query: str):
    RED_NOTICE_URL = "https://cbi.gov.in/interpol-red-notice"
    YELLOW_NOTICE_URL = "https://cbi.gov.in/interpol-yellow-notice"

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="en-US",
            color_scheme="light",
            timezone_id="Asia/Kolkata",
            java_script_enabled=True
        )

        
        fetch_cbi_notices(query, RED_NOTICE_URL, "Red", context)
        fetch_cbi_notices(query, YELLOW_NOTICE_URL, "Yellow", context)

        browser.close()


if __name__ == "__main__":
    name_query = input("Enter name to search: ").strip()
    fetch_cbi_interpol(name_query)
