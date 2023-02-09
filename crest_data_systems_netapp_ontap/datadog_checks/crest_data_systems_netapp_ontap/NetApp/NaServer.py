import base64
import http.client as httplib
import socket
import sys
import xml.parsers.expat

import xmltodict

from .constants import ciphers
from .NaElement import NaDict, NaElement

ssl_import = True
try:
    import ssl
except ImportError:
    ssl_import = False


# dtd files
FILER_dtd = "file:/etc/netapp_filer.dtd"
DFM_dtd = "file:/etc/netapp_dfm.dtd"
AGENT_dtd = "file:/etc/netapp_agent.dtd"

# URLs
AGENT_URL = "/apis/XMLrequest"
FILER_URL = "/servlets/netapp.servlets.admin.XMLrequest_filer"
NETCACHE_URL = "/servlets/netapp.servlets.admin.XMLrequest"
DFM_URL = "/apis/XMLrequest"

ZAPI_xmlns = "http://www.netapp.com/filer/admin"


class NaServer:
    """Class for managing Network Appliance(r) Storage System
    using ONTAPI(tm) and DataFabric Manager API(tm).

    An NaServer encapsulates an administrative connection to
    a NetApp Storage Systems running Data ONTAP 6.4 or later.
    NaServer can also be used to establish connection with
    DataFabric Manager (DFM). You construct NaElement objects
    that represent queries or commands, and use invoke_elem()
    to send them to the storage systems or DFM server. The
    return from the call is another NaElement which either
    has children containing the command results, or an error
    indication.

    The following routines are available for setting up
    administrative connections to a storage system or DFM server.
    """

    def __init__(self, server, major_version, minor_version):
        """Create a new connection to server 'server'.  Before use,
        you either need to set the style to "hosts.equiv" or set
        the username (always "root" at present) and password with
        set_admin_user().
        """

        self.server = server
        self.major_version = major_version
        self.minor_version = minor_version
        self.transport_type = "HTTP"
        self.port = 80
        self.user = "root"
        self.password = ""
        self.style = "LOGIN"
        self.timeout = None
        self.vfiler = ""
        self.server_type = "FILER"
        self.debug_style = ""
        self.xml = ""
        self.originator_id = ""
        self.cert_file = None
        self.key_file = None
        self.ca_file = None
        self.need_cba = False
        self.need_server_auth = False
        self.need_cn_verification = False
        self.url = FILER_URL
        self.dtd = FILER_dtd
        self.ZAPI_stack = []
        self.ZAPI_atts = {}

    def set_style(self, style):
        """Pass in 'LOGIN' to cause the server to use HTTP simple
        authentication with a username and password.  Pass in 'HOSTS'
        to use the hosts.equiv file on the filer to determine access
        rights (the username must be root in that case). Pass in
        'CERTIFICATE' to use certificate based authentication with the
        DataFabric Manager server.
        If style = CERTIFICATE, you can use certificates to authenticate
        clients who attempt to connect to a server without the need of
        username and password. This style will internally set the transport
        type to HTTPS. Verification of the server's certificate is required
        in order to properly authenticate the identity of the server.
        Server certificate verification will be enabled by default using this
        style and Server certificate verification will always enable hostname
        verification. You can disable server certificate (with hostname)
        verification using set_server_cert_verification().
        """

        if style != "HOSTS" and style != "LOGIN" and style != "CERTIFICATE":
            return self._fail_response(13001, 'in NaServer::set_style: bad style "' + style + '"')

        if style == "CERTIFICATE":
            if ssl_import is False:
                return self._fail_response(
                    13001,
                    'in NaServer::set_style: "' + style + "\" cannot be used as 'ssl' module is not imported.",
                )
            ret = self.set_transport_type("HTTPS")
            if ret:
                return ret
            self.need_cba = True
            self.need_server_auth = True
            self.set_server_cert_verification(True)
        else:
            self.need_cba = False
            self.need_server_auth = False
            self.set_server_cert_verification(False)
        self.style = style
        return None

    def get_style(self):
        """Get the authentication style"""

        return self.style

    def set_admin_user(self, user, password):
        """Set the admin username and password.  At present 'user' must
        always be 'root'.
        """

        self.user = user
        self.password = password

    def set_transport_type(self, scheme):
        """Override the default transport type.  The valid transport
        type are currently 'HTTP' and 'HTTPS'.
        """

        if scheme != "HTTP" and scheme != "HTTPS":
            return self._fail_response(13001, 'in NaServer::set_transport_type: bad type " ' + scheme + '"')

        if scheme == "HTTP":
            self.transport_type = "HTTP"

            if self.server_type == "DFM":
                self.port = 8088

            else:
                self.port = 80

        if scheme == "HTTPS":
            self.transport_type = "HTTPS"

            if self.server_type == "DFM":
                self.port = 8488

            else:
                self.port = 443

        return None

    def get_transport_type(self):
        """Retrieve the transport used for this connection."""

        return self.transport_type

    def set_port(self, port):
        """Override the default port for this server."""

        self.port = port

    def get_port(self):
        """Retrieve the port used for the remote server."""

        return self.port

    def is_debugging(self):
        """Check the type of debug style and return the
        value for different needs. Return 1 if debug style
        is NA_PRINT_DONT_PARSE,    else return 0.
        """

        if self.debug_style == "NA_PRINT_DONT_PARSE":
            return 1

        else:
            return 0

    def set_raw_xml_output(self, xml):
        """Save the raw XML output."""

        self.xml = xml

    def get_raw_xml_output(self):
        """Return the raw XML output."""

        return self.xml

    def use_https(self):
        """Determines whether https is enabled."""

        if self.transport_type == "HTTPS":
            return 1

        else:
            return 0

    def invoke_elem(self, req, clean):
        """Submit an XML request already encapsulated as
        an NaElement and return the result in another
        NaElement.
        """

        server = self.server
        user = self.user
        password = self.password
        debug_style = self.debug_style
        vfiler = self.vfiler
        originator_id = self.originator_id
        xmlrequest = req.toEncodedString()
        vfiler_req = ""
        originator_id_req = ""

        try:
            if self.transport_type == "HTTP":
                connection = httplib.HTTPConnection(server, port=self.port, timeout=self.timeout)

            else:  # for HTTPS
                if self.need_cba is True or self.need_server_auth is True or self.need_cn_verification is True:
                    connection = CustomHTTPSConnection(
                        server,
                        self.port,
                        key_file=self.key_file,
                        cert_file=self.cert_file,
                        ca_file=self.ca_file,
                        need_server_auth=self.need_server_auth,
                        need_cn_verification=False and self.need_cn_verification,
                        timeout=self.timeout,
                    )
                    connection.connect()
                    if self.need_cn_verification is True:
                        cn_name = connection.get_commonName()
                        if cn_name.lower() != server.lower():
                            cert_err = (
                                "server certificate verification failed: server certificate name (CN="
                                + cn_name
                                + "), hostname ("
                                + server
                                + ") mismatch."
                            )
                            connection.close()
                            return self._fail_response(13001, cert_err)
                else:
                    if hasattr(ssl, "create_default_context"):
                        updated_ciphers = ssl._DEFAULT_CIPHERS

                        # Append ciphers from ta_ontap_config_ssl.conf if python version >= 2.7.13
                        # to support older ssl ciphers for ONTAP 7-mode
                        py_ver = [2, 7, 12]
                        sys_py_ver = list(sys.version_info[:3])
                        check = False
                        for i in range(3):
                            if sys_py_ver[i] > py_ver[i]:
                                check = True
                                break
                        if check:
                            try:
                                updated_ciphers += ":" + ciphers
                                updated_ciphers = updated_ciphers.replace(":!3DES:", ":")
                            except Exception:
                                pass
                        context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
                        context.set_ciphers(updated_ciphers)
                        connection = httplib.HTTPSConnection(
                            server,
                            port=self.port,
                            timeout=self.timeout,
                            context=context,
                        )
                    else:
                        connection = httplib.HTTPSConnection(server, port=self.port, timeout=self.timeout)

            connection.putrequest("POST", self.url)
            connection.putheader("Content-type", 'text/xml; charset="UTF-8"')

            if self.get_style() != "HOSTS":
                base64string = base64.b64encode(("%s:%s" % (user, password)).encode())
                auth_header = "Basic %s" % base64string.decode().strip()

                connection.putheader("Authorization", auth_header)

            if vfiler != "":
                vfiler_req = ' vfiler="' + vfiler + '"'

            if originator_id != "":
                originator_id_req = ' originator_id="' + originator_id + '"'

            content = (
                "<?xml version='1.0' encoding='utf-8'?>"
                + "<!DOCTYPE netapp SYSTEM '"
                + self.dtd
                + "'>"
                + "<netapp"
                + vfiler_req
                + originator_id_req
                + ' version="'
                + str(self.major_version)
                + "."
                + str(self.minor_version)
                + '"'
                + ' xmlns="'
                + ZAPI_xmlns
                + '">'
                + xmlrequest
                + "</netapp>"
            )

            if debug_style == "NA_PRINT_DONT_PARSE":
                self.log.info("INPUT \n{content}".format(content=content))  # noqa: G00

            connection.putheader("Content-length", str(len(content)))
            connection.endheaders()
            connection.send(content.encode())

        except socket.error:
            message = sys.exc_info()
            return self._fail_response(13001, message[1])

        response = connection.getresponse()

        if not response:
            connection.close()
            return self._fail_response(13001, "No response received")

        if response.status == 401:
            connection.close()
            return self._fail_response(13002, "Authorization failed")

        xml_response = response.read()

        if self.is_debugging() > 0 and debug_style != "NA_PRINT_DONT_PARSE":
            self.set_raw_xml_output(xml_response)
            self.log.info(("\nOUTPUT :", xml_response, "\n"))
            connection.close()
            return self._fail_response(13001, "debugging bypassed xml parsing")

        connection.close()

        return self._parse_xml(xml_response, clean)

    def set_timeout(self, timeout):
        """Sets the connection timeout value, in seconds,
        for the given server context.
        """

        self.timeout = timeout

    def get_timeout(self):
        """Retrieves the connection timeout value (in seconds)
        for the given server context.
        """

        return self.timeout

    def set_ca_certs(self, ca_file):
        """Specifies the certificates of the Certificate Authorities (CAs) that are
        trusted by this application and that will be used to verify the server certificate.
        """

        self.ca_file = ca_file

    def set_server_cert_verification(self, enable):
        """Enables or disables server certificate verification by the client.
        Server certificate verification is enabled by default when style
        is set to CERTIFICATE. Hostname (CN) verification is enabled
        during server certificate verification.
        """

        if enable is not True and enable is not False:
            return self._fail_response(
                13001,
                "NaServer::set_server_cert_verification: invalid argument " + str(enable) + " specified",
            )
        if not self.use_https():
            return self._fail_response(
                13001,
                "in NaServer::set_server_cert_verification: server certificate verification can only be"
                " enabled or disabled for HTTPS transport",
            )
        if enable is True and ssl_import is False:
            return self._fail_response(
                13001,
                "in NaServer::set_server_cert_verification: server certificate verification cannot be"
                " used as 'ssl' module is not imported.",
            )
        self.need_cn_verification = enable
        return None

    # "private" subroutines for use by the public routines

    # This is used when the transmission path fails, and we don't actually
    # get back any XML from the server.

    def _fail_response(self, errno, reason):
        """This is a private function, not to be called from outside NaElement"""
        n = NaElement("results")
        n._attr_set("status", "failed")
        n._attr_set("reason", reason)
        n._attr_set("errno", errno)
        return n

    def _start_element(self, name, attrs):
        """This is a private function, not to be called from outside NaElement"""

        n = NaElement(name)
        self.ZAPI_stack.append(n)
        self.ZAPI_atts = {}
        attr_name = list(attrs.keys())
        attr_value = list(attrs.values())
        i = 0
        for att in attr_name:
            val = attr_value[i]
            i = i + 1
            self.ZAPI_atts[att] = val
            n._attr_set(att, val)

    def _end_element(self, name):
        """This is a private function, not to be called from outside NaElement"""

        stack_len = len(self.ZAPI_stack)

        if stack_len > 1:
            n = self.ZAPI_stack.pop(stack_len - 1)
            i = len(self.ZAPI_stack)

            if i != stack_len - 1:
                self.log.info("pop did not work!!!!\n")

            self.ZAPI_stack[i - 1].child_add(n)

    def _char_data(self, data):
        """This is a private function, not to be called from outside NaElement"""

        i = len(self.ZAPI_stack)
        self.ZAPI_stack[i - 1].add_content(data)

    def _parse_xml(self, xmlresponse, clean):
        """This is a private function, not to be called from outside NaElement"""

        if clean:
            r = xmltodict.parse(xmlresponse)

            if not r.get("netapp"):
                return self._fail_response(
                    13001,
                    "Zapi::_parse_xml - Expected <netapp> element but got " + r.element["name"],
                )

            r = r["netapp"]
            results = r.get("results")

            if results is None:
                return self._fail_response(13001, "Zapi::_parse_xml - No results element in output!")

            return NaDict(results)

        p = xml.parsers.expat.ParserCreate()
        p.StartElementHandler = self._start_element
        p.EndElementHandler = self._end_element
        p.CharacterDataHandler = self._char_data
        p.Parse(xmlresponse, 1)
        stack_len = len(self.ZAPI_stack)

        if stack_len <= 0:
            return self._fail_response(13001, "Zapi::_parse_xml-no elements on stack")

        r = self.ZAPI_stack.pop(stack_len - 1)

        if r.element["name"] != "netapp":
            return self._fail_response(
                13001,
                "Zapi::_parse_xml - Expected <netapp> element but got " + r.element["name"],
            )

        results = r.child_get("results")

        if results is None:
            return self._fail_response(13001, "Zapi::_parse_xml - No results element in output!")

        return results


try:

    class CustomHTTPSConnection(httplib.HTTPSConnection):
        """Custom class to make a HTTPS connection, with support for Certificate Based Authentication"""

        def __init__(
            self,
            host,
            port,
            key_file,
            cert_file,
            ca_file,
            need_server_auth,
            need_cn_verification,
            timeout=None,
        ):
            httplib.HTTPSConnection.__init__(
                self,
                host,
                port=port,
                key_file=key_file,
                cert_file=cert_file,
                timeout=timeout,
            )
            self.key_file = key_file
            self.cert_file = cert_file
            self.ca_file = ca_file
            self.timeout = timeout
            self.need_server_auth = need_server_auth
            self.need_cn_verification = need_cn_verification

        def connect(self):
            sock = socket.create_connection((self.host, self.port), self.timeout)

            if hasattr(ssl, "create_default_context"):
                context = ssl.create_default_context()

                context.verify_mode = ssl.CERT_REQUIRED
                context.load_verify_locations(self.ca_file)

                if self.need_server_auth is True:
                    context.load_cert_chain(self.cert_file, self.key_file)

                self.sock = context.wrap_socket(sock, server_hostname=self.host)
            else:
                if self.need_server_auth is True:
                    self.sock = ssl.wrap_socket(
                        sock,
                        self.key_file,
                        self.cert_file,
                        ca_certs=self.ca_file,
                        cert_reqs=ssl.CERT_REQUIRED,
                    )
                else:
                    self.sock = ssl.wrap_socket(sock, ca_certs=self.ca_file, cert_reqs=ssl.CERT_REQUIRED)

        def get_commonName(self):
            cert = self.sock.getpeercert()
            for x in cert["subject"]:
                if x[0][0].lower() == "commonname":
                    return x[0][1]
            return ""

except AttributeError:
    pass
