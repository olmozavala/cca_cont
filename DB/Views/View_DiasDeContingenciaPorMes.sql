/* This script generates a view with the number or days which maximum value exceeds 166 for each month*/
CREATE VIEW cont_monthly_onesixsix AS
SELECT count(*), mes, anio
    FROM (
        /* This internal query obtains the max daily ozone values from all stations */
        SELECT max(val) as mval, date_part('day',fecha) as dia, 
                date_part('month',fecha) as mes, date_part('year',fecha) as anio 
        FROM cont_otres
        GROUP BY dia, mes, anio 
        ORDER BY anio ASC, mes ASC, dia ASC
        ) as maxvalues

    WHERE mval > 166
    GROUP BY mes, anio
    ORDER BY anio, mes
