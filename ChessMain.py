# -*- coding: utf-8 -*-
"""
Created on Mon Apr 19 08:41:16 2021

@author: Alexander Leszczynski

This file is responsible for handling user input and displaying the current GameState object

"""
import json
import multiprocessing
import pathlib
import sys
import time
import argparse
import os
import os.path as osp
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

import pygame as py
import ChessEngine
from agents.expert import MrExpert
from agents.random import MrRandom
from student_agents.template import Agent as Agent1
from student_agents.template2 import Agent as Agent2
from sys import exit
from multiprocessing import Process, Queue, freeze_support
import importlib.util
import statistics as np

# Opening JSON file
with open('Settings.json') as f:
    # returns JSON object as
    # a dictionary
    data = json.load(f)

BOARD_COLOR = data["Board color"]
# 1 for Chess.com
# 2 for lichess.org

# DIFFICULTY_WHITE = data["Difficulty White"]
# DIFFICULTY_BLACK = data["Difficulty Black"]


# 0 if human player
# 1 nega max with alpha-beta, move ordering, no threefold , piecepositions
# 2 nega max with alpha-beta no position score <-- is bad
# 3 nega max with alpha-beta threefold 
# 4 nega max with alpha-beta no move order
# 5 nega max with alpha-beta, move ordering, no threefold , piecepositions * 0.1 
# 17 random



# global colors
# if BOARD_COLOR == 1:
#     colors = [py.Color((235, 235, 208)), py.Color((119, 148, 85))]  # these are the chess.com standard colors
# elif BOARD_COLOR == 2:
#     colors = [py.Color((240, 217, 181)), py.Color((181, 136, 99))]  # these are the lichess.org standard colors

# py.init()  # initializing pygame
BOARD_WIDTH = BOARD_HEIGHT = 400  # size of the board in pixels, the larger the number the worse the resolution
DIMENSION = 6  # dimensions of a chess board in Diana Chess are 6x6
MOVE_LOG_PANEL_WIDTH = 250
MOVE_LOG_PANEL_HEIGHT = BOARD_HEIGHT
CLOCK_PANEL_WIDTH = BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH
CLOCK_PANEL_HEIGHT = 150
SQ_SIZE = BOARD_HEIGHT // DIMENSION
MAX_FPS = 15  # for animations later on
IMAGES = {}


def loadImages():
    """
    Initialize a global dictionary of images. This will be called exactly once in the main.

    Returns
    -------
    None.

    """
    pieces = ["wp", "wR", "wN", "wB", "wK", "wQ", "bp", "bR", "bN", "bB", "bK", "bQ"]
    for piece in pieces:
        IMAGES[piece] = py.transform.scale(py.image.load("images/" + piece + ".png"), (SQ_SIZE, SQ_SIZE))
    # Note: we can acess an image by saying 'IMAGES["wp"]'


def main(args):
    """
    The main driver for our code. This will handle user or AI input and updating the graphics

    Returns
    -------
    None.
    :param args:
    :param agent_file_path2:
    :param agent_file_path1:

    """
    num_games = args.num_games - 1
    KingImg = py.image.load("images/bK.png")
    py.display.set_icon(KingImg)
    py.display.set_caption("Chess")

    if args.output_file:
        if osp.isfile(args.output_file):
            os.remove(args.output_file)

        pathlib.Path(os.path.dirname(args.output_file)).mkdir(parents=True, exist_ok=True)
        with open(args.output_file, 'w+') as f:
            pass

    def return_agent(path_or_name: str):
        if path_or_name == 'MrRandom':
            agent = MrRandom
        elif path_or_name == 'MrNovice':
            agent = None
        elif path_or_name == 'MrExpert':
            agent = MrExpert
        elif path_or_name == 'Human':
            agent = None
        elif path_or_name == 'Agent1':
            agent = Agent1
        elif path_or_name == 'Agent2':
            agent = Agent2
        else:
            spec = importlib.util.spec_from_file_location("Agent", path_or_name)
            foo = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(foo)
            agent = foo.Agent

        return agent

    agent1 = return_agent(args.agent1)
    agent2 = return_agent(args.agent2)


    py.init()
    if args.use_gui:
        screen = py.display.set_mode((BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT + CLOCK_PANEL_HEIGHT))
    clock = py.time.Clock()
    # screen.fill(py.Color("white"))
    game_state = ChessEngine.GameState()
    valid_moves = game_state.getValidMoves()
    move_made = False  # flag variable for when a move is made
    animate = False  # flag variable for when we should animate a move
    loadImages()  # only do this once, before the while loop
    running = True
    sqSelected = ()  # no square is selected, keep track of the last click of the user (tuple: (row,col))
    playerClicks = []  # keep track of player clicks (two tuples: [(6,4),(4,4)])
    game_over = False
    ai_thinking = False
    move_undone = False
    move_finder_process = None  # neu
    moveLogFont = py.font.SysFont("Arial", 14, False, False)
    halfmoveClock = 0  # global halfmoveClock
    GameTable = {"Draw by 50 move rule": 0, "Draw by threefold position repetition": 0, "Black wins by checkmate": 0,
                 "White wins by checkmate": 0, "Black wins on time": 0, "White wins on time": 0,
                 "Draw by insufficient material": 0, "White wins by illegal move": 0,
                 "Black wins by illegal move": 0}

    start_time = -1

    # playerOne = DIFFICULTY_WHITE == 0  # If a Human is playing white, else false
    # playerTwo = DIFFICULTY_BLACK == 0  # If a Human is playing white, else false
    playerOne = agent1 is None
    playerTwo = agent2 is None

    average_depth_per_move = []
    average_depth_per_game = []

    # clock logic
    clock_counter, clock_text = args.time_control, str(args.time_control).rjust(3)
    py.time.set_timer(py.USEREVENT, 1000)
    clock_font = py.font.SysFont('Consolas', 40)

    if agent1:
        chessai_white = agent1()
    if agent2:
        chessai_black = agent2()

    while running:
        human_turn = (game_state.whiteToMove and playerOne) or (not game_state.whiteToMove and playerTwo)
        for e in py.event.get():
            # remaining clocktime logic
            if e.type == py.USEREVENT:
                clock_counter -= 1
                clock_text = str(clock_counter).rjust(3) if clock_counter >= 0 else 'GAME OVER'
            # quitting the application
            if e.type == py.QUIT:
                running = False
                py.quit()
                exit()
            # mouse operations
            elif e.type == py.MOUSEBUTTONDOWN:
                if not game_over:
                    location = py.mouse.get_pos()  # (x,y) location of mouse
                    col = location[0] // SQ_SIZE
                    row = location[1] // SQ_SIZE
                    # bugfix where col or row can be 6 when the outer rim is clicked
                    if row >= 5:
                        row = 5
                    if sqSelected == (row, col) or col >= 6:  # the user clicked the same square twice
                        sqSelected = ()  # deselect
                        playerClicks = []  # clear player clicks
                    else:
                        sqSelected = (row, col)
                        playerClicks.append(sqSelected)  # append for both 1st and 2nd clicks
                    if len(playerClicks) == 2 and human_turn:  # after 2nd click
                        move = ChessEngine.Move(playerClicks[0], playerClicks[1], game_state.board)
                        # checks wether move is a valid move
                        for i in range(len(valid_moves)):
                            if move == valid_moves[i]:
                                game_state.makeMove(move)
                                if move.pieceCaptured == "--" and move.pieceMoved[1] != "p":
                                    halfmoveClock += 1
                                else:
                                    halfmoveClock = 0
                                move_made = True
                                animate = True
                                sqSelected = ()  # resets slected Squares
                                playerClicks = []  # resets player clicks
                    # if two clicks on the same square were made
                    if not move_made:
                        if sqSelected != () and sqSelected[0] < DIMENSION:
                            playerClicks = [sqSelected]

            # key operations
            elif e.type == py.KEYDOWN:
                if e.key == py.K_u:  # undo when "u" is pressed
                    game_state.undoMove()
                    if halfmoveClock != 0:
                        halfmoveClock -= 1
                    move_made = True
                    animate = False
                    game_over = False
                    if ai_thinking:
                        move_finder_process.terminate()
                        ai_thinking = False
                    move_undone = False
                if e.key == py.K_r:  # reset the board when "r" is pressed
                    game_state = ChessEngine.GameState()
                    valid_moves = game_state.getValidMoves()
                    sqSelected = ()
                    playerClicks = []
                    halfmoveClock = 0
                    move_made = False
                    animate = False
                    game_over = False
                    clock_counter = args.time_control
                    if ai_thinking:
                        move_finder_process.terminate()
                        ai_thinking = False
                    move_undone = False

        # AI Move finder with multiprocessing
        # print([game_over, human_turn, move_undone])
        if not game_over and not human_turn and not move_undone:
            if not ai_thinking:
                ai_thinking = True
                # print('white' if game_state.whiteToMove else 'black')
                chessai = chessai_white if game_state.whiteToMove else chessai_black
                return_queue = Queue()  # used to pass data between threads
                chessai.clear_queue(return_queue)

                move_finder_process = Process(target=chessai.findBestMove, args=(game_state, ))
                move_finder_process.start()
                start_time = time.time()
                # print("AI is thinking ... ")

            if time.time() - start_time > args.time_control or not move_finder_process.is_alive():
                move_finder_process.kill()
                move_finder_process.join()
            # if not move_finder_process.is_alive():
                ai_move, nextMoveScore, currentDepth = chessai.get_move()
                if not ai_move in game_state.getValidMoves():
                    game_state.illegal_move_done = True

                if game_state.whiteToMove:
                    average_depth_per_game.append(currentDepth)
                    average_depth_per_move.append(currentDepth)

                if args.verbose:
                    s = f"{'White' if game_state.whiteToMove else 'Black'}'s move: {str(ai_move)}\n" + \
                        f"Current Depth is: {currentDepth}\n" + \
                        f"The Score this move has is: {nextMoveScore}\n"
                    print(s)
                    if args.output_file:
                        if not osp.isfile(args.output_file):
                            raise SystemExit(str(args.output_file) + ' does no longer exist!')
                        with open(args.output_file, 'a') as f:
                            f.write(s)
                # if ai_move is None:
                #     print("sth wrong then??")
                #     ai_move = ChessAI.findRandomMove(valid_moves)
                game_state.makeMove(ai_move)
                move_made = True
                if ai_move.pieceCaptured == "--" and ai_move.pieceMoved[1] != "p":
                    halfmoveClock += 1
                else:
                    halfmoveClock = 0
                animate = True
                ai_thinking = False

        # move animation and resetting clock
        if move_made:
            if args.use_gui:
                if animate:
                    animateMove(game_state.moveLog[-1], screen, game_state.board, clock)
            valid_moves = game_state.getValidMoves()
            move_made = False
            animate = False
            clock_counter = args.time_control + 1

        if args.use_gui:
            drawGameState(screen, game_state, valid_moves, sqSelected, moveLogFont)

        # draw EndGameText
        if game_state.checkMate or game_state.staleMate or halfmoveClock == 100 or clock_counter < 0 - 0.3 or game_state.threefold or game_state.draw or game_state.illegal_move_done:
            game_over = True
            if game_state.threefold:
                text = "Draw by threefold position repetition"
            elif halfmoveClock == 100:
                text = "Draw by 50 move rule"
            elif game_state.checkMate and game_state.whiteToMove:
                text = "Black wins by checkmate"
            elif game_state.checkMate:
                text = "White wins by checkmate"
            elif clock_counter < 0 and game_state.whiteToMove:
                text = "Black wins on time"
            elif game_state.draw:
                text = "Draw by insufficient material"
            elif game_state.illegal_move_done:
                text = f"{'White' if game_state.whiteToMove else 'Black'} wins by illegal move"
            else:
                text = "White wins on time"
            if args.use_gui:
                drawEndGameText(screen, text)

        # restart the game if repetitions are on
        if game_over == True:
            # if args.use_gui:
            #     time.sleep(5)
            if num_games > 0:
                GameTable[text] += 1
                if args.verbose:
                    print('Intermediate Results:')
                    print(GameTable)
                    if average_depth_per_move:
                        print('avg depth: ', np.mean(average_depth_per_move))
                    if args.output_file:
                        with open(args.output_file, 'a') as f:
                            f.write(str(GameTable) + "\n")
                            if average_depth_per_move:
                                f.write(str(np.mean(average_depth_per_move)) + '\n')
                average_depth_per_move = []
                # same as py.event K_r
                game_state = ChessEngine.GameState()
                valid_moves = game_state.getValidMoves()
                sqSelected = ()
                playerClicks = []
                halfmoveClock = 0
                move_made = False
                animate = False
                game_over = False
                clock_counter = args.time_control + 1
                if ai_thinking:
                    move_finder_process.terminate()
                    ai_thinking = False
                move_undone = False
                num_games -= 1

        # print out the gametable if no more repetitions are in line
        if num_games == 0 and game_over:
            GameTable[text] += 1
            print('Final Results:')
            print(GameTable)
            if average_depth_per_move:
                print('avg depth:', np.mean(average_depth_per_move))
            if average_depth_per_game:
                print('avg depth overall:', np.mean(average_depth_per_game))
            if args.output_file:
                with open(args.output_file, 'a') as f:
                    f.write('Final Results:\n')
                    f.write(str(GameTable))
                    if average_depth_per_move:
                        f.write('avg depth:' + str(np.mean(average_depth_per_move)) + '\n')
                    if average_depth_per_game:
                        f.write('avg depth overall:' + str(np.mean(average_depth_per_game)))
            num_games -= 1
            if not args.use_gui:
                raise SystemExit()

        if args.use_gui:
            screen.blit(clock_font.render(clock_text, True, (255, 255, 255)),
                        (CLOCK_PANEL_WIDTH / 3, BOARD_HEIGHT + CLOCK_PANEL_HEIGHT / 2))
            py.display.flip()
        clock.tick(MAX_FPS)


def drawGameState(screen, gs, validMoves, sqSelected, moveLogFont):
    """
    Responsible for all the graphics within a current game state.

    Parameters
    ----------
    screen : TYPE
        DESCRIPTION.
    gs : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    """
    drawBoard(screen)  # draw squares on the board
    highlightSquares(screen, gs, validMoves, sqSelected)
    drawPieces(screen, gs.board)  # draw pieces on top of those sqaures
    drawMoveLog(screen, gs, moveLogFont)
    drawClock(screen)


def drawBoard(screen):
    """
    Draws the squares on the board. The top left square is always light.
    

    Parameters
    ----------
    screen : pygame screen
        Initally the screen is blank with the Size of the constants "WIDTH" and "HEIGHT" 

    Returns
    -------
    None.

    """
    global colors
    if BOARD_COLOR == 1:
        colors = [py.Color((235, 235, 208)), py.Color((119, 148, 85))]  # these are the chess.com standard colors
    elif BOARD_COLOR == 2:
        colors = [py.Color((240, 217, 181)), py.Color((181, 136, 99))]  # these are the lichess.org standard colors

    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[(r + c) % 2]  # a chessboard square row + column is always white when its an even number
            py.draw.rect(screen, color, py.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))


def highlightSquares(screen, gs, validMoves, sqSelected):
    """
    Highlights the selected square and the possible moves for the selected piece

    Parameters
    ----------
    screen : pygame screen
        The board with the pieces and stuff
    gs : ChessEngine GameState 
        gamestate of the game
    validMoves : list
        list of valid moves 
    sqSelected : tuple
        (row, col) of the Square that gets highlighted by this function

    Returns
    -------
    None.

    """
    # highlight last move
    if (len(gs.moveLog)) > 0:
        lastMove = gs.moveLog[-1]
        s = py.Surface((SQ_SIZE, SQ_SIZE))
        s.set_alpha(100)
        s.fill(py.Color('green'))
        screen.blit(s, (lastMove.endCol * SQ_SIZE, lastMove.endRow * SQ_SIZE))
    if sqSelected != ():
        r, c = sqSelected
        rc = r * 6 + c
        if gs.board[rc][0] == ("w" if gs.whiteToMove else "b"):  # sqSelected is a piece that can be moved
            # highlight selected square
            s = py.Surface((SQ_SIZE, SQ_SIZE))
            s.set_alpha(100)  # transparancy value -> 0 transparent; 255 opaque
            s.fill(py.Color("blue"))
            screen.blit(s, (c * SQ_SIZE, r * SQ_SIZE))
            # highlight moves from that square
            s.fill(py.Color("yellow"))
            for move in validMoves:
                if move.startRow == r and move.startCol == c:
                    screen.blit(s, (move.endCol * SQ_SIZE, move.endRow * SQ_SIZE))


def drawPieces(screen, board):
    """
    Draws the pieces on the board using current GameState.board
    

    Parameters
    ----------
    screen : pygame screen
        Initally the screen is blank with the Size of the constants "WIDTH" and "HEIGHT"
    board : list of lists
        a list of lists with the current pieces on the board

    Returns
    -------
    None.

    """
    rc = 0
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            rc = r * 6 + c

            piece = board[rc]
            if piece != "--":  # not empty square
                screen.blit(IMAGES[piece], py.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))


def animateMove(move, screen, board, clock):
    """
    Animates the move

    Parameters
    ----------
    move : ChessEngine Move
        the move that is to be animated
    screen : pygame Screen
         Screen of the board with pieces and stuff
    board : list of list
        list of list
    clock : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    """
    global colors
    dR = move.endRow - move.startRow
    dC = move.endCol - move.startCol
    framesPerSquare = 10  # frames to move one square
    frameCount = (abs(dR) + abs(dC)) * framesPerSquare
    for frame in range(frameCount + 1):
        r, c = (move.startRow + dR * frame / frameCount, move.startCol + dC * frame / frameCount)
        drawBoard(screen)
        drawPieces(screen, board)
        # erase the piece moved from its ending square
        color = colors[(move.endRow + move.endCol) % 2]
        endSquare = py.Rect(move.endCol * SQ_SIZE, move.endRow * SQ_SIZE, SQ_SIZE, SQ_SIZE)
        py.draw.rect(screen, color, endSquare)
        # drawing moving piece
        screen.blit(IMAGES[move.pieceMoved], py.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))
        py.display.flip()
        clock.tick(144)  # fps


def drawMoveLog(screen, gs, font):
    """
    Draws the move log

    Parameters
    ----------
    screen : pygame screen
        screen of the game
    gs : ChessEngine GameState 
        gamestate of the game
    moveLogFont : string
        the font we want our moveLog to be in

    Returns
    -------
    None.

    """
    moveLogRect = py.Rect(BOARD_WIDTH, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT)
    py.draw.rect(screen, py.Color((39, 37, 34)), moveLogRect)
    moveLog = gs.moveLog
    moveTexts = []
    for i in range(0, len(moveLog), 2):
        moveString = str(i // 2 + 1) + ".  " + str(moveLog[i]) + " "
        if i + 1 < len(moveLog):  # make sure black made a move
            moveString += str(moveLog[i + 1]) + "  "
        moveTexts.append(moveString)

    movesPerRow = 3
    padding = 5
    lineSpacing = 2
    textY = padding
    for i in range(0, len(moveTexts), movesPerRow):
        text = ""
        for j in range(movesPerRow):
            if i + j < len(moveTexts):
                text += moveTexts[i + j]
        textObject = font.render(text, True, py.Color("white"))
        textLocation = moveLogRect.move(padding, textY)
        screen.blit(textObject, textLocation)
        textY += textObject.get_height() + lineSpacing


def drawClock(screen):
    """
    The clock is underneath the board and the moveLog panel

    Parameters
    ----------
    screen : TYPE
        DESCRIPTION.
    gs : TYPE
        DESCRIPTION.
    font : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    """
    clockRect = py.Rect(0, BOARD_HEIGHT, CLOCK_PANEL_WIDTH, CLOCK_PANEL_HEIGHT)
    py.draw.rect(screen, py.Color((39, 37, 34)), clockRect)


def drawEndGameText(screen, text):
    """
    

    Parameters
    ----------
    screen : pygame screen
        Its a pygame screen the message is supposed to be drawn onto
    text : string
        The message that we want to display

    Returns
    -------
    None.

    """
    font = py.font.SysFont("Helvetica", 32, True, False)
    textObject = font.render(text, 0, py.Color("Gray"))
    textLocation = py.Rect(0, 0, BOARD_WIDTH, BOARD_HEIGHT).move(BOARD_WIDTH / 2 - textObject.get_width() / 2,
                                                                 BOARD_HEIGHT / 2 - textObject.get_height() / 2)
    screen.blit(textObject, textLocation)
    textObject = font.render(text, 0, py.Color("Black"))
    screen.blit(textObject, textLocation.move(2, 2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--agent1', type=str, required=True,
                        help='Either path to the .py file containing your agent or "MrRandom".')
    parser.add_argument('--agent2', type=str, required=True,
                        help='See --agent_one.')
    parser.add_argument('--output_file', type=str, default=None,
                        help='File to save results to. If not given, all output will be printed to terminal only.'
                             'This file will be overwritten, if it exists.')
    parser.add_argument('--verbose', default=False, action='store_true',
                        help='Whether the output file only contains the final result or all moves.')
    parser.add_argument('--use_gui', default=True, action='store_true',
                        help='Whether the output file only contains the final result or all moves.')
    parser.add_argument('--num_games', type=int, default=1,
                        help='How many games you want to play with this settings and agents.'
                             'Agents do NOT switch sides after each game.')
    parser.add_argument('--time_control', type=int, default=20,
                        help='How many seconds per move each player has.')
    parser.add_argument('--evaluation', default=False, action='store_true',
                        help="Sets graphics driver to 'dummy', so that this runs on a server without optical output.")

    args = parser.parse_args()

    # activate, if on server without video driver:
    # if multiprocessing.cpu_count() > 17:
    if args.evaluation:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
    # freeze_support()

    main(args)
