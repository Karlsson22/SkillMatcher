from playwright.sync_api import sync_playwright
import json
import argparse
import sys
import traceback
import time
import re
import requests
from xml.etree import ElementTree
from datetime import datetime, timedelta
from urllib.parse import urljoin

class JobScraper:
    def __init__(self, max_jobs=5, days_back=None):
        self.jobs = []
        self.max_jobs = max_jobs
        self.days_back = days_back
        self.job_dates = {}  # Store dates from sitemap

    def is_within_date_range(self, date_str):
        """Check if the job posting date is within the specified range"""
        if self.days_back is None:
            return True
            
        try:
            job_date = datetime.strptime(date_str, '%Y-%m-%d')
            cutoff_date = datetime.now() - timedelta(days=self.days_back)
            return job_date >= cutoff_date
        except (ValueError, TypeError):
            return True  # If we can't parse the date, include the job

    def get_dates_from_sitemap(self):
        """Get job posting dates from the sitemap"""
        try:
            response = requests.get('https://demando.io/sitemap/jobs-sitemap.xml')
            if response.status_code == 200:
                root = ElementTree.fromstring(response.content)
                # Define the XML namespace
                ns = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
                # Get all URL elements
                for url in root.findall('.//ns:url', ns):
                    loc = url.find('ns:loc', ns).text
                    lastmod = url.find('ns:lastmod', ns)
                    if lastmod is not None:
                        # Convert date to a more readable format
                        date = datetime.fromisoformat(lastmod.text.replace('Z', '+00:00'))
                        formatted_date = date.strftime('%Y-%m-%d')
                        self.job_dates[loc] = formatted_date
        except Exception as e:
            print(f"Error fetching sitemap: {e}")

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

                # Find job cards
                job_cards = page.query_selector_all("li.c-iSYTDB")
                print(f"Found {len(job_cards)} job listings")
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
                            
                            # Get the upload date
                            upload_date_elem = job_page.query_selector("div.c-jalXcY.c-jalXcY-jroWjL-align-center.c-jalXcY-cxMxEp-gap-2:nth-child(2) span.c-fbRPId.c-fbRPId-fkodZJ-size-3.c-fbRPId-eqqxgc-weight-bold")
                            if upload_date_elem:
                                upload_date = upload_date_elem.inner_text().strip()
                                # Skip if not within date range
                                if not self.is_within_date_range(upload_date):
                                    job_page.close()
                                    continue
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
                                # Try to get the next sibling element after the heading
                                next_sibling = desc_heading.evaluate_handle("node => node.nextElementSibling")
                                if next_sibling:
                                    sibling_text = next_sibling.inner_text().strip()
                                    if sibling_text and len(sibling_text) > 20:
                                        description = sibling_text
                                # If not, try to get the parent and all text under it
                                if description == "N/A" or len(description) < 20:
                                    parent = desc_heading.evaluate_handle("node => node.parentElement")
                                    if parent:
                                        full_text = parent.inner_text()
                                        # Remove the heading itself if present
                                        if full_text.startswith("Om jobbet"):
                                            full_text = full_text[len("Om jobbet"):].strip()
                                        if full_text and len(full_text) > 20:
                                            description = full_text
                                # Fallback: try to get a main content section
                                if (description == "N/A" or len(description) < 20):
                                    main_content = job_page.query_selector("main")
                                    if main_content:
                                        main_text = main_content.inner_text().strip()
                                        if main_text and len(main_text) > 20:
                                            description = main_text
                                # Final fallback: just get the text after the heading
                                if description == "N/A" or len(description) < 20:
                                    description = desc_heading.inner_text().strip()
                                # Clean up any HTML tags if present
                                description = re.sub(r'<[^>]+>', '', description).strip()
                            
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

    def scrape_demando(self, keyword, location):
        try:
            # First get dates from sitemap
            print("Fetching dates from sitemap...")
            self.get_dates_from_sitemap()
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                url = f"https://demando.io/jobs?q={keyword}&location={location}"
                print(f"Navigating to: {url}")
                page.goto(url)
                time.sleep(3)  # Let the page load
                
                # Find job cards
                job_cards = page.query_selector_all("a.flex.w-96")
                print(f"Found {len(job_cards)} job listings")
                
                if not job_cards or len(job_cards) == 0:
                    job_cards = page.query_selector_all("a[class*='flex'][href*='/company/']")
                    print(f"Found {len(job_cards)} job listings with alternative selector")
                
                job_cards = job_cards[:self.max_jobs]

                for card in job_cards:
                    try:
                        job_url = card.get_attribute("href")
                        if job_url:
                            if not job_url.startswith("http"):
                                job_url = f"https://demando.io{job_url}"
                            
                            # Visit the job posting page
                            job_page = browser.new_page()
                            job_page.goto(job_url)
                            time.sleep(3)  # Give more time to load
                            
                            print(f"Fetching description for: {job_url}")
                            
                            description = "N/A"
                            upload_date = "N/A"
                            skills = []
                            
                            try:
                                # Try to get skills first
                                skills_containers = card.query_selector_all("div.flex")
                                for container in skills_containers:
                                    text = container.inner_text().strip()
                                    # Skills are usually shown as single words or short phrases
                                    if len(text.split('\n')) > 1:  # Multiple items
                                        skills = [s.strip() for s in text.split('\n')]
                                        if any(s for s in skills if s in ["Go", "Java", "C#", "Javascript", "+"]): # Found skills section
                                            break
                                
                                # Check if the keyword is in the skills
                                keyword_lower = keyword.lower()
                                skills_lower = [s.lower() for s in skills]
                                if keyword_lower not in skills_lower:
                                    print(f"Skipping job - {keyword} not found in skills: {skills}")
                                    return None
                                
                                # Get the job description from the main content
                                selectors = [
                                    "main div[class*='prose']",
                                    "main div[class*='content']",
                                    "main div[class*='description']",
                                    "div[class*='job-description']",
                                    "main"
                                ]
                                
                                for selector in selectors:
                                    description_elem = job_page.query_selector(selector)
                                    if description_elem:
                                        description = description_elem.inner_text().strip()
                                        if description and len(description) > 20:
                                            print(f"Found description using selector: {selector}")
                                            break
                                
                                if description == "N/A":
                                    print("Could not find description with any selector")
                                
                                # Try to get date from the page
                                date_selectors = [
                                    'meta[property="article:published_time"]',
                                    'meta[name="date"]',
                                    'time[datetime]',
                                    'div[class*="date"]',
                                    'span[class*="date"]'
                                ]
                                
                                for selector in date_selectors:
                                    date_elem = job_page.query_selector(selector)
                                    if date_elem:
                                        # Try different attributes
                                        for attr in ['content', 'datetime', 'title']:
                                            date_str = date_elem.get_attribute(attr)
                                            if date_str:
                                                try:
                                                    date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                                                    upload_date = date.strftime('%Y-%m-%d')
                                                    print(f"Found date using selector: {selector}")
                                                    break
                                                except ValueError:
                                                    continue
                                        if upload_date != "N/A":
                                            break
                                
                            except Exception as e:
                                print(f"Error getting page content: {e}")
                            finally:
                                job_page.close()
                            
                            # If we didn't find the required keyword in skills, skip this job
                            if keyword_lower not in skills_lower:
                                continue
                        
                        # Get title
                        title_elem = card.query_selector("h3")
                        title = title_elem.inner_text() if title_elem else "N/A"
                        
                        # Get company name
                        company = "N/A"
                        if job_url:
                            company_match = re.search(r'/company/([^/]+)/', job_url)
                            if company_match:
                                company = company_match.group(1).replace('-', ' ').title()
                        
                        # Get location - look for text next to location icon or in a flex container
                        location_val = "N/A"
                        try:
                            # Try to get just the location part
                            location_containers = card.query_selector_all("div.flex")
                            for container in location_containers:
                                text = container.inner_text().strip()
                                if any(city in text for city in ["Stockholm", "Göteborg", "Malmö"]):
                                    # Try to get just the city name
                                    lines = text.split('\n')
                                    for line in lines:
                                        if any(city in line for city in ["Stockholm", "Göteborg", "Malmö"]):
                                            location_val = line.strip()
                                            break
                                    break
                        except Exception as e:
                            print(f"Error getting location: {e}")
                        
                        # Get upload date from sitemap
                        upload_date = self.job_dates.get(job_url, "N/A")
                        if upload_date == "N/A":
                            # Try to get date from URL structure or page metadata
                            try:
                                meta_date = job_page.query_selector('meta[property="article:published_time"]')
                                if meta_date:
                                    date_str = meta_date.get_attribute('content')
                                    if date_str:
                                        date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                                        upload_date = date.strftime('%Y-%m-%d')
                            except Exception as e:
                                print(f"Error getting date from metadata: {e}")
                        
                        job_data = {
                            "title": title,
                            "company": company,
                            "location": location_val,
                            "url": job_url,
                            "description": description,
                            "upload_date": upload_date,
                            "deadline": "N/A",  # Demando doesn't show deadlines
                            "source": "Demando",
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

    def scrape_utvecklarjobb(self, keyword, location):
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                # Go to main page first
                base_url = "https://ledigajobb.se"
                search_url = f"{base_url}/sok?s={keyword}&cs={location}"
                print(f"Navigating to: {search_url}")
                
                page.goto(search_url)
                time.sleep(3)  # Let the page load
                
                # Find all job listings using the correct selector
                job_cards = page.query_selector_all("div.job-card")
                print(f"Found {len(job_cards)} job listings")
                
                # Process each job listing
                for i, card in enumerate(job_cards[:self.max_jobs]):
                    try:
                        # Get the job link and URL
                        job_link = card.query_selector("a.job-link")
                        if not job_link:
                            continue
                            
                        title = job_link.inner_text().strip()
                        job_url = job_link.get_attribute("href")
                        if not job_url.startswith("http"):
                            job_url = base_url + job_url
                            
                        print(f"\nProcessing job: {title}")
                        
                        # Get company name
                        company_elem = card.query_selector("span.text-truncate-1")
                        company = company_elem.inner_text().strip() if company_elem else "N/A"
                        
                        # Get location
                        location_elem = card.query_selector("a[href*='/lediga-jobb/']")
                        location_val = location_elem.inner_text().strip() if location_elem else location
                        
                        # Visit the job page to get more details
                        job_page = browser.new_page()
                        job_page.goto(job_url)
                        time.sleep(2)
                        
                        # Get description from the job page
                        description = "N/A"
                        desc_elem = job_page.query_selector("script[type='application/ld+json']")
                        if desc_elem:
                            try:
                                json_data = json.loads(desc_elem.inner_text())
                                description = json_data.get("description", "N/A")
                            except:
                                pass
                        
                        # Get upload date and deadline from the job page
                        upload_date = "N/A"
                        deadline = "N/A"
                        
                        # Try to get date from JSON-LD
                        if desc_elem:
                            try:
                                json_data = json.loads(desc_elem.inner_text())
                                if "datePosted" in json_data:
                                    date = datetime.fromisoformat(json_data["datePosted"].replace('Z', '+00:00'))
                                    upload_date = date.strftime('%Y-%m-%d')
                                if "validThrough" in json_data:
                                    date = datetime.fromisoformat(json_data["validThrough"].replace('Z', '+00:00'))
                                    deadline = date.strftime('%Y-%m-%d')
                            except:
                                pass
                        
                        # If we couldn't get dates from JSON-LD, try to get them from the page
                        if upload_date == "N/A":
                            date_elem = job_page.query_selector("span.text-nowrap.text-gray-700")
                            if date_elem:
                                date_text = date_elem.inner_text().strip()
                                if "dagar kvar" in date_text:
                                    days_left = int(date_text.split()[0])
                                    deadline = (datetime.now() + timedelta(days=days_left)).strftime('%Y-%m-%d')
                        
                        job_data = {
                            "title": title,
                            "company": company,
                            "location": location_val,
                            "url": job_url,
                            "description": description,
                            "upload_date": upload_date,
                            "deadline": deadline,
                            "source": "Ledigajobb"
                        }
                        
                        self.jobs.append(job_data)
                        print(f"Added job {len(self.jobs)}/{self.max_jobs}: {title} at {company}")
                        
                        job_page.close()
                        
                    except Exception as e:
                        print(f"Error processing job listing: {e}")
                        print(traceback.format_exc())
                        continue
                
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
    parser = argparse.ArgumentParser(description='Scrape job listings from multiple sources')
    parser.add_argument('--keyword', type=str, required=True, help='Job keyword to search for')
    parser.add_argument('--location', type=str, required=True, help='Location to search in')
    parser.add_argument('--output', type=str, default='jobs.json', help='Output JSON file name')
    parser.add_argument('--max-jobs', type=int, default=3, help='Maximum number of jobs to scrape (default: 3)')
    parser.add_argument('--days-back', type=int, help='Only include jobs posted within this many days')
    parser.add_argument('--source', type=str, choices=['jobbsafari', 'demando', 'utvecklarjobb', 'all'], 
                      default='all', help='Which source to scrape from')
    args = parser.parse_args()

    print(f"Starting job scrape for keyword: {args.keyword} and location: {args.location}")
    scraper = JobScraper(max_jobs=args.max_jobs, days_back=args.days_back)
    
    if args.source in ['jobbsafari', 'all']:
        print("Scraping Jobbsafari...")
        scraper.scrape_jobbsafari(args.keyword, args.location)
    
    if args.source in ['demando', 'all']:
        print("Scraping Demando...")
        scraper.scrape_demando(args.keyword, args.location)
        
    if args.source in ['utvecklarjobb', 'all']:
        print("Scraping UtvecklarJobb...")
        scraper.scrape_utvecklarjobb(args.keyword, args.location)
    
    scraper.save_to_json(args.output)

if __name__ == "__main__":
    sys.exit(main()) 