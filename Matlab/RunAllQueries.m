function RunAllQueries()
    close all;
    clear all;
    clc;

    javaaddpath('/usr/share/java/postgresql-jdbc4-9.2.jar');

    conn = database('contingencia','argel','contargel',...
            'Vendor','PostgreSQL',...
            'Server','132.248.8.238')

    tablas = getTablas()
    ppmVal = '166';

    try
        
        for ii = 1:length(tablas)
            tabla = tablas{ii}
            %[years, count] = ContingenciasPorAnio(tabla,ppmVal,conn)
            %[dates, minis] = MinimosMaximos(tabla,conn);
            [dates, minis] = MinimosMaximosHorarios(tabla,conn);
        end
    catch err
        display('Closing connection!');
        close(conn)
        rethrow(err)
    end

    display('Closing connection!');
    close(conn)
end

