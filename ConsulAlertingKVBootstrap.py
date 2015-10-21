import consulate
import json
import sys
import settings

blacklist_nodes = []
blacklist_services = []
blacklist_checks = []


health_check_tags = []


notify_plugins = ["hipchat","slack","mailgun","email","pagerduty"]

notify_hipchat= {"api_token":"",
                 "url":"",
                 "rooms":{}}

notify_slack= {"api_token":"",
                 "rooms":{}}

notify_mailgun= {"api_token":"",
                 "mailgun_domain":"",
                 "from": "",
                 "teams":{}
                 }

notify_email= {"mail_domain_address":"",
               "username":"",
               "password":"",
               "from": "",
               "teams":{}
                }

notify_pagerduty= {"teams":{}}


try:
    settings.consul.kv[settings.KV_ALERTING_HEALTH_CHECK_TAGS] = json.dumps(health_check_tags)

    settings.consul.kv[settings.KV_ALERTING_BLACKLIST_NODES] = json.dumps(blacklist_nodes)

    settings.consul.kv[settings.KV_ALERTING_BLACKLIST_SERVICES] = json.dumps(blacklist_services)

    settings.consul.kv[settings,KV_ALERTING_BLACKLIST_CHECKS] = json.dumps(blacklist_checks)

    settings.consul.kv[settings.KV_ALERTING_AVAILABLE_PLUGINS] = json.dumps(notify_plugins)

    settings.consul.kv[settings.KV_ALERTING_NOTIFY_HIPCHAT] = json.dumps(notify_hipchat)

    settings.consul.kv[settings.KV_ALERTING_NOTIFY_SLACK] = json.dumps(notify_slack)

    settings.consul.kv[settings.KV_ALERTING_NOTIFY_MAILGUN] = json.dumps(notify_mailgun)

    settings.consul.kv[settings.KV_ALERTING_NOTIFY_EMAIL] = json.dumps(notify_email)

    settings.consul.kv[settings.KV_ALERTING_NOTIFY_PAGERDUTY] = json.dumps(notify_pagerduty)

    settings.consul.kv[settings.KV_PRIOR_STATE] = []
except TypeError:
    print "One of the python data structures is not JSON serializable, may have accidentally created a set()"
    raise




