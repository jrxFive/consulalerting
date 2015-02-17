#!/usr/bin/env python
import unittest
import simplejson as json
from consulalerting import NotificationEngine
from consulalerting import ConsulHealthStruct


KV_ALERTING_AVAILABLE_PLUGINS = ["hipchat","slack","mailgun"]
ALERT_LIST = [{"Node": "consul-agent",
               "CheckID": "serfHealth",
               "Name": "Serf Health Status",
               "Tags": ["devops", "consul","mailgun","hipchat"],
               "ServiceName": "",
               "Notes": "",
               "Status": "critical",
               "ServiceID": "",
               "Output": "Agent not live or unreachable"},
              {"Node": "consul-agent",
               "CheckID": "service:redis",
               "Name": "Service 'redis' check",
               "Tags": ["devops","redis","techops","dev","slack"],
               "ServiceName": "redis",
               "Notes": "",
               "Status": "critical",
               "ServiceID": "redis",
               "Output": "Usage: check_redis.py [options]\n\ncheck_redis.py: error: Warning level required\n"},
              {"Node": "consul",
               "CheckID": "serfHealth",
               "Name": "Serf Health Status",
               "Tags": ["dev", "consul"],
               "ServiceName": "",
               "Notes": "",
               "Status": "passing",
               "ServiceID": "",
               "Output": "Agent alive and reachable"},
              {"Node": "consul",
               "CheckID": "service:redis",
               "Name": "Service 'redis' check",
               "Tags": ["qa", "redis-slave"],
               "ServiceName": "redis",
               "Notes": "",
               "Status": "critical",
               "ServiceID": "redis",
               "Output": "Usage: check_redis.py [options]\n\ncheck_redis.py: error: Warning level required\n"}]

CONSUL_HEALTH_STRUCT_ALERT_LIST = [ConsulHealthStruct.ConsulHealthStruct(**obj) for obj in ALERT_LIST]

MAILGUN_NOTIFIER = {"teams":
                        {"devops":["jrxfive@gmail.com","jonathancr.cross@gmail.com"]},
                    "from": "Consul@example.com",
                    "MAILGUN_DOMAIN": "sandbox1b8b7a197a214e778894e5af2f7799a4.mailgun.org",
                    "API_TOKEN": "key-55028aa08ee351a714e662ccb736dd74"}

class NotificationEngineTests(unittest.TestCase):




    def setUp(self):
        self.ne = NotificationEngine.NotificationEngine(CONSUL_HEALTH_STRUCT_ALERT_LIST)
        self.ne.available_plugins = KV_ALERTING_AVAILABLE_PLUGINS
        self.ne.unique_tags = set(["hipchat","mailgun"])


    def test_uniqueTags(self):
        unique_tags = self.ne.get_unique_tags_keys()
        self.assertEqual(len(unique_tags),len(set(["devops","consul","mailgun","hipchat","redis","techops","dev","slack","qa","redis-slave"])))


    def test_loadPluginsFromTags(self):
        hipchat,slack,mailgun,email = self.ne.load_plugins_from_tags()
        self.assertFalse(email)
        self.assertTrue(hipchat)
        self.assertFalse(slack)
        self.assertTrue(mailgun)

    def test_commonNotifiers(self):
        common = self.ne.common_notifiers(CONSUL_HEALTH_STRUCT_ALERT_LIST[0],"teams",MAILGUN_NOTIFIER)
        self.assertEqual(len(common),1)





if __name__ == '__main__':
    unittest.main()
