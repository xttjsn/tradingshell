class API {

  getPlotWebsocket = (host) => {
    if (typeof host == 'undefined' || host == null) { host = ''; }
    return fetch(host + '/plot', {
      method: 'GET',
    })
      .then(res => res.text())
      .then(data => JSON.parse(data))
      .then(jsondata => jsondata.port)
      .then(wsport => {
        var host = window.location.hostname;
        var ws = new WebSocket('ws:' + host + ':' + wsport.toString());
        return ws;
      });
  }

  newSession = (host) => {
    if (typeof host == 'undefined' || host == null) { host = ''; }
    return fetch(host + '/api/newSession', {
      method: 'POST',
      headers: {
        'Content-Type': "application/json",
      },
      body: JSON.stringify({
        dummy: 'dummy'
      })
    });
  }

  getAllAlgo = (host) => {
    if (typeof host == 'undefined' || host == null) { host = ''; }
    return fetch(host + '/api/getAllAlgo', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        dummy: 'dummy'
      })
    })
      .then(res => res.text())
      .then(res => JSON.parse(res).StrategyNames);
  }
  
  getAlgoCode = (algoName, host) => {
    if (typeof host == 'undefined' || host == null) { host = ''; }
    return fetch(host + '/api/getAlgoCode', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        algoName: algoName,
      })
    });
  }

  submitAlgoCode = (algoCode, run, host) => {
    if (typeof host == 'undefined' || host == null) { host = ''; }
    return fetch(host + '/api/submitAlgoCode', {
      method: 'POST',
      headers : {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        algoCode: algoCode,
        run: run
      })
    });
  }

  verifySubmit = (algoCode, host) => {
    if (typeof host == 'undefined' || host == null) { host = ''; }
    return fetch(host + '/api/verifySubmit', {
      method: 'POST',
      headers : {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        algoCode: algoCode
      })
    });
  }

  runBacktest = (algoCode, mode, session_id, host) => {
    if (typeof host == 'undefined' || host == null) { host = ''; }
    return fetch(host + '/api/runBacktest', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        algoCode: algoCode,
        mode: mode,
        session_id: session_id
      })
    }).then(res => res.text())
      .then(wsport => { // This is the port that runs websocket server
        var host = window.location.hostname;
        var ws = new WebSocket('ws:' + host + ':' + wsport);
        return ws;
      });
  }
}

var api = new API();
export default api;
