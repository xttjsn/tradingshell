import React, { Component } from 'react';
import CodePanel from './CodePanel';
import SearchPanel from './SearchPanel';
import './Panel.css';

class StrategyBoard extends Component {
  render() {
    return (
      <div className={`overlay_container strategy_board`}>
        <CodePanel
          code={this.props.algocode}
          onCodeChange={this.props.onCodeChange}/>
        <SearchPanel/>
      </div>
    );
  }
}

export default StrategyBoard;
