# -*- coding: utf-8 -*-
from flask import Flask, session, jsonify, send_from_directory
from flask import render_template
from flask import Response
from flask import jsonify
from flask import request
from flask import redirect
from flask import abort
from werkzeug import secure_filename
from werkzeug.routing import BaseConverter
from jinja2 import TemplateNotFound
from flask.ext.security import Security, PeeweeUserDatastore, UserMixin, RoleMixin, login_required
from flask.ext.security import *
from flask.ext.sqlalchemy import SQLAlchemy
from flask_mail import Mail
from functools import update_wrapper
from flask import make_response, request, current_app

import gpxpy
import gpxpy.gpx
from shapely.geometry import shape
from shapely.geometry import LineString
from shapely.geometry import Point
import psycopg2
import json
import requests

import urllib
from markupsafe import Markup

import hashlib

from datetime import timedelta

from werkzeug.routing import NumberConverter, ValidationError

# Geoalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, Float
from geoalchemy2 import Geometry
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine


app = Flask(__name__)


# Config file
app.config.from_pyfile('deltur.cfg')
app.url_map.strict_slashes = False # Ignore trailing slash or not in URL(needed for reset password)

# Postgres config
pg_db = app.config['PG_DB']
pg_host = app.config['PG_HOST']
pg_user = app.config['PG_USER']
pg_passwd = app.config['PG_PASSWD']
pg_port = app.config['PG_PORT']


app.debug = True
app.secret_key = '....'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://'+pg_user+':'+pg_passwd+'@'+pg_host+':'+pg_port+'/'+pg_db
app.config['SECURITY_TRACKABLE'] = True
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_RECOVERABLE'] = True #Reset password
#app.config['SECURITY_RESET_URL'] = "/reset"


app.config['SECURITY_CHANGEABLE'] = True #Change password
app.config['SECURITY_SEND_REGISTER_EMAIL'] = True
app.config['SECURITY_PASSWORD_HASH'] = "bcrypt"
app.config['SECURITY_PASSWORD_SALT'] = '$2a$12$byc5TEXXKHqMIP9inxqnQO'

#app.config['SECURITY_RESET_PASSWORD_TEMPLATE'] = "security/login_user.html"

#app.config['REMEMBER_COOKIE_DURATION'] = timedelta(microseconds=-1)


# E-post settings
#app.config['USER_DOES_NOT_EXIST'] = 'Denne brukeren finnes ikke'
app.config['SECURITY_EMAIL_SENDER'] = 'espen@kresendo.no'
app.config['SECURITY_EMAIL_SUBJECT_PASSWORD_RESET'] = 'Instruksjoner for bytte av passord'
app.config['SECURITY_EMAIL_SUBJECT_PASSWORD_NOTICE'] = 'Ditt passord har blitt byttet'
app.config['SECURITY_EMAIL_SUBJECT_REGISTER'] = 'Velkommen til deltur.no'
app.config['SECURITY_EMAIL_SUBJECT_CONFIRM'] = 'Verifiser din e-post adresse'
app.config['SECURITY_EMAIL_SUBJECT_PASSWORD_CHANGE_NOTICE'] = 'Nytt passord hos deltur.no'

app.config['MAIL_SERVER'] = 'smtp.mandrillapp.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'espen@kresendo.no'
app.config['MAIL_PASSWORD'] = 'tnrGGTWmlGS5Gc6AQSnZYg'
app.config['MAIL_DEBUG'] = True
mail = Mail(app)

#app.messages['USER_DOES_NOT_EXIST'] = 'Det finnes ikke noe bruker med denne e-post adressen'

def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator

# Used to encode URLs
@app.template_filter('urlencode')
def urlencode_filter(s):
    if type(s) == 'Markup':
        s = s.unescape()
    s = s.encode('utf8')
    s = urllib.quote_plus(s)
    return Markup(s)


# Accept negative floats as input
# Used in /del/sted/
class NegativeFloatConverter(NumberConverter):
    regex = r'\-?\d+\.\d+'
    num_convert = float
 
    def __init__(self, map, min=None, max=None):
        NumberConverter.__init__(self, map, 0, min, max)
app.url_map.converters['float'] = NegativeFloatConverter


# Create database connection object
db = SQLAlchemy(app)

# Define models
roles_users = db.Table('roles_users',
        db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
        db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    current_login_at = db.Column(db.DateTime())
    last_login_at = db.Column(db.DateTime())
    last_login_ip = db.Column(db.String(255))
    current_login_ip = db.Column(db.String(255))
    login_count = db.Column(db.Integer)
    plan = db.Column(db.String(255))
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))

# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

# Create a user to test with
#@app.before_first_request
#def create_user():
#    db.create_all()
#    user_datastore.create_user(email='matts@nobien.net', password='password')
#    db.session.commit()

Base = declarative_base()

class Point(Base):
    __tablename__ = 'points'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    url = Column(String)
    description = Column(String)
    markertype = Column(String)
    markercolor = Column(String)
    markerpopup = Column(Boolean)
    markerlabel_static = Column(Boolean)
    markerlabel_text = Column(String)
    markersymbol = Column(String)
    image_width = Column(Integer)
    image_height = Column(Integer)
    geo = Column(Geometry('POINT'))

class Line(Base):
    __tablename__ = 'trips'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    #url = Column(String)
    description = Column(String)
    style_color = Column(String)
    style_width = Column(Float)
    style_opacity = Column(Boolean)
    style_start_icon = Column(Boolean)
    style_end_icon = Column(Boolean)
    style_popup = Column(Boolean)
    style_label_text = Column(String)
    geo = Column(Geometry('POINT'))

engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'], echo=True)
Session = sessionmaker(bind=engine)




class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]

app.url_map.converters['regex'] = RegexConverter

# maptypes
# 1 = turkart
# 2 = skikart
# 3 = kartverket
# 4 = satellitt
# 5 = kartverket
mapTypesList = ['turkart','skikart','veikart','topokart', 'satellitt', 'kartverket']




### READ ###


@app.route('/test')
@login_required
def test():
    return current_user.get_auth_token()


@app.route('/<regex("[a-z0-9]+"):hash>/metadata', methods=['GET'])
@login_required
def getHashMetadata(hash):
    try:
        conn = psycopg2.connect("dbname="+pg_db+" user="+pg_user+" password="+pg_passwd+" host="+pg_host+" ")
    except:
        print "Could not connect to database " + pg_db
        
    cursor = conn.cursor()

    sql_string = "select ids from hash where hash=%s"
    cursor.execute(sql_string, (hash,))
    idString = cursor.fetchone()[0]
    conn.commit();

    ids = idString.split("+")
    points = []
    lines = []
    for id in ids:
        if isPoint(id):
            points.append(id)
        else:
            lines.append(id)

    data = {
            'lines': lines,
            'points': points
            }
        
    js = json.dumps(data)
    
    resp = Response(js, status=200, mimetype='application/json')
    
    return resp



@app.route('/<int:id>/metadata')
def getTripMetadata(id):
    try:
        return getLineMetadataFromDB(id)
    except:
        return getPointMetadataFromDB(id)

@app.route('/numMapviews')
@login_required
def getNumMapviews():
    try:
        conn = psycopg2.connect("dbname="+pg_db+" user="+pg_user+" password="+pg_passwd+" host="+pg_host+" ")
    except:
        print "Could not connect to database " + pg_db
        
    cursor = conn.cursor()
    
    sql_string = "select mapviews from \"user\" where id=%s"
    cursor.execute(sql_string, (current_user.id,))
    mapviews = cursor.fetchone()[0]
    conn.commit();

    data = {
                'mapviews'  : mapviews
            }

    js = json.dumps(data)

    resp = Response(js, status=200, mimetype='application/json')

    return resp


@app.route('/numAPI')
@login_required
def getNumAPI():
    try:
        conn = psycopg2.connect("dbname="+pg_db+" user="+pg_user+" password="+pg_passwd+" host="+pg_host+" ")
    except:
        print "Could not connect to database " + pg_db
        
    cursor = conn.cursor()
    
    sql_string = "select api from \"user\" where id=%s"
    cursor.execute(sql_string, (current_user.id,))
    api = cursor.fetchone()[0]
    conn.commit();

    data = {
                'numapicalls'  : api
            }

    js = json.dumps(data)

    resp = Response(js, status=200, mimetype='application/json')

    return resp

@app.route('/numImages')
@login_required
def getNumImages():
    try:
        conn = psycopg2.connect("dbname="+pg_db+" user="+pg_user+" password="+pg_passwd+" host="+pg_host+" ")
    except:
        print "Could not connect to database " + pg_db
        
    cursor = conn.cursor()
    
    sql_string = "select images from \"user\" where id=%s"
    cursor.execute(sql_string, (current_user.id,))
    images = cursor.fetchone()[0]
    conn.commit();

    data = {
                'numimages'  : images
            }

    js = json.dumps(data)

    resp = Response(js, status=200, mimetype='application/json')

    return resp
    
        

@app.route('/<int:id>/geojson')
def getTripGeoJSON(id):
    try:
        increaseLineAccess(id)
        return getLineFromDB(id)
    except:
        increasePointAccess(id)
        return getPointFromDB(id)
        
@app.route('/<int:id>/osm')
def getTripOSM(id):
    if isPoint(id):
        try:
            increaseLineAccess(id)
            r = requests.get('http://beta.deltur.no/feature/deltur_point/'+str(id)+'?service=osm')
            return Response(r.text, mimetype='text/xml')
        except:
            return "Error"
    else:
        try:
            increasePointAccess(id)
            r = requests.get('http://beta.deltur.no/feature/deltur_line/'+str(id)+'?service=osm')
            return Response(r.text, mimetype='text/xml')
        except:
            return "Error"
    
@app.route('/<int:id>/kml')
def getTripKML(id):
    if isPoint(id):
        try:
            increaseLineAccess(id)
            r = requests.get('http://beta.deltur.no/feature/deltur_point/'+str(id)+'?service=kml')
            return Response(r.text, mimetype='text/xml')
        except:
            return "Error"
    else:
        try:
            increasePointAccess(id)
            r = requests.get('http://beta.deltur.no/feature/deltur_line/'+str(id)+'?service=kml')
            return Response(r.text, mimetype='text/xml')
        except:
            return "Error"

@app.route('/<int:id>/csv')
def getTripCSV(id):
    if isPoint(id):
        try:
            increaseLineAccess(id)
            r = requests.get('http://beta.deltur.no/feature/deltur_point/'+str(id)+'?service=csv')
            return Response(r.text, mimetype='text/plain')
        except:
            return "Error"
    else:
        try:
            increasePointAccess(id)
            r = requests.get('http://beta.deltur.no/feature/deltur_line/'+str(id)+'?service=csv')
            return Response(r.text, mimetype='text/plain')
        except:
            return "Error"

@app.route('/<int:id>/gpx')
def getTripGPX(id):
    if isPoint(id):
        try:
            increaseLineAccess(id)
            r = requests.get('http://beta.deltur.no/feature/deltur_point/'+str(id)+'?service=gpx')
            return Response(r.text, mimetype='text/xml')
        except:
            return "Error"
    else:
        try:
            increasePointAccess(id)
            r = requests.get('http://beta.deltur.no/feature/deltur_line/'+str(id)+'?service=gpx')
            return Response(r.text, mimetype='text/xml')
        except:
            return "Error"

@app.route('/hashes')
@login_required
def getAllHashes():
    try:
        conn = psycopg2.connect("dbname="+pg_db+" user="+pg_user+" password="+pg_passwd+" host="+pg_host+" ")
    except:
        print "Could not connect to database " + pg_db
            
    cursor = conn.cursor()
    sql_string = """select hash, ids, dato::date as dato from hash where userid=%s order by id desc"""
    #print sql_string , current_user.id
    cursor.execute(sql_string, [current_user.id],)

    hashes = cursor.fetchall()
    conn.commit();
    
    data = []
    for hash in hashes:
        data.append({
                'hash': hash[0],
                'ids': hash[1],
                'date': str(hash[2])
            })
    js = json.dumps(data)
    
    resp = Response(js, status=200, mimetype='application/json')
    
    return resp

@app.route('/lines')
@login_required
def getAllLines():
    try:
        conn = psycopg2.connect("dbname="+pg_db+" user="+pg_user+" password="+pg_passwd+" host="+pg_host+" ")
    except:
        print "Could not connect to database " + pg_db
            
    cursor = conn.cursor()
    sql_string = """select id, title, description, dato::date from trips where userid=%s order by id desc"""
    #print sql_string , current_user.id
    cursor.execute(sql_string, [current_user.id],)

    lines = cursor.fetchall()
    conn.commit();
    
    data = []
    for line in lines:
        data.append({
                'id': line[0],
                'title': line[1],
                'description': line[2],
                'date': str(line[3]),
            })
    js = json.dumps(data)
    
    resp = Response(js, status=200, mimetype='application/json')
    
    return resp

@app.route('/points')
@login_required
def getAllPoints():
    try:
        conn = psycopg2.connect("dbname="+pg_db+" user="+pg_user+" password="+pg_passwd+" host="+pg_host+" ")
    except:
        print "Could not connect to database " + pg_db
            
    cursor = conn.cursor()
    sql_string = """select id, title, description, dato::date from points where userid=%s order by id desc"""
    #print sql_string , current_user.id
    cursor.execute(sql_string, [current_user.id],)

    points = cursor.fetchall()
    conn.commit();
    
    data = []
    for point in points:
        data.append({
                'id': point[0],
                'title': point[1],
                'description': point[2],
                'date': str(point[3]),
            })
    js = json.dumps(data)
    
    resp = Response(js, status=200, mimetype='application/json')
    
    return resp





### WRITE ###

@app.route('/hash/<regex("[0-9+]+"):ids>')
@login_required
def hashTripToken(ids):
    return hashTrip(request, ids)

@app.route('/hash/<regex("[0-9+]+"):ids>')
@auth_token_required
def hashTripLogin(ids):
    increaseApiAccess(current_user.id)
    return hashTrip(request, ids)


def hashTrip(request, ids):
    try:
        conn = psycopg2.connect("dbname="+pg_db+" user="+pg_user+" password="+pg_passwd+" host="+pg_host+" ")
    except:
        print "Could not connect to database " + pg_db

    hash = hashlib.md5(ids).hexdigest()

    cursor = conn.cursor()

    try:
        sql_string = "insert into hash (hash, ids, userid, dato) VALUES(%s,%s,%s, now())"
        cursor.execute(sql_string, (hash, ids, current_user.id,))
        conn.commit();
        conn.close()

        data = {
                    'hash'  : hash
                }
    except: # Hash already in table
        data = {
                    'hash'  : hash
                }
       
    js = json.dumps(data)

    resp = Response(js, status=200, mimetype='application/json')

    return resp


@app.route('/<regex("[0-9]+"):id>', methods=['DELETE'])
@login_required
def deleteTrip(id):
    try:
        conn = psycopg2.connect("dbname="+pg_db+" user="+pg_user+" password="+pg_passwd+" host="+pg_host+" ")
    except:
        print "Could not connect to database " + pg_db
        
    cursor = conn.cursor()

    if isPoint(id):
        sql_string = "DELETE FROM points where id=%s"
        cursor.execute(sql_string, (id,))
        conn.commit();
    else:
        sql_string = "DELETE FROM trips where id=%s"
        cursor.execute(sql_string, (id,))
        conn.commit();

    resp = Response('', status=204)
    
    return resp

@app.route('/<regex("[a-z0-9]+"):hash>', methods=['DELETE'])
@login_required
def deleteHash(hash):
    try:
        conn = psycopg2.connect("dbname="+pg_db+" user="+pg_user+" password="+pg_passwd+" host="+pg_host+" ")
    except:
        print "Could not connect to database " + pg_db

    cursor = conn.cursor()

    cascade = request.args.get('cascade', '')
    if cascade is not None:
        sql_string = "select ids from hash where hash=%s"
        cursor.execute(sql_string, (hash,))
        idsString = cursor.fetchone()[0]
        ids = idsString.split("+")
        for id in ids:
            deleteTrip(id)
    
    sql_string = "DELETE FROM hash where hash=%s"
    cursor.execute(sql_string, (hash,))
    conn.commit();

    resp = Response('', status=204)
    
    return resp


@app.route('/delturno/sted/<float:lon>/<float:lat>', methods=['POST', 'GET'])
@login_required
def createPointJSONLogin(lon=10, lat=60):
    return createPoint(request, lon, lat)

@app.route('/del/sted/<float:lon>/<float:lat>', methods=['POST', 'GET'])
@auth_token_required
def createPointJSONToken(lon=10, lat=60):
    increaseApiAccess(current_user.id)
    return createPoint(request, lon, lat)

def createPoint(request, lon, lat):
    if request.method == 'POST':
        return addPointToDB(lon, lat, request.json['url'], request.json['description'], "", request.json['title'])
    else:
        return addPointToDB(lon, lat, "", "", "", "")

@app.route('/del/addImageCount', methods=['GET'])
@login_required
def addImage():
    increaseNumImages(current_user.id)
    resp = Response('', status=200, mimetype='application/json')
    return resp

@app.route('/del/addMapviewCount/<regex("[0-9+]+"):ids>', methods=['GET'])
def addMapview(ids):
    increaseNumMapviews(ids)
    resp = Response('', status=200, mimetype='application/json')
    return resp
 
@app.route('/delturno/gpx', methods = ['POST'])
@login_required
def createGPXTripLogin(): 
    return addGPXTrip(request)

@app.route('/del/gpx', methods = ['POST'])
@auth_token_required
def createGPXTripToken():
    increaseApiAccess(current_user.id)
    return addGPXTrip(request)  

def addGPXTrip(request):    
    points = list()
    if request.headers['Content-Type'] == 'application/gpx+xml' or request.headers['Content-Type'] == 'application/gpx+xml; charset=UTF-8':
        try:
            gpx = gpxpy.parse(request.data)
    	    for track in gpx.tracks:
                for segment in track.segments:
                    for point in segment.points:
                        #print 'aPoint at ({0},{1}) -> {2}'.format(point.latitude, point.longitude, point.elevation)
                        p = Point(point.latitude, point.longitude)
                        #p = '({0},{1})'.format(point.latitude, point.longitude)
                        points.append((p.y,p.x))
        except:
            return "Ikke gyldig GPX"
        
        linestring = LineString(points)
        return addLineToDB(linestring, "")
        
    else:
        return "Feil format!"    

@app.route('/delturno/geojson', methods = ['POST'])
@login_required
def createGeoJSONTripLogin():
    return addGeoJSONTrip(request)

@app.route('/del/geojson', methods = ['POST'])
@auth_token_required
def createGeoJSONTripToken():
    increaseApiAccess(current_user.id)
    return addGeoJSONTrip(request)

def addGeoJSONTrip(request):

     # Firefox adds charset automatically    
    if request.headers['Content-Type'] == 'application/json' or request.headers['Content-Type'] == 'application/json; charset=UTF-8':
        
        try:
            try:
                linestring = shape(request.json)
            except:
                linestring = shape(request.json['features'][0]['geometry'])
        except:
            return "Ikke gyldig GeoJSON"
        return addLineToDB(linestring, "")
    else:
        return "Feil format!"    

@app.route('/<int:id>/delturno/copy', methods = ['GET'])
@login_required
def copyIdLogin(id):
    return copyId(request, id)

@app.route('/<int:id>/copy', methods = ['GET'])
@auth_token_required
def copyIdToken(id):
    return copyId(request, id)

def copyId(request, id):
    try:
        conn = psycopg2.connect("dbname="+pg_db+" user="+pg_user+" password="+pg_passwd+" host="+pg_host+" ")
    except:
        print "Could not connect to database " + pg_db
            
    cursor = conn.cursor()

    if copyAllowed(id):
        if isPoint(id):
            sql_string = """INSERT INTO points(title, url, description, markertype, dato, token, geo, markercolor, 
                                    markerpopup, markerlabel_static, markerlabel_text, image_width, image_height, 
                                    userid, accessed) 
                            SELECT title, url, description, markertype, dato, token, geo, markercolor, 
                                    markerpopup, markerlabel_static, markerlabel_text, image_width, image_height, 
                                    %s, 0 FROM points where id=%s RETURNING id
                        """
            cursor.execute(sql_string, (current_user.id, id))
            id = cursor.fetchone()[0]
            conn.commit();
        else:
            sql_string = """INSERT INTO trips(title, dato, geo, style_color, style_width, style_opacity, style_start_icon,
                                            style_end_icon, style_popup, style_label_text, style_label_static, description,
                                            userid, accessed) 
                            SELECT title, dato, geo, style_color, style_width, style_opacity, style_start_icon,
                                            style_end_icon, style_popup, style_label_text, style_label_static, description,
                                            %s, 0 FROM trips where id=%s RETURNING id
                        """
            cursor.execute(sql_string, (current_user.id, id))
            id = cursor.fetchone()[0]
            conn.commit();


        data = {
                'id'  : id
            }
        js = json.dumps(data)

        resp = Response(js, status=200, mimetype='application/json')
        return resp

    else:
        abort(403)

    

def copyAllowed(id):
    try:
        conn = psycopg2.connect("dbname="+pg_db+" user="+pg_user+" password="+pg_passwd+" host="+pg_host+" ")
    except:
        print "Could not connect to database " + pg_db
            
    cursor = conn.cursor()
    if isPoint(id):
        sql_string = "select u.copyallowed from \"user\" u, points p where p.userid=u.id and p.id=%s"
        cursor.execute(sql_string, (id, ))
        copyAllowed = cursor.fetchone()[0]
    else:
        sql_string = "select u.copyallowed from \"user\" u, trips t where t.userid=u.id and t.id=%s"
        cursor.execute(sql_string, (id, ))
        copyAllowed = cursor.fetchone()[0]

    #print "copyallowed: " , copyAllowed
    return copyAllowed

@app.route('/delturno/getCopyAllowed', methods = ['GET'])
@login_required
def getCopyAllowed():
    try:
        conn = psycopg2.connect("dbname="+pg_db+" user="+pg_user+" password="+pg_passwd+" host="+pg_host+" ")
    except:
        print "Could not connect to database " + pg_db
            
    cursor = conn.cursor()
    sql_string = "select copyallowed from \"user\" where id=%s"
    cursor.execute(sql_string, (current_user.id, ))
    copyAllowed = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    cursor.close()

    data = {
            'copyallowed'  : copyAllowed
        }
    js = json.dumps(data)

    resp = Response(js, status=200, mimetype='application/json')
    return resp



@app.route('/setCopyAllowed', methods = ['GET'])
@login_required
def setCopyAllowed():
    return setCopyAllowedInDB(True)

@app.route('/removeCopyAllowed', methods = ['GET'])
@login_required
def removeCopyAllowed():
    return setCopyAllowedInDB(False)

def setCopyAllowedInDB(allowed):
    try:
        conn = psycopg2.connect("dbname="+pg_db+" user="+pg_user+" password="+pg_passwd+" host="+pg_host+" ")
    except:
        print "Could not connect to database " + pg_db
            
    cursor = conn.cursor()
    #print current_user.email
    #print cursor.mogrify("update \"user\" set copyallowed=%s where id=%s;", (allowed, current_user.id ) )
    sql_string = "update \"user\" set copyallowed=%s where id=%s"
    cursor.execute(sql_string, (allowed, current_user.id ))
    conn.commit()
    conn.close()
    cursor.close()
    #copyAllowed = cursor.fetchone()[0]

    data = {
            'copyallowed'  : allowed
        }
    js = json.dumps(data)

    resp = Response(js, status=200, mimetype='application/json')
    return resp



@app.route('/<int:id>/delturno/setStyle', methods = ['POST'])
@login_required
def setStyleLogin(id):
    return setStyle(request, id)

@app.route('/<int:id>/setStyle', methods = ['POST'])
@auth_token_required
def setStyleToken(id):
    if current_user.plan != "free":
        increaseApiAccess(current_user.id)
        return setStyle(request, id)
    else:
        abort(403)



def setStyle(request, id):

     # Firefox adds charset automatically    
    if request.headers['Content-Type'] == 'application/json' or request.headers['Content-Type'] == 'application/json; charset=UTF-8':
        try:
            conn = psycopg2.connect("dbname="+pg_db+" user="+pg_user+" password="+pg_passwd+" host="+pg_host+" ")
        except:
            print "Could not connect to database " + pg_db
                
        cursor = conn.cursor()

        # Get the JSON data sent
        jsondata = request.data

        # Convert the JSON data into a Python structure
        data = json.loads(jsondata)


        if isPoint(id):
            session = Session()
            session._model_changes = {} # Fix for blending flask-sqlalchemy and pure sqlalchemy/geoalchemy
            point = session.query(Point).filter_by(id=id).first()
            if data.get("markercolor"):
                point.markercolor = data["markercolor"]
            if data.get("markersymbol"):
                point.markersymbol = data["markersymbol"]
            if data.get("markerType"):
                point.markertype = data["markerType"]

            if data.get("label"):
                if data["label"].get("static"):
                    point.markerlabel_static = data["label"]["static"]
                if data["label"].get("text"):
                    point.markerlabel_text = data["label"]["text"]
            
            if data.get("popup"):
                if data["popup"].get("image"):
                    if data["popup"]["image"].get("url"):
                        point.url = data["popup"]["image"]["url"]
                    point.image_height = -1
                    if data["popup"]["image"].get("width"):
                        point.image_width = data["popup"]["image"]["width"]
                if data["popup"].get("show"):
                    point.markerpopup = data["popup"]["show"]
                if data["popup"].get("title"):
                    point.title = data["popup"]["title"]
                if data["popup"].get("description"):
                    point.description = data["popup"]["description"]
            session.commit();

        else:
            session = Session()
            session._model_changes = {} # Fix for blending flask-sqlalchemy and pure sqlalchemy/geoalchemy
            line = session.query(Line).filter_by(id=id).first()
            if data.get("color"):
                line.style_color = data["color"]
            if data.get("width"):
                line.style_width = data["width"]
            if data.get("opacity"):
                line.style_opacity = data["opacity"]
            if data.get("start_icon"):
                line.style_start_icon = data["start_icon"]
            if data.get("end_icon"):
                line.style_end_icon = data["end_icon"]
            if data.get("popup"):
                if data["popup"].get("show"):
                    line.style_popup = data["popup"]["show"]
                if data["popup"].get("title"):
                    line.title = data["popup"]["title"]
                if data["popup"].get("description"):
                    line.description = data["popup"]["description"]
            if data.get("label"):
                if data["label"].get("text"):
                    line.style_label_text = data["label"]["text"]
            session.commit();

            sql_string = """update trips set style_color=%s, style_width=%s, style_opacity=%s, style_start_icon=%s, 
                       style_end_icon=%s, style_popup=%s, title=%s, description=%s, style_label_text=%s
                        where id=%s"""
            #cursor.execute(sql_string, (data["color"], data["width"], data["opacity"], data["start_icon"], data["end_icon"], data["popup"]["show"], data["popup"]["title"], data["popup"]["description"], data["label"]["text"], id,))

        
        try:
            data = {
                'status'  : "success"
            }
        except:
            data = {
                'status'  : "failure"
            }

        conn.commit()
        conn.close()
        cursor.close()

        js = json.dumps(data)

        resp = Response(js, status=200, mimetype='application/json')

        return resp
    else:
        return "Feil format!"    



### TEMPLATES ###

@app.route('/<regex("[0-9+]+"):ids>/')
@app.route('/<regex("[0-9+]+"):ids>/<string:mapType>/')
def getTripHTML(ids, mapType='topokart'):
    map = mapTypesList.index(mapType)

    showLogo = showLogoInMap(ids)

    return render_template('tur.html', mapType=map, idList=ids, showLogo=showLogo)



@app.route('/<regex("[a-z0-9]+"):hash>/tilejson.json')
def getTilejson(hash):
    try:
        conn = psycopg2.connect("dbname="+pg_db+" user="+pg_user+" password="+pg_passwd+" host="+pg_host+" ")
    except:
        print "Could not connect to database " + pg_db
        
    cursor = conn.cursor()

    sql_string = "select tilejson from hash where hash=%s"
    cursor.execute(sql_string, (hash,))
    tilejson = cursor.fetchone()[0]
    if tilejson == '':
        tilejson = json.dumps({})
    conn.commit();
    print tilejson

    resp = Response(tilejson, status=200, mimetype='application/json')
    return resp

@app.route('/<regex("[a-z0-9]+"):hash>/tilejson.json', methods = ['PUT'])
def setTilejson(hash):
    try:
        conn = psycopg2.connect("dbname="+pg_db+" user="+pg_user+" password="+pg_passwd+" host="+pg_host+" ")
    except:
        print "Could not connect to database " + pg_db
        
    cursor = conn.cursor()

    if request.headers['Content-Type'] == 'application/json' or request.headers['Content-Type'] == 'application/json; charset=UTF-8':
        print "UPDATE"
        sql_string = "UPDATE hash set tilejson=%s where hash=%s"
        print request.data
        cursor.execute(sql_string, (request.data, hash, ))
        conn.commit();

    resp = Response('{"result": "success"}', status=200, mimetype='application/json')
    return resp

@app.route('/<regex("[a-z0-9]+"):hash>/tilejson.retina.json', methods = ['PUT'])
def setTilejsonRetina(hash):
    try:
        conn = psycopg2.connect("dbname="+pg_db+" user="+pg_user+" password="+pg_passwd+" host="+pg_host+" ")
    except:
        print "Could not connect to database " + pg_db
        
    cursor = conn.cursor()

    if request.headers['Content-Type'] == 'application/json' or request.headers['Content-Type'] == 'application/json; charset=UTF-8':
        #print "UPDATE"
        sql_string = "UPDATE hash set tilejson_retina=%s where hash=%s"
        #print request.data
        cursor.execute(sql_string, (request.data, hash, ))
        conn.commit();

    resp = Response('{"result": "success"}', status=200, mimetype='application/json')
    return resp

@app.route('/<regex("[a-z0-9]+"):hash>/tilejson.retina.json')
def getRetinaTilejson(hash):
    try:
        conn = psycopg2.connect("dbname="+pg_db+" user="+pg_user+" password="+pg_passwd+" host="+pg_host+" ")
    except:
        print "Could not connect to database " + pg_db
        
    cursor = conn.cursor()

    sql_string = "select tilejson_retina from hash where hash=%s"
    cursor.execute(sql_string, (hash,))
    tilejson = cursor.fetchone()[0]

    # If retina is not set, just return regular tilejson
    if tilejson=='':
        sql_string = "select tilejson from hash where hash=%s"
        cursor.execute(sql_string, (hash,))
        tilejson = cursor.fetchone()[0]
        if tilejson == '':
            tilejson = json.dumps({})

    conn.commit();

    resp = Response(tilejson, status=200, mimetype='application/json')
    return resp
    
@app.route('/<regex("[0-9+]+"):ids>/embed/')
@app.route('/<regex("[0-9+]+"):ids>/embed/<string:mapType>/')
def getTripEmbed(ids, mapType='topokart'):
    map = mapTypesList.index(mapType)

    showLogo = showLogoInMap(ids)
    plan = getLowestPlan(ids)

    embedType = request.args.get('embedType', '')
    
    if plan != "noreg":
        if embedType != '':
            if plan == "expert":
                try:
                    return render_template('embeds/' + embedType + '.html', mapType=map, idList=ids)
                except TemplateNotFound:
                    return render_template('404.html'), 404
            else:
                return render_template('404.html'), 404
        else:
            return render_template('embeds/index.html', mapType=map, idList=ids, showLogo=showLogo)
    else:
        abort(403)
    

# Hash input
#[a-z0-9]+
@app.route('/<regex("^([0-9]+[a-zA-Z]+|[a-zA-Z]+[0-9]+)[0-9a-zA-Z]*$"):hash>/')
@app.route('/<regex("^([0-9]+[a-zA-Z]+|[a-zA-Z]+[0-9]+)[0-9a-zA-Z]*$"):hash>/<string:mapType>/')
def getTripHTMLByHash(hash, mapType='topokart'):
    try:
        conn = psycopg2.connect("dbname="+pg_db+" user="+pg_user+" password="+pg_passwd+" host="+pg_host+" ")
    except:
        print "Could not connect to database " + pg_db
        
    cursor = conn.cursor()

    sql_string = "select ids from hash where hash=%s"
    cursor.execute(sql_string, (hash,))
    idString = cursor.fetchone()[0]
    conn.commit();

    showLogo = showLogoInMap(idString)

    if mapType == "custom":
        map = -1
    else:
        map = mapTypesList.index(mapType)
    return render_template('tur.html', mapType=map, idList=idString, hash=hash, showLogo=showLogo)

@app.route('/<regex("[a-z0-9]+"):hash>/embed/')
@app.route('/<regex("[a-z0-9]+"):hash>/embed/<string:mapType>/')
def getTripEmbedByHash(hash, mapType='topokart'):

    #Check if there is a tilejson set
    if mapType == "custom":
        map = -1
    else:
        map = mapTypesList.index(mapType)

    try:
        conn = psycopg2.connect("dbname="+pg_db+" user="+pg_user+" password="+pg_passwd+" host="+pg_host+" ")
    except:
        print "Could not connect to database " + pg_db
        
    cursor = conn.cursor()


    sql_string = "select ids from hash where hash=%s"
    cursor.execute(sql_string, (hash,))
    idString = cursor.fetchone()[0]
    conn.commit();

    showLogo = showLogoInMap(idString)
    plan = getLowestPlan(idString)

    if plan != "noreg":
        embedType = request.args.get('embedType', '')
        if embedType != '':
            if plan == "expert":
                try:
                    return render_template('embeds/' + embedType + '.html', mapType=map, idList=idString, hash=hash)
                except TemplateNotFound:
                    return render_template('404.html'), 404
            else:   
                return render_template('404.html'), 404
        else:
            return render_template('embeds/index.html', mapType=map, idList=idString, hash=hash, showLogo=showLogo)
    else:
        abort(403)
    

@app.route('/del/kml/', methods = ['POST'])
def createKMLTrip():
    
    return addLineToDB(linestring, "")
    

@app.route('/editer/')
def edit():
    return render_template('advanced_fullscreen.html')    

    
@app.route('/elev/elevationprofile.json', methods = ['POST'])
def elev():
    return redirect("http://localhost/elev/elevationprofile.json")
    
@app.route('/pro/')
def pro():
    return render_template('pro.html')
    
@app.route('/registrer/')
def register():
    return render_template('register.html')

@app.route('/terms/')
def terms():
    return render_template('terms.html')


@app.route('/')
def home():
    #return render_template('index.html')
    return render_template('infoside/index.html')


@app.route('/closed/')
def closedTrip():
    return render_template('closedTrip.html')

#@app.route('/info')
#def infohome():
#    return render_template('infoside/index.html')

@app.route('/info')
def infoexplore():
    return render_template('infoside/explore.html')
@app.route('/priser')
def infopriser():
    return render_template('infoside/plans.html')
@app.route('/eksempler')
def infoeksempler():
    return render_template('infoside/eksempler.html')
@app.route('/api')
def infoapi():
    return render_template('infoside/api.html')
@app.route('/faq')
def infofaq():
    return render_template('infoside/faq.html')
@app.route('/kontakt')
def infokontakt():
    return render_template('infoside/contact.html')
@app.route('/brukeravtale')
def infoterms():
    return render_template('infoside/terms.html')
@app.route('/personvern')
def infoprivacypolicy():
    return render_template('infoside/privacy_policy.html')
 

@app.route('/admin')
@login_required
def adminIndex():
    return render_template('admin/index.html')
@app.route('/admin/abbonement')
@login_required
def adminInvoice():
    return render_template('admin/invoice.html')
@app.route('/admin/innstillinger')
@login_required
def adminSettings():
    return render_template('admin/settings.html')
@app.route('/admin/trips')
@login_required
def adminTrips():
    return render_template('admin/trips.html')
@app.route('/admin/tools')
@login_required
def adminTools():
    return render_template('admin/tools.html')

 ### UTILITY FUNCTIONS ### 

def insertUser(_id):
    try:
        conn = psycopg2.connect("dbname="+pg_db+" user="+pg_user+" password="+pg_passwd+" host="+pg_host+" ")
    except:
        print "Could not connect to database " + pg_db
            
    cursor = conn.cursor()

    if isPoint(_id):
        sql_string = "UPDATE points set userid=%s where id=%s"
        #print sql_string , " ",  current_user.id , " ",  _id
        cursor.execute(sql_string, (current_user.id, _id))
        conn.commit();
    else:
        sql_string = "UPDATE trips set userid=%s where id=%s"
        #print sql_string
        cursor.execute(sql_string, (current_user.id, _id))
        conn.commit();

    
def addPointToDB(lon, lat, url, description, markerType, title):
    try:
        conn = psycopg2.connect("dbname="+pg_db+" user="+pg_user+" password="+pg_passwd+" host="+pg_host+" ")
    except:
        print "Could not connect to database " + pg_db
            
    cursor = conn.cursor()

    sql_string = "INSERT INTO points(dato, title, markerType, url, description, geo) VALUES (now(), %s,%s,%s,%s, ST_GEOMFROMTEXT('POINT(%s %s)', 4326) ) RETURNING id;"
    cursor.execute(sql_string, (title, "", url, description, lat, lon))
    id = cursor.fetchone()[0]
    conn.commit();

    # Update table with user info
    if current_user.is_authenticated():
        insertUser(id)
    
    
    data = {
            'id'  : id
        }
    js = json.dumps(data)

    resp = Response(js, status=200, mimetype='application/json')

    return resp
    
    
    
def addLineToDB(line, title):
    try:
        conn = psycopg2.connect("dbname="+pg_db+" user="+pg_user+" password="+pg_passwd+" host="+pg_host+" ")
    except:
        print "Could not connect to database " + pg_db
            
    cursor = conn.cursor()

    sql_string = "INSERT INTO trips(dato, title, geo) VALUES (now(), %s,ST_MULTI(ST_GEOMFROMTEXT(%s, 4326))) RETURNING id;"
    cursor.execute(sql_string, (title, line.wkt))
    id = cursor.fetchone()[0]
    conn.commit();

    # Update table with user info
    if current_user.is_authenticated():
        insertUser(id)
    
    data = {
            'id'  : id
        }
    js = json.dumps(data)

    resp = Response(js, status=200, mimetype='application/json')

    return resp
    
def getPointFromDB(id):
    try:
        conn = psycopg2.connect("dbname="+pg_db+" user="+pg_user+" password="+pg_passwd+" host="+pg_host+" ")
    except:
        print "Could not connect to database " + pg_db
            
    cursor = conn.cursor()
    
    sql_string = "Select st_asgeojson(geo) from points where id=%s"
    cursor.execute(sql_string, (id,))
    geojson = cursor.fetchone()[0]
    conn.commit();
    
    resp = Response(geojson, status=200, mimetype='application/json')
    
    return resp
        
def getLineFromDB(id):
    try:
        conn = psycopg2.connect("dbname="+pg_db+" user="+pg_user+" password="+pg_passwd+" host="+pg_host+" ")
    except:
        print "Could not connect to database " + pg_db
            
    cursor = conn.cursor()
    
    sql_string = "Select st_asgeojson(st_linemerge(geo)) from trips where id=%s"
    cursor.execute(sql_string, (id,))
    geojson = cursor.fetchone()[0]
    conn.commit();
    
    resp = Response(geojson, status=200, mimetype='application/json')
    
    return resp
    
def getPointMetadataFromDB(id):
    try:
        conn = psycopg2.connect("dbname="+pg_db+" user="+pg_user+" password="+pg_passwd+" host="+pg_host+" ")
    except:
        print "Could not connect to database " + pg_db
            
    cursor = conn.cursor()
    
    sql_string = """Select url, description, title, markerType, markersymbol, 
                    markerpopup, markerlabel_static, markerlabel_text, image_height, 
                    image_width, st_x(geo), st_y(geo), markercolor, 14-(now()::date-dato::date) as lifespan, userid 
                    from points where id=%s"""
    cursor.execute(sql_string, (id,))
    res = cursor.fetchone()
    conn.commit();

    # Check remaining days
    remaining_days = res[13]
    userid = res[14]
    if userid is not None:
        sql_check_plan = 'select plan from "user" where id=%s'
        cursor.execute(sql_check_plan, (userid,))
        userPlan = cursor.fetchone()[0]
    else: 
        userPlan = "noreg"
    if userPlan != "noreg":
        remaining_days = -1

    data = {
            'id': id,
            'lat': res[11],
            'lon': res[10],
            'remaining_days': remaining_days,
            'style': {
                'markercolor': res[12],
                'markerType':res[3],
                'markersymbol':res[4],
                'popup': {
                    'show':res[5],
                    'title':res[2],
                    'description':res[1],
                    'image': {
                        'url':res[0],
                        #'height':res[8],
                        'width':res[9]
                    },
                },
                'label': {
                    'static':res[6],
                    'text':res[7]
                }
            }
        }
    js = json.dumps(data)
    
    resp = Response(js, status=200, mimetype='application/json')
    
    return resp
    
    
def getLineMetadataFromDB(id):
    try:
        conn = psycopg2.connect("dbname="+pg_db+" user="+pg_user+" password="+pg_passwd+" host="+pg_host+" ")
    except:
        print "Could not connect to database " + pg_db
            
    cursor = conn.cursor()
    
    sql_string = "Select title, description, style_color, style_width, style_opacity, style_start_icon, style_end_icon, style_popup, style_label_text, 14-(now()::date-dato::date) as lifespan, userid  from trips where id=%s"
    #print sql_string
    cursor.execute(sql_string, (id,))
    res = cursor.fetchone()
    conn.commit();

    # Check remaining days
    remaining_days = res[9]
    userid = res[10]
    if userid is not None:
        sql_check_plan = 'select plan from "user" where id=%s'
        cursor.execute(sql_check_plan, (userid,))
        userPlan = cursor.fetchone()[0]
    else: 
        userPlan = "noreg"
    if userPlan != "noreg":
        remaining_days = -1

    
    data = {
            'id': id,
            'remaining_days': remaining_days,
            'style': {
                'popup': {
                    'show':res[7],
                    'title':res[0],
                    'description':res[1],
                },
                'label': {
                    'text': res[8]
                },
                'color':res[2],
                'width':res[3],
                'opacity':res[4],
                'start_icon':res[5],
                'end_icon':res[6]
                #'label': {
                #    'static':res[7],
                #    'text':res[8]
                #}
            }
        }
    js = json.dumps(data)
    
    resp = Response(js, status=200, mimetype='application/json')
    
    return resp
    
def isPoint(id):
    try:
        conn = psycopg2.connect("dbname="+pg_db+" user="+pg_user+" password="+pg_passwd+" host="+pg_host+" ")
    except:
        print "Could not connect to database " + pg_db
        
    cursor = conn.cursor()
    
    sql_string = "Select count(*) from points where id=%s"
    cursor.execute(sql_string, (id,))
    res = cursor.fetchone()[0]
    conn.commit();
    
    if res == 1:
        return True
    else:
        return False

def increaseLineAccess(id):
    try:
        conn = psycopg2.connect("dbname="+pg_db+" user="+pg_user+" password="+pg_passwd+" host="+pg_host+" ")
    except:
        print "Could not connect to database " + pg_db
        
    cursor = conn.cursor()
    
    sql_string = "update trips set accessed=accessed+1 where id=%s"
    cursor.execute(sql_string, (id,))
    conn.commit();

def increasePointAccess(id):
    try:
        conn = psycopg2.connect("dbname="+pg_db+" user="+pg_user+" password="+pg_passwd+" host="+pg_host+" ")
    except:
        print "Could not connect to database " + pg_db
        
    cursor = conn.cursor()
    
    sql_string = "update points set accessed=accessed+1 where id=%s"
    cursor.execute(sql_string, (id,))
    conn.commit();

def increaseApiAccess(id):
    try:
        conn = psycopg2.connect("dbname="+pg_db+" user="+pg_user+" password="+pg_passwd+" host="+pg_host+" ")
    except:
        print "Could not connect to database " + pg_db
        
    cursor = conn.cursor()
    
    sql_string = "update \"user\" set api=api+1 where id=%s"
    cursor.execute(sql_string, (id,))
    conn.commit();

def increaseNumImages(id):
    try:
        conn = psycopg2.connect("dbname="+pg_db+" user="+pg_user+" password="+pg_passwd+" host="+pg_host+" ")
    except:
        print "Could not connect to database " + pg_db
        
    cursor = conn.cursor()
    
    sql_string = "update \"user\" set images=images+1 where id=%s"
    cursor.execute(sql_string, (id,))
    conn.commit();

def increaseNumMapviews(idString):
    try:
        conn = psycopg2.connect("dbname="+pg_db+" user="+pg_user+" password="+pg_passwd+" host="+pg_host+" ")
    except:
        print "Could not connect to database " + pg_db
        
    cursor = conn.cursor()

    userids = []
    ids = idString.split("+")
    for id in ids:
        if isPoint(id):
            sql_string = "select userid from points where id=%s"
        else:
            sql_string = "select userid from trips where id=%s"                    
        cursor.execute(sql_string, (id,))
        userids.append(cursor.fetchone()[0])

    for userid in set(userids):
        sql_string = "update \"user\" set mapviews=mapviews+1 where id=%s"
        cursor.execute(sql_string, (userid,))
        conn.commit();

def showLogoInMap(idString):
    try:
        conn = psycopg2.connect("dbname="+pg_db+" user="+pg_user+" password="+pg_passwd+" host="+pg_host+" ")
    except:
        print "Could not connect to database " + pg_db
        
    cursor = conn.cursor()

    ids = idString.split("+")
    showLogo = False
    for id in ids:
        if isPoint(id):
            sql_string = "select p.userid, u.plan from points p, \"user\" u where p.id=%s and p.userid=u.id"
        else:
            sql_string = "select t.userid, u.plan from trips t, \"user\" u where t.id=%s and t.userid=u.id"                    
        cursor.execute(sql_string, (id,))

        plan = cursor.fetchone()[1]
        if plan == "noreg" or plan == "free" or plan== "standard":
            showLogo = True;

    return showLogo;

def getLowestPlan(idString):

    try:
        conn = psycopg2.connect("dbname="+pg_db+" user="+pg_user+" password="+pg_passwd+" host="+pg_host+" ")
    except:
        print "Could not connect to database " + pg_db
        
    cursor = conn.cursor()

    ids = idString.split("+")
    lowestplan = "expert"
    for id in ids:
        if isPoint(id):
            sql_string = "select p.userid, u.plan from points p, \"user\" u where p.id=%s and p.userid=u.id"
        else:
            sql_string = "select t.userid, u.plan from trips t, \"user\" u where t.id=%s and t.userid=u.id"                    
        cursor.execute(sql_string, (id,))

        plan = cursor.fetchone()[1]
        if lowestplan=="expert":
            if plan == "noreg":
                lowestplan = "noreg"
            if plan == "free":
                lowestplan = "free"
            if plan == "standard":
                lowestplan = "standard"
            if plan == "pro":
                lowestplan = "pro"
        if lowestplan=="pro":
            if plan == "noreg":
                lowestplan = "noreg"
            if plan == "free":
                lowestplan = "free"
            if plan == "standard":
                lowestplan = "standard"
        if lowestplan=="standard":
            if plan == "noreg":
                lowestplan = "noreg"
            if plan == "free":
                lowestplan = "free"
        if lowestplan=="free":
            if plan == "noreg":
                lowestplan = "noreg"
            

    return lowestplan;

import xmltodict
@app.route('/ssrSok')
def ssrSok():
    query = request.args.get('query', '')
    #r = requests.get('https://ws.geonorge.no/SKWS3Index/ssr/sok?navn='+query+'*&antPerSide=9&epsgKode=4258&eksakteForst=true')
    r = requests.get('http://beta.turkompisen.no/search/ssr?query='+query)
    #doc = xmltodict.parse(r.text)
    js = r.text #json.dumps(r.text)

    resp = Response(js, status=200, mimetype='application/json')
    return resp
    
       

"""
@app.route('/robots.txt')
@app.route('/sitemap.xml')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])

@app.route('/css/images/markers-soft.png')
@app.route('/css/images/markers-shadow.png')
@app.route('/css/images/markers-soft@2x.png')
@app.route('/css/images/markers-shadow@2x.png')
@crossdomain(origin='*')
def static_cors_from_root():
    return send_from_directory(app.static_folder, request.path[1:])


import os
@app.route('/fontawesome/fonts/<path:path>')
@crossdomain(origin='*')
def static_proxy(path):
    # send_static_file will guess the correct MIME type
    return app.send_static_file(os.path.join('fontawesome/fonts', path))
"""


