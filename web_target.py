import ipaddress
import re
from urllib.parse import urlsplit, urlunsplit


def normalize_url(value):
   
    value = value.strip()
    if not value or any(c.isspace() for c in value):
        raise ValueError("No Value or an space in your ip")
    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        pass
    else:
        if address.version == 6:
            value = f"[{address}]"
    parsed = urlsplit(value if "://" in value else "https://" + value)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("Only http/https allowed")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("No Usernames please in your ip")
    host = parsed.hostname
    try:
        address = ipaddress.ip_address(host)
        host = f"[{address}]" if address.version == 6 else str(address)
    except ValueError:
        host = host.encode("idna").decode("ascii").rstrip(".").lower()
        if len(host) > 253 or not all(
            re.fullmatch(r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?", label)
            for label in host.split(".")
        ):
            raise ValueError("Unknown Hostname")
    port = parsed.port  
    if port == 0 or parsed.netloc.endswith(":"):
        raise ValueError("Unknown Port")
    authority = f"{host}:{port}" if port is not None else host
    return urlunsplit((parsed.scheme, authority, parsed.path or "/", parsed.query, ""))


def dns_target(value):
    url = normalize_url(value)
    host = urlsplit(url).hostname
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return url, "CNAME", host
    return url, "A" if address.version == 4 else "AAAA", str(address)
