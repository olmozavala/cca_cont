function makePlot( ptitle, pX, pY)
    plot(pX,pY,'r') 
    datetick('x','dd/mm/yyyy','keeplimits','keepticks')
    title(ptitle)
