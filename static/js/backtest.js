$(function() {
    $("#sel_algo").change(function(){
	$.ajax({
	    type: "POST",
	    url:  "/backtest",
	    data: {
		"algoname" : $("#sel_algo").val()
	    },
	    success: function(data){
		$("#algocode").val($.parseJSON(data)['code']);
	    }
	});
    });


    function getWebSocketURL() {
	var loc = window.location, new_uri;
	if (loc.protocol == "https:") {
	    new_uri = "wss:";
	} else {
	    new_uri = "ws:";
	}
	new_uri += "//" + loc.host:
	new_uri += loc.pathname;
	return new_uri;
    }

    var chartOption = {
	chart: {
	    type : 'line'
	},
	title: {
	    text : 'Performance'
	},
	xAxis: {
	    type: 'datetime',
	    labels: {
		formatter: function() {
		    return Highcharts.dateFormat("%Y-%b-%d", this.value);
		}
	    }
	},
	yAxis: {
	    title: {
		text: 'Portfolio Value'
	    }
	},
	series: [{
	    data: [100000],
	    pointStart: Date.UTC(2010, 1, 1),
	    pointInterval: 24 * 3600 * 1000
	}]
    };

    var myChart = Highcharts.chart('chart', chartOption);

    function addData(chart, data) {
	myChart.series[0].addPoint(data);
    }

    function randFloat(lo, hi) {
	return Math.random() * (hi - lo) + lo;
    }

    function bootstrap() {
	// Populate data
	var startDate = new Date('2012-01-01')
	var endDate = new Date('2012-12-01')

	myChart.series[0].pointStart = startDate;

	var d = startDate;

	function addPoint() {
	    if (d <= endDate) {
		addData(myChart, randFloat(1e6, 2e6));
		d.setDate(d.getDate() + 1);
		myChart.redraw();
	    }
	}

	setInterval(addPoint, 1000);
    }

    $("#btn_submit").click(function() {
	url = getWebSocketURL() + "_ws";
	var bSocket = new WebSocket(url);
	var msg = {
	    type: "cmd:run_backtest",
	    algo : $("#algocode").val(),
	}
	bSocket.send(JSON.stringfy(msg));

	bSocket.onmessage = function(event) {
	    msg = JSON.parse(event.data);
	    pf_value = msg.portfolio_value;
	    date = new Date(msg.date);
	    addData(myChart, pf_value);
	}
    });

});

    
