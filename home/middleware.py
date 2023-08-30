from datetime import datetime, timedelta
from django.conf import settings
from django.shortcuts import redirect

class AutoLogoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            current_time = datetime.now()
            last_activity_time = request.session.get('last_activity_time')

            if last_activity_time:
                last_activity_time = datetime.strptime(last_activity_time, '%Y-%m-%d %H:%M:%S')

                if current_time > last_activity_time + timedelta(minutes=settings.AUTO_LOGOUT_INTERVAL):
                    redirect_url = settings.AUTO_LOGOUT_REDIRECT_URL
                    response = redirect(redirect_url)
                    response.delete_cookie(settings.SESSION_COOKIE_NAME)
                    return response

            request.session['last_activity_time'] = current_time.strftime('%Y-%m-%d %H:%M:%S')

        response = self.get_response(request)
        return response