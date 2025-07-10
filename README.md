# Air Quality Data Analysis Dashboard

A Dash-based web application for analyzing air quality monitoring data from multiple stations.

## Features

- **Interactive Map**: Select monitoring stations by clicking on the map
- **Pollutant Analysis**: Choose from different air pollutants (Ozone, CO₂, NOx, PM, etc.)
- **Time Series Visualization**: View pollutant levels over customizable time periods
- **Flexible Time Windows**: Adjust the analysis window from 1 hour to 6 months

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Database Connection

The dashboard uses the database connection utilities from `db_utils.sql_common.py`. 
Make sure your `.netrc` file contains the credentials for the `DB-OZ` machine.

### 3. Pollutant Mapping

The pollutant mapping is configured in `db_utils.sql_common.py` with the correct table names:

```python
POLLUTANT_MAPPING = {
    'co': 'Carbon monoxide (CO)',
    'no': 'Nitric oxide (NO)',
    'nox': 'Nitrogen oxides (NOₓ: NO + NO₂)',
    'pmdiez': 'Particulate matter ≤ 10 µm (PM₁₀)',
    'pmdoscinco': 'Particulate matter ≤ 2.5 µm (PM₂.₅)',
    'sodos': 'Carbon dioxide (CO₂)',
    'otres': 'Ozone (O₃)'
}
```

### 4. Run the Dashboard

```bash
python dashboard.py
```

The dashboard will be available at `http://localhost:8050`

## Usage

### By Station Tab

1. **Select Pollutant**: Choose the air pollutant you want to analyze from the dropdown
2. **Set Start Date**: Use the calendar to select the starting date (defaults to 10 days ago)
3. **Adjust Time Window**: Use the slider to set how many hours of data to display (1 hour to 6 months)
4. **Select Station**: Click on a station in the map to view its data
5. **View Results**: The time series plot will show pollutant levels for the selected station and time period

## Database Schema

The dashboard expects the following tables:

- `cont_estaciones`: Station information with geometry
- `cont_{pollutant}`: Pollutant data tables (e.g., `cont_otres`, `cont_co`, etc.)

Each pollutant table should have columns:
- `id`: Primary key
- `fecha`: Timestamp
- `val`: Numeric value
- `id_est`: Station ID (foreign key to `cont_estaciones.id`)

## Customization

### Adding New Pollutants

1. Add the table name and display name to `POLLUTANT_MAPPING` in `db_utils.sql_common.py`
2. Ensure the table follows the expected schema

### Adding New Tabs

1. Add new `dcc.Tab` components to the layout
2. Create corresponding callback functions for interactivity

## Troubleshooting

### Database Connection Issues

- Verify database credentials in `config.py`
- Ensure PostgreSQL is running and accessible
- Check that the database contains the expected tables

### Map Not Loading

- Verify that `cont_estaciones` table has valid geometry data
- Check that the `geom` column contains valid coordinates

### No Data Displayed

- Verify the selected station has data for the chosen pollutant
- Check the date range - ensure data exists for the selected period
- Verify table names match the pollutant mapping 