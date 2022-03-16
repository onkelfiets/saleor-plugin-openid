from typing import Optional

# from authlib.integrations.requests_client import OAuth2Session
from django.core.handlers.wsgi import WSGIRequest
from saleor.account.models import User
from saleor.core.auth import get_token_from_request
from saleor.core.jwt import get_user_from_access_payload, jwt_decode
from saleor.plugins.base_plugin import BasePlugin, ConfigurationTypeField

import jwt  # PyJWT
from jwt import PyJWKClient


from .dataclasses import Auth0AuthConfig
from .util import get_token_auth_header


class Auth0AuthPlugin(BasePlugin):
    PLUGIN_ID = "toastedtoast.authentication.openidauth"
    PLUGIN_NAME = "Auth0 Auth"

    DEFAULT_CONFIGURATION = [
        {"name": "domain", "value": None},
        {"name": "client_id", "value": None},
        {"name": "client_secret", "value": None},
        {"name": "json_web_key_set_url", "value": None},
    ]

    CONFIG_STRUCTURE = {
        "domain": {
            "type": ConfigurationTypeField.STRING,
            "help_text": ("Your Domain required to authenticate on the provider side."),
            "label": "Domain",
        },
        "client_id": {
            "type": ConfigurationTypeField.STRING,
            "help_text": (
                "Your Client ID required to authenticate on the provider side."
            ),
            "label": "Client ID",
        },
        "client_secret": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": (
                "Your client secret required to authenticate on provider side."
            ),
            "label": "Client Secret",
        },
        "json_web_key_set_url": {
            "type": ConfigurationTypeField.STRING,
            "help_text": (
                "The JSON Web Key Set (JWKS) is a set of keys containing the public "
                "keys used to verify any JSON Web Token (JWT) issued by the "
                "authorization server and signed using the RS256 signing algorithm."
            ),
            "label": "JSON Web Key Set URL",
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Convert to dict to easier take config elements
        configuration = {item["name"]: item["value"] for item in self.configuration}
        self.config = Auth0AuthConfig(
            domain=configuration["domain"],
            client_id=configuration["client_id"],
            client_secret=configuration["client_secret"],
            json_web_key_set_url=configuration["json_web_key_set_url"],
        )
        # self.oauth = self._get_oauth_session()

    # def _get_oauth_session(self):
    #     scope = "openid profile email"
    #     # if self.config.enable_refresh_token:
    #     #     scope += " offline_access"
    #     return OAuth2Session(
    #         client_id=self.config.client_id,
    #         client_secret=self.config.client_secret,
    #         scope=scope,
    #     )

    def authenticate_user(self, request: WSGIRequest, previous_value) -> Optional[User]:
        if not self.active:
            return previous_value

        print(request)
        token = get_token_auth_header(request)
        if token:
            raise Exception(f"Token found: {token}")
            return previous_value

        jwks_client = PyJWKClient(self.config.json_web_key_set_url)
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        if not signing_key:
            raise Exception(f"No signing key found: {token}")
            return previous_value

        data = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience="https://core.unverpackt-riedberg.de",
        )

        if not data:
            raise Exception(f"Decode data failed: {token}")
            return previous_value

        print(data)
        return previous_value

        return get_user_from_access_payload(payload)
