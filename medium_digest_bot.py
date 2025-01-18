import imaplib
import email
from email.header import decode_header
import requests
from bs4 import BeautifulSoup


from dotenv import load_dotenv
import os

load_dotenv()
EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_PASS = os.getenv('EMAIL_PASS')
EMAIL_SERVER = os.getenv('EMAIL_SERVER')
SENDER_EMAIL = os.getenv('SENDER_EMAIL')

TELEGRAM_BOT_API = os.getenv('TELEGRAM_BOT_API')
TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')

def connect_to_email():
    mail = imaplib.IMAP4_SSL(EMAIL_SERVER)
    mail.login(EMAIL_USER, EMAIL_PASS)
    mail.select('inbox')  
    return mail

def get_most_recent_medium_email(mail):
    status, messages = mail.search(None, f'(FROM "{SENDER_EMAIL}")')
    if status != 'OK':
        print("No messages found!")
        return None
    email_ids = messages[0].split()
    if email_ids:
        return email_ids[-1] 
    return None


def extract_medium_links(email_data):
    links = []
    for part in email_data.walk():
        if part.get_content_type() == 'text/html': 
            html_content = part.get_payload(decode=True).decode()
            soup = BeautifulSoup(html_content, 'html.parser')
            a_tags = soup.find_all('a', href=True)
            for tag in a_tags:
                link = tag['href']
                if 'medium.com' in link and len(links) < 10: 
                    links.append(link)
    return links
def format_medium_links(medium_links):
    formatted_links = []
    for link in medium_links:
        freedium_link = f"https://freedium.cfd/{link}"
        formatted_links.append(freedium_link)
    return formatted_links
def send_to_telegram(message):
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_API}/sendMessage'
    params = {
        'chat_id': TELEGRAM_CHANNEL_ID,
        'text': message
    }
    response = requests.get(url, params=params)
    return response.json()


def send_medium_links_to_telegram():
    mail = connect_to_email()
    email_id = get_most_recent_medium_email(mail)

    if not email_id:
        print("No email found from Medium.")
        return

    status, email_data = mail.fetch(email_id, '(RFC822)')
    if status != 'OK':
        print("Failed to retrieve email.")
        return

    raw_email = email.message_from_bytes(email_data[0][1])
    medium_links = extract_medium_links(raw_email)

    if not medium_links:
        print("No Medium links found in the email.")
        return
    formatted_links = format_medium_links(medium_links)
    for link in formatted_links:
        send_message = send_to_telegram(f"Check out this article: {link}")
        if send_message.get('ok'):
            print(f"Message sent to Telegram: {link}")
        else:
            print(f"Failed to send the message: {link}")
def send_test_message():
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_API}/sendMessage'
    params = {
        'chat_id': TELEGRAM_CHANNEL_ID, 
        'text': 'This is a test message'
    }
    response = requests.get(url, params=params)
    print(response.json()) 

def get_chat_id():
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_API}/getUpdates'
    response = requests.get(url)
    updates = response.json()
    print(updates)  


def main():
    print("Sending test message...")
    send_test_message()
    print("Fetching and sending Medium links to Telegram...")
    send_medium_links_to_telegram()

if __name__ == '__main__':
    main()
