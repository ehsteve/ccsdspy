"""Optional Cython helpers for variable-length decoding."""


def get_packet_starts(const unsigned char[:] file_bytes):
    cdef Py_ssize_t nbytes = file_bytes.shape[0]
    cdef Py_ssize_t offset = 0
    cdef list packet_starts = []

    while offset < nbytes:
        packet_starts.append(offset)
        offset += file_bytes[offset + 4] * 256 + file_bytes[offset + 5] + 7

    return packet_starts, offset
