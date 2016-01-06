import os
import random
import re
import slackclient
import sys

# randombot is a simple example of what you could do with a bot that responds
# to messages. To keep it simple, it only responds to a very limited set of
# direct messages, so there's no point inviting it into #robots because it won't
# say anything.

# We're going to accept input messages of the form 'x to y', where x and y are
# integers. We don't detect the start or end of the string, so we can ignore
# leading and trailing text.
random_re = re.compile('([0-9]+) to ([0-9]+)')

# I'm not sharing my API token with you! Keeping sensitive information like
# tokens and passwords in environment variables instead of source code is
# generally a good idea.
try:
    token = os.environ['SLACK_API_TOKEN']
except Exception as e:
    print('Could not find Slack API token:', e)
    sys.exit(1)

# Start up a realtime connection, like in the tutorial.
client = slackclient.SlackClient(token)
if client.rtm_connect():
    while True:
        messages = client.rtm_read()
        for message in messages:
            if message.get('type', None) != 'message' or 'text' not in message:
                continue

            # Reject messages coming from ourself! I cheated and used the bot's
            # user ID which I checked after deploying the bot. For a better way
            # of doing this, see weatherbot.
            if message['user'] == 'U0HQDMKJL':
                continue

            # We only want to respond to direct messages in this example.
            # Direct message channel IDs always start with D.
            if message['channel'][0] != 'D':
                continue

            # If the message contains multiple 'x to y' patterns,  we'll respond
            # to all of them.
            matches = random_re.findall(message['text'])
            numbers = []
            for (low, high) in matches:
                number = random.randrange(int(low), int(high))
                numbers.append(str(number))
            if len(numbers) != 0:
                client.rtm_send_message(message['channel'], ', '.join(numbers))
            else:
                # Provide a help message if we think the user made a mistake
                # entering their request.
                if 'x to y' in message['text']:
                    client.rtm_send_message(message['channel'],
                        "Nearly there. Now replace x and y with some numbers!")
                else:
                    client.rtm_send_message(message['channel'],
                        "I'm not sure what you mean. Send me a message containing 'x to y' somewhere!")
else:
    print('Could not connect to Slack')
    sys.exit(1)
