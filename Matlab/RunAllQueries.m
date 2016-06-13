function RunAllQueries()
    close all;
    clear all;
    clc;

    javaaddpath('/usr/share/java/postgresql-jdbc4-9.2.jar');

    conn = database('contingencia','argel','contargel',...
            'Vendor','PostgreSQL',...
            'Server','132.248.8.238')

    mycolors = 'rgbcmyk';

    tablas = getTablas();
    [claves allest] = getEstaciones(conn);
    ppmVal = '166';

    try
        [years, count] = ContingenciasPorAnio('cont_otres',ppmVal,conn);

        for ii = 1:length(tablas)
            tabla = tablas{ii};

            [dates, vals] = MinimosMaximosDiarios(tabla,conn);
            [dates, vals] = MinimosGlobalesDiarios(tabla,conn);
            [dates, vals] = MinimosGlobalesHorarios(tabla,conn);
            
            [dates, vals] = PromediosGlobalesDiarios(tabla,conn);

            [dates, vals] = MaximosGlobalesHorarios(tabla,conn);
            [dates, vals] = MaximosGlobalesDiarios(tabla,conn);

%            % --------------------------------------------------------------%
%            % Plotting values by station, in this case maximum value by day
%            estWithValues = 1;
%            [dates vals estvals] = GetSomethingByDay(tabla,'MAX',2015,2016,false,conn);
%            if length(vals) > 0
%                figure
%                diffEst = unique(estvals,'rows');
%                for jj = 1:length(diffEst)
%                    estIdxs =  strmatch(diffEst(jj,:),estvals);
%                    plot(dates(estIdxs),vals(estIdxs),strcat('.',mycolors(mod(jj,7)+1)),'MarkerSize',.5);
%                    hold on;
%                end
%                legend(diffEst);
%                [accr contaminante] = getContaminante(tabla);
%                title(contaminante)
%                hold off;
%            end

        end
    catch err
        display('Closing connection!');
        close(conn)
        rethrow(err)
    end

    display('Closing connection!');
    close(conn)
end
