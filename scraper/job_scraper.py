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
        self.job_dates = {}
        self.jobs_scraped = 0
        self.sources = ['jobbsafari', 'demando', 'utvecklarjobb']
        jobs_per_source = max_jobs // 3
        remainder = max_jobs % 3
        self.jobs_per_source = {
            'jobbsafari': jobs_per_source,
            'demando': jobs_per_source,
            'utvecklarjobb': jobs_per_source + remainder
        }

    def can_scrape_more(self):
        return self.jobs_scraped < self.max_jobs

    def add_job(self, job_data):
        if self.can_scrape_more():
            self.jobs.append(job_data)
            self.jobs_scraped += 1
            return True
        return False

    def is_within_date_range(self, date_str):
        if self.days_back is None:
            return True
            
        try:
            job_date = datetime.strptime(date_str, '%Y-%m-%d')
            cutoff_date = datetime.now() - timedelta(days=self.days_back)
            return job_date >= cutoff_date
        except (ValueError, TypeError):
            return True

    def get_dates_from_sitemap(self):
        try:
            response = requests.get('https://demando.io/sitemap/jobs-sitemap.xml')
            if response.status_code == 200:
                root = ElementTree.fromstring(response.content)
                ns = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
                for url in root.findall('.//ns:url', ns):
                    loc = url.find('ns:loc', ns).text
                    lastmod = url.find('ns:lastmod', ns)
                    if lastmod is not None:
                        date = datetime.fromisoformat(lastmod.text.replace('Z', '+00:00'))
                        formatted_date = date.strftime('%Y-%m-%d')
                        self.job_dates[loc] = formatted_date
        except Exception as e:
            print(f"Error fetching sitemap: {e}")

    def clean_description(self, text):
        if not text or text == "N/A":
            return "N/A"
            
        text = re.sub(r'<[^>]+>', '', text)
        
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        text = re.sub(r' +', ' ', text)
        
        text = re.sub(r'\n\s+', '\n', text)
        text = re.sub(r'\s+\n', '\n', text)
        
        text = text.strip()
        
        if len(text) < 20:
            return "N/A"
            
        return text

    def scrape_jobbsafari(self, keyword, location):
        try:
            if not self.can_scrape_more():
                print("Reached maximum number of jobs, skipping Jobbsafari")
                return

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                url = f"https://jobbsafari.se/lediga-jobb?sok={keyword}&sok={keyword}%2C+{location}"
                print(f"Navigating to: {url}")
                page.goto(url)
                time.sleep(3)

                job_cards = page.query_selector_all("li.c-iSYTDB")
                print(f"Found {len(job_cards)} job listings")
                job_cards = job_cards[:self.jobs_per_source['jobbsafari']]

                for card in job_cards:
                    if not self.can_scrape_more():
                        break
                    try:
                        job_link = card.query_selector("a.c-PJLV")
                        job_url = job_link.get_attribute("href") if job_link else "N/A"
                        if job_url != "N/A":
                            job_url = f"https://jobbsafari.se{job_url}"
                            
                            job_page = browser.new_page()
                            job_page.goto(job_url)
                            time.sleep(2)
                            
                            desc_elem = job_page.query_selector("script[type='application/ld+json']")
                            description = "N/A"
                            if desc_elem:
                                try:
                                    data = json.loads(desc_elem.inner_text())
                                    description_html = data.get("description", "")
                                    description = re.sub(r'<br ?/?>', '\n', description_html)
                                    description = re.sub(r'<[^>]+>', '', description)
                                    description = description.strip()
                                except Exception as e:
                                    description = "N/A"
                            if not description or description == "N/A" or len(description) < 20:
                                main_content = job_page.query_selector("main")
                                if main_content:
                                    description = main_content.inner_text().strip()
                                else:
                                    description = "N/A"
                            
                            upload_date_elem = job_page.query_selector("div.c-jalXcY.c-jalXcY-jroWjL-align-center.c-jalXcY-cxMxEp-gap-2:nth-child(2) span.c-fbRPId.c-fbRPId-fkodZJ-size-3.c-fbRPId-eqqxgc-weight-bold")
                            if upload_date_elem:
                                upload_date = upload_date_elem.inner_text().strip()
                                if not self.is_within_date_range(upload_date):
                                    job_page.close()
                                    continue
                            else:
                                upload_date = "N/A"
                            
                            deadline_elem = job_page.query_selector("div.c-jalXcY.c-jalXcY-jroWjL-align-center.c-jalXcY-cxMxEp-gap-2:nth-child(3) span.c-fbRPId.c-fbRPId-fkodZJ-size-3.c-fbRPId-eqqxgc-weight-bold")
                            if deadline_elem:
                                deadline = deadline_elem.inner_text().strip()
                            else:
                                deadline = "N/A"
                            
                            description = self.clean_description(description)
                            
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
                        if not self.add_job(job_data):
                            break
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
            if not self.can_scrape_more():
                print("Reached maximum number of jobs, skipping Demando")
                return

            print("Fetching dates from sitemap...")
            self.get_dates_from_sitemap()
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                url = f"https://demando.io/jobs?q={keyword}&location={location}"
                print(f"Navigating to: {url}")
                page.goto(url)
                time.sleep(3)
                
                job_cards = page.query_selector_all("a.flex.w-96")
                print(f"Found {len(job_cards)} job listings")
                
                if not job_cards or len(job_cards) == 0:
                    job_cards = page.query_selector_all("a[class*='flex'][href*='/company/']")
                    print(f"Found {len(job_cards)} job listings with alternative selector")
                
                job_cards = job_cards[:self.jobs_per_source['demando']]

                for card in job_cards:
                    if not self.can_scrape_more():
                        break
                    try:
                        job_url = card.get_attribute("href")
                        if job_url:
                            if not job_url.startswith("http"):
                                job_url = f"https://demando.io{job_url}"
                            
                            job_page = browser.new_page()
                            job_page.goto(job_url)
                            time.sleep(3)
                            
                            print(f"Fetching description for: {job_url}")
                            
                            description = "N/A"
                            upload_date = "N/A"
                            skills = []
                            
                            try:
                                skills_containers = card.query_selector_all("div.flex")
                                for container in skills_containers:
                                    text = container.inner_text().strip()
                                    if len(text.split('\n')) > 1:
                                        skills = [s.strip() for s in text.split('\n')]
                                        if any(s for s in skills if s in ["Go", "Java", "C#", "Javascript", "+"]): # Found skills section
                                            break
                                
                                keyword_lower = keyword.lower()
                                skills_lower = [s.lower() for s in skills]
                                if keyword_lower not in skills_lower:
                                    print(f"Skipping job - {keyword} not found in skills: {skills}")
                                    return None
                                
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
                                        raw_description = description_elem.inner_text().strip()
                                        description = self.clean_description(raw_description)
                                        if description != "N/A":
                                            print(f"Found description using selector: {selector}")
                                            break
                                
                                if description == "N/A":
                                    print("Could not find description with any selector")
                                
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
                            
                            if keyword_lower not in skills_lower:
                                continue
                        
                        title_elem = card.query_selector("h3")
                        title = title_elem.inner_text() if title_elem else "N/A"
                        
                        company = "N/A"
                        if job_url:
                            company_match = re.search(r'/company/([^/]+)/', job_url)
                            if company_match:
                                company = company_match.group(1).replace('-', ' ').title()
                        
                        location_val = "N/A"
                        try:
                            location_containers = card.query_selector_all("div.flex")
                            for container in location_containers:
                                text = container.inner_text().strip()
                                if any(city in text for city in ["Stockholm", "Göteborg", "Malmö"]):
                                    lines = text.split('\n')
                                    for line in lines:
                                        if any(city in line for city in ["Stockholm", "Göteborg", "Malmö"]):
                                            location_val = line.strip()
                                            break
                                    break
                        except Exception as e:
                            print(f"Error getting location: {e}")
                        
                        upload_date = self.job_dates.get(job_url, "N/A")
                        if upload_date == "N/A":
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
                            "deadline": "N/A",
                            "source": "Demando",
                        }
                        if not self.add_job(job_data):
                            break
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
            if not self.can_scrape_more():
                print("Reached maximum number of jobs, skipping UtvecklarJobb")
                return

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                base_url = "https://ledigajobb.se"
                search_url = f"{base_url}/sok?s={keyword}&cs={location}"
                print(f"Navigating to: {search_url}")
                page.goto(search_url)
                time.sleep(3)
                job_cards = page.query_selector_all("div.job-card")
                print(f"Found {len(job_cards)} job listings")
                job_cards = job_cards[:self.jobs_per_source['utvecklarjobb']]

                for card in job_cards:
                    if not self.can_scrape_more():
                        break
                    try:
                        job_link = card.query_selector("a.job-link")
                        if not job_link:
                            continue
                            
                        title = job_link.inner_text().strip()
                        job_url = job_link.get_attribute("href")
                        if not job_url.startswith("http"):
                            job_url = base_url + job_url
                            
                        print(f"\nProcessing job: {title}")
                        
                        company_elem = card.query_selector("span.text-truncate-1")
                        company = company_elem.inner_text().strip() if company_elem else "N/A"
                        
                        location_elem = card.query_selector("a[href*='/lediga-jobb/']")
                        location_val = location_elem.inner_text().strip() if location_elem else location
                        
                        job_page = browser.new_page()
                        job_page.goto(job_url)
                        time.sleep(2)
                        
                        description = "N/A"
                        desc_elem = job_page.query_selector("script[type='application/ld+json']")
                        if desc_elem:
                            try:
                                json_data = json.loads(desc_elem.inner_text())
                                description = json_data.get("description", "N/A")
                            except:
                                pass
                        
                        upload_date = "N/A"
                        deadline = "N/A"
                        
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
                        if not self.add_job(job_data):
                            break
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