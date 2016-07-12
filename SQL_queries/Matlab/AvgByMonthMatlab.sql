/* Average contaminant divided by month */
SELECT avg(val) as mval, date_part('month',fecha) as mymonth
    FROM TABLE
    GROUP BY mymonth

