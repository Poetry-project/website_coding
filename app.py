import sqlite3
import csv
import os
import re
import base64
import hashlib
import tweepy
import requests
from flask import Flask
from flask import request, render_template
from generate_text_class  import GenerateText
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
import pandas as pd

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] =\
    'sqlite:///' + os.path.join(basedir, 'arabicPoetry.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Data(db.Model):
    # __table__ = db.Model.metadata.tables['data']
    id = db.Column(db.Integer, primary_key=True)
    poem_id = db.Column(db.Integer)
    poet_name = db.Column(db.String(256))
    poem_title = db.Column(db.String(100))
    poem_text = db.Column(db.Text)
    era = db.Column(db.String(256))
    country = db.Column(db.String(100))
    poem_style = db.Column(db.String(100))

    # def __repr__(self):
    # return f'{self.poem_text}'

    def __str__(self):
        return f'{self.poem_text}'


client_id = "cVdTV2Fic1FySUF5NVp4WnFfYjk6MTpjaQ"
client_secret = "6gVt0-BRzG6CQNV0IMfOnUPvRknmJONy8O9swMtSbn6J3RvIWH"
auth_url = "https://twitter.com/i/oauth2/authorize"
token_url = "https://api.twitter.com/2/oauth2/token"
redirect_uri = "http://127.0.0.1:5000/oauth/callback"


scopes = ["tweet.read", "users.read", "tweet.write"]
code_verifier = base64.urlsafe_b64encode(os.urandom(30)).decode("utf-8")
code_verifier = re.sub("[^a-zA-Z0-9]+", "", code_verifier)
code_challenge = hashlib.sha256(code_verifier.encode("utf-8")).digest()
code_challenge = base64.urlsafe_b64encode(code_challenge).decode("utf-8")
code_challenge = code_challenge.replace("=", "")


# Posting the Tweet
def post_tweet(payload, new_token):
    print("Tweeting!")
    return requests.request(
        "POST",
        "https://api.twitter.com/2/tweets",
        json=payload,
        headers={
            "Authorization": "Bearer {}".format(new_token["access_token"]),
            "Content-Type": "application/json",
        },
    )


@app.route("/oauth/callback", methods=["GET"])
def callback():
    code = request.args.get("code")    
    token = twitter.fetch_token(
        token_url=token_url,
        client_secret=client_secret,
        code_verifier=code_verifier,
        code=code,
    )
    response = post_tweet(payload, token).json()
    return response


@app.route('/', methods=['GET', 'POST'])
def main():
    if request.method == 'POST':
        # generate = []
        phrase = request.form["txt_generate"]
        # generate.append(phrase)
        # if phrase 
        # output = obj.predict(seed_text=phrase, seq_length=1000)
        output = obj.predict(seed_text= phrase , seq_length=1000)
        return render_template('result.html', result=output)
    return render_template('index.html')


@app.route('/features', methods=['GET', 'POST'])
def features():
    return (render_template('features.html'))



# background process happening without any refreshing
@app.route('/GenerateCustom', methods=['POST', 'GET'])
def GenerateCustom():
   if request.method == "POST":
        phrase = request.form['txtGenerate'] 
        # print (phrase)
        # print (' '.join(phrase))
        # phrase = 'واستباح'
        output = obj.predict(seed_text=' '.join(phrase), seq_length=1000)     
        print (output)
        return output


# background process happening without any refreshing
@app.route('/GenerateAi', methods=['POST', 'GET'])
def GenerateAi():    
    row = Data.query.order_by(func.random()).first()
    # print(row)
    phrase = str(row).split()[:3]
    # print (phrase)
    # print (' '.join(phrase))
    # phrase = 'واستباح'
    output = obj.predict(seed_text=' '.join(phrase), seq_length=1000)     
    return output


@app.route('/login', methods=['GET', 'POST'])
def login():
    return (render_template('login.html'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    return (render_template('signup.html'))

@app.route('/about', methods=['GET'])
def about():
    return (render_template('about.html'))

def createDb():
    PATH_TO_CSV = 'dataset/new_dataset.csv'    
    url = 'https://drive.google.com/file/d/1CJ6vIcgtw84qJeelklolsSBKbEg7RpX1/view?usp=drive_link'
    
    if not os.path.exists('arabicPoetry.db'):
        # if os.path.exists(PATH_TO_CSV):
        # Connecting to the geeks database
        connection = sqlite3.connect('arabicPoetry.db')
        # Creating a cursor object to execute
        # SQL queries on a database table
        cursor = connection.cursor()
        # Table Definition
        # poem_id,poet_name,poem_title,poem_text,era,country,poem_style
        create_table = '''CREATE TABLE if not exists data(
                                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                                            poem_id  INTEGER NOT NULL,
                                            poet_name TEXT NOT NULL,
                                            poem_title TEXT NOT NULL,
                                            poem_text TEXT NOT NULL,
                                            era TEXT NOT NULL,
                                            country TEXT NOT NULL,
                                            poem_style TEXT NOT NULL
                                        ); '''

        # Creating the table into our
        # database
        cursor.execute(create_table)
        # Opening the person-records.csv file
        # file = open(PATH_TO_CSV, encoding='utf-8-sig')
        # Reading the contents of the
        # person-records.csv file
        # contents = csv.reader(file)
        contents = pd.read_csv(url , encoding='utf-8-sig')
        # SQL query to insert data into the
        # person table
        insert_records = "INSERT INTO data (poem_id,poet_name,poem_title,poem_text,era,country,poem_style) VALUES(?, ?, ?, ?, ?, ?, ?)"
        # Importing the contents of the file
        # into our person table
        cursor.executemany(insert_records, contents)
        # Committing the changes
        connection.commit()
        # closing the database connection
        connection.close()
    else:
        print("Pleas load the dataset file csv")


if __name__ == '__main__':
    createDb()
    obj = GenerateText()
    app.secret_key = "123456"
    # app.debug = True
    app.run()