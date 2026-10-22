#!/usr/bin/env python3
"""Check whether TCP ports are available on a local address."""

import argparse
import errno
import ipaddress
import socket


def port_number(value):
    number = int(value)
    if not 1 <= number <= 65535:
        raise argparse.ArgumentTypeError("port must be between 1 and 65535")
    return number


def socket_family(host):
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return socket.AF_INET
    return socket.AF_INET6 if address.version == 6 else socket.AF_INET


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ports", nargs="+", type=port_number)
    parser.add_argument("--host", default="127.0.0.1", help="local IPv4 or IPv6 address to test")
    args = parser.parse_args()

    unavailable = False
    family = socket_family(args.host)
    for port in args.ports:
        with socket.socket(family, socket.SOCK_STREAM) as sock:
            try:
                sock.bind((args.host, port))
            except OSError as error:
                unavailable = True
                if error.errno == errno.EADDRINUSE:
                    print(f"IN USE {args.host}:{port}")
                else:
                    print(f"ERROR  {args.host}:{port}: {error}")
            else:
                print(f"FREE   {args.host}:{port}")
    return int(unavailable)


if __name__ == "__main__":
    raise SystemExit(main())
