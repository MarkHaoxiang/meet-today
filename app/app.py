from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_socketio import SocketIO, send, emit, join_room, leave_room
from flask_mysqldb import MySQL
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, PasswordField, SubmitField, validators
from passlib.hash import pbkdf2_sha256


app = Flask(__name__)
#Init
mysql = MySQL(app)
socketio = SocketIO(app)
#Config
key = 'YEK_TERCES'
app.config['SECRET_KEY'] = key
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_DB'] = 'meettoday'

#=======================================================SPACER=============================================================#

@socketio.on('msg')
def handleMessage(msg,usr,room):
	emit('msg', (msg,usr), room=room,broadcast=True)

@socketio.on('join')
def on_join(room):
    join_room(room)

#=======================================================SPACER=============================================================#

class EntryForm(FlaskForm):
    uname = StringField("Username",[validators.Length(min=4,max=30)])
    email = StringField("Email",[validators.Email()])
    pwd = PasswordField('Password',[
        validators.DataRequired(),
        validators.EqualTo('pwdc')
        ])
    pwdc = PasswordField('Confirm Password')
    submit1 = SubmitField('Register')

class LoginForm(FlaskForm):
    uname = StringField("Username",[validators.Length(min=4,max=30)])
    pwd = PasswordField('Password',[validators.DataRequired()])
    submit2 = SubmitField('Login')

class UnameForm(FlaskForm):
    uname = StringField("Username",[validators.Length(min=1,max=30)])
    submit3 = SubmitField('Join chat')

#=======================================================SPACER=============================================================#

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/dashboard')
def account():
    #Check if user is logged in
    try:
        session['logged_in']
    except:
        flash('You have to login first before creating a meet room!', 'danger')
        return redirect(url_for('entry'))
    if not session['logged_in']:
        flash('You have to login first before creating a meet room!', 'danger')
        return redirect(url_for('entry'))
    uname = session['user']
    cur = mysql.connect.cursor()
    cur.execute('SELECT*FROM users WHERE username=%s',(uname,))
    user = cur.fetchone()
    cur.close()
    id = user[0]
    email = user[1]
    date = user[4]
    return render_template("dashboard.html",uname=uname,id=id,email=email,date=date)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged Out', 'success')
    return redirect(url_for('entry'))


@app.route('/chat')
def join():
    return render_template("join.html")

@app.route('/chat/<string:id>',methods=['GET','POST'])
def chat(id):
    unameForm = UnameForm()
    try:
        session['username']
        if session['username'] == None:
            try:
                if session['logged_in']:
                    session['username'] = session["user"]
                else:
                    session['username'] = None
            except:
                session['username']= None
    except:
        try:
            if session['logged_in']:
                session['username'] = session["user"]
            else:
                session['username'] = None
        except:
            session['username']= None

    if unameForm.submit3.data and unameForm.validate_on_submit():
        session['username'] = unameForm.uname.data
        return redirect(url_for('chat',id=id))
    username = session['username']
    return render_template("chat.html",id=id,username=username,unameForm=unameForm)

@app.route('/entry',methods=['GET','POST'])
def entry():
    #register
    entryForm = EntryForm()
    loginForm = LoginForm()
    #login
    if loginForm.submit2.data and loginForm.validate_on_submit():
        uname = loginForm.uname.data
        inputpwd = loginForm.pwd.data
        cur = mysql.connect.cursor()
        cur.execute('SELECT*FROM users WHERE username=%s',(uname,))
        result = cur.fetchone()
        if result != None:
            #get password if user found
            passwordHash = result[3]
            if pbkdf2_sha256.verify(inputpwd+key,passwordHash):
                session['logged_in'] = True
                session['user'] = uname
                return redirect(url_for('account'))
            else:
                flash('Incorrect password', 'danger')
        else:
            flash('User not found', 'danger')

    if entryForm.submit1.data and entryForm.validate_on_submit():
        cur = mysql.connection.cursor()
        uname = entryForm.uname.data
        cur.execute('SELECT*FROM users WHERE username=%s',(uname,))
        result = cur.fetchone()
        print("Registering ", result)
        if result != None:
            flash('Someone has already used this username!', 'danger')
        else:
            email = entryForm.email.data
            pwd = pbkdf2_sha256.hash(str(entryForm.pwd.data + key))
            cur.execute('INSERT INTO users(username,email,password) VALUES (%s,%s,%s)',(uname,email,pwd))
            mysql.connection.commit()
            cur.close()
            flash('Awesome! You just registered. Please login.', 'success')
            return redirect(url_for('entry'))

    return render_template("entry.html",entryForm=entryForm,loginForm=loginForm)


if __name__ == '__main__':
    print("Starting")
    socketio.run(app,debug=True)
