from threading import Lock
from flask import Flask, render_template, session, request, jsonify, url_for
from flask_socketio import SocketIO, emit, disconnect
import time
import random
import math
import MySQLdb
import ConfigParser
import serial
from serial import Serial
import os

async_mode = None

app = Flask(__name__)

config = ConfigParser.ConfigParser()
config.read('config.cfg')
myhost = config.get('mysqlDB', 'host')
myuser = config.get('mysqlDB', 'user')
mypasswd = config.get('mysqlDB', 'passwd')
mydb = config.get('mysqlDB', 'db')
print myhost

app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()

def background_thread(args):
    count = 0
    dataCounter = 0
    dataList = []
    db = MySQLdb.connect(host=myhost,user=myuser,passwd=mypasswd,db=mydb)
    vol_pr = -1
    vol_stat = 0
    pos = -1
    i = 1
    while True:
        if args:
            A = dict(args).get('A')
            dbV = dict(args).get('db_value')
            ocV = dict(args).get('oc_value')
            sV = dict(args).get('s_value')
        else:
            A = '0'
            dbV = 'notstarted'
            ocV = 'notopened'
            sV = 'notset'
        print args
        if ocV == 'open':
            ser=serial.Serial(
                port = '/dev/ttyS1',
                baudrate = 9600,
                parity = serial.PARITY_NONE,
                stopbits = serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                timeout = 1
            )
            if ser.inWaiting() >= 0:
                #read_ser=ser.read(3)
                read_ser=ser.readline()
                print(read_ser)
            if sV == 'set':
                if int(A) < 10:
                    ser.write(bytes('0'))
                if int(A) < 100:
                    ser.write(bytes('0'))
                ser.write((bytes(A)))
                vol_stat = 1
                sV='notset'
            count += 1
            dataCounter +=1
            try:
                pos = int(read_ser)
                vol = round(float(read_ser)/36,3)
                if vol_stat == 1:
                    vol_pr = vol
                    if i == 2:
                        vol_stat = 0
                        i = 0
                    i = i + 1
                else:
                    if vol != vol_pr:
                        vol_set = vol
                    vol_pr = vol
            except:
                pass
            if dbV == 'start':
              dataDict = {
                "t": time.time(),
                "x": dataCounter,
                "yPos": pos,
                "yVol": vol_set}
              dataList.append(dataDict)
            else:
              if len(dataList)>0:
                fuj = str(dataList).replace("'", "\"")
                print fuj
                cursor = db.cursor()
                cursor.execute("SELECT MAX(id) FROM graph")
                maxid = cursor.fetchone()
                cursor.execute("INSERT INTO graph (id, hodnoty) VALUES (%s, %s)", (maxid[0] + 1, fuj))
                db.commit()
                str2 = "\r\n"
                str1 = str(fuj)
                str3 = str1 + str2
                fo = open("static/files/test.txt","a+")
                fo.write(str3)
                fo.close
              dataList = []
              dataCounter = 0
            if pos != -1:
              socketio.emit('my_response',
                          {'dataPos': pos, 'dataVol': vol_set, 'count': count},
                          namespace='/test')
            else:
              print('Serial port not opened!')
        socketio.sleep(2)
    db.close()

@app.route('/')
def tabs():
    return render_template('tabs.html', async_mode=socketio.async_mode)

@app.route('/dbdata')
def dbdata_all():
  db = MySQLdb.connect(host=myhost,user=myuser,passwd=mypasswd,db=mydb)
  cursor = db.cursor()
  cursor.execute('''SELECT hodnoty FROM graph EXCEPT SELECT hodnoty FROM graph WHERE id=1''')
  rv = cursor.fetchall()
  return str(rv)    

@app.route('/dbdata/<string:num>', methods=['GET', 'POST'])
def dbdata(num):
  db = MySQLdb.connect(host=myhost,user=myuser,passwd=mypasswd,db=mydb)
  cursor = db.cursor()
  print num
  cursor.execute("SELECT hodnoty FROM graph WHERE id=%s", str(int(num)+1))
  rv = cursor.fetchone()
  return str(rv[0])

@app.route('/fldata/<string:num>', methods=['GET', 'POST'])
def fldata(num):
    fo = open("static/files/test.txt","r")
    rows = fo.readlines()
    return rows[int(num)-1]
      
@socketio.on('my_event', namespace='/test')
def test_message(message):   
    if message['value'] != 1:
        session['receive_count'] = session.get('receive_count', 0) + 1
        session['A'] = message['value']    
        emit('my_response_set',
            {'dataPos': message['value'], 'count': session['receive_count']})
        session['s_value'] = 'set'
        socketio.sleep(2)
        session['s_value'] = 'notset'

@socketio.on('oc_event', namespace='/test')
def oc_message(message):   
#    session['receive_count'] = session.get('receive_count', 0) + 1 
    session['oc_value'] = message['value']    
#    emit('my_response',
#         {'data': message['value'], 'count': session['receive_count']})
    if message['value'] == 'close':
        os._exit(0)

@socketio.on('db_event', namespace='/test')
def db_message(message):   
#    session['receive_count'] = session.get('receive_count', 0) + 1 
    session['db_value'] = message['value']    
#    emit('my_response',
#         {'data': message['value'], 'count': session['receive_count']})

@socketio.on('disconnect_request', namespace='/test')
def disconnect_request():
#    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response_cd',
         {'dataPos': 'Disconnected!', 'count': 1})
    disconnect()

@socketio.on('connect', namespace='/test')
def test_connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(target=background_thread, args=session._get_current_object())
            session['A'] = '0'
            session['oc_value'] = 'notopened'
            session['db_value'] = 'notstarted'
            session['s_value'] = 'notset'
    emit('my_response_cd', {'dataPos': 'Connected', 'count': 0})

# @socketio.on('slider_event', namespace='/test')
# def slider_message(message):  
#     #print message['value']   
#     session['slider_value'] = message['value']

@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected', request.sid)

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=80, debug=True)