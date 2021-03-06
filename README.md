MATLAB and Postgresql
========================

Install in Linux (Ubuntu)
---------------------------
0.- Install java. The java version depends on your version of the jdb driver, if you are up to date it should work with java 8:

  `apt-get install openjdk-7-jdk`

1.- Install jdbc driver for postgresql:

  `apt-get install libpostgresql-jdbc-java`

2.- Save the directory outputted by Matlab when typing `prefdir`. Create file `javaclasspath.txt` in this
directory and add the path of the postgresql driver. In debian the driver should be in `/usr/share/java/postgresql-jdbc4-9.2.jar`.

3.- Restart Matlab

4.- Test the connection to the database with matlab:
  ~~~~
   javaaddpath('/usr/share/java/postgresql-jdbc4-9.2.jar');

   conn = database('contingencia','soloread','SH3<t!4e',...
                  'Vendor','PostgreSQL','Server','132.248.8.238')
  ~~~~

Install in Windows (Ubuntu)
---------------------------
1.- Dowload and install Java JDK. First check which version of Java does your Matlab uses with `java -version`.
 For version JDK 7. Download from [Oracle](http://www.oracle.com/technetwork/java/javase/downloads/jdk7-downloads-1880260.html)

2.- Download jdbc driver for postgresql from here [link](https://jdbc.postgresql.org/) (please select the one that corresponds
to your Java version, if you are using Java 7 then it should be JDBC41).

3.- Test the connection to the database with matlab:
  ~~~~
   javaaddpath('.\DB\JDBCDriver\postgresql-9.4.1211.jre7.jar');

   conn = database('contingencia','soloread','SH3<t!4e',...
                  'Vendor','PostgreSQL','Server','132.248.8.238')
  ~~~~
