import React, { Component } from 'react';
import { Container, Row, Col } from 'reactstrap';
import 'bootstrap/dist/css/bootstrap.min.css';

class Layout extends Component {
  render() {
    return (
      <Container>
	<Row>
          <Col>{this.props.left}</Col>
          <Col>{this.props.right}</Col>
        </Row>
      </Container>
    );
  }
}

export default Layout;
