import requests
import bs4
import re
import json
from urllib.parse import urljoin
import pandas as pd

SITE_URL = r'https://outerjoin.us'
JOBS_URL = urljoin(SITE_URL, 'remote-data-science-jobs')
# also, 'https://outerjoin.us/remote-data-science-jobs?page=2' etc.

# get list of job links
def scrape_jobs_list(url):
    r = requests.get(JOBS_URL)
    if r.status_code != 200:
        raise Exception(f'Error retrieving job list from {JOBS_URL}')
    soup = bs4.BeautifulSoup(r.content, "html.parser")
    return soup

def parse_jobs_list(soup):
    ''' 
    Returns a list of url suffixes for job detail pages
    '''
    jobs = soup.find_all("a", class_="job-title")
    return [job.get('href') for job in jobs if 'data scientist' in job.get_text().lower()]

def scrape_job_detail(link):
    job_detail_url = urljoin(SITE_URL, link)
    r = requests.get(job_detail_url)
    soup = bs4.BeautifulSoup(r.content, "html.parser")
    return soup

def parse_job_detail(soup):
    ''' 
    Returns a list of dicts with keys:
    * company
    * position
    * date_posted
    * list_title
    * list_item
    '''

    # get company and position
    t = soup.title.string
    m = re.match(r'([A-Za-z\s]+):\s([A-Za-z\s]+)\s\| Outer Join', t)
    company, position = m.groups()

    # get date posted
    s = soup.find('script', string=re.compile("identifier"))
    json_data = json.loads(s.get_text(), strict=False)
    date_posted = json_data['datePosted']

    # get list titles and bullet text (will this work in general?)
    description = soup.find('div', class_='job-description')
    bullets = []
    for ul in description.find_all('ul'):
        list_title = ul.find_previous_sibling().get_text()
        for li in ul.find_all('li'):
            bullets.append((list_title, li.text))

    # gather into dataframe
    n = len(bullets)
    d = [{ 
        'company': company, 
        'position': position,
        'date_posted': date_posted,
        'list_title': title,
        'list_item': item
        } for title, item in bullets]

    return d

soup = scrape_jobs_list(JOBS_URL)
job_links = parse_jobs_list(soup)

data = []
for link in job_links:
    soup = scrape_job_detail(link)
    job_data = parse_job_detail(soup)
    job_data['job_url'] = [urljoin(SITE_URL, link)] * len(job_data)
    df_list.append(job_data)

data = pd.concat(df_list)

# append source ('Outer Join') column to data


    



