"""Tests for F3 — Certificate persistence wiring of inquiry_class.

Verifies: TheatreCertificate column configuration and theatre_bridge
wiring logic at the source level.
"""
from __future__ import annotations

import ast


class TestCertificateInquiryPersistence:
    """Verify TheatreCertificate inquiry_class wiring in theatre_bridge.py."""

    def test_theatre_bridge_reads_inquiry_class_from_theatre(self) -> None:
        """theatre_bridge.py extracts inquiry_class from theatre record."""
        with open("backend/services/theatre_bridge.py") as f:
            source = f.read()
        # Verify inquiry_class is extracted from theatre
        assert 'inquiry_class = theatre.inquiry_class or "COUNTERFACTUAL"' in source

    def test_theatre_bridge_passes_inquiry_class_to_certificate(self) -> None:
        """theatre_bridge.py passes inquiry_class to TheatreCertificate constructor."""
        with open("backend/services/theatre_bridge.py") as f:
            source = f.read()
        assert "inquiry_class=inquiry_class," in source

    def test_model_column_has_server_default(self) -> None:
        """models.py TheatreCertificate inquiry_class has server_default."""
        with open("backend/database/models.py") as f:
            source = f.read()
        # Find the TheatreCertificate section (multi-line column definition)
        cert_start = source.index("class TheatreCertificate")
        # Find next class definition after TheatreCertificate
        next_class = source.index("\nclass ", cert_start + 1)
        cert_section = source[cert_start:next_class]
        assert "inquiry_class" in cert_section
        assert 'server_default="COUNTERFACTUAL"' in cert_section
