import json
import os
import re
import slackclient
import sys

# weatherbot is a more complicated example of a bot. There are a couple of new
# things here,  compared to the simple randombot:
#  * It can detect mentions as well as direct messages
#  * It calls an external service to get data before responding
#  * It uses the chat.postMessage API call instead of rtm_send_message, so it
#    can display fancier formatting
# Have a read!

def main():
    try:
        token = os.environ['SLACK_API_TOKEN']
    except Exception as e:
        print('Could not find Slack API token:', e)
        sys.exit(1)

    client = slackclient.SlackClient(token)
    if client.rtm_connect():
        # We're going to use a Slack API method here to get information about the
        # current user account (that is, weatherbot's account!). We need this so
        # we know what weatherbot's user ID is, and can detect when someone mentions
        # it. The first thing to do is make the API call!
        raw_response = client.api_call('auth.test')
        # For more info on this call, see
        # https://api.slack.com/methods/auth.test

        # Now we have a response as raw bytes, we can convert ot to a nice string,
        # assuming it's encoded as utf-8. If you don't know what utf-8 is, don't
        # worry too much. If you're interested, check out this article:
        # www.joelonsoftware.com/articles/Unicode.html
        response = raw_response.decode('utf-8')

        # The Slack API communicated using JSON, so let's parse a JSON object from
        # the string.
        auth_info = json.loads(response)

        # Now we can use auth_info as a regular dict:
        if not auth_info['ok']:
            # This should never happen!
            print('auth.test returned not OK:', auth_info['error'])
            sys.exit(1)

        # Finally, we can get our ID!
        my_id = auth_info['user_id']

        # Slack formats mentions like so: <@USER_ID>. So we need a regex to match
        # that so we can test messages for mentions of ourself.
        mentioned = re.compile('<@' + my_id + '>')

        while True:
            messages = client.rtm_read()
            for message in messages:
                if message.get('type', None) != 'message' or 'text' not in message:
                    continue

                # Calling .match on a regex returns an object if there was a match.
                if mentioned.match(message['text']) is not None:
                    # We're in business! Let's get the city the user wants to know
                    # the weather for.
                    city = get_city_mentioned(message['text'])

                    # If we couldn't tell what city the user wants, send them a
                    # nice error message.
                    if city is None:
                        reply = message_to_user(message['user'],
                            "Are you sure that's a city? Maybe it's a town!")
                        client.rtm_send_message(message['channel'], reply)
                        continue

                    forecast = get_forecast(city)
                    attachments = format_weather_attachment(forecast)
                    send_message(
                        client,
                        message['channel'],
                        "Weather forecast for " + city,
                        attachments,
                    )

def message_to_user(user, message):
    return '<@{}>: {}'.format(user, message)

def get_city_mentioned(text):
    for city in ['Sydney', 'Brisbane', 'Melbourne', 'Adelaide', 'Perth', 'Hobart']:
        if city in text:
            return city
    return None

def get_forecast(city):
    # TODO: find a web API to get this data from lol
    if city == 'Sydney':
        today = 'rain'
        tomorrow = 'rain'
    else:
        today = 'sun'
        tomorrow = 'sun'
    return [today, tomorrow]

def format_weather_attachment(forecast):
    attachments = []
    [today, tomorrow] = forecast
    attachments.append({
        'title': 'Today',
        'text': today,
        'color': None if today == 'rain' else 'warning',
    })
    attachments.append({
        'title': 'Tomorrow',
        'text': tomorrow,
        'color': None if tomorrow == 'rain' else 'warning',
    })
    return attachments

def send_message(client, channel, text, attachments):
    # For documentation on chat.postMessage, see
    # https://api.slack.com/methods/chat.postMessage
    raw_response = client.api_call('chat.postMessage',
        channel = channel,
        text = text,
        as_user = True,
        # Attachments must be sent as a text blob for some reason.
        attachments = json.dumps(attachments),
    )
    response = json.loads(raw_response.decode('utf-8'))
    if 'error' in response:
        print('Slack API error', response['error'])

if __name__ == '__main__':
    main()
