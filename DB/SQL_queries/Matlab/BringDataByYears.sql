/* This query obtains the number of days where the max value of ozone exceeds 150 ppb */
SELECT val, date_part('year',fecha) as anio,
	date_part('month',fecha) as mes,
	date_part('day',fecha) as dia,
	date_part('hour',fecha) as hora,
	id_est
    FROM TABLE
    WHERE 
      date_part('year',fecha) >= MINANIO
	AND
      date_part('year',fecha) <= MAXANIO
	AND
	id_est IN ('ESTATION')
    ORDER BY fecha
