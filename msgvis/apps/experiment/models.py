from django.db import models
from msgvis.apps.corpus import models as corpus_models
from msgvis.apps.enhance import models as enhance_models
from msgvis.apps.coding import models as coding_models
from django.contrib.auth.models import User
from random import shuffle
from msgvis.apps.coding import utils as coding_utils
from msgvis.apps.base.utils import check_or_create_dir

def create_a_pair(output, default_stage):

    current_user_count = User.objects.count()

    # user 1
    username1 = "user_%03d" % (current_user_count + 1)
    password1 = User.objects.make_random_password()
    user1 = User.objects.create_user(username=username1,
                                     password=password1)

    # set the user to the default stage
    Progress.objects.get_or_create(user=user1, current_stage=default_stage)

    # user 2
    username2 = "user_%03d" % (current_user_count + 2)
    password2 = User.objects.make_random_password()
    user2 = User.objects.create_user(username=username2,
                                     password=password2)

    # set the user to the default stage
    Progress.objects.get_or_create(user=user2, current_stage=default_stage)

    pair = Pair()
    pair.save()
    pair.users.add(user1)
    pair.users.add(user2)

    print >> output, "Pair #%d" %(pair.id)
    print >> output, "username: %s | password: %s" %(username1, password1)
    print >> output, "username: %s | password: %s" %(username2, password2)

    return pair

class Experiment(models.Model):
    """
    A model for experiments
    """

    name = models.CharField(max_length=250, default=None, blank=True)
    """The experiment name."""

    description = models.TextField(default="", blank=True)
    """description of the experiments"""

    created_at = models.DateTimeField(auto_now_add=True)
    """The experiment created time"""

    dictionary = models.ForeignKey(enhance_models.Dictionary, related_name='experiments', default=None, null=True)
    """Which :class:`enhance_models.Dictionary` this experiment uses"""

    saved_path_root = models.FilePathField(default=None, blank=True, null=True)
    """The root path of this experiment.
       The svm model in scikit-learn format will be saved in the directories in this path."""

    @property
    def stage_count(self):
        return self.stages.count()

    @property
    def condition_count(self):
        return self.conditions.count()

    @property
    def user_count(self):
        return self.users.count()

    def __repr__(self):
        return self.name

    def __unicode__(self):
        return self.__repr__()

    def initialize_experiment(self, num_conditions, num_stages, num_pairs, output):

        print >>output, "Initializing the experiment with %d conditions." % num_conditions

        # create a list for saving conditions
        condition_list = []
        # create conditions
        for i in range(num_conditions):
            condition_name = "Condition %d" %(i + 1)
            condition = Condition(experiment=self, name=condition_name)
            condition.save()
            condition_list.append(condition)

        print >>output, "For each condition, users will go through %d stages." % num_stages
        # create a list for saving stages
        stage_list = []
        # create stages
        for i in range(1, num_stages + 1):
            stage = Stage(experiment=self, order=i)
            stage.save()
            stage_list.append(stage)

        # random assign messages
        # TODO: may change this to be done after each stage
        self.random_assign_messages()

        # create a stage for golden code data
        golden_stage = Stage(experiment=self, order=0)
        golden_stage.save()
        self.assign_messages_with_golden_code(golden_stage)

        print >>output, "Each condition has %d pairs." %num_pairs
        print >>output, "Pair list"
        print >>output, "========="
        # create a list for saving pairs
        pair_list = []
        num_total_pairs = num_conditions * num_pairs
        for i in range(num_total_pairs):
            pair = create_a_pair(output, default_stage=golden_stage)
            pair_list.append(pair)

        print >>output, "Assignment list"
        print >>output, "==============="
        # shuffle pair list for random assignment
        shuffle(pair_list)
        for idx, condition in enumerate(condition_list):
            print >>output, "\nIn %s" % condition.name
            for i in range(num_pairs):
                assignment = Assignment(pair=pair_list[idx * num_pairs + i],
                                        experiment=self,
                                        condition=condition)
                assignment.save()
                print >>output, "Pair #%d" %pair_list[idx * num_pairs + i].id

    def random_assign_messages(self):
        message_count = self.dictionary.dataset.get_messages_without_golden_code().count()
        messages = map(lambda x: x, self.dictionary.dataset.get_messages_without_golden_code())
        shuffle(messages)
        num_stages = self.stage_count
        num_per_stage = int(round(message_count / num_stages))

        start = 0
        end = num_per_stage
        for stage in self.stages.all():
            selection = []
            for idx, message in enumerate(messages[start:end]):
                item = MessageSelection(stage=stage, message=message, order=idx + 1)
                selection.append(item)
            MessageSelection.objects.bulk_create(selection)
            start += num_per_stage
            end += num_per_stage

    def assign_messages_with_golden_code(self, golden_stage):

        messages = map(lambda x: x, self.dictionary.dataset.get_messages_with_golden_code())

        selection = []
        for idx, message in enumerate(messages):
            item = MessageSelection(stage=golden_stage, message=message, order=idx + 1)
            selection.append(item)
        MessageSelection.objects.bulk_create(selection)

    def process_stage(self, stage, source, use_tfidf=False):
        features = list(self.dictionary.features.filter(source__isnull=True).all())
        features += list(source.features.filter(valid=True).all())
        messages = stage.messages.all()
        model_save_path = "%s/%s_stage%d/" % (self.saved_path_root, source.username, stage.order)
        check_or_create_dir(model_save_path)

        X, y, code_map_inverse = coding_utils.get_formatted_data(source=source, messages=messages, features=features)
        lin_clf = coding_utils.train_model(X, y, model_save_path=model_save_path)

        svm_model = coding_models.SVMModel(user=source, source_stage=stage, saved_path=model_save_path)
        svm_model.save()

        weights = []
        for code_index, code_id in code_map_inverse.iteritems():
            for feature_index, feature in enumerate(features):
                weight = lin_clf.coef_[code_index][feature_index]

                model_weight = coding_models.SVMModelWeight(svm_model=svm_model, code_id=code_id,
                                              feature=feature, weight=weight)

                weights.append(weights)

        coding_models.SVMModelWeight.objects.bulk_create(weights)

        next_stage = stage.get_next_stage()
        next_message_set = next_stage.messages.all()
        next_message_num = next_message_set.count()

        code_assignments = []
        next_X = coding_utils.get_formatted_X(messages=next_message_set, features=features)
        predict_y, prob = coding_utils.get_prediction(lin_clf, next_X)
        for idx in range(next_message_num):
            code_id = code_map_inverse[predict_y[idx]]
            probability = prob[idx]
            code_assignment = coding_models.CodeAssignment(source=source, code_id=code_id, is_user_label=False, probability=probability)
            code_assignments.append(code_assignment)
        coding_models.CodeAssignment.objects.bulk_create(code_assignments)



class Condition(models.Model):
    """
    A model for conditions in an experiment
    """

    name = models.CharField(max_length=250, default=None, blank=True)
    """The condition name."""

    description = models.TextField(default="", blank=True)
    """description of the condition"""

    experiment = models.ForeignKey(Experiment, related_name='conditions')
    """Which :class:`Experiment` this condition belongs to"""

    created_at = models.DateTimeField(auto_now_add=True)
    """The condition created time"""

    @property
    def user_count(self):
        return self.users.count()

    def __repr__(self):
        return "Experiment %s / Condition %s" % (self.experiment.name, self.name)

    def __unicode__(self):
        return self.__repr__()


class Stage(models.Model):
    """
    A model for stages in an experiment
    """

    order = models.IntegerField()

    experiment = models.ForeignKey(Experiment, related_name='stages')
    """Which :class:`Experiment` this condition belongs to"""

    created_at = models.DateTimeField(auto_now_add=True)
    """The condition created time"""

    messages = models.ManyToManyField(corpus_models.Message, related_name="stages", through="MessageSelection")
    svm_models = models.ManyToManyField(coding_models.SVMModel, related_name="source_stage")
    features = models.ManyToManyField(enhance_models.Feature, related_name="source_stage")

    @property
    def message_count(self):
        return self.messages.count()

    def __repr__(self):
        return "Experiment %s / Stage %d" % (self.experiment.name, self.order)

    def __unicode__(self):
        return self.__repr__()

    def get_next_stage(self):
        return self.experiment.stages.filter(order__gt=self.order).first()

    def get_messages_by_code(self, source, code):
        messages = self.messages.filter(message_selection__is_selected=True,
                                        code_assignments__valid=True,
                                        code_assignments__user=source,
                                        code_assignments__code=code).all()

        return messages

    class Meta:
        ordering = ['order']


class Pair(models.Model):
    """
    A model for assigning users to a pair
    """
    users = models.ManyToManyField(User, related_name="pair")

    def get_partner(self, current_user):
        for user in self.users.all():
            if user != current_user:
                return user


class Assignment(models.Model):
    """
    A model for assigning pairs to an experiment + a condition
    """
    pair = models.OneToOneField(Pair, related_name="assignment")
    experiment = models.ForeignKey(Experiment, related_name="assignments")
    condition = models.ForeignKey(Condition, related_name="assignments")


class MessageSelection(models.Model):
    """
    A model for saving message order in a stage
    """
    stage = models.ForeignKey(Stage)
    message = models.ForeignKey(corpus_models.Message, related_name="message_selection")
    order = models.IntegerField()
    is_selected = models.BooleanField(default=False)

    class Meta:
        ordering = ["order"]

    # TODO: add a field to subselect messages


class Progress(models.Model):
    """
    A model for recording a user's current stage
    """
    user = models.ForeignKey(User, related_name="progress", unique=True)
    current_stage = models.ForeignKey(Stage, related_name="progress")

    created_at = models.DateTimeField(auto_now_add=True)
    """The code created time"""

    last_updated = models.DateTimeField(auto_now_add=True, auto_now=True)
    """The code updated time"""

