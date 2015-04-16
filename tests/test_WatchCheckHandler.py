#!/usr/bin/env python
from __future__ import absolute_import
import unittest
import simplejson as json
from consulalerting.WatchCheckHandler import WatchCheckHandler
from consulalerting.ConsulHealthStruct import ConsulHealthStruct


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

HEALTH_CHECK_TAGS = ["devops","hipchat"]

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

class WatchCheckHandlerTests(unittest.TestCase):




    def setUp(self):
        self.watch = WatchCheckHandler()
        self.watch.health_current = CURRENT_STATE
        self.watch.health_prior = PRIOR_STATE

    def test_CreateConsulHealthNodeList(self):
        current_obj_list = self.watch.createConsulHealthList(CURRENT_STATE)
        self.assertEqual(current_obj_list[0],ConsulHealthStruct(**CURRENT_STATE[0]))


    def test_GetObjectListByStateWarning(self):
        current_obj_list = self.watch.createConsulHealthList(CURRENT_STATE)
        current_state_warning = self.watch.getObjectListByState(
                    current_obj_list, self.watch.WARNING_STATE)
        self.assertEqual(0,len(current_state_warning))

    def test_GetObjectListByStatePassing(self):
        current_obj_list = self.watch.createConsulHealthList(CURRENT_STATE)
        current_state_warning = self.watch.getObjectListByState(
                    current_obj_list, self.watch.PASSING_STATE)
        self.assertEqual(2,len(current_state_warning))


    def test_filterByBlacklistsExceptions(self):
        self.assertRaises(TypeError,self.watch.filterByBlacklists)





if __name__ == '__main__':
    unittest.main()

