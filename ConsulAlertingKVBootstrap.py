import consulate
import simplejson as json

blacklist_nodes = []
blacklist_services = []
blacklist_checks = []


health_check_tags = []


notify_plugins = ["hipchat","slack","mailgun","email"]

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


consulate_session = consulate.Consulate()

try:
    consulate_session.kv["alerting/healthchecktags"] = json.dumps(health_check_tags)

    consulate_session.kv["alerting/blacklist/nodes"] = json.dumps(blacklist_nodes)

    consulate_session.kv["alerting/blacklist/services"] = json.dumps(blacklist_services)

    consulate_session.kv["alerting/blacklist/checks"] = json.dumps(blacklist_checks)

    consulate_session.kv["alerting/notify/plugins"] = json.dumps(notify_plugins)

    consulate_session.kv["alerting/notify/hipchat"] = json.dumps(notify_hipchat)

    consulate_session.kv["alerting/notify/slack"] = json.dumps(notify_slack)

    consulate_session.kv["alerting/notify/mailgun"] = json.dumps(notify_mailgun)

    consulate_session.kv["alerting/notify/email"] = json.dumps(notify_email)

    consulate_session.kv["alerting/prior/"] = []
except TypeError:
    print "One of the python data structures is not JSON serializable, may have accidentally created a set()"
    raise




