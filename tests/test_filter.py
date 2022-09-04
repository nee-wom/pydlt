import pytest
import sys
from pydlt import (
    Filter,
    FilterList,
    DltMessage,
    MessageType,
    MessageLogInfo,
    ArgumentString,
)
import xml.etree.ElementTree as ET
import re
from pathlib import Path


CURRENT_DIR = Path(__file__).parent.absolute()
TEST_RESULTS_DIR_PATH = CURRENT_DIR / "results"
TEST_RESULTS_DIR_PATH.mkdir(exist_ok=True)


def make_filter(**kwargs: object) -> Filter:
    xml = "<filter>\n"
    for key, value in kwargs.items():
        xml += f"<{key}>{value}</{key}>\n"
    xml += "</filter>"
    f = Filter()
    f.from_xml(ET.fromstring(xml))
    return f


def make_message(
    ecuid="", apid="", ctid="", level=MessageLogInfo.DLT_LOG_INFO, payload=None
) -> DltMessage:
    args = []
    if payload is not None:
        args.append(ArgumentString(payload))
    return DltMessage.create_verbose_message(
        args, MessageType.DLT_TYPE_LOG, level, apid, ctid, ecu_id=ecuid
    )


def test_filter_empty():
    f = make_filter()
    assert f.enable
    assert f.name == ""
    assert f.positive
    assert not f.negative
    assert f.ecuid is None
    assert f.apid is None
    msg = make_message(ecuid="ECU", apid="APP")
    assert f.match(msg)
    assert f == eval(repr(f))


def test_filter_type():
    msg = make_message(ecuid="ECU", apid="APP")
    f0 = make_filter(type=0)
    assert f0.positive
    assert not f0.negative
    assert f0.match(msg)
    f1 = make_filter(type=1)
    assert not f1.positive
    assert f1.negative
    assert f1.match(msg)
    f2 = make_filter(type=2)
    assert not f2.positive
    assert not f2.negative
    # type is evaluated in FilterList, not in Filter directly
    assert f2.match(msg)
    assert f0 == eval(repr(f0))
    assert f1 == eval(repr(f1))
    assert f2 == eval(repr(f2))


def test_filter_name():
    f = make_filter(name="Foo")
    assert f.name == "Foo"
    f.name = "bar"
    assert f.name == "bar"
    assert f == eval(repr(f))


def test_filter_disabled():
    f = make_filter(ecuid="ECU1", enableecuid=1, enablefilter=0)
    assert f.match(make_message(ecuid="ECU1"))
    assert f.match(make_message(ecuid="ECU2"))
    assert f == eval(repr(f))


def test_filter_ecuid():
    f = make_filter(ecuid="ECU1")
    assert f.match(make_message(ecuid="ECU1"))
    assert f.match(make_message(ecuid="ECU2"))
    assert f == eval(repr(f))
    f = make_filter(ecuid="ECU1", enableecuid=1)
    assert f.match(make_message(ecuid="ECU1"))
    assert not f.match(make_message(ecuid="ECU2"))
    assert f == eval(repr(f))
    f = make_filter(enableecuid=1)
    assert f.match(make_message(ecuid=""))
    assert not f.match(make_message(ecuid="ECU1"))
    assert not f.match(make_message(ecuid="ECU2"))
    assert f == eval(repr(f))


def test_filter_apid():
    f = make_filter(applicationid="AP1")
    assert f.match(make_message(apid="AP1"))
    assert f.match(make_message(apid="AP2"))
    assert f == eval(repr(f))
    f = make_filter(applicationid="AP1", enableapplicationid=1)
    assert f.match(make_message(apid="AP1"))
    assert not f.match(make_message(apid="AP2"))
    assert f == eval(repr(f))
    f = make_filter(enableapplicationid=1)
    assert f.match(make_message(apid=""))
    assert not f.match(make_message(apid="AP1"))
    assert not f.match(make_message(apid="AP2"))
    assert f == eval(repr(f))


def test_filter_apid_regex():
    f = make_filter(applicationid="AP.", enableregexp_Appid=1)
    assert f.match(make_message(apid="AP1"))
    assert f.match(make_message(apid="NIX"))
    assert f == eval(repr(f))
    f = make_filter(applicationid="A..", enableapplicationid=1, enableregexp_Appid=1)
    assert f.match(make_message(apid="AP1"))
    assert f.match(make_message(apid="APX"))
    assert not f.match(make_message(apid="NIX"))
    assert f == eval(repr(f))


def test_filter_ctid():
    f = make_filter(contextid="CTX1")
    assert f.match(make_message(ctid="CTX1"))
    assert f.match(make_message(ctid="CTX1"))
    assert f == eval(repr(f))
    f = make_filter(contextid="CTX1", enablecontextid=1)
    assert f.match(make_message(ctid="CTX1"))
    assert not f.match(make_message(ctid="CTX2"))
    assert f == eval(repr(f))
    f = make_filter(enablecontextid=1)
    assert f.match(make_message(ctid=""))
    assert not f.match(make_message(ctid="CTX1"))
    assert not f.match(make_message(ctid="CTX2"))
    assert f == eval(repr(f))


def test_filter_ctid_regex():
    f = make_filter(contextid="CTX.", enableregexp_Context=1)
    assert f.match(make_message(ctid="CTX1"))
    assert f.match(make_message(ctid="NIX"))
    assert f == eval(repr(f))
    f = make_filter(contextid="CTX.", enablecontextid=1, enableregexp_Context=1)
    assert f.match(make_message(ctid="CTX1"))
    assert f.match(make_message(ctid="CTX_"))
    assert not f.match(make_message(ctid="NIX"))
    assert f == eval(repr(f))


def test_filter_payload():
    f = make_filter(payloadtext="foobar")
    assert f.match(make_message())
    assert f.match(make_message(payload="Hello World"))
    assert f == eval(repr(f))
    f = make_filter(payloadtext="foobar", enablepayloadtext=1)
    assert not f.match(make_message())
    assert not f.match(make_message(payload="Hello World"))
    assert f.match(make_message(payload="Hello foobar"))
    assert f == eval(repr(f))
    f = make_filter(enablepayloadtext=1)
    # substr "" is always a match
    assert f.match(make_message())
    assert f.match(make_message(payload="Hello World"))
    assert f.match(make_message(payload="Hello foobar"))
    assert f == eval(repr(f))


def test_filter_payload_regex():
    f = make_filter(payloadtext="foobar.*", enableregexp_Payload=1)
    assert f.match(make_message())
    assert f.match(make_message(payload="Hello World"))
    assert f == eval(repr(f))
    f = make_filter(payloadtext="foobar.*", enableregexp_Payload=1, enablepayloadtext=1)
    assert not f.match(make_message())
    assert not f.match(make_message(payload="Hello World"))
    assert not f.match(make_message(payload="Hello foobar"))
    assert f.match(make_message(payload="foobar hello"))
    assert f == eval(repr(f))


def test_filter_payload_ignore_case():
    f = make_filter(payloadtext="Foobar", enablepayloadtext=1, ignoreCase_Payload=1)
    assert not f.match(make_message())
    assert not f.match(make_message(payload="Hello World"))
    assert f.match(make_message(payload="Hello foobar"))
    assert f.match(make_message(payload="Hello FOOBAR"))
    assert f == eval(repr(f))


def test_filter_payload_regex_overrides_ic():
    f = make_filter(
        payloadtext="Foobar",
        enablepayloadtext=1,
        ignoreCase_Payload=1,
        enableregexp_Payload=1,
    )
    assert isinstance(f.payload, re.Pattern)
    assert f == eval(repr(f))


def test_maxlevel():
    f = make_filter(logLevelMax=2, enableLogLevelMax=1)
    assert f.match(make_message(level=0))
    assert f.match(make_message(level=1))
    assert f.match(make_message(level=2))
    assert not f.match(make_message(level=3))
    msg = make_message(level=1)
    msg.ext_header = None
    assert not f.match(msg)
    msg = make_message(level=1)
    msg.ext_header.message_type = 1
    assert not f.match(msg)
    assert f == eval(repr(f))


def test_minlevel():
    f = make_filter(logLevelMin=2, enableLogLevelMin=1)
    assert not f.match(make_message(level=0))
    assert not f.match(make_message(level=1))
    assert f.match(make_message(level=2))
    assert f.match(make_message(level=3))
    msg = make_message(level=2)
    msg.ext_header = None
    assert not f.match(msg)
    msg = make_message(level=2)
    msg.ext_header.message_type = 1
    assert not f.match(msg)
    assert f == eval(repr(f))


def test_list_empty():
    flist = FilterList()
    assert flist.match(make_message())
    assert flist.match(make_message(ctid="CTX1"))
    assert flist.match(make_message(ctid="CTX2"))
    assert flist.match(make_message(ctid="CTX3"))
    assert flist == eval(repr(flist))


def test_list_2_positive():
    f1 = make_filter(contextid="CTX1", enablecontextid=1)
    f2 = make_filter(contextid="CTX2", enablecontextid=1)
    flist = FilterList([f1, f2])
    assert 2 == len(flist._pfilters)
    assert 0 == len(flist._nfilters)
    assert not flist.match(make_message())
    assert flist.match(make_message(ctid="CTX1"))
    assert flist.match(make_message(ctid="CTX2"))
    assert not flist.match(make_message(ctid="CTX3"))
    assert flist == eval(repr(flist))


def test_list_2_positive_1_disabled():
    f1 = make_filter(contextid="CTX1", enablecontextid=1, enablefilter=0)
    f2 = make_filter(contextid="CTX2", enablecontextid=1)
    flist = FilterList([f1, f2])
    assert 1 == len(flist._pfilters)
    assert 0 == len(flist._nfilters)
    assert not flist.match(make_message())
    assert not flist.match(make_message(ctid="CTX1"))
    assert flist.match(make_message(ctid="CTX2"))
    assert not flist.match(make_message(ctid="CTX3"))
    assert flist == eval(repr(flist))


def test_list_1_negative():
    f1 = make_filter(contextid="CTX1", enablecontextid=1, type=1)
    flist = FilterList([f1])
    assert 0 == len(flist._pfilters)
    assert 1 == len(flist._nfilters)
    assert flist.match(make_message())
    assert not flist.match(make_message(ctid="CTX1"))
    assert flist.match(make_message(ctid="CTX2"))
    assert flist.match(make_message(ctid="CTX3"))
    assert flist == eval(repr(flist))


def test_list_2_positive_1_negative():
    f1 = make_filter(contextid="CTX1", enablecontextid=1)
    f2 = make_filter(contextid="CTX2", enablecontextid=1)
    f3 = make_filter(contextid="CTX1", enablecontextid=1, type=1)
    flist = FilterList([f1, f2, f3])
    assert 2 == len(flist._pfilters)
    assert 1 == len(flist._nfilters)
    assert not flist.match(make_message())
    assert not flist.match(make_message(ctid="CTX1"))
    assert flist.match(make_message(ctid="CTX2"))
    assert not flist.match(make_message(ctid="CTX3"))
    assert flist == eval(repr(flist))


def test_list_read_xml_string():
    flist = FilterList()
    flist.fromstring(
        """<dltfilter>
    <filter>
        <type>0</type>
        <name>Foo</name>
        <contextid>CTR</contextid>
        <enablecontextid>1</enablecontextid>
    </filter>
    <filter>
        <type>1</type>
        <name>Bar</name>
    </filter>
    </dltfilter>"""
    )
    assert 2 == len(flist.filters)
    assert 1 == len(flist._pfilters)
    assert 1 == len(flist._nfilters)
    assert flist._pfilters[0].name == "Foo"
    assert flist._nfilters[0].name == "Bar"
    f1 = flist.filters[0]
    assert f1.positive
    assert f1.name == "Foo"
    assert f1.apid is None
    assert f1.ctid == "CTR"
    assert f1.payload is None
    assert f1.maxlevel is None
    assert f1.minlevel is None
    f2 = flist.filters[1]
    assert f2.negative
    assert f2.name == "Bar"
    assert flist == eval(repr(flist))


def test_list_read_xml_file():
    flist = FilterList()
    flist.read(CURRENT_DIR / "example.dlf")
    assert 3 == len(flist.filters)
    assert 2 == len(flist._pfilters)
    assert 0 == len(flist._nfilters)
    assert flist.filters[0].name == "Foo"
    assert flist.filters[1].name == "Bar"
    assert flist.filters[2].name == "Baz"
    assert flist._pfilters[0].name == "Foo"
    assert flist._pfilters[1].name == "Bar"
    assert flist == eval(repr(flist))


def test_list_write_xml_file():
    path = TEST_RESULTS_DIR_PATH / Path(f"{sys._getframe().f_code.co_name}.dlf")
    f1 = make_filter(
        contextid="CTX1", enablecontextid=1, enablefilter=0, ecuid="ECU1", enableecuid=1
    )
    f2 = make_filter(
        contextid="CTX2", enablecontextid=1, applicationid="APL1", enableapplicationid=1
    )
    f3 = make_filter(applicationid="APL2", enableapplicationid=1, enableregexp_Appid=1)
    f4 = make_filter(contextid="CTX", enablecontextid=1, enableregexp_Context=1)
    f5 = make_filter(payloadtext="foo", enablepayloadtext=1, ignoreCase_Payload=1)
    f6 = make_filter(payloadtext="foo2", enablepayloadtext=1, enableregexp_Payload=1)
    f7 = make_filter(
        logLevelMax=5, enableLogLevelMax=1, logLevelMin=5, enableLogLevelMin=1
    )
    flist = FilterList([f1, f2, f3, f4, f5, f6, f7])
    flist.write(path)
    copy = FilterList()
    copy.read(path)
    assert flist == copy
    assert copy.filters[0].ctid == "CTX1"
    assert not copy.filters[0].enable
    assert copy.filters[0].ecuid == "ECU1"


if __name__ == "__main__":
    pytest.main(sys.argv)
