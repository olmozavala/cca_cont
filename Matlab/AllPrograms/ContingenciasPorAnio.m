function [years, vals] = ContingenciasPorAnio(tabla,limite,conn)

    folder = getSqlFolder()
    sqlquery = fileread(strcat(folder,'/','DiasDeContingenciaPorAnioMatlab.sql');
    sqlquery = strrep(sqlquery,'TABLE',tabla);
    sqlquery = strrep(sqlquery,'PARAM',limite)

    curs = exec(conn,sqlquery);%Este regresa un cursor
    curData = fetch(curs); %Este hace un fetch de los datos, se puede usar como filtro tabla = datos.Data; %Aquí le exprimes los datos 
    datos = curData.Data;
    years = cell2mat(datos(:,2));
    vals = cell2mat(datos(:,1));
    titleF = strcat('Dias de contingencias por ano con ppb > ',limite);
    f = figure('Position',[300 300 1500 400]);
    plot(years,vals,'.r');
    title(titleF);
    set(gcf,'PaperPositionMode','auto');
    mkdir('Figures','DiasDeContingenciaPorAnio');
    saveas(f,strcat('Figures/DiasDeContingenciaPorAnio.jpg'));
end
