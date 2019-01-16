import React, { Component } from 'react';
import CodePanel from './CodePanel';
import SearchPanel from './SearchPanel';
import MenuPanel from './MenuPanel';
import './Panel.css';

class StrategyBoard extends Component {
  render() {
    return (
      <div className={``}>
        <MenuPanel
          setBacktestStartDate={this.props.setBacktestStartDate}
          setBacktestEndDate={this.props.setBacktestEndDate}
          backtestStartDate={this.props.backtestStartDate}
          backtestEndDate={this.props.backtestEndDate}
          setInitCapital={this.props.setInitCapital}
          initCapital={this.props.initCapital}/>
        <CodePanel
          code={this.props.algocode}
          onCodeChange={this.props.onCodeChange}/>
      </div>
    );
  }
}

export default StrategyBoard;
