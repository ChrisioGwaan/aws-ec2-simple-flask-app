# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START gae_python38_render_template]
# [START gae_python3_render_template]
import datetime

import os

from flask import Flask, render_template, request, flash, redirect, url_for

import key_configer as keys

import boto3

from boto3.dynamodb.conditions import Key, Attr

from botocore.exceptions import ClientError

app = Flask(__name__)

# Configure the AWS credentials
dynamodb = boto3.resource('dynamodb',
                    aws_access_key_id=keys.ACCESS_KEY_ID,
                    aws_secret_access_key=keys.ACCESS_SECRET_KEY,
                    aws_session_token=keys.AWS_SESSION_TOKEN,
                    region_name='us-east-1')

@app.route('/')
def root():
    # For the sake of example, use static information to inflate the template.
    # This will be replaced with real information in later steps.
    # dummy_times = [datetime.datetime(2018, 1, 1, 10, 0, 0),
    #                datetime.datetime(2018, 1, 2, 10, 30, 0),
    #                datetime.datetime(2018, 1, 3, 11, 0, 0),
    #                ]

    return render_template('signup.html')

@app.route('/signup', methods=['post'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        user_name = request.form['user_name']
        password = request.form['password']
        
        table = dynamodb.Table('login')

        response = table.get_item(
        Key={
                'email': email
            }
        )
        
        # if the email already exists, return a message
        # else, add the new user to the database
        if 'Item' in response:
            msg = "The email already exists"
            return render_template('signup.html', name = msg)
        else:
            table.put_item(
                    Item={
                    'email': email,
                    'user_name': user_name,
                    'password': password
                }
            )
            msg = "Registration Complete. Please Login to your account !"
            return render_template('login.html', msg = msg)
    return render_template('signup.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/check_login', methods = ['GET','POST'])
def check_login():
    if request.method=='POST':
        
        email = request.form['email']
        password = request.form['password']
        
        table = dynamodb.Table('login')
        
        response = table.query(
            KeyConditionExpression=Key('email').eq(email),
            FilterExpression=Attr('password').eq(password)
        )
        items = response['Items']

        # if the email and password match, redirect to the main page
        # else, return a message
        if items:
            return redirect(url_for('main_page', email=email))
        else:
            msg = "email or password is invalid"
            return render_template('login.html', name = msg)
    return render_template("login.html")

@app.route('/logout', methods = ['POST'])
def logout():
    return render_template('login.html')

# pass through the email to the main page
@app.route('/main_page/<email>', methods = ['GET'])
def main_page(email):
    # query the database using email to get the user_name
    table = dynamodb.Table('login')
    response = table.query(KeyConditionExpression=Key('email').eq(email))
    items = response['Items']
    user_name = items[0]['user_name']
    
    return render_template('main_page.html', user_name=user_name, email=email)

# pass through the email on subscription_area that continued with the main page
@app.route('/main_page/<email>/subscription_area', methods = ['GET'])
def subscription_area(email):
    s3 = boto3.client('s3')
    table = dynamodb.Table('subscription')

    response = table.scan(FilterExpression=Attr('email').eq(email))

    items = response['Items']
    
    # if items list is empty, return a message
    # else, get the url of the image from s3
    if not items:
        msg = "You have not subscribed to any stocks yet."
        return render_template('subscription_area.html', email=email, msg=msg)
    
    for item in items:
        
        # remove the space in the artist name
        temp_artist = item['artist'].replace(' ', '')
        
        # generate the same name as the image in s3
        key = f"{temp_artist}.jpg"
        
        # get the url of the image
        url = s3.generate_presigned_url('get_object', Params={'Bucket': 's3830776-assignment1', 'Key': key})
        item['url'] = url

    return render_template('subscription_area.html', email=email, items=items)

# pass through the email on query_area that continued with the main page
@app.route('/main_page/<email>/query_area', methods = ['GET', 'POST'])
def query_area(email):
    if request.method == 'POST':
        title = request.form['title']
        
        # if the year is not empty, convert it to int
        # else, set it to None
        if request.form['year'] != "":
            year = int(request.form['year'])
        else:
            year = None
            
        artist = request.form['artist']
        
        table = dynamodb.Table('music')

        # the if-else statements are used to generate the query based on the input
        # including all the combinations of title, year and artist
        # <title, year, artist>
        # <title, year>
        # <title, artist>
        # <year, artist>
        # <title> only
        # <year> only
        # <artist> only
        # ELSE - return all the items in the table
        if title and year and artist:
            response = table.query(
                KeyConditionExpression=Key('title').eq(title) & Key('artist').eq(artist),
                FilterExpression=Attr('year').eq(year)
            )
        elif title and year:
            response = table.query(
                KeyConditionExpression=Key('title').eq(title),
                FilterExpression=Attr('year').eq(year)
            )
        elif title and artist:
            response = table.query(KeyConditionExpression=Key('title').eq(title) & Key('artist').eq(artist))
        elif year and artist:
            response = table.scan(FilterExpression=Attr('year').eq(year) & Attr('artist').eq(artist))
        elif title:
            response = table.query(KeyConditionExpression=Key('title').eq(title))
        elif year:
            response = table.scan(FilterExpression=Attr('year').eq(year))
        elif artist:
            response = table.scan(FilterExpression=Attr('artist').eq(artist))
        else:
            response = table.scan()

        items = response['Items']

        # if items list is empty, return a message
        if not items:
            msg = "No result is retrieved. Please query again!"
            return render_template('query_area.html', email=email, msg=msg)
        
        # get the url of the image from s3
        s3 = boto3.client('s3')
        for item in items:
            temp_artist = item['artist'].replace(' ', '')
            
            key = f"{temp_artist}.jpg"
            
            url = s3.generate_presigned_url('get_object', Params={'Bucket': 's3830776-assignment1', 'Key': key})
            item['url'] = url

        return render_template('query_area.html', email=email, items=items)
    return render_template('query_area.html', email=email)

# Subscribe action
@app.route('/main_page/<email>/query_area/subscribe', methods=['POST'])
def subscribe(email):
    email = request.form['email']
    title = request.form['title']
    artist = request.form['artist']
    year = request.form['year']
    
    table = dynamodb.Table('subscription')

    response = table.scan(FilterExpression=Attr('email').eq(email) & Attr('title').eq(title) & Attr('artist').eq(artist) & Attr('year').eq(year))
    
    items = response['Items']

    # if items list is empty, return a message
    if items:
        msg = "You already subscribed to this stock!"
        return render_template('query_area.html', email=email, msg=msg)
    
    response = table.scan()

    items = response['Items']

    id = 0 # default id

    # if the subscription table is empty, id starts from 0
    # else, get the max id and add 1 to it
    if not items:
        table.put_item(
            Item={
                'id': id,
                'email': email,
                'title': title,
                'artist': artist,
                'year': year
            }
        )
    else:
        for item in items:
            if item['id'] > id:
                id = item['id']

        id += 1
        table.put_item(
            Item={
                'id': id,
                'email': email,
                'title': title,
                'artist': artist,
                'year': year
            }
        )

    msg = f"You have subscribed song {title}!"
    
    return render_template('query_area.html', email=email, msg=msg)

# Remove action
@app.route('/main_page/<email>/subscription_area/remove', methods=['POST'])
def remove(email):
    title = request.form['title']
    artist = request.form['artist']
    year = request.form['year']
    
    # Find the subscription in DynamoDB
    table = dynamodb.Table('subscription')

    response = table.scan(FilterExpression=Attr('email').eq(email) & Attr('title').eq(title) & Attr('artist').eq(artist) & Attr('year').eq(year))
    
    items = response['Items']
    id = items[0]['id']

    response = table.delete_item(
        Key={
            'id': id
        }
    )

    msg = f"You have removed song {title}!"
    
    # Return a response to the user
    return render_template('subscription_area.html', email=email, msg=msg)

if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)), debug=True)
# [END gae_python3_render_template]
# [END gae_python38_render_template]
