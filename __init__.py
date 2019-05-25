#!/usr/bin/env python
#from __future__ import absolute_import
from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
#from databasesetup import Base, Catalog, CatalogItem, User
from flask import session as login_session

from databasesetup import Base, Catalog, CatalogItem, User
import random
import string
#from oauth2client.client import flow_from_clientsecrets
#from oauth2client.client import FlowExchangeError
#import httplib2
import json
from flask import make_response
import requests
#from apiclient import discovery
from googleapiclient.discovery import build
#from googleapiclient.discovery import build
import httplib2
from oauth2client import client


app = Flask(__name__)

CLIENT_ID = json.loads(
    open('/var/www/catalog/catalog/client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "catalog"
app.secret_key = 'super_secret_key'

# Connect to Database and create database session
#engine = create_engine('sqlite:///catalogitem.db')
engine = create_engine('postgresql://catalog:catalog@localhost/catalog')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(
        random.choice(string.ascii_uppercase + string.digits) for x in range(32))
    login_session['state'] = state
    #return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Obtain authorization code, now compatible with Python3
    request.get_data()
    code = request.data.decode('utf-8')
    CLIENT_SECRET_FILE = '/var/www/catalog/catalog/client_secrets.json'

    credentials = client.credentials_from_clientsecrets_and_code(
    CLIENT_SECRET_FILE,
    ['https://www.googleapis.com/auth/drive.appdata', 'profile', 'email'],
    code)

    http_auth = credentials.authorize(httplib2.Http())
    drive_service = build('drive', 'v3', http=http_auth)
    #appfolder = drive_service.files().get(fileId='appfolder').execute()
    #userid = credentials.id_token['sub']
    #email = credentials.id_token['email']
    

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    # Submit request, parse response - Python3 compatible
    h = httplib2.Http()
    response = h.request(url, 'GET')[1]
    str_response = response.decode('utf-8')
    result = json.loads(str_response)
    
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    
    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    
    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    return output


# User Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user

def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return str(user.id)
    except:
        return None

# DISCONNECT - Revoke a current user's token and reset their login_session


@app.route('/gdisconnect')
def gdisconnect():
        # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        flash('Current user not connected')
        return redirect(url_for('showCatalogs'))

    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200' or result['status'] == '400':
        # Reset the user's sesson.
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        flash('Successfully disconnected.')
        return redirect(url_for('showCatalogs'))
    else:
        flash('Failed to disconnected.')
        return redirect(url_for('showCatalogs'))


# JSON APIs to view Catalog Information
@app.route('/catalog/<int:catalog_id>/item/JSON')
def catalogItemsJSON(catalog_id):
    catalog = session.query(Catalog).filter_by(id=catalog_id).one()
    items = session.query(CatalogItem).filter_by(
        catalog_id=catalog_id).all()
    return jsonify(CatalogItem=[i.serialize for i in items])


@app.route('/catalog/<int:catalog_id>/item/<int:item_id>/JSON')
def catalogItemJSON(catalog_id, item_id):
    Catalog_Item = session.query(CatalogItem).filter_by(id=item_id).one()
    return jsonify(Catalog_Item=Catalog_Item.serialize)


@app.route('/catalog/JSON')
def catalogsJSON():
    catalogs = session.query(Catalog).all()
    return jsonify(catalogs=[r.serialize for r in catalogs])


#Show all catalogs
@app.route('/')
@app.route('/catalog/')
def showCatalogs():
    catalogs = session.query(Catalog).order_by(asc(Catalog.name))
    if 'username' not in login_session:
        return render_template('publiccatalogs.html', catalogs = catalogs)
    else:
        return render_template('catalogs.html', catalogs = catalogs)


# Create a new catalog
@app.route('/catalog/new/', methods=['GET', 'POST'])
def newCatalog():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newCatalog = Catalog(
            name=request.form['name'], user_id=login_session['user_id'])
        session.add(newCatalog)
        flash('New Catalog %s Successfully Created' % newCatalog.name)
        session.commit()
        return redirect(url_for('showCatalogs'))
    else:
        return render_template('newCatalog.html')


# Edit a catalog
@app.route('/catalog/<int:catalog_id>/edit/', methods=['GET', 'POST'])
def editCatalog(catalog_id):
    editedCatalog = session.query(
        Catalog).filter_by(id=catalog_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if str(editedCatalog.user_id) != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to edit this catalog. Please create your own catalog in order to edit.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            editedCatalog.name = request.form['name']
            flash('Catalog Successfully Edited %s' % editedCatalog.name)
            return redirect(url_for('showCatalogs'))
    else:
        return render_template('editCatalog.html', catalog=editedCatalog)


# Delete a catalog
@app.route('/catalog/<int:catalog_id>/delete/', methods=['GET', 'POST'])
def deleteCatalog(catalog_id):
    catalogToDelete = session.query(
        Catalog).filter_by(id=catalog_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if str(catalogToDelete.user_id) != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to delete this catalog. Please create your own catalog in order to delete.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(catalogToDelete)
        flash('%s Successfully Deleted' % catalogToDelete.name)
        session.commit()
        return redirect(url_for('showCatalogs', catalog_id=catalog_id))
    else:
        return render_template('deleteCatalog.html', catalog=catalogToDelete)


# Show a catalog item
@app.route('/catalog/<int:catalog_id>/')
@app.route('/catalog/<int:catalog_id>/item/')
def showItem(catalog_id):
    catalog = session.query(Catalog).filter_by(id=catalog_id).one()
    creator = getUserInfo(catalog.user_id)
    items = session.query(CatalogItem).filter_by(
        catalog_id=catalog_id).all()
    if 'username' not in login_session or str(creator.id) != login_session['user_id']:
        return render_template('publicitem.html', items=items, catalog=catalog)
    else:
        return render_template('item.html', items=items, catalog=catalog, creator=creator)


# Create a new catalog item
@app.route('/catalog/<int:catalog_id>/menu/new/', methods=['GET', 'POST'])
def newCatalogItem(catalog_id):
    if 'username' not in login_session:
        return redirect('/login')
    catalog = session.query(Catalog).filter_by(id=catalog_id).one()
    if login_session['user_id'] != str(catalog.user_id):
        return "<script>function myFunction() {alert('You are not authorized to add items to this catalog. Please create your own catalog in order to add items.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        newItem = CatalogItem(name=request.form['name'], description=request.form['description'], 
                           catalog_id=catalog_id, user_id=catalog.user_id)
        session.add(newItem)
        session.commit()
        flash('New Item %s Item Successfully Created' % (newItem.name))
        return redirect(url_for('showItem', catalog_id=catalog_id))
    else:
        return render_template('newCatalogItem.html', catalog_id=catalog_id)


# Edit a catalog item
@app.route('/catalog/<int:catalog_id>/item/<int:item_id>/edit', methods=['GET', 'POST'])
def editCatalogItem(catalog_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedItem = session.query(CatalogItem).filter_by(id=item_id).one()
    catalog = session.query(Catalog).filter_by(id=catalog_id).one()
    if login_session['user_id'] != str(catalog.user_id):
        return "<script>function myFunction() {alert('You are not authorized to edit catalog items to this catalog. Please create your own catalog in order to edit items.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        session.add(editedItem)
        session.commit()
        flash('Catalog Item Successfully Edited')
        return redirect(url_for('showItem', catalog_id=catalog_id))
    else:
        return render_template('editCatalogItem.html', catalog_id=catalog_id, item_id=item_id, item=editedItem)


# Delete a catalog item
@app.route('/catalog/<int:catalog_id>/item/<int:item_id>/delete', methods=['GET', 'POST'])
def deleteCatalogItem(catalog_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    catalog = session.query(Catalog).filter_by(id=catalog_id).one()
    itemToDelete = session.query(CatalogItem).filter_by(id=item_id).one()
    if login_session['user_id'] != str(catalog.user_id):
        return "<script>function myFunction() {alert('You are not authorized to delete catalog items to this catalog. Please create your own catalog in order to delete items.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Catalog Item Successfully Deleted')
        return redirect(url_for('showItem', catalog_id=catalog_id))
    else:
        return render_template('deleteCatalogItem.html', item=itemToDelete)


if __name__ == '__main__':
    #app.secret_key = 'super_secret_key'
    app.debug = True
    app.run()
