# -*- coding: utf-8 -*-
"""
Created on Mon Apr 19 08:41:31 2021

@author: Alexander Leszczynski


 
"""
# import numpy as np
import copy
import random
import time


class GameState:
    """
    This class is responsible for storing all the information about the current state of a chess game.
    It is also responsible for determining the valid moves at the current state and also keeps a move log.
    """

    def __init__(self):
        """
        This is the Constructor of the Gamestate class

        Returns
        -------
        None.

        """
        # board is an 6x6 1d list, each piece on the board is represented by 2 letters in the list
        # The first character represents the color of the piece, "b" or "w"
        # The second character represents the type of the piece "K", "Q", "R", "B", "N" or "p"
        # "--" represents an empty space with no piece
        self.board = ['bR', 'bB', 'bN', 'bK', 'bB', 'bR',
                      'bp', 'bp', 'bp', 'bp', 'bp', 'bp',
                      '--', '--', '--', '--', '--', '--',
                      '--', '--', '--', '--', '--', '--',
                      'wp', 'wp', 'wp', 'wp', 'wp', 'wp',
                      'wR', 'wB', 'wN', 'wK', 'wB', 'wR']

        # for testing interesting positions

        self.board = ['bR', '--', '--', '--', '--', '--',
                      '--', '--', 'bK', '--', '--', '--',
                      '--', '--', '--', 'bp', '--', '--',
                      '--', '--', 'bB', 'wp', 'bp', '--',
                      'bp', '--', 'wK', '--', 'wp', '--',
                      'bR', '--', '--', '--', '--', '--']

        # to flip the board:

        for j in range(len(self.board)):
            print('b' in self.board[j])
            if 'b' in self.board[j]:
                self.board[j] = self.board[j].replace('b', 'w')
            elif 'w' in self.board[j]:
                self.board[j] = self.board[j].replace('w', 'b')
        self.board.reverse()
        for j in range(len(self.board) // 6):
            print(self.board[j * 6: (j*6)+5])


        self.moveFunctions = {'p': self.getPawnMoves, 'R': self.getRookMoves, 'N': self.getKnightMoves,
                              'B': self.getBishopMoves, 'K': self.getKingMoves, 'Q': self.getQueenMoves}
        self.whiteToMove = True
        self.dimension = 6
        self.above = - self.dimension
        self.under = self.dimension
        self.left = -1
        self.right = 1
        self.moveLog = []
        self.whiteKingLocation = (5, 3)
        self.blackKingLocation = (0, 3)  # to not have to scan for the king

        self.inCheck = False
        self.pins = []
        self.checks = []

        # self.currentCastlingRight = CastleRights(False, False, False, False) # this has to be in the code when testing positions where castling is not allowed

        self.currentCastlingRight = CastleRights(True, True, True,
                                                 True)  # this has to be commented out when testing positions where castling is not allowed
        self.castleRightsLog = [CastleRights(self.currentCastlingRight.wks, self.currentCastlingRight.bks,
                                             self.currentCastlingRight.wqs, self.currentCastlingRight.bqs)]

        self.checkMate = False
        self.staleMate = False
        self.draw = False
        self.threefold = False
        self.illegal_move_done = False
        self.game_log = {}

    def __str__(self):
        s = copy.deepcopy(self.board)
        r = ''
        for j, ss in enumerate(s):
            if j % 6 == 5:
                r += ss + '\n'
            else:
                r += ss + ' '
        return r

    def makeMove(self, move):

        """
        Makes the move on the board. 

        Parameters
        ----------
        move : Move

        Returns
        -------
        None.

        """

        self.board[move.startRC] = "--"  # Square left behind will be empty
        self.board[move.endRC] = move.pieceMoved
        self.moveLog.append(move)  # log the move so we can undo it later
        self.whiteToMove = not self.whiteToMove  # swap players turn

        # update kings location
        if move.pieceMoved == "wK":
            self.whiteKingLocation = (move.endRow, move.endCol)
        if move.pieceMoved == "bK":
            self.blackKingLocation = (move.endRow, move.endCol)

        # pawn promotion
        if move.isPawnPromotion:  # auto promotion to queen
            # promotedPiece = input("Promote to Q, R, B or N:")
            self.board[move.endRC] = move.pieceMoved[0] + "R"  # promotedPiece

        # make castle move
        if move.pieceMoved[1] == "K" and abs(move.endCol - move.startCol) == 2:
            if move.endCol - move.startCol == 2:  # kingside castle move
                self.board[move.endRC - 1] = move.pieceMoved[0] + "R"  # moves the rook
                self.board[move.endRC] = move.pieceMoved  # deletes old rook
            else:  # queenside castle move
                self.board[move.endRC + 1] = self.board[move.endRC - 1]  # moves the rook
                self.board[move.endRC - 1] = "--"

        # update castling rights - whenever a rook or a king moves
        self.updateCastleRights(move)
        self.castleRightsLog.append(CastleRights(self.currentCastlingRight.wks, self.currentCastlingRight.bks,
                                                 self.currentCastlingRight.wqs, self.currentCastlingRight.bqs))

        # threefold logic
        if tuple(self.board) in self.game_log:
            self.game_log[tuple(self.board)] += 1
            if self.game_log[tuple(self.board)] == 3:
                self.threefold = True
        else:
            self.game_log.update({tuple(self.board): 1})

        # check for draw by insufficient material
        self.draw = not ('bR' in self.board or 'bB' in self.board or 'bN' in self.board or
                         'bp' in self.board or 'bB' in self.board or 'bR' in self.board or
                         'wR' in self.board or 'wB' in self.board or 'wN' in self.board or
                         'wp' in self.board or 'wB' in self.board or 'wR' in self.board)

    def undoMove(self):
        """
        Takes the last move made from the moveLog and undoes it

        Returns
        -------
        None.

        """

        if len(self.moveLog) != 0:  # make sure at least one move has been made to undo
            move = self.moveLog.pop()
            # undo move from GameLog to avoid threefold stacking
            self.game_log[tuple(self.board)] -= 1

            self.board[move.startRC] = move.pieceMoved
            self.board[move.endRC] = move.pieceCaptured
            self.whiteToMove = not self.whiteToMove  # swap players turn

            # update kings location if needed
            if move.pieceMoved == "wK":
                self.whiteKingLocation = (move.startRow, move.startCol)
            if move.pieceMoved == "bK":
                self.blackKingLocation = (move.startRow, move.startCol)

            # undo castling rights
            self.castleRightsLog.pop()  # get rid of the castle rights from the move we are undoing
            castleRights = copy.deepcopy(self.castleRightsLog[-1])
            self.currentCastlingRight = castleRights

            # undo the castle move
            if move.pieceMoved[1] == "K" and abs(move.endCol - move.startCol) == 2:
                if move.endCol - move.startCol == 2:  # kingside
                    self.board[move.endRC] = self.board[move.endRC - 1]  # moves the rook
                    self.board[move.endRC - 1] = "--"  # deletes old rook
                else:  # queenside
                    self.board[move.endRC - 1] = self.board[move.endRC + 1]  # moves the rook
                    self.board[move.endRC + 1] = "--"  # deletes old rook

            # undo checkmate and Stalemate flags
            self.checkMate = False
            self.staleMate = False

    def updateCastleRights(self, move):
        """
        Update the castle rights given the move

        Parameters
        ----------
        move : Move
            Is an instance of Move class

        Returns
        -------
        None.

        """

        if move.pieceMoved == "wK":
            self.currentCastlingRight.wks = False
            self.currentCastlingRight.wqs = False
        elif move.pieceMoved == "bK":
            self.currentCastlingRight.bks = False
            self.currentCastlingRight.bqs = False
        elif move.pieceMoved == "wR":
            if move.startRow == 5:
                if move.startCol == 0:  # left Rook
                    self.currentCastlingRight.wqs = False
                elif move.startCol == 5:  # right Rook
                    self.currentCastlingRight.wks = False
        elif move.pieceMoved == "bR":
            if move.startRow == 0:
                if move.startCol == 0:  # left Rook
                    self.currentCastlingRight.bqs = False
                elif move.startCol == 5:  # right Rook
                    self.currentCastlingRight.bks = False

        # if a rook is captured
        if move.pieceCaptured == 'wR':
            if move.endRow == 5:
                if move.endCol == 0:
                    self.currentCastlingRight.wqs = False
                elif move.endCol == 5:
                    self.currentCastlingRight.wks = False
        elif move.pieceCaptured == 'bR':
            if move.endRow == 0:
                if move.endCol == 0:
                    self.currentCastlingRight.bqs = False
                elif move.endCol == 5:
                    self.currentCastlingRight.bks = False

    def getValidMoves(self):
        """
        All moves considering checks

        Returns
        -------
        list of moves

        """
        moves = []

        self.inCheck, self.pins, self.checks = self.checkForPinsAndChecks()
        if self.whiteToMove:
            kingRow = self.whiteKingLocation[0]
            kingCol = self.whiteKingLocation[1]
        else:
            kingRow = self.blackKingLocation[0]
            kingCol = self.blackKingLocation[1]

        if self.inCheck:
            if len(self.checks) == 1:  # only 1 check, block check or move king
                moves = self.getAllPossibleMoves()
                # to block a check you must move a piece into one of the sqaures between the enemy piece and king
                check = self.checks[0]  # check info
                checkRow = check[0]
                checkCol = check[1]
                checkRC = checkRow * 6 + checkCol
                pieceChecking = self.board[checkRC]  # enemy piece causing the check
                validSquares = []  # squares that pieces can move to
                # if knight, must be captured or move king, other pieces can be blocked
                if pieceChecking[1] == "N":
                    validSquares = [(checkRow, checkCol)]
                else:
                    for i in range(1, 6):
                        validSquare = (kingRow + check[2] * i,
                                       kingCol + check[3] * i)  # check[2] and check[3] are the check directions
                        validSquares.append(validSquare)
                        if validSquare[0] == checkRow and validSquare[
                            1] == checkCol:  # you arrived at  the checking piece
                            break
                # get rid of any moves that don't block check or move king
                for i in range(len(moves) - 1, -1, -1):  # going backwards through the moves
                    if moves[i].pieceMoved[1] != "K":  # move doesn't move king so it must block or capture
                        if not (moves[i].endRow, moves[i].endCol) in validSquares:  # move doesnt block or capture piece
                            moves.remove(moves[i])
            else:  # double check, king has to move
                self.getKingMoves(kingRow, kingCol, moves)
            if len(moves) == 0:
                self.checkMate = True

        else:  # not in check therefore all moves are fine
            moves = self.getAllPossibleMoves()
            self.getCastleMoves(kingRow, kingCol, moves)
        if len(moves) == 0 and not self.checkMate:
            self.staleMate = True

        random.shuffle(moves)

        return moves

    def squareUnderAttack(self, r, c):  # nötig für castle moves
        """
        determines if enemy can attack the square (r, c)

        Parameters
        ----------
        r : int
            Row
        c : int
            Column

        Returns
        -------
        Bool
            True if square is under attack
        """
        self.whiteToMove = not self.whiteToMove  # switch opponents turn
        oppMoves = self.getAllPossibleMoves()
        self.whiteToMove = not self.whiteToMove  # switch turns back

        if (self.whiteToMove and r > 0) or (not self.whiteToMove and r < self.dimension - 1):
            r_offset = -1 if self.whiteToMove else 1
            enemy_color = 'b' if self.whiteToMove else 'w'
            column_offsets = []
            if c < self.dimension - 1: column_offsets.append(1)
            if c > 0: column_offsets.append(-1)
            if any([self.board[self.dimension * (r + r_offset) + (c + c_offset)] == enemy_color + 'p' for c_offset in column_offsets]):
                return True

        for move in oppMoves:
            if move.endRow == r and move.endCol == c:  # square is under attack
                return True
        return False

    def checkForPinsAndChecks(self):
        # TODO: dimension dependent.
        """
        checks for Pins and checks and returns all pins and checks

        Returns
        -------
        Bool,List,List
            if the Player is in check, list of pins and list of checks

        """
        pins = []  # squares where the allied pinned piece is and the direction it is pinned from
        checks = []  # squares where enemy is applying check
        inCheck = False
        if self.whiteToMove:
            enemyColor = "b"
            allyColor = "w"
            startRow = self.whiteKingLocation[0]
            startCol = self.whiteKingLocation[1]
        else:
            enemyColor = "w"
            allyColor = "b"
            startRow = self.blackKingLocation[0]
            startCol = self.blackKingLocation[1]
        # check outward from king for pins and checks, keep track of pins
        directions = ((-1, 0), (0, -1), (1, 0), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1))
        for j in range(len(directions)):
            d = directions[j]
            possiblePin = ()  # reset possible pins
            for i in range(1, self.dimension):
                endRow = startRow + d[0] * i
                endCol = startCol + d[1] * i
                endRC = endRow * 6 + endCol
                if 0 <= endRow < self.dimension and 0 <= endCol < self.dimension:
                    endPiece = self.board[endRC]
                    if endPiece[0] == allyColor and endPiece[1] != "K":
                        if possiblePin == ():  # 1st allied piece could be pinned
                            possiblePin = (endRow, endCol, d[0], d[1])
                        else:  # 2nd allied piece, so no pin or check possible for this direction
                            break
                    elif endPiece[0] == enemyColor:
                        typus = endPiece[1]
                        # 4 possibilities in this condition
                        # 1.) orthogonally away from king and piece is a rook
                        # 2.) diagonally away from king and piece is a bishop
                        # 3.) 1 sqare away diagonally from king and piece is a pawn
                        # 4.) any direction 1 square away and piece is a king (to prevent Kings checking each other)
                        if (0 <= j <= 3 and typus == "R") or \
                                (4 <= j <= 7 and typus == "B") or \
                                (i == 1 and typus == "p" and (
                                        (enemyColor == "w" and 6 <= j <= 7) or (enemyColor == "b" and 4 <= j <= 5))) or \
                                (typus == "Q") or (i == 1 and typus == "K"):
                            if possiblePin == ():  # no piece blocking, so check
                                inCheck = True
                                checks.append((endRow, endCol, d[0], d[1]))
                                break
                            else:  # piece blocking so pin
                                pins.append(possiblePin)
                                break
                        else:  # enemy piece not applying check
                            break
                else:  # off board
                    break
                    # check for knight checks
        knightMoves = ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1))
        for m in knightMoves:
            endRow = startRow + m[0]
            endCol = startCol + m[1]
            endRC = endRow * 6 + endCol
            if 0 <= endRow < self.dimension and 0 <= endCol < self.dimension:
                endPiece = self.board[endRC]
                if endPiece[0] == enemyColor and endPiece[1] == "N":  # enemy knight attacking king
                    inCheck = True
                    checks.append((endRow, endCol, m[0], m[1]))
        return inCheck, pins, checks

    def getAllPossibleMoves(self):
        """
        All moves without considering checks

        Returns
        -------
        list of moves

        """
        # moves = [Move((4,3),(3,3), self.board) ] #just to test if it works so far Many weird bugs because of this was left in
        moves = []
        for r in range(6):  # number of rows on the board
            for c in range(6):  # number of columns in the row r
                rc = r * 6 + c
                turn = self.board[rc][0]
                if (turn == "w" and self.whiteToMove) or (
                        turn == "b" and not self.whiteToMove):  # here the "or" used to be an "and" which i think was wrong
                    piece = self.board[rc][1]
                    self.moveFunctions[piece](r, c, moves)  # calls the appropriate move function based on piece type

        return moves

    # TODO: this method is dimension dependent.
    def getPawnMoves(self, r, c, moves):
        """
        get all the pawn moves of the pawn located at row r column c and add them to the moves list

        Parameters
        ----------
        r : int
            Row of the pawn
        c : int
            Column of the pawn
        moves : list
            list of possible moves

        Returns
        -------
        None.

        """
        rc = r * 6 + c

        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        if self.whiteToMove:
            moveAmount = -1
            moveAmountl = -6
            enemyColor = "b"
            kingRow, kingCol = self.whiteKingLocation
        else:
            moveAmount = 1
            moveAmountl = 6
            enemyColor = "w"
            kingRow, kingCol = self.blackKingLocation

        if self.board[rc + moveAmountl] == "--":  # 1square move
            if not piecePinned or pinDirection == (moveAmount, 0):
                moves.append(Move((r, c), (r + moveAmount, c), self.board))
        if c - 1 >= 0:  # capture to the left
            if not piecePinned or pinDirection == (moveAmount, -1):
                if self.board[rc + moveAmountl - 1][0] == enemyColor:
                    moves.append(Move((r, c), (r + moveAmount, c - 1), self.board))
        if c + 1 <= 5:  # capture to the right
            if not piecePinned or pinDirection == (moveAmount, 1):
                if self.board[rc + moveAmountl + 1][0] == enemyColor:
                    moves.append(Move((r, c), (r + moveAmount, c + 1), self.board))

    def getRookMoves(self, r, c, moves):
        """
        get all the Rook moves of the Rook located at row r column c and add them to the moves list

        Parameters
        ----------
        r : int
            Row of the Rook
        c : int
            Column of the Rook
        moves : list
            list of possible moves
        Returns
        -------
        None.

        """
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        directions = ((-1, 0), (0, -1), (1, 0), (0, 1))
        enemyColor = "b" if self.whiteToMove else "w"

        for d in directions:
            for i in range(1, 6):
                endRow = r + d[0] * i
                endCol = c + d[1] * i
                endRC = endRow * 6 + endCol
                if 0 <= endRow < self.dimension and 0 <= endCol < self.dimension:  # in the board dimensions
                    if not piecePinned or pinDirection == d or pinDirection == (-d[0], -d[1]):
                        endPiece = self.board[endRC]
                        if endPiece == "--":  # empty target square
                            moves.append(Move((r, c), (endRow, endCol), self.board))
                        elif endPiece[0] == enemyColor:  # enemy piece on targetsquare
                            moves.append(Move((r, c), (endRow, endCol), self.board))
                            break  # ends inner for loop
                        else:
                            break
                else:  # off board
                    break

    def getKnightMoves(self, r, c, moves):
        """
        get all the Knight moves of the Knight located at row r column c and add them to the moves list
        
        A Horsie has 8 possible Jumps at best, all 8 are getting checked in this function

        Parameters
        ----------
        r : int
            Row of the Knight
        c : int
            Column of the Knight
        moves : list
            list of possible moves
        Returns
        -------
        None.

        """
        piecePinned = False
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                self.pins.remove(self.pins[i])
                break

        knightMoves = ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1))
        allyColor = "w" if self.whiteToMove else "b"

        for m in knightMoves:
            endRow = r + m[0]
            endCol = c + m[1]
            endRC = endRow * 6 + endCol
            if 0 <= endRow < self.dimension and 0 <= endCol < self.dimension:  # in the board dimensions
                if not piecePinned:
                    endPiece = self.board[endRC]
                    if endPiece[0] != allyColor:  # not a piece of own color
                        moves.append(Move((r, c), (endRow, endCol), self.board))

    def getBishopMoves(self, r, c, moves):
        """
        get all the Bishop moves of the Bishop located at row r column c and add them to the moves list

        Parameters
        ----------
        r : int
            Row of the Bishop
        c : int
            Column of the Bishop
        moves : list
            list of possible moves
        Returns
        -------
        None.

        """
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        directions = ((-1, -1), (-1, 1), (1, -1), (1, 1))
        enemyColor = "b" if self.whiteToMove else "w"

        for d in directions:
            for i in range(1, 8):  # max distance a bishop can move is 7 squares
                endRow = r + d[0] * i
                endCol = c + d[1] * i
                endRC = endRow * 6 + endCol
                if 0 <= endRow < self.dimension and 0 <= endCol < self.dimension:  # in the board dimensions
                    if not piecePinned or pinDirection == d or pinDirection == (-d[0], -d[1]):
                        endPiece = self.board[endRC]
                        if endPiece == "--":  # empty target square
                            moves.append(Move((r, c), (endRow, endCol), self.board))
                        elif endPiece[0] == enemyColor:  # enemy piece on targetsquare
                            moves.append(Move((r, c), (endRow, endCol), self.board))
                            break  # ends inner for loop
                        else:
                            break
                else:  # off board
                    break

    def getQueenMoves(self, r, c, moves):
        """
        get all the Queen moves of the Queen located at row r column c and add them to the moves list

        Parameters
        ----------
        r : int
            Row of the King
        c : int
            Column of the King
        moves : list
            list of possible moves
        Returns
        -------
        None.

        """
        self.getRookMoves(r, c, moves)
        self.getBishopMoves(r, c, moves)

    def getKingMoves(self, r, c, moves):
        """
        get all the King moves of the King located at row r column c and add them to the moves list

        Parameters
        ----------
        r : int
            Row of the King
        c : int
            Column of the King
        moves : list
            list of possible moves
        Returns
        -------
        None.

        """

        rowMoves = (-1, -1, -1, 0, 0, 1, 1, 1)
        colMoves = (-1, 0, 1, -1, 1, -1, 0, 1)
        allyColor = "w" if self.whiteToMove else "b"

        for i in range(8):
            endRow = r + rowMoves[i]
            endCol = c + colMoves[i]
            endRC = endRow * 6 + endCol
            if 0 <= endRow < self.dimension and 0 <= endCol < self.dimension:  # in the board dimensions
                endPiece = self.board[endRC]
                if endPiece[0] != allyColor:  # not a piece of own color
                    # place the king on end square and check for checks
                    if allyColor == "w":
                        self.whiteKingLocation = (endRow, endCol)
                    else:
                        self.blackKingLocation = (endRow, endCol)
                    inCheck, pins, checks = self.checkForPinsAndChecks()
                    if not inCheck:
                        moves.append(Move((r, c), (endRow, endCol), self.board))
                        # place king back on original location
                    if allyColor == "w":
                        self.whiteKingLocation = (r, c)
                    else:
                        self.blackKingLocation = (r, c)

    def getCastleMoves(self, r, c, moves):

        """
        Generate all valid castle moves for the king at (r,c) and add them to the list of moves

        Returns
        -------
        None.

        """

        if (self.whiteToMove and self.currentCastlingRight.wks and self.whiteKingLocation[1] == 3) or \
                (not self.whiteToMove and self.currentCastlingRight.bks and self.blackKingLocation[1] == 3):
            self.getKingsideCastleMoves(r, c, moves)
        if (self.whiteToMove and self.currentCastlingRight.wqs) or (
                not self.whiteToMove and self.currentCastlingRight.bqs):
            self.getQueensideCastleMoves(r, c, moves)

    def getKingsideCastleMoves(self, r, c, moves):
        """
        adds valid kingside castling moves if there are any

        Parameters
        ----------
        r : int
            Row
        c : int
            Column
        moves : list
            list of valid moves

        Returns
        -------
        None.

        """
        rc = r * 6 + c
        if self.board[rc + 1] == "--":
            if not self.squareUnderAttack(r, c + 1):
                moves.append(Move((r, c), (r, c + 2), self.board))

    def getQueensideCastleMoves(self, r, c, moves):
        """
        adds valid queenside castling moves if there are any

        Parameters
        ----------
        r : int
            Row
        c : int
            Column
        moves : list
            list of valid moves

        Returns
        -------
        None.

        """
        rc = r * 6 + c
        if self.board[rc - 1] == "--" and self.board[rc - 2] == "--":
            if not self.squareUnderAttack(r, c - 1) and not self.squareUnderAttack(r, c - 2):
                moves.append(Move((r, c), (r, c - 2), self.board))


class CastleRights:
    """
    This class creates an object that holds the castle Rights 
    """

    def __init__(self, wks, bks, wqs, bqs):
        self.wks = wks
        self.bks = bks
        self.wqs = wqs
        self.bqs = bqs


class Move():
    """
    This class creates a move object with all the information about a move
    """
    # maps keys to values
    # key : value
    ranksToRows = {"1": 5, "2": 4, "3": 3, "4": 2,
                   "5": 1, "6": 0}
    rowsToRanks = {v: k for k, v in ranksToRows.items()}

    filesToCols = {"a": 0, "b": 1, "c": 2, "d": 3,
                   "e": 4, "f": 5}
    colsToFiles = {v: k for k, v in filesToCols.items()}

    def __init__(self, startSq, endSq, board):
        self.startRow = startSq[0]
        self.startCol = startSq[1]
        self.startRC = self.startRow * 6 + self.startCol
        self.endRow = endSq[0]
        self.endCol = endSq[1]
        self.endRC = self.endRow * 6 + self.endCol

        self.pieceMoved = board[self.startRC]
        self.pieceCaptured = board[self.endRC]

        self.moveID = self.startRow * 1000 + self.startCol * 100 + self.endRow * 10 + self.endCol

        # pawn promotion
        self.isPawnPromotion = (self.pieceMoved == "wp" and self.endRow == 0) or (
                    self.pieceMoved == "bp" and self.endRow == 5)

        # castle moves
        self.isCastleMove = self.pieceMoved[1] == "K" and abs(self.endCol - self.startCol) == 2

        # captures
        self.isCapture = self.pieceCaptured != "--"

        # self.created_timestamp = ' ' + str(time.time())
        self.created_timestamp = ''

    def __eq__(self, other):
        """
        Overriding the equals method

        Parameters
        ----------
        other : Move
            another Move

        Returns
        -------
        Boolean
            True when its the same move

        """
        if isinstance(other, Move):
            return self.moveID == other.moveID
        return False

    def getChessNotation(self):
        """
        Gets the chess notation of a move

        Returns
        -------
        String
            Chess notation

        """
        # To make this like real chess notations
        return self.getRankFile(self.startRow, self.startCol) + self.getRankFile(self.endRow, self.endCol)

    def getRankFile(self, r, c):
        """
        Converts rows and columns to ranks and files

        Parameters
        ----------
        r : int
            row
        c : int
            column

        Returns
        -------
        Sring
            Chess notation

        """
        return self.colsToFiles[c] + self.rowsToRanks[r]

    # overriding the str() function
    def __str__(self):
        """
        Overriding string method to make it look more like real chess notation

        Returns
        -------
        String
            Chess notation

        """
        # castle move
        if self.isCastleMove:
            return "O-O" + self.created_timestamp if self.endCol == 5 else "O-O-O"

        endSquare = self.getRankFile(self.endRow, self.endCol)
        # pawn moves
        if self.pieceMoved[1] == "p":
            if self.isCapture:
                return self.colsToFiles[self.startCol] + "x" + endSquare + self.created_timestamp
            else:
                return endSquare + self.created_timestamp

            # pawn promotions
        # two of the same type of piece moving to a square, Nbd2 if both Knights can move to d2

        # also adding + for check move and # for checkmate move

        # piece moves
        moveString = self.pieceMoved[1]
        if self.isCapture:
            moveString += "x"
        return moveString + endSquare + self.created_timestamp
