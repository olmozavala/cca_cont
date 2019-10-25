/* This query obtains the number of days where the max value of ozone exceeds 150 ppb */
SELECT val, date_part('year',fecha) as anio,
	date_part('month',fecha) as mes,
	date_part('day',fecha) as dia,
	date_part('hour',fecha) as hora
    FROM TABLA
      
    ORDER BY fecha
