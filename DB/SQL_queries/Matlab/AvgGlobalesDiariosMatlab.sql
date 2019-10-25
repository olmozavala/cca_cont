/* This query obtains the minimum value from all the stations for each day */
SELECT avg(val) as mval, 
     date_part('day',fecha) as dia, 
      date_part('month',fecha) as mes, 
      date_part('year',fecha) as anio
  FROM TABLE 
  GROUP BY dia,mes,anio
  ORDER BY anio,mes,dia
