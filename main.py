import copy
import json
from typing import Callable
from datetime import datetime

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from core.enigma import enigma
from core.logging import logging


INITIAL_CHATS: list[dict[str, str]] = [
    {
        'role': 'assistant',
        'content': 'Hello! I am ENIGMA. How may I help you?',
    }
]


def restart_chat():
    if 'chat_history' in st.session_state:
        init_chat()


def init_chat():
    logging.info('--------------- New Chat --------------------')
    st.session_state['chat_history'] = copy.deepcopy(INITIAL_CHATS)
    st.session_state['chat_id'] = f"ENIGMA_CONV_{datetime.now().timestamp()}".replace('.', '-')
    return st.session_state['chat_history']


def get_chat_id():
    if 'chat_id' not in st.session_state:
        init_chat()
    return st.session_state['chat_id']


def get_messages():
    if 'chat_history' not in st.session_state:
        init_chat()
    return st.session_state['chat_history']


def show_message(role='user', msg='', container=st):
    return container.chat_message(role).write(msg)


def ai_reply(container: DeltaGenerator, ai: Callable):
    with st.spinner('Thinking...'):
        response = ai(get_messages())
    container.chat_message('assistant').write(response)
    st.session_state['chat_history'].append({'role': 'assistant', 'content': response})


# ── Page Config ──
st.set_page_config(initial_sidebar_state='collapsed')
st.title('ENIGMA')
st.caption('Expert Network for Intelligent Guidance and Multi-task Assistance')

messages_container = st.container(border=True)
message_box = messages_container.container(height=550, border=True)

# ── Sidebar ──
with st.sidebar:
    st.header('Conversation Actions')
    st.button('Restart', on_click=restart_chat, use_container_width=True, type='primary')
    st.download_button(
        'Download',
        json.dumps(get_messages(), indent=2),
        f'{get_chat_id()}.json',
        use_container_width=True,
        type='secondary',
    )

# ── Chat Display ──
with message_box:
    for msg in get_messages():
        if msg['role'] in ('user', 'assistant'):
            show_message(msg['role'], msg['content'])

    if prompt := messages_container.chat_input('Type your message'):
        st.session_state['chat_history'].append({'role': 'user', 'content': prompt})
        show_message('user', prompt)
        ai_reply(container=message_box, ai=enigma.process)
