# This file is only here to help me gather ideas on what I want to have as an
# API from the point of view of the user (writer of a template). This is the
# minified version of ELF template, to serve as an example.

import srddl.helpers as sh
import srddl.fields as sf
import srddl.models as sm

# Atomic types.
class ElfN_Addr(sf.Field):
    @property
    def size(self):
        return self.root[0].e_indent.ei_class / 8

class ElfN_Off(ElfN_Addr): pass

# Structures
EI_INDENT = 16

class ElfN_Ehdr(sm.Struct):
    class ElfN_Ehdr__Indent(sm.Struct):
        ei_mag = sf.ByteArrayField('Magic', 4, valid=sh.equals(b'\x7fELF'))
        ei_class = sf.ByteField('Binary Architecture')
        ei_data = sf.ByteField('Data encoding (endianess)')
        ei_version = sf.ByteField('ELF specification number')
        ei_osabi = sf.ByteField('Operating system ABI')
        ei_abiversion = sf.ByteField('ABI Version')
        ei_pad = sf.Padding(EI_INDENT, mode=sf.PaddingMode.FILL)

    e_indent = sf.SuperField(ElfN_Ehdr__Indent)
    e_type = sf.Field('Object file type', size=2)
    e_machine = sf.Field('Machine architecture', size=2)
    e_version = sf.Field('File version', size=4)
    e_entry = ElfN_Addr('Entry point of the program')
    e_phoff = ElfN_Off('Program header table offset')
    e_shoff = ElfN_Off('Section header table offset')
    e_flags = sf.Field('Machine flags (unused)', size=4)
    e_ehsize = sf.Field('ELF Header size', size=2)
    e_phentsize = sf.Field('Program header entry size', size=2)
    e_phnum = sf.Field('Number of entries in program header table', size=2)
    e_shentsize = sf.Field('Section header entry size', size=2)
    e_shnum = sf.Field('Number of entrues in section heade table', size=2)
    e_shstrndx = sf.Field('Index of string table section header', size=2)
