from django import template
from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from social_django.models import UserSocialAuth
from social_django.utils import load_strategy
from datetime import date
from dateutil.relativedelta import relativedelta
from . import apis


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

    channel_items = apis.get_channel_items(access_token)
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
            'channel_info': apis.get_channel_analytics_info(access_token, channel_id, start_date, end_date),
            'view_traffic_infos': apis.get_view_traffic_info(access_token, channel_id, start_date, end_date),
            'watched_traffic_infos': apis.get_watched_traffic_info(access_token, channel_id, start_date, end_date),
            'most_watched_videos': apis.get_most_watched_videos(access_token, start_date, end_date),
            'external_traffics': apis.get_external_traffics(access_token, channel_id, start_date, end_date),
        }
    )
