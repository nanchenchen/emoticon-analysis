import json

from emoticonvis.apps.corpus.models import *


class AttributeDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


def create_a_participant_from_json(json_str, dataset_obj):
    """
    Given a dataset object, imports a participant from json string into
    the dataset.
    """
    data = AttributeDict(json.loads(json_str))
    participant = Participant(id=data.id, name=data.name)
    participant.save()
    return participant


def create_a_message_from_json(json_str, dataset_obj):
    """
    Given a dataset object, imports a participant from json string into
    the dataset.
    """
    data = AttributeDict(json.loads(json_str))
    message = Message(id=data.id, participant_id=data.participant_id,
                      idx=data.idx, session_id=data.session_id,
                      time=data.time, type=data.type,
                      text=data.message)
    message.save()
    return message

def create_an_emoticon_from_json(json_str, dataset_obj):
    """
    Given a dataset object, imports a participant from json string into
    the dataset.
    """
    data = AttributeDict(json.loads(json_str))
    emoticon = Emoticon(id=data.id, text=data.emoticon)
    emoticon.save()
    return emoticon