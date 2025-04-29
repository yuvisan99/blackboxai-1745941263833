from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class RollNoBackend(BaseBackend):
    def authenticate(self, request, number=None, roll_no=None, password=None, **kwargs):
        try:
            try:
                user = User.objects.get(roll_no=roll_no)
            except User.DoesNotExist:
                user = User.objects.get(number=number)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None
