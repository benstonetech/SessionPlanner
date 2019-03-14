import os

from flask import Flask, flash, jsonify, redirect, render_template, request, session,session,url_for, make_response, g
import sqlite3
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
#from flask_session import Session
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from time import gmtime, strftime
import json
from sqlalchemy.ext.serializer import loads, dumps

from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields, pprint
from sqlalchemy_serializer import SerializerMixin
import datetime
import psycopg2



# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"


app.config['SQLALCHEMY_DATABASE_URI'] =  os.environ.get('DATABASE_URI')
app.secret_key = os.environ.get('SECRET_KEY')
test= os.environ.get('S3_KEY')
#Session(app)
g.test = test
db = SQLAlchemy(app)
migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)

class users(db.Model):
    uid = db.Column('uid', db.Integer, primary_key = True)
    uname = db.Column(db.String(200))
    uemail = db.Column(db.String(100))
    uhash = db.Column(db.String(200))  
    uadmin = db.Column(db.String(200))
  

    def __init__(self, uname,uemail, uhash, uadmin):
        self.uname = uname
        self.uemail = uemail
        self.uhash = uhash
        self.uadmin = uadmin

class exercises(db.Model, SerializerMixin):
    eid = db.Column('eid', db.Integer, primary_key = True)
    ename = db.Column(db.String(100))
    edesc = db.Column(db.String(1000))
    esets = db.Column(db.Integer)
    ereptype = db.Column(db.String(100))
    ereps = db.Column(db.Integer)
    def to_json(self):
        return dict(eid=self.eid, ename=self.ename,
                edesc=self.edesc, esets = self.esets, ereptype=self.ereptype,ereps = self.ereps)

def __init__(self,ename,edesc,esets,ereptype,ereps):
    self.ename = ename
    self.edesc = edesc
    self.esets = esets
    self.ereptype = ereptype
    self.ereps = ereps

class exerciseSchema(Schema):
    eid = fields.Integer()
    ename = fields.String()
    edesc = fields.String()
    esets = fields.Integer()
    ereptype = fields.String()
    ereps = fields.Integer()

class anon(db.Model):
   id = db.Column('id', db.Integer, primary_key = True)
   timestamp = db.Column('timestamp', db.DateTime)
   
   def __init__(self, timestamp):
       self.timestamp = timestamp

app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RTY'

@app.route("/")
def index():
    c_logged_in = request.cookies.get('c_logged_in')
    c_user_id = request.cookies.get('c_user_id')

    g.c_logged_in = c_logged_in

    return render_template("index.html", rule=request.url_rule)

@app.route("/anon")
def anon_login():
    new_anon = anon(
        datetime.datetime.now()
    )
    db.session.add(new_anon)
    db.session.commit()

    resp = make_response(redirect("/session"))
    resp.set_cookie('c_user_id','Guest')
    resp.set_cookie('c_logged_in', 'True')
    
    g.c_logged_in = 'True'
    return resp

@app.route("/login", methods=["GET", "POST"])
def login():
    
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Query database for username
        
        user = users.query.filter_by(uemail=request.form.get("email")).first()
        # Ensure username exists and password is correct
        if user == None:
            flash("Error signing in email", "danger")
            return redirect("/")
        elif not check_password_hash(user.uhash, request.form.get("password")):
            flash("Error signing in", "danger")
            return redirect("/")
        else:
            resp = make_response(redirect("/session"))
            resp.set_cookie('c_user_id',str(user.uid))
            resp.set_cookie('c_logged_in', 'True')
            
            g.c_logged_in = 'True'
            return resp
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return redirect("/logout")


@app.route("/logout", methods=["GET", "POST"])
def logout():
    resp = make_response(redirect("/"))
    
    resp.set_cookie('c_user_id', expires=0)
    resp.set_cookie('c_logged_in', expires=0)

    g.c_logged_in = 'False'

    return resp

@app.route("/register", methods=["GET", "POST"])
def register():
    
    if request.method == "POST":
        
        errors = []
        uname = request.form.get("name")

        if uname != "":
            uname_valid = 1


        uemail_exists = []
        uemail = request.form.get("email")
        uemail_exists = users.query.filter_by(uemail = uemail).all()

        if len(uemail_exists) != 0 :
            uemail_valid = 0
        else:
            uemail_valid = 1

        # Check the password fields match
        password = request.form.get("password")
        confirm_password = request.form.get("confirmation")

        if password == confirm_password:
            # Hash the password
            hashed_password = generate_password_hash(password)
            print("Hashed Password:" + hashed_password)

            pass_valid = 1
        else:
            pass_valid = 0

        # Update the database
        if uname_valid == 1 and uemail_valid == 1 and pass_valid == 1:
            
            new_user = users(
                uname,uemail,hashed_password,0
            )
            db.session.add(new_user)
            db.session.commit()
            user = users.query.filter_by(uemail = uemail).one()


            resp = make_response(redirect("/session"))
    
            resp.set_cookie('c_user_id', str(user.uid))
            resp.set_cookie('c_logged_in', 'True')

            g.c_logged_in = 'True'

            return resp
        # Redirect to the homescreen
            return redirect("/")
        else:
            flash("There was an error with your sign up", "danger")
            return redirect("/")
    else:
        return render_template("register.html")


@app.route("/session")
def trainingSession():
    c_logged_in = request.cookies.get('c_logged_in')
    c_user_id = request.cookies.get('c_user_id')

    g.c_logged_in = c_logged_in
    
    _exercises = exercises.query.all()
    e_schema = exerciseSchema(many=True)
    
    Exercises = e_schema.dump(_exercises) 
    
    print(Exercises)
    return render_template("session.html",exercises=Exercises)


@app.route("/admin")
def adminInterface():

    return render_template("admin.html")

@app.route("/createexercise", methods=["POST"])
def createExercise():
    ename = request.form.get("ename")
    edesc = request.form.get("edesc")
    esets = request.form.get("esets")
    ereptype = request.form.get("ereptype")
    ereps = request.form.get("ereps")

    #TODO: Add validation to the inputs
    db.execute("INSERT INTO exercises VALUES(NULL,:ename,:edesc,:esets,:ereptype, :ereps)", ename=ename,edesc=edesc, esets=esets,ereptype=ereptype,ereps=ereps)

    return redirect("/admin")

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    # return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)


if __name__ == '__main__':
    manager.run()
    db.create_all()


