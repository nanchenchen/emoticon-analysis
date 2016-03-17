import json

from emoticonvis.apps.corpus.models import *


class AttributeDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


lang_map = {
    "English": "En",
    "French": "Fr"
}

def create_a_participant_from_json(json_str, dataset_obj):
    """
    Given a dataset object, imports a participant from json string into
    the dataset.
    """
    data = AttributeDict(json.loads(json_str))
    participant = Participant(id=data.id, name=data.name, dataset=dataset_obj)
    participant.save()
    return participant

def update_full_participant_background_from_json(json_str, dataset_obj):
    """
    Given a dataset object, imports a participant from json string into
    the dataset.
    """
    data = AttributeDict(json.loads(json_str))
    participant = Participant.objects.get(id=data.id)
    participant.position = data.status
    if lang_map.get(data.lang):
        participant.language = lang_map[data.lang]
    participant.save()

    return participant

def update_participant_background_from_json(json_str, dataset_obj):
    """
    Given a dataset object, imports a participant from json string into
    the dataset.
    """
    data = AttributeDict(json.loads(json_str))
    participant = Participant.objects.get(id=data.id)
    participant.status = data.status
    if lang_map.get(data.lang):
        participant.language = lang_map[data.lang]
    participant.is_selected = True
    participant.save()

    return participant

def create_a_message_from_json(json_str, dataset_obj):
    """
    Given a dataset object, imports a participant from json string into
    the dataset.
    """
    data = AttributeDict(json.loads(json_str))

    message = Message(dataset=dataset_obj,
                      id=data.id, participant_id=data.participant_id,
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

valence_map = {
    "positive": "P",
    "negative": "N",
    "neutral": "O",
}

def update_emoticon_valence_from_json(json_str, dataset_obj):
    """
    Given a dataset object, imports a participant from json string into
    the dataset.
    """
    data = AttributeDict(json.loads(json_str))
    emoticon = Emoticon.objects.get(id=data.id)
    emoticon.valence = valence_map[data.valence]
    emoticon.save()
    return emoticon