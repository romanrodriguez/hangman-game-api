"""utils.py - File for collecting general utility functions."""

import logging
from google.appengine.ext import ndb
import endpoints
from models import Score


def get_by_urlsafe(urlsafe, model):
    """Returns an ndb.Model entity that the urlsafe key points to. Checks
        that the type of entity returned is of the correct kind. Raises an
        error if the key String is malformed or the entity is of the incorrect
        kind
    Args:
        urlsafe: A urlsafe key string
        model: The expected entity kind
    Returns:
        The entity that the urlsafe Key string points to or None if no entity
        exists.
    Raises:
        ValueError:"""
    try:
        key = ndb.Key(urlsafe=urlsafe)
    except TypeError:
        raise endpoints.BadRequestException('Invalid Key')
    except Exception, e:
        if e.__class__.__name__ == 'ProtocolBufferDecodeError':
            raise endpoints.BadRequestException('Invalid Key')
        else:
            raise

    entity = key.get()
    if not entity:
        return None
    if not isinstance(entity, model):
        raise ValueError('Incorrect Kind')
    return entity


def wins_minus_losses_count(user):
    """Calculates a user's score from games won or lost"""
    scores = Score.query(Score.user == user.key)
    count_wins = 0
    count_losses = 0

    for score in scores:
        if (score.won == True):
            count_wins += 1
        else:
            count_losses += 1

    return count_wins - count_losses
