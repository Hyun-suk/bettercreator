from django import template
from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from social_django.models import UserSocialAuth
from social_django.utils import load_strategy
from datetime import date
from dateutil.relativedelta import relativedelta
import requests
import json


def index(request):
    return render(request, 'index.html', {})

@login_required
def channels(request):
    strategy = load_strategy()
    current_user = User.objects.get(id = request.user.id)
    social = current_user.social_auth.get(provider='google-oauth2')
    social.refresh_token(strategy=strategy)

    request.session['access_token'] = social.extra_data['access_token']
    access_token = request.session['access_token']

    params = {
        'mine': True,
        'part': 'id,snippet',
        'access_token': request.session['access_token'],
    }

    response = requests.get(
        'https://www.googleapis.com/youtube/v3/channels',
        params=params
    )

    items = json.loads(response.text)['items']

    return render(
        request,
        'channels.html',
        {
            'channel_items': items,
        }
    )

@login_required
def detail(request, channel_id):
    current_user = User.objects.get(id = request.user.id)
    social = current_user.social_auth.get(provider='google-oauth2')
    social.refresh_token(load_strategy())

    request.session['access_token'] = social.extra_data['access_token']
    access_token = request.session['access_token']

    start_date = date.today() - relativedelta(months=1, days=1)
    end_date = date.today() - relativedelta(months=0, days=1)


    return render(
        request,
        'channel_detail.html',
        {
            'channel_info': get_channel_info(access_token, channel_id, start_date, end_date),
            'view_traffic_infos': get_view_traffic_info(access_token, channel_id, start_date, end_date),
            'watched_traffic_infos': get_watched_traffic_info(access_token, channel_id, start_date, end_date)
        }
    )

def get_channel_info(access_token, channel_id, start_date, end_date):
    params = {
        'ids': 'channel=={}'.format(channel_id),
        'dimensions': 'channel',
        'startDate': str(start_date),
        'endDate': str(end_date),
        'metrics': 'estimatedRevenue,subscribersGained,subscribersLost,views,averageViewDuration',
        'access_token': access_token,
    }

    response = requests.get(
        'https://youtubeanalytics.googleapis.com/v2/reports',
        params=params
    )

    return json.loads(response.text)['rows'][0]

def get_view_traffic_info(access_token, channel_id, start_date, end_date):

    params = {
        'ids': 'channel=={}'.format(channel_id),
        'dimensions': 'insightTrafficSourceDetail',
        'startDate': str(start_date),
        'endDate': str(end_date),
        'metrics': 'views',
        'filters': 'insightTrafficSourceType==YT_SEARCH',
        'maxResults': 25,
        'sort': '-views',
        'access_token': access_token,
    }

    response = requests.get(
        'https://youtubeanalytics.googleapis.com/v2/reports',
        params=params
    )

    view_traffic_sources = json.loads(response.text)['rows']

    total_views = 0
    for traffic_source in view_traffic_sources:
        total_views += traffic_source[1]

    view_traffic_infos = [(view_traffic_source[0], view_traffic_source[1]/total_views) for view_traffic_source in view_traffic_sources]

    return view_traffic_infos

def get_watched_traffic_info(access_token, channel_id, start_date, end_date):

    params = {
        'ids': 'channel=={}'.format(channel_id),
        'dimensions': 'insightTrafficSourceDetail',
        'startDate': str(start_date),
        'endDate': str(end_date),
        'metrics': 'estimatedMinutesWatched',
        'filters': 'insightTrafficSourceType==YT_SEARCH',
        'maxResults': 25,
        'sort': '-estimatedMinutesWatched',
        'access_token': access_token,
    }

    response = requests.get(
        'https://youtubeanalytics.googleapis.com/v2/reports',
        params=params
    )

    watched_traffic_sources = json.loads(response.text)['rows']

    total_watched = 0
    for traffic_source in watched_traffic_sources:
        total_watched += traffic_source[1]

    watched_traffic_infos = [(watched_traffic_source[0], watched_traffic_source[1]/total_watched) for watched_traffic_source in watched_traffic_sources]

    return watched_traffic_infos
