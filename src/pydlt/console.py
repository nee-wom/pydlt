#!/usr/bin/env python3
import click
from pydlt import DltClient, ControlResponse, DltFileReader


@click.group()
@click.version_option()
def cli():
    """DLT client and file utility"""
    pass


@cli.command()
@click.option(
    "--hostname", default="localhost", show_default=True, help="hostname of DLT daemon"
)
@click.option("--port", default=3490, show_default=True, help="tcp port of DLT daemon")
def receive(hostname, port):
    """Connects to the DLT Daemon and receives log messages"""
    with DltClient(hostname, port) as dlt:
        while True:
            click.echo(dlt.receive())


@cli.command()
@click.option(
    "--hostname", default="localhost", show_default=True, help="hostname of DLT daemon"
)
@click.option("--port", default=3490, show_default=True, help="tcp port of DLT daemon")
def get_sw_version(hostname, port):
    """Gets the ECU software version from the DLT daemon"""
    with DltClient(hostname, port) as dlt:
        msg = dlt.receive()
        ecuid = msg.std_header.ecu_id  # TODO ecuid property
        status, count, log = dlt.get_software_version(ecuid)
        if status != ControlResponse.OK:
            raise click.ClickException(f"Failed to get sw version: {repr(status)}")
        print(log)


@cli.command()
@click.option(
    "--hostname", default="localhost", show_default=True, help="hostname of DLT daemon"
)
@click.option("--port", default=3490, show_default=True, help="tcp port of DLT daemon")
@click.argument("level", type=int)
@click.option(
    "-a",
    "--apid",
    required=True,
    type=str,
    help="Application id that shall be affected",
)
@click.option("-c", "--ctid", type=str, help="Context id that shall be affected")
def set_log_level(hostname, port, level, apid, ctid):
    """Sets a new log level to the DLT daemon"""
    with DltClient(hostname, port) as dlt:
        # TODO: DRY
        msg = dlt.receive()
        ecuid = msg.std_header.ecu_id  # TODO ecuid property
        status = dlt.set_log_level(ecuid, level, apid, ctid)
        if status != ControlResponse.OK:
            raise click.ClickException(f"Failed to set log level: {repr(status)}")


@cli.command()
@click.option(
    "--hostname", default="localhost", show_default=True, help="hostname of DLT daemon"
)
@click.option("--port", default=3490, show_default=True, help="tcp port of DLT daemon")
@click.argument("level", type=int)
def set_default_log_level(hostname, port, level):
    """Sets a new default log level to the DLT daemon"""
    with DltClient(hostname, port) as dlt:
        # TODO: DRY
        msg = dlt.receive()
        ecuid = msg.std_header.ecu_id  # TODO ecuid property
        status = dlt.set_default_log_level(ecuid, level)
        if status != ControlResponse.OK:
            raise click.ClickException(f"Failed to set log level: {status}")


@cli.command()
@click.argument("dltfile", type=click.Path(exists=True))
def convert(dltfile):
    """Converts DLTFILE into other formats"""
    with DltFileReader(dltfile) as dlt:
        for msg in dlt:
            print(msg)
