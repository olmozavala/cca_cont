# coding=utf-8
import sys, string
__author__="Olmo S. Zavala Romero"

import subprocess

def downloadData():
    "Downloads all the meteorological data for the years 1986 to 2016"
    for y in range(1986,2017):
        url = "wget http://148.243.232.112:8080/opendata/anuales_horarios_gz/meteorología_%s.csv.gz --directory-prefix=data"%(y)
        print(url)
        #subprocess.call(url,shell=True)

    url = "wget http://148.243.232.112:8080/opendata/catalogos/cat_parametros.csv --directory-prefix=data"
    print(url)
    subprocess.call(url,shell=True)

    url = "wget http://148.243.232.112:8080/opendata/catalogos/cat_unidades.csv --directory-prefix=data"
    print(url)
    subprocess.call(url,shell=True)

if __name__ == "__main__":
    downloadData()

