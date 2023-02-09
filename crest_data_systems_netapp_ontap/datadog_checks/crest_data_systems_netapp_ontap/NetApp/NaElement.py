import re
import sys

import xmltodict


class NaDict(dict):
    def results_status(self):
        """Indicates success or failure of API call.
        Returns either 'passed' or 'failed'.
        """
        r = self.get("status")

        if r == "passed":
            return "passed"

        else:
            return "failed"

    def results_reason(self):
        """Human-readable string describing a failure.
        Only present if results_status does not return 'passed'.
        """

        r = self.get("status")
        if r == "passed":
            return None

        r = self.get("reason")
        if not r:
            return "No reason given"

        return str(r)

    def results_errno(self):
        """Returns an error number, 0 on success."""

        r = self.get("status")

        if r == "passed":
            return 0

        r = self.get("errno")

        if not r:
            r = -1

        return r

    def sprintf(self):
        """Sprintf pretty-prints the element and its children,
        recursively, in XML-ish format. This is of use
        mainly in exploratory and utility programs.

        Parameter 'indent' is optional.
        """

        return xmltodict.unparse(self)


class NaElement:
    """Class encapsulating Netapp XML request elements.

    An NaElement encapsulates one level of an XML element.
    Elements can be arbitrarily nested.  They have names,
    corresponding to XML tags, attributes (only used for
    results), values (always strings) and possibly children,
    corresponding to nested tagged items.  See NaServer for
    instructions on using NaElements to invoke ONTAPI API calls.

    The following routines are available for constructing and
    accessing the contents of NaElements.
    """

    # Global Variables
    DEFAULT_KEY = "#u82fyi8S5\017pPemw"
    MAX_CHUNK_SIZE = 256

    def __init__(self, name, value=None):
        """Construct a new NaElement.  The 'value' parameter is
        optional for top level elements.
        """

        self.element = {
            "name": name,
            "content": "",
            "children": [],
            "attrkeys": [],
            "attrvals": [],
        }
        if value is not None:
            self.element["content"] = value

    def results_status(self):
        """Indicates success or failure of API call.
        Returns either 'passed' or 'failed'.
        """
        r = self._attr_get("status")

        if r == "passed":
            return "passed"

        else:
            return "failed"

    def results_reason(self):
        """Human-readable string describing a failure.
        Only present if results_status does not return 'passed'.
        """

        r = self._attr_get("status")
        if r == "passed":
            return None

        r = self._attr_get("reason")
        if not r:
            return "No reason given"

        return str(r)

    def results_errno(self):
        """Returns an error number, 0 on success."""

        r = self._attr_get("status")

        if r == "passed":
            return 0

        r = self._attr_get("errno")

        if not r:
            r = -1

        return r

    def child_get(self, name):
        """Get a named child of an element, which is also an
        element.  Elements can be nested arbitrarily, so
        the element you get with this could also have other
        children.  The return is either an NaElement named
        'name', or None if none is found.
        """

        arr = self.element["children"]

        for i in arr:
            if name == i.element["name"]:
                return i

        return None

    def set_content(self, content):
        """Set the element's value to 'content'.  This is
        not needed in normal development.
        """

        self.element["content"] = content

    def add_content(self, content):
        """Add the element's value to 'content'.  This is
        not needed in normal development.
        """

        self.element["content"] = self.element["content"] + content

    def child_add(self, child):
        """Add the element 'child' to the children list of
        the current object, which is also an element.
        """

        arr = self.element["children"]
        arr.append(child)
        self.element["children"] = arr

    def child_add_string(self, name, value):
        """Construct an element with name 'name' and contents
        'value', and add it to the current object, which
        is also an element.
        """

        elt = NaElement(name, value)
        self.child_add(elt)

    def child_get_string(self, name):
        """Gets the child named 'name' from the current object
        and returns its value.  If no child named 'name' is
        found, returns None.
        """

        elts = self.element["children"]

        for elt in elts:
            if name == elt.element["name"]:
                return elt.element["content"]

        return None

    def children_get(self):
        """Returns the list of children as an array."""

        elts = self.element["children"]
        return elts

    def sprintf(self, indent=""):
        """Sprintf pretty-prints the element and its children,
        recursively, in XML-ish format.  This is of use
        mainly in exploratory and utility programs.  Use
        child_get_string() to dig values out of a top-level
        element's children.

        Parameter 'indent' is optional.
        """

        name = self.element["name"]
        s = indent + "<" + name
        keys = self.element["attrkeys"]
        vals = self.element["attrvals"]
        j = 0

        for i in keys:
            s = s + " " + str(i) + '="' + str(vals[j]) + '"'
            j = j + 1

        s = s + ">"
        children = self.element["children"]

        if len(children) > 0:
            s = s + "\n"

        for i in children:
            c = i

            if not re.search("NaElement.NaElement", str(c.__class__), re.I):
                sys.exit("Unexpected reference found, expected NaElement.NaElement not " + str(c.__class__) + "\n")

            s = s + c.sprintf(indent + "\t")

        s = s + str(self.element["content"])

        if len(children) > 0:
            s = s + indent

        s = s + "</" + name + ">\n"
        return s

    def toEncodedString(self):
        """Encodes string embedded with special chars like &,<,>.
        This is mainly useful when passing string values embedded
        with special chars like &,<,> to API.
        """
        n = self.element["name"]
        s = "<" + n
        keys = self.element["attrkeys"]
        vals = self.element["attrvals"]
        j = 0

        for i in keys:
            s = s + " " + str(i) + '="' + str(vals[j]) + '"'
            j = j + 1

        s = s + ">"
        children = self.element["children"]

        for i in children:
            c = i

            if not re.search("NaElement.NaElement", str(c.__class__), re.I):
                sys.exit("Unexpected reference found, expected NaElement.NaElement not " + str(c.__class__) + "\n")

            s = s + c.toEncodedString()

        cont = str(self.element["content"])
        cont = re.sub(r"&", "&amp;", cont, count=0)
        cont = re.sub(r"<", "&lt;", cont, count=0)
        cont = re.sub(r">", "&gt;", cont, count=0)
        cont = re.sub(r"'", "&apos;", cont, count=0)
        cont = re.sub(r'"', "&quot;", cont, count=0)
        s = s + cont
        s = s + "</" + n + ">"
        return s

    # ------------------------------------------------------------#
    #
    # routines beyond this point are "private"
    #
    # ------------------------------------------------------------#

    def _attr_set(self, key, value):
        """This is a private function, not to be called from outside NaElement."""

        arr = self.element["attrkeys"]
        arr.append(key)
        self.element["attrkeys"] = arr
        arr = self.element["attrvals"]
        arr.append(value)
        self.element["attrvals"] = arr

    def _attr_get(self, key):
        """This is a private function, not to be called from outside NaElement."""

        keys = self.element["attrkeys"]
        vals = self.element["attrvals"]
        j = 0

        for i in keys:
            if i == key:
                return vals[j]

            j = j + 1

        return None
