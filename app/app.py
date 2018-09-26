from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_socketio import SocketIO, send, emit, join_room, leave_room
from flask_mysqldb import MySQL
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, PasswordField, SubmitField, validators
import os
import urllib
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
    path = "rooms/"+room+".txt"
    f = open(path, "a")
    f.write(usr + ":::" + msg+"\n")
    f.close()
    emit('msg', (msg,usr), room=room,broadcast=True)

@socketio.on('join')
def on_join(room):
    join_room(room)

@socketio.on('clear')
def clear(usr,room):
    cur = mysql.connect.cursor()
    cur.execute('SELECT author_id FROM rooms WHERE room_name=%s',(room,))
    author = cur.fetchone()
    cur.execute('SELECT id FROM users WHERE username=%s',(usr,))
    creator = cur.fetchone()
    if author == creator:
        open("rooms/"+room+".txt", "w").close()
    cur.close()

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
#Landing Page
def index():
    return render_template("index.html")

#Accounts
@app.route('/dashboard',methods=['GET','POST'])
def account():
    #Check if user is logged in
    url = ""
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
    id = user[0]
    email = user[1]
    date = user[4]
    if request.method=='POST':
        print("Recieved")
        cur = mysql.connection.cursor()
        #Create the room
        data = request.values
        roomName = data["name"]
        roomName = urllib.parse.quote(roomName)
        roomTime = int(data["time"])
        roomAuthor = session['user']
        roomLog = roomName + ".txt"
        if data["public"] == "true":
            roomPublic = True
            print("True")
        else:
            roomPublic = False

        cur.execute('SELECT*FROM rooms WHERE room_name=%s',(roomName,))
        query = cur.fetchone()
        print(query)
        if query == None:
            print("Inserting")
            cur.execute('SELECT id FROM users WHERE username=%s',(roomAuthor,))
            roomAuthorID = cur.fetchone()
            cur.execute('INSERT INTO rooms(author_id,room_name,text,run_time,public) VALUES (%s,%s,%s,%s,%s)',(roomAuthorID,roomName,roomLog,roomTime,roomPublic))
            mysql.connection.commit()
            cur.execute('SELECT*FROM rooms')
            query = cur.fetchall();
            #Create message history
            f = open("rooms/"+roomLog, "w")
            f.close()
            #Delete all rooms over time
            for i in query:
                time = i[5]
                cur.execute('DELETE FROM rooms WHERE start_date < DATE_SUB(NOW(), INTERVAL %s DAY) AND room_id = %s',(time,i[0]))
                mysql.connection.commit()
                if cur.rowcount > 0:
                    path = "rooms/"+i[3]
                    if os.path.exists(path):
                        os.remove(path)
                    else:
                        print("The file does not exist")
            cur.close()
            url = '/chat/'+roomName
        redirect(url_for('account'))
    return render_template("dashboard.html",uname=uname,id=id,email=email,date=date)

#Easy logout
@app.route('/logout')
def logout():
    session.clear()
    flash('Logged Out', 'success')
    return redirect(url_for('entry'))

#List of all public chatrooms/a button to join a chatroom
@app.route('/chat')
def join():
    cur = mysql.connection.cursor()
    cur.execute("SELECT*FROM rooms WHERE public = TRUE")
    publicRooms = cur.fetchall()
    cur.close()
    return render_template("join.html",publicRooms=publicRooms)

#A chat room
@app.route('/invalid')
def invalid():
    return render_template('invalid.html')

@app.route('/chat/<string:id>',methods=['GET','POST'])
def chat(id):
    #Validate if chatroom exists
    text = urllib.parse.quote(id)
    cur = mysql.connection.cursor()
    cur.execute('SELECT*FROM rooms WHERE room_name=%s',(text,))
    result = cur.fetchone()
    if result == None:
        return redirect(url_for('invalid'))
    #Get log of txt
    path = "rooms/"+result[3]
    creator_id = result[1]
    cur.execute('SELECT username FROM users WHERE id=%s',(creator_id,))
    l = cur.fetchone()
    creator = l[0]
    messages = [] #The stored messages of the chat room
    f = open(path, "r")
    for line in f:
        cline = line.split(":::")
        messages.append((cline[0],cline[1]))
    f.close()
    cur.close()
    #Page Forms
    unameForm = UnameForm()
    loggedIn = False
    try:
        if session['logged_in']:
            loggedIn = True
    except:
        loggedIn = False

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
    return render_template("chat.html",id=id,username=username,unameForm=unameForm,messages=messages,loggedIn=loggedIn,creator=creator)


#Login and register
@app.route('/entry',methods=['GET','POST'])
def entry():
    entryForm = EntryForm()
    loginForm = LoginForm()
    #login, must ensure that correct form with loginform.submit2.data
    if loginForm.submit2.data and loginForm.validate_on_submit():
        uname = loginForm.uname.data
        inputpwd = loginForm.pwd.data
        cur = mysql.connect.cursor()
        cur.execute('SELECT*FROM users WHERE username=%s',(uname,))
        result = cur.fetchone()
        if result != None:
            #get password if user found
            passwordHash = result[3]
            #verify password
            if pbkdf2_sha256.verify(inputpwd+key,passwordHash):
                session['logged_in'] = True
                session['user'] = uname
                return redirect(url_for('account'))
            else:
                flash('Incorrect password', 'danger')
        else:
            flash('User not found', 'danger')
            #register
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
    socketio.run(app)
