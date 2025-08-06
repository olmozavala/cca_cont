# Database Schema

## Tables

### climatologia
| Column | Type |
|--------|------|
| id_tabla | text |
| id_est | character |
| id_cont | text |
| mes | integer |
| hora | time without time zone |
| val | double precision |

### cont_co
| Column | Type |
|--------|------|
| id | integer |
| fecha | timestamp without time zone |
| val | real |
| id_est | character |

**Foreign Keys:**

| Column | References |
|--------|------------|
| id_est | cont_estaciones(id) |

### cont_codos
| Column | Type |
|--------|------|
| id | integer |
| fecha | timestamp without time zone |
| val | real |
| id_est | character |

**Foreign Keys:**

| Column | References |
|--------|------------|
| id_est | cont_estaciones(id) |

### cont_estaciones
| Column | Type |
|--------|------|
| id | character |
| nombre | text |
| geom | USER-DEFINED |
| lastyear | integer |
| altitude | double precision |

### cont_no
| Column | Type |
|--------|------|
| id | integer |
| fecha | timestamp without time zone |
| val | real |
| id_est | character |

**Foreign Keys:**

| Column | References |
|--------|------------|
| id_est | cont_estaciones(id) |

### cont_nodos
| Column | Type |
|--------|------|
| id | integer |
| fecha | timestamp without time zone |
| val | real |
| id_est | character |

**Foreign Keys:**

| Column | References |
|--------|------------|
| id_est | cont_estaciones(id) |

### cont_nox
| Column | Type |
|--------|------|
| id | integer |
| fecha | timestamp without time zone |
| val | real |
| id_est | character |

**Foreign Keys:**

| Column | References |
|--------|------------|
| id_est | cont_estaciones(id) |

### cont_otres
| Column | Type |
|--------|------|
| id | integer |
| fecha | timestamp without time zone |
| val | real |
| id_est | character |

**Foreign Keys:**

| Column | References |
|--------|------------|
| id_est | cont_estaciones(id) |

### cont_pmco
| Column | Type |
|--------|------|
| id | integer |
| fecha | timestamp without time zone |
| val | real |
| id_est | character |

**Foreign Keys:**

| Column | References |
|--------|------------|
| id_est | cont_estaciones(id) |

### cont_pmdiez
| Column | Type |
|--------|------|
| id | integer |
| fecha | timestamp without time zone |
| val | real |
| id_est | character |

**Foreign Keys:**

| Column | References |
|--------|------------|
| id_est | cont_estaciones(id) |

### cont_pmdoscinco
| Column | Type |
|--------|------|
| id | integer |
| fecha | timestamp without time zone |
| val | real |
| id_est | character |

**Foreign Keys:**

| Column | References |
|--------|------------|
| id_est | cont_estaciones(id) |

### cont_sodos
| Column | Type |
|--------|------|
| id | integer |
| fecha | timestamp without time zone |
| val | real |
| id_est | character |

**Foreign Keys:**

| Column | References |
|--------|------------|
| id_est | cont_estaciones(id) |

### cont_units
| Column | Type |
|--------|------|
| id | integer |
| unit | character varying |
| nombre | character varying |

### forecast_co
| Column | Type |
|--------|------|
| id | integer |
| fecha | timestamp without time zone |
| val | real |
| id_est | character |
| id_tipo_pronostico | integer |

**Foreign Keys:**

| Column | References |
|--------|------------|
| id_tipo_pronostico | tipo_pronostico(id) |

### forecast_no
| Column | Type |
|--------|------|
| id | integer |
| fecha | timestamp without time zone |
| val | real |
| id_est | character |

### forecast_nodos
| Column | Type |
|--------|------|
| id | integer |
| fecha | timestamp without time zone |
| val | real |
| id_est | character |

### forecast_nox
| Column | Type |
|--------|------|
| id | integer |
| fecha | timestamp without time zone |
| val | real |
| id_est | character |
| id_tipo_pronostico | integer |

**Foreign Keys:**

| Column | References |
|--------|------------|
| id_tipo_pronostico | tipo_pronostico(id) |

### forecast_otres
| Column | Type |
|--------|------|
| fecha | timestamp without time zone |
| val | real |
| id_est | character |
| id | integer |
| id_tipo_pronostico | integer |
| id_hora_pronostico |
| hour_p01 | real |
| hour_p02 | real |
| hour_p03 | real |
| hour_p04 | real |
| hour_p05 | real |
| hour_p06 | real |
| hour_p07 | real |
| hour_p08 | real |
| hour_p09 | real |
| hour_p10 | real |
| hour_p11 | real |
| hour_p12 | real |
| hour_p13 | real |
| hour_p14 | real |
| hour_p15 | real |
| hour_p16 | real |
| hour_p17 | real |
| hour_p18 | real |
| hour_p19 | real |
| hour_p20 | real |
| hour_p21 | real |
| hour_p22 | real |
| hour_p23 | real |
| hour_p24 | real |

**Foreign Keys:**

| Column | References |
|--------|------------|
| id_tipo_pronostico | tipo_pronostico(id) |

### forecast_pmco
| Column | Type |
|--------|------|
| id | integer |
| fecha | timestamp without time zone |
| val | real |
| id_est | character |


### forecast_pmdiez
| Column | Type |
|--------|------|
| id | integer |
| fecha | timestamp without time zone |
| val | real |
| id_est | character |
| id_tipo_pronostico | integer |

**Foreign Keys:**

| Column | References |
|--------|------------|
| id_tipo_pronostico | tipo_pronostico(id) |

### forecast_pmdoscinco
| Column | Type |
|--------|------|
| id | integer |
| fecha | timestamp without time zone |
| val | real |
| id_est | character |

### forecast_sodos
| Column | Type |
|--------|------|
| id | integer |
| fecha | timestamp without time zone |
| val | real |
| id_est | character |
| id_tipo_pronostico | integer |

**Foreign Keys:**

| Column | References |
|--------|------------|
| id_tipo_pronostico | tipo_pronostico(id) |

### historical_values
| Column | Type |
|--------|------|
| id | integer |
| fecha | timestamp without time zone |
| id_tabla | text |
| id_est | character |
| val | real |

### met_pba
| Column | Type |
|--------|------|
| id | integer |
| fecha | timestamp without time zone |
| val | real |
| id_est | character |

### met_rh
| Column | Type |
|--------|------|
| id | integer |
| fecha | timestamp without time zone |
| val | real |
| id_est | character |

### met_tmp
| Column | Type |
|--------|------|
| id | integer |
| fecha | timestamp without time zone |
| val | real |
| id_est | character |

### met_wdr
| Column | Type |
|--------|------|
| id | integer |
| fecha | timestamp without time zone |
| val | real |
| id_est | character |

### met_wsp
| Column | Type |
|--------|------|
| id | integer |
| fecha | timestamp without time zone |
| val | real |
| id_est | character |

### spatial_ref_sys
| Column | Type |
|--------|------|
| srid | integer |
| auth_name | character varying |
| auth_srid | integer |
| srtext | character varying |
| proj4text | character varying |

### tipo_pronostico
| Column | Type |
|--------|------|
| id | real |
| tipo_pronostico | text |
| descripcion | text |

## Views

### geography_columns
| Column | Type |
|--------|------|
| f_table_catalog | name |
| f_table_schema | name |
| f_table_name | name |
| f_geography_column | name |
| coord_dimension | integer |
| srid | integer |
| type | text |

### geometry_columns
| Column | Type |
|--------|------|
| f_table_catalog | character varying |
| f_table_schema | name |
| f_table_name | name |
| f_geometry_column | name |
| coord_dimension | integer |
| srid | integer |
| type | character varying |

