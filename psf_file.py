import struct

class PSFType:
    _serialised = None

    @property
    def serialised(self):
        if not self._serialised:
            self._serialised = "{:4.4}".format(self.TYPE_STRING) + "\x00"*4 + self.serialise()
        return self._serialised

class PSFInt(PSFType):
    TYPE_STRING = "ui32"

    def __init__(self, i):
        if isinstance(i, str):
            i = struct.unpack(">I", i)[0]
        self.int_ = i

    def serialise(self):
        return struct.pack(">I", self.int_)

class PSFString(PSFType):
    TYPE_STRING = "stri"

    def __init__(self, s):
        self.unicode_ = unicode(s)

    def serialise(self):
        asc = str(self.unicode_)
        return struct.pack(">II", len(asc) + 1, len(self.unicode_) + 1) + asc + "\x00" + self.unicode_.encode('utf-16_be') + "\x00"*2

class PSFProfile(PSFType):
    TYPE_STRING = "prof"

    def __init__(self, data):
        self.data = data
        self._serialised = None

    def serialise(self):
        return self.data

class PSFProfileDef:
    UNKNOWN_DATA = '\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x07\xe2\x00\x03\x00\x14\x00\x11\x00\n\x00\x03AsPs\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x07'

    def __init__(self, *args):
        self.properties = [
            ("{:4.4}".format(str(k)), self.py_to_psf(v)) for k, v in args
        ]

    @staticmethod
    def py_to_psf(val):
        if isinstance(val, (str, unicode)):
            return PSFString(val)
        elif isinstance(val, int):
            return PSFInt(val)
        return val

    def save(self, file_path):
        f = open(file_path, "wb")

        f.write("\x00" * 4) # placeholder for file size

        # write data we don't yet understand
        f.write(self.UNKNOWN_DATA)

        # calc length of property header
        cur_pos = f.tell()
        next_val_pos = cur_pos + len(self.properties) * 12

        # write property declarations in order
        for k, v in self.properties:
            f.write(k)
            val_len = len(v.serialised)
            f.write(struct.pack(">II", next_val_pos, val_len))
            next_val_pos += val_len

            # make it up to factor of 4
            rmndr = val_len % 4
            if rmndr:
                fill = 4 - rmndr
                f.write("\x00" * fill)
                next_val_pos += fill

        # write vals in same order
        for k, v in self.properties:
            f.write(v.serialised)

        # write size to beginning
        size = f.tell()
        f.seek(0)
        f.write(struct.pack(">I", size))

        f.close()

