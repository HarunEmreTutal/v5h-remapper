class BitParser:
    def __init__(self, lengths):
        self._lengths = lengths

    def parse(self, data) -> list[int]:
        raw_data = int.from_bytes(data, byteorder="little")
        result = []
        offset = 0
        for l in self._lengths:
            mask = self.get_bitmask(l, offset)
            value = (raw_data & mask) >> offset
            result.append(value)
            offset += l
        return result

    @staticmethod
    def get_bitmask(bit_count, offset=0) -> int:
        return (2**bit_count - 1) << offset
