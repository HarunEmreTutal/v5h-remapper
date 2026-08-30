import sys, enum
from math import floor

import pyvjoy
import pyvjoy.exceptions as pyvjoyexc
from v5h import SnopyV5H
from utils import (
    invert_axis,
    normalize_axis,
    split_centered_axis
)


HANDBRAKE_TRESHOLD: int = 0.25

# [Target Device]
VJOY_DEVICE_ID: int = 1
VJOY_MAX_AXIS_VALUE: int = 32767


class BrakeState(enum.Enum):
    NO_INPUT = enum.auto()
    HANDBRAKE = enum.auto()
    BRAKE_PEDAL = enum.auto()


class V5HRemapper:
    def __init__(self):
        self.brake_state = BrakeState.NO_INPUT
        self.last_backward = 0


        self.v5h = SnopyV5H()

        ## Define Target Virtual Device
        try:
            self.vdevice = pyvjoy.VJoyDevice(VJOY_DEVICE_ID)
        except pyvjoyexc.vJoyFailedToAcquireException:
            print("Sanal cihaz kullanılabilir değil.")
            sys.exit(1)

    def step(self):
        self.v5h.update()

        ## X Axis Routing
        x_axis = self.v5h["X_AXIS"]
        x_axis = normalize_axis(x_axis, 255)  # !FIX: Magic Number
        _x = floor(VJOY_MAX_AXIS_VALUE * x_axis)
        self.vdevice.set_axis(pyvjoy.HID_USAGE_X, _x)

        ## Y Axis Routing
        y_axis = self.v5h["Y_AXIS"]
        y_axis = normalize_axis(y_axis, 255)  # !FIX: Magic Number
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
        dpad = self.v5h["DPAD"]
        if 0 <= dpad <= 7:
            self.vdevice.set_cont_pov(1, dpad * 4500)
        else:
            self.vdevice.set_cont_pov(1, -1)

        buttons = self.v5h["BUTTONS"]
        for i in range(12):
            btn_index = 1 << i
            if buttons & btn_index:
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
