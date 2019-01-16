import React, { Component } from 'react';
import logo from './logo.svg';
import './App.css';
import Layout from './Layout';
import StrategyBoard from './StrategyBoard';

class App extends Component {
  constructor(props) {
    super(props);

    this.state = {
      algocode: "import asyncio\nprint('Hello')"
    };
  }

  onCodeChange = (newCode) => {
    this.setState({
      algocode: newCode
    });
  }
  
  render() {
    var strategyBoard = (<StrategyBoard
                           algocode={this.state.algocode}
                           onCodeChange={this.onCodeChange}/>);
    return (
      <Layout left={strategyBoard} right="World!"/>
     );
  }
}

export default App;
