"""
Unit tests for dataset repository.
"""


def test_repository_has_data(repo):
    """Test that the repository contains data."""
    assert len(repo.get_all_hosts()) > 0
    assert len(repo.get_all_certificates()) > 0


def test_host_by_ip(repo):
    """Test getting host by IP."""
    hosts = repo.get_all_hosts()
    if hosts:
        first_host = hosts[0]
        found_host = repo.get_host_by_ip(first_host.ip)
        assert found_host is not None
        assert found_host.ip == first_host.ip


def test_cert_by_fingerprint(repo):
    """Test getting certificate by fingerprint."""
    certs = repo.get_all_certificates()
    if certs:
        first_cert = certs[0]
        found_cert = repo.get_certificate_by_fingerprint(first_cert.fingerprint_sha256)
        assert found_cert is not None
        assert found_cert.fingerprint_sha256 == first_cert.fingerprint_sha256
