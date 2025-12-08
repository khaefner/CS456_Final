import csv
import time
import os
import random  # <--- NEW IMPORT
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from flask_httpauth import HTTPDigestAuth

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# --- AUTHENTICATION SETUP ---
auth = HTTPDigestAuth()

@auth.get_password
def get_password(username):
    try:
        with open('.auth', 'r') as f:
            for line in f:
                line = line.strip()
                if ':' in line:
                    user, pw = line.split(':', 1)
                    if user == username:
                        return pw
    except FileNotFoundError:
        print("ERROR: .auth file missing!")
        return None
    return None

# --- Global Game State ---
players = {}
questions = []
current_question_idx = -1
question_start_time = 0 

# --- Load CSV ---
def load_questions():
    q_list = []
    answer_map = {'1': 'A', '2': 'B', '3': 'C', '4': 'D'}
    try:
        with open('final.csv', 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cleaned_row = {
                    'question': row['Question'],
                    'option_a': row['Answer 1'],
                    'option_b': row['Answer 2'],
                    'option_c': row['Answer 3'],
                    'option_d': row['Answer 4'],
                    'correct_answer': answer_map.get(str(row['Correct Answer']).strip(), 'A'),
                    'duration': int(row.get('Time (sec)', 30))
                }
                q_list.append(cleaned_row)
        print(f"DEBUG: Successfully loaded {len(q_list)} questions.")
    except Exception as e:
        print(f"ERROR loading CSV: {e}")
    return q_list

questions = load_questions()

# --- Helper: Reveal Answers ---
def reveal_answers():
    for sid in players:
        if players[sid]['last_answer_status'] == 'waiting':
             players[sid]['last_answer_status'] = 'incorrect'
             players[sid]['pending_score'] = 0
        
        players[sid]['score'] += players[sid]['pending_score']
        
        if players[sid]['pending_score'] > 0:
            players[sid]['last_answer_status'] = 'correct'
        else:
            players[sid]['last_answer_status'] = 'incorrect'
            
    emit('round_over', players, broadcast=True)

# --- Routes ---
@app.route('/')
def player_view(): 
    return render_template('player.html')

@app.route('/host')
@auth.login_required
def host_view(): 
    return render_template('host.html')

# --- Socket Events ---
@socketio.on('join_game')
def handle_join(data):
    # 1. Truncate to 10 characters
    base_name = data['name'][:10]
    username = base_name

    # 2. Check for duplicates and resolve
    existing_names = [p['name'] for p in players.values()]
    while username in existing_names:
        username = f"{base_name}{random.randint(10, 99)}"
    
    # 3. Add player with Avatar (Default to '1' if missing)
    selected_avatar = data.get('avatar', '1') 
    
    players[request.sid] = {
        'name': username, 
        'avatar': selected_avatar,  # <--- NEW FIELD
        'score': 0, 
        'last_answer_status': 'waiting', 
        'pending_score': 0
    }
    emit('update_player_list', players, broadcast=True)

@socketio.on('next_question')
def handle_next_question():
    global current_question_idx, question_start_time
    current_question_idx += 1
    
    # 1. Reset Player State
    for sid in players:
        players[sid]['last_answer_status'] = 'waiting'
        players[sid]['pending_score'] = 0
    
    emit('reset_round', broadcast=True)

    # 2. Send Question and START TIMER
    if current_question_idx < len(questions):
        q = questions[current_question_idx]
        question_start_time = time.time() 
        emit('new_question', q, broadcast=True)
    else:
        emit('game_over', players, broadcast=True)

@socketio.on('request_leaderboard')
def handle_leaderboard_request():
    sorted_players = sorted(players.values(), key=lambda x: x['score'], reverse=True)
    emit('show_leaderboard', sorted_players[:5], broadcast=True)

@socketio.on('time_up')
def handle_time_up():
    reveal_answers()

@socketio.on('submit_answer')
def handle_answer(data):
    if request.sid not in players: return
    if players[request.sid]['last_answer_status'] != 'waiting': return 

    players[request.sid]['last_answer_status'] = 'answered'
    
    if 0 <= current_question_idx < len(questions):
        q = questions[current_question_idx]
        correct = q['correct_answer']
        
        if data['answer'] == correct:
            duration = q['duration']
            time_taken = time.time() - question_start_time
            time_taken = max(0, min(time_taken, duration))
            score_calc = 1000 * (1 - ((time_taken / duration) / 2))
            
            players[request.sid]['pending_score'] = int(score_calc)
        else:
            players[request.sid]['pending_score'] = 0

    total = len(players)
    answered_count = sum(1 for p in players.values() if p['last_answer_status'] != 'waiting')
    
    emit('update_answer_count', {'count': answered_count, 'total': total}, broadcast=True)
    
    if answered_count == total:
        reveal_answers()

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0')
