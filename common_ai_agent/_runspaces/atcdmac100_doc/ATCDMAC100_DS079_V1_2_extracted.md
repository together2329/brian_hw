# ATCDMAC100 DS079 V1.2 Extracted Requirement Evidence
- source: `/Users/brian/Desktop/andes/platform/AE210P_20161118/DOCS/AndeShape_ATCDMAC100_DS079_V1.2.pdf`
- sha256: `009859054f1992b6c64ec7e4e09402aad1b2ee21558c6c3cce48d91a4b231ac9`
- pages: 34
- extracted_at: 2026-05-18T02:21:25Z

This file is a mechanical text extraction used as ATLAS SSOT import evidence. Preserve source page markers when promoting facts into SSOT.


## Page 1

AAnnddeeSShhaappee™™
AATTCCDDMMAACC110000
DDaattaa SShheeeett
Document DS079-12
Number
Date Issued 2016-01-27
Copyright © 2014–2016 Andes Technology Corporation.
All rights reserved.

## Page 2

Copyright Notice
Copyright © 2014–2016 Andes Technology Corporation. All rights reserved.
AndesCore™, AndeShape™, AndeSight™, AndESLive™, AndeSoft™, AndeStar™, AICE™,
AICE-MCU™, AICE-MINI™, Andes Custom Extension™, and COPILOT™ are trademarks
owned by Andes Technology Corporation. All other trademarks used herein are the property of
their respective owners.
This document contains confidential information of Andes Technology Corporation. Use of this
copyright notice is precautionary and does not imply publication or disclosure. Neither the
whole nor part of the information contained herein may be reproduced, transmitted, transcribed,
stored in a retrieval system, or translated into any language in any form by any means without
the written permission of Andes Technology Corporation.
The product described herein is subject to continuous development and improvement;
information herein is given by Andes in good faith but without warranties.
This document is intended only to assist the reader in the use of the product. Andes Technology
Corporation shall not be liable for any loss or damage arising from the use of any information in
this document, or any incorrect use of the product.
Contact Information
Should you have any problems with the information contained herein, please contact Andes
Technology Corporation
by email support@andestech.com
or online website https://es.andestech.com/eservice/
for support giving:
 the document title
 the document number
 the page number(s) to which your comments apply
 a concise explanation of the problem
General suggestions for improvements are welcome.

## Page 3

AndeShape™ ATCDMAC100 Data Sheet
Revision History
Revised
Rev. Revision Date Revised Content
Chapter-Section
Revise the clear condition of channel abort register as
1.2 2016-01-27 3.8
write one clear
1.1 2015-09-09 1.1 Describe the multiple address width support
1.0 2014-03-06 All Initial release
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.

### Page 3 Table 1

Rev. | Revision Date | C | Revised |  | Revised Content
 |  |  | hapter-Section |  | 
1.2 | 2016-01-27 | 3.8 |  |  | Revise the clear condition of channel abort register as write one clear
1.1 | 2015-09-09 | 1.1 |  |  | Describe the multiple address width support
1.0 | 2014-03-06 | All |  |  | Initial release


## Page 4

AndeShape™ ATCDMAC100 Data Sheet
Table of Contents
COPYRIGHT NOTICE ............................................................................................................................................................. I
CONTACT INFORMATION ................................................................................................................................................... I
REVISION HISTORY ............................................................................................................................................................ II
LIST OF TABLES .....................................................................................................................................................................V
LIST OF FIGURES ................................................................................................................................................................ VI
1. INTRODUCTION ........................................................................................................................................................... 1
1.1. FEATURES .................................................................................................................................................................... 1
1.2. BLOCK DIAGRAM ......................................................................................................................................................... 1
1.3. FUNCTION DESCRIPTION ............................................................................................................................................ 2
1.3.1. Channel Arbitration ............................................................................................................................................ 3
1.3.2. Hardware Handshaking .................................................................................................................................... 3
1.3.3. Chain Transfer ..................................................................................................................................................... 4
1.3.4. Data Order ........................................................................................................................................................... 5
2. SIGNAL DESCRIPTION .............................................................................................................................................. 8
3. PROGRAMMING MODEL ......................................................................................................................................... 11
3.1. REGISTER SUMMARY .................................................................................................................................................. 11
3.2. REGISTER DESCRIPTION ........................................................................................................................................... 12
3.3. ID AND REVISION REGISTER (OFFSET 0X00) .......................................................................................................... 12
3.4. DMAC CONFIGURATION REGISTER (OFFSET 0X10) ............................................................................................... 13
3.5. DMAC CONTROL REGISTER (OFFSET 0X20)........................................................................................................... 14
3.6. INTERRUPT STATUS REGISTER (OFFSET 0X30) ....................................................................................................... 14
3.7. CHANNEL ENABLE REGISTER (OFFSET 0X34) ......................................................................................................... 15
3.8. CHANNEL ABORT REGISTER (OFFSET 0X40) ........................................................................................................... 15
3.9. CHANNEL N CONTROL REGISTER (OFFSET 0X44+N*0X14) .................................................................................... 16
3.10. CHANNEL N SOURCE ADDRESS REGISTER (OFFSET 0X48+N*0X14) ...................................................................... 19
3.11. CHANNEL N DESTINATION ADDRESS REGISTER (OFFSET 0X4C+N*0X14) ............................................................. 19
3.12. CHANNEL N TRANSFER SIZE REGISTER (OFFSET 0X50+N*0X14) .......................................................................... 20
3.13. CHANNEL N LINKED LIST POINTER REGISTER (OFFSET 0X54+N*0X14) ............................................................... 20
4. HARDWARE CONFIGURATION OPTIONS ...................................................................................................... 21
4.1. NUMBER OF DMA CHANNELS .................................................................................................................................. 21
4.2. FIFO SIZE ................................................................................................................................................................. 21
4.3. DMA REQUEST/ACKNOWLEDGE NUMBER .............................................................................................................. 21
4.4. DMA REQUEST SYNCHRONIZATION SUPPORT ......................................................................................................... 21
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.

## Page 5

AndeShape™ ATCDMAC100 Data Sheet
4.5. CHAIN TRANSFER SUPPORT ...................................................................................................................................... 22
4.6. ADDRESS WIDTH....................................................................................................................................................... 22
5. PROGRAMMING SEQUENCE ................................................................................................................................ 23
5.1. TRANSFER WITHOUT CHAIN TRANSFER ................................................................................................................... 23
5.1.1. Scenario .............................................................................................................................................................. 23
5.1.2. Program Sequence ............................................................................................................................................ 23
5.1.3. Interrupt Handling ........................................................................................................................................... 24
5.2. CHAIN TRANSFER ...................................................................................................................................................... 25
5.2.1. Scenario .............................................................................................................................................................. 25
5.2.2. Program Sequence ............................................................................................................................................ 25
5.2.3. Interrupt Handling ........................................................................................................................................... 25
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.

## Page 6

AndeShape™ ATCDMAC100 Data Sheet
List of Tables
TABLE 1. FORMAT OF LINKED LIST DESCRIPTOR .......................................................................................................................... 5
TABLE 2. ATCDMAC100 SIGNAL DEFINITION ............................................................................................................................ 9
TABLE 3. ATCDMAC100 REGISTER SUMMARY .......................................................................................................................... 11
TABLE 4. ID AND REVISION REGISTER ........................................................................................................................................ 12
TABLE 5. DMAC CONFIGURATION REGISTER ............................................................................................................................. 13
TABLE 6. DMAC CONTROL REGISTER......................................................................................................................................... 14
TABLE 7. INTERRUPT STATUS REGISTER ..................................................................................................................................... 14
TABLE 8. CHANNEL ENABLE REGISTER ....................................................................................................................................... 15
TABLE 9. CHANNEL ABORT REGISTER ......................................................................................................................................... 15
TABLE 10. CHANNEL N CONTROL REGISTER ............................................................................................................................... 16
TABLE 11. CHANNEL N SOURCE ADDRESS REGISTER .................................................................................................................. 19
TABLE 12. CHANNEL N DESTINATION ADDRESS REGISTER ......................................................................................................... 19
TABLE 13. CHANNEL N TRANSFER SIZE REGISTER ...................................................................................................................... 20
TABLE 14. CHANNEL LINKED LIST POINTER REGISTER .............................................................................................................. 20
TABLE 15. REGISTER SETUP SAMPLE FOR TRANSFER WITHOUT CHAIN TRANSFER ................................................................... 24
TABLE 16. REGISTER SETUP SAMPLE FOR TRANSFER WITH CHAIN TRANSFER .......................................................................... 26
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.

## Page 7

AndeShape™ ATCDMAC100 Data Sheet
List of Figures
FIGURE 1. ATCDMAC100 BLOCK DIAGRAM ................................................................................................................................ 1
FIGURE 2. EXAMPLE OF DMA DATA TRANSFERS.......................................................................................................................... 2
FIGURE 3. EXAMPLE OF HARDWARE HANDSHAKING ................................................................................................................... 3
FIGURE 4. LINKED LIST STRUCTURE FOR CHAIN TRANSFERS ...................................................................................................... 4
FIGURE 5. DATA ORDER AT THE DESTINATION WHEN THE SOURCE ADDRESS MODE IS THE INCREMENT MODE ...................... 6
FIGURE 6. DATA ORDER AT THE DESTINATION WHEN THE SOURCE ADDRESS MODE IS THE DECREMENT MODE ..................... 6
FIGURE 7. DATA ORDER AT THE DESTINATION WHEN THE SOURCE ADDRESS MODE IS THE FIXED MODE ................................ 7
FIGURE 8. ATCDMAC100 INTERFACES ....................................................................................................................................... 8
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.

## Page 8

AndeShape™ ATCDMAC100 Data Sheet
Typographical Convention Index
Document Element Font Font Style Size Color
Normal text Georgia Normal 12 Black
Command line, Lucida Console Normal 11 Indigo
source code or
file paths
VARIABLES OR LUCIDA CONSOLE BOLD + ALL-CAPS 11 INDIGO
PARAMETERS IN
COMMAND LINE,
SOURCE CODE OR
FILE PATHS
Note or warning Georgia Normal 12 Red
Hyperlink Georgia Underlined 12 Blue
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.

### Page 8 Table 1

 | Document Element |  | Font |  |  | Font Style |  |  | Size |  |  | Color | 
Normal text |  |  | Georgia |  | Normal |  |  | 12 |  |  | Black |  | 
Command line, source code or file paths |  |  | Lucida Console |  | Normal |  |  | 11 |  |  | Indigo |  | 
VARIABLES OR PARAMETERS IN COMMAND LINE, SOURCE CODE OR FILE PATHS |  |  | LUCIDA CONSOLE |  | BOLD + ALL-CAPS |  |  | 11 |  |  | INDIGO |  | 
Note or warning |  |  | Georgia |  | Normal |  |  | 12 |  |  | Red |  | 
Hyperlink |  |  | Georgia |  | Underlined |  |  | 12 |  |  | Blue |  | 


## Page 9

AndeShape™ ATCDMAC100 Data Sheet
1. Introduction
AndeShape™ ATCDMAC100 is a direct memory access controller which transfers regions of data
efficiently on bus.
1.1. Features
 Compliant with AMBA™ 2 AHB protocol specification
 Supports up to 8 DMA channels
 Supports up to 16 request/acknowledge pairs for hardware handshaking
 Provides the round-robin arbitration with 2 priority levels
 Supports 8/16/32-bit wide data transfer
 Supports 24/32-bit address bus
 Supports chain transfer
1.2. Block Diagram
Figure 1 shows the block diagram of ATCDMAC100, which contains one AHB master interface
for data transfer and one AHB slave interface for register programming.
AHB Bus
AHB Master AHB Slave
FIFO
DMA Core
Arbiter
ATCDMAC100
Figure 1. ATCDMAC100 Block Diagram
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.

## Page 10

AndeShape™ ATCDMAC100 Data Sheet
1.3. Function Description
ATCDMAC100 supports up to 8 DMA channels. Each DMA channel provides a set of registers to
describe the intended data transfers. Multiple DMA channels can be enabled concurrently, but
the DMA controller services one channel at a time.
Figure 2 shows an illustration of data transfer timing for a channel. To prevent channels from
being starved, the DMA controller services all ready-channels alternatively, performing at most
SrcBurstSize data transfers each time. Consequently, the data transfers of a channel may be split
into several chunks when the total transfer size (TranSize) is larger than the source burst size
(SrcBurstSize). When the overall data transfers of a channel complete, the DMA controller will
update the interrupt status register, IntStatus, and assert the dma_int interrupt signal if the
terminal count interrupt is enabled.
The data transfers of a channel will be stopped when an error occurs. The data transfers of a
channel can also be aborted by software. In either case, the DMA controller will disable the
channel, and assert dma_int if the corresponding interrupt is enabled.
TranSize Transfers
SrcBurstSize Transfers SrcBurstSize Transfers Remaining Transfers
R0 Rn W0 Wn’ R0 Rn W0 Wn’ R0 Rm W0 Wm’
Channel arbitration
dma_int
Figure 2. Example of DMA Data Transfers
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.

## Page 11

AndeShape™ ATCDMAC100 Data Sheet
1.3.1. Channel Arbitration
ATCDMAC100 provides two priority levels for channel arbitration. Every channel is associated
with a priority level by the Priority field of the channel control register, ChnCtrl. During the
channel arbitration, the DMA controller selects a high priority channel first. A low priority
channel is only selected if there is no high priority channel. Channels of the same priority level
will be selected by the round-robin scheme.
1.3.2. Hardware Handshaking
ATCDMAC100 provides up to 16 pairs of hardware handshake signals (dma_req/dma_ack) for
data transfers with low-speed devices. Figure 3 gives an example of hardware handshaking. The
device should assert dma_req only when it prepares enough data to transfer or when it has
enough empty space to receive the incoming data. The DMA controller only issues bus requests
to read/write the data when it sees the dma_req asserted, avoiding holding the bus in the wait
state indefinitely. The DMA controller asserts dma_ack when it completes SrcBurstSize data
transfers from/to the device. The device should de-assert dma_req after detecting the assertion
of dma_ack. The DMA controller should de-assert dma_ack after detecting the de-assertion of
dma_req. If an error is encountered during the data transfers, the DMA controller will disable
the channel without asserting dma_ack. The error handling software should reset both the
source and destination of the DMA transfer to deassert dma_req.
SrcBurstSize Transfers SrcBurstSize Transfers
dma_req
dma_ack
Figure 3. Example of Hardware Handshaking
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.

## Page 12

AndeShape™ ATCDMAC100 Data Sheet
1.3.3. Chain Transfer
ATCDMAC100 provides the chain transfer function, with which multiple blocks of data can be
transferred consecutively without the intervention of the main processor.
Before a chain transfer is started, a linked list structure must be built to describe the data blocks
to move and the associated control setups. The first element of the list (the head of the list) is
described by the channel control registers. The rest of elements of the list are specified by the
linked list descriptors stored in the memory, where the linked list descriptor holds the control
values to load to the channel control registers to continue the data transfer. Figure 4 shows an
example of the linked list structure.
When the channel is enabled, the DMA controller will first transfer data according to the
channel control registers. After the data transfer completes, the DMA controller will continue the
data transfer by following the ChnLLPointer. The content of the linked list descriptor pointed by
ChnLLPointer will be loaded to the channel control registers if ChnLLPointer is not zero. The
loaded descriptor becomes the new head of the list and this process repeats until the
ChnLLPointer is zero.
Head of List 2’nd Element 3’rd Element 4’th Element
ChnCtrl Ctrl Ctrl Ctrl
ChnSrcAddr SrcAddr SrcAddr SrcAddr
ChnDstAddr DstAddr DstAddr DstAddr
ChnTranSize TranSize TranSize TranSize
ChnLLPointer LLPointer LLPointer LLPointer (0)
Channel Control Registers Descriptors in Memory
Figure 4. Linked List Structure for Chain Transfers
When the terminal count interrupt (IntTCMask) of a channel is enabled, the DMA controller will
generate an interrupt and disable the channel when the data transfer for the head of the list is
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.

### Page 12 Table 1

ChnCtrl
ChnSrcAddr
ChnDstAddr
ChnTranSize
ChnLLPointer


### Page 12 Table 2

Ctrl
SrcAddr
DstAddr
TranSize
LLPointer


### Page 12 Table 3

Ctrl
SrcAddr
DstAddr
TranSize
LLPointer


### Page 12 Table 4

Ctrl
SrcAddr
DstAddr
TranSize
LLPointer (0)


## Page 13

AndeShape™ ATCDMAC100 Data Sheet
done. If the ChnLLPointer is not zero, the channel control registers will be preloaded with the
next descriptor before the interrupt is generated. The interrupt handling software could resume
the chain transfer by just re-enabling the channel.
Table 1 shows the format of the linked list descriptor. The bit field definition of each descriptor
word is the same as the corresponding channel control register except the channel enable bit,
which is reserved in the linked list descriptor.
Table 1. Format of Linked List Descriptor
Name Offset Description Format
Ctrl 0x00 Channel control See Table 10
SrcAddr 0x04 Source address See Table 11
DstAddr 0x08 Destination address See Table 12
TranSize 0x0C Total transfer size See Table 13
LLPointer 0x10 Linked list pointer See Table 14
1.3.4. Data Order
ATCDMAC100 provides three address control modes: increment mode, decrement mode, and
fixed mode. At the increment mode, the address is increased after the DMA controller accesses a
data of the source/destination. At the decrement mode, the address is decreased after the DMA
controller accesses a data of the source/destination. At the fixed mode, the address remains
unchanged after the DMA controller accesses a data of the source/destination.
When the address control mode of the source is the same as that of the destination, the DMA
controller maintains the same byte order of the data between the source and the destination.
When the address control mode of the source is opposite to that of the destination, the data
written to the destination will be in the reverse byte order of that read from the source. The data
order of the fixed mode is treated the same as that of the increment mode.
Figure 5, Figure 6 and Figure 7 illustrate the byte order of the data at the destination when the
source address mode is increment, decrement, and fixed respectively.
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.

## Page 14

AndeShape™ ATCDMAC100 Data Sheet
d c
0xc
b a 9 8
0x8
Destination: Increment
7 6 5 4
0x2 ~ 0xd 0x4
Source: Increment
3 2
0x2 ~ 0xd 0x0
f e d c 2 3
0xc 0xc
b a 9 8 4 5 6 7
0x8 0x8
Destination: decrement
7 6 5 4 8 9 a b
0x4 0xd ~ 0x2 0x4
3 2 1 0 c d
0x0 0x0
0xc
0x8
Destination: fixed
d c b a
0x4 0x4
0x0
Figure 5. Data Order at the Destination when the Source Address Mode is the Increment Mode
2 3
0xc
4 5 6 7
0x8
Destination: Increment
8 9 a b
0x2 ~ 0xd 0x4
Source: decrement
c d
0xd ~ 0x2 0x0
f e d c f e d c
0xc 0xc
b a 9 8 b a 9 8
0x8 0x8
Destination: decrement
7 6 5 4 7 6 5 4
0x4 0xd ~ 0x2 0x4
3 2 1 0 3 2 1 0
0x0 0x0
0xc
0x8
Destination: fixed
2 3 4 5
0x4 0x4
0x0
Figure 6. Data Order at the Destination when the Source Address Mode is the Decrement Mode
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.

### Page 14 Table 1

 |  | d | c
b | a | 9 | 8
7 | 6 | 5 | 4
3 | 2 |  | 


### Page 14 Table 2

f | e |  |  | d | c
b | a |  | 9 |  | 
 |  |  |  |  | 8
7 | 6 |  | 5 |  | 4
3 | 2 |  | 1 |  | 0


### Page 14 Table 3

 |  | 2 | 3
4 | 5 | 6 | 7
8 | 9 | a | b
c | d |  | 


### Page 14 Table 4

d | c | b | a


### Page 14 Table 5

 |  | 2 | 3
4 | 5 | 6 | 7
8 | 9 | a | b
c | d |  | 


### Page 14 Table 6

f | e | d | c
b | a | 9 | 8
7 | 6 | 5 | 4
3 | 2 | 1 | 0


### Page 14 Table 7

f | e | d | c
b | a | 9 | 8
7 | 6 | 5 | 4
3 | 2 | 1 | 0


### Page 14 Table 8

2 | 3 | 4 | 5


## Page 15

AndeShape™ ATCDMAC100 Data Sheet
7 6
0xc
5 4 7 6
0x8
Destination: Increment
5 4 7 6
0x2 ~ 0xd 0x4
Source: Fixed
5 4
0x4 0x0
f e d c 4 5
0xc 0xc
b a 9 8 6 7 4 5
0x8 0x8
Destination: decrement
7 6 5 4 6 7 4 5
0x4 0xd ~ 0x2 0x4
3 2 1 0 6 7
0x0 0x0
0xc
0x8
Destination: fixed
7 6 5 4
0x4 0x4
0x0
Figure 7. Data Order at the Destination when the Source Address Mode is the Fixed Mode
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.

### Page 15 Table 1

 |  | 7 | 6
5 | 4 | 7 | 6
5 | 4 | 7 | 6


### Page 15 Table 2

 |  | d | c
b | a | 9 | 8
7 | 6 | 5 | 
 |  |  | 4
3 | 2 | 1 | 0


### Page 15 Table 3

6 | 7 | 4 | 5
6 | 7 | 4 | 5
6 | 7 |  | 


### Page 15 Table 4

7 | 6 | 5 | 4


## Page 16

AndeShape™ ATCDMAC100 Data Sheet
2. Signal Description
Figure 8 shows the interfaces of the ATCDMAC100.
hclk haddr_mst[31:0]
hresetn htrans_mst[1:0]
haddr[31:0] hwrite_mst
htrans[1:0] hsize_mst[2:0]
hwrite hprot_mst[3:0]
hsize[2:0] hlock_mst
hburst[2:0] hburst_mst[2:0]
hwdata[31:0] hwdata_mst[31:0]
hsel ATCDMAC100 hrdata_mst[31:0]
hreadyin hready_mst
hrdata[31:0] hresp_mst[1:0]
hresp[1:0] hbusreq_mst
hready hgrant_mst
dma_int
dma_req[15:0]
dma_ack[15:0]
Figure 8. ATCDMAC100 Interfaces
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.

## Page 17

AndeShape™ ATCDMAC100 Data Sheet
Table 2 gives the detailed descriptions of ATCDMAC100 I/O signals.
Table 2. ATCDMAC100 Signal Definition
Signal Name I/O Type Description
AHB global signals
hclk I System bus clock
hresetn I System bus reset
DMA signals
dma_int O Interrupt request
dma_req[M:0] I Burst transfer request
(M is ATCDMAC100_REQ_ACK_NUM – 1)
dma_ack[M:0] O Burst transfer acknowledge
AHB slave signals
haddr[N:0] I AHB address bus
(N is 23 and 31 for AHB 24-bit and 32-bit address,
respectively)
htrans[1:0] I AHB transfer type
hwrite I AHB write signal
hsize[2:0] I AHB transfer size
hburst[2:0] I AHB burst type
hwdata[31:0] I AHB write data bus
hsel I AHB slave select signal
hreadyin I AHB ready input
hrdata[31:0] O AHB read data bus
hresp[1:0] O AHB transfer response
hready O AHB ready output
AHB master signals
haddr_mst[N:0] O AHB address bus
htrans_mst[1:0] O AHB transfer type
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.

### Page 17 Table 1

 | Signal Name |  |  | I/O Type |  | Description
 | AHB global signa | ls |  |  |  | 
 | hclk |  |  | I |  | System bus clock
 | hresetn |  |  | I |  | System bus reset
 | DMA signals |  |  |  |  | 
 | dma_int |  |  | O |  | Interrupt request
dma_req[M:0] | dma_req[M:0] |  | I | I |  | Burst transfer request
 |  |  |  |  |  | (M is ATCDMAC100_REQ_ACK_NUM – 1)
 | dma_ack[M:0] |  |  | O |  | Burst transfer acknowledge
 | AHB slave signals |  |  |  |  | 
haddr[N:0] | haddr[N:0] |  | I | I |  | AHB address bus
 |  |  |  |  |  | (N is 23 and 31 for AHB 24-bit and 32-bit address,
 |  |  |  |  |  | respectively)
 | htrans[1:0] |  |  | I |  | AHB transfer type
 | hwrite |  |  | I |  | AHB write signal
 | hsize[2:0] |  |  | I |  | AHB transfer size
 | hburst[2:0] |  |  | I |  | AHB burst type
 | hwdata[31:0] |  |  | I |  | AHB write data bus
 | hsel |  |  | I |  | AHB slave select signal
 | hreadyin |  |  | I |  | AHB ready input
 | hrdata[31:0] |  |  | O |  | AHB read data bus
 | hresp[1:0] |  |  | O |  | AHB transfer response
 | hready |  |  | O |  | AHB ready output
 | AHB master signals |  |  |  |  | 
 | haddr_mst[N:0] |  |  | O |  | AHB address bus
 | htrans_mst[1:0] |  |  | O |  | AHB transfer type


## Page 18

AndeShape™ ATCDMAC100 Data Sheet
Signal Name I/O Type Description
hwrite_mst O AHB write signal
hsize_mst[2:0] O AHB transfer size
hprot_mst[3:0] O AHB protection control
hlock_mst O AHB lock request
hburst_mst[2:0] O AHB burst type
hwdata_mst[31:0] O AHB write data bus
hrdata_mst[31:0] I AHB read data bus
hresp_mst[1:0] I AHB transfer response
hready_mst I AHB data ready input
hbusreq_mst O AHB bus request signal
hgrant_mst I AHB bus grant signal
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.

### Page 18 Table 1

 | Signal Name |  |  | I/O Type |  | Description
 | hwrite_mst |  |  | O |  | AHB write signal
 | hsize_mst[2:0] |  |  | O |  | AHB transfer size
 | hprot_mst[3:0] |  |  | O |  | AHB protection control
 | hlock_mst |  |  | O |  | AHB lock request
 | hburst_mst[2:0] |  |  | O |  | AHB burst type
 | hwdata_mst[31:0] |  |  | O |  | AHB write data bus
 | hrdata_mst[31:0] |  |  | I |  | AHB read data bus
 | hresp_mst[1:0] |  |  | I |  | AHB transfer response
 | hready_mst |  |  | I |  | AHB data ready input
 | hbusreq_mst |  |  | O |  | AHB bus request signal
 | hgrant_mst |  |  | I |  | AHB bus grant signal


### Page 18 Table 2



## Page 19

AndeShape™ ATCDMAC100 Data Sheet
3. Programming Model
3.1. Register Summary
Table 3. ATCDMAC100 Register Summary shows a summary of the ATCDMAC100 registers.
Table 3. ATCDMAC100 Register Summary
Offset Name Description
ID and revision register
+0x00 IdRev ID and revision register
+0x04~0x0C - Reserved
Configuration register
+0x10 DMACfg DMAC configuration register
+0x14~0x1C - Reserved
Global control registers
+0x20 DMACtrl DMAC control register
+0x24~0x2C - Reserved
Channel status register
+0x30 IntStatus Interrupt status register
+0x34 ChEN Channel enable register
+0x38~0x3c - Reserved
Channel control registers
+0x40 ChAbort Channel abort register
+0x44 + n*0x14 ChnCtrl Channel n control register
+0x48 + n*0x14 ChnSrcAddr Channel n source address register
+0x4c + n*0x14 ChnDstAddr Channel n destination address register
+0x50 + n*0x14 ChnTranSize Channel n transfer size register
+0x54 + n*0x14 ChnLLPointer Channel n linked list pointer register
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.

## Page 20

AndeShape™ ATCDMAC100 Data Sheet
3.2. Register Description
The following sections describe ATCDMAC100 registers in detail. The abbreviations for the Type
column are summarized below:
RO: read only
WO: write only
R/W: readable and writable
R/W1C: readable and write 1 to clear
3.3. ID and Revision Register (Offset 0x00)
This register holds the ID number and the revision number. The reset values of the two revision
fields are revision dependent.
Table 4. ID and Revision Register
Name Bit Type Description Reset
ID 31:12 RO ID number for DMAC 0x01021
RevMajor 11:4 RO Major revision number Revision
dependent
RevMinor 3:0 RO Minor revision number Revision
dependent
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.

## Page 21

AndeShape™ ATCDMAC100 Data Sheet
3.4. DMAC Configuration Register (Offset 0x10)
Table 5. DMAC Configuration Register
Name Bit Type Description Reset
ChainXfr 31 RO Chain transfer Configuration
0x0: chain transfer is not configured dependent
0x1: chain transfer is configured
ReqSync 30 RO DMA request synchronization. The DMA Configuration
request synchronization should be configured dependent
to avoid signal integrity problems when the
request signal is not clocked by the system bus
clock, which the DMA control logic operates
in. If the request synchronization is not
configured, the request signal is sampled
directly without synchronization.
0x0: request synchronization is not configured
0x1: request synchronization is configured
Reserved 29:15 - - -
ReqNum 14:10 RO Request/acknowledge number Configuration
dependent
FIFODepth 9:4 RO FIFO depth Configuration
dependent
ChannelNum 3:0 RO Channel number Configuration
dependent
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.

## Page 22

AndeShape™ ATCDMAC100 Data Sheet
3.5. DMAC Control Register (Offset 0x20)
Table 6. DMAC Control Register
Name Bit Type Description Reset
Reserved 31:1 - - -
Reset 0 WO Software reset control. Set this bit to 1 to reset 0x0
the DMA core and disable all channels.
3.6. Interrupt Status Register (Offset 0x30)
This register contains the terminal count, error, and abort status. The terminal count status of a
channel is asserted when the channel encounters the terminal counter event. The error/abort
status of a channel is asserted when the channel encounters the error/abort event. There is one
bit of status for each channel and the status bit is zero when the corresponding channel is not
configured.
Table 7. Interrupt Status Register
Name Bit Type Description Reset
Reserved 31:24 - - -
TC 23:16 R/W1C The terminal count status of DMA channels, one 0x0
bit per channel. The terminal count status is
asserted when a channel transfer finishes
without abort or error event.
0x0: channel N has no terminal count status
0x1: channel N has terminal count status
Abort 15:8 R/W1C The abort status of channel, one bit per channel. 0x0
The abort status is asserted when a channel
transfer is aborted.
0x0: channel N has no abort status
0x1: channel N has abort status
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.

## Page 23

AndeShape™ ATCDMAC100 Data Sheet
Name Bit Type Description Reset
Error 7:0 R/W1C The error status, one bit per channel. The error 0x0
status is asserted when a channel transfer
encounters the following error events:
 Bus error
 Unaligned address
 Unaligned transfer width
 Reserved configuration
0x0: channel N has no error status
0x1: channel N has error status
3.7. Channel Enable Register (Offset 0x34)
The register shows the DMA channel enable status. The status fields only exist when the
corresponding channels are configured. This register is an alias of the Enable fields of all
ChnCtrl registers.
Table 8. Channel Enable Register
Name Bit Type Description Reset
ChEN N:0 RO Alias of the Enable field of all ChnCtrl registers 0x0
3.8. Channel Abort Register (Offset 0x40)
The register controls the abortion of the DMA channel transfers, one-bit per channel. Write 1 to
stop the current transfer of the corresponding channel. The abort bit is automatically cleared by
hardware when the corresponding status bit in the interrupt status register is cleared.
Table 9. Channel Abort Register
Name Bit Type Description Reset
ChAbort N:0 WO Write 1 to this field to stop the channel transfer. 0x0
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.

## Page 24

AndeShape™ ATCDMAC100 Data Sheet
Name Bit Type Description Reset
The bits can only be set when the corresponding
channels are enabled. Otherwise, the writes will
be ignored for channels that are not enabled.
3.9. Channel n Control Register (Offset 0x44+n*0x14)
Table 10. Channel n Control Register
Name Bit Type Description Reset
Reserved 31:30 - - -
Priority 29 R/W Channel priority level 0x0
0x0: lower priority
0x1: higher priority
Reserved 28:25 - - -
SrcBurstSize 24:22 R/W Source burst size. This field indicates the 0x0
number of transfers before DMA channel
re-arbitration.
Total byte of a burst is SrcBurstSize * SrcWidth.
0x0: 1 transfer
0x1: 2 transfers
0x2: 4 transfers
0x3: 8 transfers
0x4: 16 transfers
0x5: 32 transfers
0x6: 64 transfers
0x7: 128 transfers
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.

## Page 25

AndeShape™ ATCDMAC100 Data Sheet
Name Bit Type Description Reset
SrcWidth 21:20 R/W Source transfer width 0x2
0x0: byte transfer
0x1: half-word transfer
0x2: word transfer
0x3: reserved, setting the field with this value
triggers error exception
DstWidth 19:18 R/W Destination transfer width. 0x2
Both the total transfer byte and the total burst
bytes should be aligned to the destination
transfer width; otherwise the error event will be
triggered. For example, destination transfer
width should be set as byte transfer if total
transfer byte is not aligned to word or half-word.
See SrcBurstSize field above for the definition of
total burst byte and section 3.12 for the
definition of the total transfer bytes.
0x0: byte transfer
0x1: half-word transfer
0x2: word transfer
0x3: reserved, set the field as this value triggers
error exception
SrcMode 17 R/W Source DMA handshake mode 0x0
0x0: normal mode
0x1: handshake mode
DstMode 16 R/W Destination DMA handshake mode 0x0
0x0: normal mode
0x1: handshake mode
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.

## Page 26

AndeShape™ ATCDMAC100 Data Sheet
Name Bit Type Description Reset
SrcAddrCtrl 15:14 R/W Source address control 0x0
0x0: increment address
0x1: decrement address
0x2: fixed address
0x3: reserved, setting the field with this value
triggers the error exception
DstAddrCtrl 13:12 R/W Destination address control 0x0
0x0: increment address
0x1: decrement address
0x2: fixed address
0x3: reserved, setting the field with this value
triggers the error exception
SrcReqSel 11:8 R/W Source DMA request select. Select the 0x0
request/ack handshake pair that the source
device is connected to.
DstReqSel 7:4 R/W Destination DMA request select. Select the 0x0
request/ack handshake pair that the destination
device is connected to.
IntAbtMask 3 R/W Channel abort interrupt mask 0x0
0x0: allow the abort interrupt to be triggered
0x1: disable the abort interrupt
IntErrMask 2 R/W Channel error interrupt mask 0x0
0x0:allow the error interrupt to be triggered
0x1: disable the error interrupt
IntTCMask 1 R/W Channel terminal count interrupt mask. 0x0
0x0: allow the terminal count interrupt to be
triggerd
0x1: disable the terminal count interrupt
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.

## Page 27

AndeShape™ ATCDMAC100 Data Sheet
Name Bit Type Description Reset
Enable 0 R/W Channel enable bit 0x0
0x0: disable
0x1: enable
3.10. Channel n Source Address Register (Offset 0x48+n*0x14)
Table 11. Channel n Source Address Register
Name Bit Type Description Reset
SrcAddr 31:0 R/W Source starting address. When a transfer 0x0
completes, its value is updated to the ending
address + sizeof(SrcWidth).
This address must be aligned to the source
transfer size; otherwise, an error event will be
triggered.
3.11. Channel n Destination Address Register (Offset 0x4C+n*0x14)
Table 12. Channel n Destination Address Register
Name Bit Type Description Reset
DstAddr 31:0 R/W Destination starting address. When a transfer 0x0
completes, its value is updated to the ending
address + sizeof(DstWidth).
This address must be aligned to the destination
transfer size; otherwise the error event will be
triggered.
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.

## Page 28

AndeShape™ ATCDMAC100 Data Sheet
3.12. Channel n Transfer Size Register (Offset 0x50+n*0x14)
Table 13. Channel n Transfer Size Register
Name Bit Type Description Reset
Reserved 31:22 - - -
TranSize 21:0 R/W Total transfer size from source. The total 0x0
number of transferred bytes is TranSize *
SrcWidth. The value is updated to zero when
the DMA transfer is done.
If a channel is enabled with zero total transfer
size, the error event will be triggered and the
transfer will be terminated.
3.13. Channel n Linked List Pointer Register (Offset 0x54+n*0x14)
Table 14. Channel Linked List Pointer Register
Name Bit Type Description Reset
LLPointer 31:2 R/W Pointer to the next block descriptor. The pointer 0x0
must be word aligned.
Reserved 1:0 - - -
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.

## Page 29

AndeShape™ ATCDMAC100 Data Sheet
4. Hardware Configuration Options
4.1. Number of DMA Channels
Define ATCDMAC100_CH_NUM_n to specify the number of DMA channels, where n=1~8.The
following example configures ATCDMAC100 with 4 channels:
`define ATCDMAC100_CH_NUM_4
4.2. FIFO Size
Define ATCDMAC100_FIFO_DEPTH_n to specify the FIFO size as n entries (each entry is
32-bit). n could be 4, 8, 16, and 32. The following example configures the FIFO size as 8 entries:
`define ATCDMAC100_FIFO_DEPTH_8
4.3. DMA Request/Acknowledge Number
Define ATCDMAC100_REQ_ACK_NUM to specify the number of request/acknowledge pairs
for hardware handshaking. The value could be 1 to 16. The following example configures
ATCDMAC100 with 8 request/acknowledge pairs.
`define ATCDMAC100_REQ_ACK_NUM 8
4.4. DMA Request Synchronization Support
Define ATCDMAC100_REQ_SYNC_SUPPORT to add synchronizers at all DMA request input
ports. Under this configuration, the DMA requests are allowed to be clocked by different clocks
other than the system bus clock.
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.

## Page 30

AndeShape™ ATCDMAC100 Data Sheet
4.5. Chain Transfer Support
Define ATCDMAC100_CHAIN_TRANSFER_SUPPORT to support the chain transfer.
4.6. Address Width
Define ATCDMAC100_ADDR_WIDTH_24 to set the address width to 24-bit. Default address
width is 32-bit.
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.

## Page 31

AndeShape™ ATCDMAC100 Data Sheet
5. Programming Sequence
5.1. Transfer without Chain Transfer
5.1.1. Scenario
The following sample programming sequence sets up channel 2 for
 Transfer of 32-words
 Source: 32-bit wide system memory
 Destination: fixed address, 32-bit wide device
 32-tansfer burst
 Hardware handshaking is enabled. Source is connected to pair 1 and destination is
connected to pair 2.
 All interrupts are enabled
5.1.2. Program Sequence
1. Check ChannelNum in the Configuration Register (0x10) bit[3:0] for the existence of
channel 2.
2. Set Channel Control Registers of channel 2 as Table 15. Ch2Ctrl should be programmed the
last since the DMA channel becomes enabled once the register is programmed.
3. Wait for the DMA interrupt and check the Interrupt Status Register (0x30).
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.

## Page 32

AndeShape™ ATCDMAC100 Data Sheet
5.1.3. Interrupt Handling
The following example demonstrates DMA interrupt handling:
1. Check Interrupt Status Register (0x30) to determine the cause of the interruption.
2. Handle the interrupt accordingly.
3. Clear interrupt status by writing 1’s to the Interrupt Status Register.
Table 15. Register Setup Sample for Transfer without Chain Transfer
Name Offset Value of the control register
Ch2Ctrl 0x44+2*0x14
0x216B2121
Field Value
Priority 0x1
SrcBurstSize 0x5
SrcWidth 0x2
DstWidth 0x2
SrcMode 0x1
DstMode 0x1
SrcAddrCtrl 0x0
DstAddrCtrl 0x2
SrcReqSel 0x1
DstReqSel 0x2
IntAbtMask 0x0
IntErrMask 0x0
IntTCMask 0x0
Enable 0x1
Ch2SrcAddr 0x48+2*0x14 The source address
Ch2DstAddr 0x4c+2*0x14 The destination address
Ch2TranSize 0x50+2*0x14 32
Ch2LLPointer 0x54+2*0x14 0x0
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.

## Page 33

AndeShape™ ATCDMAC100 Data Sheet
5.2. Chain Transfer
5.2.1. Scenario
The following sample programming sequence sets up channel 0 for
 Transfer of 128 words split into four 32-word discontinuous data blocks
 Source: 32-bit wide memory
 Destination: fixed address, 32-bit wide device
 32-transfer burst
 Hardware handshake is disabled
 All interrupts are enabled
5.2.2. Program Sequence
1. Check ChannelNum in the Configuration Register (0x10) bit[3:0] for the existence of
channel 0.
2. Create a linked list of block descriptors for the last three data blocks. Each block descriptor
describes the transfer for the respective 32-word data block.
3. Set Channel Control Registers according to Table 16 for the first data block and start the
transfer. Ch0Ctrl should be programmed the last since the DMA channel becomes enabled
once the register is programmed.
4. Wait for the DMA interrupt and check the Interrupt Status Register (0x30).
5.2.3. Interrupt Handling
The following sequence demonstrates DMA interrupt handling for chain transfers:
1. Check Interrupt Status Register (0x30) to determine the cause of the interruption.
2. Handle the interrupt accordingly.
3. Clear interrupt status by writing 1’s to the Interrupt Status Register.
4. Enable the channel if the interruption type is the terminal count interrupt and the chain
transfer has more blocks to transfer (CnLLPointer !=0).
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.

## Page 34

AndeShape™ ATCDMAC100 Data Sheet
Table 16. Register Setup Sample for Transfer with Chain Transfer
Name Offset Value of the control register
Ch0Ctrl 0x44+0*0x14
0x2168200F
Field Value
Priority 0x1
SrcBurstSize 0x5
SrcWidth 0x2
DstWidth 0x2
SrcMode 0x0
DstMode 0x0
SrcAddrCtrl 0x0
DstAddrCtrl 0x2
SrcReqSel 0x1
DstReqSel 0x2
IntAbtMask 0x1
IntErrMask 0x1
IntTCMask 0x1
Enable 0x1
Ch0SrcAddr 0x48+0*0x14 The source address for the first data block
Ch0DstAddr 0x4c+0*0x14 The destination address (fixed)
Ch0TranSize 0x50+0*0x14 32
Ch0LLPointer 0x54+0*0x14 Pointer to the subsequent link list descriptor in the memory
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.
