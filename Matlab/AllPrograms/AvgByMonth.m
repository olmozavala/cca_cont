
function [vals] = AvgByMonth(tabla,conn)
    %%% AVGBYMONTH Gets the average contaminant by month

    sqlquery = fileread('../DB/SQL_queries/Matlab/AvgByMonthMatlab.sql');
    sqlquery = strrep(sqlquery,'TABLE',tabla);

    curs = exec(conn,sqlquery);%Este regresa un cursor
    curData = fetch(curs); %Este hace un fetch de los datos, se puede usar como filtro tabla = datos.Data; %Aquí le exprimes los datos 
    datos = curData.Data;

    vals = cell2mat(datos(:,1));
    [accr contaminante] = getContaminante(tabla);
    titleF = strcat('Promedios de: ', accr);

    for ii = 1:12
        monthStr{ii} = strcat(num2str(ii),'-1-2000');
    end
    [del labels] = month(monthStr);
  
    f = figure('Position',[300 300 800 400]);
    bar(vals,'FaceColor',[0 .5 .5],'EdgeColor',[0 .9 .9],'LineWidth',1.5);
    ylim([min(vals)-std(vals) max(vals)+std(vals)]);
    title(titleF);
    grid
    set(gca,'Xtick',del,'XtickLabel',labels);
    set(gcf,'PaperPositionMode','auto');
    mkdir('Figures','AvgByMonth');
    saveas(f,strcat('Figures/AvgByMonth/',tabla,'.jpg'));
end
