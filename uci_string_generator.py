import chess
from numpy import int8


class UCIStringGenerator:
	piece_types = {
		4: chess.PAWN,
		5: chess.ROOK,
		6: chess.KNIGHT,
		7: chess.BISHOP,
		8: chess.KING,
		9: chess.QUEEN,
		10: chess.PAWN,
		11: chess.ROOK,
		12: chess.KNIGHT,
		13: chess.BISHOP,
		14: chess.KING,
		15: chess.QUEEN,
  }

	def __init__(self, initial_board=None):
		if (not initial_board is None) and  type(initial_board) != chess.Board:
			initial_board = self._convertToChessModuleBoard(initial_board)
		self.last_board = initial_board

	def getUCIPossibleMove(self, current_board, possible_moves):
		if possible_moves is None or len(possible_moves) == 0:
			return []
		self.current_board = self._convertToChessModuleBoard(current_board)
		possible_moves = self._convertPossibleMoves(possible_moves)
		if not self.last_board is None:
			possible_moves = self._filterMoveConvertLastToCurrentBoard(possible_moves)
		self.last_board = self.current_board

		possible_moves_uci = self._convertMovesToUCI(possible_moves)

		return possible_moves_uci

	def _getChessPieceChar(self, id):
		char = chess.piece_symbol(self._getChessModulePieceType(id))

		if self._pieceIsBlack(id):
			char = char.upper()
		return char

	def _convertToChessModuleBoard(self, board):
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

				board_fen += self._getChessPieceChar(id)
			if consecutive_empty_positions > 0:
					board_fen += str(consecutive_empty_positions)
			if rank < 7:
				board_fen += "/"

		return chess.Board(board_fen)

	def _filterMoveConvertLastToCurrentBoard(self, board, moves):
		return moves

	def _convertMovesToUCI(self, moves):
		possible_moves_uci = []
		for move in moves:
			possible_moves_uci.append(move.uci())
		return possible_moves_uci

	def _convertPossibleMoves(self, moves):
		uci_moves = []
		# uci_moves.append(self._convertPossibleTwoPieceMoves(moves))
		uci_moves += self._convertPossibleOnePieceMoves(moves)
		return uci_moves

	# One piece moves are moves that can be described by one piece only, that is, en passants and simple movements without promotions,
	#  captured pieces, or castlings
	# en passants are one piece moves because in this logic because the movement of the capturing pawn is enough to understand what happened.
	def _convertPossibleOnePieceMoves(self, moves):
		one_piece_moves = []
		for move in moves:
			if self._partOfMoveOutOfBoard(move):
				continue
			one_piece_moves.append(self._generateUCIFromMove(move[1], move[2]))
		return one_piece_moves

	def _partOfMoveOutOfBoard(self, move):
		return self._coordinatesOutOfBoard(move[1]) or self._coordinatesOutOfBoard(move[2])

	def _generateUCIFromMove(self, origin, destination, promotion_type=None):
		origin = self._getSquare(origin)
		destination = self._getSquare(destination)
		move = chess.Move(origin, destination, promotion=promotion_type)
		# try:
		# 	move = self.current_board.find_move(origin, destination, promotion=promotion_type)
		# except chess.IllegalMoveError:
		# 	move = None
		return move

	# Two piece moves are promotions, captures (that aren't en passant), and castlings.
	# These moves have one thing in common: two pieces move, and the origin point of one is the destination of the other.
	def _convertPossibleTwoPieceMoves(self, moves):
		two_piece_moves = []
		n_moves = len(moves)
		for i in range(n_moves):
			move_i = moves[i]
			if self._movementHappenedOutOfBoard(move_i):
				continue

			for j in range(i, n_moves):
				move_j = moves[j]
				if self._movementHappenedOutOfBoard(move_j):
					continue

				two_piece_move = self._tryCreateTwoPieceMove(move_i, move_j)
				if not two_piece_move is None:
					two_piece_moves.append(two_piece_move)

			return two_piece_moves

	def _tryCreateTwoPieceMove(self, first, second):
		capture = self._tryCreateCaptureMove(first, second)
		if not capture is None:
			return capture

		promotion = self._tryCreatePromotionMove(first, second)
		if not promotion is None:
			return promotion

		castling = self._tryCreateCastlingMove(first, second)
		if not castling is None:
			return castling

	# A capture involves one piece moving to the position of another, which is of the opposite color and moves to out of board
	# en passants are handled as one piece moves.
	def _tryCreateCaptureMove(self, first, second):
		if self._piecesAreOfSameColor(first[0], second[0]):
			return None

		capturing = None
		captured = None

		if first[2] == second[1] and self._coordinatesOutOfBoard(second[2]):
			capturing = first
		elif second[2] == first[1] and self._coordinatesOutOfBoard(first[2]):
			capturing = second
		else:
			return None

		return self._generateUCIFromMove(capturing[1], capturing[2])

	def _piecesAreOfSameColor(self, first_piece_id, second_piece_id):
		if self._pieceIsWhite(first_piece_id):
			return self._pieceIsWhite(second_piece_id)
		else:
			return self._pieceIsBlack(second_piece_id)

	def _pieceIsWhite(self, id):
		return 4 <= id and id <= 9

	def _pieceIsBlack(self, id):
		return 10 <= id and id <= 15

	# A capture involves one pawn moving from board to graveyard and another piece of the same color (that isn't a king or pawn) moving to the
	# last rank and to the same file as the original pawn
	def _tryCreatePromotionMove(self, first, second):
		if not self._piecesAreOfSameColor(first[0], second[0]):
			return None

		pawn = None
		promoted = None

		if self._isPawn(first) and self._isValidPromotionPieceType(second):
			pawn = first
			promoted = second
		elif self._isPawn(second) and self._isValidPromotionPieceType(first):
			pawn = second
			promoted = first
		else:
			return None

		promotion_type = self._getChessModulePieceType(promoted[0])

		return self._generateUCIFromMove(pawn[1], promoted[2], promotion_type)

	def _isPawn(self, move):
		id = move[0]
		return id == 4 or id == 10

	def _isKing(self, move):
		id = move[0]
		return id == 8 or id == 14

	def _isValidPromotionPieceType(self, move):
		return not (self._isPawn(move) or self._isKing(move))

	def _getChessModulePieceType(self, id):
		return UCIStringGenerator.piece_types[id]

	def _movementHappenedOutOfBoard(self, move):
		return self._coordinatesOutOfBoard(move[1]) and self._coordinatesOutOfBoard(move[2])

	def _coordinatesOutOfBoard(self, coordinates):
		(rank, file) = coordinates
		# graveyard files are out of board
		return (not rank in range(0, 8)) or (not file in range(2, 10))

	def _getSquare(self, coordinates):
		return chess.parse_square(self._getSquareName(coordinates))

	ascii_a = ord('a')

	def _getSquareName(self, coordinates):
		(rank, file) = coordinates
		return chr(UCIStringGenerator.ascii_a + file - 2) + str(rank)
