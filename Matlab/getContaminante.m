function [accr name] = getContaminantes(tabla)
    if strcmp(tabla,'cont_pmdoscinco')
        accr = 'PM2.5'
        name = 'Particulas menores a 2.5'
    end
    if strcmp(tabla,'cont_nox')
        accr = 'NOX'
        name = 'Oxidos de nitrogeno'
    end
    if strcmp(tabla,'cont_co')
        accr = 'CO'
        name = 'Monoxido de carbono'
    end
    if strcmp(tabla,'cont_nodos')
        accr = 'NO2'
        name = 'Dioxodo de nitrogeno'
    end
    if strcmp(tabla,'cont_no')
        accr = 'NO'
        name = 'Monoxido de nitrogeno'
    end
    if strcmp(tabla,'cont_otres')
        accr = 'O3'
        name = 'Ozono'
    end
    if strcmp(tabla,'cont_sodos')
        accr = 'SO2'
        name = 'Dioxido de azufre'
    end
    if strcmp(tabla, 'cont_pmdiez')
        accr = 'PM10'
        name = 'Particulas menores a 10'
    end
end
