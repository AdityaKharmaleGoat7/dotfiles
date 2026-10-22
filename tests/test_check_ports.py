import importlib.util
import pathlib
import socket
import unittest


SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "check_ports.py"
spec = importlib.util.spec_from_file_location("check_ports", SCRIPT)
check_ports = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(check_ports)


class SocketFamilyTests(unittest.TestCase):
    def test_ipv4_uses_af_inet(self):
        self.assertEqual(check_ports.socket_family("127.0.0.1"), socket.AF_INET)

    def test_ipv6_uses_af_inet6(self):
        self.assertEqual(check_ports.socket_family("::1"), socket.AF_INET6)

    def test_hostname_defaults_to_ipv4(self):
        self.assertEqual(check_ports.socket_family("localhost"), socket.AF_INET)


if __name__ == "__main__":
    unittest.main()
