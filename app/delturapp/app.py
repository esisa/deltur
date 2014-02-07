# -*- coding: utf-8 -*-
from flask import Flask, session, jsonify
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

pg_db = "deltur"
pg_host = "localhost"
pg_user = "deltur"
pg_passwd = "deltur._01"
pg_port = "5432"


app = Flask(__name__)
app.debug = True
app.secret_key = '....'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://deltur:dsfdsfdsdeltsur._01@localhost:5432/deltur'
app.config['SECURITY_TRACKABLE'] = True
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_RECOVERABLE'] = False #Reset password
app.config['SECURITY_CHANGEABLE'] = False #Change password
app.config['SECURITY_SEND_REGISTER_EMAIL'] = False
app.config['SECURITY_PASSWORD_HASH'] = "bcrypt"
app.config['SECURITY_PASSWORD_SALT'] = '$2a$12$byc5TEXXKHqMIP9inxqnQO'

app.config['MAIL_SERVER'] = 'smtp.mandrillapp.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'espen@kresendo.no'
app.config['MAIL_PASSWORD'] = 'tnrGGTWmlGS5Gc6AQSnZYg'
#mail = Mail(app)



#app.messages['USER_DOES_NOT_EXIST'] = 'Det finnes ikke noe bruker med denne e-post adressen'



# Used to encode URLs
@app.template_filter('urlencode')
def urlencode_filter(s):
    if type(s) == 'Markup':
        s = s.unescape()
    s = s.encode('utf8')
    s = urllib.quote_plus(s)
    return Markup(s)


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
# 4 = kartverket



mapTypesList = ['turkart','skikart','veikart','topokart', 'satellitt', 'kartverket']




### READ ###


@app.route('/test')
@login_required
def test():
    return current_user.get_auth_token()

@app.route('/<int:id>/metadata')
def getTripMetadata(id):
    try:
        return getLineMetadataFromDB(id)
    except:
        return getPointMetadataFromDB(id)
        

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
            r = requests.get('http://deltur.no/feature/deltur_point/'+str(id)+'?service=osm')
            return Response(r.text, mimetype='text/xml')
        except:
            return "Error"
    else:
        try:
            increasePointAccess(id)
            r = requests.get('http://deltur.no/feature/deltur_line/'+str(id)+'?service=osm')
            return Response(r.text, mimetype='text/xml')
        except:
            return "Error"
    
@app.route('/<int:id>/kml')
def getTripKML(id):
    if isPoint(id):
        try:
            increaseLineAccess(id)
            r = requests.get('http://deltur.no/feature/deltur_point/'+str(id)+'?service=kml')
            return Response(r.text, mimetype='text/xml')
        except:
            return "Error"
    else:
        try:
            increasePointAccess(id)
            r = requests.get('http://deltur.no/feature/deltur_line/'+str(id)+'?service=kml')
            return Response(r.text, mimetype='text/xml')
        except:
            return "Error"

@app.route('/<int:id>/csv')
def getTripCSV(id):
    if isPoint(id):
        try:
            increaseLineAccess(id)
            r = requests.get('http://deltur.no/feature/deltur_point/'+str(id)+'?service=csv')
            return Response(r.text, mimetype='text/plain')
        except:
            return "Error"
    else:
        try:
            increasePointAccess(id)
            r = requests.get('http://deltur.no/feature/deltur_line/'+str(id)+'?service=csv')
            return Response(r.text, mimetype='text/plain')
        except:
            return "Error"

@app.route('/<int:id>/gpx')
def getTripGPX(id):
    if isPoint(id):
        try:
            increaseLineAccess(id)
            r = requests.get('http://deltur.no/feature/deltur_point/'+str(id)+'?service=gpx')
            return Response(r.text, mimetype='text/xml')
        except:
            return "Error"
    else:
        try:
            increasePointAccess(id)
            r = requests.get('http://deltur.no/feature/deltur_line/'+str(id)+'?service=gpx')
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
    sql_string = """select hash, ids, dato::date as dato from hash where userid=%s order by id"""
    #print sql_string , current_user.id
    cursor.execute(sql_string, [current_user.id],)

    hashes = cursor.fetchall()
    conn.commit();
    
    data = []
    for hash in hashes:
        data.append({
                'hash': hash[0],
                'ids': hash[1],
                'date': str(hash[2]),
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
    sql_string = """select id, title, description, dato::date from trips where userid=%s order by id"""
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
    sql_string = """select id, title, description, dato::date from points where userid=%s order by id"""
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
def hashTrip(ids):
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

    resp = Response('', status=200, mimetype='application/json')
    
    return resp


@app.route('/del/sted/<float:lon>/<float:lat>', methods=['POST', 'GET'])
def createPointJSON(lon=10, lat=60):
    #if not current_user.is_authenticated():
    #    print "ikke autorisert bruker"

    if request.method == 'POST':
        return addPointToDB(lon, lat, request.json['url'], request.json['description'], "", request.json['title'])
    else:
        return addPointToDB(lon, lat, "", "", "", "")
 

@app.route('/del/gpx', methods = ['POST'])
def createGPXTrip():
    #file = request.files['file']
    #if file:
    #    filename = secure_filename(file.filename)
    #    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    #print filename   
    
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


@app.route('/del/geojson', methods = ['POST'])
def createGeoJSONTrip():

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

@app.route('/<int:id>/setStyle', methods = ['POST'])
def setStyle(id):

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
            sql_string = """update points set markercolor=%s, markerpopup=%s, markersymbol=%s, markerType=%s, 
                        markerlabel_static=%s, markerlabel_text=%s, url=%s, image_height=%s, image_width=%s,
                        title=%s, description=%s
                        where id=%s"""
            cursor.execute(sql_string, (data["markercolor"], data["popup"]["show"], data["markersymbol"], data["markerType"], data["label"]["static"], data["label"]["text"], data["popup"]["image"]["url"], -1, data["popup"]["image"]["width"], data["popup"]["title"], data["popup"]["description"],id,))

        else:
            sql_string = """update trips set style_color=%s, style_width=%s, style_opacity=%s, style_start_icon=%s, 
                        style_end_icon=%s, style_popup=%s, title=%s, description=%s, style_label_text=%s
                        where id=%s"""
            cursor.execute(sql_string, (data["color"], data["width"], data["opacity"], data["start_icon"], data["end_icon"], data["popup"]["show"], data["popup"]["title"], data["popup"]["description"], data["label"]["text"], id,))

        
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

@app.route('/<regex("[0-9+]+"):ids>')
@app.route('/<regex("[0-9+]+"):ids>/<string:mapType>')
def getTripHTML(ids, mapType='topokart'):
    map = mapTypesList.index(mapType)
    return render_template('tur.html', mapType=map, idList=ids)

# Hash input
@app.route('/<regex("[a-z0-9]+"):hash>')
@app.route('/<regex("[a-z0-9]+"):hash>/<string:mapType>')
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

    map = mapTypesList.index(mapType)
    return render_template('tur.html', mapType=map, idList=idString)
    
@app.route('/<regex("[0-9+]+"):ids>/embed')
@app.route('/<regex("[0-9+]+"):ids>/embed/<string:mapType>')
def getTripEmbed(ids, mapType='topokart'):
    map = mapTypesList.index(mapType)

    embedType = request.args.get('embedType', '')
    if embedType != '':
        try:
            return render_template('embeds/' + embedType + '.html', mapType=map, idList=ids)
        except TemplateNotFound:
            return render_template('404.html'), 404
    else:
        return render_template('embeds/index.html', mapType=map, idList=ids)

@app.route('/<regex("[a-z0-9]+"):hash>/embed')
@app.route('/<regex("[a-z0-9]+"):hash>/embed/<string:mapType>')
def getTripEmbedByHash(hash, mapType='topokart'):
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

    embedType = request.args.get('embedType', '')
    if embedType != '':
        try:
            return render_template('embeds/' + embedType + '.html', mapType=map, idList=idString)
        except TemplateNotFound:
            return render_template('404.html'), 404
    else:
        return render_template('embeds/index.html', mapType=map, idList=idString)

@app.route('/del/kml/', methods = ['POST'])
def createKMLTrip():
    
    return addLineToDB(linestring, "")
    

@app.route('/advanced/')
def advanced():
    return render_template('advanced.html')    

    
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
    return render_template('index.html')


@app.route('/info')
def infohome():
    return render_template('infoside/index.html')
@app.route('/info/features')
def infoexplore():
    return render_template('infoside/explore.html')
@app.route('/info/priser')
def infopriser():
    return render_template('infoside/plans.html')
@app.route('/info/eksempler')
def infoeksempler():
    return render_template('infoside/eksempler.html')
@app.route('/info/api')
def infoapi():
    return render_template('infoside/api.html')
@app.route('/info/faq')
def infofaq():
    return render_template('infoside/faq.html')
@app.route('/info/kontakt')
def infokontakt():
    return render_template('infoside/contact.html')
 

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
@app.route('/admin/turer')
@login_required
def adminTrips():
    return render_template('admin/trips.html')

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
                    image_width, st_x(geo), st_y(geo), markercolor, 45-(now()::date-dato::date) as lifespan, userid 
                    from points where id=%s"""
    #print sql_string
    cursor.execute(sql_string, (id,))
    res = cursor.fetchone()
    conn.commit();

    # Check remaining days
    remaining_days = res[13]
    sql_check_plan = 'select plan from "user" where id=%s'
    cursor.execute(sql_check_plan, (res[14],))
    userPlan = cursor.fetchone()
    if userPlan[0] != "free":
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
    
    sql_string = "Select title, description, style_color, style_width, style_opacity, style_start_icon, style_end_icon, style_popup, style_label_text, 45-(now()::date-dato::date) as lifespan, userid  from trips where id=%s"

    cursor.execute(sql_string, (id,))
    res = cursor.fetchone()
    conn.commit();

    # Check remaining days
    remaining_days = res[9]
    sql_check_plan = 'select plan from "user" where id=%s'
    cursor.execute(sql_check_plan, (res[10],))
    userPlan = cursor.fetchone()
    if userPlan[0] != "free":
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

