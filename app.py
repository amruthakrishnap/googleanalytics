from flask import Flask, render_template, request, jsonify
from playwright.sync_api import sync_playwright
from supabase import create_client, Client
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

# Supabase configuration
url = 'https://vjgxtqqrbehmoqsgorvq.supabase.co'
key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZqZ3h0cXFyYmVobW9xc2dvcnZxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjI4NTI5ODcsImV4cCI6MjAzODQyODk4N30.Qlhws14rMtrM7frgxLKgM6flg3I1JvJ-JPd5gd6A3-Q'
supabase: Client = create_client(url, key)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    link = request.form.get('link')

    if not link:
        return jsonify({'status': 'error', 'message': 'No link provided'})

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(link)

            while True:
                try:
                    load_more_button = page.query_selector('button:has-text("Load more")')
                    if load_more_button:
                        load_more_button.click()
                        page.wait_for_timeout(2000)
                    else:
                        break
                except Exception as e:
                    break

            html = page.content()
            soup = BeautifulSoup(html, 'html.parser')

            names = [item.get_text(strip=True) for item in soup.find_all(class_='LfYwpe')]
            dates = [item.get_text(strip=True) for item in soup.find_all(class_='ydlbEf')]
            ratings = [item.get('aria-label', '').strip() for item in soup.find_all(class_='B1UG8d')]
            reviews = [item.get_text(strip=True) for item in soup.find_all(class_='fzDEpf')]
            helpfuls = [item.get_text(strip=True) for item in soup.find_all(class_='ZRk0Tb')]

            extension_name_elements = soup.find_all(class_='Pa2dE')
            extension_url_elements = soup.find_all('a', class_='KgGEHd')
            developer_elements = soup.find_all(class_='cJI8ee')
            overall_rating_elements = soup.find_all(class_=['GlMWqe', 'SxpA2e'])
            total_rating_elements = soup.find_all(class_='PloaX')
            extension_type_elements = soup.find_all(class_=['gqpEIe', 'bgp7Ye'])
            developer_details_elements = soup.find_all('a', class_='cJI8ee')
            total_users_elements = soup.find_all(class_='F9iKBc')

            extension_name = extension_name_elements[0].get_text(strip=True) if extension_name_elements else 'No name found'
            extension_url = 'https://chromewebstore.google.com/' + extension_url_elements[0].get('href', '').strip().lstrip('.') if extension_url_elements else 'No URL found'
            developer = developer_elements[0].get_text(strip=True) if developer_elements else 'No developer found'
            overall_rating = overall_rating_elements[0].get_text(strip=True) if overall_rating_elements else 'No rating found'
            total_rating = total_rating_elements[0].get_text(strip=True) if total_rating_elements else 'No total rating found'
            total_users_text = total_users_elements[0].get_text(strip=True) if total_users_elements else 'No total users found'
            total_users_match = re.search(r'(\d+,\d+|\d+)', total_users_text)
            total_users = total_users_match.group(0) if total_users_match else 'No total users found'
            extension_type = extension_type_elements[-1].get_text(strip=True) if extension_type_elements else 'No type found'
            developer_details = 'https://chromewebstore.google.com/' + developer_details_elements[0].get('href', '').strip().lstrip('.') if developer_details_elements else 'No developer details found'

            length = min(len(names), len(dates), len(ratings), len(reviews), len(helpfuls))

            names = names[:length]
            dates = dates[:length]
            ratings = ratings[:length]
            reviews = reviews[:length]
            helpfuls = helpfuls[:length]

            data = [
                {
                    'name': names[i],
                    'date': dates[i],
                    'rating': ratings[i],
                    'review': reviews[i],
                    'helpful': helpfuls[i],
                    'extension_name': extension_name,
                    'extension_url': extension_url,
                    'developer': developer,
                    'overall_rating': overall_rating,
                    'total_rating': total_rating,
                    'extension_type': extension_type,
                    'developer_details': developer_details,
                    'total_users': total_users
                }
                for i in range(length)
            ]

            response = supabase.table('scraped_data').insert(data).execute()

            browser.close()

            return jsonify({'status': 'success', 'message': 'Data has been successfully scraped and stored in Supabase.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
