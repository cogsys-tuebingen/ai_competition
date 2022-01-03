Notes for Assignment 8 (Chess AI)
--------------------------------------------------------------------------------

o We recommend using an IDE (like Pycharm) for working on this assignment.

o IMPORTANT: Please make sure you use python>=3.7 for this assignment.

o First, you need to install python pygame package by executing the following command in terminal:

  § pip install pygame

  If you are using Pycharm, you can also add the package from:
  File-> Settings-> Project:dianachess-> Project Interpreter. Click the '+' sign to 
  add new packages. Search pygame and install the package.

o The game gui can be started by running the script 'ChessMain.py' the following way:

  § python ChessMain.py --agent1 [*] --agent2 [*] --verbose --time_control [how many seconds either player gets per move] --use_gui
  
  For [*] you can put either 'MrRandom', 'Agent1', 'Agent2', 'Human', or a path to your agent file. 'MrRandom' will play
  completely random moves (valid moves), 'Agent1' will use the class Agent from 'student_agents/template.py' while
  'Agent2' will use the class Agent from 'student_agents/template2.py'. By entering 'Human' you act as the agent and can
  play yourself (if the gui is activated).
  WINDOWS USERS: Here you need to use 'Agent', it does not work to use the file path.
  

o By choosing in between 1 and 2 in 'Settings.json' you can choose whichever board you like.

o Please note that for the evaluation, --time_control=20 will be used (pending further
  tests, a higher value may instead be used to account for the server running 
  the games being slightly slower, however your agent should be prepared for being 
  given less time than expected by registering preliminary moves)

o If your agent is still running after the time limit has passed, your agent will
  lose unless you have registered a preliminary move with update_move. See the 
  template student_agents/template.py for details.

o WHEN YOU WANT TO RUN ChessMain.py with '--agentx Agent1' you need to keep the file name 'template.py'.

o FOR THE SUBMISSION you must rename the file studentagent.py to the last name of both team members 
  (e.g. rahim_schroeder.py} for Rahim and Schröder). Keep the class name as 'Agent'. Your agent's
  functionality should be similar to the class MrRandom in 'agents/random.py'. You are not allowed
  to modify any other file in the program, so please make sure your agent works with the base version of the
  game as distributed. Please do not split your implementation across multiple files.

  Important: please include some documentation for your agent as a separate document.
  Document which algorithm you are using, what the idea behind your heuristic/evaluation function is, etc.

o If you find any inefficiency in the code, e.g in ChessMain.py, ChessEngine.py,
  (or worse, bugs) and you can suggest any improvement, please send an email to
  martin.messmer@uni-tuebingen.de until 22.12.21.
  
o You are allowed to use any basic package in python that helps in your implementation.
  Basic includes anything included in python3.7, numpy, and what might be discussed in the forum.

o Your agent should be single-threaded. A multi-threaded agent will not get any
  marks for the assignment and will be disqualified from the tournament.

o One agent is included in this framework to allow you to test your agent:

  - MrRandom: A very primitive agent that selects its moves randomly from the
    list of legal moves. Basically any agent should be able to beat this.

