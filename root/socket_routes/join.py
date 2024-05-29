from root.app import socketio
import os
from dotenv import load_dotenv
load_dotenv()
import jwt
from flask_socketio import emit,join_room
from root.auth.check import token_auth



@socketio.on('join')
def on_join(data):
    if "token" not in data  or "roomCode" not in data or not data:
        print("no data")
    token = data["token"]
    room = data['roomCode']
    if not token_auth(token):
        roomid = "message"
        join_room(room)
        emit(roomid, {"error":"Wrong token provided"},room=room)
        return "Failure"
    username = data['userName']
    encoded = jwt.encode({"outletName": username},'test@123', algorithm="HS256")
    join_room(room)
    emit('message', {"message":"Socket connected.","room":room,"username":username,"update_endpoint":encoded}, room=room)

@socketio.on('disconnect')
def on_disconnect():
    print("Client disconnected")