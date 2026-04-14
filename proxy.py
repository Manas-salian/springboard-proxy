#!/usr/bin/env python3
"""
Springboard Proxy - HTTPS intercepting proxy server.

Uses mitmproxy to intercept and log all HTTP/HTTPS traffic.
Designed for use with FoxyProxy browser extension.

Usage:
    python proxy.py [--port PORT] [--listen-host HOST] [-q]
"""

import os
import argparse
import asyncio

# Patch h2 to accept malformed headers from upstream servers.
# Some servers (e.g. infyspringboard) send CSP headers with trailing whitespace,
# which violates HTTP/2 spec and causes h2 to raise ProtocolError.
import h2.config
_orig_h2_init = h2.config.H2Configuration.__init__
def _patched_h2_init(self, *args, **kwargs):
    kwargs["validate_inbound_headers"] = False
    _orig_h2_init(self, *args, **kwargs)
h2.config.H2Configuration.__init__ = _patched_h2_init

from mitmproxy import options
from mitmproxy.tools.dump import DumpMaster

from addons.logger import RequestResponseLogger
from addons.interceptor import TargetInterceptor

DEFAULT_PORT = 9876

BANNER = """
  Springboard Proxy
  HTTPS Intercepting Proxy Server
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Springboard HTTPS Proxy")
    parser.add_argument(
        "-p", "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Proxy listen port (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--listen-host",
        type=str,
        default="127.0.0.1",
        help="Proxy listen host (default: 127.0.0.1)",
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress mitmproxy's default event log",
    )
    return parser.parse_args()


async def start_proxy(args: argparse.Namespace) -> None:
    opts = options.Options(
        listen_host=args.listen_host,
        listen_port=args.port,
        ssl_insecure=True,
    )

    master = DumpMaster(
        opts,
        with_termlog=not args.quiet,
        with_dumper=False,
    )

    master.addons.add(RequestResponseLogger())
    master.addons.add(TargetInterceptor())

    print(BANNER)
    print(f"  Listening on  {args.listen_host}:{args.port}")
    ca_dir = os.path.join(os.path.expanduser("~"), ".mitmproxy")
    print(f"  Logs          ./logs/")
    print(f"  CA certs      {ca_dir}")
    print()
    print(f"  FoxyProxy     HTTP Proxy -> 127.0.0.1:{args.port}")
    print(f"  CA install    http://mitm.it (with proxy active)")
    print()
    print(f"  Ctrl+C to stop")
    print("-" * 50)
    print()

    try:
        await master.run()
    except KeyboardInterrupt:
        master.shutdown()


def main():
    args = parse_args()
    asyncio.run(start_proxy(args))


if __name__ == "__main__":
    main()
