import sys
import enum
from math import floor

import hid
import pyvjoy
import pyvjoy.exceptions as pyvjoyexc


## :: Config ::
# [Source Device]
VENDOR_ID: int = 0x11ff
PRODUCT_ID: int = 0x3331

# TODO: Gelecek sürümlerde `Report Descriptor` ile cihaz veri paketi anatomisini çözeceğim.
# Şuan da `Report Descriptor` okuyarak, veri paketini ayrıştıramıyorum.
DATA_LENGTH: int = 8
X_AXIS_MAX: int = 255
Y_AXIS_MAX: int = 255

HANDBRAKE_TRESHOLD: int = 0.25

# [Target Device]
VJOY_DEVICE_ID: int = 1
VJOY_MAX_AXIS_VALUE: int = 32767
## :: Config End ::


def clamp(value, min_value, max_value) -> int | float:
    return min(
        max_value,
        max(min_value, value)
    )

def normalize_axis(value, max_value) -> float:
    return clamp(value / max_value, 0, 1)

def split_centered_axis(axis_value) -> tuple[int | float]:
    forward = ((1 - axis_value) - 0.5) * 2
    forward = clamp(forward, 0, 1)

    backward = (axis_value - 0.5) * 2
    backward = clamp(backward, 0, 1)
    return forward, backward

def invert_axis(axis_value):
    return clamp(1 - axis_value, 0, 1)


class BrakeState(enum.Enum):
    NO_INPUT = enum.auto()
    HANDBRAKE = enum.auto()
    BRAKE_PEDAL = enum.auto()


class V5HRemapper:
    def __init__(self):
        self.brake_state = BrakeState.NO_INPUT
        self.last_backward = 0

        ## Define Source Device
        self.v5h = hid.device()
        try:
            self.v5h.open(VENDOR_ID, PRODUCT_ID)
        except IOError:
            print("HID cihaz bağlı değil.")
            sys.exit(1)

        ## Define Target Virtual Device
        try:
            self.vdevice = pyvjoy.VJoyDevice(VJOY_DEVICE_ID)
        except pyvjoyexc.vJoyFailedToAcquireException:
            print("Sanal cihaz kullanılabilir değil.")
            sys.exit(1)

    def step(self):
        try:
            input_data = bytearray(self.v5h.read(DATA_LENGTH))
        except IOError:
            print("Cihaz bağlantısı koptu.")
            sys.exit(1)

        x_axis, y_axis, *_, main_buttons, extra_buttons, mode = input_data 

        ## X Axis Routing
        x_axis = normalize_axis(x_axis, X_AXIS_MAX)
        _x = floor(VJOY_MAX_AXIS_VALUE * x_axis)
        self.vdevice.set_axis(pyvjoy.HID_USAGE_X, _x)

        ## Y Axis Routing
        y_axis = normalize_axis(y_axis, Y_AXIS_MAX)
        if y_axis <= 0.5:
            _y = floor(VJOY_MAX_AXIS_VALUE * invert_axis(y_axis))
            self.vdevice.set_axis(pyvjoy.HID_USAGE_Y, _y)

        else:
            _, backward = split_centered_axis(y_axis)

            is_bw_full = backward == 1
            is_value_jumped = 1 - self.last_backward >= HANDBRAKE_TRESHOLD
            is_not_handbrake = self.brake_state != BrakeState.HANDBRAKE

            # Eksen değerinin değişikliklerini karşılaştır
            # Değer değişikliğine göre girdi tipini seç.
            if is_bw_full and is_value_jumped and is_not_handbrake:
                self.brake_state = BrakeState.HANDBRAKE
            elif 0.06 < backward < 1:
                self.brake_state = BrakeState.BRAKE_PEDAL
            elif backward < 0.06:
                self.brake_state = BrakeState.NO_INPUT

            # Duruma göre `HANDBRAKE` girdisini ayarla
            if self.brake_state == BrakeState.HANDBRAKE:
                self.vdevice.set_button(13, 1)
            else:
                self.vdevice.set_button(13, 0)

            # Duruma göre `BRAKE_PEDAL` girdisini ayarla
            if self.brake_state == BrakeState.BRAKE_PEDAL:
                _y = floor(VJOY_MAX_AXIS_VALUE * invert_axis(y_axis))
            else:
                _y = floor(VJOY_MAX_AXIS_VALUE * .5)
            self.vdevice.set_axis(pyvjoy.HID_USAGE_Y, _y)

            self.last_backward = backward
        ## Y Axis Routing End.

        ## Main Buttons and DPad Routing
        dpad = main_buttons & 0x0F
        buttons = (main_buttons >> 4) & 0x0F

        if 0 <= dpad <= 7:
            self.vdevice.set_cont_pov(1, dpad * 4500)
        else:
            self.vdevice.set_cont_pov(1, -1)

        # Buttons
        _buttons = buttons | (extra_buttons << 4)
        for i in range(12):
            btn_index = 1 << i
            if _buttons & btn_index:
                self.vdevice.set_button(i + 1, 1)
            else:
                self.vdevice.set_button(i + 1, 0)

    def _loop(self):
        while True:
            try:
                self.step()
            except (KeyboardInterrupt, SystemExit):
                break

    def stop(self):
        self.v5h.close()
        print("Program Sonlandırıldı.")
        sys.exit(0)

    def run(self):
        self._loop()
        self.stop()

if __name__ == "__main__":
    V5HRemapper().run()
