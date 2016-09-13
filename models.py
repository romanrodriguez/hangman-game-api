"""models.py - This file contains the class definitions for the Datastore
entities used by the Game. Because these classes are also regular Python
classes they can include methods (such as 'to_form' and 'new_game')."""

import random
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb


class User(ndb.Model):
    """User profile"""
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty()
    victories = ndb.IntegerProperty(default=0)
    games_played = ndb.IntegerProperty(default=0)

    """field that gets calculated with players' victories and losses"""
    @property
    def victory_percentage(self):
        if self.total_played > 0:
            return float(self.victories) / float(self.games_played)
        else:
            return 0

    def to_form(self):
        """form for rankings table"""
        return UserForm(name=self.name,
                        email=self.email,
                        victories=self.victories,
                        games_played=self.games_played,
                        win_percentage=self.victory_percentage)

    def add_victory(self):
        """store a player's victory"""
        self.victories += 1
        self.games_played += 1
        self.put()

    def add_loss(self):
        """store a player's loss"""
        self.games_played += 1
        self.put()


class Game(ndb.Model):
    """Game object"""
    user = ndb.KeyProperty(required=True, kind='User')
    guess_word = ndb.StringProperty(required=True)
    letter_attempts = ndb.StringProperty(required=True, default='')
    attempts_allowed = ndb.IntegerProperty(required=True, default=9)
    attempts_remaining = ndb.IntegerProperty(required=True, default=9)
    game_over = ndb.BooleanProperty(required=True, default=False)
    history = ndb.PickleProperty(required=True, default=[])

    @classmethod
    def new_game(cls, user, attempts):
        """Creates and returns a new game"""
        words = ["zigzagging", "jaywalking", "gabbiness", "queuing",
                 "quizzers", "fluffiest", "whizzing", "jinxing",
                 "buzzing", "alkalizing"]
        """List of words for players to guess"""
        d = random.randint(0, 9)
        """picks word at random from the list"""
        guess_word = str(words[d])
        """points the guess_word string to the word"""
        game = Game(user=user,
                    guess_word=guess_word,
                    letter_attempts='',
                    history=[],
                    attempts_allowed=attempts,
                    attempts_remaining=attempts,
                    game_over=False)
        game.put()
        return game

    def to_form(self, message):
        """Returns a GameForm representation of the Game"""
        form = GameForm()
        form.urlsafe_key = self.key.urlsafe()
        form.user_name = self.user.get().name
        form.letter_attempts = self.letter_attempts
        form.attempts_remaining = self.attempts_remaining
        form.game_over = self.game_over
        form.message = message
        return form

    def end_game(self, won=False):
        """Ends the game - if won is True, the player won. - if won is False,
        the player lost."""
        self.game_over = True
        self.put()
        # Add the game to the score 'board'
        score = Score(user=self.user, date=date.today(), won=won,
                      guesses=self.attempts_allowed - self.attempts_remaining)
        score.put()
        if won:
            self.user.get().add_victory()
        else:
            self.user.get().add_loss()


class Score(ndb.Model):
    """Score object"""
    user = ndb.KeyProperty(required=True, kind='User')
    date = ndb.DateProperty(required=True)
    won = ndb.BooleanProperty(required=True)
    guesses = ndb.IntegerProperty(required=True)

    def to_form(self):
        return ScoreForm(user_name=self.user.get().name, won=self.won,
                         date=str(self.date), guesses=self.guesses)


class GameForm(messages.Message):
    """GameForm for outbound game state information"""
    urlsafe_key = messages.StringField(1, required=True)
    attempts_remaining = messages.IntegerField(2, required=True)
    game_over = messages.BooleanField(3, required=True)
    message = messages.StringField(4, required=True)
    user_name = messages.StringField(5, required=True)
    letter_attempts = messages.StringField(6, required=True)


class GameForms(messages.Message):
    """Return multiple GameForms"""
    items = messages.MessageField(GameForm, 1, repeated=True)


class NewGameForm(messages.Message):
    """Used to create a new game"""
    user_name = messages.StringField(1, required=True)


class MakeMoveForm(messages.Message):
    """Used to make a move in an existing game"""
    guess = messages.IntegerField(1, required=True)


class ScoreForm(messages.Message):
    """ScoreForm for outbound Score information"""
    user_name = messages.StringField(1, required=True)
    date = messages.StringField(2, required=True)
    won = messages.BooleanField(3, required=True)
    guesses = messages.IntegerField(4, required=True)


class ScoreForms(messages.Message):
    """Return multiple ScoreForms"""
    items = messages.MessageField(ScoreForm, 1, repeated=True)


class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    message = messages.StringField(1, required=True)


class UserForm(messages.Message):
    """UserForm"""
    name = messages.StringField(1, required=True)
    email = messages.StringField(2)
    victories = messages.IntegerField(3, required=True)
    games_played = messages.IntegerField(4, required=True)
    victory_percentage = messages.FloatField(5, required=True)


class UserForms(messages.Message):
    """Return multiple UserForms """
    items = messages.MessageField(UserForm, 1, repeated=True)
