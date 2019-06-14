from flask import (Flask,
    request,
    jsonify, url_for)
from flask_sqlalchemy import SQLAlchemy
import datetime
import sqlite3
import bcrypt
import base64
import uuid
import os
from werkzeug.utils import secure_filename
import json
from password_strength import PasswordPolicy
from password_strength import PasswordStats
import re

policy = PasswordPolicy.from_names(
    length=8,
    uppercase=0,  # need min. 0 uppercase letters
    numbers=0,  # need min. 0 digits
    special=0,  # need min. 0 special characters
    nonletters=0,  # need min. 0 non-letter characters (digits, specials, anything)
    strength=0.1  # need a password that scores at least 0.3 with its strength
)

""" Set salt encoding beginning code"""
salt = b"$2a$12$w40nlebw3XyoZ5Cqke14M."

""" Initiate flask in app """
app = Flask("__name__")

UPLOAD_FOLDER = os.path.dirname(__file__) + "Images"
#print("upload folder", UPLOAD_FOLDER)

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


""" Initiate database """
db_path = os.path.join(os.path.dirname(__file__), 'Assignment01-dev-ad.db')
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
    image_id = db.relationship('Image', backref='books', uselist=False)

    """ CONSTRUCTOR """
    def __init__(self,title, author, isbn, quantity):
        self.title = title
        self.author = author
        self.isbn = isbn
        self.quantity = quantity

""" IMAGE TABLE """
class Image(db.Model):
    id = db.Column('id', db.Text(length=36), default=lambda: str(uuid.uuid4()), primary_key=True, unique=True)
    url = db.Column(db.String(500), unique=True)
    book_id = db.Column(db.Text(length=36), db.ForeignKey('books.id'))

    """ CONSTRUCTOR """
    def __init__(self,url, book_id):
        self.url = url
        self.book_id = book_id
        

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
    return jsonify("Unauthorized"), 401

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

            """ VERIFY EMAIL """
            is_valid = re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', email)
            if not is_valid:
                return jsonify("Bad email request"), 400
            

            """ VERIFY PASSWORD """
            myPassword = request.json.get('password')
            if not myPassword:
                return jsonify("Bad request"), 400

            """ CHECKING STRENGTH OF PASSWORD """
            if policy.test(myPassword):
                return jsonify("Password not strong enough"), 400

            """ CHECKING REPEATED USER """
            if db.session.query(Person.username).filter_by(username=email).scalar() is not None:
                return jsonify("User already exists"), 200

            """ HASHING PASSWORD """
            password = bcrypt.hashpw(myPassword.encode('utf-8'), salt)

            """ ADDING USER TO TABLE """
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
            img_set = db.session.query(Image).filter_by(id=bookId).first()

            """ DELETE BOOK FROM DATABASE """
            db.session.delete(book)
            db.session.commit()
            db.session.delete(img_set)
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

            print(bookId)

            """ OBTAIN BOOK BY ID """
            book = db.session.query(Books).filter_by(id=bookId).first()

            if (book == None):
                return jsonify("Not found"), 404
            image = db.session.query(Image).filter_by(book_id=bookId).first()
            print("image : ", image.id)

            bookData = {}
            bookData["id"] = book.id
            bookData["title"] = book.title
            bookData["author"] = book.author
            bookData["isbn"] = book.isbn
            bookData["quantity"] = book.quantity
            bookData['Image'] = ''
            json1 = json.dumps(bookData, indent=4)

            print("before  image")
            image_array = {}
            image_array['id'] = image.id
            image_array['url'] = image.url
            print("after populate image array")

            json2 = json.dumps(image_array, indent=4)
            resUm = json.loads(json1)
            print("loadd bookr array for image")
            resUm['Image'] = json.loads(json2)
            print("after loading book array with image")
            return json.dumps(resUm, indent=4), 200

        print("intry  exception")
        return jsonify("Unauthorized"), 401
    except Exception as e:
        print("in exception")
        return jsonify("Unauthorized"), 401


"""
UPDATE A BOOK
"""
@app.route("/book", methods=["PUT"])
def update_book():
    try:
        # bookId = id
        """ AUTHENTICATE BY TOKEN """
        if not request.headers.get('Authorization'):
            return jsonify("Unauthorized"), 401

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
            print("book", book)
            if (book == None):
                return jsonify("No content"), 204
            image = db.session.query(Image).filter_by(id=bookId).first()
            print("img", image)
            book.id = bookId
            print(book.id)
            book_data = request.get_json()
            print(book_data)
            image_data = book_data['image']
            book.title = book_data['title']
            print("Bok title", book.title)
            book.author = book_data['author']
            book.isbn = book_data['isbn']
            book.quantity = book_data['quantity']
            print("QUANT", book.quantity)
            print("IMG DATA", image_data)
            image.id = image_data['id']
            print("image id", image.id)
            image.url = image_data['url']
            print("image url", image.url)
            # image.book_id = image_data['book_id']
            db.session.commit()
            print("Committed")

            """ DISPLAY BOOK DETAILS """
            # output = []
            bookData = {}
            print(bookData)
            bookData["id"] = book.id
            print(bookData["id"])
            bookData["title"] = book.title
            bookData["author"] = book.author
            bookData["isbn"] = book.isbn
            bookData["quantity"] = book.quantity
            bookData['Image'] = ''
            json1 = json.dumps(bookData, indent=4)
            print(json1)

            image_array = {}
            image_array['id'] = image.id
            image_array['url'] = image.url

            json2 = json.dumps(image_array, indent=4)

            print(json2)
            resUm = json.loads(json1)
            print (resUm)
            resUm['Image'] = json.loads(json2)
            return json.dumps(resUm, indent=4), 200
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
                print("if not json")
                return jsonify("Bad request"), 400
            try:

                """ OBTAIN AND STORE BOOK DETAILS FROM JSON IN DATABSE """
                #book.id = bookId
                book_data = request.get_json()
                print(book_data)
                image_data = book_data['image']
                print(image_data)
                title = book_data['title']
                print(title)
                author = book_data['author']
                isbn = book_data['isbn']
                quantity = book_data['quantity']
                book_id = image_data['book_id']
                url = image_data['url']

                #image_id = 

                """ ADD BOOK IN DATABASE """
                test = Books(title, author, isbn, quantity)
                print(test)
                print(url)
                print(book_id)

                if not url:
                    print("Inside")
                    if not book_id:
                        print("Beifre dcommitting")
                        db.session.add(test)
                        print("test added")
                        db.session.commit()
                        print("Committed")
                        return jsonify("Posted"), 200

                # is not None and book_id is not None:
                img_set = Image(url, book_id)
                db.session.add(img_set)
                db.session.commit()
                # db.session.add(test)
                # db.session.commit()

                
                

                """ DISPLAY BOOK DETAILS """
                # output = []
                bookData = {}
                print(bookData)
                bookData["id"] = test.id
                bookData["id"]
                bookData["title"] = test.title
                bookData["author"] = test.author
                bookData["isbn"] = test.isbn
                bookData["quantity"] = test.quantity
                bookData['Image'] = ''
                json1 = json.dumps(bookData, indent=4)

                image_array = {}
                image_array['book_id'] = img_set.book_id
                print("Image data for json", image_array)
                image_array['url'] = img_set.url

                json2 = json.dumps(image_array, indent=4)
                print(json2)
                resUm = json.loads(json1)
                print (resUm)
                resUm['Image'] = json.loads(json2)
                return json.dumps(resUm, indent=4), 200
            except Exception as e:
                print("in exception")
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
            img_es = db.session.query(Image).all()
            print("****",img_es)
            print("My book:", books)

            output = []
            for book in books:
                if not img_es:
                    bookData = {}
                    bookData["id"] = book.id
                    bookData["title"] = book.title
                    bookData["author"] = book.author
                    bookData["isbn"] = book.isbn
                    bookData["quantity"] = book.quantity
                    bookData['Image'] = ''
                    json1 = json.dumps(bookData, indent=4)
                    image_array = {}
                    image_array["id"] = ''
                    image_array["url"] = ''
                    json2 = json.dumps(image_array, indent=4)
                    resUm = json.loads(json1)
                    resUm['Image'] = json.loads(json2)
                    jsonFile = json.dumps(resUm)
                    output.append(jsonFile)
            
                else:

                    for img in img_es:

                        bookData = {}
                        bookData["id"] = book.id
                        bookData["title"] = book.title
                        bookData["author"] = book.author
                        bookData["isbn"] = book.isbn
                        bookData["quantity"] = book.quantity
                        bookData['Image'] = ''
                        json1 = json.dumps(bookData, indent=4)

# return jsonify(output), 200
                        # if img_es.id:
                        if img.book_id==book.id:
                            image_array = {}
                            print("img_es.id ",img.id)
                            image_array["id"] = img.id
                            image_array["url"] = img.url
                            image_array["book_id"] = img.book_id
                            json2 = json.dumps(image_array, indent=4)
                            print(json2)
                            resUm = json.loads(json1)
                            print (resUm)
                            resUm['Image'] = json.loads(json2)
                            jsonFile = json.dumps(resUm)
                            output.append(jsonFile)
                            # return json.dumps(resUm, indent=4), 200
                        else:
                            image_array = {}
                            image_array["id"] = ''
                            image_array["url"] = ''
                            json2 = json.dumps(image_array, indent=4)
                            resUm = json.loads(json1)
                            resUm['Image'] = json.loads(json2)
                            jsonFile = json.dumps(resUm)
                            output.append(jsonFile)
            return jsonify(output), 200



                # return jsonify(), 201
        return jsonify("Unauthorized"), 401
    except Exception as e:
        return jsonify(e), 500


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


""" Upload book image """
@app.route("/book/<string:id>/image", methods=["POST"])
def upload_image(id):

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

            print ("in upload_image")
            if 'file' in request.files:
                print("file present")

                file = request.files['file']
                print (file.filename)

                if file.filename == '':
                    print('No selected file')

                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)

                    print("filename: ",filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    url_for_image = os.path.join(app.config['UPLOAD_FOLDER'], filename)

                    print("url: ", url_for_image)

                    """ OBTAIN BOOK ID TO COMPARE IN DATABASE """
                    bookId = id
                    if (bookId == None):
                        return jsonify("Bad request"), 400

                    """ OBTAIN BOOK BY ID """
                    book = db.session.query(Books).filter_by(id=bookId).first()
                    if (book == None):
                        return jsonify("No content"), 204


                    """ ADD IMAGE in table IMAGE"""
                    img = Image(url_for_image, bookId)
                    db.session.add(img)
                    db.session.commit()

                    """ OBTAIN IMAGE FROM IMAGE TABLE USING BOOKID And update Book table with the imageid"""
                    image = db.session.query(Image).filter_by(book_id=bookId).first()
                    print(image)
                    print(image.id)
                    #db.session.commit()

                    print("image id: ", image.id)

                    """ DISPLAY BOOK DETAILS """
                    bookData = {}
                    bookData["id"] = book.id
                    bookData["title"] = book.title
                    bookData["author"] = book.author
                    bookData["isbn"] = book.isbn
                    bookData["quantity"] = book.quantity
                    bookData['Image'] = ''
                    # output.append(bookData)
                    json1 = json.dumps(bookData, indent=4)

                    image_array = {}
                    image_array['id'] = image.id
                    #image_array['book_id'] = image.book_id
                    image_array['url'] = image.url

                    json2 = json.dumps(image_array, indent=4)
                    print(json2)

                   
                    resUm = json.loads(json1)
                    print (resUm)
                    resUm['Image'] = json.loads(json2)
                    #print (json.dumps(res)   
                    

                    return json.dumps(resUm, indent=4), 201
        except Exception as e:
            return jsonify(e), 500



""" UPDATE BOOK IMAGE """
@app.route("/book/<string:id>/image/<string:imgId>", methods=["PUT"])
def update_image(id, imgId):
    bookId = id
    imageId = imgId

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

            print ("in upload_image")
            if 'file' in request.files:
                print("file present")

                file = request.files['file']
                print (file.filename)

                if file.filename == '':
                    print('No selected file')

                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)

                    print("filename: ",filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    url_for_image = os.path.join(app.config['UPLOAD_FOLDER'], filename)

                    print("url: ", url_for_image)

                    """ OBTAIN BOOK ID TO COMPARE IN DATABASE """
                    bookId = id
                    if (bookId == None):
                        return jsonify("Bad request"), 400

                    """ OBTAIN BOOK BY ID """
                    book = db.session.query(Books).filter_by(id=bookId).first()
                    if (book == None):
                        return jsonify("No content"), 204
                    image = db.session.query(Image).filter_by(book_id=bookId).first()

                    image.id = imgId
                    image.url = url_for_image
                    image.book_id = bookId

                    db.session.commit()

                    """ OBTAIN IMAGE FROM IMAGE TABLE USING BOOKID And update Book table with the imageid"""
                    
                    print(image)
                    print(image.id)

                return jsonify('No Content'),204

            return json.dumps(resUm, indent=4), 201
        except Exception as e:
            return jsonify(e), 500


"""
DELETE A IMAGE
"""
@app.route("/book/<string:id>/image/<string:imgId>", methods=["DELETE"])
def delete_image(id, imgId):
    try:
        bookId = id
        imageId = imgId

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
            image = db.session.query(Image).filter_by(id=imgId).first()

            if (image == None):
                return jsonify("No content"), 204

            if (book == None):
                return jsonify("No content"), 204

            if image.book_id == bookId:
                
                """ DELETE BOOK FROM DATABASE """
                db.session.delete(image)
                db.session.commit()


            return jsonify('No Content'),204
        return jsonify("Unauthorized"), 401
    except Exception as e:
        return jsonify("Unauthorized"), 401


"""
GET BOOK IMAGE
"""
@app.route("/book/<string:id>/image/<string:imgId>", methods=["GET"])
def get_book_image(id, imgId):
    try:
        print("in get book image")
        bookId = id
        imageId = imgId

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
            image = db.session.query(Image).filter_by(id=imageId).filter_by(book_id=bookId).first()

            output = []
            image_data = {}
            image_data["id"] = image.id
            image_data["url"] = image.url
            
            output.append(image_data)
                        
            return jsonify(output),200

        return jsonify("Unauthorized"), 401
    except Exception as e:

        print("in exception")
        return jsonify("Unauthorized"), 401




if __name__ == '__main__':
    
    """ CREATE DATABASE """
    db.create_all()

    """ RUN FLASK APP """
    app.run()

