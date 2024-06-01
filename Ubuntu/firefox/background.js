// Assuming the Socket.IO client is loaded from `socket.io.min.js` as configured in `manifest.json`
var socket = io('http://localhost:5000', {transports: ['websocket'], upgrade: false});

socket.on('connect', function() {
    console.log('WebSocket connection established');
});

socket.on('server_response', function(data) {
    console.log('Message from server:', data.message);
});

socket.on('disconnect', function() {
    console.log('WebSocket connection disconnected');
});

socket.on('request_tabs', function(data) {
    console.log(data.message);
    browser.windows.getCurrent().then(windowInfo => {
        browser.tabs.query({windowId: windowInfo.id}).then(tabs => {
            let tabsInfo = tabs.map(tab => ({ title: tab.title, url: tab.url }));
            console.log("Sending tabs info and window ID:", tabsInfo);
            // Include the window ID in the data sent back
            socket.emit('send_tabs', {tabs: tabsInfo, windowId: windowInfo.id});
        }).catch(err => {
            console.error('Error querying tabs:', err);
        });
    });
});


socket.on('activate_first_tab', function(data) {
    console.log(data.message);
    // Retrieve the current window and then the first tab
    browser.windows.getCurrent().then(windowInfo => {
        browser.tabs.query({windowId: windowInfo.id, index: 0}).then(tabs => {
            if (tabs.length > 0) {
                browser.tabs.update(tabs[0].id, {active: true}).then(() => {
                    console.log("First tab activated.");
                    // Now send the window ID to the Flask server
                    socket.emit('window_info', {windowId: windowInfo.id, title: tabs[0].title});
                });
            }
        }).catch(err => console.error('Error querying tabs:', err));
    });
});




// Handle clicks on the browser action icon
browser.browserAction.onClicked.addListener(() => {
    if (socket.connected) {
        socket.emit('client_message', {data: 'Hello, Flask Server!'});
    } else {
        console.log('WebSocket is not connected.');
    }
});
