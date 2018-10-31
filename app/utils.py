import time


class AutoSwitch:
    """
    Switch which will automatically turn off

    >>> switch = AutoSwitch(1)
    >>> switch.value
    False
    >>> switch.on()
    >>> switch.value
    True
    >>> time.sleep(1)
    >>> switch.value
    False
    >>> switch.on()
    >>> switch.value
    True
    >>> switch.off()
    >>> switch.value
    False
    """
    def __init__(self, limit_sec: int):
        self._limit_sec = limit_sec  # switch will turn off automatically after this seconds
        self._value = False
        self._on_start_sec = 0.  # type: float

    @property
    def value(self) -> bool:
        if not self._value:
            return False

        # self._value == True
        if time.time() - self._on_start_sec > self._limit_sec:
            self._value = False
        return self._value

    @property
    def left_sec(self) -> int:
        if not self._value:
            return 0
        elapsed_sec = time.time() - self._on_start_sec
        left_sec = self._limit_sec - elapsed_sec
        return int(left_sec)

    def on(self) -> None:
        self._on_start_sec = time.time()
        self._value = True

    def off(self) -> None:
        self._value = False

