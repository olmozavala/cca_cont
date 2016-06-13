MATLAB and Postgresql
========================

1.- Install jdbc driver for postgresql:

  `apt-get install libpostgresql-jdbc-java`


2.- Save the directory outputted by Matlab when typing `prefdir`. Create file `javaclasspath.txt` in this
directory and add the path of the postgresql driver. In debian the driver should be in `/usr/share/java/postgresql-jdbc4-9.2.jar`.

3.- Restart Matlab

4.- Test matlab:
