from __future__ import absolute_import
import unittest
import json as json
import consulalerting.settings as settings
import consulalerting.utilities as utilities


CURRENT_STATE = json.loads("""[
{
"Node": "foobar",
"CheckID": "serfHealth",
"Name": "Serf Health Status",
"Status": "passing",
"Notes": "",
"Output": "",
"ServiceID": "",
"ServiceName": ""
},
{
"Node": "foobar",
"CheckID": "service:redis",
"Name": "Service 'redis' check",
"Status": "passing",
"Notes": "",
"Output": "",
"ServiceID": "redis",
"ServiceName": "redis"
}
]""")


class utilitiesTests(unittest.TestCase):

    def test_createConsulHealthList(self):
        obj_list = utilities.createConsulHealthList(CURRENT_STATE)
        self.assertEqual(2, len(obj_list))

    def test_getHashStateSet(self):
        obj_list = utilities.createConsulHealthList(CURRENT_STATE)
        passing_list = utilities.getHashStateSet(
            obj_list, settings.PASSING_STATE)

        self.assertEqual(2, len(passing_list))

    # Integration tests
    def test_checkForKey(self):
        r = utilities.checkForKey("asdf")
        self.assertFalse(r)

    def test_putKey(self):
        utilities.putKey("asdf", "testing123")
        r = utilities.checkForKey("asdf")
        self.assertTrue(r)

        del settings.consul.kv["asdf"]

    def test_currentState(self):
        r = utilities.currentState()
        self.assertTrue(r)

    def test_getCheckTags(self):
        r = utilities.getCheckTags(settings.KV_ALERTING_HEALTH_CHECK_TAGS)
        self.assertTrue(isinstance(r, list))

        del settings.consul.kv[settings.KV_ALERTING_HEALTH_CHECK_TAGS]

        r = utilities.getCheckTags(settings.KV_ALERTING_HEALTH_CHECK_TAGS)
        self.assertTrue(isinstance(r, list))

        settings.consul.kv[settings.KV_ALERTING_HEALTH_CHECK_TAGS] = []

    def test_getPriorState(self):
        r = utilities.priorState(settings.KV_PRIOR_STATE)
        self.assertTrue(isinstance(r, list))

        r = utilities.priorState(settings.KV_PRIOR_STATE + "/dummy")
        self.assertTrue(isinstance(r, list))

    def test_getBlacklist(self):
        bl_node = utilities.getBlacklist(settings.KV_ALERTING_BLACKLIST_NODES)
        self.assertTrue(isinstance(bl_node, list))

        bl_node = utilities.getBlacklist(
            settings.KV_ALERTING_BLACKLIST_NODES + "/dummy")
        self.assertTrue(isinstance(bl_node, list))
