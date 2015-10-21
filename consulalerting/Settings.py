import sys
import logging
import consulate


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
KV_ALERTING_HASHES = "alerting/hashes"

WARNING_STATE = "warning"
CRITICAL_STATE = "critical"
PASSING_STATE = "passing"
UNKNOWN_STATE = "unknown"
ANY_STATE = "any"

CONSUL_HOST = "0.0.0.0"
CONSUL_PORT = 8500

if sys.version_info >= (2, 6, 0):
    consul = consulate.Consul(host=CONSUL_HOST,port=CONSUL_PORT)
    consul._adapter.timeout = 5
else:
    consul = consulate.Consulate(host=CONSUL_HOST,port=CONSUL_PORT)
    consul._adapter.timeout = 5

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if sys.version_info >= (2, 7, 0):
    handler = logging.StreamHandler(stream=sys.stdout)
else:
    handler = logging.StreamHandler(strm=sys.stdout)

handler.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s Filename= %(filename)s Level= %(levelname)s "
                              "LineNumber=%(lineno)d %(message)s")

handler.setFormatter(formatter)

logger.addHandler(handler)