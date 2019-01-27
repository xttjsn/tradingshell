import React, { Component } from 'react';
import { Form, FormGroup, Input } from 'reactstrap';

class LoggingPanel extends Component {
  render() {
    return (
      <Form>
        <FormGroup>
          <Input
            type='textarea'
            readOnly
            name='logArea'
            id='logArea'
            disabled={true}
            style={{ width: '500px', height: '300px'}}
            value={this.props.logs.join('\n')}
          />
        </FormGroup>
      </Form>
    );
  }
}

export default LoggingPanel;
