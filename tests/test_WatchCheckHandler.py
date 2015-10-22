#!/usr/bin/env python
from __future__ import absolute_import
import unittest
import json as json
import consulalerting.settings as settings
import consulalerting.utilities as utilities
import consulalerting.WatchCheckHandler as WatchCheckHandler
import consulalerting.ConsulHealthStruct as ConsulHealthStruct


FOOBAR_CATALOG = json.loads("""{
"Node": {
"Node": "foobar",
"Address": "10.1.10.12"
},
"Services": {
"consul": {
  "ID": "consul",
  "Service": "consul",
  "Tags": null,
  "Port": 8300
},
"redis": {
  "ID": "redis",
  "Service": "redis",
  "Tags": [
    "v1"
  ],
  "Port": 8000
}
}
}""")

HEALTH_CHECK_TAGS = ["devops", "hipchat"]

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


PRIOR_STATE = json.loads("""[
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
"Status": "warning",
"Notes": "",
"Output": "",
"ServiceID": "redis",
"ServiceName": "redis"
}
] """)

CURRENT_STATE_PASSING = json.loads("""[
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

CURRENT_STATE_WARNING = json.loads("""[
{
"Node": "foobar",
"CheckID": "service:redis",
"Name": "Service 'redis' check",
"Status": "warning",
"Notes": "",
"Output": "",
"ServiceID": "redis",
"ServiceName": "redis"
}
]""")

CURRENT_STATE_CRITICAL = json.loads("""[
{
"Node": "foobar",
"CheckID": "service:redis",
"Name": "Service 'redis' check",
"Status": "critical",
"Notes": "",
"Output": "",
"ServiceID": "redis",
"ServiceName": "redis"
}
]""")


PRIOR_STATE_PASSING = json.loads("""[
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
] """)

PRIOR_STATE_WARNING = json.loads("""[
{
"Node": "foobar",
"CheckID": "service:redis",
"Name": "Service 'redis' check",
"Status": "warning",
"Notes": "",
"Output": "",
"ServiceID": "redis",
"ServiceName": "redis"
}
] """)

PRIOR_STATE_CRITICAL = json.loads("""[
{
"Node": "foobar",
"CheckID": "service:redis",
"Name": "Service 'redis' check",
"Status": "critical",
"Notes": "",
"Output": "",
"ServiceID": "redis",
"ServiceName": "redis"
}
] """)


class WatchCheckHandlerTests(unittest.TestCase):

    def setUp(self):
        self.watch = WatchCheckHandler.WatchCheckHandler(settings.consul)
        self.watch.health_current = CURRENT_STATE
        self.watch.health_prior = PRIOR_STATE

    def test_CreateConsulHealthNodeList(self):
        current_obj_list = utilities.createConsulHealthList(CURRENT_STATE)
        self.assertEqual(current_obj_list[
                         0], ConsulHealthStruct.ConsulHealthStruct(**CURRENT_STATE[0]))

    def test_GetObjectListByStateWarning(self):
        current_obj_list = utilities.createConsulHealthList(CURRENT_STATE)
        current_state_warning = utilities.getObjectListByState(
            current_obj_list, settings.WARNING_STATE)
        self.assertEqual(0, len(current_state_warning))

    def test_GetObjectListByStatePassing(self):
        current_obj_list = utilities.createConsulHealthList(CURRENT_STATE)
        current_state_warning = utilities.getObjectListByState(
            current_obj_list, settings.PASSING_STATE)
        print current_state_warning
        self.assertEqual(2, len(current_state_warning))

    def test_FromPassingToPassing(self):
        self.watch.health_current = CURRENT_STATE_PASSING
        self.watch.health_prior = PRIOR_STATE_PASSING

        curr = utilities.createConsulHealthList(self.watch.health_current)
        prior = utilities.createConsulHealthList(self.watch.health_prior)

        alert_list = self.watch.checkForAlertChanges(curr, prior)
        self.assertEqual(alert_list, None)

    def test_FromPassingToWarning(self):
        self.watch.health_current = CURRENT_STATE_WARNING
        self.watch.health_prior = PRIOR_STATE_PASSING

        curr = utilities.createConsulHealthList(self.watch.health_current)
        prior = utilities.createConsulHealthList(self.watch.health_prior)

        alert_list = self.watch.checkForAlertChanges(curr, prior)
        self.assertEqual(1, len(alert_list))

    def test_FromPassingToCritical(self):
        self.watch.health_current = CURRENT_STATE_CRITICAL
        self.watch.health_prior = PRIOR_STATE_PASSING

        curr = utilities.createConsulHealthList(self.watch.health_current)
        prior = utilities.createConsulHealthList(self.watch.health_prior)

        alert_list = self.watch.checkForAlertChanges(curr, prior)
        self.assertEqual(1, len(alert_list))

    def test_FromCriticalToCritical(self):
        self.watch.health_current = CURRENT_STATE_CRITICAL
        self.watch.health_prior = PRIOR_STATE_CRITICAL

        curr = utilities.createConsulHealthList(self.watch.health_current)
        prior = utilities.createConsulHealthList(self.watch.health_prior)

        alert_list = self.watch.checkForAlertChanges(curr, prior)
        self.assertEqual(alert_list, None)

    def test_FromCriticalToWarning(self):
        self.watch.health_current = CURRENT_STATE_WARNING
        self.watch.health_prior = PRIOR_STATE_CRITICAL

        curr = utilities.createConsulHealthList(self.watch.health_current)
        prior = utilities.createConsulHealthList(self.watch.health_prior)

        alert_list = self.watch.checkForAlertChanges(curr, prior)
        self.assertEqual(1, len(alert_list))

    def test_FromCriticalToPassing(self):
        self.watch.health_current = CURRENT_STATE_PASSING
        self.watch.health_prior = PRIOR_STATE_CRITICAL

        curr = utilities.createConsulHealthList(self.watch.health_current)
        prior = utilities.createConsulHealthList(self.watch.health_prior)

        alert_list = self.watch.checkForAlertChanges(curr, prior)
        self.assertEqual(1, len(alert_list))

    def test_FromWarningToWarning(self):
        self.watch.health_current = CURRENT_STATE_WARNING
        self.watch.health_prior = PRIOR_STATE_WARNING

        curr = utilities.createConsulHealthList(self.watch.health_current)
        prior = utilities.createConsulHealthList(self.watch.health_prior)

        alert_list = self.watch.checkForAlertChanges(curr, prior)
        self.assertEqual(alert_list, None)

    def test_FromWarningToPassing(self):
        self.watch.health_current = CURRENT_STATE_PASSING
        self.watch.health_prior = PRIOR_STATE_WARNING

        curr = utilities.createConsulHealthList(self.watch.health_current)
        prior = utilities.createConsulHealthList(self.watch.health_prior)

        alert_list = self.watch.checkForAlertChanges(curr, prior)
        self.assertEqual(1, len(alert_list))

    def test_FromWarningToCritical(self):
        self.watch.health_current = CURRENT_STATE_CRITICAL
        self.watch.health_prior = PRIOR_STATE_WARNING

        curr = utilities.createConsulHealthList(self.watch.health_current)
        prior = utilities.createConsulHealthList(self.watch.health_prior)

        alert_list = self.watch.checkForAlertChanges(curr, prior)
        self.assertEqual(1, len(alert_list))

    def test_filterByBlacklistsExceptions(self):
        self.assertRaises(TypeError, self.watch.filterByBlacklists)

    #Integration Test
    def test_Run(self):
        w = WatchCheckHandler.WatchCheckHandler(settings.consul)
        alert_list = w.Run()
        settings.consul.session.destroy(w.session_id)

        self.assertEqual(alert_list, None)


if __name__ == '__main__':
    unittest.main()
