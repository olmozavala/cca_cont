MATLAB and Postgresql
========================

0.- Install java. The java version depends on your version of the jdb driver, if you are up to date it should work with java 8:

  `apt-get install penjdk-8-jdk`

1.- Install jdbc driver for postgresql:

  `apt-get install libpostgresql-jdbc-java`


2.- Save the directory outputted by Matlab when typing `prefdir`. Create file `javaclasspath.txt` in this
directory and add the path of the postgresql driver. In debian the driver should be in `/usr/share/java/postgresql-jdbc4-9.2.jar`.

3.- Restart Matlab

4.- Test the connection to the database with matlab:

   conn = database('contingencia','soloread','SH3<t!4e',...
                  'Vendor','PostgreSQL','Server','132.248.8.238')
