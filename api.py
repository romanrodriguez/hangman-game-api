"""Hangman API built on Google Cloud Endpoints."""

import re
import endpoints
from protorpc import remote, messages
from google.appengine.api import (
    memcache,
    taskqueue,
)
from models import (
    User,
    Game,
    Score,
)
from models import (
    StringMessage,
    NewGameForm,
    GameForm,
    MakeMoveForm,
    ScoreForms,
    GameForms,
    UserForms,
)
from utils import get_by_urlsafe

NEW_GAME_REQUEST = endpoints.ResourceContainer(
    NewGameForm)
GET_GAME_REQUEST = endpoints.ResourceContainer(
    urlsafe_game_key=messages.StringField(1),)
MAKE_MOVE_REQUEST = endpoints.ResourceContainer(
    MakeMoveForm,
    urlsafe_game_key=messages.StringField(1),)
USER_REQUEST = endpoints.ResourceContainer(
    user_name=messages.StringField(1),
    email=messages.StringField(2))
GET_HIGH_SCORES_REQUEST = endpoints.ResourceContainer(
    results=messages.IntegerField(1))

MEMCACHE_MOVES_REMAINING = 'MOVES_REMAINING'


@endpoints.api(name='hangman_game', version='v1')
class HangmanGameApi(remote.Service):
    """Game API"""
    @endpoints.method(request_message=USER_REQUEST,
                      response_message=StringMessage,
                      path='user',
                      name='create_user',
                      http_method='POST')
    def create_user(self, request):
        """Create a User. Requires a unique username"""
        if User.query(User.name == request.user_name).get():
            raise endpoints.ConflictException(
                'A User with that name already exists!')
        user = User(name=request.user_name, email=request.email)
        """
        Use regex to check email validity.
        Could add sending activation emails instead, as it is common practice
        and a more secure and standard way nowadays.
        """
        match = re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]'
                         '+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', request.email)
        if match is None:
            raise endpoints.ConflictException(
                'Not a valid email! Please enter a correct email address.')
        user.put()
        return StringMessage(message='User {} created!'.format(
            request.user_name))

    @endpoints.method(request_message=NEW_GAME_REQUEST,
                      response_message=GameForm,
                      path='game',
                      name='new_game',
                      http_method='POST')
    def new_game(self, request):
        """Creates new game"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                'A User with that name does not exist!')
        try:
            game = Game.new_game(user.key, 9)
        except ValueError:
            raise endpoints.BadRequestException('Error with the request')

        # Use a task queue to update the average attempts remaining.
        # This operation is not needed to complete the creation of a new game
        # so it is performed out of sequence.
        taskqueue.add(url='/tasks/cache_average_attempts')
        return game.to_form('Good luck playing this awesome Hangman game!')

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=StringMessage,
                      path='game/{urlsafe_game_key}/history',
                      name='get_game_history',
                      http_method='GET')
    def get_game_history(self, request):
        """Returns a game's history"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
            raise endpoints.NotFoundException('Game not found!')
        return StringMessage(message=str(game.history))

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='get_game',
                      http_method='GET')
    def get_game(self, request):
        """Return the current game state."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            return game.to_form('Guess another letter to move on.')
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=GameForms,
                      path='user/games',
                      name='get_user_games',
                      http_method='GET')
    def get_user_games(self, request):
        """Return all games"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException('User not found')
        games = Game.query(Game.user == user.key).\
            filter(Game.game_over == False)
        return GameForms(items=[game.to_form("game on") for game in games])

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=StringMessage,
                      path='game/{urlsafe_game_key}',
                      name='cancel_game',
                      http_method='DELETE')
    def cancel_game(self, request):
        """ Remove and end game that is under way"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
            raise endpoints.NotFoundException('Game not found!')
        if game.game_over:
            raise endpoints.BadRequestException(
                'You cannot delete completed games')

        game.key.delete()
        return StringMessage(message='Game id key:{} removed'.format(request.urlsafe_game_key))

    @endpoints.method(request_message=MAKE_MOVE_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='make_move',
                      http_method='PUT')
    def make_move(self, request):
        """Makes a move. Returns a game state with message"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        # Test if game is already over
        if game.game_over:
            raise endpoints.ForbiddenException(
                'Illegal action: Game is already over.')
        if not request.guess.isalpha():
            raise endpoints.ForbiddenException(
                'You can only type alphabetic characters.')
        if request.guess in game.letter_attempts:
            raise endpoints.ForbiddenException('Already said that letter.')
        if request.guess == game.guess_word:
            game.end_game(True)
            return game.to_form('You guessed the word! You win!')
        elif len(request.guess) != 1:
            raise endpoints.ForbiddenException(
                'Only provide one letter at a time or the entire exact word.')

        game.letter_attempts += request.guess

        if request.guess not in game.guess_word:
            game.attempts_remaining -= 1
            game.history.append((request.guess, "not found"))
            msg = 'Your letter is NOT in the word.'
        if request.guess in game.guess_word:
            msg = 'Your letter is in the word. Keep going.'
            game.history.append((request.guess, "found"))
        if game.attempts_remaining == 0:
            game.end_game(True)
            return game.to_form(msg + ' Game over!')
        else:
            game.put()
        return game.to_form(msg)

    @endpoints.method(response_message=ScoreForms,
                      path='scores',
                      name='get_scores',
                      http_method='GET')
    def get_scores(self, request):
        """Return all scores"""
        return ScoreForms(items=[score.to_form() for score in Score.query()])

    @endpoints.method(request_message=GET_HIGH_SCORES_REQUEST,
                      response_message=ScoreForms,
                      path='high_scores',
                      name='get_high_scores',
                      http_method='GET')
    def get_high_scores(self, request):
        """Return scores from highest"""
        Scores = Score.query(Score.won == True).order(Score.guesses).fetch(
            request.results)
        return ScoreForms(items=[score.to_form() for score in Scores])

    @endpoints.method(response_message=UserForms,
                      path='user/rankings',
                      name='get_user_rankings',
                      http_method='GET')
    def get_user_rankings(self, request):
        """Return user_rankings on victory percentages"""
        users = User.query(User.games_played > 0).fetch()
        users = sorted(users, key=lambda x: x.victory_percentage, reverse=True)
        return UserForms(items=[user.to_form() for user in users])

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=ScoreForms,
                      path='scores/user/{user_name}',
                      name='get_user_scores',
                      http_method='GET')
    def get_user_scores(self, request):
        """Returns all of an individual User's scores"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                'A User with that name does not exist!')
        scores = Score.query(Score.user == user.key)
        return ScoreForms(items=[score.to_form() for score in scores])

    @endpoints.method(response_message=StringMessage,
                      path='games/average_attempts',
                      name='get_average_attempts_remaining',
                      http_method='GET')
    def get_average_attempts(self, request):
        """Get the cached average moves remaining"""
        return StringMessage(message=memcache.get(
            MEMCACHE_MOVES_REMAINING) or '')

    @staticmethod
    def _cache_average_attempts():
        """Populates memcache with the average moves remaining of Games"""
        games = Game.query(Game.game_over == False).fetch()
        if games:
            count = len(games)
            total_attempts_remaining = sum([game.attempts_remaining
                                            for game in games])
            average = float(total_attempts_remaining) / count
            memcache.set(MEMCACHE_MOVES_REMAINING,
                         'Average moves remaining is {:.2f}'.format(average))


api = endpoints.api_server([HangmanGameApi])
