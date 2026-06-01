"""UUID v7 generator — time-ordered IDs.

UUID v7 (RFC 9562 §5.7) encodes a 48-bit Unix-millis timestamp in the high
bits, giving us:
- B-tree-friendly inserts (sorted by time, no page-split storms)
- No count leakage (unlike serial IDs)
- Cross-system safe (collision-resistant random suffix)

When Python 3.14 lands `uuid.uuid7()` in stdlib, drop this module and import
from there. Until then, this is a minimal pure-stdlib implementation.
"""

from __future__ import annotations

import os
import time
from uuid import UUID


def uuid7() -> UUID:
    """Generate a UUID version 7 (time-ordered)."""
    timestamp_ms = int(time.time() * 1000) & 0xFFFFFFFFFFFF  # 48 bits
    rand_a = int.from_bytes(os.urandom(2), "big") & 0x0FFF  # 12 bits
    rand_b = int.from_bytes(os.urandom(8), "big") & 0x3FFFFFFFFFFFFFFF  # 62 bits

    uuid_int = (
        (timestamp_ms << 80)
        | (0x7 << 76)  # version 7
        | (rand_a << 64)
        | (0b10 << 62)  # RFC 9562 variant
        | rand_b
    )
    return UUID(int=uuid_int)
