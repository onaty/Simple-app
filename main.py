import datetime
from flask import Flask, render_template
from google.cloud import datastore
import google.oauth2.id_token
from flask import Flask, render_template, request
from google.auth.transport import requests

app = Flask(__name__)
datastore_client = datastore.Client()
firebase_request_adapter = requests.Request()


def store_time(email, dt):
    entity = datastore.Entity(key=datastore_client.key('User', email, 'visit'))
    entity.update({'timestamp': dt})
    datastore_client.put(entity)


def fetch_times(email, limit):
    ancestor_key = datastore_client.key('User', email)
    query = datastore_client.query(kind='visit', ancestor=ancestor_key)
    query.order = ['-timestamp']
    times =  query.fetch(limit=limit)
    # print(times,ancestor_key)
    return times


@app.route('/')
def root():
    # query firebase for the request token and set other variables to none for now
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    times = None

    # if we have an ID token then verify it against firebase if it doesn't check out then
    # log the error message that is returned
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token,
            firebase_request_adapter)
            store_time(claims['email'], datetime.datetime.now())
            times = fetch_times(claims['email'], 10)
        
        except ValueError as exc:
            error_message = str(exc)

    # render the template with the last times we have
    return render_template('index.html', user_data=claims, error_message=error_message,times=times)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
