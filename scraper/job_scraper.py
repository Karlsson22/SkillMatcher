from playwright.sync_api import sync_playwright
import json
import os
from datetime import datetime

class JobScraper:
    def __init__(self):
        self.jobs = []

    def scrape_indeed(self, keyword, location):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Navigate to Indeed
            url = f"https://www.indeed.com/jobs?q={keyword}&l={location}"
            page.goto(url)
            
            # Wait for job listings to load
            page.wait_for_selector(".job_seen_beacon")
            
            # Extract job data
            job_cards = page.query_selector_all(".job_seen_beacon")
            
            for card in job_cards:
                try:
                    title = card.query_selector(".jobTitle").inner_text()
                    company = card.query_selector(".companyName").inner_text()
                    location = card.query_selector(".companyLocation").inner_text()
                    
                    job_data = {
                        "title": title,
                        "company": company,
                        "location": location,
                        "source": "Indeed",
                        "scraped_at": datetime.now().isoformat()
                    }
                    
                    self.jobs.append(job_data)
                except Exception as e:
                    print(f"Error scraping job: {e}")
            
            browser.close()
    
    def save_to_json(self, filename="jobs.json"):
        with open(filename, "w") as f:
            json.dump(self.jobs, f, indent=2)

if __name__ == "__main__":
    scraper = JobScraper()
    scraper.scrape_indeed("software engineer", "remote")
    scraper.save_to_json() 