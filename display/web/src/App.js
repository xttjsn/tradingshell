import React, { Component } from 'react';
import logo from './logo.svg';
import './App.css';
import PerformanceBoard from './PerformanceBoard';
import moment from 'moment';
import api from './API';

// A display for showing the portfolio changes
class App extends Component {

  componentDidMount() {
    this.connect();
  }

  constructor(props) {
    super(props);

    this.state = {
      host: this.props.host,
      performanceSeries: [],
      logs: [],
      title: "Performance Series"
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

  connect = () => {
    if (this.state.backtestWebsocket) {
      this.state.backtestWebsocket.close();
    }
    
    api.getPlotWebsocket() 
      .then(ws => {        
        this.setState({
          backtestWebsocket: ws
        });
        ws.onmessage = this.updatePerformance;
      }); 
  }
   
  updatePerformance = (e) => {
    console.log('receive message ');
    console.log(e.data);
    this.log('recived message');

    try {
      let msg = JSON.parse(e.data);

      switch (msg.type) {
      case 'Init':
        // Set up the plot with parameters
        let title = msg.title;
        let xlabel = msg.xlable;
        let lastDate = new Date(msg.startDate);
        lastDate.setDate(lastDate.getDate() - 1);
        this.setState({
          lastDate: lastDate,
          title: title,
          xlabel: xlabel
        });

        break;
      case 'Update':
        // Update the plot with a new data point
        let portfolioValue = parseFloat(msg.portfolioValue);
        let pnl = parseFloat(msg.pnl);
        let returnVal = parseFloat(msg.return);

        let nextDate = new Date(this.state.lastDate);
        nextDate.setDate(nextDate.getDate() + 1);
        let newSeries = this.state.performanceSeries.concat([{date: nextDate,
                                                              portfolioValue: portfolioValue,
                                                              pnl: pnl,
                                                              return: returnVal
                                                              }]);
        this.setState({
          performanceSeries: newSeries,
          lastDate: nextDate
        });
        
        break;
      case 'End':
        // The server says no more data, we close the websocket
        this.state.backtestWebsocket.close();
        break;
      }
    } catch(err) {
      console.error(err);
    }
  };

  render() {
    if (this.state.performanceSeries.length > 10) {
      return (
        <PerformanceBoard
        dataSeries={this.state.performanceSeries}
        logs={this.state.logs}
        title={this.state.title}
        xlabel={this.state.xlabel}/>
     );
    } else {
      return ("Waiting for data...");
    }
  }
}

export default App;
