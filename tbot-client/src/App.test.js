import React from 'react';
import ReactDOM from 'react-dom';
import { shallow, mount } from 'enzyme';
import chai, { expect } from 'chai';
import chaiAsPromised from 'chai-as-promised';
import sha256 from 'crypto-js/sha256';
import sinon from 'sinon';
import App from './App';
import StrategyBoard from './StrategyBoard';
import moment from 'moment';
import api from './API';
import { ButtonDropdown, DropdownToggle, DropdownMenu, DropdownItem, ButtonGroup } from 'reactstrap';

chai.use(chaiAsPromised);
chai.should();

function sleep (time) {
  return new Promise((resolve) => setTimeout(resolve, time));
}

function factorial(n) {
  if (n === 0) { return 1; }
  else if (n < 0) { return -1; }
  else {
    return n * factorial(n - 1);
  }
}

it('renders without crashing', () => {
  const div = document.createElement('div');
  ReactDOM.render(<App host="http://localhost:9000"/>, div);
  ReactDOM.unmountComponentAtNode(div);
});

describe('Test api', () => {

  it('Get algorithm code', () => {

    let testAlgoCode = "print('Test code')";
    
    return api.getAlgoCode('testAlgo', 'http://localhost:9000')
      .then(res => res.text())
      .then(code => {
        expect(code).to.be.a('string');
        expect(code).to.equal(testAlgoCode);
      });
  });

  it('Submit algorithm code', () => {
    
    let testAlgoCode = "print('Submit algorithm code')";

    return api.verifySubmit(testAlgoCode, 'http://localhost:9000')
      .then(res => res.text())
      .then(codeHash => {
        expect(codeHash).to.be.a('string');
        expect(codeHash).to.equal(sha256(testAlgoCode).toString());
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
                                initCapital={initCap}
                                isTesting={true}/>);
    strategyBoard.update();
    strategyBoard.find('#dd_tgl_strategies').first().simulate('click');
    strategyBoard.update();    
    strategyBoard.find('#dd_itm_sma').first().simulate('click');
    strategyBoard.update();
    
    return api.getAlgoCode('SMA', 'http://localhost:9000')
      .then(res => res.text())
      .then(smaCode => {
        // Sleep 0.5 second to ensure the algorithm has been downloaded
        sleep(500).then(() => {
          expect(code).to.be.a('string');
          expect(smaCode).to.be.a('string');
          expect(code).to.equal(smaCode);
          strategyBoard.unmount();          
        });
      });
  });  
});

describe('Test performance board', () => {

  it('Websocket performance data stream is plotted correctedly', () => {
  
  });

  it('Websocket logging data stream is displayed correctedly', () => {
  
  });  
});

// Make the function wait until the connection is made...
function waitForSocketConnection(socket, callback){
    setTimeout(
        function () {
            if (socket.readyState === 1) {
                console.log("Connection is made")
                if(callback != null){
                    callback();
                }
                return;

            } else {
                console.log("wait for connection...")
                waitForSocketConnection(socket, callback);
            }

        }, 5); // wait 5 milisecond for the connection...
}

describe('Test server-client websocket communication', () => {
  
  it('Factorial generator returns each number generated correctedly ', (done) => {

    api.newSession('http://localhost:9000')
      .then(res => res.text())
      .then(session_id => {
        api.getAlgoCode('__TEST_FACTORIAL', 'http://localhost:9000')
          .then(res => res.text())
          .then(code => {
            api.runBacktest(code, 'GENERATOR_MODE', session_id, 'http://localhost:9000')
              .then(ws => {
                var i = 10;
                var res = 1;

                waitForSocketConnection(ws, () => {
                  
                ws.onmessage = (e) => {
                  let msg = JSON.parse(e.data);
                  let val = parseInt(msg.value);
                  expect(val).to.equal(999);
                  expect(val).to.equal(res * i);
                  res *= i;
                  i -= 1;
                  if (i == 0) {
                    expect(res).to.equal(3628800);
                  }
                  done();
                };

                  
                });


              });
          });
      });
  });
});

