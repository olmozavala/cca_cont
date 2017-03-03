close all;
clear all;
clc;

if(isunix)
    addpath('./lib/')
    addpath('./AllPrograms/')
    javaaddpath('/usr/share/java/postgresql-jdbc4-9.2.jar');
elseif(ispc)
    addpath('.\lib')
  kk  addpath('.\AllPrograms')
    javaaddpath('.\DB\JDBCDriver\postgresql-9.4.1211.jre7');
    end

    conn = database('contingencia','soloread','SH3<t!4e',...
            'Vendor','PostgreSQL',...
            'Server','132.248.8.238')

    mycolors = 'rgbcmyk';

    tablas = getTablas();
    [claves allest] = getEstaciones(conn);
    ppmVal = '166';

try

    tabla = 'cont_otres'
    from = 2010
    to = 2013
    for idx = 1:length(claves)
        display(claves(idx,:))
        GetContaminantByTimeRange(tabla,from,to,claves(idx,:),conn)
    end
catch err
        display('Closing connection!');
        close(conn)
    rethrow(err)
end

display('Closing connection!');
close(conn)

