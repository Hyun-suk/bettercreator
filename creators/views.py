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

    channel_info = json.loads(response.text)['rows'][0]

    params = {
        'ids': 'channel=={}'.format(channel_id),
        'dimensions': 'insightTrafficSourceDetail',
        'startDate': str(start_date),
        'endDate': str(end_date),
        'metrics': 'views,estimatedMinutesWatched',
        'filters': 'insightTrafficSourceType==YT_SEARCH',
        'maxResults': 10,
        'sort': '-views',
        'access_token': access_token,
    }

    response = requests.get(
        'https://youtubeanalytics.googleapis.com/v2/reports',
        params=params
    )

    traffic_sources = json.loads(response.text)['rows']

    return render(
        request,
        'channel_detail.html',
        {
            'channel_info': channel_info,
            'traffic_sources': traffic_sources
        }
    )
