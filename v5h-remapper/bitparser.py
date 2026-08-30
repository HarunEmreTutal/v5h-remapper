class BitParser:
    def __init__(self, lengths):
        self._lengths = lengths

    def parse(self, data) -> dict[str, int]:
        raw_data = int.from_bytes(data, byteorder="little")
        result = {}
        offset = 0
        for usage, rsize in self._lengths:
            mask = self.get_bitmask(rsize, offset)
            value = (raw_data & mask) >> offset
            result[usage] = value
            offset += rsize
        return result

    @staticmethod
    def get_bitmask(bit_count, offset=0) -> int:
        return (2**bit_count - 1) << offset
