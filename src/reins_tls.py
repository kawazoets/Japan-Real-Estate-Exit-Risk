"""Trust-preserving REINS HTTPS recovery for an incomplete intermediate CA chain.

An unverified handshake inspects ONLY the public certificate's CA-Issuers URL.
Never accept HTTP market data from it. The full certificate must first validate
back to standard public roots with OpenSSL; then requests performs a fresh
hostname-verified TLS handshake. Do not introduce verify=False.
"""
from __future__ import annotations
import atexit
import os
import re
import socket
import ssl
import subprocess
import tempfile
from urllib.parse import urlparse
import certifi
import requests

_CACHE={}
_FILES=[]
_MAX_ISSUERS=3

def _run(args):
    return subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                          text=True,timeout=20,check=False)

def _tmp(data):
    with tempfile.NamedTemporaryFile(prefix="reins-ca-",suffix=".pem",delete=False) as f:
        f.write(data)
        path=f.name
    _FILES.append(path)
    return path

@atexit.register
def _cleanup():
    for path in _FILES:
        try:os.unlink(path)
        except OSError:pass

def _ca_issuer(pem):
    out=_run(["openssl","x509","-in",_tmp(pem),"-noout","-text"])
    if out.returncode:raise RuntimeError("Unable to inspect TLS certificate")
    match=re.search(r"CA Issuers\s*-\s*URI:(https?://[^\s,]+)",out.stdout)
    if not match:return None
    u=urlparse(match.group(1))
    if not u.hostname or u.username or u.password or u.port not in (None,80,443):
        raise ValueError("Invalid issuer URL")
    return match.group(1)

def _issuer_pem(url):
    # CA-issued certificate is PUBLIC metadata. Even if fetched using HTTP,
    # it is untrusted until OpenSSL verifies it up to certifi's trust anchors.
    response=requests.get(url,timeout=20,allow_redirects=False)
    response.raise_for_status()
    if len(response.content)>200000:raise ValueError("Issuer certificate too large")
    raw=_tmp(response.content)
    for form in ("DER","PEM"):
        out=_run(["openssl","x509","-inform",form,"-in",raw,"-outform","PEM"])
        if not out.returncode and "BEGIN CERTIFICATE" in out.stdout:
            return out.stdout.encode("ascii")
    raise ValueError("Not an X509 issuer certificate")

def _leaf(host):
    # CERT_NONE is used only to read public certificate bytes, never web data.
    context=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname=False
    context.verify_mode=ssl.CERT_NONE
    with socket.create_connection((host,443),timeout=20) as conn:
        with context.wrap_socket(conn,server_hostname=host) as tls:
            der=tls.getpeercert(binary_form=True)
    if not der:raise RuntimeError("Missing HTTPS leaf certificate")
    return ssl.DER_cert_to_PEM_cert(der).encode("ascii")

def _verified_bundle(host):
    if host in _CACHE:return _CACHE[host]
    leaf=_leaf(host)
    leaf_file=_tmp(leaf)
    current=leaf
    issuers=[]
    for _ in range(_MAX_ISSUERS):
        url=_ca_issuer(current)
        if url is None:break
        issuer=_issuer_pem(url)
        if issuer in issuers:break
        issuers.append(issuer)
        untrusted=_tmp(b"\n".join(issuers))
        # An untrusted intermediate MUST be certified by existing CA roots.
        checked=_run(["openssl","verify","-CAfile",certifi.where(),
                      "-untrusted",untrusted,leaf_file])
        if not checked.returncode:
            with open(certifi.where(),"rb") as f:roots=f.read()
            bundle=_tmp(roots+b"\n"+b"\n".join(issuers))
            _CACHE[host]=bundle
            return bundle
        current=issuer
    raise requests.exceptions.SSLError(
        "REINS chain could not be validated against standard public CA roots")

def verified_reins_get(session,url,**kwargs):
    p=urlparse(url)
    if p.scheme!="https" or p.hostname not in ("www.reins.or.jp","reins.or.jp"):
        raise ValueError("Not the official REINS HTTPS host")
    if p.hostname in _CACHE:
        return session.get(url,verify=_CACHE[p.hostname],**kwargs)
    try:
        return session.get(url,**kwargs)
    except requests.exceptions.SSLError:
        bundle=_verified_bundle(p.hostname)
        return session.get(url,verify=bundle,**kwargs)
