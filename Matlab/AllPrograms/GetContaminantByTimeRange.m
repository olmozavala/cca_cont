
function [dates vals est] = GetContaminantByTimeRange(tabla,minyear,maxyear, station,conn)
    %%% GETSOMETHINGBYDAY Gets one operation by day

    datos = {};
    folder = getSqlFolder()
    sqlquery = fileread(strcat(folder,'/','BringDataByYears.sql'));
    sqlquery = strrep(sqlquery,'TABLE',tabla);
    sqlquery = strrep(sqlquery,'MINANIO',num2str(minyear));
    sqlquery = strrep(sqlquery,'MAXANIO',num2str(maxyear));
    sqlquery = strrep(sqlquery,'ESTATION',station);

    sqlquery

    curs = exec(conn,sqlquery); %Este regresa un cursor
    curData = fetch(curs); %Este hace un fetch de los datos, se puede usar como filtro tabla = datos.Data; %Aquí le exprimes los datos 
    datos = curData.Data;

    save(strcat('ozone',station),'datos')
end
