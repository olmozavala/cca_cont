close all;
clear all;
clc;

conn = database('contingencia','argel','contargel',...
        'Vendor','PostgreSQL',...
        'Server','132.248.8.238');

%tables = {'cont_otres','cont_co'};
tables = {'cont_otres'};
%compoundTitle = {'Ozono','Monoxido de carbono'};
compoundTitle = {'Ozono'};
%years = [1986:2016];
years = [2010];

try 

    [est_claves est_names] = getEstaciones(conn);

    for year = years
        year
        for idE = 1:length(est_claves)
        %for idE = 3:3
            for idx = 1:length(tables)
            %for idx = 1:1
                sqlquery = ['SELECT fecha,val FROM',' ', tables{idx},' WHERE ' ...
                        'date_part(' '''year''' ',fecha) = ''',num2str(year),''' ' ...
                        ' AND id_est =''',est_claves(idE,:),''' ' ...
                        ' ORDER BY fecha ' ];
                
                curs = exec(conn,sqlquery); %Este regresa un cursor
                datos = fetch(curs); %Este hace un fetch de los datos, se puede usar como filtro 
                tabla = datos.Data; %Aquí le exprimes los datos

                if(length(tabla) > 1)
                    values = [];
                    values = cell2mat(tabla(:,2));
                    dates = datetime(tabla(:,1),'InputFormat','yyyy-MM-dd HH:mm:ss.0');
                    f = figure
                    titleF = strcat(compoundTitle(idx),' para: ',' ',est_names(idE,:),'-',est_claves(idE,:),' (',num2str(year),')');
                    makePlot( titleF, dates, values)
                    folder = strcat('Figures/',num2str(year));
                    system(strcat('mkdir',' ./', folder)); 
                    fileName = strrep(strcat(folder,'/',compoundTitle(idx),est_claves(idE,:)),' ','_'); 
                    saveas(f,fileName{1},'jpg');
                    pause(1);
                else
                    display(strcat('No data for table: ',est_names(idE,:)))
                end
            end % For tables
        end % For estaciones
    end % for years
catch err
    display('Closing connection!');
    close(conn)
    rethrow(err)
end

display('Closing connection!');
close(conn)
