import React from 'react';
import ReactDOM from 'react-dom';
import { shallow, mount } from 'enzyme';
import { expect } from 'chai';
import { SHA256 } from 'crypto-js/sha256';
import sinon from 'sinon';
import App from './App';
import StrategyBoard from './StrategyBoard';
import moment from 'moment';
import api from './API';

it('renders without crashing', () => {
  const div = document.createElement('div');
  ReactDOM.render(<App />, div);
  ReactDOM.unmountComponentAtNode(div);
});

describe('Test api', () => {

  it('Get algorithm code', () => {

    let testAlgoCode = "print('Get algorithm code')";
    
    api.getAlgoCode('testAlgo')
      .then(code => {
        expect(code).to.be.a('string');
        expect(code).to.equal(testAlgoCode);
      });
  });

  it('Submit algorithm code', () => {
    
    let testAlgoCode = "print('Submit algorithm code')";

    api.submitAlgoCode(testAlgoCode, true)  // Require code hash to be sent back
      .then(codeHash => {
        expect(codeHash).to.be.a('string');
        expect(codeHash).to.equal(SHA256(testAlgoCode).toString());
      });
  });
  
});

describe('Test strategy board', () => {
  
  it('Code panel can populate selected algorithm\'s code', () => {
    let sDate = moment('2018-01-01');
    let eDate = moment('2019-01-01');
    let initCap = 10000;
    let setSDate = sinon.spy();
    let setEDate = sinon.spy();
    let setInitCap = sinon.spy();
    let code;
    let setCode = (newCode) => {
      code = newCode;
    };
    let strategyBoard = mount(<StrategyBoard
                                algocode={""}
                                onCodeChange={setCode}
                                setBacktestsStartDate={setSDate}
                                setBacktestsEndDate={setEDate}
                                setInitCapital={setInitCap}                            
                                backtestStartDate={sDate}
                                backtestEndDate={eDate}
                                initCapital={initCap}/>);
    
    strategyBoard.find('#DropdownToggleStrategies').simulate('click');
    strategyBoard.find('#DropdownItemSMA').simulate('click');

    api.getAlgoCode('SMA')
      .then(smaCode => {
        expect(code).to.be.a('string');
        expect(smaCode).to.be.a('string');
        expect(code).to.equal(smaCode);
      });

    strategyBoard.unmount();
  });  
});

describe('Test performance board', () => {

  it('Websocket performance data stream is plotted correctedly', () => {
  
  });

  it('Websocket logging data stream is displayed correctedly', () => {
  
  });  
});

describe('Test server side communication', () => {
  
  it('Run backtest command sends correct data to server', () => {
  
  });
});

