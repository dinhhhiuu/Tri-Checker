directions = [
    (-1, -1),
    (-1, 0),
    (0, -1),
    (0, 1),
    (1, 0),
    (1, 1)
]

class TriangleBoard:
    def __init__(self, size = 10):
        self.size = size

        # Tạo board tam giác [[0], [0, 0], [0, 0, 0], ...]
        self.board = [
            [0 for _ in range(r + 1)]
            for r in range(size)
        ]

    # SET PIECE
    def _set_piece(self, row, col, piece):
        if self._is_valid_position(row, col):
            self.board[row][col] = piece

    # GET PIECE
    def _get_piece(self, row, col):
        if self._is_valid_position(row, col):
            return self.board[row][col]
        return None

    # CHECK VALID POSITION
    def _is_valid_position(self, row, col):
        return 0 <= row < self.size and 0 <= col <= row
    
    # CHECK EMPTY POSITION
    def _is_empty_position(self, row, col):
        if not self._is_valid_position(row, col):
            return False
        return self._get_piece(row, col) == 0

    # CHECK JUMP POSITIONS
    def _get_jump_paths(self, row, col, path=None, visited=None):
        if path is None:
            path = [(row, col)]
        if visited is None:
            visited = set()

        all_paths = []
        has_jump = False

        for dr, dc in directions:
            mid_r, mid_c = row + dr, col + dc
            jump_r, jump_c = row + 2*dr, col + 2*dc

            # check hợp lệ
            if not self._is_valid_position(mid_r, mid_c):
                continue
            if not self._is_valid_position(jump_r, jump_c):
                continue

            # phải có quân ở giữa
            if self._is_empty_position(mid_r, mid_c):
                continue

            # ô đích phải trống
            if not self._is_empty_position(jump_r, jump_c):
                continue

            if (jump_r, jump_c) in visited:
                continue

            has_jump = True

            new_path = path + [(jump_r, jump_c)]
            new_visited = visited | {(jump_r, jump_c)}

            # tiếp tục nhảy
            sub_paths = self._get_jump_paths(jump_r, jump_c, new_path, new_visited)

            if sub_paths:
                all_paths.extend(sub_paths)
            else:
                all_paths.append(new_path)

        # nếu không nhảy thêm được nữa
        if not has_jump and len(path) > 1:
            return [path]

        return all_paths

    # CHECK NORMAL MOVES
    def _get_normal_moves(self, row, col):
        normal_moves = []

        for dr, dc in directions:
            nr, nc = row + dr, col + dc
            if self._is_valid_position(nr, nc) and self._is_empty_position(nr, nc):
                normal_moves.append((nr, nc))

        return normal_moves
    
    # GET ALL MOVES (JUMP + NORMAL)
    def get_all_moves(self, row, col):
        jump_moves = self._get_jump_paths(row, col)
        normal_moves = self._get_normal_moves(row, col)

        normal_paths = [
            [(row, col), (nr, nc)]
            for (nr, nc) in normal_moves
        ]

        return jump_moves + normal_paths

    # GET BOARD
    def get_board(self):
        print("Getting board" + str(self.board) + "\n")
        return self.board
    
    # GET ALL PIECES FOR A PLAYER
    def get_all_pieces(self, player):
        res = []
        for r in range(self.size):
            for c in range(r + 1):
                if self.board[r][c] == player:
                    res.append((r, c))
        print("Getting all pieces for player " + str(player) + ": " + str(res) + "\n")
        return res
    
    # PRINT BOARD
    def print_board(self):
        for r in range(self.size):
            print(' ' * (self.size - r - 1), end='')  # In khoảng trắng để tạo hình tam giác
            for c in range(r + 1):
                piece = self.board[r][c]
                if piece == 0:
                    print('.', end=' ')
                elif piece == 1:
                    print('1', end=' ')
                elif piece == 2:
                    print('2', end=' ')
                elif piece == 3:
                    print('3', end=' ')
            print()