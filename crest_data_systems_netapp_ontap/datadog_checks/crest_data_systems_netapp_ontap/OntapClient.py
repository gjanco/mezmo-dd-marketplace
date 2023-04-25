# Core Python Imports
import json
import re
import xml.etree.ElementTree as ET

import six

# Netapp OnTap Api Imports
from .NetApp import NaErrno
from .NetApp.NaElement import NaElement
from .NetApp.NaServer import NaServer
from .OntapFormatters import naElementToDict

ERROR_HEADER = "[OntapClient] "


class BaseOntapClientException(Exception):
    """
    Base Class for raising ontap client exceptions
    """

    ERROR_TYPE = "BASE ONTAP CLIENT EXCEPTION"

    def __init__(self, errno, reason, more=""):
        self.errno = errno
        self.reason = reason
        if isinstance(more, str) and more != "":
            self.more = ", " + more
        else:
            self.more = more

    def __str__(self):
        return ERROR_HEADER + self.ERROR_TYPE + " {0}: {1}{2}".format(self.errno, self.reason, self.more)

    def __unicode__(self):
        return six.text_type(self.__str__())


class AuthenticationError(BaseOntapClientException):
    """
    Authentication Errors are when we don't authenticate properly
    """

    ERROR_TYPE = "Authentication Error"

    def __init__(self, errno=NaErrno.EAPIAUTHENTICATION, reason="Authentication Refused", more=""):
        super(AuthenticationError, self).__init__(errno, reason, more)


class LicensingError(BaseOntapClientException):
    """
    Licensing Errors occur when we call an API corresponding to licensed functionality
    which we do not have enabled.
    """

    ERROR_TYPE = "Licensing Error"

    def __init__(self, errno=NaErrno.EAPILICENSE, reason="License invalid", more=""):
        super(LicensingError, self).__init__(errno, reason, more)


class SSLError(BaseOntapClientException):
    """
    SSL Errors occur when SSL certificate verification fails when calling an API.
    """

    ERROR_TYPE = "SSL Error"

    def __init__(self, errno=NaErrno.EAPIERROR, reason="SSL Verification Failed", more=""):
        super(SSLError, self).__init__(errno, reason, more)


class ConnectionError(BaseOntapClientException):
    """
    Connection Errors are really socket.error number 61, Connection Refused
    """

    ERROR_TYPE = "Connection Error"

    def __init__(self, errno=NaErrno.EAPIERROR, reason="[Errno 61] Connection refused", more=""):
        super(ConnectionError, self).__init__(errno, reason, more)


class ClientSideError(BaseOntapClientException):
    """
    Client Side errors indicate a problem with the ontap client or the environment
    """

    ERROR_TYPE = "Client Side Code Error"

    def __init__(self, errno=NaErrno.EAPIERROR, reason="Problem with client side code", more=""):
        super(ClientSideError, self).__init__(errno, reason, more)


class QueryError(BaseOntapClientException):
    """
    Query Errors get returned when a query returns an error code
    These may not be critical, but will influence the results returned
    for compound queries
    """

    ERROR_TYPE = "Query Error"

    def __init__(self, errno, reason, more=""):
        super(QueryError, self).__init__(errno, reason, more)


class ArgumentError(Exception):
    """
    An internal error class meant to notify the developers
    """

    def __init__(self, argument, message):
        self.argument = argument
        self.message = message

    def __str__(self):
        return ERROR_HEADER + "Argument Error {0}: {1}".format(self.argument, self.message)

    def __unicode__(self):
        return six.text_type(self.__str__())


class BadQueryError(Exception):
    """
    Another internal error class meant to notify the developers
    This time when they have json that is illegal
    """

    def __init__(self, arguments):
        self.arguments = arguments.__str__()

    def __str__(self):
        return ERROR_HEADER + "Bad Query Error {0}".format(self.arguments)

    def __unicode__(self):
        return six.text_type(self.__str__())


class OntapElementEncoder(json.JSONEncoder):
    """Overrides the default processing to deal with our NaElement objects"""

    def default(self, obj):
        if isinstance(obj, NaElement):
            rethash = {}
            if len(obj.element["children"]) == 0:
                rethash[obj.element["name"]] = obj.element["content"]
            else:
                rethash[obj.element["name"]] = obj.element["children"]
            return rethash
        return json.JSONEncoder.default(self, obj)


class OntapClient(object):
    """
    The OntapClient acts as an interface class for the ontap api, encapsulating
    commonly used methods and (hopefully) making them easier to use.  No
    connections are established until the request is made, so the more api calls
    piggyback on a single connection, so that's pretty good.

    The main method of interest is queryApi and formatResults
    """

    # Version Constants
    MIN_MAJOR = 1
    MIN_MINOR = 13

    # Default iterator API request size limit
    ITER_API_MAX_RECORDS = 30

    CONNECTION_TIMEOUT = 30

    def __init__(
        self,
        server,
        username,
        password,
        log,
        port=443,
        transport="HTTPS",
        realm=None,
        debug_server=None,
    ):
        self.port = port
        self.server = server
        self.realm = realm if realm is not None else server
        self.transport = transport
        self.clustered = None
        self.major = self.MIN_MAJOR
        self.minor = self.MIN_MINOR
        self.supportedApis = None
        # Specifically used for performance metrics
        self.perfCounters = {}

        self.username = username
        self.password = password
        self.log = log

        # Set up the netapp connection
        if debug_server is None:
            na = NaServer(self.server, self.major, self.minor)
            na.set_transport_type(self.transport)
            na.set_port(self.port)
            na.set_timeout(self.CONNECTION_TIMEOUT)
            na.set_style("LOGIN")
            na.set_admin_user(self.username, self.password)
            self.connection = na
            self.log.info("NETAPP ONTAP INFO: Server {server} initialized".format(server=self.server))  # noqa: G001
        else:
            self.connection = debug_server

    @staticmethod
    def projectResponse(response):
        """
        Returns exactly what is passed.
        """
        return response

    @staticmethod
    def convertElementToJSON(response):
        """
        Takes a set of NAElements and converts it to json
        """
        return OntapElementEncoder().encode(response)

    @staticmethod
    def convertElementToDict(response):
        """
        Takes a set of NAElements and converts it to a python dict
        """
        return json.loads(OntapClient.convertElementToJSON(response))

    @staticmethod
    def convertElementToXML(response):
        """
        Takes a set of NAElements and converts it to xml using the provided sprintf
        """
        return response.sprintf()

    @staticmethod
    def convertElementToElementTree(response):
        """
        Takes a set of NAElements and converts it into the ElementTree representation
        """
        return ET.fromstring(response.sprintf())

    @staticmethod
    def counterListInfoResults(results):
        """
        Used to grab the results when 'perf-object-list-info' is called on an object
        Outputs a hash of the available counter information and rates and stuff
        """
        counterMap = {}
        if len(results.element["children"]) == 0:
            return counterMap
        # Seems fragile, make better
        for brat in results.element["children"][0].element["children"]:
            if brat.element["name"] == "counter-info":
                counterInfo = brat.element["children"]
                singleCounter = {}
                name = None
                for counterData in counterInfo:
                    if counterData.element["name"] == "name":
                        name = counterData.element["content"]
                    elif counterData.element["name"] == "labels":
                        singleCounter[counterData.element["name"]] = counterData.element["children"][0].element[
                            "content"
                        ]
                    else:
                        singleCounter[counterData.element["name"]] = counterData.element["content"]
                counterMap[name] = singleCounter
        return counterMap

    def checkConnection(self):
        timeout = 5
        try:
            self.connection.set_timeout(timeout)
            self.getApiVersion(cached=False)
        except Exception as e:
            return False, e
        else:
            return True, None
        finally:
            self.connection.set_timeout(self.CONNECTION_TIMEOUT)

    def getApiVersion(self, cached=True):
        """
        Requests the api version from the agent and stores them in the
        major and minor locally
        """
        if not cached or self.major is None or self.minor is None:
            results = self.queryApi("system-get-ontapi-version", OntapClient.convertElementToXML, False)
            root = ET.fromstring(results)
            self.major = int(root.find("major-version").text)
            self.minor = int(root.find("minor-version").text)
        return self.major, self.minor

    def isClustered(self, cached=True):
        """
        Requests information to see whether or not we are dealing
        with a clustered environment.  Caches this information for future use.
        """
        # TODO: Exception handling
        if not cached or self.clustered is None:
            results = self.queryApi("system-get-version", OntapClient.convertElementToXML, False)
            root = ET.fromstring(results)
            clustered = root.find("is-clustered")
            if clustered is not None and clustered.text == "true":
                self.clustered = True
            else:
                self.clustered = False
        return self.clustered

    def getSupportedApis(self, cached=True):
        """
        Requests the list of apis supported by the system.
        We can use this list to check and see if the api we have is supported
        or if this is an older version that we need to support
        """
        # TODO: We can also grab the arguments for the supported apis
        # by calling 'system-api-get-elements'
        if not cached or self.supportedApis is None:
            results = self.queryApi("system-api-list", OntapClient.convertElementToXML, False)
            root = ET.fromstring(results)
            self.supportedApis = [name.text for name in root.findall(".//name")]
        return self.supportedApis

    def getSupportedPerformanceCounters(self, objectName, cached=True):
        """
        Requests a list of performance counters
        supported by the filer.  These are stored
        here and not with the perf object because these are static and only
        need to be queried once per session

        These are a list of statically defined counters for the different objects.  They define
        the names of the counter, the description, the privilege level (described below)
        the properties of the data (described below) and the units for the data

        This really only needs to be queried once per session (if at all,
        beyond an initial configuration). The documentation says they never change,
        so that's cool.

        PROPERTIES (From page 16 of the Performance Management Design Guide:
        Raw - no math
        Rate - two samples need to be calculated and computed as (c2-c1)/(t2-t1)
        Delta - two samples, compute as (t2-t1)
        Average - two samples of the counter (c) and two samples of a
                base counter (b) compute as (c2-c1)/(b2-b1)
        Percent - two samples of the counter(c) and two samples of a
                base counter (b) compute as 100*(c2-c1)/(b2-b1)
        String - no manipulation
        Nodisp - these counters are never exported or displayed (its a base counter used
                for other math)

        PRIVILEGE-LEVEL - defines visibility of the counters
        Basic - essential counters
        Admin - for admin purposes
        Advanced - advanced, need not be customer visible
        Diag - used only for diagnostic purposes, can report incorrect data
        Perfmon_*,Stats_*, etc. - visible through perfmon/stats/etc
        sampled - objects that are automatically sampled

        This method is the same for cluster and 7 mode
        """
        if not cached or objectName not in self.perfCounters:
            counters = self.queryApi(
                {"perf-object-counter-list-info": {"objectname": objectName}},
                OntapClient.counterListInfoResults,
            )
            self.perfCounters[objectName] = counters
        return self.perfCounters[objectName]

    def convertDictToElements(self, query):
        """
        Takes a dict (looks and smells like json)
        and converts into a NaElement suitable for invoke_elem
        """
        if isinstance(query, set):
            # TODO: Make this message a part of the query and verify, send to logs also
            self.log.info("NETAPP ONTAP INFO: Malformed Query {query}".format(query=query.__str__()))  # noqa: G001
            raise BadQueryError(query)
        for k, v in query.items():
            if isinstance(v, dict):
                element = NaElement(k)
                element.child_add(self.convertDictToElements(v))
                return element
            elif isinstance(v, list):
                element = NaElement(k)
                for item in v:
                    element.child_add(self.convertDictToElements(item))
                return element
            else:
                element = NaElement(k, v)
                return element

    def getClusterNodeList(self, return_generator=False):
        """
        For a cluster mode oc this gets gets the full list of nodes in the
        cluster. If return_generator is passed as True this returns a generator
        for the list as opposed to the list itself.
        ARGS:
                return_generator - if True return a generator instead of list

        RETURNS a list or generator
        """
        if self.isClustered():
            query = {"system-node-get-iter": {"desired-attributes": {"node-details-info": {"node": ""}}}}

            def convertResults(results):
                """
                Simple node name extraction from node-details-info
                """
                out_array = []
                for attributes_list in results.children_get():
                    for node_info in attributes_list.children_get():
                        node_tag = node_info.child_get("node")
                        if node_tag is not None:
                            out_array.append(node_tag.element["content"])
                return out_array

            if return_generator:
                return self.queryApiIter(query, max_records=10, convert_results=convertResults)
            else:
                out_array = []
                for chunk in self.queryApiIter(query, max_records=10, convert_results=convertResults):
                    out_array += chunk
                return out_array
        else:
            raise ValueError("There's no nodes in seven mode you crazy person!")

    def queryApi(self, query, convert_results=None, clean=True):
        """
        This method queries the na-server according to the query string
        then stringifies the results according to the stringify method
        passed in.
        Note that query may be of the following types:
                NaElement, Dict, or String
        Note that convert_results is set to OntapClient.convertElementToDict
        if None is passed.
        ARGS:
                query - the ontap api query to perform
                convert_results - the callback to perform on the response to the given query

        returns convert_results(response)
        """
        if convert_results is None:
            convert_results = OntapClient.convertElementToDict

        # Convert the query into a NaElement
        if isinstance(query, dict):
            api = self.convertDictToElements(query)
        elif isinstance(query, str):
            api = NaElement(query)
        elif isinstance(query, NaElement):
            api = query
        else:
            raise TypeError(
                "query passed to OntapClient.queryApi must be of type: dict, str, NaElement, actual type={0}".format(
                    str(type(query))
                )
            )

        response = self.connection.invoke_elem(api, clean)
        if response.results_status() == "passed":
            self.log.info("NETAPP ONTAP INFO: Query to server {server} passed".format(server=self.server))  # noqa: G001
        else:
            errno = int(response.results_errno())
            reason = response.results_reason()
            # Re-enable for more verbose debugging.  In general, throwing here can lead to issues
            # with misleading error messages.  Throw/catch/print out the error elsewhere
            # self.logger.error("[QueryError] Query to server=%s errorno=%s reason=%s", self.server, errno, reason)
            if errno == NaErrno.EAPIAUTHENTICATION:
                raise AuthenticationError(errno, reason)
            elif errno == NaErrno.EAPILICENSE:
                # raise LicensingError(errno, reason)
                # We're masking the licensing error here, because they don't have the granularity to tune this.
                # As such, as soon as the license gets installed then they should start seeing the appropriate data
                # It also pollutes the log messages with messages that can be normal or aren't going to be addressed
                pass
            elif errno == NaErrno.EAPIERROR:
                if reason.startswith("[SSL: CERTIFICATE_VERIFY_FAILED]") or "_ssl.c" in reason:
                    raise SSLError(errno, reason)
                elif reason.startswith("[Errno 61]") or "timed out" in reason or "[Errno 8]" in reason:
                    raise ConnectionError(errno, reason, "server=" + self.server)
                elif re.match(r".*?was not found\.$", reason) or re.match("can't get counters for", reason):
                    # We need to check in case the filer was reconfigured but datadog wasn't.  For example
                    # If they update from a 7 to a cluster mode filer, but keep the same ip/hostname
                    pass  # For objects not found, this situation is expected, we shouldn't raise an exception
                else:
                    raise ClientSideError(errno, reason)
        return response if clean else convert_results(response)

    def queryApiIter(self, query, max_records=None, convert_results=None, preserve_metatags=False):
        """
        This method encapsulates the pattern of calling an "iter" style endpoint
        in the netapp ontap API. The iterator API is different for cluster
        mode and for 7 mode: cluster mode requires calling a single
        '-get-iter' endpoint, while 7 mode uses '-start-iter', '-next-iter',
        and '-end-iter' calls.  This method abstracts away the differences
        between the modes; in particular it sets the number of requested
        records and/or tag values.  The query passed to this method SHOULD
        NEVER include 'max-records' or 'maximum' parameters; instead, use the
        max_records method argument.  For cluster mode iterator, format the
        '-get-iter' as you ordinarily would, omitting the 'max-records'
        parameter.  For 7 mode, use the '-iter-start' endpoint and its
        arguments when building the query, be sure to omit the 'maximum'
        parameter.  This method will take care of issuing '-iter-next' and
        '-iter-end' requests.
        Examples:
                {'ems-message-get-iter': {'some-param': 'some-value', 'another-par', 0}} # cluster mode
            {'volume-list-info-iter-start': {'verbose': 1}} # 7-mode

        This method returns a generator that yields `max_records` records at a time, each
        pass getting the convert_results callback issued and returned. Note that
        prior to convert_results being called, the metatags e.g. next-tag, and
        num-records will be removed unless preserve_metatags is passed as True.
        ARGS:
                query - the dict form of the query to send to the api
                convert_results - callback to issue on the returned NaElements
                preserve_metatags - if False removes iteration elements before passing
                        the response to convert_results, defaults to False

        RETURNS a generator of the convert_results parsed responses
        """
        if max_records is None:
            max_records = self.ITER_API_MAX_RECORDS

        if convert_results is None:
            convert_results = OntapClient.convertElementToDict
        api = self.convertDictToElements(query) if isinstance(query, dict) else NaElement(query)

        def processResponse(response, next_tag_field, num_records_field):
            next_tag = None
            num_records = None
            new_children = []
            for node in response.children_get():
                elem = node.element
                if elem["name"] == next_tag_field:
                    next_tag = elem["content"]
                elif elem["name"] == num_records_field:
                    num_records = int(elem["content"])
                else:
                    new_children.append(node)
            if not preserve_metatags:
                response.element["children"] = new_children
            return response, next_tag, num_records

        def queryClusterModeGen():
            # Convert the query into a NaElement
            api.child_add(NaElement("max-records", max_records))
            response = self.queryApi(api, OntapClient.projectResponse)
            response, next_tag, num_records = processResponse(response, "next-tag", "num-records")
            self.log.info(
                "NETAPP ONTAP INFO: Query returned an iterator tag for {num_records} records".format(  # noqa: G001
                    num_records=num_records
                ),
            )
            yield convert_results(response)
            while next_tag is not None:
                tag = api.child_get("tag")
                if tag is None:
                    tag = NaElement("tag")
                    api.child_add(tag)
                tag.element["content"] = next_tag
                response = self.queryApi(api, OntapClient.projectResponse)
                response, next_tag, num_records = processResponse(response, "next-tag", "num-records")
                yield convert_results(response)

        def query7ModeGen():
            # assume that api variable contains -iter-start query when first invoked
            # and that on successful invocation it gives back a valid 'tag' (not None or empty)
            response = naElementToDict(self.queryApi(api, OntapClient.projectResponse))
            if "tag" in response and response["tag"]:
                tag = response["tag"]
                total_records = int(response["records"])
                read_records = 0
                api_name = list(query.keys())[0] if isinstance(query, dict) else query
                api_next_name = re.sub("start$", "next", api_name)
                api_next = self.convertDictToElements({api_next_name: [{"maximum": max_records}, {"tag": tag}]})
                api_end_name = re.sub("start$", "end", api_name)
                api_end = self.convertDictToElements({api_end_name: [{"tag": tag}]})
                num_records = int(response["records"]) if "records" in response else 0
                while num_records > 0 and read_records < total_records:
                    response = self.queryApi(api_next, OntapClient.projectResponse)
                    response, next_tag, num_records = processResponse(response, "", "records")
                    del next_tag
                    read_records += num_records
                    yield convert_results(response)
                response = self.queryApi(api_end, OntapClient.projectResponse)
                self.log.info("NETAPP ONTAP INFO: Finished iterating over %s", api_end_name)

        if self.isClustered():
            return queryClusterModeGen()
        else:
            return query7ModeGen()
