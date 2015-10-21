import requests
import settings
import smtplib
import string
import json as json

def notify_hipchat(obj, message_template, common_notifiers, consul_hipchat):
    notify_value = 0
    color_value = "yellow"

    for roomname in common_notifiers:

        if obj.Status == settings.PASSING_STATE:
            color_value = "green"
            notify_value = 0

        elif obj.Status == settings.WARNING_STATE:
            color_value = "yellow"
            notify_value = 1

        elif obj.Status == settings.CRITICAL_STATE:
            color_value = "red"
            notify_value = 1

        elif obj.Status == settings.UNKNOWN_STATE:
            color_value = "gray"
            notify_value = 1

        try:
            response = requests.post(
                consul_hipchat["url"],
                params={
                    'room_id': int(consul_hipchat["rooms"][roomname]),
                    'from': 'Consul',
                    'message': message_template,
                    'notify': notify_value,
                    'color': color_value,
                    'auth_token': consul_hipchat["api_token"]})

        except requests.exceptions.SSLError:

            response = requests.post(
                consul_hipchat["url"],
                verify=False,
                params={
                    'room_id': int(consul_hipchat["rooms"][roomname]),
                    'from': 'Consul',
                    'message': message_template,
                    'notify': notify_value,
                    'color': color_value,
                    'auth_token': consul_hipchat["api_token"]},
            )

        if response.status_code == 200:
            settings.logger.info(
                "NotifyPlugin=Hipchat Server={url} "
                "Room={room} Message={message} "
                "Status_Code={status}".format(
                    url=consul_hipchat["url"],
                    room=consul_hipchat["rooms"][roomname],
                    message=message_template,
                    status=response.status_code))

            return response.status_code
        else:
            settings.logger.error(
                "NotifyPlugin=Hipchat Server={url} "
                "Room={room} Message={message} "
                "Status_Code={status}".format(
                    url=consul_hipchat["url"],
                    room=consul_hipchat["rooms"][roomname],
                    message=message_template,
                    status=response.status_code))

            return response.status_code


def notify_slack(message_template, common_notifiers, consul_slack):
    for roomname in common_notifiers:

        response = requests.post(
            "https://slack.com/api/chat.postMessage",
            params={
                'channel': consul_slack["rooms"][roomname],
                'username': 'Consul',
                'token': consul_slack["api_token"],
                'text': message_template})

        if response.status_code == 200:
            settings.logger.info(
                "NotifyPlugin=Slack "
                "Room={room} "
                "Message={message} "
                "Status_Code={status}".format(
                    room=consul_slack["rooms"][roomname],
                    message=message_template,
                    status=response.status_code))

            return response.status_code
        else:
            settings.logger.error(
                "NotifyPlugin=Slack "
                "Room={room} "
                "Message={message} "
                "Status_code={status}".format(
                    room=consul_slack["rooms"][roomname],
                    message=message_template,
                    status=response.status_code))
            return response.status_code


def notify_mailgun(message_template, common_notifiers, consul_mailgun):
    api_endpoint = "https://api.mailgun.net/v2/{domain}/messages".format(
        domain=consul_mailgun["mailgun_domain"])
    auth_tuple = ('api', consul_mailgun["api_token"])

    for teamname in common_notifiers:

        response = requests.post(api_endpoint,
                                 auth=auth_tuple,
                                 data={'from': consul_mailgun["from"],
                                       'to': consul_mailgun["teams"][teamname],
                                       'subject': 'Consul Alert',
                                       'text': message_template})

        if response.status_code == 200:
            settings.logger.info(
                "NotifyPlugin=Mailgun "
                "Endpoint={url} Message={message} "
                "Status_Code={status}".format(url=api_endpoint,
                                              message=message_template,
                                              status=response.status_code))

            return response.status_code
        else:
            settings.logger.error(
                "NotifyPlugin=Mailgun "
                "Endpoint={url} "
                "Message={message} "
                "Status_code={status}".format(url=api_endpoint,
                                              message=message_template,
                                              status=response.status_code))
            return response.status_code


def notify_email(message_template, common_notifiers, consul_email):
    server = smtplib.SMTP(consul_email["mail_domain_address"])

    if consul_email["username"] and consul_email["password"]:
        server.login(consul_email["username"], consul_email["password"])

    from_address = consul_email["from"]
    subject = "Consul Alert"

    for teamname in common_notifiers:
        body = string.join((
            "From: %s" % from_address,
            "To: %s" % ', '.join(consul_email["teams"][teamname]),
            "Subject: %s" % subject,
            "",
            message_template
        ), "\r\n")

        server.sendmail(from_address, consul_email["teams"][teamname], body)

    server.quit()


def notify_pagerduty(
        obj, message_template, common_notifiers, consul_pagerduty):
    for teamname in common_notifiers:

        if obj.Status == settings.PASSING_STATE:
            pagerduty_event_type = "resolve"
        else:
            pagerduty_event_type = "trigger"

        pagerduty_incident_key = "{node}/{CheckID}".format(node=obj.Node,
                                                           CheckID=obj.CheckID)

        pagerduty_data = {"service_key": consul_pagerduty["teams"][teamname],
                          "event_type": pagerduty_event_type,
                          "description": message_template,
                          "incident_key": pagerduty_incident_key}

        response = requests.post(
            "https://events.pagerduty.com/generic/2010-04-15/create_event.json",
            data=json.dumps(pagerduty_data),
            headers={'content-type': 'application/json'})


        if response.status_code == 200:
            settings.logger.info(
                "NotifyPlugin=PagerDuty "
                "Message={message} "
                "Status_Code={status}".format(message=message_template,
                                              status=response.status_code))
            return response.status_code
        else:
            settings.logger.error(
                "NotifyPlugin=Mailgun "
                "Message={message} "
                "Status_Code={status}".format(message=message_template,
                                              status=response.status_code))
            return response.status_code