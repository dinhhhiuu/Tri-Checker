# APPLY MOVE
def apply_move(board, path):
    ''' 
        Áp dụng nước đi path lên board. \n
        Path là list các vị trí (row, col) mà quân sẽ đi qua, bao gồm cả vị trí đầu và cuối. \n
        Hàm này sẽ di chuyển quân từ vị trí đầu đến vị trí cuối, 
        đồng thời xử lý việc ăn quân nếu có nhảy qua.
        \n
        => Thay đổi trực tiếp board được truyền vào, không trả về gì.
    '''
    piece = board.board[path[0][0]][path[0][1]]

    # xóa quân ở vị trí đầu
    board.board[path[0][0]][path[0][1]] = 0

    for i in range(1, len(path)):
        prev_r, prev_c = path[i - 1]
        curr_r, curr_c = path[i]

        # nếu là jump (nhảy 2 ô)
        if abs(curr_r - prev_r) == 2 or abs(curr_c - prev_c) == 2:
            mid_r = (prev_r + curr_r) // 2
            mid_c = (prev_c + curr_c) // 2

            mid_piece = board.board[mid_r][mid_c]

            # nếu là quân địch -> ăn
            if mid_piece != 0 and mid_piece != piece:
                board.board[mid_r][mid_c] = 0

    # đặt quân ở vị trí cuối
    end_r, end_c = path[-1]
    board.board[end_r][end_c] = piece