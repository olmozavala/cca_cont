/*
* To change this license header, choose License Headers in Project Properties.
* To change this template file, choose Tools | Templates
* and open the template in the editor.
*/
package paquete_service;

import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.text.DateFormat;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.Date;
import java.util.logging.Level;
import java.util.logging.Logger;
import javax.ejb.Stateless;
import javax.ws.rs.core.Context;
import javax.ws.rs.core.UriInfo;
import javax.ws.rs.Produces;
import javax.ws.rs.GET;
import javax.ws.rs.Path;
import javax.ws.rs.PathParam;
import javax.ws.rs.core.MediaType;
import org.postgresql.core.Version;

/**
 * REST Web Service
 *
 * @author ixchel
 */
@Stateless
@Path("contingencia")
public class GenericResource {
	
	@Context
	private UriInfo context;
	
	/**
	 * Creates a new instance of GenericResource
	 */
	public GenericResource() {
	}
	
	/**
	 * Retrieves representation of an instance of paquete_service.GenericResource
	 * @return an instance of java.lang.String
	 */
	@GET
	@Path("/{particula}/{id_est}/{fecha}/{hora}")
	@Produces(MediaType.APPLICATION_JSON)
	public String getContOtres(@PathParam("particula") String particula, @PathParam("id_est") String id_est, @PathParam("fecha") String fecha, @PathParam("hora") String hora) {
		Conection miConection = new Conection("soloread", "SH3<t!4e", "contingencia");
		Connection con = miConection.getConnection();
		
		String sql = "";
		String sql_ = "";
		String sql_check = "";
		Statement sentencia = null;
		ResultSet resultado = null;
		Statement sentencia_check = null;
		ResultSet resultado_check = null;
		Statement sentencia_ = null;
		ResultSet resultado_ = null;
		String jsonResult = "";
		DateFormat formatter ;
		Date datey ;
		formatter = new SimpleDateFormat("yyyy-MM-dd HH");
		
		try {
			// We parse the current date and time and create
			// two dates, one +24 and one -24 from the recuested date.
			datey = formatter.parse(fecha+' '+hora);
			Date date1= addDays(datey,-1);
			Date date2 = addDays(datey,1);
			
			DateFormat df = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
			// Put all the 3 dates as strings.
			String str_date1 = df.format(date1);
			String str_datey = df.format(datey);
			String str_date2 = df.format(date2);
			
			try{
				//*************** Reading data from the stations ***************
				jsonResult += "{ \"report\" :[";
				//sql = "SELECT row_to_json(t) FROM (SELECT fecha,val FROM cont_otres WHERE fecha >='"+str_date1+"' AND fecha < '"+str_datey+"' AND id_est='"+id_est+"') t;";
//				sql = "SELECT fecha,val FROM cont_"+particula+" WHERE fecha >='"+str_date1+"' AND fecha < '"+str_datey+"' AND id_est='"+id_est+"';";
				// In this case we are using the interval function to select the dates
				sql = "SELECT fecha,val FROM cont_"+particula+" WHERE fecha <@ tsrange('"+str_date1+"','"+str_datey+"', '[)') AND id_est='"+id_est+"';";
				sentencia = con.createStatement();
				resultado = sentencia.executeQuery(sql);
				
				while(resultado.next()){
					//jsonResult+="[\""+resultado.getString(1).replace(' ','T')+"Z\","+resultado.getString(2)+"]";
					jsonResult+="[\""+resultado.getString(1)+"\","+resultado.getString(2)+"]";
					if (!resultado.isLast()) {
						// last iteration
						jsonResult+=",";
					}
				}
				
			
				resultado.close();
				sentencia.close();

				//*************** Reading data from the forecast ***************
				jsonResult += "], \"forecast\": [";
				
				//check if forecast exists
				//SELECT to_regclass('public.forecast_otres');
				/*sql_check = "SELECT to_regclass('public.forecast_"+particula+"');";
				sentencia_check = con.createStatement();
				resultado_check = sentencia_check.executeQuery(sql_check);
				while(resultado_check.next()){*/
				//sql_ = "SELECT row_to_json(t) FROM (SELECT fecha,val FROM forecast_otres WHERE fecha >='"+str_date1+"' AND fecha < '"+str_date2+"' AND id_est='"+id_est+"') t;";
//				sql_ = "SELECT fecha,val FROM forecast_"+particula+" WHERE fecha >='"+str_date1+"' AND fecha < '"+str_date2+"' AND id_est='"+id_est+"';";
				sql_ = "SELECT fecha,val FROM forecast_"+particula+" WHERE fecha <@ tsrange('"+str_date1+"','"+str_date2+"', '[)') AND id_est='"+id_est+"';";
				sentencia_ = con.createStatement();
				resultado_ = sentencia_.executeQuery(sql_);
				
				while(resultado_.next()){
					//jsonResult+=resultado_.getString(1);
					//jsonResult+="[\""+resultado_.getString(1).replace(' ','T')+"Z\","+resultado_.getString(2)+"]";
					jsonResult+="[\""+resultado_.getString(1)+"\","+resultado_.getString(2)+"]";
					if (!resultado_.isLast()) {
						// last iteration
						jsonResult+=",";
					}
				}

				jsonResult += "],"; 
				
				resultado.close();
				sentencia.close();
				//*************** Reading station name  ***************

				jsonResult += " \"station\" :";
				sql = "SELECT nombre  FROM cont_estaciones WHERE  id='"+id_est+"';";
				sentencia = con.createStatement();
				resultado = sentencia.executeQuery(sql);
				
				while(resultado.next()){
					jsonResult+= "\""+resultado.getString(1)+"\"";
				}
				
				jsonResult += "}";
				
				resultado_.close();
				sentencia_.close();
				con.close();
			}catch(SQLException ex){
				Logger lgr = Logger.getLogger(Version.class.getName());
				lgr.log(Level.SEVERE, ex.getMessage(), ex);
			}
		} catch (ParseException ex) {
			Logger lgr = Logger.getLogger(GenericResource.class.getName());
			lgr.log(Level.SEVERE, ex.getMessage(), ex);
		}
		
		return jsonResult;
	}
	
	public static Date addDays(Date date, Integer days) {
		Calendar cal = Calendar.getInstance();
		cal.setTime(date);
		cal.add(Calendar.DAY_OF_MONTH, days);
		return cal.getTime();
	}
	
}
