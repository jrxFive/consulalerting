package main

//Structure to represent Telegraphite plugin stanza and associated Key/Values
type TelegraphitePlugin struct {
	Plugin   string
	KV       []string
	Protocol string
	Service  bool
	IP       string
	Port     int
}

//Generic Template
var TeleGraphiteTemplate string = `# Telegraf configuration

[tags]

# Configuration for telegraf agent
[agent]
	# Default data collection interval for all plugins
	interval = "10s"

	# If utc = false, uses local time (utc is highly recommended)
	utc = true

	# Precision of writes, valid values are n, u, ms, s, m, and h
	# note: using second precision greatly helps InfluxDB compression
	precision = "s"

	# run telegraf in debug mode
	debug = false

	# Override default hostname, if empty use os.Hostname()
	hostname = ""


###############################################################################
#                                  OUTPUTS                                    #
###############################################################################

[outputs]

# Configuration for the AMQP server to send metrics to
[outputs.amqp]
	# AMQP url
	url = "amqp://localhost:5672/influxdb"
	# AMQP exchange
	exchange = "telegraf"
	# Telegraf tag to use as a routing key
	#  ie, if this tag exists, it's value will be used as the routing key
	routing_tag = "host"

# Configuration for DataDog API to send metrics to.
[outputs.datadog]
	# Datadog API key
	apikey = "my-secret-key" # required.

	# Connection timeout.
	# timeout = "5s"

# Configuration for influxdb server to send metrics to
[outputs.influxdb]
	# The full HTTP endpoint URL for your InfluxDB instance
	# Multiple urls can be specified for InfluxDB cluster support. Server to
	# write to will be randomly chosen each interval.
	urls = ["http://localhost:8086"] # required.

	# The target database for metrics. This database must already exist
	database = "telegraf" # required.

	# Connection timeout (for the connection with InfluxDB), formatted as a string.
	# Valid time units are "ns", "us" (or "µs"), "ms", "s", "m", "h".
	# If not provided, will default to 0 (no timeout)
	# timeout = "5s"

	# username = "telegraf"
	# password = "metricsmetricsmetricsmetrics"

	# Set the user agent for the POSTs (can be useful for log differentiation)
	# user_agent = "telegraf"

# Configuration for the Kafka server to send metrics to
[outputs.kafka]
	# URLs of kafka brokers
	brokers = ["localhost:9092"]
	# Kafka topic for producer messages
	topic = "telegraf"
	# Telegraf tag to use as a routing key
	#  ie, if this tag exists, it's value will be used as the routing key
	routing_tag = "host"

# Configuration for MQTT server to send metrics to
[outputs.mqtt]
 	servers = ["localhost:1883"] # required.

        # MQTT outputs send metrics to this topic format
        #    "<topic_prefix>/host/<hostname>/<pluginname>/"
        #   ex: prefix/host/web01.example.com/mem/available
        # topic_prefix = "prefix"

        # username and password to connect MQTT server.
 	# username = "telegraf"
 	# password = "metricsmetricsmetricsmetrics"

# Configuration for OpenTSDB server to send metrics to
[outputs.opentsdb]
	# prefix for metrics keys
	prefix = "my.specific.prefix."

	## Telnet Mode ##
	# DNS name of the OpenTSDB server in telnet mode
	host = "opentsdb.example.com"

	# Port of the OpenTSDB server in telnet mode
	port = 4242

	# Debug true - Prints OpenTSDB communication
	debug = false


###############################################################################
#                                  PLUGINS                                    #
###############################################################################

[{{.Plugin}}]
{{if .Service}}servers = ["{{.Protocol}}{{.IP}}:{{.Port}}"]{{end}}
{{range .KV}}{{.}}
{{end}}`
