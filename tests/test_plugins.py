import unittest
import responses
import json as json
import consulalerting.plugins as plugins
import consulalerting.settings as settings
import consulalerting.utilities as utilities
import consulalerting.ConsulHealthStruct as ConsulHealthStruct
from mock import patch, MagicMock, Mock


ALL_REQUESTS_ALERTING_AVAILABLE_PLUGINS = [
    "hipchat", "slack", "mailgun", "pagerduty", "influxdb"]

ALL_REQUESTS_PLUGINS_ALERT_LIST = [{"Node": "consul",
                                    "CheckID": "service:redis",
                                    "Name": "Service 'redis' check",
                                    "Tags": ["hipchat", "slack", "mailgun", "pagerduty", "influxdb", "devops", "db"],
                                    "ServiceName": "redis",
                                    "Notes": "",
                                    "Status": "critical",
                                    "ServiceID": "redis",
                                    "Output": "Usage: check_redis.py [options]\n\ncheck_redis.py: error: Warning level required\n"}]

CONSUL_HEALTH_STRUCT_ALL_REQUESTS_PLUGINS_ALERT_LIST = [
    ConsulHealthStruct.ConsulHealthStruct(**obj) for obj in ALL_REQUESTS_PLUGINS_ALERT_LIST]


CONSUL_SLACK = {"api_token": "testing123testing123",
                "rooms": {"devops": ""}}

CONSUL_HIPCHAT = {"api_token": "testing123testing123",
                  "url": "https://api.hipchat.com/v1/",
                  "rooms": {"devops": 1}}

CONSUL_MAILGUN = {"api_token": "testing123testing123",
                  "mailgun_domain": "sandboxtesting123testing123.mailgun.org",
                  "from": "consul@example.com",
                  "teams": {"devops": ["jrxfive@gmail.com", "jrxsix@gmail.com"]}
                  }

CONSUL_PAGERDUTY = {"teams": {"devops": ""}}

CONSUL_INFLUXDB = {"url":"http://localhost:8086/write", "series":"test", "databases":{"db":"mydb"}}

CONSUL_ELASTICSEARCHLOG = {"logpaths": ["/path/to/log1", "/path/to/log2"]}


class PluginsTests(unittest.TestCase):

    def setUp(self):
        self.obj = CONSUL_HEALTH_STRUCT_ALL_REQUESTS_PLUGINS_ALERT_LIST[0]

        self.message_template = "Service {name}: "\
            "is in a {state} state on {node}. "\
            "Output from check: {output}".format(name=self.obj.ServiceName,
                                                 state=self.obj.Status,
                                                 node=self.obj.Node,
                                                 output=self.obj.Output)

    @responses.activate
    def test_notifySlack(self):
        responses.add(
            responses.POST, "https://slack.com/api/chat.postMessage", json=True, status=200)

        status_code = plugins.notify_slack(
            self.message_template, ["devops"], CONSUL_SLACK)

        self.assertEqual(200, status_code)

    @responses.activate
    def test_notifySlackHipchat(self):
        responses.add(
            responses.POST, "https://slack.com/api/chat.postMessage", json=True, status=200)
        responses.add(
            responses.POST, "https://api.hipchat.com/v1/", json=True, status=200)

        status_code = plugins.notify_slack(
            self.message_template, ["devops"], CONSUL_SLACK)

        self.assertEqual(200, status_code)

        status_code = 0

        status_code = plugins.notify_hipchat(
            self.obj, self.message_template, ["devops"], CONSUL_HIPCHAT)

        self.assertEqual(200, status_code)

    @responses.activate
    def test_notifyPagerduty(self):
        responses.add(
            responses.POST, "https://events.pagerduty.com/generic/2010-04-15/create_event.json", json=True, status=200)

        status_code = plugins.notify_pagerduty(
            self.obj, self.message_template, ["devops"], CONSUL_PAGERDUTY)

        self.assertEqual(200, status_code)

    @responses.activate
    def test_notifyMailgun(self):
        responses.add(
            responses.POST, "https://api.mailgun.net/v2/{domain}/messages".format(
                domain=CONSUL_MAILGUN["mailgun_domain"]),
            json=True, status=200)
        status_code = plugins.notify_mailgun(
            self.message_template, ["devops"], CONSUL_MAILGUN)

        self.assertEqual(200, status_code)

    @responses.activate
    def test_notifyHipchat(self):
        responses.add(
            responses.POST, "https://api.hipchat.com/v1/", json=True, status=200)
        status_code = plugins.notify_hipchat(
            self.obj, self.message_template, ["devops"], CONSUL_HIPCHAT)

        self.assertEqual(200, status_code)

    @responses.activate
    def test_notifyInfluxdb(self):
        responses.add(
            responses.POST, "http://localhost:8086/write", json=True, status=204)

        status_code = plugins.notify_influxdb(
            self.obj, self.message_template, ["db"], CONSUL_INFLUXDB)

        self.assertEqual(204, status_code)

    @responses.activate
    def test_notifySlackFail(self):
        responses.add(
            responses.POST, "https://slack.com/api/chat.postMessage", json=True, status=400)

        status_code = plugins.notify_slack(
            self.message_template, ["devops"], CONSUL_SLACK)

        self.assertNotEqual(200, status_code)

    @responses.activate
    def test_notifyPagerdutyFail(self):
        responses.add(
            responses.POST, "https://events.pagerduty.com/generic/2010-04-15/create_event.json", json=True, status=40)

        status_code = plugins.notify_pagerduty(
            self.obj, self.message_template, ["devops"], CONSUL_PAGERDUTY)

        self.assertNotEqual(200, status_code)

    @responses.activate
    def test_notifyMailgunFail(self):
        responses.add(
            responses.POST, "https://api.mailgun.net/v2/{domain}/messages".format(
                domain=CONSUL_MAILGUN["mailgun_domain"]),
            json=True, status=400)
        status_code = plugins.notify_mailgun(
            self.message_template, ["devops"], CONSUL_MAILGUN)

        self.assertNotEqual(200, status_code)

    @responses.activate
    def test_notifyHipchatFail(self):
        responses.add(
            responses.POST, "https://api.hipchat.com/v1/", json=True, status=400)
        status_code = plugins.notify_hipchat(
            self.obj, self.message_template, ["devops"], CONSUL_HIPCHAT)

        self.assertNotEqual(200, status_code)

    @responses.activate
    def test_notifyInfluxdbFail(self):
        responses.add(
            responses.POST, "http://localhost:8086/write", json=True, status=400)

        status_code = plugins.notify_influxdb(
            self.obj, self.message_template, ["db"], CONSUL_INFLUXDB)

        self.assertNotEqual(204, status_code)

    def test_notifyElasticSearchLog(self):
        open_mock = MagicMock()
        with patch('__builtin__.open', open_mock):
            open_mock.return_value = MagicMock(spec=file)
            plugins.notify_elasticsearchlog(self.obj, self.message_template, CONSUL_ELASTICSEARCHLOG["logpaths"],
                                            CONSUL_ELASTICSEARCHLOG)

        file_handle = open_mock.return_value.__enter__.return_value
        file_handle.write.assert_called_with("\n")
