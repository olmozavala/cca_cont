/* This query obtains the maximum of all the minimums (by station) for every day*/
SELECT max(mval), hora, dia, mes, anio FROM 
( SELECT min(val) as mval, 
  date_part('hour',fecha) as hora, 
  date_part('day',fecha) as dia, 
  date_part('month',fecha) as mes, 
  date_part('year',fecha) as anio,
  id_est
  FROM TABLE
  GROUP BY hora, dia, mes, anio, id_est
  ORDER BY anio ASC, mes ASC, dia) as minbyest

GROUP BY hora, dia, mes, anio
ORDER BY anio,mes,dia,hora 
