/* This query obtains the minimum value from all the stations for each hour */
SELECT max(val) as mval, fecha
  FROM TABLE
  GROUP BY fecha
  ORDER BY fecha
