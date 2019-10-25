/* This query obtains the minimum value from all the stations for each day */
SELECT min(val) as mval, 
     date_part('day',fecha) as dia, 
      date_part('month',fecha) as mes, 
      date_part('year',fecha) as anio
  FROM cont_otres
  GROUP BY dia,mes,anio
  ORDER BY anio,mes,dia
