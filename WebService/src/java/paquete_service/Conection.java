/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package paquete_service;

import java.sql.Connection;
import java.sql.DriverManager;

/**
 *
 * @author ixchel
 */
public class Conection {
    
    private String driver, url, base_datos, usuario, password;
    
    public Conection(String u, String p, String bd){
        this.driver = "org.postgresql.Driver";
        this.base_datos = bd;
        this.usuario = u;
        this.password = p;
        this.url = "jdbc:postgresql://132.248.8.238:5432/"+base_datos+"?user="+usuario+"&password="+password;
    }
    
    public Connection getConnection(){
        Connection con = null;
        try{
            Class.forName(driver);
            con = DriverManager.getConnection(url);
        }catch(Exception e){
            e.getMessage();
        }
        return con;
    } 
}
