import React, { Component } from 'react';
import logo from './logo.svg';
import './App.css';
import Layout from './Layout';
import StrategyBoard from './StrategyBoard';
import PerformanceBoard from './PerformanceBoard';
import moment from 'moment';

class App extends Component {
  constructor(props) {
    super(props);

    this.state = {
      algocode: "import asyncio\nprint('Hello')",
      backtestStartDate: moment('2012-01-01'),
      backtestEndDate: moment('2018-01-01'),
      initCapital: 100000
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
                           backtestStartDate={this.state.backtestStartDate}
                           backtestEndDate={this.state.backtestEndDate}
                           setInitCapital={this.setInitCapital}
                           initCapital={this.state.initCapital}/>);
    let performanceBoard = (<PerformanceBoard/>);
    return (
      <Layout left={strategyBoard} right={performanceBoard}/>
     );
  }
}

export default App;
