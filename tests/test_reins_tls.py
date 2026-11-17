"""REINS CA-chain recovery must never accept unverified market payloads."""
import pytest
import requests
from src import reins_tls

class Session:
    def __init__(self,initial_failure=True):
        self.calls=[]
        self.initial_failure=initial_failure
    def get(self,url,**kwargs):
        self.calls.append((url,kwargs))
        if self.initial_failure and len(self.calls)==1:
            raise requests.exceptions.SSLError("missing intermediate")
        return object()

def test_normal_verified_requests_uses_default_certificate_verification():
    s=Session(initial_failure=False)
    reins_tls._CACHE.clear()
    reins_tls.verified_reins_get(s,"https://www.reins.or.jp/library/2026.html",timeout=5)
    assert s.calls==[("https://www.reins.or.jp/library/2026.html",{"timeout":5})]

def test_missing_intermediate_is_retried_only_with_validated_ca_bundle(monkeypatch):
    s=Session()
    reins_tls._CACHE.clear()
    monkeypatch.setattr(reins_tls,"_verified_bundle",lambda host:"/tmp/verified_ca_bundle.pem")
    reins_tls.verified_reins_get(s,"https://www.reins.or.jp/library/2026.html",timeout=5)
    assert len(s.calls)==2
    assert s.calls[-1][1]["verify"]=="/tmp/verified_ca_bundle.pem"
    assert all(call[1].get("verify") is not False for call in s.calls)

def test_invalid_ca_chain_does_not_download_market_data(monkeypatch):
    s=Session()
    reins_tls._CACHE.clear()
    def refuse(host):
        raise requests.exceptions.SSLError("issuer not rooted")
    monkeypatch.setattr(reins_tls,"_verified_bundle",refuse)
    with pytest.raises(requests.exceptions.SSLError):
        reins_tls.verified_reins_get(s,"https://www.reins.or.jp/library/2026.html")
    assert len(s.calls)==1

def test_disallow_nonofficial_hosts_even_when_https():
    with pytest.raises(ValueError):
        reins_tls.verified_reins_get(Session(False),"https://example.net/library/2026.html")
    with pytest.raises(ValueError):
        reins_tls.verified_reins_get(Session(False),"http://www.reins.or.jp/library/2026.html")
