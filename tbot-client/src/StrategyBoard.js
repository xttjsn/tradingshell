import React, { Component } from 'react';
import CodePanel from './CodePanel';
import SearchPanel from './SearchPanel';
import MenuPanel from './MenuPanel';
import './Panel.css';
import api from './API';

class StrategyBoard extends Component {
  render() {

    let loadAlgoCode = (codePanel, algoName) => {
      api.getAlgoCode(algoName, this.props.isTesting ? 'http://localhost:9000' : null)
        .then(res => res.text())
        .then(code => {
          this.props.onCodeChange(code);
        });
    };

    let codePanel = <CodePanel
                      code={this.props.algocode}
                      onCodeChange={this.props.onCodeChange}/>;

    loadAlgoCode = loadAlgoCode.bind(this, codePanel);
    
    return (
      <div className={``}>
        <MenuPanel
          setBacktestStartDate={this.props.setBacktestStartDate}
          setBacktestEndDate={this.props.setBacktestEndDate}
          setInitCapital={this.props.setInitCapital}
          backtestStartDate={this.props.backtestStartDate}
          backtestEndDate={this.props.backtestEndDate}
          initCapital={this.props.initCapital}
          loadAlgoCode={loadAlgoCode}/>
        {codePanel}
      </div>
    );
  }
}

export default StrategyBoard;
