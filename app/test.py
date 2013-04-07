import gpxpy
import gpxpy.gpx

# Parsing an existing file:
# -------------------------

gpx_file = open('test.gpx', 'r')

gpx = gpxpy.parse(gpx_file)

for track in gpx.tracks:
    for segment in track.segments:
        for point in segment.points:
            print 'aPoint at ({0},{1}) -> {2}'.format(point.latitude, point.longitude, point.elevation)

for waypoint in gpx.waypoints:
    print 'waypoint {0} -> ({1},{2})'.format(waypoint.name, waypoint.latitude, waypoint.longitude)

for route in gpx.routes:
    print 'Route:'
    for point in route:
        print 'Point at ({0},{1}) -> {2}'.format(point.latitude, point.longitude, point.elevation)
