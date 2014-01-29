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

import gpxpy
import gpxpy.gpx
from shapely.geometry import shape
from shapely.geometry import LineString
from shapely.geometry import Point
import psycopg2
import json
import requests

app = Flask(__name__)
app.debug = True
app.secret_key = '....'


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

pg_db = "deltur"
pg_host = "localhost"
pg_user = "deltur"
pg_passwd = "deltur._01"
pg_port = "5432"

mapTypesList = ['turkart','skikart','veikart','topokart', 'satellitt', 'kartverket']

### READ ###


@app.route('/<int:id>/metadata')
def getTripMetadata(id):
    try:
        return getLineMetadataFromDB(id)
    except:
        return getPointMetadataFromDB(id)
        

@app.route('/<int:id>/geojson')
def getTripGeoJSON(id):
    try:
        return getLineFromDB(id)
    except:
        return getPointFromDB(id)
        
@app.route('/<int:id>/osm')
def getTripOSM(id):
    if isPoint(id):
        try:
            r = requests.get('http://deltur.no/feature/deltur_point/'+str(id)+'?service=osm')
            return Response(r.text, mimetype='text/xml')
        except:
            return "Error"
    else:
        try:
            r = requests.get('http://deltur.no/feature/deltur_line/'+str(id)+'?service=osm')
            return Response(r.text, mimetype='text/xml')
        except:
            return "Error"
    
@app.route('/<int:id>/kml')
def getTripKML(id):
    if isPoint(id):
        try:
            r = requests.get('http://deltur.no/feature/deltur_point/'+str(id)+'?service=kml')
            return Response(r.text, mimetype='text/xml')
        except:
            return "Error"
    else:
        try:
            r = requests.get('http://deltur.no/feature/deltur_line/'+str(id)+'?service=kml')
            return Response(r.text, mimetype='text/xml')
        except:
            return "Error"

@app.route('/<int:id>/csv')
def getTripCSV(id):
    if isPoint(id):
        try:
            r = requests.get('http://deltur.no/feature/deltur_point/'+str(id)+'?service=csv')
            return Response(r.text, mimetype='text/plain')
        except:
            return "Error"
    else:
        try:
            r = requests.get('http://deltur.no/feature/deltur_line/'+str(id)+'?service=csv')
            return Response(r.text, mimetype='text/plain')
        except:
            return "Error"

@app.route('/<int:id>/gpx')
def getTripGPX(id):
    if isPoint(id):
        try:
            r = requests.get('http://deltur.no/feature/deltur_point/'+str(id)+'?service=gpx')
            return Response(r.text, mimetype='text/xml')
        except:
            return "Error"
    else:
        try:
            r = requests.get('http://deltur.no/feature/deltur_line/'+str(id)+'?service=gpx')
            return Response(r.text, mimetype='text/xml')
        except:
            return "Error"




### WRITE ###

@app.route('/del/sted/<float:lon>/<float:lat>', methods=['POST', 'GET'])
def createPointJSON(lon=10, lat=60):
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





### TEMPLATES ###

@app.route('/<regex("[0-9+]+"):ids>')
@app.route('/<regex("[0-9+]+"):ids>/<string:mapType>')
def getTripHTML(ids, mapType='topokart'):
    map = mapTypesList.index(mapType)
    return render_template('tur.html', mapType=map, idList=ids)


    
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

@app.route('/login/')
def login():
    return render_template('admin/login.html')

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
 



 ### UTILITY FUNCTIONS ###   
    
    
def addPointToDB(lon, lat, url, description, markerType, title):
    try:
        conn = psycopg2.connect("dbname="+pg_db+" user="+pg_user+" password="+pg_passwd+" host="+pg_host+" ")
    except:
        print "Could not connect to database " + pg_db
            
    cursor = conn.cursor()

    sql_string = "INSERT INTO points(title, markerType, url, description, geo) VALUES (%s,%s,%s,%s, ST_GEOMFROMTEXT('POINT(%s %s)', 4326) ) RETURNING id;"
    cursor.execute(sql_string, (title, "", url, description, lat, lon))
    id = cursor.fetchone()[0]
    conn.commit();
    
    
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

    sql_string = "INSERT INTO trips(title, geo) VALUES (%s,ST_MULTI(ST_GEOMFROMTEXT(%s, 4326))) RETURNING id;"
    cursor.execute(sql_string, (title, line.wkt))
    id = cursor.fetchone()[0]
    conn.commit();
    
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
    
    sql_string = "Select url, description, title, markerType, markersymbol, markerpopup, markerlabel_static, markerlabel_text, image_height, image_width from points where id=%s"
    print sql_string
    cursor.execute(sql_string, (id,))
    res = cursor.fetchone()
    conn.commit();
    
    data = {
            'id': id,
            'description':res[1],
            'title': res[2],
            'style': {
                'markerType':res[3],
                'markersymbol':res[4],
                'markerpopup':res[5],
                'image': {
                    'url':res[0],
                    'height':res[8],
                    'width':res[9]
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
    
    sql_string = "Select title, style_color, style_width, style_opacity, style_start_icon, style_end_icon, style_popup, style_label_static, style_label_text from trips where id=%s"
    print sql_string
    cursor.execute(sql_string, (id,))
    res = cursor.fetchone()
    conn.commit();
    
    data = {
            'id': id,
            'title': res[0],
            'style': {
                'color':res[1],
                'width':res[2],
                'opacity':res[3],
                'start_icon':res[4],
                'end_icon':res[5],
                'popup':res[6],
                'label': {
                    'static':res[7],
                    'text':res[8]
                }
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
