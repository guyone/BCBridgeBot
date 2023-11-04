from datetime import datetime, timedelta
from dotenv import load_dotenv
from pymongo import MongoClient
from urllib.parse import quote_plus
import os
import certifi

load_dotenv()

class Calculator:
    MAX_STREAK = timedelta(days=36500)  # 100 years

    def __init__(self):
        # MongoDB setup
        self.MONGODB_USERNAME = quote_plus(os.getenv('MONGODB_USERNAME', 'default_username'))
        self.MONGODB_PASSWORD = quote_plus(os.getenv('MONGODB_PASSWORD', 'default_password'))
        self.client = MongoClient(
            f"mongodb+srv://{self.MONGODB_USERNAME}:{self.MONGODB_PASSWORD}"
            f"@{os.getenv('MONGODB_NAME', 'default_name')}"
            f".{os.getenv('MONGODB_CLUSTER', 'default_cluster')}"
            f".mongodb.net/test?retryWrites=true&w=majority",
            ssl=True,
            tlsCAFile=certifi.where()
        )
        self.db = self.client[os.getenv('MONGODB_DB_NAME', 'default_db_name')]
        self.bridge_incidents_col = self.db[os.getenv('MONGODB_COLLECTION_1', 'default_collection_1')]
        self.processed_comments_col = self.db[os.getenv('MONGODB_COLLECTION_2', 'default_collection_2')]

    def calculate_stats(self):
        """Calculates statistical data based on bridge incidents."""
        try:
            bridge_posts = list(self.bridge_incidents_col.find().sort('timestamp', 1))
            total_num_of_incidents = len(bridge_posts)

            if total_num_of_incidents == 0:
                return 0, 0, 0, "No data available"

            longest_streak = timedelta(days=0)
            shortest_streak = self.MAX_STREAK
            prev_timestamp = datetime.strptime(bridge_posts[0]['timestamp'], '%Y-%m-%d')

            for post in bridge_posts[1:]:
                curr_timestamp = datetime.strptime(post['timestamp'], '%Y-%m-%d')
                delta = curr_timestamp - prev_timestamp

                longest_streak = max(longest_streak, delta)
                shortest_streak = min(shortest_streak, delta)

                prev_timestamp = curr_timestamp

            last_incident_date = bridge_posts[-1]['timestamp']
            return total_num_of_incidents, longest_streak.days, shortest_streak.days, last_incident_date

        except Exception as e:
            # Handle specific exceptions you expect (KeyError, ValueError, etc.)
            print(f"An error occurred: {e}")
            # Depending on your error policy, you may want to re-raise the exception or return a default value
            return 0, 0, 0, "Error in data"