from django.views import generic
from django.http import Http404
from django.utils.translation import ugettext as _

from msgvis.apps.corpus import models as corpus_models
from msgvis.apps.enhance import models as enhance_models
from django.contrib.auth.decorators import login_required


class LoginRequiredMixin(object):
    """A mixin that forces a login to view the CBTemplate."""

    @classmethod
    def as_view(cls, **initkwargs):
        view = super(LoginRequiredMixin, cls).as_view(**initkwargs)
        return login_required(view)

class HomeView(LoginRequiredMixin, generic.TemplateView):
    """The homepage view for the website."""

    template_name = 'home.html'


class ExplorerView(generic.DetailView):
    """The view for the visualization tool."""

    template_name = 'explorer.html'

    pk_url_kwarg = 'dataset_pk'
    default_dataset_pk = 1

    def get_queryset(self):
        return corpus_models.Dataset.objects.all()


    def get_object(self, queryset=None):

        if queryset is None:
            queryset = self.get_queryset()

        pk = self.kwargs.get(self.pk_url_kwarg, None)
        if pk is None:
            pk = self.default_dataset_pk
            
        queryset = queryset.filter(pk=pk)

        try:
            # Get the single item from the filtered queryset
            obj = queryset.get()
        except queryset.model.DoesNotExist:
            raise Http404(_("No %(verbose_name)s found matching the query") %
                          {'verbose_name': queryset.model._meta.verbose_name})
        return obj


class GrouperView(LoginRequiredMixin, generic.DetailView):
    """The view for the visualization tool."""

    template_name = 'grouper.html'

    pk_url_kwarg = 'dataset_pk'
    default_dataset_pk = 1

    def get_queryset(self):
        return corpus_models.Dataset.objects.all()


    def get_object(self, queryset=None):

        if queryset is None:
            queryset = self.get_queryset()

        pk = self.kwargs.get(self.pk_url_kwarg, None)
        if pk is None:
            pk = self.default_dataset_pk

        queryset = queryset.filter(pk=pk)

        try:
            # Get the single item from the filtered queryset
            obj = queryset.get()
        except queryset.model.DoesNotExist:
            raise Http404(_("No %(verbose_name)s found matching the query") %
                          {'verbose_name': queryset.model._meta.verbose_name})
        return obj

class TextCoderView(LoginRequiredMixin, generic.DetailView):
    """The view for the visualization tool."""

    template_name = 'textcoder.html'

    pk_url_kwarg = 'dictionary_pk'
    default_dictionary_pk = 1

    def get_queryset(self):
        return enhance_models.Dictionary.objects.all()


    def get_object(self, queryset=None):

        if queryset is None:
            queryset = self.get_queryset()

        pk = self.kwargs.get(self.pk_url_kwarg, None)
        if pk is None:
            pk = self.default_dictionary_pk

        queryset = queryset.filter(pk=pk)

        try:
            # Get the single item from the filtered queryset
            obj = queryset.get()
        except queryset.model.DoesNotExist:
            raise Http404(_("No %(verbose_name)s found matching the query") %
                          {'verbose_name': queryset.model._meta.verbose_name})
        return obj

class TweetCoderView(generic.DetailView):
    """The view for the visualization tool."""

    template_name = 'tweetcoder.html'

    pk_url_kwarg = 'dictionary_pk'
    default_dictionary_pk = 1

    def get_queryset(self):
        return enhance_models.Dictionary.objects.all()


    def get_object(self, queryset=None):

        if queryset is None:
            queryset = self.get_queryset()

        pk = self.kwargs.get(self.pk_url_kwarg, None)
        if pk is None:
            pk = self.default_dictionary_pk

        queryset = queryset.filter(pk=pk)

        try:
            # Get the single item from the filtered queryset
            obj = queryset.get()
        except queryset.model.DoesNotExist:
            raise Http404(_("No %(verbose_name)s found matching the query") %
                          {'verbose_name': queryset.model._meta.verbose_name})
        return obj

class TweetCoderVizView(generic.DetailView):
    """The view for the visualization tool."""

    template_name = 'tweetcoderviz.html'

    pk_url_kwarg = 'dictionary_pk'
    default_dictionary_pk = 1

    def get_queryset(self):
        return enhance_models.Dictionary.objects.all()


    def get_object(self, queryset=None):

        if queryset is None:
            queryset = self.get_queryset()

        pk = self.kwargs.get(self.pk_url_kwarg, None)
        if pk is None:
            pk = self.default_dictionary_pk

        queryset = queryset.filter(pk=pk)

        try:
            # Get the single item from the filtered queryset
            obj = queryset.get()
        except queryset.model.DoesNotExist:
            raise Http404(_("No %(verbose_name)s found matching the query") %
                          {'verbose_name': queryset.model._meta.verbose_name})
        return obj