#!/home/codespace/.python/current/bin/python3 scrape-names.py

import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin

url = "https://www.dssg.pt/projetos/"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

response = requests.get(url, headers=headers)

all_u_texts = []

if response.status_code == 200:
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all 'a' tags
    links = soup.find_all('a')

    # Extract href attributes that contain 'projetos/' or 'projects/'
    hrefs = set()
    for link in links:
        href = link.get('href')
        if href and ('projetos/' in href or 'projects/' in href):
            hrefs.add(href)

    # Loop through each href and scrape <u> tags
    for href in hrefs:
        # Extract project name from href (handle both 'projetos/' and 'projects/')
        if 'projetos/' in href:
            project_name = href.split('projetos/')[-1].strip('/')
        else:
            project_name = href.split('projects/')[-1].strip('/')
        print(f"Scraping: {href} - Project: {project_name}")
        try:
            page_response = requests.get(href, headers=headers)
            if page_response.status_code == 200:
                page_soup = BeautifulSoup(page_response.content, 'html.parser')
                
                # Count <p> tags containing "maker"
                p_tags = page_soup.find_all('p')
                maker_count = sum(1 for p in p_tags if 'maker' in p.get_text().lower())
                
                # Get all <u> tags and take the last 'maker_count' ones
                u_tags = page_soup.find_all('u')
                selected_u_tags = u_tags[-maker_count:] if maker_count > 0 else []
                
                print(f"Found {maker_count} 'maker' paragraphs, selecting last {len(selected_u_tags)} <u> tags")
                
                for u in selected_u_tags:
                    text = u.get_text().strip()
                    if text:
                        parent_a = u.find_parent('a', href=True)
                        contact_href = ''
                        if parent_a:
                            contact_href = urljoin(href, parent_a['href'])
                        all_u_texts.append({
                            'Name': text,
                            'Project': project_name,
                            'Contact': contact_href
                        })
                        print(text)
            else:
                print(f"Failed to retrieve {href}. Status code: {page_response.status_code}")
        except Exception as e:
            print(f"Error scraping {href}: {e}")
else:
    print(f"Failed to retrieve the webpage. Status code: {response.status_code}")

# Create pandas dataframe
if all_u_texts:
    df = pd.DataFrame(all_u_texts)
    print("\nDataframe created (before grouping):")
    print(df.head())
    
    # Group by Name and collapse projects and contacts into comma-separated strings
    df_grouped = df.groupby('Name').agg({
        'Project': lambda x: ', '.join(x),
        'Contact': lambda x: ', '.join(sorted(set(y for y in x if y)))
    }).reset_index()
    
    print("\nDataframe after grouping (unique names with projects and contacts):")
    print(df_grouped.head())
    
    # Save to CSV
    df_grouped.to_csv('scraped_names.csv', index=False)
    print("\nDataframe saved to 'scraped_names.csv'")