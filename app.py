from flask import Flask, render_template, request
import csv, os, json
import numpy as np
from datetime import datetime

app = Flask(__name__)

USER_FILE = "users.csv"
KEY_FILE = "typing_data.csv"

def init_files():
    if not os.path.exists(USER_FILE):
        with open(USER_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["username", "password"])
    if not os.path.exists(KEY_FILE):
        with open(KEY_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["username","key","press_time","release_time","duration","flight_time","timestamp"])
    

init_files()

def save_keystrokes(username, keystrokes_list):
    # keystrokes_list is a list of multiple attempts
    with open(KEY_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        for attempt in keystrokes_list:
            for k in attempt:
                writer.writerow([
                    username,
                    k.get("key",""),
                    k.get("press_time",""),
                    k.get("release_time",""),
                    k.get("duration",""),
                    k.get("flight_time",""),
                    k.get("timestamp","")
                ])

def load_features(username):
    feats = []
    with open(KEY_FILE, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["username"] == username:
                try:
                    d = float(row["duration"])
                    ftime = float(row["flight_time"])
                    feats.append([d, ftime])
                except:
                    continue
    return feats

def verify_typing(username, attempt_keystrokes):
    """
    Returns: (typing_ok: bool, message: str, distance: float|None)
    """
    stored = load_features(username)
    if len(stored) == 0:
        return False, "No keystroke profile found for this user.", None

    attempt = []
    for k in attempt_keystrokes:
        try:
            d = float(k.get("duration",0))
            ft = float(k.get("flight_time",0))
            attempt.append([d, ft])
        except:
            continue
    if len(attempt) == 0:
        return False, "No valid keystroke features captured.", None

    stored_mean = np.mean(stored, axis=0)
    attempt_mean = np.mean(attempt, axis=0)
    dist = float(np.linalg.norm(stored_mean - attempt_mean))
    threshold = 50.0
    if dist < threshold:
        return True, f"Access Granted ✅ (distance={dist:.2f})", dist
    else:
        return False, f"Access Denied ❌ (distance={dist:.2f})", dist

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        all_timings_raw = request.form.get('all_timings', '[]')
        try:
            all_timings = json.loads(all_timings_raw)
        except:
            all_timings = []

        # Save credentials
        with open(USER_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([username, password])

        # Save keystrokes
        save_keystrokes(username, all_timings)
        return render_template('success.html', username=username, msg=f"User {username} registered successfully!")
    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    timings_raw = request.form.get('timings', '[]')
    try:
        timings = json.loads(timings_raw)
    except:
        timings = []
    # Verify credentials
    credentials_match = False
    with open(USER_FILE, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['username'] == username and row['password'] == password:
                credentials_match = True
                break

    # Default values for logging
    typing_ok = False
    typing_msg = "No typing verification performed."
    distance = None

    if not credentials_match:
        typing_msg = "Invalid username or password ❌"
        return render_template('success.html', username=username, msg=typing_msg)

    # Credentials matched: verify typing
    typing_ok, typing_msg, distance = verify_typing(username, timings)

    # (logging of attempts was removed to avoid creating extra files)

    return render_template('success.html', username=username, msg=typing_msg)

if __name__ == '__main__':
    app.run(debug=True)
