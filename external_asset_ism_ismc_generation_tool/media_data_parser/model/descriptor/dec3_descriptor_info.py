    # Dolby Digital info
    #
    # (Starting with MSB = 0)
    # 0 Front Left (L)
    # 1 Front Center (C)
    # 2 Front Right (R)
    # 3 Left Surround (Ls)
    # 4 Right Surround (Rs)
    # 5 Left Center/Right Center (Lc/Rc)
    # 6 Left Rear Surround/Right Rear Surround (Lrs/Rrs)
    # 7 Center Surround (Cs)
    # 8 Top Surround (Ts)
    # 9 Left Side Surround/Right Side Surround (Lsd/Rsd)
    # 10 Left Wide/Right Wide (Lw/Rw)
    # 11 Vertical High Left/Vertical High Right (Vhl/Vhr)
    # 12 Vertical High Center (Vhc)
    # 13 Left Top Surround/Right Top Surround (Lts/Rts)
    # 14 Low-Frequency Effects 2 (LFE2)
    # 15 Low-Frequency Effects (LFE)
    #
    # Based on acmod (Audio Coding Mode):
    # 000 Channels 1, 2
    # 001 Center
    # 010 Left, Right
    # 011 Left, Center, Right
    # 100 Left, Right, Surround
    # 101 Left, Center, Right, Surround
    # 110 Left, Right, Surround Left, Surround Right
    # 111 Left, Center, Right, Surround Left, Surround Right
    #
    # Channel Location (chan_loc):
    # 0 Lc/Rc (Left Center/Right Center)
    # 1 Lrs/Rrs (Left Rear Surround/Right Rear Surround)
    # 2 Cs (Center Surround)
    # 3 Ts (Top Surround)
    # 4 Lsd/Rsd (Left Side Surround/Right Side Surround)
    # 5 Lw/Rw (Left Wide/Right Wide)
    # 6 Lvh/Rvh (Vertical High Left/Vertical High Right)
    # 7 Cvh (Vertical High Center)
    # 8 LFE2 (Low-Frequency Effects 2)
    #
    # According to the Digital Cinema standards, referenced in the Blu-ray Disc Specification,
    # speaker placement is generally laid out as follows:
    #
    #       +---+       +---+       +---+
    #       |Vhl|       |Vhc|       |Vhr|        (High speakers)
    #       +---+       +---+       +---+
    # +---+ +---+ +---+ +---+ +---+ +---+ +---+
    # |Lw | | L | |Lc | | C | |Rc | | R | |Rw |
    # +---+ +---+ +---+ +---+ +---+ +---+ +---+
    #             +----+       +----+
    #             |LFE1|       |LFE2|
    # +---+       +----+ +---+ +----+      +---+
    # |Ls |              |Ts |             |Rs |
    # +---+              +---+             +---+
    #
    # +---+                               +---+
    # |Lsd|                               |Rsd|
    # +---+ +---+       +---+       +---+ +---+
    #       |Rls|       |Cs |       |Rrs|
    #       +---+       +---+       +---+
    #
    # Terminology Variations:
    # Constant                | HDMI  | Digital Cinema | DTS Extension
    # ================================================================
    # FRONT_LEFT              | FL    | L              | L
    # FRONT_RIGHT             | FR    | R              | R
    # FRONT_CENTER            | FC    | C              | C
    # LOW_FREQUENCY           | LFE   | LFE            | LFE
    # BACK_LEFT               | (RLC) | Rls            | Lsr
    # BACK_RIGHT              | (RRC) | Rrs            | Rsr
    # FRONT_LEFT_OF_CENTER    | FLC   | Lc             | Lc
    # FRONT_RIGHT_OF_CENTER   | FRC   | Rc             | Rc
    # BACK_CENTER             | RC    | Cs             | Cs
    # SIDE_LEFT               | (RL)  | Ls             | Lss
    # SIDE_RIGHT              | (RR)  | Rs             | Rss
    # TOP_CENTER              | TC    | Ts             | Oh
    # TOP_FRONT_LEFT          | FLH   | Vhl            | Lh
    # TOP_FRONT_CENTER        | FCH   | Vhc            | Ch
    # TOP_FRONT_RIGHT         | FRH   | Vhr            | Rh
    # WIDE_LEFT               | FLW   | Lw             | Lw
    # WIDE_RIGHT              | FRW   | Rw             | Rw
    # SURROUND_DIRECT_LEFT    |       | Lsd            | Ls
    # SURROUND_DIRECT_RIGHT   |       | Rsd            | Rs

class DEC3DescriptorInfo():

    dolby_digital_chan_loc = {
        0: 'Lc/Rc',
        1: 'Lrs/Rrs',
        2: 'Cs',
        3: 'Ts',
        4: 'Lsd/Rsd',
        5: 'Lw/Rw',
        6: 'Vhl/Vhr',
        7: 'Vhc',
        8: 'LFE2'
    }

    dolby_digital_acmod = {
        0: ['Ch1', 'Ch2'], # two completely independent program channels (dual mono) are encoded into the bit stream
        1: ['C'],
        2: ['L', 'R'],
        3: ['L', 'C', 'R'],
        4: ['L', 'R', 'Cs'],
        5: ['L', 'C', 'R', 'Cs'],
        6: ['L', 'R', 'Ls', 'Rs'],
        7: ['L', 'C', 'R', 'Ls', 'Rs']
    }

    dolby_digital_masks = {
        'L':       0x1,             # SPEAKER_FRONT_LEFT
        'R':       0x2,             # SPEAKER_FRONT_RIGHT
        'C':	   0x4,             # SPEAKER_FRONT_CENTER
        'LFE':     0x8,             # SPEAKER_LOW_FREQUENCY
        'Ls':      0x10,            # SPEAKER_BACK_LEFT
        'Rs':      0x20,            # SPEAKER_BACK_RIGHT
        'Lc':      0x40,            # SPEAKER_FRONT_LEFT_OF_CENTER
        'Rc':      0x80,            # SPEAKER_FRONT_RIGHT_OF_CENTER
        'Cs':      0x100,           # SPEAKER_BACK_CENTER
        'Lrs':     0x200,           # SPEAKER_SIDE_LEFT
        'Rrs':     0x400,           # SPEAKER_SIDE_RIGHT
        'Ts':      0x800,           # SPEAKER_TOP_CENTER
        'Vhl/Vhr': 0x1000 | 0x4000, # SPEAKER_TOP_FRONT_LEFT/SPEAKER_TOP_FRONT_RIGHT
        'Vhc':     0x2000,          # SPEAKER_TOP_FRONT_CENTER
    }

    dolby_digital_sample_rates = {
        0 : 48000 , # 48 kHz
        1 : 44100 , # 44,1 kHz
        2 : 32000 , # 32 kHz
        3 : 0       # reserved
    }
