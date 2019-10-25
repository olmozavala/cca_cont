/* Average contaminant divided by the day of the week */
SELECT avg(val) as mval, date_part('dow',fecha) as dofw
    FROM cont_otres       
    GROUP BY dofw

