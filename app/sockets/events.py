from flask_socketio import Namespace, emit, join_room, leave_room
from flask_jwt_extended import decode_token

class UserNamespace(Namespace):
    def on_connect(self):
        # no-op; frontend should authenticate and call 'authenticate' after connect
        pass

    def on_authenticate(self, data):
        # data should contain access_token
        token = data.get('access_token')
        if not token:
            return False
        try:
            decoded = decode_token(token)
            identity = decoded.get('sub')
            user_id = identity.get('user_id')
            join_room(f'user_{user_id}')
            emit('authenticated', {'ok': True})
        except Exception as e:
            emit('authenticated', {'ok': False, 'error': str(e)})

    def on_disconnect(self):
        pass
