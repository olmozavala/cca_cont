clear;
clc;

%Se especifican las variables de inter�s. Si es m�s de una agregar
%filename1, filename2, etc. seg�n sea el caso.
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

%Pide ingresar las latitudes y longitudes de inter�s
minlat=input('Introduce la latitud m�nima deseada  :     ');
maxlat=input('Introduce la latitud m�xima deseada  :     ');
minlon=input('Introduce la longitud m�nima deseada  :     ');
maxlon=input('Introduce la longitud m�xima deseada  :     ');


%Regresa la variable (newfile), el vector LONGITUDE y LATITUDE  cortados para el dominio de inter�s 
[NewFileName]=ByBBox(filename,LON,LAT,lon,lat,minlat,maxlat,minlon,maxlon)
%[newfile1,LATITUDE,LONGITUDE]=ByBBox(filename1,LON,LAT,lon,lat,minlat,maxlat,minlon,maxlon)
%[newfile2,LATITUDE,LONGITUDE]=ByBBox(filename2,LON,LAT,lon,lat,minlat,maxlat,minlon,maxlon)
