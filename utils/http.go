package main

import (
	"flag"
	"fmt"
	"net/http"
	"os"
	"time"
)

func main() {
	os.Exit(httpmain())
}

const usageText = `Usage: http [options]

Options:

  -ip=""            IP of service
  -port=  			Port of IP service, default is 80
  -endpoint=""      Endpoint of service if not just the domain
  -address=""       Full 'www' address, port, and endpoint
  -timeout=""       Time duration till connection attempt will be closed


Examples:
	http -ip 10.0.2.15 -port 8000 -endpoint /admin
	http --ip=10.0.2.15 --port=8000 
	http -address=www.google.com
	http --address=www.yahoo.com
`

func httpmain() int {

	var httpIP string
	var httpPort int
	var httpAddress string
	var httpEndpoint string
	var httpTimeout int

	httpFlags := flag.NewFlagSet("http", flag.ExitOnError)
	httpFlags.Usage = func() { printUsage() } //used when Parse error occurs
	httpFlags.StringVar(&httpIP, "ip", "", "IP of service")
	httpFlags.StringVar(&httpAddress, "address", "", "Address of services")
	httpFlags.StringVar(&httpEndpoint, "endpoint", "", "When using IP and want to reach a particular endoint")
	httpFlags.IntVar(&httpPort, "port", 80, "Specified port of service, default is 80")
	httpFlags.IntVar(&httpTimeout, "timeout", 3, "Duration to wait till timing out on a request in seconds")

	if err := httpFlags.Parse(os.Args[1:]); err != nil {
		httpFlags.Usage()
		return 1
	}

	c := http.Client{
		Timeout: time.Duration(httpTimeout) * time.Second,
	}

	var addr string

	if len(httpIP) > 0 {
		addr = fmt.Sprintf("http://%s:%d%s", httpIP, httpPort, httpEndpoint)
	} else if len(httpAddress) > 0 {
		addr = fmt.Sprintf("http://%s", httpAddress)
	} else {
		fmt.Println("Either IP or Address required")
		httpFlags.Usage()
		return 1
	}

	resp, err := c.Get(addr)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error occured when attempt GET on: %s\n", addr)
		return 1
	}

	if resp.StatusCode != 200 {
		fmt.Fprintf(os.Stdout, "Address: %s, Response: %s", addr, resp.Status)
		return 2
	}

	fmt.Fprintf(os.Stdout, "Address: %s, Response: %s", addr, resp.Status)
	return 0

}

func printUsage() {
	fmt.Fprintf(os.Stderr, usageText)
}
