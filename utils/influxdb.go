package main

import (
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io/ioutil"
	"math/rand"
	"net/http"
	"net/url"
	"os"
)

const usageText = `Usage: influxdb08 [options]
Options:
  -ip=""            IP of InfluxDB service, Required
  -port=            Port of InfluxDB service, default is 8086
  -database=""      Database to Query, Required
  -user=""          Username that has access to the database specified, default root
  -password=""      Password to the username that has access to the InfluxDB database, default root
  -series=""        Full series name of the timeseries you want to check thresholds, Either Series or Custom Required
  -custom=""        Custom Influx Query of the series you want to check thresholds, Either Series or Custom Required
  -delta=           Now() - delta, default 60s
  -count            Compare threshold to count
  -min              Compare threshold to min
  -max              Compare threshold to max
  -mean             Compare threshold to mean
  -mode             Compare threshold to mode
  -median           Compare threshold to median
  -derivative       Compare threshold to derivative
  -sum              Compare threshold to sum
  -stddev           Compare threshold to standard deviation
  -first            Compare threshold to first
  -lessthan         Warning and Critical values will notify if less than
  -warning=         Exits with code 1 if exceeded, Optional
  -critical=        Exits with code 2 if exceeded, Required
Examples:
	influxdb08 -ip="0.0.0.0" -series="servers.consulalerting.cpu.total.idle" -mean -delta=500 -database="db" -critical=200
`

//Used for Points First Array
const TIME int = 0

//Used for Points Second Array
const VALUE int = 1

//InfluxResponse,Influxdb0.8 HTTP GET representation of JSON
type InfluxResponse struct {
	Columns []string    `json:"columns"`
	Name    string      `json:"name"`
	Points  [][]float64 `json:"points"`
}

func main() {
	os.Exit(influxdbmain())
}

func influxdbmain() int {

	var (
		IP         string
		Port       int
		DB         string
		User       string
		Password   string
		Series     string
		Custom     string
		Count      bool
		Min        bool
		Max        bool
		Mean       bool
		Mode       bool
		Median     bool
		Derivative bool
		Sum        bool
		Stddev     bool
		First      bool
		Delta      int
		LessThan   bool
		Warning    float64
		Critical   float64
	)

	randomFloat := rand.Float64()

	influxFlags := flag.NewFlagSet("influxdb", flag.ExitOnError)
	influxFlags.Usage = func() { printUsage() }

	//
	influxFlags.StringVar(&IP, "ip", "", "IP of the InfluxDB service")
	influxFlags.IntVar(&Port, "port", 8086, "Port of the InfluxDB service")
	influxFlags.StringVar(&DB, "database", "", "Database to query from InfluxDB service")
	influxFlags.StringVar(&User, "user", "root", "Username that has access to the database specified")
	influxFlags.StringVar(&Password, "password", "root", "Password to the username that has access to the InfluxDB database")
	influxFlags.StringVar(&Series, "series", "", "Full series name of the timeseries you want to check thresholds")
	influxFlags.StringVar(&Custom, "custom", "", "Custom Influx Query of the series you want to check thresholds")

	//
	influxFlags.IntVar(&Delta, "delta", 60, "Now() - delta")

	//
	influxFlags.BoolVar(&Count, "count", false, "Compare threshold to count")
	influxFlags.BoolVar(&Min, "min", false, "Compare threshold to min")
	influxFlags.BoolVar(&Max, "max", false, "Compare threshold to max")
	influxFlags.BoolVar(&Mean, "mean", false, "Compare threshold to mean")
	influxFlags.BoolVar(&Mode, "mode", false, "Compare threshold to mode")
	influxFlags.BoolVar(&Median, "median", false, "Compare threshold to median")
	influxFlags.BoolVar(&Derivative, "derivative", false, "Compare threshold to derivative")
	influxFlags.BoolVar(&Sum, "sum", false, "Compare threshold to sum")
	influxFlags.BoolVar(&Stddev, "stddev", false, "Compare threshold to standard deviation")
	influxFlags.BoolVar(&First, "first", false, "Compare threshold to first")

	//
	influxFlags.BoolVar(&LessThan, "lessthan", false, "Warning and Critical values will notify if less than")
	influxFlags.Float64Var(&Warning, "warning", randomFloat, "Exits with code 1")
	influxFlags.Float64Var(&Critical, "critical", randomFloat, "Exits with code 2")

	if err := influxFlags.Parse(os.Args[1:]); err != nil {
		influxFlags.Usage()
		return 1
	}

	queryString, err := createQuery(Series, Custom, Delta, Count, Min, Max, Mean, Mode, Derivative, Sum, Stddev, First)
	if err != nil {
		return 1
	}

	result, err := queryDB(IP, Port, DB, User, Password, queryString)
	if err != nil {
		return 1
	}

	exitCode := thresholdChecker(result, LessThan, Warning, Critical, randomFloat)
	return exitCode
}

func messageGenerator(thresholdType string, thresholdValue, curerntValue float64, series string) {
	fmt.Fprintf(os.Stdout, "Threshold Event:%s ThresholdValue:%f CurrentValue:%f Series:%s\n", thresholdType, thresholdValue, curerntValue, series)
}

func exceeded(thresholdValue, currentValue float64, lessthan bool) bool {
	switch lessthan {
	case true:
		if thresholdValue <= currentValue {
			return false
		}
		return true
	case false:
		if thresholdValue >= currentValue {
			return false
		}
		return true
	default:
		return false
	}

}

func thresholdChecker(ir []InfluxResponse, lessthan bool, warningValue, criticalValue, random float64) int {
	currentValue := ir[0].Points[TIME][VALUE]

	if warningValue == random && criticalValue == random {
		fmt.Fprintln(os.Stderr, "Critical threshold must be specified")
		return 1
	}

	if exceeded(criticalValue, currentValue, lessthan) {
		//ALERT CRITICAL
		messageGenerator("CRITICAL", criticalValue, currentValue, ir[0].Name)
		return 2
	} else if warningValue != random && exceeded(criticalValue, currentValue, lessthan) == false && exceeded(warningValue, currentValue, lessthan) == true {
		//ALERT WARNING
		messageGenerator("WARNING", warningValue, currentValue, ir[0].Name)
		return 1
	} else {
		messageGenerator("PASSING", warningValue, currentValue, ir[0].Name)
		return 0
	}

}

func queryBuilder(functionName string, series string, delta int) string {
	return fmt.Sprintf("select %s(value) from \"%s\" where time > now() - %ds", functionName, series, delta)
}

func createQuery(series, custom string, delta int, count, min, max, mean, mode, derivative, sum, stddev, first bool) (string, error) {
	if len(custom) > 0 {
		return custom, nil
	} else if len(series) > 0 {

		if count {
			return queryBuilder("COUNT", series, delta), nil
		} else if min {
			return queryBuilder("MIN", series, delta), nil
		} else if max {
			return queryBuilder("MAX", series, delta), nil
		} else if mean {
			return queryBuilder("MEAN", series, delta), nil
		} else if mode {
			return queryBuilder("MODE", series, delta), nil
		} else if derivative {
			return queryBuilder("DERIVATIVE", series, delta), nil
		} else if sum {
			return queryBuilder("SUM", series, delta), nil
		} else if stddev {
			return queryBuilder("STDDEV", series, delta), nil
		} else if first {
			return queryBuilder("FIRST", series, delta), nil
		}

		fmt.Fprintln(os.Stderr, "If using Series function type required")
		return "", errors.New("If using Series function type required")

	} else {
		fmt.Fprintln(os.Stderr, "Series or Custom not given, required")
		return "", errors.New("Series or Custom not given, required")
	}
}

// queryDB convenience function to query the database
func queryDB(ip string, port int, db string, username, password, query string) ([]InfluxResponse, error) {

	encodedQuery := url.QueryEscape(query)
	response, err := http.Get(fmt.Sprintf("http://%s:%d/db/%s/series?u=%s&p=%s&q=%s", ip, port, db, username, password, encodedQuery))
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		return nil, err
	}

	result, err := ioutil.ReadAll(response.Body)
	defer response.Body.Close()
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		return nil, err
	}

	ir := []InfluxResponse{}
	json.Unmarshal(result, &ir)

	return ir, nil

}

func printUsage() {
	fmt.Fprintln(os.Stderr, usageText)
}
