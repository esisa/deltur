createuser -SdR deltur
createdb -E UTF8 -O deltur deltur
createlang plpgsql deltur
psql -d deltur -f /usr/share/postgresql/9.1/contrib/postgis-1.5/postgis.sql
psql -d deltur -f /usr/share/postgresql/9.1/contrib/postgis-1.5/spatial_ref_sys.sql
psql deltur -c "ALTER TABLE geometry_columns OWNER TO deltur" -h localhost
psql deltur -c "ALTER TABLE spatial_ref_sys OWNER TO deltur" -h localhost
psql deltur -c "ALTER TABLE geography_columns OWNER TO deltur" -h localhost
psql deltur -c "alter database deltur owner to deltur" -h localhost


CREATE SEQUENCE common_trip_id_seq;

drop table if exists trips;
create table trips(
    id int4 DEFAULT nextval('common_trip_id_seq') NOT NULL,
    title varchar(50),
    dato timestamp
);
SELECT AddGeometryColumn ('public','trips','geo',4326,'MULTILINESTRING',2);

drop table if exists points;
create table points(
    id int4 DEFAULT nextval('common_trip_id_seq') NOT NULL,
    title varchar(50),
    url varchar(100),
    description varchar(250),
    markerType varchar(20),
    dato timestamp
);
SELECT AddGeometryColumn ('public','points','geo',4326,'POINT',2);