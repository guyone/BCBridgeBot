import requests, os
from dotenv import load_dotenv

load_dotenv()

class RedditMetadata:
    def __init__(self,active=None, provider=None, address=None):
        self.REDDIT_API = os.getenv('REDDIT_API')
        self.active = active
        self.provider = provider
        self.address = address

    def fetch_crypto_contact(self, author):
        if not hasattr(author, 'name') or not hasattr(author, 'id'):
            raise AttributeError("Author object must have 'name' and 'id' attributes.")
        
        try:
            url = f"{self.REDDIT_API}{author.name}"
            response = requests.get(url, timeout=10)

            if response.status_code != 200:
                response.raise_for_status()

            try:
                data = response.json()
            except ValueError as e:
                print(f"Error parsing JSON: {e}")
                return self.active, self.provider, self.address

            contacts = data.get('contacts', {})
            user_data_list = contacts.get(f't2_{author.id}', [])

            if user_data_list:
                user_data = user_data_list[0]
                self.active = user_data.get('active')
                self.provider = user_data.get('provider')
                self.address = user_data.get('address')
                    
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error: {e}")
        except requests.exceptions.ConnectionError as e:
            print(f"Connection error: {e}")
        except requests.exceptions.Timeout as e:
            print(f"Timeout error: {e}")
        except requests.exceptions.RequestException as e:
            print(f"Error during request: {e}")

        return self.active, self.provider, self.address