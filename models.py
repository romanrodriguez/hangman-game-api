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


class Game(ndb.Model):
    """
    Game object includes the registered user,
    the word to be guessed,
    the letter attempts towards guessing the word,
    the number of attempts allowed,
    the count of attempts already tried,
    a game over property in case the attempts allowed are surpased,
    and a history one to keep record of all the attempts.
    """
    user = ndb.KeyProperty(required=True, kind='User')
    guess_word = ndb.StringProperty(required=True)
    word_length = ndb.IntegerProperty(required=True)
    letter_attempts = ndb.StringProperty(required=True, default='')
    letter_attempts_correct = ndb.StringProperty(required=True, default='')
    letter_attempts_wrong = ndb.StringProperty(required=True, default='')
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
                    word_length=len(guess_word),
                    letter_attempts='',
                    letter_attempts_correct='',
                    letter_attempts_wrong='',
                    history=[],
                    attempts_allowed=9,
                    attempts_remaining=9,
                    game_over=False)
        game.put()
        return game

    def to_form(self, message):
        """Returns a GameForm representation of the Game"""
        form = GameForm()
        form.urlsafe_key = self.key.urlsafe()
        form.user_name = self.user.get().name
        form.letter_attempts = self.letter_attempts
        form.letter_attempts_correct = self.letter_attempts_correct
        form.letter_attempts_wrong = self.letter_attempts_wrong
        form.word_length = self.word_length
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
    letter_attempts_correct = messages.StringField(7, required=True)
    letter_attempts_wrong = messages.StringField(8, required=True)
    word_length = messages.IntegerField(9, required=True)


class GameForms(messages.Message):
    """Return multiple GameForms"""
    games = messages.MessageField(GameForm, 1, repeated=True)


class NewGameForm(messages.Message):
    """Used to create a new game"""
    user_name = messages.StringField(1, required=True)


class MakeMoveForm(messages.Message):
    """Used to make a move in an existing game"""
    guess = messages.StringField(1, required=True)


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


class RankingForm(messages.Message):
    """Used for user ranking and high scores"""
    user_name = messages.StringField(1, required=True)
    score = messages.IntegerField(2, required=True)


class RankingForms(messages.Message):
    """Return multiple Rankings"""
    rankings = messages.MessageField(RankingForm, 1, repeated=True)
