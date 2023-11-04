from datetime import datetime

def load_existing_ids():
    existing_ids = set()
    try:
        with open('post_ids.txt', 'r') as f:
            for line in f:
                existing_ids.add(line.strip())
    except FileNotFoundError:
        with open('post_ids.txt', 'w') as f:
            pass
    return existing_ids

def write_new_id_to_file(post_id):
    with open('post_ids.txt', 'a') as f:
        f.write(post_id + '\n')

def update_last_post_date():
    with open('last_post_date.txt', 'w') as f:
        f.write(str(datetime.now()))

def days_since_last_post():
    try:
        with open('last_post_date.txt', 'r') as f:
            last_post_date_str = f.read().strip()
            if last_post_date_str:
                last_post_date = datetime.fromisoformat(last_post_date_str)
                delta = datetime.now() - last_post_date
                return delta.days
            else:
                return None
    except FileNotFoundError:
        return None