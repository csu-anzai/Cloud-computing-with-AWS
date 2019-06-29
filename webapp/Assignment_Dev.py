from flask import (Flask,
    request,
    jsonify, url_for)
from flask_sqlalchemy import SQLAlchemy
from flaskext.mysql import MySQL
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
import boto3
import os
aws_s3_bucket_name = os.environ['S3_BUCKET_NAME']

policy = PasswordPolicy.from_names(
    length=8,
    uppercase=0,  # need min. 0 uppercase letters
    numbers=0,  # need min. 0 digits
    special=0,  # need min. 0 special characters
    nonletters=0,  # need min. 0 non-letter characters (digits, specials, anything)
    strength=0.1  # need a password that scores at least 0.3 with its strength
)

"""
    UPLOAD FOLDER TO AWS S3 BUCKET
"""
# def upload_on_s3(path):
#     session = boto3.session.Session(
#         aws_access_key_id = os.environ['AWS_ACCESS_KEY'],
#         aws_secret_access_key = os.environ['AWS_SECRET_ACCESS_KEY_ID'],
#         region_name = os.environ['AWS_REGION_NAME'])
        
#     s3 = session.resource("s3")
#     bucket = s3.Bucket(aws_s3_bucket_name)
#     print("bucket : ", bucket)

#     print("path : ", os.walk(path))

#     for subdir, dirs, files in os.walk(path):
#         print("for 1")
#         for file in files:
#             print("for 2")
#             full_path = os.path.join(subdir, file)
#             print("for 3". full_path)
#             with open(full_path, 'rb') as data:
#                 bucket.put_object(key = full_path[len(path)+1:],Body=data)

# def upload_on_s3( filename ):

#     print("filename inupload: ", os.path.dirname(__file__) + "Images"+ "/" + filename)
#     key_filename = "Images"+ "/" + filename
#     print(key_filename)
#     filename = filename

#     s3 = boto3.client(
#         "s3",
#         aws_access_key_id = os.environ['AWS_ACCESS_KEY'],
#         aws_secret_access_key = os.environ['AWS_SECRET_ACCESS_KEY_ID'],
#     )   
#     bucket_resource = s3

#     print("bucket_resource", bucket_resource)

#     bucket_resource.upload_file(
#         Bucket = aws_s3_bucket_name,
#         Filename=filename,
#         Key=key_filename
#     )
#     print("uploAD SUCCESSFULL")

# s3_key = filename
def upload_on_s3(filename):

    s3_key = filename
    print("S# KEY", s3_key)
    bucketName = 'csye6225-su19-deogade.me.csye6225.com'
    outPutName = filename
    s3 = boto3.client("s3")
    s3.upload_file(s3_key,bucketName,outPutName)
    print("UPLOADED")


""" Set salt encoding beginning code"""
salt = b"$2a$12$w40nlebw3XyoZ5Cqke14M."

""" Initiate flask in app """
app = Flask("__name__")

app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'password'
app.config['MYSQL_DATABASE_DB'] = 'MyWebApp'
app.config['MYSQL_DATABASE_HOST'] = '127.0.0.1'

db = MySQL()
db.init_app(app)

conn = db.connect()
cur = conn.cursor()

UPLOAD_FOLDER = os.path.dirname(__file__) + "Images"
#print("upload folder", UPLOAD_FOLDER)

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


""" Initiate database """
# db_path = os.path.join(os.path.dirname(__file__), 'Assignment01-dev-ad.db')
# db_uri = 'sqlite:///{}'.format(db_path)
# app.config['SQLALCHEMY_DATABASE_URI'] = db_uri

""" Create secret key for UUID in database """
app.config['SECRET_KEY'] = 'my_key'
        

""" ROUTE TO ROOT """
@app.route("/")
def index():
    
    """ VERIFYING BASIC AUTH """
    if not request.authorization:
        return jsonify("Unauthorized"), 401

    # cur = db.connection.cursor()
    dbUsername = request.authorization.username
    print("dbUsername",dbUsername)
    # cur.execute("INSERT INTO MyUsers(firstName, lastName) VALUES (%s, %s)", (firstName, lastName))
    conn = db.connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM Person where username=%s", dbUsername)
    user = cur.fetchone()

    # print("**************************",user) 
    # print("**************************",user["username"]) 
    # print("**************************",user["id"])
    print("**************************",user[2])  
    # db.connection.commit()
    

    """ OBTAIN USERNAME AND PASSWORD BY TOKEN FROM DATABASE """
    #user = Person.query.filter_by(username=request.authorization.username).first()
    if not user:
        return jsonify("Unauthorized"), 401
    userData = {}
    
    userData["username"] = user[1]

    userData["password"] = user[2]
    if request.authorization and request.authorization.username == userData["username"] and (bcrypt.checkpw(request.authorization.password.encode('utf-8'),userData["password"].encode('utf-8'))):

        cur.close()
        return jsonify(str(datetime.datetime.now())), 200
    cur.close()
    return jsonify("Unauthorized"), 401

""" REGISTER USER """
@app.route('/user/register', methods=['POST'])
def retrieve_info():
    try:
        if not request.json:
            return jsonify("Bad request"), 400
        try:
            email = request.json.get('username')
            print("email : ",email)
            if not email:
                return jsonify("Bad request"), 400

            """ VERIFY EMAIL """
            is_valid = re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', email)
            if not is_valid:
                return jsonify("Bad email request"), 400
            

            """ VERIFY PASSWORD """
            myPassword = request.json.get('password')
            print("Password : ", myPassword)

            if not myPassword:
                return jsonify("Bad request"), 400

            """ CHECKING STRENGTH OF PASSWORD """
            if policy.test(myPassword):
                return jsonify("Password not strong enough"), 400

            # cur = db.connection.cursor()
            print("cur :", cur)
            cur.execute("SELECT * FROM Person where username=%s", email)
            user = cur.fetchone()
            # print("user : ", len(user))
            



            print("usertype: ", type(user))
            """ CHECKING REPEATED USER """
            if user is not None:
                return jsonify("User already exists"), 200

            """ HASHING PASSWORD """
            password = bcrypt.hashpw(myPassword.encode('utf-8'), salt)

            """ ADDING USER TO TABLE """
            #test = Person(email, password)

            cur.execute("INSERT INTO Person(id, username, password) VALUES (uuid(), %s, %s)", (email, password))

            print("executed nsert")
            conn.commit()
            cur.close()
            return jsonify('User registered'), 200
        except Exception as e:
            return jsonify(e), 500
    except Exception as e:
        return jsonify(e), 400


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
        userData["username"] = user[1]
        userData["password"] = user[2]

        """ VERIFY TOKEN """
        if bcrypt.checkpw(dataDict["password"].encode('utf-8'), userData["password"]):

            """ OBTAIN BOOK BY ID """
            book = db.session.query(Books).filter_by(id=bookId).first()
            if (book == None):
                return jsonify("No content"), 204

            img_set = db.session.query(Image).filter_by(id=bookId).first()
            print("tesing img",img_set)

            if not img_set:
                print("No imiage")
                db.session.delete(book)
                db.session.commit()

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
        userData["username"] = user[1]
        userData["password"] = user[2] 

        """ VERIFY TOKEN """
        if bcrypt.checkpw(dataDict["password"].encode('utf-8'), userData["password"]):

            print(bookId)

            """ OBTAIN BOOK BY ID """
            book = db.session.query(Books).filter_by(id=bookId).first()

            if (book == None):
                return jsonify("Not found"), 404
            image = db.session.query(Image).filter_by(book_id=bookId).first()
            # print("image : ", image.id)
            if image:
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
            else:
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
                image_array['id'] = ''
                image_array['url'] = ''
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
        userData["username"] = user[1]
        userData["password"] = user[2]  

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
            print("ID", image_data['id'])
            if image_data['id']:
                image.id = image_data['id']
            if image_data['url']:
                image.url = image_data['url']

            
            # print("image id", image.id)
            
            # print("image url", image.url)
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
            # print("IMAGE ID", image)
            if not image:
                image_array['id'] = ''
                image_array['url'] = ''

                json2 = json.dumps(image_array, indent=4)

                print(json2)
                resUm = json.loads(json1)
                print (resUm)
                resUm['Image'] = json.loads(json2)
                return json.dumps(resUm, indent=4), 200

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
        print("header : ", myHeader)

        if (myHeader == None):
            return jsonify("Unauthorized"), 401

        decoded_header = base64.b64decode(myHeader)
        decoded_header_by_utf = decoded_header.decode('utf-8')

        dataDict = {}
        dataDict["username"], dataDict["password"] = decoded_header_by_utf.split(":")
        print("header data dict: ", dataDict)
        # print(dbUsername)

        """ OBTAIN USERNAME AND PASSWORD FROM TOKEN AND DATABASE """
        # print("cur",cur)
        print("username :",dataDict["username"])
        conn = db.connect()
        cur = conn.cursor()
        print("CUR",cur)
        cur.execute("SELECT * FROM Person where username=%s", dataDict["username"])
        user = cur.fetchone()
        print("user : ",user[1])

        # user = Person.query.filter_by(username=dataDict["username"]).first()
        if not user:
            print("User null")
            return jsonify("Unauthorized"), 401

        userData = {}
        userData["username"] = user[1]
        userData["password"] = user[2]
        print(user[2])
        print("user2: ",userData['password'])

        """ VERIFY USER """
        if bcrypt.checkpw(dataDict["password"].encode('utf-8'), userData["password"].encode('utf-8')):
            print("in if")
            if not request.json:
                print("if not json")
                return jsonify("Bad request"), 400
            try:
                print("try")
                """ OBTAIN AND STORE BOOK DETAILS FROM JSON IN DATABSE """
                #book.id = bookId
                book_data = request.get_json()
                
                image_data = book_data['image']
                
                title = book_data['title']
                author = book_data['author']
                isbn = book_data['isbn']
                quantity = book_data['quantity']
        
                print("book", book_data)
                book_id = image_data['id']
                url = image_data['url']
                cur.close()

                #image_id = 

                """ ADD BOOK IN DATABASE """
                # test = Books(title, author, isbn, quantity)
                # print(test)
                # print(url)
                # print(book_id)
                
                # db.session.add(test)
                # print("test added")
                # # db.session.commit()
                # print("Committed")
                # book = db.session.query(Books).filter_by(id=bookId).first()
                # book_id = book.id
                

                if not url:
                    print("Inside")
                    if not book_id:
                        print("in book id")
                        conn = db.connect()
                        cur = conn.cursor()
                        cur.execute("INSERT INTO Books(id, title, author, quantity, isbn) VALUES(uuid(), title, author, quantity, isbn)")
                        # db.session.add(test)
                        # db.session.commit()
                        print("CUR",cur)
                        conn.commit()
                        cur.close()
                        return jsonify("Posted"), 200

                # is not None and book_id is not None:
                # img_set = Image(url)
                # db.session.add(img_set)
                # db.session.commit()
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
                print("no ans")
                return json.dumps(resUm, indent=4), 200
            except Exception as e:
                print("in exception")
                return jsonify("Bad request"), 400
        return jsonify("Unauthorized"), 401
    except Exception as e:
        print("outer exception")
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
        # user = Person.query.filter_by(username=dataDict["username"]).first()
        conn = db.connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM Person where username=%s", dataDict["username"])
        user = cur.fetchone()

        if not user:
            return jsonify("Unauthorized"), 401

        userData = {}
        userData["username"] = user[1]
        userData["password"] = user[2]

        if bcrypt.checkpw(dataDict["password"].encode('utf-8'), userData["password"].encode('utf-8')):

            cur.execute("SELECT * FROM Books")
            books = cur.fetchall()
            cur.execute("SELECT * FROM Image")
            img_es = cur.fetchall()

            # books = db.session.query(Books).all()
            # img_es = db.session.query(Image).all()
            print("****",img_es)
            print("My book:", books)

            output = []
            for book in books:
                if not img_es:
                    bookData = {}
                    bookData["id"] = book[0]
                    bookData["title"] = book[1]
                    bookData["author"] = book[2]
                    bookData["isbn"] = book[3]
                    bookData["quantity"] = book[4]
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
                        bookData["id"] = book[0]
                        bookData["title"] = book[1]
                        bookData["author"] = book[2]
                        bookData["isbn"] = book[3]
                        bookData["quantity"] = book[4]

                        bookData['Image'] = ''
                        json1 = json.dumps(bookData, indent=4)

# return jsonify(output), 200
                        # if img_es.id:
                        if img.book_id==book.id:
                            image_array = {}
                            print("img_es.id ",img[0])
                            image_array["id"] = img[0]
                            image_array["url"] = img[1]
                            image_array["book_id"] = img[2]
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

                            conn.close()
            return jsonify(output), 200

            print("first try end")

                # return jsonify(), 201
        return jsonify("Unauthorized"), 401
    except Exception as e:
        print("first try exception")
        return jsonify(e), 500


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


""" Upload book image """
@app.route("/book/<string:id>/image", methods=["POST"])
def upload_image(id):

    conn = db.connect()
    cur = conn.cursor()

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


    cur.execute("SELECT * FROM Person where username=%s", dataDict["username"])
    user = cur.fetchone()

    if not user:
        return jsonify("Unauthorized"), 401
    userData = {}
    userData["username"] = user[1]
    userData["password"] = user[2]

    """ VERIFY USER """
    if bcrypt.checkpw(dataDict["password"].encode('utf-8'), userData["password"].encode('utf-8')):
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
                    # upload_on_s3

                    print("filename: ",filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    url_for_image = os.path.join(app.config['UPLOAD_FOLDER'], filename)

                    print("url: ", url_for_image)

                    """ OBTAIN BOOK ID TO COMPARE IN DATABASE """
                    bookId = id
                    if (bookId == None):
                        return jsonify("Bad request"), 400

                    """ OBTAIN BOOK BY ID """
                    cur.execute("SELECT * FROM Books where id=%s", bookId)
                    book = cur.fetchone()
                    # book = db.session.query(Books).filter_by(id=bookId).first()
                    if (book == None):
                        return jsonify("No content"), 204

                    cur.execute("INSERT INTO Image(id, url, book_id) VALUES (uuid(),%s, %s)", (url_for_image, bookId))
                    conn.commit()

                    '''upload image on S_3 bucket'''
                    upload_on_s3(url_for_image)


                    """ ADD IMAGE in table IMAGE"""
                    # img = Image(url_for_image, bookId)
                    # db.session.add(img)
                    # db.session.commit()


                    """ OBTAIN IMAGE FROM IMAGE TABLE USING BOOKID And update Book table with the imageid"""
                    cur.execute("SELECT * FROM Image where book_id=%s", bookId)
                    image = cur.fetchone()

                    # image = db.session.query(Image).filter_by(book_id=bookId).first()
                    print(image)
                    print(image[0])
                    #db.session.commit()

                    print("image id: ", image[0])

                    """ DISPLAY BOOK DETAILS """
                    bookData = {}
                    bookData["id"] = book[0]
                    bookData["title"] = book[1]
                    bookData["author"] = book[2]
                    bookData["isbn"] = book[3]
                    bookData["quantity"] = book[4]
                    bookData['Image'] = ''
                    # output.append(bookData)
                    json1 = json.dumps(bookData, indent=4)

                    image_array = {}
                    image_array['id'] = image[0]
                    #image_array['book_id'] = image.book_id
                    image_array['url'] = image[1]

                    json2 = json.dumps(image_array, indent=4)
                    print(json2)

                   
                    resUm = json.loads(json1)
                    print (resUm)
                    resUm['Image'] = json.loads(json2)
                    #print (json.dumps(res)   
                    cur.close()

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
    userData["username"] = user[1]
    userData["password"] = user[2]

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
        userData["username"] = user[1]
        userData["password"] = user[2]  

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
    # db.create_all()

    """ RUN FLASK APP """
    app.run()

