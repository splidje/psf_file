import os
import struct

class PSFType(object):
    _serialised = None

    @staticmethod
    def create(val):
        if isinstance(val, (str, unicode)):
            return PSFString(val)
        elif isinstance(val, int):
            return PSFInt(val)
        raise ValueError("Don't know how to convert a {}".format(type(val)))

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

# ICC file content
class PSFProfile(PSFType):
    TYPE_STRING = "prof"

    def __init__(self, data):
        self.data = data
        self._serialised = None

    def serialise(self):
        if isinstance(self.data, file):
            return self.data.read()
        elif os.path.exists(self.data) and os.path.isfile(self.data):
            return open(self.data, "rb").read()
        return data

class PSFFile:
    UNKNOWN_DATA = '\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x07\xe2\x00\x03\x00\x14\x00\x11\x00\n\x00\x03AsPs\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x07'

    def __init__(
        self,
        profile="",
        name="Untitled", writer_name="Adobe Photoshop 6.0",
        intent=1, simulate="papW", kpc=1, proof_type="conv",
    ):
        self.properties = (
            ("name", PSFString(name)),
            ("wNam", PSFString(writer_name)),
            ("cInt", PSFInt(intent)),
            ("dSim", PSFInt(simulate)),
            ("kpc ", PSFInt(kpc)),
            ("pTyp", PSFInt(proof_type)),
            ("pPrf", PSFProfile(profile)),
        )

    def save(self, file_path):
        f = open(file_path, "wb")

        f.write("\x00" * 4) # placeholder for file size

        # write data we don't yet understand
        f.write(self.UNKNOWN_DATA)

        # calc length of property header
        cur_pos = f.tell()
        next_val_pos = cur_pos + len(self.properties) * 12

        fills = []

        # write property declarations in order
        for k, v in self.properties:
            f.write(k)
            val_len = len(v.serialised)
            f.write(struct.pack(">II", next_val_pos, val_len))
            next_val_pos += val_len

            # make it up to factor of 4
            fill = 0
            remainder = val_len % 4
            if remainder:
                fill = 4 - remainder
                next_val_pos += fill
            fills.append(fill)

        # write vals in same order
        for i, (k, v) in enumerate(self.properties):
            f.write(v.serialised)
            if fills[i]:
                f.write("\x00" * fills[i])

        # write size to beginning
        size = f.tell()
        f.seek(0)
        f.write(struct.pack(">I", size))

        f.close()

