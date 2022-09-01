import socket
import struct
from pydlt import (
    StandardHeader,
    DltMessage,
    MessageType,
    ServiceId,
    ControlResponse,
    MessageLogInfo,
)
from typing import Optional


def _tobytes(value: str) -> bytes:
    if value is None:
        return b""
    return value.encode("ascii")


class DltClient:
    # TODO other connection methods
    def __init__(self, hostname, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((hostname, port))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.socket.close()

    def _recv(self, msglen: int):
        chunks = []
        bytes_recd = 0
        while bytes_recd < msglen:
            chunk = self.socket.recv(msglen - bytes_recd)
            if chunk == b"":
                raise RuntimeError("socket connection broken")
            chunks.append(chunk)
            bytes_recd = bytes_recd + len(chunk)
        return b"".join(chunks)

    def _send(self, msg: bytes):
        totalsent = 0
        while totalsent < len(msg):
            sent = self.socket.send(msg[totalsent:])
            if sent == 0:
                raise RuntimeError("socket connection broken")
            totalsent += sent

    def receive(self) -> DltMessage:
        """receive next dlt message (blocking)"""
        # TODO timeout
        msg_data = self._recv(StandardHeader.DATA_MIN_LENGTH)
        msgsize = struct.unpack(StandardHeader.STRUCT_MIN_FORMAT, msg_data)[2]
        msg_data += self._recv(msgsize - len(msg_data))
        return DltMessage.create_from_bytes(msg_data, False)

    def control(self, msg: DltMessage) -> DltMessage:
        """send control message and receive response"""
        self._send(msg.to_bytes())
        while True:
            rsp = self.receive()  # TODO: howto not lose those messages? callback?
            if (
                rsp.ext_header is not None
                and rsp.ext_header.message_type == MessageType.DLT_TYPE_CONTROL
                and msg.payload.message_id == rsp.payload.message_id
            ):
                return rsp

    def set_log_level(
        self,
        ecuid: str,
        new_log_level: MessageLogInfo,
        apid: Optional[str] = None,
        ctid: Optional[str] = None,
        com: Optional[str] = None,
    ):
        """Set new log level"""
        arguments = struct.pack(
            "<4s4sb4s", _tobytes(apid), _tobytes(ctid), new_log_level, _tobytes(com)
        )
        msg = DltMessage.create_control_message(
            ServiceId.SET_LOG_LEVEL, ecuid, arguments
        )
        rsp = self.control(msg)
        endian = ">" if rsp.std_header.msb_first else "<"
        (status,) = struct.unpack(f"{endian}B", rsp.payload.non_static_data[:1])
        return ControlResponse(status)

    def set_default_log_level(
        self, ecuid: str, new_log_level: MessageLogInfo, com: Optional[str] = None
    ):
        arguments = struct.pack("<b4s", new_log_level, _tobytes(com))
        msg = DltMessage.create_control_message(
            ServiceId.SET_DEFAULT_LOG_LEVEL, ecuid, arguments
        )
        rsp = self.control(msg)
        endian = ">" if rsp.std_header.msb_first else "<"
        (status,) = struct.unpack(f"{endian}B", rsp.payload.non_static_data[:1])
        return ControlResponse(status)

    def get_software_version(self, ecuid: str):
        """Get ECU Software Version (7.7.7.1.24)"""
        msg = DltMessage.create_control_message(ServiceId.GET_SOFTWARE_VERSION, ecuid)
        rsp = self.control(msg)
        endian = ">" if rsp.std_header.msb_first else "<"
        status, length = struct.unpack(f"{endian}BI", rsp.payload.non_static_data[:5])
        return (
            ControlResponse(status),
            length,
            rsp.payload.non_static_data[5:].decode("ascii"),
        )
