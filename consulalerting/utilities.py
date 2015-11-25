import consulate
import hashlib
import requests
import json
import settings
from ConsulHealthStruct import ConsulHealthStruct


def currentState():
    try:
        current = settings.consul.health.state("any")
        settings.logger.debug("CurrentConsulHealth={health}".format(health=current))

        return current
    except KeyError:
        settings.logger.error("Message=Could no obtain current catalog from consul"
                     "ConsulURI={u}".format(u=settings.consul._base_uri))


def priorState(key):
    try:
        prior = settings.consul.kv[key]
        settings.logger.debug("PriorConsulHealth={health}".format(
            health=prior))

        return json.loads(prior)
    except:
        prior = []
        settings.logger.warn("Message=No previous prior catalog health found from "
                    "ConsulURI={l}".format(l=key))

        return prior


def getCheckTags(key):
    try:
        tags = settings.consul.kv[key]
        settings.logger.debug("HealthCheckTags={tags}".format(
            tags=tags))

        return json.loads(tags)
    except:
        tags = []
        settings.logger.warn("Message=Could not obtain system check tags from "
                    "ConsulURI={l}".format(l=key))

        return tags




def createSession():
    return settings.consul.session.create(ttl='10s', delay='0s', behavior='delete')


def getHash(currentState):
    return hashlib.md5(str(currentState)).hexdigest()


def checkForKey(key):
    return key in settings.consul.kv


def putKey(key, value):

    try:
        settings.consul.kv[key] = value
    except:
        pass


def acquireLock(key, session_id):

    return settings.consul.kv.acquire_lock(key, session_id)


def releaseLock(key, session_id):

    return settings.consul.kv.release_lock(key, session_id)


def getBlacklist(key):

    try:
        bl = settings.consul.kv[key]
        settings.logger.debug("Key={k} Tags={t}".format(k=key, t=bl))

        return json.loads(bl)

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


def common_notifiers(obj, kv_tags_dictname, kv_dict):
    keynames = set(kv_dict[kv_tags_dictname].keys())
    obj_tags = set(obj.Tags)

    common = keynames.intersection(obj_tags)

    return common


def load_plugin(KV_LOCATION, tags_dictname):
    # get request to 0.0.0.0:8500/v1/kv/notify/<plugin_name>
    #  which routes to consul master
    plugin = json.loads(settings.consul.kv[KV_LOCATION])

    # Convert Keys to lower case
    plugin = _dict_keys_to_low(plugin)

    plugin[tags_dictname] = dict((key.lower(), value) for key,
                                 value in plugin[tags_dictname].iteritems())

    return plugin


def _dict_keys_to_low(dictionary):
    dict_keys_lowercase = dict((key.lower(), value)
                               for key, value in dictionary.iteritems())

    return dict_keys_lowercase
