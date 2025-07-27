

from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
from rich import print

def fetch_fugitives(name_input):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        stealth_sync(page)

        base_url = "https://www.fbi.gov"
        wanted_url = f"{base_url}/wanted/fugitives"

        print("[bold cyan]Accessing FBI Wanted Fugitives...[/bold cyan]")
        page.goto(wanted_url, wait_until="domcontentloaded")

        try:
            page.wait_for_selector("li.portal-type-person", timeout=15000)
        except:
            print("[bold red]Failed to load fugitive data.[/bold red]")
            return

        cards = page.query_selector_all("li.portal-type-person")
        results = []

        for card in cards:
            try:
                name_el = card.query_selector("p.name a")
                category_el = card.query_selector("h3.title a")
                link = name_el.get_attribute("href")
                name = name_el.inner_text().strip()
                category = category_el.inner_text().strip()

                if name_input.lower() in name.lower(): 
                    results.append((name, category, link))
            except:
                continue

        
        if results:
            print(f"[bold cyan]Found '{name_input}' in FBI!!:[/bold cyan]")
            for name, category, link in results:
                print(f"\n[bold cyan] {name}[/bold cyan]")
                print(f"Category: [green]{category}[/green]")
                print(f"Poster Link: [blue]{link}[/blue]")
        else:
            print(f"[bold red]No matches found in FBI!!.[/bold red]")

        context.close()
        browser.close()



if __name__ == "__main__":
    full_name = input("Enter full name to search: ").strip()
    fetch_fugitives(full_name)
