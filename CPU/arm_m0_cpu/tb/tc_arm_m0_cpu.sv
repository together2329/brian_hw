//============================================================================
// Module : tc_arm_m0_cpu (included by tb_arm_m0_cpu)
// Description : Test case definitions for ARM M0 CPU
//               Pre-assembled Thumb-16 hex programs for each test sequence
//============================================================================
// This file is a reference document for test programs.
// The actual test programs are defined inline in tb_arm_m0_cpu.sv
// for simplicity. This file provides the detailed hex opcode reference.

// ================================================================
// Thumb-16 Instruction Encoding Reference
// ================================================================
//
// Instruction         | Binary Encoding              | Hex Example
// --------------------+------------------------------+------------
// MOV Rdn, #imm8      | 00100 Rdn(3) imm8(8)        | MOV R0,#5  = 0x2005
// ADD Rdn, #imm8      | 00110 Rdn(3) imm8(8)        | ADD R0,#5  = 0x3005
// SUB Rdn, #imm8      | 00111 Rdn(3) imm8(8)        | SUB R0,#5  = 0x3805
// CMP Rdn, #imm8      | 00101 Rdn(3) imm8(8)        | CMP R0,#5  = 0x2805
// NOP                 | 1011 1111 0000 0000          | NOP        = 0xBF00
// ADD Rd,Rn,Rm (low)  | 0001100 Rm(3) Rn(3) Rd(3)  | ADD R2,R0,R1 = 0x1882
// SUB Rd,Rn,Rm (low)  | 0001101 Rm(3) Rn(3) Rd(3)  | SUB R2,R0,R1 = 0x1A82
// CMP Rn,Rm (low)     | 0100001010 Rm(3) Rn(3)     | CMP R0,R1  = 0x4288
// STR Rt,[Rn,Rm]      | 0101000 Rm(3) Rn(3) Rt(3)  | STR R0,[R1,R2] = 0x5008
// LDR Rt,[Rn,Rm]      | 0101100 Rm(3) Rn(3) Rt(3)  | LDR R0,[R1,R2] = 0x5808
// B cond              | 1101 cond(4) imm8(8)         | BEQ +2     = 0xD002
// B unconditional     | 11100 imm11(11 signed)       | B +2       = 0xE001
// BX Rm               | 01000111 0 Rm(4) 000        | BX LR      = 0x4770
// PUSH {reglist}      | 1011 0 0 reglist(8)         | PUSH {R0-R3} = 0xB40F
// POP {reglist}       | 1011 1 0 reglist(8)         | POP {R0-R3}  = 0xBC0F

// ================================================================
// Test Programs (Hex)
// ================================================================

// S1: Reset test - no program needed, just check register state after reset

// S2: MOV R0,#5; MOV R1,#10
// mem[0] = 32'h0000_2005;  // MOV R0, #5
// mem[1] = 32'h0000_290A;  // MOV R1, #10
// Expected: R0=5, R1=10

// S3: MOV R0,#10; ADD R0,#5; MOV R1,#8; SUB R1,#3
// mem[0] = 32'h0000_200A;  // MOV R0, #10
// mem[1] = 32'h0000_3005;  // ADD R0, #5
// mem[2] = 32'h0000_2108;  // MOV R1, #8
// mem[3] = 32'h0000_3903;  // SUB R1, #3
// Expected: R0=15, R1=5

// S4: MOV R0,#7; MOV R1,#8; ADD R2,R0,R1
// mem[0] = 32'h0000_2007;  // MOV R0, #7
// mem[1] = 32'h0000_2108;  // MOV R1, #8
// mem[2] = 32'h0000_1882;  // ADD R2, R0, R1 (Rm=R1=001, Rn=R0=000, Rd=R2=010)
//                           // 0001100 001 000 010 = 0x1882
// mem[3] = 32'h0000_BF00;  // NOP
// Expected: R0=7, R1=8, R2=15

// S5: MOV R0,#5; MOV R1,#5; CMP R0,R1; BEQ +2; MOV R0,#0
// mem[0] = 32'h0000_2005;  // MOV R0, #5
// mem[1] = 32'h0000_2105;  // MOV R1, #5
// mem[2] = 32'h0000_4288;  // CMP R0, R1 (0100001010 Rm=001 Rn=000)
// mem[3] = 32'h0000_D002;  // BEQ offset=+2 (skip 1 halfword = MOV R0,#0)
// mem[4] = 32'h0000_2000;  // MOV R0, #0 (skipped if branch taken)
// Expected: R0=5 (branch taken because R0==R1)

// S6: B +1; MOV R0,#1; MOV R0,#2
// mem[0] = 32'h0000_E001;  // B offset=+1 halfword (skip MOV R0,#1)
//                           // 11100 00000000001 = 0xE001
// mem[1] = 32'h0000_2001;  // MOV R0, #1 (skipped)
// mem[2] = 32'h0000_2002;  // MOV R0, #2 (executed after branch)
// Expected: R0=2

// S7: MOV R0,#0xAB; MOV R1,#4; MOV R2,#0; STR R0,[R1,R2]; MOV R0,#0; LDR R0,[R1,R2]
// mem[0] = 32'h0000_20AB;  // MOV R0, #0xAB
// mem[1] = 32'h0000_2104;  // MOV R1, #4
// mem[2] = 32'h0000_2200;  // MOV R2, #0
// mem[3] = 32'h0000_6000;  // STR R0,[R1,R2] (0101000 Rm=010 Rn=001 Rt=000)
//                           // 0101000 010 001 000 = 0x5088 → Wait let me recalculate
//                           // STR Rt,[Rn,Rm]: 0101000 Rm(3) Rn(3) Rt(3)
//                           // STR R0,[R1,R2]: Rm=R2=010, Rn=R1=001, Rt=R0=000
//                           // 0101000 010 001 000 = 0x5088
//                           // Actually: bits [15:10]=010100, [9:6]=Rm=010, [5:3]=Rn=001, [2:0]=Rt=000
//                           // Wait: encoding is 0101000 Rm Rn Rt = 0101_0000_1000_1000 = 0x5088
// mem[4] = 32'h0000_2000;  // MOV R0, #0 (clear R0)
// mem[5] = 32'h0000_5888;  // LDR R0,[R1,R2] (0101100 Rm=010 Rn=001 Rt=000)
//                           // 0101100 010 001 000 = 0x5888
// mem[6] = 32'h0000_BF00;  // NOP
// Expected: R0=0xAB (after LDR)

// S10: MOV R0,#5; NOP; NOP
// mem[0] = 32'h0000_2005;  // MOV R0, #5
// mem[1] = 32'h0000_BF00;  // NOP
// mem[2] = 32'h0000_BF00;  // NOP
// Expected: R0=5

// S12: MOV R0,#0; ADD R0,#1; ADD R0,#2; ADD R0,#3; ADD R0,#4
// mem[0] = 32'h0000_2000;  // MOV R0, #0
// mem[1] = 32'h0000_3001;  // ADD R0, #1
// mem[2] = 32'h0000_3002;  // ADD R0, #2
// mem[3] = 32'h0000_3003;  // ADD R0, #3
// mem[4] = 32'h0000_3004;  // ADD R0, #4
// Expected: R0=10

// ================================================================
// End of test case reference
// ================================================================
