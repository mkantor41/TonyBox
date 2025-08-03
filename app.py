import os
import sqlite3
import re
from flask import Flask, request, render_template, redirect, url_for
from dotenv import load_dotenv
from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO

load_dotenv()

app = Flask(__name__)
DATABASE = 'nfc_tags.db'
reader = SimpleMFRC522()

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS tags (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tag_id TEXT NOT NULL,
                        spotify_uri TEXT NOT NULL,
                        media_type TEXT NOT NULL,
                        comment TEXT
                    )''')
    conn.commit()
    conn.close()

def extract_uri_and_type(link):
    match = re.search(r"open\.spotify\.com\/(track|album|playlist)\/([a-zA-Z0-9]+)", link)
    if not match:
        return None, None
    media_type, uri_id = match.groups()
    return f"spotify:{media_type}:{uri_id}", media_type

@app.route('/', methods=['GET'])
def index():
    conn = get_db_connection()
    tags = conn.execute('SELECT * FROM tags').fetchall()
    conn.close()
    return render_template('index.html', tags=tags)

@app.route('/add', methods=['POST'])
def add():
    tag_id = request.form['tag_id']
    link = request.form['spotify_link']
    comment = request.form['comment']
    spotify_uri, media_type = extract_uri_and_type(link)
    if not spotify_uri:
        return "Invalid Spotify link", 400

    conn = get_db_connection()
    conn.execute('INSERT INTO tags (tag_id, spotify_uri, media_type, comment) VALUES (?, ?, ?, ?)',
                 (tag_id, spotify_uri, media_type, comment))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/read_tag_id', methods=['GET'])
def read_tag_id():
    try:
        tag_id = reader.read()[0]
        return {'tag_id': str(tag_id)}
    except Exception as e:
        return {'error': str(e)}, 500
    finally:
        GPIO.cleanup()

@app.route('/edit/<int:tag_id>', methods=['POST'])
def edit(tag_id):
    tag_val = request.form['tag_id']
    link = request.form['spotify_link']
    comment = request.form['comment']
    spotify_uri, media_type = extract_uri_and_type(link)
    if not spotify_uri:
        return "Invalid Spotify link", 400

    conn = get_db_connection()
    conn.execute('''
        UPDATE tags SET tag_id = ?, spotify_uri = ?, media_type = ?, comment = ?
        WHERE id = ?
    ''', (tag_val, spotify_uri, media_type, comment, tag_id))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete/<int:tag_id>', methods=['POST'])
def delete_tag(tag_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM tags WHERE id = ?', (tag_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
