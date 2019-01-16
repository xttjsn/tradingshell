import React, { Component } from 'react';
import { Container, Row, Col } from 'reactstrap';
import PerformanceChart from './PerformanceChart';
import LoggingPanel from './LoggingPanel';
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
      <Container>
        <Row>
          <PerformanceChart data={this.state.data} width={500} ratio={0.8}/>          
        </Row>
        <Row>
          <LoggingPanel/>
        </Row>
      </Container>

    );
  }
}

export default PerformanceBoard;
