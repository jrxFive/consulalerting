# Consul Alerting
A set of python files for Consul for checks, watches, and notifications

After installing files in a directory of your choosing, use/edit ConsulAlertingKVBootstrap.py to ensure
the scripts can obtain the necessary KV information from Consul

```python

ConsulAlertingKVBoostrap.py


blacklist_nodes = {"fqdn":"",
                   "other_fqdn":""}
blacklist_services = {"redis":""}
blacklist_checks = {"service:redis":""}

health_check_tags = ["devops","hipchat","techops"]

notify_hipchat= {"API_TOKEN":"",
                 "URL":"",
                 "rooms":{"devops":3},
                        {"techops":4},
                 }

```

| Variable Name | Type | Description |
| blacklist_nodes | Dict | Consul agents are not to notify of state changes, by "Node" name in /v1/health/node/<node> |
| blacklist_services | Dict | Consul agents are not to notify of particular services, by "ServiceName" in /v1/health/node/<node> |
| blacklist_checks | Dict | Consul agents are not to notify based on checks, by "CheckID" in  /v1/health/node/<node> |
| health_check_tags | List | Tags to be used to determine who to alert to and what type of alerts for non-application checks |
| notify_hipchat | Dict | Required API_TOKEN, URL, optional: rooms ( Dict ), with Dict objects of "roomname" : roomvalue |


# Using Tags to notify

```javascript
{
  "service": {
    "name": "redis",
    "tags": ["devops","master","hipchat","dev"],
    "port": 8000,
    "check": {
      "script": "/usr/local/bin/check_redis.py",
      "interval": "10s"
    }
  }
}
```


After the script is run, you can always change these within the Consul UI

# Consul Watch Check Handler Setup
```javascript
{
  "watches": [
    {
      "type": "checks",
      "handler": "/opt/consul/scripts/WatchCheckHandler.py"
    }
  ]
}
```
