class API {
  getAlgoCode = (algoName, host) => {
    if (typeof host === 'undefined' || host == null) { host = ''; }
    return fetch(host + '/api/getAlgoCode', {
      method: 'POST',
      headers : {
        'Content-Type': 'application/json',
        
      },
      body: JSON.stringify({
        algoName: algoName
      })
    });
  }

  submitAlgoCode = (algoCode, run, host) => {
    if (typeof host === 'undefined' || host == null) { host = ''; }
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
    if (typeof host === 'undefined' || host == null) { host = ''; }
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

  runBacktest = (algoCode, mode, host) => {
    if (typeof host === 'undefined' || host == null) { host = ''; }
    return fetch(host + '/api/runBacktest', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        algoCode: algoCode,
        mode: mode
      })
    }).then(res => res.text())
      .then(uri => { // This is the uri that the server has granted us for websocket
        var ws = new WebSocket(uri);
        return ws;
      });
  }
}

var api = new API();
export default api;
