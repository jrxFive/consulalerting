import requests
import consulate
import json as json
import smtplib
import string
import sys
import settings
import plugins
from multiprocessing import Process


class NotificationEngine(object):

    """
    NotificationEngine, routes given ConsulHealthNodeStruct objects
    using the plugins available and based off tags in ConsulHealthNodeStruct.
    ConsulHealthNodeStruct is an python object representation of
        {
        "Node": "foobar",
        "CheckID": "service:redis",
        "Name": "Service 'redis' check",
        "Status": "passing",
        "Tags": [],
        "Notes": "",
        "Output": "",
        "ServiceID": "redis",
        "ServiceName": "redis"
        }

    Example use:

        NotificationEngine([ConsulHealthNodeStruct,ConsulHealthNodeStruct]).Run()
    """

    def __init__(self, alert_list, consulate_session):
        """consul_watch_handler_checks, will send a list of ConsulHealthNodeStruct
        :param list alert_list: of ConsulHealthNodeStruct Object
        """
        self.alert_list = alert_list
        self.consul = consulate_session

    def __getattr__(self, item):
        return None

    def get_available_plugins(self):
        try:
            self.available_plugins = set(
                json.loads(self.consul.kv[settings.KV_ALERTING_AVAILABLE_PLUGINS]))

            settings.logger.info(
                "Plugins available, Plugins={plug}".format(
                    plug=list(self.available_plugins)))

            return self.available_plugins
        except TypeError:
            settings.logger.error(
                "Could not obtain alerting"
                "plugins from ConsulURI=%{location}".format(
                    location=settings.KV_ALERTING_AVAILABLE_PLUGINS))
            raise

    def get_unique_tags_keys(self):
        """
         find unique tags in the list of ConsulHealthNodeStruct objects, used to determine which plugins to load
        """

        # python 2.6 syntax
        self.unique_tags = set(
            tag for obj in self.alert_list for tag in obj.Tags)

        settings.logger.info("Unique tags found,"
                             "Tags={tags}".format(tags=list(self.unique_tags)))

        return self.unique_tags

    def load_plugins_from_tags(self):
        # set intersection of unique_tags and available_plugins
        configurations_files_to_load = self.unique_tags.intersection(
            self.available_plugins)

        settings.logger.info(
            "Configuration files to load,"
            "Configurations={configs}".format(configs=list(configurations_files_to_load)))

        if "hipchat" in configurations_files_to_load:
            self.hipchat = self.load_plugin(
                settings.KV_ALERTING_NOTIFY_HIPCHAT, "rooms")

        if "slack" in configurations_files_to_load:
            self.slack = self.load_plugin(
                settings.KV_ALERTING_NOTIFY_SLACK, "rooms")

        if "mailgun" in configurations_files_to_load:
            self.mailgun = self.load_plugin(
                settings.KV_ALERTING_NOTIFY_MAILGUN, "teams")

        if "email" in configurations_files_to_load:
            self.email = self.load_plugin(
                settings.KV_ALERTING_NOTIFY_EMAIL, "teams")

        if "pagerduty" in configurations_files_to_load:
            self.pagerduty = self.load_plugin(
                settings.KV_ALERTING_NOTIFY_PAGERDUTY, "teams")

        return (self.hipchat, self.slack, self.mailgun,
                self.email, self.pagerduty)

    @staticmethod
    def dict_keys_to_low(dictionary):
        dict_keys_lowercase = dict((key.lower(), value)
                                   for key, value in dictionary.iteritems())

        return dict_keys_lowercase

    def load_plugin(self, KV_LOCATION, tags_dictname):
        # get request to 0.0.0.0:8500/v1/kv/notify/<plugin_name>
        #  which routes to consul master
        plugin = json.loads(self.consul.kv[KV_LOCATION])

        # Convert Keys to lower case
        plugin = NotificationEngine.dict_keys_to_low(plugin)

        plugin[tags_dictname] = dict((key.lower(), value) for key,
                                     value in plugin[tags_dictname].iteritems())

        return plugin

    def common_notifiers(self, obj, kv_tags_dictname, kv_dict):
        keynames = set(kv_dict[kv_tags_dictname].keys())
        obj_tags = set(obj.Tags)

        common = keynames.intersection(obj_tags)

        return common

    def message_pattern(self, obj):

        if obj.ServiceName or obj.ServiceID:

            message_template = "Service {name}: "\
                "is in a {state} state on {node}. "\
                "Output from check: {output}".format(name=obj.ServiceName,
                                                     state=obj.Status,
                                                     node=obj.Node,
                                                     output=obj.Output)

        else:

            message_template = "System Check {name}: is "\
                "in a {state} state on {node}. "\
                "Output from check: {output}".format(name=obj.CheckID,
                                                     state=obj.Status,
                                                     node=obj.Node,
                                                     output=obj.Output)

        return message_template

    def run_notifiers(self, obj):

        message_template = self.message_pattern(obj)

        if "hipchat" in obj.Tags and self.hipchat:
            common_notifiers = self.common_notifiers(
                obj, "rooms", self.hipchat)
            hipchat = self.hipchat
            Process(target=plugins.notify_hipchat, args=(obj, message_template,
                                                 common_notifiers,
                                                 hipchat)).start()

        if "slack" in obj.Tags and self.slack:
            common_notifiers = self.common_notifiers(obj, "rooms", self.slack)
            slack = self.slack
            Process(target=plugins.notify_slack, args=(message_template,
                                               common_notifiers,
                                               slack)).start()

        if "mailgun" in obj.Tags and self.mailgun:
            common_notifiers = self.common_notifiers(
                obj, "teams", self.mailgun)
            mailgun = self.mailgun
            Process(target=plugins.notify_mailgun, args=(message_template,
                                                 common_notifiers,
                                                 mailgun)).start()

        if "email" in obj.Tags and self.email:
            common_notifiers = self.common_notifiers(obj, "teams", self.email)
            email = self.email
            Process(target=plugins.notify_email, args=(message_template,
                                               common_notifiers,
                                               email)).start()

        if "pagerduty" in obj.Tags and self.pagerduty:
            common_notifiers = self.common_notifiers(
                obj, "teams", self.pagerduty)
            pagerduty = self.pagerduty
            Process(target=plugins.notify_pagerduty, args=(obj,
                                                   message_template,
                                                   common_notifiers,
                                                   pagerduty)).start()

    def Run(self):
        self.get_available_plugins()
        self.get_unique_tags_keys()
        self.load_plugins_from_tags()

        for obj in self.alert_list:
            self.run_notifiers(obj)
