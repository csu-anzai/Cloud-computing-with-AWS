import unittest
from Assignment01Dev import app, Person, Books, db

from flask import json
#import config
from sqlalchemy.engine import Engine
from sqlalchemy import event
import base64
import os


class MyTestCase(unittest.TestCase):


    def create_app(self):
        app.config['TESTING']=True
        db_path = os.path.join(os.path.dirname(__file__), 'Assignment01-test.db')
        db_uri = 'sqlite:///{}'.format(db_path)
        app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
        return app


    def setUp(self):
        #print("in setup")
        self.app = self.create_app()
        db.create_all()

    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        #print("inpragma")
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    def test_valid_User_register(self):
        #print("in valid user test method")
        response = app.test_client().post('/user/register', json=({'username': "333", 'password': "333"}), content_type='application/json',)
        #print("************USER LOGIN*************" ,response)

        data = json.loads(response.get_data())
        #print("Data: ",data)

        assert response.status_code == 200

    def test_invalid_User_register(self):
        #print("in test method")
        response = app.test_client().post('/user/register', json=({'email': "333", 'password': "333"}), content_type='application/json',)
        #print("************USER LOGIN*************" ,response)

        data = json.loads(response.get_data())
        #print("Data: ",data)

        assert response.status_code == 400


if "__name__"=="__main__":
    unittest.main(exit=False)


