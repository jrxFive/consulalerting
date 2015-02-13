class ConsulAlerting(object):

    KV_ALERTING_BLACKLIST_NODES = "alerting/blacklist/nodes"
    KV_ALERTING_BLACKLIST_SERVICES = "alerting/blacklist/services"
    KV_ALERTING_BLACKLIST_CHECKS = "alerting/blacklist/checks"
    KV_ALERTING_BLACKLIST_NODE_CHECKS = "alerting/blacklist/nodechecks"
    KV_ALERTING_HEALTH_CHECK_TAGS = "alerting/healthchecktags"
    KV_ALERTING_NOTIFY_HIPCHAT = "alerting/notify/hipchat"
    KV_PRIOR_STATE = "alerting/prior"

    WARNING_STATE = "warning"
    CRITICAL_STATE = "critical"
    PASSING_STATE = "passing"
    UNKNOWN_STATE = "unknown"
    ANY_STATE = "any"
    def __init__(self):
        pass
