#!/usr/bin/env python
import hipchat
import consulate
from ConsulHealthNodeStruct import ConsulHealthNodeStruct


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

    def __init__(self, alert_list):
        """consul_watch_handler_checks, will send a list of ConsulHealthNodeStruct
        :param list alert_list: of ConsulHealthNodeStruct Object
        """
        self.alert_list = alert_list

        # eventually load these values some other way
        self.available_plugins = set(["hipchat"])

    def __getattr__(self, item):
        return None

    def get_unique_tags_keys(self):
        """
         find unique tags in the list of ConsulHealthNodeStruct objects, used to determine which plugins to load
        """

        # python 2.6 syntax
        self.unique_tags = set(
            tag for obj in self.alert_list for tag in obj.Tags)

    def load_from_tags_keys(self):
        # set intersection of unique_tags and available_plugins
        configurations_files_to_load = self.unique_tags.intersection(
            self.available_plugins)

        # Wrapper around pthon-requests, has some constants for api
        session = consulate.Consulate(host="0.0.0.0")

        if "hipchat" in configurations_files_to_load:

            # get request to 0.0.0.0:8500/v1/kv/notify/hipchat which routes to
            # consul master
            self.hipchat = session.kv["alerting/notify/hipchat"]

            # Convert Keys to lower case
            self.hipchat = dict((key.lower(), value)
                                for key, value in self.hipchat.iteritems())

            # convert room keys to lower case
            self.hipchat["rooms"] = dict(
                (key.lower(), value) for key, value in self.hipchat["rooms"].iteritems())

        if "email" in configurations_files_to_load:
            email_consul = None
            email_value = None
            self.email = None

    def Run(self):
        self.get_unique_tags_keys()
        self.load_from_tags_keys()

        for obj in self.alert_list:
            # if hipchat in tags and if hipchat KV information exists, need
            # better way to confirm existence
            if "hipchat" in obj.Tags and self.hipchat:
                self.notify_hipchat(obj)

            if "email" in obj.Tags and self.email:
                pass

    def notify_hipchat(self, obj):

        # get keys from "rooms" in KV hipchat
        hipchat_room_keynames = set(self.hipchat["rooms"].keys())
        trigger_tags = set(obj.Tags)

        # common keys found in trigger tags and kv hipchat rooms
        common_hipchat_rooms = hipchat_room_keynames.intersection(trigger_tags)

        # Use hipchat library to use for notifications requires api_token and
        # url
        hipster = hipchat.HipChat(
            token=self.hipchat["api_token"], url=self.hipchat["url"])

        for roomname in common_hipchat_rooms:

            if obj.Status == ConsulHealthNodeStruct.PASSING_STATE:
                color_value = "green"
                notify_value = 0

            elif obj.Status == ConsulHealthNodeStruct.WARNING_STATE:
                color_value = "yellow"
                notify_value = 1

            elif obj.Status == ConsulHealthNodeStruct.CRITICAL_STATE:
                color_value = "red"
                notify_value = 1

            elif obj.Status == ConsulHealthNodeStruct.UNKNOWN_STATE:
                color_value = "gray"
                notify_value = 1

            if obj.ServiceName or obj.ServiceID:

                message_template = "Service {name}: is in a {state} state on {node}. " \
                                   "Output from test: {output}".format(name=obj.ServiceName,
                                                                       state=obj.Status,
                                                                       node=obj.Node,
                                                                       output=obj.Output)

            else:

                message_template = "System Check {name}: is in a {state} state on {node}. " \
                                   "Output from test: {output}".format(name=obj.CheckID,
                                                                       state=obj.Status,
                                                                       node=obj.Node,
                                                                       output=obj.Output)

            hipster.message_room(room_id=int(self.hipchat["rooms"][roomname]), message_from="Consul",
                                 message=message_template,
                                 notify=notify_value,
                                 color=color_value)
