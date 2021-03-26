import datetime
from flask import Flask, render_template, redirect
from google.cloud import datastore
import google.oauth2.id_token
from flask import Flask, render_template, request
from google.auth.transport import requests
import random

app = Flask(__name__)
datastore_client = datastore.Client()
firebase_request_adapter = requests.Request()


@app.route('/delete_address/<int:id>', methods=['POST'])
def deleteAddressFromUser(id):
    id_token = request.cookies.get("token")
    error_message = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token,
                                                                  firebase_request_adapter)
            deleteAddress(claims, id)
        except ValueError as exc:
            error_message = str(exc)
    return redirect('/')


@app.route('/delete_addressv1/<int:id>', methods=['POST'])
def deleteAddressFromUserv1(id):
    id_token = request.cookies.get("token")
    error_message = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token,
                                                                  firebase_request_adapter)
            deleteAddress(claims, id)
        except ValueError as exc:
            error_message = str(exc)
    return redirect('/')


def deleteAddress(claims, id):
    user_info = retrieveUserInfo(claims)
    address_list = user_info['address_list']
    del address_list[id]
    user_info.update({
        'address_list': address_list
    })
    datastore_client.put(user_info)


def deleteAddressv1(claims, id):
    user_info = retrieveUserInfo(claims)
    address_list_keys = user_info['address_list']
    address_key = datastore_client.key('Address', address_list_keys[id])
    datastore_client.delete(address_key)
    del address_list_keys[id]
    user_info.update({
        'address_list': address_list_keys
    })
    datastore_client.put(user_info)


@app.route('/add_address', methods=['POST'])
def addAddress():
    id_token = request.cookies.get("token")
    claims = None
    user_info = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token,
                                                                  firebase_request_adapter)
            user_info = retrieveUserInfo(claims)
            print(request)
            address = createAddress(request.form['address1'], request.form['address2'],
                                    request.form['address3'], request.form['address4'])
            addAddressToUser(user_info, address)
        except ValueError as exc:
            error_message = str(exc)
    return redirect('/')


@app.route('/add_addressv1', methods=['POST'])
def addAddressv1():
    id_token = request.cookies.get("token")
    claims = None
    user_info = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token,
                                                                  firebase_request_adapter)
            user_info = retrieveUserInfo(claims)
            id = createAddress(claims, request.form['address1'],
                               request.form['address2'], request.form['address3'], request.form['address4'])
            addAddressToUser(user_info, id)
        except ValueError as exc:
            error_message = str(exc)
    return redirect('/')


def retrieveUserInfo(claims):
    entity_key = datastore_client.key('UserInfo', claims['email'])
    entity = datastore_client.get(entity_key)
    return entity


@app.route('/edit_user_info', methods=['POST'])
def editUserInfo():
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    user_info = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token,
                                                                  firebase_request_adapter)
            new_string = request.form['string_update']
            new_int = request.form['int_update']
            new_float = request.form['float_update']
            updateUserInfo(claims, new_string, new_int, new_float)
        except ValueError as exc:
            error_message = str(exc)
    return redirect("/")


def addAddressToUser(user_info, address_entity):
    addresses = user_info['address_list']
    addresses.append(address_entity)
    user_info.update({
        'address_list': addresses
    })
    datastore_client.put(user_info)


def createAddress(address1, address2, address3, address4):
    entity = datastore.Entity()
    entity.update({
        'address1': address1,
        'address2': address2,
        'address3': address3,
        'address4': address4
    })
    return entity


def updateUserInfo(claims, new_string, new_int, new_float):
    entity_key = datastore_client.key('UserInfo', claims['email'])
    entity = datastore_client.get(entity_key)
    entity.update({
        'string_value': new_string,
        'int_value': new_int,
        'float_value': new_float
    })
    datastore_client.put(entity)


def retrieveAddresses(user_info):
    # make key objects out of all the keys and retrieve them
    address_ids = user_info['address_list']
    address_keys = []
    for i in range(len(address_ids)):
        address_keys.append(datastore_client.key('Address', address_ids[i]))
    address_list = datastore_client.get_multi(address_keys)
    return address_list


def createUserInfo(claims):
    entity_key = datastore_client.key('UserInfo', claims['email'])
    entity = datastore.Entity(key=entity_key)
    entity.update({
        'email': claims['email'],
        'name': claims['name'],
        'address_list': []
    })

    datastore_client.put(entity)


def retrieveUserInfo(claims):
    entity_key = datastore_client.key('UserInfo', claims['email'])
    entity = datastore_client.get(entity_key)
    return entity


def store_time(email, dt):
    entity = datastore.Entity(key=datastore_client.key('User', email, 'visit'))
    entity.update({'timestamp': dt})
    datastore_client.put(entity)


def fetch_times(email, limit):
    ancestor_key = datastore_client.key('User', email)
    query = datastore_client.query(kind='visit', ancestor=ancestor_key)
    query.order = ['-timestamp']
    times = query.fetch(limit=limit)
    # print(times,ancestor_key)
    return times


def addAddressToUser(user_info, id):
    address_keys = user_info['address_list']
    address_keys.append(id)
    user_info.update({
        'address_list': address_keys
    })
    datastore_client.put(user_info)


def createAddressv1(claims, address1, address2, address3, address4):

    # 63 bit random number that will serve as the key for this address object. not sure why the data store doesn't like 64 bit numbers
    id = random.getrandbits(63)
    entity_key = datastore_client.key('Address', id)
    entity = datastore.Entity(key=entity_key)
    entity.update({
        'address1': address1,
        'address2': address2,
        'address3': address3,
        'address4': address4
    })
    datastore_client.put(entity)
    return id


@app.route('/transaction_add', methods=['POST'])
def transactionAdd():
    id_token = request.cookies.get("token")
    error_message = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token,
                                                                  firebase_request_adapter)
            entity_9 = createDummyData(9)
            entity_10 = createDummyData(10)
            entity_11 = createDummyData(11)
            entity_12 = createDummyData(12)
            transaction = datastore_client.transaction()
            with transaction:
                transaction.put(entity_9)
                transaction.put(entity_10)
                transaction.put(entity_11)
                transaction.put(entity_12)
        except ValueError as exc:
            error_message = str(exc)
    return redirect('/')


@app.route('/multi_delete', methods=['POST'])
def multiDelete():
    id_token = request.cookies.get("token")
    error_message = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token,
                                                                  firebase_request_adapter)
            entity_1_key = datastore_client.key('DummyData', 1)
            entity_2_key = datastore_client.key('DummyData', 2)
            entity_3_key = datastore_client.key('DummyData', 3)
            entity_4_key = datastore_client.key('DummyData', 4)
            datastore_client.delete_multi([entity_1_key, entity_2_key, entity_3_key,
                                           entity_4_key])
        except ValueError as exc:
            error_message = str(exc)
    return redirect('/')


@app.route('/batch_delete', methods=['POST'])
def batchDelete():
    id_token = request.cookies.get("token")
    error_message = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token,
                                                                  firebase_request_adapter)
            entity_5_key = datastore_client.key('DummyData', 5)
            entity_6_key = datastore_client.key('DummyData', 6)
            entity_7_key = datastore_client.key('DummyData', 7)
            entity_8_key = datastore_client.key('DummyData', 8)
            batch = datastore_client.batch()
            with batch:
                batch.delete(entity_5_key)
                batch.delete(entity_6_key)
                batch.delete(entity_7_key)
                batch.delete(entity_8_key)
        except ValueError as exc:
            error_message = str(exc)
    return redirect('/')


@app.route('/batch_add', methods=['POST'])
def batchAdd():
    id_token = request.cookies.get("token")
    error_message = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token,
                                                                  firebase_request_adapter)
            entity_5 = createDummyData(5)
            entity_6 = createDummyData(6)
            entity_7 = createDummyData(7)
            entity_8 = createDummyData(8)
            batch = datastore_client.batch()
            with batch:
                batch.put(entity_5)
                batch.put(entity_6)
                batch.put(entity_7)
                batch.put(entity_8)
        except ValueError as exc:
            error_message = str(exc)
    return redirect('/')


@app.route('/multi_add', methods=['POST'])
def multiAdd():
    id_token = request.cookies.get("token")
    error_message = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token,
                                                                  firebase_request_adapter)
            entity_1 = createDummyData(1)
            entity_2 = createDummyData(2)
            entity_3 = createDummyData(3)
            entity_4 = createDummyData(4)
            datastore_client.put_multi(
                [entity_1, entity_2, entity_3, entity_4])
        except ValueError as exc:
            error_message = str(exc)
    return redirect('/')


def createDummyData(name, id, boolean):
    entity_key = datastore_client.key('DummyData', id)
    entity = datastore.Entity(key=entity_key)
    entity.update({
        'name': name,
        'id': id,
        'boolean': boolean
    })
    return entity


def createDummyDatav1(number):
    entity_key = datastore_client.key('DummyData', number)
    entity = datastore.Entity(key=entity_key)
    entity.update({
        'number': number,
        'squared': number ** 2,
        'cubed': number ** 3
    })
    return entity


@app.route('/query_multiple_attribs', methods=['POST'])
def queryMultipleAttribs():
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    times = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token,
                                                                  firebase_request_adapter)
            query = datastore_client.query(kind='DummyData')
            query.add_filter('id', '<', 4)
            query.add_filter('boolean', '=', True)
            result = query.fetch()
        except ValueError as exc:
            error_message = str(exc)
    return render_template('index.html', user_data=claims, error_message=error_message,
                           data=result)


@app.route('/pull_entity_by_name', methods=['POST'])
def pullEntityByName():
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    times = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token,
                                                                  firebase_request_adapter)
            if request.form['name'] == '':
                return redirect('/')
            name = request.form['name']
            query = datastore_client.query(kind='DummyData')
            query.add_filter('name', '=', name)
            result = query.fetch()
        except ValueError as exc:
            error_message = str(exc)
    return render_template('index.html', user_data=claims, error_message=error_message,
                           data=result)


@app.route('/pull_entity_by_id', methods=['POST'])
def pullEntityById():
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    times = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token,
                                                                  firebase_request_adapter)
            if request.form['id'] == '':
                return redirect('/')
            id = int(request.form['id'])
            query = datastore_client.query(kind='DummyData')
            query.add_filter('id', '=', id)
            result = query.fetch()
        except ValueError as exc:
            error_message = str(exc)
    return render_template('index.html', user_data=claims, error_message=error_message,
                           data=result)


@app.route('/initialise_dummy_data', methods=['POST'])
def initialiseDummyData():
    entity_1 = createDummyData("foo", 1, True)
    entity_2 = createDummyData("bar", 2, False)
    entity_3 = createDummyData("baz", 3, False)
    entity_4 = createDummyData("wookie", 4, True)
    datastore_client.put_multi([entity_1, entity_2, entity_3, entity_4])
    return redirect('/')


@app.route('/')
def root():
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    times = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token,
                                                                  firebase_request_adapter)
            query = datastore_client.query(kind='DummyData')
            result = query.fetch()
        except ValueError as exc:
            error_message = str(exc)
    return render_template('index.html', user_data=claims, error_message=error_message,
                           data=result)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
