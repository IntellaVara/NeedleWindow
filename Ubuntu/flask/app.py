from flask import Flask, request, jsonify
import requests
import PyPDF2
import os
from flask_socketio import SocketIO, emit
import subprocess
import re 
from bs4 import BeautifulSoup  # Import BeautifulSoup


from threading import Thread

import signal

from langchain_community.llms import Ollama
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
import argparse
from tkinter import PhotoImage


import tkinter as tk
from tkinter import simpledialog
import requests
from tkinter import font as tkfont  # Import tkinter font module

from pydantic import BaseModel, Field

import json
import sys

import logging

# Set up basic configuration
logging.basicConfig(level=logging.WARNING)  # Options are DEBUG, INFO, WARNING, ERROR, CRITICAL


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)
#socketio = SocketIO(app, cors_allowed_origins="*")



def signal_handler(sig, frame):
    print('Signal received:', sig)
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


pages_data = {}  # Array to store page data
hf_emb = None
vector_store = None


# Initialize the language model and vector store based on GPU availability
def init_lang_components(use_cuda):
    global hf_emb, vector_store
    
    model_kwargs = {'device': 'cuda' if use_cuda else 'cpu'}
    encode_kwargs = {'normalize_embeddings': False}
    hf_emb = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-mpnet-base-v2",
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs
    )

    # Initialize vector store
    vector_store = Chroma.from_texts([""], hf_emb)
    vector_store.delete_collection()
    vector_store = Chroma.from_texts([""], hf_emb)

@app.route('/receive_page_data', methods=['POST'])
def receive_page_data():
    print("Firing receive_page_data")
    try:
        data = request.get_json()
        browser = data['browser']
        page_type = data['type']
        tab_id = data['tabId']
        url = data['url']
        print("\n\nTab ID:", tab_id)

        print("page_type:", page_type)
        
        # Initialize page content string
        page_content = f"<id>{browser}_{tab_id}</id>\n"
        
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
            page_content += f"<id>{browser}_{tab_id}</id>\n"


        

        # Add the content to the vector store with the tab ID as identifier
        vector_store.add_texts([page_content], ids=[f"{browser}_"+str(tab_id)])

        
        print("Found browser:", browser)
        # Append the formatted page content string to a local data store
        pages_data[f"{browser}_"+str(tab_id)] = page_content

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

    

@socketio.on('connect', namespace='/firefox')
def handle_connect():
    print('Firefox client connected')
    emit('server_response', {'message': 'Hello from Flask to Firefox!'}, namespace='/firefox')
    
@socketio.on('disconnect', namespace='/firefox')
def handle_disconnect():
    print('Firefox client disconnected')

@socketio.on('connect', namespace='/chrome')
def handle_connect_chrome():
    print('Chrome client connected')
    emit('server_response', {'message': 'Hello from Flask to Chrome!'}, namespace='/chrome')

@socketio.on('disconnect', namespace='/chrome')
def handle_disconnect_chrome():
    print('Chrome client disconnected')
    # Perform any necessary cleanup or actions

# @socketio.on('disconnect')
# def handle_disconnect():
#     print('Client Disconnected')
#     try:
#         # Perform necessary cleanup
#         print('Performed cleanup after disconnection.')
#     except Exception as e:
#         print(f'Error during disconnect: {str(e)}')


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


@socketio.on('window_info', namespace='/firefox')
def handle_window_info(data):
    print("Received window info:", data)
    window_id = data['windowId']  # Assuming the window ID is directly usable
    print(f"Window ID is {window_id}")
    if 'title' in data:
        result = focus_firefox_window_by_title(data['title'])
        print(result)
   

@socketio.on('window_info_chrome', namespace='/chrome')
def handle_window_info_chrome(data):
    print("HANDLING CHROME WINDOW INFO!!")
    print("Received window info (Chrome):", data)
    window_id = data['windowId']  # Assuming the window ID is directly usable
    print(f"Window ID is {window_id}")
    if 'title' in data:
        result = focus_chrome_window_by_title(data['title'])
        print(f"Focus result for Chrome: {result}")


# @app.route('/find_matching_tab', methods=['POST'])
# def find_matching_tab():
#     data = request.get_json()
#     user_query = data['query']
#     top_n = int(data.get('top_n', 1))  # Default to 1 if not provided
#     print("\n\nUser query:", user_query)

#     try:
#         # Perform a similarity search in the vector store
#         search_results = vector_store.similarity_search(user_query, k=top_n)

#         # Filter results to find the top matching tab, if any
#         if search_results:
#             top_result = search_results[0]  # Assuming the first result is the best match
#             # Extract ID and title from the very end of the formatted page content
#             tab_id_match = re.search(r'<id>(\d+)</id>\s*$', top_result.page_content, re.MULTILINE)
#             title_match = re.search(r'<title>(.*?)</title>\s*$', top_result.page_content, re.MULTILINE)

#             if tab_id_match and title_match:
#                 tab_id = tab_id_match.group(1)
#                 title = title_match.group(1)

#                 print("Extracted Tab ID:", tab_id)
#                 print("Extracted title:", title)

#                 # Emit event to activate the matching tab
#                 emit('activate_matching_tab', {'title': title, 'tabId': tab_id}, namespace='/', broadcast=True)
#                 return jsonify({"status": "success", "message": "Matching tab activation attempted.", "title": title}), 200
#             else:
#                 return jsonify({"status": "error", "message": "Unable to extract tab ID or title from document."}), 400
#         else:
#             return jsonify({"status": "success", "message": "No matching document found."}), 200

#     except Exception as e:
#         return jsonify({"status": "error", "message": str(e)}), 500



@app.route('/selected_n_activate', methods=['POST'])
def selected_n_activate():
    data = request.get_json()
    title = data.get('title')
    tab_id = data.get('tabId')

    print(f"Activating tab with ID: {tab_id} and title: {title}")
    browser = tab_id.split('_')[0]
    tab_id = tab_id.split('_')[1]

    print(f"Activating tab in {browser} with ID: {tab_id} and title: {title}")
    
    
    # Emit the command to activate the matching tab based on the browser
    if browser == 'firefox':
        socketio.emit('activate_matching_tab', {'title': title, 'tabId': tab_id}, namespace='/firefox')
    elif browser == 'chrome':
        socketio.emit('activate_matching_tab', {'title': title, 'tabId': tab_id}, namespace='/chrome')
    else:
        print(f"Unsupported browser: {browser}")
        return jsonify({"status": "error", "message": f"Unsupported browser: {browser}"})
    
    return jsonify({"status": "success", "message": "Activation attempt sent."})



@app.route('/find_matching_tab', methods=['POST'])
def find_matching_tab():
    data = request.get_json()
    user_query = data['query']
    top_n = int(data.get('top_n', 1))  # Default to 1 if not provided
    print("\n\nUser query:", user_query)

    try:
        # Perform a similarity search in the vector store
        search_results = vector_store.similarity_search(user_query, k=top_n)

        if top_n > 1:
            # Handle multiple results for GUI display
            results = []
            for result in search_results:
                print("Result:", result)
                tab_id_match = re.search(r'<id>([a-zA-Z0-9_]+)</id>\s*$', result.page_content, re.MULTILINE)
                title_match = re.search(r'<title>(.*?)</title>\s*$', result.page_content, re.MULTILINE)

                print("id match?", tab_id_match)
                if tab_id_match and title_match:
                    results.append({'tabId': tab_id_match.group(1), 'title': title_match.group(1)})
            return jsonify({"status": "success", "results": results}), 200
        else:
            # Handle single result for direct activation
            if search_results:
                top_result = search_results[0]
                tab_id_match = re.search(r'<id>([a-zA-Z0-9_]+)</id>\s*$', result.page_content, re.MULTILINE)
                title_match = re.search(r'<title>(.*?)</title>\s*$', top_result.page_content, re.MULTILINE)
                if tab_id_match and title_match:
                    tab_id = tab_id_match.group(1)
                    title = title_match.group(1)
                    emit('activate_matching_tab', {'title': title, 'tabId': tab_id}, namespace='/', broadcast=True)
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



def focus_chrome_window_by_title(title_from_extension):
    try:
        # Retrieve all Chrome windows with their titles
        output = subprocess.check_output(
            "xdotool search --onlyvisible --class 'google-chrome' | xargs -I % sh -c 'echo \"%,$(xdotool getwindowname %)\"'",
            shell=True
        ).decode()

        # Process the output to find a matching window
        for line in output.splitlines():
            window_id, window_title = line.split(",", 1)

            # print title from extension and window title
            print("title from extension", title_from_extension)
            print("window_title", window_title)
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



def run_gui(flask_pid, keyboard_listener_pid=None):
    """Run the persistent Tkinter GUI for input."""
    root = tk.Tk()
    root.title("Query Input")

    # Set the window icon
    icon_path = '../firefox/icons/icon-128.png'  # Update this path to where your icon is stored
    icon_image = PhotoImage(file=icon_path)
    root.iconphoto(True, icon_image)  # The 'True' parameter makes this icon used for all windows if more windows are opened

    root.tk.call('tk', 'scaling', 1.5)  # Adjusts the scaling factor

    # Define fonts
    label_font = tkfont.Font(family='Helvetica', size=14, weight='bold')
    entry_font = tkfont.Font(family='Helvetica', size=12)
    button_font = tkfont.Font(family='Helvetica', size=12, weight='bold')

    # def on_submit(event=None):  # Allow the function to be called with an event
    #     user_query = entry.get()
    #     top_n = top_n_spinbox.get()  # Get the value from the spinbox
    #     if user_query:
    #         url = 'http://localhost:5000/find_matching_tab'
    #         response = requests.post(url, json={"query": user_query, "top_n": top_n})
    #         result_label.config(text=f"Response: {response.text}")
    #     entry.delete(0, tk.END)  # Clear the entry after submitting
    # def on_submit(event=None):
    #     """Handle the submission of the query and the selection of results."""
    #     user_query = entry.get()
    #     top_n = top_n_spinbox.get()  # Get the value from the spinbox
    #     if user_query:
    #         url = 'http://localhost:5000/find_matching_tab'
    #         response = requests.post(url, json={"query": user_query, "top_n": top_n})
    #         response_data = response.json()
            
    #         # Clear previous results
    #         for widget in results_frame.winfo_children():
    #             widget.destroy()
            
    #         if response_data['status'] == 'success':
    #             # Check if there are multiple results
    #             if 'results' in response_data:
    #                 for result in response_data['results']:
    #                     btn = tk.Button(results_frame, text=f"{result['title']}",
    #                                     command=lambda r=result: select_result(r))
    #                     btn.pack()
    #             else:
    #                 result_label.config(text=f"Response: {response_data['message']}")
    #         else:
    #             result_label.config(text=f"Error: {response_data['message']}")
            
    #         entry.delete(0, tk.END)  # Clear the entry after submitting

    def on_submit(event=None):
        """Handle the submission of the query and the selection of results."""
        user_query = entry.get()
        top_n = top_n_spinbox.get()  # Get the value from the spinbox
        if user_query:
            url = 'http://localhost:5000/find_matching_tab'
            response = requests.post(url, json={"query": user_query, "top_n": top_n})
            response_data = response.json()
            
            # Clear previous results
            for widget in results_frame.winfo_children():
                widget.destroy()
            
            if response_data['status'] == 'success':
                # Check if there are multiple results
                if 'results' in response_data:
                    for result in response_data['results']:
                        btn = tk.Button(results_frame, text=f"{result['title']}",
                                        command=lambda r=result: select_result(r))
                        btn.pack()
                else:
                    result_label.config(text=f"Response: {response_data['message']}")

                #print("doing")
                #print("response data keys", response_data.keys())
                results_frame.pack_propagate(True)  # Allow frame to shrink
                #result_label.config(text=f"Response: {response_data['message']}")
                results_frame.config(height=1)  # Set to minimal height when there are no results
            else:
                results_frame.pack_propagate(True)  # Allow frame to shrink
                result_label.config(text=f"Error: {response_data['message']}")
                results_frame.config(height=1)  # Set to minimal height on error


            # else:
            #     result_label.config(text=f"Error: {response_data['message']}")
            
            entry.delete(0, tk.END)  # Clear the entry after submitting



    def select_result(result):
        """Handle the selection of a result to emit its data."""
        print("Selected Result:", result)
        url = 'http://localhost:5000/selected_n_activate'
        response = requests.post(url, json={"title": result['title'], "tabId": result['tabId']})
    
        print(response.json())





    def on_close(flask_pid, keyboard_listener_pid, root):
        print("Stopping Flask app and optional keyboard listener...")
        os.kill(flask_pid, signal.SIGINT)  # Send SIGINT to Flask app
        if keyboard_listener_pid:
            os.kill(keyboard_listener_pid, signal.SIGTERM)  # Optionally kill the keyboard listener
        root.destroy()  # Close the GUI

    # Layout management
    input_frame = tk.Frame(root)
    input_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

    # Setup the results frame in your GUI
    results_frame = tk.Frame(root)
    results_frame.pack(fill='both', expand=True)


    tk.Label(input_frame, text="Enter your query:", font=label_font).pack(side=tk.LEFT)

    entry = tk.Entry(input_frame, font=entry_font, width=50)
    entry.pack(side=tk.LEFT, padx=5)
    entry.focus_set()  # Set focus on the entry widget
    entry.bind("<Return>", on_submit)  # Bind the Enter key to the submit function

    submit_button = tk.Button(input_frame, text="Submit", command=on_submit, font=button_font)
    submit_button.pack(side=tk.LEFT, padx=5)

    # Top N selection
    top_n_frame = tk.Frame(root)
    top_n_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

    tk.Label(top_n_frame, text="Top N:", font=label_font).pack(side=tk.LEFT)
    top_n_spinbox = tk.Spinbox(top_n_frame, from_=1, to=10, width=5, font=entry_font)
    top_n_spinbox.pack(side=tk.LEFT, padx=5)

    result_label = tk.Label(root, text="", font=label_font)
    result_label.pack(pady=5)

    root.protocol("WM_DELETE_WINDOW", lambda: on_close(flask_pid, keyboard_listener_pid, root))
    root.mainloop()




# Main entry point to launch the Flask app with command-line arguments for CUDA and GUI mode
def main(use_cuda, use_gui, keyboard_listener_pid=None):

    print(f"Running with {'GPU support' if use_cuda else 'CPU only'}.")
    init_lang_components(use_cuda)

    if use_gui:
        print("GUI mode enabled.")
        # Run the GUI in a separate thread
        gui_thread = Thread(target=run_gui, args=(os.getpid(), keyboard_listener_pid))
        gui_thread.start()
    else:
        print("Hotkeys mode enabled.")

    #socketio.run(app, port=5000, debug=True, use_reloader=False)
    #socketio.run(app, host='127.0.0.1', port=5000, debug=True, use_reloader=False, ssl_context=('localhost.crt', 'localhost.key'), allow_unsafe_werkzeug=True)
    app.run(port=5000, debug=True, use_reloader=False)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run the Flask app with optional CUDA and GUI support.')
    parser.add_argument('--cuda', action='store_true', help='Enable CUDA support for GPU processing.')
    parser.add_argument('--gui', action='store_true', help='Enable GUI mode instead of hotkeys interaction.')
    parser.add_argument('--keyboard_listener_pid', default=None, help='PID of the keyboard listener process, if any.')

    args = parser.parse_args()
    
    if args.keyboard_listener_pid == 'None':
        args.keyboard_listener_pid = None
    print("main pid is ", os.getpid())
    # print the args
    print(args)
    main(args.cuda, args.gui, args.keyboard_listener_pid)