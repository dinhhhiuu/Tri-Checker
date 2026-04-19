import json
import queue
import socket
import threading
from typing import Any


DEFAULT_PORT = 5000


def serialize_path(path):
    return [[row, col] for row, col in path]


def deserialize_path(path):
    if not isinstance(path, list):
        return []
    return [tuple(step) for step in path if isinstance(step, list) and len(step) == 2]


class _BaseSession:
    def __init__(self) -> None:
        self._events: queue.Queue[dict[str, Any]] = queue.Queue()
        self._closed = threading.Event()
        self._send_lock = threading.Lock()
        self.status = "offline"

    def poll_events(self) -> list[dict[str, Any]]:
        events = []

        while True:
            try:
                events.append(self._events.get_nowait())
            except queue.Empty:
                return events

    def close(self) -> None:
        self._closed.set()

    def _push_event(self, event_type: str, **payload: Any) -> None:
        self._events.put({"type": event_type, **payload})


class HostSession(_BaseSession):
    def __init__(self, host: str = "0.0.0.0", port: int = DEFAULT_PORT) -> None:
        super().__init__()
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((host, port))
        self.server_socket.listen(1)
        self.server_socket.settimeout(0.5)
        self.client_socket: socket.socket | None = None
        self.status = "waiting for client"
        self._accept_thread = threading.Thread(target=self._accept_loop, daemon=True)
        self._accept_thread.start()

    def has_client(self) -> bool:
        return self.client_socket is not None

    def _accept_loop(self) -> None:
        while not self._closed.is_set():
            try:
                client_socket, address = self.server_socket.accept()
            except socket.timeout:
                continue
            except OSError:
                return

            if self.client_socket is not None:
                client_socket.close()
                continue

            client_socket.settimeout(0.5)
            self.client_socket = client_socket
            self.status = f"client connected: {address[0]}:{address[1]}"
            self._push_event("client_connected", address=address)
            threading.Thread(target=self._read_loop, args=(client_socket,), daemon=True).start()

    def _read_loop(self, client_socket: socket.socket) -> None:
        buffer = ""

        while not self._closed.is_set():
            try:
                chunk = client_socket.recv(4096)
            except socket.timeout:
                continue
            except OSError:
                break

            if not chunk:
                break

            buffer += chunk.decode("utf-8")

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if not line.strip():
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                self._push_event("client_message", payload=payload)

        self._disconnect_client(notify=True)

    def send(self, payload: dict[str, Any]) -> None:
        if self.client_socket is None:
            return

        message = (json.dumps(payload) + "\n").encode("utf-8")
        try:
            with self._send_lock:
                self.client_socket.sendall(message)
        except OSError:
            self._disconnect_client(notify=True)

    def _disconnect_client(self, notify: bool) -> None:
        if self.client_socket is None:
            return

        try:
            self.client_socket.close()
        except OSError:
            pass

        self.client_socket = None
        self.status = "waiting for client"
        if notify and not self._closed.is_set():
            self._push_event("client_disconnected")

    def close(self) -> None:
        super().close()
        self._disconnect_client(notify=False)
        try:
            self.server_socket.close()
        except OSError:
            pass


class ClientSession(_BaseSession):
    def __init__(self, host: str, port: int = DEFAULT_PORT, timeout: float = 5.0) -> None:
        super().__init__()
        self.host = host
        self.port = port
        self.socket = socket.create_connection((host, port), timeout=timeout)
        self.socket.settimeout(0.5)
        self.status = f"connected to {host}:{port}"
        self._reader_thread = threading.Thread(target=self._read_loop, daemon=True)
        self._reader_thread.start()

    def _read_loop(self) -> None:
        buffer = ""

        while not self._closed.is_set():
            try:
                chunk = self.socket.recv(4096)
            except socket.timeout:
                continue
            except OSError:
                break

            if not chunk:
                break

            buffer += chunk.decode("utf-8")

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if not line.strip():
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                self._push_event("server_message", payload=payload)

        self.status = "disconnected"
        if not self._closed.is_set():
            self._push_event("server_disconnected")

    def send(self, payload: dict[str, Any]) -> None:
        message = (json.dumps(payload) + "\n").encode("utf-8")
        with self._send_lock:
            self.socket.sendall(message)

    def create_room(self, max_players: int = 2, ai_slots: dict | None = None) -> None:
        payload: dict = {"type": "create_room", "max_players": max(2, min(3, max_players))}
        if ai_slots:
            payload["ai_slots"] = {str(k): v for k, v in ai_slots.items()}
        self.send(payload)

    def join_room(self, room_id: str) -> None:
        self.send({"type": "join_room", "room_id": room_id.upper().strip()})

    def get_lobby(self) -> None:
        self.send({"type": "get_lobby"})

    def close(self) -> None:
        super().close()
        try:
            self.socket.close()
        except OSError:
            pass