function [vals] = Avgbyhour_yiz(tabla,conn)

    %%% It Gets the average for each hour from all the stations

    folder = getSqlFolder()
    sqlquery = fileread(strcat(folder,'/','AvgByHour.sql'));
    sqlquery = strrep(sqlquery,'TABLE',tabla);

    curs = exec(conn,sqlquery);%Este regresa un cursor
    curData = fetch(curs); %Este hace un fetch de los datos, se puede usar como filtro tabla = datos.Data; %Aquí le exprimes los datos 
    datos = curData.Data;
    vals = cell2mat(datos(:,1));
    [accr contaminante] = getContaminante(tabla);
    titleF = strcat('Promedios de: ', accr);
    H=[0:1:24]; % dar formato
    %[del labels] = weekday([2:8],'long','local');
  
    f = figure('Position',[300 300 800 400]);
    bar(vals,'FaceColor',[0 .5 .5],'EdgeColor',[0 .9 .9],'LineWidth',1.5);
    ylim([min(vals)-std(vals) max(vals)+std(vals)]);
    title(titleF);
    grid
    set(gca,'Xtick',H);
    set(gcf,'PaperPositionMode','auto');
    mkdir('Figures','AvgByHour');
    saveas(f,strcat('Figures/AvgByHour/',tabla,'.jpg'));
end