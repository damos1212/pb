import pygame, sys, random, os

class CPU:

    clockrate = 4194300
    
    #Full memory
    memory = [0x00] * 65536

    """
    0x0000-0x3FFF: Permanently-mapped ROM bank.
    0x4000-0x7FFF: Area for switchable ROM banks.
    0x8000-0x9FFF: Video RAM.
    0xA000-0xBFFF: Area for switchable external RAM banks.
    0xC000-0xCFFF: Game Boys working RAM bank 0 .
    0xD000-0xDFFF: Game Boys working RAM bank 1.
    0xFE00-0xFEFF: Sprite Attribute Table.
    0xFF00-0xFF7F: Devices Mappings. Used to access I/O devices.
    0xFF80-0xFFFE: High RAM Area.
    0xFFFF: Interrupt Enable Register.
    """

    """
    Cart Header
    $0100-$0103	NOP / JP $0150
    $0104-$0133	Nintendo Logo
    $0134-$013E	Game Title (Uppercase ASCII)
    $013F-$0142	4-byte Game Designation
    $0143	Color Compatibility byte
    $0144-$0145	New Licensee Code
    $0146	SGB Compatibility byte
    $0147	Cart Type
    $0148	Cart ROM size
    $0149	Cart RAM size
    $014A	Destination code
    $014B	Old Licensee code
    $014C	Mask ROM version
    $014D	Complement checksum
    $014E-$014F	Checksum
    """

    #Memory accessible by cpu
    wram = [0x00] * 8192

    #Memory accessible by ppu
    vram = [0x00] * 8192

    #Accumulator Register
    A = 0x00

    #Register 1
    B = 0x00

    #Register 2
    C = 0x00

    #Register 3
    D = 0x00

    #Register 4
    E = 0x00

    #Status Register
    F = 0x00

    #Register 5
    H = 0x00

    #Register 6
    L = 0x00

    #Stack Pointer 16bit
    SP = 0x0000

    #Program Counter 16bit
    PC = 0x0000

    opcode = 0x00
    
    cycle = 0

class GPU:
    fps = 60

    #Screen Dimensions
    screen_width = 160
    screen_height = 144
    
    #Window scaling
    screen_scale = 1
    
    #Color palette for gameboy
    color_palette = [(0,0,0), (75, 75, 75), (175, 175, 175), (255, 255, 255)]
    
    #Array of pixels to fill the screen
    screen_pixel_array = [x[:] for x in [[0] * screen_height] * screen_width]

    scanline_counter = 0
    
    screen = pygame.display.set_mode((screen_width * screen_scale, screen_height * screen_scale))
    
    screen_buffer = pygame.Surface((screen_width * screen_scale, screen_height * screen_scale))
    
pygame.init()
clock = pygame.time.Clock()
pygame.display.set_caption("Gameboy Emulator")

#Load game into memory
def load_game(filename):
    with open(filename, mode='rb') as file:
        rom = file.read()
    return bytearray(rom)

game_rom = load_game("game.gb")
boot_rom = load_game("DMG_ROM.bin")
for x in range (0,2047):
    CPU.memory[x] = game_rom[x]
for x in range (0,255):
    CPU.memory[x] = boot_rom[x]


#$0134-$013E	Game Title (Uppercase ASCII)
ascii_game_name = [0x00] * 16
for x in range (0, 15):
    ascii_game_name[x] = CPU.memory[308 + x]
game_name = ""
for x in ascii_game_name:
    game_name += chr(x)

print(" \n Game Title: ", game_name)
pygame.display.set_caption(game_name.rstrip('\x00'))

def decode_opcode(opcode, PC):
    operation = (opcode & 0xFF00) >> 8
    cycle = 0
    match operation:
        case 0x31:
            CPU.SP = CPU.memory[CPU.PC + 1] << 8 | CPU.memory[CPU.PC + 2]
            CPU.PC += 3
            cycle += 3
        case 0xAF:
            CPU.A = CPU.A ^ CPU.A
            CPU.PC += 1
            cycle += 1
        case 0x21:
            CPU.H = CPU.memory[CPU.PC + 2]
            CPU.L = CPU.memory[CPU.PC + 1]
            CPU.PC += 3
            cycle += 1
        case 0x32:
            CPU.memory[CPU.H << 8 | CPU.L]
            val = CPU.H << 8 | CPU.L
            val -= 1
            CPU.H = (val & 0xff << 8) >> 8
            CPU.L = (val & 0xff)
            CPU.PC += 1
            cycle += 1
        case 0xCB:
            cycle += 1
            match (opcode & 0xFF):
                case 0x7C:
                    flag = CPU.H
                    cycle += 2
                    match flag >> 7:
                        case 0x00:
                            flag = 0b01000000
                            CPU.F |= flag
                        case 0x01:
                            flag = 0b00000000
                            CPU.F |= flag
                    CPU.PC += 2
        case 0x20:
            cycle += 2
            match CPU.F >> 7:
                case 0x01:
                    match (opcode & 0xFF) >> 7:
                        case 0x00:
                            CPU.PC += ((opcode & 0xFF) & 0x7f)
                            CPU.PC += 2
                        case 0x01:
                            CPU.PC += (((opcode & 0xFF) & 0x7f) - 128)
                            CPU.PC += 2
                case other:
                    CPU.PC +=2
        case 0x0E:
            CPU.C = opcode & 0xff
            CPU.PC += 2
            cycle += 2
        case 0x3E:
            CPU.A = opcode & 0xff
            CPU.PC += 2
            cycle += 2
        case 0xE2:
            CPU.memory[0xFF00 + CPU.C] = CPU.A
            CPU.PC += 1
            cycle += 1
        case 0x0C:
            CPU.C += 1
            CPU.PC += 1
            cycle += 1
        case 0x77:
            CPU.memory[CPU.H << 8 | CPU.L] = CPU.A
            CPU.PC += 1
            cycle += 1
        case 0xE0:
            CPU.memory[0xFF00 + (opcode & 0xff)] = CPU.A
            CPU.PC += 2
            cycle += 2
        case 0x11:
            CPU.D = CPU.memory[CPU.PC + 2]
            CPU.E = CPU.memory[CPU.PC + 1]
            CPU.PC += 3
            cycle += 3
        case 0x1A:
            CPU.A = (CPU.D << 8 | CPU.E)
            CPU.PC += 1
            cycle += 1
        case 0xCD:
            CPU.memory[CPU.SP] = (CPU.memory[CPU.PC + 1] << 8 | CPU.memory[CPU.PC + 2])
            CPU.SP += 1
            CPU.PC += 3
            cycle += 3
        case 0x13:
            val = CPU.D << 8 | CPU.E
            val += 1
            CPU.D = (val & 0xff << 8) >> 8
            CPU.E = (val & 0xff)
            CPU.PC += 1
            cycle += 1
        case 0x7B:
            CPU.A = CPU.E
            CPU.PC += 1
            cycle += 1
        case 0xFE:
            val = CPU.A - opcode & 0xff
            flag = 0b01000000
            flag += ((val & 0xFF) == 0) << 7
            flag += (((CPU.A & 0xF) - ((opcode & 0xff) & 0xF)) < 0) << 5
            flag += (val < 0) << 4
            CPU.F &= 0b00000000
            CPU.F |= flag
            CPU.PC += 2
            cycle += 2
        case 0x06:
            CPU.B = opcode & 0xff
            CPU.PC += 2
            cycle += 2
        case 0x22:
            CPU.memory[CPU.H << 8 | CPU.L]
            val = CPU.H << 8 | CPU.L
            val += 1
            CPU.H = (val & 0xff << 8) >> 8
            CPU.L = (val & 0xff)
            CPU.PC += 1
            cycle += 1
        case 0x23:
            val = CPU.H << 8 | CPU.L
            val += 1
            CPU.H = (val & 0xff << 8) >> 8
            CPU.L = (val & 0xff)
            CPU.PC += 1
            cycle += 1
        case 0x05:
            CPU.B -= 1
            CPU.PC += 1
            cycle += 1
        case 0xEA:
            CPU.memory[(opcode & 0xff << 8 | ((opcode + 1) & 0xff))] = CPU.A
            CPU.PC += 3
            cycle += 3
        case 0x3D:
            CPU.A -= 1
            CPU.PC += 1
            cycle += 1
        case 0x28:
            cycle += 2
            match CPU.F >> 7:
                case 0x00:
                    match (opcode & 0xFF) >> 7:
                        case 0x00:
                            CPU.PC += ((opcode & 0xFF) & 0x7f)
                            CPU.PC += 2
                        case 0x01:
                            CPU.PC += (((opcode & 0xFF) & 0x7f) - 128)
                            CPU.PC += 2
                case other:
                    CPU.PC +=2
        case 0x0D:
            CPU.C -= 1
            CPU.PC += 1
            cycle += 1
        case 0x2E:
            CPU.L = opcode & 0xff
            CPU.PC += 2
            cycle += 2
        case 0x18:
            cycle += 2
            match (opcode & 0xFF) >> 7:
                case 0x00:
                    CPU.PC += ((opcode & 0xFF) & 0x7f)
                    CPU.PC += 2
                case 0x01:
                    CPU.PC += (((opcode & 0xFF) & 0x7f) - 128)
                    CPU.PC += 2
        case 0x67:
            CPU.H = CPU.A
            CPU.PC += 1
            cycle += 1
        case 0x57:
            CPU.D = CPU.A
            CPU.PC += 1
            cycle += 1
        case 0x04:
            CPU.B += 1
            CPU.PC += 1
            cycle += 1
        case 0x1E:
            CPU.E = opcode & 0xff
            CPU.PC += 2
            cycle += 2
        case 0xF0:
            CPU.A = CPU.memory[0xFF00 + (opcode & 0xff)]
            CPU.PC += 2
            cycle += 2
        case 0x1D:
            CPU.E -= 1
            CPU.PC += 1
            cycle += 1
        case 0x24:
            CPU.H += 1
            CPU.PC += 1
            cycle += 1
        case 0x7C:
            CPU.A = CPU.H
            CPU.PC += 1
            cycle += 1
        case 0x90:
            CPU.A -= CPU.B
            CPU.PC += 1
            cycle += 1
        case 0x15:
            CPU.D -= 1
            CPU.PC += 1
            cycle += 1
        case 0x16:
            CPU.D = opcode & 0xff
            CPU.PC += 2
            cycle += 2
        case other:
            print("Current Opcode: ", "0x{:04X}".format(opcode), " Not Implemented Yet")
    return cycle

def emulate_cpu():
    opcode = CPU.memory[CPU.PC] << 8 | CPU.memory[CPU.PC + 1]
    cycle = decode_opcode(opcode, CPU.PC)
    return cycle

def draw_tiles():
    r = random.randint(0,3)
    for x in range (0,GPU.screen_width):
            pygame.draw.rect(GPU.screen_buffer, GPU.color_palette[r], (x,CPU.memory[0xFF44],1,1))
    GPU.screen.blit(GPU.screen_buffer, (0,0))
    return

def draw_sprites():
    return

def draw_scanline():    
    lcd_register = CPU.memory[0xFF40] 
    bit = [int(i) for i in "{0:08b}".format(lcd_register)]
    if (bit[0]):
        draw_tiles() 

    if (bit[1]):
        draw_sprites() 

def emulate_gpu(cycle):
    #SetLCDStatus()
    
    if CPU.memory[0xFF40] & 1 == 1:
        GPU.scanline_counter -= cycle
    else:
        return 

    #Next Scanline
    if (GPU.scanline_counter <= 0):
        CPU.memory[0xFF44] += 1
        current_scanline = CPU.memory[0xFF44]
        scanline_counter = 456

    #Vblank
    if (current_scanline == 144):
        #RequestInterupt(0)
        return

    #if gone past scanline 153 reset to 0
    elif (current_scanline > 153):
        CPU.memory[0xFF44] = 0

    #draw the current scanline
    elif (current_scanline < 144):
        draw_scanline()
        return


#game loop
def main():
    running = True
    GPU.screen_status = False
    cycles_per_second = CPU.clockrate / GPU.fps
    while running:
        clock.tick_busy_loop(GPU.fps)
        while (CPU.cycle < cycles_per_second):
            cycle = emulate_cpu()
            CPU.cycle += cycle
            emulate_gpu(cycle)
        CPU.cycle = 0
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            pressed = pygame.key.get_pressed()
            if pressed[pygame.K_ESCAPE]:
                print("Current Opcode: ", "0x{:04X}".format(CPU.memory[CPU.PC] << 8 | CPU.memory[CPU.PC + 1]), "A:", "0x{:02X}".format(CPU.A), "B:", "0x{:02X}".format(CPU.B), "C:", "0x{:02X}".format(CPU.C), "D:", "0x{:02X}".format(CPU.D), "E:", "0x{:02X}".format(CPU.E), "F:", "0x{:02X}".format(CPU.F), "H:", "0x{:02X}".format(CPU.H), "L:", "0x{:02X}".format(CPU.L), "SP:", "0x{:04X}".format(CPU.SP), "PC:", "0x{:04X}".format(CPU.PC))
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    return
                
if __name__ == "__main__":
    main() 