/* This query obtains the maximum of all the minimums (by station) for every day*/
SELECT max(mval), dia, mes, anio FROM (
	SELECT min(val) as mval,   
	  date_part('day',fecha) as dia, 
	  date_part('month',fecha) as mes, 
	  date_part('year',fecha) as anio,
	  id_est
	  FROM TABLE
	  GROUP BY anio,mes,dia,id_est
	  ORDER BY anio, mes, dia) as minbyest	  
  GROUP BY anio,mes,dia
  ORDER BY anio, mes, dia

