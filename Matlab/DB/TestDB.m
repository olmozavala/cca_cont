close all;
clear all;
clc;

javaaddpath('/usr/share/java/postgresql-jdbc4-9.2.jar');

conn = database('contingencia','argel','XXXXX',...
        'Vendor','PostgreSQL',...
        'Server','132.248.8.238');

sqlquery = 'SELECT * FROM cont_estaciones';

curs = exec(conn,sqlquery); %Este regresa un cursor
datos = fetch(curs); %Este regresa otro cursor pero ya trae los datos
tabla = datos.Data %Aquí le exprimes los datos

close(conn)
