function [NewFileName]=ByBBox(filename,LON,LAT,lon,lat,minlat,maxlat,minlon,maxlon)


%Escanea los vectores LAT y LONG hasta encontrar minlon,maxlon,minlat,maxlat y guarda
%sus posiciones correspondientes.

for i=1:lon
    if LON(i) >= minlon  
        lon1=i-1;
        break
    end
end 
    LON1=LON(lon1)
    
    

for i=1:lon
    if LON(i) >= maxlon   
        lon2=i;
        break
    end
end  
   LON2=LON(lon2)
    
for j=1:lat
     if LAT(j) >= minlat
         lat1=j-1;
         break
     end 
end 
    LAT1=LAT(lat1)
    
for j=1:lat
    if LAT(j) >= maxlat  
        lat2=j;
        break
    end
end 
    LAT2=LAT(lat2)
    
    Velocity=filename(lon1:lon2,lat1:lat2);  
    LATITUDE=LAT(lat1:lat2);
    LONGITUDE=LON(lon1:lon2);
    



%  ----------- Normal steps for creating a new NetCDF file
display('---------------------------------');
NewFileName = 'NewFile.nc'; % Name of the file


% 1.- Create the file OPTS: 'CLOBBER' -> overwrite existing files
newf = netcdf.create( NewFileName, 'CLOBBER');

% 2.- Define dimensions
dimlon = netcdf.defDim(newf, 'LONGITUDE', length(LONGITUDE));
dimlat = netcdf.defDim(newf, 'LATITUDE', length(LATITUDE));

% 3.- Create variables ----------------
% 3.1.- Create dimension variables
varlon = netcdf.defVar(newf, 'Longitude', 'float', dimlon);
varlat = netcdf.defVar(newf, 'Latitude', 'float', dimlat);
varu = netcdf.defVar(newf, 'Velocity', 'float', [dimlon dimlat]);

netcdf.endDef(newf);% Important! We are finishing the definition of the file

% 3.2.- Add data into the variables
netcdf.putVar(newf, varlon, LONGITUDE);
netcdf.putVar(newf, varlat, LATITUDE);
netcdf.putVar(newf, varu, Velocity);

% 5.- Close file
netcdf.close(newf);


% Check header of new file
ncdisp(NewFileName);

     
        
