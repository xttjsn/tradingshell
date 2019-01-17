import React, { Component } from 'react';
import { ButtonDropdown, DropdownToggle, DropdownMenu, DropdownItem, ButtonGroup } from 'reactstrap';
import { Button, Form, FormGroup, Label, Input, FormText } from 'reactstrap';
import Calendar from 'rc-calendar';
import Modal from 'react-modal';
import PropTypes from 'prop-types';
import './Panel.css';

import 'rc-calendar/assets/index.css';

const modalStyle = {
  content: {
    top                   : '50%',
    left                  : '50%',
    right                 : 'auto',
    bottom                : 'auto',
    marginRight           : '-50%',
    transform             : 'translate(-50%, -50%)'
  }
};

class MenuPanel extends Component {
  static propTypes = {
    backtestStartDate: PropTypes.object,
    backtestEndDate: PropTypes.object
  }
  
  constructor(props) {
    super(props);

    this.state = {
      strategiesDropdownOpen: false,
      backtestDropdownOpen: false,
      modalOpen: false,
    };
  }

  strategiesDropdownToggle = () => {
    this.setState({
      strategiesDropdownOpen: !this.state.strategiesDropdownOpen
    });
  }

  backtestDropdownToggle = () => {
    this.setState({
      backtestDropdownOpen: !this.state.backtestDropdownOpen
    });
  }

  startDateOnClick = () => {
    this.setState({
      modalOpen: true,
      calendarOpen: true,
      calendarValue: this.props.backtestStartDate,
      calendarOnChange: (newDate) => {
        this.props.setBacktestStartDate(newDate);
      }
    });
  }

  endDateOnClick = () => {
    this.setState({
      modalOpen: true,
      calendarOpen: true,
      calendarValue: this.props.backtestEndDate,
      calendarOnChange: (newDate) => {
        this.props.setBacktestEndDate(newDate);
      }
    });
  }

  initCapOnClick = () => {
    this.setState({
      modalOpen: true,
      capitalFormOpen: true
    });
  }

  dismissModal = () => {
    this.setState({
      modalOpen: false,
      calendarOpen: false,
      capitalFormOpen: false
    });
  }
  
  render() {
    
    let modalContent;
    if (this.state.calendarOpen) {
      modalContent = <div className="text-align-center">
                       <Calendar
                         defaultValue={this.state.calendarValue}
                         onChange={this.state.calendarOnChange}/>
                       <Button className="margined"
                               color='secondary'
                               onClick={this.dismissModal}>Confirm</Button>
                     </div>;
    }
    else if (this.state.capitalFormOpen) {
      modalContent = <Form>
                       <FormGroup className="text-align-center">
                         <Label >Initial Capital</Label>
                         <Input type="number"
                                name="initCap"
                                id="initCap"
                                placeholder="100,000"
                                onChange={this.props.setInitCapital}
                                value={this.props.initCapital}/>
                         <Button className="margined"
                                 color='secondary'
                                 onClick={this.dismissModal}>Confirm</Button>
                       </FormGroup>
                     </Form>;
    }
    
    return (
      <ButtonGroup className="margined">
        <ButtonDropdown isOpen={this.state.strategiesDropdownOpen} toggle={this.strategiesDropdownToggle}>
          <DropdownToggle caret >Strategies</DropdownToggle>
          <DropdownMenu>
            <DropdownItem>SMA</DropdownItem>
            <DropdownItem>LMA</DropdownItem>
          </DropdownMenu>
        </ButtonDropdown>

        <ButtonDropdown isOpen={this.state.backtestDropdownOpen} toggle={this.backtestDropdownToggle}>
          <DropdownToggle caret>Backtest</DropdownToggle>
          <DropdownMenu>
            <DropdownItem onClick={this.startDateOnClick}>Start Date</DropdownItem>
            <DropdownItem onClick={this.endDateOnClick}>End Date</DropdownItem>
            <DropdownItem onClick={this.initCapOnClick}>Initial Capital</DropdownItem>
            <DropdownItem onClick={this.props.runBacktest}>Run Backtest</DropdownItem>
          </DropdownMenu>
        </ButtonDropdown>

        <Modal
          isOpen={this.state.modalOpen}
          style={modalStyle}
          contentLabel="Example Modal">
          {modalContent}
        </Modal>
      </ButtonGroup>
    );
  }
}

export default MenuPanel;
