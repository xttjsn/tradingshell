import React, { Component } from 'react';
import './Panel.css';

class SearchPanel extends Component {
  render() {
    return (
      <div className={`overlay_div z_index_5 search_panel`}>
        Search Lives Here
      </div>
    );
  }
}

export default SearchPanel;
