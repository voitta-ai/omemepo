"""Secret redaction for omemepo profile packing.

Schema-based blacklist: redact JSON object values whose KEY name contains
any blacklisted substring (case-insensitive). Default-allow.
"""

import json


DEFAULT_BLACKLIST = ("token", "secret", "password", "passwd")

REDACTED = "<redacted>"


def _key_blacklisted(key: str, blacklist) -> bool:
    lower = key.lower()
    for pat in blacklist:
        if pat.lower() in lower:
            retval = True
            return retval
    retval = False
    return retval


def _walk(node, blacklist):
    if isinstance(node, dict):
        out = {}
        for k, v in node.items():
            if isinstance(k, str) and _key_blacklisted(k, blacklist):
                out[k] = REDACTED
            else:
                out[k] = _walk(v, blacklist)
        retval = out
        return retval
    if isinstance(node, list):
        items = [_walk(x, blacklist) for x in node]
        retval = items
        return retval
    retval = node
    return retval


def redact_json(data, blacklist=DEFAULT_BLACKLIST):
    """Return a deep-copied tree with blacklisted-key values replaced."""
    retval = _walk(data, blacklist)
    return retval


def redact_text(text: str, blacklist=DEFAULT_BLACKLIST) -> str:
    """Parse a JSON document, redact, re-serialize. Preserves indent=2."""
    parsed = json.loads(text)
    redacted = redact_json(parsed, blacklist)
    retval = json.dumps(redacted, indent=2) + "\n"
    return retval
