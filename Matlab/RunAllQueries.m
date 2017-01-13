function RunAllQueries()
    close all;
    clear all;
    clc;

    if(isunix)
        addpath('./lib/')
        addpath('./AllPrograms/')
        javaaddpath('/usr/share/java/postgresql-jdbc4-9.2.jar');
    elseif(ispc)
        addpath('.\lib')
        addpath('.\AllPrograms')
        javaaddpath('.\DB\JDBCDriver\postgresql-9.4.1211.jre6.jar');
        %javaaddpath('C:\Users\Felipe\Documents\servicio_datos\cca_cont\Matlab\DB\JDBCDriver\postgresql-9.4.1211.jre6.jar')
    end

    conn = database('contingencia','soloread','SH3<t!4e',...
            'Vendor','PostgreSQL',...
            'Server','132.248.8.238')

    mycolors = 'rgbcmyk';

    tablas = getTablas();
    [claves,allest] = getEstaciones(conn);
    ppmVal = '166';
tablas
    try
%        [years, count] = ContingenciasPorAnio('cont_otres',ppmVal,conn);

        for ii = 1:length(tablas)
            tabla = tablas{ii};

            %[dates, vals] = MinimosMaximosDiarios(tabla,conn);
%            [dates, vals] = MinimosMaximosDiariosByYear(tabla,num2str(2012),conn);
%            [dates, vals] = MinimosGlobalesDiarios(tabla,conn);
%            [dates, vals] = MinimosGlobalesHorarios(tabla,conn);
%            
%            [dates, vals] = PromediosGlobalesDiarios(tabla,conn);
%
%            [dates, vals] = MaximosGlobalesHorarios(tabla,conn);
%            [dates, vals] = MaximosGlobalesDiarios(tabla,conn);
%            [vals] = AvgDayOfWeek(tabla,conn);
%            [vals] = AvgByMonth(tabla,conn);
             [vals] = Avgbyhour_yiz(tabla,conn);  

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

