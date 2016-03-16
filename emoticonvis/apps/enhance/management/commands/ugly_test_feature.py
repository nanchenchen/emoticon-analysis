import unittest
from django.core.management.base import BaseCommand, make_option, CommandError
from emoticonvis.apps.enhance.models import Dictionary, MessageFeature, Feature


class ParametrizedTestCase(unittest.TestCase):
    """ TestCase classes that want to be parametrized should
        inherit from this class.
    """
    def __init__(self, methodName='runTest', param=None):
        super(ParametrizedTestCase, self).__init__(methodName)
        self.param = param

    @staticmethod
    def parametrize(testcase_klass, param=None):
        """ Create a suite containing all tests taken from the given
            subclass, passing them the parameter 'param'.
        """
        testloader = unittest.TestLoader()
        testnames = testloader.getTestCaseNames(testcase_klass)
        suite = unittest.TestSuite()
        for name in testnames:
            suite.addTest(testcase_klass(name, param=param))
        return suite

class TestFeature(ParametrizedTestCase):

    def test_is_in_message(self):
        feature = ['girlfriend were', 'propose']
        dictionary = self.param

        message_1 = 'Omg this guy & his girlfriend were running the marathon in Boston. His girlfriend died, & he was going to propose to her. So heartbreaking.'
        message_2 = 'He was going to propose and his girlfriend were running the marathon'
        message_3 = 'My question is. what was an 8 year old girl doing running a marathon that long..?'
        message_4 = 'He was going to propose, but his girlfriend did not want to get married'

        self.assertEqual(dictionary.is_user_feature_in_message(feature, message_1), True)
        self.assertEqual(dictionary.is_user_feature_in_message(feature, message_2), True)
        self.assertEqual(dictionary.is_user_feature_in_message(feature, message_3), False)    
        self.assertEqual(dictionary.is_user_feature_in_message(feature, message_4), False)

    def test_get_last_feature_index(self):
        dictionary = self.param

        dictionary_last_feature_index = dictionary.get_last_feature_index()
        self.assertEqual(dictionary_last_feature_index, 198)

    def test_add_feature(self):
        dictionary = self.param

        dictionary_last_feature_index = dictionary.get_last_feature_index()

        raw_feature = ['finish line', 'boyfriend', 'girl']
        feature = dictionary.add_feature(raw_feature)

        self.assertEqual(feature.index, dictionary_last_feature_index + 1)
        self.assertEqual(feature.document_frequency, 5)
        self.assertEqual(MessageFeature.objects.filter(feature_index=feature.index).count(), 5)

        Feature.objects.filter(index=feature.index).delete()

class Command(BaseCommand):
    help = "Extract topics for a dataset."
    args = "<dataset id>"
    option_list = BaseCommand.option_list + (
        make_option('--name',
                    dest='name',
                    default='my topic model',
                    help="The name for your keyword dictionary"),
    )

    def handle(self, dataset_id, *args, **options):
        name = options.get('name')

        if not dataset_id:
            raise CommandError("Dataset id is required.")
        try:
            dataset_id = int(dataset_id)
        except ValueError:
            raise CommandError("Dataset id must be a number.")

        dictionary = Dictionary.objects.filter(dataset_id=dataset_id).first()
        
        suite = unittest.TestSuite()
        suite.addTest(ParametrizedTestCase.parametrize(TestFeature, param=dictionary))
        unittest.TextTestRunner().run(suite)
    
