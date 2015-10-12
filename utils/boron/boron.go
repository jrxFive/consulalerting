package main

import (
	"bufio"
	"errors"
	"flag"
	"fmt"
	"io/ioutil"
	"math"
	"math/rand"
	"os"
	"os/exec"
	"regexp"
	"strconv"
	"strings"
	"text/template"
)

const usageText = `Usage: boron [options]
Options:
  -ip=""                   IP of service, default localhost
  -port=                   Port of Service, default 8000
  -protocol                Protocol of Service, default empty ie tcp:// or http://
  -service                 To enable Service parameters in template generation, default false
  -series                  Single Telegraphite timeseries to check against
  -plugin                  Telegraphite Plugin name
  -plugin-parameters       Parameters for Telegraphite Plugin, separator '|'
  -telegraphite-location   Absolute path of telegraphite binary
  -working-location        Working location to generate temporary plugin files
  -lessthan                Warning and Critical values will notify if less than
  -warning=                Exits with code 1 if exceeded, Optional
  -critical=               Exits with code 2 if exceeded, Required
Examples:
	./boron -plugin cpu --working-location . -telegraphite-location ./telegraphite -plugin-parameters 'percpu = true|totalcpu = true|drop = ["cpu_time"]' -series 'some.example.com.cpu.cpu1.cpu_usage_idle' -critical 0
	./boron -warning=20971520 -critical=104857600 -series 'some.example.com.host.10.0.0.1.port.6379.redis_used_memory' -plugin redis -telegraphite-location './telegraphite' -service -ip "0.0.0.0" -port 6379 -protocol "tcp://" -plugin-parameters "key = value|key2 = value2"
`

func main() {
	os.Exit(boronMain())
}

func boronMain() int {

	var (
		IP                   string
		Port                 int
		Protocol             string
		Service              bool
		Series               string
		Plugin               string
		PluginParameters     string
		TelegraphiteLocation string
		WorkingLocation      string
		LessThan             bool
		Warning              float64
		Critical             float64
	)

	randomFloat := rand.Float64()

	boronFlags := flag.NewFlagSet("boron", flag.ExitOnError)
	boronFlags.Usage = func() { printUsage() }

	//
	boronFlags.StringVar(&IP, "ip", "localhost", "IP of Service")
	boronFlags.IntVar(&Port, "port", 8000, "Port of Service")
	boronFlags.StringVar(&Protocol, "protocol", "", "Protocol of Service i.e http:// or tcp://")
	boronFlags.BoolVar(&Service, "service", false, "Query a Service which requires an array of Protocol,IP,Port")

	//
	boronFlags.StringVar(&Series, "series", "", "Single Telegraphite timeseries to check against")
	boronFlags.StringVar(&Plugin, "plugin", "", "Telegraphite Plugin name")
	boronFlags.StringVar(&PluginParameters, "plugin-parameters", "", "Parameters for Telegraphite Plugin")
	boronFlags.StringVar(&TelegraphiteLocation, "telegraphite-location", "/usr/bin/telegraphite", "Absolute path of telegraphite binary")
	boronFlags.StringVar(&WorkingLocation, "working-location", "/tmp/", "Working location to generate temporary plugin files")

	boronFlags.BoolVar(&LessThan, "lessthan", false, "Warning and Critical values will notify if less than")
	boronFlags.Float64Var(&Warning, "warning", randomFloat, "Exits with code 1")
	boronFlags.Float64Var(&Critical, "critical", randomFloat, "Exits with code 2")

	if err := boronFlags.Parse(os.Args[1:]); err != nil {
		boronFlags.Usage()
		return 1
	}

	temporaryConfig, err := writeTemplate(Plugin, PluginParameters, IP, Port, Service, Protocol, WorkingLocation, TeleGraphiteTemplate)
	if err != nil {
		return 2
	}

	defer os.Remove(temporaryConfig)

	seriesResult, err := executeTeleGraphite(TelegraphiteLocation, temporaryConfig, Plugin, Series)
	if err != nil || seriesResult == math.MaxFloat64 {
		fmt.Fprintf(os.Stderr, "Error could not find series: %s for specified plugin: %s\n", Series, Plugin)
		return 1
	}

	exitCode := thresholdChecker(seriesResult, Series, LessThan, Warning, Critical, randomFloat)
	return exitCode
}

//Splits Plugin parameters
func splitParameters(PluginParameters string) []string {
	return strings.Split(PluginParameters, "|")
}

//Generates template  file for given plugin
func writeTemplate(Plugin string, PluginParameters string, IP string, Port int, Service bool, Protocol string, WorkingLocation, Template string) (string, error) {

	t, err := template.New("plugin").Parse(Template)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		return "", err
	}

	temporaryFileLocation := fmt.Sprintf("%s%s.conf", WorkingLocation, Plugin)
	fh, err := os.Create(temporaryFileLocation)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		return "", err
	}
	defer fh.Close()

	wr := bufio.NewWriter(fh)
	defer wr.Flush()

	tp := TelegraphitePlugin{
		Plugin:   Plugin,
		KV:       splitParameters(PluginParameters),
		IP:       IP,
		Port:     Port,
		Protocol: Protocol,
		Service:  Service,
	}

	err = t.Execute(wr, tp)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		return "", err
	}

	return temporaryFileLocation, nil
}

//Executes Telegraphite in STDOUT mode with the generated config file.
//Parses STDOUT and abstracts value
func executeTeleGraphite(TelegraphiteLocation, Config, Plugin, Series string) (float64, error) {
	cmd := exec.Command(TelegraphiteLocation, "-config", Config, "-filter", Plugin, "-test", "|", "grep", Series)
	stdout, err := cmd.StdoutPipe()
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		return math.MaxFloat64, err
	}

	if err := cmd.Start(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		return math.MaxFloat64, err
	}

	r, err := ioutil.ReadAll(stdout)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		return math.MaxFloat64, err
	}

	re := regexp.MustCompile(fmt.Sprintf(`%s (\d*\.?\d+)`, Series))
	regexResult := re.FindAllString(string(r), -1)

	if len(regexResult) >= 1 {
		delimit := strings.Split(regexResult[0], " ")
		f, err := strconv.ParseFloat(delimit[1], 64)
		if err != nil {
			fmt.Fprintln(os.Stderr, errors.New(fmt.Sprintf("Series: %s not found", Series)))
			return math.MaxFloat64, errors.New(fmt.Sprintf("Series: %s not found", Series))
		}
		return f, nil
	} else {
		return math.MaxFloat64, errors.New(fmt.Sprintf("Series: %s not found", Series))
	}

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

func thresholdChecker(currentValue float64, series string, lessthan bool, warningValue, criticalValue, random float64) int {
	if warningValue == random && criticalValue == random {
		fmt.Fprintln(os.Stderr, "Critical threshold must be specified")
		return 1
	}

	if exceeded(criticalValue, currentValue, lessthan) {
		//ALERT CRITICAL
		messageGenerator("CRITICAL", criticalValue, currentValue, series)
		return 2
	} else if warningValue != random && exceeded(criticalValue, currentValue, lessthan) == false && exceeded(warningValue, currentValue, lessthan) == true {
		//ALERT WARNING
		messageGenerator("WARNING", warningValue, currentValue, series)
		return 1
	} else {
		messageGenerator("PASSING", warningValue, currentValue, series)
		return 0
	}

}

func printUsage() {
	fmt.Fprintln(os.Stderr, usageText)
}
