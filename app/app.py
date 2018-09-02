from flask import Flask, render_template
from flask_socketio import SocketIO

app = Flask(__name__)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/login')
def account():
    return render_template("account.html")

if __name__ == '__main__':
    app.run(debug=True)
