# Hangman Game API

## Project Overview
- Wrote platform-agnostic app using Google App Engine backed by Google Datastore.
- Wrote an API with endpoints that allows anyone to develop a front-end for the game.
- Used API explorer to test the API.


## Game Description:
This Hangman game is intended to be played by a single user who needs to guess a word provided by the game's API. The API provides a set of secret words that will be chosen at random for the player to guess in each game. The API methods are described in more detail below. The player can either guess the word in full or letter by letter. Each wrong attempt will count towards a maximum number of attempts. If the player doesn't guess the entire word before hitting that number of attempts, the player loses. Otherwise, the player wins the game.

For score-keeping, the guesses by the player get recorded in `letter_attempts`, and for recording games, the property `history` is used. Players are ranked by number of wins and loses.

To play, we first need to create a new user, using the `create_user` endpoint.
Use `new_game` to create a game. Remember to copy the `urlsafe_key` property for later use. With `make_move` you'll be able to make sure the player avids to the game's rules. Below, you can find more information about other endpoints you can/ should use and they are also commented in the code.


## Set-Up Instructions:
1.  Update the value of application in app.yaml to the app ID you have registered
 in the App Engine admin console and would like to use to host your instance of this sample.
2.  Run the app with the devserver using dev_appserver.py DIR, and ensure it's
 running by visiting the API Explorer - by default localhost:8080/_ah/api/explorer.
3.  (Optional) Generate your client library(ies) with the endpoints tool.
 Deploy your application.


## Files Included:
 - api.py: Contains endpoints and game playing logic.
 - app.yaml: App configuration.
 - cron.yaml: Cronjob configuration.
 - main.py: Handler for taskqueue handler.
 - models.py: Entity and message definitions including helper methods.
 - utils.py: Helper function for retrieving ndb.Models by urlsafe Key string.


## Endpoints Included:
 - **create_user**
    - Path: 'user'
    - Method: POST
    - Parameters: user_name, email (required)
    - Returns: Message confirming creation of the User.
    - Description: Creates a new User. user_name provided must be unique. Will 
    raise a ConflictException if a User with that user_name already exists, or if User doesn't provide a valid email address.
    
 - **new_game**
    - Path: 'game'
    - Method: POST
    - Parameters: user_name
    - Returns: GameForm with initial game state.
    - Description: Creates a new Game. User_name provided must correspond to an
    existing user - will raise a NotFoundException if not. Also adds a task to a task queue to update the average moves remaining
    for active games.
     
 - **get_game_history**
    - Path: game/{urlsafe_game_key}/history
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: All moves performed in the game
    - Description: Processes all historical data on games.

 - **get_game**
    - Path: 'game/{urlsafe_game_key}'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameForm with current game state.
    - Description: Returns the current state of a game.
    
- **get_user_games**
    - Path: 'user/games'
    - Method: GET
    - Parameters: user_name
    - Returns: All games from one user that are active and not finished
    - Description: Returns all of a User's active games.

 - **cancel_game**
    - Path: 'game/{urlsafe_game_key}',
    - Method: DELETE
    - Parameters: urlsafe_game_key
    - Returns: Games from a user that are active and not done
    - Description: Users can cancel a game in progress, yet completed games cannot be removed. 

 - **make_move**
    - Path: 'game/{urlsafe_game_key}'
    - Method: PUT
    - Parameters: urlsafe_game_key, guess
    - Returns: GameForm with new game state.
    - Description: Accepts a 'guess' and returns the updated state of the game.
    If this causes a game to end, a corresponding Score entity will be created.
    
 - **get_scores**
    - Path: 'scores'
    - Method: GET
    - Parameters: None
    - Returns: ScoreForms.
    - Description: Returns all Scores in the database (unordered).
 
 - **get_high_scores**
    - Path: 'high_scores'
    - Method: GET
    - Parameters: Total number of records stored
    - Returns: All scores ranked by wins on top and after by least amount of attempts to win.
    - Description: Can tell who has won the most games and times players have tried to win.

 - **get_user_rankings**
    - Path: 'user/rankings'
    - Method: GET
    - Parameters: None 
    - Returns: Players that have played games displayed by ranking (win ratio)
    - Description: Ranks the performance of each player.

 - **get_user_scores**
    - Path: 'scores/user/{user_name}'
    - Method: GET
    - Parameters: user_name
    - Returns: ScoreForms. 
    - Description: Returns all Scores recorded by the provided player (unordered).
    Will raise a NotFoundException if the User does not exist.
 
- **get_average_attempts**
    - Path: 'games/average_attempts'
    - Method: GET
    - Parameters: None
    - Returns: StringMessage
    - Description: Gets the average number of attempts remaining for all games
    from a previously cached memcache key.


## Models Included:
 - **User**
    - Stores unique user_name and (optional) email address.
 - **Game**
    - Stores unique game states. Associated with User model via KeyProperty.
 - **Score**
    - Records completed games. Associated with Users model via KeyProperty.


## Forms Included:
 - **GameForm**
    - Representation of a Game's state (urlsafe_key, attempts_remaining,
    game_over flag, message, user_name).
 - **GameForms**
    - Return multiple GameForms (items).
 - **NewGameForm**
    - Used to create a new game (user_name).
 - **MakeMoveForm**
    - Inbound make move form (guess). Used to make a move in an existing game.
 - **ScoreForm**
    - Representation of a completed game's Score (user_name, date, won flag,
    guesses).
 - **ScoreForms**
    - Return multiple ScoreForms (items).
 - **StringMessage**
    - General purpose String container (message).
 - **UserForm**
    - Outbound user identity form (name, email, victories, games_played, victory_percentage).
 - **UserForms**
    - Return multiple UserForms (items).


    ## Additional Resources:
    - [Checked code for PEP8 requirements](http://pep8online.com/)
    - https://en.wikipedia.org/wiki/Hangman_(game)
    - http://localhost:8080/_ah/api/explorer

    ## Testing
    To test this project I first export the path of Google App Engine to the directory that holds my project in it:
    `export PATH=$PATH:/Users/Username/google_appengine/`

    Then, I start the server to be able to browse the project locally by specifying its directory in the following command:
    `dev_appserver.py DIR`

    Last, to be able to test the API without browser issues, I run the following command, which opens a new Google Chrome window that allows the project to smoothly throughout the testing phase:
   `/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome http://localhost:8080/_ah/api/explorer http://localhost:8000 --user-data-dir=test -allow-running-insecure-content --disable-extensions --no-first-run --no-default-browser-check`


