#!/usr/bin/env python

import optparse
import sys
import re
try:
    from influxdb import InfluxDBClient
except ImportError:
    print "python-influxdb is required for this script to work"
    raise


class InfluxDBQuery(object):

    """
    Query InfluxDB via commandline
    """
    POINTS_OUTER_ARRAY_INDEX = 0
    POINTS_INNER_ARRAY_FIRST_VALUE = 1
    JSON_RESPONSE_ARRAY_INDEX = 0
    EXIT_OK = 0
    EXIT_WARNING = 1
    EXIT_CRITICAL = 2

    def __init__(self, options):
        self.options = options

    def _createSeries(self):
        if self.options.query_custom:
            pass
        elif self.options.query_full:

            self.influx_hostname_series = self.options.query_full

        elif self.options.query_fqdn:
            fqdn = re.sub(
                r'\.', self.options.query_replace, self.options.query_fqdn)

            self.influx_hostname_series = "{prefix}.{fqdn}.{series}".format(
                fqdn=fqdn,
                series=self.options.query_series,
                prefix=self.options.query_prefix)

        else:
            self.influx_hostname_series = "{prefix}.\
            {hostname}{delimit}{domain}{series}".format(
                hostname=self.options.query_hostname,
                delimit=self.options.query_replace,
                domain=self.options.query_domain)

    # TODO option for column name
    # TODO option for seconds
    # Could make a dict of query type lookups and format it based on that
    # instead of long IF/ELIF/ELSE
    def _buildInfluxDBQuery(self):
        self.query_string = None

        if self.options.query_custom:
            self.query_string = self.options.query_custom

        elif self.options.query_count:
            self.query_string = "select COUNT(value) from " \
                                "{hostname_series} where" \
                                " time > now() - {seconds}s".format(
                                    hostname_series=self.influx_hostname_series,
                                    seconds=self.options.query_count)
        elif self.options.query_min:
            self.query_string = "select MIN(value) from" \
                                " {hostname_series} where" \
                                " time > now() - {seconds}s".format(
                                    hostname_series=self.influx_hostname_series,
                                    seconds=self.options.query_min)
        elif self.options.query_max:
            self.query_string = "select MAX(value) from " \
                                "{hostname_series} where" \
                                " time > now() - {seconds}s".format(
                                    hostname_series=self.influx_hostname_series,
                                    seconds=self.options.query_max)
        elif self.options.query_mean:
            self.query_string = "select MEAN(value) from" \
                                " {hostname_series} where" \
                                " time > now() - {seconds}s".format(
                                    hostname_series=self.influx_hostname_series,
                                    seconds=self.options.query_mean)
        elif self.options.query_mode:
            self.query_string = "select MODE(value) from" \
                                " {hostname_series} where" \
                                " time > now() - {seconds}s".format(
                                    hostname_series=self.influx_hostname_series,
                                    seconds=self.options.query_mode)
        elif self.options.query_median:
            self.query_string = "select MEDIAN(value) from" \
                                " {hostname_series} where" \
                                " time > now() - {seconds}s".format(
                                    hostname_series=self.influx_hostname_series,
                                    seconds=self.options.query_median)
        elif self.options.query_derivative:
            self.query_string = "select DERIVATIVE(value) from" \
                                " {hostname_series} where" \
                                " time > now() - {seconds}s".format(
                                    hostname_series=self.influx_hostname_series,
                                    seconds=self.options.query_derivative)
        elif self.options.query_sum:
            self.query_string = "select SUM(value) from" \
                                " {hostname_series} where" \
                                " time > now() - {seconds}s".format(
                                    hostname_series=self.influx_hostname_series,
                                    seconds=self.options.query_sum)
        elif self.options.query_stddev:
            self.query_string = "select STDDEV(value) from" \
                                " {hostname_series} where" \
                                " time > now() - {seconds}s".format(
                                    hostname_series=self.influx_hostname_series,
                                    seconds=self.options.query_stddev)
        elif self.options.query_first:
            self.query_string = "select FIRST(value) from" \
                                " {hostname_series} where" \
                                " time > now() - {seconds}s".format(
                                    hostname_series=self.influx_hostname_series,
                                    seconds=self.options.query_first)

    def _runQuery(self):
        # TODO try/except
        client = InfluxDBClient(self.options.influxdb_ip,
                                self.options.influxdb_port,
                                self.options.influxdb_user,
                                self.options.influxdb_pass,
                                self.options.influxdb_database,
                                timeout=self.options.query_timeout)

        try:
            self.query_result = client.query(
                self.query_string,
                time_precision=self.options.query_time_precision)
        except Exception:
            sys.stdout.write(
                "Error in InfluxDB query request, may be an invalid query: {query}".format(
                    query=self.query_string))
            sys.exit(InfluxDBQuery.EXIT_CRITICAL)

    def _returnInfluxDBQueryValuesList(self, json_dict):
        # influxdb response should have a length of two
        if json_dict:
            values = json_dict[
                InfluxDBQuery.JSON_RESPONSE_ARRAY_INDEX]["points"]
        else:
            sys.stdout.write(
                "No Values found, possibly diamond has not sent data yet to influxdb, InfluxDB Series: {series}".format(
                    series=self.influx_hostname_series))
            sys.exit(InfluxDBQuery.EXIT_WARNING)

        return values

    def _messageGenerator(self, threshold_value, current_value):

        message_template = "InfluxDB Series: {series}" " Query Performed: {query}".format(
            series=self.influx_hostname_series, query=self.query_string)

        message_values = " Current Value: {current}, Threshold Value:{threshold}".format(
            current=current_value,
            threshold=threshold_value)

        sys.stdout.write(message_template + message_values)

    def _compareQueryToThresholds(self):
        values = self._returnInfluxDBQueryValuesList(self.query_result)

        current_value = values[InfluxDBQuery.POINTS_OUTER_ARRAY_INDEX][
            InfluxDBQuery.POINTS_INNER_ARRAY_FIRST_VALUE]

        if not self.options.threshold_lessthan:

            if self.options.threshold_warning:

                if self.options.threshold_critical <= current_value:
                    self._messageGenerator(
                        self.options.threshold_critical,
                        current_value)
                    sys.exit(InfluxDBQuery.EXIT_CRITICAL)

                if self.options.threshold_warning < current_value and \
                        current_value <= self.options.threshold_critical:
                    self._messageGenerator(
                        self.options.threshold_warning,
                        current_value)
                    sys.exit(InfluxDBQuery.EXIT_WARNING)

                sys.exit(InfluxDBQuery.EXIT_OK)
            else:
                if self.options.threshold_critical <= current_value:
                    self._messageGenerator(
                        self.options.threshold_critical,
                        current_value)
                    sys.exit(InfluxDBQuery.EXIT_CRITICAL)

                sys.exit(InfluxDBQuery.EXIT_OK)
        else:

            if self.options.threshold_warning:
                if self.options.threshold_critical >= current_value:
                    self._messageGenerator(
                        self.options.threshold_critical,
                        current_value)
                    sys.exit(InfluxDBQuery.EXIT_CRITICAL)

                if self.options.threshold_warning > current_value \
                        and current_value >= self.options.threshold_critical:
                    self._messageGenerator(
                        self.options.threshold_warning,
                        current_value)
                    sys.exit(InfluxDBQuery.EXIT_WARNING)

                sys.exit(InfluxDBQuery.EXIT_OK)
            else:
                if self.options.threshold_critical >= current_value:
                    self._messageGenerator(
                        self.options.threshold_critical,
                        current_value)
                    sys.exit(InfluxDBQuery.EXIT_CRITICAL)

                sys.exit(InfluxDBQuery.EXIT_OK)

    def Run(self):
        self._createSeries()
        self._buildInfluxDBQuery()
        self._runQuery()
        self._compareQueryToThresholds()


def set_cli_parameters():
    parser = optparse.OptionParser()
    parser.add_option(
        "--influxdb-ip",
        action="store",
        type="string",
        dest="influxdb_ip",
        help="IP of the InfluxDB timeseries database",
        default="127.0.0.1")

    parser.add_option(
        "--influxdb-port",
        action="store",
        type="int",
        dest="influxdb_port",
        help="Port of the InfluxDB time series database",
        default=8083)

    parser.add_option(
        "--influxdb-user",
        action="store",
        type="string",
        dest="influxdb_user",
        help="Username that has access to the database specified",
        default="root")

    parser.add_option(
        "--influxdb-pass",
        action="store",
        type="string",
        dest="influxdb_pass",
        help="Password to the username that has access to the influxdb database",
        default="root")

    parser.add_option(
        "--influxdb-database",
        action="store",
        type="string",
        dest="influxdb_database",
        help="Database to query from InfluxDB",
        default="diamond")

    parser.add_option(
        "--query-full",
        action="store",
        type="string",
        dest="query_full",
        help="Full series name of the timeseries you want to check thresholds: \n \
    servers.name_domain.cpu.total.idle")

    parser.add_option(
        "--query-root-prefix",
        action="store",
        type="string",
        dest="query_prefix",
        help="ADD",
        default="servers")

    parser.add_option(
        "--query-custom",
        action="store",
        dest="query_custom",
        type="string",
        help="Use a custom query")

    parser.add_option(
        "--query-fqdn",
        action="store",
        type="string",
        dest="query_fqdn",
        help="Fully qualified domain name shown in InfluxDB of the time series to check thresholds: \n \
    name_domain")

    parser.add_option(
        "--query-hostname",
        action="store",
        type="string",
        dest="query_hostname",
        help="Hostname shown in InfluxDB of the time series to check thresholds: \n \
    name")

    parser.add_option(
        "--query-domain",
        action="store",
        type="string",
        dest="query_domain",
        help="Domain shown in InfluxDB of the time series to check\
        thresholds domain")

    parser.add_option(
        "--query-series",
        action="store",
        type="string",
        dest="query_series",
        help="Series name shown in InfluxDB, can check using web interface\
         'list series': cpu.total.idle")

    parser.add_option(
        "--query-count-seconds",
        action="store",
        dest="query_count",
        type="int",
        help="Compare threshold over the X seconds count")

    parser.add_option(
        "--query-min-seconds",
        action="store",
        dest="query_min",
        type="int",
        help="Compare threshold over the X seconds min")

    parser.add_option(
        "--query-max-seconds",
        action="store",
        dest="query_max",
        type="int",
        help="Compare threshold over the X seconds max")

    parser.add_option(
        "--query-mean-seconds",
        action="store",
        dest="query_mean",
        type="int",
        help="Compare threshold over the X seconds mean")

    parser.add_option(
        "--query-mode-seconds",
        action="store",
        dest="query_mode",
        type="int",
        help="Compare threshold over the X seconds average")

    parser.add_option(
        "--query-median-seconds",
        action="store",
        dest="query_median",
        type="int",
        help="Compare threshold over the X seconds mode")

    parser.add_option(
        "--query-derivative-seconds",
        action="store",
        dest="query_derivative",
        type="int",
        help="Compare threshold against the derivative")

    parser.add_option(
        "--query-sum-seconds",
        action="store",
        dest="query_sum",
        type="int",
        help="Compare threshold against the sum")

    parser.add_option(
        "--query-stddev-seconds",
        action="store",
        dest="query_stddev",
        type="int",
        help="Compare threshold against the standard deviation")

    parser.add_option(
        "--query-first-seconds",
        action="store",
        dest="query_first",
        type="int",
        help="Compare threshold against the first value in the query")

    parser.add_option(
        "--query-timeout",
        action="store",
        dest="query_timeout",
        type="float",
        help="Time till timeout exception is raised when querying influxdb, default is 3.0s",
        default=3.0)

    parser.add_option(
        "--query-replace-periods-with",
        action="store",
        dest="query_replace",
        help="Usually InfluxDB fqdn will not show up as hostname.domain"
             " but instead as hostname_domain, pick delimiter",
        default="_")

    parser.add_option(
        "--query-time-precision",
        action="store",
        dest="query_time_precision",
        help="InfluxDB timestamp is a microsecond epoch,"
             " default is milliseconds",
        default="ms")

    parser.add_option(
        "--threshold-less-than",
        action="store_true",
        dest="threshold_lessthan",
        help="Instead of looking for greater than critical or warning value,"
             " check when less than critical or warning",
        default=False)

    parser.add_option(
        "--threshold-warning",
        action="store",
        type="float",
        dest="threshold_warning",
        help="When equal to or exceeding this value but below the critical "
             "threshold exit with code 1")

    parser.add_option(
        "--threshold-critical",
        action="store",
        type="float",
        dest="threshold_critical",
        help="When equal to or exceeding this value exit with code 2")

    (options, args) = parser.parse_args()

    # check for required influxdb options

    if not all([options.influxdb_ip,
                options.influxdb_port,
                options.influxdb_user,
                options.influxdb_pass,
                options.influxdb_database]):
        parser.error("all influxdb options are required, or have a default")

    if options.query_full or options.query_custom:
        pass
    else:
        if all([options.query_fqdn, options.query_series]):
            pass
        else:
            if all([options.query_hostname,
                    options.query_domain,
                    options.query_series]):
                pass
            else:
                parser.error(
                    "query option required, eithre just --query-full, or"
                    " (--query-fqdn and --query-series), or "
                    "(--query-hostname,--query-domain,--query-series)")

    if not options.threshold_critical:
        parser.error("--threshold-critical is required")

    if not any([options.query_count,
                options.query_min,
                options.query_max,
                options.query_mean,
                options.query_mode,
                options.query_median,
                options.query_derivative,
                options.query_sum,
                options.query_stddev,
                options.query_first,
                options.query_custom]):

        parser.error("At least one --query options is required")

    return options, args


if __name__ == '__main__':
    options, args = set_cli_parameters()
    i = InfluxDBQuery(options)
    i.Run()
