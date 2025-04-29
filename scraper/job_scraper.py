from playwright.sync_api import sync_playwright
import json
import argparse
import sys
import traceback
import time

class JobScraper:
    def __init__(self, max_jobs=5):
        self.jobs = []
        self.max_jobs = max_jobs

    def scrape_jobbsafari(self, keyword, location):
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                # Build the correct search URL
                url = f"https://jobbsafari.se/lediga-jobb?sok={keyword}&sok={keyword}%2C+{location}"
                print(f"Navigating to: {url}")
                page.goto(url)
                time.sleep(3)  # Let the page load

                # Find job cards (li[data-automation='search-result'])
                job_cards = page.query_selector_all("li.c-iSYTDB")
                print(f"Found {len(job_cards)} job listings")
                if not job_cards or len(job_cards) == 0:
                    # Get the main content area where jobs should be
                    main_content = page.query_selector("main")
                    if main_content:
                        with open("debug_jobbsafari.html", "w", encoding="utf-8") as f:
                            f.write(main_content.inner_html())
                    else:
                        with open("debug_jobbsafari.html", "w", encoding="utf-8") as f:
                            f.write(page.content())
                    print("Saved page HTML to debug_jobbsafari.html")
                job_cards = job_cards[:self.max_jobs]

                for card in job_cards:
                    try:
                        # Get the job URL
                        job_link = card.query_selector("a.c-PJLV")
                        job_url = job_link.get_attribute("href") if job_link else "N/A"
                        if job_url != "N/A":
                            job_url = f"https://jobbsafari.se{job_url}"
                            
                            # Visit the job posting page to get description, upload date, and deadline
                            job_page = browser.new_page()
                            job_page.goto(job_url)
                            time.sleep(2)  # Let the page load
                            
                            # Save the HTML of the first job page for debugging
                            if len(self.jobs) == 0:
                                with open("debug_job_page.html", "w", encoding="utf-8") as f:
                                    f.write(job_page.content())
                                print("Saved job page HTML to debug_job_page.html")
                            
                            # Get the upload date
                            upload_date_elem = job_page.query_selector("div.c-jalXcY.c-jalXcY-jroWjL-align-center.c-jalXcY-cxMxEp-gap-2:nth-child(2) span.c-fbRPId.c-fbRPId-fkodZJ-size-3.c-fbRPId-eqqxgc-weight-bold")
                            if upload_date_elem:
                                upload_date = upload_date_elem.inner_text().strip()
                            else:
                                upload_date = "N/A"
                            
                            # Get the deadline
                            deadline_elem = job_page.query_selector("div.c-jalXcY.c-jalXcY-jroWjL-align-center.c-jalXcY-cxMxEp-gap-2:nth-child(3) span.c-fbRPId.c-fbRPId-fkodZJ-size-3.c-fbRPId-eqqxgc-weight-bold")
                            if deadline_elem:
                                deadline = deadline_elem.inner_text().strip()
                            else:
                                deadline = "N/A"
                            
                            # Get the job description (all text under 'Om jobbet')
                            desc_heading = job_page.query_selector("text=Om jobbet")
                            description = "N/A"
                            if desc_heading:
                                # Try to get the parent and then all text under it
                                parent = desc_heading.evaluate_handle("node => node.parentElement")
                                if parent:
                                    description = parent.inner_text()
                            
                            job_page.close()
                        else:
                            description = "N/A"
                            upload_date = "N/A"
                            deadline = "N/A"

                        title_elem = card.query_selector("h3.c-fbRPId")
                        title = title_elem.inner_text() if title_elem else "N/A"
                        company_elem = card.query_selector("a[href*='/lediga-jobb/foretag/']")
                        company = company_elem.inner_text() if company_elem else "N/A"
                        location_elem = card.query_selector("a[href*='/lediga-jobb/ort/']")
                        location_val = location_elem.inner_text() if location_elem else "N/A"
                        
                        job_data = {
                            "title": title,
                            "company": company,
                            "location": location_val,
                            "url": job_url,
                            "description": description,
                            "upload_date": upload_date,
                            "deadline": deadline,
                            "source": "Jobbsafari",
                        }
                        self.jobs.append(job_data)
                        print(f"Scraped: {title} at {company}")
                    except Exception as e:
                        print(f"Error scraping job: {e}")
                        print(traceback.format_exc())
                browser.close()
        except Exception as e:
            print(f"Error during scraping: {e}")
            print(traceback.format_exc())
            raise

    def save_to_json(self, filename="jobs.json"):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.jobs, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(self.jobs)} jobs to {filename}")

def main():
    parser = argparse.ArgumentParser(description='Scrape job listings from Jobbsafari')
    parser.add_argument('--keyword', type=str, required=True, help='Job keyword to search for')
    parser.add_argument('--location', type=str, required=True, help='Location to search in')
    parser.add_argument('--output', type=str, default='jobs.json', help='Output JSON file name')
    parser.add_argument('--max-jobs', type=int, default=5, help='Maximum number of jobs to scrape')
    args = parser.parse_args()

    print(f"Starting job scrape for keyword: {args.keyword} and location: {args.location}")
    scraper = JobScraper(max_jobs=args.max_jobs)
    scraper.scrape_jobbsafari(args.keyword, args.location)
    scraper.save_to_json(args.output)

if __name__ == "__main__":
    sys.exit(main()) 