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
    dato timestamp,
    token varchar(50)
);
SELECT AddGeometryColumn ('public','trips','geo',4326,'MULTILINESTRING',2);
ALTER TABLE trips ADD COLUMN description varchar(500);
ALTER TABLE trips ADD COLUMN style_color varchar(20);
ALTER TABLE trips ADD COLUMN style_width float;
ALTER TABLE trips ADD COLUMN style_opacity float;
ALTER TABLE trips ADD COLUMN style_start_icon boolean;
ALTER TABLE trips ADD COLUMN style_end_icon boolean;
ALTER TABLE trips ADD COLUMN style_popup boolean;
ALTER TABLE trips ADD COLUMN style_label_static boolean;
ALTER TABLE trips ADD COLUMN style_label_text varchar(300);
ALTER TABLE trips ADD COLUMN userid int;
ALTER TABLE ONLY trips ALTER COLUMN userid SET DEFAULT null;
ALTER TABLE ONLY trips ALTER COLUMN title SET DEFAULT '';
ALTER TABLE ONLY trips ALTER COLUMN description SET DEFAULT '';
ALTER TABLE ONLY trips ALTER COLUMN style_color SET DEFAULT '#ff7800';
ALTER TABLE ONLY trips ALTER COLUMN style_width SET DEFAULT 5;
ALTER TABLE ONLY trips ALTER COLUMN style_opacity SET DEFAULT 0.65;
ALTER TABLE ONLY trips ALTER COLUMN style_start_icon SET DEFAULT false;
ALTER TABLE ONLY trips ALTER COLUMN style_end_icon SET DEFAULT false;
ALTER TABLE ONLY trips ALTER COLUMN style_popup SET DEFAULT false;
ALTER TABLE ONLY trips ALTER COLUMN style_label_static SET DEFAULT false;
ALTER TABLE ONLY trips ALTER COLUMN style_label_text SET DEFAULT '';
ALTER TABLE ONLY trips ALTER COLUMN style_label_text SET DEFAULT '';
ALTER TABLE ONLY trips ALTER COLUMN style_label_text type varchar(300);

drop view if exists trips_v;
create view trips_v as 
    select id, title, dato, st_linemerge(geo) as geo
    from trips;

drop table if exists points;
create table points(
    id int4 DEFAULT nextval('common_trip_id_seq') NOT NULL,
    title varchar(50),
    url varchar(500),
    description varchar(500),
    markerType varchar(20),
    dato timestamp,
    token varchar(50)
);
SELECT AddGeometryColumn ('public','points','geo',4326,'POINT',2);
ALTER TABLE points ADD COLUMN markercolor varchar(20);
ALTER TABLE points ADD COLUMN markersymbol varchar(30);
ALTER TABLE points ADD COLUMN markerpopup boolean;
ALTER TABLE points ADD COLUMN markerlabel_static boolean;
ALTER TABLE points ADD COLUMN markerlabel_text varchar(300);
ALTER TABLE points ADD COLUMN image_width int;
ALTER TABLE points ADD COLUMN image_height int;
ALTER TABLE ONLY points ALTER COLUMN title SET DEFAULT '';
ALTER TABLE ONLY points ALTER COLUMN url SET DEFAULT '';
ALTER TABLE ONLY points ALTER COLUMN description SET DEFAULT '';
ALTER TABLE ONLY points ALTER COLUMN markertype SET DEFAULT 'fa';
ALTER TABLE ONLY points ALTER COLUMN markersymbol SET DEFAULT 'map-marker';
ALTER TABLE ONLY points ALTER COLUMN markercolor SET DEFAULT 'blue';
ALTER TABLE ONLY points ALTER COLUMN markerpopup SET DEFAULT true;
ALTER TABLE ONLY points ALTER COLUMN markerlabel_static SET DEFAULT false;
ALTER TABLE ONLY points ALTER COLUMN markerlabel_text SET DEFAULT '';
ALTER TABLE ONLY points ALTER COLUMN image_height SET DEFAULT -1;
ALTER TABLE ONLY points ALTER COLUMN image_width SET DEFAULT -1;
ALTER TABLE points ADD COLUMN userid int;
ALTER TABLE ONLY points ALTER COLUMN userid SET DEFAULT null;
ALTER TABLE ONLY points ALTER COLUMN markerlabel_text type varchar(300);

ALTER TABLE user ADD COLUMN plan varchar(50);
ALTER TABLE ONLY user ALTER COLUMN plan SET DEFAULT 'free';




