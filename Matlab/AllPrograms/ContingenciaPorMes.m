close all;
clear all;
clc;

conn = database('contingencia','argel','contargel',...
        'Vendor','PostgreSQL',...
        'Server','132.248.8.238');

tables = {'cont_otres'};
compoundTitle = {'Ozono'};
ppbLimit = 166;

try 
        %for idx = 1:1
            sqlquery = [
            ' SELECT count(*), mes, anio ' ...
                'FROM (' ...
        ' SELECT max(val) as mval, date_part(''day'',fecha) as dia, ' ... 
        '         date_part(''month'',fecha) as mes, date_part(''year'',fecha) as anio ' ...
        ' FROM cont_otres                                         ' ... 
        ' GROUP BY dia, mes, anio                                 ' ... 
        ' ORDER BY anio ASC, mes ASC, dia ASC                     ' ... 
        ' ) as maxvalues                                          ' ...
           '  WHERE mval > ''',num2str(ppbLimit),''' ' ...
           '  GROUP BY mes,anio ' ...
           '  ORDER BY anio,mes ' ];
            
            curs = exec(conn,sqlquery); %Este regresa un cursor
            datos = fetch(curs); %Este hace un fetch de los datos, se puede usar como filtro 
            tabla = datos.Data; %Aquí le exprimes los datos

            if(length(tabla) > 1)

                % DO THIS PART BETTER
                datesT = cell(length(tabla),1);

                for ii = 1:length(tabla)
                    datesT{ii} = strcat(num2str(tabla{ii,3}),'-',num2str(tabla{ii,2}));
                end
                % DO THIS PART BETTER

                values = [];
                values = cell2mat(tabla(:,1));
                dates = datetime(datesT,'InputFormat','yyyy-MM');
                f = figure
                titleF = strcat('Numero de dias > ',num2str(ppbLimit),' ppm por mes ');
                makePlot( titleF, dates, values)
                folder = strcat('Figures/Contingencia');
                system(strcat('mkdir',' ./', folder)); 
                fileName = strcat(folder,'/numdias_pormes_mayoresa',num2str(ppbLimit)); 
                saveas(f,fileName,'jpg');
                pause(1);
            else
                display(strcat('No data '))
            end
catch err
    display('Closing connection!');
    close(conn)
    rethrow(err)
end

display('Closing connection!');
close(conn)
