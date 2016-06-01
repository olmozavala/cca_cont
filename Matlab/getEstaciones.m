function [claves, nombres] = getEstaciones(conn)
    % GETESTACIONES Gets the ids and names of the meteorological stations
    sqlquery = ['SELECT * FROM cont_estaciones' ]
        
    curs = exec(conn,sqlquery) %Este regresa un cursor
    datos = fetch(curs) %Este hace un fetch de los datos, se puede usar como filtro 
    tabla = datos.Data 

    claves = cell2mat(tabla(:,1));
    nombres= tabla(:,2);
