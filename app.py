from flask import Flask, render_template, send_from_directory
import subprocess
import sys
import os

app = Flask(__name__)
panda_proc = None

# Get the directory where app.py lives
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/')
def index():
    return render_template('index.html')

# New Route: Serve the celebration sound file
@app.route('/celebrate.mp3')
def serve_sound():
    return send_from_directory(BASE_DIR, 'celebrate.mp3')

@app.route('/start')
def start():
    global panda_proc
    # Launching your engine script
    if panda_proc is None or panda_proc.poll() is not None:
        panda_proc = subprocess.Popen([sys.executable, "panda_engine.py"])
    return {"status": "success"}

@app.route('/stop')
def stop():
    global panda_proc
    if panda_proc:
        panda_proc.terminate()
        panda_proc = None
    return {"status": "success"}

if __name__ == '__main__':
    # Ensure app runs on port 5000
    app.run(port=5000, debug=True)