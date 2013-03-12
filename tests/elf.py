# This file only is here to help me gather what I want to have as an API from
# the point of view of the user (writer of a template).

import sys

import srddl.helpers as sh
import srddl.fields as sf
import srddl.models as sm

# Atomic types.
class ElfN_Addr(sf.IntField):
    def _isize(self, struct):
        return struct.e_indent.ei_class.value * 4

class ElfN_Off(ElfN_Addr): pass

# Structures
EI_INDENT = 16

class ElfN_Ehdr(sm.Struct):
    class ElfN_Ehdr__Indent(sm.Struct):
        ei_mag = sf.ByteArrayField(4, 'Magic', valid=sh.equals(b'\x7fELF'))

        ei_class = sf.IntField('Binary architecture', values=[
            sf.Value(0, 'ELFCLASSNONE', 'Invalid Class', valid=sh.invalid),
            sf.Value(1, 'ELFCLASS32', '32 bits architecture'),
            sf.Value(2, 'ELFCLASS64', '64 bits architecture'),
        ])

        ei_data = sf.IntField('Data encoding (endianess)', values=[
            sf.Value(0, 'ELFDATANONE', 'Unknown data format'),
            sf.Value(1, 'ELFDATA2LSB', 'Two\'s complement, little-endian'),
            sf.Value(2, 'ELFDATA2MSB', 'Two\'s complement, big-endian'),
        ])

        ei_version = sf.IntField('ELF specification number', values=[
            sf.Value(0, 'EV_NONE', 'Invalid version'),
            sf.Value(1, 'EV_CURRENT', 'Current version'),
        ])

        ei_osabi = sf.IntField('Operating system ABI', values=[
            sf.Value(0x0, 'ELFOSABI_NONE', 'Same as ELFOSABI_SYSV'),
            sf.Value(0x1, 'ELFOSABI_SYSV', 'UNIX System V ABI'),
            sf.Value(0x2, 'ELFOSABI_HPUX', 'HP-UX ABI'),
            sf.Value(0x3, 'ELFOSABI_NETBSD', 'NetBSD ABI'),
            sf.Value(0x4, 'ELFOSABI_LINUX', 'Linux ABI'),
            sf.Value(0x5, 'ELFOSABI_SOLARIS', 'Solaris ABI'),
            sf.Value(0x6, 'ELFOSABI_IRIX', 'IRIX ABI'),
            sf.Value(0x7, 'ELFOSABI_FREEBSD', 'FreeBSD ABI'),
            sf.Value(0x8, 'ELFOSABI_TRU64', 'TRU64 UNIX ABI'),
            sf.Value(0x9, 'ELFOSABI_ARM', 'ARM architecture ABI'),
            sf.Value(0xA, 'ELFOSABI_STANDALONE', 'Stand-alone (embedded) ABI'),
        ])

        ei_abiversion = sf.IntField('ABI Version')

        ei_pad = sf.PaddingField(EI_INDENT, mode=sf.PaddingMode.FILL)


    e_indent = sf.SuperField(ElfN_Ehdr__Indent)

    e_type = sf.IntField('Object file type', size=sf.Field_Sizes.INT16, values=[
        sf.Value(0, 'ET_NONE', 'Unknown type.'),
        sf.Value(1, 'ET_REL', 'Relocatable file.'),
        sf.Value(2, 'ET_EXEC', 'Executable file.'),
        sf.Value(3, 'ET_DYN', 'Shared object.'),
        # ET_CORE left appart for testing purposes.
    ])

    e_machine = sf.IntField('Machine architecture', size=sf.Field_Sizes.INT16, values=[
        # Not necessary though, this is just here for documentation purposes.
    ])

    e_version = sf.IntField('File version', size=sf.Field_Sizes.INT32, values=[
        sf.Value(0, 'EV_NONE', 'Invalid version'),
        sf.Value(1, 'EV_CURRENT', 'Current version'),
    ])

    e_entry = ElfN_Addr('Entry point of the program')
    e_phoff = ElfN_Off('Program header table offset')
    e_shoff = ElfN_Off('Section header table offset')
    e_flags = sf.IntField('Machine flags (unused)', size=sf.Field_Sizes.INT32)
    e_ehsize = sf.IntField('ELF Header size', size=sf.Field_Sizes.INT16)
    e_phentsize = sf.IntField('Program header entry size', size=sf.Field_Sizes.INT16)
    e_phnum = sf.IntField('Number of entries in program header table', size=sf.Field_Sizes.INT16)
    e_shentsize = sf.IntField('Section header entry size', size=sf.Field_Sizes.INT16)
    e_shnum = sf.IntField('Number of entrues in section heade table', size=sf.Field_Sizes.INT16)
    e_shstrndx = sf.IntField('Index of string table section header', size=sf.Field_Sizes.INT16)

if __name__ == '__main__':
    prog = '/bin/ls' if len(sys.argv) == 1 else sys.argv[1]
    with open(prog, 'rb') as f:
        s = ElfN_Ehdr(f.read(), 0)
        for field_name in s._srddl.fields:
            val = getattr(s, field_name)
            print(field_name + ':', val)
            if field_name == 'e_indent':
                for it in val._srddl.fields:
                    print('\t' + it + ':', getattr(val, it))
