import React, { Component } from 'react';
import brace from 'brace';
import AceEditor from 'react-ace';

import 'brace/mode/python';
import 'brace/theme/github';

import './Panel.css';

class CodePanel extends Component {
  render() {
    return (
      <div className="overlay_div z_index_0">
        <AceEditor
          mode="python"
          theme="github"
          name="CODE_PANEL"
          onChange={this.props.onCodeChange}
          editorProps={{$blockScrolling: true}}
          value={this.props.code}
        />
      </div>
    );
  }
}

export default CodePanel;
