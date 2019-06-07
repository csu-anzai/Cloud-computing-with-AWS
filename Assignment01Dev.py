from flask import (Flask,
    request,
    jsonify)
from flask_sqlalchemy import SQLAlchemy
import datetime
import sqlite3
import bcrypt
import base64
import uuid
import os

""" Set salt encoding beginning code"""
salt = b"$2a$12$w40nlebw3XyoZ5Cqke14M."

""" Initiate flask in app """
app = Flask("__name__")

""" Initiate database """
db_path = os.path.join(os.path.dirname(__file__), 'Assignment01-dev.db')
db_uri = 'sqlite:///{}'.format(db_path)
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri

""" Create secret key for UUID in database """
app.config['SECRET_KEY'] = 'my_key'

""" Initiate sql-alchemy database in db """
db = SQLAlchemy(app)

""" PERSON TABLE """
class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(220), unique=True)
    password = db.Column(db.String(220))
    
    """ CONSTRUCTOR """
    def __init__(self,username, password):
        self.username = username
        self.password = password



""" ROUTE TO ROOT """
@app.route("/")
def index():
    
    """ VERIFYING BASIC AUTH """
    if not request.authorization:
        return jsonify("Unauthorized"), 401

    """ OBTAIN USERNAME AND PASSWORD BY TOKEN FROM DATABASE """
    user = Person.query.filter_by(username=request.authorization.username).first()
    if not user:
        return jsonify("Unauthorized"), 401
    userData = {}
    userData["username"] = user.username
    userData["password"] = user.password
    if request.authorization and request.authorization.username == userData["username"] and (bcrypt.checkpw(request.authorization.password.encode('utf-8'),userData["password"])):
        return jsonify(str(datetime.datetime.now())), 200

""" REGISTER USER """
@app.route('/user/register', methods=['POST'])
def retrieve_info():
    try:
        if not request.json:
            return jsonify("Bad request"), 400
        try:
            email = request.json.get('username')
            if not email:
                return jsonify("Bad request"), 400
            

            """ VERIFY PASSWORD """
            myPassword = request.json.get('password')
            if not myPassword:
                return jsonify("Bad request"), 400
            if db.session.query(Person.username).filter_by(username=email).scalar() is not None:
                return jsonify("User already exists"), 200

            password = bcrypt.hashpw(myPassword.encode('utf-8'), salt)
            test = Person(email, password)
            
            """ REGISTER USER """
            db.session.add(test)
            db.session.commit()
            return jsonify('User registered'), 200
        except Exception as e:
            return jsonify(e), 500
    except:
        return jsonify("Bad request"), 400


if __name__ == '__main__':
    
    """ CREATE DATABASE """
    db.create_all()

    """ RUN FLASK APP """
    app.run()

