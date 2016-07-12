/* This query obtains the some value from for a day, for an specific year range and station */
SELECT OPER(val) as mval, 
     date_part('day',fecha) as dia, 
      date_part('month',fecha) as mes, 
      date_part('year',fecha) as anio,
      id_est
  FROM TABLE
  WHERE 
    date_part('year',fecha) >= MINANIO
    and date_part('year',fecha) <= MAXANIO
  GROUP BY dia,mes,anio,id_est
  ORDER BY anio,mes,dia
