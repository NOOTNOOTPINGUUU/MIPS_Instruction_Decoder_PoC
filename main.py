WIDTH = 32
class Registers:
    def __init__(self):
        self._regs = [0] * WIDTH
        for i in range(WIDTH):
            self._regs[i] = i
        self.name_map = {
            'zero': 0, 'at': 1, 'v0': 2, 'v1': 3,
            'a0': 4, 'a1': 5, 'a2': 6, 'a3': 7,
            't0': 8, 't1': 9, 't2': 10, 't3': 11, 't4': 12, 't5': 13, 't6': 14, 't7': 15,
            's0': 16, 's1': 17, 's2': 18, 's3': 19, 's4': 20, 's5': 21, 's6': 22, 's7': 23,
            't8': 24, 't9': 25, 'k0': 26, 'k1': 27, 'gp': 28, 'sp': 29, 'fp': 30, 'ra': 31
        }
    def set_register_by_index(self, index, value):
        if index == 0:
            return
        self._regs[index] = value
    def set_register(self, name, value):
        idx = self.name_map.get(name, 0)
        if idx != 0:
            self._regs[idx] = value
    def get_register_by_index(self, index):
        return self._regs[index]
    def get_register_by_name(self, name):
        return self._regs[self.name_map.get(name, 0)]
    def dump(self):
        changed = {f"${name}": self._regs[idx] for name, idx in self.name_map.items()}
        return changed
class CPUCore:
    def __init__(self):
        self.registers = Registers()
        self.pc = 0x00400000
        self.memory = [0] * (2**10) # 1KB of memory
        self.overflow = 0
        self.exception = None
    def execute(self, bin_code):
        # IF
        bin_code = self.Instruction_Format(bin_code)
        # ID
        control_signals = self.control_unit(bin_code[26:32])
        # print(f"bincode={bin_code[:6][::-1]}:{bin_code[6:11][::-1]}:{int(bin_code[11:16][::-1],2)}:{int(bin_code[16:21][::-1],2)}:{int(bin_code[21:26][::-1],2)}:{bin_code[26:]}")
        rs = self.registers.get_register_by_index(int(bin_code[21:26][::-1], 2))
        rt = self.registers.get_register_by_index(int(bin_code[16:21][::-1], 2))
        rd = self.registers.get_register_by_index(int(bin_code[11:16][::-1], 2))
        # print(f"rs({int(bin_code[21:26][::-1], 2)}): {rs}, rt({int(bin_code[16:21][::-1], 2)}): {rt}, rd({int(bin_code[11:16][::-1], 2)}): {rd}")
        # EX
        if control_signals["alu_src"]:  #ALUSrc multiplexor
            op_b = int(bin_code[3])  # immediate value
            # print(f"ALUSrc is 1, using constant {op_b} as op_b")
        ALU_control_signals = self.ALU_control_unit(bin_code[0:6][::-1], control_signals["alu_op1"], control_signals["alu_op0"])
        alu_result, zero_flag = self.ALU_32(ALU_control_signals, rs, rt)
        # print(f"ALU result: {alu_result}, zero_flag: {zero_flag}")
        
        # MEM
        # WB
        if self.exception:
            print(f"Exception: {self.exception}")
            return
        if not self.overflow:
            self.registers.set_register_by_index(int(bin_code[11:16][::-1], 2), alu_result)
        else:
            print("Overflow occurred. Result not written to register.")
            self.overflow = 0  # Reset overflow flag after handling
    def Instruction_Format(self, instruction):

        return instruction
    def control_unit(self, opcode):
        signals ={
            "reg_dst": 0,
            "alu_src": 0,
            "mem_to_reg": 0,
            "reg_write": 0,
            "mem_read": 0,
            "mem_write": 0,
            "branch": 0,
            "ext_op": 0,
            "alu_op1": 0,
            "alu_op0": 0
        }
        op = []
        for i in range(6):
            op.append(int(opcode[5-i]))
        r_type, lw, sw, beq = 0,0,0,0
        r_type = (not op[5]) and (not op[4]) and (not op[3]) and (not op[2]) and (not op[1]) and (not op[0])
        lw = op[5] and (not op[4]) and (not op[3]) and (not op[2]) and op[1] and op[0]
        sw = op[5] and (not op[4]) and op[3] and (not op[2]) and op[1] and op[0]
        beq = (not op[5]) and (not op[4]) and (not op[3]) and op[2] and (not op[1]) and (not op[0])
        # r_type = bool(r_type)
        # lw = bool(lw)
        # sw = bool(sw)
        # beq = bool(beq)
        signals["reg_dst"] = r_type
        signals["alu_src"] = (lw or sw)
        signals["mem_to_reg"] = lw
        signals["reg_write"] = (r_type or lw )
        signals["mem_read"] = lw
        signals["mem_write"] = sw
        signals["branch"] = beq
        signals["ext_op"] = 0
        signals["alu_op1"] = r_type
        signals["alu_op0"] = beq
        for key,value in signals.items():
            signals[key] = 1 if value else 0 # Formatting for clear looks <3
        # print(f"op: {op}")
        # print(f"r_type: {r_type}, lw: {lw}, sw: {sw}, beq: {beq}")
        # print(f"control_unit: {signals}")
        return signals
    def ALU_control_unit(self, func_code,alu_op1, alu_op0):
        # print(f"ALU_control_unit: func_code={func_code}, alu_op1={alu_op1}, alu_op0={alu_op0}")
        signals = [0] * 4 # [ainvert,binvert, op1, op0]
        if alu_op1 ==1 and alu_op0 == 0:
            if func_code == '100100': #and
                # do nothing, default is [0,0,0,0]
                pass
            elif func_code == '100101': #or
                signals[3] = 1
            elif func_code == '100000': #add
                signals[2] = 1
            elif func_code == '100010': #sub
                signals[1] = 1
                signals[2] = 1
            elif func_code == '100111': #nor
                signals[0] = 1
                signals[1] = 1
            elif func_code == '101010': #slt
                signals[1] = 1
                signals[2] = 1
                signals[3] = 1
        # if opcode in ['and', 'or', 'add', 'sub', 'nor', 'slt', 'addi']: #plaintext ALU operations
        #     if opcode == 'and':
        #         # do nothing, default is 0,0
        #         pass
        #     elif opcode == 'or':
        #         signals[3] = 1
        #     elif opcode == 'add' or opcode == 'addi':
        #         signals[2] = 1
        #     elif opcode == 'sub':
        #         signals[1] = 1
        #         signals[2] = 1
        #     elif opcode == 'nor':
        #         signals[0] = 1
        #         signals[1] = 1
        #     elif opcode == 'slt':
        #         signals[1] = 1
        #         signals[2] = 1
        #         signals[3] = 1
        return signals
    def ALU_32(self, table, op_a, op_b):
        op_a = op_a & 0xFFFFFFFF
        op_b = op_b & 0xFFFFFFFF
        result = 0x0
        carry_in = 0
        zero_flag = 0
        WIDTH = 32
        for i in range(WIDTH):
            bit_a = (op_a >> i) & 1
            bit_b = (op_b >> i) & 1
            if i == 0:
                carry_in = table[1] #carry_in = binvert in first round
            if i == WIDTH-1:
                last_carry_in = carry_in
            result_bit, carry_in = self.ALU_01(table, bit_a, bit_b, carry_in)
            result |= result_bit<<i
            # print(f"ALU_32: carry_in={carry_in}, result_bit={result_bit}, result={result}")
        overflow_flag = carry_in ^ last_carry_in
        if table[2] and table[3]:  # SLT operation
            # print(f"ALU_32: SLT operation, carry_out={carry_in}, before_result={result}, zero_flag={zero_flag}, overflow_flag={overflow_flag}, result_bit={result_bit}")
            result = result_bit^overflow_flag
            self.overflow = 0
        if result == 0: #and all bits are zero, set zero_flag
            zero_flag = 1
        if overflow_flag:
            self.overflow = 1
        return result & 0xFFFFFFFF, zero_flag
        
    def ALU_01(self, table, op_a, op_b, carry_in): #table: [ainvert, binvert, op1, op0]
        carry_out = 0
        # print(f"ALU_01: op_a={op_a}, op_b={op_b}, carry_in={carry_in}")

        if table[0]: op_a = (~op_a)&1
        if table[1]: op_b = (~op_b)&1
        gate_and = op_a & op_b
        gate_or = op_a | op_b
        gate_add = op_a + op_b + carry_in
        carry_out = 1 if (gate_add) > 1 else 0
        gate_add = gate_add % 2
        if table[2] == 0:
            if table[3] ==0:
                return gate_and, carry_out # and
            return gate_or, carry_out # or
        if table[2]:
            result_bit = gate_add
            return result_bit%2, carry_out
        else:
            self.exception = "Invalid ALU operation"
class Compiler:
    def __init__(self):
        self.reg_table = Registers()
        self.instructions = []
    def compile(self, cmd):
        cmd = cmd.replace("$", "").replace(",", " ").replace("\t", " ").strip().split()
        print(f"Decoded command: {cmd}")

        bin_code = '0'*WIDTH
        # print(f"bincode={bin_code[:6]}:{bin_code[6:11]}:{bin_code[11:16]}:{bin_code[16:21]}:{bin_code[21:26]}:{bin_code[26:]}")
        bin_code = self.registers_to_bin(cmd, bin_code)
        # print(f"bincode={bin_code[:6]}:{bin_code[6:11]}:{bin_code[11:16]}:{bin_code[16:21]}:{bin_code[21:26]}:{bin_code[26:]}")
        inst = cmd[0].lower()
        func_code = 0b000000
        if  inst in ['and', 'or', 'add', 'sub', 'nor', 'slt']: #R-type[op:6,rs:5,rt:5,rd:5,shamt:5,funct:6]
            if inst == 'and':
                func_code = 0b100100
            elif inst == 'or':
                func_code = 0b100101
            elif inst == 'add':
                func_code = 0b100000
            elif inst == 'sub':
                func_code = 0b100010
            elif inst == 'nor':
                func_code = 0b100111
            elif inst == 'slt':
                func_code = 0b101010
            inst = f'{0:06b}'
            bin_code = f'{inst}'+bin_code[6:26] + f'{func_code:06b}'
            # print(f"bincode={bin_code[:6]}:{bin_code[6:11]}:{bin_code[11:16]}:{bin_code[16:21]}:{bin_code[21:26]}:{bin_code[26:]}")
        # elif inst in ['addi']:
        #     inst = f'{0b00100000:06b}'
        #     bin_code = bin_code[:6] + f'{int(cmd[1]):05b}' + bin_code[11:]
        #     bin_code = bin_code[:11] + f'{int(cmd[2]):05b}' + bin_code[16:]
        #     bin_code = bin_code[:16] + f'{int(cmd[3]):05b}' + bin_code[21:]
        #     bin_code = bin_code[:21] + f'{int(cmd[4]):05b}' + bin_code[26:]
        # elif inst in ['lw', 'sw']:
        #     inst = bin(0b10001111)
        #     bin_code = bin_code[:6] + f'{int(cmd[1]):05b}' + bin_code[11:]
        #     bin_code = bin_code[:11] + f'{int(cmd[2]):05b}' + bin_code[16:]
        #     bin_code = bin_code[:16] + f'{int(cmd[3]):05b}' + bin_code[21:]
        #     bin_code = bin_code[:21] + f'{int(cmd[4]):05b}' + bin_code[26:]
        # elif inst in ['beq']:
        #     inst = bin(0b00000100)
        else:
            self.exception = "Invalid opcode"
        bin_code = bin_code[::-1] # little endian
        # print(f"bincode={bin_code[:6]}:{bin_code[6:11]}:{bin_code[11:16]}:{bin_code[16:21]}:{bin_code[21:26]}:{bin_code[26:]}")
        return bin_code
    def registers_to_bin(self, cmd, bin_code):
        rs,rt,rd,shamt=0,0,0,0
        cmd_len = len(cmd)
        if cmd_len > 1:
            rd = f'{self.reg_table.name_map[cmd[1]]& 0x1F:05b}'
            bin_code = bin_code[:16] + rd + bin_code[21:]
        if cmd_len > 2:
            rs = f'{self.reg_table.name_map[cmd[2]]& 0x1F:05b}'
            bin_code = bin_code[:6] + rs + bin_code[11:]
        if cmd_len > 3:
            rt = f'{self.reg_table.name_map[cmd[3]]& 0x1F:05b}'
            bin_code = bin_code[:11] + rt + bin_code[16:]
            try:
                shamt_val = int(cmd[3]) & 0x1F
            except (ValueError, TypeError):
                shamt_val = 0     
            shamt = f'{shamt_val:05b}'
            bin_code = bin_code[:21] + shamt + bin_code[26:]
        return bin_code

        
def interface():
    CPU = CPUCore()
    Compiler_32 = Compiler()
    registers = CPU.registers
    print("Welcome to the command line interface. Type 'exit' to quit.")
    while (True):
        try:
            cmd = input("$ ")
        except KeyboardInterrupt:
            print("\nExiting the program.")
            break
        if cmd.lower() == 'exit':
            print("Exiting the program.")
            break
        if cmd == "":
            continue
        if cmd == "registers":
            display = registers.dump()
            for i in range(0, len(display), 4):
                
                print(" ".join(f"{k}: {v:032b}" for k, v in list(display.items())[i:i+4]))
            continue
        machine_code = Compiler_32.compile(cmd)
        
        CPU.execute(machine_code)
        display = registers.dump()
        for i in range(0, len(display), 4):
            print(" ".join(f"{k}: {v}" for k, v in list(display.items())[i:i+4]))



if __name__ == "__main__":
        interface()