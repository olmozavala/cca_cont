
function [dates vals] = MinimosGlobalesDiariosPorEstacion(est, tabla,conn)
    %%% MINIMOSGLOBALESHORARIOS Gets the minimum values for each hour from all the stations

    folder = getSqlFolder()
    sqlquery = fileread(strcat(folder,'/','MinimosGlobalesDiariosPorEstacionMatlab.sql'));
    sqlquery = strrep(sqlquery,'TABLE',tabla);
    sqlquery = strrep(sqlquery,'ESTATION',est);
    display(est)

    curs = exec(conn,sqlquery);%Este regresa un cursor
    curData = fetch(curs); %Este hace un fetch de los datos, se puede usar como filtro tabla = datos.Data; %Aquí le exprimes los datos 
    datos = curData.Data;
    if( length(datos) > 1)

        dates = datetime(cell2mat(datos(:,4:-1:2)));

        vals = cell2mat(datos(:,1));
        [accr contaminante] = getContaminante(tabla);
        titleF = strcat('Minimos globales Diarios de: ', accr, ' estacion:', est);

        f = figure('Position',[300 300 1500 400]);
        plot(dates,vals,'.k','MarkerSize',.5);
        datetick('x','dd/mm/yyyy','keeplimits','keepticks');
        title(titleF)
        axis('tight')
        grid
        set(gcf,'PaperPositionMode','auto');
        mkdir('Figures','MinimosPorEstacionDiarios');
        saveas(f,strcat('Figures/MinimosPorEstacionDiarios/',tabla,'_',est,'.jpg'));
        close(f)
    else
        dates = -1;
        vals = -1;
    end
end
