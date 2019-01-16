import React, { Component } from 'react';
import Chart from './Chart';
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
      <Chart data={this.state.data} width={500} ratio={0.8}/>
    );
  }
}

export default PerformanceBoard;
