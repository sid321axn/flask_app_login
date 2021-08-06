from flask import Flask, render_template,flash,request,redirect,session
from flask_mail import Mail,Message
from flask_login import logout_user
from passlib.context import CryptContext
from flaskext.mysql import MySQL
import re
import os
import uuid

app = Flask(__name__)
app.secret_key=os.urandom(24)
mysql = MySQL()

app.config['MYSQL_DATABASE_HOST'] = 'sql5.freesqldatabase.com'
app.config['MYSQL_DATABASE_PORT'] = 3306
app.config['MYSQL_DATABASE_USER'] = 'sql5404675'
app.config['MYSQL_DATABASE_PASSWORD'] = 'ts3vjkUpG3'
app.config['MYSQL_DATABASE_DB'] = 'sql5404675'

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'wisdomml2020@gmail.com'
app.config['MAIL_PASSWORD'] = 'abmzwmqpuksljniv'

pwd_context = CryptContext(
        schemes=["pbkdf2_sha256"],
        default="pbkdf2_sha256",
        pbkdf2_sha256__default_rounds=30000
)
  
mysql.init_app(app)

mail =Mail(app)



@app.route('/')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/home')
def home():
    if 'user_id' in session:
        return render_template('home.html')
    else:
        return redirect('/')

@app.route("/logout")
def logout():
    session.clear()
    return redirect('/')

@app.route('/predict')
def predict():
    if 'user_id' in session:
        return render_template('predict_norm.html')
    else:
        return redirect('/')
    



@app.route('/forgot',methods=["POST","GET"])
def forgot():
    if request.method == "POST":
        email=request.form["email"]
        token = str(uuid.uuid4())
        conn = mysql.connect()
        cursor = conn.cursor()
        result = cursor.execute('SELECT * FROM accounts WHERE email = %s', (email))
        if result>0:
            data = cursor.fetchone()
            msg = Message(subject="Forgot Password Request", sender="wisdomml2020@gmail.com",recipients=[email])
            msg.body = render_template("sent.html",token=token, data=data)
            mail.send(msg)
            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.execute('UPDATE accounts set token=%s WHERE email = %s', (token,email))
            conn.commit()
            cursor.close()
            
            lbl="Kindly check your Email"
            return redirect('/reset')
        else:
            
            lbl="This email is not registered with us"
            return render_template('forgot.html', lbl=lbl)
    
    return render_template('forgot.html')

@app.route('/reset', methods=["POST","GET"])
def reset():
    if request.method == "POST":
        password=request.form["password"]
        confirm_password=request.form["confirm_password"]
        token = request.form["token"]

        if password!= confirm_password:
            flash("Password do not match",'danger')
            return redirect('/reset')
        passencr = pwd_context.encrypt(password)
        token1 = str(uuid.uuid4())
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM accounts WHERE token = %s', (token))
        user = cursor.fetchone()
        if user:
            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.execute('UPDATE accounts set token=%s, password=%s WHERE token = %s', (token1,passencr,token))
            conn.commit()
            cursor.close()
            
            lbl="Your password successfully updated."
            return render_template('login.html', lbl=lbl)
            
        else:
            lbl="Your token is invalid"
            return render_template('reset.html', lbl=lbl)
    
    return render_template('reset.html')


@app.route('/login_validation', methods=['POST'])
def login_validation():
    email = request.form.get('email')
    password = request.form.get('password')
    
    
    conn = mysql.connect()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM accounts WHERE email = %s', (email))
    users = cursor.fetchall()
    hashed = users[0][1]
    print(hashed)
    
    if (len(users)>0) and (pwd_context.verify(password, hashed))==True:
        session['user_id']=users[0][0]
        return redirect('/home')
    else:
        err="Username / Password is incorrect"
        return render_template('login.html', err=err)

    return ""

@app.route('/add_user', methods=['POST'])
def add_user():
    conn = mysql.connect()
    cursor = conn.cursor()

    username=request.form.get('uusername')
    mail = request.form.get('uemail')
    passw = request.form.get('upassword')
    passw = pwd_context.encrypt(passw)
    
    cursor.execute('SELECT * FROM accounts WHERE email = %s', (mail))
    account = cursor.fetchone()
        # If account exists show error and validation checks
    msg=""
    if account:
        msg = 'Account already exists!'
    elif not re.match(r'[^@]+@[^@]+\.[^@]+', mail):
        msg = 'Invalid email address!'
    elif not re.match(r'[A-Za-z0-9]+', username):
        msg = 'Username must contain only characters and numbers!'
    
    else:
        cursor.execute('INSERT INTO accounts VALUES ( %s, %s, %s)', (username, passw, mail))
        conn.commit()
        cursor.close()
        msg='User registered successfully'
    return render_template('register.html', msg=msg)



if __name__ == "__main__":
    app.run(debug=True)