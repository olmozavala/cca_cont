
function [dates vals] = MinimosGlobalesDiarios(tabla,conn)
    %%% MINIMOSGLOBALESHORARIOS Gets the minimum values for each hour from all the stations

    folder = getSqlFolder()
    sqlquery = fileread(strcat(folder,'/','AvgGlobalesDiariosMatlab.sql');
    sqlquery = strrep(sqlquery,'TABLE',tabla);

    curs = exec(conn,sqlquery);%Este regresa un cursor
    curData = fetch(curs); %Este hace un fetch de los datos, se puede usar como filtro tabla = datos.Data; %Aquí le exprimes los datos 
    datos = curData.Data;

    dates = datetime(cell2mat(datos(:,4:-1:2)));

    vals = cell2mat(datos(:,1));
    [accr contaminante] = getContaminante(tabla);
    titleF = strcat('Promedios globales Diarios de: ', accr);

    f = figure('Position',[300 300 1500 400]);
    plot(dates,vals,'.k','MarkerSize',.5);
    datetick('x','dd/mm/yyyy','keeplimits','keepticks');
    title(titleF)
    axis('tight')
    grid
    set(gcf,'PaperPositionMode','auto');
    mkdir('Figures','PromediosGlobalesDiarios');
    saveas(f,strcat('Figures/PromediosGlobalesDiarios/',tabla,'.jpg'));
end
