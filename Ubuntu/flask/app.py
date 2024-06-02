from flask import Flask, request, jsonify

from flask_socketio import SocketIO, emit
import subprocess
import re 
from bs4 import BeautifulSoup  # Import BeautifulSoup

from langchain_community.llms import Ollama
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate

from pydantic import BaseModel, Field

import json

llm = Ollama(model="llama3:instruct")
embedding = FastEmbedEmbeddings()

# umm...
vector_store = Chroma.from_texts([""], embedding)
vector_store.delete_collection()
vector_store = Chroma.from_texts([""], embedding)


retriever = vector_store.as_retriever(search_type="similarity_score_threshold", 
                                      search_kwargs={"k":10,
                                                     "score_threshold":0.1,}
                                                     )

# Define your desired data structure for text matching.
class TextMatch(BaseModel):
    #match_found: bool = Field(description="Whether an exact match was found")
    title: str = Field(description="The html tag title of the text document")
    id: str = Field(description="The id of the text document")
    
# Set up a parser + inject instructions into the prompt template.
parser = JsonOutputParser(pydantic_object=TextMatch)

prompt = PromptTemplate(
    template="{format_instructions} \n Please check if the user query is in any of the context items." \
         " If there is an exact matching context item, please return its title html tag contents only." \
         " ONLY GIVE THE TOP MATCH."\
         " ONLY PROVIDE THE JSON OUTPUT." \
         " ANSWER BRIEFLY." \
         " DO NOT FORGET THE ID." \
         " only reply with the FULL AND COMPLETE <title> </title> of the matched context item IF IT IS A GOOD MATCH. " \
         " Return \"title\" : \"none\" if there are no incredibly STRONGLY RELEVANT matches." \
         " Context: {context}" \
         " \n\nQuery: {input}\n" \
         ,
         
    input_variables=["context", "input"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)


document_chain = create_stuff_documents_chain(llm, prompt)
chain = create_retrieval_chain(retriever, document_chain)



app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

pages_data = {}  # Array to store page data


query_prompt = "Leg Workout big quads"



@app.route('/receive_page_data', methods=['POST'])
def receive_page_data():
    print("Firing receive_page_data")
    try:
        data = request.get_json()
        html_content = data['html']
        tab_id = data['tabId']  # Retrieve the tab ID sent from the extension
        print("\n\n tab_id:", tab_id)
        soup = BeautifulSoup(html_content, 'html.parser')

        # Start building the page content string
        page_content = ""

        page_content += f"<id>{tab_id}</id>\n"

        # Extract and append the title with HTML tags
        title_content = soup.title
        if title_content:
            page_content += f"<title>{title_content.text.strip()}</title>\n"
        else:
            page_content += "<title>Not found</title>\n"
 
        # Extract and append the first three h1, h2, h3 headers, each enclosed in their respective tags
        for tag in ['h1', 'h2', 'h3']:
            headers = soup.find_all(tag, limit=3)  # Limit to the first 3 headers of each type
            for header in headers:
                header_text = f"<{header.name}>{header.text.strip()[:200]}</{header.name}>"
                page_content += header_text + "\n"

        # Extract and append the first five paragraphs, each enclosed in <p> tags
        paragraphs = soup.find_all('p', limit=5)
        for index, paragraph in enumerate(paragraphs):
            paragraph_text = f"<p>{paragraph.text.strip()[:200]}</p>"  # Enclose in paragraph tags
            page_content += paragraph_text + "\n"

        # Add the content to the vector store with the tab ID as identifier
        vector_store.add_texts([page_content], ids=[str(tab_id)])

        # Append the formatted page content string to a local data store, if needed
        pages_data[str(tab_id)] = page_content

        print(f"Total pages received: {len(pages_data)}")
        print("Recently added page content with Tab ID {tab_id}:\n", page_content)

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

    # Assuming 'chain' is already set up and ready to be used
    response = chain.invoke({"input": user_query})
    print("Response:", response)

    try:
        # Using regex to extract ID from response; assumes ID is always a number
        match = re.search(r'"id"\s*:\s*"(\d+)"', response['answer'])
        if match:
            tab_id = match.group(1)
            print("Extracted Tab ID:", tab_id)

            if tab_id in pages_data:
                page_content = pages_data[tab_id]
                # Extract title from page_content using regex
                title_match = re.search(r'<title>(.*?)</title>', page_content)
                title = title_match.group(1) if title_match else 'None'
                print("Extracted title:", title)

                if title != 'None':
                    emit('activate_matching_tab', {'title': title}, namespace='/', broadcast=True)
                    return jsonify({"status": "success", "message": "Matching tab activation attempted.", "title": title}), 200
                else:
                    return jsonify({"status": "success", "message": "No matching tab found."}), 200
            else:
                return jsonify({"status": "error", "message": "No content found for the given Tab ID."}), 404
        else:
            return jsonify({"status": "error", "message": "Tab ID not found in response."}), 404

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
