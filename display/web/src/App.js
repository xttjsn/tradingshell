import React, { Component } from 'react';
import logo from './logo.svg';
import './App.css';
import PerformanceBoard from './PerformanceBoard';
import moment from 'moment';
import api from './API';

// A display for showing the portfolio changes
class App extends Component {

  constructor(props) {
    super(props);

    this.state = {
      host: this.props.host,
      performanceSeries: [],
      logs: [],
    };

  }

  log = (newLog) => {
    this.setState({
      logs: this.state.logs.concat([newLog])
    });
  }

  changeSeries = (newSeries) => {
    // Change to another series.
    // Keep the old series in a map.
  }

  someFunctionToCall = () => {
    if (this.state.backtestWebsocket) {
      this.state.backtestWebsocket.close();
    }
    
      api.runBacktest(this.state.algocode,
                    this.state.mode,
                    this.state.session_id)
      .then(ws => {
        
        this.setState({
          backtestWebsocket: ws
        });
        
        ws.onmessage = this.updatePerformance;
        
        ws.onopen = () => {
          ws.send('READY');
        };

      }); 
  }
   
  updatePerformance = (e) => {
    console.log('receive message ');
    console.log(e.data);
    this.log('recived message');

    try {
      let msg = e.data;
      if (msg == 'end') {
        this.state.backtestWebsocket.send('FINISHED');
        this.state.backtestWebsocket.close();
      }
      else {
        let val = parseInt(msg);

        if (this.state.performanceSeries.length == 0) {
          this.setState({
            performanceSeries: [{
              date: this.state.backtestStartDate.toDate(),
              val: val
            }]
          });
        } else {
          let len = this.state.performanceSeries.length;
          let lastDataPoint = this.state.performanceSeries[len - 1];
          let newDate = new Date(lastDataPoint.date);
          newDate.setDate(newDate.getDate() + 1);
          let newSeries = this.state.performanceSeries.concat([{date: newDate, val: val}]);
          this.setState({
            performanceSeries: newSeries
          });
        }      
    }
    } catch(err) {
      console.error(err);
    }
  };

  render() {
    return (
      <PerformanceBoard
        dataSeries={this.state.performanceSeries}
        logs={this.state.logs}/>
     );
  }
}

export default App;
