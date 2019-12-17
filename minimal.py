#-----------------------------------------------------------------------------
"""
Minimal(-ish) Z80 system
"""
#-----------------------------------------------------------------------------

from __future__ import print_function
import memory
import z80da
import z80

# Python 2/3
try: input = raw_input
except NameError: pass

#-----------------------------------------------------------------------------

class memmap:
    """memory devices and address map"""

    def __init__(self, romfile = './roms/tec1a.rom'):
        self.rom = memory.rom(11)
#        self.rom.load_file(0, romfile)
        self.ram = memory.ram(11)
        self.empty = memory.null()

    def select(self, adr):
        """return the memory object selected by this address"""
        # select with 2k granularity
        memmap = (
            self.ram,   # 0x0000 - 0x07ff
            self.rom,   # 0x0800 - 0x0fff
            self.empty, # 0x1000
            self.empty, # 0x1800
            self.empty, # 0x2000
            self.empty, # 0x2800
            self.empty, # 0x3000
            self.empty, # 0x3800
            self.empty, # 0x4000
            self.empty, # 0x4800
            self.empty, # 0x5000
            self.empty, # 0x5800
            self.empty, # 0x6000
            self.empty, # 0x6800
            self.empty, # 0x7000
            self.empty, # 0x7800
            self.empty, # 0x8000
            self.empty, # 0x8800
            self.empty, # 0x9000
            self.empty, # 0x9800
            self.empty, # 0xa000
            self.empty, # 0xa800
            self.empty, # 0xb000
            self.empty, # 0xb800
            self.empty, # 0xc000
            self.empty, # 0xc800
            self.empty, # 0xd000
            self.empty, # 0xd800
            self.empty, # 0xe000
            self.empty, # 0xe800
            self.empty, # 0xf000
            self.empty, # 0xf800
        )
        return memmap[adr >> 11]

    def __getitem__(self, adr):
        adr &= 0xffff
        return self.select(adr)[adr]

    def __setitem__(self, adr, val):
        adr &= 0xffff
        self.select(adr)[adr] = val

#-----------------------------------------------------------------------------


class io:
    """io handler"""

    def __init__(self):
        self.out = ""
        self.inp = ""

    def rd(self, adr):
        """input from any port acts reads from the keyboard"""
        if self.inp == "":
            self.inp = input("> ")
            if self.inp == "":
                self.inp = "?"
        r = self.inp[0]
        self.inp = self.inp[1:]
        return ord(r)

    def wr(self, adr, val):
        """output to any port acts like a 20 character scrolling display"""
        if val < 32:
            self.out = ""
        else:
            self.out += chr(val)
            self.out = self.out[-20:]

#-----------------------------------------------------------------------------

class minimal:

    def __init__(self):
        self.mem = memmap()
        self.io = io()
        self.cpu = z80.cpu(self.mem, self.io)
        self.bootstrap()


    def bootstrap(self):
        """ensure an unhandled ret goes to a halt"""
        self.mem.ram.load(0, (0x76 for n in range(0x800)))
        self.cpu.sp = 0x400
        self.cpu._push(0x400)


    def run(self):
        """run the emulation"""
        irq = False
        while True:
            try:
                pc = self.cpu._get_pc()
                if  irq:
                    self.cpu.interrupt(0)
                    irq = False
                else:
                    self.cpu.execute()
            except z80.Error:
                self.cpu._set_pc(pc)
                raise ('exception: %s\n' % self._current_instruction())

    def _quick_regs(self):
        return "af:%04x bc:%04x de:%04x hl:%04x" % (
                self.cpu._get_af(),
                self.cpu._get_bc(),
                self.cpu._get_de(),
                self.cpu._get_hl(),
                )


    def _current_instruction(self):
        """return a string for the current instruction"""
        pc = self.cpu._get_pc()
        (operation, operands, n) = self.cpu.da(pc)
        return '%04x %-5s %s' % (pc, operation, operands)


    def _step(self):
        """single step the cpu"""
        done = self._current_instruction()
        self.cpu.execute()
        next = self._current_instruction()
        return [done, next]


#-----------------------------------------------------------------------------

if __name__ == "__main__":
    m = minimal()

    code = [0xdb,1,     # in a,(1)
            0xd3,1,     # out (1),a
            0xc9,       # ret
           ]       

    m.mem.ram.load(0, code)
    while not m.cpu.halt:
        print("%-22s [%-20s] %s" % (m._step()[0], m.cpu.io.out, m._quick_regs()))
