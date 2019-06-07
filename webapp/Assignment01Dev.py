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

""" BOOKS TABLE """
class Books(db.Model):
    id = db.Column('id', db.Text(length=36), default=lambda: str(uuid.uuid4()), primary_key=True, unique=True)
    title = db.Column(db.String(100))
    author = db.Column(db.String(100))
    isbn = db.Column(db.String(100))
    quantity = db.Column(db.Integer)
    
    """ CONSTRUCTOR """
    def __init__(self,title, author, isbn, quantity):
        self.title = title
        self.author = author
        self.isbn = isbn
        self.quantity = quantity


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


"""

DELETE A BOOK

"""
@app.route("/book/<string:id>", methods=["DELETE"])
def delete_book(id):
    try:
        bookId = id
        """ AUTHENTICATE BY TOKEN """
        if not request.headers.get('Authorization'):
            return jsonify("Unauthorized"), 401
        # if not request.headers.get('id'):
        #     return jsonify("Unauthorized"), 401

        """ OBTAIN HEADERS """
        myHeader = request.headers["Authorization"]

        
        """ DECODE TOKEN """
        data = base64.b64decode(myHeader)
        newData = data.decode('utf-8')
        dataDict = {}

        """ OBTAIN USERNAME AND PASSWORD FROM TOKEN AND DATABASE """
        dataDict["username"], dataDict["password"] = newData.split(":")
        user = Person.query.filter_by(username=dataDict["username"]).first()

        if not user:
            return jsonify("Unauthorized"), 401
        userData = {}
        userData["username"] = user.username
        userData["password"] = user.password  

        """ VERIFY TOKEN """
        if bcrypt.checkpw(dataDict["password"].encode('utf-8'), userData["password"]):

            """ OBTAIN BOOK BY ID """
            book = db.session.query(Books).filter_by(id=bookId).first()
            if (book == None):
                return jsonify("No content"), 204

            """ DELETE BOOK FROM DATABASE """
            db.session.delete(book)
            db.session.commit()

            return jsonify(''),204
        return jsonify("Unauthorized"), 401
    except Exception as e:
        return jsonify("Unauthorized"), 401

"""

GET BOOK BY ID

"""
@app.route("/book/<string:id>", methods=["GET"])
def request_a_book(id):
    try:
        bookId = id

        """ AUTHENTICATE BY TOKEN """
        if not request.headers.get('Authorization'):
            return jsonify("Unauthorized"), 401
        # if not request.headers.get('id'):
        #     return jsonify("Unauthorized"), 401

        """ OBTAIN HEADERS """
        myHeader = request.headers["Authorization"]


        

        """ DECODE TOKEN """
        data = base64.b64decode(myHeader)
        newData = data.decode('utf-8')
        dataDict = {}

        """ OBTAIN USERNAME AND PASSWORD FROM TOKEN AND DATABASE """
        dataDict["username"], dataDict["password"] = newData.split(":")
        user = Person.query.filter_by(username=dataDict["username"]).first()

        if not user:
            return jsonify("Unauthorized"), 401
        userData = {}
        userData["username"] = user.username
        userData["password"] = user.password  

        """ VERIFY TOKEN """
        if bcrypt.checkpw(dataDict["password"].encode('utf-8'), userData["password"]):

            """ OBTAIN BOOK BY ID """
            book = db.session.query(Books).filter_by(id=bookId).first()
            if (book == None):
                return jsonify("Not found"), 404
            output = []
            bookData = {}
            bookData["id"] = book.id
            bookData["title"] = book.title
            bookData["author"] = book.author
            bookData["isbn"] = book.isbn
            bookData["quantity"] = book.quantity
            output.append(bookData)
            return jsonify(output), 200
        return jsonify("Unauthorized"), 401
    except Exception as e:
        return jsonify("Unauthorized"), 401


"""

UPDATE A BOOK

"""
@app.route("/book", methods=["PUT"])
def update_book():
    try:
        bookId = id
        """ AUTHENTICATE BY TOKEN """
        if not request.headers.get('Authorization'):
            return jsonify("Unauthorized"), 401
        # if not request.headers.get('id'):
        #     return jsonify("Unauthorized"), 401

        """ OBTAIN HEADERS """
        myHeader = request.headers["Authorization"]

        """ DECODE TOKEN """
        data = base64.b64decode(myHeader)
        newData = data.decode('utf-8')
        dataDict = {}

        """ OBTAIN USERNAME AND PASSWORD FROM TOKEN AND DATABASE """
        dataDict["username"], dataDict["password"] = newData.split(":")
        user = Person.query.filter_by(username=dataDict["username"]).first()

        if not user:
            return jsonify("Unauthorized"), 401
        userData = {}
        userData["username"] = user.username
        userData["password"] = user.password  

        """ VERIFY TOKEN """
        if bcrypt.checkpw(dataDict["password"].encode('utf-8'), userData["password"]):

            """ OBTAIN BOOK ID TO CPMARE IN DATABASE """
            bookId = request.json.get("id")
            if (bookId == None):
                return jsonify("Bad request"), 400

            """ OBTAIN BOOK BY ID """
            book = db.session.query(Books).filter_by(id=bookId).first()
            if (book == None):
                return jsonify("No content"), 204

            book.id = bookId
            book.title = request.json.get('title')
            book.author = request.json.get('author')
            book.isbn = request.json.get('isbn')
            book.quantity = request.json.get('quantity')
            db.session.commit()

            """ DISPLAY BOOK DETAILS """
            output = []
            bookData = {}
            bookData["id"] = book.id
            bookData["title"] = book.title
            bookData["author"] = book.author
            bookData["isbn"] = book.isbn
            bookData["quantity"] = book.quantity
            output.append(bookData)
            return jsonify(output), 200
        return jsonify("Unauthorized"), 401
    except Exception as e:
        return jsonify("Unauthorized"), 401

""" REGISTER BOOK """
@app.route("/book", methods=["POST"])
def register_book():
    try:

        """ AUTHENTICATE BY TOKEN """
        if not request.headers.get("Authorization"):
            return jsonify("Unauthorized"), 401
        myHeader = request.headers["Authorization"]
        if (myHeader == None):
            return jsonify("Unauthorized"), 401

        decoded_header = base64.b64decode(myHeader)
        decoded_header_by_utf = decoded_header.decode('utf-8')

        dataDict = {}
        dataDict["username"], dataDict["password"] = decoded_header_by_utf.split(":")

        """ OBTAIN USERNAME AND PASSWORD FROM TOKEN AND DATABASE """
        user = Person.query.filter_by(username=dataDict["username"]).first()
        if not user:
            return jsonify("Unauthorized"), 401
        userData = {}
        userData["username"] = user.username
        userData["password"] = user.password

        """ VERIFY USER """
        if bcrypt.checkpw(dataDict["password"].encode('utf-8'), userData["password"]):
            if not request.json:
                jsonify("Bad request"), 400
            try:

                """ OBTAIN AND STORE BOOK DETAILS FROM JSON IN DATABSE """
                title = request.json.get('title')
                if not title:
                    return jsonify("Bad request"), 400
                author = request.json.get('author')

                if not author:
                    return jsonify("Bad request"), 400

                isbn = request.json.get('isbn')
                if not isbn:
                    return jsonify("Bad request"), 400

                quantity = request.json.get('quantity')
                if not quantity:
                    return jsonify("Bad request"), 400

                """ ADD BOOK IN DATABASE """
                test = Books(title, author, isbn, quantity)
                db.session.add(test)
                db.session.commit()
                """ DISPLAY BOOK DETAILS """
                output = []
                bookData = {}
                bookData["id"] = test.id
                bookData["title"] = test.title
                bookData["author"] = test.author
                bookData["isbn"] = test.isbn
                bookData["quantity"] = test.quantity
                output.append(bookData)
                return jsonify(output), 201
            except Exception as e:
                return jsonify("Bad request"), 400
        return jsonify("Unauthorized"), 401
    except Exception as e:
        return jsonify("Unauthorized"), 401



"""

GET ALL BOOKS

"""
@app.route("/book", methods=["GET"])
def request_all_books():
    try:

        """ AUTHENTICATE BY TOKEN """
        if not request.headers.get('Authorization'):
            return jsonify("Unauthorized"), 401

        """ OBTAIN HEADER """
        myHeader = request.headers["Authorization"]
        if (myHeader == None):
            return jsonify("Unauthorized"), 401


        decoded_header = base64.b64decode(myHeader)
        decoded_header_by_utf = decoded_header.decode('utf-8')

        dataDict = {}
        dataDict["username"], dataDict["password"] = decoded_header_by_utf.split(":")

        """ OBTAIN USERNAME AND PASSWORD FROM TOKEN AND DATABASE """
        user = Person.query.filter_by(username=dataDict["username"]).first()
        if not user:
            return jsonify("Unauthorized"), 401

        userData = {}
        userData["username"] = user.username
        userData["password"] = user.password

        if bcrypt.checkpw(dataDict["password"].encode('utf-8'), userData["password"]):
            books = db.session.query(Books).all()

            output = []
            for book in books:
                bookData = {}
                bookData["id"] = book.id
                bookData["title"] = book.title
                bookData["author"] = book.author
                bookData["isbn"] = book.isbn
                bookData["quantity"] = book.quantity
                output.append(bookData)
            return jsonify(output), 200
        return jsonify("Unauthorized"), 401
    except Exception as e:
        return jsonify(e), 500





if __name__ == '__main__':
    
    """ CREATE DATABASE """
    db.create_all()

    """ RUN FLASK APP """
    app.run()
