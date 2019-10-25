/* This query obtains the number of days where the max value of ozone exceeds 150 ppb */

SELECT count(*), anio 
    FROM (
        /* This internal query obtains the max daily ozone values from all stations */
        SELECT max(val) as mval, date_part('day',fecha) as dia, 
                date_part('month',fecha) as mes, date_part('year',fecha) as anio 
        FROM cont_otres
        GROUP BY dia, mes, anio 
        ORDER BY anio ASC, mes ASC, dia ASC
        ) as maxvalues

    WHERE mval > 150
    GROUP BY anio
    ORDER BY anio
