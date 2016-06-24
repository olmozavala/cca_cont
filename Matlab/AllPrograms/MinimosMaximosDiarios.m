function [dates vals] = MinimosMaximosDiarios(tabla,conn)
    %%%
    sqlquery = fileread('../DB/SQL_queries/Matlab/MinimosMaximosDiariosMatlab.sql');
    sqlquery = strrep(sqlquery,'TABLE',tabla);

    curs = exec(conn,sqlquery);%Este regresa un cursor
    curData = fetch(curs); %Este hace un fetch de los datos, se puede usar como filtro tabla = datos.Data; %Aquí le exprimes los datos 
    datos = curData.Data;

    dates = datetime(cell2mat(datos(:,4:-1:2)));
    vals = cell2mat(datos(:,1));
    [accr contaminante] = getContaminante(tabla);
    titleF = strcat('Maximos minimos de:',' ', accr);

    f = figure('Position',[300 300 1500 400]);
    plot(dates,vals,'.k') 
    datetick('x','dd/mm/yyyy','keeplimits','keepticks')
    title(titleF)
    axis('tight')
    grid
    set(gcf,'PaperPositionMode','auto');
    mkdir('Figures','MinimosMaximos');
    saveas(f,strcat('Figures/MinimosMaximos/',tabla,'.jpg'));
end
