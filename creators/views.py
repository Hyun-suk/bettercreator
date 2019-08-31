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

    channel_items = get_channel_items(access_token)
    request.session['channel_items'] = channel_items

    return render(
        request,
        'channels.html',
        {
            'channel_items': channel_items
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

    channel_items = request.session['channel_items']
    for num, item in enumerate(channel_items):
        if item['id'] == channel_id:
            break

    return render(
        request,
        'channel_detail.html',
        {
            'channel_item': channel_items[num],
            'channel_info': get_channel_analytics_info(access_token, channel_id, start_date, end_date),
            'view_traffic_infos': get_view_traffic_info(access_token, channel_id, start_date, end_date),
            'watched_traffic_infos': get_watched_traffic_info(access_token, channel_id, start_date, end_date),
            'most_watched_videos': get_most_watched_videos(access_token, start_date, end_date),
            'external_traffics': get_external_traffics(access_token, channel_id, start_date, end_date),
        }
    )

def get_channel_analytics_info(access_token, channel_id, start_date, end_date):
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

def get_channel_items(access_token):
    params = {
        'part': 'id,snippet,statistics',
        'mine': True,
        'access_token': access_token,
    }

    response = requests.get(
        'https://www.googleapis.com/youtube/v3/channels',
        params=params
    )

    return json.loads(response.text)['items']

def get_most_watched_videos(access_token, start_date, end_date):
    params = {
        'dimensions': 'video',
        'ids': 'channel==MINE',
        'metrics': 'estimatedMinutesWatched,views,likes,subscribersGained',
        'maxResults': 10,
        'sort': '-estimatedMinutesWatched',
        'access_token': access_token,
        'startDate': str(start_date),
        'endDate': str(end_date),
    }

    response = requests.get(
        'https://youtubeanalytics.googleapis.com/v2/reports',
        params=params
    )

    most_watched_videos = json.loads(response.text)['rows']

    ids = list()
    for video in most_watched_videos:
        ids.append(video[0])
    ids = ','.join(ids)

    params = {
        'part': 'snippet',
        'id': ids,
        'access_token': access_token,
    }

    response = requests.get(
        'https://www.googleapis.com/youtube/v3/videos',
        params=params
    )

    video_infos = json.loads(response.text)['items']

    return zip(most_watched_videos, video_infos)

def get_external_traffics(access_token, channel_id, start_date, end_date):
    params = {
        'dimensions': 'insightTrafficSourceDetail',
        'ids': 'channel=={}'.format(channel_id),
        'metrics': 'estimatedMinutesWatched,views',
        'filters': 'insightTrafficSourceType==EXT_URL',
        'maxResults': 25,
        'sort': '-views',
        'access_token': access_token,
        'startDate': str(start_date),
        'endDate': str(end_date),
    }

    response = requests.get(
        'https://youtubeanalytics.googleapis.com/v2/reports',
        params=params
    )

    return json.loads(response.text)['rows']
