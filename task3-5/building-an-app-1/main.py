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

from flask import Flask, render_template, request, flash, redirect, url_for

import key_configer as keys

import boto3

from boto3.dynamodb.conditions import Key, Attr

app = Flask(__name__)

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

@app.route('/check_login',methods = ['post'])
def check_login():
    if request.method=='POST':
        
        email = request.form['email']
        password = request.form['password']
        
        table = dynamodb.Table('login')
        response = table.query(
            KeyConditionExpression=Key('email').eq(email)
        )
        items = response['Items']
        # print(items[0]['password'])

        if password == items[0]['password']:
            
            return redirect(url_for('main_page', name=items[0]['user_name'], email = email))
        else:
            msg = "email or password is invalid"
            return render_template('login.html', name = msg)
    return render_template("login.html")

@app.route('/logout', methods = ['post'])
def logout():
    return render_template('login.html')

@app.route('/main_page/<email>')
def main_page(email):
    return render_template('main_page.html', email=email)

@app.route('/main_page/<email>/subscription_area')
def subscription_area(email):
    s3 = boto3.client('s3')
    table = dynamodb.Table('subscription')

    response = table.query(
            KeyConditionExpression=Key('email').eq(email)
        )

    items = response['Items']
    
    # if items list is empty, return a message
    if not items:
        msg = "You have not subscribed to any stocks yet."
        return render_template('subscription_area.html', email=email, msg=msg)
    
    for item in items:
        
        temp_artist = item['artist'].replace(' ', '')
        
        key = f"{temp_artist}.jpg"
        
        url = s3.generate_presigned_url('get_object', Params={'Bucket': 's3830776-assignment1', 'Key': key})
        item['url'] = url

    return render_template('subscription_area.html', email=email, items=items)

@app.route('/main_page/<email>/query_area', methods = ['GET', 'POST'])
def query_area(email):
    if request.method == 'POST':
        title = request.form['title']
        if request.form['year'] != "":
            year = int(request.form['year'])
        else:
            year = None
        artist = request.form['artist']
        
        table = dynamodb.Table('music')

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
            response = table.query(
                KeyConditionExpression=Key('title').eq(title) & Key('artist').eq(artist)
            )
        elif year and artist:
            response = table.scan(FilterExpression=Attr('year').eq(year) & Attr('artist').eq(artist))
        elif title:
            response = table.query(
                KeyConditionExpression=Key('title').eq(title)
            )
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
        
        s3 = boto3.client('s3')
        for item in items:
            temp_artist = item['artist'].replace(' ', '')
            
            key = f"{temp_artist}.jpg"
            
            url = s3.generate_presigned_url('get_object', Params={'Bucket': 's3830776-assignment1', 'Key': key})
            item['url'] = url

        return render_template('query_area.html', email=email, items=items)
    return render_template('query_area.html', email=email)

if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
# [END gae_python3_render_template]
# [END gae_python38_render_template]
