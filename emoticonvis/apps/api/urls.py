from django.conf.urls import url

from emoticonvis.apps.api import views
from django.views.decorators.csrf import csrf_exempt

api_root_urls = {

    'dataset': url(r'^dataset/$', csrf_exempt(views.DatasetView.as_view()), name='dataset'),
    'message': url(r'^message/(?P<message_id>[0-9]+)$', csrf_exempt(views.MessageView.as_view()), name='message'),
    'dictionary': url(r'^dictionary/$', csrf_exempt(views.DictionaryView.as_view()), name='dictionary'),

}

urlpatterns = api_root_urls.values() + [
    url(r'^$', views.APIRoot.as_view(root_urls=api_root_urls)),
]
