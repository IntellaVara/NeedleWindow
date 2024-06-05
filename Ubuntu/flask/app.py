from flask import Flask, request, jsonify
import requests
import PyPDF2
import os
from flask_socketio import SocketIO, emit
import subprocess
import re 
from bs4 import BeautifulSoup  # Import BeautifulSoup

from langchain_community.llms import Ollama
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings


from pydantic import BaseModel, Field

import json


model_name = "sentence-transformers/all-mpnet-base-v2"
model_kwargs = {'device': 'cuda'}
encode_kwargs = {'normalize_embeddings': False}
hf_emb = HuggingFaceEmbeddings(
    model_name=model_name,
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs
)

# what is this nonsense?
vector_store = Chroma.from_texts([""], hf_emb)
vector_store.delete_collection()
vector_store = Chroma.from_texts([""], hf_emb)


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

pages_data = {}  # Array to store page data


query_prompt = ""



@app.route('/receive_page_data', methods=['POST'])
def receive_page_data():
    print("Firing receive_page_data")
    try:
        data = request.get_json()
        page_type = data['type']
        tab_id = data['tabId']
        url = data['url']
        print("\n\nTab ID:", tab_id)

        print("page_type:", page_type)
        
        # Initialize page content string
        page_content = f"<id>{tab_id}</id>\n"
        
        if page_type == 'html':
            html_content = data['html']
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract title
            title_content = soup.title
            if title_content:
                page_content += f"<title>{title_content.text.strip()}</title>\n"
            else:
                page_content += "<title>Not found</title>\n"

            # Extract headers
            for tag in ['h1', 'h2', 'h3']:
                headers = soup.find_all(tag, limit=3)
                for header in headers:
                    header_text = f"<{header.name}>{header.text.strip()[:200]}</{header.name}>"
                    page_content += header_text + "\n"

            # Extract paragraphs
            paragraphs = soup.find_all('p', limit=5)
            for index, paragraph in enumerate(paragraphs):
                paragraph_text = f"<p>{paragraph.text.strip()[:200]}</p>"
                page_content += paragraph_text + "\n"
        
        # elif page_type == 'pdf':
        #     pdf_text = data['text']
        #     pdf_title = data['title'] if 'title' in data else 'PDF Document'
        #     page_content += f"<title>{pdf_title}</title>\n"
        #     page_content += f"{pdf_text}\n"

       
        elif page_type == 'pdf':
            # Download PDF
            response = requests.get(url)
            pdf_path = f"/tmp/{tab_id}.pdf"  # Temp path for the PDF
            with open(pdf_path, 'wb') as f:
                f.write(response.content)

            # Extract text from PDF
            pdf_text = []
            with open(pdf_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                num_pages = min(3, len(reader.pages))  # Limit to the first 3 pages
                for i in range(num_pages):
                    page = reader.pages[i]
                    text = page.extract_text() or ''
                    words = text.split()
                    pdf_text.append(' '.join(words[:200]))  # Only first 200 words per page

            os.remove(pdf_path)  # Clean up the downloaded file

            # Join the extracted text with two newlines and prepare the title
            pdf_text_combined = '\n\n'.join(filter(None, pdf_text))
            pdf_title = data.get('title', 'PDF Document')
            page_content += f"<title>{pdf_title}</title>\n{pdf_text_combined}\n"
            page_content += f"<id>{tab_id}</id>\n"


        # Add the content to the vector store with the tab ID as identifier
        vector_store.add_texts([page_content], ids=[str(tab_id)])

        # Append the formatted page content string to a local data store
        pages_data[str(tab_id)] = page_content

        print(f"Total pages received: {len(pages_data)}")
        print(f"Recently added page content with Tab ID {tab_id}:\n", page_content)

        return jsonify({"status": "success", "message": "Data received"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500



@socketio.on('remove_tab')
def handle_remove_tab(data):
    tab_id = data['tabId']
    print(f"Attempting to remove data associated with Tab ID: {tab_id}")

    try:
        # Perform the deletion from the vector store using the tab ID
        vector_store.delete([str(tab_id)])  # Ensure the ID is a string if necessary
        print(f"Data for Tab ID {tab_id} successfully removed from vector store.")
    except Exception as e:
        print(f"Failed to remove data for Tab ID {tab_id}: {e}")
        # Optionally, you can emit a response back to the client if needed
        emit('removal_error', {'tabId': tab_id, 'error': str(e)})

    return {'status': 'success', 'message': f'Data for Tab ID {tab_id} removed.'}

    

@socketio.on('connect')
def handle_connect():
    print('Client Connected')
    emit('server_response', {'message': 'Hello from Flask!'})
    

@socketio.on('disconnect')
def handle_disconnect():
    print('Client Disconnected')
    try:
        # Perform necessary cleanup
        print('Performed cleanup after disconnection.')
    except Exception as e:
        print(f'Error during disconnect: {str(e)}')


@socketio.on('client_message')
def handle_client_message(message):
    print('Received message from client:', message)
    emit('server_response', {'message': 'Received your message: ' + str(message)})

@app.route('/hello')
def hello_world():
    print("Hello World triggered from shortcut")
    return "Hello World response from flask!"

@app.route('/request_tabs')
def request_tabs():
    print("Request for tabs triggered by shortcut")
    emit('request_tabs', {'message': 'Please send tabs'}, namespace='/', broadcast=True)
    return "Requested tabs from extension"

@socketio.on('send_tabs')
def handle_send_tabs(data):
    print("Received tabs from the extension:")
    if 'windowId' in data:
        print(f"Window ID: {data['windowId']}")



@app.route('/activate_first_tab')
def activate_first_tab():
    # Emit an event to the extension to activate the first tab and focus the window
    emit('activate_first_tab', {'message': 'Activate first tab and focus window'}, namespace='/', broadcast=True)
    return "Command to activate first tab and focus window sent."


@socketio.on('window_info')
def handle_window_info(data):
    print("Received window info:", data)
    window_id = data['windowId']  # Assuming the window ID is directly usable
    print(f"Window ID is {window_id}")
    if 'title' in data:
        result = focus_firefox_window_by_title(data['title'])
        print(result)
   


@app.route('/find_matching_tab', methods=['POST'])
def find_matching_tab():
    data = request.get_json()
    user_query = data['query']
    print("\n\nUser query:", user_query)

    try:
        # Perform a similarity search in the vector store
        search_results = vector_store.similarity_search(user_query, k=3)

        # Filter results to find the top matching tab, if any
        if search_results:
            top_result = search_results[0]  # Assuming the first result is the best match
            # Extract ID and title from the very end of the formatted page content
            tab_id_match = re.search(r'<id>(\d+)</id>\s*$', top_result.page_content, re.MULTILINE)
            title_match = re.search(r'<title>(.*?)</title>\s*$', top_result.page_content, re.MULTILINE)

            if tab_id_match and title_match:
                tab_id = tab_id_match.group(1)
                title = title_match.group(1)

                print("Extracted Tab ID:", tab_id)
                print("Extracted title:", title)

                # Emit event to activate the matching tab
                emit('activate_matching_tab', {'title': title}, namespace='/', broadcast=True)
                return jsonify({"status": "success", "message": "Matching tab activation attempted.", "title": title}), 200
            else:
                return jsonify({"status": "error", "message": "Unable to extract tab ID or title from document."}), 400
        else:
            return jsonify({"status": "success", "message": "No matching document found."}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500



def focus_firefox_window_by_title(title_from_extension):


    try:
        # Retrieve all Firefox windows with their titles
        output = subprocess.check_output(
            "xdotool search --onlyvisible --class 'firefox' | xargs -I % sh -c 'echo \"%,$(xdotool getwindowname %)\"'",
            shell=True
        ).decode()
        
        # Process the output to find a matching window
        for line in output.splitlines():
            window_id, window_title = line.split(",", 1)
            # Check if the window title from extension matches the one retrieved by xdotool
            if title_from_extension in window_title:
                print(f"Matching window found: {window_id}, focusing now.")
                subprocess.run(['xdotool', 'windowactivate', window_id])
                return f"Focused window with ID: {window_id}"
        return "No matching window found."
    except subprocess.CalledProcessError as e:
        return f"Failed to execute xdotool command: {str(e)}", 500
    except Exception as e:
        return f"Error: {str(e)}", 500



if __name__ == '__main__':
    socketio.run(app, debug=True)
