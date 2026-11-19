"""Narrow publisher redirect wait checks; host/TLS/body validation stays caller-owned."""
import re


class PublisherRedirectHold(ValueError):
    """The redirect's minimum wait is not proven satisfied by this operation."""


def redirect_wait_satisfied(status, headers):
    """Accept absent Retry-After or one parsed zero delay on an HTTP redirect.

    RFC 9110 section 10.2.3 applies Retry-After on a 3xx response to the
    subsequent redirected request. Only zero delay-seconds is satisfied here;
    positive delays, dates, malformed values and duplicates retain a hold.
    This function never grants permission for a final 200, 401, 403 or 429.
    """
    if type(status) is not int or status not in (301, 302, 303, 307, 308):
        raise PublisherRedirectHold('publisher_redirect_status_required')
    if not callable(getattr(headers, 'get_all', None)):
        raise PublisherRedirectHold('publisher_retry_after_header_inventory_required')
    values = headers.get_all('Retry-After', [])
    if not values:
        return {'retry_after_state': 'absent', 'minimum_delay_seconds': 0}
    if len(values) != 1:
        raise PublisherRedirectHold('publisher_duplicate_retry_after')
    value = values[0]
    if not isinstance(value, str) or not re.fullmatch(r'[ \t]*0+[ \t]*', value):
        raise PublisherRedirectHold('publisher_redirect_retry_after')
    return {'retry_after_state': 'zero_delay_satisfied', 'minimum_delay_seconds': 0}
