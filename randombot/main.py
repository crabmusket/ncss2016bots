import os
import re
import slackclient
import sys
import random

random_re = re.compile('([0-9]+) to ([0-9]+)')

def main():
    try:
        token = os.environ['SLACK_API_TOKEN']
    except Exception as e:
        print('Could not find Slack API token:', e)
        sys.exit(1)

    client = slackclient.SlackClient(token)
    if client.rtm_connect():
        while True:
            messages = client.rtm_read()
            for message in messages:
                if message.get('type', None) == 'message':
                    matches = random_re.findall(message['text'])
                    numbers = []
                    for (low, high) in matches:
                        number = random.randrange(int(low), int(high))
                        numbers.append(str(number))
                    if len(numbers) != 0:
                        client.rtm_send_message(message['channel'], ', '.join(numbers))
                    else:
                        if 'x to y' in message['text']:
                            client.rtm_send_message(message['channel'], "Nearly there. Now replace x and y with some numbers!")
                        else:
                            client.rtm_send_message(message['channel'], "I'm not sure what you mean. Send me a message containing 'x to y' somewhere!")
    else:
        print('Could not connect to Slack')
        sys.exit(1)

if __name__ == '__main__':
    main()
