from threading import Lock
from flask import Flask, render_template, session, request, jsonify, url_for
from flask_socketio import SocketIO, emit, disconnect
import time
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

app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()

A = '0'
ocV = 'notopened'
prV = 'notstarted'
dbV = 'notrecording'
flV = 'notrecording'
sV = 'notset'

def background_thread(args):
    global A
    global ocV
    global prV
    global dbV
    global flV
    global sV
    count = 0
    dataCounter = 0
    dataList = []
    dataCounter2 = 0
    dataList2 = []
    db = MySQLdb.connect(host=myhost,user=myuser,passwd=mypasswd,db=mydb)
    pos = -1
    vol = -1
    ard = 0
    ser=serial.Serial(
        port = '/dev/ttyS1',
        baudrate = 9600,
        parity = serial.PARITY_NONE,
        stopbits = serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout = 1
    )
    while True:
        cursor = db.cursor()
        cursor.execute("SELECT MAX(id) FROM graph")
        maxid = cursor.fetchone()
        db.commit()
        max_id = int(maxid[0]) - 1
        try:
            num_lines = sum(1 for line in open("static/files/test.txt"))
        except:
            num_lines = 0
        if ocV == 'open':
            if ard == 0:
                ser.write((bytes(181)))
                print('Serial communication started.')
                ard = 1
            if ser.inWaiting() >= 0:
                read_ser=ser.readline()
                read_ser2=ser.readline()
            if sV == 'set':
                if int(A) < 10:
                    ser.write(bytes('0'))
                if int(A) < 100:
                    ser.write(bytes('0'))
                ser.write((bytes(A)))
                vol_stat = 1
                sV='notset'
            count += 1
            if prV == 'resume':
                dataCounter +=1
                dataCounter2 +=1
                try:
                    pos = int(read_ser)
                    vol = float(read_ser2)
                except:
                    pass
                if pos != '' and vol != '':
                    if dbV == 'record':
                      dataDict = {
                        "t": time.time(),
                        "x": dataCounter,
                        "yPos": pos,
                        "yVol": vol}
                      dataList.append(dataDict)
                      print('Capturing data to database..')
                    else:
                      if len(dataList)>0:
                        fuj = str(dataList).replace("'", "\"")
                        print fuj
                        cursor = db.cursor()
                        cursor.execute("SELECT MAX(id) FROM graph")
                        maxid = cursor.fetchone()
                        cursor.execute("INSERT INTO graph (id, hodnoty) VALUES (%s, %s)", (maxid[0] + 1, fuj))
                        db.commit()
                        print('Data written to database.')
                        max_id = int(maxid[0])
                      dataList = []
                      dataCounter = 0
                    if flV == 'record':
                      dataDict2 = {
                        "t": time.time(),
                        "x": dataCounter2,
                        "yPos": pos,
                        "yVol": vol}
                      dataList2.append(dataDict2)
                      print('Capturing data to file..')
                    else:
                      if len(dataList2)>0:
                        fuj2 = str(dataList2).replace("'", "\"")
                        print fuj2
                        str2 = "\r\n"
                        str1 = str(fuj2)
                        str3 = str1 + str2
                        fo = open("static/files/test.txt","a+")
                        fo.write(str3)
                        fo.close()
                        print('Data written to file.')
                        num_lines = sum(1 for line in open("static/files/test.txt"))
                      dataList2 = []
                      dataCounter2 = 0
                    if pos != -1:
                      socketio.emit('my_response',
                        {'dataPos': pos, 'dataVol': vol, 'count': count},
                        namespace='/test')
                    else:
                      print('Serial port not opened!')
                    print('Monitoring..')
                else:
                    print('Error: No data fetched!')
            elif prV == 'pause':
                print('Monitoring paused.')
        elif ocV == 'close':
            ser.write((bytes(182)))
            print('Server closed successfully.')
            os._exit(0)
        socketio.emit('my_response_max',
            {'dbMax': max_id, 'flMax': num_lines},
            namespace='/test')
        socketio.sleep(1)
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
  num = int(num)
  numstr1 = str(int((num + 1)/10))
  numstr2 = str((num + 1) - int((num + 1)/10)*10)
  db = MySQLdb.connect(host=myhost,user=myuser,passwd=mypasswd,db=mydb)
  cursor = db.cursor()
  cursor.execute("SELECT hodnoty FROM graph WHERE id=%s%s" % (numstr1, numstr2))
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
        global A
        global sV
        A = message['value']    
        emit('my_response_set',
            {'dataPos': message['value'], 'count': session['receive_count']})
        sV = 'set'
        socketio.sleep(2)
        sV = 'notset'

@socketio.on('oc_event', namespace='/test')
def oc_message(message):   
    global ocV
    ocV = message['value']

@socketio.on('pr_event', namespace='/test')
def oc_message(message):   
    global prV
    prV = message['value']

@socketio.on('db_event', namespace='/test')
def db_message(message):   
    global dbV
    dbV = message['value']
    
@socketio.on('fl_event', namespace='/test')
def fl_message(message):   
    global flV
    flV = message['value']

@socketio.on('connect', namespace='/test')
def test_connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(target=background_thread, args=session._get_current_object())
    emit('my_response_cd', {'dataPos': 'Connected', 'count': 0})

@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected', request.sid)

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=80, debug=True)
