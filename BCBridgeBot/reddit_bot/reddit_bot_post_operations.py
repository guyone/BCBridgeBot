import re
from collections import Counter

def get_image_url_from_inline_media(content):
    image_urls = re.findall(r'(https?://[^\s]*\.(?:jpg|jpeg|gif|png)[^\s]*)', content)
    return image_urls[0] if image_urls else ""

def count_user_comments_by_subreddit(reddit, username):
    user = reddit.redditor(username)
    subreddit_counter = Counter()
    
    for comment in user.comments.new(limit=50):
        subreddit_counter[comment.subreddit.display_name] += 1

    return subreddit_counter