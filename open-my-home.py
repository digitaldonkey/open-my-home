from flask import Flask, session, jsonify, Response, send_from_directory, render_template
import RPi.GPIO as GPIO
import time
import re
from flask import make_response
import json
from os import urandom, getenv
import datetime

from web3.auto import w3
from eth_account.messages import defunct_hash_message


app = Flask(__name__)
app.secret_key = "super secret key"

# TODO Implement max session open Time
MAX_RESPONSE_TIME = 120 # sec


# @app.route("/blink")
# def blink():
#     return openRelay()

# Template example
@app.route('/')
def welcome(name=None):
    return render_template('index.html', name=name)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.root_path,'favicon.ico', mimetype='image/vnd.microsoft.icon')


# Submit challenge
@app.route('/api/submit/<pubkey>/<signature>', methods=['GET'])
def submitSignature(pubkey=None, signature=None):
    if signature and isAuthorizedKey(pubkey) :
        try:
            challenge = session[pubkey]['challenge']
            timestamp = session[pubkey]['timestamp']
            restoredPubkey = ecVerify(challenge, signature)
            isValidTimespan = datetime.datetime.fromtimestamp(timestamp + MAX_RESPONSE_TIME) > datetime.datetime.now()

            if restoredPubkey == pubkey and isValidTimespan:
                openRelay()
                return Response(
                    status=200,
                    mimetype='application/json'
                )
        except ValueError :
            pass
    return make_response('Unauthorized', 401)

# Request challenge
@app.route('/api/get/<pubkey>', methods=['GET'])
def requestAuthToken(pubkey=None):
    now = datetime.datetime.now()
    challenge = 'Let me open the door at ' + now.strftime("%Y-%m-%d %H:%M:%S")
    if isAuthorizedKey(pubkey) :
        session[pubkey] = {
            'pubkey':     pubkey,
            'timestamp': int(time.time()),
            'challenge':  challenge,
        }
        return Response(
            json.dumps(session[pubkey]),
            status=200,
            mimetype='application/json'
        )
    return make_response(jsonify(challenge), 201)


def openRelay(gpio=21):
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(gpio,GPIO.OUT)
    # print "LED on"
    GPIO.output(gpio,GPIO.HIGH)
    time.sleep(1)
    # print "LED off"
    GPIO.output(gpio,GPIO.LOW)
    return "The light blinked for 1 sec"

def ecVerify(message, signature):
    message_hash = defunct_hash_message(text=message)
    return w3.eth.account.recoverHash(message_hash, signature=signature)

# Validate Public
#   Formal input validation and check if key is in config/authorized_keys
def isAuthorizedKey(pubkey):
    isValidKey = None
    if re.match('^0x[0-9a-fA-F]{40}$', pubkey) :

        with open('config/authorized_keys') as f:
            content = f.readlines()
        # Remove whitespace characters
        authorizedKeys = [x.strip() for x in content]

        try:
            isValidKey = authorizedKeys.index(pubkey)
        except ValueError :
            pass

    return isValidKey != None

# @app.route("/morse")
# def love():
#     return morse('.. / .-.. --- ...- . / -.-- --- ..- / -.-. ..- - . / --. .. .-. .-..')
#
# def morse(morseCode):
#     gpio = 21
#
#     GPIO.setmode(GPIO.BCM)
#     GPIO.setwarnings(False)
#     GPIO.setup(gpio,GPIO.OUT)
#     # print "LED on"
#
#     for letter in list(morseCode):
#
#         if (letter == '.'):
#             GPIO.output(gpio,GPIO.HIGH)
#             time.sleep(.1)
#
#         if (letter == '-'):
#             GPIO.output(gpio,GPIO.HIGH)
#             time.sleep(.2)
#
#         if (letter == ' '):
#             time.sleep(.2)
#
#         if (letter == '/'):
#             time.sleep(.4)
#
#         # print "LED off"
#         GPIO.output(gpio,GPIO.LOW)
#         time.sleep(.1)
#
#     return make_response(jsonify(morseCode), 201)
