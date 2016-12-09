SELECT avg(val) as mval, date_part('hour',fecha) as myhour
    FROM TABLE
    GROUP BY myhour