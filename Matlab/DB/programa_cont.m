clear;
clc;

festivos=csvread('dias_festivos.csv');
festivos(find(isnan(festivos))) = [];           %Elimina todos los valores NaN del arreglo "festivos".

[f,c]=size(festivos');                          %Regresa en f el no. de filas y en c el no. de columnas de "festivos".
F=f*c;

festivos=reshape(festivos,F,1);                 %Transforma la matriz fxc en un vector con f*c elementos.
festivos=num2str(festivos);                     %Convierte el arreglo númerico "festivos" en un arreglo de caracter y lo sobreescribre.


%Para generar las fechas de interés
cal=ones(F,1);
year=1995;                                      %Un año menos del de interés.

for i=1:f;
  for j=1:c;
        cal(i,j)=i+datenum(year,12,31);         %Convierte las fechas a partir del 1/ene/1996 hasta el 31/dic/2016 en valores numéricos.       
  end
end

calendario=datestr(cal,'dd/mmm/yyyy');          %Calcula para cada valor obtenido por "datenum" la fecha correspondiente.
tabla=strcat(calendario(:,:),':  ',festivos)    %Concatena el arreglo "calendario" con el arreglo "festivos".

