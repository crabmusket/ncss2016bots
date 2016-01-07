import json
import os
import re
import slackclient
import sys
import asyncio

def main():
    try:
        token = os.environ['SLACK_API_TOKEN']
    except Exception as e:
        print('Could not find Slack API token:', e)
        sys.exit(1)

    client = slackclient.SlackClient(token)
    if client.rtm_connect():
        auth = json.loads(client.api_call('auth.test').decode('utf-8'))
        if 'ok' in auth and not auth['ok']:
            print('auth.test returned not OK')
            sys.exit(1)
        my_id = auth['user_id']
        tutorbot(client, my_id)
    else:
        print('Could not connect to Slack')
        sys.exit(1)

def tutorbot(client, my_id):
    tutor = None
    running_tutorials = {}
    mentioned = re.compile('<@' + my_id + '>')
    while True:
        messages = client.rtm_read()
        for message in messages:
            if 'user' in message and message['user'] == my_id:
                continue
            if message.get('type', None) == 'message' and 'text' in message:
                if message['channel'][0] == 'D':
                    if 'I am the tutor' in message['text'].lower():
                        if tutor is None:
                            tutor = message['user']
                        else:
                            send_message(client, message['channel'], 'Nice try')
                    else:
                        handle_private_message(client, message, running_tutorials)
                elif mentioned.match(message['text']) is not None:
                    handle_public_message(client, message)

def handle_public_message(client, message):
    send_message(client, message['channel'], "<@"+message['user']+">, come talk to me in https://ncss2016bots.slack.com/messages/@tutorbot/")

def handle_private_message(client, message, tutorials):
    user = message['user']
    if user in tutorials:
        try:
            tutorials[user].send(message)
        except (StopIteration, UserQuit):
            del tutorials[user]
            send_message(client, message['channel'], 'Bye!')
        except:
            del tutorials[user]
            send_message(client, message['channel'], 'Something went wrong!')
    else:
        tutorial = run_tutorial(client, user, message['channel'])
        tutorial.send(None)
        tutorials[user] = tutorial

def example(text):
    return text[1:]

ex1script = example('''
import slackclient

token = 'your Slack API token here!'
client = slackclient.SlackClient(token)
if client.rtm_connect():
    print('connected!')
else:
    print('failed for some reason :(')
''')

ex2script = example('''
    while True:
        messages = client.rtm_read()
        for message in messages:
            print(message)
''')

ex3script = example('''
                if message.get('type', None) != 'message' or 'text' not in message:
                    continue
                if 'robots suck' in message['text']:
                    client.rtm_send_message(message['channel'], 'I heard that!')
''')

class UserQuit(Exception):
    pass

@asyncio.coroutine
def run_tutorial(client, pupil, channel):
    def say(text, **kwargs):
        if len(kwargs) == 0:
            client.rtm_send_message(channel, text)
        else:
            send_message(client, channel, text, **kwargs)

    say("Hey there! If you'd like me to start the tutorial, send me a message with 'begin' in it!")
    msg = yield
    if 'begin' not in msg['text'].lower():
        say("Never mind then. Come back any time! :upside_down_face:")
        raise StopIteration()

    say(
        "Yay! :smile:"
        " At any time during the tutorial, you can send me 'quit' to stop."
        " Got it?"
    )

    yield from next_message()

    say((
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
    say(
        "Copy the API token somewhere safe!"
        " You could even paste it here and I'll remember it for you."
        " Once you've set up your bot (choose a nice emoticon, won't you? :scream:), click `Save integration`. Let me know once that's done."
    )

    yield from next_message()
    say(
        "Okay, great. Now it's time to write some Python!"
        " Create a new Python file in IDLE, and we'll start by importing the `slackclient` library and connecting to the realtime API!"
        " It looks something like this:"
    )

    send_file(client, channel,
        name = 'step 1.py',
        filetype = 'python',
        content = ex1script,
    )

    say(
        "Try running this - it should print out `connected!`."
        " Let me know when you're ready to continue."
    )

    yield from next_message()
    say((
        "Now that you know how to connect to Slack, let's start listening to some messages."
        " Bots can only see messages from channels they've been invited into (like vampires), so before you do this, invite your bot into #robots."
        " Here's Daniel inviting me by @mentioning me in the #robots channel:"
    ), attach_image = 'http://i.imgur.com/2wybb1W.png')

    say("Once you've done that, let me know!")
        
    yield from next_message()
    say(
        "Now we can add a little more code to start listening for messages."
        " Put this inside the `if` branch after `print('connected!')`:"
    )
    send_file(client, channel,
        name = 'step 2.py',
        filetype = 'python',
        content = ex2script,
    )
    say(
        "If you run that code, then send a message in the #robots channel, and you should see it printed out by your program!"
        " The message will appear as a JSON object."
        " JSON objects are just like Python dicts."
        " You'll see several different fields in each message."
        " Try running the code and let me know how it goes!"
    )

    yield from next_message()
    say(
        "Notice there are messages with several different `type`s, and they each have different contents."
        " You can see a list of all the possible message types at https://api.slack.com/rtm."
        " Now that we can see messages coming in, let's respond to them!"
        " Tell me when I should keep going."
    )

    yield from next_message()
    say(
        "Instances of the `SlackClient` class have a `rtm_send_message` method which we can use to quickly send messages to a channel"
        " You can use it like this: `client.rtm_send_message('channel ID', 'message here!')`."
        " The tricky part is finding the right channel ID for a particular message."
        " For now, we'll write a bot that only responds to messages in the same channel they appeared in, so we can get the channel out of the message object, like this:"
    )
    send_file(client, channel,
        name = 'step 3.py',
        filetype = 'python',
        content = ex3script,
    )
    say(
        "Notice that we're ignoring events that aren't messages."
        " Those messages might not have a `text` property, so we wouldn't know what to do with them!"
        " Replace `print(message)` in your file with that code, give it a try, and let me know how you get on!"
    )

    yield from next_message()
    say(
        "Well done!"
        " This is the end of the introductory tutorial! :party:"
        " Now you know how to connect to Slack as a bot, receive messages, and send messages back."
        " What will you do now?"
        "\n * Get some ideas for a bot to create https://github.com/eightyeight/ncss2016bots#bot-ideas"
        "\n * See a simple example bot: my friend @randombot https://github.com/eightyeight/ncss2016bots/blob/master/randombot/main.py"
        "\n * See a more complicated example bot: @weatherbot https://github.com/eightyeight/ncss2016bots/blob/master/weatherbot/main.py"
        "\n * Read my own source code! https://github.com/eightyeight/ncss2016bots/blob/master/tutorbot/main.py"
        "\n * Read about how Slack messages are formatted so you can send fancier messages https://api.slack.com/docs/formatting"
    )

@asyncio.coroutine
def next_message():
    message = yield
    text = message['text'] = message['text'].lower()
    if 'exit' in text or 'quit' in text:
        raise UserQuit()
    return message

def send_message(client, channel, text, attach_image = None):
    attachments = []
    if attach_image is not None:
        attachments.append({
            'text': '',
            'image_url': attach_image,
        })

    raw_response = client.api_call('chat.postMessage',
        channel = channel,
        text = text,
        as_user = True,
        attachments = json.dumps(attachments),
    )
    response = json.loads(raw_response.decode('utf-8'))
    if 'error' in response:
        print('Slack API error', response['error'])

def send_file(client, channel, content, name, filetype):
    raw_response = client.api_call('files.upload',
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
