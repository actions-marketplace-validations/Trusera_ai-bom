"""Scanner modules for AI-BOM detection.

Importing this package triggers auto-registration of all scanner classes
via the __init_subclass__ hook in BaseScanner.

Available scanners:
    - CodeScanner: Detects AI libraries and frameworks in source code
    - DockerScanner: Detects AI services in Docker/Kubernetes deployments
    - NetworkScanner: Detects AI endpoints and credentials in config files
    - CloudScanner: Detects AI services in Terraform, CloudFormation, etc.
    - N8nScanner: Detects AI components in n8n workflow automation
"""

from ai_bom.scanners.base import BaseScanner, get_all_scanners

# Import scanner modules to trigger registration via __init_subclass__
from ai_bom.scanners import (
    cloud_scanner,
    code_scanner,
    docker_scanner,
    n8n_scanner,
    network_scanner,
)

__all__ = ["BaseScanner", "get_all_scanners"]
