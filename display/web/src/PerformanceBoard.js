import React, { Component } from 'react';
import { Container, Row, Col } from 'reactstrap';
import PerformanceChart from './PerformanceChart';
import LoggingPanel from './LoggingPanel';
import { getData } from './utils';

class PerformanceBoard extends Component {
  
  render() {
    if (this.props.dataSeries == null || this.props.dataSeries.length < 2) {
      return <div>Waiting for data..</div>;
    }
    
    return (
      <Container>
        <Row>
          <PerformanceChart
            data={this.props.dataSeries}
            width={500}
            ratio={0.8}
            title={this.props.title}
            xlabel={this.props.xlabel}
          />          
        </Row>
        <Row>
          <LoggingPanel logs={this.props.logs}/>
        </Row>
      </Container>

    );
  }
}

export default PerformanceBoard;
