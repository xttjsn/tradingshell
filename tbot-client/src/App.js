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
      .then(session_id => {
        this.setState({
          session_id: session_id
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
      host: this.props.host
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
  
  render() {
    let strategyBoard = (<StrategyBoard
                           algocode={this.state.algocode}
                           onCodeChange={this.onCodeChange}
                           setBacktestStartDate={this.setBacktestStartDate}
                           setBacktestEndDate={this.setBacktestEndDate}
                           setInitCapital={this.setInitCapital}
                           backtestStartDate={this.state.backtestStartDate}
                           backtestEndDate={this.state.backtestEndDate}
                           initCapital={this.state.initCapital}/>);
    let performanceBoard = (<PerformanceBoard/>);
    return (
      <Layout left={strategyBoard} right={performanceBoard}/>
     );
  }
}

export default App;
