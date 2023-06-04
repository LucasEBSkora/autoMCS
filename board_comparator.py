from numpy import int8
from chess import Board

def boardPiecePositionsIdentical(first, second):
  first_board_fen_positions = _getBoardFenPositions(first)
  second_board_fen_positions = _getBoardFenPositions(second)

  return first_board_fen_positions == second_board_fen_positions

def _getBoardFenPositions(board) -> str:
  if board is Board:
    return _getChessBoardFenPositions(board)
  elif board is int8:
    return _getReaderBoardFenPositions(board)

def _getChessBoardFenPositions(board: Board) -> str:
  return board.fen().split(' ')[0]

_piece_chars = {
		4: 'P',
		5: 'R',
		6: 'N',
		7: 'B',
		8: 'K',
		9: 'Q',
		10: 'p',
		11: 'r',
		12: 'n',
		13: 'b',
		14: 'k',
		15: 'q',
}

def _getReaderBoardFenPositions(board: int8) -> str:
  board_fen = ""
  for rank in range(board.shape[0]):
    consecutive_empty_positions = 0
    for file in range(2, board.shape[1] - 2):
      id = board[rank][file]
      if id == 0:
        consecutive_empty_positions += 1
        continue
      elif consecutive_empty_positions > 0:
        board_fen += str(consecutive_empty_positions)
        consecutive_empty_positions = 0

      board_fen += _piece_chars[id]
    if consecutive_empty_positions > 0:
        board_fen += str(consecutive_empty_positions)
    if rank < 7:
      board_fen += "/"

  return board_fen
