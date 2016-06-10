function [years, vals] = ContingenciasPorAnio(tabla,limite,conn)
    sqlquery = fileread('../DB/SQL_queries/DiasDeContingenciaPorAnioMatlab.sql');
    sqlquery = strrep(sqlquery,'TABLE',tabla)
    sqlquery = strrep(sqlquery,'PARAM',limite)

    curs = exec(conn,sqlquery) %Este regresa un cursor
    curData = fetch(curs); %Este hace un fetch de los datos, se puede usar como filtro tabla = datos.Data; %Aquí le exprimes los datos 
    datos = curData.Data;
    years = cell2mat(datos(:,2));
    vals = cell2mat(datos(:,1));
    titleF = strcat('Dias de contingencias por ano con ppb > ',limite);
    plot(years,vals,'or') 
    title(titleF)
end
