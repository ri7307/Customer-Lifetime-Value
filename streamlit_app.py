import os
import socket
import threading
import time

import streamlit as st
from streamlit.components.v1 import iframe

import clv_dashboard


def is_port_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex((host, port)) != 0


def find_free_port(start_port: int = 8050, host: str = "127.0.0.1") -> int:
    port = start_port
    while port < 9000:
        if is_port_free(host, port):
            return port
        port += 1
    raise RuntimeError("No free port found for Dash server")


def run_dash_server() -> int:
    host = "127.0.0.1"
    port = int(os.environ.get("DASH_PORT", 8050))
    if not is_port_free(host, port):
        port = find_free_port(start_port=port, host=host)

    thread = threading.Thread(
        target=clv_dashboard.app.run,
        kwargs={
            "host": host,
            "port": port,
            "debug": False,
        },
        daemon=True,
    )
    thread.start()
    return port


st.set_page_config(page_title="CLV Intelligence Dashboard", layout="wide")

st.title("CLV Intelligence Dashboard")
st.write("Your Dash dashboard is embedded below. If the dashboard does not appear, refresh the page.")

try:
    dash_port = run_dash_server()
    time.sleep(1.0)
    dash_url = f"http://127.0.0.1:{dash_port}"
    iframe(dash_url, height=900)
except Exception as err:
    st.error("Unable to start the Dash server inside Streamlit.")
    st.exception(err)
