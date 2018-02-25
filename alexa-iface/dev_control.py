import logging
from flask import Flask
from flask_ask import Ask, statement, question
import requests

app = Flask(__name__)
ask = Ask(app, "/dev")
logging.getLogger("flask_ask").setLevel(logging.DEBUG)
LOG = logging.getLogger("flask_ask")


@ask.launch
def start_skill():
    welcome_message = "Hello there, would you like to turn dev on?"
    return question(welcome_message)


@ask.intent("YesIntent")
def turn_left():
    turn_motor('left')
    msg = "dev turned on"
    return statement(msg)


@ask.intent("NoIntent")
def turn_right():
    turn_motor('right')
    msg = "dev turned off"
    return statement(msg)


def turn_motor(direction):
    if direction == 'left':
        pin = 3
    elif direction == 'right':
        pin = 4

    res = requests.get('http://192.168.0.19/digital/%s/LOW' % str(pin))
    LOG.debug(res)


if __name__ == '__main__':
    app.run(debug=True)
