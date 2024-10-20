# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from typing import Any

from ldap3 import (
    Server,
    Connection,
    AUTO_BIND_NO_TLS,
    AUTO_BIND_TLS_BEFORE_BIND,
    ANONYMOUS,
    SIMPLE,
    SYNC,
    SUBTREE,
    NONE,
)

from django.conf import settings
from ldap3.utils.conv import escape_filter_chars
from taiga.base.connectors.exceptions import ConnectorBaseException


class LDAPError(ConnectorBaseException):
    pass


class LDAPConnectionError(LDAPError):
    pass


class LDAPUserLoginError(LDAPError):
    pass


# TODO https://github.com/Monogramm/taiga-contrib-ldap-auth-ext/issues/16
SERVER = getattr(settings, "LDAP_SERVER", "localhost")
PORT = getattr(settings, "LDAP_PORT", "389")

SEARCH_BASE = getattr(settings, "LDAP_SEARCH_BASE", "")
SEARCH_FILTER_ADDITIONAL = getattr(settings, "LDAP_SEARCH_FILTER_ADDITIONAL", "")
BIND_DN = getattr(settings, "LDAP_BIND_DN", "")
BIND_WITH_USER_PROVIDED_CREDENTIALS = getattr(
    settings, "LDAP_BIND_WITH_USER_PROVIDED_CREDENTIALS", False
)
BIND_PASSWORD = getattr(settings, "LDAP_BIND_PASSWORD", "")

USERNAME_ATTRIBUTE = getattr(settings, "LDAP_USERNAME_ATTRIBUTE", "uid")
EMAIL_ATTRIBUTE = getattr(settings, "LDAP_EMAIL_ATTRIBUTE", "mail")
FULL_NAME_ATTRIBUTE = getattr(settings, "LDAP_FULL_NAME_ATTRIBUTE", "displayName")
PROFILE_ATTRIBUTES = [USERNAME_ATTRIBUTE, EMAIL_ATTRIBUTE, FULL_NAME_ATTRIBUTE]

TLS_CERTS = getattr(settings, "LDAP_TLS_CERTS", "")
START_TLS = getattr(settings, "LDAP_START_TLS", False)


def _get_server() -> Server:
    """Connect to an LDAP server (no authentication yet)."""
    tls = TLS_CERTS or None
    use_ssl = SERVER.lower().startswith("ldaps://")

    try:
        return Server(SERVER, port=PORT, get_info=NONE, use_ssl=use_ssl, tls=tls)
    except Exception as e:
        error = "Error connecting to LDAP server: %s" % e
        raise LDAPConnectionError({"error_message": error})


def _get_auth_details(
    username_sanitized: str, user_provided_password: str
) -> dict[str, Any]:
    """
    Return a dictionary with LDAP auth credentials.

    The dictionary contains the following fields:

    - "user": DN of the user to bind with
    - "password": Password of the user to bind with
    - "authentication": Bind method

    The bind method may be SIMPLE or ANONYMOUS.
    The user to bind with may be a dedicated bind user, or a dynamically
    determined DN from the provided user credentials.
    """

    if BIND_WITH_USER_PROVIDED_CREDENTIALS:
        # Authenticate using the provided user credentials
        user = BIND_DN.replace("<username>", username_sanitized)
        password = user_provided_password
        authentication = SIMPLE
    elif BIND_DN:
        # Authenticate with dedicated bind credentials
        user = BIND_DN
        password = BIND_PASSWORD
        authentication = SIMPLE
    else:
        # Use anonymous auth
        user = None
        password = None
        authentication = ANONYMOUS

    return {"user": user, "password": password, "authentication": authentication}


def _extract_user(response: Any) -> Any:
    """Extract a single user object from the LDAP response.

    Throw an error if there is not exactly 1 user in the response."""

    users_found = [r for r in response if "raw_attributes" in r and "dn" in r]

    # stop if no search results
    if not users_found:
        raise LDAPUserLoginError({"error_message": "LDAP login not found"})

    # handle multiple matches
    if len(users_found) > 1:
        raise LDAPUserLoginError(
            {"error_message": "LDAP login could not be determined."}
        )

    return users_found[0]


def _extract_profile(raw_attributes: Any) -> tuple[str, str, str]:
    """Extract the profile from the given user's attributes.

    The profile consists of the following attributes:

    - Username
    - Email
    - Full name

    Throw an error if the attributes are not all set."""
    for attribute in PROFILE_ATTRIBUTES:
        if not raw_attributes.get(attribute):
            raise LDAPUserLoginError({"error_message": "LDAP login is invalid."})

    return (
        raw_attributes.get(attribute)[0].decode("utf-8")
        for attribute in PROFILE_ATTRIBUTES
    )


def login(username_or_email: str, password: str) -> tuple[str, str, str]:
    """
    Connect to LDAP server, perform a search and attempt a bind.

    Can raise `exc.LDAPConnectionError` exceptions if the
    connection to LDAP fails.

    Can raise `exc.LDAPUserLoginError` exceptions if the
    login to LDAP fails.

    :param username_or_email: a possibly unsanitized username or email
    :param password: a possibly unsanitized password
    :returns: tuple (username, email, full_name)
    """
    server = _get_server()
    username_or_email_sanitized = escape_filter_chars(username_or_email)
    auto_bind = AUTO_BIND_TLS_BEFORE_BIND if START_TLS else AUTO_BIND_NO_TLS

    try:
        c = Connection(
            server,
            auto_bind=auto_bind,
            client_strategy=SYNC,
            check_names=True,
            **_get_auth_details(username_or_email_sanitized, password),
        )
    except Exception as e:
        error = "Error connecting to LDAP server: %s" % e
        raise LDAPConnectionError({"error_message": error})

    # search for user-provided login
    search_filter = f"(|({USERNAME_ATTRIBUTE}={username_or_email_sanitized})({EMAIL_ATTRIBUTE}={username_or_email_sanitized}))"
    if SEARCH_FILTER_ADDITIONAL:
        search_filter = f"(&{search_filter}{SEARCH_FILTER_ADDITIONAL})"
    try:
        c.search(
            search_base=SEARCH_BASE,
            search_filter=search_filter,
            search_scope=SUBTREE,
            attributes=PROFILE_ATTRIBUTES,
            paged_size=5,
        )
    except Exception as e:
        error = "LDAP login incorrect: %s" % e
        raise LDAPUserLoginError({"error_message": error})

    user = _extract_user(c.response)
    raw_attributes = user.get("raw_attributes")
    user_profile = _extract_profile(raw_attributes)

    # attempt LDAP bind
    try:
        dn = str(bytes(user.get("dn"), "utf-8"), encoding="utf-8")
        Connection(
            server,
            auto_bind=auto_bind,
            client_strategy=SYNC,
            check_names=True,
            authentication=SIMPLE,
            user=dn,
            password=password,
        )
    except Exception as e:
        error = "LDAP bind failed: %s" % e
        raise LDAPUserLoginError({"error_message": error})

    # Return user profile so that it can be used by Taiga,
    # e.g., to set the user's full name in the database
    return user_profile
