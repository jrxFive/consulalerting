import consulate
import hashlib
import requests
import json
import settings
from ConsulHealthStruct import ConsulHealthStruct


def currentState(consul):
    try:
        current = consul.health.state("any")
        settings.logger.debug("CurrentConsulHealth={health}".format(health=current))

        return current
    except KeyError:
        settings.logger.error("Message=Could no obtain current catalog from consul"
                     "ConsulURI={u}".format(u=consul._base_uri))


def priorState(consul, key):
    try:
        prior = consul.kv[key]
        settings.logger.debug("PriorConsulHealth={health}".format(
            health=prior))

        return json.loads(prior)
    except:
        prior = []
        settings.logger.warn("Message=No previous prior catalog health found from "
                    "ConsulURI={l}".format(l=key))

        return prior


def getCheckTags(consul, key):
    try:
        tags = consul.kv[key]
        settings.logger.debug("HealthCheckTags={tags}".format(
            tags=tags))

        return json.loads(tags)
    except:
        tags = []
        settings.logger.warn("Message=Could not obtain system check tags from "
                    "ConsulURI={l}".format(l=key))

        return tags




def createSession(consul):
    return consul.session.create(ttl='10s', delay='0s', behavior='delete')


def getHash(currentState):
    return hashlib.md5(str(currentState)).hexdigest()


def checkForKey(consul, key):
    return key in consul.kv


def putKey(consul, key, value):

    try:
        consul.kv[key] = value
    except:
        pass


def acquireLock(consul, key, session_id):

    return consul.kv.acquire_lock(key, session_id)


def getBlacklist(consul, key):

    try:
        bl = consul.kv[key]
        settings.logger.debug("Key={k} Tags={t}".format(k=key, t=bl))

        return bl

    except KeyError:
        settings.logger.warn("Message=Could not obtain node blacklist from "
                    "ConsulURI={location}".format(location=key))
        return []


def createConsulHealthList(object_list):
    """
    Creates a list of ConsulHealthStruct
    """
    try:
        object_list = [ConsulHealthStruct(**obj) for obj in object_list]
        settings.logger.debug("ConsulHealthList={lo}".format(lo=object_list))
        return object_list

    except TypeError:
        settings.logger.error("Message=createConsulHealthList failed, "
                     "object_list needs to be iterable")
        raise


def getHashStateSet(object_list, state):
    """
    Used to compare prior node state to current
    """
    return set(
        [hash(obj) for obj in object_list if obj.Status == state])


def getObjectListByState(object_list, state):
    """
    Filter a list of ConsulHealtNodeStruct by state
    States: passing,warning,critical,unknown
    """
    return filter(
        lambda obj: obj.Status == state, object_list)
