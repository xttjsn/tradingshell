import React, { Component } from 'react';
import CodePanel from './CodePanel';
import SearchPanel from './SearchPanel';
import MenuPanel from './MenuPanel';
import './Panel.css';
import api from './API';

class StrategyBoard extends Component {
  render() {

    let codePanel = <CodePanel
                      code={this.props.algocode}
                      onCodeChange={this.props.onCodeChange}/>;
    
    return (
      <div className={``}>
        <MenuPanel
          setBacktestStartDate={this.props.setBacktestStartDate}
          setBacktestEndDate={this.props.setBacktestEndDate}
          setInitCapital={this.props.setInitCapital}
          backtestStartDate={this.props.backtestStartDate}
          backtestEndDate={this.props.backtestEndDate}
          initCapital={this.props.initCapital}
          changeStrategy={this.props.changeStrategy}
          selectedStrategy={this.props.selectedStrategy}/>
        {codePanel}
      </div>
    );
  }
}

export default StrategyBoard;
