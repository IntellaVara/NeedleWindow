console.log('Debug: Background script started.');


// Load the Socket.IO library
importScripts('socket.io.min.js');

var socket = io('http://localhost:5000/chrome', { transports: ['websocket'], upgrade: false });
//var socket = io('ws://localhost:5000/chrome', { transports: ['websocket'], upgrade: false });



// Listening for any tab creation events
chrome.tabs.onCreated.addListener(tab => {
  console.log(`Debug: New tab created with ID ${tab.id}, Title: ${tab.title}, URL: ${tab.url}`);
});

// Listening for updates to any tab
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (tab.url.startsWith('chrome://')) {
    return; // Do nothing for chrome:// URLs
  }
  // We only want to log the info once the tab has finished loading the new page
  if (changeInfo.status === 'complete') {
    console.log(`Debug: Tab updated with ID ${tabId}`);
    console.log(`Updated Tab Info: ID: ${tab.id}, Title: ${tab.title}, URL: ${tab.url}`);

    // Check if the tab is an HTML page
    if (!tab.url.endsWith('.pdf') && !tab.url.includes('/pdf')) {
      // Retrieve the HTML content of the tab
      chrome.scripting.executeScript({
        target: { tabId: tabId },
        function: () => document.documentElement.outerHTML
      }, (results) => {
        if (chrome.runtime.lastError) {
          console.error(chrome.runtime.lastError);
          return;
        }

        if (results && results[0]) {
          const pageHTML = results[0].result;
          const pageInfo = {
            browser: 'chrome',
            type: 'html',
            url: tab.url,
            html: pageHTML,
            tabId: tabId
          };

          // Send the page info to the Flask server
          sendDataToServer(pageInfo);
        }
      });
    }
  }
});

socket.on('activate_matching_tab', function(data) {
  console.log("here");
  console.log("Attempting to activate matching tab with ID:", data.tabId);

  chrome.tabs.query({}, function(tabs) {
      console.log("All open tab titles and IDs:");
      tabs.forEach(tab => {
          console.log(`Title: ${tab.title}, ID: ${tab.id}`); // Detailed print for debugging
      });

      // Find the tab using the tab ID directly for a more reliable match
      const foundTab = tabs.find(tab => tab.id === parseInt(data.tabId));
      if (foundTab) {
          chrome.tabs.update(foundTab.id, {active: true}, function() {
              console.log("Matching tab activated:", foundTab.title, "ID:", foundTab.id);
              socket.emit('window_info_chrome', {windowId: foundTab.windowId, title: foundTab.title});
          });
      } else {
          console.log("No matching tab found for ID:", data.tabId);
      }
  });
});



// Listening for tab closure
chrome.tabs.onRemoved.addListener((tabId, removeInfo) => {
  console.log(`Debug: Tab with ID ${tabId} has been closed`);
});

// Function to send data to the Flask server
function sendDataToServer(pageInfo) {
  console.log('Debug: Sending page info to the Flask server:', pageInfo);
  
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