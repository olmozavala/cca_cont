  //<!--
  (function($){
    $(document).ready(function(){
    	/*initialize with todays date, create charts for every station*/
        var estaciones= ['AJM', 'MGH', 'SFE', 'UAX', 'CUA', 'NEZ', 'CAM','LPR', 'SAG','TAH','ATI','FAC','UIZ','MER','PED','TLA','XAL','BJU'];
    	estaciones.sort();
    	var fecha =  new Date();
    	var mes = fecha.getMonth()+1;
		var dia = fecha.getDate();
		var fecha = fecha.getFullYear() + '-' +
		    ((''+mes).length<2 ? '0' : '') + mes + '-' +
		    ((''+dia).length<2 ? '0' : '') + dia;
    	var contaminante = $('#slct_pollutant option:selected').val();
    	//console.log(fecha, contaminante);    	
    	createCharts(estaciones, contaminante, fecha);    	
    	
        /*datepicker input handler*/
        $( "#datepicker" ).datepicker({
        	onSelect: function(dateStr) {
		      var fecha = $(this).datepicker('getDate');
		      var mes = fecha.getMonth()+1;
			  var dia = fecha.getDate();
			  var fecha = fecha.getFullYear() + '-' +
			      ((''+mes).length<2 ? '0' : '') + mes + '-' +
			      ((''+dia).length<2 ? '0' : '') + dia;
			  var contaminante = $('#slct_pollutant option:selected').val();
	    	  //console.log(fecha, contaminante);    	
	    	  createCharts(estaciones, contaminante, fecha);
		    }
        });
        $("#datepicker").datepicker('setDate', new Date());

        /*select handler on change*/
        $( "#slct_pollutant" ).change(function() {
		  fecha = $("#datepicker").datepicker('getDate');
          var mes = fecha.getMonth()+1;
		  var dia = fecha.getDate();
		  var fecha = fecha.getFullYear() + '-' +
		      ((''+mes).length<2 ? '0' : '') + mes + '-' +
		      ((''+dia).length<2 ? '0' : '') + dia;
		  var contaminante = $('#slct_pollutant option:selected').val();
    	  //console.log(fecha, contaminante);    	
    	  createCharts(estaciones, contaminante, fecha);
		});

    });
  })(jQuery);

  function createCharts(estaciones, contaminante, fecha){

  	$("#all_charts").empty();
  	
  	for( var i=0; i<estaciones.length; i++ ){
      nuevoChart = new PollutantChart(estaciones[i],contaminante,fecha,null);
      nuevoChart.theChart;
   	}

  }
  //-->