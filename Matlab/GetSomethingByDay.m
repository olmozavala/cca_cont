
function [dates vals est] = GetSomethingByDay(tabla,oper,minyear,maxyear,drawFig, conn)
    %%% GETSOMETHINGBYDAY Gets one operation by day

    datos = {};
    sqlquery = fileread('../DB/SQL_queries/Matlab/CustomByDay.sql');
    sqlquery = strrep(sqlquery,'TABLE',tabla);
    sqlquery = strrep(sqlquery,'OPER',oper);
    sqlquery = strrep(sqlquery,'MINANIO',num2str(minyear));
    sqlquery = strrep(sqlquery,'MAXANIO',num2str(maxyear));
    sqlquery

    curs = exec(conn,sqlquery); %Este regresa un cursor
    curData = fetch(curs); %Este hace un fetch de los datos, se puede usar como filtro tabla = datos.Data; %Aquí le exprimes los datos 
    datos = curData.Data;

    if length(datos) > 1 
        dates = datetime(cell2mat(datos(:,4:-1:2)));
        est = cell2mat(datos(:,5));
        vals = cell2mat(datos(:,1));
        if drawFig
            [accr contaminante] = getContaminante(tabla);
            titleF = strcat(upper(oper),' diarios de: ', accr);
            f = figure
            plot(dates,vals,'.k','MarkerSize',.5);
            datetick('x','dd/mm/yyyy','keeplimits','keepticks');
            title(titleF)
            axis('tight')
            grid
            saveas(f,strcat('Figures/ByDay/',tabla,'_',oper,'_',minyear,'-',maxyear,'.jpg'));
        end
    else
        dates = [];
        vals = [];
        est = [];
    end
end
