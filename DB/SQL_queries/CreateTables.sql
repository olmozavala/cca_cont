--
-- PostgreSQL database dump
--

-- Dumped from database version 9.4.6
-- Dumped by pg_dump version 9.5.3

-- Started on 2016-06-09 17:42:07 CDT

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 2 (class 3079 OID 12723)
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- TOC entry 4239 (class 0 OID 0)
-- Dependencies: 2
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


--
-- TOC entry 1 (class 3079 OID 30901)
-- Name: adminpack; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS adminpack WITH SCHEMA pg_catalog;


--
-- TOC entry 4240 (class 0 OID 0)
-- Dependencies: 1
-- Name: EXTENSION adminpack; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION adminpack IS 'administrative functions for PostgreSQL';


--
-- TOC entry 3 (class 3079 OID 32153)
-- Name: postgis; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA public;


--
-- TOC entry 4241 (class 0 OID 0)
-- Dependencies: 3
-- Name: EXTENSION postgis; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION postgis IS 'PostGIS geometry, geography, and raster spatial types and functions';


SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- TOC entry 177 (class 1259 OID 21692)
-- Name: cont_co; Type: TABLE; Schema: public; Owner: olmozavala
--

CREATE TABLE cont_co (
    id integer NOT NULL,
    fecha timestamp without time zone NOT NULL,
    val real NOT NULL,
    id_est character(3) NOT NULL
);


ALTER TABLE cont_co OWNER TO olmozavala;

--
-- TOC entry 193 (class 1259 OID 21958)
-- Name: cont_codos; Type: TABLE; Schema: public; Owner: olmozavala
--

CREATE TABLE cont_codos (
    id integer NOT NULL,
    fecha timestamp without time zone NOT NULL,
    val real NOT NULL,
    id_est character(3) NOT NULL
);


ALTER TABLE cont_codos OWNER TO olmozavala;

--
-- TOC entry 175 (class 1259 OID 21682)
-- Name: cont_estaciones; Type: TABLE; Schema: public; Owner: olmozavala
--

CREATE TABLE cont_estaciones (
    id character(3) NOT NULL,
    nombre text NOT NULL,
    geom geometry(Point,4326),
    lastyear integer,
    altitude double precision
);


ALTER TABLE cont_estaciones OWNER TO olmozavala;

--
-- TOC entry 4243 (class 0 OID 0)
-- Dependencies: 175
-- Name: TABLE cont_estaciones; Type: COMMENT; Schema: public; Owner: olmozavala
--

COMMENT ON TABLE cont_estaciones IS 'These are the meteorological stations';


--
-- TOC entry 4244 (class 0 OID 0)
-- Dependencies: 175
-- Name: COLUMN cont_estaciones.nombre; Type: COMMENT; Schema: public; Owner: olmozavala
--

COMMENT ON COLUMN cont_estaciones.nombre IS 'Nombre de la estacion';


--
-- TOC entry 179 (class 1259 OID 21712)
-- Name: cont_otres; Type: TABLE; Schema: public; Owner: olmozavala
--

CREATE TABLE cont_otres (
    id integer NOT NULL,
    fecha timestamp without time zone NOT NULL,
    val real NOT NULL,
    id_est character(3) NOT NULL
);


ALTER TABLE cont_otres OWNER TO olmozavala;

--
-- TOC entry 195 (class 1259 OID 31345)
-- Name: cont_monthly_onesixsix; Type: VIEW; Schema: public; Owner: argel
--

CREATE VIEW cont_monthly_onesixsix AS
 SELECT count(*) AS count,
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
  ORDER BY maxvalues.anio, maxvalues.mes;


ALTER TABLE cont_monthly_onesixsix OWNER TO argel;

--
-- TOC entry 191 (class 1259 OID 21928)
-- Name: cont_no; Type: TABLE; Schema: public; Owner: olmozavala
--

CREATE TABLE cont_no (
    id integer NOT NULL,
    fecha timestamp without time zone NOT NULL,
    val real NOT NULL,
    id_est character(3)
);


ALTER TABLE cont_no OWNER TO olmozavala;

--
-- TOC entry 181 (class 1259 OID 21727)
-- Name: cont_nodos; Type: TABLE; Schema: public; Owner: olmozavala
--

CREATE TABLE cont_nodos (
    id integer NOT NULL,
    fecha timestamp without time zone NOT NULL,
    val real NOT NULL,
    id_est character(3)
);


ALTER TABLE cont_nodos OWNER TO olmozavala;

--
-- TOC entry 185 (class 1259 OID 21747)
-- Name: cont_nox; Type: TABLE; Schema: public; Owner: olmozavala
--

CREATE TABLE cont_nox (
    id integer NOT NULL,
    fecha timestamp without time zone NOT NULL,
    val real NOT NULL,
    id_est character(3)
);


ALTER TABLE cont_nox OWNER TO olmozavala;

--
-- TOC entry 183 (class 1259 OID 21737)
-- Name: cont_pmdiez; Type: TABLE; Schema: public; Owner: olmozavala
--

CREATE TABLE cont_pmdiez (
    id integer NOT NULL,
    fecha timestamp without time zone NOT NULL,
    val real NOT NULL,
    id_est character(3)
);


ALTER TABLE cont_pmdiez OWNER TO olmozavala;

--
-- TOC entry 189 (class 1259 OID 21913)
-- Name: cont_pmdoscinco; Type: TABLE; Schema: public; Owner: olmozavala
--

CREATE TABLE cont_pmdoscinco (
    id integer NOT NULL,
    fecha timestamp without time zone NOT NULL,
    val real NOT NULL,
    id_est character(3)
);


ALTER TABLE cont_pmdoscinco OWNER TO olmozavala;

--
-- TOC entry 176 (class 1259 OID 21690)
-- Name: cont_seq_co; Type: SEQUENCE; Schema: public; Owner: olmozavala
--

CREATE SEQUENCE cont_seq_co
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE cont_seq_co OWNER TO olmozavala;

--
-- TOC entry 4250 (class 0 OID 0)
-- Dependencies: 176
-- Name: cont_seq_co; Type: SEQUENCE OWNED BY; Schema: public; Owner: olmozavala
--

ALTER SEQUENCE cont_seq_co OWNED BY cont_co.id;


--
-- TOC entry 192 (class 1259 OID 21956)
-- Name: cont_seq_codos; Type: SEQUENCE; Schema: public; Owner: olmozavala
--

CREATE SEQUENCE cont_seq_codos
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE cont_seq_codos OWNER TO olmozavala;

--
-- TOC entry 4251 (class 0 OID 0)
-- Dependencies: 192
-- Name: cont_seq_codos; Type: SEQUENCE OWNED BY; Schema: public; Owner: olmozavala
--

ALTER SEQUENCE cont_seq_codos OWNED BY cont_codos.id;


--
-- TOC entry 190 (class 1259 OID 21926)
-- Name: cont_seq_no; Type: SEQUENCE; Schema: public; Owner: olmozavala
--

CREATE SEQUENCE cont_seq_no
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE cont_seq_no OWNER TO olmozavala;

--
-- TOC entry 4252 (class 0 OID 0)
-- Dependencies: 190
-- Name: cont_seq_no; Type: SEQUENCE OWNED BY; Schema: public; Owner: olmozavala
--

ALTER SEQUENCE cont_seq_no OWNED BY cont_no.id;


--
-- TOC entry 180 (class 1259 OID 21725)
-- Name: cont_seq_nodos; Type: SEQUENCE; Schema: public; Owner: olmozavala
--

CREATE SEQUENCE cont_seq_nodos
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE cont_seq_nodos OWNER TO olmozavala;

--
-- TOC entry 4253 (class 0 OID 0)
-- Dependencies: 180
-- Name: cont_seq_nodos; Type: SEQUENCE OWNED BY; Schema: public; Owner: olmozavala
--

ALTER SEQUENCE cont_seq_nodos OWNED BY cont_nodos.id;


--
-- TOC entry 184 (class 1259 OID 21745)
-- Name: cont_seq_nox; Type: SEQUENCE; Schema: public; Owner: olmozavala
--

CREATE SEQUENCE cont_seq_nox
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE cont_seq_nox OWNER TO olmozavala;

--
-- TOC entry 4254 (class 0 OID 0)
-- Dependencies: 184
-- Name: cont_seq_nox; Type: SEQUENCE OWNED BY; Schema: public; Owner: olmozavala
--

ALTER SEQUENCE cont_seq_nox OWNED BY cont_nox.id;


--
-- TOC entry 178 (class 1259 OID 21710)
-- Name: cont_seq_otres; Type: SEQUENCE; Schema: public; Owner: olmozavala
--

CREATE SEQUENCE cont_seq_otres
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE cont_seq_otres OWNER TO olmozavala;

--
-- TOC entry 4255 (class 0 OID 0)
-- Dependencies: 178
-- Name: cont_seq_otres; Type: SEQUENCE OWNED BY; Schema: public; Owner: olmozavala
--

ALTER SEQUENCE cont_seq_otres OWNED BY cont_otres.id;


--
-- TOC entry 182 (class 1259 OID 21735)
-- Name: cont_seq_pmdiez; Type: SEQUENCE; Schema: public; Owner: olmozavala
--

CREATE SEQUENCE cont_seq_pmdiez
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE cont_seq_pmdiez OWNER TO olmozavala;

--
-- TOC entry 4256 (class 0 OID 0)
-- Dependencies: 182
-- Name: cont_seq_pmdiez; Type: SEQUENCE OWNED BY; Schema: public; Owner: olmozavala
--

ALTER SEQUENCE cont_seq_pmdiez OWNED BY cont_pmdiez.id;


--
-- TOC entry 188 (class 1259 OID 21911)
-- Name: cont_seq_pmdoscinco; Type: SEQUENCE; Schema: public; Owner: olmozavala
--

CREATE SEQUENCE cont_seq_pmdoscinco
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE cont_seq_pmdoscinco OWNER TO olmozavala;

--
-- TOC entry 4257 (class 0 OID 0)
-- Dependencies: 188
-- Name: cont_seq_pmdoscinco; Type: SEQUENCE OWNED BY; Schema: public; Owner: olmozavala
--

ALTER SEQUENCE cont_seq_pmdoscinco OWNED BY cont_pmdoscinco.id;


--
-- TOC entry 187 (class 1259 OID 21772)
-- Name: cont_sodos; Type: TABLE; Schema: public; Owner: olmozavala
--

CREATE TABLE cont_sodos (
    id integer NOT NULL,
    fecha timestamp without time zone NOT NULL,
    val real NOT NULL,
    id_est character(3)
);


ALTER TABLE cont_sodos OWNER TO olmozavala;

--
-- TOC entry 186 (class 1259 OID 21770)
-- Name: cont_seq_sodos; Type: SEQUENCE; Schema: public; Owner: olmozavala
--

CREATE SEQUENCE cont_seq_sodos
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE cont_seq_sodos OWNER TO olmozavala;

--
-- TOC entry 4259 (class 0 OID 0)
-- Dependencies: 186
-- Name: cont_seq_sodos; Type: SEQUENCE OWNED BY; Schema: public; Owner: olmozavala
--

ALTER SEQUENCE cont_seq_sodos OWNED BY cont_sodos.id;


--
-- TOC entry 210 (class 1259 OID 33590)
-- Name: cont_units; Type: TABLE; Schema: public; Owner: olmozavala
--

CREATE TABLE cont_units (
    id integer NOT NULL,
    unit character varying(10) NOT NULL,
    nombre character varying(100) NOT NULL
);


ALTER TABLE cont_units OWNER TO olmozavala;

--
-- TOC entry 209 (class 1259 OID 33588)
-- Name: cont_units_id_seq; Type: SEQUENCE; Schema: public; Owner: olmozavala
--

CREATE SEQUENCE cont_units_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE cont_units_id_seq OWNER TO olmozavala;

--
-- TOC entry 4260 (class 0 OID 0)
-- Dependencies: 209
-- Name: cont_units_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: olmozavala
--

ALTER SEQUENCE cont_units_id_seq OWNED BY cont_units.id;


--
-- TOC entry 194 (class 1259 OID 31337)
-- Name: cont_year_onesixsix; Type: VIEW; Schema: public; Owner: argel
--

CREATE VIEW cont_year_onesixsix AS
 SELECT count(*) AS count,
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
  ORDER BY maxvalues.anio;


ALTER TABLE cont_year_onesixsix OWNER TO argel;

--
-- TOC entry 4048 (class 2604 OID 21695)
-- Name: id; Type: DEFAULT; Schema: public; Owner: olmozavala
--

ALTER TABLE ONLY cont_co ALTER COLUMN id SET DEFAULT nextval('cont_seq_co'::regclass);


--
-- TOC entry 4056 (class 2604 OID 21961)
-- Name: id; Type: DEFAULT; Schema: public; Owner: olmozavala
--

ALTER TABLE ONLY cont_codos ALTER COLUMN id SET DEFAULT nextval('cont_seq_codos'::regclass);


--
-- TOC entry 4055 (class 2604 OID 21931)
-- Name: id; Type: DEFAULT; Schema: public; Owner: olmozavala
--

ALTER TABLE ONLY cont_no ALTER COLUMN id SET DEFAULT nextval('cont_seq_no'::regclass);


--
-- TOC entry 4050 (class 2604 OID 21730)
-- Name: id; Type: DEFAULT; Schema: public; Owner: olmozavala
--

ALTER TABLE ONLY cont_nodos ALTER COLUMN id SET DEFAULT nextval('cont_seq_nodos'::regclass);


--
-- TOC entry 4052 (class 2604 OID 21750)
-- Name: id; Type: DEFAULT; Schema: public; Owner: olmozavala
--

ALTER TABLE ONLY cont_nox ALTER COLUMN id SET DEFAULT nextval('cont_seq_nox'::regclass);


--
-- TOC entry 4049 (class 2604 OID 21715)
-- Name: id; Type: DEFAULT; Schema: public; Owner: olmozavala
--

ALTER TABLE ONLY cont_otres ALTER COLUMN id SET DEFAULT nextval('cont_seq_otres'::regclass);


--
-- TOC entry 4051 (class 2604 OID 21740)
-- Name: id; Type: DEFAULT; Schema: public; Owner: olmozavala
--

ALTER TABLE ONLY cont_pmdiez ALTER COLUMN id SET DEFAULT nextval('cont_seq_pmdiez'::regclass);


--
-- TOC entry 4054 (class 2604 OID 21916)
-- Name: id; Type: DEFAULT; Schema: public; Owner: olmozavala
--

ALTER TABLE ONLY cont_pmdoscinco ALTER COLUMN id SET DEFAULT nextval('cont_seq_pmdoscinco'::regclass);


--
-- TOC entry 4053 (class 2604 OID 21775)
-- Name: id; Type: DEFAULT; Schema: public; Owner: olmozavala
--

ALTER TABLE ONLY cont_sodos ALTER COLUMN id SET DEFAULT nextval('cont_seq_sodos'::regclass);


--
-- TOC entry 4057 (class 2604 OID 33593)
-- Name: id; Type: DEFAULT; Schema: public; Owner: olmozavala
--

ALTER TABLE ONLY cont_units ALTER COLUMN id SET DEFAULT nextval('cont_units_id_seq'::regclass);


--
-- TOC entry 4062 (class 2606 OID 21697)
-- Name: pk_cont_co; Type: CONSTRAINT; Schema: public; Owner: olmozavala
--

ALTER TABLE ONLY cont_co
    ADD CONSTRAINT pk_cont_co PRIMARY KEY (id);


--
-- TOC entry 4065 (class 2606 OID 21717)
-- Name: pk_cont_co_1; Type: CONSTRAINT; Schema: public; Owner: olmozavala
--

ALTER TABLE ONLY cont_otres
    ADD CONSTRAINT pk_cont_co_1 PRIMARY KEY (id);


--
-- TOC entry 4090 (class 2606 OID 21918)
-- Name: pk_cont_co_11; Type: CONSTRAINT; Schema: public; Owner: olmozavala
--

ALTER TABLE ONLY cont_pmdoscinco
    ADD CONSTRAINT pk_cont_co_11 PRIMARY KEY (id);


--
-- TOC entry 4095 (class 2606 OID 21933)
-- Name: pk_cont_co_13; Type: CONSTRAINT; Schema: public; Owner: olmozavala
--

ALTER TABLE ONLY cont_no
    ADD CONSTRAINT pk_cont_co_13 PRIMARY KEY (id);


--
-- TOC entry 4100 (class 2606 OID 21963)
-- Name: pk_cont_co_15; Type: CONSTRAINT; Schema: public; Owner: olmozavala
--

ALTER TABLE ONLY cont_codos
    ADD CONSTRAINT pk_cont_co_15 PRIMARY KEY (id);


--
-- TOC entry 4070 (class 2606 OID 21732)
-- Name: pk_cont_co_3; Type: CONSTRAINT; Schema: public; Owner: olmozavala
--

ALTER TABLE ONLY cont_nodos
    ADD CONSTRAINT pk_cont_co_3 PRIMARY KEY (id);


--
-- TOC entry 4075 (class 2606 OID 21742)
-- Name: pk_cont_co_5; Type: CONSTRAINT; Schema: public; Owner: olmozavala
--

ALTER TABLE ONLY cont_pmdiez
    ADD CONSTRAINT pk_cont_co_5 PRIMARY KEY (id);


--
-- TOC entry 4080 (class 2606 OID 21752)
-- Name: pk_cont_co_7; Type: CONSTRAINT; Schema: public; Owner: olmozavala
--

ALTER TABLE ONLY cont_nox
    ADD CONSTRAINT pk_cont_co_7 PRIMARY KEY (id);


--
-- TOC entry 4085 (class 2606 OID 21777)
-- Name: pk_cont_co_9; Type: CONSTRAINT; Schema: public; Owner: olmozavala
--

ALTER TABLE ONLY cont_sodos
    ADD CONSTRAINT pk_cont_co_9 PRIMARY KEY (id);


--
-- TOC entry 4059 (class 2606 OID 21797)
-- Name: pk_cont_estaciones; Type: CONSTRAINT; Schema: public; Owner: olmozavala
--

ALTER TABLE ONLY cont_estaciones
    ADD CONSTRAINT pk_cont_estaciones PRIMARY KEY (id);


--
-- TOC entry 4104 (class 2606 OID 33595)
-- Name: pk_cont_units; Type: CONSTRAINT; Schema: public; Owner: olmozavala
--

ALTER TABLE ONLY cont_units
    ADD CONSTRAINT pk_cont_units PRIMARY KEY (id);


--
-- TOC entry 4102 (class 2606 OID 33581)
-- Name: unique_codos; Type: CONSTRAINT; Schema: public; Owner: olmozavala
--

ALTER TABLE ONLY cont_codos
    ADD CONSTRAINT unique_codos UNIQUE (fecha, id_est);


--
-- TOC entry 4097 (class 2606 OID 33534)
-- Name: unique_no; Type: CONSTRAINT; Schema: public; Owner: olmozavala
--

ALTER TABLE ONLY cont_no
    ADD CONSTRAINT unique_no UNIQUE (fecha, id_est);


--
-- TOC entry 4072 (class 2606 OID 33565)
-- Name: unique_nodos; Type: CONSTRAINT; Schema: public; Owner: olmozavala
--

ALTER TABLE ONLY cont_nodos
    ADD CONSTRAINT unique_nodos UNIQUE (fecha, id_est);


--
-- TOC entry 4082 (class 2606 OID 33538)
-- Name: unique_nox; Type: CONSTRAINT; Schema: public; Owner: olmozavala
--

ALTER TABLE ONLY cont_nox
    ADD CONSTRAINT unique_nox UNIQUE (fecha, id_est);


--
-- TOC entry 4067 (class 2606 OID 33540)
-- Name: unique_otres; Type: CONSTRAINT; Schema: public; Owner: olmozavala
--

ALTER TABLE ONLY cont_otres
    ADD CONSTRAINT unique_otres UNIQUE (fecha, id_est);


--
-- TOC entry 4077 (class 2606 OID 33542)
-- Name: unique_pmdiez; Type: CONSTRAINT; Schema: public; Owner: olmozavala
--

ALTER TABLE ONLY cont_pmdiez
    ADD CONSTRAINT unique_pmdiez UNIQUE (fecha, id_est);


--
-- TOC entry 4092 (class 2606 OID 33545)
-- Name: unique_pmdoscinco; Type: CONSTRAINT; Schema: public; Owner: olmozavala
--

ALTER TABLE ONLY cont_pmdoscinco
    ADD CONSTRAINT unique_pmdoscinco UNIQUE (fecha, id_est);


--
-- TOC entry 4087 (class 2606 OID 33547)
-- Name: unique_sodos; Type: CONSTRAINT; Schema: public; Owner: olmozavala
--

ALTER TABLE ONLY cont_sodos
    ADD CONSTRAINT unique_sodos UNIQUE (fecha, id_est);


--
-- TOC entry 4060 (class 1259 OID 29899)
-- Name: idx_cont_co; Type: INDEX; Schema: public; Owner: olmozavala
--

CREATE INDEX idx_cont_co ON cont_co USING btree (id_est);


--
-- TOC entry 4098 (class 1259 OID 29893)
-- Name: idx_cont_codos; Type: INDEX; Schema: public; Owner: olmozavala
--

CREATE INDEX idx_cont_codos ON cont_codos USING btree (id_est);


--
-- TOC entry 4093 (class 1259 OID 29887)
-- Name: idx_cont_no; Type: INDEX; Schema: public; Owner: olmozavala
--

CREATE INDEX idx_cont_no ON cont_no USING btree (id_est);


--
-- TOC entry 4068 (class 1259 OID 29881)
-- Name: idx_cont_nodos; Type: INDEX; Schema: public; Owner: olmozavala
--

CREATE INDEX idx_cont_nodos ON cont_nodos USING btree (id_est);


--
-- TOC entry 4078 (class 1259 OID 22009)
-- Name: idx_cont_nox; Type: INDEX; Schema: public; Owner: olmozavala
--

CREATE INDEX idx_cont_nox ON cont_nox USING btree (id_est);


--
-- TOC entry 4063 (class 1259 OID 22015)
-- Name: idx_cont_otres; Type: INDEX; Schema: public; Owner: olmozavala
--

CREATE INDEX idx_cont_otres ON cont_otres USING btree (id_est);


--
-- TOC entry 4073 (class 1259 OID 22042)
-- Name: idx_cont_pmdiez; Type: INDEX; Schema: public; Owner: olmozavala
--

CREATE INDEX idx_cont_pmdiez ON cont_pmdiez USING btree (id_est);


--
-- TOC entry 4088 (class 1259 OID 22003)
-- Name: idx_cont_pmveinticinco; Type: INDEX; Schema: public; Owner: olmozavala
--

CREATE INDEX idx_cont_pmveinticinco ON cont_pmdoscinco USING btree (id_est);


--
-- TOC entry 4083 (class 1259 OID 22036)
-- Name: idx_cont_sodos; Type: INDEX; Schema: public; Owner: olmozavala
--

CREATE INDEX idx_cont_sodos ON cont_sodos USING btree (id_est);


--
-- TOC entry 4105 (class 2606 OID 33484)
-- Name: fk_cont_co; Type: FK CONSTRAINT; Schema: public; Owner: olmozavala
--

ALTER TABLE ONLY cont_co
    ADD CONSTRAINT fk_cont_co FOREIGN KEY (id_est) REFERENCES cont_estaciones(id) ON DELETE CASCADE;


--
-- TOC entry 4113 (class 2606 OID 33479)
-- Name: fk_cont_codos; Type: FK CONSTRAINT; Schema: public; Owner: olmozavala
--

ALTER TABLE ONLY cont_codos
    ADD CONSTRAINT fk_cont_codos FOREIGN KEY (id_est) REFERENCES cont_estaciones(id) ON DELETE CASCADE;


--
-- TOC entry 4112 (class 2606 OID 33474)
-- Name: fk_cont_no; Type: FK CONSTRAINT; Schema: public; Owner: olmozavala
--

ALTER TABLE ONLY cont_no
    ADD CONSTRAINT fk_cont_no FOREIGN KEY (id_est) REFERENCES cont_estaciones(id) ON DELETE CASCADE;


--
-- TOC entry 4107 (class 2606 OID 33464)
-- Name: fk_cont_nodos; Type: FK CONSTRAINT; Schema: public; Owner: olmozavala
--

ALTER TABLE ONLY cont_nodos
    ADD CONSTRAINT fk_cont_nodos FOREIGN KEY (id_est) REFERENCES cont_estaciones(id) ON DELETE CASCADE;


--
-- TOC entry 4109 (class 2606 OID 33454)
-- Name: fk_cont_nox; Type: FK CONSTRAINT; Schema: public; Owner: olmozavala
--

ALTER TABLE ONLY cont_nox
    ADD CONSTRAINT fk_cont_nox FOREIGN KEY (id_est) REFERENCES cont_estaciones(id) ON DELETE CASCADE;


--
-- TOC entry 4106 (class 2606 OID 33459)
-- Name: fk_cont_otres; Type: FK CONSTRAINT; Schema: public; Owner: olmozavala
--

ALTER TABLE ONLY cont_otres
    ADD CONSTRAINT fk_cont_otres FOREIGN KEY (id_est) REFERENCES cont_estaciones(id) ON DELETE CASCADE;


--
-- TOC entry 4108 (class 2606 OID 33494)
-- Name: fk_cont_pmdiez; Type: FK CONSTRAINT; Schema: public; Owner: olmozavala
--

ALTER TABLE ONLY cont_pmdiez
    ADD CONSTRAINT fk_cont_pmdiez FOREIGN KEY (id_est) REFERENCES cont_estaciones(id) ON DELETE CASCADE;


--
-- TOC entry 4111 (class 2606 OID 33449)
-- Name: fk_cont_pmveinticinco; Type: FK CONSTRAINT; Schema: public; Owner: olmozavala
--

ALTER TABLE ONLY cont_pmdoscinco
    ADD CONSTRAINT fk_cont_pmveinticinco FOREIGN KEY (id_est) REFERENCES cont_estaciones(id) ON DELETE CASCADE;


--
-- TOC entry 4110 (class 2606 OID 33489)
-- Name: fk_cont_sodos; Type: FK CONSTRAINT; Schema: public; Owner: olmozavala
--

ALTER TABLE ONLY cont_sodos
    ADD CONSTRAINT fk_cont_sodos FOREIGN KEY (id_est) REFERENCES cont_estaciones(id) ON DELETE CASCADE;


--
-- TOC entry 4238 (class 0 OID 0)
-- Dependencies: 8
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- TOC entry 4242 (class 0 OID 0)
-- Dependencies: 177
-- Name: cont_co; Type: ACL; Schema: public; Owner: olmozavala
--

REVOKE ALL ON TABLE cont_co FROM PUBLIC;
REVOKE ALL ON TABLE cont_co FROM olmozavala;
GRANT ALL ON TABLE cont_co TO olmozavala;
GRANT ALL ON TABLE cont_co TO argel;
GRANT ALL ON TABLE cont_co TO tai;


--
-- TOC entry 4245 (class 0 OID 0)
-- Dependencies: 175
-- Name: cont_estaciones; Type: ACL; Schema: public; Owner: olmozavala
--

REVOKE ALL ON TABLE cont_estaciones FROM PUBLIC;
REVOKE ALL ON TABLE cont_estaciones FROM olmozavala;
GRANT ALL ON TABLE cont_estaciones TO olmozavala;
GRANT ALL ON TABLE cont_estaciones TO argel;
GRANT ALL ON TABLE cont_estaciones TO tai;


--
-- TOC entry 4246 (class 0 OID 0)
-- Dependencies: 179
-- Name: cont_otres; Type: ACL; Schema: public; Owner: olmozavala
--

REVOKE ALL ON TABLE cont_otres FROM PUBLIC;
REVOKE ALL ON TABLE cont_otres FROM olmozavala;
GRANT ALL ON TABLE cont_otres TO olmozavala;
GRANT ALL ON TABLE cont_otres TO argel;
GRANT ALL ON TABLE cont_otres TO tai;


--
-- TOC entry 4247 (class 0 OID 0)
-- Dependencies: 181
-- Name: cont_nodos; Type: ACL; Schema: public; Owner: olmozavala
--

REVOKE ALL ON TABLE cont_nodos FROM PUBLIC;
REVOKE ALL ON TABLE cont_nodos FROM olmozavala;
GRANT ALL ON TABLE cont_nodos TO olmozavala;
GRANT ALL ON TABLE cont_nodos TO argel;
GRANT ALL ON TABLE cont_nodos TO tai;


--
-- TOC entry 4248 (class 0 OID 0)
-- Dependencies: 185
-- Name: cont_nox; Type: ACL; Schema: public; Owner: olmozavala
--

REVOKE ALL ON TABLE cont_nox FROM PUBLIC;
REVOKE ALL ON TABLE cont_nox FROM olmozavala;
GRANT ALL ON TABLE cont_nox TO olmozavala;
GRANT ALL ON TABLE cont_nox TO argel;
GRANT ALL ON TABLE cont_nox TO tai;


--
-- TOC entry 4249 (class 0 OID 0)
-- Dependencies: 183
-- Name: cont_pmdiez; Type: ACL; Schema: public; Owner: olmozavala
--

REVOKE ALL ON TABLE cont_pmdiez FROM PUBLIC;
REVOKE ALL ON TABLE cont_pmdiez FROM olmozavala;
GRANT ALL ON TABLE cont_pmdiez TO olmozavala;
GRANT ALL ON TABLE cont_pmdiez TO argel;
GRANT ALL ON TABLE cont_pmdiez TO tai;


--
-- TOC entry 4258 (class 0 OID 0)
-- Dependencies: 187
-- Name: cont_sodos; Type: ACL; Schema: public; Owner: olmozavala
--

REVOKE ALL ON TABLE cont_sodos FROM PUBLIC;
REVOKE ALL ON TABLE cont_sodos FROM olmozavala;
GRANT ALL ON TABLE cont_sodos TO olmozavala;
GRANT ALL ON TABLE cont_sodos TO argel;
GRANT ALL ON TABLE cont_sodos TO tai;


-- Completed on 2016-06-09 17:42:10 CDT

--
-- PostgreSQL database dump complete
--

