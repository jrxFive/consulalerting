from Settings import Settings


class ConsulHealthStruct(Settings):
    """
    A Python Object representation of Consul /v1/health/node/<node>
      {
        "Node": "foobar",
        "CheckID": "service:redis",
        "Name": "Service 'redis' check",
        "Status": "passing",
        "Notes": "",
        "Output": "",
        "ServiceID": "redis",
        "ServiceName": "redis"
      }
    """

    def __init__(self, **kwargs):
        """
        Constructs a :class `ConsulHealthStruct <ConsulHealth> using
        a unpacked dictionary from /v1/health/node/<node>. Will also associate
        Tags from /v1/catalog/node/<node>

        :param node_catalog, /v1/catalog/node/<node>, dictionary
        :param non_service_checks, /v1/kv/systemchecks, list, list of tags usually for non service checks
        :param **kwargs, unpacked dictionary object of /v1/health/node/<node>
        """
        super(ConsulHealthStruct, self).__init__()
        self.__dict__.update(kwargs)

    def __str__(self):
        return "{dict}".format(dict=self.__dict__)

    def __getattr__(self, item):
        return None

    def __repr__(self):
        return "{dict}".format(dict=self.__dict__)

    def __hash__(self):
        """
        Uses key/values from /v1/health/node/<node>,
        Node,CheckID,Name,ServiceID,ServiceName, Status,Notes,Output are omitted due to that they will change
        The hash is used to determine if a check was ever in a prior state, in WatchCheckHandler.py
        """
        return hash((self.Node, self.CheckID, self.Name, self.ServiceID, self.ServiceName))

    def __eq__(self, other):
        return (self.Node, self.CheckID, self.Name, self.ServiceID, self.ServiceName) == (
        other.Node, other.CheckID, other.Name, other.ServiceID, other.ServiceName)

    def addTags(self, node_catalog, non_service_checks):
        """
        Determines what type of check the object is based on attributes of ServiceID and ServiceName
        If both are blank then the check is not associated to an Application, to know who to alert to
        use the tags give from non_service_checks, otherwise do a lookup of the tags its associated to
        based on the catalog dictionary. ensures all the tags are lowercase

        :param node_catalog, /v1/catalog/node/<node>, dictionary
        :param non_service_checks, /v1/kv/systemchecks, list, list of tags usually for non service checks
        """
        if not self.ServiceID and not self.ServiceName:  # Is a system check
            tag_list = non_service_checks
        else:
            tag_list = node_catalog["Services"][self.ServiceID]["Tags"]

        try:
            if tag_list:
                self.Tags = map(lambda tag: tag.lower(), tag_list)
            else:
                self.Tags = []
        except TypeError:
            ConsulHealthStruct.logger.error(
                "Message=non_service_checks is not an iterable Type={type}, Value={value}".format(type=type(non_service_checks),
                                                                                          value=non_service_checks))
            raise
        except AttributeError:
            ConsulHealthStruct.logger.error(
                "Message=value within non_service_checks is not a string Type={type}, Value={value}".format(
                    type=type(non_service_checks),
                    value=non_service_checks))
