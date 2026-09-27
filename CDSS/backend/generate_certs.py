"""
generate_certs.py — Generate self-signed SSL certificate for CDSS development.
Run once: python generate_certs.py
Outputs: cert.pem, key.pem  (in the same directory)

For production, replace with certificates from Let's Encrypt or your CA.
"""

import os
import datetime
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

CERT_FILE = os.path.join(os.path.dirname(__file__), "cert.pem")
KEY_FILE  = os.path.join(os.path.dirname(__file__), "key.pem")


def generate():
    print("Generating RSA-4096 private key...")
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,
    )

    print("Building self-signed certificate (valid 365 days)...")
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME,            "IN"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME,  "Maharashtra"),
        x509.NameAttribute(NameOID.LOCALITY_NAME,           "Mumbai"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME,       "CDSS Clinical System"),
        x509.NameAttribute(NameOID.COMMON_NAME,             "localhost"),
    ])

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
        .add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.IPAddress(__import__("ipaddress").IPv4Address("127.0.0.1")),
            ]),
            critical=False,
        )
        .sign(private_key, hashes.SHA256())
    )

    # Write private key
    with open(KEY_FILE, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))

    # Write certificate
    with open(CERT_FILE, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    print(f"Certificate -> {CERT_FILE}")
    print(f"Private Key -> {KEY_FILE}")
    print("\nIMPORTANT: Your browser will show a security warning.")
    print("Click 'Advanced' -> 'Proceed to localhost (unsafe)' to continue.")
    print("For production, replace with a CA-signed certificate (Let's Encrypt).")


if __name__ == "__main__":
    generate()
