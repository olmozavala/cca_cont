function [dates vals] = MinimosMaximosHorarios(tabla,conn)
    sqlquery = fileread('../DB/SQL_queries/MinimosMaximosHorariosMatlab.sql');
    sqlquery = strrep(sqlquery,'TABLE',tabla)

    curs = exec(conn,sqlquery) %Este regresa un cursor
    curData = fetch(curs); %Este hace un fetch de los datos, se puede usar como filtro tabla = datos.Data; %Aquí le exprimes los datos 
    datos = curData.Data;

    dates = datetime(cell2mat(datos(:,5:-1:3)));
    vals = cell2mat(datos(:,1));
    [accr contaminante] = getContaminante(tabla)
    titleF = strcat('Maximos minimos de ', accr);

    f = figure
    plot(dates,vals,'.k','MarkerSize',.5);
    datetick('x','dd/mm/yyyy','keeplimits','keepticks');
    title(titleF)
    axis('tight')
    grid
    saveas(f,strcat('Figures/MinimosMaximos/',tabla,'.jpg'));
end
