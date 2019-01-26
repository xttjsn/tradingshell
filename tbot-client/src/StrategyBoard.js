import React, { Component } from 'react';
import CodePanel from './CodePanel';
import SearchPanel from './SearchPanel';
import api from './API';
import { Button, Form, FormGroup, Label, Input, FormText } from 'reactstrap';
import PropTypes from 'prop-types';
import moment from 'moment';
import './Panel.css';


class StrategyBoard extends Component {
  static propTypes = {
    backtestStartDate: PropTypes.object,
    backtestStartDate: PropTypes.object
  }
  
  render() {

    return (
      <div className={``}>
        <Form>
          <FormGroup>
            <Label for='strategySelect'>Strategy</Label>
            <Input type='select' name='strategySelect' id='strategySelect'
                   onChange={(e) => this.props.changeStrategy(e.target.value)}
                   value={this.props.selectedStrategy}>
              <option value='SMA'>SMA</option>
              <option value='__TEST_FACTORIAL'>__TEST_FACTORIAL</option>
            </Input>
          </FormGroup>
          <FormGroup>
            <Label for='initDate'>Initial Date</Label>
            <Input type='date' name='initDate' id='initDate'
                   defaultValue={this.props.backtestStartDate.format('YYYY-MM-DD')}
                   onChange={(e) => this.props.setBacktestStartDate(moment(e.target.value))}/>
          </FormGroup>
          <FormGroup>
            <Label for='endDate'>End Date</Label>
            <Input type='date' name='endDate' id='endDate'
                   value={this.props.backtestEndDate.format('YYYY-MM-DD')}
                   onChange={(e) => this.props.setBacktestEndDate(moment(e.target.value))}/>
          </FormGroup>
          <FormGroup>
            <Label for='mode'>Backtest Mode</Label>
            <Input type='select' name='mode' id='modeSelect'
                   onChange={(e) => this.props.setMode(e.target.value)}
                   value={this.props.mode}>
              <option>GENERATOR</option>
              <option>Zipline</option>
            </Input>
          </FormGroup>
        </Form>
        <CodePanel
          code={this.props.algocode}
          onCodeChange={this.props.onCodeChange}/>
      </div>
    );
  }
}

export default StrategyBoard;
