from django.test import TestCase
from django.utils.timezone import now, timedelta
from emoticonvis.apps.corpus import models as corpus_models
from emoticonvis.apps.corpus import utils as corpus_utils
from emoticonvis.apps.coding import models as coding_models
from emoticonvis.apps.api import serializers
from django.contrib.auth.models import User

from emoticonvis.apps.api.tests import api_time_format


class CodeSerializerTest(TestCase):
    """

    """

    def test_code_definition_serialization(self):
        master = User.objects.create_user(username='master')
        user1 = User.objects.create_user(username='user1')
        code = corpus_models.Code.objects.create(text='testcode')
        dataset = corpus_models.Dataset.objects.create(name='test', description='test')
        messages = [corpus_models.Message.objects.create(dataset=dataset, text='msg0'),
                    corpus_models.Message.objects.create(dataset=dataset, text='msg1'),
                    corpus_models.Message.objects.create(dataset=dataset, text='msg2')]

        code_definition1 = coding_models.CodeDefinition.objects.create(code=code, source=master, text='master_def')
        code_definition1.examples.add(messages[0])
        code_definition1.examples.add(messages[2])

        code_definition2 = coding_models.CodeDefinition.objects.create(code=code, source=user1, text='user1_def')
        code_definition2.examples.add(messages[1])
        code_definition2.examples.add(messages[2])

        desired_result = [
            {
                "code": code.text,
                "source": "master",
                "text": "master_def",
                "examples": [serializers.MessageSerializer(messages[0]).data, serializers.MessageSerializer(messages[2]).data]
            },
            {
                "code": code.text,
                "source": "user1",
                "text": "user1_def",
                "examples": [serializers.MessageSerializer(messages[1]).data, serializers.MessageSerializer(messages[2]).data]
            }
        ]

        code_definitions = [code.get_definition(master), code.get_definition(user1)]

        serializer = serializers.CodeDefinitionSerializer(code_definitions, many=True)
        try:
            result = serializer.data
            self.assertListEqual(result, desired_result)
        except:
            import pdb
            pdb.set_trace()


    def test_code_message_serialization(self):
        master = User.objects.create_user(username='master')
        code = corpus_models.Code.objects.create(text='testcode')
        code2 = corpus_models.Code.objects.create(text='testcode2')
        dataset = corpus_models.Dataset.objects.create(name='test', description='test')
        messages = [corpus_models.Message.objects.create(dataset=dataset, text='msg0'),
                    corpus_models.Message.objects.create(dataset=dataset, text='msg1'),
                    corpus_models.Message.objects.create(dataset=dataset, text='msg2')]

        code_assignment1 = coding_models.CodeAssignment.objects.create(code=code, source=master, message=messages[0])
        code_assignment2 = coding_models.CodeAssignment.objects.create(code=code, source=master, message=messages[1])
        code_assignment3 = coding_models.CodeAssignment.objects.create(code=code2, source=master, message=messages[1])



        desired_result = [
            {
                "code": code.text,
                "source": "master",
                "messages": [serializers.MessageSerializer(messages[0]).data, serializers.MessageSerializer(messages[1]).data]
            },
            {
                "code": code2.text,
                "source": "master",
                "messages": [serializers.MessageSerializer(messages[1]).data]
            }
        ]

        source = master
        codes = [code.text, code2.text]
        code_messages = []
        for code in codes:
            if corpus_models.Code.objects.filter(text=code).exists():
                code_obj = corpus_models.Code.objects.get(text=code)
                messages = corpus_models.Message.objects.filter(code_assignments__valid=True,
                                                                code_assignments__source=source,
                                                                code_assignments__code=code_obj).all()
                code_messages.append({
                    "code": code,
                    "source": source,
                    "messages": messages,
                })

        serializer = serializers.CodeMessageSerializer(code_messages, many=True)
        try:
            result = serializer.data
            self.assertListEqual(result, desired_result)
        except:
            import pdb
            pdb.set_trace()
