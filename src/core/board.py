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
        '''
            [
                [0],
                [0, 0],
                [0, 0, 0],
                ...
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
             ]
        '''
        self.size = size

        # Tạo board tam giác [[0], [0, 0], [0, 0, 0], ...]
        self.board = [
            [0 for _ in range(r + 1)]
            for r in range(size)
        ]

    # SET PIECE
    def _set_piece(self, row, col, piece):
        '''Đặt piece (0: trống, 1: player 1, 2: player 2, 3: player 3) vào vị trí (row, col)'''
        if self._is_valid_position(row, col):
            self.board[row][col] = piece

    # GET PIECE
    def _get_piece(self, row, col):
        '''Lấy piece ở vị trí (row, col)'''
        if self._is_valid_position(row, col):
            return self.board[row][col]
        return None

    # CHECK VALID POSITION
    def _is_valid_position(self, row, col):
        '''Kiểm tra xem (row, col) có nằm trong board tam giác hay không'''
        return 0 <= row < self.size and 0 <= col <= row
    
    # CHECK EMPTY POSITION
    def _is_empty_position(self, row, col):
        '''Kiểm tra xem (row, col) có trống hay không'''
        if not self._is_valid_position(row, col):
            return False
        return self._get_piece(row, col) == 0

    # CHECK JUMP POSITIONS
    def _get_jump_paths(self, row, col, path=None, visited=None):
        '''Đệ quy tìm tất cả đường nhảy hợp lệ từ vị trí (row, col)'''
        if path is None:
            path = [(row, col)]
        if visited is None:
            visited = set()

        all_paths = []

        for dr, dc in directions:
            mid_r, mid_c = row + dr, col + dc
            jump_r, jump_c = row + 2*dr, col + 2*dc

            if not self._is_valid_position(mid_r, mid_c):
                continue
            if not self._is_valid_position(jump_r, jump_c):
                continue
            if self._is_empty_position(mid_r, mid_c):
                continue
            if not self._is_empty_position(jump_r, jump_c):
                continue
            if (jump_r, jump_c) in visited:
                continue

            new_path = path + [(jump_r, jump_c)]
            new_visited = visited | {(jump_r, jump_c)}

            # Cho phép dừng tại điểm này
            all_paths.append(new_path)

            # Tiếp tục nhảy thêm từ điểm này
            sub_paths = self._get_jump_paths(jump_r, jump_c, new_path, new_visited)
            all_paths.extend(sub_paths)

        return all_paths

    # CHECK NORMAL MOVES
    def _get_normal_moves(self, row, col):
        '''Tìm tất cả nước đi bình thường (di chuyển 1 ô) từ vị trí (row, col)'''
        normal_moves = []

        for dr, dc in directions:
            nr, nc = row + dr, col + dc
            if self._is_valid_position(nr, nc) and self._is_empty_position(nr, nc):
                normal_moves.append((nr, nc))

        return normal_moves
    
    # GET ALL MOVES (JUMP + NORMAL)
    def get_all_moves(self, row, col):
        '''Tìm tất cả nước đi hợp lệ (bao gồm nhảy và di chuyển bình thường) từ vị trí (row, col)'''
        jump_moves = self._get_jump_paths(row, col)
        normal_moves = self._get_normal_moves(row, col)

        normal_paths = [
            [(row, col), (nr, nc)]
            for (nr, nc) in normal_moves
        ]

        return jump_moves + normal_paths

    # CHECK WINNER
    def check_winner(self):
        '''Kiểm tra xem có người chơi nào thắng chưa (chỉ còn 1 người chơi có quân trên board)'''
        players = [1, 2, 3]

        alive = []

        for p in players:
            if len(self.get_all_pieces(p)) > 0:
                alive.append(p)

        if len(alive) == 1:
            return alive[0]

        return None

    # GET BOARD
    def get_board(self):
        '''Trả về trạng thái hiện tại của board dưới dạng list of lists'''
        print("Getting board" + str(self.board) + "\n")
        return self.board
    
    # GET ALL PIECES FOR A PLAYER
    def get_all_pieces(self, player):
        '''Lấy tất cả vị trí quân của player trên board'''
        res = []
        for r in range(self.size):
            for c in range(r + 1):
                if self.board[r][c] == player:
                    res.append((r, c))
        # print("Getting all pieces for player " + str(player) + ": " + str(res) + "\n")
        return res
    
    # PRINT BOARD
    def print_board(self):    
        for r in range(self.size):
            '''In ra board theo dạng tam giác, dùng '.' cho ô trống, '1' cho quân player 1, '2' cho quân player 2, '3' cho quân player 3'''
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