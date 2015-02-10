#!/usr/bin/env python
__author__ = 'jxfiveMBP-W7'

import requests
import sys
import optparse


class HttpCheck(object):
    def __init__(self,options_object):
        self.option = options_object

    def _verifyRequirements(self):

        if not (self.option.http_ip or self.option.http_address) or (self.option.http_ip and self.option.http_address):
            sys.stdout.write("Require either --ip or --address values")
            sys.exit(1)


    def _buildRequest(self):

        if self.option.http_ip:
            request = "http://{ip}".format(ip=self.option.http_ip)

        elif self.option.http_address:
            request = "http://{address}".format(address=self.option.http_address)

        if self.option.http_port:
            request = "".join([request,":{port}".format(port=self.option.http_port)])

        if self.option.http_endpoint:
            request = "".join([request,"{endpoint}".format(endpoint=self.option.http_endpoint)])

        return request

    def Run(self):
        self._verifyRequirements()
        request = self._buildRequest()

        try:
            request_exception_string = "Request String: {request}".format(request=request)
            response = requests.get(request,timeout=self.option.http_timeout)

            if response.status_code != 200:
                sys.stdout.write("{request} returned status code: {status}, timeout set to {timeout}".format(request=request,
                                                                                                             status=response.status_code,
                                                                                                             timeout=self.option.http_timeout))
                sys.exit(2)
            else:
                sys.exit(0)

        except requests.exceptions.ConnectionError:
            sys.stdout.write("A Connection error occurred. {request_info}\n".format(request_info=request_exception_string))
            sys.exit(1)
        except requests.exceptions.HTTPError:
            sys.stdout.write("An HTTP error occurred. {request_info}\n".format(request_info=request_exception_string))
            sys.exit(1)
        except requests.exceptions.URLRequired:
            sys.stdout.write("A valid URL is required to make a request. {request_info}\n".format(request_info=request_exception_string))
            sys.exit(1)
        except requests.exceptions.TooManyRedirects:
            sys.stdout.write("A Connection error occurred. {request_info}\n".format(request_info=request_exception_string))
            sys.exit(1)
        except requests.exceptions.ConnectTimeout:
            sys.stdout.write("The request timed out while trying to connect to the remote server. {request_info}\n".format(request_info=request_exception_string))
            sys.exit(1)
        except requests.exceptions.ReadTimeout:
            sys.stdout.write("The server did not send any data in the allotted amount of time. {request_info}\n".format(request_info=request_exception_string))
            sys.exit(1)
        except requests.exceptions.ReadTimeout:
            sys.stdout.write("The server did not send any data in the allotted amount of time. {request_info}\n".format(request_info=request_exception_string))
            sys.exit(1)




def set_cli_parameters():
    parser = optparse.OptionParser()
    parser.add_option("--ip", action="store", type="string",
                      dest="http_ip", help="IP of HTTP service")

    parser.add_option("--port", action="store", type="int", dest="http_port",
                      help="Port of HTTP service if needed")


    parser.add_option("--address", action="store", type="string",
                      dest="http_address", help="Address of HTTP service")


    parser.add_option("--endpoint", action="store", type="string", dest="http_endpoint",
                      help="Endpoint to check")


    parser.add_option("--timeout", action="store", type="float", dest="http_timeout",
                      help="Timeout wait period till reporting critical error",default=3.0)

    (options, args) = parser.parse_args()
    return options, args


if __name__ == "__main__":
    options, args = set_cli_parameters()
    h = HttpCheck(options)
    h.Run()