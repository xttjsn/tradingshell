import React, { Component } from 'react';
import PerformanceChart from './PerformanceChart';
import { getData } from './utils';

class PerformanceBoard extends Component {
  componentDidMount() {
    getData().then(data => {
      this.setState({ data });
    });
  }
  
  render() {
    if (this.state == null) {
      return <div>Loading...</div>;
    }
    
    return (
      <PerformanceChart data={this.state.data} width={500} ratio={0.8}/>
    );
  }
}

export default PerformanceBoard;
