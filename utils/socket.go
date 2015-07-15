package main

import (
	"flag"
	"fmt"
	"net"
	"os"
	"strings"
	"time"
)

func main() {
	os.Exit(socketmain())
}

const usageText = `Usage: socket [options]

Options:

  -ip=""            IP of service
  -port=  			Port of IP service, default is 80
  -address=""       Full address of service and port
  -timeout=""       Time duration till connection attempt will be closed
  -input=""         Command to send to socket service, newline appended automatically
  -output=""        Exact expected output from input command


Examples:
	socket -ip 10.0.2.15 -port 8000 -input PING -outpt '+PONG'
	socket --address 10.0.2.15:8000 -input PING -outpt '+PONG'
`

func socketmain() int {

	const socketNetwork string = "tcp"

	var socketIP string
	var socketPort int
	var socketAddress string
	var socketTimeout int
	var socketInput string
	var socketOutput string

	socketFlags := flag.NewFlagSet("socket", flag.ExitOnError)
	socketFlags.Usage = func() { printUsage() } //used when Parse error occurs
	socketFlags.StringVar(&socketIP, "ip", "", "IP of service")
	socketFlags.IntVar(&socketPort, "port", 80, "Specified port of service, default is 80")
	socketFlags.StringVar(&socketAddress, "address", "", "Full Address and port of socket service")
	socketFlags.IntVar(&socketTimeout, "timeout", 3, "Duration to wait till timing out on a request in seconds")
	socketFlags.StringVar(&socketInput, "input", "", "Command to input")
	socketFlags.StringVar(&socketOutput, "output", "", "Expected output based on input")

	if err := socketFlags.Parse(os.Args[1:]); err != nil {
		socketFlags.Usage()
		return 1
	}

	if len(socketInput) == 0 || len(socketOutput) == 0 {
		fmt.Fprintf(os.Stderr, "input and output must be declared\n")
		return 1
	}

	var addr string

	if len(socketIP) > 0 {
		addr = fmt.Sprintf("%s:%d", socketIP, socketPort)
	} else if len(socketAddress) > 0 {
		addr = fmt.Sprintf("%s", socketAddress)
	} else {
		fmt.Fprintf(os.Stderr, "Either use IP flag or Address, if both IP will be used\n")
		printUsage()
		return 1
	}

	r := make([]byte, 1024)
	tDuration := time.Now().Add(time.Duration(socketTimeout) * time.Second)
	raddr, err := net.ResolveTCPAddr(socketNetwork, addr)
	checkPrintError(err)

	conn, err := net.DialTCP(socketNetwork, nil, raddr)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error occured connecting or possible timeout Addr:%s\n", addr)
		fmt.Fprintln(os.Stderr, err)
		return 2
	}
	defer conn.Close()

	err = conn.SetReadDeadline(tDuration)
	checkPrintError(err)

	fmt.Fprintf(conn, "%s\n", socketInput)
	checkPrintError(err)

	for {
		_, err = conn.Read(r)
		checkPrintError(err)

		if strings.Contains(string(r), string(socketOutput)) {
			fmt.Fprintf(os.Stdout, "Returned output: %s, Expected output:%s\n", string(r), socketOutput)
			return 0
		}
		fmt.Fprintf(os.Stdout, "Returned output: %s, Expected output:%s\n", string(r), socketOutput)
		return 2
	}

}

func checkPrintError(err error) {
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
}

func printUsage() {
	fmt.Fprintf(os.Stderr, usageText)
	os.Exit(1)
}
