"""
Dataset repository for loading and querying host and certificate data.
Follows the same repository pattern as the conversation repository.
"""

from __future__ import annotations

import json
import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)


# Nested models for structured data
class Location(BaseModel):
    city: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = None


class AutonomousSystem(BaseModel):
    asn: int
    name: str
    country_code: Optional[str] = None


class DNS(BaseModel):
    hostname: Optional[str] = None


class OperatingSystem(BaseModel):
    vendor: Optional[str] = None
    product: Optional[str] = None


class Vulnerability(BaseModel):
    cve_id: str
    severity: str
    cvss_score: float
    description: Optional[str] = None


class Software(BaseModel):
    product: str
    vendor: Optional[str] = None
    version: Optional[str] = None


class Certificate(BaseModel):
    fingerprint_sha256: str
    subject: Optional[str] = None
    issuer: Optional[str] = None
    self_signed: Optional[bool] = None


class MalwareDetection(BaseModel):
    name: str
    type: str
    confidence: float
    threat_actors: List[str] = []


class Service(BaseModel):
    port: int
    protocol: str
    banner: Optional[str] = None
    software: List[Software] = []
    vulnerabilities: List[Vulnerability] = []
    tls_enabled: Optional[bool] = None
    certificate: Optional[Certificate] = None
    malware_detected: Optional[MalwareDetection] = None
    authentication_required: Optional[bool] = None
    access_restricted: Optional[bool] = None
    error_message: Optional[str] = None
    response_details: Optional[Dict[str, Any]] = None


class ThreatIntelligence(BaseModel):
    security_labels: List[str] = []
    malware_families: List[str] = []
    risk_level: Optional[str] = None  # Make optional to handle missing data
    organization_mismatch: Optional[bool] = None
    suspicious_patterns: List[str] = []


class HostRecord(BaseModel):
    """Represents a host record from the dataset."""

    ip: str
    location: Optional[Location] = None
    autonomous_system: Optional[AutonomousSystem] = None
    dns: Optional[DNS] = None
    operating_system: Optional[OperatingSystem] = None
    services: List[Service] = []
    threat_intelligence: Optional[ThreatIntelligence] = None


# Certificate-specific nested models
class CertificateSubject(BaseModel):
    common_name: Optional[str] = None
    organization: Optional[str] = None
    country: Optional[str] = None


class CertificateIssuer(BaseModel):
    common_name: str
    organization: str
    country: str


class ValidityPeriod(BaseModel):
    not_before: str
    not_after: str
    length_days: int
    status: str


class KeyInfo(BaseModel):
    algorithm: str
    key_size: int
    public_key_fingerprint: str


class CertificateAuthority(BaseModel):
    name: str
    type: str
    validation_level: str


class CertificateTransparency(BaseModel):
    logs_count: int
    first_seen: Optional[str] = None
    logs: List[str] = []


class Validation(BaseModel):
    trusted_by_major_browsers: bool
    validation_paths: Dict[str, bool] = {}
    expiry_status: Optional[str] = None
    validation_issues: Optional[str] = None


class Revocation(BaseModel):
    crl_revoked: bool
    ocsp_revoked: bool


class SecurityAnalysis(BaseModel):
    zlint_status: str
    failed_lints: List[str] = []
    risk_level: str
    notes: Optional[str] = None


class UsageIndicators(BaseModel):
    ever_seen_in_scan: bool
    last_seen: str


class CertificateRecord(BaseModel):
    """Represents a certificate record from the dataset."""

    fingerprint_sha256: str
    fingerprint_sha1: Optional[str] = None
    fingerprint_md5: Optional[str] = None
    domains: List[str] = []
    subject: Optional[CertificateSubject] = None
    issuer: Optional[CertificateIssuer] = None
    validity_period: Optional[ValidityPeriod] = None
    key_info: Optional[KeyInfo] = None
    certificate_authority: Optional[CertificateAuthority] = None
    certificate_transparency: Optional[CertificateTransparency] = None
    validation: Optional[Validation] = None
    revocation: Optional[Revocation] = None
    security_analysis: Optional[SecurityAnalysis] = None
    threat_intelligence: Optional[ThreatIntelligence] = None
    usage_indicators: Optional[UsageIndicators] = None


class DatasetMetadata(BaseModel):
    """Metadata about a dataset."""

    description: str
    created_at: str
    data_sources: List[str]
    hosts_count: Optional[int] = None
    certificates_count: Optional[int] = None


class DatasetRepository(ABC):
    """Abstract base class for dataset access."""

    @abstractmethod
    def get_all_hosts(self) -> List[HostRecord]:
        """Get all hosts for parallel distribution."""
        pass

    @abstractmethod
    def get_host_by_ip(self, ip: str) -> Optional[HostRecord]:
        """Get specific host by IP (primary axis)."""
        pass

    @abstractmethod
    def get_all_certificates(self) -> List[CertificateRecord]:
        """Get all certificates for parallel distribution."""
        pass

    @abstractmethod
    def get_certificate_by_fingerprint(self, fingerprint: str) -> Optional[CertificateRecord]:
        """Get specific certificate by fingerprint (primary axis)."""
        pass


class FileBasedDatasetRepository(DatasetRepository):
    """File-based implementation that loads JSON datasets from disk."""

    def __init__(self, hosts_file: Path, certificates_file: Path):
        self.hosts_file = hosts_file
        self.certificates_file = certificates_file
        self._hosts_data: Optional[Dict[str, Any]] = None
        self._certificates_data: Optional[Dict[str, Any]] = None
        self._hosts_records: Optional[List[HostRecord]] = None
        self._certificates_records: Optional[List[CertificateRecord]] = None

    def _load_hosts_data(self) -> Dict[str, Any]:
        """Load hosts data from JSON file."""
        if self._hosts_data is None:
            try:
                if self.hosts_file.exists():
                    with open(self.hosts_file, "r") as f:
                        self._hosts_data = json.load(f)
                        logger.info(f"Loaded hosts dataset from {self.hosts_file}")
                else:
                    logger.warning(f"Hosts dataset file not found: {self.hosts_file}")
                    self._hosts_data = {"metadata": {}, "hosts": []}
            except Exception as e:
                logger.error(f"Error loading hosts dataset: {e}")
                self._hosts_data = {"metadata": {}, "hosts": []}
        return self._hosts_data

    def _load_certificates_data(self) -> Dict[str, Any]:
        """Load certificates data from JSON file."""
        if self._certificates_data is None:
            try:
                if self.certificates_file.exists():
                    with open(self.certificates_file, "r") as f:
                        self._certificates_data = json.load(f)
                        logger.info(f"Loaded certificates dataset from {self.certificates_file}")
                else:
                    logger.warning(f"Certificates dataset file not found: {self.certificates_file}")
                    self._certificates_data = {"metadata": {}, "certificates": []}
            except Exception as e:
                logger.error(f"Error loading certificates dataset: {e}")
                self._certificates_data = {"metadata": {}, "certificates": []}
        return self._certificates_data

    def get_all_hosts(self) -> List[HostRecord]:
        """Get all hosts for parallel distribution."""
        if self._hosts_records is None:
            data = self._load_hosts_data()
            self._hosts_records = [HostRecord(**host) for host in data.get("hosts", [])]
        return self._hosts_records

    def get_host_by_ip(self, ip: str) -> Optional[HostRecord]:
        """Get specific host by IP (primary axis)."""
        hosts = self.get_all_hosts()
        for host in hosts:
            if host.ip == ip:
                return host
        return None

    def get_all_certificates(self) -> List[CertificateRecord]:
        """Get all certificates for parallel distribution."""
        if self._certificates_records is None:
            data = self._load_certificates_data()
            self._certificates_records = [CertificateRecord(**cert) for cert in data.get("certificates", [])]
        return self._certificates_records

    def get_certificate_by_fingerprint(self, fingerprint: str) -> Optional[CertificateRecord]:
        """Get specific certificate by fingerprint (primary axis)."""
        certificates = self.get_all_certificates()
        for cert in certificates:
            if cert.fingerprint_sha256 == fingerprint:
                return cert
        return None


class MockDatasetRepository(DatasetRepository):
    """Mock implementation for testing."""

    def __init__(self):
        self._mock_hosts = [
            HostRecord(
                ip="192.168.1.1",
                location={"city": "Test City", "country": "Test Country", "country_code": "TC"},
                services=[{"port": 80, "protocol": "HTTP"}],
            )
        ]
        self._mock_certificates = [CertificateRecord(fingerprint_sha256="test123", domains=["test.example.com"])]

    async def get_hosts(self, limit: Optional[int] = None) -> List[HostRecord]:
        hosts = self._mock_hosts
        if limit:
            hosts = hosts[:limit]
        return hosts

    async def get_host_by_ip(self, ip: str) -> Optional[HostRecord]:
        for host in self._mock_hosts:
            if host.ip == ip:
                return host
        return None

    async def get_certificates(self, limit: Optional[int] = None) -> List[CertificateRecord]:
        certificates = self._mock_certificates
        if limit:
            certificates = certificates[:limit]
        return certificates

    async def get_certificate_by_fingerprint(self, fingerprint: str) -> Optional[CertificateRecord]:
        for cert in self._mock_certificates:
            if cert.fingerprint_sha256 == fingerprint:
                return cert
        return None

    async def search_hosts_by_location(
        self, country: Optional[str] = None, city: Optional[str] = None
    ) -> List[HostRecord]:
        return self._mock_hosts

    async def search_certificates_by_domain(self, domain: str) -> List[CertificateRecord]:
        return self._mock_certificates

    async def get_hosts_metadata(self) -> Optional[DatasetMetadata]:
        return DatasetMetadata(
            description="Mock dataset for testing",
            created_at="2025-01-01",
            data_sources=["mock"],
            hosts_count=len(self._mock_hosts),
        )

    async def get_certificates_metadata(self) -> Optional[DatasetMetadata]:
        return DatasetMetadata(
            description="Mock dataset for testing",
            created_at="2025-01-01",
            data_sources=["mock"],
            certificates_count=len(self._mock_certificates),
        )


# Global repository instance
_dataset_repository: Optional[DatasetRepository] = None


def get_dataset_repository() -> DatasetRepository:
    """Get the current dataset repository instance."""
    global _dataset_repository
    if _dataset_repository is None:
        # Determine which implementation to use based on environment
        use_mock = os.getenv("USE_MOCK_DATASETS", "false").lower() == "true"

        if use_mock:
            _dataset_repository = MockDatasetRepository()
            logger.info("Using mock dataset repository")
        else:
            # Get paths from environment or use defaults
            backend_dir = Path(__file__).parent.parent
            hosts_file = Path(os.getenv("HOSTS_DATASET_PATH", str(backend_dir / "dataset" / "hosts_dataset.json")))
            certificates_file = Path(
                os.getenv("CERTIFICATES_DATASET_PATH", str(backend_dir / "dataset" / "web_properties_dataset.json"))
            )

            _dataset_repository = FileBasedDatasetRepository(hosts_file, certificates_file)
            logger.info(f"Using file-based dataset repository: hosts={hosts_file}, certificates={certificates_file}")

    return _dataset_repository


def set_dataset_repository(repo: DatasetRepository) -> None:
    """Set the dataset repository implementation (for testing)."""
    global _dataset_repository
    _dataset_repository = repo
