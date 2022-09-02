import pytest
import sys
import socket
from pydlt import DltClient, DltMessage, MessageType, MessageLogInfo, ArgumentString


def create_message(counter):
    msg = DltMessage.create_verbose_message(
        [ArgumentString(f"foo {counter}")],
        MessageType.DLT_TYPE_LOG,
        MessageLogInfo.DLT_LOG_INFO,
        "app",
        "ctx",
        timestamp=93678,  # 9.3678 sec
        session_id=12345,
        ecu_id="ecu",
        message_counter=counter
    )
    return msg


class DltServer:
    def __init__(self, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(('localhost', port))
        self.socket.listen(2)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.socket.close()

    def __del__(self):
        self.socket.close()

    def accept(self):
        conn, address = self.socket.accept()
        data = create_message(1).to_bytes()
        with conn:
            conn.sendall(data)
            conn.recv()


def test_receive():
    with DltServer(43900) as server:
        with DltClient("localhost", 43900) as dlt:
            server.accept()
            msg = dlt.receive()
            assert msg.std_header.message_counter == 1


if __name__ == "__main__":
    pytest.main(sys.argv)
