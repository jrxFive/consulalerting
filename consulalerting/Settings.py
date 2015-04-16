import sys
import logging


class Settings(object):
    KV_ALERTING_BLACKLIST_NODES = "alerting/blacklist/nodes"
    KV_ALERTING_BLACKLIST_SERVICES = "alerting/blacklist/services"
    KV_ALERTING_BLACKLIST_CHECKS = "alerting/blacklist/checks"

    KV_ALERTING_HEALTH_CHECK_TAGS = "alerting/healthchecktags"

    KV_ALERTING_AVAILABLE_PLUGINS = "alerting/notify/plugins"
    KV_ALERTING_NOTIFY_HIPCHAT = "alerting/notify/hipchat"
    KV_ALERTING_NOTIFY_SLACK = "alerting/notify/slack"
    KV_ALERTING_NOTIFY_MAILGUN = "alerting/notify/mailgun"
    KV_ALERTING_NOTIFY_EMAIL = "alerting/notify/email"
    KV_ALERTING_NOTIFY_PAGERDUTY = "alerting/notify/pagerduty"

    KV_PRIOR_STATE = "alerting/prior"

    WARNING_STATE = "warning"
    CRITICAL_STATE = "critical"
    PASSING_STATE = "passing"
    UNKNOWN_STATE = "unknown"
    ANY_STATE = "any"

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.WARN)

    if sys.version_info > (2, 6, 0):
        handler = logging.StreamHandler(stream=sys.stdout)
    else:
        handler = logging.StreamHandler(strm=sys.stdout)

    handler.setLevel(logging.WARN)

    formatter = logging.Formatter(
        '%(asctime)s \
        Filename=%(filename)s \
        Level=%(levelname)s \
        LineNumber=%(lineno)d \
        %(message)s')

    handler.setFormatter(formatter)

    logger.addHandler(handler)

    def __init__(self):
        pass
