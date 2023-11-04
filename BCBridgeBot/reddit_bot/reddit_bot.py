import time, os, certifi
from reddit_bot.reddit_bot_post_operations import get_image_url_from_inline_media
from reddit_bot.reddit_bot_comment_operations import make_mod_comment
from pymongo import MongoClient
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB setup
MONGODB_USERNAME = quote_plus(os.getenv('MONGODB_USERNAME'))
MONGODB_PASSWORD = quote_plus(os.getenv('MONGODB_PASSWORD'))
client = MongoClient(
    f"mongodb+srv://{MONGODB_USERNAME}:{MONGODB_PASSWORD}"
    f"@{os.getenv('MONGODB_NAME')}"
    f".{os.getenv('MONGODB_CLUSTER')}"
    f".mongodb.net/test?retryWrites=true&w=majority",
    ssl=True,
    tlsCAFile=certifi.where()
)
db = client[os.getenv('MONGODB_DB_NAME')]
db_bridge_incidents = db[os.getenv('MONGODB_COLLECTION_1')]

SLEEP_TIME = 5 #3600 for 1h

# Function to check existing submissions in MongoDB
def check_existing_submission_in_db(submission_id):
    existing_entry = db_bridge_incidents.find_one({"id": submission_id})
    return bool(existing_entry)

def get_post_details(submission):
    post_type = ''
    post_content = ''
    if submission.is_self:
        post_type = 'text'
        post_content = submission.selftext
        if "&#x200B;" in post_content:
            post_type = 'image'
            post_content = get_image_url_from_inline_media(post_content)
    elif any(ext in submission.url for ext in ['.jpg', '.png', '.gif']):
        post_type = 'image'
        post_content = submission.url
        if hasattr(submission, 'preview'):
            post_content = submission.preview['images'][0]['source']['url']
    else:
        post_type = 'link'
        post_content = submission.url
    return post_type, post_content

def run_bot(reddit, subreddit):
    print(f'Now watching {subreddit} for new posts')
    while True:
        for submission in reddit.subreddit(subreddit).new(limit=5):
            
            if submission.link_flair_text == "Truck Hits Overpass":
                
                # Check MongoDB for existing submission ID
                if check_existing_submission_in_db(submission.id):
                    continue
                print(f'POST: Truck Hits Overpass post has been made. {submission.id} Processing...')
                
                make_mod_comment(submission)

        time.sleep(SLEEP_TIME)
        print('rechecking...')