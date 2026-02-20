import os

import numpy as np

from .. import decode


def test_packet_start_scanner_matches_python_reference():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    bin_path = os.path.join(dir_path, "data", "var_length", "var_length_packets.bin")
    file_bytes = np.fromfile(bin_path, "u1")

    starts_ref, offset_ref = decode._get_packet_starts_python(file_bytes)
    starts_actual, offset_actual = decode._get_packet_starts(file_bytes)

    assert starts_actual == starts_ref
    assert offset_actual == offset_ref


def test_packet_start_scanner_prefers_cython_when_available(monkeypatch):
    file_bytes = np.arange(16, dtype="u1")

    called = {"value": False}

    def _fake_cython(arr):
        called["value"] = True
        return [1, 2, 3], 123

    monkeypatch.setattr(decode, "_load_cython_packet_starts", lambda: _fake_cython)

    starts, offset = decode._get_packet_starts(file_bytes)

    assert called["value"] is True
    assert starts == [1, 2, 3]
    assert offset == 123


def test_byte_aligned_fast_path_matches_unaligned():
    """Verify byte-aligned fast path produces equivalent results to unaligned path."""
    dir_path = os.path.dirname(os.path.realpath(__file__))
    bin_path = os.path.join(dir_path, "data", "var_length", "var_length_packets_with_footer.bin")

    from .. import VariableLength, PacketField, PacketArray

    pkt = VariableLength(
        [
            PacketArray(
                name="data",
                data_type="uint",
                bit_length=16,
                array_shape="expand",
            ),
            PacketField(name="footer", data_type="uint", bit_length=16),
        ]
    )

    field_arrays = pkt.load(bin_path, include_primary_header=False)
    assert np.all(field_arrays["footer"] == 1)

