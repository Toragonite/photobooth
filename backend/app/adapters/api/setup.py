"""Setup API endpoints for certificate installation."""

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(prefix="/setup", tags=["setup"])

# Certificate file path - can be overridden by environment variable
CERT_PATH = os.environ.get(
    "ROOT_CA_PATH",
    "/app/certs/rootCA.pem"
)

# Fallback paths for development
DEV_CERT_PATHS = [
    Path(__file__).parent.parent.parent.parent.parent / "rootCA.pem",  # project root
    Path.home() / ".local/share/mkcert/rootCA.pem",  # mkcert default location
]


def find_certificate() -> Path | None:
    """Find the root CA certificate file."""
    # Check configured path first
    configured_path = Path(CERT_PATH)
    if configured_path.is_file():
        return configured_path

    # Try fallback paths for development
    for path in DEV_CERT_PATHS:
        if path.is_file():
            return path

    return None


@router.get("/certificate")
async def download_certificate():
    """Download the root CA certificate for HTTPS trust.

    This certificate must be installed on client devices to trust
    the self-signed HTTPS certificate used by the photobooth.
    """
    cert_path = find_certificate()

    if cert_path is None:
        raise HTTPException(
            status_code=404,
            detail="Root CA certificate not found. Please contact administrator."
        )

    return FileResponse(
        path=str(cert_path),
        filename="rootCA.pem",
        media_type="application/x-pem-file",
        headers={
            "Content-Disposition": "attachment; filename=rootCA.pem"
        }
    )


@router.get("/certificate/info")
async def certificate_info():
    """Get information about the certificate availability."""
    cert_path = find_certificate()

    if cert_path is None:
        return {
            "available": False,
            "message": "Certificate not found"
        }

    return {
        "available": True,
        "filename": "rootCA.pem",
        "size": cert_path.stat().st_size
    }
