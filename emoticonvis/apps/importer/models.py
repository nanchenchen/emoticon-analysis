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


def create_a_lang_session_from_json(json_str, dataset_obj):
    """
    Given a dataset object, imports a participant from json string into
    the dataset.
    """
    data = AttributeDict(json.loads(json_str))
    lang_session = LanguageSession(dataset=dataset_obj, id=data.id,
                                   start_time=data.st_time, end_time=data.ed_time)
    lang_session.save()

    return lang_session


def update_a_lang_session_participant_from_json(json_str, dataset_obj):
    """
    Given a dataset object, imports a participant from json string into
    the dataset.
    """
    data = AttributeDict(json.loads(json_str))
    lang_session = LanguageSession.objects.get(id=data.lang_session_id)
    participant = Participant.objects.get(id=data.participant_id)
    lang_session.participants.add(participant)

    return lang_session


def update_a_lang_session_info_from_json(json_str, dataset_obj):
    """
    Given a dataset object, imports a participant from json string into
    the dataset.
    """
    data = AttributeDict(json.loads(json_str))
    lang_session = LanguageSession.objects.get(id=data.lang_session_id)
    lang_session.num_en = data.en_num
    lang_session.num_fr = data.fr_num
    lang_session.en_proportion = data.en_proportion
    lang_session.type = data["class"]
    lang_session.save()

    return lang_session


def update_message_lang_session_from_json(json_str, dataset_obj):
    """
    Given a dataset object, imports a participant from json string into
    the dataset.
    """
    data = AttributeDict(json.loads(json_str))
    message = Message.objects.get(id=data.point_id)
    message.lang_session_id = data.lang_session_id
    message.save()

    return message


def update_message_emotions_from_json(json_str, dataset_obj):
    """
    Given a dataset object, imports a participant from json string into
    the dataset.
    """
    data = AttributeDict(json.loads(json_str))
    message = Message.objects.get(id=data.mid)
    #emoticon = Emoticon.objects.get(id=data.eid)
    message.emoticons.add(data.eid)
    return message