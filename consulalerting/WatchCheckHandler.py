#!/usr/bin/env python

import consulate
import json as json
import sys
import utilities
import settings
from NotificationEngine import NotificationEngine
from ConsulHealthStruct import ConsulHealthStruct


class WatchCheckHandler(object):

    """
    WatchCheckHandler will compare current state from previous,
    if there are changes in checks will return those objects
    as a list of ConsulHealthStruct.

    When running checkForAlertChanges, current state will be
    filtered by blacklists in Consul KV.
    """

    def __init__(self, consulate_session):
        """
        """
        self.consul = consulate_session

    def __getattr__(self, item):
        return None

    def filterByBlacklists(self, object_list):
        """
        Filter a list of ConsulHealthStruct by the blacklists in the KV.

        Returns:
          filtered_object_list: Removal of flagged blacklist catalog
        Raises:
          TypeError: when a blacklist does not exist within the object
        """
        try:
            filtered_object_list = []
            for obj in object_list:

                # filter by service_blacklist
                if (obj.ServiceName and obj.ServiceName in self.service_blacklist) or ("*" in self.service_blacklist):
                    continue

                # filter by check_blacklist
                if (obj.CheckID and obj.CheckID in self.check_blacklist) or ("*" in self.check_blacklist):
                    continue

                # filter by node_blacklist
                if (obj.Node and obj.Node in self.node_blacklist) or ("*" in self.node_blacklist):
                    continue

                filtered_object_list.append(obj)

            settings.logger.debug("FilteredConsulHealthStructList={filtered_list}".format(
                filtered_list=filtered_object_list))
            return filtered_object_list

        except TypeError:
            settings.logger.error(
                "Message=Blacklist variables not found")

            raise TypeError("blacklist variables not found")

    def nodeCatalogTags(self, object_list, health_check_tags=None):
        """
        Add tags to each object in a list of ConsulHealthStruct, acquires
        catalog for each 'Node' to associate service tags for
        NotificationEngine to determine who to alert. Consul checks not
        associated to application or services do not have tags, used list
        of check_tags or the Consul KV check tags to determine who to notify.
        """
        if not health_check_tags:
            health_check_tags = self.health_check_tags

        for obj in object_list:
            node_catalog = self.consul.catalog.node(obj.Node)
            obj.addTags(node_catalog, health_check_tags)

    def checkForAlertChanges(
            self,
            health_current_object_list,
            health_prior_object_list):
        """
        Return alerts that have changed in status, if never PUT in Consul KV
        return object list if there any warning/critical statuses.

        If PUT beforehand compare based on object hash values, if there are
        any changes return object list (ConsulHealthStruct)
        """

        # list is empty, need to put current_health in KV when
        # completed

        if not health_prior_object_list:

            try:
                # filter by state
                current_state_warning = utilities.getObjectListByState(
                    health_current_object_list,
                    settings.WARNING_STATE)
                current_state_critical = utilities.getObjectListByState(
                    health_current_object_list,
                    settings.CRITICAL_STATE)

                # PUT current health (json)
                self.consul.kv[
                    settings.KV_PRIOR_STATE] = json.dumps(
                    self.health_current)

                alert_list = current_state_warning + current_state_critical

                if alert_list:
                    settings.logger.debug("NoPriorAlertList={alert_list}".format(
                        alert_list=alert_list))
                    return alert_list
                else:
                    settings.logger.debug("NoPriorAlertList=None")
                    return None

            except Exception:
                settings.logger.error("Message=Failed to create alert list with "
                                      "no prior catalog")
                raise

        else:

            try:
                health_current_object_set_pass = utilities.getHashStateSet(
                    health_current_object_list,
                    settings.PASSING_STATE)

                health_current_object_set_warning = utilities.getHashStateSet(
                    health_current_object_list,
                    settings.WARNING_STATE)

                health_current_object_set_critical = utilities.getHashStateSet(
                    health_current_object_list,
                    settings.CRITICAL_STATE)

                health_current_object_set_unknown = utilities.getHashStateSet(
                    health_current_object_list,
                    settings.UNKNOWN_STATE)

                health_prior_object_set_warning = utilities.getHashStateSet(
                    health_prior_object_list, settings.WARNING_STATE)

                health_prior_object_set_critical = utilities.getHashStateSet(
                    health_prior_object_list, settings.CRITICAL_STATE)

                # Check for all current passing that were in prior
                #  warning/critical, set
                # intersection
                from_crit_to_pass = health_current_object_set_pass & \
                    health_prior_object_set_critical

                # Check for all current passing that were in prior
                #  warning, set
                # intersection
                from_warn_to_pass = health_current_object_set_pass & \
                    health_prior_object_set_warning

                # Check for current warning in prior warning,
                #  if not in prior new alert,
                # set difference
                warning_to_warning_diff = health_current_object_set_warning - \
                    health_prior_object_set_warning

                # check for current warning in prior critical,
                #  set intersection
                from_critical_to_warning = health_current_object_set_warning &\
                    health_prior_object_set_critical

                # check for current critical in prior critical, if not
                #  in prior new alert,
                # set difference
                crit_to_crit_diff = health_current_object_set_critical - \
                    health_prior_object_set_critical

                # combine set results, set union
                alert_hash_set = health_current_object_set_unknown | \
                    from_crit_to_pass | \
                    from_warn_to_pass | \
                    warning_to_warning_diff | \
                    from_critical_to_warning | \
                    crit_to_crit_diff

                if alert_hash_set:

                    # Find alerts based on hash value
                    alert_list = [
                        obj for obj in health_current_object_list
                        if hash(obj) in alert_hash_set]

                    settings.logger.debug("PriorAlertList={alert_list}".format(
                        alert_list=alert_list))
                    return alert_list

                else:
                    settings.logger.debug("PriorAlertList=None")
                    return None

            except Exception:
                settings.logger.error(
                    "Message=Failed to create alert list with prior catalog")
                raise

    def Run(self):
        """ Performs the internal operations to create an alert_list
        if there is one at all. Will not run if another consulalerting
        instance has acquired a lock on the same catalog

        Returns:
          alert_list: A list of ConsulHealthChecks to notify on or blank list
        """
        settings.logger.info("Message=Performing consul api lookups")

        self.health_current = utilities.currentState()

        currMD5Hash = utilities.getHash(self.health_current)
        session_id = utilities.createSession()

        lock_result = utilities.acquireLock("{k}/{h}".format(k=settings.KV_ALERTING_HASHES,
                                                             h=currMD5Hash), session_id)

        if not lock_result:
            settings.logger.info("Message=Other consul alerting instance"
                                 "Processing alert and notifcation")
            return []

        self.consul.kv[settings.KV_PRIOR_STATE] = json.dumps(
            self.health_current)

        self.health_prior = utilities.priorState(settings.KV_PRIOR_STATE)

        self.health_check_tags = utilities.getCheckTags(
            settings.KV_ALERTING_HEALTH_CHECK_TAGS)

        settings.logger.info("Message=Obtaining blacklists")

        self.node_blacklist = utilities.getBlacklist(
            settings.KV_ALERTING_BLACKLIST_NODES)

        self.service_blacklist = utilities.getBlacklist(
            settings.KV_ALERTING_BLACKLIST_SERVICES)

        self.check_blacklist = utilities.getBlacklist(
            settings.KV_ALERTING_BLACKLIST_CHECKS)

        settings.logger.info("Message=Creating current and prior health "
                             "ConsulHealthStruct lists")

        health_prior_object_list = utilities.createConsulHealthList(
            self.health_prior)

        health_current_object_list = utilities.createConsulHealthList(
            self.health_current)

        settings.logger.info(
            "Message=Filtering current and prior health against blacklists")

        health_prior_object_list_filtered = self.filterByBlacklists(
            health_prior_object_list)

        health_current_object_list_filtered = self.filterByBlacklists(
            health_current_object_list)

        settings.logger.info("Message=Creating alert list")

        alert_list = self.checkForAlertChanges(
            health_current_object_list_filtered,
            health_prior_object_list_filtered)

        if alert_list:
            settings.logger.info(
                "Message=AlertsCreated={numAlerts}".format(numAlerts=len(alert_list)))

            settings.logger.info(
                "Message=Obtaining Tags for new alerts")

            alert_list = self.nodeCatalogTags(alert_list)

        settings.logger.info("Message=Returning list of alerts")

        return alert_list


if __name__ == "__main__":
    w = WatchCheckHandler(settings.consul)
    alert_list = w.Run()

    if alert_list:
        n = NotificationEngine(alert_list, settings.consul)
        n.Run()
