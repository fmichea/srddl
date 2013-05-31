import srddl.data as sd
import srddl.fields as sf
import srddl.helpers as sh
import srddl.models as sm

class PcapFileHeader(sm.Struct):
  magic = sf.IntField('magic', size=4)
  version_major = sf.IntField('', size=2)
  version_minor = sf.IntField('', size=2)
  thiszone = sf.IntField('gmt to local correction', size=4)
  sigfigs = sf.IntField('accuracy of timestamps', size=4)
  snaplen = sf.IntField('max length saved portion for each pkt', size=4)
  linktype = sf.IntField('data link type (LINKTYPE_*)', size=4)

class Timeval(sm.Struct):
  tv_sec = sf.IntField('', size=4)
  tv_usec = sf.IntField('', size=4)

class PcapPkthdr(sm.Struct):
  ts = sf.SuperField(Timeval)
  caplen = sf.IntField('length of portion present', size=4)
  length = sf.IntField('length this packet (off wire)', size=4)

class PcapPacket(sm.Struct):
  pkthdr = sf.SuperField(PcapPkthdr)
  payload = sf.ByteArrayField(lambda strct : strct.pkthdr.caplen)

class Pcap(sm.FileType):
    '''Packet Capture File'''

    class Meta:
        author = ''
        author_email = ''
        extensions = ''

    def check(self, data):
        return data.unpack_from('4s', 0)[0] == bytes.fromhex('d4c3b2a1')

    def setup(self, data):
        header = data.map(0, PcapFileHeader)
        data.map_fill_array(header['size'], -1, PcapPacket)
