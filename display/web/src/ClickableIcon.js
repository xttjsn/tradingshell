import React, { Component } from 'react';
import "./App.css";

class ClickableIcon extends Component {
  render() {
    return (
      <div className={[this.props.className, "clickable"].join(' ')}>{this.props.icon}</div>
    );
  }
}

export default ClickableIcon;
