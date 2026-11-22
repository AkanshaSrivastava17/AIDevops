"""
Unit and Integration Tests for Universal Polyglot AST Adapter (Tree-sitter).
Tests parsing, AST chunking, and dependency extraction across Python, JS, TS, Go, and Java.
"""
import pytest
from app.ingestion.universal_adapter import UniversalASTAdapter
from app.ingestion.python_adapter import PythonASTAdapter
from app.ingestion.schema import DocumentType, EventType


@pytest.fixture
def adapter():
    return UniversalASTAdapter(
        candidate_components=["dcim", "ipam", "circuits", "users", "auth"]
    )


def test_is_supported_file(adapter):
    assert adapter.is_supported_file("models.py") is True
    assert adapter.is_supported_file("App.tsx") is True
    assert adapter.is_supported_file("service.js") is True
    assert adapter.is_supported_file("main.go") is True
    assert adapter.is_supported_file("DeviceService.java") is True
    assert adapter.is_supported_file("readme.txt") is False
    assert adapter.is_supported_file("image.png") is False


def test_parse_python(adapter):
    code = """
import os
from netbox.dcim import models

def calculate_ip(prefix, vrf):
    \"\"\"Assigns IP.\"\"\"
    return f"{prefix}-{vrf}"

class DeviceManager:
    def sync(self):
        pass
"""
    chunks, deps = adapter.parse_file("netbox/ipam/service.py", code, "netbox", "2026-11-22T00:00:00Z")
    assert len(chunks) >= 2
    symbol_names = [c.metadata["symbol_name"] for c in chunks]
    assert "calculate_ip" in symbol_names
    assert "DeviceManager" in symbol_names

    # Check dependency link extracted
    dep_targets = [d.target_component for d in deps]
    assert "dcim" in dep_targets


def test_parse_javascript(adapter):
    code = """
import { Device } from './dcim';
import auth from '../auth/service';

function processDevice(dev) {
    return dev.id;
}

class ClusterService {
    deploy() {}
}
"""
    chunks, deps = adapter.parse_file("src/ui/cluster.js", code, "frontend", "2026-11-22T00:00:00Z")
    assert len(chunks) >= 2
    symbol_names = [c.metadata["symbol_name"] for c in chunks]
    assert "processDevice" in symbol_names
    assert "ClusterService" in symbol_names

    dep_targets = [d.target_component for d in deps]
    assert "dcim" in dep_targets or "auth" in dep_targets


def test_parse_typescript(adapter):
    code = """
import { Circuit } from '../circuits/types';

interface NetworkProps {
    id: string;
}

export function provision(props: NetworkProps): boolean {
    return true;
}
"""
    chunks, deps = adapter.parse_file("src/network.ts", code, "frontend", "2026-11-22T00:00:00Z")
    assert len(chunks) >= 1
    symbol_names = [c.metadata["symbol_name"] for c in chunks]
    assert "provision" in symbol_names or "NetworkProps" in symbol_names

    dep_targets = [d.target_component for d in deps]
    assert "circuits" in dep_targets


def test_parse_go(adapter):
    code = """
package main

import (
    "fmt"
    "github.com/netbox/ipam"
)

func AllocatePrefix(p string) string {
    return p
}

type RouterManager struct {
    Name string
}
"""
    chunks, deps = adapter.parse_file("pkg/router.go", code, "backend", "2026-11-22T00:00:00Z")
    assert len(chunks) >= 2
    symbol_names = [c.metadata["symbol_name"] for c in chunks]
    assert "AllocatePrefix" in symbol_names
    assert "RouterManager" in symbol_names

    dep_targets = [d.target_component for d in deps]
    assert "ipam" in dep_targets


def test_parse_java(adapter):
    code = """
package com.netbox.circuits;

import com.netbox.dcim.Device;
import java.util.List;

public class CircuitManager {
    public void provisionCircuit() {
        System.out.println("ok");
    }
}
"""
    chunks, deps = adapter.parse_file("src/main/java/CircuitManager.java", code, "backend", "2026-11-22T00:00:00Z")
    assert len(chunks) >= 1
    symbol_names = [c.metadata["symbol_name"] for c in chunks]
    assert "CircuitManager" in symbol_names or "provisionCircuit" in symbol_names

    dep_targets = [d.target_component for d in deps]
    assert "dcim" in dep_targets


def test_python_ast_adapter_backwards_compatible():
    legacy_adapter = PythonASTAdapter(candidate_components=["dcim"])
    code = "def legacy_func():\n    return 42\n"
    chunks, deps = legacy_adapter.parse_file("legacy.py", code, "repo", "now")
    assert len(chunks) == 1
    assert chunks[0].metadata["symbol_name"] == "legacy_func"
