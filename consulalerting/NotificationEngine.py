#!/usr/bin/env python
import requests
import hipchat
import consulate
import smtplib
import string
from slacker import Slacker
from ConsulHealthStruct import ConsulHealthStruct
from Settings import Settings

class NotificationEngine(Settings):

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

    def __init__(self, alert_list,consul_host="0.0.0.0"):
        """consul_watch_handler_checks, will send a list of ConsulHealthNodeStruct
        :param list alert_list: of ConsulHealthNodeStruct Object
        """
        super(NotificationEngine,self).__init__()
        self.alert_list = alert_list
        self.session = consulate.Consulate(consul_host)
        # eventually load these values some other way


    def __getattr__(self, item):
        return None

    def get_available_plugins(self):
        self.available_plugins = set(self.session.kv[NotificationEngine.KV_ALERTING_AVAILABLE_PLUGINS])
        return self.available_plugins

    def get_unique_tags_keys(self):
        """
         find unique tags in the list of ConsulHealthNodeStruct objects, used to determine which plugins to load
        """

        # python 2.6 syntax
        self.unique_tags = set(
            tag for obj in self.alert_list for tag in obj.Tags)

        return self.unique_tags

    def load_plugins_from_tags(self):
        # set intersection of unique_tags and available_plugins
        configurations_files_to_load = self.unique_tags.intersection(
            self.available_plugins)


        if "hipchat" in configurations_files_to_load:
            self.hipchat = self.load_plugin(NotificationEngine.KV_ALERTING_NOTIFY_HIPCHAT,"rooms")

        if "slack" in configurations_files_to_load:
            self.slack = self.load_plugin(NotificationEngine.KV_ALERTING_NOTIFY_SLACK,"rooms")

        if "mailgun" in configurations_files_to_load:
            self.mailgun = self.load_plugin(NotificationEngine.KV_ALERTING_NOTIFY_MAILGUN,"teams")

        if "email" in configurations_files_to_load:
            self.email = self.load_plugin(NotificationEngine.KV_ALERTING_NOTIFY_EMAIL,"teams")


        return (self.hipchat,self.slack,self.mailgun,self.email)



    @staticmethod
    def dict_keys_to_low(dictionary):
        dict_keys_lowercase = dict((key.lower(), value)
                                for key, value in dictionary.iteritems())

        return dict_keys_lowercase

    def load_plugin(self,KV_LOCATION,tags_dictname):
        # get request to 0.0.0.0:8500/v1/kv/notify/<plugin_name> which routes to
        # consul master
        plugin = self.session.kv[KV_LOCATION]

        # Convert Keys to lower case
        plugin = NotificationEngine.dict_keys_to_low(plugin)

        plugin[tags_dictname] = dict(
                (key.lower(), value) for key, value in plugin[tags_dictname].iteritems())

        return plugin


    def Run(self):
        self.get_available_plugins()
        self.get_unique_tags_keys()
        self.load_plugins_from_tags()

        for obj in self.alert_list:
            # if hipchat in tags and if hipchat KV information exists, need
            # better way to confirm existence
            if "hipchat" in obj.Tags and self.hipchat:
                self.notify_hipchat(obj,self.message_pattern(obj))

            if "slack" in obj.Tags and self.slack:
                self.notify_slack(obj,self.message_pattern(obj))

            if "mailgun" in obj.Tags and self.mailgun:
                self.notify_mailgun(obj,self.message_pattern(obj))

            if "email" in obj.Tags and self.email:
                self.notify_email(obj,self.message_pattern(obj))



    def common_notifiers(self,obj,kv_tags_dictname,kv_dict):
        keynames = set(kv_dict[kv_tags_dictname].keys())
        obj_tags = set(obj.Tags)

        common = keynames.intersection(obj_tags)

        return common

    def message_pattern(self,obj):

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

        return message_template

    def notify_hipchat(self, obj, message_template):
        common_hipchat_rooms = self.common_notifiers(obj,"rooms",self.hipchat)

        # Use hipchat library to use for notifications requires api_token and
        # url
        hipster = hipchat.HipChat(
            token=self.hipchat["api_token"], url=self.hipchat["url"])

        for roomname in common_hipchat_rooms:

            if obj.Status == NotificationEngine.PASSING_STATE:
                color_value = "green"
                notify_value = 0

            elif obj.Status == NotificationEngine.WARNING_STATE:
                color_value = "yellow"
                notify_value = 1

            elif obj.Status == NotificationEngine.CRITICAL_STATE:
                color_value = "red"
                notify_value = 1

            elif obj.Status == NotificationEngine.UNKNOWN_STATE:
                color_value = "gray"
                notify_value = 1


            hipster.message_room(room_id=int(self.hipchat["rooms"][roomname]), message_from="Consul",
                                 message=message_template,
                                 notify=notify_value,
                                 color=color_value)

    def notify_slack(self, obj, message_template):
        common_slack_rooms = self.common_notifiers(obj,"rooms",self.slack)


        # Use slack library to use for notifications requires api_token and
        # url
        slacker = Slacker(self.slack["api_token"])

        for roomname in common_slack_rooms:

            slacker.chat.post_message(self.slack["rooms"][roomname],message_template,"Consul")


    def notify_mailgun(self,obj, message_template):
        common_mailgun_teams = self.common_notifiers(obj,"teams",self.mailgun)


        api_endpoint = "https://api.mailgun.net/v2/{domain}/messages".format(domain=self.mailgun["mailgun_domain"])
        auth_tuple=('api', self.mailgun["api_token"])

        for teamname in common_mailgun_teams:

            requests.post(api_endpoint,
                          auth=auth_tuple,
                          data={'from':self.mailgun["from"],
                                'to':self.mailgun["teams"][teamname],
                                'subject': 'Consul Alert',
                                'text': message_template})



    def notify_email(self,obj,message_template):
        common_email_teams = self.common_notifiers(obj,"teams",self.email)

        server = smtplib.SMTP(self.email["mail_domain_address"])

        if self.email["username"] and self.email["password"]:
            server.login(self.email["username"],self.email["password"])

        from_address = self.email["from"]
        subject = "Consul Alert"

        for teamname in common_email_teams:

            body = string.join((
                "From: %s" % from_address,
                "To: %s" % ', '.join(teamname),
                "Subject: %s" % subject ,
                "",
                message_template
                ), "\r\n")

            server.sendmail(from_address,teamname,body)

        server.quit()



