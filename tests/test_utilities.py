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
		self.assertEqual(2,len(obj_list))

	def test_getHashStateSet(self):
		obj_list = utilities.createConsulHealthList(CURRENT_STATE)
		passing_list = utilities.getHashStateSet(obj_list,settings.PASSING_STATE)

		self.assertEqual(2,len(passing_list))

	#Integration tests
	def test_checkForKey(self):
		r = utilities.checkForKey(settings.consul,"asdf")
		self.assertFalse(r)

	def test_putKey(self):
		utilities.putKey(settings.consul,"asdf","testing123")
		r = utilities.checkForKey(settings.consul,"asdf")
		self.assertTrue(r)

		del settings.consul.kv["asdf"]

	def test_currentState(self):
		r = utilities.currentState(settings.consul)
		self.assertTrue(r)


		