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
