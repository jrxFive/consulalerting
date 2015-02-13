import consulate
import simplejson as json

blacklist_nodes = {}
blacklist_services = {}
blacklist_checks = {}
blacklist_nodechecks = {}
health_check_tags = []

notify_hipchat= {"API_TOKEN":"",
                 "URL":"",
                 "rooms":{}}


consulate_session = consulate.Consulate()

try:
    consulate_session.kv["alerting/healthchecktags"] = json.dumps(health_check_tags)

    consulate_session.kv["alerting/blacklist/nodes"] = json.dumps(blacklist_nodes)

    consulate_session.kv["alerting/blacklist/services"] = json.dumps(blacklist_services)

    consulate_session.kv["alerting/blacklist/checks"] = json.dumps(blacklist_checks)

    consulate_session.kv["alerting/blacklist/nodechecks"] = json.dumps(blacklist_nodechecks)

    consulate_session.kv["alerting/notify/hipchat"] = json.dumps(notify_hipchat)

    consulate_session.kv["alerting/prior/"]
except TypeError:
    print "One of the python data structures is not JSON serializable, may have accidentally created a set()"
    raise




