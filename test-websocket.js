const WebSocket = require('ws');

const ws = new WebSocket('ws://localhost:8004/graphql', {
  headers: {
    'Sec-WebSocket-Protocol': 'graphql-ws'
  }
});

ws.on('open', function open() {
  console.log('WebSocket connected');
  
  // Send connection init
  ws.send(JSON.stringify({
    type: 'connection_init',
    payload: {}
  }));
});

ws.on('message', function message(data) {
  console.log('Received:', data.toString());
  const msg = JSON.parse(data.toString());
  
  if (msg.type === 'connection_ack') {
    console.log('Connection acknowledged, sending subscription');
    
    // Subscribe to risk alerts
    ws.send(JSON.stringify({
      id: '1',
      type: 'subscribe',
      payload: {
        query: `
          subscription {
            riskAlert(companyIds: ["1", "2"]) {
              id
              timestamp
              companyId
              severity
              message
              riskScore
              factors {
                type
                description
                impact
              }
            }
          }
        `
      }
    }));
  }
});

ws.on('error', function error(err) {
  console.error('WebSocket error:', err);
});

ws.on('close', function close() {
  console.log('WebSocket disconnected');
});

// Keep the script running
setTimeout(() => {
  console.log('Closing connection');
  ws.close();
}, 30000); // 30 seconds