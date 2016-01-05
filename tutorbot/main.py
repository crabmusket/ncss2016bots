import json
import os
import re
import slackclient
import subprocess
import sys
import asyncio

def main():
    try:
        token = os.environ['SLACK_API_TOKEN']
    except Exception as e:
        print('Could not find Slack API token:', e)
        sys.exit(1)

    slack = slackclient.SlackClient(token)
    if slack.rtm_connect():
        auth = json.loads(slack.api_call('auth.test').decode('utf-8'))
        if 'ok' in auth and not auth['ok']:
            print('auth.test returned not OK')
            sys.exit(1)
        my_id = auth['user_id']
        tutorbot(slack, my_id)
    else:
        print('Could not connect to Slack')
        sys.exit(1)

def tutorbot(slack, my_id):
    tutor = None
    running_tutorials = {}
    mentioned = re.compile('<@' + my_id + '>')
    while True:
        messages = slack.rtm_read()
        for message in messages:
            if 'user' in message and message['user'] == my_id:
                continue
            if message.get('type', None) == 'message':
                if message['channel'][0] == 'D':
                    if 'I am the tutor' in message['text'].lower():
                        if tutor is None:
                            tutor = message['user']
                        else:
                            say(slack, message['channel'], 'Nice try')
                    else:
                        handle_private_message(slack, message, running_tutorials)
                elif mentioned.match(message['text']) is not None:
                    handle_public_message(slack, message)

def handle_public_message(slack, message):
    say(slack, message['channel'], "<@"+message['user']+">, come talk to me in https://ncss2016bots.slack.com/messages/@tutorbot/")

def handle_private_message(slack, message, tutorials):
    user = message['user']
    if user in tutorials:
        try:
            tutorials[user].send(message)
        except StopIteration:
            del tutorials[user]
            say(slack, message['channel'], 'Bye!')
    else:
        tutorial = run_tutorial(slack, user, message['channel'])
        tutorial.send(None)
        tutorials[user] = tutorial

@asyncio.coroutine
def run_tutorial(slack, pupil, channel):
    say(slack, channel, "Hey there! If you'd like me to start the tutorial, send me a message with 'begin' in it!")
    msg = yield
    if 'begin' not in msg['text'].lower():
        say(slack, channel, "Never mind then. Come back any time! :upside_down_face:")
        raise StopIteration()

    say(slack, channel, (
        "Yay! :smile:"
        " At any time during the tutorial, you can send me 'quit' to stop."
        " Got it?"
    ))

    yield from next_message()

    say(slack, channel, (
        "The first thing you'll need to do to make a Slack bot is get an API token."
        " This is like a password that lets you send and receive messages."
        " Every bot needs its own token."
        " To get your token, visit https://ncss2016bots.slack.com/apps/build/custom-integration and then click on `Bots`."
        " Please name your bot after yourself, so we know which bots belong to who!"
        " For example, Daniel's bot should be called `danielbot`."
        " Let me know once you've named your bot and got to the config page."
        " It should look like this:"
    ), attach_image = 'http://i.imgur.com/JAO12nm.png')

    yield from next_message()
    say(slack, channel, (
        "Copy the API token somewhere safe!"
        " You could even paste it here and I'll remember it for you."
        " Once you've set up your bot (choose a nice emoticon, won't you? :scream:), click 'Save integration'. Let me know once that's done."
    ))

    yield from next_message()
    say(slack, channel, (
        "Okay, great. Now it's time to write some Python!"
        " Create a new Python file in IDLE, and we'll start by importing the `slackclient` library and connecting to the realtime API!"
        " It looks something like this:"
    ))

    send_file(slack, channel,
        name = 'step 1.py',
        filetype = 'python',
        content = '\n'.join([
            'import slackclient',
            '',
            'token = \'your Slack API token here!\'',
            'client = slackclient.SlackClient(token)',
            'if client.rtm_connect():',
            '    print(\'connected!\')',
            'else:',
            '    print(\'failed for some reason :(\')',
        ]),
    )

    say(slack, channel, "Let me know when you're ready to continue.")

    yield from next_message()

@asyncio.coroutine
def next_message():
    message = None
    while message is None:
        message = yield
        text = message['text'] = message['text'].lower()
        if 'exit' in text or 'quit' in text:
            raise StopIteration()
        if 'help' in text or 'how do i' in text or 'can\'t' in text:
            print('Help requested?', text)
        elif text.startswith('feedback:'):
            print(text)
            message = None
    return message

def say(slack, channel, text, attach_image = None):
    attachments = []
    if attach_image is not None:
        attachments.append({
            'text': '',
            'image_url': attach_image,
        })

    raw_response = slack.api_call('chat.postMessage',
        channel = channel,
        text = text,
        as_user = True,
        attachments = json.dumps(attachments),
    )
    response = json.loads(raw_response.decode('utf-8'))
    if 'error' in response:
        print('Slack API error', response['error'])

def send_file(slack, channel, content, name, filetype):
    raw_response = slack.api_call('files.upload',
        channels = channel,
        content = content,
        filename = name,
        filetype = filetype,
    )
    response = json.loads(raw_response.decode('utf-8'))
    if 'error' in response:
        print('Slack API error', response['error'])

if __name__ == '__main__':
    main()
