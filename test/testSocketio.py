from flask import Flask,render_template
from flask_socketio import SocketIO
from flask_socketio import send,emit

import time
import hashlib
app=Flask(__name__)
app.config['SECRET_KEY']='secret!'
socketio = SocketIO(app)

@socketio.on('message')
def handle_message(message):
  print('received message:'+message)
  send("hello "+message)
  
@socketio.on('json')
def handle_json(json):
  print('received json:'+str(json))
  send({"a":1,"b":2},json=True)
  
@socketio.on('my event')
def handle_my_eustom_event(json):
  print('received my event json:'+str(json),type(json))
  emit('my response',{"x":"abc","y":999})
  for i in range(100):
    emit('idx',{"idx":i})
    emit('idx1',hashlib.sha256(str(i).encode()).hexdigest())
    time.sleep(0.5)  
@app.route('/index',methods=['GET'])
def react():
  return render_template('index.html',data="youht")

@app.route('/hello',methods=['GET'])
def react():
  return render_template('index.html',data="youht")

if __name__ == '__main__':
  socketio.run(app,host='0.0.0.0',debug=True,port=5000)
  #app.run(host="0.0.0.0")