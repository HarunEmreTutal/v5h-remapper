import hid
from bitparser import BitParser

class SnopyV5H:
    VENDOR_ID: int = 0x11ff
    PRODUCT_ID: int = 0x3331
    USAGES: tuple[tuple[str, int]] = (
        ("X_AXIS", 8),
        ("Y_AXIS", 8),
        ("Z_AXIS", 8),
        ("Z_AXIS2", 8),
        ("RX_AXIS", 8),
        ("DPAD", 4),
        ("BUTTONS", 12),
        ("VENDOR_USAGE", 8),
    )

    def __init__(self):
        self._device = hid.device()
        try:
            self._device.open(
                self.VENDOR_ID,
                self.PRODUCT_ID
            )
        except IOError:
            print("Cihaz Bulunamadı.")

        self._data_length = 0
        for _, i in self.USAGES:
            self._data_length += i
        self._data_length /= 8

        self._parser = BitParser(self.USAGES)
        self._parsed_data = {}

    def update(self) -> None:
        try:
            input_data = self._device.read(self._data_length)
        except IOError:
            print("Veri Alınamıyor.")

        self._parsed_data = self._parser.parse(input_data)

    def __getitem__(self, key) -> int:
        value = self._parsed_data.get(key)
        if value is None:
            # raise Exception()
            print("Böyle bir kullanım verisi yok.")
        return value

    def close(self) -> None:
        self._device.close()
