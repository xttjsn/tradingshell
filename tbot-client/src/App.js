import React, { Component } from 'react';
import logo from './logo.svg';
import './App.css';
import Layout from './Layout';
import StrategyBoard from './StrategyBoard';
import PerformanceBoard from './PerformanceBoard';
import moment from 'moment';
import api from './API';

class App extends Component {

  componentDidMount() {
    api.newSession(this.props.host)
      .then(res => res.text())
      .then(session_id => {
        this.setState({
          session_id: session_id
        });
      });

    api.getAllAlgo()
      .then(names => {
        this.setState({
          algoNames: names
        });
      });
  }
  
  constructor(props) {
    super(props);

    this.state = {
      algocode: "import asyncio\nprint('Hello')",
      backtestStartDate: moment('2012-01-01'),
      backtestEndDate: moment('2018-01-01'),
      initCapital: 100000,
      host: this.props.host,
      selectedStrategy: 'SMA',
      mode: 'GENERATOR_MODE',
      performanceSeries: [],
      logs: [],
      algoNames: []
    };

  }

  onCodeChange = (newCode) => {
    this.setState({
      algocode: newCode
    });
  }

  setBacktestStartDate = (newDate) => {
    this.setState({
      backtestStartDate: newDate
    });
  }

  setBacktestEndDate = (newDate) => {
    this.setState({
      backtestEndDate: newDate
    });
  }

  setInitCapital = (newCapital) => {
    this.setState({
      initCapital: newCapital
    });
  }

  changeStrategy = (algoName) => {
    this.setState({
      selectedStrategy: algoName
    });

    api.getAlgoCode(algoName)
      .then(res => res.text())
      .then(code => {
        this.onCodeChange(code);
      });
  }

  setMode = (newMode) => {
    this.setState({
      mode: newMode
    });
  }

  log = (newLog) => {
    this.setState({
      logs: this.state.logs.concat([newLog])
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

  runBacktest = (e) => {
    e.preventDefault();

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
  };
  
  render() {
    let strategyBoard = (<StrategyBoard
                           algocode={this.state.algocode}
                           onCodeChange={this.onCodeChange}
                           setBacktestStartDate={this.setBacktestStartDate}
                           setBacktestEndDate={this.setBacktestEndDate}
                           setInitCapital={this.setInitCapital}
                           backtestStartDate={this.state.backtestStartDate}
                           backtestEndDate={this.state.backtestEndDate}
                           initCapital={this.state.initCapital}
                           changeStrategy={this.changeStrategy}
                           selectedStrategy={this.state.selectedStrategy}
                           runBacktest={this.runBacktest}
                           setMode={this.setMode}
                           mode={this.state.mode}
                           algoNames={this.state.algoNames}
                         />);
    let performanceBoard = (<PerformanceBoard
                              dataSeries={this.state.performanceSeries}
                              logs={this.state.logs}/>);
    return (
      <Layout left={strategyBoard} right={performanceBoard}/>
     );
  }
}

export default App;
