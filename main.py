import json
from typing import Any, Callable

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from core.enigma import enigma
from core.logging import logging

INITIAL_CHATS:list[dict[str,str]] = [
    {
        'role': "assistant",
        'content': "Hello I am Enigma. How may I help you?.",
    }
]

def restart_chat():
    if "chat_history" in st.session_state:
        init_chat()

def init_chat():
    logging.info("---------------New Chat--------------------")
    logging.info("Called init_chat")
    st.session_state["chat_history"] = INITIAL_CHATS

    return st.session_state["chat_history"]


def get_messages():
    if "chat_history" not in st.session_state:
        init_chat()
    return st.session_state["chat_history"]


def init_chatbox(height=550, container:Any=st): #type: ignore
    return container.container(height=height, border=True)


def show_message(role='user', msg='This is new message', container=st):
    return container.chat_message(role).write(msg)


def new_message(role: str = "user", msg: str = "This is new message", container=st):
    st.session_state["chat_history"].append({'role': role, 'content': msg})
    return show_message(role, msg, container)


def ai_reply(container:DeltaGenerator, ai:Callable): #type: ignore
    response = ai(get_messages())
    container.chat_message('assistant').write(response)

    st.session_state["chat_history"].append({'role': 'assistant', 'content': response})

st.set_page_config(initial_sidebar_state="collapsed")

st.title("E.N.I.G.M.A")
st.caption("Expert Network for Intelligent Guidance and Multi-task Assistance")

messages_container = st.container(border=True)
message_box = init_chatbox(height=550, container=messages_container)

with st.sidebar:
    st.header("Conversation Actions")
    st.button("Restart", on_click=restart_chat, use_container_width=True, type="primary")
    st.download_button("Download", json.dumps(get_messages()), use_container_width=True, type="secondary")

with message_box:
    for i, msg in enumerate(get_messages()):
        if msg['role'] != 'system':
            show_message(msg['role'], msg['content'])

    if prompt := messages_container.chat_input("Type your message"):
        new_message(msg=prompt)
        ai_reply(container=message_box, ai=enigma.process)
