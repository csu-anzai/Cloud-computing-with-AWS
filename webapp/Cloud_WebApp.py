#!/usr/bin/python

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
from botocore.client import Config
import os
import configparser
import logging.config
import mysql.connector
from mysql.connector import Error
import subprocess
from subprocess import call
import json
import statsd
import logging
from flask_statsdclient import StatsDClient
import logging.config
from logging.config import dictConfig


""" Config parser """
config = configparser.ConfigParser()
pathToConfig = "/home/centos/my.cnf"
config.read(pathToConfig)

""" Storing cofig variables in python variables """
local_run = config["Config"]['LOCAL_RUN']
aws_region = config["Config"]["AWS_REGION_NAME"]
print(aws_region)
production_run = config["Config"]['PRODUCTION_RUN']
print(production_run)


""" A password policy """
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

""" Initiate flask in app, db and statsd """
app = Flask("__name__")
db = MySQL()
c = StatsDClient(app)
db.init_app(app)

""" Initiate statsd """
app.config['STATSD_HOST'] = 'localhost'
app.config['STATSD_PORT'] = 8125
app.config['STATSD_PREFIX'] = 'statsd'

""" Initiate database """
if(production_run):
    print("In production_run")
    print(production_run)
    aws_s3_bucket_name = config["Config"]['S3_BUCKET_NAME']
    app.config['MYSQL_DATABASE_USER'] = 'csye6225master'
    app.config['MYSQL_DATABASE_PASSWORD'] = 'csye6225password'
    app.config['MYSQL_DATABASE_DB'] = 'csye6225'
    app.config['MYSQL_DATABASE_HOST'] = config["Config"]['RDS_INSTANCE']


elif(local_run):
    app.config['MYSQL_DATABASE_USER'] = "root"
    app.config['MYSQL_DATABASE_PASSWORD'] = 'password'
    app.config['MYSQL_DATABASE_DB'] = 'csye6225'
    app.config['MYSQL_DATABASE_HOST'] = 'localhost'

""" Logging config """
LOGGING_CONFIG = None
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '{asctime} {levelname} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'default': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename' : '/opt/aws/amazon-cloudwatch-agent/logs/csye6225.log',
            'formatter': 'standard'
        },
    },
    'loggers': {
        '': {
            'handlers': ['default'],
            'propagate': True,
        }
    }
})

logger = logging.getLogger(__name__)
logger.setLevel("INFO")
 
''' IMAGES FOLDER PATH '''
UPLOAD_FOLDER = os.path.dirname(__file__) + "Images"


''' ALLOWED EXTENSIONS FOR UPLOAD ''' 
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

""" Create secret key for UUID in database """
app.config['SECRET_KEY'] = 'my_key'
rds = config["Config"]['RDS_INSTANCE']    
dbUser = config["Config"]['MYSQL_DATABASE_USER']    
dbPass = config["Config"]['MYSQL_DATABASE_PASSWORD'] 
 
""" CREATE DB TABLES """   
rdsInstance = "-h"+rds
dataUser = "-u"+dbUser
dataPass = "-p"+dbPass
# call(["mysql", rdsInstance , dataUser, dataPass, "<", "createScripts.sql"])
print("Database created")

""" Connect to RDS instance """
print("RDS", rds)
try:
    connection = mysql.connector.connect(host=rds,
        user = dbUser,
        password = dbPass,
        database = 'csye6225',
        buffered=True)
    if connection.is_connected():
        print("inside db $$$$$", connection.get_server_info())
except Error as e:
    print("Error", e)



""" Create tables in Database """
def create_database():
    logger.info("Databse creation method initiated")
    print("db", db)
    # conn = connection.connect()

    # print("connect", conn)
    cur = connection.cursor()
    print("cursor", cur)
    cur.execute("show databases")
    # cur.execute("use csye6225")
    cur.execute("CREATE table if not exists Person(id varchar(100) NOT NULL, username varchar(100) DEFAULT NULL, password varchar(100) DEFAULT NULL, PRIMARY KEY ( id ))")

    cur.execute("CREATE table if not exists Books(id varchar(100) NOT NULL, title varchar(50) DEFAULT NULL, author varchar(50) DEFAULT NULL, isbn varchar(50) DEFAULT NULL, quantity varchar(50) DEFAULT NULL, PRIMARY KEY ( id ))")
    cur.execute("CREATE table if not exists Image(id varchar(100) NOT NULL, url varchar(1000) DEFAULT NULL, book_id varchar(100) DEFAULT NULL, PRIMARY KEY ( id ))")
    print("Tables created")
    logger.info("Tables created")



""" UPLOAD IMAGE on S3 """
def upload_on_s3( filename ):
    logger.info("Uploading image on s3")
    print("filename inupload: ", os.path.dirname(__file__) +  filename)

    key_filename = filename
    print(key_filename)

    #filename = filename

    s3 = boto3.client(
        "s3")
        # aws_access_key_id = AWS_ACCESS_KEY,
        # aws_secret_access_key = AWS_SECRET_ACCESS_KEY_ID
    # )   
    bucket_resource = s3

    print("bucket_resource", bucket_resource)

    bucket_resource.upload_file(
        Bucket = aws_s3_bucket_name,
        Filename=filename,
        Key=key_filename
    )
    print("UPLOAD SUCCESSFULL")
    logger.info("Image uploaded in s3")


""" DELETE IMAGE FROM S3 BUCKET """
def delete_image_from_s3( filename ):

    key_filename = filename
    print("key_filename : ", key_filename)

    s3 = boto3.client(
        "s3")
        # aws_access_key_id = AWS_ACCESS_KEY,
        # aws_secret_access_key = AWS_SECRET_ACCESS_KEY_ID
    # )
    bucket_resource = s3
    print("bucket_resource", bucket_resource)
    try:
        # s3.deleteObject(
        #   Bucket= aws_s3_bucket_name,
        #   Key= key_filename
        # ),

        s3.delete_object(
            Bucket = aws_s3_bucket_name,
            Key=key_filename)
    

        print("deleted image from S3")
        logger.info("Image deleted from s3")            
    except Exception as e:
        logger.exception("Exception in image deletion from s3: ", e)
        print("Exception : ",e)



def presignedUrl( filename ):
    filename = filename
    print("filename : ", filename)
    s3_client = boto3.client('s3',
    # aws_access_key_id = AWS_ACCESS_KEY,
    #     aws_secret_access_key = AWS_SECRET_ACCESS_KEY_ID,
         config=Config(signature_version='s3v4'))
    print("s3 client: ", s3_client)
    try:
        print("Bucket name:", aws_s3_bucket_name)
        resp_url = s3_client.generate_presigned_url(
            'get_object',
            Params = {
            'Bucket': aws_s3_bucket_name,
             'Key': filename,
             },
            ExpiresIn = 60*2
        )
        # return resp_url

        print(resp_url)
        logger.info("presigned url generated")
    except Exception as e:
        logger.exception("Exception in presigned url generaiton: ", e)
        print("Exception is:", e)
    logger.info("Presigned url sent")
    return resp_url
    



""" REGISTER USER """
@app.route('/user/register', methods=['POST'])
def register_user():
    c.incr("register_user")
    logger.info("Registering for user")
    try:
        request.get_json()
    except Exception as e:
        logger.exception("Error: ", e)
        return jsonify("Bad request one"), 400
    try:
        if not request.get_json():
            logger.error("Json format error")
            return jsonify("Bad request two"), 400
        try:
            email = request.json.get('username')
            print("email : ",email)
            if not email:
                logger.error("Email not found")
                return jsonify("Bad request"), 400

            """ VERIFY EMAIL """
            is_valid = re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', email)
            if not is_valid:
                logger.error("Invalid email format")
                return jsonify("Bad email request"), 400

            """ VERIFY PASSWORD """
            myPassword = request.json.get('password')
            if not myPassword:
                logger.error("Password not found")
                return jsonify("Bad request"), 400

            """ CHECKING STRENGTH OF PASSWORD """
            if policy.test(myPassword):
                logger.error("Password not strong enough")
                return jsonify("Password not strong enough"), 400

            """ HASHING PASSWORD """
            password = bcrypt.hashpw(myPassword.encode('utf-8'), salt)
            logger.info("Password encrypted")

            """ CHECK IF USER EXISITS """
            conn = db.connect()
            logger.info("Connecting to database")
            cur = conn.cursor()
            logger.info("Creating cursor for database")

            cur.execute("SELECT * FROM Person where username=%s", email)
            logger.info("Fetching user details from database")
            user = cur.fetchone()

            if user is not None:
                logger.error("user already exists")
                return jsonify("User already exists"), 200


            """ ADDING USER TO DATABASE """
            cur.execute("INSERT INTO Person(id, username, password) VALUES (uuid(), %s, %s)", (email, password))
            logger.info("User registration successful")

            conn.commit()
            cur.close()
            logger.info("Database connection closed")

            return jsonify('User registered successfully'), 200
        except Exception as e:
            logger.exception("Exception: ", e)
            return jsonify(e), 500
    except Exception as e:
        logger.exception("Exception: ", e)
        return jsonify(e), 400



""" ROUTE TO ROOT """
@app.route("/")
def index():
    c.incr("api.index")
    logger.info("User request auth")
    
    """ VERIFYING BASIC AUTH """
    if not request.authorization:
        logger.error("Email or password not entered")
        return jsonify("Unauthorized"), 401

    username = request.authorization.username

    conn = db.connect()
    cur = conn.cursor()
    cur.execute("SELECT username, password FROM Person where username=%s", username)
    user = cur.fetchone()
    print("user :", user)

    """ OBTAIN USERNAME AND PASSWORD BY TOKEN FROM DATABASE """
    if not user:
        logger.error("User does not exist in database")
        return jsonify("Unauthorized"), 401

    userData = {}
    userData["username"] = user[0]
    userData["password"] = user[1]


    if request.authorization and request.authorization.username == userData["username"] and (bcrypt.checkpw(request.authorization.password.encode('utf-8'),userData["password"].encode('utf-8'))):
        cur.close()
        logger.info("User authenticated")
        return jsonify(str(datetime.datetime.now())), 200

    cur.close()
    logger.error("User credentials incorrect")
    return jsonify("Unauthorized"), 401



""" REGISTER BOOK """
@app.route("/book", methods=["POST"])
def register_book():
    c.incr("api.register_book")
    logger.info("In api for registering book")
    try:
        """ AUTHENTICATE BY TOKEN """
        if not request.headers.get("Authorization"):
            logger.error("No token available for authentication")
            return jsonify("Unauthorized"), 401

        myHeader = request.headers["Authorization"]

        if (myHeader == None):
            logger.error("Authorization headers unavailable")
            return jsonify("Unauthorized"), 401

        try:
            decoded_header = base64.b64decode(myHeader)
            decoded_header_by_utf = decoded_header.decode('utf-8')
            dataDict = {}
            dataDict["username"], dataDict["password"] = decoded_header_by_utf.split(":")
        except Exception as e:
            logger.exception("Exception in bs4 decoding:", e)
            return jsonify("Bad headers"), 401
        print("header data dict: ", dataDict)

        """ OBTAIN USERNAME AND PASSWORD FROM TOKEN AND DATABASE """
        conn = db.connect()
        cur = conn.cursor()

        cur.execute("SELECT username, password FROM Person where username=%s", dataDict["username"])
        user = cur.fetchone()
        logger.info("Fetching user from database")
        print("user : ", user)

        if not user:
            logger.error("User not found")
            return jsonify("Unauthorized"), 401

        userData = {}
        userData["username"] = user[0]
        userData["password"] = user[1]

        """ VERIFY USER """
        if bcrypt.checkpw(dataDict["password"].encode('utf-8'), userData["password"].encode('utf-8')):
            logger.info("User verified")
            if not request.json:
                logger.error("Book details not entered in proper format")
                return jsonify("Bad request"), 400
            try:
                """ OBTAIN AND STORE BOOK DETAILS FROM JSON IN DATABSE """
                logger.info("Obtaining book data")

                book_data = request.get_json()
                image_data = book_data['image']
                
                title = book_data['title']
                author = book_data['author']
                isbn = book_data['isbn']
                quantity = book_data['quantity']
        
                book_id = image_data['id']
                url = image_data['url']

                if not url:
                    if not book_id:
                        conn = db.connect()
                        cur = conn.cursor()

                        cur.execute("INSERT INTO Books(id, title, author, quantity, isbn) VALUES(uuid(), %s, %s, %s, %s)", (title, author, quantity, isbn))

                        conn.commit()
                        cur.close()
                        logger.info("User created in database")
                        return jsonify("Posted"), 200


                """ DISPLAY BOOK DETAILS """
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
                logger.info("Fetching book details")

                image_array = {}
                image_array['book_id'] = img_set.book_id
                print("Image data for json", image_array)
                image_array['url'] = img_set.url
                logger.info("Fetching image details")

                json2 = json.dumps(image_array, indent=4)
                print(json2)
                resUm = json.loads(json1)
                print (resUm)
                resUm['Image'] = json.loads(json2)
                print("no ans")
                logger.info("Book with image details obtained")
                return json.dumps(resUm, indent=4), 200
            except Exception as e:
                logger.exception("Exception in fetching book details: ", e)
                print("in exception")
                return jsonify("Bad request"), 400
        logger.error("User not authenticated")
        return jsonify("Unauthorized"), 401
    except Exception as e:
        print("outer exception")
        logger.exception("Exception in registering user: ", e)
        return jsonify("Unauthorized"), 401



"""
GET BOOK BY ID
"""
@app.route("/book/<string:id>", methods=["GET"])
def request_a_book(id):
    c.incr("api.request_a_book")
    logger.info("Getting book by id")
    try:
        bookId = id
        logger.info("Book id obtained from header")

        """ AUTHENTICATE BY TOKEN """
        if not request.headers.get('Authorization'):
            logger.error("Headers unavailable")
            return jsonify("Unauthorized"), 401

        """ OBTAIN HEADER """
        myHeader = request.headers["Authorization"]
        if (myHeader == None):
            logger.error("Headers unavailable")
            return jsonify("Unauthorized"), 401


        try:
            decoded_header = base64.b64decode(myHeader)
            decoded_header_by_utf = decoded_header.decode('utf-8')
            dataDict = {}
            dataDict["username"], dataDict["password"] = decoded_header_by_utf.split(":")
        except Exception as e:
            logger.exception("Exception in bs4 decoding:", e)
            return jsonify("Bad headers"), 401
        print(dataDict)
        """ OBTAIN USERNAME AND PASSWORD FROM TOKEN AND DATABASE """
        # user = Person.query.filter_by(username=dataDict["username"]).first()
        conn = db.connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM Person where username=%s", dataDict["username"])
        user = cur.fetchone()

        if not user:
            logger.error("User not available in database")
            return jsonify("Unauthorized"), 401

        userData = {}
        userData["username"] = user[1]
        userData["password"] = user[2]

        if bcrypt.checkpw(dataDict["password"].encode('utf-8'), userData["password"].encode('utf-8')):

            """ OBTAIN BOOK BY ID """
            conn = db.connect()
            cur = conn.cursor()

            cur.execute("SELECT id, title, author, isbn, quantity FROM Books where id=%s", bookId)
            book = cur.fetchone()

            if (book == None):
                logger.error("Book not available in database")
                return jsonify("Not found"), 404


            cur.execute("SELECT id, url FROM Image where book_id=%s", bookId)
            image = cur.fetchone()

            if image:
                logger.info("Image obtained for book")
                bookData = {}
                bookData["id"] = book[0]
                bookData["title"] = book[1]
                bookData["author"] = book[2]
                bookData["isbn"] = book[3]
                bookData["quantity"] = book[4]
                bookData['Image'] = ''
                json1 = json.dumps(bookData, indent=4)

                image_array = {}
                image_array['id'] = image[0]
                image_array['url'] = image[1]

                json2 = json.dumps(image_array, indent=4)
                resUm = json.loads(json1)
                
                resUm['Image'] = json.loads(json2)
                return json.dumps(resUm, indent=4), 200
            else:
                logger.info("Fetching book details")
                bookData = {}
                bookData["id"] = book[0]
                bookData["title"] = book[1]
                bookData["author"] = book[2]
                bookData["isbn"] = book[3]
                bookData["quantity"] = book[4]
                bookData['Image'] = ''
                json1 = json.dumps(bookData, indent=4)

                image_array = {}
                image_array['id'] = ''
                image_array['url'] = ''

                json2 = json.dumps(image_array, indent=4)
                resUm = json.loads(json1)

                resUm['Image'] = json.loads(json2)
                logger.info("Book available to user")
                return json.dumps(resUm, indent=4), 200
        logger.error("User not authenticated")
        return jsonify("Unauthorized"), 401
    except Exception as e:
        print("in exception")
        logger.exception("Exception in fetching book by id: ", e)
        return jsonify("Unauthorized"), 401

"""
GET ALL BOOKS
"""
@app.route("/book", methods=["GET"])
def request_all_books():
    c.incr("api.request_all_books")
    logger.info("Requesting all books")
    try:
        """ AUTHENTICATE BY TOKEN """
        if not request.headers.get('Authorization'):
            logger.error("Authentication headers unavailable")
            return jsonify("Unauthorized"), 401

        """ OBTAIN HEADER """
        myHeader = request.headers["Authorization"]
        if (myHeader == None):
            logger.info("Authentication headers unavailable")
            return jsonify("Unauthorized"), 401

        try:

            decoded_header = base64.b64decode(myHeader)
            decoded_header_by_utf = decoded_header.decode('utf-8')

            dataDict = {}
            dataDict["username"], dataDict["password"] = decoded_header_by_utf.split(":")
        except Exception as e:
            logger.exception("Exception in bs4 decoding:", e)
            return jsonify("Bad headers"), 401
        """ OBTAIN USERNAME AND PASSWORD FROM TOKEN AND DATABASE """
        # user = Person.query.filter_by(username=dataDict["username"]).first()
        conn = db.connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM Person where username=%s", dataDict["username"])
        user = cur.fetchone()

        if not user:
            logger.info("User unavailable in Database")
            return jsonify("Unauthorized"), 401

        userData = {}
        userData["username"] = user[1]
        userData["password"] = user[2]

        if bcrypt.checkpw(dataDict["password"].encode('utf-8'), userData["password"].encode('utf-8')):

            cur.execute("SELECT * FROM Books")
            books = cur.fetchall()
            logger.info("All books fetched")
            print(len(books))

            cur.execute("SELECT * FROM Image")
            img_es = cur.fetchall()
            logger.info("All images fetched")
            print(len(img_es))

            output = []
            for book in books:
                if not img_es:
                    logger.info("No image in database")
                    print("no images")
                    bookData = {}
                    bookData["id"] = book[0]
                    print("Book 0", book[0])
                    bookData["title"] = book[1]
                    bookData["author"] = book[2]
                    bookData["isbn"] = book[3]
                    bookData["quantity"] = book[4]
                    bookData['Image'] = ''
                    json1 = json.dumps(bookData, indent=4)
                    logger.info("Books fetched")

                    image_array = {}
                    image_array["id"] = ''
                    image_array["url"] = ''
                    json2 = json.dumps(image_array, indent=4)
                    logger.info("Images fetched")

                    resUm = json.loads(json1)
                    resUm['Image'] = json.loads(json2)
                    jsonFile = json.dumps(resUm)
                    output.append(jsonFile)
                    print("output",output)
            
                else:
                    for img in img_es:
                        logger.info("Obtaining Image")
                        bookData = {}
                        bookData["id"] = book[0]
                        bookData["title"] = book[1]
                        bookData["author"] = book[2]
                        bookData["isbn"] = book[3]
                        bookData["quantity"] = book[4]

                        bookData['Image'] = ''
                        json1 = json.dumps(bookData, indent=4)

                        if img[2]==book[0]:
                            logger.info("Obtaining book")
                            image_array = {}
                            image_array["id"] = img[0]
                            image_array["url"] = img[1]
                            print("Image 1", img[1])
                            image_array["book_id"] = img[2]
                            json2 = json.dumps(image_array, indent=4)

                            resUm = json.loads(json1)

                            resUm['Image'] = json.loads(json2)
                            jsonFile = json.dumps(resUm)
                            output.append(jsonFile)

                            cur.close()
                            

                        else:
                            image_array = {}
                            image_array["id"] = ''
                            image_array["url"] = ''
                            json2 = json.dumps(image_array, indent=4)

                            resUm = json.loads(json1)
                            resUm['Image'] = json.loads(json2)
                            jsonFile = json.dumps(resUm)
                            output.append(jsonFile)

                            cur.close()
                            
            logger.info("All books fetched")
            return jsonify(output), 200
        logger.error("User not authenticated")
        return jsonify("Unauthorized"), 401
    except Exception as e:
        print("first try exception")
        logger.exception("Exception in fetching all books: ", e)
        return jsonify(e), 500



"""
UPDATE A BOOK
"""
@app.route("/book", methods=["PUT"])
def update_book():
    c.incr("api.update_book")
    logger.info("api for updating book")
    try:
        """ AUTHENTICATE BY TOKEN """
        if not request.headers.get('Authorization'):
            logger.error("headers unavailable")
            return jsonify("Unauthorized"), 401

        """ OBTAIN HEADERS """
        myHeader = request.headers["Authorization"]

        """ DECODE TOKEN """
        try:
            decoded_header = base64.b64decode(myHeader)
            decoded_header_by_utf = decoded_header.decode('utf-8')
            dataDict = {}
            dataDict["username"], dataDict["password"] = decoded_header_by_utf.split(":")
        except Exception as e:
            logger.exception("Exception in bs4 decoding:", e)
            return jsonify("Bad headers"), 401

        conn = db.connect()
        cur = conn.cursor()

        cur.execute("SELECT * FROM Person where username=%s", dataDict["username"])
        user = cur.fetchone()
        logger.info("User fetched from Database")

        if not user:
            logger.error("User unavailable in database")
            return jsonify("Unauthorized"), 401

        userData = {}
        userData["username"] = user[1]
        userData["password"] = user[2]  

        print("userData: ",userData)
        print("encode pass:", dataDict["password"].encode('utf-8'))
        print("user pass: ", userData["password"])

        """ VERIFY TOKEN """
        if bcrypt.checkpw(dataDict["password"].encode('utf-8'), userData["password"].encode('utf-8')):

            print("in if")

            """ OBTAIN BOOK ID TO COMARE IN DATABASE """
            bookId = request.json.get("id")
            print("id : ", bookId)

            if (bookId==None):
                print("Book not entered")
                logger.info("Book not entered")
                return jsonify("Bad request"), 400
            """ OBTAIN BOOK BY ID """
            cur.execute("SELECT * FROM Books where id = %s", bookId)
            book = cur.fetchone()
            cur.close
            print("book : ", book)

            if (book == None):
                logger.error("Book unavailable in database")
                return jsonify("No content"), 204

            cur = conn.cursor()

            cur.execute("SELECT * FROM Image where book_id=%s", bookId)
            image = cur.fetchone()
            try:

               book_data = request.get_json()
            except Exception as e:
                logger.exception("Exception in fetching book: ", e)
                return jsonify("Bad request"), 400

            sql_update_query = """UPDATE Books SET title=%s, author=%s, isbn=%s, quantity=%s where id=%s"""
            title = book_data['title']
            author = book_data['author']
            isbn = book_data['isbn']
            quantity = book_data['quantity']
            id = book_data['id']

            inputValues = (title, author, isbn, quantity, id)
            cur.execute(sql_update_query, inputValues)
            logger.info("Updating book data")

            conn.commit()

            cur.execute("SELECT * FROM Books where id=%s", book_data['id'])
            book = cur.fetchone()

            cur.execute("SELECT * FROM Image where book_id=%s", book_data['id'])
            image = cur.fetchone()


            """ DISPLAY BOOK DETAILS """
            bookData = {}
            bookData["id"] = book[0]
            bookData["title"] = book[1]
            bookData["author"] = book[2]
            bookData["isbn"] = book[3]
            bookData["quantity"] = book[4]
            bookData['Image'] = ''

            json1 = json.dumps(bookData, indent=4)

            image_array = {}
            if not image:
                image_array['id'] = ''
                image_array['url'] = ''

                json2 = json.dumps(image_array, indent=4)
                resUm = json.loads(json1)
                resUm['Image'] = json.loads(json2)
                logger.info("Book displayed to user")
                return json.dumps(resUm, indent=4), 200

            image_array['id'] = image[0]
            image_array['url'] = image[1]

            json2 = json.dumps(image_array, indent=4)
            resUm = json.loads(json1)
            resUm['Image'] = json.loads(json2)
            logger.info("Book displayed to user with image")

            return json.dumps(resUm, indent=4), 200
        logger.error("User not authorized")
        return jsonify("Unauthorized"), 401

    except Exception as e:
        logger.exception("Exception in updating book: ", e)
        return jsonify("Unauthorized"), 401



"""
DELETE A BOOK
"""
@app.route("/book/<string:id>", methods=["DELETE"])
def delete_book(id):
    c.incr("api.delete_book")
    logger.info("Deleting book")
    try:
        bookId = id

        """ AUTHENTICATE BY TOKEN """
        if not request.headers.get('Authorization'):
            logger.error("Headers unavailable")
            return jsonify("Unauthorized"), 401

        """ OBTAIN HEADERS """
        myHeader = request.headers["Authorization"]
        
        """ DECODE TOKEN """
        try:
            decoded_header = base64.b64decode(myHeader)
            decoded_header_by_utf = decoded_header.decode('utf-8')
            dataDict = {}
            dataDict["username"], dataDict["password"] = decoded_header_by_utf.split(":")
        except Exception as e:
            logger.exception("Exception in bs4 decoding:", e)
            return jsonify("Bad headers"), 401

        conn = db.connect()
        cur = conn.cursor()

        cur.execute("SELECT  * FROM Person where username=%s", dataDict["username"])
        user = cur.fetchone()

        if not user:
            print("not usuer")
            logger.info("user not registered")
            return jsonify("Unauthorized"), 401

        userData = {}
        userData["username"] = user[1]
        userData["password"] = user[2]
        print("usesrData: ", userData)

        """ VERIFY TOKEN """
        if bcrypt.checkpw(dataDict["password"].encode('utf-8'), userData["password"].encode('utf-8')):

            cur.execute("SELECT * FROM Image where book_id=%s", bookId)
            img_set =cur.fetchone()
            print("print img_set: ", img_set)

            imageUrl = img_set[1]
            print("url: ",imageUrl)

            if not img_set:
                cur.execute("DELETE FROM Books WHERE id=%s", bookId)
                conn.commit()
                logger.info("Book without image deleted")
            else:
                """ DELETE BOOK FROM DATABASE """
                cur.execute("DELETE FROM Books WHERE id=%s", bookId)
                conn.commit()
                logger.info("Book alone deleted")

                cur.execute("DELETE FROM Image WHERE id=%s", img_set[0])
                conn.commit()
                logger.info("Book's image also deleted")
            
            cur.close()

            # if not local_run:
            ''' DELETING IMAGE FROM S3 IF EXISIS '''
            logger.info("Deleting book from s3")
            delete_image_from_s3(imageUrl)
            logger.info("Book deleted from s3")

            return jsonify(''),204
        logger.error("User not authorized")
        return jsonify("Unauthorized"), 401
    except Exception as e:
        logger.exception("Exception in deleting book: ", e)
        return jsonify("Unauthorized"), 401

""" Upload book image """
@app.route("/book/<string:id>/image", methods=["POST"])
def upload_image(id):
    c.incr("api.upload_image")
    logger.info("Uploading book image")
    conn = db.connect()
    cur = conn.cursor()

    """ AUTHENTICATE BY TOKEN """
    if not request.headers.get("Authorization"):
        logger.error("Headers unavailable")
        return jsonify("Unauthorized"), 401

    myHeader = request.headers["Authorization"]
    if (myHeader == None):
        logger.error("Headers unavailable")
        return jsonify("Unauthorized"), 401

    try:
        decoded_header = base64.b64decode(myHeader)
        decoded_header_by_utf = decoded_header.decode('utf-8')
        dataDict = {}
        dataDict["username"], dataDict["password"] = decoded_header_by_utf.split(":")
    except Exception as e:
        logger.exception("Exception in bs4 decoding:", e)
        return jsonify("Bad headers"), 401


    cur.execute("SELECT * FROM Person where username=%s", dataDict["username"])
    user = cur.fetchone()

    if not user:
        logger.error("User not registered")
        return jsonify("Unauthorized"), 401

    userData = {}
    userData["username"] = user[1]
    userData["password"] = user[2]

    """ VERIFY USER """
    if bcrypt.checkpw(dataDict["password"].encode('utf-8'), userData["password"].encode('utf-8')):
        if not request.json:
            logger.error("bad json")
            jsonify("Bad request"), 400

        try:
            if 'file' in request.files:

                file = request.files['file']

                if file.filename == '':
                    logger.info("File not selected")
                    print('No selected file')

                if file and allowed_file(file.filename):
                    logger.info("Verfiying file type")
                    filename = secure_filename(file.filename)
                    logger.info("File type verified")
                    # upload_on_s3
                    print("My filename", filename)
                    logger.info("Saving file to folder")
                    file.save(os.path.join(UPLOAD_FOLDER, filename))
                    logger.info("File saved to folder")
                    # print(app.config['UPLOAD_FOLDER'])
                    # file.save(filename)
                    url_for_image = os.path.join(UPLOAD_FOLDER, filename)

                    """ OBTAIN BOOK ID TO COMPARE IN DATABASE """
                    bookId = id
                    logger.info("Book id fetched")
                    if (bookId == None):
                        logger.error("Book not available")
                        return jsonify("Bad request"), 400

                    """ OBTAIN BOOK BY ID """
                    logger.info("Fetching book from database")
                    cur.execute("SELECT * FROM Books where id=%s", bookId)
                    book = cur.fetchone()
                    logger.info("Book fetched form database")

                    if (book == None):
                        logger.error("Book not found in database")
                        return jsonify("No content"), 204
                    logger.info("Fetching book image")
                    cur.execute("SELECT * FROM Image WHERE book_id=%s", bookId)
                    image = cur.fetchone()
                    logger.info("Book image fetched")
                    print("Image:", image)
                    # imageId = image[0]

                    if image is None:
                        logger.info("No image for book")
                        
                        print("printg **********")
                    else:
                        print("image exists")
                        imageId = image[0]
                        logger.info("Deleting current book image")
                        cur.execute("DELETE FROM Image WHERE book_id=%s", bookId)
                        conn.commit()
                        logger.info("Deleting current book image successful")
                        print("image deleted")
                        
                    logger.info("Inserting new book image")
                    cur.execute("INSERT INTO Image(id, url, book_id) VALUES (uuid(),%s, %s)", (url_for_image, bookId))
                    conn.commit()
                    logger.info("Inserting new book image successful")

                    '''upload image on S_3 bucket'''
                    # if production_run==True:
                    logger.info("Uploading book image to s3")
                    upload_on_s3(url_for_image)
                    logger.info("Uploading book image to s3 successful")

                    """ OBTAIN IMAGE FROM IMAGE TABLE USING BOOKID And update Book table with the imageid"""
                    logger.info("Fetching book image from db")
                    cur.execute("SELECT * FROM Image where book_id=%s", bookId)
                    image = cur.fetchone()
                    logger.info("Book image fetched from db")

                    """ DISPLAY BOOK DETAILS """
                    bookData = {}
                    bookData["id"] = book[0]
                    bookData["title"] = book[1]
                    bookData["author"] = book[2]
                    bookData["isbn"] = book[3]
                    bookData["quantity"] = book[4]
                    bookData['Image'] = ''
                    json1 = json.dumps(bookData, indent=4)

                    image_array = {}
                    image_array['id'] = image[0]
                    image_array['url'] = image[1]

                    json2 = json.dumps(image_array, indent=4)
                    resUm = json.loads(json1)
                    resUm['Image'] = json.loads(json2)
 
                    cur.close()
                    logger.info("Book with image displayed")

                    return json.dumps(resUm, indent=4), 201

        except Exception as e:
            logger.exception("Exception in uploading book image: ", e)
            return jsonify(e), 500



"""
GET BOOK IMAGE
"""
@app.route("/book/<string:id>/image/<string:imgId>", methods=["GET"])
def get_book_image(id, imgId):
    c.incr("api.get_book_image")
    logger.info("Getting book image from id")
    try:
        print("Getting book image")
        bookId = id
        logger.info("Book id obtained")
        # print("BOOK ID", bookId)
        imageId = imgId
        logger.info("Image id obtained")

        print("bookid: " + bookId + "img id: "+imageId)
        conn = db.connect()
        cur = conn.cursor()
        print("conn establised")

        """ AUTHENTICATE BY TOKEN """
        if not request.headers.get("Authorization"):
            logger.error("Headers unavailable")
            return jsonify("Unauthorized"), 401

        myHeader = request.headers["Authorization"]
        if (myHeader == None):
            logger.info("Headers unavailable")
            return jsonify("Unauthorized"), 401

        try:
            decoded_header = base64.b64decode(myHeader)
            decoded_header_by_utf = decoded_header.decode('utf-8')
            dataDict = {}
            dataDict["username"], dataDict["password"] = decoded_header_by_utf.split(":")
        except Exception as e:
            logger.exception("Exception in bs4 decoding:", e)
            return jsonify("Bad headers"), 401


        cur.execute("SELECT * FROM Person where username=%s", dataDict["username"])
        user = cur.fetchone()

        if not user:
            logger.error("user not found in database")
            return jsonify("Unauthorized"), 401

        userData = {}
        userData["username"] = user[1]
        userData["password"] = user[2]

        """ VERIFY USER """
        if bcrypt.checkpw(dataDict["password"].encode('utf-8'), userData["password"].encode('utf-8')):

            
                """ OBTAIN BOOK BY ID from local db"""
                cur.execute("SELECT * FROM Image where id=%s and book_id=%s", (imageId, bookId))
                image = cur.fetchone()
                print("MYIMAGE", image)
                logger.info("Image fetched from database")

                output = []
                image_data = {}
                image_data["id"] = image[0]
                image_data["url"] = image[1]

                # if(local_run==True):
                #     print("IN LOCAL RUN")
                #     output.append(image_data)
                #     cur.cose()
                #     return jsonify(output),200
                # else:
                print("IN PRESIGNED URL")
                print("my urls is", image_data["url"])
                url_pre = str(image_data["url"])
                modified_url = presignedUrl(url_pre)
                print("url", modified_url)
                image_data["url"] = modified_url
                print("image data url", image_data["url"])
                output.append(image_data)
                logger.info("Image details displayed to user")
                return jsonify(output),200



            


        cur.close()
        logger.info("Database connection closed")
        logger.error("Invalid login information")
        return jsonify("Unauthorized"), 401
    logger.exception("Exception in fetching image details: ", e)
    except Exception as e:

        print("in exception", e)
        logger.exception("Exception in fetching image details: ", e)
        return jsonify("Unauthorized"), 401



""" UPDATE BOOK IMAGE """
@app.route("/book/<string:id>/image/<string:imgId>", methods=["PUT"])
def update_image(id, imgId):
    c.incr("api.update_image")
    logger.info("Updating book image")
    bookId = id
    logger.info("Book id obtained")
    imageId = imgId
    logger.info("Image id obtained")

    conn = db.connect()
    cur = conn.cursor()
    logger.info("Database connection establised")

    """ AUTHENTICATE BY TOKEN """
    if not request.headers.get("Authorization"):
        logger.info("Headers unavailable")
        return jsonify("Unauthorized"), 401

    myHeader = request.headers["Authorization"]
    if (myHeader == None):
        logger.info("Headers unavailable")
        return jsonify("Unauthorized"), 401

    try:
        decoded_header = base64.b64decode(myHeader)
        decoded_header_by_utf = decoded_header.decode('utf-8')

        dataDict = {}
        dataDict["username"], dataDict["password"] = decoded_header_by_utf.split(":")
    except Exception as e:
        logger.exception("Exceptio in decoding bs4: ",e)
        return jsonify("Bad authorization headers"), 401
    """ OBTAIN USERNAME AND PASSWORD FROM TOKEN AND DATABASE """
    cur.execute("SELECT * FROM Person WHERE username=%s", dataDict["username"])
    user = cur.fetchone()

    if not user:
        logger.error("User not available in database")
        return jsonify("Unauthorized"), 401

    userData = {}
    userData["username"] = user[1]
    userData["password"] = user[2]

    """ VERIFY USER """
    if bcrypt.checkpw(dataDict["password"].encode('utf-8'), userData["password"].encode('utf-8')):
        if not request.json:
            logger.error("Bad json format")
            jsonify("Bad request"), 400

        try:
            print ("in upload_image")

            if 'file' in request.files:
                print("file present")

                file = request.files['file']
                print (file.filename)

                if file.filename == '':
                    logger.info("No file selected")
                    print('No selected file')

                if file and allowed_file(file.filename):
                    logger.info("Checking file format")
                    filename = secure_filename(file.filename)
                    logger.info("File format valid")

                    print("filename: ",filename)
                    logger.info("Saving image in folder")
                    file.save(os.path.join(UPLOAD_FOLDER, filename))
                    logger.info("Image saved in folder")
                    url_for_image = os.path.join(UPLOAD_FOLDER, filename)

                    print("url: ", url_for_image)

                    """ OBTAIN BOOK ID TO COMPARE IN DATABASE """
                    bookId = id
                    if (bookId == None):
                        logger.error("Book id not available")
                        return jsonify("Bad request"), 400

                    """ OBTAIN BOOK BY ID """
                    cur.execute("SELECT * FROM Books WHERE id=%s", bookId)
                    book = cur.fetchone()
                    print("book: ", book)
                    logger.info("Book fetched from database")

                    if (book == None):
                        print("no book")
                        logger.error("Book not available in database")
                        return jsonify("No content"), 204

                    cur.execute("SELECT * FROM Image WHERE id=%s", imageId)
                    imageDb = cur.fetchone()
                    logger.info("Image fetched from database")

                    if imageDb:
                        logger.info("Updating book image")
                        cur.execute("UPDATE Image SET url=%s WHERE book_id=%s", (url_for_image, bookId))
                        conn.commit()
                        cur.close()
                        logger.info("Book image updated")

                    # else:
                        # return jsonify('Cannot update'), 204
                logger.info("Updating book image successful")
                return jsonify('No Content'),204
            logger.info("Updating book image details")
            return json.dumps(resUm, indent=4), 201
        except Exception as e:
            logger.exception("Exception in updating book image: ", e)
            return jsonify(e), 500

"""
DELETE A IMAGE
"""
@app.route("/book/<string:id>/image/<string:imgId>", methods=["DELETE"])
def delete_image(id, imgId):
    c.incr("api.delete_image")
    logger.info("Deleting book image")
    try:
        bookId = id
        logger.info("Book id fetched")
        imageId = imgId
        logger.info("Image id fetched")

        conn = db.connect()
        cur = conn.cursor()

        """ AUTHENTICATE BY TOKEN """
        if not request.headers.get("Authorization"):
            print("no auth")
            logger.error("Headers unavailable")
            return jsonify("Unauthorized"), 401

        myHeader = request.headers["Authorization"]
        print("headers: ", myHeader)

        if (myHeader == None):
            logger.info("Headers unavailable")
            return jsonify("Unauthorized"), 401

        try:
            decoded_header = base64.b64decode(myHeader)
            decoded_header_by_utf = decoded_header.decode('utf-8')
            dataDict = {}
            dataDict["username"], dataDict["password"] = decoded_header_by_utf.split(":")
        except Exception as e:
            logger.exception("Exception in bs4 decoding:", e)
            return jsonify("Bad headers"), 401

        """ OBTAIN USERNAME AND PASSWORD FROM TOKEN AND DATABASE """
        cur.execute("SELECT * FROM Person WHERE username=%s", dataDict["username"])
        user = cur.fetchone()
        print("user: ", user)
        logger.info("User fetched")

        if not user:
            logger.info("User not available in database")
            return jsonify("Unauthorized"), 401

        userData = {}
        userData["username"] = user[1]
        userData["password"] = user[2]

        """ VERIFY USER """
        if bcrypt.checkpw(dataDict["password"].encode('utf-8'), userData["password"].encode('utf-8')):

            """ OBTAIN BOOK BY ID """
            # cur.execute("SELECT * FROM Books WHERE id=bookId")
            # book = cur.fetchone()

            cur.execute("SELECT * FROM Image WHERE id=%s", imgId)
            image = cur.fetchone()
            logger.info("Image fetched from database")
            print("image :", image)
            imageUrl = image[1]

            if (image == None):
                logger.info("Image not in database")
                return jsonify("No content"), 204

            # if (book == None):
            #     return jsonify("No content"), 204

            print("image book id : ", image[2])
            print("book book id : ", bookId)

            if image[2] == bookId:
                print("in if")

                """ DELETE Image FROM DATABASE """
                logger.info("Deleting book image from database")
                cur.execute("DELETE FROM Image WHERE id=%s", image[0])
                conn.commit()
                cur.close()
                logger.info("Deleting book image successful")

                # if not local_run:
                ''' DELETING IMAGE FROM S3 IF EXISIS '''
                logger.info("Deleting book image form s3")
                delete_image_from_s3(imageUrl)
                logger.info("Deleting book image from s3 successful")

            logger.info("Deleting book image successful")
            return jsonify('No Content'),204
        logger.error("Invalid user information")
        return jsonify("Unauthorized"), 401
    except Exception as e:
        print("exception : ", e)
        logger.exception("Exception in deleting book image: ", e)
        return jsonify("Unauthorized"), 401


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@app.route('/shutdown', methods=['GET'])
def shutdown():
    shutdown_server()
    return 'Server shutting down...'

if __name__ == '__main__':
    
    """ RUN FLASK APP """
    logger.info("Database creation initiated")
    create_database()
    logger.info("Database created")
    app.run(host='0.0.0.0')


# def presignedUrl():
#     s3_client = boto3.client('s3')
#     resp = s3_client.generate_presigned_url('get_object', Params = {'Bucket': aws_s3_bucket_name, 'Key': }, ExpiresIn = 100)
#     print(resp)


# 