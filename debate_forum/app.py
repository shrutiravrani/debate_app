from flask import Flask, render_template, redirect, url_for, flash, request, session, g, jsonify
import sqlite3
from hashlib import sha256
import time
import os

# Configuration
DATABASE = 'database.db'
SECRET_KEY = 'my_secret_key'

# Flask application setup
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

# Database connection
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row  # This allows accessing columns by name
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    try:
        cur = get_db().execute(query, args)
        rv = cur.fetchall()
        cur.close()
        return (rv[0] if rv else None) if one else rv
    except Exception as e:
        app.logger.error(f"Error querying database: {e}")
        return None

def insert_db(query, args=()):
    try:
        db = get_db()
        cur = db.execute(query, args)
        db.commit()
        return cur.lastrowid
    except Exception as e:
        app.logger.error(f"Error inserting into database: {e}")
        return None

# Routes
@app.route('/')
def index():
    topics = query_db('''
        SELECT t.topicID, t.topicName, u.userName, datetime(t.creationTime, 'unixepoch') 
        FROM topic t
        JOIN "user" u ON t.postingUser = u.userID
        ORDER BY t.creationTime DESC
    ''')
    return render_template('index.html', topics=topics)


@app.route('/topic/<int:topic_id>')
def topic(topic_id):
    topic = query_db('SELECT topicID, topicName FROM topic WHERE topicID = ?', [topic_id], one=True)
    claims = query_db('''
        SELECT c.claimID, c.text, u.userName, datetime(c.creationTime, 'unixepoch') as creationTime
        FROM claim c
        JOIN "user" u ON c.postingUser = u.userID
        WHERE c.topic = ?
        ORDER BY c.updateTime DESC
    ''', [topic_id])
    return render_template('topic.html', topic=topic, claims=claims)


@app.route('/add_topic', methods=['POST'])
def add_topic():
    try:
        topic_name = request.form['topicName']
        user_id = session.get('user_id')
        if user_id:
            topic_id = insert_db('INSERT INTO topic (topicName, postingUser, creationTime, updateTime) VALUES (?, ?, ?, ?)',
                                 [topic_name, user_id, int(time.time()), int(time.time())])
            username = query_db('SELECT userName FROM user WHERE userID = ?', [user_id], one=True)['userName']
            return jsonify({'topicID': topic_id, 'topicName': topic_name, 'username': username, 'postedAt': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time()))})
        return jsonify({'error': 'Unauthorized'}), 403
    except Exception as e:
        app.logger.error(f"Error adding topic: {e}")
        return jsonify({'error': str(e)}), 500

@app.template_filter('datetimeformat')
def datetimeformat(value, format='%Y-%m-%d %H:%M:%S'):
    return time.strftime(format, time.localtime(value))

@app.route('/add_claim', methods=['POST'])
def add_claim():
    try:
        claim_text = request.form['claimText']
        topic_id = request.form['topicID']
        user_id = session.get('user_id')
        if user_id:
            claim_id = insert_db('INSERT INTO claim (topic, postingUser, creationTime, updateTime, text) VALUES (?, ?, ?, ?, ?)',
                                 [topic_id, user_id, int(time.time()), int(time.time()), claim_text])
            username = query_db('SELECT userName FROM "user" WHERE userID = ?', [user_id], one=True)['userName']
            return jsonify({'claimID': claim_id, 'claimText': claim_text, 'username': username, 'postedAt': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time()))})
        return jsonify({'error': 'Unauthorized'}), 403
    except Exception as e:
        app.logger.error(f"Error adding claim: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/claim/<int:claim_id>')
def claim(claim_id):
    claim = query_db('SELECT claimID, text, postingUser, creationTime FROM claim WHERE claimID = ?', [claim_id], one=True)
    if claim:
        replies = query_db('''
            SELECT r.replyTextID, r.text, u.userName, r.creationTime, rt.claimReplyTypeID, rt.claimReplyType, rr.parent
            FROM replyText r
            JOIN "user" u ON r.postingUser = u.userID
            LEFT JOIN replyToClaim rc ON r.replyTextID = rc.reply
            LEFT JOIN replyToClaimType rt ON rc.replyToClaimRelType = rt.claimReplyTypeID
            LEFT JOIN replyToReply rr ON r.replyTextID = rr.reply
            WHERE rc.claim = ? OR rr.parent IS NOT NULL
            ORDER BY r.creationTime
        ''', [claim_id])
        equivalent_claims = query_db('''
            SELECT c.claimID, c.text, u.userName, c.creationTime
            FROM claim c
            JOIN claimToClaim cc ON c.claimID = cc.second
            JOIN "user" u ON c.postingUser = u.userID
            WHERE cc.first = ? AND cc.claimRelType = 2
        ''', [claim_id])
        opposed_claims = query_db('''
            SELECT c.claimID, c.text, u.userName, c.creationTime
            FROM claim c
            JOIN claimToClaim cc ON c.claimID = cc.second
            JOIN "user" u ON c.postingUser = u.userID
            WHERE cc.first = ? AND cc.claimRelType = 1
        ''', [claim_id])
        return render_template('claim.html', claim=claim, replies=replies, equivalent_claims=equivalent_claims, opposed_claims=opposed_claims)
    return "Claim not found", 404


@app.route('/add_related_claim', methods=['POST'])
def add_related_claim():
    try:
        related_claim_text = request.form['relatedClaimText']
        related_claim_id = request.form['relatedClaimID']
        relationship_type = int(request.form['relationshipType'])
        user_id = session.get('user_id')
        if user_id:
            # Get the topic ID from the related claim
            related_claim = query_db('SELECT topic FROM claim WHERE claimID = ?', [related_claim_id], one=True)
            if related_claim:
                topic_id = related_claim['topic']
                claim_id = insert_db('INSERT INTO claim (topic, postingUser, creationTime, updateTime, text) VALUES (?, ?, ?, ?, ?)',
                                     [topic_id, user_id, int(time.time()), int(time.time()), related_claim_text])
                insert_db('INSERT INTO claimToClaim (first, second, claimRelType) VALUES (?, ?, ?)',
                          [related_claim_id, claim_id, relationship_type])
                return jsonify({'claimID': claim_id, 'claimText': related_claim_text, 'relationshipType': relationship_type})
        return jsonify({'error': 'Unauthorized'}), 403
    except Exception as e:
        app.logger.error(f"Error adding related claim: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/add_reply', methods=['POST'])
def add_reply():
    try:
        reply_text = request.form['replyText']
        claim_id = request.form['claimID']
        reply_type = int(request.form['replyType'])
        parent_reply_id = request.form.get('parentReplyID')
        user_id = session.get('user_id')
        if user_id:
            reply_id = insert_db('INSERT INTO replyText (postingUser, creationTime, text) VALUES (?, ?, ?)',
                                 [user_id, int(time.time()), reply_text])
            if parent_reply_id:
                insert_db('INSERT INTO replyToReply (reply, parent, replyToReplyRelType) VALUES (?, ?, ?)',
                          [reply_id, parent_reply_id, reply_type])
            else:
                insert_db('INSERT INTO replyToClaim (reply, claim, replyToClaimRelType) VALUES (?, ?, ?)',
                          [reply_id, claim_id, reply_type])
            username = query_db('SELECT userName FROM "user" WHERE userID = ?', [user_id], one=True)['userName']
            return jsonify({'replyID': reply_id, 'replyText': reply_text, 'replyType': reply_type, 'username': username, 'postedAt': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time())), 'parentReplyID': parent_reply_id})
        return jsonify({'error': 'Unauthorized'}), 403
    except Exception as e:
        app.logger.error(f"Error adding reply: {e}")
        return jsonify({'error': str(e)}), 500



@app.route('/register', methods=['GET', 'POST'])
def register():
    try:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            password_hash = sha256(password.encode()).hexdigest()
            insert_db('INSERT INTO user (userName, passwordHash, isAdmin, creationTime, lastVisit) VALUES (?, ?, ?, ?, ?)',
                      [username, password_hash, False, int(time.time()), int(time.time())])
            flash('You were successfully registered')
            return redirect(url_for('index'))
        return render_template('register.html')
    except Exception as e:
        app.logger.error(f"Error registering user: {e}")
        return str(e), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            password_hash = sha256(password.encode()).hexdigest()
            user = query_db('SELECT * FROM user WHERE userName = ? AND passwordHash = ?', [username, password_hash], one=True)
            if user:
                session['user_id'] = user['userID']
                session['username'] = user['userName']
                return redirect(url_for('index'))
            else:
                flash('Invalid credentials')
        return render_template('login.html')
    except Exception as e:
        app.logger.error(f"Error logging in: {e}")
        return str(e), 500

@app.route('/logout')
def logout():
    try:
        session.pop('user_id', None)
        session.pop('username', None)
        return redirect(url_for('index'))
    except Exception as e:
        app.logger.error(f"Error logging out: {e}")
        return str(e), 500


# Initialize the database if it does not exist
if not os.path.exists(DATABASE):
    def init_db():
        db = sqlite3.connect(DATABASE)
        cursor = db.cursor()
        with open("dump.sql") as f:
            cursor.executescript(f.read())
        db.commit()
        db.close()

    init_db()

# Run the application
if __name__ == '__main__':
    app.run(debug=True)
