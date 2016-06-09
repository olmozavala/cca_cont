CREATE SCHEMA "public";

CREATE TABLE "public".cont_estaciones ( 
	id                   char(3)  NOT NULL,
	nombre               text  NOT NULL,
	CONSTRAINT pk_cont_estaciones PRIMARY KEY ( id )
 );

ALTER TABLE "public".cont_estaciones ADD column geom geometry('POINT','4326');

COMMENT ON TABLE "public".cont_estaciones IS 'These are the meteorological stations';

COMMENT ON COLUMN "public".cont_estaciones.nombre IS 'Nombre de la estacion';

CREATE TABLE "public".cont_no ( 
	id                   serial  NOT NULL,
	fecha                timestamp  NOT NULL,
	val                  real  NOT NULL,
	id_est               char(3)  ,
	CONSTRAINT pk_cont_co_13 PRIMARY KEY ( id )
 );

CREATE INDEX idx_cont_no ON "public".cont_no ( id_est );

CREATE TABLE "public".cont_nodos ( 
	id                   serial  NOT NULL,
	fecha                timestamp  NOT NULL,
	val                  real  NOT NULL,
	id_est               char(3)  ,
	CONSTRAINT pk_cont_co_3 PRIMARY KEY ( id )
 );

CREATE INDEX idx_cont_nodos ON "public".cont_nodos ( id_est );

CREATE TABLE "public".cont_nox ( 
	id                   serial  NOT NULL,
	fecha                timestamp  NOT NULL,
	val                  real  NOT NULL,
	id_est               char(3)  ,
	CONSTRAINT pk_cont_co_7 PRIMARY KEY ( id )
 );

CREATE INDEX idx_cont_nox ON "public".cont_nox ( id_est );

CREATE TABLE "public".cont_otres ( 
	id                   serial  NOT NULL,
	fecha                timestamp  NOT NULL,
	val                  real  NOT NULL,
	id_est               char(3)  NOT NULL,
	CONSTRAINT pk_cont_co_1 PRIMARY KEY ( id )
 );

CREATE INDEX idx_cont_otres ON "public".cont_otres ( id_est );

CREATE TABLE "public".cont_pmco ( 
	id                   serial  NOT NULL,
	fecha                timestamp  NOT NULL,
	val                  float8  NOT NULL,
	id_est               char(3)  ,
	CONSTRAINT pk_cont_pmc PRIMARY KEY ( id )
 );

CREATE TABLE "public".cont_pmdiez ( 
	id                   serial  NOT NULL,
	fecha                timestamp  NOT NULL,
	val                  real  NOT NULL,
	id_est               char(3)  ,
	CONSTRAINT pk_cont_co_5 PRIMARY KEY ( id )
 );

CREATE INDEX idx_cont_pmdiez ON "public".cont_pmdiez ( id_est );

CREATE TABLE "public".cont_pmdoscinco ( 
	id                   serial  NOT NULL,
	fecha                timestamp  NOT NULL,
	val                  real  NOT NULL,
	id_est               char(3)  ,
	CONSTRAINT pk_cont_co_11 PRIMARY KEY ( id )
 );

CREATE INDEX idx_cont_pmveinticinco ON "public".cont_pmdoscinco ( id_est );

CREATE TABLE "public".cont_sodos ( 
	id                   serial  NOT NULL,
	fecha                timestamp  NOT NULL,
	val                  real  NOT NULL,
	id_est               char(3)  ,
	CONSTRAINT pk_cont_co_9 PRIMARY KEY ( id )
 );

CREATE INDEX idx_cont_sodos ON "public".cont_sodos ( id_est );

CREATE TABLE "public".cont_co ( 
	id                   serial  NOT NULL,
	fecha                timestamp  NOT NULL,
	val                  real  NOT NULL,
	id_est               char(3)  NOT NULL,
	CONSTRAINT pk_cont_co PRIMARY KEY ( id )
 );

CREATE INDEX idx_cont_co ON "public".cont_co ( id_est );

CREATE TABLE "public".cont_codos ( 
	id                   serial  NOT NULL,
	fecha                timestamp  NOT NULL,
	val                  real  NOT NULL,
	id_est               char(3)  NOT NULL,
	CONSTRAINT pk_cont_co_15 PRIMARY KEY ( id )
 );

CREATE INDEX idx_cont_codos ON "public".cont_codos ( id_est );

CREATE VIEW "public".cont_monthly_onesixsix AS  SELECT count(*) AS count,
    maxvalues.mes,
    maxvalues.anio
   FROM ( SELECT max(cont_otres.val) AS mval,
            date_part('day'::text, cont_otres.fecha) AS dia,
            date_part('month'::text, cont_otres.fecha) AS mes,
            date_part('year'::text, cont_otres.fecha) AS anio
           FROM cont_otres
          GROUP BY date_part('day'::text, cont_otres.fecha), date_part('month'::text, cont_otres.fecha), date_part('year'::text, cont_otres.fecha)
          ORDER BY date_part('year'::text, cont_otres.fecha), date_part('month'::text, cont_otres.fecha), date_part('day'::text, cont_otres.fecha)) maxvalues
  WHERE (maxvalues.mval > (166)::double precision)
  GROUP BY maxvalues.mes, maxvalues.anio
  ORDER BY maxvalues.anio, maxvalues.mes;;

CREATE VIEW "public".cont_year_onesixsix AS  SELECT count(*) AS count,
    maxvalues.anio
   FROM ( SELECT max(cont_otres.val) AS mval,
            date_part('day'::text, cont_otres.fecha) AS dia,
            date_part('month'::text, cont_otres.fecha) AS mes,
            date_part('year'::text, cont_otres.fecha) AS anio
           FROM cont_otres
          GROUP BY date_part('day'::text, cont_otres.fecha), date_part('month'::text, cont_otres.fecha), date_part('year'::text, cont_otres.fecha)
          ORDER BY date_part('year'::text, cont_otres.fecha), date_part('month'::text, cont_otres.fecha), date_part('day'::text, cont_otres.fecha)) maxvalues
  WHERE (maxvalues.mval > (166)::double precision)
  GROUP BY maxvalues.anio
  ORDER BY maxvalues.anio;;

ALTER TABLE "public".cont_co ADD CONSTRAINT fk_cont_co FOREIGN KEY ( id_est ) REFERENCES "public".cont_estaciones( id );

COMMENT ON CONSTRAINT fk_cont_co ON "public".cont_co IS '';

ALTER TABLE "public".cont_codos ADD CONSTRAINT fk_cont_codos FOREIGN KEY ( id_est ) REFERENCES "public".cont_estaciones( id );

COMMENT ON CONSTRAINT fk_cont_codos ON "public".cont_codos IS '';

ALTER TABLE "public".cont_no ADD CONSTRAINT fk_cont_no FOREIGN KEY ( id_est ) REFERENCES "public".cont_estaciones( id );

COMMENT ON CONSTRAINT fk_cont_no ON "public".cont_no IS '';

ALTER TABLE "public".cont_nodos ADD CONSTRAINT fk_cont_nodos FOREIGN KEY ( id_est ) REFERENCES "public".cont_estaciones( id );

COMMENT ON CONSTRAINT fk_cont_nodos ON "public".cont_nodos IS '';

ALTER TABLE "public".cont_nox ADD CONSTRAINT fk_cont_nox FOREIGN KEY ( id_est ) REFERENCES "public".cont_estaciones( id );

COMMENT ON CONSTRAINT fk_cont_nox ON "public".cont_nox IS '';

ALTER TABLE "public".cont_otres ADD CONSTRAINT fk_cont_otres FOREIGN KEY ( id_est ) REFERENCES "public".cont_estaciones( id );

COMMENT ON CONSTRAINT fk_cont_otres ON "public".cont_otres IS '';

ALTER TABLE "public".cont_pmco ADD CONSTRAINT fk_cont_pmco_cont_estaciones FOREIGN KEY ( id_est ) REFERENCES "public".cont_estaciones( id );

COMMENT ON CONSTRAINT fk_cont_pmco_cont_estaciones ON "public".cont_pmco IS '';

ALTER TABLE "public".cont_pmdiez ADD CONSTRAINT fk_cont_pmdiez FOREIGN KEY ( id_est ) REFERENCES "public".cont_estaciones( id );

COMMENT ON CONSTRAINT fk_cont_pmdiez ON "public".cont_pmdiez IS '';

ALTER TABLE "public".cont_pmdoscinco ADD CONSTRAINT fk_cont_pmveinticinco FOREIGN KEY ( id_est ) REFERENCES "public".cont_estaciones( id );

COMMENT ON CONSTRAINT fk_cont_pmveinticinco ON "public".cont_pmdoscinco IS '';

ALTER TABLE "public".cont_sodos ADD CONSTRAINT fk_cont_sodos FOREIGN KEY ( id_est ) REFERENCES "public".cont_estaciones( id );

COMMENT ON CONSTRAINT fk_cont_sodos ON "public".cont_sodos IS '';

