// Log when the whole page (including images, scripts, etc.) is fully loaded
window.addEventListener('load', function() {
    console.log("All resources and assets finished loading!");
    console.log("Current MIME type:", document.contentType);  // Log the MIME type of the document
    console.log("Current URL:", window.location.href);  // Log the current URL

    // Check if the current document is a PDF by looking at the MIME type or URL
    const isPdfMimeType = document.contentType === 'application/pdf';
    const isPdfUrl = window.location.href.endsWith('.pdf');
    console.log("Is PDF MIME Type:", isPdfMimeType);  // Log whether the MIME type indicates a PDF
    console.log("Is PDF URL:", isPdfUrl);  // Log whether the URL ends with .pdf

    if (isPdfMimeType || isPdfUrl) {
        console.log("Detected as PDF, handling with PDF.js");
        handlePDFDocument();
    } else {
        console.log("Detected as HTML, handling normally");
        handleHTMLDocument();
    }
});

function handleHTMLDocument() {
    browser.runtime.sendMessage({ action: "getCurrentTabInfo" })
    .then(tab => {
        const pageHTML = document.documentElement.innerHTML;
        const pageInfo = {
            type: 'html',  // Indicate this is HTML content
            url: window.location.href,
            html: pageHTML,
            tabId: tab.id
        };

        sendDataToServer(pageInfo);
    })
    .catch(err => console.error('Error retrieving current tab from background:', err));
}




// function handlePDFDocument() {
//     console.log("PDF document handler initiated"); // Log initiation of PDF handling

//     browser.runtime.sendMessage({ action: "getCurrentTabInfo" })
//     .then(tab => {
//         console.log("Tab information received:", tab); // Log tab info reception

//         // Configure PDF.js to use the worker from your extension's accessible resources
//         pdfjsLib.GlobalWorkerOptions.workerSrc = browser.runtime.getURL('pdf.worker.mjs');

//         const loadingTask = pdfjsLib.getDocument({
//             url: window.location.href
//         });

//         loadingTask.promise.then(function(pdf) {
//             console.log(`PDF loaded with ${pdf.numPages} pages total`); // Log PDF load and page count

//             let allTextPromises = [];
//             let pdfTitle = (pdf._metadata && pdf._metadata.get('Title')) ? pdf._metadata.get('Title') : "No Title Found";
//             console.log("PDF Title:", pdfTitle); // Log extracted title from metadata

//             // Only fetch up to the first 3 pages
//             for (let pageNum = 1; pageNum <= Math.min(pdf.numPages, 3); pageNum++) {
//                 allTextPromises.push(pdf.getPage(pageNum).then(page => {
//                     return page.getTextContent().then(textContent => {
//                         console.log(`Text from page ${pageNum} extracted`); // Log text extraction from each page
//                         return textContent.items.map(item => item.str).join(' ');
//                     });
//                 }));
//             }

//             Promise.all(allTextPromises).then(pagesText => {
//                 console.log("All selected pages' text combined"); // Log final text combination

//                 const pageInfo = {
//                     type: 'pdf',  // Indicate this is PDF content
//                     url: window.location.href,
//                     text: pagesText.join('\n\n'),  // Join all pages text with two newlines
//                     title: pdfTitle,  // PDF Title from metadata
//                     tabId: tab.id
//                 };

//                 console.log("Sending PDF info to server:", pageInfo); // Log the information being sent
//                 sendDataToServer(pageInfo);
//             });
//         }).catch(err => {
//             console.error('Error loading PDF:', err); // Log errors from PDF loading
//         });
//     })
//     .catch(err => {
//         console.error('Error retrieving current tab from background:', err); // Log errors in retrieving tab information
//     });
// }



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
