clear all
close all
load /home2/Dropbox/Articulos/Contingencia/MAT_72est_historicos/O3_1986-2016.mat

Nuevas_estaciones = { ...
    'ACO','ARA','ATI','AZC','BJU','CAM','CES','CFE','CHA','CHO', ...
    'COR','COY','CUA','CUI','DIC','EAC','EAJ','EDL','FAC','FAN', ...
    'HAN','IBM','IMP','INE','IZT','LAA','LAG','LLA','LOM','LPR', ...
    'LVI','MCM','MER','MIN','MON','MPA','NET','NEZ','NTS','PAR', ...
    'PED','PLA','POT','SAG','SHA','SJA','SNT','SUR','TAC','TAH', ...
    'TAX','TEC','TLA','TLI','TPN','UIZ','VAL','VIF','VIR','XAL', ...
    'XCH','PER','HGM','SFE','AJM','MGH','INN','CUT','UAX','AJU',...
    'CCA','GAM'};

Dat = datevec(FechasGrande);
% T = 24*60*60*datenum(Dat(:,1),Dat(:,2),Dat(:,3),Dat(:,4),Dat(:,5),Dat(:,6));
FechasGrande2 = datenum(Dat(:,1),Dat(:,2),Dat(:,3),Dat(:,4),Dat(:,5),Dat(:,6));

plot(FechasGrande2,MedicionesGrande(:,32)) %%Estacion MER

Anual = (2*pi)/365;
Semianual = (2*pi)/(365/2);
Semanal = (2*pi)/7;
Semisemanal = (2*pi)/(7/2);
Diaria = (2*pi)/(1);
Semidiurna = (2*pi)/(1/2);

I = find(isnan(MedicionesGrande(:,32))==0);


% H = [I./I, sin(Anual*FechasGrande2(I)), cos(Anual*FechasGrande2(I)) ];
% H = [I./I, sin(Anual*FechasGrande2(I)), cos(Anual*FechasGrande2(I)) , ...
%        sin(Semanal*FechasGrande2(I)), cos(Semanal*FechasGrande2(I))];
H = [I./I, sin(Anual*FechasGrande2(I)), cos(Anual*FechasGrande2(I)) , ...
       sin(Semianual*FechasGrande2(I)), cos(Semianual*FechasGrande2(I)) , ...
       sin(Semanal*FechasGrande2(I)), cos(Semanal*FechasGrande2(I)), ...
       sin(Semisemanal*FechasGrande2(I)), cos(Semisemanal*FechasGrande2(I)), ...
       sin(Diaria*FechasGrande2(I)), cos(Diaria*FechasGrande2(I)),...
       sin(Semidiurna*FechasGrande2(I)), cos(Semidiurna*FechasGrande2(I))];

% calcula las componentes

A = inv(H'*H)*H'*MedicionesGrande(I,32);
%Ozono32 = A(1) + A(2)*sin(Anual*FechasGrande2) + A(3)*cos(Anual*FechasGrande2) ;
%  Ozono32 = A(1) + A(2)*sin(Anual*FechasGrande2) + A(3)*cos(Anual*FechasGrande2)...
%      + A(4)*sin(Semanal*FechasGrande2) + A(5)*cos(Semanal*FechasGrande2);

 Ozono32 = A(1) + A(2)*sin(Anual*FechasGrande2) + A(3)*cos(Anual*FechasGrande2)...
                 + A(4)*sin(Semianual*FechasGrande2) + A(5)*cos(Semianual*FechasGrande2)...
                 + A(6)*sin(Semanal*FechasGrande2) + A(7)*cos(Semanal*FechasGrande2)...
                 + A(8)*sin(Semisemanal*FechasGrande2) + A(9)*cos(Semisemanal*FechasGrande2)...
                 + A(10)*sin(Diaria*FechasGrande2) + A(11)*cos(Diaria*FechasGrande2)...
                 + A(12)*sin(Semidiurna*FechasGrande2) + A(13)*cos(Semidiurna*FechasGrande2);
hold on
plot (FechasGrande2, Ozono32,'r'); 


Err = MedicionesGrande(:,32)-Ozono32;
figure()
plot(FechasGrande2, Err,'m'); 





%% Extraccion de datos de ECAIM salidas wrf 




