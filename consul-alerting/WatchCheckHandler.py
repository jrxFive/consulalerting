#!/usr/bin/env python

import consulate
import socket
import simplejson as json
import sys
import logging
from NotificationEngine import NotificationEngine
from ConsulHealthNodeStruct import ConsulHealthNodeStruct


class WatchCheckHandler(object):

    """
    WatchCheckHandler will compare current node state from previous,
    if there are changes in checks will return those objects as a list of ConsulHealthNodeStruct.

    When running checkForAlertChanges, current node state will be filtered by blacklists in
    Consul KV
    """

    def __init__(self, hostname=socket.gethostname(), consulAgentIP="0.0.0.0"):
        """

        """

        self.hostname = hostname
        self.kv_hostname_lookup = "node/{hostname}".format(
            hostname=self.hostname)
        self.consulate_session = consulate.Consulate(host="0.0.0.0")
        self.consulAPILookups()
        self.alertsBlacklist()

    def __getattr__(self, item):
        return None

    def consulAPILookups(self):
        """
        Get prior node state if any, the current node state, and the catalog of services/checks associated
        with this node. Since checks do not have a tag attribute, use the ConsulKV alerting/healthchecktags
        to determine who will get notified by what
        """
        try:
            self.catalog_node = self.consulate_session.catalog.node(self.hostname)
            self.health_node_current = self.consulate_session.health.node(
                self.hostname)
            self.health_check_tags = self.consulate_session.kv[
                "alerting/healthchecktags"]
        except KeyError:
            raise

        try:
            self.health_node_prior = self.consulate_session.kv[
                self.kv_hostname_lookup]
        except KeyError:
            self.health_node_prior = []

    def alertsBlacklist(self):
        """
        Obtain blacklist options, if KeyError these keys do not exist in Consul KV
        """
        try:
            self.node_blacklist = self.consulate_session.kv[
                "alerting/blacklist/nodes"]
            self.service_blacklist = self.consulate_session.kv[
                "alerting/blacklist/services"]
            self.check_blacklist = self.consulate_session.kv[
                "alerting/blacklist/checks"]
        except KeyError:
            print "Consul blacklists do not exist"
            raise

    def getHashStateSet(self, object_list, state):
        """
        Used to compare prior node state to current
        """
        return set(
            [hash(obj) for obj in object_list if obj.Status == state])

    def getObjectListByState(self, object_list, state):
        return filter(
            lambda obj: obj.Status == state, object_list)

    def filterByBlacklists(self, object_list):

        try:
            # filter by services
            filter_1 = [
                obj for obj in object_list if obj.ServiceName not in self.service_blacklist]

            # filter by checks
            final_filter = [
                obj for obj in filter_1 if obj.ServiceName not in self.check_blacklist]

            return final_filter

        except Exception:
            raise

    def createConsulHealthNodeList(self):

        self.health_node_current_object_list = [ConsulHealthNodeStruct(
            self.catalog_node, self.health_check_tags, **obj) for obj in self.health_node_current]

        self.health_node_prior_object_list = [ConsulHealthNodeStruct(
            self.catalog_node, self.health_check_tags, **obj) for obj in self.health_node_prior]

        return (self.health_node_current_object_list, self.health_node_prior_object_list)

    def checkForAlertChanges(self):
        """
        Return alerts that have changed in status, if the node has never PUT in Consul KV return object list if there
        any warning/critical statuses.

        If the node has PUT beforehand compare based on object hash values, if there are any changes return
        object list (ConsulHealthNodeStruct)
        """

        # current host is blacklisted
        if self.hostname in self.node_blacklist:
            return None

        # list is empty, need to put current_node_health in KV/node when
        # completed
        if not self.health_node_prior:

            try:
                health_node_current_object_list, _ = self.createConsulHealthNodeList()
                health_node_current_object_list = self.filterByBlacklists(
                    health_node_current_object_list)

                # filter by state
                node_current_state_warning = self.getObjectListByState(
                    health_node_current_object_list, ConsulHealthNodeStruct.WARNING_STATE)
                node_current_state_critical = self.getObjectListByState(
                    health_node_current_object_list, ConsulHealthNodeStruct.CRITICAL_STATE)

                # PUT current health (json) into node/hostname
                self.consulate_session.kv[self.kv_hostname_lookup] = json.dumps(
                    self.health_node_current)

                return node_current_state_warning + node_current_state_critical

            except Exception:
                raise
            finally:
                self.consulate_session.kv[self.kv_hostname_lookup] = json.dumps(
                    self.health_node_current)

        else:

            try:
                # create object lists of ConsulHealthNodeStruct
                health_node_current_object_list, health_node_prior_object_list = self.createConsulHealthNodeList()

                health_node_current_object_list = self.filterByBlacklists(
                    health_node_current_object_list)
                health_node_prior_object_list = self.filterByBlacklists(
                    health_node_prior_object_list)

                health_node_current_object_set_passing = self.getHashStateSet(
                    health_node_current_object_list, ConsulHealthNodeStruct.PASSING_STATE)

                health_node_current_object_set_warning = self.getHashStateSet(
                    health_node_current_object_list, ConsulHealthNodeStruct.WARNING_STATE)

                health_node_current_object_set_critical = self.getHashStateSet(
                    health_node_current_object_list, ConsulHealthNodeStruct.CRITICAL_STATE)

                health_node_current_object_set_unknown = self.getHashStateSet(
                    health_node_current_object_list, ConsulHealthNodeStruct.UNKNOWN_STATE)

                health_node_prior_object_set_warning = self.getHashStateSet(
                    health_node_prior_object_list, ConsulHealthNodeStruct.WARNING_STATE)

                health_node_prior_object_set_critical = self.getHashStateSet(
                    health_node_prior_object_list, ConsulHealthNodeStruct.CRITICAL_STATE)

                # Check for all current passing that were in prior warning/critical, set
                # intersection
                from_warning_or_critical_to_pass = health_node_current_object_set_passing & health_node_prior_object_set_warning & health_node_prior_object_set_warning

                # Check for current warning in prior warning, if not in prior new alert,
                # set difference
                warning_to_warning_difference = health_node_current_object_set_warning - \
                    health_node_prior_object_set_warning

                # check for current warning in prior critical, set intersection
                from_critical_to_warning = health_node_current_object_set_warning & health_node_prior_object_set_critical

                # check for current critical in prior critical, if not in prior new alert,
                # set difference
                critical_to_critical_difference = health_node_current_object_set_critical - \
                    health_node_prior_object_set_critical

                # combine set results, set union
                alert_hash_set = health_node_current_object_set_unknown | from_warning_or_critical_to_pass | warning_to_warning_difference | from_critical_to_warning | critical_to_critical_difference

                self.consulate_session.kv[self.kv_hostname_lookup] = json.dumps(
                    self.health_node_current)

                if alert_hash_set:
                    return [
                        obj for obj in health_node_current_object_list if hash(obj) in alert_hash_set]
                else:
                    return None

            except Exception:
                raise
            finally:
                self.consulate_session.kv[self.kv_hostname_lookup] = json.dumps(
                    self.health_node_current)


if __name__ == "__main__":
    w = WatchCheckHandler()
    alert_list = w.checkForAlertChanges()

    if alert_list:
        n = NotificationEngine(alert_list)
        n.Run()
