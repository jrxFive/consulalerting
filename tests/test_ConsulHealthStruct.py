import unittest
import consulalerting.utilities as utilities
import consulalerting.ConsulHealthStruct as ConsulHealthStruct
import json as json


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

class ConsulHealthStructTests(unittest.TestCase):

	def test_Hash(self):
		obj = utilities.createConsulHealthList(CURRENT_STATE)
		self.assertEqual(-5352519189505265712,hash(obj[0]))
		self.assertEqual(3614443627497883396,hash(obj[1]))

	def test_Equal(self):
		obj_Current = utilities.createConsulHealthList(CURRENT_STATE)
		obj_Prior = utilities.createConsulHealthList(PRIOR_STATE)

		self.assertTrue(obj_Current[1] == obj_Prior[1])

	def test_AddTags(self):
		obj = utilities.createConsulHealthList(CURRENT_STATE)
		obj[1].addTags(FOOBAR_CATALOG,HEALTH_CHECK_TAGS)

		self.assertEqual(1,len(obj[1].Tags))

		obj[0].addTags(FOOBAR_CATALOG,HEALTH_CHECK_TAGS)

		self.assertEqual(2,len(obj[0].Tags))








