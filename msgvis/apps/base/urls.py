from django.conf.urls import patterns, include, url
from django.contrib import admin

from msgvis.apps.base import views

urlpatterns = patterns('',
                       url(r'^$', views.HomeView.as_view(), name='home'),
                       # url(r'^explorer/$', views.ExplorerView.as_view(), name='explorer'),
                       (r'^accounts/logout/$', 'django.contrib.auth.views.logout',{'next_page': '/'}),
                       url(r'^accounts/', include('django.contrib.auth.urls')),
                       url(r'^textcoder(?:/(?P<dictionary_pk>\d+))?/$', views.TextCoderView.as_view(), name='textcoder'),
                       url(r'^tweetcoder(?:/(?P<dictionary_pk>\d+))?/$', views.TweetCoderView.as_view(), name='tweetcoder'),
                       url(r'^tweetcoderviz(?:/(?P<dictionary_pk>\d+))?/$', views.TweetCoderVizView.as_view(), name='tweetcoderviz'),
)
