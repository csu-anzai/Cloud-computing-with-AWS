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


#local_run = os.environ['LOCAL_RUN']
#production_run = os.environ['PRODUCTION_RUN']



# print("Production run value", production_run)
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


# if(production_run):
print("In production_run", os.environ["PATH"])
# print(production_run)
print("Hello")
aws_s3_bucket_name = os.environ.get('S3_BUCKET_NAME')
app.config['MYSQL_DATABASE_USER'] = 'csye6225master'
app.config['MYSQL_DATABASE_PASSWORD'] = 'csye6225password'
app.config['MYSQL_DATABASE_DB'] = 'csye6225'
app.config['MYSQL_DATABASE_HOST'] = os.environ['RDS_INSTANCE']

# elif(local_run):
# 	app.config['MYSQL_DATABASE_USER'] = "root"
# 	app.config['MYSQL_DATABASE_PASSWORD'] = 'password'
# 	app.config['MYSQL_DATABASE_DB'] = 'csye6225'
# 	app.config['MYSQL_DATABASE_HOST'] = 'localhost'

db = MySQL()
db.init_app(app)

 
''' IMAGES FOLDER PATH '''
UPLOAD_FOLDER = os.path.dirname(__file__) + "Images"


''' ALLOWED EXTENSIONS FOR UPLOAD ''' 
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

""" Create secret key for UUID in database """
app.config['SECRET_KEY'] = 'my_key'
       

def create_database():
    conn = db.connect()
    cur = conn.cursor()
    cur.execute("CREATE table if not exists Person(id varchar(100) NOT NULL, username varchar(100) DEFAULT NULL, password varchar(100) DEFAULT NULL, PRIMARY KEY ( id ))")
    cur.execute("CREATE table if not exists Books(id varchar(100) NOT NULL, title varchar(50) DEFAULT NULL, author varchar(50) DEFAULT NULL, isbn varchar(50) DEFAULT NULL, quantity varchar(50) DEFAULT NULL, PRIMARY KEY ( id ))")
    cur.execute("CREATE table if not exists Image(id varchar(100) NOT NULL, url varchar(1000) DEFAULT NULL, book_id varchar(100) DEFAULT NULL, PRIMARY KEY ( id ))")
    

""" UPLOAD IMAGE on S3 """
def upload_on_s3( filename ):
    print("filename inupload: ", os.path.dirname(__file__) +  filename)

    key_filename = filename
    print(key_filename)

    #filename = filename

    s3 = boto3.client(
        "s3",
        aws_access_key_id = os.environ['AWS_ACCESS_KEY'],
        aws_secret_access_key = os.environ['AWS_SECRET_ACCESS_KEY_ID'],
    )   
    bucket_resource = s3

    print("bucket_resource", bucket_resource)

    bucket_resource.upload_file(
        Bucket = aws_s3_bucket_name,
        Filename=filename,
        Key=key_filename
    )
    print("UPLOAD SUCCESSFULL")


""" DELETE IMAGE FROM S3 BUCKET """
def delete_image_from_s3( filename ):

    key_filename = filename
    print("key_filename : ", key_filename)

    s3 = boto3.client(
        "s3",
        aws_access_key_id = os.environ['AWS_ACCESS_KEY'],
        aws_secret_access_key = os.environ['AWS_SECRET_ACCESS_KEY_ID'],
    )
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
    except Exception as e:
        print("Exception : ",e)



def presignedUrl( filename ):
    filename = filename
    print("filename : ", filename)
    s3_client = boto3.client('s3',
    aws_access_key_id = os.environ['AWS_ACCESS_KEY'],
        aws_secret_access_key = os.environ['AWS_SECRET_ACCESS_KEY_ID'],
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
    except Exception as e:
        print("Exception is:", e)
    return resp_url
    



""" REGISTER USER """
@app.route('/user/register', methods=['POST'])
def register_user():
    try:
        if not request.get_json():
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
            if not myPassword:
                return jsonify("Bad request"), 400

            """ CHECKING STRENGTH OF PASSWORD """
            if policy.test(myPassword):
                return jsonify("Password not strong enough"), 400

            """ HASHING PASSWORD """
            password = bcrypt.hashpw(myPassword.encode('utf-8'), salt)


            """ CHECK IF USER EXISITS """
            conn = db.connect()
            cur = conn.cursor()

            cur.execute("SELECT * FROM Person where username=%s", email)
            user = cur.fetchone()

            if user is not None:
                return jsonify("User already exists"), 200


            """ ADDING USER TO DATABASE """
            cur.execute("INSERT INTO Person(id, username, password) VALUES (uuid(), %s, %s)", (email, password))

            conn.commit()
            cur.close()

            return jsonify('User registered successfully'), 200
        except Exception as e:
            return jsonify(e), 500
    except Exception as e:
        return jsonify(e), 400



""" ROUTE TO ROOT """
@app.route("/")
def index():
    
    """ VERIFYING BASIC AUTH """
    if not request.authorization:
        return jsonify("Unauthorized"), 401

    username = request.authorization.username

    conn = db.connect()
    cur = conn.cursor()
    cur.execute("SELECT username, password FROM Person where username=%s", username)
    user = cur.fetchone()
    print("user :", user)

    """ OBTAIN USERNAME AND PASSWORD BY TOKEN FROM DATABASE """
    if not user:
        return jsonify("Unauthorized"), 401

    userData = {}
    userData["username"] = user[0]
    userData["password"] = user[1]

    if request.authorization and request.authorization.username == userData["username"] and (bcrypt.checkpw(request.authorization.password.encode('utf-8'),userData["password"].encode('utf-8'))):
        cur.close()
        return jsonify(str(datetime.datetime.now())), 200

    cur.close()
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
        print("header data dict: ", dataDict)

        """ OBTAIN USERNAME AND PASSWORD FROM TOKEN AND DATABASE """
        conn = db.connect()
        cur = conn.cursor()

        cur.execute("SELECT username, password FROM Person where username=%s", dataDict["username"])
        user = cur.fetchone()
        print("user : ", user)

        if not user:
            return jsonify("Unauthorized"), 401

        userData = {}
        userData["username"] = user[0]
        userData["password"] = user[1]

        """ VERIFY USER """
        if bcrypt.checkpw(dataDict["password"].encode('utf-8'), userData["password"].encode('utf-8')):
            if not request.json:
                return jsonify("Bad request"), 400
            try:
                """ OBTAIN AND STORE BOOK DETAILS FROM JSON IN DATABSE """

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
GET BOOK BY ID
"""
@app.route("/book/<string:id>", methods=["GET"])
def request_a_book(id):
    try:
        bookId = id

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
        print(dataDict)
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

            """ OBTAIN BOOK BY ID """
            conn = db.connect()
            cur = conn.cursor()

            cur.execute("SELECT id, title, author, isbn, quantity FROM Books where id=%s", bookId)
            book = cur.fetchone()

            if (book == None):
                return jsonify("Not found"), 404


            cur.execute("SELECT id, url FROM Image where book_id=%s", bookId)
            image = cur.fetchone()

            if image:
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

                return json.dumps(resUm, indent=4), 200

        return jsonify("Unauthorized"), 401
    except Exception as e:
        print("in exception")
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
            print(len(books))

            cur.execute("SELECT * FROM Image")
            img_es = cur.fetchall()
            print(len(img_es))

            output = []
            for book in books:
                if not img_es:
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

                    image_array = {}
                    image_array["id"] = ''
                    image_array["url"] = ''
                    json2 = json.dumps(image_array, indent=4)

                    resUm = json.loads(json1)
                    resUm['Image'] = json.loads(json2)
                    jsonFile = json.dumps(resUm)
                    output.append(jsonFile)
                    print("output",output)
            
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

                        if img[2]==book[0]:
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
                            

            return jsonify(output), 200

        return jsonify("Unauthorized"), 401
    except Exception as e:
        print("first try exception")
        return jsonify(e), 500



"""
UPDATE A BOOK
"""
@app.route("/book", methods=["PUT"])
def update_book():
    try:
        """ AUTHENTICATE BY TOKEN """
        if not request.headers.get('Authorization'):
            return jsonify("Unauthorized"), 401

        """ OBTAIN HEADERS """
        myHeader = request.headers["Authorization"]

        """ DECODE TOKEN """
        data = base64.b64decode(myHeader)
        newData = data.decode('utf-8')
        

        """ OBTAIN USERNAME AND PASSWORD FROM TOKEN AND DATABASE """
        dataDict = {}
        dataDict["username"], dataDict["password"] = newData.split(":")

        conn = db.connect()
        cur = conn.cursor()

        cur.execute("SELECT * FROM Person where username=%s", dataDict["username"])
        user = cur.fetchone()

        if not user:
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

        	if (bookId == None):
        		return jsonify("Bad request"), 400

        	""" OBTAIN BOOK BY ID """
        	cur.execute("SELECT * FROM Books where id = %s", bookId)
        	book = cur.fetchone()
        	cur.close
        	print("book : ", book)

        	if (book == None):
        		return jsonify("No content"), 204

        	cur = conn.cursor()

        	cur.execute("SELECT * FROM Image where book_id=%s", bookId)
        	image = cur.fetchone()

        	book_data = request.get_json()
        	
        	sql_update_query = """UPDATE Books SET title=%s, author=%s, isbn=%s, quantity=%s where id=%s"""
        	title = book_data['title']
        	author = book_data['author']
        	isbn = book_data['isbn']
        	quantity = book_data['quantity']
        	id = book_data['id']

        	inputValues = (title, author, isbn, quantity, id)
        	cur.execute(sql_update_query, inputValues)

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

        		return json.dumps(resUm, indent=4), 200

        	image_array['id'] = image[0]
        	image_array['url'] = image[1]

        	json2 = json.dumps(image_array, indent=4)
        	resUm = json.loads(json1)
        	resUm['Image'] = json.loads(json2)

        	return json.dumps(resUm, indent=4), 200
        	# return "updated", 200

        return jsonify("Unauthorized"), 401

    except Exception as e:
    	return jsonify("Unauthorized"), 401



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
        

        """ OBTAIN USERNAME AND PASSWORD FROM TOKEN AND DATABASE """
        dataDict = {}
        dataDict["username"], dataDict["password"] = newData.split(":")
        print("dataDict : ", dataDict)

        conn = db.connect()
        cur = conn.cursor()

        cur.execute("SELECT  * FROM Person where username=%s", dataDict["username"])
        user = cur.fetchone()

        if not user:
        	print("not usuer")
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
            else:
            	""" DELETE BOOK FROM DATABASE """
            	cur.execute("DELETE FROM Books WHERE id=%s", bookId)
            	conn.commit()

            	cur.execute("DELETE FROM Image WHERE id=%s", img_set[0])
            	conn.commit()
            
            cur.close()

            # if not local_run:
            ''' DELETING IMAGE FROM S3 IF EXISIS '''
            delete_image_from_s3(imageUrl)

            return jsonify(''),204
        return jsonify("Unauthorized"), 401
    except Exception as e:
        return jsonify("Unauthorized"), 401




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
            if 'file' in request.files:

                file = request.files['file']

                if file.filename == '':
                    print('No selected file')

                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    # upload_on_s3
                    print("My filename", filename)

                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    # print(app.config['UPLOAD_FOLDER'])
                    # file.save(filename)
                    url_for_image = os.path.join(app.config['UPLOAD_FOLDER'], filename)

                    """ OBTAIN BOOK ID TO COMPARE IN DATABASE """
                    bookId = id
                    if (bookId == None):
                        return jsonify("Bad request"), 400

                    """ OBTAIN BOOK BY ID """
                    cur.execute("SELECT * FROM Books where id=%s", bookId)
                    book = cur.fetchone()

                    if (book == None):
                        return jsonify("No content"), 204

                    cur.execute("SELECT * FROM Image WHERE book_id=%s", bookId)
                    image = cur.fetchone()
                    print("Image:", image)
                    # imageId = image[0]

                    if image is None:
                        
                        print("printg **********")
                    else:
                        print("omage exists")
                        imageId = image[0]
                        cur.execute("DELETE FROM Image WHERE book_id=%s", bookId)
                        conn.commit()
                        print("image deleted")
                        

                    cur.execute("INSERT INTO Image(id, url, book_id) VALUES (uuid(),%s, %s)", (url_for_image, bookId))
                    conn.commit()

                    '''upload image on S_3 bucket'''
                    # if production_run==True:
                    upload_on_s3(url_for_image)

                    """ OBTAIN IMAGE FROM IMAGE TABLE USING BOOKID And update Book table with the imageid"""
                    cur.execute("SELECT * FROM Image where book_id=%s", bookId)
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
                    image_array['id'] = image[0]
                    image_array['url'] = image[1]

                    json2 = json.dumps(image_array, indent=4)
                    resUm = json.loads(json1)
                    resUm['Image'] = json.loads(json2)
 
                    cur.close()

                    return json.dumps(resUm, indent=4), 201

        except Exception as e:
            return jsonify(e), 500



"""
GET BOOK IMAGE
"""
@app.route("/book/<string:id>/image/<string:imgId>", methods=["GET"])
def get_book_image(id, imgId):
    try:
        print("Getting pook image")
        bookId = id
        # print("BOOK ID", bookId)
        imageId = imgId

        print("bookid: " + bookId + "img id: "+imageId)
        conn = db.connect()
        cur = conn.cursor()
        print("conn establised")

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

            
                """ OBTAIN BOOK BY ID from local db"""
                cur.execute("SELECT * FROM Image where id=%s and book_id=%s", (imageId, bookId))
                image = cur.fetchone()
                print("MYIMAGE", image)

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
                return jsonify(output),200



            


        cur.close()
        return jsonify("Unauthorized"), 401
    except Exception as e:

        print("in exception", e)
        return jsonify("Unauthorized"), 401



""" UPDATE BOOK IMAGE """
@app.route("/book/<string:id>/image/<string:imgId>", methods=["PUT"])
def update_image(id, imgId):
    bookId = id
    imageId = imgId

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

    """ OBTAIN USERNAME AND PASSWORD FROM TOKEN AND DATABASE """
    cur.execute("SELECT * FROM Person WHERE username=%s", dataDict["username"])
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

                    print("filename: ",filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    url_for_image = os.path.join(app.config['UPLOAD_FOLDER'], filename)

                    print("url: ", url_for_image)

                    """ OBTAIN BOOK ID TO COMPARE IN DATABASE """
                    bookId = id
                    if (bookId == None):
                        return jsonify("Bad request"), 400

                    """ OBTAIN BOOK BY ID """
                    cur.execute("SELECT * FROM Books WHERE id=%s", bookId)
                    book = cur.fetchone()
                    print("book: ", book)

                    if (book == None):
                    	print("no book")
                    	return jsonify("No content"), 204

                    cur.execute("SELECT * FROM Image WHERE id=%s", imageId)
                    imageDb = cur.fetchone()

                    if imageDb:
	                    cur.execute("UPDATE Image SET url=%s WHERE book_id=%s", (url_for_image, bookId))
	                    conn.commit()
	                    cur.close()

	                # else:
	                	# return jsonify('Cannot update'), 204

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

        conn = db.connect()
        cur = conn.cursor()

        """ AUTHENTICATE BY TOKEN """
        if not request.headers.get("Authorization"):
            print("no auth")
            return jsonify("Unauthorized"), 401

        myHeader = request.headers["Authorization"]
        print("headera: ", myHeader)

        if (myHeader == None):
            return jsonify("Unauthorized"), 401

        decoded_header = base64.b64decode(myHeader)
        decoded_header_by_utf = decoded_header.decode('utf-8')

        dataDict = {}
        dataDict["username"], dataDict["password"] = decoded_header_by_utf.split(":")

        """ OBTAIN USERNAME AND PASSWORD FROM TOKEN AND DATABASE """
        cur.execute("SELECT * FROM Person WHERE username=%s", dataDict["username"])
        user = cur.fetchone()
        print("user: ", user)

        if not user:
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
            print("image :", image)
            imageUrl = image[1]

            if (image == None):
                return jsonify("No content"), 204

            # if (book == None):
            #     return jsonify("No content"), 204

            print("iamge book id : ", image[2])
            print("book book id : ", bookId)

            if image[2] == bookId:
                print("in if")

                """ DELETE BOOK FROM DATABASE """
                cur.execute("DELETE FROM Image WHERE id=%s", image[0])
                conn.commit()
                cur.close()

                # if not local_run:
                ''' DELETING IMAGE FROM S3 IF EXISIS '''
                delete_image_from_s3(imageUrl)

            return jsonify('No Content'),204

        return jsonify("Unauthorized"), 401
    except Exception as e:
        print("exception : ", e)
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
    create_database()
    app.run(host='0.0.0.0')


# def presignedUrl():
#     s3_client = boto3.client('s3')
#     resp = s3_client.generate_presigned_url('get_object', Params = {'Bucket': aws_s3_bucket_name, 'Key': }, ExpiresIn = 100)
#     print(resp)

