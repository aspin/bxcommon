from enum import Flag


class StatEventLogicFlags(Flag):
    NONE = 0
    BLOCK_INFO = 1
    MATCH = 2
    SUMMARY = 4

    def __str__(self):
        return str(self.value)

