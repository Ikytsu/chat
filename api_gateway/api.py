from .db import get_db

import redis
import json
from datetime import datetime

SYSTEM_USER_ID=1

redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

def get_user_name(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT name FROM user WHERE id = ?', (user_id,))
    result = cursor.fetchone()
    if result:
        return result[0]  # Return the user's name
    else:
        return None  # User not found

def send_system_message(room_id, text):
    send_message(room_id, SYSTEM_USER_ID, text)

def get_participants(room_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT user_id FROM participant WHERE room_id = ?', (room_id,))
    return [p[0] for p in cursor.fetchall()]

def send_message(room_id, author_id, text):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('INSERT INTO message (room_id, author_id, text) VALUES (?, ?, ?)', (room_id, author_id, text))
    db.commit()

    message_id = cursor.lastrowid
    cursor.execute('SELECT created_at FROM message WHERE id = ?', (message_id,))
    created_at: datetime = cursor.fetchone()[0]

    enqueue_for_participants(room_id, {
        'message': {
            'room_id': room_id,
            'author_id': author_id,
            'text': text,
            'created_at': created_at.isoformat()
        }
    })
    
def enqueue_for_participants(room_id, event):
    participants = get_participants(room_id)
    for participant_id in participants:
        enqueue_event(participant_id, json.dumps(event))

def enqueue_event(user_id, event):
    redis_client.rpush(f'user:{user_id}', json.dumps(event))