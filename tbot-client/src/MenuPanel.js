import React, { Component } from 'react';
import { ButtonDropdown, DropdownToggle, DropdownMenu, DropdownItem, ButtonGroup } from 'reactstrap';
import { Button, Form, FormGroup, Label, Input, FormText } from 'reactstrap';
import Calendar from 'rc-calendar';
import Modal from 'react-modal';
import PropTypes from 'prop-types';
import './Panel.css';

import 'rc-calendar/assets/index.css';

class MenuPanel extends Component {
  static propTypes = {
    backtestStartDate: PropTypes.object,
    backtestEndDate: PropTypes.object
  }
  
  constructor(props) {
    super(props);

    this.state = {
    };
  }
  
  render() {
    
    var form = <Form>
                 <FormGroup>
                   <Label for='strategySelect'>Strategy</Label>
                   <Input type='select' name='strategySelect' id='strategySelect' onChange={(e) => this.props.changeStrategy(e.target.value)} value={this.props.selectedStrategy}>
                     <option value='SMA'>SMA</option>
                     <option value='__TEST_FACTORIAL'>__TEST_FACTORIAL</option>
                   </Input>
                 </FormGroup>
                 <FormGroup>
                   <Label for='initDate'>Initial Date</Label>
                   <Input type='date' name='initDate' id='initDate' defaultValue={this.props.backtestStartDate.format('YYYY-MM-DD')}/>
                 </FormGroup>
                 <FormGroup>
                   <Label for='endDate'>End Date</Label>
                   <Input type='date' name='endDate' id='endDate' value={this.props.backtestEndDate.format('YYYY-MM-DD')}/>
                 </FormGroup>
                 <FormGroup>
                   <Label for='mode'>Backtest Mode</Label>
                   <Input type='select' name='mode' id='modeSelect'>
                     <option>GENERATOR</option>
                     <option>Zipline</option>
                   </Input>
                 </FormGroup>
               </Form>;
    
    return form;
  }
}

export default MenuPanel;
