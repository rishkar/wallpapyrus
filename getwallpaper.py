import sys
from datetime import datetime
from datetime import timedelta
import praw
import configparser
import json
import os
import urllib.request
from PIL import Image
import ctypes


# Get and read config
config_arr = configparser.ConfigParser()
config_arr.read('config.ini')
config_arr = config_arr['MAIN']

# Open database file and load it to memory. We will overwrite this later.
usedImages = {}
if os.path.exists('database.json'):
    usedImages = json.load(open('database.json', 'r'))

# Clean up any old images in the database
for post in usedImages:
    if (datetime.now() - datetime.strptime(usedImages[post], "%Y%m%d%H%M%S")) > timedelta(days=31): # TODO: change according to config
        # Delete the file first
        oldImage = glob.glob("image/%s.*" % post)
        if oldImage[0]:
            os.remove(oldImage[0])
        del post



# Set up reddit instance and grab values from config.ini
reddit_instance = praw.Reddit(client_id=config_arr['client_id'],
                              client_secret=config_arr['client_secret'],
                              user_agent=config_arr['user_agent'])
# Set up subreddit instance
subreddit_instance = reddit_instance.subreddit(config_arr['subreddit_name'])

# Listings array
listing_arr = subreddit_instance.top(time_filter=config_arr['time_filter'])

# Start going post by post to find the one we like
desired_post, desired_post_filename = None, None
for post in listing_arr:
    # Skip if we've used this before
    if post.id in usedImages:
        continue

    # nsfw check
    if post.over_18:
        usedImages[str(post.id)] = datetime.strftime(datetime.now(), "%Y%m%d%H%M%S")
        continue

    # upvote check
    if post.score < int(config_arr['upvote_limit']):
        sys.exit("There are no more posts on the specified subreddit that are above the upvote limit specified in the "
                 "config.")

    # Download image
    filename = "image/" + post.id + '.' + post.url.split('.')[-1]  # Last part grabs the extension of the image
    urllib.request.urlretrieve(post.url, filename)

    # test image dimensions
    image = Image.open(filename).size
    if image[0] < 1920 or image[1] < 1080:
        usedImages[str(post.id)] = datetime.strftime(datetime.now(), "%Y%m%d%H%M%S")
        os.remove(filename) # Remove the image file too so we don't leave cruft
        continue

    # We now know we want to use this image
    desired_post = post
    desired_post_filename = filename
    break

# We're using this image, so let's add it to the used images database so it doesn't get used again.
usedImages[str(desired_post)] = datetime.strftime(datetime.now(), "%Y%m%d%H%M%S")

# set wallpaper
print((os.getcwd().replace("\\", "/") + '/' + desired_post_filename))
print(desired_post_filename)
print(ctypes.windll.user32.SystemParametersInfoW(20, 0, (os.getcwd().replace("\\", "/") + '/' + desired_post_filename), 3))

# save image database
json.dump(usedImages, open('database.json', 'w'))
