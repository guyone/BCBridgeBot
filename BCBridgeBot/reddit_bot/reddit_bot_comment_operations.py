import openai, os, time, random, requests, certifi
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne
from urllib.parse import quote_plus
from praw.models import Comment, Submission, Redditor
from prawcore.exceptions import TooManyRequests, NotFound
from pytz import timezone
from threading import Lock

from utils.calculate import Calculator
from utils.find_redditor_meta import RedditMetadata
from utils.banned_subs import banned_subreddits
from reddit_bot.reddit_bot_post_operations import count_user_comments_by_subreddit
from utils.image_text import SignEditor
from ai.ai_prompts import ComedyGenerator
from reddit_bot.reddit_bot_replies import create_incident_reply, create_stats_comment
# Load environment variables
load_dotenv()

# Setting up the instance of the comedy AI
comedy_generator = ComedyGenerator()

# Setting up instance of the sign editor
sign_editor = SignEditor()

reddit_metadata = RedditMetadata()
calculator = Calculator()

# OpenAI API setup
openai.api_key = os.getenv('OPENAI_API_KEY')

IMGUR_CLIENT_ID = os.getenv('IMGUR_CLIENT_ID')
IMGUR_SECRET = os.getenv('IMGUR_SECRET')

imgur_headers = {"Authorization": f"Client-ID {IMGUR_CLIENT_ID}"}

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
bridge_incidents_col = db[os.getenv('MONGODB_COLLECTION_1')]
processed_comments_col = db[os.getenv('MONGODB_COLLECTION_2')]
users_col = db[os.getenv('MONGODB_COLLECTION_3')]

MAX_COMMENT_LENGTH = 200  # set the maximum length of each comment
MAX_COMMENTS = 50  # set the maximum number of comments to consider

users_to_update_lock = Lock()

# timestamp setup
utc_now = datetime.utcnow()
pst = timezone('America/Los_Angeles')
pst_now = utc_now.astimezone(pst)
CURRENT_YEAR = datetime.now().year

# Reddit Rate limits
COMMENT_CHECK_SLEEP_TIME = 5
COMMENT_CHECK_RATE_RESET_SLEEP_TIME = 60

# Initialize an empty list to hold users to be queued for the db
users_to_update = []
ignored_users = ["AutoModerator", "BCBridgeBot"]

response_engine = os.getenv('OPENAI_RESPONSE_ENGINE')

def generate_url(obj):
    if isinstance(obj, Submission):
        return f"https://www.reddit.com/r/{obj.subreddit.display_name}/comments/{obj.id}/{obj.title.replace(' ', '_')}/"
    elif isinstance(obj, Comment):
        return f"https://www.reddit.com/r/{obj.subreddit.display_name}/comments/{obj.submission.id}/{obj.submission.title.replace(' ', '_')}/{obj.id}/"
    else:
        return None

# writes the entry for users into the database
def write_user_to_mongodb(author, comment):
    global users_to_update
    try:
        if author is None:
            print("Author is None. Skipping...")
            return
        
        timestamp = datetime.utcnow().strftime('%Y-%m-%d')
        
        active, provider, address = reddit_metadata.fetch_crypto_contact(author)

        entry = {
            'last_updated': timestamp,
            'user': author.name,
            'user_id': author.id,
            'has_verified_email': author.has_verified_email,
            'creation_date': author.created_utc,
            'active': active,
            'provider': provider,
            'address': address
        }
        
        # Update the MongoDB entry for this user
        full_url = generate_url(comment)
        comment_object = {
            'full_url': full_url,
            'text': comment.body,
            'subreddit': comment.subreddit.display_name,
            'timestamp': comment.created_utc
        }
        
        # Update the MongoDB entry for this user
        # Instead of updating MongoDB here, append to users_to_update
        update_operation = UpdateOne(
        {'user_id': author.id}, 
        {'$set': entry, '$push': {'comments': comment_object}}, 
        upsert=True
        )
        with users_to_update_lock:
            users_to_update.append(update_operation)
            print(f'Collected {len(users_to_update)} of 10 comments.')

        # If we've collected enough users, perform a bulk write
        if len(users_to_update) >= 10:
            users_col.bulk_write(users_to_update)
            users_to_update = []
            print('Collected 10 entries and updated users')
    except NotFound:
        print(f"Reddit user {author} not found. Skipping...")
        return False

# writes the entry into the database
def write_to_mongodb(collection, id, url, author_name, author_id, bot_reply=None):
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

# makes sure the username isn't [deleted]
def handle_author(obj):
    return (obj.author.name, obj.author.id) if obj.author is not None else ("Deleted User", "N/A")

# write the bridge post to the database to keep track of them
def write_bridge_post(submission, bot_reply=None):
    author_name, author_id = handle_author(submission)
    post_url = generate_url(submission)
    write_to_mongodb(bridge_incidents_col, submission.id, post_url, author_name, author_id, bot_reply)

# writes a comment from a user to the database. This is usually a !command
def write_processed_comment(comment, bot_reply=None):
    author_name, author_id = handle_author(comment)
    comment_url = generate_url(comment)
    write_to_mongodb(processed_comments_col, comment.id, comment_url, author_name, author_id, bot_reply)

# recevies the bridge posts from the DB
def load_bridge_posts():
    return [doc for doc in bridge_incidents_col.find({})]

def find_latest_timestamp(bridge_posts):
    if bridge_posts:
        latest_post = bridge_posts[-1]
        latest_timestamp = latest_post.get('timestamp', 'No timestamp')
        return latest_timestamp
    return 'No posts found'

def make_mod_comment(submission):
    bridge_posts = load_bridge_posts()
    bridge_post_ids = {post['id'] for post in bridge_posts}

    latest_timestamp_str = find_latest_timestamp(bridge_posts)
    latest_timestamp = datetime.strptime(latest_timestamp_str, '%Y-%m-%d')
    submission_timestamp = datetime.utcfromtimestamp(submission.created_utc)

    # Calculate the difference in days
    days_since_last_incident = (submission_timestamp - latest_timestamp).days

    if submission.id in bridge_post_ids:
        return

    prompt = f"Channel your inner Canadian comedian {comedy_generator.select_comedian()} and take a line from {comedy_generator.select_joke_type()} but change it to reference the number {days_since_last_incident}."
    response = openai.Completion.create(engine="text-davinci-003", prompt=prompt, max_tokens=50)

    comment_text = response.choices[0].text.strip()
    query = {"timestamp": {"$regex": f"^{CURRENT_YEAR}"}}

    # Get the count of matching entries using count_documents()
    count_in_2023 = bridge_incidents_col.count_documents(query)
    total_incidents = bridge_incidents_col.count_documents({})

    sign_editor.add_text_to_image('images/incident_sign.jpg', days_since_last_incident)

    with open("images/modified_image.jpg", "rb") as img:
        response = requests.post(
            "https://api.imgur.com/3/image",
            headers=imgur_headers,
            data={
                'image': img.read(),
                'type': 'file',
            }
        )

    # Extract the link from the response
    imgur_link = response.json()["data"]["link"]
    
    full_comment = submission.reply(create_incident_reply(imgur_link, days_since_last_incident, count_in_2023, total_incidents))
    if full_comment:
        comment_text = {'style': comedy_generator.select_joke_type(), 'comment': comment_text}
        write_bridge_post(submission, bot_reply=comment_text)
        full_comment.mod.distinguish(how='yes', sticky=True)
        print("Sticky comment made on new post.")
    else:
        print("Failed to post comment.")

# this watches for new comments in a subreddit and does the commands
def listen_for_subreddit_commands(reddit, bot_username):
    subreddit = reddit.subreddit(os.getenv("REDDIT_SUBREDDIT"))
    for comment in subreddit.stream.comments(skip_existing=True):
        if comment.author and comment.author.name in ignored_users:
            continue
        print(f"NEW COMMENT FOUND: by u/{comment.author.name}.")
        result = write_user_to_mongodb(comment.author, comment)
        if result == False:
            continue
        # Count subreddits the user has commented in (last 50 comments)
        subreddit_counter = count_user_comments_by_subreddit(reddit, comment.author.name)

        # check_user(subreddit_counter, comment, reddit, subreddit)

        if comment.body.strip() == "!bridge":
            prompt = "Generate a random 'welcome or hello' quote from a popular comedy movie."
            response = openai.Completion.create(
                engine="text-davinci-003", 
                prompt=prompt, 
                max_tokens=50
            )
            quote_text = response.choices[0].text.strip()
            full_comment = (f"{quote_text}  \n"
                            f"  \n"
                            f"Try one of my commands: !info, !bridgestats, !bridgefact"
            )
            # Reply to the comment
            comment.reply(full_comment)
            print(f'NEW COMMENT: {comment.body} found by {comment.author} and processed.')

def listen_for_stats_command(reddit, bot_username):
    last_interaction_by_user = {}
    bot_start_timestamp = pst_now.strftime("%H:%M %p, %d-%m-%Y")
    
    last_processed_comment_time = datetime.utcnow()  # Initialize this to the current time when the bot starts
    
    while True:
        try:
            existing_ids = {doc['id'] for doc in processed_comments_col.find({}, {'_id': 0, 'id': 1})}

            for comment in reddit.inbox.comment_replies(limit=5):
                comment_time = datetime.utcfromtimestamp(comment.created_utc)
                
                if comment_time <= last_processed_comment_time:
                    continue
                
                # Only update last_processed_comment_time if comment_time is greater
                if comment_time > last_processed_comment_time:
                    last_processed_comment_time = comment_time

                parent_author = comment.parent().author.name if comment.parent().author else 'Deleted User'

                if comment.id in existing_ids:
                    continue
                
                # last_interaction_time = last_interaction_by_user.get(parent_author, None)
                # if last_interaction_time and (comment_time - last_interaction_time).total_seconds() < 3600:
                #     continue
                
                last_interaction_by_user[parent_author] = comment_time

                if comment.body.strip() == "!info" and parent_author == bot_username:
                    info_comment = (f"BridgeBot is a AI bot built to keep track of the ongoing issue of trucks hitting overpasses and bridges in British Columbia.  \n"
                                    f"  \n"
                                    f"This bot was created by u/GuyOne and has been running since {bot_start_timestamp}.  \n"
                                    f"  \n"
                                    f"Commands: !bridge, !info, !bridgestats, !bridgefact, !bcfact")
                    
                    comment.reply(info_comment)
                    write_processed_comment(comment, bot_reply=info_comment)
                    print(f'COMMENT: {comment.body} by {comment.author}.')
                    
                if comment.body.strip() == "!bridgestats" and parent_author == bot_username:
                    print(f"Recognized !bridgestats command in comment {comment.id}.")
                    
                    total, longest, shortest, last_date = calculator.calculate_stats()

                    stats_comment = create_stats_comment(last_date, total, longest, shortest)
                    
                    comment.reply(stats_comment)
                    write_processed_comment(comment, bot_reply=stats_comment)
                    
                    # Since the comment is new and processed, add it to existing_ids
                    existing_ids.add(comment.id)

                if comment.body.strip() == "!bridgefact" and parent_author == bot_username:
                    selected_prompt = random.choice(comedy_generator.bridge_fact_prompts)
                    print(f"Recognized !bridgefact command in comment {comment.id}.")
                    
                    response = openai.Completion.create(engine=response_engine, prompt=selected_prompt, max_tokens=100)
                    fact_text = response.choices[0].text.strip().split('\n')[0]

                    comment.reply(fact_text)
                    write_processed_comment(comment, bot_reply=fact_text)
                    
                    existing_ids.add(comment.id)
                
                if comment.body.strip() == "!bcfact" and parent_author == bot_username:
                    selected_prompt = random.choice(comedy_generator.bc_related_prompts)
                    print(f"Recognized !bcfact command in comment {comment.id}.")
                    
                    response = openai.Completion.create(engine=response_engine, prompt=selected_prompt, max_tokens=100)
                    fact_text = response.choices[0].text.strip().split('\n')[0]

                    comment.reply(fact_text)
                    write_processed_comment(comment, bot_reply=fact_text)
                    
                    existing_ids.add(comment.id)

            time.sleep(COMMENT_CHECK_SLEEP_TIME)
        except TooManyRequests:
            print("Hit rate limit. Sleeping for a bit...")
            time.sleep(COMMENT_CHECK_RATE_RESET_SLEEP_TIME)

def check_user(subreddit_counter, comment, reddit, subreddit):
    for banned_sub in banned_subreddits:
        if subreddit_counter.get(banned_sub, 0) >= 3:
            print(f"User {comment.author.name} has commented more than 3 times in '{banned_sub}', checking for malicious activity.")
            reddit_user = Redditor(reddit, name=comment.author.name)
            last_50_comments = list(reddit_user.comments.new(limit=MAX_COMMENTS))
            comment_list = [comment.body[:MAX_COMMENT_LENGTH] for comment in last_50_comments]
            prompt = f"This redditor {reddit_user} posts in a subreddit that is known to be far-right or extreme. Look at these {MAX_COMMENTS} comments of theirs and determine if there is a possibility that they could be commenting in bad faith, arguing, being rude or trolling in anyway. Simply respond 'yes' or 'no'. {comment_list}"
            response = openai.Completion.create(engine="text-davinci-003", prompt=prompt, max_tokens=50)
            comment_text = response.choices[0].text.strip()
            print(comment_text)
            print(f'Results from analyzing comment by {comment.author.name}: {comment_text}')
            comment_text_lower = comment_text.lower()

            if 'yes' in comment_text_lower:
                # Ban the user from the current subreddit
                try:
                    subreddit.banned.add(
                        comment.author.name,
                        ban_reason=f"Banned for being active in 'r/{banned_sub}'",
                        note=f"Participating in r/{banned_sub}",
                        message="You have been banned for being active in subreddits that allow/promote misinformation and hate.\n\nThis was an automated process and could be in error. If you would like to appeal this ban, reply here and a human mod will help you."
                    )
                    # Remove the comment
                    comment.mod.remove()
                    print(f"Successfully banned {comment.author.name} and removed their comment.")
                except Exception as e:
                    print(f"Failed to ban {comment.author.name} or remove their comment. Error: {e}")
                break  # Exit the loop as the user is already banned
            elif 'no' in comment_text_lower:
                print(f'It was determined not to ban the user {comment.author.name}')