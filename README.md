# BCBridgeBot

## Description
The province of British Columbia is having an epidemic of trucks hitting overpasses and other objects. This bot helps database and keep track of statistics related to the incidents on the subreddit r/BritishColumbia.

## Features
* Stores all incident Reddit posts with the flair "Truck Hits Overpass" in a MongoDB cloud database
* Creates a sticky comment when a new post is detected and gives a funny AI generated quote related to the number of times since the last incident
* Creates a meme image of the last time an incident occured.
* This bot also checks user's history to see if they frequent subs that are on the banned list. If so, those users are banned from the subreddit.

### !Commands

These commands can be used anywhere in the subreddit:
* !bridge - Used anywhere in the subreddit of r/BritishColumbia to summon the bot

These commands can be used as replies to u/BCBridgeBot
* !info - Information from the bot
* !bridgestats - The bot replies with BC Overpass statistics
* !bridgefact - The bot replies with an AI generated fact about bridges in British Columbia
* !bcfact - The bot replies with an AI generated fact about British Columbia
