# This file only is here to help me gather what I want to have as an API from
# the point of view of the user (writer of a template).

# All values were found in /usr/bin/elf.h of my GNU/Linux distribution.

import sys
import functools

import srddl.data as sd
import srddl.exceptions as se
import srddl.fields as sf
import srddl.helpers as sh
import srddl.models as sm


# Atomic types.
class IntFieldN(sf.IntField):
    @functools.lru_cache()
    def _size(self, struct):
        try:
            header = struct['data'].mapped[0]
        except:
            header = struct
        res = header.e_indent.ei_class['value'] * 4
        return res

class ElfN_Off(IntFieldN):
    def _display_value(self, val):
        return '{:#x}'.format(val)

class ElfN_Addr(ElfN_Off): pass

class BitMaskFieldN(sf.BitMaskField):
    @functools.lru_cache()
    def _size(self, struct):
        try:
            header = struct['data'].mapped[0]
        except se.NoMappedDataError:
            header = struct
        res = header.e_indent.ei_class['value'] * 4
        return res

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

        ei_pad = sf.PaddingField(EI_INDENT, mode=sf.PaddingField.Mode.FILL)


    e_indent = sf.SuperField(ElfN_Ehdr__Indent)

    e_type = sf.IntField('Object file type', size=sf.IntField.Size.INT16, values=[
        sf.Value(0, 'ET_NONE', 'Unknown type.'),
        sf.Value(1, 'ET_REL', 'Relocatable file.'),
        sf.Value(2, 'ET_EXEC', 'Executable file.'),
        sf.Value(3, 'ET_DYN', 'Shared object.'),
        # ET_CORE left appart for testing purposes.
    ])

    e_machine = sf.IntField('Machine architecture', size=sf.IntField.Size.INT16, values=[
        # Not necessary though, this is just here for documentation purposes.
    ])

    e_version = sf.IntField('File version', size=sf.IntField.Size.INT32, values=[
        sf.Value(0, 'EV_NONE', 'Invalid version'),
        sf.Value(1, 'EV_CURRENT', 'Current version'),
    ])

    e_entry = ElfN_Addr('Entry point of the program')
    e_phoff = ElfN_Off('Program header table offset')
    e_shoff = ElfN_Off('Section header table offset')
    e_flags = sf.IntField('Machine flags (unused)', size=sf.IntField.Size.INT32)
    e_ehsize = sf.IntField('ELF Header size', size=sf.IntField.Size.INT16)
    e_phentsize = sf.IntField('Program header entry size', size=sf.IntField.Size.INT16)
    e_phnum = sf.IntField('Number of entries in program header table', size=sf.IntField.Size.INT16)
    e_shentsize = sf.IntField('Section header entry size', size=sf.IntField.Size.INT16)
    e_shnum = sf.IntField('Number of entrues in section heade table', size=sf.IntField.Size.INT16)
    e_shstrndx = sf.IntField('Index of string table section header', size=sf.IntField.Size.INT16)

    def _setup(self, data):
        if self.e_phoff:
            data.map_array(self.e_phoff, self.e_phnum, ElfN_Phdr)
        if self.e_shoff:
            data.map_array(self.e_shoff, self.e_shnum, ElfN_Shdr)


class ElfN_Phdr(sm.Struct):
    p_type = sf.IntField(size=sf.IntField.Size.INT32, values=[
        sf.Value(0, 'PT_NULL'),
        sf.Value(1, 'PT_LOAD'),
        sf.Value(2, 'PT_DYNAMIC'),
        sf.Value(3, 'PT_INTERP'),
        sf.Value(4, 'PT_NOTE'),
        sf.Value(5, 'PT_SHLIB'),
        sf.Value(6, 'PT_PHDR'),
        sf.Value(7, 'PT_TLS'),
        sf.Value(8, 'PT_NUM'),
        sf.Value(0x60000000, 'PT_LOOS', 'Start of OS Specific'),
        sf.Value(0x6474e550, 'PT_GNU_EH_FRAME'),
        sf.Value(0x6474e551, 'PT_GNU_STACK'),
        sf.Value(0x6474e552, 'PT_GNU_RELRO'),
        sf.Value(0x6ffffffa, 'PT_LOSUNW,PT_SUNWBSS'),
        sf.Value(0x6ffffffb, 'PT_SUNWSTACK'),
        sf.Value(0x6fffffff, 'PT_HISUNW,PT_HIOS'),
        sf.Value(0x70000000, 'PT_LOPROC'),
        sf.Value(0x7fffffff, 'PT_HIPROC'),
    ])

    p_offset = ElfN_Off()
    p_vaddr = ElfN_Addr()
    p_paddr = ElfN_Addr()
    p_filesz = IntFieldN()
    p_memsz = IntFieldN()
    p_flags = sf.BitMaskField(size=sf.BitMaskField.Size.INT32, values=[
        sf.Value(0x1, 'PF_X'),
        sf.Value(0x2, 'PF_W'),
        sf.Value(0x4, 'PF_R'),
        sf.Value(0x0ff00000, 'PF_MASKOS'),
        sf.Value(0xf0000000, 'PF_MASKPROC'),
    ])

    p_align = IntFieldN()

    def _pre_mapping(self, data, lst):
        if data.mapped[0].e_indent.ei_class['name'] == 'ELFCLASS64':
            return [('p_flags', 1)]
        return []


class ElfN_Shdr(sm.Struct):
    sh_name = sf.IntField(size=sf.IntField.Size.INT32)

    sh_type = sf.IntField(size=sf.IntField.Size.INT32, values=[
        sf.Value(0, 'SHT_NULL'),
        sf.Value(1, 'SHT_PROGBITS'),
        sf.Value(2, 'SHT_SYMTAB'),
        sf.Value(3, 'SHT_STRTAB'),
        sf.Value(4, 'SHT_RELA'),
        sf.Value(5, 'SHT_HASH'),
        sf.Value(6, 'SHT_DYNAMIC'),
        sf.Value(7, 'SHT_NOTE'),
        sf.Value(8, 'SHT_NOBITS'),
        sf.Value(9, 'SHT_REL'),
        sf.Value(10, 'SHT_SHLIB'),
        sf.Value(11, 'SHT_DYNSYM'),
        sf.Value(14, 'SHT_INIT_ARRAY'),
        sf.Value(15, 'SHT_FINI_ARRAY'),
        sf.Value(16, 'SHT_PREINIT_ARRAY'),
        sf.Value(17, 'SHT_GROUP'),
        sf.Value(18, 'SHT_SYMTAB_SHNDX'),
        sf.Value(19, 'SHT_NUM'),
        sf.Value(0x60000000, 'SHT_LOOS'),
        sf.Value(0x6ffffff5, 'SHT_GNU_ATTRIBUTES'),
        sf.Value(0xfffffff6, 'SHT_GNU_HASH'),
        sf.Value(0x6ffffff7, 'SHT_GNU_LIBLIST'),
        sf.Value(0x6ffffff8, 'SHT_CHECKSUM'),
        sf.Value(0x6ffffffa, 'SHT_LOSUNW,SHT_SUNW_move'),
        sf.Value(0x6ffffffb, 'SHT_SUNW_COMDAT'),
        sf.Value(0x6ffffffc, 'SHT_SUNW_syminfo'),
        sf.Value(0x6ffffffd, 'SHT_GNU_verdef'),
        sf.Value(0x6ffffffe, 'SHT_GNU_verneed'),
        sf.Value(0x6fffffff, 'SHT_GNU_versym,SHT_HISUNW,SHT_HIOS'),
        sf.Value(0x70000000, 'SHT_LOPROC'),
        sf.Value(0x7fffffff, 'SHT_HIPROC'),
        sf.Value(0x80000000, 'SHT_LOUSER'),
        sf.Value(0x8fffffff, 'SHT_HIUSER'),
    ])

    sh_flags = BitMaskFieldN(values=[
        sf.Value(0x1, 'SHF_WRITE'),
        sf.Value(0x2, 'SHF_ALLOC'),
        sf.Value(0x4, 'SHF_EXECINSTR'),
        sf.Value(0x8, 'SHF_MERGE'),
        sf.Value(0x10, 'SHF_STRINGS'),
        sf.Value(0x20, 'SHF_INFO_LINK'),
        sf.Value(0x40, 'SHF_LINK_ORDER'),
        sf.Value(0x80, 'SHF_OS_NONCONFORMING'),
        sf.Value(0x100, 'SHF_GROUP'),
        sf.Value(0x200, 'SHF_TLS'),
        sf.Value(0x0ff00000, 'SHF_MASKOS'),
        sf.Value(0xf0000000, 'SHF_MASKPROC'),
        sf.Value(0x40000000, 'SHF_ORDERED'),
        sf.Value(0x80000000, 'SHF_EXCLUDE'),
    ])

    sh_addr = ElfN_Addr()
    sh_offset = ElfN_Off()
    sh_size = IntFieldN()
    sh_link = sf.IntField(size=sf.IntField.Size.INT32)
    sh_info = sf.IntField(size=sf.IntField.Size.INT32)
    sh_addralign = IntFieldN()
    sh_entsize = IntFieldN()

if __name__ == '__main__':
    prog = '/bin/ls' if len(sys.argv) == 1 else sys.argv[1]

    f = sd.FileData(prog)
    f.map(0, ElfN_Ehdr)
