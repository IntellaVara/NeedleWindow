// Log when the whole page (including images, scripts, etc.) is fully loaded
window.addEventListener('load', function() {
    console.log("All resources and assets finished loading!");

    // Send a message to the background script to get the current tab information
    browser.runtime.sendMessage({ action: "getCurrentTabInfo" })
    .then(tab => {
        const pageHTML = document.documentElement.innerHTML;
        const pageInfo = {
            url: window.location.href,
            html: pageHTML,
            tabId: tab.id  // Received the current tab ID from background
        };

        // Send the data to your Flask server using the Fetch API
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
    })
    .catch(err => {
        console.error('Error retrieving current tab from background:', err);
    });
});
