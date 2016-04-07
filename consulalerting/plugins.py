import smtplib
import string
import json as json
from datetime import datetime
from urlparse import urljoin

import requests
import settings
from requests import ConnectionError, HTTPError


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


def notify_influxdb(obj, message_template, common_notifiers, consul_influxdb):
    for database in common_notifiers:

        message_template = message_template.replace('\n', ' ')

        tags = 'ServiceID={ServiceID},CheckID={CheckID},Status={Status}'.format(
            ServiceID=obj.ServiceID,
            CheckID=obj.CheckID,
            Status=obj.Status)

        message_template = '{series},{tags} value="{msg}"'.format(
            series=consul_influxdb["series"],
            tags=tags,
            msg=message_template)

        response = requests.post(
            consul_influxdb["url"],
            params={'db': consul_influxdb["databases"][database]},
            data=message_template)

        if response.status_code == 200:
            settings.logger.info(
                "NotifyPlugin=InfluxDB Server={url} "
                "Database={database} Message={message} "
                "Status_Code={status}".format(
                    url=consul_influxdb["url"],
                    database=consul_influxdb["databases"][database],
                    message=message_template,
                    status=response.status_code))

            return response.status_code
        else:
            settings.logger.error(
                "NotifyPlugin=InfluxDB Server={url} "
                "Database={database} Message={message} "
                "Status_Code={status}".format(
                    url=consul_influxdb["url"],
                    database=consul_influxdb["databases"][database],
                    message=message_template,
                    status=response.status_code))

            return response.status_code


def notify_cache(obj, message_template, cachet_config):
    if not cachet_config.get('api_token'):
        settings.logger.error("A Cachet API token must be provided in order to post incidents!")
        return

    if not cachet_config.get('site_url'):
        settings.logger.error('A Cachet site url must be provided in order to post incidients!')
        return

    # Constants and configuration for the rest of the function
    component_endpoint = "/api/v1/components"
    component_url = urljoin(cachet_config['site_url'], component_endpoint)

    incident_endpoint = "/api/v1/incidents"
    incident_url = urljoin(cachet_config['site_url'], incident_endpoint)

    headers = {
        'X-Cachet-Token': cachet_config['api_token'],
        'content-type': 'application/json',
    }

    incident_status = {
        'Investigating': 1,
        'Identified': 2,
        'Watching': 3,
        'Fixed': 4
    }

    component_statuses = {
        'Operational': 1,
        'Performance Issues': 2,
        'Partial Outage': 3,
        'Major Outage': 4
    }

    status_incident_map = {
        settings.PASSING_STATE: incident_status['Fixed'],
        settings.WARNING_STATE: incident_status['Investigating'],
        settings.CRITICAL_STATE: incident_status['Investigating'],
        settings.UNKNOWN_STATE: incident_status['Investigating']
    }

    status_component_map = {
        settings.PASSING_STATE: component_statuses['Operational'],
        settings.WARNING_STATE: component_statuses['Performance Issues'],
        settings.CRITICAL_STATE: component_statuses['Major Outage'],
        settings.UNKNOWN_STATE: component_statuses['Partial Outage']
    }

    # Get existing components to see if we can match the Consul state change to a Cachet component
    # component_id will be set as a result
    component_id = None
    intersecting_tag = None
    try:
        components_response = requests.get(component_url)
        components_response.raise_for_status()
        components = components_response.json().get('data')
        if components:
            component_names = [component.get('name') for component in components]
            intersecting_tag, = set(component_names).intersection(obj.Tags)
            if intersecting_tag:
                component_id = [comp['id'] for comp in components if comp['name'] == intersecting_tag][0]
    except (ConnectionError, HTTPError) as components_exception:
        settings.logger.error('Unable to retrieve Cachet components: {error}'.format(error=components_exception))
    except ValueError:
        # there was no intersecting tag to unpack
        pass

    # Construct the payload
    data = {
        'name': intersecting_tag if intersecting_tag else 'Consul State Change',
        'message': message_template.replace('\n', ' '),
        'status': status_incident_map.get(obj.Status),
        'visible': 1,  # always visible
        'notify': cachet_config['notify_subscribers'] if cachet_config['notify_subscribers'] else False
    }
    if component_id:
        data['component_id'] = component_id
        data['component_status'] = status_component_map.get(obj.Status)

    try:
        response = requests.post(incident_url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        return response.status_code
    except (ConnectionError, HTTPError) as incidents_exception:
        settings.logger.error('Unable to post Cachet incident: {error}'.format(error=incidents_exception))


def notify_elasticsearchlog(obj, message_template, es_logpath):

    logdata = {"@timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
               "Message": message_template.replace('\n', ' '),
               "Node": obj.Node,
               "CheckID": obj.CheckID,
               "Name": obj.Name,
               "Tags": ', '.join(obj.Tags),
               "Notes": obj.Notes,
               "Output": obj.Output,
               "ServiceID": obj.ServiceID,
               "ServiceName": obj.ServiceName
               }

    try:
        with open(es_logpath["logpath"], "a") as elasticsearchlog:
            json.dump(logdata, elasticsearchlog)
            elasticsearchlog.write("\n")

    except IOError, es_log_error:
        settings.logger.error("There was an issue writing to {logpath}: {error}".format(logpath=es_logpath,
                                                                                        error=es_log_error))
