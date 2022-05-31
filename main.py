from flask import Flask, render_template
from flask_socketio import SocketIO
import base64
import os
import stem
import stem.connection
import nacl.public
import sys
import getopt
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

from stem.control import Controller
import time
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(12).hex()
socketio = SocketIO(app)

count_users = 0

def generate_key ():
    client_auth_priv_key_raw = nacl.public.PrivateKey.generate()
    client_auth_priv_key = key_str(client_auth_priv_key_raw)
    client_auth_pub_key = key_str(client_auth_priv_key_raw.public_key)

    return  client_auth_pub_key, client_auth_priv_key

def key_str(key):
        """
        Returns a base32 decoded string of a key.
        """
        # bytes to base 32
        key_bytes = bytes(key)
        key_b32 = base64.b32encode(key_bytes)
        # strip trailing ====
        assert key_b32[-4:] == b"===="
        key_b32 = key_b32[:-4]
        # change from b'ASDF' to ASDF
        s = key_b32.decode("utf-8")
        return s

@app.route('/')
def sessions():
    global count_users

    if (app.config.get('max_users') > 0):
        if count_users >= app.config.get('max_users'):
            return render_template('max_users.html')
        else:
            return render_template('yatch.html')
    else:
        return render_template('yatch.html')

@socketio.on('connect')
def test_connect():
    global count_users

    count_users = count_users + 1

    socketio.emit('user_connected', count_users)

@socketio.on('disconnect')
def test_disconnect():

    global count_users

    count_users = count_users - 1

    socketio.emit('user_disconnected',count_users)


@socketio.on('my event')
def handle_my_custom_event(json, methods=['GET', 'POST']):

    now = datetime.now()

    current_time = now.strftime("%H:%M:%S")
    timestamp = int(time.time())
    json["timestamp"] = timestamp
    json["time"] = current_time
    socketio.emit('my response', json)

@socketio.on('server_clean')
def handle_server_clean(methods=['GET', 'POST']):

    socketio.emit('client_clean')

@socketio.on('server_clean_mine')
def handle_server_clean_mine(uuid,methods=['GET', 'POST']):

    socketio.emit('client_clean_mine',uuid)

@socketio.on('server_close')
def handle_server_close( methods=['GET', 'POST']):

    socketio.emit('client_close')
    time.sleep(1)
    quit()

def time_clean_job():

    timestamp = int(time.time())
    json = {
        "timestamp": timestamp,
        "max_time": app.config.get('max_time')
    }
    socketio.emit('time_clean',json)


if __name__ == '__main__':

    private = "true"
    max_users = -1
    max_time = 30
    tor_password = ""

    argv = sys.argv[1:]
  
    try:
        opts, args = getopt.getopt(argv, "h:p:m:t:")
      
    except:
        print("Error")
        quit()
  
    for opt, arg in opts:

        if opt in ['-h']:
            tor_password = arg

        elif opt in ['-p']:
            if (arg == "true" or arg == "false"):
                private = arg
            else:
                print ("-p can only be 'true' or 'false'")
                quit()
        
        elif opt in ['-m']:
            if (isinstance(int(arg), int)):
                if (int(arg) > 0):
                    max_users = int(arg)
                else:
                    print ("-m must be a positive integer")
                    quit()
            else:
                print ("-m must be a positive integer")
                quit()
        elif opt in ['-t']:
            if (isinstance(int(arg), int)):
                if (int(arg) > 0):
                    max_time = int(arg)
                else:
                    print ("-t must be a positive integer")
                    quit()
            else:
                print ("-t must be a positive integer")
                quit()

    print(' * Connecting to tor')

    with Controller.from_port() as controller:

        controller.authenticate(tor_password.strip())
        
        # Create a hidden service where visitors of port 80 get redirected to local
        # port 5000 (this is where Flask runs by default).
        if (private == "true"):
            pub, priv = generate_key()
          
            response = controller.create_ephemeral_hidden_service({80: 5000}, client_auth_v3=pub,await_publication = True)
            print(" * Our service is available at %s.onion, press ctrl+c to quit" % response.service_id)
            print("Use this private key to join Yatch " + priv) 
        else:
            response = controller.create_ephemeral_hidden_service({80: 5000}, await_publication = True)
            print(" * Our service is available at %s.onion, press ctrl+c to quit" % response.service_id)
        try:
            scheduler = BackgroundScheduler()
            job = scheduler.add_job(time_clean_job, 'interval', seconds=10)
            scheduler.start()
            app.config['max_users'] = max_users
            app.config['max_time'] = max_time
            socketio.run(app, debug=False)
        finally:
            print(" * Shutting down our hidden service")
