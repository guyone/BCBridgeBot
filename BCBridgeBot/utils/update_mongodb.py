import os, requests, praw, certifi
from pymongo import MongoClient
from urllib.parse import quote_plus
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class MongoDBUpdater:
    def __init__(self):
        self.reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent=os.getenv("REDDIT_USER_AGENT")
        )
        self.MONGODB_USERNAME = quote_plus(os.getenv('MONGODB_USERNAME'))
        self.MONGODB_PASSWORD = quote_plus(os.getenv('MONGODB_PASSWORD'))
        self.client = MongoClient(
            f"mongodb+srv://{self.MONGODB_USERNAME}:{self.MONGODB_PASSWORD}"
            f"@{os.getenv('MONGODB_NAME')}"
            f".{os.getenv('MONGODB_CLUSTER')}"
            f".mongodb.net/test?retryWrites=true&w=majority",
            ssl=True,
            tlsCAFile=certifi.where()
        )
        self.db = self.client[os.getenv('MONGODB_DB_NAME')]
        self.db_bridge_incidents = self.db[os.getenv('MONGODB_COLLECTION_1')]
        self.db_crypto_contacts = self.db[os.getenv('MONGODB_COLLECTION_3')]

    def write_to_mongodb_bridge(self, collection, id, url, author_name, author_id, location):
        entry = {
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d'),
            'url': url,
            'user': author_name,
            'user_id': author_id,
            'id': id,
            'location': location,
        }
        collection.insert_one(entry)

    def write_to_mongodb_user(self, collection, author_id, author_name, address, creation_date, comment_karma, link_karma, has_verified_email):
        entry = {
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d'),
            'author_id': author_id,
            'author_name': author_name,
            'address': address,
            'creation_date': creation_date,
            'comment_karma': comment_karma,
            'link_karma': link_karma,
            'has_verified_email': has_verified_email
        }
        collection.insert_one(entry)

updater = MongoDBUpdater()

# Fetching data from the Reddit Meta API
username = input("Enter the username to fetch information: ")
url = f"{updater.REDDIT_API}{username}"
response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    print(f"Full JSON response: {data}")  # Debug print

    # Fetch Reddit user details using praw
    redditor = updater.reddit.redditor(username)
    creation_date = datetime.utcfromtimestamp(redditor.created_utc).strftime('%Y-%m-%d')
    comment_karma = redditor.comment_karma
    link_karma = redditor.link_karma
    has_verified_email = redditor.has_verified_email

    contacts = data.get('contacts', {})
    user_data_list = contacts.get(f't2_{redditor.id}', [])  # Changed this line

    print(f"user_data_list: {user_data_list}")  # Debug print

    if user_data_list:
        user_data = user_data_list[0]
        author_id = user_data.get('userId')
        author_name = user_data.get('username')
        address = user_data.get('address')

        print(f"author_id: {author_id}, author_name: {author_name}, address: {address}")  # Debug print

        updater.write_to_mongodb_user(updater.db_crypto_contacts, author_id, author_name, address, creation_date, comment_karma, link_karma, has_verified_email)
        print(f"Stored {author_name} into MongoDB.")
    else:
        print(f"No crypto contact information found for user {username}.")
else:
    print("Failed to get data from Reddit Meta API")

while True:
    print("Enter information for a post with the flair 'Truck Hits Overpass'")
    timestamp = input("Enter the timestamp (YYYY-MM-DD): ")
    post_id = input("Enter the post ID: ")
    post_title = input("Enter the post title: ")
    post_url = input("Enter the post URL: ")
    author_name = input("Enter the author's username: ")
    author_id = input("Enter the author's ID: ")
    location = input("Enter the location: ")

    entry = {
        'timestamp': timestamp,
        'title': post_title,
        'url': post_url,
        'user': author_name,
        'user_id': author_id,
        'id': post_id,
        'location': location  # Added location to the entry
    }

    updater.db_bridge_incidents.insert_one(entry)

    print(f"Stored post ID {post_id} with title '{post_title}' and location '{location}' into MongoDB.")  # Updated message to include location

    another_entry = input("Do you want to add another entry? (y/n): ")
    if another_entry.lower() != 'y':
        break