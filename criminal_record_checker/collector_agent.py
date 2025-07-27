import interpol_scraping
import cbi_scraping
import fbi_scraping
from rich import print
from concurrent.futures import ThreadPoolExecutor

def collector_agent():
    fore_name = input("Enter Fore Name (First Name): ").strip()
    family_name = input("Enter Family Name (Last Name): ").strip()
    full_name = f"{fore_name} {family_name}"

    print("[bold green]Checking for the name in three sites FBI/INTERPOL/CBI:[/bold green]")

    
    def check_site(site_name, scraper_func, *args):
        print(f"[bold green]Checking in {site_name}...[/bold green]")
        result = scraper_func(*args)
        if result:  
            print(f"[bold green] FOUND in {site_name}![/bold green]")
            print(result)
        

    with ThreadPoolExecutor(max_workers=3) as executor:
       
        executor.submit(check_site, "FBI", fbi_scraping.fetch_fugitives, full_name)
        executor.submit(check_site, "INTERPOL", interpol_scraping.fetch_interpol, fore_name, family_name)
        executor.submit(check_site, "CBI", cbi_scraping.fetch_cbi_interpol, full_name)

    print("[bold yellow] Finished checking!![/bold yellow]")


collector_agent()
