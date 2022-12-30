import os
from paramiko import SSHClient, AutoAddPolicy
from flask import Flask, jsonify, render_template
from time import sleep

ip = "172.16.1.10"
valheim_port = 2456
client = SSHClient()
client.set_missing_host_key_policy(AutoAddPolicy())
app = Flask(__name__)

def connect():
    client.connect(ip, username='username', password='password')

def disconnect():
    client.close()

def is_server_up():
    response = os.system("ping -c 1 " + ip)
    if response == 0:
        return True
    return False

def low_on_disk():
    connect()
    stdin, stdout, stderr = client.exec_command('''powershell -c "(Get-CimInstance -ClassName Win32_LogicalDisk)[0].FreeSpace / 1GB"''')
    freespace = (f'{stdout.read().decode("utf8")}')
    errors = (f'{stderr.read().decode("utf8")}')
    result  = False

    if(errors):
        result = '???'
    
    if(float(freespace) < 12.8):
        result = True

    disconnect()

    if(result):
        return result
    
    return False

def valheim_running():

        #check if the application is also running on the machine via a ssh connection or something. 
        connect()
        stdin, stdout, stderr = client.exec_command('''powershell -c "Get-Process | ? { $_.ProcessName -like 'valheim_server'}"''')
        valheim_server_process = (f'{stdout.read().decode("utf8")}')
        errors = (f'{stderr.read().decode("utf8")}')
        disconnect()

        if(errors):
            print(errors)
            return '???'
        
        if(valheim_server_process):
            return True
        else:
            return False

def get_valheim_version():
    return '???'

def get_state(): 
    state = {}
    state['Valheim Host Up'] = is_server_up()
    state['Low on Diskspace'] = low_on_disk()
    state['Valheim Running'] = valheim_running()
    state['Valheim Version'] = get_valheim_version()

    if(state['Valheim Host Up'] == False):
        state['State'] = 'Critical Issue'
    elif(state['Valheim Running'] == False or state['Valheim Running'] == '???'):
        state['State'] = 'Critical Issue'
    elif(state['Low on Diskspace'] == True or state['Low on Diskspace'] == '???'):
        state['State'] = 'Warning issues imminent'
    else:
        state['State'] = 'OK'

    return state


@app.route("/api")
def api():
    return jsonify(get_state())

@app.route("/")
def home():
    return render_template('valheim.html', state=get_state())
    # return jsonify(get_state())

if __name__ == '__main__':
    app.run(debug=True, port=80, host='0.0.0.0')


