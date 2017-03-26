clear;
clc;

%Se especifican las variables de interés. Si es más de una agregar
%filename1, filename2, etc. según sea el caso.
filename=ncread('NewFile.nc','velocity');
%filename1=ncread('NewFile.nc','variable1');
%filename2=ncread('NewFile.nc','variable2');

%Guarda las variables Longitude y Latitude del archivo NetCDF en LON y LAT
%respectivamente.
LON=ncread('NewFile.nc','Longitude');
LAT=ncread('NewFile.nc','Latitude');

lon=length(LON);
lat=length(LAT);

%Calcula min y max de LON y LAT
minLON=min(LON);
maxLON=max(LON);
minLAT=min(LAT);
maxLAT=max(LAT);

fprintf('El siguiente es el intervalo de latitudes disponible \n');
            minLAT,maxLAT
            
fprintf('El siguiente es el intervalo de longitudes disponible \n');
            minLON,maxLON

%Pide ingresar las latitudes y longitudes de interés
minlat=input('Introduce la latitud mínima deseada  :     ');
maxlat=input('Introduce la latitud máxima deseada  :     ');
minlon=input('Introduce la longitud mínima deseada  :     ');
maxlon=input('Introduce la longitud máxima deseada  :     ');


%Regresa la variable (newfile), el vector LONGITUDE y LATITUDE  cortados para el dominio de interés 
[NewFileName]=ByBBox(filename,LON,LAT,lon,lat,minlat,maxlat,minlon,maxlon)
%[newfile1,LATITUDE,LONGITUDE]=ByBBox(filename1,LON,LAT,lon,lat,minlat,maxlat,minlon,maxlon)
%[newfile2,LATITUDE,LONGITUDE]=ByBBox(filename2,LON,LAT,lon,lat,minlat,maxlat,minlon,maxlon)
