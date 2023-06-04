import chess

def convertUCIPossibleMoves(possible_moves: list[tuple]) -> list[str]:
	if possible_moves is None or len(possible_moves) == 0:
		return []
	
	moves = _convertPossibleMoves(moves)
	possible_moves_uci = [move.uci() for move in moves]
	return possible_moves_uci

def _convertPossibleMoves(moves):
	uci_moves = _convertPossibleTwoPieceMoves(moves)
	uci_moves += _convertPossibleOnePieceMoves(moves)
	return uci_moves

# One piece moves are moves that can be described by one piece only, that is, en passants and simple movements without promotions,
#  captured pieces, or castlings
# en passants are one piece moves because in this logic because the movement of the capturing pawn is enough to understand what happened.
def _convertPossibleOnePieceMoves(moves):
	one_piece_moves = []
	for move in moves:
		if _partOfMoveOutOfBoard(move):
			continue
		one_piece_moves.append(_generateUCIFromMove(move[1], move[2]))
	return one_piece_moves

def _partOfMoveOutOfBoard(move):
	return _coordinatesOutOfBoard(move[1]) or _coordinatesOutOfBoard(move[2])

def _generateUCIFromMove(origin, destination, promotion_type=None):
	origin = _getSquare(origin)
	destination = _getSquare(destination)
	move = chess.Move(origin, destination, promotion=promotion_type)
	return move

# Two piece moves are promotions, captures (that aren't en passant), and castlings.
# These moves have one thing in common: two pieces move, and the origin point of one is the destination of the other.
def _convertPossibleTwoPieceMoves(moves):
	two_piece_moves = []
	n_moves = len(moves)
	if n_moves < 2:
		return []
	i = 0
	while i < n_moves:
		move_i = moves[i]
		if _movementHappenedOutOfBoard(move_i):
			i += 1
			continue
			
		j = i + 1

		found_move_with_piece = False
		
		while j < n_moves:
			move_j = moves[j]
			if _movementHappenedOutOfBoard(move_j):
				continue

			two_piece_move = _tryCreateTwoPieceMove(move_i, move_j)
			if not two_piece_move is None:
				two_piece_moves.append(two_piece_move)
				moves.remove(move_i)
				moves.remove(move_j)
				n_moves -= 2
				found_move_with_piece = True
				break
			j += 1
		if not found_move_with_piece:
			i += 1
	
	return two_piece_moves

def _tryCreateTwoPieceMove(first, second):
	capture = _tryCreateCaptureMove(first, second)
	if not capture is None:
		return capture

	promotion = _tryCreatePromotionMove(first, second)
	if not promotion is None:
		return promotion

	castling = _tryCreateCastlingMove(first, second)
	if not castling is None:
		return castling

	return None

# A capture involves one piece moving to the position of another, which is of the opposite color and moves to out of board
# en passants are handled as one piece moves.
def _tryCreateCaptureMove(first, second):
	if _piecesAreOfSameColor(first[0], second[0]):
		return None

	capturing = None
	captured = None

	if first[2] == second[1] and _coordinatesOutOfBoard(second[2]):
		capturing = first
	elif second[2] == first[1] and _coordinatesOutOfBoard(first[2]):
		capturing = second
	else:
		return None

	return _generateUCIFromMove(capturing[1], capturing[2])

# A capture involves one pawn moving from board to graveyard and another piece of the same color (that isn't a king or pawn) moving to the
# last rank and to the same file as the original pawn
def _tryCreatePromotionMove(first, second):
	if not _piecesAreOfSameColor(first[0], second[0]):
		return None

	pawn = None
	promoted = None

	if _isPawn(first) and _isValidPromotionPieceType(second):
		pawn = first
		promoted = second
	elif _isPawn(second) and _isValidPromotionPieceType(first):
		pawn = second
		promoted = first
	else:
		return None

	promotion_type = _getChessModulePieceType(promoted[0])

	return _generateUCIFromMove(pawn[1], promoted[2], promotion_type)

# A castling move involves one king and rook of the same color moving along the same rank
# last rank and to the same file as the original pawn
def _tryCreateCastlingMove(first, second):
	if not _piecesAreOfSameColor(first[0], second[0]):
		return None

	king = None
	rook = None

	if _isKing(first) and _isRook(second):
		king = first
		rook = second
	elif _isKing(second) and _isRook(first):
		king = second
		rook = first
	else:
		return None
	
	if not _moveIsCastling(king, rook):
		return None
	
	return _generateUCIFromMove(king[1], king[2])

def _moveIsCastling(king, rook):
	if not _areKingAndRookInCorrectRankForCastling(king, rook):
		return False 

	if not _kingInStartingFile(king):
		return False

	return _isKingSideCastling(king, rook) or _isQueenSideCastling(king, rook)

def _areKingAndRookInCorrectRankForCastling(king, rook):
	if _pieceIsWhite(king[0]):
		expected_rank = 0
	else: 
		expected_rank = 7

	return king[1][0] == expected_rank and king[2][0] == expected_rank and rook[1][0] == expected_rank and rook[2][0] == expected_rank
	
def _kingInStartingFile(king):
	return king[1][1] == 6

def _isKingSideCastling(king, rook):
	return rook[1][1] == 9 and rook[2][1] == 7 and king[2][1] == 8

def _isQueenSideCastling(king, rook):
	return rook[1][1] == 2 and rook[2][1] == 5 and king[2][1] == 4

def _piecesAreOfSameColor(first_piece_id, second_piece_id):
	if _pieceIsWhite(first_piece_id):
		return _pieceIsWhite(second_piece_id)
	else:
		return _pieceIsBlack(second_piece_id)

def _pieceIsWhite(id):
	return 4 <= id and id <= 9

def _pieceIsBlack(id):
	return 10 <= id and id <= 15

def _isPawn(move):
	id = move[0]
	return id == 4 or id == 10

def _isKing(move):
	id = move[0]
	return id == 8 or id == 14

def _isRook(move):
	id = move[0]
	return id == 5 or id == 11

def _isValidPromotionPieceType(move):
	return not (_isPawn(move) or _isKing(move))

_piece_types = {
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

def _getChessModulePieceType(id):
	return _piece_types[id]

def _movementHappenedOutOfBoard(move):
	return _coordinatesOutOfBoard(move[1]) and _coordinatesOutOfBoard(move[2])

def _coordinatesOutOfBoard(coordinates):
	(rank, file) = coordinates
	# graveyard files are out of board
	return (not rank in range(0, 8)) or (not file in range(2, 10))

def _getSquare(coordinates):
	return chess.parse_square(_getSquareName(coordinates))

ascii_code_for_lowercase_a = ord('a')

def _getSquareName(coordinates):
	(rank, file) = coordinates
	return chr(ascii_code_for_lowercase_a + file - 2) + str(rank + 1)
