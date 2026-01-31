sessions_store = {}

def get_session(session_id: str):
    if session_id not in sessions_store:
        sessions_store[session_id] = []
    return sessions_store[session_id]


def add_message(session_id: str, role: str, content: str):
    history = get_session(session_id)
    history.append({"role": role, "content": content})