#!/usr/bin/env python

import socket
import sys
import optparse


class SocketCheck(object):
    def __init__(self,options_object):
        self.option = options_object

    def _verifyRequirements(self):

        if not (self.option.socket_ip and self.option.socket_input and self.option.socket_output):
            sys.stdout.write("Require --ip , --command-input, --command-output")
            sys.exit(1)

        if self.option.socket_inet:
            if not self.option.socket_port:
                sys.stdout.write("When using inet need --port")
                sys.exit(1)


    def _buildSocketRequest(self):

        if self.option.socket_unix:
            sock = socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
            sock.connect(self.option.socket_ip)
            sock.settimeout(self.option.socket_timeout)
        else:
            sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            sock.connect((self.option.socket_ip,self.option.socket_port))
            sock.settimeout(self.option.socket_timeout)

            return sock

    def _evaluateOutput(self,data):
        if self.option.socket_output in data:
            sys.exit(0)
        else:
            sys.stdout.write("--command-output not found in returned data. Expected Output: {command_output}, received_output: {recv_output}".format(command_output=self.option.socket_output,
                                                                                                                                                    recv_output=data))
            sys.exit(2)


    def Run(self):
        self._verifyRequirements()

        try:
            sock = self._buildSocketRequest()
            sock.send("{command}\n".format(command=self.option.socket_input))
            sock_data_output = sock.recv(4096)
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()
            self._evaluateOutput(sock_data_output)

        except socket.error as err:
            sys.stdout.write("Socket Error: Error Number: {error_number}, Error String: {error_string}".format(error_number=err.errno,
                                                                                                               error_string=err.strerror))
            sys.exit(1)
        except socket.timeout:
            sys.stdout.write("Socket timeout, timeout: {timeout_value}".format(timeout_value=self.option.socket_timeout))
            sys.exit(1)





def set_cli_parameters():
    parser = optparse.OptionParser()
    parser.add_option("--ip", action="store", type="string",
                      dest="socket_ip", help="IP of socket")

    parser.add_option("--port", action="store", type="int", dest="socket_port",
                      help="Port of socket service")


    parser.add_option("--inet", action="store_true", dest="socket_inet",
                      help="Port of HTTP service if needed",default=True)


    parser.add_option("--unix", action="store_false", dest="socket_unix",
                      help="Port of HTTP service if needed",default=False)


    parser.add_option("--command-input", action="store", type="string", dest="socket_input",
                      help="Endpoint to check")


    parser.add_option("--command-output", action="store", type="string", dest="socket_output",
                      help="Endpoint to check")


    parser.add_option("--timeout", action="store", type="float", dest="socket_timeout",
                      help="Timeout wait period till reporting critical error",default=3.0)

    (options, args) = parser.parse_args()
    return options, args


if __name__ == "__main__":
    options, args = set_cli_parameters()
    s = SocketCheck(options)
    s.Run()
