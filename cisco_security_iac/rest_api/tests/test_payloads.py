"""Offline unit tests for the FMC REST payload builders (no FMC contacted)."""
from fmc_access_policy import (
    build_access_policy_payload,
    build_access_rule_payload,
    build_network_payload,
)


def test_network_payload():
    p = build_network_payload("inside-net", "198.18.2.0/24", "d")
    assert p["type"] == "Network"
    assert p["value"] == "198.18.2.0/24"
    assert p["name"] == "inside-net"
    assert p["description"] == "d"


def test_access_policy_payload_defaults_to_block():
    p = build_access_policy_payload("inside-to-outside-policy")
    assert p["type"] == "AccessPolicy"
    assert p["name"] == "inside-to-outside-policy"
    assert p["defaultAction"]["action"] == "BLOCK"


def test_access_rule_allows_inside_to_outside():
    src = {"type": "Network", "name": "inside-net", "id": "1"}
    dst = {"type": "Network", "name": "outside-net", "id": "2"}
    r = build_access_rule_payload("allow-inside-to-outside", src, dst)
    assert r["type"] == "AccessRule"
    assert r["action"] == "ALLOW"
    assert r["enabled"] is True
    assert r["sourceNetworks"]["objects"][0]["id"] == "1"
    assert r["destinationNetworks"]["objects"][0]["id"] == "2"
