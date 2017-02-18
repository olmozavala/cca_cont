clear
clc
festivos=csvread('dias_festivos.csv');
%festivos=num2str(festivos);
festivos=reshape(festivos,7686,1);
festivos=num2str(festivos);
festivos(find(isnan(festivos))) = [];
cal=ones(366,21);
year=1995;
for i=1:366;
  for j=1:21;
        cal(i,j)=i+datenum(year,12,31);
        year=year+1;
        
        if j==21;
            year=1995;
        end
            
  end
end
cal=reshape(cal,7686,1);
calendario=datestr(cal,'dd/mmm/yyyy');

strcat(calendario(:,:),':  ',festivos);


