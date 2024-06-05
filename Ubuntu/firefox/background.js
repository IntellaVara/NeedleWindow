


const processedUrls = new Map();

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

// Listen for tab closure
browser.tabs.onRemoved.addListener(function(tabId, removeInfo) {
    console.log(`Tab with ID ${tabId} has been closed`);
    // Emit an event to the Flask server to remove this tab from the vector store
    socket.emit('remove_tab', {tabId: tabId});

    processedUrls.forEach((value, key) => {
        if (key.startsWith(`${tabId}_`)) {
            processedUrls.delete(key);
        }
    });
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



socket.on('activate_matching_tab', function(data) {
    console.log("Attempting to activate matching tab with title:", data.title);
    browser.tabs.query({}).then(tabs => {
        console.log("All open tab titles:");
        tabs.forEach(tab => {
            console.log(tab.title); // Print each tab's title for debugging
        });

        const foundTab = tabs.find(tab => tab.title.includes(data.title));
        if (foundTab) {
            browser.tabs.update(foundTab.id, {active: true}).then(() => {
                console.log("Matching tab activated:", foundTab.title);
                socket.emit('window_info', {windowId: foundTab.windowId, title: foundTab.title});
            });
        } else {
            console.log("No matching tab found for title:", data.title);
        }
    }).catch(err => console.error('Error querying tabs:', err));
});


// Listen for messages from the content scripts
browser.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "getCurrentTabInfo") {
        // Retrieve current tab information and send it back to the sender
        browser.tabs.query({active: true, currentWindow: true})
        .then(tabs => {
            if (tabs.length > 0) {
                sendResponse(tabs[0]);
            } else {
                throw new Error("No active tab found");
            }
        })
        .catch(error => {
            console.error("Error retrieving current tab:", error);
            sendResponse({ error: error.toString() });
        });
        return true;  // Indicate that we want to send a response asynchronously
    }
});


browser.tabs.onUpdated.addListener(function(tabId, changeInfo, tab) {
    let key = `${tabId}_${tab.url}`;
    if (changeInfo.status === 'complete' && (tab.url.endsWith('.pdf') || tab.url.includes('/pdf'))) {
        if (!processedUrls.has(key)) {
            console.log(`Processing PDF in tab ID ${tabId} with URL ${tab.url}`);
            console.log(`Title of the tab: ${tab.title}`);
            processedUrls.set(key, true);

            // Prepare PDF info to send to the server
            const pageInfo = {
                type: 'pdf',
                url: tab.url,
                title: tab.title,
                tabId: tabId
            };

            sendDataToServer(pageInfo);
        } else {
            console.log(`Already processed tab ID ${tabId} with URL ${tab.url}`);
            console.log(`Title of the tab: ${tab.title}`);
        }
    }
});


function sendDataToServer(pageInfo) {
    fetch('http://localhost:5000/receive_page_data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(pageInfo)
    })
    .then(response => response.json())
    .then(data => console.log('Success:', data))
    .catch((error) => console.error('Error:', error));
}



// Handle clicks on the browser action icon
browser.browserAction.onClicked.addListener(() => {
    if (socket.connected) {
        socket.emit('client_message', {data: 'Hello, Flask Server!'});
    } else {
        console.log('WebSocket is not connected.');
    }
});
