Date.prototype.addDays = function(days) {
       var dat = new Date(this.valueOf())
       dat.setDate(dat.getDate() + days);
       return dat;
}

Date.prototype.addHours= function(h){
    var copiedDate = new Date(this.getTime());
    copiedDate.setHours(copiedDate.getHours()+h);
    return copiedDate;
}

class PollutantChart {
  constructor(est, pollutant, day, ndays) {
    this.est = est;
    this.pollutant = pollutant;
    var date = new Date(day);
    this.day = new Date(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate(), date.getUTCHours(), date.getUTCMinutes(), date.getUTCSeconds());
    //this.day.setHours(0);
    this.ndays = 3;
  }

  /* 
   * This function adds a zero at the beggining in an attemp to format hour and dates 
   * @param {int} i
   */
  addZero(i) {
	if (i < 10) {
	  i = "0" + i;
	}
	return i;
  }

  /**
   * This function creates an array of dates between startDate and stopDate.
   * @param {Date} startDate
   * @param {Date} stopDate
   */
  getDates(startDate, stopDate) {
	var dateArray = new Array();
	var currentDate = startDate;
	while (currentDate <= stopDate) {
	  dateArray.push(currentDate)
	  currentDate = currentDate.addHours(1);
	}
	return dateArray;
  }

  /**
   * This function is used to obtain the correct title for each contaminant 
   * @param {String} shortName
   * @returns {String}
   */
  getContaminantName(shortName){
    var shortNames = ["pmdoscinco", "pmdiez", "nox" , "codos" , "co" , "nodos" , "no" , "otres" , "sodos"];
    var longNames = ["PM2.5", "PM10", "NOX", "CO2", "CO", "NO2", "NO", "O3", "SO2"];
    for(var i=0; i<shortNames.length; i++){
      if(shortNames[i] === shortName){
        return longNames[i];
      }
    }
  }

  /**
   * This function draws the chart, 
   * first it calls the function that calls the webservice
   * and then when the data is retrieve this function calls the one that draws the chart
   */
  get theChart(){
  	this.getData();
  }

  getData(){
  	var date = this.day;
    var n = date.toISOString().slice(0,10);
    var hr = this.addZero(date.getHours())+':'+this.addZero(date.getMinutes());
    var elurl = "http://132.248.8.98:12999/WebServiceContingencia/API/contingencia/"+this.pollutant+"/"+this.est+"/"+n+"/"+hr+"/"+this.ndays;
    var me = this;
    var rdata = null;
    /*call rest web service for data to create highcharts*/
    $.ajax({
      url: elurl,
      async: true,
      crossDomain : true,
      type: "GET",
      dataType: 'json',
      success: function(data) {
        rdata = data;
        console.log(data);
        if(data.report.length != 0){
          var div = document.createElement("div");
          div.className = "one_chart";
          div.id = 'chart_'+this.est;
          document.getElementById("all_charts").appendChild(div);
          me.createChartFvsR(data,div);
        } 
        
      },
      error: function(ex) {
        console.log(ex);
        console.log('NOT!');
      }
    });
  }

  createChartFvsR(data,div){

  	var me = this;

  	var date = this.day;
  	var hr = this.addZero(date.getHours())+':'+this.addZero(date.getMinutes());

    var report = [];
    var forecast = [];

    //Access the result data from
    var reportLength = data.report.length;
    var forecastLength = data.forecast.length;
    var station = data.station;
        
    // Create the range of dates that we can obtain back
    // from the query
    var ellength = data.report.length;
    var forecastlen = data.forecast.length;
        
    var day1=date;
    //day1.setHours(hr.slice(0,2),0,0,0);
    var day2 = (day1).addDays(-me.ndays);
    var eday = (day1).addDays(1);
    var dateArray = me.getDates(day2,eday);

    var fechaRd = null;
    var fechaRdi = null;
                        
    for(var i=0;i<ellength;i++){
      fechaRd = new Date(data.report[i][0]);
      for(var j=0;j<dateArray.length;j++){
        if(fechaRd.getTime()  ===  dateArray[j].getTime()){
          report[j] = data.report[i][1];
        } else if(report[j] != null) {
          //
        } else {
          report[j] = null;
        }
      }
    }
                        
    for(var i=0;i<forecastlen;i++){
      fechaRdi = new Date(data.forecast[i][0]);
      for(var j=0;j<dateArray.length;j++){
        if(fechaRdi.getTime() === dateArray[j].getTime() ){
          if(data.forecast[i][1] != -1){ forecast[j] = data.forecast[i][1]; }
        } else if(forecast[j] != null) {
           //
        } else {
          forecast[j] = null;
        }
      }
    }

    if(forecast.length == 0){
      forecast = [null];
    }
    
    //Create the chart
    Highcharts.chart({
      chart: {
        renderTo: div
      },
      title: {
        text: 'Estación VS Pronóstico, ' +station
      },
      subtitle: {
        text: 'Contaminante '+me.getContaminantName(this.pollutant)
      },
      xAxis: {
        categories: dateArray,
        labels: {
          formatter: function () {
            return this.value.getDate()+'/'+me.addZero(this.value.getMonth()+1)+'/'+this.value.getFullYear()+' '+this.value.getHours()+":00";
          }
        },
        title: {
          text: 'Fecha'
        }
      },
      yAxis: [
        { // Primary yAxis
          labels: {
            //format: '{value}°C',
          },
          title: {
            text: 'Concentración del contaminante'
          },
          min: 0,
          max: Math.max(Math.max.apply(NaN,forecast), Math.max.apply(NaN,report)),
          /*plotBands: [{ // pollutant contingency adviced
                from: 160,
                to: 200,
                color: 'rgba(229, 0, 0, 0.1)',
                label: {
                  text: 'Contingencia',
                  style: {
                    color: '#606060'
                  }
                }
          }]*/
        }
      ],
      tooltip: {
        shared: true
        //pointFormat: "{point.y:.2f} "
      },
      series: [
        {
          name: 'Estación',
          type: 'spline',
          data: report,
          dashStyle: 'shortdot'
        },{
          name: 'Pronóstico',
          type: 'spline',
          data: forecast
        }
      ]
    });	/*end of highcharts definition*/			      
  }
}