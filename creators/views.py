from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from social_django.models import UserSocialAuth
from social_django.utils import load_strategy
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
