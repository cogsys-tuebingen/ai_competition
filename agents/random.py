import random


class MrRandom:
    def __init__(self):
        self.move_queue = None

        self.nextMove = None
        self.counter = None
        self.currentDepth = None
        self.start = None
        self.timeout = None
        self.globalBestMove = None
        self.globalBestScore = None
        self.nextMoveScore = None

    def get_move(self):
        move = None
        while not self.move_queue.empty():
            move = self.move_queue.get()
        return move

    def update_move(self, move, score=-1, depth=-1):
        self.move_queue.put([move, score, depth])

    def clear_queue(self, outer_queue):
        self.move_queue = outer_queue


    def findBestMove(self, gs):
        """
        AI that plays a random Move out of the legal Moves

        Parameters
        ----------
        validMoves : list
            list of valid/legal moves

        Returns
        -------
        Move

        """

        validMoves = gs.getValidMoves()
        self.update_move(random.choice(validMoves), -1, -1)
