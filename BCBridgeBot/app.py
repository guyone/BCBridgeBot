import threading, os
from dotenv import load_dotenv
from reddit_bot.reddit_bot import run_bot
from reddit_bot.reddit_bot_comment_operations import listen_for_stats_command, listen_for_subreddit_commands
from reddit_bot.reddit_bot_connection import init_reddit

load_dotenv()

# Initialize Reddit API
reddit = init_reddit()

# Start Reddit bot in a thread
threading.Thread(target=run_bot, args=(reddit, os.getenv('REDDIT_SUBREDDIT'))).start()

# listening for comments in the subreddit
threading.Thread(target=listen_for_subreddit_commands, args=(reddit, os.getenv('REDDIT_USERNAME'))).start()

# Start another thread to listen for stats command
threading.Thread(target=listen_for_stats_command, args=(reddit, os.getenv('REDDIT_USERNAME'))).start()