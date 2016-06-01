close all;
clear all;
clc;

conn = database('contingencia','argel','contargel',...
        'Vendor','PostgreSQL',...
        'Server','132.248.8.238');

tables = {'cont_co'};
compoundTitle = {'Monoxido de carbono'};

try 

    folder = strcat('Figures/AllYears');
    [est_claves est_names] = getEstaciones(conn);

        for idE = 1:length(est_claves)
        %for idE = 3:3
            for idx = 1:length(tables)
            %for idx = 1:1
                sqlquery = ['SELECT avg(val) as pro, date_part(''month'',fecha) as mes, date_part(''year'',fecha) as anio' ...
                        ' FROM',' ', tables{idx},' WHERE ' ...
                        ' id_est =''',est_claves(idE,:),''' ' ...
                        ' GROUP BY mes, anio' ... 
                        ' ORDER BY anio ASC, mes ASC'];
                
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
                    values = cell2mat(tabla(:,2));
                    dates = datetime(datesT,'InputFormat','yyyy-MM');
                    f = figure
                    titleF = strcat(compoundTitle(idx),' para: ',' ',est_names(idE,:),'-',est_claves(idE,:));
                    makePlot( titleF, dates, values)
                    system(strcat('mkdir',' ./', folder)); 
                    fileName = strrep(strcat(folder,'/',compoundTitle(idx),est_claves(idE,:)),' ','_'); 
                    saveas(f,fileName{1},'jpg');
                    pause(1);
                else
                    display(strcat('No data for table: ',est_names(idE,:)))
                end
            end % For tables
        end % For estaciones

catch err
    display('Closing connection!');
    close(conn)
    rethrow(err)
end

display('Closing connection!');
close(conn)
