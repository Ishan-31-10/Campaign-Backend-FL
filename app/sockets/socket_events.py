from flask_socketio import Namespace, emit, join_room, leave_room
from flask_jwt_extended import decode_token
from flask import current_app

def register(socketio):
    @socketio.on('connect')
    def handle_connect():
        # client should call 'authenticate' with token after connecting
        pass

    @socketio.on('authenticate')
    def handle_auth(data):
        token = data.get('access_token')
        if not token:
            return
        try:
            decoded = decode_token(token)
            identity = decoded.get('sub')
            user_id = identity.get('user_id')
            room = f'user_{user_id}'
            join_room(room)
            emit('authenticated', {'ok': True}, room=room)
        except Exception as e:
            current_app.logger.exception('socket auth failed')
            emit('authenticated', {'ok': False, 'error': str(e)})
