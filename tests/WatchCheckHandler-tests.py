#!/usr/bin/env python
import unittest
import simplejson as json
import consulalerting.WatchCheckHandler
import consulalerting.ConsulHealthNodeStruct


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
        self.watch = consulalerting.WatchCheckHandler()
        self.watch.health_current = CURRENT_STATE
        self.watch.health_prior = PRIOR_STATE

    def test_CreateConsulHealthNodeList(self):
        current_obj_list, prior_obj_list = self.watch.createConsulHealthNodeList()
        self.assertEqual(current_obj_list[0],consulalerting.ConsulHealthNodeStruct(**CURRENT_STATE[0]))


    def test_GetObjectListByStateWarning(self):
        current_obj_list, prior_obj_list = self.watch.createConsulHealthNodeList()
        current_state_warning = self.watch.getObjectListByState(
                    current_obj_list, self.watch.WARNING_STATE)
        self.assertEqual(0,len(current_state_warning))

    def test_GetObjectListByStatePassing(self):
        current_obj_list, prior_obj_list = self.watch.createConsulHealthNodeList()
        current_state_warning = self.watch.getObjectListByState(
                    current_obj_list, self.watch.PASSING_STATE)
        self.assertEqual(2,len(current_state_warning))


    def test_filterByBlacklistsExceptions(self):
        self.assertRaises(TypeError,self.watch.filterByBlacklists)





if __name__ == '__main__':
    unittest.main()

