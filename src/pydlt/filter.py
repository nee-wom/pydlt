import re
from builtins import isinstance
from pathlib import Path
from typing import Union
from pydlt.message import DltMessage, MessageType
from enum import IntEnum
import xml.etree.ElementTree as ET


class FilterType(IntEnum):
    POSITIVE = 0
    NEGATIVE = 1
    MARKER = 2


class Filter:
    def __init__(
        self,
        enable: bool = True,
        name: str = "",
        type: FilterType = FilterType.POSITIVE,
        ecuid: str = None,
        apid: Union[str, re.Pattern] = None,
        ctid: Union[str, re.Pattern] = None,
        payload: Union[str, re.Pattern] = None,
        payload_ignorecase: bool = False,
        minlevel: int = None,
        maxlevel: int = None,
    ):
        self.enable = enable
        self.name = name
        self.type = type
        self.ecuid = ecuid
        self.apid = apid
        self.ctid = ctid
        self.payload = payload
        self.payload_ignorecase = payload_ignorecase
        self.minlevel = minlevel
        self.maxlevel = maxlevel

    def __repr__(self):
        val = f'Filter(enable={self.enable}, name="{self.name}", type={self.type}'
        if self.ecuid is not None:
            val += f', ecuid="{self.ecuid}"'
        if self.apid is not None:
            val += f", apid={repr(self.apid)}"
        if self.ctid is not None:
            val += f", ctid={repr(self.ctid)}"
        if self.payload is not None:
            val += f", payload={repr(self.payload)}"
        val += f", payload_ignorecase={self.payload_ignorecase}"
        if self.minlevel is not None:
            val += f", minlevel={self.minlevel}"
        if self.maxlevel is not None:
            val += f", maxlevel={self.maxlevel}"
        val += ")"
        return val

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return (
                self.enable == other.enable
                and self.name == other.name
                and self.type == other.type
                and self.ecuid == other.ecuid
                and self.apid == other.apid
                and self.ctid == other.ctid
                and self.payload == other.payload
                and self.payload_ignorecase == other.payload_ignorecase
                and self.minlevel == other.minlevel
                and self.minlevel == other.minlevel
            )
        return False

    def from_xml(self, el: ET.Element):
        """Reads the configuration from the xml node"""
        regex_apid = False
        regex_ctid = False
        regex_payload = False
        use_ecuid = False
        use_apid = False
        use_ctid = False
        use_payload = False
        use_minlevel = False
        use_maxlevel = False

        for child in el:
            if child.tag == "type":
                self.type = int(child.text)
            elif child.tag == "name":
                self.name = "" if child.text is None else child.text
            elif child.tag == "ecuid":
                self.ecuid = child.text
            elif child.tag == "applicationid":
                self.apid = child.text
            elif child.tag == "contextid":
                self.ctid = child.text
            elif child.tag == "payloadtext":
                self.payload = child.text
            elif child.tag == "logLevelMax":
                self.maxlevel = int(child.text)
            elif child.tag == "logLevelMin":
                self.minlevel = int(child.text)
            elif child.tag == "enableregexp_Appid":
                regex_apid = int(child.text) != 0
            elif child.tag == "enableregexp_Context":
                regex_ctid = int(child.text) != 0
            elif child.tag == "enableregexp_Payload":
                regex_payload = int(child.text) != 0
            elif child.tag == "enablefilter":
                self.enable = int(child.text) != 0
            elif child.tag == "enableecuid":
                use_ecuid = int(child.text) != 0
            elif child.tag == "enableapplicationid":
                use_apid = int(child.text) != 0
            elif child.tag == "enablecontextid":
                use_ctid = int(child.text) != 0
            elif child.tag == "enablepayloadtext":
                use_payload = int(child.text) != 0
            elif child.tag == "enableLogLevelMax":
                use_maxlevel = int(child.text) != 0
            elif child.tag == "enableLogLevelMin":
                use_minlevel = int(child.text) != 0
            elif child.tag == "ignoreCase_Payload":
                self.payload_ignorecase = int(child.text) != 0

        if not use_ecuid:
            self.ecuid = None
        elif self.ecuid is None:
            self.ecuid = ""

        if use_apid:
            if self.apid is None:
                self.apid = ""
            if regex_apid:
                self.apid = re.compile(self.apid)
        else:
            self.apid = None

        if use_ctid:
            if self.ctid is None:
                self.ctid = ""
            if regex_ctid:
                self.ctid = re.compile(self.ctid)
        else:
            self.ctid = None

        if use_payload:
            if self.payload is None:
                self.payload = ""
            if regex_payload:
                self.payload = re.compile(self.payload)
        else:
            self.payload = None

        if not use_maxlevel:
            self.maxlevel = None
        if not use_minlevel:
            self.minlevel = None

    def to_xml(self, el: ET.Element):
        """Writes the configuration to the given xml node"""
        ET.SubElement(el, "type").text = str(self.type.value)
        ET.SubElement(el, "name").text = "" if self.name is None else self.name
        ET.SubElement(el, "enablefilter").text = "1" if self.enable else "0"
        ET.SubElement(el, "ecuid").text = self.ecuid
        ET.SubElement(el, "enableecuid").text = "0" if self.ecuid is None else "1"

        if isinstance(self.apid, str) or self.apid is None:
            ET.SubElement(el, "applicationid").text = self.apid
            ET.SubElement(el, "enableregexp_Appid").text = "0"
        else:
            ET.SubElement(el, "applicationid").text = self.apid.pattern
            ET.SubElement(el, "enableregexp_Appid").text = "1"
        ET.SubElement(el, "enableapplicationid").text = (
            "0" if self.apid is None else "1"
        )

        if isinstance(self.ctid, str) or self.ctid is None:
            ET.SubElement(el, "contextid").text = self.ctid
            ET.SubElement(el, "enableregexp_Context").text = "0"
        else:
            ET.SubElement(el, "contextid").text = self.ctid.pattern
            ET.SubElement(el, "enableregexp_Context").text = "1"
        ET.SubElement(el, "enablecontextid").text = "0" if self.ctid is None else "1"

        if isinstance(self.payload, str) or self.payload is None:
            ET.SubElement(el, "payloadtext").text = self.payload
            ET.SubElement(el, "enableregexp_Payload").text = "0"
        else:
            ET.SubElement(el, "payloadtext").text = self.payload.pattern
            ET.SubElement(el, "enableregexp_Payload").text = "1"
        ET.SubElement(el, "enablepayloadtext").text = (
            "0" if self.payload is None else "1"
        )
        ET.SubElement(el, "ignoreCase_Payload").text = (
            "1" if self.payload_ignorecase else "0"
        )

        ET.SubElement(el, "logLevelMax").text = (
            "0" if self.maxlevel is None else str(self.maxlevel)
        )
        ET.SubElement(el, "enableLogLevelMax").text = (
            "0" if self.maxlevel is None else "1"
        )

        ET.SubElement(el, "logLevelMin").text = (
            "0" if self.minlevel is None else str(self.minlevel)
        )
        ET.SubElement(el, "enableLogLevelMin").text = (
            "0" if self.minlevel is None else "1"
        )

    @property
    def positive(self) -> bool:
        """Indicates a positive filter (show message if filter matches)"""
        return self.type == 0

    @property
    def negative(self) -> bool:
        """Indicates a negative filter (hide message if filter matches)"""
        return self.type == 1

    def match(self, msg: DltMessage) -> bool:
        if not self.enable:
            return True

        if self.ecuid is not None and msg.ecuid != self.ecuid:
            return False

        if self.apid is not None:
            if isinstance(self.apid, str):
                if msg.apid != self.apid:
                    return False
            else:
                if self.apid.match(msg.apid) is None:
                    return False

        if self.ctid is not None:
            if isinstance(self.ctid, str):
                if msg.ctid != self.ctid:
                    return False
            else:
                if self.ctid.match(msg.ctid) is None:
                    return False

        if self.payload is not None:
            payload = str(msg.payload)
            if isinstance(self.payload, str):
                token = (
                    self.payload
                    if not self.payload_ignorecase
                    else self.payload.lower()
                )
                payload = payload if not self.payload_ignorecase else payload.lower()
                if -1 == payload.find(token):
                    return False
            else:
                if self.payload.match(payload) is None:
                    return False

        if self.maxlevel is not None:
            if msg.ext_header is None:
                return False
            if msg.ext_header.message_type != MessageType.DLT_TYPE_LOG:
                return False
            if msg.ext_header.message_type_info > self.maxlevel:
                return False

        if self.minlevel is not None:
            if msg.ext_header is None:
                return False
            if msg.ext_header.message_type != MessageType.DLT_TYPE_LOG:
                return False
            if msg.ext_header.message_type_info < self.minlevel:
                return False

        return True


class FilterList:
    def __init__(self, filters=[]):
        self.filters = filters
        self._nfilters = []
        self._pfilters = []
        self._sort()

    def __repr__(self):
        return f"FilterList({self.filters})"

    def __eq__(self, other):
        return self.filters == other.filters

    def read(self, path: Union[str, Path]):
        """loads a filter list from a dlf file"""
        tree = ET.parse(path)
        self._parse(tree.getroot())

    def fromstring(self, xml: str):
        """Loads a filter list from a xml string in dlf format"""
        root = ET.fromstring(xml)
        self._parse(root)

    def _parse(self, root: ET.Element):
        self.filters = []
        for child in root:
            if child.tag == "filter":
                f = Filter()
                f.from_xml(child)
                self.filters.append(f)
        self._sort()

    def write(self, path: Union[str, Path]):
        """Writes the filter set to a dlf file"""
        root = ET.Element("dltfilter")
        for f in self.filters:
            child = ET.SubElement(root, "filter")
            f.to_xml(child)
        tree = ET.ElementTree(root)
        tree.write(path)

    def match(self, msg: DltMessage) -> bool:
        """Returns true if the filter matches with the dlt message"""
        # if there are no positive filters the message is found
        # (unless a negative filter hides it)
        found = True if len(self._pfilters) == 0 else False
        for f in self._pfilters:
            if f.match(msg):
                found = True
                break
        if found:
            for f in self._nfilters:
                if f.match(msg):
                    found = False
                    break
        return found

    def _sort(self):
        self._nfilters = []
        self._pfilters = []
        for f in self.filters:
            if f.positive and f.enable:
                self._pfilters.append(f)
            elif f.negative and f.enable:
                self._nfilters.append(f)
