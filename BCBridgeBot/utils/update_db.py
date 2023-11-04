from pymongo import MongoClient
from urllib.parse import quote_plus
from datetime import datetime
import os, time
from reddit_bot.reddit_bot_connection import init_reddit
import certifi

# You can import your `init_reddit` function from your existing file, if it's in a different file

class MongoDBUpdater:
    def __init__(self):
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
        self.SLEEP_TIME = 60

    def write_to_mongodb(self, collection, id, url, author_name, author_id, bot_reply=None):
        entry = {
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d'),
            'url': url,
            'user': author_name,
            'user_id': author_id,
            'id': id,
        }
        if bot_reply:
            entry['bot_reply'] = bot_reply
        collection.insert_one(entry)

    def search_and_store_posts_with_flair(self, subreddit_name):
        print("Initializing Reddit...")
        reddit = init_reddit()
        if not reddit:
            print("Failed to initialize Reddit.")
            return

        print(f"Accessing subreddit: {subreddit_name}")
        subreddit = reddit.subreddit(subreddit_name)

        # Create an empty set to store processed post IDs
        processed_posts = set()
        print("Entering infinite loop...")

        while True:  # This will make the function run indefinitely
            print("Fetching new posts...")
            for submission in subreddit.new(limit=10):  # Limit reduced for more frequent checks
                print(f"Checking post with ID: {submission.id}")
                
                if submission.id in processed_posts:
                    print(f"Already processed post with ID: {submission.id}")
                    continue  # Skip already processed posts

                if submission.link_flair_text == "Truck Hits Overpass":
                    print(f"Found post with ID: {submission.id}, Title: {submission.title}")
                    print(f"Found post with ID: {submission.id}, Title: {submission.title}")

                    # If the author is deleted, use "Deleted User" and "N/A" for username and id
                    author_name = submission.author.name if submission.author else "Deleted User"
                    author_id = submission.author.id if submission.author else "N/A"
                    
                    post_url = f"https://www.reddit.com/r/{submission.subreddit.display_name}/comments/{submission.id}/{submission.title.replace(' ', '_')}/"
                    
                    self.write_to_mongodb(self.db_bridge_incidents, submission.id, post_url, author_name, author_id)
                    print(f"Stored post with ID: {submission.id} into MongoDB.")

                    # Add this post ID to the processed_posts set
                    processed_posts.add(submission.id)
                    
                    # Wait for a minute before processing the next post
                    time.sleep(self.SLEEP_TIME)

    # Run the function
    search_and_store_posts_with_flair('BritishColumbia')  # Replace 'your_subreddit' with the actual subreddit name