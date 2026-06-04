# Download SINAICA data as CSV

Hourly air-quality observations from the [Sistema Nacional de Información de Calidad del Aire (SINAICA)](https://sinaica.inecc.gob.mx/) — Instituto Nacional de Ecología y Cambio Climático (INECC).

This folder contains one script, `sinaica_descarga.sh`, that queries the public SINAICA web API and saves results as CSV.

## What you need

| Tool | When |
|------|------|
| `bash` | Always |
| `curl` | Always (HTTP download) |
| `python3` | When using `-c` to build the CSV |

Activate your environment so `python3` is available (optional but recommended):

```bash
source /home/olmozavala/uv/envs/eoasweb/bin/activate
```

## Before you download

1. Open the [SINAICA data portal](https://sinaica.inecc.gob.mx/data.php).
2. Pick a **network**, **station**, and note the station **ID** (`estacionId`).
3. Choose the **pollutant** code (e.g. `O3`, `PM10`, `PM2.5`) and the **start date**.

Each run downloads **one station × one pollutant × one time range**.

## Quick start (CSV)

```bash
cd /home/olmozavala/Dropbox/CODE/cca_cont/download_from_sinaica
chmod +x sinaica_descarga.sh   # once
mkdir -p temp_output

bash sinaica_descarga.sh \
  -e 134 \
  -p O3 \
  -f 2026-06-03 \
  -r 1dia \
  -c \
  -o temp_output/cuernavaca_o3.csv
```

Always pass **`-c`** when you want a CSV file. Use **`-o`** to set the output path.

Help text from the script:

```bash
bash sinaica_descarga.sh -h
```

## Command-line options

| Flag | Required | Description |
|------|----------|-------------|
| `-e` | Yes | Station ID from SINAICA |
| `-p` | Yes | Pollutant: `O3`, `PM10`, `PM2.5`, `CO`, `NO2`, `SO2`, `NO`, `NOx`, `TMP`, `HR`, … |
| `-f` | Yes | Start date `YYYY-MM-DD` |
| `-r` | Yes | Period: `1dia`, `1semana`, `2semanas`, `1mes`, `1anio`, `2anios` |
| `-t` | No | Data type: default = raw (Crude); `V` = validated; `M` = manual |
| `-o` | No | Output path (use with `-c` for CSV) |
| `-c` | No | **Write CSV** (requires `python3`) |
| `-v` | No | Verbose HTTP |
| `-h` | No | Help |

If you use `-c` without `-o`, the file is named  
`sinaica_<stationId>_<param>_<date>_<range>.csv` in the current directory.

With `-c` and `-o temp_output/myfile.csv`, the CSV is written to that path (any extension you pass is treated as `.csv`).

## CSV format

Each row is one hourly record. Columns:

| Column | Description |
|--------|-------------|
| `id` | SINAICA record identifier |
| `fecha` | Date (`YYYY-MM-DD`) |
| `hora` | Hour of day (0–23) |
| `valor` | Measured value |
| `bandO` | Quality flag |
| `val` | Validity flag |
| `estacion_id` | Station ID (added by script) |
| `parametro` | Pollutant code (added by script) |

Files use UTF-8 with BOM so Excel opens them correctly in Spanish locales.

## Station catalog

Use the **ID** column as `-e` in `sinaica_descarga.sh`. List taken from the [SINAICA data portal](https://sinaica.inecc.gob.mx/data.php) monitoring-station selector (**Red** networks, 181 stations). For the latest IDs, check the portal if a download fails.

| ID | State | Network | Station |
|----|-------|---------|----------|
| 31 | Aguascalientes | Aguascalientes | CBTIS |
| 33 | Aguascalientes | Aguascalientes | Centro |
| 303 | Aguascalientes | Aguascalientes | Instituto Educativo |
| 32 | Aguascalientes | Aguascalientes | Secretaría de Medio Ambiente |
| 504 | Baja California - Estatal | Ensenada | Ensenada |
| 41 | Baja California - Estatal | Mexicali | CESPM |
| 39 | Baja California - Estatal | Mexicali | COBACH |
| 371 | Baja California - Estatal | Mexicali | UABC |
| 503 | Baja California - Estatal | Tecate | Tecate |
| 47 | Baja California - Estatal | Tijuana | La Mesa |
| 46 | Baja California - Estatal | Tijuana | Laboratorio |
| 437 | Baja California - Municipal | Municipio de Mexicali | Centro Cívico |
| 499 | Baja California - Municipal | Municipio de Mexicali | Comandancia Anáhuac |
| 491 | Baja California Sur | Baja California Sur | Junta Estatal de Caminos |
| 50 | Chiapas | Tuxtla Gutiérrez | Palacio Municipal |
| 428 | Chihuahua - | Ciudad Juárez 2 | Instituto de Ingeniería y Tecnología |
| 112 | Chihuahua - Ciudad Juárez | Municipio de Juárez | Advance - Keytronic |
| 111 | Chihuahua - Ciudad Juárez | Municipio de Juárez | Canales Lira |
| 482 | Chihuahua - Ciudad Juárez | Municipio de Juárez | Clínica de Nutrición |
| 448 | Chihuahua - Ciudad Juárez | Municipio de Juárez | Planta de Tratamiento de Aguas Residuales Norte |
| 55 | Chihuahua - Municipal | CHIH2 | CIMAV |
| 54 | Chihuahua -Estatal | CHIH1 | Centro |
| 53 | Chihuahua -Estatal | CHIH1 | SUR |
| 240 | Ciudad de México | Valle de México | Acolman |
| 242 | Ciudad de México | Valle de México | Ajusco Medio |
| 243 | Ciudad de México | Valle de México | Atizapán |
| 300 | Ciudad de México | Valle de México | Benito Juárez |
| 244 | Ciudad de México | Valle de México | Camarones |
| 245 | Ciudad de México | Valle de México | Centro de Ciencias de la Atmósfera |
| 246 | Ciudad de México | Valle de México | Chalco |
| 248 | Ciudad de México | Valle de México | Cuajimalpa |
| 249 | Ciudad de México | Valle de México | Cuautitlán |
| 250 | Ciudad de México | Valle de México | FES Acatlán |
| 431 | Ciudad de México | Valle de México | FES Aragón |
| 302 | Ciudad de México | Valle de México | Gustavo A. Madero |
| 251 | Ciudad de México | Valle de México | Hospital General de México |
| 252 | Ciudad de México | Valle de México | Iztacalco |
| 253 | Ciudad de México | Valle de México | La Presa |
| 254 | Ciudad de México | Valle de México | Los Laureles |
| 256 | Ciudad de México | Valle de México | Merced |
| 263 | Ciudad de México | Valle de México | Miguel Hidalgo |
| 258 | Ciudad de México | Valle de México | Nezahualcóyotl |
| 259 | Ciudad de México | Valle de México | Pedregal |
| 260 | Ciudad de México | Valle de México | San Agustín |
| 262 | Ciudad de México | Valle de México | Santa Fe |
| 432 | Ciudad de México | Valle de México | Santiago Acahualtepec |
| 265 | Ciudad de México | Valle de México | Tlahuac |
| 266 | Ciudad de México | Valle de México | Tlalnepantla |
| 267 | Ciudad de México | Valle de México | Tultitlán |
| 268 | Ciudad de México | Valle de México | UAM Iztapalapa |
| 269 | Ciudad de México | Valle de México | UAM Xochimilco |
| 270 | Ciudad de México | Valle de México | Villa de las Flores |
| 271 | Ciudad de México | Valle de México | Xalostoc |
| 305 | Coahuila | Monclova | Jurisdicción Sanitaria |
| 306 | Coahuila | Piedras Negras | Centro de Rehabilitación DIF |
| 486 | Coahuila | Ramos Arizpe | Servicios Municipales |
| 304 | Coahuila | Saltillo | Finanzas |
| 56 | Coahuila | Torreón | CONALEP |
| 57 | Colima | Colima | Tecnologico |
| 59 | Durango | Durango | IPN |
| 58 | Durango | Durango | ITD |
| 60 | Durango | Durango | SRNyMA |
| 65 | Durango | Gómez Palacio | Campestre |
| 430 | Durango | Gómez Palacio | Parque La Esperanza |
| 67 | Durango | Lerdo | SAGARPA |
| 342 | Durango | Lerdo | Tecnológico Lerdo |
| 356 | Guanajuato | Abasolo | Presidencia Municipal |
| 68 | Guanajuato | Celaya | Policía |
| 70 | Guanajuato | Celaya | San Juanico |
| 69 | Guanajuato | Celaya | Tecnológico |
| 359 | Guanajuato | Guanajuato | Universidad Gto Sede Belen |
| 72 | Guanajuato | Irapuato | Bomberos |
| 71 | Guanajuato | Irapuato | Sec. Oficial |
| 73 | Guanajuato | Irapuato | Teódula |
| 74 | Guanajuato | León | CICEG - Bomberos |
| 75 | Guanajuato | León | Facultad de Medicina |
| 76 | Guanajuato | León | T21 |
| 423 | Guanajuato | Purísima del Rincón | Purísima del Rincón |
| 77 | Guanajuato | Salamanca | Cruz roja |
| 78 | Guanajuato | Salamanca | DIF |
| 79 | Guanajuato | Salamanca | Nativitas |
| 358 | Guanajuato | San Luis de la Paz | Presidencia Municipal |
| 352 | Guanajuato | San Miguel de Allende | Presidencia Municipal |
| 80 | Guanajuato | Silao | Hospital General |
| 82 | Hidalgo | Atitalaquia | Centro de Salud |
| 83 | Hidalgo | Atotonilco | Primaria Revolución |
| 85 | Hidalgo | Huichapan | Hospital |
| 495 | Hidalgo | Mineral de la Reforma | Mineral de la Reforma |
| 487 | Hidalgo | Mixquiahuala de Juárez | Primaria Amado Nervo |
| 95 | Hidalgo | Pachuca | Instituto Tecnológico de Pachuca |
| 501 | Hidalgo | Pachuca | Primaria Ignacio Zaragoza |
| 84 | Hidalgo | Tepeapulco | Estación de Bomberos de Cd. Sahagún |
| 87 | Hidalgo | Tepeji | Primaria Melchor Ocampo |
| 96 | Hidalgo | Tizayuca | Biblioteca |
| 502 | Hidalgo | Tula | Primaria Venustiano Carranza |
| 442 | Hidalgo | Tula | Universidad Tecnológica de Tula Tepeji |
| 292 | Hidalgo | Tulancingo | Tulancingo |
| 101 | Jalisco | Guadalajara | Atemajac |
| 102 | Jalisco | Guadalajara | Centro |
| 492 | Jalisco | Guadalajara | Country |
| 104 | Jalisco | Guadalajara | Las Pintas |
| 103 | Jalisco | Guadalajara | Las Águilas |
| 105 | Jalisco | Guadalajara | Loma Dorada |
| 106 | Jalisco | Guadalajara | Miravalle |
| 107 | Jalisco | Guadalajara | Oblatos |
| 494 | Jalisco | Guadalajara | Santa Anita |
| 108 | Jalisco | Guadalajara | Santa Fe |
| 493 | Jalisco | Guadalajara | Santa Margarita |
| 109 | Jalisco | Guadalajara | Tlaquepaque |
| 110 | Jalisco | Guadalajara | Vallarta |
| 131 | Michoacán | Morelia | Laboratorio de Salud |
| 388 | Michoacán | Morelia | Palacio Municipal |
| 129 | Michoacán | Morelia | Universidad Michoacana de San Nicolás Hidalgo |
| 132 | Morelos | Cuautla | Palacio Municipal Cuautla |
| 134 | Morelos | Cuernavaca | Cuernavaca 01 |
| 133 | Morelos | Ocuituco | Palacio Municipal |
| 135 | Morelos | Zacatepec | Tecnológico de Zacatepec |
| 456 | México | Toluca | Almoloya de Juárez |
| 458 | México | Toluca | Calimaya |
| 123 | México | Toluca | Ceboruco |
| 125 | México | Toluca | Metepec |
| 126 | México | Toluca | Oxtotitlán |
| 128 | México | Toluca | San Mateo Atenco |
| 124 | México | Toluca | Toluca Centro |
| 457 | México | Toluca | Xonacatlán |
| 136 | Nayarit | Tepic | Tecnológico de Tepic |
| 480 | Nayarit | Tepic | Universidad |
| 146 | Nuevo León | Monterrey | Apodaca |
| 424 | Nuevo León | Monterrey | Cadereyta |
| 144 | Nuevo León | Monterrey | Escobedo |
| 145 | Nuevo León | Monterrey | García |
| 143 | Nuevo León | Monterrey | ITNL |
| 147 | Nuevo León | Monterrey | Juárez |
| 479 | Nuevo León | Monterrey | Misión San Juan |
| 141 | Nuevo León | Monterrey | Obispado |
| 446 | Nuevo León | Monterrey | Pesquería |
| 426 | Nuevo León | Monterrey | Preparatoria ITESM Eugenio Garza Lagüera |
| 140 | Nuevo León | Monterrey | San Bernabé |
| 142 | Nuevo León | Monterrey | San Nicolás |
| 148 | Nuevo León | Monterrey | San Pedro |
| 139 | Nuevo León | Monterrey | Santa Catarina |
| 425 | Nuevo León | Monterrey | UANL |
| 297 | Oaxaca | Oaxaca | Casa Hogar |
| 160 | Oaxaca | Oaxaca | Centro de Educación Artística |
| 161 | Puebla | Puebla | Agua Santa |
| 484 | Puebla | Puebla | Atlixco |
| 163 | Puebla | Puebla | Benemérito Instituto Normal del Estado |
| 162 | Puebla | Puebla | Las Ninfas |
| 485 | Puebla | Puebla | San Martín Texmelucan |
| 483 | Puebla | Puebla | Tehuacán |
| 406 | Puebla | Puebla | Universidad Tecnológica de Puebla |
| 165 | Puebla | Puebla | Velódromo |
| 410 | Querétaro | San Juan del Rio | San Juan del Río |
| 408 | Querétaro | Zona Metropolitana de Querétaro | Carrillo Puerto |
| 450 | Querétaro | Zona Metropolitana de Querétaro | Corregidora |
| 460 | Querétaro | Zona Metropolitana de Querétaro | Epigmenio González |
| 169 | Querétaro | Zona Metropolitana de Querétaro | Félix Osores |
| 454 | Querétaro | Zona Metropolitana de Querétaro | Josefa Vergara |
| 174 | San Luis Potosí | San Luis Potosí Estatal | Biblioteca |
| 172 | San Luis Potosí | San Luis Potosí Estatal | DIF |
| 427 | San Luis Potosí | San Luis Potosí Estatal | Escuela Primaria 1° de mayo |
| 171 | San Luis Potosí | San Luis Potosí Estatal | Industriales Potosinos Asociados |
| 481 | San Luis Potosí | ZM de Rioverde - Cd Fernández | Rioverde |
| 181 | Sinaloa | Los Mochis (Ahome) | DIF Municipal |
| 179 | Sinaloa | Mazatlán | Junta Municipal de Agua Potable |
| 186 | Sonora | Hermosillo | Universidad de Sonora |
| 187 | Sonora | Nogales | Instituto Tecnológico de Nogales |
| 190 | Sonora | San Luis Río Colorado | San Luis Río Colorado |
| 192 | Tabasco | Centro | Instituto Tecnológico de Villahermosa |
| 438 | Tlaxcala | Apizaco | Centro de Salud |
| 221 | Tlaxcala | Calpulalpan | Calpulalpan |
| 220 | Tlaxcala | Tlaxcala | Palacio de Gobierno |
| 476 | Veracruz | Coatzacoalcos | Bomberos y Protección Civil Municipal |
| 234 | Veracruz | Minatitlán | Instituto Tecnológico de Minatitlán |
| 291 | Veracruz | Poza Rica | USBI UV Poza Rica |
| 477 | Veracruz | San Andrés Tuxtla | Poder Judicial del Estado |
| 478 | Veracruz | Tuxpan | Clínica Hospital ISSSTE |
| 447 | Veracruz | Veracruz | Cruz Roja Mexicana |
| 235 | Veracruz | Xalapa | Secretaría de Trabajo y Previsión Social y de Productividad del Estado |
| 236 | Yucatán | Mérida | SDS01 |
| 490 | Zacatecas | Zacatecas | Atmosférico 1 |

## More CSV examples

```bash
# One day, three pollutants, same station
FECHA=2026-06-03
for p in O3 PM10 PM2.5; do
  bash sinaica_descarga.sh -e 134 -p "$p" -f "$FECHA" -r 1dia -c \
    -o "temp_output/cuernavaca_134_${p}_${FECHA}.csv"
done

# One month of PM10, validated data
bash sinaica_descarga.sh -e 271 -p PM10 -f 2026-01-01 -r 1mes -t V -c \
  -o temp_output/pm10_enero.csv
```

## Folder layout

```
download_from_sinaica/
├── README.md
├── sinaica_descarga.sh
└── temp_output/     ← create this; put your CSVs here
```

## Messages and errors

- Status lines (`[INFO]`, `[OK]`, `[WARN]`, `[ERROR]`) print to the terminal; the CSV is written to the path from `-o`.
- Success needs HTTP **200** from SINAICA.
- If there is no data for that query, you get a warning and an empty or missing file.

## How the download works

The script sends a POST request to:

`https://sinaica.inecc.gob.mx/pags/datGrafs.php`

with `estacionId`, `param`, `fechaIni`, `rango`, and optional `tipoDatos`. The response HTML contains a JSON array (`var dat = [...]`). With `-c`, `python3` converts that JSON to the CSV described above.
