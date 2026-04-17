import argparse
import json
import os
import random
import socket
import string
import threading
from dataclasses import dataclass, field

from src.ai.minimax_ai import choose_minimax_move
from src.ai.mcts_ai import choose_mcts_move
from src.ai.ml_ai import choose_ml_move
from src.ai.random_ai import choose_random_move
from src.core.board import TriangleBoard
from src.core.move import apply_move
from src.core.utils import init_players, is_valid_move_for_player, next_player
from src.network.session import DEFAULT_PORT, deserialize_path, serialize_path

AI_MODES = ("random", "minimax", "mcts", "ml")


def _random_room_id(length: int = 6) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


@dataclass
class ConnectedClient:
    conn_id: int
    sock: socket.socket
    address: tuple[str, int]
    buffer: str = ""
    send_lock: threading.Lock = field(default_factory=threading.Lock)
    room: "GameRoom | None" = None
    player_id: int | None = None


class GameRoom:
    """Manages a 2 or 3-player match. ai_slots maps player_id -> AI mode."""

    def __init__(self, room_id: str, lobby: "LobbyServer", max_players: int = 2,
                 ai_slots: dict[int, str] | None = None) -> None:
        self.room_id = room_id
        self.lobby = lobby
        self.max_players = max(2, min(3, max_players))
        self.active_players = list(range(1, self.max_players + 1))
        # ai_slots: {player_id: "random"|"minimax"}
        self.ai_slots: dict[int, str] = {}
        if ai_slots:
            for pid, mode in ai_slots.items():
                if mode in AI_MODES:
                    self.ai_slots[int(pid)] = mode
        self.board = TriangleBoard()
        self.turn = 1
        self.winner = None
        self.game_over = False
        self.last_move_path = None
        self.last_move_player = None
        self.clients: dict[int, ConnectedClient] = {}
        self.lock = threading.Lock()
        self._reset_board()

    def _reset_board(self) -> None:
        self.board = TriangleBoard()
        init_players(self.board, self.active_players)
        self.turn = self.active_players[0]
        self.winner = None
        self.game_over = False
        self.last_move_path = None
        self.last_move_player = None

    def is_full(self) -> bool:
        # AI slots count as filled without a real client
        human_slots = self.max_players - len(self.ai_slots)
        return len(self.clients) >= human_slots

    def player_count(self) -> int:
        return len(self.clients)

    def _human_count_needed(self) -> int:
        return self.max_players - len(self.ai_slots)

    def _available_player_id(self) -> int | None:
        for pid in self.active_players:
            if pid not in self.clients and pid not in self.ai_slots:
                return pid
        return None

    def _build_state(self, status_text: str | None = None) -> dict:
        payload = {
            "type": "state",
            "board_size": int(self.board.size),
            "board": self.board.board,
            "turn": int(self.turn),
            "winner": self.winner,
            "game_over": self.game_over,
            "active_players": list(self.active_players),
            "match_ready": len(self.clients) == self._human_count_needed(),
            "connected_players": sorted(self.clients),
            "last_move_path": serialize_path(self.last_move_path) if self.last_move_path else [],
            "last_move_player": self.last_move_player,
            "room_id": self.room_id,
            "max_players": self.max_players,
            "ai_slots": {str(k): v for k, v in self.ai_slots.items()},
        }
        if status_text:
            payload["status_text"] = status_text
        return payload

    def _send(self, client: ConnectedClient, payload: dict) -> bool:
        message = (json.dumps(payload) + "\n").encode("utf-8")
        try:
            with client.send_lock:
                client.sock.sendall(message)
            return True
        except OSError:
            return False

    def _broadcast(self, payload: dict) -> None:
        for client in list(self.clients.values()):
            self._send(client, payload)

    def add_client(self, client: ConnectedClient) -> bool:
        with self.lock:
            pid = self._available_player_id()
            if pid is None:
                return False
            client.player_id = pid
            client.room = self
            self.clients[pid] = client
            if len(self.clients) == self._human_count_needed():
                self._reset_board()
                status = "Match started!"
            else:
                remaining = self._human_count_needed() - len(self.clients)
                status = f"Waiting for {remaining} more player{'s' if remaining > 1 else ''}..."
            state = self._build_state(status_text=status)
        self._send(client, {
            "type": "welcome",
            "player_id": pid,
            "room_id": self.room_id,
            "message": f"Joined room {self.room_id} as Player {pid}",
        })
        self._broadcast(state)
        return True

    def remove_client(self, player_id: int) -> None:
        with self.lock:
            client = self.clients.pop(player_id, None)
            if client is None:
                return
            client.room = None
            client.player_id = None
            self._reset_board()
            payload = self._build_state(status_text="Opponent disconnected. Waiting for another player...") if self.clients else None
        if payload is not None:
            self._broadcast(payload)
        self.lobby._broadcast_lobby()

    def _run_ai_turns_async(self) -> None:
        """Run AI turns in a background thread, broadcasting after each move."""
        while True:
            with self.lock:
                if self.game_over or self.turn not in self.ai_slots:
                    break
                mode = self.ai_slots[self.turn]
                pid = self.turn
                board_snapshot = self.board  # shared reference, read under lock ok

            # Compute move OUTSIDE lock so server stays responsive
            if mode == "minimax":
                move = choose_minimax_move(board_snapshot, pid, mode="minimax", depth=2)
            elif mode == "mcts":
                move = choose_mcts_move(board_snapshot, pid, mode="mcts")
            elif mode == "ml":
                move = choose_ml_move(board_snapshot, pid)
            else:
                move = choose_random_move(board_snapshot, pid, mode="random")

            with self.lock:
                # Re-check: turn may have changed if another thread acted
                if self.game_over or self.turn != pid or pid not in self.ai_slots:
                    break
                if not move:
                    # AI has no valid moves (pieces all captured) — skip turn
                    self.turn = next_player(self.turn, self.active_players)
                    state = self._build_state()
                else:
                    apply_move(self.board, move)
                    self.last_move_path = move
                    self.last_move_player = pid
                    self.winner = self.board.check_winner()
                    self.game_over = self.winner is not None
                    if not self.game_over:
                        self.turn = next_player(self.turn, self.active_players)
                    state = self._build_state()

            self._broadcast(state)

    def _run_ai_turns(self) -> None:
        """Run AI moves while current turn belongs to an AI slot."""
        while not self.game_over and self.turn in self.ai_slots:
            mode = self.ai_slots[self.turn]
            pid = self.turn
            if mode == "minimax":
                move = choose_minimax_move(self.board, pid, mode="minimax", depth=2)
            elif mode == "mcts":
                move = choose_mcts_move(self.board, pid, mode="mcts")
            elif mode == "ml":
                move = choose_ml_move(self.board, pid)
            else:
                move = choose_random_move(self.board, pid, mode="random")
            if not move:
                # No valid moves — skip this AI player's turn
                self.turn = next_player(self.turn, self.active_players)
                continue
            apply_move(self.board, move)
            self.last_move_path = move
            self.last_move_player = pid
            self.winner = self.board.check_winner()
            self.game_over = self.winner is not None
            if not self.game_over:
                self.turn = next_player(self.turn, self.active_players)

    def _handle_move(self, player_id: int, payload: dict) -> None:
        with self.lock:
            client = self.clients.get(player_id)
            if client is None:
                return
            if len(self.clients) < self._human_count_needed():
                resp = {"type": "error", "message": "Waiting for another player."}
                state = None
            elif self.game_over:
                resp = {"type": "error", "message": "Game over. Restart to play again."}
                state = None
            elif player_id != self.turn:
                resp = {"type": "error", "message": "Not your turn."}
                state = None
            else:
                path = deserialize_path(payload.get("path", []))
                if not is_valid_move_for_player(self.board, player_id, path):
                    resp = {"type": "error", "message": "Invalid move."}
                    state = None
                else:
                    apply_move(self.board, path)
                    self.last_move_path = path
                    self.last_move_player = player_id
                    self.winner = self.board.check_winner()
                    self.game_over = self.winner is not None
                    if not self.game_over:
                        self.turn = next_player(self.turn, self.active_players)
                    resp = None
                    state = self._build_state()
        if resp is not None:
            self._send(client, resp)
        elif state is not None:
            self._broadcast(state)
            # Run AI turns in background thread (non-blocking)
            if not self.game_over and self.turn in self.ai_slots:
                threading.Thread(target=self._run_ai_turns_async, daemon=True).start()

    def _handle_restart(self, player_id: int) -> None:
        with self.lock:
            if player_id not in self.clients:
                return
            self._reset_board()
            state = self._build_state(status_text=f"Player {player_id} restarted the match")
        self._broadcast(state)

    def handle_payload(self, player_id: int, payload: dict) -> None:
        t = payload.get("type")
        if t == "move":
            self._handle_move(player_id, payload)
        elif t == "restart":
            self._handle_restart(player_id)


class LobbyServer:
    """Central server: manages rooms so multiple pairs can play simultaneously.
    Clients first arrive in the lobby, then create or join a room.
    """

    def __init__(self, host: str = "0.0.0.0", port: int = DEFAULT_PORT) -> None:
        self.host = host
        self.port = port
        self.rooms: dict[str, GameRoom] = {}
        self.connections: dict[int, ConnectedClient] = {}
        self._next_conn_id = 0
        self.lock = threading.Lock()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((host, port))
        self.server_socket.listen(50)
        self.server_socket.settimeout(0.5)
        self.running = True

    def _new_room_id(self) -> str:
        while True:
            rid = _random_room_id()
            if rid not in self.rooms:
                return rid

    def _lobby_payload(self) -> dict:
        with self.lock:
            rooms = [
                {
                    "room_id": rid,
                    "players": room.player_count(),
                    "max_players": room.max_players,
                    "ai_slots": {str(k): v for k, v in room.ai_slots.items()},
                }
                for rid, room in self.rooms.items()
                if room.player_count() > 0
            ]
        return {"type": "lobby", "rooms": rooms}

    def _send_to(self, client: ConnectedClient, payload: dict) -> None:
        message = (json.dumps(payload) + "\n").encode("utf-8")
        try:
            with client.send_lock:
                client.sock.sendall(message)
        except OSError:
            pass

    def _broadcast_lobby(self) -> None:
        """Push updated room list to all clients currently in the lobby."""
        payload = self._lobby_payload()
        with self.lock:
            lobby_clients = [c for c in self.connections.values() if c.room is None]
        for client in lobby_clients:
            self._send_to(client, payload)

    def _handle_create_room(self, client: ConnectedClient, max_players: int = 2,
                             ai_slots: dict | None = None) -> None:
        max_players = max(2, min(3, max_players))
        with self.lock:
            rid = self._new_room_id()
            room = GameRoom(rid, self, max_players=max_players, ai_slots=ai_slots)
            self.rooms[rid] = room
        if not room.add_client(client):
            self._send_to(client, {"type": "error", "message": "Could not create room."})
        else:
            self._broadcast_lobby()

    def _handle_join_room(self, client: ConnectedClient, room_id: str) -> None:
        room_id = room_id.upper().strip()
        with self.lock:
            room = self.rooms.get(room_id)
        if room is None:
            self._send_to(client, {"type": "error", "message": f"Room '{room_id}' not found."})
            return
        if room.is_full():
            self._send_to(client, {"type": "error", "message": f"Room '{room_id}' is full."})
            return
        if not room.add_client(client):
            self._send_to(client, {"type": "error", "message": f"Could not join room '{room_id}'."})
        else:
            self._broadcast_lobby()

    def _cleanup_empty_rooms(self) -> None:
        with self.lock:
            empty = [rid for rid, room in self.rooms.items() if room.player_count() == 0]
            for rid in empty:
                del self.rooms[rid]

    def _handle_lobby_message(self, client: ConnectedClient, payload: dict) -> None:
        t = payload.get("type")
        if t == "create_room":
            raw_ai = payload.get("ai_slots", {})
            ai_slots = {int(k): v for k, v in raw_ai.items() if v in AI_MODES} if isinstance(raw_ai, dict) else {}
            self._handle_create_room(client,
                max_players=int(payload.get("max_players", 2)),
                ai_slots=ai_slots or None)
        elif t == "join_room":
            self._handle_join_room(client, str(payload.get("room_id", "")))
        elif t == "get_lobby":
            self._send_to(client, self._lobby_payload())

    def _client_loop(self, client: ConnectedClient) -> None:
        while self.running:
            try:
                chunk = client.sock.recv(4096)
            except socket.timeout:
                continue
            except OSError:
                break
            if not chunk:
                break
            client.buffer += chunk.decode("utf-8")
            while "\n" in client.buffer:
                line, client.buffer = client.buffer.split("\n", 1)
                if not line.strip():
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if client.room is not None and client.player_id is not None:
                    client.room.handle_payload(client.player_id, payload)
                else:
                    self._handle_lobby_message(client, payload)

        if client.room is not None and client.player_id is not None:
            client.room.remove_client(client.player_id)
        with self.lock:
            self.connections.pop(client.conn_id, None)
        self._cleanup_empty_rooms()
        self._broadcast_lobby()

    def _register_client(self, sock: socket.socket, address: tuple[str, int]) -> None:
        with self.lock:
            conn_id = self._next_conn_id
            self._next_conn_id += 1
            sock.settimeout(0.5)
            client = ConnectedClient(conn_id=conn_id, sock=sock, address=address)
            self.connections[conn_id] = client
        self._send_to(client, self._lobby_payload())
        threading.Thread(target=self._client_loop, args=(client,), daemon=True).start()

    def serve_forever(self) -> None:
        print(f"[Tri-Checker] Lobby server listening on {self.host}:{self.port}")
        print("[Tri-Checker] Waiting for players...")
        try:
            while self.running:
                try:
                    sock, address = self.server_socket.accept()
                    print(f"[Tri-Checker] New connection from {address[0]}:{address[1]}")
                except socket.timeout:
                    continue
                except OSError:
                    break
                self._register_client(sock, address)
        except KeyboardInterrupt:
            print("\n[Tri-Checker] Stopping server...")
        finally:
            self.close()

    def close(self) -> None:
        self.running = False
        try:
            self.server_socket.close()
        except OSError:
            pass


# Backward-compatibility alias
DedicatedGameServer = LobbyServer


def main() -> None:
    parser = argparse.ArgumentParser(description="Tri-Checker lobby server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", str(DEFAULT_PORT))))
    args = parser.parse_args()

    server = LobbyServer(host=args.host, port=args.port)
    server.serve_forever()


if __name__ == "__main__":
    main()