#setup streamlit
import streamlit as st
import requests
 
BACKEND_URL = "http://127.0.0.1:8000/ask"

st.set_page_config(page_title="AI Mental Health Therapist", page_icon=":robot_face:", layout="wide")
st.title("Safe Space: AI Mental Health Therapist")

#initialize chat history in session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

#user is able to ask question

#chat input
user_input =st.chat_input("what is on your mind today?")
if user_input:
    #append user input to chat history
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    response=requests.post(BACKEND_URL, json={"message": user_input})
    
    st.session_state.chat_history.append({"role": "assistant", "content": f'{response.json()["response"]} WITH TOOL: [{response.json()["tool_called"]}]'})


#show message 
for message in st.session_state.chat_history:
    if message["role"] == "user":
        st.chat_message("user").markdown(message["content"])
    else:
        st.chat_message("assistant").markdown(message["content"])
        