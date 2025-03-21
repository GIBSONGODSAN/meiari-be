
from .models import MeiAriUser
from rest_framework.authentication import BaseAuthentication
from rest_framework.authentication import get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
import jwt


class MeiAriUserTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        try:
            print("Authenticating user...")
            token = get_authorization_header(request).decode("utf-8").split()

            if len(token) != 2:
                raise AuthenticationFailed("Invalid token format.")

            decoded_token = jwt.decode(token[1], settings.SECRET_KEY, algorithms=["HS256"])
            user = MeiAriUser.objects.filter(id=decoded_token["id"]).first()

            if not user:
                raise AuthenticationFailed("User not found.")

            return user, decoded_token  # Return user and token payload

        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Token has expired.")
        except jwt.InvalidTokenError:
            raise AuthenticationFailed("Invalid token.")
        except Exception as e:
            print(f"Authentication error: {e}")
            raise AuthenticationFailed("Authentication failed.")