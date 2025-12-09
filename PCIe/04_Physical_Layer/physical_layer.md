# 4. Physical Layer Logical Block 

### 4.1 Introduction

The Physical Layer isolates the Transaction and Data Link Layers from the signaling technology used for Link data interchange. The Physical Layer is divided into the logical and electrical sub-blocks (see § Figure 4-1).
![img-0.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-0.jpeg)

Figure 4-1 Layering Diagram Highlighting Physical Layer
§ Chapter 4. describes the logical suㅌb-block and § Chapter 8. describes the electrical sub-block. ${ }^{64}$

### 4.2 Logical Sub-block 5

The logical sub-block has two main sections: a Transmit section that prepares outgoing information passed from the Data Link Layer for transmission by the electrical sub-block, and a Receiver section that identifies and prepares received information before passing it to the Data Link Layer.

The logical sub-block and electrical sub-block coordinate the state of each Transceiver through a status and control register interface or functional equivalent. The logical sub-block directs control and management functions of the Physical Layer.

PCI Express uses three types of encoding (8b/10b, 128b/130b, and 1b/1b) and two Data Stream modes (Flit Mode and Non-Flit Mode). A Data Stream in the Non-Flit Mode is defined as a contiguous collection of TLPs, DLLPs, and Logical Idle/IDL Token, starting at the end of an Ordered Set and ending with another Ordered Set or a Link Electrical Idle. A Data Stream in Flit Mode is defined as a set of Flits (see § Section 4.2.3), starting at the end of the first SKP Ordered Set after an SDS Ordered Set, and ending with the last Flit prior to an Ordered Set other than SKP Ordered Set that causes the Link to exit out of L0 state or if the Link enters Electrical Idle. The encoding is determined by the Data Rate of the Link. The Data Stream mode is determined during initial Link training. If not disabled (see Flit Mode Disable) and if both the Ports (and all Pseudo-Ports, if any) support it, (see Flit Mode Supported), Flit Mode is chosen. Otherwise, Non-Flit Mode is chosen. See § Table 4-1 for valid encoding and symbol placement mode combinations.

[^0]
[^0]:    64. Prior to [PCle-4.0] § Chapter 4. described both logical and electrical sub-blocks. With [PCle-4.0], the electrical section was moved to a new § Chapter 8. and a new Retimer section was added.

Table 4-1 Valid Encoding and Data Stream Mode Combinations

| Current Data Rate | Flit Mode Negotiated <br> during Configuration <br> when LinkUp=0b | Encoding | Data Stream |  |
| :--: | :--: | :--: | :--: | :--: |
| $2.5 \mathrm{GT} / \mathrm{s}, 5.0 \mathrm{GT} / \mathrm{s}$ | No | $8 \mathrm{~b} / 10 \mathrm{~b}$ | Non-Flit Mode |  |
| $2.5 \mathrm{GT} / \mathrm{s}, 5.0 \mathrm{GT} / \mathrm{s}$ | Yes | $8 \mathrm{~b} / 10 \mathrm{~b}$ | Flit Mode |  |
| $8.0 \mathrm{GT} / \mathrm{s}, 16.0 \mathrm{GT} / \mathrm{s}, 32.0 \mathrm{GT} / \mathrm{s}$ | No | $128 \mathrm{~b} / 130 \mathrm{~b}$ | Non-Flit Mode |  |
| $8.0 \mathrm{GT} / \mathrm{s}, 16.0 \mathrm{GT} / \mathrm{s}, 32.0 \mathrm{GT} / \mathrm{s}$ | Yes | $128 \mathrm{~b} / 130 \mathrm{~b}$ | Flit Mode |  |
| $64.0 \mathrm{GT} / \mathrm{s}$ | Yes (mandatory) | $1 \mathrm{~b} / 1 \mathrm{~b}$ | Flit Mode |  |

The Ordered Set encoding follows the $8 \mathrm{~b} / 10 \mathrm{~b}, 128 \mathrm{~b} / 130 \mathrm{~b}$, and $1 \mathrm{~b} / 1 \mathrm{~b}$ encoding as defined in $\S$ Table 4-2.
Table 4-2 Valid Encoding for Ordered Sets

| Current <br> Data Rate | Flit Mode Negotiated <br> during Configuration <br> when LinkUp=0b | Encoding | Comments |
| :--: | :--: | :--: | :-- |
| 2.5 GT/s, <br> $5.0 \mathrm{GT} / \mathrm{s}$ | Yes / No | $8 \mathrm{~b} / 10 \mathrm{~b}$ | Same Ordered Sets are used in Flit Mode as well as Non-Flit Mode. |
| $8.0 \mathrm{GT} / \mathrm{s}$ | No | $128 \mathrm{~b} /$ <br> 130b | Only Standard SKP Ordered Set sent when SKP OS needs to be sent. Rest of the <br> Ordered Sets are identical for Non-Flit Mode and Flit Mode in 8.0 GT/s. |
| $16.0 \mathrm{GT} / \mathrm{s}$, <br> $32.0 \mathrm{GT} / \mathrm{s}$ | No | $128 \mathrm{~b} /$ <br> 130b | Alternates between Standard SKP OS and Control SKP OS, when SKP OS needs <br> to be sent. Rest of the Ordered Sets are identical for Non-Flit Mode and Flit <br> Mode in the corresponding Data Rate. |
| $8.0 \mathrm{GT} / \mathrm{s}$, <br> $16.0 \mathrm{GT} / \mathrm{s}$, <br> $32.0 \mathrm{GT} / \mathrm{s}$ | Yes | $128 \mathrm{~b} /$ <br> 130b | Alternates between Standard SKP OS and Control SKP OS, when SKP OS needs <br> to be sent. Rest of the Ordered Sets are identical for Non-Flit Mode and Flit <br> Mode in the corresponding Data Rate. |
| $64.0 \mathrm{GT} / \mathrm{s}$ | Yes (mandatory) | $1 \mathrm{~b} / 1 \mathrm{~b}$ | All Ordered Sets follow 1b/1b encoding at 64.0 GT/s with PAM4 signaling. Only <br> Control SKP OS sent when SKP OS needs to be sent. |

# IMPLEMENTATION NOTE: 

## FLIT MODE IDENTIFICATION THROUGHOUT THE DOCUMENT

Support for Flit Mode behavior is referenced five times in the specification through the use of the following fields/ variables:

## Flit Mode Supported bit

Bit 0 of the Data Rate Identifier Symbol of 8b/10b and 128b/130b encoded TS1s and TS2s. This bit is Set when the Flit Mode Supported bit in the PCI Express Capabilities Register is Set and the Flit Mode Disable bit in the Link Control Register is Clear. See § Table 4-34, § Table 4-35, and § Table 4-36.

## Flit_Mode_Enabled

Variable that indicates whether or not Flit Mode has been successfully negotiated. See § Section 4.2.7.1.1 and § Section 4.2.7.3.2 .

## Flit Mode Supported

Field in the PCI Express Capabilities Register. Flit Mode is supported when this bit is Set. See § Section 7.5.3.2

## Flit Mode Disable

Field in the Link Control Register. This bit used to disable Flit Mode. This bit is most useful in Downstream Ports but is also defined for Upstream Ports (useful for crosslinks or by device firmware). See § Section 7.5.3.7 . Setting this bit may be useful to workaround faulty hardware.

## Flit Mode Status

Field in the Link Status 2 Register. Indicates that that the Link is or will be operating in Flit Mode. Should match the Flit_Mode_Enabled variable. See § Section 7.5.3.20 .

### 4.2.1 8b/10b Encoding for 2.5 GT/s and 5.0 GT/s Data Rates

### 4.2.1.1 Symbol Encoding

At 2.5 and 5.0 GT/s, PCI Express uses an 8b/10b transmission code. The definition of this transmission code is identical to that specified in ANSI X3.230-1994, clause 11 (and also IEEE 802.3z, 36.2.4). Using this scheme, 8 -bit data characters are treated as 3 bits and 5 bits mapped onto a 4 -bit code group and a 6 -bit code group, respectively. The control bit in conjunction with the data character is used to identify when to encode one of the 12 Special Symbols included in the 8b/ 10b transmission code. These code groups are concatenated to form a 10-bit Symbol. As shown in § Figure 4-2, ABCDE maps to abcdei and FGH maps to fghj.

![img-1.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-1.jpeg)

Figure 4-2 Character to Symbol Mapping

# 4.2.1.1.1 Serialization and De-serialization of Data 

The bits of a Symbol are placed on a Lane starting with bit "a" and ending with bit "j". Examples are shown in $\S$ Figure 4-3 and $\S$ Figure 4-4.
![img-2.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-2.jpeg)

Figure 4-3 Bit Transmission Order on Physical Lanes - x1 Example

![img-3.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-3.jpeg)

Figure 4-4 Bit Transmission Order on Physical Lanes - x4 Example

# 4.2.1.1.2 Special Symbols for Framing and Link Management (K Codes) 

The 8b/10b encoding scheme provides Special Symbols that are distinct from the Data Symbols used to represent Characters. These Special Symbols are used for various Link Management mechanisms described later in this chapter. Special Symbols are also used to frame DLLPs and TLPs ${ }^{95}$ in Non-Flit Mode, using distinct Special Symbols to allow these two types of Packets to be quickly and easily distinguished. When Flit Mode is enabled, each Symbol (Byte) of the Data Stream is still encoded with 8b/10b encoding without the Framing described. The Flit Mode operation is described in $\S$ Section 4.2.3.1 . Even when Flit Mode is enabled, the Ordered Sets follow the description provided in $\S$ Section 4.2.1, when operating in $2.5 \mathrm{GT} / \mathrm{s}$ or $5.0 \mathrm{GT} / \mathrm{s}$ Data Rates.
$\S$ Table 4-3 shows the Special Symbols used for PCI Express and provides a brief description for each. These Symbols will be discussed in greater detail in following sections. Each of these Special Symbols, as well as the data Symbols, must be interpreted by looking at the 10-bit Symbol in its entirety.

Table 4-3 Special Symbols in 8b/10b Encoding

| Encoding | Symbol | Name | Description |
| :--: | :--: | :--: | :--: |
| K28.5 | COM | Comma | Used for Lane and Link initialization and management |

| Encoding | Symbol | Name | Description |
| :--: | :--: | :--: | :--: |
|  |  |  | Used identically in Flit Mode and Non-Flit Mode |
| K27.7 | STP | Start TLP | Marks the start of a Transaction Layer Packet in Non-Flit Mode. |
|  |  |  | Reserved in Flit Mode. |
| K28.2 | SDP | Start DLLP | Marks the start of a Data Link Layer Packet in Non-Flit Mode. |
|  |  |  | Reserved in Flit Mode. |
| K29.7 | END | End | Marks the end of a Transaction Layer Packet or a Data Link Layer Packet in Non-Flit Mode. |
|  |  |  | Reserved in Flit Mode. |
| K30.7 | EDB | EnD Bad | Marks the end of a nullified TLP in Non-Flit Mode. |
|  |  |  | Reserved in Flit Mode. |
| K23.7 | PAD | Pad | Used in Framing in Non-Flit Mode only. It is also used in Link Width and Lane ordering negotiations in both Non-Flit Mode and Flit Mode. |
| K28.0 | SKP | Skip | Used for compensating for different bit rates for two communicating Ports. |
|  |  |  | Used identically in Flit Mode and Non-Flit Mode. |
| K28.1 | FTS | Fast Training Sequence | Used within an Ordered Set to exit from LOs to L0 in Non-Flit Mode. |
|  |  |  | No usage for this Encoding is defined in Flit Mode. |
| K28.3 | IDL | Idle | Used in the Electrical Idle Ordered Set (EIOS) |
|  |  |  | Used identically in Flit Mode and Non-Flit Mode. |
| K28.4 |  |  | Reserved |
| K28.6 |  |  | Reserved |
| K28.7 | EIE | Electrical Idle Exit | Reserved in $2.5 \mathrm{GT} / \mathrm{s}$ |
|  |  |  | Used in the Electrical Idle Exit Ordered Set (EIEOS) and sent prior to sending FTS at data rates other than $2.5 \mathrm{GT} / \mathrm{s}$ |

# 4.2.1.1.3 8b/10b Decode Rules 

The Symbol tables for the valid 8b/10b codes are given in Appendix B. These tables have one column for the positive disparity and one column for the negative disparity.

A Transmitter is permitted to pick any disparity, unless otherwise required, when first transmitting differential data after being in an Electrical Idle state. The Transmitter must then follow proper 8b/10b encoding rules until the next Electrical Idle state is entered.

The initial disparity for a Receiver that detects an exit from Electrical Idle is set to the disparity of the first Symbol used to obtain Symbol lock. Disparity may also be re-initialized if Symbol lock is lost and regained during the transmission of differential information due to an implementation specific number of errors. All following received Symbols after the initial disparity is set must be found in the proper column corresponding to the current running disparity.

If a received Symbol is found in the column corresponding to the incorrect running disparity or if the Symbol does not correspond to either column, the Physical Layer must notify the Data Link Layer that the received Symbol is invalid. This is a Receiver Error, and is a reported error associated with the Port (see § Section 6.2 ) in Non-Flit Mode. In Flit Mode, the Symbol in error is passed to the FEC logic to correct; the Receiver is permitted to send any 8-bit value to the FEC logic if an 8b/10b error or k-char is detected inside the Flit boundary.

# 4.2.1.2 Framing and Application of Symbols to Lanes 

There are two classes of framing and application of Symbols to Lanes. The first class consists of the Ordered Sets. The second class consists of TLPs and DLLPs in the Data Stream. Ordered Sets are always transmitted serially on each Lane, such that a full Ordered Set appears simultaneously on all Lanes of a multi-Lane Link. The Non-Flit Mode of Data Stream is described below. The Flit Mode description for Data Stream is described in § Section 4.2.3.2 and § Section 4.2.3.3 . There are no defined framing-related errors while using 8b/10b encoding in Flit Mode.

### 4.2.1.2.1 Framing and Application of Symbols to Lanes for TLPs and DLLPs in Non-Flit Mode

The Framing mechanism uses Special Symbol K28.2 "SDP" to start a DLLP and Special Symbol K27.7 "STP" to start a TLP. The Special Symbol K29.7 "END" is used to mark the end of either a TLP or a DLLP.

The conceptual stream of Symbols must be mapped from its internal representation, which is implementation dependent, onto the external Lanes. The Symbols are mapped onto the Lanes such that the first Symbol (representing Character 0) is placed onto Lane 0; the second is placed onto Lane 1; etc. The x1 Link represents a degenerate case and the mapping is trivial, with all Symbols placed onto the single Lane in order.

When no packet information or special Ordered Sets are being transmitted, the Transmitter is in the Logical Idle state. During this time idle data must be transmitted. The idle data must consist of the data byte 0 (00h), scrambled according to the rules of $\S$ Section 4.2.1.3 and 8b/10b encoded according to the rules of $\S$ Section 4.2.1.1, in the same way that TLP and DLLP Data Symbols are scrambled and encoded. Likewise, when the Receiver is not receiving any packet information or special Ordered Sets, the Receiver is in Logical Idle and shall receive idle data as described above. During transmission of the idle data, the SKP Ordered Set must continue to be transmitted as specified in § Section 4.2.8 .

For the following rules, "placed" is defined to mean a requirement on the Transmitter to put the Symbol into the proper Lane of a Link.

- TLPs must be framed by placing an STP Symbol at the start of the TLP and an END Symbol or EDB Symbol at the end of the TLP (see § Figure 4-5).
- A properly formed TLP contains a minimum of 18 symbols between the STP and END or EDB Symbols. If a received sequence has less than 18 symbols between the STP and END or EDB symbols, the Receiver is permitted to treat this as a Receiver Error.
- If checked, this is a reported error associated with the Receiving Port (see § Section 6.2 ).
- DLLPs must be framed by placing an SDP Symbol at the start of the DLLP and an END Symbol at the end of the DLLP (see § Figure 4-6).

- Logical Idle is defined to be a period of one or more Symbol Times when no information: TLPs, DLLPs or any type of Special Symbol is being Transmitted/Received. Unlike Electrical Idle, during Logical Idle the Idle data Symbol (00h) is being transmitted and received.
- When the Transmitter is in Logical Idle, the Idle data Symbol (00h) shall be transmitted on all Lanes. This is scrambled according to the rules in $\S$ Section 4.2.1.3 .
- Receivers must ignore incoming Idle data Symbols, and must not have any dependency other than scramble sequencing on any specific data patterns.
- For Links wider than x1, the STP Symbol (representing the start of a TLP) must be placed in Lane 0 when starting Transmission of a TLP from a Logical Idle Link condition.
- For Links wider than x1, the SDP Symbol (representing the start of a DLLP) must be placed in Lane 0 when starting Transmission of a DLLP from a Logical Idle Link condition.
- The STP Symbol must not be placed on the Link more frequently than once per Symbol Time.
- The SDP Symbol must not be placed on the Link more frequently than once per Symbol Time.
- As long as the above rules are satisfied, TLP and DLLP Transmissions are permitted to follow each other successively.
- One STP Symbol and one SDP Symbol may be placed on the Link in the same Symbol Time.
- Links wider than x4 can have STP and SDP Symbols placed in Lane $4^{\star} \mathrm{N}$, where N is a positive integer. For example, for x8, STP and SDP Symbols can be placed in Lanes 0 and 4; and for x16, STP and SDP Symbols can be placed in Lanes 0, 4, 8, or 12.
- For $x$ Links where N is 8 or more, if an END or EDB Symbol is placed in a Lane K, where K does not equal N-1, and is not followed by an STP or SDP Symbol in Lane K+1 (i.e., there is no TLP or DLLP immediately following), then PAD Symbols must be placed in Lanes K+1 to Lane N-1.
- For example, on a x8 Link, if END or EDB is placed in Lane 3, PAD must be placed in Lanes 4 to 7, when not followed by STP or SDP.
- The EDB Symbol is used to mark the end of a nullified TLP. Refer to § Section 3.6.2.1 for information on the usage of EDB.
- Receivers may optionally check for violations of the rules of this section. These checks are independently optional (see § Section 6.2.3.4). If checked, violations are Receiver Errors, and are reported errors associated with the Port (see § Section 6.2).
![img-4.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-4.jpeg)

Figure 4-5 TLP with Framing Symbols Applied

![img-5.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-5.jpeg)

Figure 4-6 DLLP with Framing Symbols Applied
![img-6.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-6.jpeg)

Figure 4-7 Framed TLP on a x1 Link

![img-7.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-7.jpeg)

Figure 4-8 Framed TLP on a x2 Link 9
![img-8.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-8.jpeg)

Figure 4-9 Framed TLP on a x4 Link 10

# 4.2.1.3 Data Scrambling 

In order to improve electrical characteristics of a Link, data is typically scrambled. This is applicable for both the Flit Mode as well as Non-Flit Mode at $2.5 \mathrm{GT} / \mathrm{s}$ and $5.0 \mathrm{GT} / \mathrm{s}$ Data Rates. This involves XORing the data stream with a pattern generated by a Linear Feedback Shift Register (LFSR). On the Transmit side, scrambling is applied to characters prior to the $8 \mathrm{~b} / 10 \mathrm{~b}$ encoding. On the Receive side, de-scrambling is applied to characters after 8b/10b decoding.

On a multi-Lane Link, the scrambling function can be implemented with one or many LFSRs. When there is more than one Transmit LFSR per Link, these must operate in concert, maintaining the same simultaneous (Lane-to-Lane Output Skew) value in each LFSR. When there is more than one Receive LFSR per Link, these must operate in concert, maintaining the same simultaneous (Lane-to-Lane Skew) value in each LFSR. Regardless of how they are implemented, LFSRs must interact with data on a Lane-by-Lane basis as if there was a separate LFSR as described here for each Lane within that Link.

The LFSR is graphically represented in $\S$ Figure 4-10. Scrambling or unscrambling is performed by serially XORing the 8 -bit (D0-D7) character with the 16-bit (D0-D15) output of the LFSR. An output of the LFSR, D15, is XORed with D0 of the data to be processed. The LFSR and data register are then serially advanced and the output processing is repeated for D1 through D7. The LFSR is advanced after the data is XORed. The LFSR implements the polynomial:
$G(X)=X^{16}+X^{5}+X^{4}+X^{3}+1$

The mechanism(s) and/or interface(s) utilized by the Data Link Layer to notify the Physical Layer to disable scrambling is implementation specific and beyond the scope of this specification.

The data scrambling rules are the following:

- The COM Symbol initializes the LFSR.
- The LFSR value is advanced eight serial shifts for each Symbol except the SKP.
- All data Symbols (D codes) except those within Ordered Sets (e.g., TS1, TS2, EIEOS), the Compliance Pattern (see § Section 4.2.9), and the Modified Compliance Pattern (see § Section 4.2.10) are scrambled.
- All special Symbols (K codes) are not scrambled.
- The initialized value of an LFSR seed (D0-D15) is FFFFh. Immediately after a COM exits the Transmit LFSR, the LFSR on the Transmit side is initialized. Every time a COM enters the Receive LFSR on any Lane of that Link, the LFSR on the Receive side is initialized.
- Scrambling can only be disabled at the end of Configuration (see § Section 4.2.7.3.5).
- Scrambling does not apply to a Loopback Follower.
- Scrambling is always enabled in Detect by default.


# IMPLEMENTATION NOTE: DISABLING SCRAMBLING 

Disabling scrambling is intended to help simplify test and debug equipment. Control of the exact data patterns is useful in a test and debug environment. Since scrambling is reset at the Physical Layer there is no reasonable way to reliably control the state of the data transitions through software. Thus, the Disable Scrambling bit in the TS1 and TS2 Ordered Sets is provided for these purposes.

The mechanism(s) and/or interface(s) utilized by the Data Link Layer to notify the Physical Layer to disable scrambling is implementation specific and beyond the scope of this specification.

For more information on scrambling, see § Appendix C.
![img-9.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-9.jpeg)

Figure 4-10 LFSR with 8b/10b Scrambling Polynomial

### 4.2.2 128b/130b Encoding for 8.0 GT/s, 16.0 GT/s, and 32.0 GT/s Data Rates

When a PCI Express Link is operating at a data rate of $8.0 \mathrm{GT} / \mathrm{s}, 16.0 \mathrm{GT} / \mathrm{s}$, or $32.0 \mathrm{GT} / \mathrm{s}$, it uses the $128 \mathrm{~b} / 130 \mathrm{~b}$ encoding rules described in this section. For backwards compatibility, the Link initially trains to L0 at the $2.5 \mathrm{GT} / \mathrm{s}$ data rate using 8b/10b encoding as described in § Section 4.2.1, then when the data rate is changed to $8.0 \mathrm{GT} / \mathrm{s}, 16.0 \mathrm{GT} / \mathrm{s}$, or $32.0 \mathrm{GT} / \mathrm{s}$, 128b/130b encoding is used. 128b/130b encoding uses a Link-wide packetization mechanism in Non-Flit Mode and a

per-Lane block code with scrambling in both Flit Mode and Non-Flit Modes. In the Flit Mode, the Data Stream follows the same mechanism described in $\S$ Section 4.2.3.1 , for the 128b payload inside the 128b/130b Data Block(s).

The basic entity of data transmission is an 8-bit data character, referred to as a Symbol, as shown in § Figure 4-11 and § Figure 4-12.

# IMPLEMENTATION NOTE: SYMBOL IN 128B/130B ENCODING SCHEME 

In the 128b/130b encoding scheme, the Symbol is one byte long, similar to the 10-bit Symbol of 8b/10b encoding.

### 4.2.2.1 Lane Level Encoding

The Physical Layer uses a per-Lane block code. Each Block consists of a 2-bit Sync Header and a payload. There are two valid Sync Header encodings: 10b and 01b. The Sync Header defines the type of payload that the Block contains.

A Sync Header of 10b indicates a Data Block. Each Data Block has a 128 bit payload, resulting in a Block size of 130 bits. The payload is a Data Stream described in $\S$ Section 4.2.2.3 .

A Sync Header of 01b indicates an Ordered Set Block. Each Ordered Set Block has a 128 bit payload, resulting in a Block size of 130 bits except for the SKP Ordered Set which can be of variable length.

All Lanes of a multi-Lane Link must transmit Blocks with the same Sync Header simultaneously, except when transmitting Jitter Measurement Pattern in Polling.Compliance.

The bit transmission order is as follows. A Sync Header represented as ' $\mathrm{H}_{1} \mathrm{H}_{0}$ ' is placed on a Lane starting with ' $\mathrm{H}_{0}$ ' and ending with ' $\mathrm{H}_{1}$ '. A Symbol, represented as ' $\mathrm{S}_{7} \mathrm{~S}_{6} \mathrm{~S}_{5} \mathrm{~S}_{4} \mathrm{~S}_{3} \mathrm{~S}_{2} \mathrm{~S}_{1} \mathrm{~S}_{0}$ ', is placed on a Lane starting with ' $\mathrm{S}_{0}$ ' and ending with ' $\mathrm{S}_{7}$ '. In the diagrams that show a time scale, bits represent the transmission order. In layout diagrams, bits are arranged in little-endian format, consistent with packet layout diagrams in other chapters of this specification.
![img-10.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-10.jpeg)

Figure 4-11 Example of Bit Transmission Order in a x1 Link Showing 130 Bits of a Block

![img-11.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-11.jpeg)

Figure 4-12 Example of Bit Placement in a x4 Link with One Block per Lane

# 4.2.2.2 Ordered Set Blocks 

An Ordered Set Block contains a Sync Header followed by one Ordered Set. All Lanes of a multi-Lane Link must transmit the same Ordered Set type simultaneously. The first Symbol of the Ordered Set defines the type of Ordered Set. Subsequent symbols of the Ordered Set are defined by the Ordered Set type and need not be identical across lanes of a multi-Lane Link. The Ordered Sets are described in detail in $\S$ Section 4.2.5 and $\S$ Section 4.2.8 . Ordered Set Blocks are the same for both Flit Mode and Non-Flit Mode except for the use and frequency of SKP Ordered Set. In Flit Mode at 8.0 GT/s, both Standard SKP Ordered Sets and Control SKP Ordered Sets are used.

### 4.2.2.2.1 Block Alignment

During Link training, the 130 bits of the Electrical Idle Exit Ordered Set (EIEOS) are a unique bit pattern that Receivers use to determine the location of the Block Sync Headers in the received bit stream. Conceptually, Receivers can be in three different phases of Block alignment: Unaligned, Aligned, and Locked. These phases are defined to illustrate the required behavior, but are not meant to specify a required implementation.

## Unaligned Phase

Receivers enter this phase after a period of Electrical Idle, such as when the data rate is changed to one that uses 128b/130b encoding or when they exit a low-power Link state, or if directed (by an implementation specific method). In this phase, Receivers monitor the received bit stream for the EIEOS bit pattern. When one is detected, they adjust their alignment to it and proceed to the Aligned phase.

## Aligned Phase

Receivers monitor the received bit stream for the EIEOS bit pattern and the received Blocks for a Start of Data Stream (SDS) Ordered Set. If an EIEOS bit pattern is detected on an alignment that does not match the current alignment, Receivers must adjust their alignment to the newly received EIEOS bit pattern. If an SDS Ordered Set is received, Receivers proceed to the Locked phase. Receivers are permitted to return to the Unaligned phase if an undefined Sync Header ( 00 b or 11 b ) is received.

## Locked Phase

Receivers must not adjust their Block alignment while in this phase. The Data Stream starts after an SDS Ordered Set, and adjusting the Block alignment would interfere with the processing of these Blocks. Receivers must return to the Unaligned or Aligned phase if an undefined Sync Header is received.

# IMPLEMENTATION NOTE: DETECTION OF LOSS OF BLOCK ALIGNMENT 

The sequence of EIEOS and TS Ordered Sets transmitted during training sequences will cause misaligned Receivers to detect an undefined Sync Header.

Additional Requirements:

- While in the Aligned or Locked phase, Receivers must adjust their alignment as necessary when a SKP Ordered Set is received. See $\S$ Section 4.2.8 for more information on SKP Ordered Sets.
- After any LTSSM transition to Recovery, Receivers must ignore all received TS Ordered Sets until they receive an EIEOS. Conceptually, receiving an EIEOS validates the Receiver's alignment and allows TS Ordered Set processing to proceed. If a received EIEOS initiates an LTSSM transition from L0 to Recovery, Receivers are permitted to process any TS Ordered Sets that follow the EIEOS or ignore them until another EIEOS is received after entering Recovery.
- Receivers are permitted to transition from the Locked phase to the Unaligned or Aligned phase as long as Data Stream processing is stopped. See $\S$ Section 4.2.2.3 for more information on Data Stream requirements.
- Loopback Leads: While in Loopback.Entry, Leads must be capable of adjusting their Receiver's Block alignment to received EIEOS bit patterns. While in Loopback.Active, Leads are permitted to transmit an EIEOS and adjust their Receiver's Block alignment to the looped back bit stream.
- Loopback Followers: While in Loopback.Entry, Followers must be capable of adjusting their Receiver's Block alignment to received EIEOS bit patterns. While in Loopback.Active, Followers must not adjust their Receiver's Block alignment. Conceptually, the Receiver is directed to the Locked phase when the Follower starts to loop back the received bit stream.


### 4.2.2.3 Data Blocks

The payload of Data Blocks is a stream of Symbols defined as a "Data Stream". In Non-Flit Mode, the Data Stream consists of Framing Tokens, TLPs, and DLLPs. In Flit Mode, the Data Stream is described in § Section 4.2.3.1 . Each Symbol of the Data Stream is placed on a single Lane of the Link, and the stream of Symbols is striped across all Lanes of the Link and spans Block boundaries.

A Data Stream starts with the first Symbol of the Data Block that follows an SDS Ordered Set. It ends either when a Framing Error is detected or with the last Symbol of the Data Block that precedes an Ordered Set other than a SKP Ordered Set. SKP Ordered Sets that occur within a Data Stream have specific requirements as described in the following sections.

### 4.2.2.3.1 Framing Tokens in Non-Flit-Mode

The Framing Tokens used by the Physical Layer in Non-Flit Mode are shown in § Table 4-4. Each Framing Token specifies or implies the number of Symbols associated with the Token and therefore the location of the next Framing Token. § Figure 4-15 shows an example of TLPs, DLLPs, and IDLs transmitted on a x8 link.

The first Framing Token of a Data Stream is always located in Symbol 0 of Lane 0 of the first Data Block of the Data Stream. For the rest of this chapter, the terms Framing Token and Token are used interchangeably.

| Framing Token <br> Type | Description |
| :--: | :-- |
| IDL | Logical Idle. The Framing Token is 1 Symbol. This Token is transmitted when no TLPs or DLLPs or other Framing <br> Tokens are being transmitted. |
| SDP | Start of DLLP. The Framing Token is 2 Symbols long and is followed by the DLLP information. |
| STP | Start of TLP. The Framing Token is 4 Symbols long and includes the 12-bit TLP Sequence Number. It is followed by <br> the TLP information. |
| EDB | EnD Bad. The Framing Token is 4 Symbols long and is used to confirm that the previous TLP was nullified. |
| EDS | End of Data Stream. The Framing Token is four Symbols long and indicates that the next Block will be an Ordered <br> Set Block. |

| $+0$ |  | $+1$ |  | $+2$ |  | $+3$ |  |
| :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: |
| $7|6| 5|4| 3|2| 1|0$ | $7|6| 5|4| 3|2| 1|0$ | $7|6| 5|4| 3|2| 1|0$ | $7|6| 5|4| 3|2| 1|0$ |  |  |  |
| TLP <br> Length[3:0] | 1111b | F | TLP Length[10:4] | FCRC | TLP Sequence Number |  |

# STP Token 

| $+0$ |  | $+1$ |  | $+2$ |  | $+3$ |  |
| :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: |
| $7|6| 5|4| 3|2| 1|0$ | $7|6| 5|4| 3|2| 1|0$ | $7|6| 5|4| 3|2| 1|0$ | $7|6| 5|4| 3|2| 1|0$ |  |  |  |
| 0001b | 1111b | 1b | 0000000b | 1001b | 0000000000000b |  |

EDS Token

| $+0$ | $+1$ | $+2$ | $+3$ |  |
| :--: | :--: | :--: | :--: | :--: |
| $7|6| 5|4| 3|2| 1|0$ | $7|6| 5|4| 3|2| 1|0$ | $7|6| 5|4| 3|2| 1|0$ |  |
| 11000000b | 11000000b | 11000000b | 11000000b |  |

EDB Token

| $+0$ | $+1$ |  |
| :--: | :--: | :--: |
| $7|6| 5|4| 3|2| 1|0$ |  |
| 11110000b | 10101100b |  |

## SDP Token

| $+0$ |  |  |
| :--: | :--: | :--: |
| $7|6| 5|4| 3|2| 1|0$ |  |
| 00000000b |  |  |

## IDL Token

Figure 4-13 Layout of Framing Tokens

The Physical Layer DLLP layout is shown in $\S$ Figure 4-14. Symbols 0 and 1 are the SDP Token, and Symbols 2 through 7 are the Data Link Layer DLLP information.

The Physical Layer TLP layout is shown in § Figure 4-14. Details of the STP Framing Token are shown in § Figure 4-13. The length of the TLP (in DWs) being transmitted is specified by an 11-bit field called TLP Length. The TLP Length field is the total amount of information transferred, including the Framing Token, TLP Prefixes (if any), TLP Header, TLP data payload (if any), TLP digest (if any), TLP PCRC (if any), TLP MAC (if any), and TLP LCRC. For example, if a TLP has a 3 DW header, a 1 DW data payload, and does not include a TLP digest, the TLP Length field value is 6: 1 (Framing Token) +0 (TLP Prefixes) +3 (TLP header) +1 (TLP data payload) +0 (TLP digest) +1 (TLP LCRC). If the same TLP included a TLP digest, the TLP Length field value would be 7. When a TLP is nullified, the EDB Token is considered an extension of the TLP but is not included in the calculation of the TLP Length field.

The TLP Length field is protected by a 4-bit CRC (Frame CRC), and an even parity bit (Frame Parity) protects both the TLP Length and Frame CRC fields. The Frame CRC and Frame Parity are calculated as follows:
$C[0]=L[10] \wedge L[7] \wedge L[6] \wedge L[4] \wedge L[2] \wedge L[1] \wedge L[0]$
$C[1]=L[10] \wedge L[9] \wedge L[7] \wedge L[5] \wedge L[4] \wedge L[3] \wedge L[2]$
$C[2]=L[9] \wedge L[8] \wedge L[6] \wedge L[4] \wedge L[3] \wedge L[2] \wedge L[1]$
$C[3]=L[8] \wedge L[7] \wedge L[5] \wedge L[3] \wedge L[2] \wedge L[1] \wedge L[0]$
$P=L[10] \wedge L[9] \wedge L[8] \wedge L[7] \wedge L[6] \wedge L[5] \wedge L[4] \wedge L[3] \wedge L[2] \wedge L[1] \wedge L[0] \wedge C[3] \wedge C[2] \wedge C[1] \wedge C[0]$
The Frame Parity reduces to $P=L[10] \wedge L[9] \wedge L[8] \wedge L[6] \wedge L[5] \wedge L[2] \wedge L[0]$
The TLP Length field is represented in the above equations as $L[10: 0]$, where $L[0]$ is the least significant bit and $L[10]$ is the most significant bit. Transmitters calculate the Frame CRC and Frame Parity before transmission. Receivers must calculate the Frame CRC and Frame Parity using the same algorithm as the transmitter and then compare the calculated values to the received values.

STP Tokens do not have a TLP Length field value of 1 . If a received sequence of Symbols matches the format of an STP Token with a TLP Length field value of 1, the Symbols are evaluated to determine whether they match the EDS Token.

# IMPLEMENTATION NOTE: FRAME CRC AND FRAME PARITY § 

The Frame CRC bits are effectively calculated as $\left(L[0] X^{14}+L[1] X^{13}+\ldots+L[9] X^{5}+L[10] X^{4}\right) \bmod \left(X^{4}+X+1\right)$. It should be noted that $X^{4}+X+1$ is a primitive polynomial and the CRC can detect two bit errors. The Frame Parity bit can detect an odd number of bit errors. Thus, the Frame CRC and Frame Parity together guarantee three bit error detection for the TLP Length field. It must be noted that even though in the reduced Frame Parity equation all terms are not present, it still maintains the property of detecting odd bit errors. Only those TLP Length field bits which are present in an even number of CRC terms are used in the calculation.

Note that, for TLPs, the Data Link Layer prepends 4 Reserved bits (0000b) to the TLP Sequence Number field before it calculates the LCRC. These Reserved bits are not explicitly transmitted when using 128b/130b encoding, and Receivers assume that the 4 bits received are 0000b when calculating the LCRC.

Packets containing a TLP Length field that is greater than 1535 are PMUX Packets. For such packets, the actual packet length is computed differently, the TLP Sequence Number field in the STP Token contains other information, and the Link CRC is computed using different rules. See § Appendix G. for details.

Packets containing a TLP Length field that is between 1152 and 1535 (inclusive) are reserved for future standardization.
Transmitters must transmit all DWs of a TLP specified by the TLP Length field of the STP Framing Token. TLPs are never truncated when using 128b/130b encoding - even when nullified. § Figure 4-16 shows an example of a nullified 23 DW TLP.

§ Figure 4-17 shows an example of TLPs, DLLPs, IDLs, and an EDS Token followed by a SKP Ordered Set. SKP Ordered Sets are defined in $\S$ Section 4.2.8.2 .
![img-12.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-12.jpeg)

Figure 4-14 TLP and DLLP Layout $\S$
![img-13.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-13.jpeg)

Figure 4-15 Packet Transmission in a x8 Link 9
![img-14.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-14.jpeg)

Figure 4-16 Nullified TLP Layout in a x8 Link with Other Packets $\$ \$$

![img-15.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-15.jpeg)

Figure 4-17 SKP Ordered Set of Length 66-bit in a x8 Link

# 4.2.2.3.2 Transmitter Framing Requirements in Non-Flit Mode 

The following requirements apply to the transmitted Data Stream.

- To Transmit a TLP:
- Transmit an STP Token immediately followed by the complete TLP information provided by the Data Link Layer.
- All DWs of the TLP, as specified by the TLP Length field of the STP Token, must be transmitted, even if the TLP is nullified.
- If the TLP is nullified, an EDB Token must be transmitted immediately following the TLP. There must be no Symbols between the last Symbol of the TLP and the first Symbol of the EDB Token. The value of the TLP Length field of a nullified TLP's STP Token is not adjusted to account for the EDB Token.
- The STP Token must not be transmitted more frequently than once per Symbol Time.
- To Transmit a DLLP:
- Transmit an SDP Token immediately followed by the complete DLLP information provided by the Data Link Layer.
- All 6 Symbols of the DLLP must be transmitted.
- The SDP Token must not be transmitted more frequently than once per Symbol Time.
- To Transmit a SKP Ordered Set within a Data Stream:
- Transmit an EDS Token in the last DW of the current Data Block. For example, the Token is transmitted on Lane 0 in Symbol Times 12-15 of the Block for a x1 Link, and on Lanes 12-15 of Symbol Time 15 of the Block for a x16 Link.
- Transmit the SKP Ordered Set following the current Data Block.
- Transmit a Data Block following the SKP Ordered Set. The Data Stream resumes with the first Symbol of the Data Block. If multiple SKP Ordered Sets are scheduled for transmission, each SKP Ordered Set must be preceded by a Data Block with an EDS Token.
- To end a Data Stream:
- Transmit an EDS Token in the last DW of the current Data Block, followed in the next block by an EIOS or an EIEOS. An EIOS is transmitted for LTSSM power management state transitions, and an EIEOS is transmitted for all other cases. For example, the Token is transmitted on Lane 0 in Symbol Times 12-15 of the Block for a x1 Link, and on Lanes 12-15 of Symbol Time 15 of the Block for a x16 Link.
- The IDL Token must be transmitted on all Lanes when not transmitting a TLP, DLLP, or other Framing Token.
- Multi-Lane Links:

- After transmitting an IDL Token, the first Symbol of the next STP or SDP Token must be transmitted in Lane 0 of a future Symbol Time. An EDS Token can be transmitted after an IDL Token in the same Symbol Time, since it must be transmitted in the last DW of a Block.
- For xN Links where N is 8 or more, if an EDB Token, TLP, or DLLP ends in a Lane K, where K does not equal N-1, and it is not followed by the first Symbol of an STP, SDP, or EDB Token in Lane K+1, then IDL Tokens must be placed in Lanes K+1 to N-1. For example, on a x8 Link, if a TLP or DLLP ends in Lane 3, IDL Tokens must be placed in Lanes 4 to 7. The EDS Token is an exception to this requirement, and can be transmitted following IDL Tokens.
- Tokens, TLPs, and DLLPs are permitted to follow each other successively such that more than one Token may be transmitted in the same Symbol Time as long as their transmission conforms with the other requirements stated in this section.
- Links wider than x4 can have Tokens placed starting on Lane $4^{*} \mathrm{~N}$, where N is a positive integer. For example, Tokens can be placed in Lanes 0 and 4 of a x8 Link, and Tokens can be placed in Lanes 0, 4, 8, or 12 of a x16 Link.


# 4.2.2.3.3 Receiver Framing Requirements in Non-Flit Mode 

The following requirements apply to the received Data Stream and the Block type transitions that occur at the beginning and end of the Data Stream.

- When processing Symbols that are expected to be a Framing Token, receiving a Symbol or sequence of Symbols that does not match the definition of a Framing Token is a Framing Error. It is strongly recommended that Receivers of a multi-Lane Link report an error in the Lane Error Status Register for the Lane that receives the first Symbol of an expected Framing Token when that Symbol does not match Symbol +0 of an STP (bits [3:0] only), IDL, SDP, EDB, or EDS Token (see § Figure 4-13).
- All optional error checks and error reports in this section are independently optional (see § Section 6.2.3.4).
- When an STP Token is received:
- Receivers must calculate the Frame CRC and Frame Parity of the received TLP Length field and compare the results to the received Frame CRC and Frame Parity fields. A Frame CRC or Frame Parity mismatch is a Framing Error.
- An STP Token with Framing Error is not considered part of a TLP for the purpose of reporting to the Data Link Layer.
- If the TLP Length field is 1, the Symbols are not an STP Token and are instead evaluated to determine whether they are an EDS Token.
- Receivers are permitted to check whether the TLP Length field has a value of 0 . If checked, receiving a TLP Length field of 0 is a Framing Error.
- Receivers are permitted to check whether the TLP Length field has a value of 2,3 , or 4 . If checked, receiving such a TLP Length field is a Framing Error.
- Receivers are permitted to check whether the TLP Length field has a value between 1152 and 1535 (inclusive). If checked, receiving such a TLP Length field is a Framing Error.
- Receivers on Ports that do not support Protocol Multiplexing are permitted to check whether the TLP Length field has a value greater than 1535. If checked, receiving such a TLP Length field is a Framing Error.
- Receivers on Ports that support Protocol Multiplexing, shall process STP Tokens with a TLP Length field that is greater than 1535 as the start of a PMUX Packet as defined in § Appendix G. .

- The next Token to be processed begins with the Symbol immediately following the last DW of the TLP, as determined by the TLP Length field.
- Receivers must evaluate this Symbol and determine whether it is the first Symbol of an EDB Token and therefore whether the TLP is nullified. See the EDB Token requirements.
- Receivers are permitted to check whether more than one STP Token is received in a single Symbol Time. If checked, receiving more than one STP Token in a single Symbol Time is a Framing Error
- When an EDB Token is received:
- If an EDB Token is received immediately following a TLP (there are no Symbols between the last Symbol of the TLP and the first Symbol of the EDB Token), receivers must inform the Data Link Layer that an EDB Token has been received. Receivers are permitted to inform the Data Link Layer that an EDB Token has been received after processing the first Symbol of the EDB Token or after processing any or all of the remaining Symbols of the EDB Token. Regardless of when they inform the Data Link Layer of a received EDB Token, Receivers must check all Symbols of the EDB Token. Receiving a Symbol that does not match the definition of an EDB Token is a Framing Error.
- Receiving an EDB Token at any time other than immediately following a TLP is a Framing Error.
- The next Token to be processed begins with the Symbol immediately following the EDB Token.
- When an EDS Token is received in the last four Symbols of the Data Block across the Link:
- Receivers must stop processing the Data Stream.
- Receiving an Ordered Set other than SKP, EIOS, or EIEOS in the Block following the EDS Token is a Framing Error.
- If a SKP Ordered Set is received in the Block following the EDS Token, Receivers resume Data Stream processing with the first Symbol of the Data Block that follows the SKP Ordered Set unless a Framing Error has been detected.
- When an SDP Token is received:
- The next Token to be processed begins with the Symbol immediately following the last Symbol of the DLLP.
- Receivers are permitted to check whether more than one SDP Token is received in a single Symbol Time. If checked, receiving more than one SDP Token in a single Symbol Time is a Framing Error.
- When an IDL Token is received:
- For a x1 Link, the next Token to be processed begins with the next Symbol received.
- For a x2 Link, the next Token to be processed begins with the Symbol received in Lane 0 of the next Symbol Time. It is strongly recommended that Receivers check whether the Symbol received in Lane 1, if it did not receive IDL, after an IDL Token was received in Lane 0 is also IDL and report an error for Lane 1 in the Lane Error Status Register. If checked, receiving a Symbol other than IDL is a Framing Error.
- For a x4 Link, the next Token to be processed begins with the Symbol received in Lane 0 of the next Symbol Time. It is strongly recommended that Receivers check whether the Symbols received in Lanes 1-3, after an IDL Token was received in Lane 0 are also IDL and report an error for the Lane(s) that did not receive IDL, in the Lane Error Status Register. If checked, receiving a Symbol other than IDL is a Framing Error.
- For x8 and x16 Links, the next Token to be processed begins with the Symbol received in the next DW aligned Lane following the IDL Token. For example, if an IDL Token is received in Lane 4 of a x16 Link, the next Token location begins with Lane 8 of the same Symbol Time. However, if an IDL Token is received on Lane 4 of a x8 Link, the next Token location begins with Lane 0 of the following Symbol Time. It is strongly recommended that Receivers check whether the Symbols received between the IDL Token and the next Token location are also IDL and report an error for the Lane(s) that did not

receive IDL, in the Lane Error Status Register. If checked, receiving a Symbol other than IDL is a Framing Error.

Note: The only Tokens expected to be received in the same Symbol Time following an IDL Token are additional IDL Tokens or an EDS Token.

- While processing the Data Stream, Receivers must also check the Block type received by each Lane, after accounting for Lane-to-Lane de-skew, for the following conditions:
- Receiving an Ordered Set Block on any Lane immediately following an SDS Ordered Set is a Framing Error.
- Receiving a Block with an undefined Block type (a Sync Header of 11b or 00b) is a Framing Error. It is strongly recommended that Receivers of a multi-Lane Link report an error for any Lane that received the undefined Block type in the Lane Error Status register.
- Receiving an Ordered Set Block on any Lane without receiving an EDS Token in the preceding Block is a Framing Error. For example, receiving a SKP Ordered Set without a preceding EDS Token is a Framing Error. In addition, receiving a SKP Ordered Set followed immediately by another Ordered Set Block (including another SKP Ordered Set) within a Data Stream is a Framing Error. It is strongly recommended that if the first Symbol of the Ordered Set is SKP, Receivers of a multi-Lane Link report an error for the Lane(s) in the Lane Error Status register if the received Symbol number 1 through 4 N does not match the corresponding Symbol in § Table 4-62 or § Table 4-63.
- Receiving a Data Block on any Lane when the previous block contained an EDS Token is a Framing Error. It is strongly recommended that Receivers of a multi-Lane Link report an error for the Lane(s) that received the Data Block in the Lane Error Status register.
- Receivers are permitted to check for different Ordered Sets on different Lanes. If checked, receiving different Ordered Sets is a Framing Error. For example, if Lane 0 receives a SKP Ordered Set and Lane 1 receives an EIOS, it would be a Framing Error.


# 4.2.2.3.4 Receiver Framing Requirements in Flit Mode 

While processing the Data Stream, Receivers must check the Block type received by each Lane, after accounting for Lane-to-Lane de-skew, for the following conditions:

- Not receiving a SKP Ordered Set followed by a Data Block on any Lane immediately following an SDS Ordered Set is a Framing Error.
- Receiving a Block with an undefined Block type (a Sync Header of 11b or 00b) is a Framing Error. It is strongly recommended that Receivers of a multi-Lane Link report an error for any Lane that received the undefined Block type in the Lane Error Status register.
- For Lanes that are not entering or exiting the electrical idle state as part of LOp state, the following conditions result in a Framing Error. It is strongly recommended that Receivers of a multi-Lane Link report an error for any Lane that caused the Framing Error in the Lane Error Status register.
- Receiving an Ordered Set Block on any Lane in an unscheduled Block boundary, as defined in § Section 4.2.3.1
- Not receiving one of these three Ordered Sets of the appropriate length at the scheduled Block boundary: EIEOS, SKP Ordered Set, or EIOS
- Receivers are permitted to check for different Ordered Sets on different Lanes, except as permitted for an LOp width transition. If checked, receiving different Ordered Sets is a Framing Error. For example, if Lane 0 receives a SKP Ordered Set and Lane 1 receives an EIOS and no LOp transition is expected, it would be a Framing Error.

# 4.2.2.3.5 Recovery from Framing Errors in Non-Flit Mode and Flit Mode 

If a Receiver detects a Framing Error while processing the Data Stream, it must:

- Report a Receiver Error as described in $\S$ Section 4.2.5.8 .
- Stop processing the Data Stream. Processing of a new Data Stream is initiated when the next SDS Ordered Set is received as previously described.
- Initiate the error recovery process as described in $\S$ Section 4.2.5.8 . If the LTSSM state is L0, direct the LTSSM to Recovery. If the LTSSM state is Configuration.Complete or Configuration. Idle when the Framing Error is detected, the error recovery process is satisfied by either a transition from Configuration. Idle to Recovery.RcvrLock due to the specified timeout, or a transition to Recovery through L0. If the LTSSM state is Recovery.RcvrCfg or Recovery. Idle when the Framing Error is detected, the error recovery process is satisfied by either a transition from Recovery. Idle to Recovery.RcvrLock due to the specified timeout, or a directed transition from L0 to Recovery. If the LTSSM substate is either Recovery.RcvrLock or Configuration. Linkwidth. Start, the error recovery process is satisfied upon exit from these substates and no direction of the LTSSM to Recovery is required.
- Note: The framing error recovery mechanism is not expected to directly cause any Data Link Layer initiated recovery action such as NAK.


## IMPLEMENTATION NOTE: TIME SPENT IN RECOVERY DUE TO DETECTION OF A FRAMING ERROR

When using 128b/130b encoding, all Framing Errors require Link recovery. It is expected that implementations will require less than 1 microsecond to recover from a Framing Error as measured from the time that both Ports have entered the Recovery state.

### 4.2.2.4 Scrambling in Non-Flit Mode and Flit Mode

Each Lane of the transmitter in a multi-Lane Link may implement a separate LFSR for scrambling. Each Lane of the Receiver in a multi-Lane Link may implement a separate LFSR for descrambling. Implementations may choose to implement fewer LFSRs but must achieve the same functionality as independent LFSRs.

The LFSR uses the following polynomial: $G(X)=X^{23}+X^{21}+X^{16}+X^{8}+X^{5}+X^{2}+1$ and is demonstrated in $\S$ Figure 4-18.
The scrambling rules are as follows:

- The two bits of the Sync Header used in $8.0 \mathrm{GT} / \mathrm{s}, 16.0 \mathrm{GT} / \mathrm{s}$, or $32.0 \mathrm{GT} / \mathrm{s}$ Data Rate are not scrambled and do not advance the LFSR.
- All 16 Symbols of an Electrical Idle Exit Ordered Set (EIEOS) bypass scrambling. Except during L0p, the scrambling LFSR is initialized after the last Symbol of an EIEOS is transmitted, and the descrambling LFSR is initialized after the last Symbol of an EIEOS is received.
- TS1 and TS2 Ordered Sets for $8.0 \mathrm{GT} / \mathrm{s}, 16.0 \mathrm{GT} / \mathrm{s}$, or $32.0 \mathrm{GT} / \mathrm{s}$ Data Rate:
- Symbol 0 of a TS1 or TS2 Ordered Set bypasses scrambling.
- Symbols 1-13 are scrambled.

- Symbols 14 and 15 bypass scrambling if required for DC Balance, but they are scrambled if not required for DC Balance.
- All 16 Symbols of a Fast Training Sequence (FTS) Ordered Set used in 8.0 GT/s, 16.0 GT/s, or 32.0 GT/s bypass scrambling.
- All 16 Symbols of a Start of Data Stream (SDS) Ordered Set bypass scrambling.
- All 16 Symbols of an Electrical Idle Ordered Set (EIOS) bypass scrambling.
- All Symbols of a SKP Ordered Set bypass scrambling.
- Transmitters advance their LFSR for all Symbols of all Ordered Sets except for the SKP Ordered Set. The LFSR is not advanced for any Symbols of a SKP Ordered Set.
- Receivers evaluate Ordered Sets to determine whether to advance their LFSR. If the Ordered Set is a SKP Ordered Set (see § Section 4.2.8 ), or an EIOS with L0p in the midst of a data stream then the LFSR is not advanced for any Symbol of the Ordered Set. Otherwise, the LFSR is advanced for all Symbols of the Ordered Set.
- In L0p, the scrambler on the Transmit and Receive sides associated with all the Lanes must advance whenever the scrambler associated with Lane 0 advances and does not advance whenever the scrambler associated Lane 0 does not advance. As a result, in L0p, the transmit or receipt of an EIEOS does not reset the scrambler associated with the Lane, if it is not Lane 0.


# IMPLEMENTATION NOTE: ELASTIC BUFFER AND LOP 

For implementations that descramble prior to putting entries into the elastic buffer, one way to handle the scramblers advancing in the idle lane during L0p is as follows:

- The Lane which goes to electrical idle will tie its decision to advance the scrambler, accounting for sync hdr, if any, and SKP Ordered Set to Lane 0. Since the EIOS in the Lane coincides with SKP OS in Lane 0, the scrambler in the idle Lane should be synchronized with the Lane 0 on receipt of EIOS
- The TS1/TS2 Ordered Sets exchanged when trying to upsize the Link on L0p will be scrambled using the continually running LFSR.
- Depending on the implementation, any differences in scrambler synchronization on the receive side for lanes which have recently become active can be determined on the SKP Ordered Set boundary following block alignment and adjusted accordingly.
- The special scrambler rules for L0p above apply only to $128 \mathrm{~b} / 130 \mathrm{~b}$ and $1 \mathrm{~b} / 1 \mathrm{~b}$ encoding since the Ordered Sets are scrambled, and different Lanes can have different seeds/ taps which must run continuously without being reset during the data stream. In contrast, 8b/10b encoding does not scramble Ordered Sets and all the scramblers across all Lanes will be reset during SKP Ordered Sets during the link width up-size.
- All 16 Symbols of a Data Block are scrambled and advance the scrambler.
- For Symbols that need to be scrambled, the least significant bit is scrambled first and the most significant bit is scrambled last.
- The seed value of the LFSR is dependent on the Lane number Default Lane numbers are assigned in an implementation specific manner which is invariant to Link width and Lane reversal negotiation. These default numbers must be unique. For example, each Lane of a x16 Link must be assigned a unique Lane number from 0

to 15. These default Lane numbers are reassigned to the Lane when the Link first enters Configuration. Idle (i.e., having gone through Polling from Detect with LinkUp = 0b).

- The seed values for Lane number modulo 8 are:

| Lane | Seed |
| :--: | :--: |
| 0 | 1 DBFBCh |
| 1 | 0607BBh |
| 2 | 1 EC 760 h |
| 3 | 18C0DBh |
| 4 | 010F12h |
| 5 | 19CFC9h |
| 6 | 0277CEh |
| 7 | 1BB807h |

# IMPLEMENTATION NOTE: 

## SCRAMBLING PSEUDO-CODE

The pseudo-code for the scrambler along with examples are provided in § Section C. 2 of § Appendix C.

- The seed value of the LFSR does not change while LinkUp=1. Link reconfiguration through the LTSSM Configuration state does not modify the initial Lane number assignment as long as LinkUp remains 1 (even though the Lane assignment may change during Configuration).
- Scrambling cannot be disabled in Configuration.Complete when using 128b/130b encoding.
- A Loopback Follower must not descramble or scramble the looped-back bit stream.

![img-16.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-16.jpeg)

Figure 4-18 LFSR with Scrambling Polynomial in 8.0 GT/s and Above Data Rate

# IMPLEMENTATION NOTE: 

## LFSR IMPLEMENTATION WITH A SHARED LFSR

Implementations may choose to implement one LFSR and take different tap points as shown in § Figure 4-19, which is equivalent to the individual LFSR per-lane with different seeds, as shown in § Figure 4-18. It should also be noted that the tap equations of four Lanes are the XOR of the tap equations of two neighboring Lanes. For example, Lane 0 can be obtained by XORing the output of Lanes 1 and 7; Lane 2 is the XOR of Lanes 1 and 3; Lane 4 is the XOR of Lanes 3 and 5; and Lane 6 is the XOR of Lanes 5 and 7. This can be used to help reduce the gate count at the expense of potential delay due to the XOR results of the two Lanes.

![img-17.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-17.jpeg)

Figure 4-19 Alternate Implementation of the LFSR for Descrambling

# 4.2.2.5 Precoding 

A Receiver may request precoding from its transmitter for operating at data rates of $32.0 \mathrm{GT} / \mathrm{s}$ and higher. Precoding, when enabled at a Data Rate, applies to both Flit Mode and Non-Flit Mode at that data rate. The precoding rules are as follows:

- A Port or Pseudo-Port must request precoding on all configured Lanes of the Link. Behavior is undefined if precoding is requested on some Lanes but not others by a Port or Pseudo-Port.
- A Port or Pseudo-Port may request precoding independent of other Ports or Pseudo-Ports. For example, it is possible that precoding may be turned on only in the Upstream Port in the case with no Retimers in § Figure 4-79, or on all the Lanes in $\mathrm{Tx}(\mathrm{A})$ and $\mathrm{Tx}(\mathrm{E})$ in the two Retimer example in § Figure 4-79.
- Precoding is turned off for all data rates when the LTSSM is in the Detect state.
- If a precoding request for a data rate is to be made, it must be made prior to entering that data rate. A precoding request is made by setting the Transmitter Precode Request bit in the EQ TS2 or the 128b/ 130b EQ TS2 Ordered Sets prior to the transition to Recovery.Speed for the data rate at which the precoding will be turned on. Prior to the first Link speed negotiation to $32.0 \mathrm{GT} / \mathrm{s}$ since exiting Detect, the Transmitter Precode Request bit represents the precoding request for $32.0 \mathrm{GT} / \mathrm{s}$ when the Supported Link Speeds field in the EQ TS2 or the 128b/130b EQ TS2 Ordered sets is $32.0 \mathrm{GT} / \mathrm{s}$ or above. If the Link speed has been negotiated to $32.0 \mathrm{GT} / \mathrm{s}$ since exiting Detect, the Transmitter Precode Request bit represents the precoding request for the same data rate that the values in the Transmitter Preset field apply to. For each data rate of $32.0 \mathrm{GT} / \mathrm{s}$ or higher, the precoding request must be made independently.
- Each (pseudo) Port must store the precoding request along with the Tx Eq values for each Lane from the most recent successful equalization procedure prior to the current transition through Detect. If the Link operates at $32.0 \mathrm{GT} / \mathrm{s}$ or higher data rate without performing equalization through the No Equalization Needed mechanism it negotiated in the TS1/TS2 Ordered Sets or modified TS1/TS2 Ordered Sets or the Link operates at the $32.0 \mathrm{GT} / \mathrm{s}$ or higher data rate in Polling.Compliance or Loopback, the precoding requests from the stored equalization results must be enforced. If no equalization has ever been performed on the Link (prior to the current Link up), then precoding will not be turned on.
- If the Transmitter Precode Request bit is Set to 1b in each of the received eight consecutive EQ TS2 or 128b/ 130b EQ TS2 Ordered Sets during Recovery.RcvrCfg prior to entry to Recovery.Speed, the Transmitter must turn on the precoding for the data rate at which the Link will operate on exit from Recovery.Speed if the data rate is $32.0 \mathrm{GT} / \mathrm{s}$ or higher and the precoding request was intended for the data rate of operation. If the precoding request applies to a speed other than the data rate at which the Link will operate on exit from Recovery.Speed, the received Transmitter Precode Request bit must be ignored and the Precoding setting must not be updated for any data rate. Once turned on, precoding will be in effect for that data rate until the Transmitter receives another set of eight consecutive EQ TS2 or 128b/130b EQ TS2 Ordered Sets with Transmitter Precode Request set to 0b during Recovery.RcvrCfg prior to entry to Recovery.Speed for the same data rate.
- A Transmitter must not turn on precoding for any data rates lower than $32.0 \mathrm{GT} / \mathrm{s}$.
- In data rates of $32.0 \mathrm{GT} / \mathrm{s}$ or higher, a Transmitter must set the Transmitter Precoding On bit to 1b in the TS1 Ordered Sets that it transmits in Recovery if its precoding is on for the current data rate; else the bit must be set to 0 b .
- A Transmitter that has turned on precoding for the $32.0 \mathrm{GT} / \mathrm{s}$ data rate on Lane 0 must set the $32.0 \mathrm{GT} / \mathrm{s}$ Transmitter Precoding On bit to 1b in the $32.0 \mathrm{GT} / \mathrm{s}$ Status Register; else, it must set the bit to 0 b . A Receiver that has requested, or will request, its link partner to turn on precoding at the $32.0 \mathrm{GT} / \mathrm{s}$ data rate must set the $32.0 \mathrm{GT} / \mathrm{s}$ Transmitter Precode Request to 1 b in the $32.0 \mathrm{GT} / \mathrm{s}$ Status Register; else it must set the bit to 0 b .
- A Transmitter that has turned on precoding for the $64.0 \mathrm{GT} / \mathrm{s}$ data rate on Lane 0 must set the $64.0 \mathrm{GT} / \mathrm{s}$ Transmitter Precoding On bit to 1b in the $64.0 \mathrm{GT} / \mathrm{s}$ Status Register; else it must set the bit to 0 b . A Receiver that

has requested, or will request, its link partner to turn on precoding at the 64.0 GT/s data rate must set the 64.0 GT/s Transmitter Precode Request to 1b in the 64.0 GT/s Status Register; else it must set the bit to 0b.

- See $\S$ Section 4.2.2.5.1 for 32.0 GT/s precoding requirements. See $\S$ Section 4.2.3.1.4 for 64.0 GT/s and above data rate precoding requirements.
- When in Loopback.Active, a Loopback Follower's Transmitter must not apply any additional precoding to the looped-back bit stream.


# 4.2.2.5.1 Precoding at 32.0 GT/s Data Rate 

When precoding is on at 32.0 GT/s, the following rules apply (see $\S$ Figure 4-20):

- Only scrambled bits are precoded.
- The "previous bit" used for precoding is set to 1 b on every block boundary and gets updated by the last scrambled and precoded bit transmitted within the current block boundary.
- For symbols that are scrambled, Receivers must first decode the precoded bits before sending them to the descrambler.
![img-18.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-18.jpeg)

Figure 4-20 Precoding working the scrambler/de-scrambler

# IMPLEMENTATION NOTE: PARITY IN THE SKP ORDERED SET WHEN PRECODING IS TURNED ON 

As per the rules of $\S$ Section 4.2.5.1 and $\S$ Section 4.2.8.2, when precoding is turned on, the parity in the SKP Ordered Sets should be calculated before precoding is applied on the Transmit side. Thus, the order in the Transmitter is:

1. scrambling,
2. followed by parity bit calculation,
3. followed by precoding for the scrambled bits.

Accordingly, in the Receiver, the order is:

1. precoding (if turned on by the Transmitter),
2. followed by parity bit calculation,
3. followed by descrambling.

The rationale for this order is that in a Link with one or two Retimers, different Link segments may have the precoding on or off. Let us consider an example system with one retimer between the Root Port and End Point to illustrate this. In the upstream direction, the End Point has precoding on in its Transmitter Lanes since the Retimer Receiver needs it but the Retimer to Root Port Link segment has the precoding off since the Root Port does not need precoding at its Receiver. Since the Retimer does not change the parity bit, the Root Port would get a parity error if the parity calculation was done by the Transmitter (of the End Point) after precoding.

## IMPLEMENTATION NOTE: LOOPBACK LEAD'S BEHAVIOR IF PRECODING IS ON IN ANY LINK SEGMENT

As per the rules of precoding mentioned in this section and $\S$ Section 4.2.7.4, a Loopback Lead operating at a data rate of $32.0 \mathrm{GT} / \mathrm{s}$ or higher should account for precoding to be on some link segments and off in other link segments. This is particularly relevant when the Loopback Follower transitions from sending TS1 Ordered Sets to looping back the bits. This is where the precoding on the receiver of the Loopback Lead may switch (between precoding on and off). The Loopback Lead is permitted to use implementation specific mechanisms to handle this scenario.

## IMPLEMENTATION NOTE:

## TS1/TS2 ORDERED SETS WHEN PRECODING IS TURNED ON

As per the rules in this section, when precoding is turned on, the 'previous bit' used for precoding is 1 b for the first bit of Symbol 1 since Symbol 0 is not scrambled and the 'previous bit' gets set to 1 b at the block boundary.

# 4.2.2.6 Loopback with 128b/130b Code in Non-Flit Mode and Flit Mode 

When using 128b/130b encoding, Loopback Leads must transmit Blocks with the defined 01b and 10b Sync Headers. However, they are not required to transmit an SDS Ordered Set when transitioning from Ordered Set Blocks to Data Blocks, nor are they required to transmit an EDS Token when transitioning from Data Blocks to Ordered Set Blocks. Leads must transmit SKP Ordered Sets periodically as defined in $\S$ Section 4.2.8, and they must be capable of processing received (looped-back) SKP Ordered Sets of varying length. Leads are permitted to transmit Electrical Idle Exit Ordered Sets (EIEOS) as defined in § Section 4.2.2.2.1. Leads are permitted to transmit any payload in Data Blocks and Ordered Set Blocks that they expect to be looped-back. If the Loopback Lead transmits an Ordered Set Block whose first symbol matches the first symbol of SKP OS, EIEOS, or EIOS, that Ordered Set Block must be a complete and valid SKP OS, EIEOS, or EIOS.

When using 128b/130b encoding, Loopback Followers must retransmit all bits received without modification, except for SKP Ordered Sets which can be adjusted as needed for clock compensation. If clock compensation is required, Followers must add or remove 4 SKP Symbols per Ordered Set. The modified SKP Ordered Set must meet the definition of § Section 4.2.8.2 (i.e., it must have between 4 to 20 SKP Symbols followed by the SKP_END Symbol and the three Symbols that follow it as transmitted by the Loopback Leads. If a Follower is unable to obtain Block alignment or it is misaligned, it may be unable to perform clock compensation and therefore unable to loop-back all bits received. In this case, it is permitted to add or remove Symbols as necessary to continue operation. Followers must not check for a received SDS Ordered Set when a transition from Ordered Set Blocks to Data Blocks is detected, and they must not check for a received EDS Token when a transition from Data Blocks to Ordered Set Blocks is detected.

### 4.2.3 Flit Mode Operation

Flit definition and Symbol placement is specified in this section.
Flits encoded with 8b/10b encoding follow the rules in $\S$ Section 4.2 .1 with the following exception:

- Since the Flit Mode has its fixed TLP and DLP placement, the packet markers such as STP, SDP, END, EDB are not used.

Flits Encoded with 128b/130b encoding follow the rules in $\S$ Section 4.2.2 with the following exceptions:

- Since the Flit Mode has its fixed TLP and DLP placement, the Framing Tokens are not used.

1b/1b encoding is specified in $\S$ Section 4.2.3.1.

### 4.2.3.1 1b/1b Encoding for 64.0 GT/s and higher Data Rates

When the PCI Express Link is operating at 64.0 GT/s or higher Data Rates, it uses Flit Mode. A Symbol (8 bits) is the basic unit of transfer per Lane. PAM4 signaling is used for all Symbols, whether it belongs to a Data Stream or an Ordered Set. PAM4 operates on 2-bit aligned boundaries. A Symbol, represented as ' $S_{7} S_{6} S_{5} S_{4} S_{3} S_{2} S_{1} S_{0}$ ', is placed on a Lane starting with the voltage encoding of ' $S_{1} S_{0}$ ' and ending with ' $S_{7} S_{6}$ '. An example placement of Flits (described later) or Ordered Set on a x4 Link is shown in § Figure 4-21 below.

| Time (UI): | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 252 | 253 | 254 | 255 | 256 | 257 | 258 | ... |
| :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: |
| Lane 0 | $\mathrm{S}_{1} \mathrm{~S}_{0}$ | $\mathrm{S}_{1} \mathrm{~S}_{2}$ | $\mathrm{S}_{1} \mathrm{~S}_{4}$ | $\mathrm{S}_{2} \mathrm{~S}_{6}$ | $\mathrm{S}_{1} \mathrm{~S}_{0}$ | $\mathrm{S}_{3} \mathrm{~S}_{2}$ | $\mathrm{S}_{3} \mathrm{~S}_{4}$ | $\mathrm{S}_{7} \mathrm{~S}_{6}$ |  | $\mathrm{S}_{1} \mathrm{~S}_{0}$ | $\mathrm{S}_{1} \mathrm{~S}_{2}$ | $\mathrm{S}_{3} \mathrm{~S}_{4}$ | $\mathrm{S}_{7} \mathrm{~S}_{6}$ | $\mathrm{S}_{1} \mathrm{~S}_{0}$ | $\mathrm{S}_{3} \mathrm{~S}_{2}$ | $\mathrm{S}_{3} \mathrm{~S}_{4}$ | $\mathrm{S}_{7} \mathrm{~S}_{6}$ |
|  | Symbol 0 |  |  |  | Symbol 4 |  |  |  | Symbol 252 |  |  |  | Symbol 0 of Flit or Symbol 0 of OS |  |  |  |
| Lane 1 | $\mathrm{S}_{1} \mathrm{~S}_{0}$ | $\mathrm{S}_{3} \mathrm{~S}_{2}$ | $\mathrm{S}_{3} \mathrm{~S}_{4}$ | $\mathrm{S}_{7} \mathrm{~S}_{6}$ | $\mathrm{S}_{1} \mathrm{~S}_{0}$ | $\mathrm{S}_{3} \mathrm{~S}_{2}$ | $\mathrm{S}_{3} \mathrm{~S}_{4}$ | $\mathrm{S}_{7} \mathrm{~S}_{6}$ |  | $\mathrm{S}_{1} \mathrm{~S}_{0}$ | $\mathrm{S}_{3} \mathrm{~S}_{2}$ | $\mathrm{S}_{3} \mathrm{~S}_{4}$ | $\mathrm{S}_{7} \mathrm{~S}_{6}$ | $\mathrm{S}_{1} \mathrm{~S}_{0}$ | $\mathrm{S}_{3} \mathrm{~S}_{2}$ | $\mathrm{S}_{3} \mathrm{~S}_{4}$ | $\mathrm{S}_{7} \mathrm{~S}_{6}$ |
|  | Symbol 1 |  |  |  | Symbol 5 |  |  |  | Symbol 253 |  |  |  | Symbol 1 of Flit or Symbol 0 of OS |  |  |  |
| Lane 2 | $\mathrm{S}_{1} \mathrm{~S}_{0}$ | $\mathrm{S}_{3} \mathrm{~S}_{2}$ | $\mathrm{S}_{3} \mathrm{~S}_{4}$ | $\mathrm{S}_{7} \mathrm{~S}_{6}$ | $\mathrm{S}_{1} \mathrm{~S}_{0}$ | $\mathrm{S}_{3} \mathrm{~S}_{2}$ | $\mathrm{S}_{3} \mathrm{~S}_{4}$ | $\mathrm{S}_{7} \mathrm{~S}_{6}$ |  | $\mathrm{S}_{1} \mathrm{~S}_{0}$ | $\mathrm{S}_{3} \mathrm{~S}_{2}$ | $\mathrm{S}_{3} \mathrm{~S}_{4}$ | $\mathrm{S}_{7} \mathrm{~S}_{6}$ | $\mathrm{S}_{1} \mathrm{~S}_{0}$ | $\mathrm{S}_{3} \mathrm{~S}_{2}$ | $\mathrm{S}_{3} \mathrm{~S}_{4}$ | $\mathrm{S}_{7} \mathrm{~S}_{6}$ |
|  | Symbol 2 |  |  |  | Symbol 6 |  |  |  | Symbol 254 |  |  |  | Symbol 2 of Flit or Symbol 0 of OS |  |  |  |
| Lane 3 | $\mathrm{S}_{1} \mathrm{~S}_{0}$ | $\mathrm{S}_{3} \mathrm{~S}_{2}$ | $\mathrm{S}_{3} \mathrm{~S}_{4}$ | $\mathrm{S}_{7} \mathrm{~S}_{6}$ | $\mathrm{S}_{1} \mathrm{~S}_{0}$ | $\mathrm{S}_{3} \mathrm{~S}_{2}$ | $\mathrm{S}_{3} \mathrm{~S}_{4}$ | $\mathrm{S}_{7} \mathrm{~S}_{6}$ |  | $\mathrm{S}_{1} \mathrm{~S}_{0}$ | $\mathrm{S}_{3} \mathrm{~S}_{2}$ | $\mathrm{S}_{3} \mathrm{~S}_{4}$ | $\mathrm{S}_{7} \mathrm{~S}_{6}$ | $\mathrm{S}_{1} \mathrm{~S}_{0}$ | $\mathrm{S}_{3} \mathrm{~S}_{2}$ | $\mathrm{S}_{3} \mathrm{~S}_{4}$ | $\mathrm{S}_{7} \mathrm{~S}_{6}$ |
|  | Symbol 3 |  |  |  | Symbol 7 |  |  |  | Symbol 255 |  |  |  | Symbol 3 of Flit or Symbol 0 of OS |  |  |  |
|  |  |  |  | Flit X (256 B) |  |  |  |  |  |  |  | Flit X+1 (256 B) Or Ordered Set |  |  |  |  |

Figure 4-21 Example of Symbol placement in a $x 4$ Link with 1b/1b encoding

A conceptual diagram of the Transmit side and Receive side is shown in § Figure 4-22 and § Figure 4-23 respectively. These diagrams are provided to explain the order of operations that must be performed on the Transmit and Receive side. An implementation may choose to operate on different widths depending on the design goals and constraints.

At a Flit level, on the Transmit side, CRC is first applied followed by FEC generation. After that, each Lane is allotted its Symbol in the byte interleaved fashion for the Flit. On a per Lane basis, Scrambling is performed, if required, followed by Gray Coding at a 2-bit aligned boundary, after which Precoding is performed at 2-bit aligned UI level, if enabled and required. Thus, in the Symbol above, Gray Coding and Precoding will be applied for the bits corresponding to ' $\mathrm{S}_{1} \mathrm{~S}_{0}$ ', ' $\mathrm{S}_{3} \mathrm{~S}_{2}$ ',..., ' $\mathrm{S}_{7} \mathrm{~S}_{6}$ '. As shown in the diagram below, the scrambled symbols of the TS1/TS2 Ordered sets also undergo the precoding logic (including bypass). All Symbols, whether they belong to a Flit (Data Stream) or scrambled Symbols of an Ordered Set or any pattern where explicitly mentioned (e.g., scrambled part of modified compliance pattern) undergo the Gray Coding and PAM4 encoding, whereas unscrambled Symbols of an Ordered Set or any pattern only undergo the PAM4 encoding (the gray coding and DC-balance is effectively taken care of through the bit definition). For the cases where parts of a pattern may be expressed as a repeated sequence of UIs, the Symbol here refers to the aligned 4 UI interval of that pattern.

![img-19.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-19.jpeg)

Figure 4-22 Transmit side at $64.0 \mathrm{GT} / \mathrm{s}$

The Receive side is similar to the Transmit side in the opposite direction. After the PAM4 voltage is converted to a 2-bit aligned quantity, it undergoes the Receive side precoding if applicable followed by the decoding of the Gray code, followed by descrambling on a single bit level, if applicable. The Data Stream (Flit) is aggregated across all Lanes and undergoes the FEC decode and correction followed by the CRC check before sending up the Transactions and Data Link Payload.
![img-20.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-20.jpeg)

Figure 4-23 Receive side at $64.0 \mathrm{GT} / \mathrm{s}$

# 4.2.3.1.1 PAM4 Signaling 

PAM4 stands for Pulse Amplitude Modulation 4-levels. It is a signaling mechanism where 4 levels (2 bits) are encoded in same Unit Interval (UI) resulting in 3 eyes, as shown in § Figure 4-24. It is deployed only for $64.0 \mathrm{GT} / \mathrm{s}$ or higher Data Rates. As described in § Chapter 8., PAM4 helps with the channel loss as it has the same Nyquist frequency as $32.0 \mathrm{GT} / \mathrm{s}$ for $64.0 \mathrm{GT} / \mathrm{s}$ Data Rate. The four voltage levels $0,1,2$, and 3 , nominally map to $-400 \mathrm{mV},-133 \mathrm{mV},+133 \mathrm{mV}$ and +400 mV respectively, and the Gray code encoded values of $00 b, 01 b, 11 b$, and 10 b respectively, with the little-endian bit order, as shown in § Figure 4-24. The corresponding DC Balance values to be used when designing Ordered Sets to meet the DC

balance needs is also shown in § Figure 4-24. The Reduced voltage levels (eye height or EH) and eye width (EW) increases susceptibility to errors. Gray coding is used to help minimize errors within a UI for the voltage levels.

| Scrambled 2-bit aligned <br> value |  | Unscrambled <br> 2-bit as well <br> as T50 <br> Ordered Sets | Voltage <br> Level | DC- <br> balance <br> Values |  |
| :--: | :--: | :--: | :--: | :--: | :--: |
| Prior to <br> Gray Coding | After Gray <br> Coding |  |  |  |  |
| 10 | 11 | 11 | 3 | $+3 \bullet$ |  |
| 11 | 10 | 10 | 2 | $+1 \bullet$ |  |
| 01 | 01 | 01 | 1 | $-1 \bullet$ |  |
| 00 | 00 | 00 | 0 | $-3 \bullet$ |  |

Figure 4-24 PAM4 Signaling at UI level: Voltage levels, 2-bit encoding, and their corresponding DC balance values

With PAM4 encoding, the bit error rate (BER) is expected to be significantly worse than the $10^{-12}$ BER target of the lower data rates $(2.5,5.0,8.0,16.0$, and $32.0 \mathrm{GT} / \mathrm{s})$. In addition, errors are expected to occur in bursts in a Lane and some amount of Lane to Lane correlation is also expected. The electrical spec parameters along with FBER (First Bit Error Rate) $<10^{-6}$ described in $\S$ Chapter 8 . must be met to ensure probability of a Flit error after FEC to be less than $3 \times 10^{-5}$.

A Forward Error Correction (FEC) mechanism is used to deal with the high FBER in the Data Stream. Since FEC works on fixed sized code words, Flit (flow control unit) will be used for sending/ receiving TLPs and DLLPs in a data stream. A low-overhead FEC will be used to keep the latency low. This will be augmented with a strong CRC at Flit level for high reliability. Link level retry will be deployed at the Flit level in Flit Mode. Ordered Sets will be protected through replication for Data Rates of $64.0 \mathrm{GT} / \mathrm{s}$ and above. Additionally, the precoding mechanism described below will be used for all scrambled bits to help minimize the number of errors in an error burst within a Lane.

# 4.2.3.1.2 1b/1b Scrambling 

The scrambling mechanism in the $64.0 \mathrm{GT} / \mathrm{s}$ Data Rate is identical to that for the $8.0,16.0$, and $32.0 \mathrm{GT} / \mathrm{s}$ Data Rates and is already covered in $\S$ Section 4.2.2.4, except for the T50 / TS1 / TS2 / SKP Ordered Set rules defined below. § Figure 4-25 demonstrates the scrambler on the Transmitter side. All Data Stream bits as well as some Ordered Set bits are scrambled.

- TS1 and TS2 Ordered Sets:
- Symbols 0 and 8 bypass scrambling.
- Symbols 1 through 6 and Symbols 9 through 14 are scrambled.
- Symbols 7 and 15 bypass scrambling if required for DC Balance, but they are scrambled if not required for DC Balance.
- T50 Ordered Sets:
- Symbols 0 and 8 bypass scrambling
- Symbols 1 through 6 and Symbols 9 through14 use NRZ-based scrambling
- NRZ-based scrambling consists of scrambling all 8 bits and then, in place of gray-coding, forcing the even bit 21 to be identical to the odd bit (21+1) [where 0 s/s3]. This ensures that only voltage levels 0 and 3 are sent.

- Symbols 7 and 15 bypass scrambling if required for DC Balance; else they carry even parity of Symbols 1 through 6 and Symbols 9 through 14 respectively with NRZ-scrambling
- All Symbols in TS0 are NRZ-based (i.e., each UI maps to voltage levels 0 or 3, encoded as 00b or 10b). Only TS0 Ordered Set is designed to be NRZ-based in 64.0 GT/s Data Rate.
- SKP Ordered Sets:
- When processing Ordered Sets outside of a Data Stream, receivers use the 1b/1b SKP decode rules in § Section 4.2.3.1.5 . When processing Ordered Sets inside a Data Stream, receivers use the 1b/1b SKP decode rules in § Section 4.2.3.2 . If it is determined by the Receiver that the Ordered Set is a SKP Ordered Set, then the LFSR is not advanced for any Symbol of the Block, as specified in § Section 4.2.2.4.


# IMPLEMENTATION NOTE: NRZ-BASED SCRAMBLING 

During NRZ-based scrambling, forcing the even bit $2 i$ to be identical to the odd bit (2i+1) [where $0 \leq i \leq 3$ ] can be performed after gray-coding or instead of gray-coding. The result will be the same either way.

### 4.2.3.1.3 Gray Coding at 64.0 GT/s and Higher Data Rates

Only scrambled bits on a 2-bit aligned boundary are Gray coded, when both bits are scrambled. All bits in the Data Stream are scrambled and Gray coded. Only some Symbols of the TS1/TS2 Ordered Sets are scrambled - those are Gray coded, while the unscrambled symbols are not Gray coded. All TS0 Ordered Set Symbols to be Half Scrambled undergo NRZ-based scrambling, as described in § Section 4.2.3.1.2. § Figure 4-25 represents the sequence of Gray Coding, which is followed by Tx Precoding, when enabled, followed by the PAM4 voltage translation on the Tx side as well as the Rx side, considering an error $E_{n}$ that may affect the nth 2-bit quantity on the channel.

Gray Coding is only enabled in the PAM4 mode (at 64.0 GT/s and above Data Rates). Gray-coding works on aligned 2-bit quantities on a per-Lane basis. On the Transmit side, input $G_{n}\left(G_{n 1} G_{n 0}\right)$ is transformed to output $P_{n}\left(P_{n 1} P_{n 0}\right)$, using the Gray code encoding where the input $00 b, 01 b, 10 b, 11 b$ becomes $00 b, 01 b, 11 b$, and 10 b respectively in the output. This can be represented by the equations: $P_{n 1}=G_{n 1}$ and $P_{n 0}=G_{n 1}{ }^{\wedge} G_{n 0}$. The Receive side is identical and can be represented as: $G_{n 1}=P_{n 1}$ and $G_{n 0}=P_{n 1}{ }^{\wedge} P_{n 0}$. § Table 4-6 demonstrates how a likely error of $\pm 1$ on voltage level at most affects one bit with Gray Coding.
![img-21.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-21.jpeg)

Figure 4-25 The Sequence of Gray Coding, Precoding, and PAM4 voltage translation on an aligned 2-bit boundary on a per Lane

Table 4-6 Effect of $+/-1$ voltage level error on the wire for various PAM4 voltage levels - at most one bit flips with an error on a UI

| Voltage Level | Resulting Voltage Level |  |
| :--: | :--: | :--: |
|  | Error of +1 | Error of -1 |
| 0 | 1 | 0 (no error) |
| 1 | 2 | 0 |
| 2 | 3 | 1 |
| 3 | 3 (no error) | 2 |

# 4.2.3.1.4 Precoding at 64.0 GT/s and Higher Data Rates 

Only scrambled bits on a 2-bit aligned boundary are precoded, when both bits are scrambled and precoding is enabled. Precoding is bypassed for all Symbols of TSO Ordered Sets. Other than the precoding mechanism described here, all the precoding rules in $\S$ Section 4.2.2.5 apply to $1 \mathrm{~b} / 1 \mathrm{~b}$ encoding with the exception of TSO Ordered Set. § Figure 4-25 represents the Precoding on the Transmit as well as Receive side. On the Transmit side, the input is $P_{n}$ and the output is $T_{n} . T_{n-1}$ represents the output from the precoder in the previous UI. When the prior UI was unscrambled and precoding is enabled, $T_{n-1}$ is set to 00 b . The output $T_{n}$ will be converted to the PAM4 voltage levels described above, when precoding is enabled. The channel may inject an error $E_{n}$ (no error means $E_{n}=00 b$ ). On the Receive side, $R_{n}=T_{n}+E_{n}$. The input to the Precoding logic is $R^{\prime}{ }_{n}\left(R_{n}=T_{n}+e_{n}\right)$, where $e_{n}$ is inclusive of the error on the wire $E_{n}$ as well as any internal DFE propagated error. The output of the precoding logic is $P^{\prime}{ }_{n}$, when precoding is enabled. The Truth Table for the Precoding function for the Transmit and Receive side is shown in § Table 4-7 and § Table 4-8. Precoding can help mitigate the number of errors in a burst.

Table 4-7 Truth Table
for Precoding on the
Transmit side

| $T_{n}$ |  |  |  |  |
| :--: | :--: | :--: | :--: | :--: |
| $P_{n}$ | $T_{n-1}$ |  |  |  |
|  | 00 | 01 | 11 | 10 |
| 00 | 00 | 11 | 01 | 10 |
| 01 | 01 | 00 | 10 | 11 |
| 11 | 11 | 10 | 00 | 01 |
| 10 | 10 | 01 | 11 | 00 |

Table 4-8 Truth Table
for Precoding on the
Receive side

| $P_{n}^{\prime}$ |  |  |  |
| :--: | :--: | :--: | :--: |
| $R_{n}^{\prime}$ | $R_{n-1}^{\prime}$ |  |  |
|  | 00 | 01 | 11 |
| 00 | 00 | 01 | 11 |
| 01 | 01 | 10 | 00 |
| 11 | 11 | 00 | 10 |
| 10 | 10 | 11 | 01 |

# IMPLEMENTATION NOTE: HOW DOES PRECODING HELP REDUCE THE NUMBER OF ERRORS? 

Precoding is effective with Gray coding on certain channels to reduce the impact of errors in the presence of DFE. It works similar to the precoding in $32.0 \mathrm{GT} / \mathrm{s}$, except here it works on 2-bit aligned quantities with PAM4 encoding. The most likely error scenario is $+/-1$ on the voltage level over one UI with PAM4 signaling. $\S$ Table 4-6 demonstrates the resulting voltage level under this error scenario and the resulting bit error with Gray code encoding. Gray Coding results in at most a single bit flip within that UI. Error propagation due to DFE will most likely occur in consecutive UIs. Under these assumptions, precoding ensures that the error appears in two bits within a wire: when the error gets introduced in the wire and the UI after the DFE burst stops. For cases such as error voltage magnitude is $>+1$ or $<-1$ or for cases where the DFE introduces errors in non-contiguous UI's, precoding may not be effective.

The precoding equation on Transmit side, based on the Truth Table in $\S$ Table 4-7 is: $T_{n}=\left(P_{n}-T_{n-1}\right) \bmod 4$, which is equivalent to $P_{n}=\left(T_{n}+T_{n-1}\right) \bmod 4$. The precoding equation on the Receive side, based on the Truth Table in § Table 4-8 is: $P^{\prime}{ }_{n}=\left(R_{n}+R_{n-1}\right) \bmod 4$. This can be simplified as: $P^{\prime}{ }_{n}=\left(T_{n}+e_{n}+T_{n-1}+e_{n-1}\right) \bmod 4=\left(P_{n}+e_{n}+e_{n-1}\right)$ $\bmod 4$. When we have the first error burst on the wire, $E_{n}=+/-1$ which will translate to $e_{n}=E_{n}(+/-1)$. So, with FBER, one bit gets affected in the UI where the external error happened. In the subsequent UIs, in the absence of any additional external errors, $e_{n}=-e_{n-1}$ or 0 ( 0 when DFE stops propagating the error, when it does propagate the magnitude is negative of the earlier error since the corresponding tap has a negative weight). If the error propagates due to DFE, $e_{n}+e_{n-1}=0$. If it stops propagating, $e_{n}$ becomes $+/-1$. So only two bit errors will be observed when precoding is effective: first bit error in the UI where the first error occurred in the wire and the UI following when DFE stopped propagating the error burst.
§ Table 4-9 illustrates the concept with an error in the channel and subsequent DFE error propagations. The bits after scrambling to be sent across the Link across successive UIs are in the first row, represented as $G_{n}$ (pre-gray coding). The different stages are represented in subsequent rows in the table. It must be noted that after gray coding (starting with $T_{n}$ ) until we decode with the gray-coding at the Receiver $\left(G^{\prime}{ }_{n}\right)$, we are dealing with voltage levels of $0,1,2,3$. The channel error occurs with the PAM-4 Symbol in UI \#1 of magnitude -1, which causes only one error of magnitude in the Receiver pin $\left(R_{n}\right)$. However, due to DFE burst, the error propagates in the Receiver circuits from UI\# 1 through $5\left(R^{\prime}{ }_{n}\right)$. Once we precede in the Receiver, these errors occur in two places, UI \#1 and 6, as shown in $P^{\prime}{ }_{n}$, which then translates to two bit errors, one each in UI \#1 and 6, as shown in $G^{\prime}{ }_{n}$.

Table 4-9 Example of precoding with an error in the channel and DFE error propagation at the Receiver 5

|  |  | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
| :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: |
|  | $G_{n}$ | 10 | 11 | 10 | 11 | 00 | 01 | 00 | 01 |
|  | $P_{n}$ | 11 | 10 | 11 | 10 | 00 | 01 | 00 | 01 |
|  | $T_{n}\left(\left\langle\left(P_{n} T_{n-1}\right) \bmod 4\right)\right.$ | 3 | 3 | 0 | 2 | 2 | 3 | 1 | 0 |
|  | $E_{n}$ <br> (Channel Error) | 0 | $-1$ | 0 | 0 | 0 | 0 | 0 | 0 |
|  | $R_{n}$ | 3 | 2 | 0 | 2 | 2 | 3 | 1 | 0 |
|  | DFE Error | 0 | 0 | $+1$ | $-1$ | $+1$ | $-1$ | 0 | 0 |

|  | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| $\mathrm{e}_{\mathrm{n}}$ <br> (Net Error: $\mathrm{E}_{\mathrm{n}}$ - DFE Error | 0 | -1 | +1 | -1 | +1 | -1 | 0 | 0 |
| $\mathrm{R}_{\mathrm{n}}^{\prime}$ <br> (Difference from $\mathrm{T}_{\mathrm{n}}$ is an error) | 3 | 2 | 1 | 1 | 3 | 2 | 1 | 0 |
| $\mathrm{P}_{\mathrm{n}}^{\prime+(\mathrm{e}_{\mathrm{n}} \cdot \mathrm{R}_{\mathrm{n}} \cdot \mathrm{I} \text { mod } 4)}$ | 3 | 1 | 3 | 2 | 0 | 1 | 3 | 1 |
| $\mathrm{G}_{\mathrm{n}}^{\prime}$ <br> (Difference from $\mathrm{G}_{\mathrm{n}}$ is an error) | 10 | 01 | 10 | 11 | 00 | 01 | 10 | 01 |

# 4.2.3.1.5 Ordered Set Blocks at 64.0 GT/s and Higher Data Rates 

All Ordered Sets with the exception SKP Ordered Sets (i.e., TS0, TS1, TS2, EIOS, EIEOS and SDS) are 16 Bytes long on both the Transmit and the Receive side. SKP Ordered Sets are 40 Bytes long on the Transmit side and can be 24, 32, 40, 48 or 56 bytes long on the Receive side. Ordered Sets exhibit a greater degree of redundancy than the corresponding Ordered Sets at Data Rates lower than 64.0 GT/s. The redundancy is required due to the high FBER with correlated errors with PAM4 signaling. The Ordered Sets are described in detail in § Section 4.2.5.1, § Section 4.2.5.3, § Section 4.2.5.7, and § Section 4.2.8.3 .

While processing Ordered Sets outside of a Data Stream, the following rules apply for the EIEOS, SKP OS, and EIOS, after obtaining Block alignment:

- An EIEOS is considered to be received under the following conditions:
- any 5 or more aligned and consecutive bytes in each of the first and last 8 bytes of a Block match the corresponding bytes of an EIEOS and
- either Symbol 0 or Symbol 8 of the Block matches the corresponding byte of an EIEOS. A Receiver is permitted to ignore up to one bit mismatch for this comparison

While in Aligned phase, a Receiver must switch the block boundary by $>1$ UI on an EIEOS Ordered Set or should shift the Block boundary by $\leq 1$ UI only if it receives an EIEOS followed by a valid first symbol of an expected Ordered Set.

While searching for an EIEOS, the 8-byte boundary can begin in any aligned UI and the bits must be looked at prior to performing gray coding, precoding, or descrambling in the Receiver side.

- An EIOS is considered to be received under the following conditions:
- any 5 or more aligned bytes of the first 8 bytes of a Block match the corresponding bytes of an EIOS and
- either Symbol 0 or Symbol 8 of the Block matches the corresponding byte of an EIOS. When an EIOS is received, the Lane is ready to enter Electrical Idle irrespective of what is received in the last 7 Bytes of the Block.
- A SKP OS is considered to begin under the following conditions: (i) any 5 or more aligned bytes of the first 8 bytes of a Block match a SKP, and (ii) either Symbol 0 is a SKP or Symbol 8 of the Block is either a SKP or a SKP_END. It looks at each subsequent aligned 8 byte chunks and applies the following rules:

- If any 5 or more aligned bytes match SKP_END or the current chunk is the fifth 8 byte chunk after the start of the SKP OS (i.e., current set is bytes 40 through 47 from the start of the SKP OS), the SKP OS will terminate after the next aligned 8 byte chunk.


# IMPLEMENTATION NOTE: <br> INFERRING ORDERED SETS WITHIN AND OUTSIDE OF DATA STREAMS 

Since most bytes of TS0/TS1/TS2 Ordered Sets are scrambled (except Symbols 0 and 8), one has to get an exact match in at least Symbol 0 or 8 , in addition to the match in 5 Byte positions to infer the EIEOS, EIOS, or SKP OS, while not in a Data Stream. The rules for detection of TS0, TS1, TS2, and SDS Ordered Set appears with the description of the Ordered Set. Since SKP, EIEOS, and EIOS can appear within a Data Stream, there are slightly different rules for inferring those in a Data Stream than while not in a Data Stream, taking advantage of the fact that none of these Ordered Sets have any scrambling, to ensure higher fault tolerance during a Data Stream. Hence the rules for detection of EIOS, EIEOS and SKP OS are specified twice; in this section as well as in § Section 4.2.8.3.

### 4.2.3.1.6 Alignment at Block/ Flit Level for 1b/1b Encoding

With 1b/1b encoding, Block alignment aligns with the Ordered Set boundary on a per-Lane basis. Once this is accomplished, the Flit-level alignment at the Link level occurs automatically with the Data Stream that starts at the end of the Control SKP Ordered Set that immediately follows the SDS Ordered Set sequence. Once the Flit alignment starts, it adjusts to the Flit boundary. When an Ordered Set is scheduled to be received and the received Ordered Set is a Control SKP Ordered Set, the Flit boundary is automatically adjusted to start at the conclusion of the Ordered Set.

The Block level alignment occurs with the EIEOS Ordered Set in Configuration or Recovery states. The EIEOS is a unique pattern that Receivers use to determine the start/ end of the Ordered Set boundary in the received bit stream. Conceptually, Receivers can be in three different phases of alignment: Unaligned, Aligned, and Locked. These phases are defined to illustrate the required behavior, but are not meant to specify a required implementation.

## Unaligned Phase

Receivers enter this phase after a period of Electrical Idle, such as when the data rate is changed to one that uses 1b/1b encoding or when they exit a low-power Link state, or if directed (by an implementation specific method). In this phase, Receivers monitor the received bit stream for a match against all 128 bits of the EIEOS bit pattern. When one is detected, they adjust their alignment to it and proceed to the Aligned Phase.

## Aligned Phase

Receivers monitor the received bit stream for the EIEOS OS and the received Blocks for a Start of Data Stream (SDS) Ordered Set. If an EIEOS bit pattern is detected on an alignment that does not match the current alignment and the LTSSM is in the Recovery. RcvrLock state, Receivers must adjust their alignment to the newly received EIEOS bit pattern. If an EIEOS bit pattern is detected on an alignment that does not match the current alignment, the LTSSM is in the Recovery. RcvrCfg state, and the subsequent Symbol matches the first Symbol of an expected Ordered Set, Receivers must adjust their alignment to the newly received EIEOS bit pattern. If an SDS Ordered Set is received, Receivers proceed to the Locked phase. The Data Stream starts after the SDS Ordered Set sequence is received, though Flits start after the Control SKP Ordered Set immediately succeeding the SDS Ordered Set sequence. The conclusion of the SKP Ordered Set immediately following an SDS Ordered Set sequence marks the start of the Flit boundary at the end of the Control SKP Ordered Set.

# Locked Phase 

Receivers must not adjust their Block or Flit alignment while in this phase. Data Blocks are expected to be received after the Control SKP Ordered Set following the SDS Ordered Set sequence, and adjusting the Block alignment would interfere with the processing of these Blocks. Receivers must return to the Unaligned or Aligned Phase if the Data Stream is terminated by the Link entering Recovery and/or a Framing Error is detected.

## Additional Requirements:

- While in the Aligned Phase, Receivers must adjust their Block alignment, as necessary, when a Control SKP Ordered Set is received. See $\S$ Section 4.2.8 for more information on SKP Ordered Sets.
- While in the Locked phase, Receivers must adjust their Block and Flit alignment, as necessary, when a Control SKP Ordered Set is received.
- After any LTSSM transition to Recovery, Receivers must ignore all received TS Ordered Sets until they receive an EIEOS. Conceptually, receiving an EIEOS validates the Receiver's alignment and allows TS Ordered Set processing to proceed. If a received EIEOS initiates an LTSSM transition from L0 to Recovery, Receivers are permitted to process any TS Ordered Sets that follow the EIEOS or ignore them until another EIEOS is received after entering Recovery.
- Receivers are permitted to transition from the Locked phase to the Unaligned or Aligned phase as long as Data Stream processing is stopped.
- Loopback Leads: While in Loopback.Entry, Leads must be capable of adjusting their Receiver's Block / Flit alignment to received EIEOS bit patterns. While in Loopback.Active, Leads are permitted to transmit an EIEOS and adjust their Receiver's Block alignment to the looped back bit stream.
- Loopback Followers: While in Loopback.Entry, Followers must be capable of adjusting their Receiver's Block alignment to received EIEOS bit patterns. While in Loopback.Active, Followers must not adjust their Receiver's Block alignment, except at the scheduled Control SKP Ordered Set boundary. Conceptually, the Receiver is directed to the Locked phase when the Follower starts to loop back the received bit stream.


### 4.2.3.2 Processing of Ordered Sets During Flit Mode Data Stream

Flit Mode does not employ the EDS ('End of Data Stream') token. Instead, a Data Stream can be terminated by either an EIOS (prior to entering a low power state, such as L1) or an EIEOS (upon entry into Recovery). SKP Ordered Sets appear at periodic intervals during the Data Stream (as defined in § Table 4-30). When necessary, the EIOS or EIEOS must be transmitted in place of the SKP Ordered Set, as defined in $\S$ Section 4.2.3.4.2.5 . Therefore, these three Ordered Sets are defined such that one cannot alias to another even with a burst error.

Ordered Set processing during or at the end of a Data Stream must be performed as follows by the Receiver for $64.0 \mathrm{GT} / \mathrm{s}$ or higher Data Rates:

- Receiver checks the first 8 bytes of the Ordered Set in the place where an Ordered Set is expected to appear.
- Any 5 or more aligned bytes of the first aligned 8 byte chunk matches the corresponding bytes of either a SKP, EIOS, or EIEOS for the corresponding Ordered Set to be considered valid in each of the active Lanes. Failure to meet this requirement is considered a framing error and the Link must enter Recovery.
- If a SKP Ordered Set is inferred from the first 8 bytes, the Receiver looks at each subsequent aligned 8 byte chunks and applies the following rules:
- If at least each of any 5 aligned bytes matches SKP_END or the current chunk is the fifth 8 byte chunk after the start of the SKP OS (i.e., current set is bytes 40 through 47), the SKP OS will terminate after the next aligned 8 byte chunk. At the conclusion of the SKP OS the Data Stream resumes, if the SKP OS terminated with the receipt of 5 aligned bytes of SKP_END. If the SKP OS is being terminated without receipt of 5 aligned bytes of SKP_END, a Framing Error occurs.

- Any of the following conditions are Framing Error even with the receipt of a proper OS on each of active Lanes and the Link must enter Recovery:
- Receiving any combination of these ordered sets simultaneously on any two active Lanes: EIEOS and EIOS or EIEOS and SKP OS,
- Receiving a SKP OS of unequal lengths across all Lanes
- Receiving a combination of EIOS and SKP OS and any of the following conditions is true:
- LOp has not been enabled in the Link
- The set of Lanes receiving EIOS are not contiguous
- The set of Lanes receiving SKP OS are not contiguous
- The number of Lanes receiving SKP OS is not a valid link width (1, 2, 4, or 8)
- Any of these Lanes is receiving neither SKP OS nor EIOS.
- If an EIEOS is inferred from the first 8 bytes on any active Lane, the Data Stream ends with the receipt of the EIEOS and the Link must enter Recovery when permitted by the LTSSM.
- If an EIOS is inferred from the first 8 bytes across any active Lanes, the Link prepares to enter the low-power state for which the negotiation has occurred (L0p or L1 or L2).
- Data stream continues on a reduced set of Lanes at the conclusion of the OS if all of the following conditions are true:
- An EIOS is inferred from the first 8 bytes on some active Lanes,
- The remaining active Lanes received the SKP OS on 1, 2, 4 or 8 Lanes, and
- LOp has been enabled in the Link

# IMPLEMENTATION NOTE: 

## 64.0 GT/S DATA STREAM ORDERED SET PROCESSING 5

A Flow chart depicting part of the above flow is illustrated in § Figure 4-26. This flow chart is not meant to specify all the rules but illustrate some of the rules for illustration purposes.
![img-22.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-22.jpeg)

Figure 4-26 Processing of Ordered Sets during or at the end of a Data Stream in Flit mode at 64.0 GT/s Data Rate

### 4.2.3.3 Data Stream in Flit Mode 5

The flit size is 256 Bytes, allocated as follows:

- 236 Bytes for TLPs (Bytes 0 through 235 in the Flit, as shown in § Table 4-10 through § Table 4-14)
- 6 Bytes for Data Link Layer Payload (DLP in Bytes 236 through 241 in the Flit, shown as DLP0..6 in § Table 4-10 through § Table 4-14)
- 8 Bytes for CRC (Bytes 242 through 249 in the Flit, shown as CRC0.. 7 in § Table 4-10 through § Table 4-14), and
- 6 Bytes for ECC (Bytes 250 through 255 arranged as 3 groups of ECC0[0:1], ECC1[0:1], ECC2[0:1], as shown in § Table 4-10 through § Table 4-14).

A flit is interleaved across the Lanes in the Link in a Byte aligned fashion, as shown in § Table 4-10 through § Table 4-14. Each Byte corresponds to a Symbol in the 64.0 GT/s and above Data Rates, a Symbol within the Data Block with 128b/ 130b encoding, for $8.0 \mathrm{GT} / \mathrm{s}, 16.0 \mathrm{GT} / \mathrm{s}$, and $32.0 \mathrm{GT} / \mathrm{s}$; and gets converted to a 10 b Symbol using the $8 \mathrm{~b} / 10 \mathrm{~b}$ encoding for

2.5 GT/s and 5.0 GT/s Data Rates. Since the TLP and DLP have fixed allocation of bytes within each flit, the Port will schedule the packets of each type accordingly. The 8 Bytes of CRC protects the TLP and DLLP Bytes (and not the ECC bytes). The 6 Bytes of ECC protects the entire flit, including the CRC. Even though the ECC protection is needed only with the high FBER with the PAM4 signaling at 64.0 GT/s and higher Data Rates, it will be deployed for the lower Data Rates for consistency.

On a Link layer retry, only the TLPs will be replayed, and not the DLP. Thus, the link layer payload in each flit (DLP) does not enter the Link Layer Retry Buffer (LLRB) at the Transmitter. The DLP fields in the retried flits will reflect the latest Data Link Layer Payload. Thus, a DLP can be lost and the same mechanism of replication/ aggregation for DLLPs ensures that the data link layer messages gets delivered to the Link partner.

The FEC is a 3-way interleaved ECC, with each ECC code capable of correcting a single Byte error. The interleaving is done so that a burst error of up to 16 bits in any Lane does not impact more than a Byte in each interleaved ECC code word. Each of the interleaved ECC has a different color. Thus, all blue colored Bytes [e.g., 0, 3, 6, 9,..., 231, 234, DLP1, DLP4, CRC1, CRC4, and CRC7] are part of ECC Group 0 and are covered by the 2 blue colored ECC0[0] and ECC0[1] bytes (which are placed in the last Symbol of the flit in Lanes 12 and 15 respectively).

Table 4-10 File Layout in a x16 Link 3

| Description |  | Lane |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: |
|  |  | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
| 16 <br> Symbol <br> times | TLP Bytes $[0 \ldots 223]$ | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|  |  | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24 | 25 | 26 | 27 | 28 | 29 | 30 | 31 |
|  |  | 32 | 33 | 34 | 35 | 36 | 37 | 38 | 39 | 40 | 41 | 42 | 43 | 44 | 45 | 46 | 47 |
|  |  | 48 | 49 | 50 | 51 | 52 | 53 | 54 | 55 | 56 | 57 | 58 | 59 | 60 | 61 | 62 | 63 |
|  |  | 64 | 65 | 66 | 67 | 68 | 69 | 70 | 71 | 72 | 73 | 74 | 75 | 76 | 77 | 78 | 79 |
|  |  | 80 | 81 | 82 | 83 | 84 | 85 | 86 | 87 | 88 | 89 | 90 | 91 | 92 | 93 | 94 | 95 |
|  |  | 96 | 97 | 98 | 99 | 100 | 101 | 102 | 103 | 104 | 105 | 106 | 107 | 108 | 109 | 110 | 111 |
|  |  | 12 | 112 | 113 | 114 | 115 | 116 | 117 | 118 | 120 | 121 | 122 | 123 | 124 | 125 | 126 | 127 |
|  |  | 128 | 129 | 130 | 131 | 132 | 133 | 134 | 135 | 136 | 137 | 138 | 139 | 140 | 141 | 142 | 143 |
|  |  | 144 | 145 | 146 | 147 | 148 | 149 | 150 | 151 | 152 | 153 | 154 | 155 | 156 | 157 | 158 | 159 |
|  |  | 160 | 161 | 162 | 163 | 164 | 165 | 166 | 167 | 168 | 169 | 170 | 171 | 172 | 173 | 174 | 175 |
|  |  | 176 | 177 | 178 | 179 | 180 | 181 | 182 | 183 | 184 | 185 | 186 | 187 | 188 | 189 | 190 | 191 |
|  |  | 192 | 193 | 194 | 195 | 196 | 197 | 198 | 199 | 200 | 201 | 202 | 203 | 204 | 205 | 206 | 207 |
|  |  | 206 | 209 | 210 | 211 | 212 | 213 | 214 | 215 | 216 | 217 | 218 | 219 | 220 | 221 | 222 | 223 |
|  | TLP, DLP | 224 | 225 | 226 | 227 | 228 | 229 | 230 | 231 | 232 | 233 | 234 | 235 | DLP 0 | DLP 1 | DLP 2 | DLP 3 |
|  | DLP, CRC, ECC | DLP 4 | DLP 5 | CRC 0 | CRC 1 | CRC 2 | CRC 3 | CRC 4 | CRC 5 | CRC 6 | CRC 7 | ECC 10 | ECC 11 | ECC 2 | ECC 3 | ECC 4 | ECC 5 |

# IMPLEMENTATION NOTE: 

The first 236 Bytes $(0 . .235)$ are for TLP(s), next 6 Bytes are for Data Link Layer Payload (DLP0..5), next 8 Bytes for CRC (CRC0..7) and the last 6 Bytes are for ECC (ecc 0..1). The FEC is a 3-way interleaved ECC, each capable of correcting a single Byte, with the interleaving shown in 3 colors.

| Description |  | Lane |  |  |  |  |  |  |
| :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: |
|  |  | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
| 32 <br> Symbol times | TLP Bytes [0...231] | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|  |  | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|  |  | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 |
|  |  | 24 | 25 | 26 | 27 | 28 | 29 | 30 | 31 |
|  |  | 32 | 33 | 34 | 35 | 36 | 37 | 38 | 39 |
|  |  | 40 | 41 | 42 | 43 | 44 | 45 | 46 | 47 |
|  |  | 48 | 49 | 50 | 51 | 52 | 53 | 54 | 55 |
|  |  | 56 | 57 | 58 | 59 | 60 | 61 | 62 | 63 |
|  |  | 63 | 65 | 66 | 67 | 68 | 69 | 70 | 71 |
|  |  | 72 | 73 | 74 | 75 | 76 | 77 | 78 | 79 |
|  |  | 80 | 81 | 82 | 83 | 84 | 85 | 86 | 87 |
|  |  | 88 | 89 | 90 | 91 | 92 | 93 | 94 | 95 |
|  |  | 96 | 97 | 98 | 99 | 100 | 101 | 102 | 103 |
|  |  | 104 | 105 | 106 | 107 | 108 | 109 | 110 | 111 |
|  |  | 112 | 113 | 114 | 115 | 116 | 117 | 118 | 119 |
|  |  | 120 | 121 | 122 | 123 | 124 | 125 | 126 | 127 |
|  |  | 128 | 129 | 130 | 131 | 132 | 133 | 134 | 135 |
|  |  | 136 | 137 | 138 | 139 | 140 | 141 | 142 | 143 |
|  |  | 144 | 145 | 146 | 147 | 148 | 149 | 150 | 151 |
|  |  | 152 | 153 | 154 | 155 | 156 | 157 | 158 | 159 |
|  |  | 160 | 161 | 162 | 163 | 164 | 165 | 166 | 167 |
|  |  | 168 | 169 | 170 | 171 | 172 | 173 | 174 | 175 |
|  |  | 176 | 177 | 178 | 179 | 180 | 181 | 182 | 183 |
|  |  | 184 | 185 | 186 | 187 | 188 | 189 | 190 | 191 |
|  |  | 192 | 193 | 194 | 195 | 196 | 197 | 198 | 199 |
|  |  | 200 | 201 | 202 | 203 | 204 | 205 | 206 | 207 |
|  |  | 208 | 209 | 210 | 211 | 212 | 213 | 214 | 215 |
|  |  | 216 | 217 | 218 | 219 | 220 | 221 | 222 | 223 |
|  |  | 224 | 225 | 226 | 227 | 228 | 229 | 230 | 231 |
| TLP Bytes [231...235], DLP Bytes |  | 232 | 233 | 234 | 235 | DLP 0 | DLP 1 | DLP 2 | DLP 3 |
|  | DLP, CRC Bytes | DLP 4 | DLP 5 | CRC 0 | CRC 1 | CRC 2 | CRC 3 | CRC 4 | CRC 5 |
|  | CRC, ECC Bytes | CRC 6 | $\begin{gathered} \text { CRC } \\ 7 \end{gathered}$ | $\begin{gathered} \text { ECC1 } \\ {[0:]} \end{gathered}$ | $\begin{gathered} \text { ECC2 } \\ {[0:]} \end{gathered}$ | $\begin{gathered} \text { ECC0 } \\ {[0:]} \end{gathered}$ | $\begin{gathered} \text { ECC1 } \\ {[1:]} \end{gathered}$ | $\begin{gathered} \text { ECC2 } \\ {[1:]} \end{gathered}$ | $\begin{gathered} \text { ECC0 } \\ {[1:]} \end{gathered}$ |

# IMPLEMENTATION NOTE: 

Note that the same set of Bytes form the same ECC group in the 3-way interleaved FEC as in a x16 Link. The first 236 Bytes $(0 . .235)$ are for TLP(s), next 6 Bytes are for Data Link Layer Payload (DLPO..5), next 8 Bytes for CRC (CRCO..7) and the last 6 Bytes are for ECC (ecc 0..1). The FEC is a 3-way interleaved ECC, each capable of correcting a single Byte, with the interleaving shown in 3 colors.

Table 4-12 FDI interleaving in a x4 Link

| Description |  | Lane |  |  |  |
| :--: | :--: | :--: | :--: | :--: | :--: |
|  |  | 0 | 1 | 2 | 3 |
| 64 <br> Symbol <br> times | TLP Bytes $[0 \ldots 235]$ | 0 | 1 | 2 | 3 |
|  |  | 4 | 5 | 6 | 7 |
|  |  | 8 | 9 | 10 | 11 |
|  |  | $\vdots$ | $\vdots$ | $\vdots$ | $\vdots$ |
|  |  | 224 | 225 | 226 | 227 |
|  |  | 228 | 229 | 230 | 231 |
|  |  | 232 | 233 | 234 | 235 |
|  | DLP, CRC, ECC Bytes | DLP 0 | DLP 1 | DLP 2 | DLP 3 |
|  |  | CPC 4 | CPC 5 | CRC 0 | CRC 1 |
|  |  | CRC 2 | CRC 3 | CRC 4 | CRC 5 |
|  |  | CRC 6 | CRC 7 | ECC1 [0] | ECC2 [0] |
|  |  | $\operatorname{BCC0}$ | ECC1 [1] | ECC2 [1] | ECC0 [1] |
|  |  | $[0]$ | ECC1 [1] | ECC2 [1] | ECC0 [1] |

## IMPLEMENTATION NOTE:

Note that the same set of Bytes form the same ECC group in the 3-way interleaved FEC as in a x16/x8 Link. The first 236 Bytes $(0 . .235)$ are for TLP(s), next 6 Bytes are for Data Link Layer Payload (DLPO..5), next 8 Bytes for CRC (CRCO..7) and the last 6 Bytes are for ECC (ecc 0..1). The FEC is a 3-way interleaved ECC, each capable of correcting a single Byte, with the interleaving shown in 3 colors.

Table 4-13 FDI interleaving in a x2 Link

| Description |  | Lane |  |
| :--: | :--: | :--: | :--: |
|  |  | 0 | 1 |
| 128 <br> Symbol <br> times | TLP Bytes $[0 \ldots 235]$ | 0 | 1 |
|  |  | 2 | 3 |
|  |  | 4 | 5 |
|  |  | $\vdots$ | $\vdots$ |
|  |  | 230 | 231 |
|  |  | 232 | 233 |
|  |  | 234 | 235 |
|  | DLP Bytes | DLP 0 | DLP 1 |

| Description |  | Lane |  |
| :--: | :--: | :--: | :--: |
|  |  | 0 | 1 |
| CRC Bytes |  | DLP 2 | DLP 3 |
|  |  | DLP 4 | DLP 5 |
|  | CRC Bytes | CRC 0 | CRC 1 |
|  |  | CRC 2 | CRC 3 |
|  |  | CRC 4 | CRC 5 |
|  |  | CRC 6 | CRC 7 |
| ECC Bytes |  | CRC 101 | ECC2 01 |
|  |  | CRC 0 | ECC3 02 |
|  |  | ECC2 [1] | ECC0 [3] |

# IMPLEMENTATION NOTE: 

Note that the same set of Bytes form the same ECC group in the 3 -way interleaved FEC as in a x16/x8/x4 Link. The first 236 Bytes $(0 . .235)$ are for TLP(s), next 6 Bytes are for Data Link Layer Payload (DLP0..5), next 8 Bytes for CRC (CRC0..7) and the last 6 Bytes are for ECC (ecc 0..1). The FEC is a 3 -way interleaved ECC, each capable of correcting a single Byte, with the interleaving shown in 3 colors.
![img-23.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-23.jpeg)

![img-24.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-24.jpeg)

# IMPLEMENTATION NOTE: 

Note that the same set of Bytes form the same ECC group in the 3-way interleaved FEC as in a x16/x8/x4/x2 Link. The first 236 Bytes $(0 . .235)$ are for TLP(s), next 6 Bytes are for Data Link Layer Payload (DLPO..5), next 8 Bytes for CRC (CRC0..7) and the last 6 Bytes are for ECC (ecc 0..1). The FEC is a 3-way interleaved ECC, each capable of correcting a single Byte, with the interleaving shown in 3 colors.

A conceptual representation of the processing of Symbols in the Flit Mode for the 64.0 GT/s Data Rate on the Transmit and the Receive side is demonstrated in § Figure 4-21, § Figure 4-22, and § Figure 4-25. A conceptual representation of the Flit Mode and Non-Flit Mode processing with 8b/10b encoding for $2.5 \mathrm{GT} / \mathrm{s}$ and $5.0 \mathrm{GT} / \mathrm{s}$ as well as with 128b/130b encoding for $8.0 \mathrm{GT} / \mathrm{s}, 16.0 \mathrm{GT} / \mathrm{s}$, and $32.0 \mathrm{GT} / \mathrm{s}$ for the Transmit and Receive side is shown in and respectively.
![img-25.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-25.jpeg)

Figure 4-27 Flit Mode and Non-Flit Mode processing with 8b/10b and 128b/130b encoding on the Transmit side

![img-26.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-26.jpeg)

Figure 4-28 Flit Mode and Non-Flit Mode processing with 8b/10b and 128b/130b encoding on the Receive side

# 4.2.3.4 Bytes in Flit Layout 

### 4.2.3.4.1 TLP Bytes in Flit 6

The TLP Bytes in the flit carry Transaction Layer TLPs. Since the Flit Mode does not support STP tokens, these TLP bytes must be populated by the Transaction Layer, irrespective of whether it has a TLP to send or not. A TLP may span across multiple flits depending on its length and placement. The following rules must be observed:

- When the transaction layer does not have a TLP to send, it sends a NOP TLP (1DW). Once a NOP TLP is scheduled to be sent, NOP TLPs must be scheduled till the next 4DW aligned boundary within the Flit or the Flit boundary, whichever is earlier.
- NOP TLPs do not consume any credits.
- The TLPs in Flit Mode have information in predetermined position to determine the length of the TLPs, including the case where TLP prefix is used. See § Chapter 2. for details.
- The following rules apply for the non-NOP TLPs in bytes 0 through 127 of the Flit (i.e., the TLP bytes within the first Flit half) and bytes 128 through 235 of the Flit (i.e., the TLP bytes within the second Flit half):
- No more than 8 TLPs, including partial TLPs.

Receivers are permitted to check this rule.

- If checked, this is logged as a Data Link Protocol Error in the receiving Port (see § Section 6.2).
- If a TLP at the end of a Flit gets poisoned or nullified through Flit_Status, and if that TLP extends to subsequent Flits, each of those Flits must also be poisoned or nullified through Flit_Status so that the poisoned or nullified Flit_Status is set in the Flit where the TLP ends. A Receiver is permitted to only look at the Flit_Status field in the Flit where the TLP ends.
- A TLP that gets nullified through the Flit_Status field is ignored by the Receiver if the Flit is valid, but the credits must be released.
- A TLP that gets poisoned or nullified through the Flit_Status field must be succeeded by only NOP TLPs through the end of the Flit.

# IMPLEMENTATION NOTE: <br> HANDLING TLPS SPANNING MULTIPLE FLITS 6 

When a TLP spans multiple Flits, it may be interrupted by SKPs, NOP Flits, transitions through Recovery and/or other unavoidable scenarios. Transmitters should attempt to avoid this interruption whenever possible for optimal bandwidth and latency and Receivers must be able to deal with scenarios where the TLP may be interrupted.

Example: $\S$ Table 4-15 shows an example of TLP placement in the Flit Mode for a x16 Link. For narrower Link widths, similar arrangements will exist subject to the rules mentioned above.

- This flit starts with a continuation of the remaining 2 DWs from TLP 19 (the 3rd DW of Hdr and 1 DW of Data).
- TLP 20 (4DW Hdr and 1DW Data) immediately starts in Lane 8 and ends in Lane 11 in the following Symbol.
- Since the Transmitter has nothing to send, it sends NOP sending till the 4DW aligned boundary, which is in Lane 15.
- TLPs 22, and 23 are scheduled without any intervening NOP.
- After TLP 23, the Transmitter did not have anything to send and sends 7 NOPs, aligned to a 4DW boundary till TLP 24 is ready, which continues till the flit boundary for TLP Bytes.
- After that we have 6 Bytes of DLP, 8 Bytes of CRC covering the 236 Bytes of TLP and 6 Bytes of DLP in the flit.
- Then we have the 3 sets of interleaved ECC, 2 bytes each, covering the entire 256B flit.

It should be noted that every Byte of each TLP as well the DLP is covered by one of the 3 ECC groups and each TLP/ DLP is a member of all 3 ECC groups, and as indicated in the color code.

| Description |  |  |  |  |  |  |  | Lane |  |  |  |  |  |  |  |  |
| :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: |
|  |  |  | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
| 16 <br> Symbol <br> times | TLP Bytes [0...223] | H2 | H2 | H2 | H2 | D0 | D0 | D0 | H0 | H0 | H0 | H0 | H1 | H1 | H1 | H1 | H1 |
|  |  | ...TLP 19 * |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | H2 | H2 | H2 | H3 | H3 | H3 | H3 | D0 | D0 | D0 | D0 | D0 |  |  |  |  |
|  |  | ...TLP 20 * |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | H0 | H0 | H0 | H1 | H1 | H1 | H1 | H2 | H2 | H2 | H2 | H3 | H3 | H3 | H3 | H3 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | D0 | D0 | D0 | D0 | D1 | D1 | D1 | D1 |  |  |  |  |  |  |  |  |
|  |  | ...TLP 21 * |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | H0 | H0 | H0 | H0 | H1 | H1 | H1 | H1 | H2 | H2 | H2 | H2 | H0 | H0 | H0 | H0 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | H1 | H1 | H1 | H1 | H2 | H2 | H2 | H2 | H3 | H3 | H3 | H3 | D0 | D0 | D0 | D0 |
|  |  | ...TLP 23 ... |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | D1 | D1 | D1 | D1 | D2 | D2 | D2 | D3 | D3 | D3 | D3 | D3 | D4 | D4 | D4 | D4 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | D5 | D5 | D5 | D5 |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | ...TLP 23 * |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | H0 | H0 | H0 | H1 | H1 | H1 | H1 | H2 | H2 | H2 | H2 | D0 | D0 | D0 | D0 |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | D5 | D5 | D5 | D5 | D6 | D6 | D6 | D6 | D7 | D7 | D7 | D7 | D8 | D8 | D8 | D8 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |


![img-27.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-27.jpeg)

# 4.2.3.4.2 DLP Bytes in Flit 

In every flit, 6 bytes are allotted to carry the information carried by the Data Link Layer Packets (DLLPs) described in § Chapter 3. . While the DLP bytes are designed to reuse the DLLP mechanism and formats for the most part, some optimizations have been made to effectively carry the Ack/Nak flit along with an optimized credit release (Optimized_Update_FC, defined below) or a traditional DLLP. An encoding has been added in the DLP to provide UpdateFC credits for PRH, PRD, and NPRH within one 32 bit payload of DLP. The following table summarizes the DLP encodings.

Three Flit Types have been defined in § Table 4-16, along with their intended usages. They all have the same CRC and FEC mechanism. The distinction is made for ease of reference based on the TLP and DLP Bytes they carry. IDLE Flits are only sent after the Control SKP Ordered Set following the SDS Ordered Set Sequence with 128b/130b and 1b/1b encoding. For 8b/10b encoding, an IDLE Flit will be sent at the conclusion of the TS2 Ordered Set (or after a SKP OS following the last TS2 Ordered Set, depending on the SKP insertion interval). With 8b/10b encoding, an Ordered Set vs. a Flit is distinguished the lack of a COM at the end of a SKP OS. IDLE Flits continue to be sent until a Flit other than an IDLE Flit must be sent. Devices that advertise infinite credits across all FC/VC are permitted to send NOP DLLP if there is no DLLP to be sent in DLP 2, 3, 4, and 5.

All received Flits meet one or more of the following definitions:

- A valid Flit is one where all of the following are true:
- CRC check passes after performing FEC correction (if needed)
- No ECC group of the FEC is reporting an uncorrectable error (by ECC), as described in § Section 4.2.3.4.2.4
- The Flit Usage field does not have a Reserved encoding (see § Figure 4-30).
- The Flit_Status field does not have a Reserved encoding (see § Table 4-19).
- An FEC-correctable Flit is a valid Flit that passes the CRC check after performing the FEC correction.
- An FEC uncorrectable error is an error in a Flit that is detected by the CRC after FEC correction or 'uncorrectable error' reported by an ECC group in the FEC which may result in a NAK and a replay.
- An IDLE Flit is a Flit with the Flit Usage 00b, Sequence Number 0 and Replay Command 00b as described in § Table 4-16. Implementations are permitted but not recommended to check additional fields.
- An invalid Flit is a Flit that is not a valid Flit.

- A valid non-IDLE Flit is a valid Flit that is either a NOP Flit or a Payload Flit. All subsequent Flits after the first valid non-IDLE Flit are non-IDLE Flits while the Link is in LO.
![img-28.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-28.jpeg)

Figure 4-29 DLP Byte to Bit Number Assignment
![img-29.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-29.jpeg)

Figure 4-30 DLP Bit usage

Table 4-16 Flit Types

| Flit Type | TLP Bytes | DLP Bytes 0,1 | DLP Bytes 2..5 |
| :--: | :--: | :--: | :--: |
| IDLE <br> Flit | Transmitters must place 00 h in all 236 bytes. | Transmitters must place 00 h in both bytes. | NOP2 DLLP (see § Figure 3-8) |
| NOP Flit | NOP Flit Payload (see § Section 4.2.3.4.2.2 ) | Flit Usage $=00 b$ <br> Flit Sequence Number ${ }^{66}=$ NEXT_TX_FLIT_SEQ_NUM - 1 or, if REPLAY_IN_PROGRESS is 1b, the Sequence Number of the most recent Payload Flit that was sent Other Fields = Any valid encoding | Any valid encoding |
| Payload <br> Flit | TLP content, packed per rules described in § Section 4.2.3.4.1. A portion of at least one non-NOP TLP in the 236 Bytes | Flit Usage $=01 b$ <br> Flit Sequence Number $!=00$ b if Replay Command is 00 b Other Fields = Any valid encoding | Any valid encoding |
| Table 4-17 DLP Bytes in the Flit |  |  |  |
| Field | Location | Encoding |  |
| Flit Usage | DLP0: <br> Bits 7:6 | 00b <br> 01b <br> Others | IDLE Flit or NOP Flit <br> Payload Flit <br> Reserved |
| Prior Flit was <br> Payload | DLP0: <br> Bit 5 | 0b <br> 1b | Prior flit was a NOP Flit or IDLE Flit <br> Prior flit was a Payload Flit |
| Type of DLLP Payload | DLP0: <br> Bit 4 | 0b <br> 1b | DLLP Payload in DLP 2..5 <br> Optimized_Update_FC or Flit_Marker in DLP 2..5 |

[^0]
[^0]:    66. A NOP Flit does not consume a Flit Sequence Number.

| Field | Location | Encoding |
| :--: | :--: | :--: |
| Replay Command $[1: 0]$ | DLP0: <br> Bits 3:2 | 00b <br> 01b <br> 10b <br> 11b | The Flit Sequence Number included in the Flit is an Explicit Flit Sequence Number of the transmitted Flit. <br> Ack of Flit Sequence Number from Receiver. The included Flit Sequence Number indicates the Flit Sequence Number of the last valid Flit received. <br> Nak requesting a Replay of all unacknowledged Flits. The included Flit Sequence Number indicates the Flit Sequence Number of the last valid Flit received. <br> Nak requesting a Replay of a single Flit (Flit Sequence Number + 1). The included Flit Sequence Number indicates the Flit Sequence Number of the last valid Flit received. |
| Flit Sequence Number $[9: 0]$ | (DLP0: <br> Bits 1:0, <br> DLP1: <br> Bits 7:0) | 10-bit sequence number applied to Flits. See Flit Sequence Number and Retry Mechanism. <br> DLP0[1:0] contains Flit Sequence Number[9:8] and DLP1[7:0] has Flit Sequence Number[7:0]. |
| DLLP Payload | (DLP2, DLP3, <br> DLP4, DLP5) | Type of DLLP Payload is 0b <br> Regular DLLP Payload (see § Chapter 3. ) |
| Optimized_Update_FC | Bits 31:0 <br> DLP2 is 31:24 <br> DLP3 is 23:16 <br> DLP4 is 15:8 <br> DLP5 is 7:0 | Type of DLLP Payload is 1b and bit $31=0$ b (see § Table 4-18) |
| Flit_Marker |  | Type of DLLP Payload is 1 b and bit $31=1$ b (see § Table 4-19) |

In the Table above, a Transmitter must not use the Reserved encodings.
![img-30.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-30.jpeg)

Figure 4-31 Optimized_Update_FC

Table 4-18 Optimized_Update_FC

| Bit Location | Description |
| :--: | :-- |
| 31 | Optimized Update FC Indicator Must be "0" |
| $30: 28$ | VC |
| $27: 20$ | Shared Non-Posted HdrFC - Shared credits on this VC |
| $19: 12$ | Shared Posted HdrFC - Shared credits on this VC |
| $11: 0$ | Shared Posted DataFC - Shared credits on this VC |

![img-31.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-31.jpeg)

Figure 4-32 Flit_Marker

Table 4-19 Flit_Marker

| Bit Location | Description |
| :--: | :--: |
| 31 | Flit_Marker Indicator Must be "1" |
| $30: 29$ | Flit_Status - Indicates the validity of the Last TLP in this Flit. Encoding is: <br> 00b No special information - No TLPs that end in this Flit are Nullified or Poisoned. <br> TLPs that starts in this Flit and ends in a subsequent Flit are marked in that Flit. <br> 01b Last TLP Nullified - Last TLP ending in current Flit is Nullified <br> This mechanism replaces the EDB Mechanism in Non-Flit Mode framing. <br> 10b Last TLP Poisoned - Last TLP ending in the current Flit is Poisoned <br> See § Section 2.7.2 regarding how this mechanism relates to the Transaction Layer EP bit mechanism. <br> 11b Reserved |
| 28 | PTM Message contained in this Flit - In Flit Mode, timestamps for Precision Time Measurement messages are measured at the Flit level rather than at the TLP level. This bit indicates that this Flit contains the last symbol of a non-nullified PTM Message. <br> Nullified PTM Messages do not set this bit. <br> Poisoned PTM Messages are not permitted. |

For the DLLP Payload in the above table, the Optimized_Update_FC is used to transmit performance critical NPRH, PRH, and PRD credits in 4 Bytes. For debug as well as ease of use by debug tools such as Logic Analyzers, devices must send at least one DLLP every $10 \mu \mathrm{~s}$ with an UpdateFC DLLP per VC with the scaled credit information. It is strongly recommended that a Transmitter cycles through the VCs with finite non-0 credits in the Optimized_Update_FC as long as there is a credit to be released in the corresponding VC.

Receivers are permitted to check for the following Flit errors:

- Reserved value of Flit Usage (see § Figure 4-30).
- Reserved encoding of Flit_Status field in a Flit_Marker (see § Table 4-19).
- Invalid sequence number (see § Section 4.2.3.4.2.1.4).
- Violations of the TLP packing rules as defined in § Section 4.2.3.4.1

If checked, these Flit errors are logged as a Data Link Protocol Error in the receiving Port (see § Section 6.2).
Three NOP Flit types have been defined in § Table 4-20, along with their intended usages. All types defined below are considered NOP Flits and must follow all NOP Flit rules outlined in this specification. Refer to § Section 6.37.1 for the usage model of NOP.Debug and NOP.Vendor Flit types.

The NOP Flit types defined below may rely on information provided by upper layers, but the transmission is done solely by the Physical Layer independently of the upper layers. Transmission may begin as soon as the Link enters L0. For NOP.Empty and NOP.Debug Flits, no credit checks are required for transmission. For NOP.Vendor Flits, implementation of any credit mechanism and associated checking for the credits is implementation specific. A receiver that comprehends non-zero encodings must silently drop any NOP.Debug or NOP.Vendor Flits if it does not support processing them. Receiver behavior for designs that do support processing NOP.Debug or NOP.Vendor Flits is implementation specific but transmitting/receiving NOP.Debug and NOP.Vendor Flits must not affect the link state.

Table 4-20 NOP Flit Types

| NOP Flit Type | Usage |
| :-- | :-- |
| NOP.Empty | Empty payload (see § Section 4.2.3.4.2.2.1) |
| NOP.Debug | Deliver debug information (see § Section 4.2.3.4.2.2.2) |
| NOP.Vendor | Deliver vendor-defined information (see § Section 4.2.3.4.2.2.3) |

All NOP Flit TLPs use a common definition of the first DW of the NOP Flit Payload. Subsequent content depends on the value of NOP Flit Type (see § Figure 4-33).
![img-32.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-32.jpeg)

Figure 4-33 NOP Flit Common Header

Table 4-21 NOP Flit Common Header Fields

| Field | Location | Definition |
| :--: | :--: | :--: |
| NOP Flit Type | Byte 0: Bits 7:4 | 0h <br> 1h <br> 2h to Eh <br> Fh <br> NOP.Empty Flit <br> NOP.Debug Flit and NOP.Vendor Flit <br> Incrementing per-NOP Flit Type counter of NOP.Debug and NOP.Vendor Flit types |
|  |  |  |
| Reserved | Byte 2: Bits 7:0 | Reserved |
| NOP Stream ID | Byte 3: Bits 7:0 | NOP.Empty Flit |

Transmitter populates with 00th, Receiver is permitted to ignore

| Field | Location | Definition |
| :-- | :-- | :-- |
|  |  | NOP.Debug Flit and <br> NOP.Vendor Flit |

A non-empty NOP Flit is a NOP Flit with a non-zero NOP Flit Type encoding.
A NOP Stream is a sequence of NOP Flits that are sourced by a Transmitter. The NOP Stream ID field in the NOP Flit provides a mechanism to identify the original Transmitter of the NOP Flit.

- The NOP Flit Extended Capability structure (see § Section 7.8.14) provides software control (via the NOP Stream ID Start and Number of NOP Streams fields) over the range of values that a Transmitter may use. The usage details of the programmed range are implementation specific.
- The combination of NOP Flit Type value and and NOP Stream ID value uniquely identifies a NOP Stream and its value must be unique across all entities transmitting NOP Flits over a given Link.
- NOP.Empty Flits must always transmit a NOP Stream ID value of 00h.

The NOP Flit Counter field in the NOP Flit allows dropped or missing non-empty NOP Flits to be detected.

- Every NOP Stream must have an independent counter.
- Each NOP Stream must start with a Nop Flit Counter value of 000h and every subsequent non-empty NOP Flit of the NOP Stream that is transmitted must increment the counter by one. The NOP Flit Counter must roll-over after FFEh.
- A NOP Flit Counter value of FFFh indicates an error or unexpected behavior occurred. This provides an indication that an unknown number of Flits of a NOP Stream were lost. This indication is only a hint since the Flit containing this indication could itself be lost.
- When a NOP Stream is disabled, its NOP Flit Counter must reset to 000h.
- NOP.Empty Flits must always transmit a NOP Flit Counter value of 000h.

Note: Receivers may forward received NOP Flits with a NOP Stream ID other than FFh to a different Link. In this scenario, the forwarded NOP Flit must preserve all fields as received, including the NOP Flit Type, the NOP Flit Counter and the NOP Stream ID. The forwarding Receiver is permitted to overwrite the NOP Flit Counter to FFFh in certain situations. The forwarding mechanism is implementation specific on a best-effort basis, with no guarantee of delivery. § Section 6.37.1 .

After the first DW, the remaining TLP Bytes carry the NOP Flit Payload, whose definition varies depending on the NOP Flit Type. See § Section 4.2.3.4.2.2 for NOP Flit Payload definitions.

# 4.2.3.4.2.1 Flit Sequence Number and Retry Mechanism 

## Term Definitions

## Explicit Sequence Number Flit

A Payload Flit or NOP Flit with Replay Command 00b.
Ack Flit
A Flit with Replay Command 01b.
Standard Nak Flit
A Flit with Replay Command 10b.
Selective Nak Flit
A Flit with Replay Command 11b.

# Nak Flit 

A Flit with either Replay Command 10b or 11b.

## Standard Nak

A Nak that requests a Replay of all unacknowledged Flits.

## Selective Nak

A Nak that requests a Replay of a specific Flit.

## Standard Replay

A Replay of all unacknowledged Flits in the TX Retry Buffer.

## Selective Replay

A Replay of a specific Flit from the TX Retry Buffer.

## TX Retry Buffer

The buffer which stores information for transmitted Flits until the Flit has been acknowledged by the Link partner. ${ }^{67}$

## RX Retry Buffer

The buffer which stores information for received Flits until the Flit has been consumed by the Receiver. ${ }^{68}$

## Nak Ignore Window

A time window in which received Nak Flits are ignored for a specific Flit Sequence Number.

- The Nak Ignore Window is started when a Payload Explicit Sequence Number Flit is sent with Flit Sequence Number = NAK_IGNORE_FLIT_SEQ_NUM +1 and NAK_IGNORE_FLIT_SEQ_NUM $!=0 .{ }^{69}$


## Flags and Counters

## NEXT_TX_FLIT_SEQ_NUM

10-bit unsigned counter that tracks the Flit Sequence Number for transmitted Flits.

- Set to 001h in DL_Inactive state.
- Behavior defined in NEXT_TX_FLIT_SEQ_NUM Rules.
- Usage defined in § Section 4.2.3.4.2.1.2, § Section 4.2.3.4.2.1.3, § Section 4.2.3.4.2.1.4, and § Section 4.2.3.4.2.1.6 .


## TX_ACKNAK_FLIT_SEQ_NUM

Stores the 10-bit Sequence Number to be transmitted in the next Ack Flit or Nak Flit.

- Set to 1023 in DL_Inactive state.
- Usage defined in § Section 4.2.3.4.2.1.2, § Section 4.2.3.4.2.1.3, and § Section 4.2.3.4.2.1.5 .


## CONSECUTIVE_TX_EXPLICIT_SEQ_NUM_FLITS

2-bit unsigned counter which tracks how many consecutive Explicit Sequence Number Flits have been sent by the Transmitter.

- Set to 00b IDLE Flit Handshake Phase.
- Behavior defined in CONSECUTIVE_TX_EXPLICIT_SEQ_NUM_FLITS Rules
- Usage defined in § Section 4.2.3.4.2.1.2 and § Section 4.2.3.4.2.1.3 .


## CONSECUTIVE_TX_NAK_FLITS

3-bit unsigned counter which tracks how many consecutive Nak Flits have been sent by the Transmitter.

- Set to 000b in the IDLE Flit Handshake Phase.

[^0]
[^0]:    67. The Link Speed and Link Width that a Device supports should be taken into consideration when sizing the TX Retry Buffer.
    68. Expected Nak latency should be considered when sizing the RX Retry Buffer to avoid overflow when using the Selective Replay mechanism.
    69. The Nak Ignore Window is used in the two specific scenarios: 1) A Replay is started due to a received Nak Flit. 2) A Payload Explicit Sequence Number Flit with Flit Sequence Number = NEXT_TX_FLIT_SEQ_NUM is sent after having received a Nak with Flit Sequence Number = NEXT_TX_FLIT_SEQ_NUM - 1.

- This counter saturates at 111 b and does not roll over to 000 b .
- Behavior defined in CONSECUTIVE_TX_NAK_FLITS Rules.
- Usage defined in § Section 4.2.3.4.2.1.3 and § Section 4.2.3.4.2.1.7 .


# NEXT_EXPECTED_RX_FLIT_SEQ_NUM 

10-bit unsigned counter that stores the expected Flit Sequence Number of the next valid non-IDLE non-duplicate Flit to be received.

- Set to 001 h in DL_Inactive state.
- Behavior and usage defined in § Section 4.2.3.4.2.1.5 .


## IMPLICIT_RX_FLIT_SEQ_NUM

10-bit unsigned counter that tracks the implicit Flit Sequence Number of received Flits.

- Set to 000 h in DL_Inactive state.
- Behavior defined in IMPLICIT_RX_FLIT_SEQ_NUM Rules.
- Usage defined in § Section 4.2.3.4.2.1.5 .


## ACKD_FLIT_SEQ_NUM

Stores the 10-bit Flit Sequence Number received in the most recently processed valid Ack Flit or Nak Flit.

- Set to 3FFh in DL_Inactive state.
- Behavior defined in § Section 4.2.3.4.2.1.4 .
- Usage defined in § Section 4.2.3.4.2.1.4 and § Section 4.2.3.4.2.1.6 .


## NON_IDLE_EXPLICIT_SEQ_NUM_FLIT_RCVD

Flag to indicate that a Non-IDLE Explicit Sequence Number Flit has been received since the last entry to IDLE Flit Handshake Phase.

- Set to 1 when first Non-IDLE Explicit Sequence Number Flit is received after last entry to IDLE Flit Handshake Phase.
- This must be updated before evaluating Ack, Nak, and Discard Rules in § Section 4.2.3.4.2.1.5 .
- Cleared on entry to IDLE Flit Handshake Phase.
- Usage defined in IMPLICIT_RX_FLIT_SEQ_NUM Rules.


## REPLAY_SCHEDULED

Flag to indicate that a Flit has been scheduled to be replayed from the TX Retry Buffer.

- Cleared when in DL_Inactive state.
- Behavior defined in § Section 4.2.3.4.2.1.6 .
- Usage defined in § Section 4.2.3.4.2.1.2, § Section 4.2.3.4.2.1.6, and § Section 4.2.3.4.2.1.7 .


## REPLAY_SCHEDULED_TYPE

Indicates whether a Standard Replay or a Selective Replay has been scheduled.

- If REPLAY_SCHEDULED is 1b:
- REPLAY_SCHEDULED_TYPE 0b indicates a Standard Replay.
- REPLAY_SCHEDULED_TYPE of 0b will be referred to as STANDARD_REPLAY.
- REPLAY_SCHEDULED_TYPE 1b indicates a Selective Replay.
- REPLAY_SCHEDULED_TYPE of 1b will be referred to as SELECTIVE_REPLAY.
- Behavior defined in § Section 4.2.3.4.2.1.6 .
- Usage defined in § Section 4.2.3.4.2.1.6 and § Section 4.2.3.4.2.1.7 .

# REPLAY_IN_PROGRESS 

Flag to indicate that the Transmitter is sending Flits from the TX Retry Buffer.

- Cleared when in DL_Inactive state.
- Behavior defined in REPLAY_IN_PROGRESS Rules.
- Usage defined in § Section 4.2.3.4.2.1.2, § Section 4.2.3.4.2.1.6, and § Section 4.2.3.4.2.1.7 .


## TX_REPLAY_FLIT_SEQ_NUM

Stores the 10-bit Flit Sequence Number of the first Flit to be replayed from the TX Retry Buffer.

- Set to 000 h in DL_Inactive state.
- Behavior defined in § Section 4.2.3.4.2.1.6.
- Usage defined in § Section 4.2.3.4.2.1.4, § Section 4.2.3.4.2.1.6, and § Section 4.2.3.4.2.1.7 .


## FLIT_REPLAY_NUM

3-bit unsigned counter that tracks the number of times that a Replay has been initiated without making forward progress.

- Set to 000b in DL_Inactive state.
- Behavior defined in § Section 4.2.3.4.2.1.4 and § Section 4.2.3.4.2.1.7 .
- Usage defined in § Section 4.2.3.4.2.1.7 .


## REPLAY_TIMEOUT_FLIT_COUNT

11-bit unsigned counter that counts the number of Payload Flits and NOP Flits sent since the last Ack of an outstanding Flit.

- Set to 000 h in DL_Inactive state.
- This counter saturates at 7 FFh and does not roll over to 000 h .
- Behavior defined in REPLAY_TIMEOUT_FLIT_COUNT Rules
- Usage defined in § Section 4.2.3.4.2.1.6 .


## NAK_SCHEDULED

Flag to indicate that a Nak Flit has been scheduled for transmission.

- Cleared when in DL_Inactive state.
- Behavior defined in § Section 4.2.3.4.2.1.5 .
- Usage defined in § Section 4.2.3.4.2.1.2, § Section 4.2.3.4.2.1.3, and § Section 4.2.3.4.2.1.5 .


## NAK_SCHEDULED_TYPE

Indicates whether a Standard Nak Flit or a Selective Nak Flit should be sent.

- Set to 0 b when in DL_Inactive state.
- If NAK_SCHEDULED is 1b,
- NAK_SCHEDULED_TYPE Ob indicates a Standard Nak Flit.
- NAK_SCHEDULED_TYPE of 0b will be referred to as STANDARD_NAK.
- NAK_SCHEDULED_TYPE 1b indicates a Selective Nak Flit.
- NAK_SCHEDULED_TYPE of 1b will be referred to as SELECTIVE_NAK.
- Behavior defined in § Section 4.2.3.4.2.1.5 .
- Usage defined in § Section 4.2.3.4.2.1.2, § Section 4.2.3.4.2.1.3, and § Section 4.2.3.4.2.1.5 .


## NAK_WITHDRAWAL_ALLOWED

Flag that indicates an invalid Flit was received but should not be Nak'd if the subsequent received Flit has Prior Flit was Payload set to 0 b (indicating that the invalid Flit was a NOP Flit).

- Cleared when in DL_Inactive state.
- Behavior and usage defined in § Section 4.2.3.4.2.1.5 .


# NAK_IGNORE_FLIT_SEQ_NUM 

Stores the 10-bit Flit Sequence Number to be ignored during the Nak Ignore Window.

- Set to 000 h when in DL_Inactive state.
- Behavior defined in § Section 4.2.3.4.2.1.4 and § Section 4.2.3.4.2.1.6
- Usage defined in § Section 4.2.3.4.2.1.6 .


## NEXT_RX_FLIT_SEQ_NUM_TO_STORE

Stores the 10-bit Flit Sequence Number of the next Flit to be stored in the RX Retry Buffer.

- Cleared when in DL_Inactive state.
- Behavior and usage defined in § Section 4.2.3.4.2.1.5 .


## RX_RETRY_BUFFER_OVERFLOW

Flag to indicate that a Flit was unable to be stored in the RX Retry Buffer due to the buffer becoming full before a Selective Replay was received for an outstanding Selective Nak.

- Cleared when in DL_Inactive state.
- Behavior and usage defined in § Section 4.2.3.4.2.1.5 .


## RX_RETRY_BUFFER_LAST_FLIT_SEQ_NUM

Stores the 10-bit Flit Sequence Number of the last Flit stored in the RX Retry Buffer if the RX Retry Buffer overflows.

- Cleared when in DL_Inactive state.
- Behavior and usage defined in § Section 4.2.3.4.2.1.5 .


## MAX_UNACKNOWLEDGED_FLITS

Maximum number of unacknowledged Flits outstanding.

- Set to the lesser of:
- Number of Flits that can be stored in the TX Retry Buffer.
- 511 Flits
- Usage defined in § Section 4.2.3.4.2.1.4, § Section 4.2.3.4.2.1.5, and § Section 4.2.3.4.2.1.6.


## General Rules

## Flit Sequence Number Rules:

- The valid range of Flit Sequence Numbers for Payload Flits is 1-1023.
- Flit Sequence Number 0 is only used for IDLE Flits.
- NOP Flits do not consume a Flit Sequence Number.
- A NOP Flit that is also an Explicit Sequence Number Flit sets Flit Sequence Number to NEXT_TX_FLIT_SEQ_NUM - 1.
- If no Payload Flits have been transmitted, Flit Sequence Number 1023 is used.
- If REPLAY_IN_PROGRESS is 1b, the transmitter is strongly recommended to set the Explicit Sequence Number to the Sequence Number of the most recent Payload Flit that was sent.
- All Flit Sequence Number counters will roll-over from 1023 to 1.
- Whenever text in this section refers to adding to, subtracting from, incrementing, or decrementing a sequence number, it is implied that sequence number rollover rules stated above will be followed.
- Two transmitted or received Flits are considered consecutive, even if they are separated by a SKP OS.

- The Nak Ignore Window should be the lesser of:
- Measured Ack/Nak Latency of the Link +1 maximum sized SKP Ordered Set +2 Flits
- 300 ns
- It is strongly recommended that an Ack or Nak for a received Flit is transmitted within the following times of receiving the Flit on the Receiver pins. The following times apply unless the transmitter is sending an Ordered Set. The measurement is from the first bit of the received Flit on the Receiver pins to the first bit of the associated Ack Flit or Nak Flit on the transmitter pins. § Section 4.2.3.4.2.1.5 describes when an Ack or Nak should be scheduled.
- x16: 50 ns
- x8: 52 ns
- x4: 56 ns
- x2: 64 ns
- x1: 80 ns


# Transmitter Rules 

- The Transmitter must store the following information of transmitted Payload Flits in the TX Retry Buffer:
- TLP Bytes associated with non-NOP TLPs
- Flit_Status
- Flit Sequence Number


## MAX_UNACKNOWLEDGED_FLITS Outstanding:

- If (NEXT_TX_FLIT_SEQ_NUM - ACKD_FLIT_SEQ_NUM) mod 1023 > MAX_UNACKNOWLEDGED_FLITS:
- The Transmitter must not accept any new TLPs from the Transaction Layer.
- The Transmitter must send a NOP Flit if REPLAY_SCHEDULED is 0b and REPLAY_IN_PROGRESS is 0b.


## REPLAY_IN_PROGRESS Rules:

- If REPLAY_IN_PROGRESS is 1b:
- The Transmitter must not accept any new TLPs from the Transaction Layer.
- REPLAY_IN_PROGRESS is cleared if either of the following conditions are true:
- REPLAY_SCHEDULED_TYPE is STANDARD_REPLAY and all unacknowledged Flits in the TX Retry Buffer have been transmitted.
- REPLAY_SCHEDULED_TYPE is SELECTIVE_REPLAY and Flit with Flit Sequence Number equal to TX_REPLAY_FLIT_SEQ_NUM has been transmitted.


## CONSECUTIVE_TX_EXPLICIT_SEQ_NUM_FLITS Rules

- When an Explicit Sequence Number Flit is transmitted:
- CONSECUTIVE_TX_EXPLICIT_SEQ_NUM_FLITS is incremented.
- When a non-Explicit Sequence Number Flit is transmitted:
- CONSECUTIVE_TX_EXPLICIT_SEQ_NUM_FLITS is set to 0b.
- Also see Replay Schedule Rule 0.


## REPLAY_TIMEOUT_FLIT_COUNT Rules:

- When a Payload Flit or a NOP Flit is transmitted and the TX Retry Buffer is not empty:
- REPLAY_TIMEOUT_FLIT_COUNT is incremented.
- When an Ack or Nak is received that causes a Flit stored TX Retry Buffer to be purged:

- REPLAY_TIMEOUT_FLIT_COUNT is set to 0b.
- Also see Replay Schedule Rule 0.


# NEXT_TX_FLIT_SEQ_NUM Rules 

- After the Transmitter applies the Replay Command to a Payload Flit which is NOT being replayed from the TX Retry Buffer:
- NEXT_TX_FLIT_SEQ_NUM is incremented.
- NEXT_TX_FLIT_SEQ_NUM does not change when sending any of the following:
- An IDLE Flit
- A NOP Flit
- A Flit being replayed from the TX Retry Buffer


## Receiver Rules

- If a Receiver has scheduled a Selective Nak Flit, it must continue to store non-NOP TLP bytes and Flit Sequence Number of subsequent Flits in the RX Retry Buffer.
- After the Replay for a Selective Nak is received, received Flits must continue to be processed in order of Flit Sequence Number. The management of storage and processing of Flits received after the Selective Replay Flit is received is implementation specific
- See § Section 4.2.3.4.2.1.5 for Ack, Nak, and Discard rules.


## IMPLICIT_RX_FLIT_SEQ_NUM Rules

- The value of IMPLICIT_RX_FLIT_SEQ_NUM must be updated before evaluating the rules in § Section 4.2.3.4.2.1.5
- IMPLICIT_RX_FLIT_SEQ_NUM does not change if ANY of the following are true:
- A valid IDLE Flit is received.
- A valid Explicit Sequence Number Flit is received with Flit Sequence Number 0.
- Both of the following are true:
- NON_IDLE_EXPLICIT_SEQ_NUM_FLIT_RCVD is 0b
- Either of the following are true:
- An invalid Flit is received.
- A valid non-Explicit Sequence Number Flit is received.
- Both of the following are true:
- A valid NOP Flit is received with a non-explicit Flit Sequence Number.
- Either of the following are true:
- NAK_WITHDRAWAL_ALLOWED is 0b
- NAK_WITHDRAWAL_ALLOWED is 1b and Prior Flit was Payload is 1b
- All of the following are true:
- A valid Payload Flit with a non-explicit Flit Sequence Number is received.
- NAK_WITHDRAWAL_ALLOWED is 1b
- Prior Flit was Payload is 0b
- IMPLICIT_RX_FLIT_SEQ_NUM is incremented if both of the following are true:
- NON_IDLE_EXPLICIT_SEQ_NUM_FLIT_RCVD is 1b
- Any of the following are true:

- A valid Payload Flit with a non-explicit Flit Sequence Number is received and NAK_WITHDRAWAL_ALLOWED is 0b.
- A valid Payload Flit with a non-explicit Flit Sequence Number is received with Prior Flit was Payload set to 1b and NAK_WITHDRAWAL_ALLOWED is 1b.
- A invalid Flit is received.
- IMPLICIT_RX_FLIT_SEQ_NUM is set to N if both of the following are true:
- A valid non-IDLE Explicit Sequence Number Flit is received with Flit Sequence Number N.
- $\mathrm{N}!=0$.
- IMPLICIT_RX_FLIT_SEQ_NUM is decremented if ALL of the following are true:
- A valid NOP Flit with a non-explicit Flit Sequence Number is received.
- NAK_WITHDRAWAL_ALLOWED is 1b.
- Prior Flit was Payload is 0b.


# 4.2.3.4.2.1.1 IDLE Flit Handshake Phase 

## General Rules

- A Port enters this phase when the LTSSM enters Configuration.Idle or Recovery.Idle states.


## Transmitter Rules

- The Transmitter must send IDLE Flits as required by the LTSSM rules.
- The Transmitter moves to the Sequence Number Handshake Phase when the LTSSM enters the L0 state.


## Receiver Rules

- All received Flits are discarded.
- The Receiver moves to the Sequence Number Handshake Phase when two consecutive valid IDLE Flits have been received.


### 4.2.3.4.2.1.2 Sequence Number Handshake Phase

## General Rules

- Devices are permitted to perform Data Link Feature Exchange and Flow Control Initialization in this phase if the Data Link Control and Management State Machine is in the DL_Feature or DL_Init states, respectively.
- The Port transitions to the Normal Flit Exchange Phase when both of the following are true:
- The Port has transmitted 3 or more Ack Flits with non-zero Flit Sequence Numbers after having received one or more Explicit Sequence Number Flits with a non-zero Flit Sequence Number.
- The Port has transmitted 9 or more Explicit Sequence Number Flits with a non-zero Flit Sequence Number.
- If the Port is in this phase after sending 512 Flits with 1b/1b encoding or 256 Flits with 8b/10b or 128b/ 130b encoding, the Port must enter Recovery.


## Transmitter Rules

## Flit Replay Command Rules

- The Transmitter alternates between sending three consecutive Explicit Sequence Number Flit and one Ack Flit or Nak Flit while in this phase.

- The following conditions are listed in order of priority.
- A Transmitter must send an Explicit Sequence Number Flit if the following is true:
- CONSECUTIVE_TX_EXPLICIT_SEQ_NUM_FLITS < 3.
- A Transmitter must send a Standard Nak Flit if all of the following are true:
- NAK_SCHEDULED is 1b.
- NAK_SCHEDULED_TYPE is STANDARD_NAK.
- The conditions for sending an Explicit Sequence Number Flit were not met.
- A Transmitter must send a Selective Nak Flit if all of the following are true:
- NAK_SCHEDULED is 1b.
- NAK_SCHEDULED_TYPE is SELECTIVE_NAK.
- The conditions for sending an Explicit Sequence Number Flit were not met.
- The conditions for sending a Standard Nak Flit were not met.
- A Transmitter must send an Ack Flit if all of the following are true:
- The conditions for sending an Explicit Sequence Number Flit were not met.
- The conditions for sending a Standard Nak Flit were not met.
- The conditions for sending a Selective Nak Flit were not met.
- The Transmitter may send up to six consecutive Explicit Sequence Number Flits if the CONSECUTIVE_TX_EXPLICIT_SEQ_NUM_FLITS counter is reset due to Replay Schedule Rule 0.


# Flit Replay Transmit Rules 

- The Transmitter must only begin replaying Flits from the TX Retry Buffer when sending an Explicit Sequence Number Flit and CONSECUTIVE_TX_EXPLICIT_SEQ_NUM_FLITS is 0b.
- If the Transmitter is replaying a Flit from the TX Retry Buffer, it must use the sequence number of the Flit from its TX Retry Buffer when sending an Explicit Sequence Number Flit.
- See § Section 4.2.3.4.2.1.7 for additional replay transmit rules.


## Flit Sequence Number Rules

- When transmitting an Ack Flit or Nak Flit with a non-0 Flit Sequence Number:
- The Flit Sequence Number is set to the value of TX_ACKNAK_FLIT_SEQ_NUM.
- When transmitting an Explicit Sequence Number Flit:
- A NOP Flit must set Flit Sequence Number to NEXT_TX_FLIT_SEQ_NUM - 1.
- If REPLAY_IN_PROGRESS is 1b, the transmitter is permitted to set the Explicit Sequence Number to the Sequence Number of the most recent Payload Flit that was sent.
- A replayed Payload Flit must set Flit Sequence Number to the value stored for the Flit in the TX Retry Buffer.
- A non-replayed Payload Flit must set Flit Sequence Number to NEXT_TX_FLIT_SEQ_NUM.


## Receiver Rules

- Refer to § Section 4.2.3.4.2.1.4 for Ack and Nak processing rules.
- Refer to § Section 4.2.3.4.2.1.5 for Ack and Nak scheduling rules.
- Refer to § Section 4.2.3.4.2.1.6 for Replay scheduling rules.

# 4.2.3.4.2.1.3 Normal Flit Exchange Phase 

## Transmitter Rules

- While in this Phase, Explicit Sequence Number Flits are only sent according to the Flit Replay Command Rules defined in this section.
- If a Nak Flit is sent in this phase:
- A minimum of three consecutive Nak Flits must be sent unless any of the following are true:
- CONSECUTIVE_TX_NAK_FLITS is reset due to Replay Schedule Rule 0.
- The transmission of Flits is interrupted by an exit from the L0 state.
- The NAK_SCHEDULED flag is cleared.
- If an Explicit Sequence Number Flit is sent in this phase:
- Exactly three consecutive Explicit Sequence Number Flits must be sent unless either of the following are true:
- CONSECUTIVE_TX_EXPLICIT_SEQ_NUM_FLITS is reset due to Replay Schedule Rule 0.
- The transmission of Flits is interrupted by an exit from the L0 state.


## Flit Replay Command Rules

- The following conditions are listed in order of priority.
- A Transmitter must send an Explicit Sequence Number Flit if all of the following are true:
- Any of the following are true:
- REPLAY_SCHEDULED is 1b.
- REPLAY_IN_PROGRESS is 1b.
- CONSECUTIVE_TX_EXPLICIT_SEQ_NUM_FLITS > 0.
- All of the following are true ${ }^{70}$ :
- REPLAY_SCHEDULED is 0b.
- REPLAY_IN_PROGRESS is 0b.
- NAK_IGNORE_FLIT_SEQ_NUM! $=000 \mathrm{~h}$
- CONSECUTIVE_TX_EXPLICIT_SEQ_NUM_FLITS < 3.
- Either of the following are true:
- CONSECUTIVE_TX_NAK_FLITS equals 0.
- CONSECUTIVE_TX_NAK_FLITS > 2.
- A Transmitter must send a Standard Nak Flit if all of the following are true:
- NAK_SCHEDULED is 1b.
- NAK_SCHEDULED_TYPE is STANDARD_NAK.
- The conditions for sending an Explicit Sequence Number Flit were not met.
- A Transmitter must send a Selective Nak Flit if all of the following are true:
- NAK_SCHEDULED is 1b.
- NAK_SCHEDULED_TYPE is SELECTIVE_NAK.
- The conditions for sending an Explicit Sequence Number Flit were not met.
- The conditions for sending a Standard Nak Flit were not met.

- A Transmitter must send an Ack Flit if all of the following are true:
- The conditions for sending an Explicit Sequence Number Flit were not met.
- The conditions for sending a Standard Nak Flit were not met.
- The conditions for sending a Selective Nak Flit were not met.
- The Transmitter may send up to six consecutive Explicit Sequence Number Flits if the CONSECUTIVE_TX_EXPLICIT_SEQ_NUM_FLITS counter is reset due to Replay Schedule Rule 0.


# Flit Replay Transmit Rules 

- The Transmitter must only begin replaying Flits from the TX Retry Buffer when sending an Explicit Sequence Number Flit and CONSECUTIVE_TX_EXPLICIT_SEQ_NUM_FLITS is 0b.
- If the Transmitter is replaying a Flit from the TX Retry Buffer, it must use the sequence number of the Flit from its TX Retry Buffer when sending an Explicit Sequence Number Flit.
- See § Section 4.2.3.4.2.1.7 for additional replay transmit rules.


## Flit Sequence Number Rules

- When transmitting an Ack Flit or Nak Flit:
- The Flit Sequence Number is set to the value of TX_ACKNAK_FLIT_SEQ_NUM.
- When transmitting an Explicit Sequence Number Flit:
- A NOP Flit must set Flit Sequence Number to NEXT_TX_FLIT_SEQ_NUM - 1.
- If REPLAY_IN_PROGRESS is 1b, the transmitter is permitted to set the Explicit Sequence Number to the Sequence Number of the most recent Payload Flit that was sent.
- A replayed Payload Flit must set Flit Sequence Number to the value stored for the Flit in the TX Retry Buffer.
- A non-replayed Payload Flit must set Flit Sequence Number to NEXT_TX_FLIT_SEQ_NUM.


## CONSECUTIVE_TX_NAK_FLITS Rules

- When a Nak Flit is transmitted:
- CONSECUTIVE_TX_NAK_FLITS is incremented.
- When a non-Nak Flit is transmitted:
- CONSECUTIVE_TX_NAK_FLITS is set to 0b.
- Also see Replay Schedule Rule 0.


## Receiver Rules

- Refer to § Section 4.2.3.4.2.1.4 for Ack and Nak processing rules.
- Refer to § Section 4.2.3.4.2.1.5 for Ack and Nak scheduling rules.
- Refer to § Section 4.2.3.4.2.1.6 for Replay scheduling rules.


### 4.2.3.4.2.1.4 Received Ack and Nak Processing

- A received Ack or Nak with Flit Sequence Number 0 must be ignored.
- Processing of received Ack or Nak Flits must not interrupt a replay in progress.
- Handling an invalid Flit Sequence Number in a received Ack Flit or Nak Flit:
- If:
- A valid Ack Flit or Nak Flit is received with Flit Sequence Number N where one or more of the following are true:

- ((NEXT_TX_FLIT_SEQ_NUM - 1) - N) mod 1023 > MAX_UNACKNOWLEDGED_FLITS
- (N - ACKD_FLIT_SEQ_NUM) mod 1023 > MAX_UNACKNOWLEDGED_FLITS
- Then:
- The received Ack or Nak is ignored.
- A Data Link Protocol Error is logged in the receiving Port (see § Section 6.2 ).
- If a Receiver receives a valid Ack Flit or Nak Flit with Flit Sequence Number N, it must:
- Purge all Flits stored the TX Retry Buffer that are older than and including the Flit with Flit Sequence Number N.
- If (N - ACKD_FLIT_SEQ_NUM) mod $1023>0$ :
- FLIT_REPLAY_NUM is cleared.
- ACKD_FLIT_SEQ_NUM is set to N.
- If the received Flit was an Ack Flit:
- NAK_IGNORE_FLIT_SEQ_NUM is cleared to 000h.
- If (N - TX_REPLAY_FLIT_SEQ_NUM) mod 1023 < MAX_UNACKNOWLEDGED_FLITS:
- Set TX_REPLAY_FLIT_SEQ_NUM to 000h
- Set REPLAY_SCHEDULED to 0b
- If the received Flit was a Nak Flit:
- If N = NEXT_TX_FLIT_SEQ_NUM - 1:
- NAK_IGNORE_FLIT_SEQ_NUM is set to N.
- NAK_IGNORE_FLIT_SEQ_NUM is cleared to 000h if all of the following are true:
- A valid Nak Flit is received with Flit Sequence Number N.
- N != NAK_IGNORE_FLIT_SEQ_NUM
- N != NEXT_TX_FLIT_SEQ_NUM - 1
- It is recommended that NAK_IGNORE_FLIT_SEQ_NUM is cleared to 000h if all of the following are true:
- A valid Standard Nak Flit is received with Flit Sequence Number N.
- $\mathrm{N}==$ NAK_IGNORE_FLIT_SEQ_NUM
- REPLAY_SCHEDULED_TYPE is SELECTIVE_REPLAY
- TX_REPLAY_FLIT_SEQ_NUM $==\mathrm{N}+1$
- Schedule a replay as necessary, following the Flit Replay Scheduling rules in § Section 4.2.3.4.2.1.6 .
- The value of NAK_IGNORE_FLIT_SEQ_NUM must be updated before evaluating the rules in $\S$ Section 4.2.3.4.2.1.6.


# 4.2.3.4.2.1.5 Ack, Nak, and Discard Rules 

```
if (NON_IDLE_EXPLICIT_SEQ_NUM_FLIT_RCVD == 0b) {
    See Receiver Rules in IDLE Flit Handshake Phase
}
# Invalid Flit Handling
else if (Received Invalid Flit) {
```

```
    if (NAK_SCHEDULED == 1) {
        if (NAK_SCHEDULED_TYPE == STANDARD_NAK) {
            Flit Discard 1
        }
        else {
            Nak Schedule 6
        }
    }
    else {
        if (NAK_WITHDRAWAL_ALLOWED == 1) {
            Nak Schedule 1
        }
        else {
            Nak Schedule 0
        }
    }
}
# Valid Flit Handling
else if (Received Valid Flit) {
    if ((Explicit Sequence Number Flit) && (Flit Sequence Number == 0)) {
        Flit Discard 2
    }
    else if (NAK_WITHDRAWAL_ALLOWED == 1b) {
        NAK_WITHDRAWAL_ALLOWED = 0b;
        if (Prior Flit was Payload) {
            if (NOP Flit) {
                # Schedule a Standard or Selective Nak
                Discard Flit's TLP Bytes
                NAK_SCHEDULED = 1b;
                TX_ACXNAK_FLIT_SEQ_NUM = NEXT_EXPECTED_RX_FLIT_SEQ_NUM - 1;
                NAK_SCHEDULED_TYPE = STANDARD_NAK or SELECTIVE_NAK
                NEXT_EXPECTED_RX_FLIT_SEQ_NUM does not change;
                if (Scheduling a Selective Nak) {
                    NEXT_RX_FLIT_SEQ_NUM_TO_STORE = NEXT_EXPECTED_RX_FLIT_SEQ_NUM + 1
                }
            }
            # Current Flit is Payload Flit
            else {
                # Schedule a Standard Nak
                if (Scheduling a Standard Nak) {
                    standard_nak_procedure()
            }
            # Schedule a Selective Nak
            else {
                selective_nak_procedure()
            }
        }
    }
    # Prior Flit was NOP
    else {
        if (bad_sequence_number() || ((NOP Flit) && bad_nop_sequence_number())) {
                Nak Schedule 2
```

```
    }
    # Withdraw Nak
    else {
        if (((Payload Flit) && duplicate_sequence_number()) || (NOP Flit)) {
            # Schedule Ack for NEXT_EXPECTED_RX_FLIT_SEQ_NUM - 1
            TX_ACKNAK_FLIT_SEQ_NUM is set to NEXT_EXPECTED_RX_FLIT_SEQ_NUM - 1
            Discard Flit's TLP Bytes
        }
        if ((Payload Flit) && (NEXT_EXPECTED_RX_FLIT_SEQ_NUM ==
IMPLICIT_RX_FLIT_SEQ_NUM)) {
            # Schedule Ack for NEXT_EXPECTED_RX_FLIT_SEQ_NUM
            TX_ACKNAK_FLIT_SEQ_NUM is set to NEXT_EXPECTED_RX_FLIT_SEQ_NUM
            Increment NEXT_EXPECTED_RX_FLIT_SEQ_NUM
        }
    }
    }
}
# NAK_WITHDRAWAL_ALLOWED == 0b
else {
    if (NAK_SCHEDULED == 1b) {
        if (NAK_SCHEDULED_TYPE == Standard Nak) {
            if (NOP Flit) {
                if ((Explicit Sequence Number Flit) &&
                    (IMPLICIT_RX_FLIT_SEQ_NUM == (NEXT_EXPECTED_RX_FLIT_SEQ_NUM-1))) {
                    NAK_SCHEDULED = 0b
                    Discard Flit's TLP Bytes
            }
            else {
                Flit Discard 0
            }
        }
        # Payload Flit
        else {
            standard_nak_procedure()
        }
    }
    # Selective Nak
    else {
        if (NOP Flit) {
            Flit Discard 0
        }
        # Payload Flit
        else {
            selective_nak_procedure()
        }
    }
}
else {
    if (NOP Flit) {
        if (bad_nop_sequence_number())) {
                        Nak Schedule 2
        }
        else {
```

```
                Flit Discard 0
                }
            }
            # Payload Flit
            else {
                if (duplicate_sequence_number()) {
                    Flit Discard 0
            }
            else if (bad_sequence_number()) {
                Nak Schedule 2
            }
            else {
                # Forward Progress
                Ack Schedule 0
            }
        }
        }
    }
}
# Bad Sequence Number Check Logic
def bad_sequence_number() {
    return (NEXT_EXPECT_RX_FLIT_SEQ_NUM - IMPLICIT_RX_FLIT_SEQ_NUM) mod 1023 > 511
}
def bad_nop_sequence_number() {
    return bad_sequence_number() || (IMPLICIT_RX_FLIT_SEQ_NUM ==
NEXT_EXPECTED_RX_FLIT_SEQ_NUM)
}
# Duplicate Sequence Number Check Logic
def duplicate_sequence_number() {
    return ((TX_ACKNAK_FLIT_SEQ_NUM - IMPLICIT_RX_FLIT_SEQ_NUM) mod 1023 < 511)
}
# Ack/Nak/Discard Logic when scheduling a Standard Nak or when a Standard Nak is
outstanding.
def standard_nak_procedure() {
    if (duplicate_sequence_number()) {
        if (NAK_SCHEDULED == 1b) {
            Flit Discard 0
        }
        else {
            Nak Schedule 2
        }
    }
    else if ((Received Flit is Explicit Sequence Number Flit) &&
        (IMPLICIT_RX_FLIT_SEQ_NUM == NEXT_EXPECTED_RX_FLIT_SEQ_NUM)) {
        Ack Schedule 1
    }
    else {
        if (NAK_SCHEDULED == 1b) {
            Flit Discard 0
```

```
        }
        else {
            Nak Schedule 2
        }
    }
}
# Ack/Nak/Discard Logic when scheduling a Selective Nak or when a Selective Nak is
outstanding.
def selective_nak_procedure() {
    if (duplicate_sequence_number()) {
        Flit Discard 0
    }
    else if ((Received Flit is Explicit Sequence Number Flit) &&
        (IMPLICIT_RX_FLIT_SEQ_NUM == NEXT_EXPECTED_RX_FLIT_SEQ_NUM)) {
        if (RX_RETRY_BUFFER_OVERFLOW == 1) {
            Nak Schedule 5
        }
        else {
            Ack Schedule 2
        }
    }
    else if (((IMPLICIT_RX_FLIT_SEQ_NUM == NEXT_RX_FLIT_SEQ_NUM_TO_STORE)
                        && (NAK_SCHEDULED == 1))
            || ((IMPLICIT_RX_FLIT_SEQ_NUM == NEXT_EXPECTED_RX_FLIT_SEQ_NUM + 1)
                        && (NAK_SCHEDULED == 0))) {
            if (RX RETRY BUFFER FULL) {
                Nak Schedule 4
            }
            else {
                Nak Schedule 3
            }
    }
    else {
        # RX Retry Buffer Overflow
        if ((Received Flit is Valid) && (RX_RETRY_BUFFER_OVERFLOW == 1)) {
            Either Flit Discard 0 or NAK Schedule 2 \({ }^{71}\)
        }
        # Bad Sequence Number
        else {
            Nak Schedule 2
        }
    }
}
```


# Nak Schedule 0 

- The received Flit is discarded.
- NAK_WITHDRAWAL_ALLOWED is set to 1b.
- NEXT_EXPECTED_RX_FLIT_SEQ_NUM does not change.


## Nak Schedule 1

- The received Flit is discarded.

- NAK_SCHEDULED is set to 1b.
- TX_ACKNAK_FLIT_SEQ_NUM is set to NEXT_EXPECTED_RX_FLIT_SEQ_NUM - 1.
- NAK_SCHEDULED_TYPE is set to STANDARD_NAK.
- NAK_WITHDRAWAL_ALLOWED is cleared.
- NEXT_EXPECTED_RX_FLIT_SEQ_NUM does not change.


# Nak Schedule 2 

- The TLP Bytes of the received Flit are discarded.
- TX_ACKNAK_FLIT_SEQ_NUM is set to NEXT_EXPECTED_RX_FLIT_SEQ_NUM - 1.
- NAK_SCHEDULED is set to 1b.
- NAK_SCHEDULED_TYPE is set to STANDARD_NAK.
- RX_RETRY_BUFFER_LAST_FLIT_SEQ_NUM is set to 000h.
- NEXT_EXPECTED_RX_FLIT_SEQ_NUM does not change.


## Nak Schedule 3

- If NAK_SCHEDULED is 0b
- NAK_SCHEDULED is set to 1b.
- NAK_SCHEDULED_TYPE is set to SELECTIVE_NAK
- TX_ACKNAK_FLIT_SEQ_NUM is set to NEXT_EXPECTED_RX_FLIT_SEQ_NUM - 1.
- Store the Received Flit in the RX Retry Buffer.
- RX_RETRY_BUFFER_LAST_FLIT_SEQ_NUM is set to IMPLICIT_RX_FLIT_SEQ_NUM.
- NEXT_RX_FLIT_SEQ_NUM_TO_STORE is set to IMPLICIT_RX_FLIT_SEQ_NUM + 1.
- NEXT_EXPECTED_RX_FLIT_SEQ_NUM does not change.


## Nak Schedule 4

- The TLP Bytes of the received Flit that cannot be stored in the RX Retry Buffer are discarded.
- If the Receiver chooses to continue with the Selective Nak:
- RX_RETRY_BUFFER_OVERFLOW is set to 1b.
- RX_RETRY_BUFFER_LAST_FLIT_SEQ_NUM does not change.
- If the Receiver chooses to change the Selective Nak to a Standard Nak:
- NAK_SCHEDULED_TYPE is set to STANDARD_NAK.
- TX_ACKNAK_FLIT_SEQ_NUM is set to NEXT_EXPECTED_RX_FLIT_SEQ_NUM - 1.
- All Flits stored in the RX Retry Buffer are purged.
- RX_RETRY_BUFFER_LAST_FLIT_SEQ_NUM is set to 000h.
- NEXT_EXPECTED_RX_FLIT_SEQ_NUM does not change.


## Nak Schedule 5

- NAK_SCHEDULED remains 1b.
- NAK_SCHEDULED_TYPE is set to STANDARD_NAK.
- TX_ACKNAK_FLIT_SEQ_NUM is set to RX_RETRY_BUFFER_LAST_FLIT_SEQ_NUM.
- RX_RETRY_BUFFER_OVERFLOW is cleared.
- NEXT_EXPECTED_RX_FLIT_SEQ_NUM is set to RX_RETRY_BUFFER_LAST_FLIT_SEQ_NUM + 1.
- RX_RETRY_BUFFER_LAST_FLIT_SEQ_NUM is set to 000h.

# Nak Schedule 6 

- The received Flit is discarded.
- NAK_SCHEDULED remains 1b.
- NAK_SCHEDULED_TYPE is set to STANDARD_NAK.
- RX_RETRY_BUFFER_OVERFLOW is cleared.
- TX_ACKNAK_FLIT_SEQ_NUM is set to NEXT_EXPECTED_RX_FLIT_SEQ_NUM - 1.
- All Flits stored in the RX Retry Buffer are purged.
- RX_RETRY_BUFFER_LAST_FLIT_SEQ_NUM is set to 000h.


## Nak Schedule 7

- A Receiver is permitted to change a scheduled Selective Nak of TX_ACKNAK_FLIT_SEQ_NUM to a Standard Nak of TX_ACKNAK_FLIT_SEQ_NUM for any reason.


## Ack Schedule 0

- TX_ACKNAK_FLIT_SEQ_NUM is set to NEXT_EXPECTED_RX_FLIT_SEQ_NUM.
- NEXT_EXPECTED_RX_FLIT_SEQ_NUM is incremented.


## Ack Schedule 1

- NAK_SCHEDULED is cleared.
- TX_ACKNAK_FLIT_SEQ_NUM is set to IMPLICIT_RX_FLIT_SEQ_NUM.
- NEXT_EXPECTED_RX_FLIT_SEQ_NUM is set to IMPLICIT_RX_FLIT_SEQ_NUM + 1.


## Ack Schedule 2

- NAK_SCHEDULED is cleared.
- If RX Retry Buffer is empty:
- TX_ACKNAK_FLIT_SEQ_NUM is set to IMPLICIT_RX_FLIT_SEQ_NUM.
- NEXT_EXPECTED_RX_FLIT_SEQ_NUM is set to IMPLICIT_RX_FLIT_SEQ_NUM + 1.
- If RX Retry Buffer is NOT empty:
- TX_ACKNAK_FLIT_SEQ_NUM is set to RX_RETRY_BUFFER_LAST_FLIT_SEQ_NUM.
- NEXT_EXPECTED_RX_FLIT_SEQ_NUM is set to RX_RETRY_BUFFER_LAST_FLIT_SEQ_NUM + 1.
- RX_RETRY_BUFFER_LAST_FLIT_SEQ_NUM is set to 000h.


## Flit Discard 0

- The TLP Bytes of the received Flit are discarded.
- NEXT_EXPECTED_RX_FLIT_SEQ_NUM does not change.


## Flit Discard 1

- The received Flit is discarded.
- NEXT_EXPECTED_RX_FLIT_SEQ_NUM does not change.


## Flit Discard 2

- The received Flit is discarded.
- A Data Link Protocol Error is logged in the receiving Port (see § Section 6.2 ).
- NEXT_EXPECTED_RX_FLIT_SEQ_NUM does not change.

- NAK_WITHDRAWAL_ALLOWED is cleared.
![img-33.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-33.jpeg)

Figure 4-34 Flit Ack, Nak, and Discard Rules Flow Chart (Zoom-In to View)

# 4.2.3.4.2.1.6 Flit Replay Scheduling 

## Replay Schedule Rule 0

## Replay Timeout

- If all of the following are true:
- REPLAY_TIMEOUT_FLIT_COUNT $>=1500^{72}$
- REPLAY_SCHEDULED is 0b.
- REPLAY_IN_PROGRESS is 0b.
- Then:
- REPLAY_SCHEDULED is set to 1b.
- REPLAY_SCHEDULED_TYPE is set to STANDARD_REPLAY.
- TX_REPLAY_FLIT_SEQ_NUM is set to (ACKD_FLIT_SEQ_NUM + 1).

- CONSECUTIVE_TX_EXPLICIT_SEQ_NUM_FLITS is set to 0b. ${ }^{73}$
- CONSECUTIVE_TX_NAK_FLITS is set to 0b. ${ }^{74}$
- REPLAY_TIMEOUT_FLIT_COUNT is set to 0b.
- A Replay Timer Timeout error is logged in the Port (see § Section 6.2 ).


# Replay Schedule Rule 1 

Received Nak for Payload Flit.

- If all of the following are true:
- Received a valid Nak Flit with Flit Sequence Number N.
- A Payload Flit with Flit Sequence Number N + 1 is stored in the TX Retry Buffer.
- REPLAY_SCHEDULED is 0b.
- REPLAY_IN_PROGRESS is 0b.
- Either of the following are true:
- NAK_IGNORE_FLIT_SEQ_NUM I= N.
- The Nak Ignore Window has not been started or has elapsed.
- Then:
- REPLAY_SCHEDULED is set to 1b.
- TX_REPLAY_FLIT_SEQ_NUM is set to $\mathrm{N}+1$.
- NAK_IGNORE_FLIT_SEQ_NUM is set to N .
- If the received Flit is Standard Nak Flit:
- REPLAY_SCHEDULED_TYPE is set to STANDARD_REPLAY.
- If the received Flit is a Selective Nak Flit:
- REPLAY_SCHEDULED_TYPE is set to SELECTIVE_REPLAY.


## Replay Schedule Rule 2

Received Standard Nak after Selective Nak for Payload Flit.

- If all of the following are true:
- Received a valid Standard Nak Flit with Flit Sequence Number N.
- N+1 equals TX_REPLAY_FLIT_SEQ_NUM.
- REPLAY_SCHEDULED is 1b.
- REPLAY_IN_PROGRESS is 0b.
- REPLAY_SCHEDULED_TYPE is SELECTIVE_REPLAY.
- Then:
- REPLAY_SCHEDULED is set to 1b.
- TX_REPLAY_FLIT_SEQ_NUM does not change.
- REPLAY_SCHEDULED_TYPE is set to STANDARD_REPLAY.


### 4.2.3.4.2.1.7 Flit Replay Transmit Rules 5

## Flit Replay Transmit Rule 0

Standard Replay Scenario.

[^0]
[^0]:    73. CONSECUTIVE_TX_EXPLICIT_SEQ_NUM_FLITS is cleared to allow the Transmitter to begin replaying Flits right away and avoid overflowing the TX Retry Buffer sending NOP Flits while waiting to send another Explicit Sequence Number Flit to begin the replay.
    74. Same reason as clearing CONSECUTIVE_TX_EXPLICIT_SEQ_NUM_FLITS above.

- If all of the following conditions are true:
- REPLAY_SCHEDULED is 1b.
- REPLAY_IN_PROGRESS is 0b.
- REPLAY_SCHEDULED_TYPE is STANDARD_REPLAY.
- Either of the following are true:
- The transmitter is in the Sequence Number Handshake Phase.
- CONSECUTIVE_TX_NAK_FLITS is either 0 or greater than 2.
- Either of the following are true:
- Data rate is 64.0 GT/s and FLIT_REPLAY_NUM < 111b.
- Data rate <= 32.0 GT/s and FLIT_REPLAY_NUM < 110b.
- Then:
- The Transmitter must replay all unacknowledged Flits from the TX Retry Buffer beginning with the Flit containing Flit Sequence Number TX_REPLAY_FLIT_SEQ_NUM.
- If the data rate is $64.0 \mathrm{GT} / \mathrm{s}$ :
- FLIT_REPLAY_NUM is incremented by 1.
- If the data rate $<=32.0 \mathrm{GT} / \mathrm{s}$ :
- FLIT_REPLAY_NUM is incremented by $2^{75}$.
- REPLAY_IN_PROGRESS is set to 1b.
- REPLAY_SCHEDULED is set to 0b.


# Flit Replay Transmit Rule 1 

Selective Replay Scenario.

- If all of the following conditions are true:
- REPLAY_SCHEDULED is 1b.
- REPLAY_IN_PROGRESS is 0b.
- REPLAY_SCHEDULED_TYPE is SELECTIVE_REPLAY.
- Either of the following are true:
- The transmitter is in the Sequence Number Handshake Phase.
- CONSECUTIVE_TX_NAK_FLITS is either 0 or greater than 2.
- Either of the following are true:
- Data rate is 64.0 GT/s and FLIT_REPLAY_NUM < 111b.
- Data rate <= 32.0 GT/s and FLIT_REPLAY_NUM < 110b.
- Then:
- The Transmitter must replay the Flit from the TX Retry Buffer which contains the Flit Sequence Number that matches TX_REPLAY_FLIT_SEQ_NUM.
- If the data rate is $64.0 \mathrm{GT} / \mathrm{s}$ :
- FLIT_REPLAY_NUM is incremented by 1.
- If the data rate $<=32.0 \mathrm{GT} / \mathrm{s}$ :
- FLIT_REPLAY_NUM is incremented by $2 .{ }^{76}$
- REPLAY_IN_PROGRESS is set to 1b.

[^0]
[^0]:    75. Replays should happen less often at speeds lower than $64.0 \mathrm{GT} / \mathrm{s}$. We increment FLIT_REPLAY_NUM by 2 so that the Replay Rollover will happen after fewer Replays.
    76. Previous versions of this specification had this as increment by 1 . This remains permitted, although not optimal, behavior.

- REPLAY_SCHEDULED is set to 0b.


# Flit Replay Transmit Rule 2 

Replay Rollover Scenario.

- If all of the following conditions are true:
- REPLAY_SCHEDULED is 1b.
- REPLAY_IN_PROGRESS is 0b.
- Either of the following are true:
- Data rate is 64.0 GT/s and FLIT_REPLAY_NUM equals 111b.
- Data rate <= 32.0 GT/s and FLIT_REPLAY_NUM >= 110b.
- Then:
- If the data rate is $64.0 \mathrm{GT} / \mathrm{s}$ :
- FLIT_REPLAY_NUM is incremented by 1 (causing a rollover to 000b).
- If the data rate <= 32.0 GT/s:
- FLIT_REPLAY_NUM is incremented by 2 (causing a rollover to 000b or 001b).
- A REPLAY_NUM Rollover error is logged in the Port (see § Section 6.2 ).
- The Port must enter Recovery.

# IMPLEMENTATION NOTE: FLIT ACK/NAK/REPLAY EXAMPLE 5 

Consider two devices A and B connected through a Retimer, as shown in § Figure 4-35.

1. Both Device A and Device B are in the Normal Flit Exchange Phase
2. B receives valid Payload Flits 1 through 10 from A. B sends Acks for those Flits back to A. (Ack Schedule 0)
3. B receives an invalid NOP Flit $10^{77}$ and sets NAK_WITHDRAWAL_ALLOWED to 1b. (Nak Schedule 0)
4. B then receives a valid Flit 11 with Prior Flit was Payload set to 0b, indicating that prior Flit was a NOP Flit. B sends an Ack with Flit Sequence Number 11 to A.

- NAK_WITHDRAWAL_ALLOWED is cleared and a Nak is never sent for the invalid NOP Flit 10.

5. B then receives an invalid Payload Flit 12 and sends sets NAK_WITHDRAWAL_ALLOWED to 1b. (Nak Schedule 0)
6. B then receives a valid Flit 13 that indicates that Flit 12 was a Payload Flit, and sends a Selective Nak Flit with Flit Sequence Number 11, requesting A to Replay only Flit 12. (Nak Schedule 1)

- B will then send a minimum of three consecutive Selective Nak Flits with Flit Sequence Number 11.
- If B was sending Explicit Sequence Number Flits when the Nak of invalid Flit 12 was scheduled, it would have held off sending the Nak Flit until it had finished sending 3 consecutive Explicit Sequence Number Flits (Replay Command Rules in Normal Flit Exchange Phase).
- The choice of a Selective Nak by B is an optimization in this case. B has enough space in its RX Retry Buffer to store the subsequent Flits.
- If B were to receive an invalid Flit with a Selective Nak outstanding, it would be required to change the outstanding Selective Nak to a Standard Nak. (Nak Schedule 6)
- B is also permitted to change the outstanding Selective Nak to a Standard Nak for any implementation specific reason. (Nak Schedule 7)

7. After B sends 3 consecutive Nak Flits with Flit Sequence Number 11, B will continue following the Replay Command Rules in Normal Flit Exchange Phase to determine whether to send Nak Flits or Explicit Sequence Number Flits.
8. In the time it took for $A$ to receive the Selective Nak of Flit 12 and schedule a Replay of Flit 12, valid Payload Flits 13 and 14 and NOP Flit 14 were received by B. B stores Payload Flits 13 and 14 in its RX Retry Buffer. The TLP Bytes of NOP Flit 14 are discarded and the Flit is not stored in the RX Retry Buffer (Flit Discard 0).
9. B then receives replayed Flit 12 from A and processes Flit 12 as well as Payload Flits 13 and 14 that were stored in the B's RX Retry Buffer.

- Note that Payload Flits 12 and 15 and NOP Flit 15 are all sent with explicit Flit Sequence Numbers in adherence to the Replay Command Rules in Normal Flit Exchange Phase

10. Next, B receives valid Payload Flit 15, and then invalid NOP Flit 15. B sets NAK_WITHDRAWAL_ALLOWED to 1b.
11. B then receives invalid Flit 16, and since there's no way for B to know that the previous invalid Flit was a NOP Flit, the Nak can't be withdrawn and B sends a Standard Nak with Flit Sequence Number 15.

- Note that B cannot send a Selective Nak since two consecutive invalid Flits were received.

12. B then receives valid Payload Flits 17 and 18, but since B has a Standard Nak outstanding, the TLP Bytes of these Flits are discarded (Flit Discard 0).
13. A then replays all unacknowledged Flits from its TX Retry Buffer (Flits 16, 17, and 18), which B receives as valid Flits and Acks accordingly.
![img-34.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-34.jpeg)

Figure 4-35 Flit Ack/Nak/Replay Example 5

# IMPLEMENTATION NOTE: TRANSMITTER THROTTLING AFTER SELECTIVE REPLAY 

In some situations, it will reduce link latency if the transmitter throttles its Flit transmission rate after sending a Selective Replay Flit.

When the Receiver issues a Selective Nak and is waiting for the selective replay, it stores valid Payload Flits in an RX retry buffer and processes these Flits after the selective replay is received. Payload Flits that arrive after the selective replay must also be stored in the RX retry buffer. All Payload Flits are processed in sequence number order.

Without transmitter throttling, this RX retry buffer adds latency to the receive path since all the entries must be consumed in order. Latency can be reduced and this performance impact can be mitigated if the transmitter throttles Flit transmission earlier allowing the RX retry buffer to drain. This early transmitter throttling does not affect overall performance - the TLPs that get delayed at the transmitter would have been delayed at the Receiver. Performing early throttling at the transmitter allows the RX retry buffer to drain so that subsequent TLPs have reduced latency.

Throttling is only needed when the Link is operating at the drain rate of the Receiver. If the Link is operating at a reduced width (e.g., due to L0p), throttling may not be needed as the RX retry buffer drain rate may be faster than the Link rate.

To compute how to throttle, the Transmitter can assume that the initial link width is the drain rate of the Receiver. On receiving a selective Nak, the Transmitter can compute the number of Payload Flits in the Receiver's RX retry buffer (or on the way to that buffer) since it knows how many Payload Flits are currently in its TX retry buffer. The transmitter should throttle and/or enforce a certain bandwidth efficiency (i.e., restrict the number of NOP TLPs in a Payload Flit) in each new Payload Flit it transmits from its Transaction Layer to allow the Receiver's RX retry buffer to drain.

For example, suppose a x8 Link receives a selective Nak for Flit number $X$ and the Transmitter has sent 4 Payload Flits after it initially sent Flit number $X$. In this case, the transmitter should throttle its upper layers to create a 4 Flit "bubble". For a x8 Link, Flits are 16 Symbols and SKP Ordered Sets are 32 Symbols so this "bubble" is either 4 NOP Flits, 2 NOP Flits and 1 SKP Ordered Set, or 2 SKP Ordered Sets. One mechanism to implement the throttling is for the transmitter to enforce $<Y \%$ NOP TLPs (e.g., $Y=25$ ) in its Payload Flits until it has sent the "bubble" (if TLPs are constantly being transmitted this could take 2 SKP Ordered Sets).

### 4.2.3.4.2.2 NOP Flit Payload

### 4.2.3.4.2.2.1 NOP.Empty Flit

A NOP.Empty Flit has an empty NOP Flit Payload with all bytes set to 00h (see § Figure 4-36).

![img-35.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-35.jpeg)

Figure 4-36 NOP.Empty Flit Payload

# 4.2.3.4.2.2.2 NOP.Debug Flit 

NOP.Debug Flits contain a list of zero or more Debug Chunks. The first Debug Chunk starts at Byte 4 of the Flit (immediately after the NOP Flit Common Header, see § Figure 4-33).

A Debug Chunk consists of a variable-sized Debug Header followed by a vendor-defined variable-sized Debug Payload (see § Figure 4-37).
![img-36.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-36.jpeg)

Figure 4-37 NOP.Debug Flit Debug Chunk

Table 4-22 NOP.Debug Flit Debug Chunk Fields

| Field | Location | Definition |
| :--: | :--: | :--: |
| Debug <br> Chunk <br> Opcode | Byte 0: Bits 7:1 | Debug opcode encoding defined by vendor that describes the debug content. |
| Debug <br> Chunk <br> Continuation <br> (C) | Byte 0: Bit 0 | Indication this Debug Chunk is a continuation from the previous Debug Chunk. <br> This is only valid for the first Debug Chunk of a Flit and must be Reserved otherwise. <br> Continuation chunks must have the same Debug Chunk Opcode and Debug Chunk Vendor ID as the previous chunk. |
| Debug <br> Chunk | Byte 1: Bits 7:2 | Length of the Debug Chunk Payload of the current Debug Chunk in DW. The length cannot exceed the remaining number of DW in the 236 Byte TLP Bytes of the Flit. The maximum Length |

| Field | Location | Definition |
| :--: | :--: | :--: |
| Payload <br> Length |  | value is 57 (1 DW NOP Flit Common Header +1 DW Debug Header +57 DW Debug Chunk Payload $=236$ Bytes of NOP Flit Payload). A Length value of 0 indicates this Debug Chunk only contains a Debug Header. |
| Debug <br> Chunk <br> Header Size <br> (S) | Byte 1: Bits 1:0 | Total size of the Debug Chunk Header in DW. Any additional bits beyond the first DW of the Debug Chunk Header are Reserved. |
|  |  | 00b <br> 01b <br> 10b <br> 11b <br> 12b <br> 11b <br> 12b <br> Receivers that support NOP. Debug Flits must handle all valid Debug Chunk Header Sizes. |  |
| Debug <br> Chunk <br> Vendor ID | \{Byte 2: Bits 7:0, Byte 3: Bits 7:0 \} | Vendor ID associated with the vendor that defined the Debug Opcode <br> For PCI-SIG defined Debug Opcodes, this field must use the PCI-SIG Vendor ID (0001h) |

![img-37.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-37.jpeg)

Figure 4-38 Example Debug Chunk with one DW Debug Chunk Heaader and one DW of Debug Chunk Payload
![img-38.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-38.jpeg)

Figure 4-39 Example Debug Chunk with two DW Debug Chunk Heaader and one DW of Debug Chunk Payload

![img-39.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-39.jpeg)

Figure 4-40 Example Debug Chunk with four DW Debug Chunk Heaader and one DW of Debug Chunk Payload 5

A NOP. Debug Flit uses one or more Debug Chunks to deliver vendor-defined link debug information. § Figure 4-41 shows a NOP. Debug Flit with a single Debug Chunk.
![img-40.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-40.jpeg)

Figure 4-41 Example NOP. Debug Flit Payload with a single Debug Chunk with a one DW Debug Chunk Header 6

If multiple Debug Chunks are inserted into a Flit, subsequent Debug Chunk Headers must begin immediately on the first available DW slot and set the Debug Chunk Continuation bit to 0b. It is permissible for Debug Chunks with different Debug Chunk Vendor ID values to be inserted into a single Flit. § Figure 4-42 shows a NOP. Debug Flit with multiple Debug Chunks.

![img-41.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-41.jpeg)

Figure 4-42 Example NOP.Debug Flit Payload with multiple Debug Chunks with one DW Debug Chunk Headers

Any unused DW slots at the end of the NOP Flit Payload of a NOP.Debug Flit must be filled with Empty Debug Chunks or set to 0 .

# 4.2.3.4.2.2.2.1 PCI-SIG Defined Debug Chunk Opcode Values 

Table 4-23 PCI-SIG Defined Debug Chunk Opcode Values

| Debug Chunk <br> Opcode Value | Name | Description |
| :--: | :--: | :--: |
| 0000000 b | Empty Debug Chunk | Padding and alignment, contains no valid debug information. See <br> \$ Section 4.2.3.4.2.2.2.2 |
| 0000001 b | Start Capture Trigger Debug Chunk | Generic indication to start trace capture |
| 0000010 b | Stop Capture Trigger Debug Chunk | Generic indication to stop trace capture |
| 0000011 b | FC Information Tracked by Transmitter <br> Debug Chunk | Flow Control information tracked by TX for TLP Transmission gating |
| 0000100 b | FC Information Tracked by Receiver <br> Debug Chunk | Flow Control information tracked by RX for TLP Receiver accounting |
| 0000101 b | Flit Mode Transmitter Retry Flags and <br> Counters Debug Chunk | Transmitter Flag and Counter values used for Flit Sequence Number <br> and retry mechanism in Flit Mode |
| 0000110 b | Flit Mode Receiver Retry Flags and <br> Counters Debug Chunk | Receiver Flag and Counter values used for Flit Sequence Number <br> and retry mechanism in Flit Mode |
| 0000111 b | Buffer Occupancy Debug Chunk | Current Occupancy of the reported structure |
| 0001000 b | Link Debug Request Debug Chunk | Request for link partner to return a NOP.Debug Flit with a specified <br> Debug Chunk Opcode |
| Others |  | All other encodings are Reserved |

# 4.2.3.4.2.2.2.2 Empty Debug Chunk 

The Empty Debug Chunk is used for padding and alignment. This Debug Chunk does not contain any meaningful debug information and the Debug Chunk Payload (if present) must be ignored by receivers.

The Debug Chunk Continuation bit must be 0 . The Debug Chunk Header Size field must be 00b. Receivers must treat any Flit containing Empty Debug Chunks, where these values are not as stated, as a NOP.Empty Flit.

## IMPLEMENTATION NOTE: <br> EMPTY DEBUG CHUNK RECOMMENDATIONS

To reduce parsing effort at the NOP.Debug receiver, it is recommended that consecutive Empty Debug Chunks be avoided. It is more efficient to use a single, larger, Empty Debug Chunk.

There is no constraint on the position of Empty Debug Chunks within a NOP.Debug Flit. Specifically, it is permitted to have an Empty Debug Chunk followed by a non-Empty Debug Chunk.
![img-42.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-42.jpeg)

Figure 4-43 Empty Debug Chunk

### 4.2.3.4.2.2.2.3 Start Capture Trigger Debug Chunk

The Start Capture Trigger Debug Chunk is used to indicate to debug tools such as Logic Analyzers to start capturing what follows the NOP.Debug Flit on the Link.

No Debug Chunk Payload is required for this Debug Chunk, but a transmitter may choose to insert implementation specific content. The Debug Chunk Continuation bit must be 0 . Receivers are permitted to silently drop any Start Capture Trigger Debug Chunk, where this value is not as stated.

For ease of use by debug tools, this Debug Chunk is only permitted as the first Debug Chunk of a NOP.Debug Flit.

![img-43.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-43.jpeg)

Figure 4-44 Start Capture Trigger Debug Chunk

# 4.2.3.4.2.2.2.4 Stop Capture Trigger Debug Chunk 

The Stop Capture Trigger Debug Chunk is used to indicate to debug tools such as Logic Analyzers to stop capturing what follows the NOP. Debug Flit on the Link.

No Debug Chunk Payload is required for this Debug Chunk but a transmitter may choose to insert implementation specific content. The Continuation bit must be 0 . Receivers are permitted to silently drop any Stop Capture Trigger Debug Chunk, where this value is not as stated.

For ease of use by debug tools, this Debug Chunk is only permitted as the first Debug Chunk of a NOP.Debug Flit.
![img-44.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-44.jpeg)

Figure 4-45 Stop Capture Trigger Debug Chunk

### 4.2.3.4.2.2.2.5 FC Information Tracked by Transmitter Debug Chunk

The FC Information Tracked by Transmitter Debug Chunk transmits the information tracked by a Transmitter for Flow Control TLP Transmission gating.

After the Debug Header, each DW of Debug Chunk Payload consists of a FC Quantity field to indicate the FC quantity information being sent in the remainder of the DW, which contains VC and Header/Data credit values. The Port must only transmit FC quantity information for VCs that it supports.
§ Figure 4-46 displays a Debug Chunk with multiple FC quantities inserted. See § Table 4-24 for the FC Quantity field encodings. The VC field contains the VC number, the Hdr FC field contains the Header credits for the FC Quantity for that VC, and the Data FC field contains the Data credits for the FC Quantity for the VC.

![img-45.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-45.jpeg)

Figure 4-46 FC Information Tracked by Transmitter Debug Chunk 9

Table 4-24 FC Information Tracked by Transmitter Encodings 9

| FC Quantity | Encoding | FC Quantity |
| :--: | :--: | :--: |
| 00000 b | No valid info |  |
| 00001 b | Credit_Consumed_P |  |
| 00010 b | Credit_Consumed_NP |  |
| 00011 b | Credit_Consumed_CPL |  |
| 00100 b | Shared_Credit_Consumed_P |  |
| 00101 b | Shared_Credit_Consumed_NP |  |
| 00110 b | Shared_Credit_Consumed_CPL |  |
| 00111 b | Shared_Credit_Consumed_Currently_P |  |
| 01000 b | Shared_Credit_Consumed_Currently_NP |  |
| 01001 b | Shared_Credit_Consumed_Currently_CPL |  |
| 01010 b | Credit_Limit_P |  |
| 01011 b | Credit_Limit_NP |  |
| 01100 b | Credit_Limit_CPL |  |
| 01101 b | Shared_Credit_Limit_P |  |
| 01110 b | Shared_Credit_Limit_NP |  |
| 01111 b | Shared_Credit_Limit_CPL |  |
| 10000 b | Sum_Shared_Credit_Consumed_P |  |
| 10001 b | Sum_Shared_Credit_Consumed_NP |  |

| FC Quantity Encoding | FC Quantity |
| :--: | :-- |
| 10010 b | Sum_Shared_Credit_Consumed_CPL |
| 10011 b | Total_Shared_Credit_Available_P |
| 10100 b | Total_Shared_Credit_Available_NP |
| 10101 b | Total_Shared_Credit_Available_CPL |
| 10110 b | Sum_Shared_Credit_Limit_P |
| 10111 b | Sum_Shared_Credit_Limit_NP |
| 11000 b | Sum_Shared_Credit_Limit_CPL |
| 11001 b | SHARED_CUMULATIVE_CREDITS_REQUIRED_P |
| 11010 b | SHARED_CUMULATIVE_CREDITS_REQUIRED_NP |
| 11011 b | SHARED_CUMULATIVE_CREDITS_REQUIRED_CPL |
| 11100 b | CUMULATIVE_CREDITS_REQUIRED_P |
| 11101 b | CUMULATIVE_CREDITS_REQUIRED_NP |
| 11110 b | CUMULATIVE_CREDITS_REQUIRED_CPL |
| 11111 b | Reserved |

# 4.2.3.4.2.2.2.6 FC Information Tracked by Receiver Debug Chunk 

The FC Information Tracked by Receiver Debug Chunk transmits the information tracked by a Receiver for Flow Control TLP Receiver accounting.

After the Debug Chunk Header, each DW of Debug Chunk Payload consists of a FC Quantity field to indicate the FC quantity information being sent in the remainder of the DW, which contains VC and Header/Data credit values. The Port must only transmit FC quantity information for VCs that it supports.
§ Figure 4-47 displays a Debug Chunk with multiple FC quantities inserted. See § Table 4-25 for the FC Quantity field encodings. The VC field contains the VC number, the Hdr_FC field contains the Header credits for the FC Quantity for that VC, and the Data_FC field contains the Data credits for the FC Quantity for the VC.

![img-46.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-46.jpeg)

Figure 4-47 FC Information Tracked by Reciever Debug Chunk

Table 4-25 FC Information Tracked by Receiver
Encodings

| FC Quantity Encoding | FC Quantity |
| :--: | :-- |
| 00000 b | No valid info |
| 00001 b | Credits_Allocated_P |
| 00010 b | Credits_Allocated_NP |
| 00011 b | Credits_Allocated_CPL |
| 00100 b | Shared_Credits_Allocated_P |
| 00101 b | Shared_Credits_Allocated_NP |
| 00110 b | Shared_Credits_Allocated_CPL |
| 00111 b | Credits_Received_P |
| 01000 b | Credits_Received_NP |
| 01001 b | Credits_Received_CPL |
| 01010 b | Shared_Credits_Received_P |
| 01011 b | Shared_Credits_Received_NP |
| 01100 b | Shared_Credits_Received_CPL |
| Others | All other encodings are Reserved |

# 4.2.3.4.2.2.2.7 Flit Mode Transmitter Retry Flags and Counters Debug Chunk 

The Flit Mode Transmitter Retry Flags and Counters Debug Chunk transmits the transmitter flag and counter values for Flit Sequence Number and retry tracking for Flit Mode.

The Length field must be 2 h . Receivers are permitted to silently drop any Flit Mode Transmitter Retry Flags and Counters Debug Chunk, where this value is not as stated.

See § Figure 4-48 for the layout of this Debug Chunk. See § Table 4-26 and § Section 4.2.3.4.2.1 for a description of the fields within this Debug Chunk Payload.
![img-47.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-47.jpeg)

Figure 4-48 Flit Mode Transmitter Retry Flags and Counters Debug Chunk

Table 4-26 Flit Mode Transmitter Retry Flags and Counters Fields

| Field | Location |
| :--: | :--: |
| Reserved | Byte 4: Bit 7 |
| FLIT_REPLAY_NUM (FRN) | Byte 4: Bits 6:4 |
| REPLAY_IN_PROGRESS (RP) | Byte 4: Bit 3 |
| REPLAY_SCHEDULED_TYPE (RT) | Byte 4: Bit 2 |
| REPLAY_SCHEDULED (RS) | Byte 4: Bit 1 |
| CONSECUTIVE_TX_NAK_FLITS (CN) | \{Byte 4: Bit 0, Byte 5: Bits 7:6 \} |
| CONSECUTIVE_TX_EXPLICIT_SEQ_NUM_FLITS (CE) | Byte 5: Bits 5:4 |
| TX_ACKNAK_FLIT_SEQ_NUM | \{Byte 5: Bits 3:0, Byte 6: Bits 7:2 \} |
| NEXT_TX_FLIT_SEQ_NUM | \{Byte 6: Bits 1:0, Byte 7: Bits 7:0 \} |
| NAK_SCHEDULED_TYPE (NT) | Byte 8: Bit 7 |
| NAK_SCHEDULED (NS) | Byte 8: Bit 6 |
| MAX_UNACKNOWLEDGED_FLITS | \{Byte 8: Bits 5:0, Byte 9: Bits 7:5 \} |
| REPLAY_TIMEOUT_FLIT_COUNT | \{Byte 9: Bits 4:0, Byte 10: Bits 7:2 \} |
| TX_REPLAY_FLIT_SEQ_NUM | \{Byte 10: Bits 1:0, Byte 11: Bits 7:0 \} |

# 4.2.3.4.2.2.2.8 Flit Mode Receiver Retry Flags and Counters Debug Chunk 

The Flit Mode Receiver Retry Flags and Counters Debug Chunk transmits the receiver flag and counter values for Flit Sequence Number and retry tracking for Flit Mode.

The Length field must be 2 h . Receivers are permitted to silently drop any Flit Mode Receiver Retry Flags and Counters Debug Chunk, where this value is not as stated.
§ Figure 4-49 shows the layout of this Debug Chunk. See § Table 4-27 and § Section 4.2.3.4.2.1 for a description of the fields within the Debug Chunk Payload.
![img-48.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-48.jpeg)

Figure 4-49 Flit Mode Receiver Retry Flags and Counters Debug Chunk

Table 4-27 Flit Mode Receiver Retry Flags and Counters Fields

| Field | Location |
| :-- | :-- |
| Reserved | Byte 4: Bit 7 |
| NON_IDLE_EXPLICIT_SEQ_NUM_FLIT_RCVD (NI) | Byte 4: Bit 6 |
| ACKD_FLIT_SEQ_NUM | \{Byte 4: Bits 5:0, Byte 5: Bits 7:4 \} |
| IMPLICIT_RX_FLIT_SEQ_NUM | \{Byte 5: Bits 3:0, Byte 6: Bits 7:2 \} |
| NEXT_EXPECTED_RX_FLIT_SEQ_NUM | \{Byte 6: Bits 1:0, Byte 7: Bits 7:0 \} |
| RX_RETRY_BUFFER_OVERFLOW (BO) | Byte 8: Bit 7 |
| NAK_WITHDRAWAL_ALLOWED (WA) | Byte 8: Bit 6 |
| RX_RETRY_BUFFER_LAST_FLIT_SEQ_NUM | \{Byte 8: Bits 5:0, Byte 9: Bits 7:4 \} |
| NEXT_RX_FLIT_SEQ_NUM_TO_STORE | \{Byte 9: Bits 3:0, Byte 10: Bits 7:2 \} |
| NAK_IGNORE_FLIT_SEQ_NUM | \{Byte 10: Bits 1:0, Byte 11: Bits 7:0 \} |

# 4.2.3.4.2.2.2.9 Buffer Occupancy Debug Chunk 

The Buffer Occupancy Debug Chunk transmits the current occupancy of the reported structure.
After the Debug Chunk Header, each DW of Debug chunk Payload consists of a Buffer ID field to indicate the buffer structure being sent in the remainder of the DW, which contains Number of Occupied Entries values. § Figure 4-50 shows a Buffer Occupancy Debug Chunk with multiple buffers being reported. See § Table 4-28 for the Buffer ID field encodings. The Number of Occupied Entries field contains the current occupancy value for the Buffer ID.

![img-49.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-49.jpeg)

Figure 4-50 Buffer Occupancy Debug Chunk

Table 4-28 Buffer Occupancy Encodings

| Buffer ID Encoding | Buffer ID |
| :--: | :-- |
| 0h | TX Retry Buffer |
| 1h | RX Retry Buffer |
| Others | All other encodings are Reserved |

# 4.2.3.4.2.2.2.10 Link Debug Request Debug Chunk 

The Link Debug Request Debug Chunk requests the Receiver to return a NOP.Debug Flit with the requested Debug Chunk Opcode.
\$ Figure 4-51 shows the layout of the Link Debug Request Debug Chunk. After the Debug Chunk Header, a single DW of Debug Chunk Payload contains the Requested Debug Chunk Opcode and Requested Debug Chunk Vendor ID.

For ease of use by the Receiver, this Debug Chunk is only permitted as the first chunk of the NOP.Debug Flit. Receiver responds on a best effort basis, and is permitted to ignore the request if it cannot service it.

| Byte $0 \rightarrow$ |  | $+0$ |  | $+1$ |  | $+2$ |  | $+3$ |  |
| :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: |
|  | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
| Byte $4 \rightarrow$ | Link Debug Request | C |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | 8 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

# 4.2.3.4.2.2.3 NOP.Vendor Flit 

A NOP.Vendor Flit (see § Figure 4-52) is a general purpose type that can be utilized by a vendor to transmit proprietary information. After the NOP Flit Common Header, the next DW contains a Vendor ID field that identifies the vendor associated with this Flit, and all other bytes in the Flit are available for vendor usage. It is recommended for vendors to include a sub-type field.
![img-50.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-50.jpeg)

Figure 4-52 NOP.Vendor Flit Payload

### 4.2.3.4.2.3 CRC Bytes in Flit

The CRC generator polynomial, defined over GF $\left(2^{8}\right)$, is $g(x)=(x+\alpha)\left(x+\alpha^{2}\right) \ldots\left(x+\alpha^{8}\right)$, where $\alpha$ is the root of the primitive polynomial of degree 8: $x^{8}+x^{5}+x^{3}+x+1$. Thus, $g(x)=x^{8}+a^{172} x^{7}+a^{116} x^{6}+a^{186} x^{5}+a^{172} x^{4}+a^{195} x^{3}+a^{134} x^{2}+a^{199} x+a^{36}$. § Figure 4-53 demonstrates how CRC bytes are generated for the Transmit as well as Receive side. On the Receive side the generated CRC bytes are compared against the received CRC bytes (after the FEC decode/ correct) and any mismatch represents an uncorrectable error.
![img-51.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-51.jpeg)
$x^{8} \cdot a(x)$

| (x) | GF(2 ${ }^{8}$ ) multiplication ( $x$ ) GF(2 ${ }^{8}$ ) addition $\quad B_{0} \cdot B_{7}:$ CRC Bytes |
| :--: | :--: |
| $a(x)$ : Information Bytes as a polynomial over GF(2 ${ }^{8}$ ) | (Legend) |

Bytes 0-241 form the input $a(x)$ whereas B0-B7 represent CRC0-crc7
Figure 4-53 CRC generation/ checking in Flit

The CRC generator using MATLAB code to output the generator matrix, the generator matrix, as well as the RTL code is provided in § Appendix K. . The CRC bytes are generated by 242 Bytes of Data * Gen Matrix. Thus, Data is 1x1936 bits, Gen

matrix is 1936x64 bits. Data is arranged from MSB to LSB - [(241,7), (241,6), (241,5), (241,4) .......... (0,7), $(0,6),(0,5),(0,4),(0,3),(0,2),(0,1),(0,0))$ where $(x, y)$ is $y$ th bit of $x$ th byte. The generator matrix appears in § Appendix K. and must be considered the standard to implement the CRC during encode and decode. Any pipelined implementation must match this mechanism. The code is provided for the Transmit side. It takes 242 Bytes as input and generates the 8B of CRC. On the Receive side, after the ECC decode/ correction, the first 242 Bytes of the Flit will be used to generate the expected 8 Bytes of CRC and each of these 8 Bytes will be compared against the received 8B of CRC. Any mismatch results in the Flit being declared not Valid and a replay requested, if needed, as described earlier.

# 4.2.3.4.2.4 ECC Bytes in Flit 

The FEC code is a 3-way interleaved, as described before, where the ECC Symbols are defined over GF( $\left.2^{8}\right)$. Thus, three consecutive Bytes in a wire belong to three different ECC groups, as shown by different colors in § Table 4-10 through § Table 4-14. Thus, any burst of length $\leq 16$ in a wire is guaranteed not to impact more than one Symbol in a code word which is capable of correcting single byte errors in an effort to minimize the FEC latency.

A sample RTL code for the FEC is provided in § Appendix J. . The rest of this section describes the construction of the FEC code. The sample RTL in the appendix is the reference should any confusion arise out of the description here. While an implementation may follow a different approach (e.g., pipelining), it must still match the RTL sample results for all permutations of values in the bytes both for the encoder as well as the decoder function.

Let $\alpha$ be the root of a primitive polynomial $x^{8}+x^{4}+x^{3}+x^{2}+1$ (represented as $0 x 1 D$ ). Hence, $\alpha^{8}=\alpha^{4}+\alpha^{3}+\alpha^{2}+1$ which can also be represented as (0001_1101). Thus, each 8 -bit symbol (over GF( $\left.2^{8}\right)$ ) can be expressed as a polynomial as powers of alpha ( 1 through 254 ) or as a degree 8 polynomial. We calculate powers of $\alpha$ along with an 8 -bit representation as follows: Should be: $\alpha^{0}(=1):(0000 \_0001), \alpha^{1}:(0000 \_0010), \ldots, \alpha^{7}:(1000 \_0000), \alpha^{8}:(0001 \_1101), \ldots \alpha^{255}=1$. Thus, we get 255 distinct numbers as powers of $\alpha$ (all 0 s is not a power of $\alpha$ ), as shown in $\S$ Figure 4-54. The log function is given in § Figure 4-55 (which is basically the inverse of constructing the power of $\alpha$ from a given 8 -bit non-zero Syndrome which will be used for error correction). The H matrix consists of two parts: Horizontal Parity and Check bits, as shown in § Figure 4-56 and § Figure 4-57. The Horizontal Parity is the bit-wise XORs of Symbols (see § Equation 4-1). The Check bits (see § Equation 4-2) is similar to a CRC calculation represented as follows:
$P=\sum_{i=0}^{83} B_{i}$
Equation 4-1 Parity bytes
$C=\sum_{i=0}^{83} B_{i} \times \alpha^{(84-i)}$

```
\(\alpha\) is the root of the primitive polynomial \(x^{8}+x^{4}+x^{3}+x^{2}+1\)
\(i \rightarrow a^{i}\) (in hex)
00: 01 01: 02 02: 04 03: 08 04: 10 05: 20 06: 40 07: 80
08: 1d 09: 3a 0a: 74 0b: e8 0c: cd 0d: 87 0e: 13 0f: 26
10: 4c 11: 98 12: 2d 13: 5a 14: b4 15: 75 16: ea 17: c9
18: 8f 19: 03 1a: 06 1b: 0c 1c: 18 1d: 30 1e: 60 1f: c0
20: 9d 21: 27 22: 4e 23: 9c 24: 25 25: 4a 26: 94 27: 35
28: 6a 29: d4 2a: b5 2b: 77 2c: ee 2d: c1 2e: 9f 2f: 23
30: 46 31: 8c 32: 05 33: 0a 34: 14 35: 28 36: 50 37: a0
38: 5d 39: ba 3a: 69 3b: d2 3c: b9 3d: 6f 3e: de 3f: a1
40: 5f 41: be 42: 61 43: c2 44: 99 45: 2f 46: 5e 47: bc
48: 65 49: ca 4a: 89 4b: 0f 4c: 1e 4d: 3c 4e: 78 4f: f0
50: fd 51: e7 52: d3 53: bb 54: 6b 55: d6 56: b1 57: 7f
58: fe 59: e1 5a: df 5b: a3 5c: 5b 5d: b6 5e: 71 5f: e2
60: d9 61: af 62: 43 63: 86 64: 11 65: 22 66: 44 67: 88
68: 0d 69: 1a 6a: 34 6b: 68 6c: d0 6d: bd 6e: 67 6f: ce
70: 81 71: 1f 72: 3e 73: 7c 74: f8 75: ed 76: c7 77: 93
78: 3b 79: 76 7a: ec 7b: c5 7c: 97 7d: 33 7e: 66 7f: cc
80: 85 81: 17 82: 2e 83: 5c 84: b8 85: 6d 86: da 87: a9
88: 4f 89: 9e 8a: 21 8b: 42 8c: 84 8d: 15 8e: 2a 8f: 54
90: a8 91: 4d 92: 9a 93: 29 94: 52 95: a4 96: 55 97: aa
98: 49 99: 92 9a: 39 9b: 72 9c: e4 9d: d5 9e: b7 9f: 73
a0: e6 a1: d1 a2: bf a3: 63 a4: c6 a5: 91 a6: 3f a7: 7e
a8: fc a9: e5 aa: d7 ab: b3 ac: 7b ad: f6 ae: f1 af: ff
b0: e3 b1: db b2: ab b3: 4b b4: 96 b5: 31 b6: 62 b7: c4
b8: 95 b9: 37 ba: 6e bb: dc bc: a5 bd: 57 be: ae bf: 41
c0: 82 c1: 19 c2: 32 c3: 64 c4: c8 c5: 8d c6: 07 c7: 0e
c8: 1c c9: 38 ca: 70 cb: e0 cc: dd cd: a7 ce: 53 cf: a6
d0: 51 d1: a2 d2: 59 d3: b2 d4: 79 d5: f2 d6: f9 d7: ef
d8: c3 d9: 9b da: 2b db: 56 dc: ac dd: 45 de: 8a df: 09
e0: 12 e1: 24 e2: 48 e3: 90 e4: 3d e5: 7a e6: f4 e7: f5
e8: f7 e9: f3 ea: fb eb: eb ec: cb ed: 8b ee: 0b ef: 16
f0: 2c f1: 58 f2: b0 f3: 7d f4: fa f5: e9 f6: cf f7: 83
f8: 1b f9: 36 fa: 6c fb: d8 fc: ad fd: 47 fe: 8e ff: 01
```

Figure 4-54 FEC Table: i to $a^{i}{ }^{i}$

a is the root of the primitive polynomial $x^{8}+x^{4}+x^{3}+x^{2}+1$

$$
a^{i} \rightarrow i(\text { in hex) }
$$

00: ff 01: 00 02: 01 03: 19 04: 02 05: 32 06: 1a 07: c6 08: 03 09: df 0a: 33 0b: ee 0c: 1b 0d: 68 0e: c7 0f: 4b 10: 04 11: 64 12: e0 13: 0e 14: 34 15: 8d 16: ef 17: 81 18: 1c 19: c1 1a: 69 1b: f8 1c: c8 1d: 08 1e: 4c 1f: 71 20: 05 21: 8a 22: 65 23: 2f 24: e1 25: 24 26: 0f 27: 21 28: 35 29: 93 2a: 8e 2b: da 2c: f0 2d: 12 2e: 82 2f: 45 30: 1d 31: b5 32: c2 33: 7d 34: 6a 35: 27 36: f9 37: b9 38: c9 39: 9a 3a: 09 3b: 78 3c: 4d 3d: e4 3e: 72 3f: a6 40: 06 41: bf 42: 8b 43: 62 44: 66 45: dd 46: 30 47: fd 48: e2 49: 98 4a: 25 4b: b3 4c: 10 4d: 91 4e: 22 4f: 88 50: 36 51: d0 52: 94 53: ce 54: 8f 55: 96 56: db 57: bd 58: f1 59: d2 5a: 13 5b: 5c 5c: 83 5d: 38 5e: 46 5f: 40 60: 1e 61: 42 62: b6 63: a3 64: c3 65: 48 66: 7e 67: 6e 68: 6b 69: 3a 6a: 28 6b: 54 6c: fa 6d: 85 6e: ba 6f: 3d 70: ca 71: 5e 72: 9b 73: 9f 74: 0a 75: 15 76: 79 77: 2b 78: 4e 79: d4 7a: e5 7b: ac 7c: 73 7d: f3 7e: a7 7f: 57 80: 07 81: 70 82: c0 83: f7 84: 8c 85: 80 86: 63 87: 0d 88: 67 89: 4a 8a: de 8b: ed 8c: 31 8d: c5 8e: fe 8f: 18 90: e3 91: a5 92: 99 93: 77 94: 26 95: b8 96: b4 97: 7c 98: 11 99: 44 9a: 92 9b: d9 9c: 23 9d: 20 9e: 89 9f: 2e a0: 37 a1: 3f a2: d1 a3: 5b a4: 95 a5: bc a6: cf a7: cd a8: 90 a9: 87 aa: 97 ab: b2 ac: dc ad: fc ae: be af: 61 b0: f2 b1: 56 b2: d3 b3: ab b4: 14 b5: 2a b6: 5d b7: 9e b8: 84 b9: 3c ba: 39 bb: 53 bc: 47 bd: 6d be: 41 bf: a2 c0: 1f c1: 2d c2: 43 c3: d8 c4: b7 c5: 7b c6: a4 c7: 76 c8: c4 c9: 17 ca: 49 cb: ec cc: 7f cd: 0c ce: 6f cf: f6 d0: 6c d1: a1 d2: 3b d3: 52 d4: 29 d5: 9d d6: 55 d7: aa d8: fb d9: 60 da: 86 db: b1 dc: bb dd: cc de: 3e df: 5a e0: cb e1: 59 e2: 5f e3: b0 e4: 9c e5: a9 e6: a0 e7: 51 e8: 0b e9: f5 ea: 16 eb: eb ec: 7a ed: 75 ee: 2c ef: d7 f0: 4f f1: ae f2: d5 f3: e9 f4: e6 f5: e7 f6: ad f7: e8 f8: 74 f9: d6 fa: f4 fb: ea fc: a8 fd: 50 fe: 58 ff: af

Figure 4-55 FEC Log Table: $a^{i}$ to $i$

$$
H=\left|\begin{array}{cccccc}
1 & 1 & \ldots & 1 & 0 & 1 \\
a^{84} & a^{83} & \ldots & a & 1 & 0
\end{array}\right| \begin{aligned}
& \text { Row Parity } \\
& \text { Check Bits }
\end{aligned}
$$

Figure 4-56 H-matrix of the FEC

|  | $B_{0}$ | $\cdots$ | $B_{82}$ | $B_{83}$ | $B_{84}$ | $B_{85}$ |
| :--: | :--: | :--: | :--: | :--: | :--: | :--: |
| 0 | $a^{84}$ | $\cdots$ | $a^{2}$ | $a$ | 1 | $p_{0}$ |
| 1 | $a^{85}$ | $\cdots$ | $a^{3}$ | $a^{2}$ | $a$ | $p_{1}$ |
| 2 | $a^{86}$ | $\cdots$ | $a^{4}$ | $a^{3}$ | $a^{2}$ | $p_{2}$ |
| 3 | $a^{87}$ | $\cdots$ | $a^{5}$ | $a^{4}$ | $a^{3}$ | $p_{3}$ |
| 4 | $a^{88}$ | $\cdots$ | $a^{6}$ | $a^{5}$ | $a^{4}$ | $p_{4}$ |
| 5 | $a^{89}$ | $\cdots$ | $a^{7}$ | $a^{6}$ | $a^{5}$ | $p_{5}$ |
| 6 | $a^{90}$ | $\cdots$ | $a^{8}$ | $a^{7}$ | $a^{6}$ | $p_{6}$ |
| 7 | $a^{91}$ | $\cdots$ | $a^{9}$ | $a^{8}$ | $a^{7}$ | $p_{7}$ |

![img-52.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-52.jpeg)

Powers of alpha for the check bits for Bytes 0 to 84
Figure 4-57 Weight of check bits for different Bytes/bits 5

The Transmitter has to calculate $B_{N-1}$ (horizontal parity) and $B_{N-2}$ (Check Symbol) during encoding from the remaining (N-2) Bytes, as described above. The same mechanism will be used to compute the corresponding two Syndrome bytes at the Receiver. $N=86$. However, only one of the three groups has 86 B in its code word, whereas the other two have 85 Bytes each to form the 256B Flit. This is resolved by forcing $B_{83}=0$ for the information part so that two groups that have 85 Bytes each effectively become 86B with 84B as information (the last Byte being 0 ) and two Bytes of ECC. The mapping of the Flit Byte $i$ to an ECC group and the Byte-offset within the group can be derived as follows:

```
For 0 ≤ i ≤ 249,
    Byte i in Flit is mapped to ECC Group i mod 3
    with Byte Offset floor(i/3)
ECC Group 1 Byte Offset 83 is 0
ECC Group 2 Byte Offset 83 is 0
For 250 ≤ i ≤ 255 (the ECC Bytes),
    Byte i in Flit is mapped to ECC Group (i-249) mod 3
    with Byte Offset ceil(i/3)
```

Thus:

- Byte 0 of Flit maps to ECC Group 0, Byte offset 0;
- Byte 1 of Flit maps to ECC Group 1, Byte offset 0;
- Byte 2 of Flit maps to ECC group 2, Byte offset 0;
- Byte 3 of Flit maps to ECC Group 0, Byte offset 1;
- Byte 4 of Flit maps to ECC Group 1, Byte offset 1;
- ...
- Byte 248 maps to ECC group 2, Byte Offset 82;
- Byte 249 maps to ECC group 0, Byte offset 83.
- ECC group 1, Byte offset 83 is 00 h .
- ECC group 2, Byte offset 83 is 00 h .

The ECC Bytes are then allocated as:

- Bytes 250 and 253 of the Flit maps to ECC Group 1, Byte offsets 84 and 85 respectively;
- Bytes 251 and 254 of the Flit maps to ECC Group 2, Byte offsets 84 and 85 respectively; and
- Bytes 252 and 255 of the Flit maps to ECC Group 0, Bytes offsets 84 and 85 respectively.

The basic idea is that horizontal parity (Synd_Parity) identifies the bits in the Symbol (or Byte) that has flipped and the check bits (Synd_Check) identifies the Symbol number that has the error. Looking at the expanded bit arrangement, one can see that knowing the bit positions one can reverse map the column number. § Figure 4-58 shows the ECC decode function. The Syndrome Parity is the XOR of $B_{0} . . B_{83}$ and $B_{85}$ (Synd_Parity). The Syndrome Check (Synd_Check) is calculated by computing the expected $\mathrm{B}_{84}$ from $\mathrm{B}_{0} . \mathrm{B}_{83}$ received and XORing with received $\mathrm{B}_{84}$. Once the two Syndrome Symbols (Bytes) are calculated, the following steps are taken:

| Synd_Check | Synd_Parity | Description |
| :--: | :--: | :-- |
| $=00 \mathrm{~h}$ | $=00 \mathrm{~h}$ | No error |
| $=00 \mathrm{~h}$ | $\neq 00 \mathrm{~h}$ | Error in $B_{85}$ : Corrected $B_{85}=B_{85}{ }^{\wedge}$ Synd_Parity |
| $\neq 00 \mathrm{~h}$ | $=00 \mathrm{~h}$ | Error in $B_{84}$ : Corrected $B_{84}=B_{84}{ }^{\wedge}$ Synd_Check |
| $\neq 00 \mathrm{~h}$ | $\neq 00 \mathrm{~h}$ | Follow the log table for Synd_Check, Synd_Parity and then follow the modulo subtraction +1 logic to <br> identify the failing column number. It is possible that we point to a non-existing column, in that case <br> it is an uncorrectable error. Once the column number is known, we can correct the Symbol and the <br> corresponding CRC correction (if applicable) |

![img-53.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-53.jpeg)

Figure 4-58 ECC Decoder function 9

The Receive side check is as follows on the 256B flit (as shown in § Figure 4-59). Each of the three ECC decoders, performs correction and error reporting as needed. In the final stage of CRC check, a decision is made whether the received flit can be accepted or retried.

![img-54.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-54.jpeg)

Figure 4-59 3-way ECC decode followed by CRC check of flit on the Receive side

# 4.2.3.4.2.5 Ordered Set insertion in Data Stream in Flit Mode 

For Data Rates of $2.5 \mathrm{GT} / \mathrm{s}$ or $5.0 \mathrm{GT} / \mathrm{s}$, the SKP Ordered Set insertion interval does not change (e.g., between 1180 and 1538 Symbols), but occurs at the Flit boundary. The other Ordered Sets that can occur with up-size or down-size with LOp is provided in $\S$ Section 4.2.6.7 .

For Data Rates of $8.0 \mathrm{GT} / \mathrm{s}$ and above, the following rules apply:

- A Control SKP Ordered Set must immediately follow the SDS Ordered Set sequence marking the start of the Data Stream, irrespective of when the prior Control SKP Ordered Set was transmitted.
- Once the Data Stream has started, an Ordered Set must be transmitted in fixed intervals, as defined § Table 4-30, as follows:
- If the Data Stream will continue, a SKP Ordered Set must be transmitted on all the active (or to be activated) Lanes.
- On an up-size with LOp: The Lanes that will be activated to join the active Lanes, an SDS Ordered Set must be transmitted on all the Lanes that will be activated (not in those that are already active) just prior to sending the SKP Ordered Set across all the wider Link, after which Flits will be sent on the wider Link
- Else If the Link will enter a low-power state, an EIOSQ must be transmitted on all the active Lanes
- Else (the Link needs to enter Recovery): An EIEOS must be transmitted on all the configured Lanes of the Link
- If the Link enters Recovery, the appropriate SKP Ordered Set must be transmitted immediately after the first Ordered Set (EIEOS).

Table 4-30 Ordered Set insertion interval once Data Stream starts in terms of number of Flits

| Link Width and Clocking Modes | $\times 16$ | $\times 8$ | $\times 4$ | $\times 2$ | $\times 1$ |
| :-- | :--: | :--: | :--: | :--: | :--: |
| Common Clock/SRNS Mode with 1b/1b encoding | 748 | 374 | 187 | 93 | 46 |
| Common Clock/SRNS Mode with 128b/130b encoding | 374 | 187 | 93 | 46 | 23 |
| SRIS Mode with 1b/1b encoding | 74 | 37 | 18 | 9 | 4 |
| SRIS Mode with 128b/130b encoding | 37 | 18 | 9 | 4 | 2 |

# IMPLEMENTATION NOTE: CONSECUTIVE SKP ORDERED SETS IN FLIT MODE 

Two consecutive SKP Ordered Sets in a Data Stream in Flit Mode are always equidistant for a given width and clocking mode when either 1b/1b encoding or 128b/130b encoding is used. For example, for a x1 Link in SRIS Mode with 128b/130b encoding, a SKP Ordered Set is always sent after two Flits, which will occupy 32 Data Blocks. However, the same spacing cannot be guaranteed with 8b/10b encoding, as the SKPs are "scheduled" every 1180 to 1583 Symbol times in non-SRIS mode and less than 154 Symbol times in SRIS mode. For example, a x1 Link in SRIS mode with 8b/10b encoding sends an average of 1.66 (=256/154) SKP Ordered Sets after every Flit (256 Symbols): sometimes it sends one SKP Ordered Set after every Flit and other times it sends two back-to-back SKP Ordered Sets.

### 4.2.4 Link Equalization Procedure for 8.0 GT/s and Higher Data Rates

The Link equalization procedure enables components to adjust the Transmitter and the Receiver setup of each Lane to improve the signal quality and meet the requirements specified in $\S$ Chapter 8 ., when operating at $8.0 \mathrm{GT} / \mathrm{s}$ and higher data rates. All the Lanes that are associated with the LTSSM (i.e., those Lanes that are currently operational or may be operational in the future due to Link Upconfigure) must participate in the equalization procedure. The procedure must be executed during the first data rate change to any data rate at $8.0 \mathrm{GT} / \mathrm{s}$ or above, unless all components in the Link have advertised that no equalization is needed. Components must arrive at the appropriate Transmitter setup for all the operating conditions and data rates that they will encounter in the future when LinkUp=1b. Components must not require that the equalization procedure be repeated at any data rate for reliable operation, although there is provision to repeat the procedure. Components must store the Transmitter setups that were agreed to during the equalization procedures and use them for future operation at $8.0 \mathrm{GT} / \mathrm{s}$ and higher data rates. Components are permitted to fine-tune their Receiver setup even after the equalization procedure is complete as long as doing so does not cause the Link to be unreliable (i.e., does not meet the requirements in § Chapter 8. ) or go to Recovery.

The Link equalization procedure is not required for any data rates and can be completely bypassed if all components in the Link have advertised that no equalization is needed in its TS1/TS2 Ordered Sets or Modified TS1/TS2 Ordered Sets (see § Table 4-34, § Table 4-35, and § Table 4-36). A component may choose to advertise that it does not need equalization at any rates above $5.0 \mathrm{GT} / \mathrm{s}$ if it supports $32.0 \mathrm{GT} / \mathrm{s}$ or higher data rates and can either operate reliably with equalization settings stored from a prior equalization procedure or does not need equalization for reliable operation.

The equalization procedure can be initiated either autonomously or by software. It is strongly recommended that components use the autonomous mechanism for all the data rates above $5.0 \mathrm{GT} / \mathrm{s}$ that they intend to operate in. However, a component that chooses not to participate in the autonomous mechanism for all the data rates above $5.0 \mathrm{GT} / \mathrm{s}$ must have its associated software ensure that the software based mechanism is applied to the data rates above $5.0 \mathrm{GT} / \mathrm{s}$ where the autonomous mechanism was not applied, prior to operating at that data rate.

Normally, equalization is performed at a higher data rate only if equalization has successfully completed at all lower data rates above $5.0 \mathrm{GT} / \mathrm{s}$. For example, a Link will complete equalization successfully at $8.0 \mathrm{GT} / \mathrm{s}$, followed by $16.0 \mathrm{GT} / \mathrm{s}$, followed by $32.0 \mathrm{GT} / \mathrm{s}$, followed by $64.0 \mathrm{GT} / \mathrm{s}$. However, an optional mechanism to begin the equalization procedures at the highest NRZ rate supported, $32.0 \mathrm{GT} / \mathrm{s}$, is permitted if all components support data rates of $32.0 \mathrm{GT} / \mathrm{s}$ or higher and the mechanism is supported by all components in the Link, as advertised in the TS1/TS2 Ordered sets or Modified TS1/ TS2 Ordered Sets. When this optional mechanism is enabled and successfully negotiated between the components, equalization is not performed the $8.0 \mathrm{GT} / \mathrm{s}$ and $16.0 \mathrm{GT} / \mathrm{s}$ data rates; the equalization procedures are performed at all common data rates above $16.0 \mathrm{GT} / \mathrm{s}$ beginning with the $32.0 \mathrm{GT} / \mathrm{s}$ data rate For all the data rates above $5.0 \mathrm{GT} / \mathrm{s}$ where equalization is not performed (specifically $8.0 \mathrm{GT} / \mathrm{s}$ and $16.0 \mathrm{GT} / \mathrm{s}$ ), the expectation is that the Link will not operate at those data rates and the components will not advertise those data rates (neither $8.0 \mathrm{GT} / \mathrm{s}$ nor $16.0 \mathrm{GT} / \mathrm{s}$ ) as the highest data rate supported. For example, a Link may train to L0 in $2.5 \mathrm{GT} / \mathrm{s}$, enter Recovery and perform equalization at $32.0 \mathrm{GT} /$ s, and then re-enter Recovery and perform equalization at $64.0 \mathrm{GT} / \mathrm{s}$, skipping equalization at $8.0 \mathrm{GT} / \mathrm{s}$ and $16.0 \mathrm{GT} / \mathrm{s}$. In this case, the intended data rates of operation of the Link are $2.5 \mathrm{GT} / \mathrm{s}, 5.0 \mathrm{GT} / \mathrm{s}, 32.0 \mathrm{GT} / \mathrm{s}$, or $64.0 \mathrm{GT} / \mathrm{s}$. If any of the equalization procedures attempted at $32.0 \mathrm{GT} / \mathrm{s}$ or $64.0 \mathrm{GT} / \mathrm{s}$ is unsuccessful even after re-equalization attempts and the Link needs to equalize at lower data rates, the Downstream Port must stop advertising Equalization Bypass to Highest NRZ Rate Support and ensure that the Link returns to operation at $2.5 \mathrm{GT} / \mathrm{s}$ or $5.0 \mathrm{GT} / \mathrm{s}$. The required equalization procedures are then performed as they would have been if the optional mechanism to skip over equalization to the highest common data rate(s) was never supported. If the equalization procedure at the highest NRZ rate supported is initially successful but the Link is not able to operate reliably at that data rate, the Downstream Port is permitted to initiate a speed change to any lower data rate followed by an equalization procedure at that rate (when necessary). The requirements of § Table 4-31 must be followed. The Upstream Port must disable Equalization Bypass to Highest NRZ Rate support as soon as an equalization procedure at the $8.0 \mathrm{GT} / \mathrm{s}$ data rate is performed. If the equalization procedure at the lower data rates is driven by software, it must set the Equalization Bypass to Highest NRZ Rate Disable and No Equalization Needed Disable register bits to lb each; set the target Link speed such that the Link will be operational at $2.5 \mathrm{GT} / \mathrm{s}$ or $5.0 \mathrm{GT} / \mathrm{s}$; and then set the target Link speed to equalize at the lower rates starting with $8.0 \mathrm{GT} / \mathrm{s}$ onwards. A port must not advertise the Equalization Bypass to Highest NRZ Rate Support if the Equalization Bypass to Highest NRZ Rate Disable bit is Set to lb.

Another optional mechanism to skip the entire equalization process and go directly to the highest common data rate is permitted if all components support data rates of $32.0 \mathrm{GT} / \mathrm{s}$ or higher and the No Equalization Needed mechanism is supported by all components in the Link, as advertised in the TS1/TS2 or Modified TS1/TS2 Ordered sets. This is done if a component is either able to retrieve the equalization and other circuit settings at all the data rates from a prior equalization that will work for the component, or it does not need equalization at all in all data rates above $5.0 \mathrm{GT} / \mathrm{s}$. A component must not advertise this capability if the Equalization Bypass to Highest NRZ Rate Disable bit is Set to lb. Components supporting $64.0 \mathrm{GT} / \mathrm{s}$ or higher data rate are strongly encouraged to support this mode, especially after the equalization has been performed at least once since power was applied. This would be helpful for faster resume times after the devices in the Link go through deep power savings states.

If one direction of the Link is advertising No Equalization Needed and the other side is advertising Equalization Bypass to Highest NRZ Rate Support in the TS1/TS2 Ordered Sets, the Link will operate in the Equalization Bypass to Highest NRZ Rate Support since the No Equalization Needed bit also indicates that the device is capable of bypassing Equalization to the highest data rate. In the Modified TS1/TS2 Ordered Sets, a device that sets No Equalization Needed bit to lb must also set the Equalization Bypass to Highest NRZ Rate Support to lb. If one direction of the Link is advertising No Equalization Needed bit and the other side is advertising Equalization Bypass to Highest NRZ Rate Support only in the Modified TS1/TS2 Ordered Sets, the Link will operate in the Equalization Bypass to Highest NRZ Rate Support. Link operation is undefined if a device advertises No Equalization Needed bit as lb and Equalization Bypass to Highest NRZ Rate Support to 0b in the Modified TS1/TS2 Ordered Sets it transmits. Components are permitted to go straight to $64.0 \mathrm{GT} / \mathrm{s}$ from any data rate without having to go through $32.0 \mathrm{GT} / \mathrm{s}$ data rate if No Equalization Needed has been negotiated, since no equalization is involved.

The autonomous mechanism is executed if both components advertise that they are capable of at least the $8.0 \mathrm{GT} / \mathrm{s}$ data rate (via the TS1 and TS2 Ordered Sets) during the initial Link negotiation (when LinkUp is set to lb) and the Downstream Port chooses to perform the equalization procedure at the intended data rates of operation above $5.0 \mathrm{GT} / \mathrm{s}$. While not recommended, the Downstream Port may choose to perform the autonomous mechanism only on a subset of

the intended data rates of operation above $5.0 \mathrm{GT} / \mathrm{s}$. In that case, the software based mechanism must be executed in order to perform the equalization procedure for the intended data rates of operation above $5.0 \mathrm{GT} / \mathrm{s}$, not covered by the autonomous mechanism. For example, if both components advertised $8.0 \mathrm{GT} / \mathrm{s}, 16.0 \mathrm{GT} / \mathrm{s}$, and $32.0 \mathrm{GT} / \mathrm{s}$ Data Rates but autonomous equalization was performed for only $8.0 \mathrm{GT} / \mathrm{s}$ and $16.0 \mathrm{GT} / \mathrm{s}$ Data Rates, then software based mechanism must be adopted for equalization at $32.0 \mathrm{GT} / \mathrm{s}$ Data Rate.

In the autonomous mechanism, after entering L0, irrespective of the current Link speed, neither component must transmit any DLLP, except the NOP2 DLLP, if the equalization procedure must be performed and until the equalization procedure completes. The equalization procedure is considered complete once the Transmitter and Receiver setup of each Lane has been adjusted for each common data rate supported above $5.0 \mathrm{GT} / \mathrm{s}$ for which the Downstream Port intends to perform equalization using the autonomous mechanism. The Downstream Port is required to initiate the speed change to the data rate where the equalization needs to be performed. During any equalization (autonomous or software initiated or re-equalization), the Downstream Port must not advertise support for any data rate above the data rate for which equalization needs to be performed in Recovery. The following example is provided to illustrate the equalization flow.

Example: Consider a Link where equalization needs to be performed autonomously at $8.0 \mathrm{GT} / \mathrm{s}$, and $16.0 \mathrm{GT} / \mathrm{s}$. The Downstream Port enters Recovery to perform equalization at $8.0 \mathrm{GT} / \mathrm{s}$ by not advertising any data rates above $8.0 \mathrm{GT} / \mathrm{s}$. The $8.0 \mathrm{GT} / \mathrm{s}$ equalization procedure is deemed to have been successfully executed if the Equalization $8.0 \mathrm{GT} / \mathrm{s}$ Phase 3 Successful bit and Equalization $8.0 \mathrm{GT} / \mathrm{s}$ Complete bit of the Link Status 2 register are both set to 1b. Immediately following the transition from Recovery to L0, after the initial data rate change to $8.0 \mathrm{GT} / \mathrm{s}$, the Downstream Port is required to transition from L0 to Recovery, advertise $16.0 \mathrm{GT} / \mathrm{s}$ data rate support (but not advertise support for $32.0 \mathrm{GT} / \mathrm{s}$, even if it is capable of supporting $32.0 \mathrm{GT} / \mathrm{s}$ ), change the data rate to $16.0 \mathrm{GT} / \mathrm{s}$ and perform the $16.0 \mathrm{GT} / \mathrm{s}$ equalization procedure.

If the Downstream Port detects equalization problems or the Upstream Port made an equalization redo request (by setting the Request Equalization bit to 1b) the Downstream Port may redo equalization prior to proceeding to operate at the data rate where the equalization failed or performing equalization at a higher data rate. The number of back-to-back equalization redos at a given data rate is implementation specific but must be finite. If at the conclusion of the initial or subsequent equalization process and the execution of an implementation specific number of equalization redo's, the Link is not able to operate reliably at the data rate where equalization was performed, then it must revert back to a lower data rate of operation.

Components using the autonomous mechanism must not initiate any autonomous Link width downsizing until the equalization procedure completes. An Upstream Port must not transmit any DLLP, except the NOP2 DLLP, until it receives a non-NOP2 DLLP from the Downstream Port. If the Downstream Port performs equalization again, it must not transmit any DLLP, except the NOP2 DLLP, until it completes the equalization procedure. A Downstream Port may perform equalization again based on its own needs or based on the request from the Upstream Port, if it can meet its system requirements. Executing equalization multiple times may interfere with software determination of Link and device status, as described in $\S$ Section 6.6 .

# IMPLEMENTATION NOTE: DLLP BLOCKING DURING AUTONOMOUS EQUALIZATION 

When using the autonomous mechanism for equalization at $8.0 \mathrm{GT} / \mathrm{s}$ or higher data rates, the Downstream Port is required to block the transmission of DLLPs until equalization has completed at all data rates for which the autonomous equalization mechanism will be performed, and the Upstream Port is required to block the transmission of DLLPs until a DLLP is received from the Downstream Port. If both components advertise that they are capable of the $16.0 \mathrm{GT} / \mathrm{s}$ (or higher) data rate but the Downstream Port only uses the autonomous mechanism for equalization at $8.0 \mathrm{GT} / \mathrm{s}$, the Downstream Port is only required to block DLLP transmission until $8.0 \mathrm{GT} / \mathrm{s}$ equalization has completed. Similarly, if both components advertise that they are capable of the $32.0 \mathrm{GT} / \mathrm{s}$ data rate but the Downstream Port only uses the autonomous mechanism for equalization at $16.0 \mathrm{GT} / \mathrm{s}$, the Downstream Port is only required to block DLLP transmission until $16.0 \mathrm{GT} / \mathrm{s}$ equalization has completed. If the Downstream Port delays entering Recovery from L0 while DLLP transmission is blocked, either the L0 Inferred Electrical Idle timeout (see § Section 4.2.5.4) or the DLLP timeout (see § Section 2.6.1.2) may expire in the Upstream or Downstream Ports. If either of these two timeouts occurs, it will result in the initiation of an entry to Recovery to perform Link retraining. Neither of these two timeouts is a reportable error condition, and the resulting Link retraining has no impact on proper Link operation.

The DLLP limitations described in this implementation note do not apply to NOP2 DLLPs. When operating in Flit Mode, since entry to Recovery must happen on an Ordered Set boundary, Flit transmission may occur prior to the completion of equalization at all data rates for which the autonomous equalization mechanism will be performed. These Flits will be transmitting NOP2 DLLPs. The receipt of NOP2 DLLPs cannot be used by the Upstream Port to unblock the transmission of non-NOP2 DLLPs.

When using the software based mechanism, software must guarantee that there will be no side-effects for transactions in flight (e.g., no timeout), if any, due to the Link undergoing the equalization procedure. Software can write 1b to the Perform Equalization bit in the Link Control 3 Register, followed by a write to the Target Link Speed field in the Link Control 2 register to enable the Link to run at $8.0 \mathrm{GT} / \mathrm{s}$ or higher, followed by a write of 1 b to the Retrain Link bit in the Link Control register of the Downstream Port to perform equalization. Software must not enable the Link to run at a data rate above $8.0 \mathrm{GT} / \mathrm{s}$ during a software initiated equalization procedure if the equalization procedure at all the lower data rates starting with $8.0 \mathrm{GT} / \mathrm{s}$ have not been successfully executed and the Link is not capable of bypassing equalization to higher data rate(s) (i.e., either Equalization Bypass to Highest NRZ Rate Supported is 0b or Equalization Bypass to Highest NRZ Rate Disable is 1b). The equalization procedure is deemed successful as follows for the following data rates:

- $8.0 \mathrm{GT} / \mathrm{s}$ : Equalization $8.0 \mathrm{GT} / \mathrm{s}$ Phase 3 Successful bit and Equalization $8.0 \mathrm{GT} / \mathrm{s}$ Complete bit of the Link Status 2 register are both set to 1b
- $16.0 \mathrm{GT} / \mathrm{s}$ : Equalization $16.0 \mathrm{GT} / \mathrm{s}$ Phase 3 Successful bit and Equalization $16.0 \mathrm{GT} / \mathrm{s}$ Complete bit of the $16.0 \mathrm{GT} / \mathrm{s}$ Status Register are both set to 1b
- 32.0 GT/s: Equalization 32.0 GT/s Phase 3 Successful bit and Equalization 32.0 GT/s Complete bit of the 32.0 GT/s Link Status Register are both set to 1b
- 64.0 GT/s: Equalization 64.0 GT/s Phase 3 Successful bit and Equalization 64.0 GT/s Complete bit of the 64.0 GT/s Link Status Register are both set to 1b

Software may set the Hardware Autonomous Width Disable bit of the Link Control register in both components, or use some other mechanism to ensure that the Link is in its full functional width prior to setting the Perform Equalization bit in the Downstream Port. The component that had initiated the autonomous width downsizing is responsible to upconfigure the Link to go to its full functional width by initiating the transition to Recovery and Configuration within 1 ms of the Hardware Autonomous Width Disable bit being set to 1b. If an Upstream Port does not advertise the $8.0 \mathrm{GT} / \mathrm{s}$ data rate, the $16.0 \mathrm{GT} / \mathrm{s}$ data rate, the $32.0 \mathrm{GT} / \mathrm{s}$, or the $64.0 \mathrm{GT} / \mathrm{s}$ data rate initially and did not participate in the autonomous

equalization mechanism for the non-advertised rates, its associated software must ensure there will be no side-effects for transactions in flight, if any, during equalization, before it instructs the Upstream Port to go to Recovery and advertise the previously non-advertised data rates and initiate a speed change. The Downstream Port subsequently initiates the equalization procedure during the initial speed change to the data rate advertised by the Upstream Port when it transitions to Recovery.

Upstream Ports are required to check for equalization setting problems in the Recovery.RcvrLock state (see § Section 4.2.7.4.1). However, both Downstream and Upstream Ports are permitted to use implementation specific methods to detect equalization problems at any time. A Port that detects a problem with its equalization settings is required to undertake the following actions, for each the following data rates:

- 8.0 GT/s: Link Equalization Request 8.0 GT/s bit in the Link Status 2 Register is set to 1b.
- 16.0 GT/s: Link Equalization Request 16.0 GT/s bit in the 16.0 GT/s Status Register is set to 1b.
- 32.0 GT/s: Link Equalization Request 32.0 GT/s bit in the 32.0 GT/s Status Register is set to 1b.
- 64.0 GT/s: Link Equalization Request 64.0 GT/s bit in the 64.0 GT/s Status Register is set to 1b.

In addition to setting the appropriate Link Equalization Request bit to 1b, an Upstream Port must initiate a transition to Recovery (if necessary) and request equalization at the appropriate data rate in the Recovery.RcvrCfg state by setting the Request Equalization bit of its transmitted TS2 Ordered Sets to 1b and the Equalization Request Data Rate bits to the data rate of the detected problem. If it requests equalization, it must request equalization for each detected problem only once. When requesting equalization, the Upstream Port is also permitted, but not required, to set the Quiesce Guarantee bit to 1b to inform the Downstream Port that an equalization process initiated within 1 ms will not cause any side-effects to its operation.

When a Downstream Port receives an equalization request from an Upstream Port (when it is in the Recovery.RcvrCfg state and receives 8 consecutive TS2 Ordered Sets with the Request Equalization bit set to 1b), it must either initiate an equalization process at the requested data rate (as defined by the received Equalization Request Data Rate bits) within 1 ms of completing the next Recovery to L0 transition, or it must set the appropriate Link Equalization Request 8.0 GT/s in its Link Status 2 register, Link Equalization Request 16.0 GT/s bit in its 16.0 GT/s Status Register, Link Equalization Request 32.0 GT/s bit in its 32.0 GT/s Status Register, or Link Equalization Request 64.0 GT/s bit in its 64.0 GT/s Status Register. It should initiate an equalization process only if it can guarantee that executing the equalization process will not cause any side-effects to either its operation or the Upstream Port's operation. The Downstream Port is permitted, but not required, to use the received Quiesce Guarantee bit to determine the Upstream Port's ability to execute an equalization process without side-effects.

If a Downstream Port wants to initiate an equalization process and can guarantee that it will not cause side-effects to its own operation but is unable to directly determine whether the equalization process will cause side-effects to the Upstream Port's operation, then it is permitted to request that the Upstream Port initiate an equalization request. The Downstream Port does so by transitioning to Recovery and in the Recovery.RcvrCfg state setting the Request Equalization bit of its transmitted TS2 Ordered Sets to 1b, the Equalization Request Data Rate bits to the desired data rate, and the Quiesce Guarantee bit to 1b. When an Upstream Port receives such an equalization request from a Downstream Port (when it is in the Recovery.RcvrCfg state and receives 8 consecutive TS2 Ordered Sets with the Request Equalization and Quiesce Guarantee bits set to 1b), it is permitted, but not required, to quiesce its operation and prepare to execute an equalization process at the data rate requested by the Downstream Port, and then request equalization at that same data rate (using the method described previously for reporting equalization setting problems) and with the Quiesce Guarantee bit set to 1b. There is no time limit on how long the Upstream Port can take to respond, but it should attempt to do so as quickly as possible. If a Downstream Port makes a request and receives such a response from the Upstream Port, then it must either initiate an equalization process at the agreed-upon data rate within 1 ms of completing the next Recovery to L0 transition if it can still guarantee that executing the equalization process will not cause any side-effects to its operation, or it must set the appropriate Link Equalization Request 8.0 GT/s bit in its Link Status 2 register, Link Equalization Request 16.0 GT/s bit in its 16.0 GT/s Status Register, Link Equalization Request 32.0 GT/s bit in its 32.0 GT/s Status Register, or Link Equalization Request 64.0 GT/s bit in its 64.0 GT/s Status Register.

# IMPLEMENTATION NOTE: USING QUIESCE GUARANTEE MECHANISM 

Side-effects due to executing equalization after the Data Link Layer is in DL_Active can occur at the Port, Device, or system level. For example, the time required to execute the equalization process could cause a Completion Timeout error to occur - possibly in a different system component. The Quiesce Guarantee information allows Ports to decide whether to execute a requested equalization or not.

A component may operate at a lower data rate after reporting its equalization problems, either by timing out through Recovery.Speed or by initiating a data rate change to a lower data rate. Any data rate change required to perform the equalization procedure is exempt from the 200 ms requirement in $\S$ Section 6.11. § Table 4-31 describes the mechanism for performing redo Equalization. Sometimes it may be necessary to perform a speed change to an intermediate data rate to redo equalization. For example, if the Downstream Port wants to redo equalization at $16.0 \mathrm{GT} / \mathrm{s}$, bypass equalization is not supported, and the current data rate is either $2.5 \mathrm{GT} / \mathrm{s}$ or $5.0 \mathrm{GT} / \mathrm{s}$, the Downstream Port must first initiate a speed change to $8.0 \mathrm{GT} / \mathrm{s}$ (the $8.0 \mathrm{GT} / \mathrm{s}$ equalization procedure will not be executed unless necessary) from which it will launch the redo equalization for $16.0 \mathrm{GT} / \mathrm{s}$. The equalization procedure can be performed at most once in each trip through the Recovery state.

Table 4-31 Equalization Requirements Under Different Conditions

From
2.5 GT/s or
$5.0 \mathrm{GT} / \mathrm{s}$ to
$8.0 \mathrm{GT} / \mathrm{s}$
Equalization

The mechanisms described here are identical for all flavors of equalization: initial or redo equalization; autonomous or software initiated.

The Downstream Port communicates the Transmitter preset values and the Receiver preset hints, if applicable, for each Lane to the Upstream Port using 8b/10b encoding. These values are communicated using the EQ TS2 Ordered Sets (defined in § Section 4.2.5.1) in Recovery.RcvrCfg, when a data rate change to the higher data rate has been negotiated, prior to transitioning to the higher data rate to perform equalization. The preset values sent in the EQ TS2 Ordered Sets are derived as follows:

- For equalization at 8.0 GT/s: Upstream Port 8.0 GT/s Transmitter Preset and Upstream Port 8.0 GT/s Receiver Preset Hint fields of each Lane Equalization Control Register Entry.

After the data rate change to the higher data rate where equalization needs to be performed, the Upstream Port transmits TS1 Ordered Sets with the preset values it received. The preset values must be within the operable range defined in § Section 8.3.3.3 if reduced swing will be used by the Transmitter.

After the data rate change to the higher data rate where equalization needs to be performed, the Downstream Port transmits TS1 Ordered Sets with the preset values as follows with the assumption that the preset values must be within the operable range defined in $\S$ Section 8.3.3.3 if reduced swing will be used by the Transmitter:

- For equalization at 8.0 GT/s: Downstream Port 8.0 GT/s Transmitter Preset and optionally Downstream Port 8.0 GT/s Receiver Preset Hint fields of each Lane Equalization Control Register Entry.

To perform redo equalization, the Downstream Port must request speed change through EQ TS1 Ordered Sets in Recovery.RcvrLock at $2.5 \mathrm{GT} / \mathrm{s}$ or $5.0 \mathrm{GT} / \mathrm{s}$ to inform the Upstream Port that it intends to redo equalization at the higher data rate. An Upstream Port should advertise the higher data rate in Recovery if it receives EQ TS1 Ordered Sets with speed change bit set to 1 b and if it intends to operate at the higher data rate in the future.

From
8.0 GT/s to
$16.0 \mathrm{GT} / \mathrm{s}$
Equalization, from
$16.0 \mathrm{GT} / \mathrm{s}$ to

The mechanisms described here are identical for all flavors of equalization: initial or redo equalization; autonomous or software initiated.

When negotiating to the higher data rate, the Downstream Port communicates the Transmitter preset values for each Lane to the Upstream Port using 128b/130b encoding. These values are communicated using 128b/ 130b EQ TS2 Ordered Sets (defined in § Section 4.2.5.1) in Recovery.RcvrCfg, when a data rate change to the higher

32.0 GT/s

Equalization, OR from 32.0 GT/s to 64.0 GT/s Equalization
data rate has been negotiated, prior to transitioning to the higher data rate. The preset values sent in the 128b/ 130b EQ TS2 Ordered Sets are derived as follows:

- For equalization at 16.0 GT/s: Upstream Port 16.0 GT/s Transmitter Preset field of the 16.0 GT/s Lane Equalization Control Register Entry corresponding to the Lane.
- For equalization at 32.0 GT/s: Upstream Port 32.0 GT/s Transmitter Preset field of the 32.0 GT/s Lane Equalization Control Register Entry corresponding to the Lane.
- For equalization at 64.0 GT/s: Upstream Port 64.0 GT/s Transmitter Preset field of the 64.0 GT/s Lane Equalization Control Register Entry corresponding to the Lane.

Optionally, the Upstream Port communicates initial Transmitter preset settings to the Downstream Port using the 128b/130b EQ TS2 Ordered Sets sent in Recovery.RcvrCfg, when a data rate change to the higher data rate has been negotiated, prior to transitioning to the higher data rate at which equalization needs to be performed. These preset values are determined by implementation specific means. After the data rate change to the higher data rate, the Upstream Port transmits TS1 Ordered Sets with the preset values it received. If the Downstream Port did not receive preset values in Recovery.RcvrCfg, after the data rate change to the higher data rate, it transmits TS1 Ordered Sets with the presets as follows:

- For equalization at 16.0 GT/s: Downstream Port 16.0 GT/s Transmitter Preset field of the 16.0 GT/s Lane Equalization Control Register Entry corresponding to the Lane.
- For equalization at 32.0 GT/s: Downstream Port 32.0 GT/s Transmitter Preset field of the 32.0 GT/s Lane Equalization Control Register Entry corresponding to the Lane.
- For equalization at 64.0 GT/s: Downstream Port 64.0 GT/s Transmitter Preset field of the 64.0 GT/s Lane Equalization Control Register Entry corresponding to the Lane.

The preset values must be within the operable range defined in $\S$ Section 8.3.3.3 if reduced swing will be used by the Transmitter.

To perform redo equalization, the Downstream Port must request speed change through TS1 Ordered Sets in Recovery.RcvrLock with the Equalization Redo bit set to 1b to inform the Upstream Port that it intends to redo equalization. An Upstream Port should advertise the higher data rate in Recovery if it receives TS1 Ordered Sets with speed change bit set to 1b, Equalization Redo bit set to 1b and it intends to operate at the higher data rate in the future.

From
2.5 GT/s or 5.0 GT/s to 32.0 GT/s Equalization

Equalization to 32.0 GT/s from 2.5 GT/s or 5.0 GT/s is possible only if the Link is capable of bypassing equalization to higher data rate(s) (i.e., Equalization Bypass to Highest NRZ Rate Supporting in 32.0 GT/s Capabilities register is 1b and Equalization Bypass to Highest NRZ Rate Disable in the 32.0 GT/s Control Register is 0b).

The mechanisms described here are identical for all flavors of equalization: initial or redo equalization; autonomous or software initiated.

The Downstream Port communicates the Transmitter preset values for each Lane to the Upstream Port using 8b/ 10b encoding. These values are communicated using the EQ TS2 Ordered Sets (defined in $\S$ Section 4.2.5.1) in Recovery.RcvrCfg, when a data rate change to the higher data rate has been negotiated, prior to transitioning to the higher data rate to perform equalization. The preset values sent in the EQ TS2 Ordered Sets are derived as follows:

- For equalization at 32.0 GT/s: Upstream Port 32.0 GT/s Transmitter Preset field of the 32.0 GT/s Lane Equalization Control Register Entry corresponding to the Lane.

After the data rate change to the higher data rate where equalization needs to be performed, the Upstream Port transmits TS1 Ordered Sets with the preset values it received. The preset values must be within the operable range defined in $\S$ Section 8.3.3.3 if reduced swing will be used by the Transmitter.

After the data rate change to the higher data rate where equalization needs to be performed, the Downstream Port transmits TS1 Ordered Sets with the preset values as follows with the assumption that the preset values must be within the operable range defined in $\S$ Section 8.3.3.3 if reduced swing will be used by the Transmitter:

- If eight consecutive EQ TS2 Ordered Sets were received with supported Transmitter Preset values in the most recent transition through Recovery.RcvrCfg, the Transmitter Preset value from those EQ TS2 Ordered Sets must be used.
- Otherwise: Downstream Port 32.0 GT/s Transmitter Preset field of the 32.0 GT/s Lane Equalization Control Register Entry corresponding to the Lane must be used.

To perform redo equalization, the Downstream Port must request speed change through EQ TS1 Ordered Sets in Recovery.RcvrLock at $2.5 \mathrm{GT} / \mathrm{s}$ or $5.0 \mathrm{GT} / \mathrm{s}$ to inform the Upstream Port that it intends to redo equalization at the higher data rate. An Upstream Port should advertise the higher data rate in Recovery if it receives EQ TS1 Ordered Sets with speed change bit set to 1 b and if it intends to operate at the higher data rate in the future.

| From <br> $2.5 \mathrm{GT} / \mathrm{s}$ or <br> $5.0 \mathrm{GT} / \mathrm{s}$ to <br> $64.0 \mathrm{GT} / \mathrm{s}$ <br> Equalization | Equalization to $64.0 \mathrm{GT} / \mathrm{s}$ from $2.5 \mathrm{GT} / \mathrm{s}$ or $5.0 \mathrm{GT} / \mathrm{s}$ is not supported. All equalization procedures at the $64.0 \mathrm{GT} / \mathrm{s}$ data rate, including re-equalization, must be initiated from the $32.0 \mathrm{GT} / \mathrm{s}$ data rate only. |
| :--: | :--: |
| Equalization at a data rate from a data rate equal to the target equalization data rate | This is only possible with a redo equalization. The combinations covered here are: $8.0 \mathrm{GT} / \mathrm{s}$ equalization from $8.0 \mathrm{GT} / \mathrm{s}$ data rate, $16.0 \mathrm{GT} / \mathrm{s}$ equalization from $16.0 \mathrm{GT} / \mathrm{s}$ data rate, and $32.0 \mathrm{GT} / \mathrm{s}$ equalization from $32.0 \mathrm{GT} / \mathrm{s}$ data rate. <br> In this case, the initial preset used during equalization is equal to the initial preset used during the last time the equalization was performed at the data rate where equalization is being performed. <br> $64.0 \mathrm{GT} / \mathrm{s}$ equalization from $64.0 \mathrm{GT} / \mathrm{s}$ is not supported. |

The equalization procedure consists of up to four Phases, as described below. When operating at $8.0 \mathrm{GT} / \mathrm{s}$ or higher data rates, the Phase information is transmitted using the Equalization Control (EC) field in the TS0 or TS1 Ordered Sets.

# Phase 0 

This phase is executed while negotiating (and prior to) to the data rate where equalization would be performed. The preset to be used for equalization is determined as described in $\S$ Table 4-31.

## Phase 1

Both components make the Link operational enough at the current data rate to be able to exchange TS1 Ordered Sets to complete the remaining phases for the fine-tuning of their Transmitter/Receiver pairs. For the Data Rates of $8.0 \mathrm{GT} / \mathrm{s}, 16.0 \mathrm{GT} / \mathrm{s}$, and $32.0 \mathrm{GT} / \mathrm{s}$, TS1 Ordered Sets are exchanged in this Phase. For the Data Rate of $64.0 \mathrm{GT} / \mathrm{s}$, TS0 Ordered Sets are exchanged in this Phase and each Pseudo-Port or Port must be able to exchange the TS0 Ordered Sets for Phase 1 and Phase 2 in the Upstream Direction (from the Upstream Port to Downstream Port) reliably when it exits this Phase. It is expected that the Link will operate at a BER of less than $10^{-4}$ before the component is ready to move on to the next Phase. Each Transmitter uses the preset values as described in § Table 4-31.

The Downstream Port initiates Phase 1 by transmitting TS1 Ordered Sets for Data Rates of $8.0 \mathrm{GT} / \mathrm{s}, 16.0 \mathrm{GT} / \mathrm{s}$ and $32.0 \mathrm{GT} / \mathrm{s}$ and TS0 Ordered Sets for the Data Rate of $64.0 \mathrm{GT} / \mathrm{s}$ with $\mathrm{EC}=01 \mathrm{~b}$ (indicating Phase 1). The Upstream Port, after adjusting its Receiver, if necessary, to ensure that it can progress with the equalization process, receives these TS0 or TS1 Ordered Sets and transitions to Phase 1 (where it transmits TS1 Ordered Sets with EC=01b if the Data Rate is $8.0 \mathrm{GT} / \mathrm{s}, 16.0 \mathrm{GT} / \mathrm{s}$, or $32.0 \mathrm{GT} / \mathrm{s}$ or TS0 Ordered Sets with EC=01b if the Data Rate is $64.0 \mathrm{GT} / \mathrm{s}$ ). The Downstream Port ensures that it can reliably receive the bit stream from the Upstream Port to continue through the rest of the Phases when it receives TS0 or TS1 Ordered Sets from the Upstream Port with EC=01b before it moves on to Phase 2.

## Phase 2

In this Phase the Upstream Port adjusts the Transmitter setting of the Downstream Port along with its own Receiver setting, independently, on each Lane, to ensure it receives the bit stream compliant with the requirements in

$\S$ Chapter 8. (e.g., each operational Downstream Lane has a BER less than $10^{-12}$ for a Data Rate of $32.0 \mathrm{GT} / \mathrm{s}$ or lower or $10^{-6}$ for the Data Rate of $64.0 \mathrm{GT} / \mathrm{s}$ ). If the Data Rate is $8.0 \mathrm{GT} / \mathrm{s}, 16.0 \mathrm{GT} / \mathrm{s}$ or $32.0 \mathrm{GT} / \mathrm{s}$, both the Downstream Port and the Upstream Port transmit TS1 Ordered Sets. If the Data Rate is $64.0 \mathrm{GT} / \mathrm{s}$, the Downstream Port transmits TS0 Ordered Sets until it receives TS0 Ordered Sets and then it transmits TS1 Ordered Sets whereas the Upstream Port transmits TS0 Ordered Sets. The Downstream Port initiates the move to Phase 2 by transmitting TS0/TS1 Ordered Sets with EC=10b to the Upstream Port. The Downstream Port advertises the Transmitter coefficients and the preset it is using per the rules below in Phase 1 for preset only and in Phase 2 for preset and coefficients. The Upstream Port receives these Ordered Sets and may request different coefficient or preset settings and continue to evaluate each setting until it arrives at the best setting for operating the Downstream Lanes. After the Upstream Port has completed this Phase, it moves the Link to Phase 3 by transmitting TS1 Ordered Sets for a Data Rate of $32.0 \mathrm{GT} / \mathrm{s}$ or lower and TS0 Ordered Sets for a Data Rate of $64.0 \mathrm{GT} / \mathrm{s}$ with $\mathrm{EC}=11 \mathrm{~b}$ to the Downstream Port.

# Phase 3 

In this Phase the Downstream Port adjusts the Transmitter setting of the Upstream Port along with its own Receiver setting, independently, on each Lane, using a handshake and evaluation process similar to Phase 2 with the exception that EC=11b. The Downstream Port signals the end of Phase 3 (and the equalization procedure) by transmitting TS1 Ordered Sets with EC=00b.

The algorithm used by a component to adjust the transmitter of its Link partner and the evaluation of that Transmitter set-up with its Receiver set-up is implementation specific. A component may request changes to any number of Lanes and can request different settings for each Lane. Each requested setting can be a preset or a set of coefficients that meets the requirements defined in $\S$ Section 4.2.4.1. Each component is responsible for ensuring that at the end of the fine-tuning (Phase 2 for Upstream Ports and Phase 3 for Downstream Ports), its Link partner has the Transmitter setting in each Lane that will cause the Link to meet the requirements in $\S$ Chapter 8 .

A Link partner receiving the request to adjust its Transmitter must evaluate the request and act on it. If a valid preset value is requested and the Transmitter is operating in full swing mode, it must be reflected in the Transmitter set-up and subsequently in the preset and coefficient fields of the TS1 Ordered Set that the Link partner transmits. If a preset value is requested, the Transmitter is operating in reduced swing mode, and the requested preset is supported as defined in § Section 8.3.3.3 it must be reflected in the Transmitter set-up and subsequently in the preset and coefficient fields of the TS1 Ordered Set that the Link partner transmits. Transmitters operating in reduced swing mode are permitted to reject preset requests that are not supported as defined in $\S$ Section 8.3.3.3. A request for adjusting the coefficients may be accepted or rejected. If the set of coefficients requested for a Lane is accepted, it must be reflected in the Transmitter set-up and subsequently in the transmitted TS1 Ordered Sets. If the set of coefficients requested for a Lane is rejected, the Transmitter set-up is not changed, but the transmitted TS1 Ordered Sets must reflect the requested coefficients along with the Reject Coefficient Values bit set to 1b. In either case of responding to a coefficient request, the preset field of the transmitted TS1 Ordered Sets is not changed from the last preset value that was transmitted. A request for adjusting the coefficients may be rejected by the Link partner only if the set of coefficients requested is not compliant with the rules defined in $\S$ Section 4.2.4.1.

When performing equalization of a crosslink, the component that played the role of the Downstream Port during the earlier crosslink initialization at the lower data rate also assumes the responsibility of the Downstream Port for equalization.

If a Lane receives a Transmitter Preset value (from a TS0, TS1 or TS2 sequence) with a Reserved or unsupported value in Polling.Compliance, Loopback, or Phase 0 or Phase 1 of Recovery. Equalization, then the Lane is permitted to use any supported Transmitter preset setting in an implementation specific manner. The Reserved or unsupported Transmitter preset value is transmitted in any subsequent compliance patterns or Ordered Sets, and not the implementation specific Transmitter preset value chosen by the Lane. For example, if a Lane of an Upstream Port receives a Transmitter preset value 1111b (Reserved) with the EQ TS2 Ordered Sets it receives in Recovery.RcvrCfg, it is permitted to use any supported Transmitter preset value for its transmitter setting after changing the data rate to $8.0 \mathrm{GT} / \mathrm{s}$, but it must transmit 1111b as its Transmitter preset value in the TS1 Ordered Sets it transmits in Phase 0 and Phase 1 of Recovery. Equalization.

In the Loopback state, the Loopback Lead is responsible for communicating the Transmitter and Receiver settings it wants the Follower to use through the EQ TS1 Ordered Sets it transmits in the $2.5 \mathrm{GT} / \mathrm{s}$ or $5.0 \mathrm{GT} / \mathrm{s}$ data rate, and the preset or coefficient settings it wants the device under test to operate under in the TS1 Ordered Sets it transmits in the $8.0 \mathrm{GT} / \mathrm{s}$ or higher data rate. Similarly, if the Polling.Compliance state for $8.0 \mathrm{GT} / \mathrm{s}$ or higher Data Rates is entered through TS1 Ordered Sets, the entity that is performing the test is required to send the appropriate settings in EQ TS1 Ordered Sets and presets for the device under test to operate with, according to the mechanism defined in $\S$ Section 4.2.7.2 .

# IMPLEMENTATION NOTE: EQUALIZATION EXAMPLE 

Some examples are presented in this note to help explain Link equalization. This is not a complete listing of all allowable equalization scenarios.

The following diagram is an example illustrating how two devices may complete the equalization procedure. If the maximum common data rate supported by both Ports is $8.0 \mathrm{GT} / \mathrm{s}$, the equalization procedure is complete at the conclusion of the $8.0 \mathrm{GT} / \mathrm{s}$ equalization procedure. If the maximum common data rate supported by both Ports is $16.0 \mathrm{GT} / \mathrm{s}$, the $8.0 \mathrm{GT} / \mathrm{s}$ equalization procedure is followed by the $16.0 \mathrm{GT} / \mathrm{s}$ equalization procedure. If either the $8.0 \mathrm{GT} / \mathrm{s}$ or $16.0 \mathrm{GT} / \mathrm{s}$ equalization procedure is repeated and is performed while the Link is in $8.0 \mathrm{GT} / \mathrm{s}$ data rate (for the $8.0 \mathrm{GT} / \mathrm{s}$ equalization) or in $16.0 \mathrm{GT} / \mathrm{s}$ (for the $16.0 \mathrm{GT} / \mathrm{s}$ equalization), Phase 0 may be skipped since there is no need for the Link to go back to $2.5 \mathrm{GT} / \mathrm{s}$ or $5.0 \mathrm{GT} / \mathrm{s}$ (for the $8.0 \mathrm{GT} / \mathrm{s}$ equalization) or $8.0 \mathrm{GT} / \mathrm{s}$ (for the $16.0 \mathrm{GT} / \mathrm{s}$ equalization) to resend the same EQ TS2 Ordered Sets to convey the presets. A Downstream Port may choose to skip Phase 2 and Phase 3 if it determines that fine-tuning of the Transmitter is not needed based on the channel and components in the platform.
§ Figure 4-62 shows an example flow for $64.0 \mathrm{GT} / \mathrm{s}$ after the Link completes the $32.0 \mathrm{GT} / \mathrm{s}$ equalization with the use of TS0 and TS1 Ordered Sets.

Note that some transitions may not be covered; such as the transition from receiving TS0 to receiving TS1 in a given sub-state.
![img-55.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-55.jpeg)

Figure 4-60 8.0 GT/s Equalization Flow
![img-56.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-56.jpeg)

Figure 4-61 16.0 GT/s Equalization Flow

![img-57.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-57.jpeg)

Phase 0: 128b/130b EQ TS2 Ordered Sets sent from Downstream Port to Upstream Port.

Phase 1: Both sides exchange TS0 Ordered Sets to establish an operational Link.
EIEOS sent every 32 TS0 Ordered Sets.
Phase 2: Upstream Port requests
Downstream Port to set its Transmitter's coefficients/presents to have its incoming Link meet the electrical requirements. The Downstream Port may send EIEOS in up to 65536 TS1 Ordered Sets, based on the Upstream Port's request. The Upstream Port sends an EIEOS every 32 TS0 Ordered Sets.

Phase 3: Downstream Port requests Upstream Port to set its Transmitter's coefficients/presents to have its incoming Link meet the electrical requirements. The Upstream Port may send EIEOS in up to 65536 TS1 Ordered Sets, based on the Downstream Port's request. The Downstream Port sends an EIEOS every 32 TS1 Ordered Sets.

# Equalization Complete 

Post 64.0 GT/s Equalization: LTSSM goes through Recovery.RcvrLock,
Recovery.RcvrCtg, and Recovery.lste to L0. EIEOS sent after every 32 TS1/TS2 Ordered Sets.

64GT-training.vsds
Figure 4-62 64.0 GT/s Equalization Flow 5

# IMPLEMENTATION NOTE: EQUALIZATION BYPASS EXAMPLE 

The following flow-chart provides an example flow where a Link may bypass equalization at lower Data Rates and go to the highest supported NRZ rate for equalization. For example, when $n=5$, the Link can train to L0 in Gen 1 data rate, establish that all components (including Retimers, if any) can bypass equalization to Gen 5, change the data rate to Gen 5 and just perform equalization at Gen 5.
![img-58.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-58.jpeg)

Figure 4-63 Equalization Bypass Example

### 4.2.4.1 Rules for Transmitter Coefficients

The explanation of the coefficients and the FIR filter it represents are provided in $\S$ Section 8.3.3.1. The following rules apply to both the advertised as well as requested coefficient settings.

1. $\boldsymbol{C}_{\boldsymbol{.}}, \boldsymbol{C}_{\boldsymbol{.}}, \mathbf{2}$, and $\boldsymbol{C}_{\boldsymbol{+}, \mathbf{2}}$ are the coefficients used in the FIR equation and represent the $2^{\text {nd }}$ pre-cursor, pre-cursor and post-cursor, respectively. The pre-cursors and post-cursor values communicated in the TS1 Ordered Sets represent their absolute values. $\boldsymbol{C}_{\boldsymbol{0}}$ represents the cursor coefficient setting and is a positive entity. The coefficient $\mathbf{C}_{\mathbf{. 2}}$ is used only for $\mathbf{6 4 . 0} \mathbf{G T} / \mathrm{s}$ and higher Data Rates.
2. The sum of the absolute values of the coefficients defines the FS (Full Swing; FS $=\left|C_{-2}\right|+\left|C_{-1}\right|+C_{0}+\left|C_{+1}\right|$ ). FS is advertised to the Link partner in Phase 1. The Transmitter FS range is defined below:

- $\mathrm{FS} \in\{24, \ldots, 63\}$ (i.e., FS must have a value from 24 through 63) for full swing mode.
- $\mathrm{FS} \in\{12, \ldots, 63\}$ for reduced swing mode.
- $\mathrm{C}_{-2}$ is set to 0 for Data Rates lower than $64.0 \mathrm{GT} / \mathrm{s}$.

3. A Transmitter advertises its LF (Low Frequency) value during Phase 1.

- This corresponds to the minimum differential voltage that can be generated by the Transmitter which is LF/FS times the Transmitters maximum differential voltage. The Transmitter must ensure that LF meets the electrical requirements defined in $\S$ Section 8.3.3.9 for $V_{\text {TX-EIROS-FS }}$ and $V_{\text {TX-EIROS-RS- }}$.

4. The following rules must be satisfied before a set of coefficients can be requested of the Link partner's Transmitter. Upon reception of an update request for TX coefficient settings, a Port must verify that the new request meets the following conditions and reject the request if any of following conditions are violated:
a. $\left|C_{-1}\right| \leq$ Floor (FS/4)
b. $\left|C_{-1}\right|+\left|C_{-2}\right|+C_{0}+\left|C_{+1}\right|=F S$
(Do not allow peak power to change with adaptation)
c. $C_{0}-\left|C_{-1}\right|+\left|C_{-2}\right|-\left|C_{+1}\right| \geq L F$
d. $\left|C_{-2}\right| \leq$ Floor (FS/8)

# 4.2.4.2 Encoding of Presets 

Definition of the Transmitter and Receiver Preset Hints appears in § Chapter 8. . The encoding for the Transmitter Preset and Receiver Preset Hint are provided in § Table 4-32 and § Table 4-33. There are two classes of presets: P0 through P10 are defined for data rates of $8.0 \mathrm{GT} / \mathrm{s}, 16.0 \mathrm{GT} / \mathrm{s}$, and $32.0 \mathrm{GT} / \mathrm{s}$ whereas Q0 through Q10 are defined for the data rate of $64.0 \mathrm{GT} / \mathrm{s}$. Even though 8 of the 11 presets across these two sets overlap, it is possible that the same preset values may get different encodings between the two classes. Receiver Preset Hints are optional and only defined for the $8.0 \mathrm{GT} / \mathrm{s}$ data rate.

Table 4-32 Transmitter Preset Encoding

| Encoding | Preset Number in \$ Table 8-1 | Preset Number in \$ Table 8-2 |
| :--: | :--: | :--: |
| 0000b | P0 | Q0 |
| 0001b | P1 | Q1 |
| 0010b | P2 | Q2 |
| 0011b | P3 | Q3 |
| 0100b | P4 | Q4 |
| 0101b | P5 | Q5 |
| 0110b | P6 | Q6 |
| 0111b | P7 | Q7 |
| 1000b | P8 | Q8 |
| 1001b | P9 | Q9 |
| 1010b | P10 | Q10 |
| 1011b through 1111b | Reserved | Reserved |

| Encoding | Receiver Preset Value |
| :--: | :--: |
| 000b | -6 dB |
| 001b | -7 dB |
| 010b | -8 dB |
| 011b | -9 dB |
| 100b | -10 dB |
| 101b | -11 dB |
| 110b | -12 dB |
| 111b | Reserved |

# IMPLEMENTATION NOTE: QUANTIZATION ERRORS AT 64.0 GT/S 

Due to the tighter preset tolerance at 64.0 GT/s some FS values will result in a quantization error larger than is allowed for the specified tolerance of the presets in $\S$ Table 8-2 of $\S$ Section 8.3.3.3 . The implementation must compensate for any quantization error from its selection of FS to meet the specified preset accuracy.

### 4.2.5 Link Initialization and Training

This section defines the Physical Layer control process that configures and initializes each Link for normal operation. This section covers the following features:

- configuring and initializing the Link
- supporting normal packet transfers
- supported state transitions when recovering from Link errors
- restarting a Port from low power states.

The following are discovered and determined during the training process:

- Link width
- Link data rate
- Lane reversal
- Lane polarity

Training does:

- Link data rate negotiation
- Bit lock per Lane

- Lane polarity
- Symbol lock or Block alignment per Lane
- Lane ordering within a Link
- Link width negotiation
- Lane-to-Lane de-skew within a multi-Lane Link.


# 4.2.5.1 Training Sequences 

Training sequences are composed of Ordered Sets used for initializing bit alignment, Symbol alignment and to exchange Physical Layer parameters.

1. When the data rate is $2.5 \mathrm{GT} / \mathrm{s}$ or $5.0 \mathrm{GT} / \mathrm{s}$, Ordered Sets are never scrambled but are always $8 \mathrm{~b} / 10 \mathrm{~b}$ encoded.
2. When the data rate is between $8.0 \mathrm{GT} / \mathrm{s}$ and $32.0 \mathrm{GT} / \mathrm{s}$, the $128 \mathrm{~b} / 130 \mathrm{~b}$ encoding is used and Symbols may or may not be scrambled, according to the rules in $\S$ Section 4.2.2.4.
3. When the data rate is $64.0 \mathrm{GT} / \mathrm{s}$ the $1 \mathrm{~b} / 1 \mathrm{~b}$ encoding is used and Symbols may or may not be scrambled, according to the rules in $\S$ Section 4.2.3.1.2 .

Training sequences (TS0, TS1, TS2, Modified TS1, or Modified TS2) are transmitted consecutively and can only be interrupted by SKP Ordered Sets (see § Section 4.2.8) or, for data rates other than $2.5 \mathrm{GT} / \mathrm{s}$, EIEOS (see § Section 4.2.5.3).

When $8.0 \mathrm{GT} / \mathrm{s}$ or higher data rates are supported, a TS1 (or TS2) Ordered Set using 8b/10b encoding (i.e., 2.5 or $5.0 \mathrm{GT} / \mathrm{s}$ data rate) can be either a standard TS1 (or TS2) Ordered Set (i.e., Symbol 6 is D10.2 for a TS1 Ordered Set or D5.2 for a TS2 Ordered Set) or an EQ TS1 Ordered Set (or EQ TS2 Ordered Set) (i.e., Symbol 6 bit 7 is 1b). The ability to transmit EQ TS1 Ordered Sets is implementation specific. Ports supporting $8.0 \mathrm{GT} / \mathrm{s}$ or higher data rates must accept either TS1 (or TS2) type in the LTSSM states unless explicitly required to look for a specific type. Ports that do not support the $8.0 \mathrm{GT} / \mathrm{s}$ data rate are permitted, but not required, to accept EQ TS1 (or TS2) Ordered Sets.

When the $16.0 \mathrm{GT} / \mathrm{s}$ and higher data rate is supported, a TS2 using 128b/130b encoding (i.e., 8.0 or higher data rate) can be either a standard TS2 Ordered Set (i.e., Symbol 7 is 45h) or an $\mathbf{1 2 8 b} / \mathbf{1 3 0 b}$ EQ TS2 (i.e., Symbol 7 bit 7 is 1b). Ports supporting the $16.0 \mathrm{GT} / \mathrm{s}$ or higher data rate must accept either TS2 type in the LTSSM states unless explicitly required to look for a specific type. Ports that do not support the $16.0 \mathrm{GT} / \mathrm{s}$ data rate are permitted, but not required, to accept 128b/ 130b EQ TS2 Ordered Sets.

When using 8b/10b encoding, TS1 or TS2 Ordered Sets are considered consecutive only if Symbol 6 matches Symbol 6 of the previous TS1 or TS2 Ordered Set.

Components that intend to either negotiate alternate protocols or pass a Training Set Message must use Modified TS1/ TS2 Ordered Sets instead of standard TS1/TS2 Ordered Sets in Configuration.Lanenum.Wait, Configuration.Lanenum.Accept, and Configuration.Complete substates. In order to be eligible to send the Modified TS1/ TS2 Ordered Sets, components must set the Enhanced Link behavior Control bits (bit 7:6 of Symbol 5) in TS1 and TS2 Ordered Sets to 11b in Polling.Active, Polling.Configuration, Configuration.Linkwidth.Start, and Configuration.Linkwidth.Accept substates and follow through the steps outlined on transition to Configuration.Lanenum.Wait substate when LinkUp=0b. If the Link partner does not support Modified TS1/TS2 Ordered Sets, then starting with Configuration.Lanenum.Wait, the standard TSs should stop sending 11b in the Enhanced Link Behavior Control field and switch to the appropriate encodings.

When using 8b/10b encoding, modified TS1 or modified TS2 Ordered Sets are considered consecutive only if all Symbols matches the corresponding Symbols of the previous modified TS1 or modified TS2 Ordered Sets and the parity in Symbol 15 matches with the expected value. Symbols 8-14 must be identical in each Modified TS1/TS2 Ordered Sets across all Lanes of a Link.

When using 128b/130b encoding, TS1 or TS2 Ordered Sets are considered consecutive only if Symbols 6-9 match Symbols 6-9 of the previous TS1 or TS2 Ordered Set, with Reserved bits treated as described below.

With 1b/1b encoding, TS0, TS1 and TS2 Ordered Sets consist of the first 8 symbols of the Ordered Set being replicated in the second 8 symbols of the Ordered Set, as shown in § Table 4-37 and § Table 4-38. The TS0 Ordered Set is used with 1b/ 1b encoding during the Recovery. Equalization, as described in the LTSSM section. Each Ul in the TS0 Ordered Set is either voltage level 0 or 3 with PAM-4 signaling, as shown in § Figure 4-24. Hence, the scrambled symbols in TS0 Ordered Sets are Half scrambled; the odd bit positions are scrambled whereas even bit position $j$ is identical to the odd bit position $j+1$. Precoding is bypassed in both the Transmitter and Receiver.

In 1b/1b encoding, valid 1b/1b TS0, TS1, or TS2 Ordered Set is defined as a received TS0, TS1, or TS2 Ordered Set where either half is valid:

- The first half is valid if Symbol 0 is a valid TS0/TS1/TS2 encoding, Symbols 0 to 7 passes its parity check after decoding Gray code and descrambling, and Symbol 7 is not equal to a DC balance pattern prior to performing gray code and descrambling.
- The second half is valid if Symbol 8 is a valid TS0/TS1/TS2 encoding, Symbols 8 to 15 passes its parity check after decoding Gray code and descrambling, and symbol 15 is not equal to a DC balance pattern prior to performing gray code and descrambling.
- Both halves are valid if Symbols 0 to 6 are identical to Symbols 8 to 14 after decoding Gray code and descrambling, and Symbols 7 and 15 are DC balance symbols prior to decoding Gray code and descrambling.
- The type of the Ordered Set (TS0, TS1, or TS2) is determined by the first symbol of the valid half.
- The even bits in the half-scrambled Symbols must be ignored after descrambling in the Receiver. (Note: because the gray code was done by forcing the even bit to be identical to the odd bit in the Transmitter, the even bit position may not be identical to the odd bit position on the Receiver after descrambling.)


# IMPLEMENTATION NOTE: HALF SCRAMBLING EXAMPLE 

Since the half-scrambled symbols are not fully gray-coded on the transmitter, rather the even bit is made identical to odd bit to have that UI be either a voltage level 0 or voltage level 3, it is possible that an even bit position in the half-scrambled symbol in the Receiver after gray-coding and descrambling may not match what was transmitted. For example, the Transmitter intends to send 80 h prior to scrambling. After scrambling, the symbol becomes 57 h and the gray-coded value by forcing the even bit to be identical to the odd bit becomes 03 h . On the Receiver side, 03 h after gray coding remains at 03 h and after descrambling becomes 94 h . Here bit 0 is different between the transmitted side 80 h vs. the receive side 94 h . However, all the odd bit positions that carry meaningful information are identical. By AND'ing 94 h with AAh, we get 80 h which was sent.

With 1b/1b encoding, two TS0, TS1 or TS2 Ordered Sets are considered consecutive if all of the following conditions apply to both the Ordered Sets:

- both Ordered Sets are of the same type
- they arrived one after the other, even though they may be separated by one or more SKP Ordered Set(s)
- each ordered set has a valid half and the first 7 symbols of the valid halves of each of the Ordered Set are identical, with Reserved bits treated as described below.

An invalid Ordered Set is a Training Set that does not pass the checks in § Section 4.2.5.1.
Reserved bits in TS0, TS1, TS2, Modified TS1 or Modified TS2 Ordered Sets must be handled as follows:

- The Transmitter must transmit 0s for Reserved bits.
- The Receiver:
- must not determine that a TS0, TS1, TS2, Modified TS1 or Modified TS2 Ordered Set is invalid based on the received value of Reserved bits
- must use the received value of Reserved bits for the purpose of a parity computation if the Reserved bits are included in a parity calculation
- may optionally compare the received value of Reserved bits within Symbols that are explicitly called out as being required to be identical in TS0, TS1, TS2, Modified TS1, or Modified TS2 Ordered Sets to determine if they are consecutive
- must not otherwise take any functional action based on the value of any received Reserved bits

When using 128b/130b or 1b/1b encoding, Transmitters are required to track the running DC Balance of the bits transmitted on the wire (after Gray code in 1b/1b, scrambling, and if turned on: precoding) that constitute the TS0, TS1, and TS2 Ordered Sets only. The running DC Balance is the difference between the number of 1 s transmitted and the number of 0 s transmitted in $8.0 \mathrm{GT} / \mathrm{s}, 16.0 \mathrm{GT} / \mathrm{s}$ or $32.0 \mathrm{GT} / \mathrm{s}$ Data Rates. The running DC Balance is the running sum of the DC balance values assigned to each voltage level in each UI, as shown in § Figure 4-24, for 64.0 GT/s Data Rate. Each Lane must track its running DC Balance independently and be capable of tracking a difference of at least $+/-511$ bits. Any counters used must saturate at their limit (not roll-over) and continue to track reductions after their limit is reached. For example, a counter that can track a difference of 511 will saturate at 511 if a difference of 513 is detected, and then change to 509 if the difference is reduced by 2 in the future.

The running DC Balance is set to 0 by two events:

1. The Transmitter exiting Electrical Idle;
2. Transmission of an EIEOS following a Data Block.

For every TS1 or TS2 Ordered Set transmitted with 128b/130b encoding, Transmitters must evaluate the running DC Balance and transmit one of the DC Balance Symbols defined for Symbols 14 and 15 as defined by the algorithm below. If the number of 1 s needs to be reduced, the DC Balance Symbols 20h (for Symbol 14) and 08h (for Symbol 15) are transmitted. If the number of 0 s needs to be reduced, the DC Balance Symbols DFh (for Symbol 14) and F7h (for Symbol 15) are transmitted. If no change is required, the appropriate TS1 or TS2 Identifier Symbol is transmitted. Any DC Balance Symbols transmitted for Symbols 14 or 15 bypass scrambling, while TS1 and TS2 Identifier Symbols follow the standard scrambling rules. The following algorithm must be used to control the DC Balance with 128b/130b encoding:

- If the running DC Balance is $>31$ at the end of Symbol 11 of the TS Ordered Set, transmit DFh for Symbol 14 and F7h for Symbol 15 to reduce the number of 0s, or 20h for Symbol 14 and 08h for Symbol 15 to reduce the number of 1 s .
- Else, if the running DC Balance is $>15$ at the end of Symbol 11 of the TS Ordered Set, transmit F7h for Symbol 15 to reduce the number of 0 s , or 08 h for Symbol 15 to reduce the number of 1 s . Transmit the normal TS Identifier Symbol (scrambled) for Symbol 14.
- Else, transmit the normal TS Identifier Symbol (scrambled) for Symbols 14 and 15.

Receivers are permitted, but not required, to check Symbols 14 and 15 for the following values when determining whether a TS1 or TS2 Ordered Set is valid with 128b/130b encoding:

- The appropriate TS Identifier Symbol after de-scrambling, or
- a valid DC Balance Symbol of DFh or 20h before de-scrambling for Symbol 14, or
- a valid DC Balance Symbol of F7h or 08h before de-scrambling for Symbol 15.

If a Receiver receives a DC balance pattern in Symbol 14 in 128b/130b encoding, it is possible that the pattern is scrambled (and precoded). Thus, if the Receiver is performing this optional check, it must keep descrambler and receive precoding running for checking Symbol 15, which can be either scrambled (and precoded) or the DC balance pattern.

# IMPLEMENTATION NOTE: SYNC HEADER AND DC BALANCE 5 

Block Sync Header bits and the first Symbol of TS1 and TS2 Ordered Sets do not affect the running DC Balance, because they have equal an number of 1 s and 0 s.

For every TS0, TS1 or TS2 Ordered Set transmitted with 1b/1b encoding, Transmitters must evaluate the running DC Balance and transmit one of the DC Balance Symbols defined for Symbols 7 and 15 as defined by the algorithm below. Any DC Balance Symbols transmitted in Symbols 7 and 15 bypass scrambling, while the byte-wise parity, if sent in Symbols 7 and 15, follows the standard scrambling rules.

- If the running DC Balance was $>+47$ at the start of the TS Ordered Set, transmit 00 h in Symbols 7 and 15 without scrambling.
- If the running DC Balance was <-47 at the start of the TS Ordered Set, transmit FFh in Symbols 7 and 15 without scrambling.
- Else, transmit the even byte parity of Symbols 0-6 (pre-scrambling) in Symbols 7 and 15 with scrambling.

While using TS0 Ordered Sets, the coefficients are not the full 6-bit value but adjusted to the appropriate number of bits that the corresponding coefficients, based on the constraints. For example, 3 bits are enough for the 2 nd pre-cursor since it cannot be higher than 7 .

The definitions of Hot_Reset_Request, Disable_Link_Request, Loopback_Request, and Compliance_Receive_Request depend on the encoding being used.

- When operating with 8b/10b or 128b/130b encoding, Hot_Reset_Request, Disable_Link_Request, Loopback_Request, or Compliance_Receive_Request are generated by asserting the appropriate Training Control bit. Hot_Reset_Request bit, Disable_Link_Request bit, and Loopback_Request bit asserted are mutually exclusive. Only one of those bits is permitted to be asserted at a time when transmitted on a configured Link or on all Lanes during Configuration. If more than one of Hot_Reset_Request bit, Disable_Link_Request bit, or Loopback_Request bit are asserted at the same time, the Link behavior is undefined. In some cases, Compliance_Receive_Request bit is permitted to be asserted when Loopback_Request bit is also asserted. The Link behavior is undefined when Compliance_Receive_Request bit is asserted and either Hot_Reset_Request bit or Disable_Link_Request bit is also asserted.
- When operating with 1b/1b encoding, Hot_Reset_Request, Disable_Link_Request, Loopback_Request, and Compliance_Receive_Request are generated using the appropriate Training Control field encoding. See § Section 4.2.5.1, § Table 4-37 for the Training Control field encodings.

The TS1 Ordered Set's Retimer Equalization Extend bit is always set to 0 b when transmitted by an Upstream Port or Downstream Port. Retimers set the bit to 1 b as described in $\S$ Section 4.3.7.2.

Table 4-34 TS1 Ordered Set in 8b/10b and 128b/130b Encoding
TS1 Ordered Set in 8b/10b and 128b/130b Encoding

| Symbol <br> Number | Description |
| :--: | :-- |
| 0 | TS1 Identifier |

| TS1 Ordered Set in 8b/10b and 128b/130b Encoding |  |
| :--: | :--: |
| Symbol <br> Number | Description |
| 1 | - When operating at 2.5 or $5.0 \mathrm{GT} / \mathrm{s}$ : COM (K28.5) for Symbol alignment. <br> - When operating at $8.0 \mathrm{GT} / \mathrm{s}$ or above: Encoded as 1Eh (TS1 Ordered Set). |
| 1 | Link Number <br> - Ports that do not support $8.0 \mathrm{GT} / \mathrm{s}$ or above: $0-255$, PAD. <br> - Downstream Ports that support $8.0 \mathrm{GT} / \mathrm{s}$ or above: $0-31$, PAD. <br> - Upstream Ports that support $8.0 \mathrm{GT} / \mathrm{s}$ or above: $0-255$, PAD. <br> - When operating at 2.5 or $5.0 \mathrm{GT} / \mathrm{s}$ : PAD is encoded as K23.7. <br> - When operating at $8.0 \mathrm{GT} / \mathrm{s}$ or above: PAD is encoded as F7h. |
| 2 | Lane Number within Link <br> - When operating at 2.5 or $5.0 \mathrm{GT} / \mathrm{s}$ : $0-31$, PAD. PAD is encoded as K23.7. <br> - When operating at $8.0 \mathrm{GT} / \mathrm{s}$ or above: $0-31$, PAD. PAD is encoded as F7h. |
| 3 | N_FTS - The number of Fast Training Sequences required by the Receiver: 0-255. Reserved when the Flit_Mode_Enabled variable is Set. |
|  | Data Rate Identifier |
|  | Bit 0 Flit Mode Supported bit: |
|  | 0b Flit Mode is not Supported (i.e., In the transmitter: either Flit Mode Supported is Clear (see PCI Express Capabilities Register) or Flit Mode Disable is Set (see Flit Mode Supported bit) |
|  | 1b Flit Mode is supported (i.e., both Flit Mode Supported is Set (see PCI Express Capabilities Register) and Flit Mode Disable is Clear (see Flit Mode Supported bit) |
|  | Bits 5:1 Supported Link Speeds: |
|  | Non-Flit Mode Encodings (valid during Flit Mode negotiation or when Flit Mode is not negotiated) |
|  | 00001 b 00011 b 00111 b 01111 b 1111 b Others | Only 2.5 GT/s supported <br> Only 2.5 and $5.0 \mathrm{GT} / \mathrm{s}$ supported <br> Only 2.5, 5.0, and $8.0 \mathrm{GT} / \mathrm{s}$ supported <br> Only 2.5, 5.0, 8.0, and $16.0 \mathrm{GT} / \mathrm{s}$ supported <br> Only 2.5, 5.0, 8.0, 16.0, and $32.0 \mathrm{GT} / \mathrm{s}$ supported <br> Reserved in Non-Flit Mode |
|  | Additional encodings permitted after Flit Mode is negotiated by all Link Partners after the first entry to Configuration. Complete from Detect or in the following states when the device supports Flit Mode: Polling.Active as a Receiver (see § Section 4.2.7.2.1), Configuration. Linkwidth.Start (see § Section 4.2.7.3.1), Recovery.Equalization (see § Section 4.2.7.4.1 and § Section 4.2.7.4.2) and Loopback (see § Section 4.2.7.10): |  |

| Symbol <br> Number | Description |
| :--: | :--: |
|  | 10111b <br> 2.5, 5.0, 8.0, 16.0, 32.0, and 64.0 GT/s supported if component had transmitted 11111 b in Supported Link Speeds in Polling and Configuration states since entering the Polling state. |
|  | Others | Reserved |
|  | Bit 6 | Autonomous Change / Selectable De-emphasis: <br> - Downstream Ports: This bit is defined for use in the following LTSSM states: Polling.Active, Configuration.Linkwidth.Start, and Loopback.Entry. In all other LTSSM states, it is Reserved. <br> - Upstream Ports: This bit is defined for use in the following LTSSM states: Polling.Active, Configuration, Recovery, and Loopback.Entry. In all other LTSSM states, it is Reserved. |
|  | Bit 7 | speed_change / SRIS Clocking <br> - Downstream Ports: <br> - In Configuration and Loopback.EntryStates: <br> - When LinkUp=0b: A 1b indicates that the Link will operate in SRIS clocking; a 0 b indicates either common clocking or SRNS clocking. The Downstream Port uses this bit to communicate the type of clocking to the Retimer(s), if any, as well as the Upstream Port so that the correct (Control) SKP Ordered Set frequency can be selected <br> - Else: this bit is Reserved <br> - In Recovery.RcvrLock: speed_change <br> - In other states: Reserved <br> - Upstream Ports: speed_change. This bit can be set to 1b only in the Recovery.RcvrLock LTSSM state. In all other LTSSM states, it is Reserved |
|  | Training Control |  |
|  | Bit 0 | Hot_Reset_Request bit <br> 0b <br> 1b <br> 1b <br> Bit 1 <br> 0b <br> 1b <br> Bit 2 <br> 0b <br> Bit 3 <br> Bit 4 | ![img-59.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-59.jpeg) <br> Loopback_Request bit <br> Deassert <br> Assert <br> Disable Scrambling bit (2.5 GT/s and 5.0 GT/s data rates) <br> Deassert <br> Assert <br> deata rates) |
|  | 0b <br> 1b <br> 0b <br> 1b | Deassert <br> Assert |

| Symbol <br> Number | Description |
| :--: | :--: |
|  | Ports that support 5.0 GT/s and higher data rate(s) must implement Compliance_Receive_Request. Ports that support only $2.5 \mathrm{GT} / \mathrm{s}$ data rate may optionally implement Compliance_Receive_Request. If not implemented, this bit is Reserved. |
| Bit 5 | Transmit Modified Compliance Pattern in Loopback. This bit is defined for use in Loopback by the Loopback Lead when 32.0 GT/s or higher data rates are supported. See § Section 4.2.7.10.1. In all other cases, this bit is Reserved. |
| Bit 7:6 | Enhanced Link Behavior Control |
|  | 00b Full Equalization Required |
|  | Modified TS1/TS2 Ordered Sets not supported |
|  | 01b Equalization Bypass to Highest NRZ Rate Support |
|  | Modified TS1/TS2 Ordered Sets not supported. |
|  | Indicates intention to perform 32.0 GT/s equalization when set by Loopback Lead. See § Section 4.2.4 and § Section 4.2.7.10.1 . |
|  | 10b No Equalization Needed |
|  | Modified TS1/TS2 Ordered Sets not supported |
|  | A device advertising this capability must support Equalization Bypass to Highest NRZ Rate Support. See § Section 4.2.4 . |
|  | 11b Modified TS1/TS2 Ordered Sets supported |
|  | Equalization bypass options specified in Modified TS1/TS2 Ordered Sets. |
|  | These bits are defined for use in Polling and Configuration when LinkUp=0b and 32.0 GT/s or higher data rates are supported and in Loopback by the Loopback Lead when 32.0 GT/s or higher data rates are supported. In all other cases, these bits are Reserved. |

When operating at 2.5 or $5.0 \mathrm{GT} / \mathrm{s}$ :

- Standard TS1 Ordered Sets encode this Symbol as a TS1 Identifier, D10.2 (4Ah).
- Compliance TS1 Ordered Sets encode the symbol as follows:

Bits 7:0 Compliance Setting Number defined in § Table 4-59. See § Section 4.2.7.2.2 for when to send Compliance TS1 Ordered Sets.

- EQ TS1 Ordered Sets encode this Symbol as follows:
- For Equalization at 8.0 GT/s Data Rate:

Bits 2:0 Receiver Preset Hint. See § Section 4.2.4.2 .
Bit 6:3 Transmitter Preset. See § Section 4.2.4.2 .
Bit 7 Set to 1b.

- For Equalization at 32.0 GT/s or higher Data Rate:

Bit 0 Transmitter Precode Request - See § Section 4.2.2.5. This bit has no defined usage in receivers at this time.
Bit 2:1
Reserved
Bit 6:3
Transmitter Preset. See § Section 4.2.4.2 .
Bit 7 Set to 1b.
When operating at $8.0 \mathrm{GT} / \mathrm{s}$ or higher data rate:
Bit 1:0 Equalization Control (EC). These bits are only used in the Recovery. Equalization and Loopback LTSSM states. See § Section 4.2.7.4.2 and § Section 4.2.7.10. In all other LTSSM states, they must be set to 00b.

|  | TS1 Ordered Set in 8b/10b and 128b/130b Encoding |  |
| :--: | :--: | :--: |
| Symbol <br> Number | Description |  |
|  | Bit 2 | Reset EIEOS Interval Count. This bit is defined for use in the Recovery. Equalization LTSSM state. See § Section 4.2.7.4.2 and § Section 4.2.5.3. In all other LTSSM states, it is Reserved. |
|  | Bit 6:3 | Transmitter Preset. See § Section 4.2.4 and § Section 4.2.7. |
|  | Bit 7 | Use Preset / Equalization Redo. This bit is defined for use in the Recovery. Equalization, Recovery.RcvrLock and Loopback LTSSM states. See § Section 4.2.7.4.1, § Section 4.2.7.4.2 and § Section 4.2.7.10. In all other LTSSM states, it is Reserved. |
| 7 | - When operating at 2.5 or 5.0 GT/s: TS1 Identifier. Encoded as D10.2 (4Ah). <br> - When operating at 8.0 GT/s or higher: <br> Bit 5:0 FS when the EC field of Symbol 6 is 01b (see § Section 4.2.4.1). Otherwise, Pre-cursor Coefficient for the current data rate of operation. |  |
|  | Bit 6 | Transmitter Precoding On. This bit is defined for use in the Recovery state for use at 32.0 GT/s or higher. See § Section 4.2.2.5. In all the other cases, it is Reserved. |
|  | Bit 7 | Retimer Equalization Extend bit. This bit is defined for use in the Recovery. Equalization LTSSM state when operating at $16.0 \mathrm{GT} / \mathrm{s}$ or higher data rate. In all other LTSSM states and when operating at $8.0 \mathrm{GT} / \mathrm{s}$, it is Reserved. |
| 8 | - When operating at 2.5 or 5.0 GT/s: TS1 Identifier. Encoded as D10.2 (4Ah). <br> - When operating at 8.0 GT/s or higher data rate: <br> Bit 5:0 LF when the EC field of Symbol 6 is 01b (see § Section 4.2.4.1). Otherwise, Cursor Coefficient for the current data rate of operation. |  |
|  | Bit 7:6 | Reserved. |
| 9 | - When operating at 2.5 or 5.0 GT/s: TS1 Identifier. Encoded as D10.2 (4Ah). <br> - When operating at 8.0 GT/s or higher data rate: <br> Bit 5:0 $\quad$ Post-cursor Coefficient for the current data rate of operation. <br> Bit 6 $\quad$ Reject Coefficient Values bit. This bit can only be set to 1 b in specific Phases of the Recovery. Equalization LTSSM State. See § Section 4.2.7.4.2. In all other LTSSM states, it must be set to 0 b . <br> Bit 7 Parity (P). This bit is the even parity computed over all bits of Symbols 6, 7, and 8 and bits 6:0 of Symbol 9 (i.e., XOR of all covered bits). Receivers must calculate the parity of the received bits and compare it to the received Parity bit. Received TS1 Ordered Sets are valid only if the calculated and received Parity match. |  |
| $10-13$ | - When operating at 2.5 or 5.0 GT/s: TS1 Identifier. Encoded as D10.2 (4Ah). <br> - When operating at 8.0 GT/s or above: TS1 Identifier. Encoded as 4Ah. |  |
| $14-15$ | - When operating at 2.5 or 5.0 GT/s: TS1 Identifier. Encoded as D10.2 (4Ah). <br> - When operating at 8.0 GT/s or above: TS1 Identifier (encoded as 4Ah) or a DC Balance Symbol. |  |

# IMPLEMENTATION NOTE: EXPECTED USAGE OF THE 64.0 GT/S SUPPORTED LINK SPEEDS ENCODING 6 

The TS1 and TS2 Ordered Sets for 8b/10b and 128b/130b encoding are permitted to have the Supported Link Speeds field encoded as 10111 b (indicating $2.5 \mathrm{GT} / \mathrm{s}$ to $64.0 \mathrm{GT} / \mathrm{s}$ support, inclusive) in the following scenarios:

1. Initial Link Training to L0 (Configuration.Complete and beyond)

The Link is training to L0 and Flit Mode has been negotiated during the training procedure (i.e., when LinkUp=0b). In this scenario the 10111 b encoding is permitted to be used once the Link enters Configuration.Complete.
2. Configuration.Linkwidth.Start (as a Receiver only)

When the Link transitions from Configuration.Linkwidth.Start to Loopback when LinkUp=0b, the Loopback Lead is permitted to transmit TS1 Ordered Sets with the Supported Link Speeds advertising 10111 b if it has prior knowledge that the Loopback Follower (i.e., the Receiver, which is still in Configuration.Linkwidth.Start) supports 64.0 GT/s. How the Loopback Lead obtains the prior knowledge of $64.0 \mathrm{GT} / \mathrm{s}$ support is outside the scope of the specification.
3. Recovery.Equalization when LinkUp=0b

Advertising the 10111 b encoding in Phase 1 of Recovery.Equalization when "Equalization for Loopback" is being performed. More specifically, this is the test scenario where Recovery.Equalization is entered from Loopback, the Link is equalized at the current data rate and then the Link returns to Loopback. In the case where the data rate is less than required (i.e., Link is equalized for $32.0 \mathrm{GT} / \mathrm{s}$ but $64.0 \mathrm{GT} / \mathrm{s}$ is needed), the 10111 b setting will be used to indicate to the Link partner the ability to transition to 64.0 GT/s upon re-entry to Loopback (after which an equalization procedure at $64.0 \mathrm{GT} / \mathrm{s}$ will be performed followed by a return to Loopback).
4. Loopback

When Loopback is entered through Configuration.Linkwidth.Start and LinkUp=0b, the Loopback Lead is permitted to use the 10111 b encoding in the TS1 Ordered sets that it transmits upon entry to Loopback.Entry (prior to the EIOSQ that proceeds Electrical Idle and the speed change).
5. Polling.Active (as a Receiver only)

Test apparatus that understands the capabilities of the Port (i.e., that the Port being exercised is capable of $64.0 \mathrm{GT} / \mathrm{s}$ operation) may transmit TS1 Ordered Sets with the Supported Link Speeds field set to the $64.0 \mathrm{GT} / \mathrm{s}$ supported encoding ( 10111 b ), and the Flit Mode Supported bit set (1b) in Polling.Active when the TS1 Ordered Sets also have Compliance_Receive_Request asserted and Loopback_Request deasserted. A Port that transitions to Polling.Compliance from Polling.Active because it received the appropriate TS1 Ordered Sets in Polling.Active will accept 10111 b as a valid Supported Link Speeds encoding (and consider it in its determination of the highest common data rate) if it supports the $64.0 \mathrm{GT} / \mathrm{s}$ data rate.

| TS2 Ordered Set in 8b/10b and 128b/130b Encoding |  |
| :--: | :--: |
| Symbol <br> Number | Description |
| 0 | TS2 Identifier <br> - When operating at 2.5 or $5.0 \mathrm{GT} / \mathrm{s}$ : COM (K28.5) for Symbol alignment. <br> - When operating at $8.0 \mathrm{GT} / \mathrm{s}$ or above: Encoded as 2 Dh (TS2 Ordered Set). |
| 1 | Link Number <br> - Ports that do not support $8.0 \mathrm{GT} / \mathrm{s}$ or above: $0-255$, PAD. <br> - Downstream Ports that support $8.0 \mathrm{GT} / \mathrm{s}$ or above: $0-31$, PAD. <br> - Upstream Ports that support $8.0 \mathrm{GT} / \mathrm{s}$ or above: $0-255$, PAD. <br> - When operating at 2.5 or $5.0 \mathrm{GT} / \mathrm{s}$ : PAD is encoded as K23.7. <br> - When operating at $8.0 \mathrm{GT} / \mathrm{s}$ or above: PAD is encoded as F7h. |
| 2 | Lane Number within Link <br> - When operating at 2.5 or $5.0 \mathrm{GT} / \mathrm{s}$ : $0-31$, PAD. PAD is encoded as K23.7. <br> - When operating at $8.0 \mathrm{GT} / \mathrm{s}$ or above: $0-31$, PAD. PAD is encoded as F7h. |
| 3 | N_FTS - The number of Fast Training Sequences required by the Receiver: 0-255. Reserved when the Flit_Mode_Enabled variable is Set. |
| 4 | Data Rate Identifier <br> Bit 0 Flit Mode Supported bit <br> 0b Flit Mode is not supported <br> 1b Flit Mode is supported <br> Bits 5:1 Supported Link Speeds: <br> Non-Flit Mode Encodings (valid during Flit Mode negotiation or when Flit Mode is not negotiated) <br> 00001 b Only 2.5 GT/s supported <br> 00011 b Only 2.5 and $5.0 \mathrm{GT} / \mathrm{s}$ supported <br> 00111 b Only 2.5, 5.0, and $8.0 \mathrm{GT} / \mathrm{s}$ supported <br> 01111 b Only 2.5, 5.0, 8.0, and $16.0 \mathrm{GT} / \mathrm{s}$ supported <br> 11111 b Only 2.5, 5.0, 8.0, 16.0, and $32.0 \mathrm{GT} / \mathrm{s}$ supported <br> Others Reserved in Non-Flit Mode <br> Additional encodings permitted after Flit Mode is negotiated by all Link Partners after the first entry to Configuration.Complete from Detect. <br> 10111 b 2.5, 5.0, 8.0, 16.0, 32.0, and $64.0 \mathrm{GT} / \mathrm{s}$ supported <br> Others Reserved |

| Symbol <br> Number | Description |
| :--: | :--: |
|  | Bit 6 Autonomous Change / Selectable De-emphasis / Link Upconfigure / LOp Capability - This bit is defined for use in the following LTSSM states: Polling.Configuration, Configuration.Complete, and Recovery. In all other LTSSM states, it is Reserved. |
|  | Bit 7 speed_change / SRIS Clocking <br> - Downstream Ports: <br> - In Configuration State: <br> - When LinkUp=0b: A 1b indicates that the Link will operate in SRIS clocking; a 0 b indicates either common clocking or SRNS clocking. The Downstream Port uses this bit to communicate the type of clocking to the Retimer(s), if any, as well as the Upstream Port so that the correct (Control) SKP Ordered Set frequency can be selected <br> - Else: this bit is Reserved <br> - In Recovery.RcvrCfg: speed_change <br> - In other states: Reserved <br> - Upstream Ports: speed_change. This bit can be set to 1b only in the Recovery.RcvrCfg LTSSM state. In all other LTSSM states, it is Reserved |
|  | Training Control |
|  | Bit 0 Hot_Reset_Request bit 0b Deassert |
|  | 1b Assert |
|  | Bit 1 Disable_Link_Request bit |
|  | 0b Deassert |
|  | 1b Assert |
|  | Bit 2 Loopback_Request bit |
|  | 0b Deassert |
|  | 1b Assert |
|  | Bit 3 Disable Scrambling bit in 2.5 GT/s and 5.0 GT/s data rates; Reserved in other data rates |
|  | 0b Deassert |
|  | 1b Assert |
|  | Bit 4 Retimer Present bit in 2.5 GT/s data rate. Reserved in other data rates. |
|  | 0b No Retimers present |
|  | 1b One or more Retimers present |
|  | Bit 5 Two Retimers Present bit in 2.5 GT/s data rate. Reserved in other data rates. |
|  | Ports that support 16.0 GT/s data rate or higher must implement this bit. Ports that support only 8.0 GT/s data rate or lower are permitted to implement this bit. |
|  | 0b Zero or one Retimers present (or bit not implemented) |
|  | 1b Two or more Retimers present |
|  | Bit 7:6 Enhanced Link Behavior Control |

| Symbol <br> Number | Description |  |
| :--: | :--: | :--: |
|  | 00b | Full Equalization Required, Modified TS1/TS2 Ordered Sets not supported. |
|  | 01b | Equalization Bypass to Highest NRZ Rate Support Modified TS1/TS2 Ordered Sets not supported. See § Section 4.2.4. |
|  | 10b | No Equalization Needed, <br> A device advertising this capability must support Equalization Bypass to Highest NRZ Rate Support. See § Section 4.2.4. <br> Modified TS1/TS2 Ordered Sets not supported |
|  | 11b | Modified TS1/TS2 Ordered Sets supported, Equalization bypass options specified in Modified TS1/TS2 Ordered Sets. |
|  | These bits defined for use in Polling and Configuration when LinkUp=0 and 32.0 GT/s or higher data rate is supported. In all other cases, Bits 7:6 are Reserved. |  |
|  | - When operating at 2.5 or $5.0 \mathrm{GT} / \mathrm{s}$ : <br> - Standard TS2 Ordered Sets encode this Symbol as a TS2 Identifier, D5.2 (45h). <br> - EQ TS2 Ordered Sets encode this Symbol as follows: <br> - For Equalization at 8.0 GT/s Data Rate: |  |
|  | Bit 2:0 | Receiver Preset Hint. See § Section 4.2.4.2. |
|  | Bit 6:3 | Transmitter Preset. See § Section 4.2.4.2. |
|  | Bit 7 | Set to 1b. |
|  | - For Equalization at 32.0 GT/s Data Rate: |  |
|  | Bit 0 | Transmitter Precode Request. See § Section 4.2.2.5 and § Section 4.2.3.1.4. |
|  | Bit 2:1 | Reserved |
|  | Bit 6:3 | Transmitter Preset. See § Section 4.2.4.2. |
|  | Bit 7 | Set to 1b. |
| 6 | - When operating at 8.0 GT/s or higher: |  |
|  | Bit 3:0 | Reserved. |
|  | Bit 5:4 | Equalization Request Data Rate. |
|  |  | 8.0 GT/s |
|  |  | 16.0 GT/s |
|  |  | 32.0 GT/s |
|  |  | 64.0 GT/s |
|  |  | These bits are defined for use in the Recovery.RcvrCfg LTSSM state. In all other LTSSM states, they are Reserved. See § Section 4.2.4 for usage and recognize that these bits are non-sequentially encoded for purposes of backwards compatibility |
|  | Bit 6 | Quiesce Guarantee. This bit is defined for use in the Recovery.RcvrCfg LTSSM state. In all other LTSSM states, it is Reserved. |
|  | Bit 7 | Request Equalization. This bit is defined for use in the Recovery.RcvrCfg LTSSM state. In all other LTSSM states, it is Reserved. |

| TS2 Ordered Set in 8b/10b and 128b/130b Encoding |  |
| :--: | :--: |
| Symbol <br> Number | Description |
| 7 | - When operating at 2.5 or 5.0 GT/s: TS2 Identifier. Encoded as D5.2 (45h). <br> - When operating at $8.0 \mathrm{GT} / \mathrm{s}$ or higher Data Rate: <br> - Standard TS2 Ordered Sets encode this Symbol as a TS2 Identifier, 45h. <br> - 128b/130b EQ TS2 Ordered Sets encode this Symbol as follows: <br> Bit 0 Transmitter Precode Request for operating at 32.0 GT/s or higher Data Rate. See § Section 4.2.2.5. This bit is Reserved if the 128b/130b EQ TS2 is sent for equalization at data rates of $8.0 \mathrm{GT} / \mathrm{s}$ or $16.0 \mathrm{GT} / \mathrm{s}$. <br> Bit 2:1 <br> Reserved <br> Bit 6:3 <br> 128b/130b Transmitter Preset. See § Section 4.2.4.2. <br> Bit 7 Set to 1b. <br> This definition is only valid in the Recovery.RcvrCfg LTSSM state when Preset values are being communicated. |
| $8-13$ | - When operating at 2.5 or 5.0 GT/s: TS2 Identifier. Encoded as D5.2 (45h). <br> - When operating at $8.0 \mathrm{GT} / \mathrm{s}$ or above: TS2 Identifier. Encoded as 45 h . |
| $14-15$ | - When operating at 2.5 or 5.0 GT/s: TS2 Identifier. Encoded as D5.2 (45h). <br> - When operating at $8.0 \mathrm{GT} / \mathrm{s}$ or above: TS2 Identifier (encoded as 45 h ) or a DC Balance Symbol. |
| Table 4-36 Modified TS1/TS2 Ordered Set (8b/10b encoding) |  |
| 0 | COM (K28.5) for Symbol alignment. |
| 1 | Link Number <br> Downstream Ports: 0-31, PAD (K23.7). <br> Upstream Ports: 0-255, PAD (K23.7). |
| 2 | Lane Number within Link - 0-31, PAD. PAD is encoded as K23.7. |
| 3 | N_FTS The number of Fast Training Sequences required by the Receiver: 0-255. Reserved when the Flit_Mode_Enabled variable is Set. |
| 4 | Data Rate Identifier <br> Bit 0 Flit Mode Supported bit <br> 0b Flit Mode is not supported <br> 1b Flit Mode is supported |

| Symbol <br> Number | Description |
| :--: | :--: |
|  | Bits 5:1 - Data Rates Supported |
| 00001 b | Only 2.5 GT/s Data Rate Supported. |
| 00011 b | Only 2.5 and 5.0 GT/s Data Rate Supported. |
| 00111 b | Only 2.5, 5.0, and 8.0 GT/s Data Rate Supported. |
| 01111 b | Only 2.5, 5.0, 8.0, and 16.0 GT/s Data Rate Supported. |
| 11111 b | Only 2.5, 5.0, 8.0, 16.0, and 32.0 GT/s Data Rate Supported. |
| Others | Reserved in Non-Flit Mode |
| Additional encodings permitted after Flit Mode is negotiated by all Link Partners after the first entry to Configuration. Complete from Detect: |  |
| 10111 b | $2.5,5.0,8.0,16.0,32.0$, and 64.0 GT/s supported |
| Others | Reserved |
| Bit 6 | Link Upconfigure / LOp Capability - This bit is defined for use in Configuration.Complete in Modified TS2 Ordered Sets. In all other LTSSM states, it is Reserved. |
| Bit 7 | SRIS Clocking - When LinkUp=0b: A 1b indicates that the Link will operate in SRIS clocking; a 0b indicates either common clocking or SRNS clocking. The Downstream Port uses this bit to communicate the type of clocking to the Retimer(s), if any, as well as the Upstream Port so that the correct (Control) SKP Ordered Set frequency can be selected |
|  | Else: this bit is Reserved |
| 5 | Training / Equalization Control |
|  | Bit 0 Equalization Bypass to Highest NRZ Rate Support. See § Section 4.2.4 |
|  | Bit 1 No Equalization Needed bit. See § Section 4.2.4 |
|  | Bit 3:2 Reserved |
|  | Bit 4 Retimer Present bit |
|  | 0b No Retimers present |
|  | 1b One Retimer is present |
|  | Bit 5 Two Retimers Present bit |
|  | 0b Zero or one Retimers present |
|  | 1b Two or more Retimers present |
|  | Bit 6 1b |
|  | Bit 7 1b |
| 6 | For Modified TS1: TS1 Identifier, encoded as D10.2 |
|  | For Modified TS2: TS2 Identifier, encoded as D5.2 |
| 7 | For Modified TS1: TS1 Identifier, encoded as D10.2 |
|  | For Modified TS2: TS2 Identifier, encoded as D5.2 |

| Modified TS1/TS2 Ordered Set (8b/10b encoding) |  |  |
| :--: | :--: | :--: |
| Symbol <br> Number | Description |  |
| 8-9 | Bits 2:0 | Modified TS Usage |
|  |  | 000b <br> 001b <br> 010b <br> Others | PCle protocol only <br> PCle protocol only with vendor defined Training Set Messages <br> Alternate Protocol Negotiation <br> Reserved <br> The values advertised in these bits must be consistent with the Modified TS Usage Mode Selected field of the 32.0 GT/s Control register and the capabilities of the device. These are bits[2:0] of Symbol 8. <br> Modified TS Information 1 <br> If Modified TS Usage $=001$ b or 010 b; else Reserved. |
| 10-11 | Training Set Message Vendor ID if Modified TS Usage $=001 b$. <br> Alternate Protocol Vendor ID if Modified TS Usage $=010 b$. <br> Reserved for other cases. |  |
| $12-14$ | If Modified TS Usage $=001 b$ or 010 b, Modified TS Information 2 <br> Else, Reserved |  |
| 15 | Bit-wise even parity of Symbols 4 through 14. <br> Symbol 15 = Symbol 4 ^ Symbol 5 ^ ... Symbol 14 |  |

Fields in the Modified TS1/TS2 Ordered Sets that extend over multiple Symbols use the little endian format using all the bits over those multiple Symbols. For example, Symbols 8 and 9 of the Modified TS1/TS2 comprise 16 bits. The Modified TS Usage field goes in bits [2:0] of Symbol 8 with the bit 0 of Modified TS Usage field placed in bit 0 of Symbol 8, bit 1 of Modified TS Usage field placed in bit 1 of Symbol 8, and bit 2 of Modified TS Usage field placed in bit 2 of Symbol 8. Similarly, bit 12 of the 13 bits of Modified TS Information 1 field is placed in bit 7 of Symbol 9 whereas bit 0 of Modified TS Information 1 is placed in bit 3 of Symbol 8.

Table 4-37 TS1/TS2 Ordered Set with 1b/1b Encoding

| Symbol <br> Numbers | Description |
| :--: | :--: |
| $0,8$ | TS1/TS2 Identifier - Unscrambled <br> - Encoded as 1Bh for TS1 <br> - Encoded as 39 h for TS2 |
| $1,9$ | - Link Number in Configuration, Hot Reset, or Recovery.RcvrCfg state - Scrambled <br> - 0-31, PAD (F7h) |

|  | TS1/TS2 Ordered Set with 1b/1b Encoding |  |
| :--: | :--: | :--: |
| Symbol <br> Numbers | Description |  |
|  | - As a Receiver in Recovery.Idle, this Byte is only used to check for PAD (F7h) <br> - Equalization Byte 0 in Recovery and Loopback for TS1 Ordered Set - Scrambled <br> Bits 1:0 Equalization Control (EC) - These bits are defined for use in Recovery. Equalization and Loopback. Entry. In all other Recovery substates these bits are 00b. In all other Loopback states, these bits are Reserved. |  |
|  | Bit 2 | Reset EIEOS Interval Count - This bit is defined for use in Recovery. Equalization. In all other Recovery substates, and in Loopback, this bit is Reserved. |
|  | Bits 6:3 | Transmitter Preset. These bits are defined for use in Recovery and Loopback. Entry See § Section 4.2.4.2, § Section 4.2.7.4, and § Section 4.2.7.10.1. In all other states these bits are Reserved. |
|  | Bit 7 | Use Preset/Equalization Redo - This bit is defined for use in Recovery. Equalization, Recovery.RcvrLock, and Loopback. Entry. See § Section 4.2.7.4.2, § Section 4.2.7.4.1, and § Section 4.2.7.10.1. In all other Recovery substates and Loopback substates, it is Reserved. |
|  | - Equalization Byte 0 in Recovery for TS2 Ordered Set - Scrambled Bit 0 |  |
|  | Bits 2:1 | Reserved |
|  | Bits 5:3 | Equalization Request Data Rate |
|  |  | 000b 8.0 GT/s |
|  |  | 001b 16.0 GT/s |
|  |  | 010b 32.0 GT/s |
|  |  | 011b 64.0 GT/s |
|  |  | Others Reserved |
|  |  | See § Section 4.2.4 for usage. |
|  | Bit 6 | Quiesce Guarantee |
|  | Bit 7 | Request Equalization |
|  | - Reserved in other states - Scrambled |  |
| 2,10 | - Lane Number in Configuration or Hot Reset state - Scrambled |  |
|  | - PAD is encoded as F7h |  |
|  | - As a Receiver in Recovery.Idle, this Byte is only used to check for PAD (F7h) |  |
|  | - Equalization Byte 1 in Recovery and Loopback. Entry - Scrambled |  |
|  | Bits 5:0 | Cursor $\left|C_{0}\right|$ for the current data rate of operation. |
|  | Bit 6 | Transmitter Precoding On (Recovery only, Reserved in Loopback. Entry) |
|  | Bit 7 | Retimer Equalization Extend bit (Recovery only, Reserved in Loopback. Entry) |
|  | - Reserved in other states - Scrambled |  |
| 3,11 | - Equalization Byte 2 in Recovery and Loopback. Entry for TS1 Ordered Sets, Reserved for TS2 Ordered Sets Scrambled |  |
|  | Bits 3:0 | First Pre-cursor Coefficient[3:0] $\left(\left[C_{-1}\right]\right)$ for the current data rate of operation |

|  | TS1/TS2 Ordered Set with 1b/1b Encoding |  |
| :--: | :--: | :--: |
| Symbol <br> Numbers | Description |  |
|  | Bits 6:4 <br> Bit 7 | Second Pre-cursor Coefficient[2:0] ([C-2]) for the current data rate of operation. <br> Reject Coefficient Values bit - This bit can only be set to 1 b in specific phases of the Recovery. Equalization LTSSM state. See § Section 4.2.7.4.2. In all other Recovery substates it must be set to 0 b. |
|  | - Reserved in other states - Scrambled |  |
| 4,12 | - Equalization Byte 3 in Recovery and Loopback. Entry for TS1 Ordered Sets, Reserved for TS2 Ordered Sets Scrambled <br> Bits 4:0 <br> Bits 7:5 | Post-cursor Coefficient[4:0] $\left\|\left(\mathrm{C}_{+1}\right)\right\|$ for the current data rate of operation. <br> Reserved |
|  | Data Rate Identifier - Scrambled |  |
|  | Bit 0 | Reserved |
|  | Bits 5:1 | Data Rates Supported |
|  |  | 0001b Only 2.5 GT/s supported |
|  |  | 00011b Only 2.5 and 5.0 GT/s supported |
|  |  | 00111b Only 2.5, 5.0, and 8.0 GT/s supported |
|  |  | 01111b Only 2.5, 5.0, 8.0, and 16.0 GT/s supported |
|  |  | 11111b Only 2.5, 5.0, 8.0, 16.0, and 32.0 GT/s supported |
| 5,13 |  | 2.5, 5.0, 8.0, 16.0, 32.0, and 64.0 GT/s supported |
|  |  | Others |
|  | Bit 6 | Autonomous Change / Selectable De-emphasis |
|  |  | Downstream Ports: This bit is defined for use in the following LTSSM states: <br> Configuration. Linkwidth. Start and Loopback. Entry for TS1 Ordered Sets, and Recovery for TS2 Ordered Sets. In all other states, it is Reserved. |
|  |  | Upstream Ports: This bit is defined for use in the following LTSSM states: Configuration, Recovery and Loopback. Entry. In all other states, it is Reserved. |
|  | Bit 7 | speed_change - This bit can be set to 1 b only in the Recovery LTSSM state. In all other LTSSM states, it is Reserved. |
| 6,14 | Training Control Used in Recovery.RcvrCfg to Disable, Hot Reset, or Loopback. Reserved for TS2 Ordered Sets in Configuration - Scrambled |  |
|  | Bits 3:0 | 0000b <br> 0001b <br> 0010b <br> 0100b | Deassert <br> Assert Hot_Reset_Request <br> Assert Disable_Link_Request <br> Assert Loopback_Request - the Follower Port at Receiver (A or F) loops back to its Transmitter |

| TS1/TS2 Ordered Set with 1b/1b Encoding |  |  |
| :--: | :--: | :--: |
| Symbol <br> Numbers | Description |  |
|  | 0101b | Assert Loopback_Request - the Pseudo-Port Receiver B or C loops back to its Transmitter, depending on which Port is the Loopback Lead (Follower Port still loops back except the Pseudo-Port that is acting as the Follower does not forward the bits) |
|  |  | What does "the bits" mean? |
|  | 0110b | Assert Loopback_Request - the Pseudo-Port Receiver D or E loops back to its Transmitter, depending on which Port is the Loopback Lead (Follower Port still loops back except the Pseudo-Port that is acting as the Follower does not forward the bits) |
|  |  | What does "the bits" mean? |
|  | 1000b | Assert Compliance_Receive_Request |
|  | 1100b | Assert Loopback_Request and Compliance_Receive_Request |
|  | Others | Reserved |
|  | Bits 7:4 | Reserved |
| 7,15 | If DC Balance needs adjustment at the start of the TS1 or TS2: DC Balance Symbol - Unscrambled |  |
|  | else: <br> Byte level even parity over | Symbols 0-6 (or 8-14) - Scrambled |
|  | Symbol 7 = Symbol 0 ^ Symbol 1 ^ ... Symbol 6 |  |
|  | Symbol 15 = Symbol 8 ^ Symbol 9 ^ ... Symbol 14 |  |
| Table 4-38 TS0 Ordered Set 9 |  |  |
| TS0 Ordered Set |  |  |
| Symbol Numbers | Description |  |
| 0,8 | TS0 Identifier - Unscrambled 33h |  |
|  | Bits 7,5,3,1 | 0101b |
|  | Bits 6,4,2,0 | Prior to Half Scrambling the bit values are don't care, but they will be identical to bits $\{7,5,3$, <br> 1) after Half Scrambling. |
| 1,9 | Equalization Byte 0 - Half Scrambled |  |
|  | Symbol 1 determines the interpretation of Symbols 2 through 6. Symbol 9 determines the interpretation of Symbols 10 through 14. |  |
|  | Bits 3,1 | Equalization Control (EC) |
|  |  | 00b Phase 0 (used during Phase 0 \& 1) |
|  |  | 01b Phase 1 (used during Phase 0 \& 1) |
|  |  | 10b Phase 2 (used during Phase 2 by Upstream Lane and by Downstream Lane only when initially requesting Upstream Lane to move to Phase 2) |
|  |  | 11b Phase 3 (only set by Upstream Lane initially when requesting Downstream Lane to move to Phase 3) |

| TSO Ordered Set |  |  |
| :--: | :--: | :--: |
| Symbol <br> Numbers | Description |  |
|  | The proper values must be sent during the corresponding phase of Recovery. Equalization. |  |
|  | Bit 5 | Reset EIEOS Interval Count - This bit is defined for use in Recovery. Equalization Phase 2. Reserved in all other states. |
|  |  | 0b <br> 1b <br> 0b <br> 1b <br> 0b <br> 0b <br> 1b <br> 1b <br> 0b <br> 1b <br> 0b <br> 0b <br> 1b <br> 0b <br> 0b <br> 0b <br> 0b <br> 0b <br> 0b <br> 0b <br> 0b <br> 0b <br> 0b <br> 0b <br> 0b <br> 0b <br> 0b <br> 0b <br> 0b <br> 0b <br> 0b <br> 0b <br> 0b <br> 0b <br> 0b <br> 0b <br> 0b <br> 0b <br> 0b <br> 0b | Reset EIEOS Interval Count <br> Reset EIEOS Interval Count <br> Use Preset <br> Use Preset <br> Prior to Half Scrambling the bit values are don't care, but they will be identical to bits (7, 5, 3, 1) after Half Scrambling. <br> Equalization Byte 1 - Half Scrambled <br> For the current data rate of operation. Interpretation depends on the EC field of Symbol 1 (or 9) <br> $\begin{aligned} & \text { Phases } 0 \& 1 \\ & \text { Phases } 2 \& 3 \\ & \text { Others } \\ & \text { Prior to Half Scrambled } \\ & \text { for } 2 \text { ( } 1 \text { ) } \\ & \text { Phases } 2 \& 3 \\ & \text { Phases } 2 \& 3 \\ & \text { Others } \\ & \text { For the current data rate of operation. Interpretation } \\ & \text { Phases } 0 \& 1 \\ & \text { Phases } 2 \& 3 \\ & \text { Others } \\ & \text { Prior to Half Scrambled } \\ & \text { for } 2 \text { ( } 1 \text { ) } \\ & \text { Phases } 0 \& 1 \\ & \text { Phases } 2 \& 3 \\ & \text { Phases } 0 \& 1 \\ & \text { Phases } 2 \& 3 \\ & \text { Others } \\ & \text { Prior to Half Scrambled } \\ & \text { for } 2 \text { ( } 1 \text { ) } \\ & \text { Phases } 0 \& 1 \\ & \text { Phases } 2 \& 3 \\ & \text { Phases } 2 \& 3 \\ & \text { Phases } 0 \& 1 \\ & \text { Phases } 2 \& 3 \\ & \text { Others } \\ & \text { Prior to Half Scrambled } \\ & \text { for } 2 \text { ( } 1 \text { ) } \\ & \text { Phases } 0 \& 1 \\ & \text { Phases } 2 \& 3 \\ & \text { Phases } 2 \& 3 \\ & \text { Phases } 0 \& 1 \\ & \text { For the current data rate of operation. Interpretation depends on the EC field of Symbol 1 (or 9) } \\ & \text { Phases } 0 \& 1 \\ & \text { Phases } 2 \& 3 \\ & \text { S11 } \\ & \text { Phases } 0 \& 1 \\ & \text { Phases } 2 \& 3 \\ & \text { Others } \\ & \text { For the current data rate of operation. Interpretation depends on the EC field of Symbol 1 (or 9) } \\ & \hline 4,12 & \text { Equalization Byte 3 - Half Scrambled } \\ & \text { For the current data rate of operation. Interpretation depends on the EC field of Symbol 1 (or 9) } \\ & \hline \end{aligned}$

| TSO Ordered Set |  |  |  |
| :--: | :--: | :--: | :--: |
| Symbol Numbers | Description |  |  |
|  | Bit 1 | Phases 0 \& 1 | LF[2] |
|  |  | Phases 2 \& 3 | Post-Cursor Coefficient[4] ( $\left.\mathrm{C}_{+1}\right)$ ) when Use Preset field of symbol 1,9 is 0 b |
|  |  | Others | Reserved |
|  | Bits 7,5,3 | Phases 0 \& 1 | LF[5:3] |
|  |  | Phases 2 \& 3 | Second Pre-Cursor Coefficient[2:0] ( $\left.\mathrm{C}_{-2}\right)$ ) when Use Preset field of symbol 1,9 is 0 b |
|  |  | Others | Reserved |
|  | Bits 6,4,2,0 | Prior to Half Scrambling the bit values are don't care, but they will be identical to bits (7, 5, 3, 1) after Half Scrambling. |  |
| 5,13 | Equalization Byte 4 - Half Scrambled |  |  |
|  | For the current data rate of operation. Interpretation depends on the EC and Use Preset fields of Symbol 1 (or 9) |  |  |
|  | Bit 7,5,3,1 | Phases 0 \& 1 | Transmitter Preset [3:0] |
|  |  | Phases 2 \& 3 | If Use Preset is 1b, Transmitter Preset [3:0], |
|  |  |  | Else |
|  |  |  | Cursor [3:0] ( $\left.\mathrm{C}_{0}\right)$ ) |
|  |  | Others | Reserved |
|  | Bits 6,4,2,0 | Prior to Half Scrambling the bit values are don't care, but they will be identical to bits (7, 5, 3, 1) after Half Scrambling. |  |
| 6,14 | Equalization Byte 5 - Half Scrambled |  |  |
|  | For the current data rate of operation. Interpretation depends on the EC field of Symbol 1 (or 9) |  |  |
|  | Bits 3,1 | Phases 2 \& 3 | Cursor [5:4] ( $\left.\mathrm{C}_{0}\right)$ ) when Use Preset field of symbol 1, 9 is 0 b |
|  |  | Others | Reserved |
|  | Bit 5 | Retimer Equalization Extend |  |
|  | Bit 7 | Reserved |  |
|  | Bits 6,4,2,0 | Prior to Half Scrambling the bit values are don't care, but they will be identical to bits (7, 5, 3, 1) after Half Scrambling. |  |
| 7,15 | If DC Balance adjustment needed at the start of the TSO: |  |  |
|  | 00 h or FFh - Unscrambled |  |  |
|  | Else: |  |  |
|  | Bits 7,5,3,1 | Byte level even parity - Half Scrambled |  |
|  |  | Symbol 7 = Symbol 0 ^ Symbol $1^{\wedge} \ldots$ Symbol 6 |  |
|  |  | Symbol 15 = Symbol 8 ^ Symbol 9 ^ ... Symbol 14 |  |
|  | Bits 6,4,2,0 | Prior to Half Scrambling the bit values are don't care, but they will be identical to bits (7, 5, 3, 1) after Half Scrambling. |  |

# 4.2.5.2 Alternate Protocol Negotiation 

In addition to the decision to skip equalization, alternate protocols are permitted to be negotiated during the Configuration.Lanenum.Wait, Configuration.Lanenum.Accept, and Configuration.Complete substates, while LinkUp=0b, through the exchange of Modified TS1/TS2 Ordered sets in the 8b/10b encoding. It is strongly recommended that a data rate of $32.0 \mathrm{GT} / \mathrm{s}$ or higher is advertised in all three substates throughout the entire alternate protocol negotiation procedure.

Alternate protocol(s) are permitted to be supported with PCIe PHY in 128b/130b or 1b/1b encodings. An alternate protocol is defined to be a non-PCIe protocol using the PCIe PHY layer. One may choose to run PCIe protocol in addition to one or multiple alternate protocols in the alternate protocol mode. The Ordered Set blocks are used as-is, along with the rules governing SKP Ordered Set insertion and the transition between Ordered Set and Data Blocks. The contents of the Data Blocks, however, may be modified according to the rules of the alternate protocol.

## IMPLEMENTATION NOTE: <br> ALTERNATE PROTOCOLS SHOULD HAVE AN EDS TOKEN EQUIVALENT 5

The EDS Token is used in PCI Express to indicate a switch from Data Blocks to Ordered Set blocks. This additional "redundant" information ensures that a random bit error in the 2 bit block header isn't incorrectly interpreted as the end of a data stream. This is one mechanism used by PCI Express to accomplish an undetected data error Hamming Distance of 4.

Alternate protocols should have an equivalent mechanism.

The following diagram represents the states where alternate protocol and equalization bypass negotiation occurs:

![img-60.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-60.jpeg)

Figure 4-64 Alternate Protocol Negotiation and Equalization Bypass LTSSM States

Downstream Ports manage Alternate Protocol Negotiation and Training Set Messages based on the value of the Modified TS Usage Mode Selected field when the Port is in Configuration.Lanenum.Wait, Configuration.Lanenum.Accept, and Configuration.Complete substates with LinkUp $=0$.

Upstream Ports must respond to unsupported Modified TS Usage values by transmitting Modified TS Usage 000b.
If Modified TS Usage Mode Selected is:

# 000b 

No Alternate Protocol Negotiation or Training Set Message occurs. The link will operate as a PCI Express Link.

## 001b

Training Set Messages are enabled. Modified TS Information 1 and Modified TS Information 2 fields carry the vendor specific messages defined by the Training Set Message Vendor ID field.

## 010b

Alternate Protocol Negotiation is enabled. Modified TS Information 1 and Modified TS Information 2 fields carry the alternate protocol details defined by the Alternate Protocol Vendor ID field. A protocol request or response is associated with the protocol defined by the Alternate Protocol Vendor ID field.

The Alternate Protocol Negotiation Status field indicates the progress of the negotiation protocol.

## others

Reserved

A Downstream Port that supports Alternate Protocol Negotiation will start the negotiation process when it first enters Configuration.Lanenum.Wait, LinkUp = 0, and Modified TS Usage Mode Selected field is 010b. Starting negotiation consists of sending Modified TS1/TS2 Ordered Sets with Modified TS Usage = 010b.

Table 4-39 Modified TS Information 1 field in Modified TS1/TS2 Ordered Sets if Modified TS Usage = 010b (Alternate Protocol)

| Bits | Field | Description |  |  |
| :--: | :--: | :--: | :--: | :--: |
| 4:3 | Alternate Protocol Negotiation Status | For Modified TS1 Ordered Sets: <br> 00b DSP <br> USP <br> 01b DSP <br> USP <br> 01b DSP <br> USP <br> 10b DSP <br> USP <br> 11b <br> 11b | Indicates a protocol request from the Downstream Port asking whether the Upstream Port supports a particular alternate protocol. Indicates that the Upstream Port does not have an answer for a protocol request yet. This occurs either when it is evaluating the protocol request or it has not received two consecutive Modified TS1s to perform the evaluation. In the former case, Alternate Protocol Vendor ID and Alternate Protocol Details reflect what it received, while Modified TS Information 2 is protocol specific. In the latter case, all 3 fields must be 0 . Reserved Indicates that the Upstream Port does not support the requested protocol. Alternate Protocol Vendor ID and Alternate Protocol Details reflect what it received. Modified TS Information 2 must be all 0 s. Reserved Indicates that the Upstream Port supports the requested protocol. Alternate Protocol Vendor ID and Alternate Protocol Details reflect what it received, while Modified TS Information 2 field is protocol specific. Reserved <br> 00b Indicates a protocol confirmation from the Downstream Port as well as the Upstream Port. Behavior is undefined if the Downstream Port had not earlier received status 10b for this protocol in this instance of protocol negotiation during the Modified TS1 Ordered Sets. Similarly, behavior is undefined if the Upstream Port had not earlier transmitted status 10b for this protocol in this instance of protocol negotiation during the Modified TS1 Ordered Sets. <br> No protocol is selected unless the Downstream Port sends and receives a protocol confirmation in the Modified TS2 Ordered Sets. If the Downstream Port decides not to use any Alternate Protocol, it must indicate this by transmitting Modified TS2 Ordered Set with Modified TS Usage of 000 b or 001 b . Reserved <br> 11b <br> Alternate Protocol Details is Modified TS Usage = 010b. |
|  |  |  |  |

If Modified TS Usage = 001b, then Modified TS Information 1 and Modified TS Information 2 contain details of the training set messages.

Alternate Protocol Negotiation must be concurrent with the Lane number negotiation. During Alternate Protocol Negotiation, the Downstream Port requests support for one or more Alternate Protocols by sending a series of Modified TS1 Ordered Sets requesting each protocol, evaluating the resulting Modified TS1 Ordered Sets, and determining the resulting protocol prior to transitioning to the Configuration.Complete substate.

Upstream Ports where Modified TS Usage Mode 2 Supported - Alternate Protocol is Set, must respond to one or more Alternate Protocol requests from the Downstream Port with Modified TS1 Ordered Sets as per § Table 4-39. Upstream Ports where Modified TS Usage Mode 2 Supported - Alternate Protocol is Clear, must respond to Alternate Protocol requests from the Downstream Port with Modified TS1 Ordered Sets with the Modified TS Usage other than 010b.

It is permitted for a Downstream Port to fall back to PCle protocol if it does not determine a supported alternate protocol. It is permitted for a Downstream Port to discontinue negotiation when it has determined a protocol to select (e.g., if A Downstream Port supports protocols $A$ and $B$ and receives a supported indication for protocol $A$, it is permitted that the Downstream Port chose protocol A without asking about support for protocol B). On a successful negotiation to alternate protocol, the Link moves to L0 at $2.5 \mathrm{GT} / \mathrm{s}$, changes the data rate to the higher data rates, performing equalization, if needed and enters L0 at the highest data rate desired. After transmitting the SDS Ordered Set in the highest data rate after equalization has been performed, the Data Blocks will carry the alternate protocol and the Link will be under the control of the alternate protocol.

If the DSP goes through Detect, it is permitted to remember which protocols were discovered prior to Detect. However, this does not circumvent the requirement for the complete alternate protocol negotiation to be performed in order to arrive at a common protocol (as described in above).

# IMPLEMENTATION NOTE: 

## ALTERNATE PROTOCOL NEGOTIATION BEFORE PCIE BASE 6.2

Some pre-6.2 USP may support an alternate protocol, in addition to PCle, but not implement the one advanced protocol at a time mechanism. There may also be cases where the 1 msec wait after the matching Lane number in Configuration.Lanenum.Wait / Configuration.Lanenum.Accept sub-states may cause an early transition before arriving at a common alternate protocol by both Ports. In these cases, it is recommended that the DSP either uses an implementation specific means to start with the common supported alternate protocol or to go through Detect and negotiate with a new set of alternate protocols it did not try in the prior unsuccessful attempts.

### 4.2.5.3 Electrical Idle Sequences (EIOS and EIEOS)

Before a Transmitter enters Electrical Idle, it must always send an Electrical Idle Ordered Set Sequence (EIOSQ), unless otherwise specified. An Electrical Idle Ordered Set Sequence (EIOSQ) is defined as one EIOS if the current Data Rate is $2.5 \mathrm{GT} / \mathrm{s}, 8.0 \mathrm{GT} / \mathrm{s}, 16.0 \mathrm{GT} / \mathrm{s}, 32.0 \mathrm{GT} / \mathrm{s}$, or $64.0 \mathrm{GT} / \mathrm{s}$ Data Rate, or two consecutive EIOSs if the current Data Rate is $5.0 \mathrm{GT} /$ s.

When using 8b/10b encoding, an EIOS is a K28.5 (COM) followed by three K28.3 (IDL) Symbols. Transmitters must transmit all Symbols of an EIOS. An EIOS is received when the COM and two of the three IDL Symbols are received. When using 128b/130b encoding, an EIOS is an Ordered Set block, as defined in § Table 4-41. When using 1b/1b encoding, an EIOS is an Ordered Set block, as defined in § Table 4-42. Transmitters must transmit all Symbols of an EIOS if additional EIOSs are to be transmitted following it. Transmitters must transmit Symbols 0-13 of an EIOS, but are permitted to terminate the EIOS anywhere in Symbols 14 or 15, when transitioning to Electrical Idle after it. An EIOS is considered received when Symbols 0-3 of an Ordered Set Block match the definition of an EIOS if the data rate is less than $64.0 \mathrm{GT} / \mathrm{s}$. At $64.0 \mathrm{GT} / \mathrm{s}$, the rules governing receipt of an EIOS appears in $\S$ Section 4.2.3.1.5.

# IMPLEMENTATION NOTE: TRUNCATION OF EIOS ORDERED SET 

Truncation in the last EIOS is allowed to help implementations where a transmitter may terminate on an internal clock boundary that may not align on a Symbol boundary due to 128b/130b encoding. Truncation is okay since Receivers will just look at the first four Symbols to conclude it is an EIOS.

After transmitting the last Symbol of the last Electrical Idle Ordered Set, the Transmitter must be in a valid Electrical Idle state as specified by $T_{\text {TX-IDLE-SET-TO-IDLE }}$ (see § Table 8-7).

Table 4-40 Electrical Idle Ordered Set (EIOS) for 2.5 GT/s and 5.0 GT/s Data Rates

| Symbol Number | Encoded Values | Description |
| :--: | :--: | :--: |
| 0 | K28.5 | COM for Symbol alignment |
| 1 | K28.3 | IDL |
| 2 | K28.3 | IDL |
| 3 | K28.3 | IDL |

Table 4-41 Electrical Idle Ordered Set (EIOS) for 128b/ 130b Encoding

| Symbol Numbers | Value | Description |
| :--: | :--: | :--: |
| $0-15$ | 66 h | EIOS Identifier and Payload |

Table 4-42 Electrical Idle Ordered Set (EIOS) for 1b/1b Encoding

| Symbol Numbers | Value | Description |
| :--: | :--: | :--: |
| $0,2,4,6,8,10,12,14$ | 0 Fh | EIOS Identifier and Payload |
| $1,3,5,7,9,11,13,15$ | F0h | EIOS Identifier and Payload |

Table 4-43 Electrical Idle Exit Ordered Set (EIEOS) for 5.0 GT/s Data Rate

| Symbol Number | Encoded Values | Description |
| :--: | :--: | :-- |
| 0 | K28.5 | COM for Symbol alignment |
| $1-14$ | K28.7 | EIE - K Symbol with low frequency components for helping achieve exit from Electrical Idle |
| 15 | D10.2 | TS1 Identifier (See Note 1) |

Notes:

1. This symbol is not scrambled. Previous versions of this specification were less clear and some implementations may have incorrectly scrambled this symbol. It is recommended that devices be tolerant of receiving EIEOS in which this symbol is scrambled.

Table 4-44 Electrical Idle Exit Ordered Set (EIEOS) for 8.0 GT/s Data Rate

| Symbol Numbers | Value | Description |
| :--: | :--: | :--: |
| $0,2,4,6,8,10,12,14$ | 00 h | Symbol 0: EIEOS Identifier <br> A low frequency pattern that alternates between eight 0 s and eight 1 s. |
| $1,3,5,7,9,11,13,15$ | FFh | A low frequency pattern that alternates between eight 0 s and eight 1 s . |
| Table 4-45 Electrical Idle Exit Ordered Set (EIEOS) for 16.0 GT/s Data Rate |  |  |
| Symbol Numbers | Value | Description |
| $0,1,4,5,8,9,12,13$ | 00 h | Symbol 0: EIEOS Identifier <br> A low frequency pattern that alternates between sixteen 0 s and sixteen 1 s. |
| $2,3,6,7,10,11,14,15$ | FFh | A low frequency pattern that alternates between sixteen 0 s and sixteen 1 s . |
| Table 4-46 Electrical Idle Exit Ordered Set (EIEOS) for 32.0 GT/s Data Rate |  |  |
| Symbol Numbers | Value | Description |
| $0,1,2,3,8,9,10,11$ | 00 h | Symbol 0: EIEOS Identifier <br> A low frequency pattern that alternates between thirty-two 0 s and thirty-two 1 s. |
| $4,5,6,7,12,13,14,15$ | FFh | A low frequency pattern that alternates between thirty-two 0 s and thirty-two 1 s . |

Table 4-47 Electrical Idle Exit Ordered Set (EIEOS)
for 64.0 GT/s Data Rate

| Symbol Numbers | Value | Description |
| :--: | :--: | :--: |
| $0-7$ | 00 h | Voltage level 0 for 32 UI |
| $8-15$ | FFh | Voltage level 3 for 32 UI |

![img-61.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-61.jpeg)
(Electrical Idle Exit Ordered Set at 8.0 GT/s Data Rate)
![img-62.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-62.jpeg)
(Electrical Idle Exit Ordered Set at 16.0 GT/s Data Rate)
![img-63.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-63.jpeg)

Figure 4-65 Electrical Idle Exit Ordered Set for 8.0 GT/s to 32.0 GT/s Data Rates (EIEOS)

The Electrical Idle Exit Ordered Set (EIEOS) is transmitted only when operating at speeds other than $2.5 \mathrm{GT} / \mathrm{s}$. It is a low frequency pattern transmitted periodically to help ensure that Receiver Electrical Idle exit detection circuitry can detect an exit from Electrical Idle. When using 128b/130b encoding, it is also used for Block Alignment as described in $\S$ Section 4.2.2.2.1 .

An Electrical Idle Exit Ordered Set Sequence (EIEOSQ) comprises of two consecutive EIEOS for the Data Rate of $32.0 \mathrm{GT} / \mathrm{s}$ and one EIEOS for $5.0 \mathrm{GT} / \mathrm{s}, 8.0 \mathrm{GT} / \mathrm{s}$, and $16.0 \mathrm{GT} / \mathrm{s}$. The two EIEOS at $32.0 \mathrm{GT} / \mathrm{s}$ must be back to back and uninterrupted in order to be considered consecutive and form an EIEOSQ. Irrespective of the length of the EIEOSQ, block alignment still occurs on an EIEOS.

At the Data Rate of $64.0 \mathrm{GT} / \mathrm{s}$, an EIEOSQ is defined as follows:

- On entry to Recovery.RcvrLock either from Recovery.Speed or from L1, until either the Receiver detects exit Electrical Idle on all Lanes or it receives two consecutive valid TS1 Ordered Sets on any Lane:
- Four consecutive EIEOS, uninterrupted by any other Ordered Set including the Control SKP Ordered Set
- While increasing Link Width with L0p till the Receiver detects exit Electrical Idle on all Lanes that need to be activated or receives two consecutive valid TS1 Ordered Sets on any Lane that needs to be activated:
- Four consecutive EIEOS, uninterrupted by any other Ordered Set including the Control SKP Ordered Set
- On entry to the Loopback state from electrical idle till the Receiver detects exit Electrical Idle on all Lanes that need to be activated or receives two consecutive valid TS1 Ordered Sets on any Lane:
- Four consecutive EIEOS, uninterrupted by any other Ordered Set including the Control SKP Ordered Set
- While transmitting Compliance Patterns or Modified Compliance Patterns:
- One EIEOS
- Else one EIEOS

When using 8b/10b encoding and operating at $5.0 \mathrm{GT} / \mathrm{s}$, an EIEOSQ, as defined in § Table 4-43, is transmitted in the following situations:

- Before the first TS1 Ordered Set after entering the LTSSM Configuration.Linkwidth.Start state.
- Before the first TS1 Ordered Set after entering the LTSSM Recovery.RcvrLock state.
- After every 32 TS1 or TS2 Ordered Sets are transmitted in the LTSSM Configuration.Linkwidth.Start, Recovery.RcvrLock, and Recovery.RcvrCfg states. The TS1/TS2 count is set to 0 when:
- An EIEOS is transmitted.
- The first TS2 Ordered Set is received while in the LTSSM Recovery.RcvrCfg state.

When using 128b/130b encoding, an EIEOSQ, as defined in § Table 4-44 through § Table 4-46 and § Figure 4-65, is transmitted in the following situations:

- Before the first TS1 Ordered Set after entering the LTSSM Configuration.Linkwidth.Start substate.
- Before the first TS1 Ordered Set after entering the LTSSM Recovery.RcvrLock substate.
- Immediately following an EDS Framing Token in Non-Flit Mode when ending a Data Stream and not transmitting an EIOS and not entering the LTSSM Recovery.RcvrLock substate.
- At the scheduled Ordered Set interval to end a Data Stream in Flit Mode.
- After every 32 TS1 or TS2 Ordered Sets are transmitted in all LTSSM states which require transmission of TS1 or TS2 Ordered Sets. The TS1/TS2 count is set to 0 when:
- An EIEOS is transmitted.
- The first TS2 Ordered Set is received while in the LTSSM Recovery.RcvrCfg state.
- The first TS2 Ordered Set is received while in the LTSSM Configuration.Complete state.
- A Downstream Port is in Phase 2 of the LTSSM Recovery. Equalization state and two consecutive TS1 Ordered Sets are received on any Lane with the Reset EIEOS Interval Count bit set.
- An Upstream Port is in Phase 3 of the LTSSM Recovery. Equalization state and two consecutive TS1 Ordered Sets are received on any Lane with the Reset EIEOS Interval Count bit set.
- After every 65,536 TS1 Ordered Sets are transmitted in the LTSSM Recovery. Equalization state if the Reset EIEOS Interval Count bit has prevented it from being transmitted for that interval. Implementations are permitted to

satisfy this requirement by transmitting an EIEOSQ within two TS1 Ordered Sets of whenever the current scrambling LFSR matches its seed value.

- As part of an FTS Ordered Set, Compliance Pattern, or Modified Compliance Pattern as described in the relevant sections.

When using 1b/1b encoding, an EIEOSQ, as defined in § Table 4-47 is transmitted in the following situations:

- Before the first TS1 Ordered Set after entering the LTSSM Configuration.Linkwidth.Start substate.
- Before the first TS1 Ordered Set after entering the LTSSM Recovery.RcvrLock substate.
- Before the first TS0 Ordered Set after entering Recovery. Equalization substate.
- At the scheduled Ordered Set interval to indicate the end of the Data Stream.
- After every 32 TS1, TS2, or TS0 Ordered Sets are transmitted in all LTSSM states which require transmission of TS1, TS2, or TS0 Ordered Sets. The TS1/TS2/TS0 count is set to 0 when:
- An EIEOS is transmitted.
- The first TS2 Ordered Set is received while in the LTSSM Recovery.RcvrCfg state.
- The first TS2 Ordered Set is received while in the LTSSM Configuration.Complete state.
- The first TS1 Ordered Set is received while in the LTSSM Recovery. Equalization state if the TS1 Ordered Set is received after TS0 Ordered Sets.
- A Downstream Port is in Phase 2 of the LTSSM Recovery. Equalization state and two consecutive TS0 Ordered Sets are received on any Lane with the Reset EIEOS Interval Count bit set.
- An Upstream Port is in Phase 3 of the LTSSM Recovery. Equalization state and two consecutive TS1 Ordered Sets are received on any Lane with the Reset EIEOS Interval Count bit set.
- After every 65,536 TS1 Ordered Sets are transmitted in the LTSSM Recovery. Equalization state if the Reset EIEOS Interval Count bit has prevented it from being transmitted for that interval. Implementations are permitted to satisfy this requirement by transmitting an EIEOSQ within two TS1 Ordered Sets of whenever the current scrambling LFSR matches its seed value.
- As part of a Compliance Pattern, or Modified Compliance Pattern as described in the relevant sections.

Example: An LTSSM enters Recovery.RcvrLock from L0 in 5.0 GT/s data rate. It transmits an EIEOS followed by TS1 Ordered Sets. It transmits 32 TS1 Ordered Sets following which it transmits the second EIEOS. Subsequently it sends two more TS1 Ordered Sets and enters Recovery.RcvrCfg where it transmits the third EIEOS after transmitting 30 TS2 Ordered Sets. It transmits 31 more TS2 Ordered Sets (after the first 30 TS2 Ordered Sets) in Recovery.RcvrCfg when it receives a TS2 Ordered Set. Since it receives its first TS2 Ordered Set, it will reset its EIEOS interval count to 0 and keep transmitting another 16 TS2 Ordered Sets before transitioning to Recovery. Idle. Thus, it did not send an EIEOS in the midst of the last 47 TS2 Ordered Sets since the EIEOS interval count got reset to 0 . From Recovery. Idle, the LTSSM transitions to Configuration.Linkwidth.Start and transmits an EIEOS after which it starts transmitting the TS1 Ordered Sets.

While operating in speeds other than $2.5 \mathrm{GT} / \mathrm{s}$, an implementation is permitted to not rely on the output of the Electrical Idle detection circuitry except when receiving the EIEOS during certain LTSSM states or during the receipt of the FTS prepended by the four consecutive EIE Symbols (see § Section 4.2.5.6) at the Receiver during Rx L0s or the Modified Compliance Pattern in Polling.Compliance when the circuitry is required to signal an exit from Electrical Idle.

# 4.2.5.4 Inferring Electrical Idle 

A device is permitted in all speeds of operation to infer Electrical Idle instead of detecting Electrical Idle using analog circuitry. § Table 4-48 summarizes the conditions to infer Electrical Idle in the various substates.

Table 4-48 Electrical Idle Inference Conditions

| State | $2.5 \mathrm{GT} / \mathrm{s}$ | $5.0 \mathrm{GT} / \mathrm{s}$ | $8.0 \mathrm{GT} / \mathrm{s}$ and higher data rates |
| :--: | :--: | :--: | :--: |
| L0 | Absence of at least one of: <br> - an UpdateFC DLLP, <br> - an Optimized_Update_FC (in Flit Mode), or <br> - a SKP Ordered Set <br> in a $128 \mu \mathrm{~s}$ window |  |  |
| Recovery.RcvrCfg | Absence of a TS1 or TS2 Ordered Set in a 1280 UI interval |  | Absence of a TS1 or TS2 Ordered Set in a 4 ms window |
| Recovery.Speed when successful_speed_negotiation $=1 b$ | Absence of a TS1 or TS2 Ordered Set in a 1280 UI interval |  | Absence of a TS1 or TS2 Ordered Set in a 4680 UI interval |
| Recovery.Speed when successful_speed_negotiation $=0 b$ | Absence of an exit from Electrical Idle in a 2000 UI interval |  | Absence of an exit from Electrical Idle in a 16000 UI interval |
| Loopback.Active (as Follower) | Absence of an exit from Electrical Idle in a 128 us window | N/A | N/A |

The Electrical Idle exit condition must not be determined based on inference of Electrical Idle condition. For area efficiency, an implementation is permitted to choose to implement a common timeout counter per LTSSM and look for the Electrical Idle inference condition within the common timeout window determined by the common counter for each of the Lanes the LTSSM controls instead of having a timeout counter per Lane.

# IMPLEMENTATION NOTE: INFERENCE OF ELECTRICAL IDLE 6 

In the L0 state, one or more Flow Control Update DLLPs are expected to be received in a $128 \mu \mathrm{~s}$ window. Also in L0, one or more SKP Ordered Sets are expected to be received in a $128 \mu \mathrm{~s}$ window. As a simplification, it is permitted to use either one (or both) of these indicators to infer Electrical Idle. Hence, the absence of a Flow Control Update DLLP and/or a SKP Ordered Set in any $128 \mu \mathrm{~s}$ window can be inferred as Electrical Idle. In Recovery.RcvrCfg as well as Recovery.Speed with successful speed negotiation, the Receiver should receive TS1 or TS2 Ordered Sets continuously with the exception of the EIEOS and the SKP Ordered Set. Hence, the absence of a TS1 or TS2 Ordered Set in the interval specified above must be treated as Electrical Idle for components that implement the inference mechanism. In the event that the device enters Recovery.Speed with successful_speed_negotiation $=0 \mathrm{~b}$, there is a possibility that the device had failed to receive Symbols. Hence, the Electrical Idle inference is done as an absence of exit from Electrical Idle. In data rates other than $2.5 \mathrm{GT} / \mathrm{s}$, Electrical Idle exit is guaranteed only on receipt of an EIEOS. Hence, the window is set to 16000 UI for detecting an exit from Electrical Idle in $5.0 \mathrm{GT} / \mathrm{s}$ and above data rates. In $2.5 \mathrm{GT} / \mathrm{s}$ data rate, Electrical Idle exit must be detected with every Symbol received. Hence, absence of Electrical Idle exit in a 2000 UI window constitutes an Electrical Idle condition.

### 4.2.5.5 Lane Polarity Inversion

During the training sequence in Polling, the Receiver looks at Symbols 6-15 of the TS1 and TS2 Ordered Sets as the indicator of Lane polarity inversion (D+ and D- are swapped). If Lane polarity inversion occurs, the TS1 Symbols 6-15

received will be D21.5 as opposed to the expected D10.2. Similarly, if Lane polarity inversion occurs, Symbols 6-15 of the TS2 Ordered Set will be D26.5 as opposed to the expected D5.2. This provides the clear indication of Lane polarity inversion.

If polarity inversion is detected the Receiver must invert the received data. The Transmitter must never invert the transmitted data. Support for Lane Polarity Inversion is required on all PCI Express Receivers across all Lanes independently.

# 4.2.5.6 Fast Training Sequence (FTS) 

Fast Training Sequence (FTS) is the mechanism that is used for bit and Symbol lock when transitioning from L0s to L0. The FTS is used by the Receiver to detect the exit from Electrical Idle and align the Receiver's bit and Symbol receive circuitry to the incoming data. Refer to $\S$ Section 4.2 .6 for a description of L0 and L0s.

- At 2.5 GT/s and 5.0 GT/s data rates:

A single FTS is comprised of one K28.5 (COM) Symbol followed by three K28.1 Symbols. The maximum number of FTSs ( $\overline{\mathrm{N}}_{\mathrm{n}}$ FTS) that a component can request is 255 , providing a bit time lock of $4^{*} 255^{*} 10^{*}$ UI. If the data rate is $5.0 \mathrm{GT} / \mathrm{s}$, four consecutive EIE Symbols are transmitted at valid signal levels prior to transmitting the first FTS. These Symbols will help the Receiver detect exit from Electrical Idle. An implementation that does not guarantee proper signaling levels for up to the allowable time on the Transmitter pins (see $\S$ Section 4.2.5.6) since exiting Electrical Idle condition is required to prepend its first FTS by extra EIE Symbols so that the Receiver can receive at least four EIE Symbols at valid signal levels. Implementations must not transmit more than eight EIE Symbols prior to transmitting the first FTS. A component is permitted to advertise different N_FTS rates at different speeds. At $5.0 \mathrm{GT} / \mathrm{s}$, a component may choose to advertise an appropriate N_FTS number considering that it will receive the four EIE Symbols. 4096 FTSs must be sent when the Extended Synch bit is Set in order to provide external Link monitoring tools with enough time to achieve bit and framing synchronization. SKP Ordered Sets must be scheduled and transmitted between FTSs as necessary to meet the definitions in $\S$ Section 4.2 .8 with the exception that no SKP Ordered Sets can be transmitted during the first N_FTS FTSs. A single SKP Ordered Set is always sent after the last FTS is transmitted. It is permitted for this SKP Ordered Set to affect or not affect the scheduling of subsequent SKP Ordered Sets for Clock Tolerance Compensation by the Transmitter as described in $\S$ Section 4.2.8. Note that it is possible that two SKP Ordered Sets can be transmitted back to back (one SKP Ordered Set to signify the completion of the 4096 FTSs and one scheduled and transmitted to meet the definitions described in $\S$ Section 4.2.8).

- At 8.0 GT/s, 16.0 GT/s, or 32.0 GT/s data rates:

A single FTS is a 130-bit unscrambled Ordered Set Block, as shown in § Table 4-49. The maximum number of FTSs (N_FTS) that a component can request is 255 , providing a bit time lock of $130^{*} 255$ UI ( $130^{*} 263$ or 273 UI if including the periodic EIEOS). A component is permitted to advertise different N_FTS values at different speeds. On exit from LOs, the transmitter first transmits an EIEOSQ which will help the Receiver detect exit from Electrical Idle due to its low frequency content. After that first EIEOSQ, the transmitter must send the required number of FTS (4096 when the Extended Synch bit is Set; otherwise N_FTS), with an EIEOSQ transmitted after every 32 FTS. The FTS sequence will enable the Receiver obtain bit lock (and optionally to do Block alignment). When the Extended Synch bit is Set, SKP Ordered Sets must be scheduled and transmitted between FTSs and EIEOSQ as necessary to meet the definitions in $\S$ Section 4.2.8. The last FTS Ordered Set of the FTS sequence, if any (no FTS Ordered Sets are sent if N_FTS is equal to zero), is followed by a final EIEOSQ that will help the Receiver acquire Block alignment. Implementations are permitted to send two EIEOS back to back even at a data rate below $32.0 \mathrm{GT} / \mathrm{s}$ following the last FTS Ordered Set if the N_FTS is a multiple of 32 . The EIEOS resets the scrambler in both the Transmitter as well as the Receiver. Following the final EIEOSQ, an SDS Ordered Set is transmitted to help the Receiver perform de-skew and to indicate the transition from Ordered Sets to Data Stream. After the SDS Ordered Set is transmitted, a Data Block must be transmitted.

# IMPLEMENTATION NOTE: 

## SCRAMBLING LFSR DURING FTS TRANSMISSION IN 128B/ 130B ENCODING

Since the scrambler is reset on the last EIEOS, and none of the Ordered Set in the FTS sequence is scrambled, it does not matter whether implementations choose to advance the scrambler or not during the time FTS is received.

Table 4-49 FTS for
8.0 GT/s and Above Data

|  | Rates |
| :--: | :--: |
| Symbol Number | Value |
| 0 | 55 h |
| 1 | 47 h |
| 2 | 4 Eh |
| 3 | C7h |
| 4 | C Ch |
| 5 | C 6 h |
| 6 | C9h |
| 7 | 25 h |
| 8 | 6 Eh |
| 9 | ECh |
| 10 | 88 h |
| 11 | 7 Fh |
| 12 | 80 h |
| 13 | 8 Dh |
| 14 | 8 Bh |
| 15 | 8 Eh |

N_FTS defines the number of FTSs that must be transmitted when transitioning from LOs to L0. At the $2.5 \mathrm{GT} / \mathrm{s}$ data rate, the value that can be requested by a component corresponds to a Symbol lock time of 16 ns (N_FTS set to 0 b and one SKP Ordered Set) to $\sim 4 \mu \mathrm{~s}$ (N_FTS set to 255), except when the Extended Synch bit is Set, which requires the transmission of 4096 FTSs resulting in a bit lock time of $64 \mu \mathrm{~s}$. For $8.0 \mathrm{GT} / \mathrm{s}$ and above data rates, when the Extended Synch bit is Set, the transmitter is required to send 4096 FTS Ordered Set Blocks. Note that the N_FTS value reported by a component may change; for example, due to software modifying the value in the Common Clock Configuration bit (see $\S$ Section 7.5.3.7).

If the N_FTS period of time expires before the Receiver obtains bit lock, Symbol lock or Block alignment, and Lane-to-Lane de-skew on all Lanes of the configured Link, the Receiver must transition to the Recovery state. This sequence is detailed in the LTSSM in § Section 4.2.6.

# 4.2.5.7 Start of Data Stream Ordered Set (SDS Ordered Set) 

The Start of Data Stream (SDS) Ordered Set, described in § Table 4-50, § Table 4-51, and § Table 4-52 is defined only for 128b/130b encoding and 1b/1b encoding. It is transmitted in the Configuration. Idle, Recovery. Idle, and Tx_LOs.FTS LTSSM states to define the transition from Ordered Set Blocks to a Data Stream, and Loopback Leads are permitted to transmit it as described in § Section 4.2.2.6. It must not be transmitted at any other time. While not in the Loopback state, the Block following an SDS Ordered Set must be a Data Block in Non-Flit Mode, and the first Symbol of that Data Block is the first Symbol of the Data Stream. In 1b/1b encoding, the Transmitter must send two back to back SDS when the conditions to send an SDS are met. The SDS Ordered Set in 1b/1b encoding must be on an aligned 128b (16B) boundary. An SDS Ordered Set sequence refers to either the single SDS Ordered set with 128b/130b encoding or the two back to back SDS Ordered Sets with 1b/1b encoding. In Flit Mode, with 128b/130b encoding and 1b/1b encoding, a Control SKP Ordered Set must be sent after the SDS Ordered Set. The first Symbol of the Data Stream starts immediately after the Control SKP Ordered Set. With 1b/1b encoding, a Receiver considers an SDS sequence valid if four good B1_C6_C6_C6 (4B) sets are received, at least two of which are in an even 4 byte aligned position (i.e., bytes 0-3, 8-11).

Table 4-50 SDS Ordered Set (for 8.0 GT/s and 16.0 GT/s Data Rate)

| Symbol Number | Value | Description |
| :--: | :--: | :--: |
| 0 | E1h | SDS Ordered Set Identifier |
| $1-15$ | 55 h | Body of SDS Ordered Set |
| Table 4-51 SDS Ordered Set (for 32.0 GT/s) |  |  |
| Symbol Number | Value | Description |
| 0 | E1h | SDS Ordered Set Identifier |
| $1-15$ | 87 h | Body of SDS Ordered Set |
| Table 4-52 SDS Ordered Set (for 64.0 GT/s) |  |  |
| Symbol Number | Value | Description |
| $0,4,8,12$ | B1h | SDS Ordered Set Identifier |
| $1-3,5-7,9-11,13-15$ | C6h | Body of SDS Ordered Set |

### 4.2.5.8 Link Error Recovery

- Link Errors, when operating with 8b/10b encoding are:
- 8b/10b decode errors, Non-Flit Mode framing related errors defined in § Section 4.2.1.2.1, loss of Symbol lock, Elasticity Buffer Overflow/Underflow, or loss of Lane-to-Lane de-skew.
- 8b/10b decode errors must be checked and must trigger a Receiver Error in specified LTSSM states (see § Table 4-58), which is a reported error associated with the Port (see § Section 6.2 ). Triggering a Receiver Error on any or all of Non-Flit Mode framing related errors defined in § Section 4.2.1.2.1, loss of Symbol Lock, Lane De-skew Error, and Elasticity Buffer Overflow/Underflow is optional.
- Link Errors, when operating with 128b/130b encoding, are:

- Framing Errors, loss of Block Alignment, Elasticity Buffer Overflow/Underflow, or loss of Lane-to-Lane de-skew.
- Framing errors must be checked and trigger a Receiver Error in the LTSSM states specified in § Table 4-58. The Receiver Error is a reported error associated with the Port (see § Section 6.2 ). Triggering a Receiver Error on any of all of loss of Block Alignment, Elasticity Buffer Overflow/Underflow, and loss of Lane-to-Lane de-skew is optional.
- Link Errors, when operating with 1b/1b encoding, are:
- Framing Errors, Elasticity Buffer Overflow/Underflow, or loss of Lane-to-Lane de-skew.
- Framing errors must be checked and trigger a Receiver Error in the LTSSM states specified in § Table 4-58. The Receiver Error is a reported error associated with the Port (see § Section 6.2 ). Triggering a Receiver Error on any of all of Elasticity Buffer Overflow/Underflow, and loss of Lane-to-Lane de-skew is optional.
- On a configured Link, which is in LO, error recovery will at a minimum be managed in a Layer above the Physical Layer (as described in § Section 3.6 ) by directing the Link to transition to Recovery.
- Note: Link Errors may also result in the Physical Layer initiating an LTSSM state transition from LO to Recovery.
- All LTSSM states other than LO make progress ${ }^{78}$ when Link Errors occur.
- When operating with 8b/10b encoding, Link Errors that occur in LTSSM states other than LO must not result in the Physical Layer initiating an LTSSM state transition.
- When operating with 128b/130b encoding and not processing a Data Stream, Link Errors that occur in LTSSM states other than LO must not result in the Physical Layer initiating an LTSSM state transition.
- When operating with 8b/10b encoding, if a Lane detects an implementation specific number of 8b/10b errors, Symbol lock must be verified or re-established as soon as possible. ${ }^{79}$


# 4.2.5.9 Reset 

Reset is described from a system point of view in § Section 6.6 .

### 4.2.5.9.1 Fundamental Reset

When Fundamental Reset is asserted:

- The Receiver terminations are required to meet $\mathrm{Z}_{\text {RX-HIGH-IMP-DC-POS }}$ and $\mathrm{Z}_{\text {RX-HIGH-IMP-DC-NEG }}$ (see § Table 8-12).
- The Transmitter is required only to meet $\mathrm{I}_{\text {TX-SHORT }}$ (see § Table 8-7).
- The Transmitter holds a constant DC common mode voltage. ${ }^{80}$

When Fundamental Reset is deasserted:

- The Port LTSSM (see § Section 4.2.6 ) is initialized (see § Section 6.6.1 for additional requirements).

[^0]
[^0]:    78. In this context, progress is defined as the LTSSM not remaining indefinitely in one state with the possible exception of Detect, or Disabled.
    79. The method to verify and re-establish Symbol lock is implementation specific.
    80. The common mode being driven is not required to meet the Absolute Delta Between DC Common Mode during LO and Electrical Idle (V ${ }_{\text {TX-CM-DC-ACTIVE-IBLE-DELTA }}$ ) specification (see § Table 8-7).

# 4.2.5.9.2 Hot Reset 

Hot Reset is a protocol reset defined in $\S$ Section 4.2.6.12 .

### 4.2.5.10 Link Data Rate Negotiation

All devices are required to start Link initialization using a $2.5 \mathrm{GT} / \mathrm{s}$ data rate on each Lane. A field in the training sequence Ordered Set (see $\S$ Section 4.2.5.1 ) is used to advertise all supported data rates. The Link trains to L0 initially in $2.5 \mathrm{GT} / \mathrm{s}$ data rate after which a data rate change occurs by going through the Recovery state.

### 4.2.5.11 Link Width and Lane Sequence Negotiation

PCI Express Links must consist of 1, 2, 4, 8, or 16 Lanes in parallel, referred to as $x 1, x 2, x 4, x 8$, and $x 16$ Links, respectively. All Lanes within a Link must simultaneously transmit data based on the same frequency with a skew between Lanes not to exceed $\mathrm{L}_{\text {TX-SKEW }}$ (§ Table 8-6). The negotiation process is described as a sequence of steps.

The negotiation establishes values for Link number and Lane number for each Lane that is part of a valid Link; each Lane that is not part of a valid Link exits the negotiation to become a separate Link or remains in Electrical Idle.

During Link width and Lane number negotiation, the two communicating Ports must accommodate the maximum allowed Lane-to-Lane skew as specified by $\mathrm{L}_{\text {RX-SKEW }}$ in § Table 8-12.

Optional Link negotiation behaviors include Lane reversal, variable width Links, splitting of Ports into multiple Links and the configuration of a crosslink.

Other specifications may impose other rules and restrictions that must be comprehended by components compliant to those other specifications; it is the intent of this specification to comprehend interoperability for a broad range of component capabilities.

### 4.2.5.11.1 Required and Optional Port Behavior

- The ability for a $x N$ Port to form a $x N$ Link as well as a $x 1$ Link (where $N$ can be $16,8,4,2$, and 1 ) is required.
- Designers must connect Ports between two different components in a way that allows those components to meet the above requirement. If the Ports between components are connected in ways that are not consistent with intended usage as defined by the component's Port descriptions/ data sheets, behavior is undefined.
- The ability for a $x N$ Port to form any Link width between $N$ and 1 is optional.
- An example of this behavior includes a x16 Port which can only configure into only one Link, but the width of the Link can be configured to be $x 8, x 4, x 2$ as well as the required widths of $x 16$ and $x 1$.
- The ability to split a Port into two or more Links is optional.
- An example of this behavior would be a x16 Port that may be able to configure two x8 Links, four x4 Links, or 16 x1 Links.
- Support for Lane reversal is optional.
- If implemented, Lane reversal must be done for both the Transmitter and Receiver of a given Port for a multi-Lane Link.

- An example of Lane reversal consists of Lane 0 of an Upstream Port attached to Lane N-1 of a Downstream Port where either the Downstream or Upstream device may reverse the Lane order to configure a xN Link.

Support for formation of a crosslink is optional. In this context, a Downstream Port connected to a Downstream Port or an Upstream Port connected to an Upstream Port is a crosslink.

Current and future electromechanical and/or form factor specifications may require the implementation of some optional features listed above. Component designers must read the specifications for the systems that the component(s) they are designing will used in to ensure compliance to those specifications.

# 4.2.5.12 Lane-to-Lane De-skew 

The Receiver must compensate for the allowable skew between all Lanes within a multi-Lane Link (see § Table 8-7 and § Table 8-12) before delivering the data and control to the Data Link Layer.

When using 8b/10b encoding, an unambiguous Lane-to-Lane de-skew mechanism may use one or more of the following:

- The COM Symbol of a received TS1 or TS2 Ordered Set
- The COM Symbol of a received Electrical Idle Exit Ordered Set
- The COM Symbol of the first received SKP Ordered Set after an FTS sequence
- The COM Symbol of a received SKP Ordered Set during a training sequence when not using SRIS.

When using 128b/130b encoding, an unambiguous Lane-to-Lane de-skew mechanism may use one or more of the following:

- A received SDS Ordered Set
- A received Electrical Idle Exit Ordered Set except when exiting L0s
- The first received Electrical Idle Exit Ordered Set after an FTS Ordered Set when exiting L0s
- When operating at $8.0 \mathrm{GT} / \mathrm{s}$, a received SKP Ordered Set
- When operating at a data rate of $16.0 \mathrm{GT} / \mathrm{s}$ or higher, the first received SKP Ordered Set after an FTS sequence
- When operating at a data rate of $16.0 \mathrm{GT} / \mathrm{s}$ or higher, a received SKP Ordered Set except when:
- exiting a training sequence or
- two SKP Ordered Sets are separated by an EDS

When using 1b/1b encoding, an unambiguous Lane-to-Lane de-skew mechanism may use one or more of the following:

- A received SDS Ordered Set
- A received Electrical Idle Exit Ordered Set
- A received Control SKP Ordered Set

Other de-skew mechanisms may also be employed, provided they are unambiguous. Lane-to-Lane de-skew must be performed during Configuration, Recovery, and L0s in the LTSSM.

# IMPLEMENTATION NOTE: UNAMBIGUOUS LANE-TO-LANE DE-SKEW: 6 

The max skew at $2.5 \mathrm{GT} / \mathrm{s}$ that a Receiver must be able to de-skew is 20 ns . A nominal SKP Ordered Set (i.e., one that does not have SKP Symbols added or removed by a Retimer) is 4 Symbols long, or 16 ns , at $2.5 \mathrm{GT} / \mathrm{s}$. Generally SKP Ordered Sets are transmitted such that they are well spaced out, and no particular care is needed to use them for de-skew (i.e., they provide an unambiguous mechanism). If back-to-back SKP Ordered Sets are transmitted, an implementation that simply looks for the COM of the SKP Ordered Set to occur on each Lane at the same point in time may fail. When exiting L0s a transmitter may send back-to-back SKP Ordered Sets after the last FTS Ordered Set of the Fast Training Sequence. De-skew must be obtained in L0s, therefore the implementation must comprehend back-to-back SKP Ordered Sets when performing de-skew in this case.

Exceptions to the unambiguous mechanism in $\S$ Section 4.2.5.12 occur because back-to-back Ordered Sets might be sent (i.e., EIEOS might be sent back-to-back when exiting L0s when using 128b/130b encoding.) EIEOS can still be used for de-skew in this case, however the implementation must comprehend back-to-back EIEOS when performing de-skew.

When operating at a data rate of $16.0 \mathrm{GT} / \mathrm{s}$ or higher, a transmitter may send back-to-back SKP Ordered Sets at the end of a Training Sequence (e.g., TS2 Ordered Set, SKP Ordered Set, SKP Ordered Set, SDS Ordered Set). Implementations that choose to use SKP Ordered Sets for de-skew in this case are recommended to recognize that the back-to-back SKP Ordered Sets are different (i.e., Standard SKP Ordered Set followed by Control SKP Ordered Set).

### 4.2.5.13 Lane vs. Link Training 

The Link initialization process builds unassociated Lanes of a Port into associated Lanes that form a Link. For Lanes to configure properly into a desired Link, the TS1 and TS2 Ordered Sets must have the appropriate fields (Symbol 3, 4, and 5) set to the same values on all Lanes.

Links are formed at the conclusion of Configuration.

- If the optional behavior of a Port being able to configure multiple Links is employed, the following observations can be made:
- A separate LTSSM is needed for each separate Link that is desired to be configured by any given Port.
- The LTSSM Rules are written for configuring one Link. The decision to configure Links in a serial fashion or parallel is implementation specific.


### 4.2.6 Link Training and Status State Machine (LTSSM) Descriptions 

The LTSSM states are illustrated in § Figure 4-67. These states are described in following sections.
All timeout values specified for the Link Training and Status state machine (LTSSM) are minus 0 seconds and plus 50\% unless explicitly stated otherwise. All timeout values must be set to the specified values after Fundamental Reset. All counter values must be set to the specified values after Fundamental Reset.

# 4.2.6.1 Detect Overview 

The purpose of this state is to detect when a far end termination is present.

### 4.2.6.2 Polling Overview

The Port transmits training Ordered Sets and responds to the received training Ordered Sets. In this state, bit lock and Symbol lock are established and Lane polarity is configured.

The Polling state includes Polling.Compliance (see § Section 4.2.7.2.2). This state is intended for use with test equipment used to assess if the Transmitter and the interconnect present in the device under test setup is compliant with the voltage and timing specifications in § Table 8-6, § Table 8-7, and § Table 8-12.

The Polling.Compliance state also includes a simplified inter-operability testing scheme that is intended to be performed using a wide array of test and measurement equipment (i.e., pattern generator, oscilloscope, BERT, etc.). This portion of the Polling.Compliance state is logically entered by at least one component transmitting a TS1 with Compliance_Receive_Request asserted upon entering Polling.Active. The ability to assert Compliance_Receive_Request is implementation specific. A provision for changing data rates to that indicated by the highest common transmitted and received Data Rate Identifiers (Symbol 4 of TS1) is also included to make this behavior scalable to various data rates.

## IMPLEMENTATION NOTE: USE OF POLLING.COMPLIANCE

Polling.Compliance is intended for a compliance test environment and not entered during normal operation and cannot be disabled for any reason. Polling.Compliance is entered based on the physical system environment or configuration register access mechanism as described in § Section 4.2.7.2.1. Any other mechanism that causes a Transmitter to output the compliance pattern is implementation specific and is beyond the scope of this specification.

### 4.2.6.3 Configuration Overview

In Configuration, both the Transmitter and Receiver are sending and receiving data at the negotiated data rate. The Lanes of a Port configure into a Link through a width and Lane negotiation sequence. Also, Lane-to-Lane de-skew must occur, scrambling can be disabled if permitted, the N_FTS is set, and the Disabled or Loopback states can be entered.

### 4.2.6.4 Recovery Overview

In Recovery, both the Transmitter and Receiver are sending and receiving data using the configured Link and Lane number as well as the previously supported data rate(s). Recovery allows a configured Link to change the data rate of operation if desired, re-establish bit lock, Symbol lock or Block alignment, and Lane-to-Lane de-skew. Recovery is also used to set a new N_FTS value and enter the Loopback, Disabled, Hot Reset, and Configuration states.

# 4.2.6.5 L0 Overview 

L0 is the normal operational state where data and control packets can be transmitted and received. All power management states are entered from this state.

### 4.2.6.6 L0s Overview

L0s is intended as a power savings state.

- L0s is not supported in Flit Mode and hardware must ignore the value of the L0s Enable bit for a Link operating in FM,
- L0s is not supported on a Link that contains Retimers, or
- L0s is not supported when operating with separate reference clocks with independent Spread Spectrum Clocking (SSC) (see § Section 4.2.8 and § Section 4.3.9).

L0s allows a Link to quickly enter and recover from a power conservation state without going through Recovery.
The entry to L0s occurs after receiving an EIOS.
The exit from L0s to L0 must re-establish bit lock, Symbol lock or Block alignment, and Lane-to-Lane de-skew.
A Transmitter and Receiver Lane pair on a Port are not required to both be in L0s simultaneously.

### 4.2.6.7 LOp Overview

L0p is a part of the L0 state and intended as a power savings state. L0p is supported only in Flit Mode, for all data rates. LOp support is optional but strongly recommended for Ports. LOp support is mandatory for Pseudo-Ports (Retimers) that support Flit Mode. LOp enables a Link to have some Lanes active while the remaining Lanes will be in electrical idle state. With Flit Mode, Link Upconfigure, which performs dynamic link width adjustment through the state transition L0 $\rightarrow$ Recovery $\rightarrow$ Configuration $\rightarrow$ L0, is not supported.

L0p is symmetric in width. All legal widths ( $\mathrm{x} 1, \mathrm{x} 2, \mathrm{x} 4, \mathrm{x} 8, \mathrm{x} 16$ ) up to the configured Link width must be supported by Ports that support LOp. When the Link is in LOp, at least one Lane in each direction must be active. LOp support is negotiated only during Configuration.Complete state when LinkUp=0b, as described in § Section 4.2.7.

Device Port Functions indicate support for LOp by Setting LOp Supported and by supplying a Port LOp Exit Latency value.
A Port Function for which LOp Enable is set to 1b, Hardware Autonomous Width Disable is set to 0b, and Target Link Width is set to 111 b , is permitted to initiate LOp requests with no architected software intervention by sending Link Management DLLPs (see § Section 4.2.6.7.1) to its Link Partner. System software can direct a Port Function to initiate an LOp Link Width change by sending to that Function a CfgWr TLP to set LOp Enable to 1b and Target Link Width to a value from 000b through 100b. It is strongly recommended that system software leave Target Link Width unchanged (i.e., 111b) other than for usage cases such as test or debug.

If the link is LOp capable and the Link width has been changed by entering the Configuration state, the following rules apply:

1. On entry to Recovery the Link will revert to its configured Link width on the last entry to L0
2. LOp cannot be used to turn on Lanes that were turned off in Configuration state.

# IMPLEMENTATION NOTE: 

The Lanes that are turned off during Configuration state may be due to issues such as reliability and are no longer associated with the LTSSM while LinkUp=1b (see § Section 4.2.7.3).

With LOp, any Lane that goes to electrical idle must be in electrical idle for a minimum time of $T_{\text {TX-IDLE-MIN }}$. The DC common mode voltage in TX during electrical idle must be within specification. The Receiver needs to wait a minimum of $T_{\text {TX-IDLE-MIN }}$ to start looking for Electrical Idle Exit.

Once LOp Is enabled, any Port can request a Link width change by sending up to three identical Link Management DLLPs within five consecutive Flits. Two Flits are considered consecutive even if they are separated by an Ordered Set. This can be either up-size to increase the number of active Lanes or down-size to reduce the number of active Lanes. If LOp Enable is Set, the Link partner must either Ack or Nak each LOp request on a valid Flit, unless it is permitted to ignore the request. If LOp Enable is Clear or Hardware Autonomous Width Disable is Set, the Link partner is strongly recommended to Nak the LOp request unless the request is an upsize to the fully configured link width. A Port must respond to an LOp request within the following time interval of receiving a valid Flit with the request: $4 \mu \mathrm{~s}$ if $8 \mathrm{~b} / 10 \mathrm{~b}$ encoding is used, $1 \mu \mathrm{~s}$ otherwise. Time is measured from the last bit of the Flit with the request on the ingress package pin to the first bit of the Flit with the response on the egress package pin. A Port that has requested a Link width change but has not received a response within the following time interval of issuing the request must either re-request the identical Link width change or abandon the request: $8 \mu \mathrm{~s}$ if $8 \mathrm{~b} / 10 \mathrm{~b}$ encoding is used, $4 \mu \mathrm{~s}$ otherwise. If identical LOp requests are received within five consecutive Flits, the same response must be sent. After responding to a request, the Link partner must consider the request to be abandoned if one of the following conditions are true:

- On an up-size request:
- the requester did not initiate the Link width upsize within $16 \mu \mathrm{~s}$ after the Flit with the Ack was transmitted AND
- the requester did not re-send the up-size request within $8 \mu \mathrm{~s}$ after the Flit with the Ack was transmitted
- On a down-size request with an Ack response:
- the requester did not resend the Link width downsize request within $4 \mu \mathrm{~s}$ after the Flit with the Ack was transmitted, AND
- the requester did not initiate the Link width downsize within $16 \mu \mathrm{~s}$ after the Flit with the Ack was transmitted and the Link Partner did not down-size the Link by sending an EIOSQ
- On a down-size request with a Nak response:
- the requester did not resend the Link width down-size request within $4 \mu \mathrm{~s}$ after the Flit with the Nak was transmitted

The following rules must be followed for LOp:

- If the Hardware Autonomous Width Disable bit in the Link Control register is set to 1b or if the LOp Enable bit is set to 0b, a Port:
- Must not request any down-size.
- Must initiate an up-size request to fully configured Link width if the Link is not at the fully configured width.
- LOp Ack and Nak Rules:
- A Port is permitted to Nak an LOp Request for a lower width than the current width if LOp.Priority is not set.

- If a Port is requesting link width down-size due to thermal throttling or reliability reasons, then it should set LOp.Priority in the LOp Request. The Link partner must Ack priority LOp Requests if it has LOp Enable Set and Hardware Autonomous Width Disable is Clear, and if it is not requesting an LOp width change and it is not going to request an LOp width change in the next Flit (in which case, the rules for simultaneous link width change requests below must be followed). If the Link partner is going to request an LOp width change in the next Flit, it must show up on the Transmitter pins in 100 ns with LOp.Priority set in the LOp Request. The requirements for setting LOp.Priority are implementation specific and behavior is undefined if LOp.Priority bit is set on an upsize.
- Any Port requesting a link width down-size that receives an Ack from its Link partner is responsible for initiating the up-size request eventually when the underlying conditions no longer prohibit the link from operating at full width.
- If both Ports are simultaneously requesting link width change the following rules apply to determine which request wins. A Port is permitted to consider a pending request for LOp as simultaneous as long as it has the LOp request scheduled to appear in its Transmitter pins within 100 ns . The Port that does not win must Ack the request to the winning Port through the proper LOp response. The port that does win must either Nak the request from the losing Port or ignore the request.
- If both requests have LOp.Priority set:
- if both sides are requesting the same width, the Downstream Port wins
- else, the request with the lower width wins
- If one request has LOp.Priority set, it wins
- If neither side has LOp.Priority set:
- if both sides are requesting the same width, the Downstream Port wins
- else, the request with the higher width wins
- A Port must ignore another LOp Request with the same width if it has already Ack'ed an LOp request and its Transmitter Lanes are already at or in the process of transitioning to the same width.
- An entry to Recovery results in the Link going to its configured Link width on the most recent transition from Configuration to L0 and all the associated LOp transition states (such as width change request/ response and all the tracking information such as time since Ack/ Nak) are reset as if no width change request was made.

Once an LOp request to change link width has been initiated, it must be completed or abandoned.
A Port must not initiate a request for a new Link width unless the following conditions are met:

1. No link width resizing has been in progress in the last $1 \mu \mathrm{~s}$ if $1 \mathrm{~b} / 1 \mathrm{~b}$ or $128 \mathrm{~b} / 130 \mathrm{~b}$ encoding is used or $4 \mu \mathrm{~s}$ if $8 \mathrm{~b} /$ 10b encoding is used.
2. If the Port abandoned its last LOp Request, at least $16 \mu \mathrm{~s}$ has elapsed since the request was abandoned.
3. If the Port Ack'ed the last LOp request from the remote Port, that request was either completed or abandoned.

On a Link width down-size, the following steps must be taken by each Port independently after the Link width down-configure request has been 'Ack'ed:

- On the next scheduled SKP Ordered Set interval, the Lanes that are being turned off will send an EIOSQ instead of a SKP Ordered Set.
- The Lanes that sent an EIOSQ go to Electrical Idle after the EIOSQ is sent. The Lanes that sent a SKP Ordered Set resume transmitting Flits with a SKP Ordered Set insertion interval that corresponds to the new Link width (see § Section 4.2.3.4.2.5).

- If the requesting Port did not receive an Ack for the L0p request, but sees the Link Partner sending the EIOSQ Ordered Set, it must treat that as an 'Ack'. (An example scenario where this may happen is if the Flit containing the Ack DLLP was corrupted.)
- During the down-size negotiation, an EIOS must be received on all lanes to be deactivated at the same time after adjusting for lane to lane skew; else the LTSSM must enter Recovery.
- A Port is permitted to enter Recovery after 24 msec of sending the EIOSQ on a downsize if the Link did not achieve the desired Link width in both directions

On a Link width up-size the following steps must be taken:

- The up-sizing action must be initiated by the requesting port. The non-requesting Port waits for detection of Electrical Idle exit on the lanes to be activated before starting the up-sizing actions.
- Data Stream continues on the active Lanes
- For the Lanes to be activated the following sequence must be followed: ${ }^{81}$
- SKP Ordered Sets must be scheduled at the same time as Lane 0 and the same number of SKPs must be added or deleted as Lane 0 by the Receiver in the (Pseudo-)Port. A Port is permitted to truncate a TS1/TS2 Ordered Set in 8b/10b encoding to transmit the SKP Ordered Set at the same time as Lane 0.
- Transmit TS1 Ordered Sets meeting the requirements for TS1 Ordered Sets in § Section 4.2.7.4.1 and § Section 4.2.5.3. The Transmitter must ensure it follows the EIEOSQ rule of not being broken up by a SKP Ordered Set even though it has to send SKP Ordered Set at the same time as the active Lanes. This can be done by scheduling the start of EIEOSQ appropriately. However, a Transmitter is permitted to restart the EIEOSQ sequence after the SKP Ordered Set if the SKP Ordered Set interrupted an EIEOSQ in progress. If an EIEOSQ is scheduled to precede a subsequent scheduled SDS Ordered Set within 256 UI, the transmitter is permitted to not send that EIEOSQ or to delay the SDS until the next SKP interval.
- If eight consecutive TS1 or TS2 Ordered sets are received on all Lanes that are to be activated, the transmitter must transition to sending TS2 Ordered Sets meeting the requirements for TS2 Ordered Sets in § Section 4.2.7.4.4 and § Section 4.2.5.3. If the Extended Synch bit is Set, it is strongly recommended that the Transmitter send a minimum of 1024 consecutive TS1 Ordered Sets before transitioning to sending TS2 Ordered Sets.
- After receiving eight consecutive TS2 Ordered Sets and sending at least 16 TS2 Ordered sets after the receipt of one TS2 Ordered Set on all the Lanes to be activated, the Port sends an SDS Ordered Set sequence if the data rate is $8.0 \mathrm{GT} / \mathrm{s}$ or higher just prior to sending the next scheduled SKP Ordered Set that will be sent (on the active as well as to be activated Lanes).
- Lane to Lane de-skew must be completed by the Receiver using the SKP Ordered Set across all the currently active as well as the Lanes being activated that have received eight consecutive TS2 Ordered Set and the SDS Ordered Set, if the data rate is $8.0 \mathrm{GT} / \mathrm{s}$ or higher. Starting with the SKP Ordered Set that follows the SDS Ordered Set, the SKP Ordered Set insertion interval that corresponds to the new Link width takes effect (see § Section 4.2.3.4.2.5).
- If 24 ms has elapsed since the start of activation and the Lanes are not part of the active Lanes, the LTSSM must be directed to enter Recovery.

The DLLP encoding for the various L0p commands and responses is shown in § Figure 3-15. The definition of the various fields in the DLLP are shown in § Table 4-54.

# IMPLEMENTATION NOTE: <br> : POPULATION OF TS1/TS2 ORDERED SET FIELDS DURING LOP 

When using 1b/1b Encoding, values to use for the various TS1/TS2 bits and fields are specified in § Table 4-37. In many cases those values depend on the current LTSSM state, which is L0 during L0p Link width up-size. However, since the rules in this section indicate that the transmitted TS1 Ordered Sets should meet the requirements specified in $\S$ Section 4.2.7.4.1, and that the transmitted TS2 Ordered Sets should meet the requirements specified in $\S$ Section 4.2.7.4.4, implementations that populate those bits and fields as if the LTSSM state was Recovery.Rcvrlock for TS1 and Recovery.RcvrCfg for TS2 will not impede forward progress and are acceptable.

## IMPLEMENTATION NOTE:

## ORTHOGONALITY OF LOP AND L1/L2

L0p is a reduced power sub-state of L0. It is orthogonal to L1 and L2. For a Port that is in the process of initiating or accepting an L1 or L2 request, it is recommended to not initiate, renew, or respond to an L0p request. Nevertheless, negotiations of L0p and L1 or L0p and L2 are permitted to occur concurrently and will ultimately resolve in one of the power states being negotiated, depending on the sequence of the negotiations and the desired intention of each Port. Refer to § Section 5.3.2 for rules that govern Link power management.

# IMPLEMENTATION NOTE: SUMMARY OF LOP TRANSMITTER/RECEIVER BEHAVIOR 

When Remote LOp Supported is set, the table below summarizes the LOp Transmitter and Receiver behavior discussed above. The table below applies independently to each end of the link. It is recommended that SW sets the Hardware Autonomous Width Disable and LOp Enable bits consistently on both sides of the link.

It is recommended that the Link is at full width prior to changing the LOp Enable setting.
It is recommended that an implementation specific repeated request limit should also be deployed.

Table 4-53 Summary of LOp Transmitter/Receiver Behavior

| SW Control bits @ Tx/Rx | Tx side behavior |  |  | Rx side behavior |  |  |
| :--: | :--: | :--: | :--: | :--: | :--: | :--: |
| Hardware <br> Autonomous <br> Width <br> Disable | LOp Enable | Issue <br> Nonpriority <br> LOp <br> request for width reduction? | Issue Priority LOp request for width reduction? | Issue LOp request for width increase? | Response to Nonpriority LOp request for width reduction? | Response to LOp request for width increase? |
| 1 | x | Not permitted | Not permitted | Must issue to achieve fully configured width, if at lower width | Recommend <br> Nak. But 'No-response' is permitted as well. | ```Recommend Nak. But 'No-response' is permitted as well.``` | Ack for full width increase. Otherwise, recommend Nak but 'No-response' is permitted as well. |
| 0 | 0 | Not permitted | Not permitted | Must issue to achieve fully configured width, if at lower width | Nak | Nak | Ack for full width increase. Otherwise, recommend Nak but 'No-response' is permitted as well. |
| 0 | 1 | Permitted | Permitted | Permitted | Ack/Nak | Ack (with exception noted in \$ Section 4.2.6.7) | Ack |

### 4.2.6.7.1 Link Management DLLP

Table 4-54 Link Management DLLP

| Field | Description |
| :--: | :--: |
| Byte 0 | Link Management DLLP - must be 0010 1000b |
| Byte 1 | Link Mgmt Type - qualifies Bytes 2 and 3 |
|  | 0000 0000b <br> Others |

## LOp DLLP

Reserved

| Field | Description |  |  |
| :--: | :--: | :--: | :--: |
| Byte 2, <br> Bit [4] | LOp.Priority - LOp Priority Request - Meaning of this field varies by LOp.Cmd value |  |  |
|  | If LOp.Cmd is: | Description is: |  |
|  | LOp Request | Request Priority <br> 0b Normal Priority LOp Request <br> 1b High Priority LOp Request |  |
|  | Others | Reserved |  |
|  | Reserved if Link Mgmt Type is other than 00h. |  |  |
| Byte 2, <br> Bits [3:0] | LOp.Cmd - LOp Command or Response |  |  |
|  | 0100b | LOp Request |  |
|  | 0110b | LOp Request Ack |  |
|  | 0111b | LOp Request Nak |  |
|  | Others | Reserved |  |
|  | Reserved if Link Mgmt Type is other than 00h. |  |  |
| Byte 3, <br> Bits [7:4] | Meaning of this field varies by LOp.Cmd value |  |  |
|  | If LOp.Cmd is: | Description is: |  |
|  | LOp Request Ack | Response Payload - Reflects the value of LOp Link Width of the corresponding command |  |
|  | LOp Request Nak | 0001b | $x 1$ |
|  |  | 0010b | $x 2$ |
|  |  | 0100b | $x 4$ |
|  |  | 1000b | $x 8$ |
|  |  | 0000b | $x 16$ |
|  |  | Others | Reserved |
|  | Others | Reserved |  |
|  | Reserved if Link Mgmt Type is other than 00h. |  |  |
| Byte 3, <br> Bits [3:0] | Meaning of this field varies by LOp.Cmd value |  |  |
|  | If LOp.Cmd is: | Description is: |  |
|  | LOp Request | LOp Link Width - Desired Link Width 0001b | $\begin{aligned} & \text { x1 } \\ & x 2 \\ & x 4 \end{aligned}$ |
|  |  | 0010b | $x 8$ |
|  |  | 0100b | $x 16$ |

| Field | Description |  |  |
| :-- | :-- | :-- | :-- |
|  | If LOp.Cmd is: | Description is: |  |
|  | Others | Reserved |  |
|  | Others | Reserved |  |
|  | Reserved if Link Mgmt Type is other than 00h. |  |  |

Receivers must silently ignore Link Management DLLPs if:

- The Link is operating in Non-Flit Mode.
- The Link Mgmt Type field contains a Reserved value.
- The Link Mgmt Type field is 00 h and the LOp.Cmd field contains a reserved value.
- The Link Mgmt Type field is 00 h , the LOp.Cmd field contains LOp Request and the LOp Link Width field contains a reserved value.
- The Link Mgmt Type field is 00 h , the LOp.Cmd field contains LOp Request Ack or LOp Request Nak and Response Payload contains a reserved value.


# IMPLEMENTATION NOTE: LOP ENTRY / EXIT TIMES 

The Lanes that are electrically idle are expected to have power savings and entry/ exit times similar to L1. The deeper the power savings, the higher the exit latency to bring those idle Lanes back to active state. For example, a PLL associated exclusively with the set of Lanes that are idle can be turned off. This will result in better power savings but the exit time to activate the Lanes will be higher.

Receiver hardware should use the LOp Exit Latency values from the Data Link Feature DLLP to help determine when to request LOp. These values are visible to software in the Local LOp Exit Latency and Remote LOp Exit Latency fields.

System software should ensure that the exit latency of all Retimers are included some Retimer LOp Exit Latency field (either Upstream or Downstream Port). In general, Retimers located on an add-in card should be included in the add-in card's Upstream Port's Retimer LOp Exit Latency and Retimers located in the system chassis should be included in the Downstream Port's Retimer LOp Exit Latency.

Example of LOp Flows: § Figure 4-66 demonstrates LOp flows in a x16 Link.

1. LOp is enabled on the Link during the Configuration.Complete state.
2. The USP requests the Link to downsize to $x 8$ which is Ack'ed by the DSP.
3. On the next SKP Ordered Set the LOp indication is provided by the Port on a per-Lane basis. Lanes 0-7 continue with the traffic whereas Lanes 8-15 send an EIOSQ and go to electrical Idle. Thus, the Link now has 8 active Lanes and 8 Lanes in idle state.
4. At a later point, the DSP requests upsizing the Link to x16 while the USP has made a request to further downsize to $x 4$. The $x 4$ request gets NAK'ed, the $x 16$ gets Ack'ed. Then link training proceeds in Lanes 8-15, initiated by the DSP with the exchange of TS1/TS2 Ordered Sets with EIEOS inserted at appropriate intervals.

When Lanes 8-15 are ready, an SDS is sent immediately preceding the next scheduled SKP Ordered Set in the Lanes.
5. The Link operates as a $\times 16$ Link after sending the SKP Ordered Set across all 16 Lanes. Even though LOp is symmetric during the transitions, the two sides may be operating at different widths for a while. This is similar to the situation during entry to L1 or L0.

Note that if the data rates is $2.5 \mathrm{GT} / \mathrm{s}$, the EIEOS and SDS will not be present. If the data rate is $5.0 \mathrm{GT} / \mathrm{s}$, EIEOS will be present but not SDS.
![img-64.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-64.jpeg)

Figure 4-66 Example of LOp flow in a $\times 16$ Link

# 4.2.6.8 L1 Overview 

L1 is intended as a power savings state.
The L1 state allows an additional power savings over LOs at the cost of additional resume latency.
The entry to L1 occurs after being directed by the Data Link Layer and receiving an EIOS.

### 4.2.6.9 L2 Overview

Power can be aggressively conserved in L2. Most of the Transmitter and Receiver may be shut off. ${ }^{82}$ Main power and clocks are not guaranteed, but Aux ${ }^{83}$ power is available.

[^0]
[^0]:    82. The exception is the Receiver termination, which must remain in a low impedance state.
    83. In this context, Aux power means a power source which can be used to drive the Beacon circuitry.

When Beacon support is required by the associated system or form factor specification, an Upstream Port that supports the wakeup capability must be able to send; and a Downstream Port must be able to receive; a wakeup signal referred to as a Beacon.

The entry to L2 occurs after being directed by the Data Link Layer and receiving an EIOS.

# 4.2.6.10 Disabled Overview 

The intent of the Disabled state is to allow a configured Link to be disabled as long as directed or until Electrical Idle is exited (i.e., due to a hot removal and insertion) after entering Disabled.

### 4.2.6.11 Loopback Overview

Loopback is intended for test and fault isolation use. Only the entry and exit behavior is specified, all other details are implementation specific. Loopback can operate on either a per-Lane or configured Link basis.

A Loopback Lead is the component requesting Loopback.
A Loopback Follower is the component looping back the data.
In 8b/10b and 128b/130b encoding, Loopback uses bit 2 (Loopback) in the Training Control Field of TS1 and TS2 Ordered Sets (see § Table 4-34 and § Table 4-35). In 1b/1b encoding, Loopback uses an encoding of bits 3:0 in the Training Control field of TS1 and TS2 Ordered Sets (see § Table 4-37).

The entry mechanism for a Loopback Lead is device specific.
The Loopback Follower device enters Loopback whenever two consecutive TS1 Ordered Sets are received with Loopback_Request asserted.

## IMPLEMENTATION NOTE: USE OF LOOPBACK

Once in the Loopback state, the Lead can send any pattern of Symbols as long as the encoding rules are followed. Once in Loopback, the concept of data scrambling is no longer relevant; what is sent out is looped back. The mechanism(s) and/or interface(s) utilized by the Data Link Layer to notify the Physical Layer to enter the Loopback state is implementation specific and beyond the scope of this specification.

## IMPLEMENTATION NOTE: LOOPBACK LEAD AND LOOPBACK FOLLOWER REPLACING OLDER TERMS

The terms Loopback Lead and Loopback Follower are newer terms while preserving the identical Loopback functionality as in [PCle-5.0]. These terms appropriately represent the functionality performed by the component. Any Port or a test equipment can be a Loopback Lead if it has that optional capability. Every Port is required to be a Loopback Follower. The test set up needs to comprehend that in such a way that it designates one Port to be the Loopback Lead and its Link Partner to be the Loopback Follower.

# 4.2.6.12 Hot Reset Overview 

The intent of the Hot Reset state is to allow a configured Link and associated downstream device to be reset using in-band signaling.

### 4.2.7 Link Training and Status State Rules

Various Link status bits are monitored through software with the exception of LinkUp which is monitored by the Data Link Layer. § Table 4-58 describes how the Link status bits must be handled throughout the LTSSM (for more information, see § Section 3.2 for LinkUp; § Section 7.5.3.8 for Link Speed, Link Width, and Link Training; § Section 6.2 for Receiver Error; and § Section 6.7 for In-Band Presence Detect). A Receiver may also optionally report an 8b/10b Error in the Lane Error Status Register when operating in 8b/10b encoding, when allowed to report the error as a Receiver Error in § Table $4-58$.

## IMPLEMENTATION NOTE: RECEIVER ERRORS DURING CONFIGURATION AND RECOVERY STATES

Allowing Receiver Errors to be set while in Configuration or Recovery is intended to allow implementations to report Link Errors that occur while processing packets in those states. For example, if the LTSSM transitions from L0 to Recovery while a TLP is being received, a Link Error that occurs after the LTSSM transition can be reported.

Table 4-58 Link Status Mapped to the LTSSM

| LTSSM State | Link <br> Width | Link Speed | LinkUp | Link <br> Training | Receiver Error | In-Band <br> Presence <br> Detect $^{\text {M }}$ |
| :--: | :--: | :--: | :--: | :--: | :--: | :--: |
| Detect | Undefined | Undefined | 0b | 0b | No action | 0b |
| Polling | Undefined | Set to $2.5 \mathrm{GT} / \mathrm{s}$ on entry from Detect. Link speed may change on entry to Polling.Compliance. | 0b | 0b | No action | 1b |
| Configuration | Set | No action | $\begin{gathered} 0 \mathrm{~b} / 1 \mathrm{~b} \\ 85 \end{gathered}$ | 1b | Set on 8b/10b Error. <br> Optional: Set on Link <br> Error when using 128b/ <br> 130b encoding. | 1b |
| Recovery | No action | Set to new speed when speed changes | 1b | 1b | Optionally set on Link <br> Error. | 1b |
| L0 | No action | No action | 1b | 0b | Set on Link Error. | 1b |
| L0s | No action | No action | 1b | 0b | No action | 1b |

[^0]
[^0]:    84. In-band refers to the fact that no sideband signals are used to calculate the presence of a powered up device on the other end of a Link.
    85. LinkUp will always be 0 if coming into Configuration via Detect $\rightarrow$ Polling $\rightarrow$ Configuration and LinkUp will always be 1 if coming into Configuration from any other state.

| LTSSM State | Link Width | Link Speed | LinkUp | Link Training | Receiver Error | In-Band Presence Detect |
| :--: | :--: | :--: | :--: | :--: | :--: | :--: |
| L1 | No action | No action | 1b | 0b | No action | 1b |
| L2 | No action | No action | 1b | 0b | No action | 1b |
| Disabled | Undefined | Undefined | 0b | 0b | Optional: Set on 8b/10b Error | 1b |
| Loopback | No action | Link speed may change on entry to Loopback from Configuration. | 0b | 0b | No action | 1b |
| Hot Reset | No action | No action | 0b | 0b | Optional: Set on 8b/10b Error | 1b |

The state machine rules for configuring and operating a PCI Express Link are defined in the following sections.

# Matching Link and Lane Numbers for 1b/1b Encoding 

With 1b/1b encoding, the Link and Lane numbers are not sent explicitly in the TS1/TS2 Ordered Sets in any States other than those listed in $\S$ Table 4-37. Thus, when using 1b/1b encoding in any LTSSM state other than where Link and Lane numbers are transmitted, any references to an exact match in the Link and/or Lane numbers between the transmitted and received TS0/TS1/TS2 Ordered Sets must be assumed to be true as long as the Ordered Set is a valid 1b/1b TS0, TS1, or TS2 Ordered Set. In Recovery.RcvrCfg, if TS2 Ordered Sets with an Equalization Request (Equalization Byte 0: Bit 0=0b and Bit $7=1 \mathrm{~b}$ ) are received, this must be treated as an exact match in the Link number. If transmitting TS2 Ordered Sets with an Equalization Request and TS2 Ordered Sets with Link Number (or PAD) are received, Receivers must check the received Link number for a match with the Link number negotiated during the Configuration LTSSM state. Similarly, when using 1b/1b encoding in any LTSSM state other than Configuration, any references to transmitting a TS0/TS1/TS2 Ordered Set using the Link number and/or Lane number negotiated during the Configuration LTSSM state must be interpreted as using the Lane number for the purposes of scrambling in the TS0/TS1/TS2 Ordered Set.

![img-65.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-65.jpeg)

OM13800F
Figure 4-67 Main State Diagram for Link Training and Status State Machine

# 4.2.7.1 Detect 

The Detect substate machine is shown in § Figure 4-68.

### 4.2.7.1.1 Detect.Q niet

- Transmitter is in an Electrical Idle state.
- The DC common mode voltage is not required to be within specification.

- $2.5 \mathrm{GT} / \mathrm{s}$ data rate is selected as the frequency of operation. If the frequency of operation was not $2.5 \mathrm{GT} / \mathrm{s}$ data rate on entry to this substate, the LTSSM must stay in this substate for at least 1 ms , during which the frequency of operation must be changed to the $2.5 \mathrm{GT} / \mathrm{s}$ data rate.
- Note: This does not affect the advertised data rate in the TS1 and TS2 Ordered Sets.
- All Receivers must meet the $\mathrm{Z}_{\text {RX-DC }}$ specification for $2.5 \mathrm{GT} / \mathrm{s}$ within 1 ms (see § Table 8-12) of entering this substate. The LTSSM must stay in this substate until the $\mathrm{Z}_{\mathrm{RX}-\mathrm{DC}}$ specification for $2.5 \mathrm{GT} / \mathrm{s}$ is met.
- LinkUp = 0b (status is cleared).
- The Equalization 8.0 GT/s Phase 1 Successful, Equalization 8.0 GT/s Phase 2 Successful, Equalization 8.0 GT/s Phase 3 Successful, and Equalization 8.0 GT/s Complete bits of the Link Status 2 Register are all set to 0b.

The Equalization 16.0 GT/s Phase 1 Successful, Equalization 16.0 GT/s Phase 2 Successful, Equalization 16.0 GT/s Phase 3 Successful and Equalization 16.0 GT/s Complete bits of the 16.0 GT/s Status Register are all set to 0b.

The Equalization 32.0 GT/s Phase 1 Successful, Equalization 32.0 GT/s Phase 2 Successful, Equalization 32.0 GT/s Phase 3 Successful and Equalization 32.0 GT/s Complete bits of the 32.0 GT/s Status Register are all set to 0b.

The Equalization 64.0 GT/s Phase 1 Successful, Equalization 64.0 GT/s Phase 2 Successful, Equalization 64.0 GT/s Phase 3 Successful, and Equalization 64.0 GT/s Complete bits of the 64.0 GT/s Status Register are all set to 0b.

- The use_modified_TS1_TS2_Ordered_Set variable is reset to 0b.
- The Remote LOp Supported bit in the Device Status 3 Register is reset to 0b.
- The Flit_Mode_Enabled variable is reset to 0b. (When Flit_Mode_Enabled is set to 0b, the link will not operate in Flit Mode.)
- The LOp_capable variable is reset to 0b.
- The SRIS_Mode_Enabled variable is reset to 0b. When the SRIS_Mode_Enabled variable is set to 1b in Flit Mode, the SKP Ordered Set transmission frequency must follow the SRIS mode frequency for the data rate of operation. Otherwise, the SKP Ordered Set transmission frequency for the SRNS / Common Clock must be followed.
- The directed_speed_change variable is reset to 0b. The upconfigure_capable variable is reset to 0b. The idle_to_rlock_transitioned variable is reset to 00 h . The select_deemphasis variable must be set to either 0 b or 1 b based on platform specific needs for an Upstream Port and identical to the Selectable Preset/De-emphasis bit in the Link Control 2 Register for a Downstream Port. The equalization_done_8GT_data_rate, equalization_done_16GT_data_rate, equalization_done_32GT_data_rate, and equalization_done_64GT_data_rate variables are reset to 0b. The perform_equalization_for_loopback and perform_equalization_for_loopback_64GT variables are reset to 0b.
- Note that since these variables are defined with [PCIe-2.0], earlier devices would not implement these variables and will always take the path as if the directed_speed_change and upconfigure_capable variables are constantly reset to 0 b and the idle_to_rlock_transitioned variable is constantly set to FFh.
- The next state is Detect.Active after a 12 ms timeout or if Electrical Idle Exit is detected on any Lane. If the transition to this state is from Hot Reset, it is strongly recommended that the Downstream Port wait for 2 ms before enabling Electrical Idle Exit detection.


# 4.2.7.1.2 Detect.Active $\S$ 

- The Transmitter performs a Receiver Detection sequence on all un-configured Lanes that can form one or more Links (see § Section 8.4.5.7 for more information).
- Next state is Polling if a Receiver is detected on all unconfigured Lanes.

- Next state is Detect.Quiet if a Receiver is not detected on any Lane.
- If at least one but not all un-configured Lanes detect a Receiver, then:

1. Wait for 12 ms .
2. The Transmitter performs a Receiver Detection sequence on all un-configured Lanes that can form one or more Links (see § Section 8.4.5.7 for more information).

- The next state is Polling if exactly the same Lanes detect a Receiver as the first Receiver Detection sequence.
- Lanes that did not detect a Receiver must:
i. Be associated with a new LTSSM if this optional feature is supported. or
ii. All Lanes that cannot be associated with an optional new LTSSM must transition to Electrical Idle. ${ }^{86}$
- These Lanes must be re-associated with the LTSSM immediately after the LTSSM in progress transitions back to Detect.
- An EIOS does not need to be sent before transitioning to Electrical Idle.
- Otherwise, the next state is Detect.Quiet.
![img-66.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-66.jpeg)

OM14313A
Figure 4-68 Detect Substate Machine

# 4.2.7.2 Polling 

The Polling substate machine is shown in § Figure 4-69.

### 4.2.7.2.1 Polling.Active

- Transmitter sends TS1 Ordered Sets with Lane and Link numbers set to PAD on all Lanes that detected a Receiver during Detect.
- The Data Rate Identifier Symbol of the TS1 Ordered Sets must advertise all data rates between $2.5 \mathrm{GT} / \mathrm{s}$ and $32.0 \mathrm{GT} /$ that the Port supports, including those that it does not intend to use.

Note: Ports are not permitted to advertise higher than $32.0 \mathrm{GT} / \mathrm{s}$ data rates in this state.

[^0]
[^0]:    86. The common mode being driven is not required to meet the Absolute Delta Between DC Common Mode During L0 and Electrical Idle (VIX-CM-DC-ACTIVE-IDLE-DELTA) specification (see § Table 8-7).

- The Transmitter must wait for its TX common mode to settle before exiting from Electrical Idle and transmitting the TS1 Ordered Sets.
- The Transmitter must drive patterns in the default voltage level of the Transmit Margin field within 192 ns from entry to this state. This transmit voltage level will remain in effect until Polling.Compliance or Recovery.RcvrLock is entered.
- Next state is Polling.Compliance if the Enter Compliance bit (bit 4) in the Link Control 2 Register is 1b. If the Enter Compliance bit was set prior to entry to Polling.Active, the transition to Polling.Compliance must be immediate without sending any TS1 Ordered Sets.
- Next state is Polling.Configuration after at least 1024 TS1 Ordered Sets were transmitted, and all Lanes that detected a Receiver during Detect receive eight consecutive training sequences (or their complement) satisfying any of the following conditions:
- TS1 with Lane and Link numbers set to PAD and Compliance_Receive_Request deasserted.
- TS1 with Lane and Link numbers set to PAD and Loopback_Request asserted.
- TS2 with Lane and Link numbers set to PAD.
- Otherwise, after a 24 ms timeout the next state is:
- Polling.Configuration if,
i. Any Lane, which detected a Receiver during Detect, received eight consecutive training sequences (or their complement) satisfying any of the following conditions:

1. TS1 with Lane and Link numbers set to PAD and with Compliance_Receive_Request deasserted.
2. TS1 with Lane and Link numbers set to PAD and Loopback_Request asserted.
3. TS2 with Lane and Link numbers set to PAD.
and a minimum of 1024 TS1 Ordered Sets are transmitted after receiving one TS1 or TS2 Ordered Set ${ }^{87}$.

And
ii. At least a predetermined set of Lanes that detected a Receiver during Detect have detected an exit from Electrical Idle at least once since entering Polling.Active.

- Note: This may prevent one or more bad Receivers or Transmitters from holding up a valid Link from being configured, and allow for additional training in Polling.Configuration. The exact set of predetermined Lanes is implementation specific. Note that up to [PCIe-1.1] this predetermined set was equal to the total set of Lanes that detected a Receiver.
- Note: Any Lane that receives eight consecutive TS1 or TS2 Ordered Sets should have detected an exit from Electrical Idle at least once since entering Polling.Active.
- Else Polling.Compliance if either (a) or (b) is true:
a. not all Lanes from the predetermined set of Lanes from (ii) above have detected an exit from Electrical Idle since entering Polling.Active.
b. any Lane that detected a Receiver during Detect received eight consecutive TS1 Ordered Sets (or their complement) with the Lane and Link numbers set to PAD, Compliance_Receive_Request asserted, and Loopback_Request deasserted.

[^0]
[^0]:    87. Earlier versions of this specification required transmission of 1024 TS1 Ordered Sets after receiving one TS1 Ordered Set. This behavior is still permitted but the implementation will be more robust if it follows the behavior of transmitting 1024 TS1 Ordered Sets after receiving one TS1 or TS2 Ordered Set.

- A port that is capable of transmitting at the 64.0 GT/s data rate may receive TS1 Ordered Sets with the Flit Mode Supported bit set to 1b and the Supported Link Speeds field set to 10111 b .
- Note: If a passive test load is applied on all Lanes then the device will go to Polling.Compliance.
- Else Detect if the conditions to transition to Polling.Configuration or Polling.Compliance are not met


# 4.2.7.2.2 Polling.Compliance 

- The Transmit Margin field of the Link Control 2 Register is sampled on entry to this substate and becomes effective on the transmit package pins within 192 ns of entry to this substate and remains effective through the time the LTSSM is in this substate.
- The data rate and de-emphasis level for transmitting the compliance pattern are determined on the transition from Polling.Active to Polling.Compliance using the following algorithm.
- If the Port is capable of transmitting at the 2.5 GT/s data rate only, the data rate for transmitting the compliance pattern is $2.5 \mathrm{GT} / \mathrm{s}$ and the de-emphasis level is -3.5 dB .
- Else if the Port entered Polling.Compliance due to detecting eight consecutive TS1 Ordered Sets in Polling.Active with Compliance_Receive_Request asserted and Loopback_Request deasserted then the data rate for transmission is determined as follows:
- If the port is capable of transmitting at the 64.0 GT/s data rate and the eight consecutive TS1 Ordered Sets received in Polling.Active that directed the port to this state had the Flit Mode Supported bit set to 1b and the Supported Link Speeds field set to 10111 b , the data rate for transmitting the compliance pattern must be $64.0 \mathrm{GT} / \mathrm{s}$.
- Else, the data rate for transmission is determined by the highest common transmitted and received Data Rate Identifiers (Symbols 4 of the TS1 sequence) advertised in the eight consecutive TS1 Ordered Sets received on any Lane that detected a Receiver during Detect.
The select_deemphasis variable must be set equal to the Selectable De-emphasis bit (Symbol 4 bit 6) in the eight consecutive TS1 Ordered Sets it received in Polling.Active substate. If the common data rate is $8.0 \mathrm{GT} / \mathrm{s}$ or higher, the select_preset variable on each Lane is set to the Transmitter preset value advertised in the Transmitter Preset bits of the eight consecutive EQ TS1 Ordered Sets on the corresponding Lane, provided the value is not a Reserved encoding, and this value must be used by the transmitter (for $8.0 \mathrm{GT} / \mathrm{s}$ Data Rate, use of the Receiver preset hint value advertised in those eight consecutive EQ TS1 Ordered Sets is optional). If the common Data Rate is $8.0 \mathrm{GT} / \mathrm{s}$ or higher, any Lanes that did not receive eight consecutive EQ TS1 Ordered Sets with Transmitter preset information, or that received a value for a Reserved encoding, can use any supported Transmitter preset in an implementation specific manner.
- Else if the Enter Compliance bit in the Link Control 2 Register is 1b, the data rate for transmitting the compliance pattern is defined by the Target Link Speed field in the Link Control 2 Register. The select_deemphasis variable is Set when the Compliance Preset/De-emphasis field in the Link Control 2 Register equals 0001b if the data rate will be $5.0 \mathrm{GT} / \mathrm{s}$. If the data rate will be $8.0 \mathrm{GT} / \mathrm{s}$ or higher, the select_preset variable on each Lane is set to, and the transmitter must operate with, the preset value provided in the Compliance Preset/De-emphasis Value (bits 15:12) in the Link Control 2 Register provided the value is not a Reserved encoding.
- Else the data rate, preset, and de-emphasis level settings are defined as follows based on the component's maximum supported data rate and the number of times Polling.Compliance has been entered with this entry criteria, in the same sequence of setting numbers as described in § Table 4-59:

Table 4-59 Compliance Pattern Settings

| Setting Nos | Data Rate | Transmitter De-emphasis or preset sequence |
| :--: | :--: | :--: |
| \#1 | $2.5 \mathrm{GT} / \mathrm{s}$ | $-3.5 \mathrm{~dB}$ |
| \#2, \#3 | $5.0 \mathrm{GT} / \mathrm{s}$ | $-3.5 \mathrm{~dB}$ followed by $-6 \mathrm{~dB}$ |
| \#4 through <br> \#14 | $8.0 \mathrm{GT} / \mathrm{s}$ | Transmitter Preset Encoding 0000b through 1010b, as defined in § Section 4.2.4.2, in increasing order |
| \#15 through <br> \#25 | $16.0 \mathrm{GT} / \mathrm{s}$ | Transmitter Preset Encoding 0000b through 1010b, as defined in § Section 4.2.4.2, in increasing order |
| \#26 through <br> \#34 | $16.0 \mathrm{GT} / \mathrm{s}$ | Transmitter Preset Encoding 0100b as defined in § Section 4.2.4.2 |
| \#35 through <br> \#45 | $32.0 \mathrm{GT} / \mathrm{s}$ | Transmitter Preset Encoding 0000b through 1010b, as defined in § Section 4.2.4.2, in increasing order |
| \#46 through <br> \#54 | $32.0 \mathrm{GT} / \mathrm{s}$ | Transmitter Preset Encoding 0100b as defined in § Section 4.2.4.2 |
| \#55 through <br> \#65 | $64.0 \mathrm{GT} / \mathrm{s}$ | Transmitter Preset Encoding 0000b through 1010b, as defined in § Section 4.2.4.2, in increasing order |
| \#66 through <br> \#84 | $64.0 \mathrm{GT} / \mathrm{s}$ | Transmitter Preset Encoding 0000b as defined in § Section 4.2.4.2 |

Subsequent entries to Polling.Compliance repeat the above sequence. For example, the state sequence which causes a Port to transmit the Compliance Pattern at a data rate of $5.0 \mathrm{GT} / \mathrm{s}$ and a de-emphasis level of -6 dB is: Polling.Active, Polling.Compliance ( $2.5 \mathrm{GT} / \mathrm{s}$ and -3.5 dB ), Polling.Active, Polling.Compliance ( $5.0 \mathrm{GT} / \mathrm{s}$ and -3.5 dB ), Polling.Active, Polling.Compliance ( $5.0 \mathrm{GT} / \mathrm{s}$ and -6 dB ).

The sequence must be set to Setting \#1 in the Polling. Configuration state if the Port supports $16.0 \mathrm{GT} / \mathrm{s}$ or higher Data Rates, or the Port's Receivers do not meet the $\mathrm{Z}_{\mathrm{RX}-\mathrm{DC}}$ specification for $2.5 \mathrm{GT} / \mathrm{s}$ when they are operating at $8.0 \mathrm{GT} / \mathrm{s}$ or higher data rates (see § Table 8-12). All Ports are permitted to set the sequence to Setting \#1 in the Polling.Configuration state.

# IMPLEMENTATION NOTE: COMPLIANCE LOAD BOARD USAGE TO GENERATE COMPLIANCE PATTERNS 

It is envisioned that the compliance load (base) board may send a 100 MHz signal for about 1 ms on one leg of a differential pair at 350 mV peak-to-peak on any Lane to cycle the device to the desired speed and de-emphasis level. The device under test is required, based on its maximum supported data rate, to cycle through the following settings in order, for each entry to Polling.Compliance from Polling.Active, starting with the first setting on the first entry to Polling.Compliance after the Fundamental Reset as defined in § Table 4-59.

- If the compliance pattern data rate is not $2.5 \mathrm{GT} / \mathrm{s}$ and any TS1 Ordered Sets were transmitted in Polling.Active prior to entering Polling.Compliance:
- The Transmitter sends two Compliance TS1 Ordered Sets if all of the following conditions are true:
- The current data rate is $2.5 \mathrm{GT} / \mathrm{s}$.

- Flit Mode is supported.
- The Transmitter is sequencing through one of the settings defined in § Table 4-59.
- Transmitter sends either one EIOS or two consecutive EIOSs prior to entering Electrical Idle.
- If the compliance pattern data rate is not $2.5 \mathrm{GT} / \mathrm{s}$ and TS1 Ordered Sets were not transmitted in Polling.Active prior to entering Polling.Compliance, the Transmitter must enter Electrical Idle without transmitting any EIOSs. During the period of Electrical Idle, the data rate is changed to the new speed and stabilized. If the frequency of operation will be $5.0 \mathrm{GT} / \mathrm{s}$, the de-emphasis/preset level must be set to -3.5 dB if the select_deemphasis variable is 1 b else it must be set to -6 dB . If the frequency of operation will be $8.0 \mathrm{GT} / \mathrm{s}$ or higher, the Transmitter preset value must be set to the value in the select_preset variable.
- If the Transmitter enters Electrical Idle while in Polling.Compliance, the period of Electrical Idle must be greater than 1 ms but must not exceed 2 ms .
- Behavior during Polling.Compliance after the data rate and de-emphasis/preset level are determined must follow the following rules:
- If the Port entered Polling.Compliance due to detecting eight consecutive TS1 Ordered Sets in Polling.Active with Compliance_Receive_Request asserted and Loopback_Request deasserted or both the Enter Compliance bit and the Enter Modified Compliance bit in the Link Control 2 Register are set to 1b then the Transmitter sends out the Modified Compliance Pattern at the above determined data rate with the error status Symbol set to all 0's on all Lanes that detected a Receiver during Detect.
- If the data rate is $2.5 \mathrm{GT} / \mathrm{s}$ or $5.0 \mathrm{GT} / \mathrm{s}$, a particular Lane's Receiver independently signifies a successful lock to the incoming Modified Compliance Pattern by looking for any one occurrence of the Modified Compliance Pattern and then setting the Pattern Lock bit (bit 7 of the error status Symbol) in the same Lane of its own transmitted Modified Compliance Pattern.
- The error status Symbols are not to be used for the lock process since they are undefined at any given moment.
- An occurrence is defined above as the following sequence of 8b/10b Symbols; K28.5, D21.5, K28.5, and D10.2 or the complement of each of the individual Symbols.
- The device under test must set the Pattern Lock bit of the Modified Compliance Pattern it transmits at the Transmitter package pin(s) after successfully locking to the incoming Modified Compliance Pattern within 1 ms of receiving the Modified Compliance Pattern at its Receiver package pin(s).
- If the data rate is $8.0 \mathrm{GT} / \mathrm{s}$ or higher: The Error_Status field is set to 00 h on entry to this substate. Each Lane sets the Pattern Lock bit independently when it achieves Block Alignment as described in § Section 4.2.2.2.1 . After Pattern Lock is achieved, Symbols received in Data Blocks are compared to the Idle data Symbol (00h) and each mismatched Symbol causes the Receiver Error Count field to be incremented by 1. The Receiver Error Count saturates at 127 (further mismatched Symbols do not change the Receiver Error Count). The Pattern Lock and Receiver Error Count information for each Lane is transmitted as part of the SKP Ordered Sets transmitted in that Lane's Modified Compliance Pattern. See § Section 4.2.8 for more information. The device under test must set the Pattern Lock bit in the SKP Ordered Set it transmits within 4 ms of receiving the Modified Compliance Pattern at its Receiver package pin(s).
- The scrambling requirements defined in § Section 4.2.2.4 are applied to the received Modified Compliance Pattern. For example, the scrambling LFSR seed is set per Lane, an EIEOS initializes the LFSR and SKP Ordered Sets do not advance the LFSR.

# IMPLEMENTATION NOTE: HANDLING BIT SLIP AND BLOCK ALIGNMENT § 

Devices should ensure that their Receivers have stabilized before attempting to obtain Block alignment and signaling Pattern Lock. For example, if an implementation expects to see bit slips in the initial few bits, it should wait for that time to be over before settling on a Block Alignment. Devices may also want to revalidate their Block alignment prior to setting the Pattern Lock bit.

- If the data rate is $2.5 \mathrm{GT} / \mathrm{s}$ or $5.0 \mathrm{GT} / \mathrm{s}$, once a particular Lane indicates it has locked to the incoming Modified Compliance Pattern the Receiver Error Count for that particular Lane is incremented every time a Receiver Error occurs.
- The error status Symbol uses the lower 7 bits as the Receiver Error Count field and this field will remain stuck at all 1's if the count reaches 127.
- The Receiver must not make any assumption about the 10-bit patterns it will receive when in this substate if $8 \mathrm{~b} / 10 \mathrm{~b}$ encoding is used.
- If the Enter Compliance bit in the Link Control 2 Register is 0b, the next state is Detect if directed
- Else if the Enter Compliance bit was set to 1b on entry to Polling.Compliance, next state is Polling.Active if any of the following conditions apply:
- The Enter Compliance bit in the Link Control 2 Register has changed to 0b
- The Port is an Upstream Port and an EIOS is received on any Lane. The Enter Compliance bit is reset to 0 b when this condition is true.

If the Transmitter was transmitting at a data rate other than $2.5 \mathrm{GT} / \mathrm{s}$, or the Enter Compliance bit in the Link Control 2 Register was set to 1b during entry to Polling.Compliance, the Transmitter sends eight consecutive EIOS and enters Electrical Idle prior to transitioning to Polling.Active. During the period of Electrical Idle, the data rate is changed to $2.5 \mathrm{GT} / \mathrm{s}$ and stabilized and the de-emphasis level is set to -3.5 dB .

Note: Sending multiple EIOS provides enough robustness such that the other Port detects at least one EIOS and exits Polling.Compliance substate when the configuration register mechanism was used for entry.

- Else if the Port entered Polling.Compliance due to the Enter Compliance bit of the Link Control 2 Register being set to 1b and the Enter Modified Compliance bit of the Link Control 2 Register being set to 0b:
a. Transmitter sends out the compliance pattern on all Lanes that detected a Receiver during Detect at the data rate and de-emphasis/preset level determined above.
b. Next state is Polling.Active if any of the following two conditions are true:

1. The Enter Compliance bit in the Link Control 2 Register has changed to 0b (from 1b) since entering Polling.Compliance.
2. The Port is an Upstream Port, the Enter Compliance bit in the Link Control 2 Register is set to 1 b and an EIOS has been detected on any Lane. The Enter Compliance bit is reset to 0 b when this condition is true.

The Transmitter sends eight consecutive EIOSs and enters Electrical Idle prior to transitioning to Polling.Active. During the period of Electrical Idle, the data rate is changed to $2.5 \mathrm{GT} / \mathrm{s}$ and stabilized.

Note: Sending multiple EIOSs provides enough robustness such that the other Port detects at least one EIOS and exits Polling.

- Else:

a. Transmitter sends out the following patterns on Lanes that detected a Receiver during Detect at the data rate and de-emphasis/preset level determined above:

- For Settings \#1 to \#25, \#35 to \#45, and \#55 to \#65: Compliance Pattern on all Lanes.
- For Setting \#26, \#46, \#66: Jitter Measurement Pattern on all Lanes.
- For Setting \#27, \#47, \#67: Jitter Measurement Pattern on Lanes 0/8 and Compliance Pattern on all other Lanes.
- For Setting \#28, \#48, \#68: Jitter Measurement Pattern on Lanes 1/9 and Compliance Pattern on all other Lanes.
- For Setting \#29, \#49, \#69: Jitter Measurement Pattern on Lanes 2/10 and Compliance Pattern on all other Lanes.
- For Setting \#30, \#50, \#70: Jitter Measurement Pattern on Lanes 3/11 and Compliance Pattern on all other Lanes.
- For Setting \#31, \#51, \#71: Jitter Measurement Pattern on Lanes 4/12 and Compliance Pattern on all other Lanes.
- For Setting \#32, \#52, \#72: Jitter Measurement Pattern on Lanes 5/13 and Compliance Pattern on all other Lanes.
- For Setting \#33, \#53, \#73: Jitter Measurement Pattern on Lanes 6/14 and Compliance Pattern on all other Lanes.
- For Setting \#34, \#54, \#74: Jitter Measurement Pattern on Lanes 7/15 and Compliance Pattern on all other Lanes.
- For Setting \#75: High Swing Toggle Pattern on all Lanes
- For Setting \#76: High Swing Toggle Pattern on Lanes 0/8 and Compliance Pattern on all other Lanes.
- For Setting \#77: High Swing Toggle Pattern on Lanes 1/9 and Compliance Pattern on all other Lanes.
- For Setting \#78: High Swing Toggle Pattern on Lanes 2/10 and Compliance Pattern on all other Lanes.
- For Setting \#79: High Swing Toggle Pattern on Lanes 3/11 and Compliance patter on all other Lanes.
- For Setting \#80: High Swing Toggle Pattern on Lanes 4/12 and Compliance Pattern on all other Lanes.
- For Setting \#81: High Swing Toggle Pattern on Lanes 5/13 and Compliance Pattern on all other Lanes.
- For Setting \#82: High Swing Toggle Pattern on Lanes 6/14 and Compliance Pattern on all other Lanes.
- For Setting \#83: High Swing Toggle Pattern on Lanes 7/15 and Compliance Pattern on all other Lanes.
- For Setting \#84: Low Swing Toggle Pattern on all Lanes
b. Next state is Polling.Active if an exit of Electrical Idle is detected at the Receiver of any Lane that detected a Receiver during Detect. If the Transmitter is transmitting at a data rate other than $2.5 \mathrm{GT} / \mathrm{s}$, the Transmitter sends eight consecutive EIOSs and enters Electrical Idle prior to transitioning to Polling.Active. During the period of Electrical Idle, the data rate is changed to $2.5 \mathrm{GT} / \mathrm{s}$ and stabilized.

# 4.2.7.2.3 Polling.Configuration $\S$ 

- Receiver must invert polarity if necessary (see § Section 4.2.5.5).
- The Transmit Margin field of the Link Control 2 Register must be reset to 000b on entry to this substate.
- The Transmitter's Polling.Compliance sequence setting is updated, if required, as described in § Section 4.2.7.2.2 .
- Transmitter sends TS2 Ordered Sets with Link and Lane numbers set to PAD on all Lanes that detected a Receiver during Detect.
- The Data Rate Identifier Symbol of the TS2 Ordered Sets must advertise all data rates between $2.5 \mathrm{GT} / \mathrm{s}$ and $32.0 \mathrm{GT} / \mathrm{s}$ that the Port supports, including those that it does not intend to use.

Note: Ports are not permitted to advertise higher than $32.0 \mathrm{GT} / \mathrm{s}$ data rates in this state.

- The next state is Configuration after eight consecutive TS2 Ordered Sets, with Link and Lane numbers set to PAD, are received on any Lanes that detected a Receiver during Detect, and 16 TS2 Ordered Sets are transmitted after receiving one TS2 Ordered Set.
- Otherwise, next state is Detect after a 48 ms timeout.


### 4.2.7.2.4 Polling.Speed $\S$

This state is unreachable given that the Link comes up to L0 in $2.5 \mathrm{GT} / \mathrm{s}$ data rate only and changes speed by entering Recovery.

## IMPLEMENTATION NOTE: SUPPORT FOR HIGHER DATA RATES THAN 2.5 GT/S $\S$

A Link will initially train to the L0 state at the $2.5 \mathrm{GT} / \mathrm{s}$ data rate even if both sides are capable of operating at a data rate greater than $2.5 \mathrm{GT} / \mathrm{s}$. Supported higher data rates are advertised in the TS Ordered Sets. The other side's speed capability is registered during the Configuration.Complete substate. Based on the highest supported common data rate, either side can initiate a change in speed from the L0 state by transitioning to Recovery.

![img-67.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-67.jpeg)

OM13801B
Figure 4-69 Polling Substate Machine

# 4.2.7.3 Configuration 

The Configuration substate machine is shown in § Figure 4-70.

### 4.2.7.3.1 Configuration. Linkwidth. Start 6

### 4.2.7.3.1.1 Downstream Lanes 6

- Next state is Disabled if directed.
- The clause "if directed" applies to a Downstream Port that is instructed by a higher Layer to assert Disable_Link_Request (TS1 and TS2) on all Lanes that detected a Receiver during Detect.
- Next state is Loopback if directed by an implementation specific method and the Transmitter is capable of being a Loopback Lead.
- The clause "if directed" applies to a Port that is instructed by a higher Layer to assert Loopback_Request on all Lanes that detected a Receiver during Detect.

- In the optional case where a crosslink is supported, the next state is Disabled after all Lanes that are transmitting TS1 Ordered Sets receive two consecutive TS1 Ordered Sets with Disable_Link_Request asserted.
- Next state is Loopback if one of the following two conditions are satisfied:
- All Lanes that are transmitting TS1 Ordered Sets, that are also receiving TS1 Ordered Sets, receive Loopback_Request asserted in two consecutive TS1 Ordered Sets.
- Any Lane that is transmitting TS1 Ordered Sets receives two consecutive TS1 Ordered Sets with Loopback_Request asserted and with the Enhanced Link Behavior Control bits set to 01b.

A Port that is capable of transmitting at the 64.0 GT/s data rate may receive TS1 Ordered Sets with the Flit Mode Supported bit set to 1b and the Supported Link Speeds field set to 10111 b .

The device receiving the Ordered Set with Loopback_Request asserted becomes the Loopback Follower. If the Loopback Follower supports 1b/1b encoding, it must take into account whether SRIS clocking is enabled (Symbol 4, Bit 7) for identifying SKP OS boundary during Loopback.

- The Transmitter sends TS1 Ordered Sets with selected Link numbers and sets Lane numbers to PAD on all the active Downstream Lanes if LinkUp is 0b or if the LTSSM is not initiating upconfiguration of the Link width. In addition, if upconfigure_capable is set to 1b, and the LTSSM is not initiating upconfiguration of the Link width, the LTSSM sends TS1 Ordered Sets with the selected Link number and sets the Lane number to PAD on each inactive Lane after it detected an exit from Electrical Idle since entering Recovery and has subsequently received two consecutive TS1 Ordered Sets with the Link and Lane numbers each set to PAD while in this substate.
- On transition to this substate from Polling, any Lane that detected a Receiver during Detect is considered an active Lane.
- On transition to this substate from Recovery, any Lane that is part of the configured Link the previous time through Configuration.Complete is considered an active Lane.
- The Data Rate Identifier Symbol of the TS1 Ordered Sets must advertise all data rates that the Port supports, including those that it does not intend to use.
- If LinkUp is 1b and the LTSSM is initiating upconfiguration of the Link width, initially it transmits TS1 Ordered Sets with both the Link and Lane numbers set to PAD on the current set of active Lanes; the inactive Lanes it intends to activate; and those Lanes where it detected an exit from Electrical Idle since entering Recovery and has received two consecutive TS1 Ordered Sets with the Link and Lane numbers each set to PAD. The LTSSM transmits TS1 Ordered Sets with the selected Link number and the Lane number set to PAD when each of the Lanes transmitting TS1 Ordered Sets receives two consecutive TS1 Ordered Sets with the Link and Lane numbers each set to PAD or 1 ms has expired since entering this substate.
- After activating any inactive Lane, the Transmitter must wait for its TX common mode to settle before exiting from Electrical Idle and transmitting the TS1 Ordered Sets.
- Link numbers are only permitted to be different for groups of Lanes capable of being a unique Link.
- Note: An example of Link number assignments is a set of eight Downstream Lanes capable of negotiating to become one x 8 Port when connected to one component or two x 4 Ports when connected to two different components. The Downstream Lanes send out TS1 Ordered Sets with the Link number set to N on four Lanes and Link number set to $\mathrm{N}+1$ on the other four Lanes. The Lane numbers are all set to PAD.
- If any Lanes first received at least one or more TS1 Ordered Sets with a Link and Lane number set to PAD, the next state is Configuration.Linkwidth.Accept immediately after any of those same Downstream Lanes receive two consecutive TS1 Ordered Sets with a non-PAD Link number that matches any of the transmitted Link numbers, and with a Lane number set to PAD.
- If the crosslink configuration is not supported, the condition of first receiving a Link and Lane number set to PAD is always true.

- Else: Optionally, if LinkUp is 0b and if crosslinks are supported, then all Downstream Lanes that detected a Receiver during Detect must first transmit 16 to 32 TS1 Ordered Sets with a non-PAD Link number and PAD Lane number and after this occurs if any Downstream Lanes receive two consecutive TS1 Ordered Sets with a Link number different than PAD and a Lane Number set to PAD, the Downstream Lanes are now designated as Upstream Lanes and a new random crosslink timeout is chosen (see $\mathrm{T}_{\text {crosslink }}$ in $\S$ Table 8-7). The next state is Configuration.Linkwidth.Start as Upstream Lanes.
- Note: This supports the optional crosslink where both sides may try to act as a Downstream Port. This is resolved by making both Ports become Upstream and assigning a random timeout until one side of the Link becomes a Downstream Port and the other side remains an Upstream Port. This timeout must be random even when hooking up two of the same devices so as to eventually break any possible deadlock.
- If crosslinks are supported, receiving a sequence of TS1 Ordered Sets with a Link number of PAD followed by a Link number of non-PAD that matches the transmitted Link number is only valid when not interrupted by the reception of a TS2 Ordered Set.


# IMPLEMENTATION NOTE: CROSSLINK INITIALIZATION 

In the case where the Downstream Lanes are connected to both Downstream Lanes (crosslink) and Upstream Lanes, the Port with the Downstream Lanes may continue with a single LTSSM as described in this section or optionally, split into multiple LTSSMs.

- The next state is Detect after a 24 ms timeout.


### 4.2.7.3.1.2 Upstream Lanes

- In the optional case where crosslinks are supported the next state is Disabled if directed.
- The clause "if directed" only applies to an optional crosslink Port that is instructed by a higher Layer to assert Disable_Link_Request (TS1 and TS2) on all Lanes that detected a Receiver during Detect.
- Next state is Loopback if directed to this state by an implementation specific method.
- The clause "if directed" applies to a Port that is instructed by a higher Layer to assert Loopback_Request (TS1 and TS2) on all Lanes that detected a Receiver during Detect.
- Next state is Disabled after any Lanes that are transmitting TS1 Ordered Sets receive two consecutive TS1 Ordered Sets with Disable_Link_Request asserted.
- In the optional case where a crosslink is supported, the next state is Disabled only after all Lanes that are transmitting TS1 Ordered Sets, that are also receiving TS1 Ordered Sets, receive Disable_Link_Request asserted in two consecutive TS1 Ordered Sets.
- Next state is Loopback if one of the following two conditions are satisfied:
- All Lanes that are transmitting TS1 Ordered Sets, that are also receiving TS1 Ordered Sets, receive Loopback_Request asserted in two consecutive TS1 Ordered Sets.
- Any Lane that is transmitting TS1 Ordered Sets receives two consecutive TS1 Ordered Sets with Loopback_Request asserted and with the Enhanced Link Behavior Control bits set to 01b.

A Port that is capable of transmitting at the 64.0 GT/s data rate may receive TS1 Ordered Sets with the Flit Mode Supported bit set to 1b and the Supported Link Speeds field set to 10111 b.

The device receiving the Ordered Set with Loopback_Request asserted becomes the Loopback Follower. If the Loopback Follower supports 1b/1b encoding, it must take into account whether SRIS Clocking is enabled (Symbol 4, Bit $7=1 \mathrm{~b}$ ) for identifying SKP OS boundaries during Loopback.

- The Transmitter sends out TS1 Ordered Sets with Link numbers and Lane numbers set to PAD on all the active Upstream Lanes; the inactive Lanes it is initiating to upconfigure the Link width; and if upconfigure capable is set to 1 b , on each of the inactive Lanes where it detected an exit from Electrical Idle since entering Recovery and has subsequently received two consecutive TS1 Ordered Sets with Link and Lane numbers, each set to PAD, in this substate.
- On transition to this substate from Polling, any Lane that detected a Receiver during Detect is considered an active Lane.
- On transition to this substate from Recovery, any Lane that is part of the configured Link the previous time through Configuration.Complete is considered an active Lane.
- On transition to this substate from Recovery, if the transition is not caused by LTSSM timeout, the Transmitter must set the Autonomous Change bit (Symbol 4 bit 6) to 1b in the TS1 Ordered Sets that it sends while in the Configuration state if the Transmitter intends to change the Link width for autonomous reasons.
- The Data Rate Identifier Symbol of the TS1 Ordered Sets must advertise all data rates that the Port supports, including those that it does not intend to use.
- If any Lane receives two consecutive TS1 Ordered Sets with Link numbers that are different than PAD and Lane number set to PAD, a single Link number is selected and Lane number set to PAD are transmitted on all Lanes that both detected a Receiver and also received two consecutive TS1 Ordered Sets with Link numbers that are different than PAD and Lane number set to PAD. Any left over Lanes that detected a Receiver during Detect must transmit TS1 Ordered Sets with the Link and Lane number set to PAD. The next state is Configuration. Linkwidth.Accept:
- If the LTSSM is initiating upconfiguration of the Link width, it waits until it receives two consecutive TS1 Ordered Sets with a non-PAD Link Number and a PAD Lane number on all the inactive Lanes it wants to activate, or, 1 ms after entry to this substate, it receives two consecutive TS1 Ordered Sets on any Lane with a non-PAD Link number and PAD Lane number, whichever occurs earlier, before transmitting TS1 Ordered Sets with selected Link number and Lane number set to PAD.
- It is recommended that any possible multi-Lane Link that received an error in a TS1 Ordered Set or lost 128b/130b Block Alignment or Block/Flit alignment with 1b/1b encoding on a subset of the received Lanes; delay the evaluation listed above by an additional two, or more, TS1 Ordered Sets when using 8b/10b encoding, or by an additional 34, or more, TS1 Ordered Sets when using 128b/ 130b or 1b/1b encoding, but must not exceed 1 ms , so as not to prematurely configure a smaller Link than possible.
- After activating any inactive Lane, the Transmitter must wait for its TX common mode to settle before exiting Electrical Idle and transmitting the TS1 Ordered Sets.
- Optionally, if LinkUp is 0b and if crosslinks are supported, then all Upstream Lanes that detected a Receiver during Detect must first transmit 16-32 TS1 Ordered Sets with a PAD Link number and PAD Lane number and after this occurs and if any Upstream Lanes first receive two consecutive TS1 Ordered Sets with Link and Lane numbers set to PAD, then:
- The Transmitter continues to send out TS1 Ordered Sets with Link numbers and Lane numbers set to PAD.
- If any Lanes receive two consecutive TS1 Ordered Sets with Link numbers that are different than PAD and Lane number set to PAD, a single Link number is selected and Lane number set to PAD are transmitted on all Lanes that both detected a Receiver and also received two consecutive TS1 Ordered Sets with Link numbers that are different than PAD and Lane number set to PAD. Any left

over Lanes that detected a Receiver during Detect must transmit TS1 Ordered Sets with the Link and Lane number set to PAD. The next state is Configuration.Linkwidth.Accept.

- It is recommended that any possible multi-Lane Link that received an error in a TS1 Ordered Set or lost 128b/130b Block Alignment or Block/Flit alignment with 1b/1b encoding on a subset of the received Lanes; delay the evaluation listed above by an additional two, or more, TS1 Ordered Sets when using 8b/10b encoding, or by an additional 34, or more, TS1 Ordered Sets when using 128b/130b or 1b/1b encoding, but must not exceed 1 ms , so as not to prematurely configure a smaller Link than possible.
- Otherwise, after a T Crosslink timeout, 16 to 32 TS2 Ordered Sets with PAD Link numbers and PAD Lane numbers are sent. The Upstream Lanes become Downstream Lanes and the next state is Configuration.Linkwidth.Start as Downstream Lanes.
- Note: This optional behavior is required for crosslink behavior where two Ports may start off with Upstream Ports, and one will eventually take the lead as a Downstream Port.
- The next state is Detect after a 24 ms timeout.


# 4.2.7.3.2 Configuration.Linkwidth.Accept 

### 4.2.7.3.2.1 Downstream Lanes

- If a configured Link can be formed with at least one group of Lanes that received two consecutive TS1 Ordered Sets with the same received Link number (non-PAD and matching one that was transmitted by the Downstream Lanes), TS1 Ordered Sets are transmitted with the same Link number and unique non-PAD Lane numbers are assigned to all these same Lanes. The next state is Configuration.Lanenum.Wait.
- The assigned non-PAD Lane numbers must range from 0 to $n-1$, be assigned sequentially to the same grouping of Lanes that are receiving the same Link number, and Downstream Lanes which are not receiving TS1 Ordered Sets must not disrupt the initial sequential numbering of the widest possible Link. Any left over Lanes must transmit TS1 Ordered Sets with the Link and Lane number set to PAD.
- It is recommended that any possible multi-Lane Link that received an error in a TS1 Ordered Set or lost 128b/130b Block Alignment or Block/Flit alignment with 1b/1b encoding on a subset of the received Lanes delay the evaluation listed above by an additional two, or more, TS1 Ordered Sets when using 8b/10b encoding, or by an additional 34, or more, TS1 Ordered Sets when using 128b/ 130b or 1b/1b encoding, but must not exceed 1 ms , so as not to prematurely configure a smaller Link than possible.
- The use_modified_TS1_TS2_Ordered_Set variable must be set to 1b if all of the following conditions are true:
- LinkUp = 0b
- The component had transmitted Modified TS1/TS2 Ordered Sets supported value (11b) in the Enhanced Link Behavior Control field in Symbol 5 of TS1 and TS2 Ordered Sets in Polling and Configuration states since entering the Polling State
- The received eight consecutive TS2 Ordered Sets on all Lanes of the configured Link that could be formed (see 1st bullet of $\S$ Section 4.2.7.3.2.1 ) that were part of the group that caused the transition from Polling.Configuration to Configuration state had the Modified TS1/TS2 Ordered Sets supported value (11b) in the Enhanced Link Behavior Control field in Symbol 5 and 32.0 GT/s data rate is supported bit is Set to 1b in the received eight consecutive TS2 Ordered Sets
- The Flit_Mode_Enabled variable must be set to 1b if all of the following conditions are true:

- LinkUp = 0b
- The component had transmitted Flit Mode Supported bit in the 'Data Rate Identifier' field (Symbol 4, Bit 0) in the TS1 and TS2 Ordered Sets in Polling and Configuration states since entering the Polling State
- The received eight consecutive TS2 Ordered Sets on all Lanes of the currently configured Link that caused the transition from Polling.Configuration to Configuration state had the Flit Mode Supported bit in the Data Rate Identifier field (Symbol 4, Bit 0) set to 1b in the received eight consecutive TS2 Ordered Sets
- The next state is Detect after a 2 ms timeout or if no Link can be configured or if all Lanes receive two consecutive TS1 Ordered Sets with Link and Lane numbers set to PAD.


# 4.2.7.3.2.2 Upstream Lanes 

- If a configured Link can be formed using Lanes that transmitted a non-PAD Link number which are receiving two consecutive TS1 Ordered Sets with the same non-PAD Link number and any non-PAD Lane number, TS1 Ordered Sets are transmitted with the same non-PAD Link number and Lane numbers that, if possible, match the received Lane numbers or are different, if necessary (i.e., Lane reversed). The next state is Configuration.Lanenum.Wait.
- The received consecutive TS1 Ordered Sets may be either standard TS1 Ordered Sets or Modified TS1 Ordered Sets. Modified TS1 Ordered Sets will only be received if the conditions to Set the use_modified_TS1_TS2_Ordered_Set variable (as described below) are met.
- The newly assigned Lane numbers must range from 0 to m -1, be assigned sequentially only to some continuous grouping of Lanes that are receiving non-PAD Lane numbers (i.e., Lanes which are not receiving any TS1 Ordered Sets always disrupt a continuous grouping and must not be included in this grouping), must include either Lane 0 or Lane n-1 (largest received Lane number), and m-1 must be equal to or smaller than the largest received Lane number ( $n-1$ ). Remaining Lanes must transmit TS1 Ordered Sets with Link and Lane numbers set to PAD.
- If any possible multi-Lane Link received an error in a TS1 Ordered Set, lost 128b/130b Block Alignment, or lost Block/Flit alignment with 1b/1b encoding on a subset of the received Lanes, it is recommended to do the following to avoid configuring a smaller Link than is possible:
- When using 8b/10b encoding, delay the evaluation listed above by an additional two or more TS1 Ordered Sets, but must not delay by more than 1 ms .
- When using 128b/130b or 1b/1b encoding, delay the evaluation listed above by an additional 34 or more TS1 Ordered Sets, but must not delay by more than 1 ms .
- The use_modified_TS1_TS2_Ordered_Set variable must be set to 1b if all of the following conditions are true:
- LinkUp = 0b
- The component has transmitted Modified TS1/TS2 Ordered Sets supported value (11b) in the Enhanced Link Behavior Control field in Symbol 5 of all TS1 and TS2 Ordered Sets in Polling and Configuration states since entering the Polling State
- The received eight consecutive TS2 Ordered Sets on all Lanes of the configured Link that could be formed (see 1st bullet of $\S$ Section 4.2.7.3.2.2 ) that were part of the group that caused the transition from Polling.Configuration to Configuration state had the Modified TS1/TS2 Ordered Sets supported value (11b) in the Enhanced Link Behavior Control field in Symbol 5 and 32.0 GT/s data rate is supported bit is Set to 1b in the received eight consecutive TS2 Ordered Sets
- The Flit_Mode_Enabled variable must be set to 1b if all of the following conditions are true:

- LinkUp $=0 b$
- The component had transmitted Flit Mode Supported bit in the 'Data Rate Identifier' field (Symbol 4, Bit 0) in the TS1 and TS2 Ordered Sets in Polling and Configuration states since entering the Polling State
- The received eight consecutive TS2 Ordered Sets on all Lanes of the currently configured Link that caused the transition from Polling.Configuration to Configuration state had the Flit Mode Supported bit in the Data Rate Identifier field (Symbol 4, Bit 0) set to 1b in the received eight consecutive TS2 Ordered Sets


# IMPLEMENTATION NOTE: NEGOTIATING FLIT MODE AND THE MODIFIED TS1/TS2 USAGE 6 

Negotiating Flit Mode and the Modified TS1/TS2 usage is orthogonal (i.e., a device can advertise and negotiate support for neither, either, or both). This note applies to the Downstream and Upstream Ports.

- The next state is Detect after a 2 ms timeout or if no Link can be configured or if all Lanes receive two consecutive TS1 Ordered Sets with Link and Lane numbers set to PAD.

# IMPLEMENTATION NOTE: EXAMPLE CASES 

Notable examples related to the configuration of Downstream Lanes:

1. A $\times 8$ Downstream Port, which can be divided into two $\times 4$ Links, sends two different Link numbers on to two $x 4$ Upstream Ports. The Upstream Ports respond simultaneously by picking the two Link numbers. The Downstream Port will have to choose one of these sets of Link numbers to configure as a Link, and leave the other for a secondary LTSSM to configure (which will ultimately happen in Configuration.Complete).
2. A $\times 8$ Downstream Port where only seven Lanes are receiving TS1 Ordered Sets with the same received Link number (non-PAD and matching one that was transmitted by the Downstream Lanes) and an eighth Lane, which is in the middle or adjacent to those same Lanes, is not receiving a TS1 Ordered Set. In this case, the eighth Lane is treated the same as the other seven Lanes and Lane numbering for a x8 Lane should occur as described above.

Notable examples related to the configuration of Upstream Lanes:

1. A $\times 8$ Upstream Port is presented with Lane numbers that are backward from the preferred numbering. If the optional behavior of Lane reversal is supported by the Upstream Port, the Upstream Port transmits the same Lane numbers back to the Downstream Port. Otherwise, the opposite Lane numbers are transmitted back to the Downstream Port, and it will be up to the Downstream Port to optionally fix the Lane ordering or exit Configuration.

Optional Lane reversal behavior is required to configure a Link where the Lane numbers are reversed and the Downstream Port does not support Lane reversal. Specifically, the Upstream Port Lane reversal will accommodate the scenario where the default Upstream sequential Lane numbering ( 0 to $n-1$ ) is receiving a reversed Downstream sequential Lane number ( $n-1$ to 0 ).
2. A $\times 8$ Upstream Port is not receiving TS1 Ordered Sets on the Upstream Port Lane 0:
a. In the case where the Upstream Port can only support a $x 8$ or $x 1$ Link and the Upstream Port can support Lane reversal. The Upstream Port will assign a Lane 0 to only the received Lane 7 (received Lane number $n-1$ ) and the remaining seven Lanes must transmit TS1 Ordered Sets with Link and Lane numbers set to PAD.
b. In the case where the Upstream Port can only support a $x 8$ or $x 1$ Link and the Upstream Port cannot support Lane reversal. No Link can be formed and the Upstream Port will eventually timeout after 2 ms and exit to Detect.
3. An optional $\times 8$ Upstream crosslink Port, which can be divided into two $\times 4$ Links, is attached to two $\times 4$ Downstream Ports that present the same Link number, and each $\times 4$ Downstream Port presents Lane numbers simultaneously that were each numbered 0 to 3 . The Upstream Port will have to choose one of these sets of Lane numbers to configure as a Link, and leave the other for a second pass through Configuration.

### 4.2.7.3.3 Configuration.Lanenum.Accept

In this sub-state, if use_modified_TS1_TS2_Ordered_Set variable is set to 1b:

- Transmitter must send Modified TS1 Ordered sets instead of TS1 Ordered Sets

- Receiver must check for receipt of Modified TS1 Ordered Sets instead of TS1 Ordered Sets [Note: See § Section 4.2.5.1 for the definition of identical consecutive modified TS1 Ordered Sets.)


# 4.2.7.3.3.1 Downstream Lanes 

- If two consecutive TS1 Ordered Sets are received with non-PAD Link and non-PAD Lane numbers that match all the non-PAD Link and non-PAD Lane numbers (or reversed Lane numbers if Lane reversal is optionally supported) that are being transmitted in Downstream Lane TS1 Ordered Sets, the next state is Configuration.Complete. If the use_modified_TS1_TS2_Ordered_Set variable is Set and an Alternate Protocol Negotiation is being performed, the transition to Configuration.Complete must be delayed for $10 \mu$ s or until the Downstream Port receives the Upstream Port's response to that protocol request (whichever happens first). See § Section 4.2.5.2 for Alternate Protocol Negotiation details. Note that Retimers are permitted to delay the transition to Configuration.Complete, as described in § Section 4.3.9.
- The SRIS_Mode_Enabled variable is Set to 1b if all of the following conditions are true:
- $\operatorname{LinkUp}=0 \mathrm{~b}$
- The Port has been transmitting SRIS Clocking (Symbol 4, bit $7=1 \mathrm{~b}$ ) in the transmitted TS1 Ordered Sets since it entered Configuration state.
- The Link Bandwidth Management Status and Link Autonomous Bandwidth Status bits of the Link Status Register must be updated as follows on a Link bandwidth change if the current transition to Configuration state was from the Recovery state:
a. If the bandwidth change was initiated by the Downstream Port due to reliability issues, the Link Bandwidth Management Status bit is Set.
b. Else if the bandwidth change was not initiated by the Downstream Port and the Autonomous Change bit (Symbol 4 bit 6) in two consecutive received TS1 Ordered Sets is 0b, the Link Bandwidth Management Status bit is Set.
c. Else the Link Autonomous Bandwidth Status bit is Set.
- The condition of Reversed Lane numbers is defined strictly as the Downstream Lane 0 receiving a TS1 Ordered Set with a Lane number equal to n -1 and the Downstream Lane n -1 receiving a TS1 Ordered Set with a Lane number equal to 0 .
- If any possible multi-Lane Link received an error in a TS1 Ordered Set, lost 128b/130b Block Alignment, or lost Block/Flit alignment with 1b/1b encoding on a subset of the received Lanes, it is recommended to do the following to avoid configuring a smaller Link than is possible:
- When using 8b/10b encoding, delay the evaluation listed above by an additional two or more TS1 Ordered Sets, but must not delay by more than 1 ms .
- When using 128b/130b or 1b/1b encoding, delay the evaluation listed above by an additional 34 or more TS1 Ordered Sets, but must not delay by more than 1 ms .
- If a configured Link can be formed with any subset of the Lanes that receive two consecutive TS1 Ordered Sets with the same transmitted non-PAD Link numbers and any non-PAD Lane numbers, TS1 Ordered Sets are transmitted with the same non-PAD Link numbers and new Lane numbers assigned and the next state is Configuration.Lanenum.Wait.
- The newly assigned transmitted Lane numbers must range from 0 to $\mathrm{m}-1$, be assigned sequentially only to some continuous grouping of the Lanes that are receiving non-PAD Lane numbers (i.e., Lanes which are not receiving any TS1 Ordered Sets always disrupt a continuous grouping and must not be included in this grouping), must include either Lane 0 or Lane n-1 (largest received Lane number), and $\mathrm{m}-1$ must be equal to or smaller than the largest received Lane number ( $\mathrm{n}-1$ ). Any left over Lanes must transmit TS1 Ordered Sets with the Link and Lane number set to PAD.

- If any possible multi-Lane Link received an error in a TS1 Ordered Set, lost 128b/130b Block Alignment, or lost Block/Flit alignment with 1b/1b encoding on a subset of the received Lanes, it is recommended to do the following to avoid configuring a smaller Link than is possible:
- When using 8b/10b encoding, delay the evaluation listed above by an additional two or more TS1 Ordered Sets, but must not delay by more than 1 ms .
- When using 128b/130b or 1b/1b encoding, delay the evaluation listed above by an additional 34 or more TS1 Ordered Sets, but must not delay by more than 1 ms .
- The next state is Detect if no Link can be configured or if all Lanes receive two consecutive TS1 Ordered Sets with Link and Lane numbers set to PAD.


# 4.2.7.3.3.2 Upstream Lanes 

- If two consecutive TS2 Ordered Sets are received with non-PAD Link and non-PAD Lane numbers that match all non-PAD Link and non-PAD Lane numbers that are being transmitted in Upstream Lane TS1 Ordered Sets, the next state is Configuration.Complete. If the use_modified_TS1_TS2_Ordered_Set variable is Set, an Alternate Protocol Negotiation was performed, and the Downstream Port decided not to use any Alternate Protocol, the received TS2 Ordered Sets will have Modified TS Usage set to a value as defined in § Table 4-39. See § Section 4.2.5.2 for Alternate Protocol Negotiation details.

The SRIS_Mode_Enabled variable is set to 1 b if all of the following conditions are true:

- $\operatorname{LinkUp}=0 \mathrm{~b}$
- Any configured Lane in the Port has the SRIS Clocking bit set (Symbol 4, bit $7=1$ b) in the two consecutive TS2 Ordered Sets

Note that Retimers are permitted to delay the transition to Configuration.Complete, as described in § Section 4.3.9 .

## IMPLEMENTATION NOTE: CLOCKING WITH SRIS MODE VS. NON-SRIS MODE

Clocking with SRIS mode vs. non-SRIS mode advertisement was added for Flit Mode support since there is no sync hdr in the 1b/1b encoding. It is advertised by the Downstream Port. However, it is defined as orthogonal to Flit Mode support. This note applies to the Downstream and Upstream Ports.

- If a configured Link can be formed with any subset of the Lanes that receive two consecutive TS1 Ordered Sets with the same transmitted non-PAD Link numbers and any non-PAD Lane numbers, TS1 Ordered Sets are transmitted with the same non-PAD Link numbers and new Lane numbers assigned and the next state is Configuration.Lanenum.Wait.
- The newly assigned transmitted Lane numbers must range from 0 to m -1, be assigned sequentially only to some continuous grouping of Lanes that are receiving non-PAD Lane numbers (i.e., Lanes which are not receiving any TS1 Ordered Sets always disrupt a continuous grouping and must not be included in this grouping), must include either Lane 0 or Lane n-1 (largest received Lane number), and m -1 must be equal to or smaller than the largest received Lane number ( $n-1$ ). Any left over Lanes must transmit TS1 Ordered Sets with the Link and Lane number set to PAD.
- If any possible multi-Lane Link received an error in a TS1 Ordered Set, lost 128b/130b Block Alignment, or lost Block/Flit alignment with 1b/1b encoding on a subset of the received Lanes, it is recommended to do the following to avoid configuring a smaller Link than is possible:

- When using 8b/10b encoding, delay the evaluation listed above by an additional two or more TS1 Ordered Sets, but must not delay by more than 1 ms .
- When using 128b/130b or 1b/1b encoding, delay the evaluation listed above by an additional 34 or more TS1 Ordered Sets, but must not delay by more than 1 ms .
- The next state is Detect if no Link can be configured or if all Lanes receive two consecutive TS1 Ordered Sets with Link and Lane numbers set to PAD.


# 4.2.7.3.4 Configuration.Lanenum.Wait 5 

In this sub-state, if use_modified_TS1_TS2_Ordered_Set variable is set to 1b:

- Transmitter must send Modified TS1 Ordered Sets instead of TS1 Ordered Sets
- Receiver must check for receipt of Modified TS1 Ordered Sets instead of TS1 Ordered Sets though it may receive TS1 Ordered Sets initially while the Link partner is transitioning to this sub-state [Note: These must be identical consecutive Modified TS1 Ordered Sets with valid parity in the last Symbol]


### 4.2.7.3.4.1 Downstream Lanes 6

- The next state is Configuration.Lanenum.Accept if any of the Lanes that detected a Receiver during Detect receive two consecutive TS1 Ordered Sets which have a Lane number different from when the Lane first entered Configuration.Lanenum.Wait, and not all the Lanes' Link numbers are set to PAD or two consecutive TS1 Ordered Sets have been received on all Lanes, with Link and Lane numbers that match what is being transmitted on all Lanes.

The Upstream Lanes are permitted to delay up to 1 ms before transitioning to Configuration.Lanenum.Accept.
The reason for delaying up to 1 ms before transitioning is to prevent received errors or skew between Lanes affecting the final configured Link width.

The condition of requiring reception of any Lane number different from when the Lane(s) first entered Configuration.Lanenum.Wait is necessary in order to allow the two Ports to settle on an agreed upon Link width. The exact meaning of the statement "any of the Lanes receive two consecutive TS1 Ordered Sets, which have a Lane number different from when the Lane first entered Configuration.Lanenum.Wait" requires that a Lane number must have changed from when the Lanes most recently entered Configuration.Lanenum.Wait before a transition to Configuration.Lanenum.Accept can occur.

- The next state is Detect after a 2 ms timeout or if all Lanes receive two consecutive TS1 Ordered Sets with Link and Lane numbers set to PAD.


### 4.2.7.3.4.2 Upstream Lanes 8

- The next state is Configuration.Lanenum.Accept
a. If any of the Lanes receive two consecutive TS1 Ordered Sets that have a Lane number different from when the Lane first entered Configuration.Lanenum.Wait, and not all the Lanes' Link numbers are set to PAD
or
b. If any Lane receives two consecutive TS2 Ordered Sets

- The next state is Detect after a 2 ms timeout or if all Lanes receive two consecutive TS1 Ordered Sets with Link and Lane numbers set to PAD.


# 4.2.7.3.5 Configuration.Complete 

A Port is allowed to change the supported data rates that it advertises when it enters this substate, but it must not change those values while in this substate.

If Flit_Mode_Enabled is 0 b and LinkUp=1b, a Port is permitted to change the Upconfigure that it advertises when it enters this substate, but it must not change the value while in this substate.

If Flit_Mode_Enabled is 1 b and LinkUp=0b, a Port is permitted to change the LOp Capability that it advertises when it enters this substate, but it must not change the value while in this substate.

In this sub-state, if use_modified_TS1_TS2_Ordered_Set variable is set to 1b:

- Transmitter must send Modified TS2 Ordered sets instead of TS2 Ordered Sets
- Receiver must check for receipt of Modified TS2 Ordered Sets, instead of TS2 Ordered Sets [Note: See § Section 4.2.5.1 for the definition of identical consecutive Modified TS1 Ordered Sets.]


### 4.2.7.3.5.1 Downstream Lanes

- TS2 Ordered Sets are transmitted using Link and Lane numbers that match the received TS1 Ordered Set Link and Lane numbers.
- The Link Upconfigure / LOp Capability bit of the TS2 Ordered Sets is permitted to be set to 1b to indicate that the Port is capable of supporting down to a x1 Link on the currently assigned Lane 0 and up-configuring the Link while LinkUp = 1b. Advertising this capability is optional.
- N_FTS must be noted for use in LOs when leaving this state.
- When using 8b/10b encoding, Lane-to-Lane de-skew must be completed when leaving this state.
- Scrambling is disabled if all configured Lanes have the Disable Scrambling bit asserted in two consecutively received TS2 Ordered Sets.
- The Port that is sending the Disable Scrambling bit on all of the configured Lanes must also disable scrambling. Scrambling can only be disabled when using 8b/10b encoding.
- The next state is Configuration. Idle immediately after all Lanes that are transmitting TS2 Ordered Sets receive eight consecutive TS2 Ordered Sets with matching Lane and Link numbers (non-PAD) and identical data rate identifiers (including identical Link Upconfigure / LOp Capability bit(Symbol 4 bit 6)), and 16 TS2 Ordered Sets are sent after receiving one TS2 Ordered Set. Implementations with the Retimer Presence Detect Supported bit of the Link Capabilities 2 Register set to 1b must also receive the eight consecutive TS2 Ordered Sets with identical Retimer Present (Symbol 5 bit 4) when the data rate is $2.5 \mathrm{GT} / \mathrm{s}$. Implementations with Two Retimers Presence Detect Supported bit of the Link Capabilities 2 Register set to 1b must also receive the eight consecutive TS2 Ordered Sets with identical Retimer Present (Symbol 5 bits 5:4) when the data rate is $2.5 \mathrm{GT} / \mathrm{s}$.
- If the data rate of operation is $2.5 \mathrm{GT} / \mathrm{s}$ :
- If the Retimer Presence Detect Supported bit of the Link Capabilities 2 Register is set to 1b and any configured Lane received the Retimer Present bit set to 1 b in the eight consecutively received TS2 Ordered Sets, then the Retimer Presence Detected bit must be set to 1b in the Link Status 2 Register otherwise the Retimer Presence Detected bit must be set to 0b.
- If the Two Retimers Presence Detect Supported bit of the Link Capabilities 2 Register is set to 1b and any configured Lane received the Two Retimers Present bit set to 1b in the eight

consecutively received TS2 Ordered Sets then the Two Retimers Presence Detected bit must be set to 1 b in the Link Status 2 Register, otherwise the Two Retimers Presence Detected bit must be set to 0 b .

- If the device supports greater than $2.5 \mathrm{GT} / \mathrm{s}$ data rate, it must record the data rate identifier received on any configured Lane of the Link. This will override any previously recorded value. A variable to track speed change in recovery state, changed_speed_recovery, is reset to 0b.
- If Flit_Mode_Enabled is 0b:

If the device sends TS2 Ordered Sets with the Link Upconfigure / LOp Capability bit (Symbol 4 bit 6) set to 1 b , and receives eight consecutive TS2 Ordered Sets with the Link Upconfigure / LOp Capability bit set to 1 b , the variable upconfigure_capable is set to 1 b , else it is reset to 0 b .

- If Flit_Mode_Enabled is 1b and LinkUp=0b:

If the device sends TS2 Ordered Sets with the Link Upconfigure / LOp Capability bit (Symbol 4 bit 6) set to 1 b , and receives eight consecutive TS2 Ordered Sets with the Link Upconfigure / LOp Capability bit set to 1 b :

- The variable LOp_capable is set to 1 b .
- The Remote LOp Supported bit in the Device Status 3 Register is set to 1b.
- All remaining Lanes that are not part of the configured Link are no longer associated with the LTSSM in progress and must:
i. Be associated with a new LTSSM if this optional feature is supported. or
ii. All Lanes that cannot be associated with an optional new LTSSM must transition to Electrical Idle. ${ }^{88}$ Those Lanes that formed a Link up to the L0 state, and LinkUp has been 1b since then, but are not a part of the currently configured Link, must be associated with the same LTSSM if the LTSSM advertises Link width upconfigure capability. It is recommended that the Receiver terminations of these Lanes be left on. If they are not left on, they must be turned on when the LTSSM enters the Recovery.RcvrCfg substate until it reaches the Configuration.Complete substate if upconfigure_capable is set to 1 b to allow for potential Link width upconfiguration. Any Lane that was not part of the LTSSM during the initial Link training through L0 cannot become a part of the LTSSM as part of the Link width upconfiguration process.
- In the case of an optional crosslink, the Receiver terminations are required to meet ZRX-HIGH-IMP-DC-POS and ZRX-HIGH-IMP-DC-NEG (see § Table 8-12).
- These Lanes must be re-associated with the LTSSM immediately after the LTSSM in progress transitions back to Detect.
- An EIOS does not need to be sent before transitioning to Electrical Idle, and the transition to Electrical Idle does not need to occur on a Symbol or Ordered Set boundary.
- After a 2 ms timeout:
- The next state is Detect if the current data rate is $2.5 \mathrm{GT} / \mathrm{s}$ or $5.0 \mathrm{GT} / \mathrm{s}$.
- The next state is Configuration.Idle if the idle_to_rlock_transitioned variable is less than FFh and the current data rate is $8.0 \mathrm{GT} / \mathrm{s}$ or higher.
i. The changed_speed_recovery variable is reset to 0 b.

[^0]
[^0]:    88. The common mode being driven does not need to meet the Absolute Delta Between DC Common Mode During L0 and Electrical Idle (VTX-CM-DC-ACTIVE-IDLE-DELTA) specification (see § Table 8-7).

ii. Lanes that are not part of the configured Link are no longer associated with the LTSSM in progress and must meet requirement (i) or (ii) specified above for the non-timeout transition to Configuration. Idle.
iii. The upconfigure_capable variable is permitted, but not required, to be updated if at least one Lane received eight consecutive TS2 Ordered Sets with matching Lane and Link numbers (non-PAD). If updated, the upconfigure_capable variable is set to 1 b when the transmitted and received Link Upconfigure bits are 1 b , else it is reset to 0 b .

- Else the next state is Detect.


# 4.2.7.3.5.2 Upstream Lanes 

- TS2 Ordered Sets are transmitted using Link and Lane numbers that match the received TS2 Link and Lane numbers.
- The Link Upconfigure / LOp Capability bit of the TS2 Ordered Sets is permitted to be set to 1b to indicate that the Port is capable of supporting a x1 Link on the currently assigned Lane 0 and up-configuring the Link while LinkUp = 1b. Advertising this capability is optional.
- N_FTS must be noted for use in L0s when leaving this state.
- When using 8b/10b encoding, Lane-to-Lane de-skew must be completed when leaving this state.
- Scrambling is disabled if all configured Lanes have the Disable Scrambling bit asserted in two consecutively received TS2 Ordered Sets.
- The Port that is sending the Disable Scrambling bit on all of the configured Lanes must also disable scrambling. Scrambling can only be disabled when using 8b/10b encoding.
- The next state is Configuration. Idle immediately after all Lanes that are transmitting TS2 Ordered Sets receive eight consecutive TS2 Ordered Sets with matching Lane and Link numbers (non-PAD) and identical data rate identifiers (including identical Link Upconfigure / LOp Capability bit (Symbol 4 bit 6)), and 16 consecutive TS2 Ordered Sets are sent after receiving one TS2 Ordered Set. Implementations with the Retimer Presence Detect Supported bit of the Link Capabilities 2 Register set to 1b must also receive the eight consecutive TS2 Ordered Sets with identical Retimer Present (Symbol 5 bit 4) when the data rate is 2.5 GT/s. Implementations with Two Retimers Presence Detect Supported bit of the Link Capabilities 2 Register set to 1b must also receive the eight consecutive TS2 Ordered Sets with identical Retimer Present (Symbol 5 bits 5:4) when the data rate is 2.5 GT/s.
- If the data rate of operation is $2.5 \mathrm{GT} / \mathrm{s}$ :
- If the Retimer Presence Detect Supported bit of the Link Capabilities 2 Register is set to 1b and any configured Lane received the Retimer Present bit set to 1b in the eight consecutively received TS2 Ordered Sets, then the Retimer Presence Detected bit must be set to 1b in the Link Status 2 Register otherwise the Retimer Presence Detected bit must be set to 0b.
- If the Two Retimers Presence Detect Supported bit of the Link Capabilities 2 Register is set to 1b and any configured Lane received the Two Retimers Present bit set to 1b in the eight consecutively received TS2 Ordered Sets then the Two Retimers Presence Detected bit must be set to 1b in the Link Status 2 Register, otherwise the Two Retimers Presence Detected bit must be set to 0 b .
- If the device supports greater than $2.5 \mathrm{GT} / \mathrm{s}$ data rate, it must record the data rate identifier received on any configured Lane of the Link. This will override any previously recorded value. A variable to track speed change in recovery state, changed_speed_recovery, is reset to 0 b .
- If Flit_Mode_Enabled is 0b:

If the device sends TS2 Ordered Sets with the Link Upconfigure / LOp Capability bit (Symbol 4 bit 6) set to 1 b , as well as receives eight consecutive TS2 Ordered Sets with the Link Upconfigure / LOp Capability bit set to 1 b , the variable upconfigure_capable is set to 1 b , else it is reset to 0 b .

- If Flit_Mode_Enabled is 1 b and LinkUp=0b:

If the device sends TS2 Ordered Sets with the Link Upconfigure / LOp Capability bit (Symbol 4 bit 6) set to 1 b , and receives eight consecutive TS2 Ordered Sets with the Link Upconfigure / LOp Capability bit set to 1 b :

- The variable LOp_capable is set to 1 b .
- The Remote LOp Supported bit in the Device Status 3 Register is set to 1b.
- All remaining Lanes that are not part of the configured Link are no longer associated with the LTSSM in progress and must:
i. Optionally be associated with a new crosslink LTSSM if this feature is supported. or
ii. All remaining Lanes that are not associated with a new crosslink LTSSM must transition to Electrical Idle, ${ }^{89}$ and Receiver terminations are required to meet $Z_{\text {Rx-HIGH-IMP-DC-POS }}$ and $Z_{\text {Rx-HIGH-IMP-DC-NEG }}$ (see § Table 8-12). Those Lanes that formed a Link up to the L0 state, and LinkUp has been 1 b since then, but are not a part of the currently configured Link, must be associated with the same LTSSM if the LTSSM advertises Link width upconfigure capability. It is recommended that the Receiver terminations of these Lanes be left on. If they are not left on, they must be turned on when the LTSSM enters the Recovery.RcvrCfg substate until it reaches the Configuration.Complete substate if upconfigure_capable is set to 1 b to allow for potential Link width upconfiguration. Any Lane that was not part of the LTSSM during the initial Link training through L0 cannot become a part of the LTSSM as part of the Link width upconfiguration process.
- These Lanes must be re-associated with the LTSSM immediately after the LTSSM in progress transitions back to Detect.
- EIOS does not need to be sent before transitioning to Electrical Idle, and the transition to Electrical Idle does not need to occur on a Symbol or Ordered Set boundary.
- After a 2 ms timeout:
- The next state is Detect if the current data rate is $2.5 \mathrm{GT} / \mathrm{s}$ or $5.0 \mathrm{GT} / \mathrm{s}$.
- The next state is Configuration.Idle if the idle_to_rlock_transitioned variable is less than FFh and the current data rate is $8.0 \mathrm{GT} / \mathrm{s}$ or higher.
i. The changed_speed_recovery variable is reset to 0 b .
ii. Lanes that are not part of the configured Link are no longer associated with the LTSSM in progress and must meet requirement (i) or (ii) specified above for the non-timeout transition to Configuration.Idle.
iii. The upconfigure_capable variable is permitted, but not required, to be updated if at least one Lane received eight consecutive TS2 Ordered Sets with matching Lane and Link numbers (non-PAD). If updated, the upconfigure_capable variable is set to 1 b when the transmitted and received Link Upconfigure bits are 1 b , else it is reset to 0 b .
- Else the next state is Detect.

[^0]
[^0]:    89. The common mode being driven does not need to meet the Absolute Delta Between DC Common Mode During L0 and Electrical Idle (V ${ }_{\text {TX-CM-DC-ACTIVE-IDLE-DELTA) }}$ specification (see § Table 8-7).

# 6.3-1.0-PUB — PCI Express ${ }^{\circledR}$ Base Specification Revision 6.3 

### 4.2.7.3.6 Configuration.Idle 5

- When using 8b/10b encoding, the Transmitter sends Idle data Symbols on all configured Lanes in Non-Flit Mode and IDLE Flits across all configured Lanes in Flit Mode.
- If LinkUp = 0b and 64.0 GT/s data rate is supported by all components in the Link, as advertised in the eight consecutive TS2 or eight consecutive and identical Modified TS2 Ordered Sets received prior to entering Configuration.Idle:
- If the No Equalization Needed bit (bit 1 of Symbol 5) was set to 1 b in the received eight consecutive and identical Modified TS2 Ordered Sets and in the transmitted Modified TS2 Ordered Sets in all the configured Lanes of the Link or if No Equalization Needed value (10b) was received in the Enhanced Link Behavior Control field (bits 7:6 of Symbol 5) in the eight consecutive TS2 Ordered Sets and was also set in the Enhanced Link Behavior Control field of the transmitted TS2 Ordered Sets:
- The equalization_done_8GT_data_rate, equalization_done_16GT_data_rate, equalization_done_32GT_data_rate, and equalization_done_64GT_data_rate variables are each set to 1 b .
- The No Equalization Needed Received bit in the 64.0 GT/s Status Register is set to 1b.
- Else If the Equalization Bypass to Highest NRZ Rate bit (bit 0 of Symbol 5) was set to 1b in the received eight consecutive and identical Modified TS2 Ordered Sets as well as in the transmitted Modified TS2 Ordered Sets in all the configured Lanes of the Link or if either No Equalization Needed or Equalization Bypass to Highest NRZ Rate value (01b or 10b) was received in the Enhanced Link Behavior Control field (bits 7:6 of Symbol 5) in the eight consecutive TS2 Ordered Sets and either No Equalization Needed or Equalization Bypass to Highest NRZ Rate value (01b or 10b) was also set in the Enhanced Link Behavior Control field of the transmitted TS2 Ordered Sets:
- The equalization_done_8GT_data_rate and equalization_done_16GT_data_rate variables are each set to 1 b .
- If entry to this sub-state was caused by receipt of eight consecutive and identical Modified TS2 Ordered Sets and LinkUp = 0b
- If the Modified TS Usage field in the received eight consecutive Modified TS2 Ordered Sets was set to 010b (Alternate Protocols) and the same value was set in the Modified TS Usage field of the transmitted Modified TS2 Ordered Sets and the Modified TS Information 1 and Alternate Protocol Vendor ID fields are identical between the transmitted and received Modified TS2 Ordered Sets in all the configured Lanes of the Link:
- The Modified TS Received bit in the 32.0 GT/s Status Register is set to 1b. The details of the negotiation will be reflected in the Received Modified TS Data 1 Register and Received Modified TS Data 2 Register based on the eight consecutive Modified TS2 Ordered Sets received.
- If LinkUp = 0b and 32.0 GT/s data rate is supported by all components in the Link, as advertised in the eight consecutive TS2 or eight consecutive and identical Modified TS2 Ordered Sets received prior to entering Configuration.Idle:
- If the No Equalization Needed bit (bit 1 of Symbol 5) was set to 1 b in the received eight consecutive and identical Modified TS2 Ordered Sets and was also set in the transmitted Modified TS2 Ordered Sets in all the configured Lanes of the Link or if No Equalization Needed value (10b) was received in the Enhanced Link Behavior Control field (bits 7:6 of Symbol 5) in the eight consecutive TS2 Ordered Sets and was also set in the Enhanced Link Behavior Control field of the transmitted TS2 Ordered Sets:
- The equalization_done_8GT_data_rate, equalization_done_16GT_data_rate, and equalization_done_32GT_data_rate variables are each set to 1b.

- The No Equalization Needed Received bit in the 32.0 GT/s Status Register is set to 1b.
- Else If the Equalization Bypass to Highest NRZ Rate bit (bit 0 of Symbol 5) was set to 1b in the received eight consecutive and identical Modified TS2 Ordered Sets and was also set in the transmitted Modified TS2 Ordered Sets in all the configured Lanes of the Link or if either No Equalization Needed or Equalization Bypass to Highest NRZ Rate value (01b or 10b) was received in the Enhanced Link Behavior Control field (bits 7:6 of Symbol 5) in the eight consecutive TS2 Ordered Sets and either No Equalization Needed or Equalization Bypass to Highest NRZ Rate value (01b or 10b) was also set in the Enhanced Link Behavior Control field of the transmitted TS2 Ordered Sets:
- The equalization_done_8GT_data_rate and equalization_done_16GT_data_rate variables are each set to 1b.
- If entry to this sub-state was caused by receipt of eight consecutive and identical Modified TS2 Ordered Sets and LinkUp $=0 b$
- If the Modified TS Usage field in the received eight consecutive Modified TS2 Ordered Sets was set to 010b (Alternate Protocols) and the same value was set in the Modified TS Usage field of the transmitted Modified TS2 Ordered Sets and the Modified TS Information 1 and Alternate Protocol Vendor ID fields are identical between the transmitted and received Modified TS2 Ordered Sets in all the configured Lanes of the Link:
- The Modified TS Received bit in the 32.0 GT/s Status Register is set to 1b. The details of the negotiation will be reflected in the Received Modified TS Data 1 Register and Received Modified TS Data 2 Register based on the eight consecutive modified TS2 Ordered Sets received.
- When using 128b/130b encoding in Non-Flit Mode:
- If the data rate is $8.0 \mathrm{GT} / \mathrm{s}$, the Transmitter sends one SDS Ordered Set on all configured Lanes to start a Data Stream and then sends Idle data Symbols on all configured Lanes. The first Idle data Symbol transmitted on Lane 0 is the first Symbol of the Data Stream.
- If the data rate is $16.0 \mathrm{GT} / \mathrm{s}$ or higher, the Transmitter sends one Control SKP Ordered Set followed immediately by one SDS Ordered Set on all configured Lanes to start a Data Stream and then sends Idle data Symbols on all configured Lanes. The first Idle data Symbol transmitted on Lane 0 is the first Symbol of the Data Stream.
- When using 1b/1b encoding or 128b/130b encoding in Flit Mode:
- Transmitter sends an SDS Ordered Set sequence followed by one Control SKP Ordered Set on all configured Lanes to start a Data Stream with IDLE Flits.
- Receiver waits for Idle data in Non-Flit Mode and for IDLE Flits in Flit Mode.
- LinkUp = 1b
- When using 8b/10b encoding in Non-Flit Mode, the next state is L0 if eight consecutive Symbol Times of Idle data are received on all configured Lanes and 16 Idle data Symbols are sent after receiving one Idle data Symbol.
- If software has written a 1b to the Retrain Link bit in the Link Control Register since the last transition to L0 from Recovery or Configuration, the Downstream Port must set the Link Bandwidth Management Status bit of the Link Status Register to 1b.
- The use_modified_TS1_TS2_Ordered_Set variable is reset to 0b on transition to L0.
- When using 128b/130b encoding in Non-Flit Mode, next state is L0 if eight consecutive Symbol Times of Idle data are received on all configured Lanes, 16 Idle data Symbols are sent after receiving one Idle data Symbol, and this state was not entered by a timeout from Configuration.Complete.
- The Idle data Symbols must be received in Data Blocks.
- Lane-to-Lane de-skew must be completed before Data Stream processing starts.

- If software has written a 1b to the Retrain Link bit in the Link Control Register since the last transition to L0 from Recovery or Configuration, the Downstream Port must set the Link Bandwidth Management Status bit of the Link Status Register to 1b.
- The idle_to_rlock_transitioned variable is reset to 00 h on transition to L0.
- In Flit Mode, the next state is L0 if two consecutive IDLE Flits are received and the minimum number of IDLE Flits are sent after receiving one IDLE Flit and this state was not entered by a timeout from Configuration.Complete. The minimum number of IDLE Flits to send is 4 with 8b/10b or 128b/130b encoding and 8 with $1 \mathrm{~b} / 1 \mathrm{~b}$ encoding.
- Lane-to-Lane de-skew must be completed before Data Stream processing starts.
- If software has written a 1b to the Retrain Link bit in the Link Control Register since the last transition to L0 from Recovery or Configuration, the Downstream Port must set the Link Bandwidth Management Status bit of the Link Status Register to 1b.
- The idle_to_rlock_transitioned variable is reset to 00 h and the use_modified_TS1_TS2_Ordered_Set variable is reset to 0 b on transition to L0.
- Otherwise, after a minimum 2 ms timeout:
- If the idle_to_rlock_transitioned variable is less than FFh, the next state is Recovery.RcvrLock.
- On transition to Recovery.RcvrLock:
- If the data rate is $8.0 \mathrm{GT} / \mathrm{s}$ or higher, the idle_to_rlock_transitioned variable is incremented by 1 .
- If the data rate is $2.5 \mathrm{GT} / \mathrm{s}$ or $5.0 \mathrm{GT} / \mathrm{s}$, the idle_to_rlock_transitioned variable is set to FFh and the use_modified_TS1_TS2_Ordered_Set variable is reset to 0 b .
- Else the next state is Detect.

![img-68.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-68.jpeg)

Figure 4-70 Configuration Substate Machine

# 4.2.7.4 Recovery 

The Recovery substate machine is shown in § Figure 4-71. For the data rate of $64.0 \mathrm{GT} / \mathrm{s}$, any reference to Pre-cursor implies the two pre-cursors used.

### 4.2.7.4.1 Recovery.RcvrLock

If the Link is operating at a data rate of $8.0 \mathrm{GT} / \mathrm{s}$ or higher, a Receiver must consider any TS0, TS1, or TS2 Ordered Set to be received only after it obtains Block Alignment in that Lane. If entry to this substate is from L1 or Recovery.Speed or L0s, the Block Alignment must be obtained after exiting Electrical Idle condition. If entry to this substate is from L0, the Block Alignment must be obtained after the end of the last Data Stream.

- If the data rate of operation is $8.0 \mathrm{GT} / \mathrm{s}$ or higher:
- If the start_equalization_w_preset variable is set to 1b:
- An Upstream Port must use the Transmitter preset values it registered from the received appropriate eight consecutive TS2 Ordered Sets (EQ TS2 if $8.0 \mathrm{GT} / \mathrm{s}$, EQ TS2 if $32.0 \mathrm{GT} / \mathrm{s}$ and Equalization Bypass to Highest NRZ Rate was negotiated, and 128b/130b EQ TS2 if 16.0 GT/ s, $32.0 \mathrm{GT} / \mathrm{s}$, or $64.0 \mathrm{GT} / \mathrm{s}$ ) in Recovery.RcvrCfg in its Transmitter setting as soon as it starts transmitting in the data rate at which equalization will be performed and ensure that it meets the preset definition in § Chapter 8. . Lanes that received a Reserved or unsupported Transmitter preset value must use an implementation specific method to choose a supported Transmitter preset setting for use as soon as it starts transmitting at the data rate where equalization needs to be performed.
- A Downstream Port must use the Transmitter preset settings according to the rules below as soon as it starts transmitting at the data rate where equalization must be performed:

1. If the data rate of equalization is $16.0 \mathrm{GT} / \mathrm{s}$ or $32.0 \mathrm{GT} / \mathrm{s}$ or $64.0 \mathrm{GT} / \mathrm{s}$ and eight consecutive EQ TS2 Ordered Sets (for the case where equalization bypass to $32.0 \mathrm{GT} / \mathrm{s}$ is to be performed) or 128b/130b EQ TS2 Ordered Sets were received with supported Transmitter Preset values in the most recent transition through Recovery.RcvrCfg, the Transmitter Preset value from those EQ TS2 or 128b/ 130b EQ TS2 Ordered Sets must be used.
2. Else, if the Transmitter preset value defined in the Downstream Port Transmitter Preset field of the appropriate Lane Equalization Control Register Entry, as defined below is supported, then it must be used:

| Data Rate of <br> Equalization | Transmitter Preset value to be used as soon as the Link transitions to the <br> data rate of equalization |
| :--: | :-- |
| $8.0 \mathrm{GT} / \mathrm{s}$ | Transmitter Preset field defined in the Lane Equalization Control Register <br> Entry for each Lane. The Downstream Port may optionally use the <br> Downstream Port 8.0 GT/s Receiver Preset Hint field defined in the Lane <br> Equalization Control Register Entry for each of its Receivers <br> corresponding to the Lane, if they are not Reserved values. |
| $16.0 \mathrm{GT} / \mathrm{s}$ | Downstream Port 16.0 GT/s Transmitter Preset field of the 16.0 GT/s Lane <br> Equalization Control Register Entry |
| $32.0 \mathrm{GT} / \mathrm{s}$ | Downstream Port 32.0 GT/s Transmitter Preset field of the 32.0 GT/s Lane <br> Equalization Control Register Entry |

| Data Rate of <br> Equalization | Transmitter Preset value to be used as soon as the Link transitions to the <br> data rate of equalization |
| :--: | :-- |
| $64.0 \mathrm{GT} / \mathrm{s}$ | Downstream Port 64.0 GT/s Transmitter Preset field of the 64.0 GT/s Lane <br> Equalization Control Register Entry |

3. Else, use an implementation specific method to choose a supported Transmitter preset setting.

The Downstream Port must ensure that it meets the preset definition in $\S$ Chapter 8. .

- Next state is Recovery.Equalization.
- Else:
- The Transmitter must use the coefficient settings agreed upon at the conclusion of the last equalization procedure.
- If this substate was entered from Recovery.Equalization, in the transmitted TS1 Ordered Sets, a Downstream Port must set the Pre-cursor, Cursor, and Post-cursor Coefficient fields to the current Transmitter settings, and if the last accepted request in Phase 2 of Recovery.Equalization was a preset request, it must set the Transmitter Preset bits to the accepted preset of that request.
- It is recommended that in this substate, in the transmitted TS1 Ordered Sets, all Ports set the Pre-cursor, Cursor, and Post-cursor Coefficient fields to the current Transmitter settings, and set the Transmitter Preset bits to the most recent preset that the Transmitter settings were set to.
- An Upstream Port that receives eight consecutive TS0 or eight consecutive TS1 Ordered Sets on all configured Lanes with the following characteristics must transition to Recovery.Equalization
- If eight consecutive TS1 Ordered Sets were received, Link and Lane numbers in the received TS1 Ordered Sets match with the Link and Lane numbers in the transmitted TS1 Ordered Sets on each Lane. See § Section 4.2.7 for more on Matching Link and Lane Numbers for 1b/1b Encoding.
- If eight consecutive TS1 Ordered Sets were received, speed_change bit is equal to 0b
- If eight consecutive TS0 Ordered Sets were received, and the latest transition to Recovery.RcvrLock was from Recovery.Speed substate
- If eight consecutive TS1 Ordered Sets were received, with the EC bits not equal to 00b


# IMPLEMENTATION NOTE: REDOING EQUALIZATION 

A Downstream Port may use this provision to redo some parts of the Transmitter Equalization process using software help or some other implementation specific means while ensuring no transactions are in flight on the Link to avoid any timeouts.

- Next state for a Downstream Port is Recovery.Equalization if Recovery.RcvrLock was not entered from Configuration.Idle or Recovery.Idle and the Perform Equalization bit in the Link

Control 3 Register is set or an implementation specific mechanism determined equalization needs to be performed, following procedures described in $\S$ Section 4.2.4.

The Downstream Port must ensure that no more than 2 TS1 Ordered Sets with EC=00b are transmitted due to being in Recovery.RcvrLock before transitioning to Recovery. Equalization and starting to transmit the TS0/TS1 Ordered Sets.

- Transmitter sends TS1 Ordered Sets on all configured Lanes using the same Link and Lane numbers that were set after leaving Configuration. The speed_change bit (bit 7 of the Data Rate Identifier Symbol in TS1 Ordered Set) must be set to 1 b if the directed_speed_change variable is set to 1 b . The directed_speed_change variable is set to 1 b if any configured Lane receives eight consecutive TS1 Ordered Sets with the speed_change bit set to 1 b . Only those data rates greater than $2.5 \mathrm{GT} / \mathrm{s}$ should be advertised that can be supported reliably. In Non-Flit Mode of operation, the N_FTS value in the TS1 Ordered Set transmitted reflects the number at the current speed of operation. A device is allowed to change the supported data rates that it advertises when it enters this substate.

A Downstream Port that intends to redo equalization with a data rate change from $2.5 \mathrm{GT} / \mathrm{s}$ or $5.0 \mathrm{GT} / \mathrm{s}$ to $8.0 \mathrm{GT} / \mathrm{s}$ or $32.0 \mathrm{GT} / \mathrm{s}$ when Equalization Bypass to Highest NRZ Rate is supported must:

- Send EQ TS1 Ordered Sets with the speed_change bit set to 1b and advertising the following data rates:
- $8.0 \mathrm{GT} / \mathrm{s}$ Data Rate Identifier if redo equalization is for $8.0 \mathrm{GT} / \mathrm{s}$ Data Rate
- $32.0 \mathrm{GT} / \mathrm{s}$ Data Rate Identifier if redo equalization is for $32.0 \mathrm{GT} / \mathrm{s}$ Data Rate
- If the equalization redo attempt is initiated by the hardware as described in $\S$ Section 4.2.4, then hardware must ensure that the Data Rate is $2.5 \mathrm{GT} / \mathrm{s}$ or $5.0 \mathrm{GT} / \mathrm{s}$ before initiating the attempt.
- If the equalization redo attempt is initiated by the software mechanism as described in $\S$ Section 4.2.4, then software must ensure that the Data Rate is $2.5 \mathrm{GT} / \mathrm{s}$ or $5.0 \mathrm{GT} / \mathrm{s}$ before initiating the attempt.

A Downstream Port that intends to redo equalization with a data rate change from $8.0 \mathrm{GT} / \mathrm{s}$ to $16.0 \mathrm{GT} / \mathrm{s}$, $16.0 \mathrm{GT} / \mathrm{s}$ to $32.0 \mathrm{GT} / \mathrm{s}$, or $32.0 \mathrm{GT} / \mathrm{s}$ to $64.0 \mathrm{GT} / \mathrm{s}$ must:

- Send TS1 Ordered Sets with the Equalization Redo bit set to 1b, the speed_change bit set to 1b, and advertising the Data Rate Identifier at which equalization redo will be performed ( $16.0 \mathrm{GT} / \mathrm{s}, 32.0 \mathrm{GT} /$ $\mathrm{s}, \mathrm{or} 64.0 \mathrm{GT} / \mathrm{s})$.
- If the equalization redo attempt is initiated by the hardware as described in $\S$ Section 4.2.4, then hardware must ensure that the Data Rate is the following before initiating the attempt to redo equalization:
- $8.0 \mathrm{GT} / \mathrm{s}$ if the equalization redo is for $16.0 \mathrm{GT} / \mathrm{s}$ Data Rate
- $16.0 \mathrm{GT} / \mathrm{s}$ if the equalization redo is for $32.0 \mathrm{GT} / \mathrm{s}$ Data Rate
- $32.0 \mathrm{GT} / \mathrm{s}$ if the equalization redo is for $64.0 \mathrm{GT} / \mathrm{s}$ Data Rate
- If the equalization redo attempt is initiated by the software mechanism as described in $\S$ Section 4.2.4, then software must ensure that the Data Rate is the following before initiating the attempt to redo equalization:
- $8.0 \mathrm{GT} / \mathrm{s}$ if the equalization redo is for $16.0 \mathrm{GT} / \mathrm{s}$ Data Rate
- $16.0 \mathrm{GT} / \mathrm{s}$ if the equalization redo is for $32.0 \mathrm{GT} / \mathrm{s}$ Data Rate
- $32.0 \mathrm{GT} / \mathrm{s}$ if the equalization redo is for $64.0 \mathrm{GT} / \mathrm{s}$ Data Rate

An Upstream Port must advertise the highest data rate support in the TS2 Ordered Sets it transmits in Recovery.RcvrCfg, and optionally in the TS1 Ordered Sets it transmits in this substate, unless the Upstream Port has determined that a problem unrelated to the highest data rate equalization prevents it from operating

reliably at the highest data rate at which equalization is being requested to be performed, if the eight consecutive Ordered Sets it receives are one of the following:

- EQ TS1 or EQ TS2 Ordered Sets with the speed_change bit set to 1b
- TS1 Ordered Sets with the Equalization Redo bit set to 1b or 128b/130b EQ TS2 Ordered Sets with the speed_change bit set to 1b.

Under other conditions, a device must not change the supported data rate values either in this substate or while in the Recovery.RcvrCfg or Recovery. Equalization substates. The successful_speed_negotiation variable is reset to 0 b upon entry to this substate.

# IMPLEMENTATION NOTE: HANDLING A REQUEST TO ADVERTISE 8.0 GT/S DATA RATE IDENTIFIER 6 

If an Upstream Port that is not advertising 8.0 GT/s Data Rate Identifiers receives EQ TSs with 8.0 GT/s Data Rate Identifiers and with the speed_change bit set in Recovery.RcvrLock, that indicates that the Downstream Port is attempting to switch the Link speed to $8.0 \mathrm{GT} / \mathrm{s}$ in order to perform the $8.0 \mathrm{GT} / \mathrm{s}$ Link Equalization Procedure. If for some reason the Upstream Port is unable or unwilling to switch to advertising 8.0 GT/s Data Rate Identifiers in the TS2 Ordered Sets it transmits once it transitions to Recovery.RcvrCfg, the 8.0 GT/s Link Equalization Procedure will not be performed in the current tenure in Recovery. This may cause the Downstream Port to permanently abandon its attempt to change the Link speed to $8.0 \mathrm{GT} / \mathrm{s}$ and perform the $8.0 \mathrm{GT} / \mathrm{s}$ Link Equalization Procedure, resulting in an operational link speed of less than $8.0 \mathrm{GT} / \mathrm{s}$ until after the link transitions through Detect and is re-trained. It is recommended that if an Upstream Port is for some temporary reason unable or unwilling to switch to advertising $8.0 \mathrm{GT} / \mathrm{s}$ Data Rate Identifiers in the condition described above, and does not intend to prohibit the Link from operating at $8.0 \mathrm{GT} / \mathrm{s}$, that it perform one of the following two actions below as soon as is reasonable for it to do so:

- If the Upstream Port supports the Quiesce Guarantee mechanism for performing the Link Equalization Procedure, enter Recovery and advertise 8.0 GT/s Data Rate Identifiers with the speed_change bit set to 1 b in the TSs that it sends. If Recovery. Equalization is not entered after changing speed to $8.0 \mathrm{GT} / \mathrm{s}$ and before entering Recovery.RcvrCfg at $8.0 \mathrm{GT} / \mathrm{s}$ (the Downstream Port did not direct an entry to Recovery.Equalization), it should set the Request Equalization and Quiesce Guarantee bits to 1b in the TS2 Ordered Sets sent at $8.0 \mathrm{GT} / \mathrm{s}$ in Recovery.RcvrCfg in order to request the Downstream Port to initiate the Link Equalization Procedure.
- Enter Recovery and advertise 8.0 GT/s Data Rate Identifiers with the speed_change bit cleared to 0b. The Downstream Port may then later initiate a speed change to $8.0 \mathrm{GT} / \mathrm{s}$ and perform the Link Equalization Procedure, though there is no guarantee that it will do so.

The process for handling a request to advertise $16.0 \mathrm{GT} / \mathrm{s}, 32.0 \mathrm{GT} / \mathrm{s}$, or $64.0 \mathrm{GT} / \mathrm{s}$ Data Rate Identifier is similar to $8.0 \mathrm{GT} / \mathrm{s}$ Data Rate Identifier with $16.0 \mathrm{GT} / \mathrm{s}, 32.0 \mathrm{GT} / \mathrm{s}$, or $64.0 \mathrm{GT} / \mathrm{s}$ Data Rate Identifier substituting $8.0 \mathrm{GT} / \mathrm{s}$ Data Rate Identifier and 128b/130b EQ TS2s substituting EQ TSs.

An Upstream Port must set the Selectable De-emphasis bit (bit 6 of Symbol 4) of the TS1 Ordered Sets it transmits to match the desired de-emphasis level at $5.0 \mathrm{GT} / \mathrm{s}$. The mechanism an Upstream Port may adopt to request a de-emphasis level if it chooses to do so is implementation specific. It must also be noted that since the Upstream Port's request may not reach the Downstream Port due to bit errors in the TS1 Ordered Sets, the Upstream Port may attempt to re-request the desired de-emphasis level in subsequent entries to Recovery state when speed change is requested. If the

Downstream Port intends to use the Upstream Port's de-emphasis information in Recovery.RcvrCfg, then it must record the value of the Selectable De-emphasis bit received in this state.

The Transmit Margin field of the Link Control 2 Register is sampled on entry to this substate and becomes effective on the transmit package pins within 192 ns of entry to this substate and remains effective until a new value is sampled on a subsequent entry to this substate from L0, L0s, or L1.

- After activating any inactive Lane, the Transmitter must wait for its TX common mode to settle before exiting Electrical Idle and transmitting the TS1 Ordered Sets with the following exceptions.
- When exiting from the L1.2 L1 PM Substate, common mode is permitted to be established passively during L1.0, and actively during Recovery. In order to ensure common mode has been established in Recovery.RcvrLock, the Downstream Port must maintain a timer, and the Downstream Port must not send TS2 Ordered Sets until a minimum of Tcommonmode has elapsed since the Downstream Port has started transmitting TS1 Ordered Sets and has detected electrical idle exit on any Lane of the configured Link. See § Section 5.5.3.3.
- Implementations must note that the voltage levels may change after an early bit lock and Symbol or Block alignment since the new Transmit Margin field becomes effective within 192 ns after the other side enter Recovery.RcvrLock. The Receiver needs to reacquire bit lock and Symbol or Block alignment under those conditions.
a. Note: The directed_speed_change variable is set to 1 b in L0 or L1 state for the side that is initiating a speed change. For the side that is not initiating a speed change, this bit is Set in this substate if the received TS Ordered Sets have the speed change bit Set. This bit is reset to 0 b in the Recovery.Speed substate.
b. A device must accept all good TLPs and DLLPs it receives after entering this substate from L0 prior to receiving the first TS Ordered Set. If operating with 128b/130b encoding, any received TLPs and DLLPs are subject to the framing rules for 128b/130b encoding in § Section 4.2.2.3 .
- Next state is Recovery.RcvrCfg if eight consecutive TS1 or TS2 Ordered Sets are received on all configured Lanes with the same Link and Lane numbers that match what is being transmitted on those same Lanes and the speed_change bit is equal to the directed_speed_change variable and the EC field is 00 b in all the consecutive TS1 Ordered Sets if the current data rate is 8.0 GT/s or higher. See § Section 4.2.7 for more on Matching Link and Lane Numbers for 1b/1b Encoding.
- If the Extended Synch bit is Set, the Transmitter must send a minimum of 1024 consecutive TS1 Ordered Sets before transitioning to Recovery.RcvrCfg.
- If this substate was entered from Recovery. Equalization, the Upstream Port must evaluate the equalization coefficients or preset received by all Lanes that receive eight TS1 Ordered Sets and note whether they are different from the final set of coefficients or preset that was accepted in Phase 2 of the equalization process. Note: Mismatches are reported in Recovery.RcvrCfg by setting the Request Equalization bit of TS2 Ordered Sets.
- Otherwise, after a 24 ms timeout:
- Next state is Recovery.RcvrCfg if the following two conditions are true:
- Either of the following conditions are true:
- Eight consecutive TS1 or TS2 Ordered Sets are received on any configured Lane with the same Link and Lane numbers that match what is being transmitted on the same Lane and the speed_change bit equal to 1b. See § Section 4.2.7 for more on Matching Link and Lane Numbers for 1b/1b Encoding.
- The Link is operating in Flit Mode and eight consecutive TS2s are received on any configured Lane with the Link number set to PAD and the Lane number matches what is being transmitted on the same Lane. See § Section 4.2.7 for more on Matching Link and Lane Numbers for 1b/1b Encoding.

- Either of the following conditions are true:
- The current data rate of operation is greater than $2.5 \mathrm{GT} / \mathrm{s}$.
- The highest data rate advertised in the Data Rate Identifier symbol of both the transmitted TS1 Ordered Sets and the (eight consecutive) received TS1 or TS2 Ordered Sets is $5.0 \mathrm{GT} / \mathrm{s}$ or greater.


# IMPLEMENTATION NOTE: <br> RECOMMENDED MECHANISM FOR LINK WIDTH REDUCTION IN FLIT MODE 

It is envisioned that when the Link Width is reduced in Flit Mode, both Ports will transition to Configuration from Recovery.RcvrCfg. If a Port proactively reduces the Link Width, it is recommended that that Port either: (1) Waits until it receives a TS2 Ordered Set on one of its Lanes or (2) Waits an additional 1 msec after the conditions are met for the Recovery.RcvrLock to Recovery.RcvrCfg transition. This decreases the likelihood that the initiator's Link Partner will take the timeout arc to Recovery.RcvrCfg since the initiator will continue to send TS1s with a valid Link and Lane number while in Recovery.RcvrLock.

- Else the next state is Recovery.Speed if the speed of operation has not changed to a mutually negotiated data rate since entering Recovery from L0 or L1 (i.e., changed_speed_recovery = 0b) and the current speed of operation is greater than $2.5 \mathrm{GT} / \mathrm{s}$.
- The new data rate to operate after leaving Recovery.Speed will be at $2.5 \mathrm{GT} / \mathrm{s}$ if $8 \mathrm{~b} / 10 \mathrm{~b}$ or $128 \mathrm{~b} / 130 \mathrm{~b}$ encoding is used. The new data rate of operation after leaving Recovery.Speed will be $32.0 \mathrm{GT} / \mathrm{s}$ if $1 \mathrm{~b} / 1 \mathrm{~b}$ encoding is used. Note: This indicates that the Link was unable to operate at the current data rate and the Link will operate at the lower data rate of either $2.5 \mathrm{GT} / \mathrm{s}$ data rate or $32.0 \mathrm{GT} / \mathrm{s}$.
- Else the next state is Recovery.Speed if the operating speed has been changed to a mutually negotiated data rate since entering Recovery from L0 or L1 (changed_speed_recovery = 1b; i.e., the arc to this substate has been taken from Recovery.Speed). The new data rate to operate after leaving Recovery.Speed is reverted back to the speed it was when Recovery was entered from L0 or L1.

Note: This indicates that the Link was unable to operate at the new negotiated data rate and will revert back to the old data rate with which it entered Recovery from L0 or L1.

- Else the next state is Configuration and the directed_speed_change variable is reset to 0 b if the following conditions are true:
- If any of the configured Lanes that are receiving a TS1 or TS2 Ordered Set have received at least one TS1 or TS2 Ordered Set with Link and Lane numbers that match what is being transmitted on those same Lanes. See § Section 4.2.7 for more on Matching Link and Lane Numbers for 1b/1b Encoding.
- The operating speed has not changed to a mutually negotiated data rate (i.e., changed_speed_recovery = 0b) since entering Recovery.
and at least one of the following conditions is true:
- The directed_speed_change variable is equal to 0 b and the speed_change bit on the received TS1 or TS2 Ordered Set is equal to 0 b.

- The current data rate of operation is $2.5 \mathrm{GT} / \mathrm{s}$ and $2.5 \mathrm{GT} / \mathrm{s}$ data rate is the highest commonly advertised data rate among the transmitted TS1 Ordered Sets and the received TS1 or TS2 Ordered $\operatorname{Set}(\mathrm{s})$.
- Otherwise, the next state is Detect.


# IMPLEMENTATION NOTE: EXAMPLE SHOWING SPEED CHANGE ALGORITHM BETWEEN 2.5 GT/S AND 5.0 GT/S 

Suppose a Link connects two greater than $5.0 \mathrm{GT} / \mathrm{s}$ capable components, A and B. The Link comes up to the L0 state in $2.5 \mathrm{GT} / \mathrm{s}$ data rate. Component A decides to change the speed to greater than $5.0 \mathrm{GT} / \mathrm{s}$, sets the directed_speed_change variable to 1b and enters Recovery.RcvrLock from L0. Component A sends TS1 Ordered Sets with the speed_change bit set to 1 b and advertises the $2.5 \mathrm{GT} / \mathrm{s}, 5.0 \mathrm{GT} / \mathrm{s}$, and $8.0 \mathrm{GT} / \mathrm{s}$ data rates. Component B sees the first TS1 in L0 state and enters Recovery.RcvrLock state. Initially, component B sends TS1s with the speed_change set to 0 b . Component B will start sending the speed_change indication in its TS1 after it receives eight consecutive TS1 Ordered Sets from component A and advertises all of the data rates it can support. Component B will enter Recovery.RcvrCfg from where it will enter Recovery.Speed. Component A will wait for eight consecutive TS1/TS2 with speed_change bit set from component B before moving to Recovery.RcvrCfg and on to Recovery.Speed. Both component $A$ and component $B$ enter Recovery.Speed and record $8.0 \mathrm{GT} / \mathrm{s}$ as the maximum speed they can operate with. The directed_speed_change variable will be reset to 0 b when in Recovery.Speed. When they enter Recovery.RcvrLock from Recovery.Speed, they will operate at $8.0 \mathrm{GT} / \mathrm{s}$ and send TS1s with speed_change set to 0 b . If both sides work well at $8.0 \mathrm{GT} / \mathrm{s}$, they will continue on to Recovery.RcvrCfg and enter L0 through Recovery. Idle at $8.0 \mathrm{GT} / \mathrm{s}$. However, if component B fails to achieve Symbol lock, it will timeout in Recovery.RcvrLock and enters Recovery.Speed. Component A would have moved on to Recovery.RcvrCfg but would see the Electrical Idle after receiving TS1s at $8.0 \mathrm{GT} / \mathrm{s}$ after component B enters Recovery.Speed. This will cause component A to move to Recovery.Speed. After entering Recovery.Speed for the second time, both sides will revert back to the speed they operated with prior to entering the Recovery state (2.5 GT/s). Both sides will enter L0 from Recovery in $2.5 \mathrm{GT} / \mathrm{s}$. Component A may initiate the directed_speed_change variable for a second time, requesting $8.0 \mathrm{GT} / \mathrm{s}$ data rate in its Data Rate Identifier, go through the same steps, fail to establish the $8.0 \mathrm{GT} / \mathrm{s}$ data rate and go back to L0 in $2.5 \mathrm{GT} / \mathrm{s}$ data rate. On the third attempt, however, component A may decide to only advertise $2.5 \mathrm{GT} / \mathrm{s}$ and $5.0 \mathrm{GT} / \mathrm{s}$ data rates and successfully establish the Link at $5.0 \mathrm{GT} / \mathrm{s}$ data rate and enter L0 at that speed. However, if either side entered Detect, that side should advertise all of the data rates it can support, since there may have been a hot plug event.

### 4.2.7.4.2 Recovery. Equalization

If this state was entered from Recovery.RcvrLock, Transmitter sends either TS0 or TS1 Ordered Sets on all configured Lanes, as described in § Table 4-61, using the same Link and Lane numbers that were set after leaving Configuration. A Receiver must consider any TS1 or TS0 Ordered Set to be received only after it obtains Block Alignment in that Lane.

If this state was entered from Loopback. Entry:

- Transmitter sends either TS0 or TS1 Ordered Sets, as described in § Table 4-61, on all Lanes that detected a Receiver during Detect using the Link and Lane numbers defined in Loopback. Entry.
- The Lane under test is the only Lane that participates in the equalization procedure.
- The Lanes that are not under test must not be included in the equalization procedure and anything received by them is permitted to be ignored. The Lanes that are not under test must have their Transmitter preset values

set to P4 / Q0. The sole purpose of the lanes that are not under test is to create the noise that is needed in Loopback.Active.

The Lanes must transmit the proper type of Ordered Set (TS0 vs TS1) and check for the receipt of the proper Ordered Set (TS0 vs TS1), according to § Table 4-61, in Recovery. Equalization anywhere TS0/TS1 is mentioned.

| Table 4-61 Use of TS0 or TS1 Ordered Sets in different phases |  |  |  |
| :--: | :--: | :--: | :--: |
| Current Data Rate / Port | Phase 0 / Phase 1 | Phase 2 | Phase 3 |
| 8.0 GT/s, 16.0 GT/s, or 32.0 GT/s; Upstream/Downstream Lanes | TS1 | TS1 | TS1 |
| 64.0 GT/s <br> Downstream Lanes | TS0 | TS0 followed by TS1 | TS1 |
| 64.0 GT/s Upstream Lanes | TS0 | TS0 | TS0 followed by TS1 |

# IMPLEMENTATION NOTE: TSO TO TS1 TRANSITIONS 

All the TSO to TS1 transitions are expected and initiated by a Port so that its Receiver is prepared for the NRZ to PAM4 transition.

The first transition occurs for the Downstream Lanes when entering Phase 2. Prior to that, the Downstream Lanes send TSO with EC=00b until they get their receiver to a target BER of 1E-4 and then they send EC = 01b. Next, they wait to receive $E C=10 \mathrm{~b}$ from the Upstream Port to make the transition. When the Upstream Port sends EC = 10b, it is guaranteed of the transition within a fixed time since the Downstream Port has already acquired its target BER of 1E-4.

The other transition happens during Phase 3 for the Upstream Lanes, when the Upstream Port receives EC=11b. Since the Downstream Port sends EC=11b, it is expecting the NRZ to PAM4 transition.

We have also made a provision for the Retimer to request extended EQ during Phase $0 \& 1$ for 64.0 GT/s equalization.

### 4.2.7.4.2.1 Downstream Lanes

Upon entry to this substate:

- Current phase is Phase 1
- If the data rate of operation is $8.0 \mathrm{GT} / \mathrm{s}$ :
- The Equalization 8.0 GT/s Phase 1 Successful, Equalization 8.0 GT/s Phase 2 Successful, Equalization 8.0 GT/s Phase 3 Successful, Link Equalization Request 8.0 GT/s, and Equalization 8.0 GT/s Complete bits of the Link Status 2 Register and the Perform Equalization bit of the Link Control 3 Register are all set to 0 b .
- The equalization_done_8GT_data_rate variable is set to 1b.
- If the data rate of operation is $16.0 \mathrm{GT} / \mathrm{s}$ :

- The Equalization 16.0 GT/s Phase 1 Successful, Equalization 16.0 GT/s Phase 2 Successful, Equalization 16.0 GT/s Phase 3 Successful, Link Equalization Request 16.0 GT/s, and Equalization 16.0 GT/s Complete bits of the 16.0 GT/s Status Register and the Perform Equalization bit of the Link Control 3 Register are all set to 0 b.
- The equalization_done_16GT_data_rate variable is set to 1 b .
- If the data rate of operation is $32.0 \mathrm{GT} / \mathrm{s}$ :
- The Equalization 32.0 GT/s Phase 1 Successful, Equalization 32.0 GT/s Phase 2 Successful, Equalization 32.0 GT/s Phase 3 Successful, Link Equalization Request 32.0 GT/s, and Equalization 32.0 GT/s Complete bits of the 32.0 GT/s Status Register and the Perform Equalization bit of the Link Control 3 Register are all set to 0 b .
- The equalization_done_32GT_data_rate variable is set to 1 b .
- If the data rate of operation is $64.0 \mathrm{GT} / \mathrm{s}$ :
- The Equalization 64.0 GT/s Phase 1 Successful, Equalization 64.0 GT/s Phase 2 Successful, Equalization 64.0 GT/s Phase 3 Successful, Link Equalization Request 64.0 GT/s, and Equalization 64.0 GT/s Complete bits of the 64.0 GT/s Status Register and the Perform Equalization bit of the Link Control 3 Register are all set to 0 b.
- The equalization_done_64GT_data_rate variable is set to 1 b .
- The start_equalization_w_preset variable is set to 0 b .


# 4.2.7.4.2.1.1 Phase 1 of Transmitter Equalization 

- Transmitter sends TS0/TS1 Ordered Sets using the Transmitter preset settings for the current data rate of operation. In the TS0/TS1 Ordered Sets, the EC field is set to 01b. For TS0 ordered sets, the EC field is initially set to 00 b . After two consecutive TS0 ordered sets are received with Retimer Equalization Extend bit set to 0b, the EC field is set to 01b. The TS0/TS1 Transmitter Preset bits of each Lane are set to the value of its corresponding Transmitter preset setting for the current data rate. The FS and LF fields are set to the appropriate values. The Post-cursor Coefficient field is set to the value corresponding to the Lane's Transmitter Preset bits if TS1 Ordered Sets are transmitted. The Transmitter Preset settings, for each configured Lane, must be chosen as follows:

1. If Recovery. Equalization was entered from Loopback. Entry:

- If EQ TS1 Ordered Sets directed the device from Configuration.Linkwidth.Start to Loopback. Entry, the Transmitter preset value specified in the Preset field of the EQ TS1 Ordered Sets must be used by the Lane under test.
- If standard TS1 Ordered Sets directed the device from Configuration.Linkwidth.Start to Loopback. Entry, an implementation specific method must be used to choose a supported Transmitter Preset value for use.
- If perform_equalization_for_loopback_64GT is 1b, Loopback Follower must advertise 64.0 GT/s support in the transmitted TS0/TS1 Ordered Sets (i.e., Data Rate Identifier must use the Flit Mode Encoding).

2. Else, if eight consecutive 128b/130b EQ TS2 Ordered Sets were received with supported Transmitter preset values in the most recent transition through Recovery.RcvrCfg and the current data rate of operation is $16.0 \mathrm{GT} / \mathrm{s}$ or higher, the Transmitter preset value requested in the 128b/130b EQ TS2 Ordered Sets must be used.
3. Else, if eight consecutive EQ TS2 Ordered Sets were received with supported Transmitter preset values in the most recent transition through Recovery.RcvrCfg, the current data rate of operation is

32.0 GT/s, and equalization bypass to $32.0 \mathrm{GT} / \mathrm{s}$ is being performed, the Transmitter preset value requested in the EQ TS2 Ordered Sets must be used.
4. Else, if the Transmitter preset setting specified by the Downstream Port 8.0 GT/s Transmitter Preset field of the Lane Equalization Control Register Entry (for operation at the $8.0 \mathrm{GT} / \mathrm{s}$ data rate) or the Downstream Port 16.0 GT/s Transmitter Preset field of the 16.0 GT/s Lane Equalization Control Register Entry (for operation at the $16.0 \mathrm{GT} / \mathrm{s}$ data rate) or the Downstream Port 32.0 GT/s Transmitter Preset field of the 32.0 GT/s Lane Equalization Control Register Entry (for operation at the 32.0 GT/s data rate) or the Downstream Port 64.0 GT/s Transmitter Preset field of the 64.0 GT/s Lane Equalization Control Register Entry (for operation at the $64.0 \mathrm{GT} / \mathrm{s}$ data rate) is a supported value and is not a Reserved value, it must be used.
5. Else, use an implementation specific method to choose a supported Transmitter preset setting for use.

- The Downstream Port is permitted to wait for up to 500 ns after entering Phase 1 before evaluating received information for TS0/TS1 Ordered Sets if it needs the time to stabilize its Receiver logic.
- Next phase is Phase 2 if all configured Lanes receive two consecutive TS0/TS1 Ordered Sets with EC=01b and the Downstream Port wants to execute Phase 2 and Phase 3. When the perform_equalization_for_loopback variable is 1 b and the Downstream Port's Flit Mode Supported field of its PCI Express Capabilities Register is set to 1b, Phase 2 and Phase 3 must be executed.
- The Receiver must complete its bit lock process and then recognize Ordered Sets within 2 ms after receiving the first bit of the first valid Ordered Set on its Receiver pin.
- If the data rate is $8.0 \mathrm{GT} / \mathrm{s}$, the Equalization $8.0 \mathrm{GT} / \mathrm{s}$ Phase 1 Successful bit of the Link Status 2 Register is set to 1 b .
- If the data rate is $16.0 \mathrm{GT} / \mathrm{s}$, the Equalization $16.0 \mathrm{GT} / \mathrm{s}$ Phase 1 Successful bit of the $16.0 \mathrm{GT} / \mathrm{s}$ Status Register is set to 1b.
- If the data rate is $32.0 \mathrm{GT} / \mathrm{s}$ and perform_equalization_for_loopback is 0 b , the Equalization $32.0 \mathrm{GT} / \mathrm{s}$ Phase 1 Successful bit of the 32.0 GT/s Status Register is set to 1b.
- If the data rate is $64.0 \mathrm{GT} / \mathrm{s}$ and perform_equalization_for_loopback is 0 b , the Equalization $64.0 \mathrm{GT} / \mathrm{s}$ Phase 1 Successful bit of the 64.0 GT/s Status Register is set to 1b.
- The LF and FS values received in the two consecutive TS0/TS1 Ordered Sets must be stored for use during Phase 3, if the Downstream Port wants to adjust the Upstream Port's Transmitter coefficients.
- Next state is Recovery.RcvrLock if all configured Lanes receive two consecutive TS0/TS1 Ordered Sets with EC=01b, perform_equalization_for_loopback is 0 b and the Downstream Port does not want to execute Phase 2 and Phase 3.
- If the data rate is $8.0 \mathrm{GT} / \mathrm{s}$, The Equalization $8.0 \mathrm{GT} / \mathrm{s}$ Phase 1 Successful, Equalization $8.0 \mathrm{GT} / \mathrm{s}$ Phase 2 Successful, Equalization 8.0 GT/s Phase 3 Successful, and Equalization 8.0 GT/s Complete bits of the Link Status 2 Register are set to 1b.
- If the data rate is $16.0 \mathrm{GT} / \mathrm{s}$, The Equalization $16.0 \mathrm{GT} / \mathrm{s}$ Phase 1 Successful, Equalization $16.0 \mathrm{GT} / \mathrm{s}$ Phase 2 Successful, Equalization 16.0 GT/s Phase 3 Successful, and Equalization 16.0 GT/s Complete bits of the 16.0 GT/s Status Register are set to 1b.
- If the data rate is $32.0 \mathrm{GT} / \mathrm{s}$, The Equalization $32.0 \mathrm{GT} / \mathrm{s}$ Phase 1 Successful, Equalization $32.0 \mathrm{GT} / \mathrm{s}$ Phase 2 Successful, Equalization 32.0 GT/s Phase 3 Successful, and Equalization 32.0 GT/s Complete bits of the 32.0 GT/s Status Register are set to 1b.
- If the data rate is $64.0 \mathrm{GT} / \mathrm{s}$, The Equalization $64.0 \mathrm{GT} / \mathrm{s}$ Phase 1 Successful, Equalization $64.0 \mathrm{GT} / \mathrm{s}$ Phase 2 Successful, Equalization 64.0 GT/s Phase 3 Successful, and Equalization 64.0 GT/s Complete bits of the 64.0 GT/s Status Register are set to 1b.

- If the data rate is 64.0 GT/s, the Transmitter must send 24 TSO Ordered Sets with EC=00b prior to transitioning to Recovery.RcvrLock
- Note: A transition to Recovery.RcvrLock might be used in the case where the Downstream Port determines that Phase 2 and Phase 3 are not needed based on the platform and channel characteristics.
- Next state is Loopback.Entry after a 24 ms timeout if perform_equalization_for_loopback is 1b.
- Else, next state is Recovery.Speed after a 24 ms timeout if perform_equalization_for_loopback is 0b.
- successful_speed_negotiation is set to 0b.
- If the data rate is 8.0 GT/s, the Equalization 8.0 GT/s Complete bit of the Link Status 2 Register is set to 1b.
- If the data rate is 16.0 GT/s, the Equalization 16.0 GT/s Complete bit of the 16.0 GT/s Status Register is set to 1 b .
- If the data rate is 32.0 GT/s, the Equalization 32.0 GT/s Complete bit of the 32.0 GT/s Status Register is set to 1 b .
- If the data rate is 64.0 GT/s, the Equalization 64.0 GT/s Complete bit of the 64.0 GT/s Status Register is set to 1 b .


# 4.2.7.4.2.1.2 Phase 2 of Transmitter Equalization 

- The Transmitter sends TSO Ordered Sets with EC=10b if the data rate is 64.0 GT/s and all Lanes have not received two consecutive TSO Ordered Sets with EC=10b since entering this Phase; else it sends TS1 Ordered Sets.
- Transmitter sends TS1 Ordered Sets with EC = 10b and the coefficient settings, set on each Lane independently, as follows:
- If two consecutive TSO/TS1 Ordered Sets with EC=10b have been received since entering Phase 2, or two consecutive TSO/TS1 Ordered Sets with EC=10b and a preset or set of coefficients (as specified by the Use Preset bit) different than the last two consecutive TSO/TS1 Ordered Sets with EC=10b:
- If the preset or coefficients requested in the most recent two consecutive TSO/TS1 Ordered Sets are legal and supported (see § Section 4.2.4):
- Change the transmitter settings to the requested preset or coefficients such that the new settings are effective at the Transmitter pins within 500 ns of when the end of the second TSO/TS1 Ordered Set requesting the new setting was received at the Receiver pin. The change of Transmitter settings must not cause any illegal voltage level or parameter at the Transmitter pin for more than 1 ns.
- In the transmitted TS1 Ordered Sets, the Transmitter Preset bits are set to the requested preset (for a preset request), the Pre-cursor, Cursor, and Post-cursor Coefficient fields are set to the Transmitter settings (for a preset or a coefficients request), and the Reject Coefficient Values bit is Clear.
- Else (the requested preset or coefficients are illegal or unsupported): Do not change the Transmitter settings used, but reflect the requested preset or coefficient values in the transmitted TS1 Ordered Sets and set the Reject Coefficient Values bit to 1b.
- Else: the preset and coefficients currently being used by the Transmitter.
- Next phase is Phase 3 if all configured Lanes receive two consecutive TSO/TS1 Ordered Sets with EC=11b.
- If the data rate is 8.0 GT/s, the Equalization 8.0 GT/s Phase 2 Successful bit of the Link Status 2 Register is set to 1 b .

- If the data rate is $16.0 \mathrm{GT} / \mathrm{s}$, the Equalization $16.0 \mathrm{GT} / \mathrm{s}$ Phase 2 Successful bit of the $16.0 \mathrm{GT} / \mathrm{s}$ Status Register is set to 1b.
- If the data rate is $32.0 \mathrm{GT} / \mathrm{s}$ and perform_equalization_for_loopback is 0 b , the Equalization $32.0 \mathrm{GT} / \mathrm{s}$ Phase 2 Successful bit of the $32.0 \mathrm{GT} / \mathrm{s}$ Status Register is set to 1 b .
- If the data rate is $64.0 \mathrm{GT} / \mathrm{s}$ and perform_equalization_for_loopback is 0 b , the Equalization $64.0 \mathrm{GT} / \mathrm{s}$ Phase 2 Successful bit of the $64.0 \mathrm{GT} / \mathrm{s}$ Status Register is set to 1 b .
- For data rates less than $64.0 \mathrm{GT} / \mathrm{s}$, next state is Loopback. Entry after a 32 ms timeout with a tolerance of -0 ms and +4 ms if perform_equalization_for_loopback is 1 b .
- For the data rate of $64.0 \mathrm{GT} / \mathrm{s}$, Next state is Loopback. Entry after a 64 ms timeout with a tolerance of -0 ms and +4 ms if perform_equalization_for_loopback is 1 b .
- Else, if the data rate is less than $64.0 \mathrm{GT} / \mathrm{s}$ : next state is Recovery.Speed after a 32 ms timeout with a tolerance of -0 ms and +4 ms
- successful_speed_negotiation is set to 0 b .
- If the data rate is $8.0 \mathrm{GT} / \mathrm{s}$, The Equalization $8.0 \mathrm{GT} / \mathrm{s}$ Complete bit of the Link Status 2 Register is set to 1 b .
- If the data rate is $16.0 \mathrm{GT} / \mathrm{s}$, The Equalization $16.0 \mathrm{GT} / \mathrm{s}$ Complete bit of the $16.0 \mathrm{GT} / \mathrm{s}$ Status Register is set to 1 b .
- If the data rate is $32.0 \mathrm{GT} / \mathrm{s}$, The Equalization $32.0 \mathrm{GT} / \mathrm{s}$ Complete bit of the $32.0 \mathrm{GT} / \mathrm{s}$ Status Register is set to 1 b .
- Else, if the data rate is $64.0 \mathrm{GT} / \mathrm{s}$ : next state is Recovery.Speed after a 64 ms timeout with a tolerance of -0 ms and +4 ms
- successful_speed_negotiation is set to 0 b .
- The Equalization $64.0 \mathrm{GT} / \mathrm{s}$ Complete bit of the $64.0 \mathrm{GT} / \mathrm{s}$ Status Register is set to 1 b .


# 4.2.7.4.2.1.3 Phase 3 of Transmitter Equalization 

- Transmitter sends TS1 Ordered Sets with EC = 11b
- The Port must evaluate and arrive at the optimal settings independently on each Lane. When perform_equalization_for_loopback is 1 b , the equalization procedure is only performed on the Lane under test. To evaluate a new preset or coefficient setting that is legal, as per the rules in $\S$ Section 4.2.4 and § Chapter 8. :
- Request a new preset by setting the Transmitter Preset bits to the desired value and set the Use Preset bit to 1b. Alternativly, request a new set of coefficients by setting the Pre-cursor, Cursor, and Post-Cursor Coefficient fields to the desired values and set the Use Preset bit to 0b. Once a request is made, it must be continuously requested for at least $1 \mu \mathrm{~s}$ or until the evaluation of the request is completed, whichever is later.
- Wait for the required time ( 500 ns plus the roundtrip delay including the logic delays through the Downstream Port) to ensure that, if accepted, the Upstream Port is transmitting using the requested settings. Obtain Block Alignment and then evaluate the incoming Ordered Sets. Note: The Downstream Port may simply ignore anything it receives during this waiting period as the incoming bit stream may be illegal during the transition to the requested settings. Hence the requirement to validate Block Alignment after this waiting period. If Block Alignment cannot be obtained after an implementation specific amount of time (in addition to the required waiting period specified above) it is recommended to proceed to perform Receiver evaluation on the incoming bit stream regardless.

- If two consecutive TS1 Ordered Sets are received with the Transmitter Preset bits (for a preset request) or the Pre-cursor, Cursor, and Post-Cursor Coefficient fields (for a coefficients request) identical to what was requested and the Reject Coefficient Values bit is Clear, then the requested setting was accepted and, depending on the results of Receiver evaluation, can be considered as a candidate final setting.
- If two consecutive TS1 Ordered Sets are received with the Transmitter Preset bits (for a preset request) or the Pre-cursor, Cursor, and Post-Cursor Coefficient fields (for a coefficients request) identical to what was requested and the Reject Coefficient Values bit is Set, then the requested setting was rejected and must not be considered as a candidate final setting.
- If, after an implementation specific amount of time following the start of Receiver evaluation, no consecutive TS1s with the Transmitter Preset bits (for a preset request) or the Pre-Cursor, Cursor, and Post-Cursor Coefficient fields (for a coefficients request) identical to what was requested are received, then the requested setting must not be considered as a candidate final setting.
- The Downstream Port is responsible for setting the Reset EIEOS Interval Count bit in the TS1 Ordered Sets it transmits according to its evaluation criteria and requirements. The Use Preset bit of the received TS1 Ordered Sets must not be used to determine whether a request is accepted or rejected.


# IMPLEMENTATION NOTE: RESET EIEOS AND COEFFICIENT/PRESET REQUESTS 

A Port may set Reset EIEOS Interval Count to 1b when it wants a longer PRBS pattern and subsequently clear it when it needs to obtain Block Alignment.

All TS1 Ordered Sets transmitted in this phase are requests. The first request maybe a new preset or a new coefficient request or a request to maintain the current link partner transmitter settings by reflecting the settings received in the two consecutive TS1 Ordered Sets with EC=11b that cause the transition to Phase 3.

- At $32.0 \mathrm{GT} / \mathrm{s}$ and below data rates, the total amount of time spent per preset or coefficients request from transmission of the request to the completion of the evaluation must be less than 2 ms . Implementations that need a longer evaluation time at the final stage of optimization may continue requesting the same preset or coefficient setting beyond the 2 ms limit but must adhere to the timeout ( 24 ms for $8.0,16.0$, and $32.0 \mathrm{GT} / \mathrm{s}$ and 48 ms for $64.0 \mathrm{GT} / \mathrm{s}$ ) in this phase and must not take this exception more than two times. If the requester is unable to receive Ordered Sets within the timeout period, it may assume that the requested setting does not work in that Lane.
- At $64.0 \mathrm{GT} / \mathrm{s}$ and higher data rates, a device is permitted to evaluate each preset or coefficients request for an arbitrary amount of time. Evaluation must be carefully managed such that the search for an acceptable preset or coefficients can be successful. The total time spent in this Phase must still adhere to the timeout.
- All new preset or coefficient settings must be presented on all configured Lanes simultaneously. Any given Lane is permitted to continue to transmit the current preset or coefficients as its new value if it does not want to change the setting at that time.
- Next state is Loopback. Entry if the data rate of operation is $32.0 \mathrm{GT} / \mathrm{s}$, perform_equalization_for_loopback is 1 b and one of the following conditions is satisfied:
a. The Lane under test is operating at its optimal setting and it received two consecutive TS1 Ordered Sets with the Retimer Equalization Extend bit set to 0b.

b. A 24 ms timeout with a tolerance of -0 ms and +2 ms .

- Next state is Loopback. Entry if the data rate of operation is $64.0 \mathrm{GT} / \mathrm{s}$, perform_equalization_for_loopback is 1 b and one of the following conditions is satisfied:
a. The Lane under test is operating at its optimal setting and all Lanes receive two consecutive TS1 Ordered Sets with the Retimer Equalization Extend bit set to 0 b are received.
b. A 48 ms timeout with a tolerance of -0 ms and +2 ms .
- Next state is Recovery. RcvrLock if perform_equalization_for_loopback is 0b, all configured Lanes are operating at their optimal setting and either the data rate of operation is $8.0 \mathrm{GT} / \mathrm{s}$ or all Lanes receive two consecutive TS1 Ordered Sets with the Retimer Equalization Extend bit set to 0b.
- If the data rate of operation is $8.0 \mathrm{GT} / \mathrm{s}$ : The Equalization $8.0 \mathrm{GT} / \mathrm{s}$ Phase 3 Successful and Equalization $8.0 \mathrm{GT} / \mathrm{s}$ Complete bits of the Link Status 2 Register are set to 1 b .
- If the data rate of operation is $16.0 \mathrm{GT} / \mathrm{s}$ : The Equalization $16.0 \mathrm{GT} / \mathrm{s}$ Phase 3 Successful and Equalization $16.0 \mathrm{GT} / \mathrm{s}$ Complete bits of the $16.0 \mathrm{GT} / \mathrm{s}$ Status Register are set to 1 b .
- If the data rate of operation is $32.0 \mathrm{GT} / \mathrm{s}$ : The Equalization $32.0 \mathrm{GT} / \mathrm{s}$ Phase 3 Successful and Equalization $32.0 \mathrm{GT} / \mathrm{s}$ Complete bits of the $32.0 \mathrm{GT} / \mathrm{s}$ Status Register are set to 1 b .
- If the data rate of operation is $64.0 \mathrm{GT} / \mathrm{s}$ : The Equalization $64.0 \mathrm{GT} / \mathrm{s}$ Phase 3 Successful and Equalization $64.0 \mathrm{GT} / \mathrm{s}$ Complete bits of the $64.0 \mathrm{GT} / \mathrm{s}$ Status Register are set to 1 b .
- Else, if the data rate is less than $64.0 \mathrm{GT} / \mathrm{s}$ : next state is Recovery. Speed after a timeout of 24 ms with a tolerance of -0 ms and +2 ms
- successful_speed_negotiation is set to 0 b .
- If the data rate of operation is $8.0 \mathrm{GT} / \mathrm{s}$ : The Equalization $8.0 \mathrm{GT} / \mathrm{s}$ Complete bit of the Link Status 2 Register is set to 1 b .
- If the data rate of operation is $16.0 \mathrm{GT} / \mathrm{s}$ : The Equalization $16.0 \mathrm{GT} / \mathrm{s}$ Complete bit of the $16.0 \mathrm{GT} / \mathrm{s}$ Status Register is set to 1 b .
- If the data rate of operation is $32.0 \mathrm{GT} / \mathrm{s}$ : The Equalization $32.0 \mathrm{GT} / \mathrm{s}$ Complete bit of the $32.0 \mathrm{GT} / \mathrm{s}$ Status Register is set to 1 b .
- Else, if the data rate is $64.0 \mathrm{GT} / \mathrm{s}$ : next state is Recovery. Speed after a timeout of 48 ms with a tolerance of -0 ms and +2 ms
- successful_speed_negotiation is set to 0 b .
- The Equalization $64.0 \mathrm{GT} / \mathrm{s}$ Complete bit of the $64.0 \mathrm{GT} / \mathrm{s}$ Status Register is set to 1 b .


# 4.2.7.4.2.2 Upstream Lanes 

Upon entry to this substate:

- Current phase is Phase 0
- If the data rate of operation is $8.0 \mathrm{GT} / \mathrm{s}$ :
- The Equalization $8.0 \mathrm{GT} / \mathrm{s}$ Phase 1 Successful, Equalization $8.0 \mathrm{GT} / \mathrm{s}$ Phase 2 Successful, Equalization $8.0 \mathrm{GT} / \mathrm{s}$ Phase 3 Successful, Link Equalization Request $8.0 \mathrm{GT} / \mathrm{s}$, and Equalization $8.0 \mathrm{GT} / \mathrm{s}$ Complete bits of the Link Status 2 Register are all set to 0 b
- The equalization_done_8GT_data_rate variable is set to 1 b .
- If the data rate of operation is $16.0 \mathrm{GT} / \mathrm{s}$ :

- The Equalization 16.0 GT/s Phase 1 Successful, Equalization 16.0 GT/s Phase 2 Successful, Equalization 16.0 GT/s Phase 3 Successful, Link Equalization Request 16.0 GT/s, and Equalization 16.0 GT/s Complete bits of the 16.0 GT/s Status Register are all set to 0b.
- The equalization_done_16GT_data_rate variable is set to 1b.
- If the data rate of operation is $32.0 \mathrm{GT} / \mathrm{s}$ :
- The Equalization 32.0 GT/s Phase 1 Successful, Equalization 32.0 GT/s Phase 2 Successful, Equalization 32.0 GT/s Phase 3 Successful, Link Equalization Request 32.0 GT/s, and Equalization 32.0 GT/s Complete bits of the 32.0 GT/s Status Register are all set to 0b.
- The equalization_done_32GT_data_rate variable is set to 1b.
- If the data rate of operation is $64.0 \mathrm{GT} / \mathrm{s}$ :
- The Equalization 64.0 GT/s Phase 1 Successful, Equalization 64.0 GT/s Phase 2 Successful, Equalization 64.0 GT/s Phase 3 Successful, Link Equalization Request 64.0 GT/s, and Equalization 64.0 GT/s Complete bits of the 64.0 GT/s Status Register are all set to 0b.
- The equalization_done_64GT_data_rate variable is set to 1b.
- The start_equalization_w_preset variable is set to 0 b .


# 4.2.7.4.2.2.1 Phase 0 of Transmitter Equalization 

- If Recovery.Equalization was entered from Loopback. Entry, transmitter sends TS0/TS1 Ordered Sets with the EC field set to 00b, the Transmitter Preset bits of the Lane is set to the value being used. The Pre-cursor Coefficient, Cursor Coefficient, and Post-cursor Coefficient fields are set to values corresponding to the Lane's Transmitter Preset bits if TS1 Ordered Sets are transmitted.
- The Transmitter Preset settings for the Lane under test must be chosen as follows:
- If EQ TS1 Ordered Sets directed the device from Configuration.Linkwidth.Start to Loopback. Entry, the Transmitter preset value specified in the Preset field of the EQ TS1 Ordered Sets must be used.
- If standard TS1 Ordered Sets directed the device from Configuration.Linkwidth.Start to Loopback. Entry, an implementation specific method must be used to choose a supported Transmitter preset value for use.
- If TS0 Ordered Sets are transmitted, while not recommended, components are permitted to use a supported Transmitter Preset value chosen by an implementation-specific method.
- If the current data rate of operation is $8.0 \mathrm{GT} / \mathrm{s}$, transmitter sends TS1 Ordered Sets using the Transmitter settings specified by the Transmitter Preset bits received in the EQ TS2 Ordered Sets during the most recent transition to $8.0 \mathrm{GT} / \mathrm{s}$ data rate from $2.5 \mathrm{GT} / \mathrm{s}$ or $5.0 \mathrm{GT} / \mathrm{s}$ data rate.

If the current data rate of operation is $16.0 \mathrm{GT} / \mathrm{s}$, transmitter sends TS1 Ordered Sets using the $16.0 \mathrm{GT} / \mathrm{s}$ Transmitter settings specified by the Transmitter Preset bits received in the 128b/130b EQ TS2 Ordered Sets during the most recent transition to $16.0 \mathrm{GT} / \mathrm{s}$ data rate from $8.0 \mathrm{GT} / \mathrm{s}$ data rate.

If the current data rate of operation is $32.0 \mathrm{GT} / \mathrm{s}$ and perform_equalization_for_loopback is 0 b , transmitter sends TS1 Ordered Sets using the 32.0 GT/s Transmitter settings specified by the Transmitter Preset bits received in the appropriate TS2 Ordered Sets during the most recent transition to the 32.0 GT/s data rate (EQ TS2 if equalization bypass was negotiated, 128b/130b EQ TS2 Ordered Sets if the most recent transition to the 32.0 GT/s data rate was from the $16.0 \mathrm{GT} / \mathrm{s}$ data rate).

If the current data rate of operation is $64.0 \mathrm{GT} / \mathrm{s}$ and perform_equalization_for_loopback is 0 b , transmitter sends TS0 Ordered Sets using the 64.0 GT/s Transmitter settings specified by the Transmitter Preset bits

received in the 128b/130b EQ TS2 Ordered Sets at $32.0 \mathrm{GT} / \mathrm{s}$ during the most recent transition to the $64.0 \mathrm{GT} / \mathrm{s}$ data rate.

Lanes that received a Reserved or unsupported Transmitter preset value must use an implementation specific method to choose a supported Transmitter preset setting for use. Any reference to Transmitter Preset bits received in EQ TS2 Ordered Sets or $16.0 \mathrm{GT} / \mathrm{s}$ or higher data rate Transmitter Preset bits in 128b/130b EQ TS2 Ordered Sets (depending on the Data Rate) for the remainder of the Recovery. Equalization state is in reference to the presets determined above. In the TS1 Ordered Sets, the EC field is set to 00b, the Transmitter Preset bits of each Lane is set to the value it received in the Transmitter Preset bits of EQ TS2 Ordered Sets or $16.0 \mathrm{GT} / \mathrm{s}$ or higher data rate Transmitter Preset bits of 128b/130b EQ TS2 Ordered Sets, and the Pre-cursor Coefficient, Cursor Coefficient, and Post-cursor Coefficient fields are set to values corresponding to the Transmitter Preset bits.

- For Lanes that received a Reserved or unsupported Transmitter preset value in the EQ TS2 Ordered Sets or 128b/130b EQ TS2 Ordered Sets (depending on the Data Rate): in the TS1/TS0 Ordered Sets, the Transmitter Preset field is set to the received Transmitter preset value, the Reject Coefficient Values bit is Set (applies to TS1 Ordered Sets only) and the Coefficient fields are set to values corresponding to the implementation specific Transmitter preset setting chosen by the Lane. ${ }^{90}$
- For Lanes that did not receive EQ TS2 Ordered Sets or 128b/130b EQ TS2 Ordered Sets (depending on the Data Rate): in the TS1/TS0 Ordered Sets, the Transmitter Preset field is set to the implementation specific Transmitter preset value chosen by the Lane, the Reject Coefficient Values bit is Clear (applies to TS1 Ordered Sets only), and the Coefficient fields are set to values corresponding to the same implementation specific Transmitter preset value chosen by the Lane and advertised in the Transmitter Preset bits. ${ }^{91}$


# IMPLEMENTATION NOTE: REJECT COEFFICIENT VALUES WITH TS0 ORDERED SETS 

The Reject Coefficient Values bit is intentionally omitted from the TS0 Ordered Set definition. As a result, Upstream Lanes are not able to explicitly indicate that a Reserved or unsupported Transmitter preset value was received in the 128b/130b EQ TS2 Ordered Sets at $32.0 \mathrm{GT} / \mathrm{s}$ during the most recent transition to the $64.0 \mathrm{GT} / \mathrm{s}$ data rate. In order to determine whether an Upstream Lane is using said Transmitter Preset, the Downstream Lane is permitted to observe the Transmitter Preset setting in the TS0 Ordered Sets received in Recovery. Equalization Phase 1 with the EC field set to 00b or 01b.

- The Upstream Port is permitted to wait for up to 500 ns after entering Phase 0 before evaluating receiver information for TS0/TS1 Ordered Sets if it needs the time to stabilize its Receiver logic.
- Next phase is Phase 1 if all the configured Lanes receive two consecutive TS1 Ordered Sets with EC = 01b or if all the configured Lanes receive two consecutive TS0 Ordered Sets with EC = 01b and Retimer Equalization Extend bit set to 0b
- The Receiver must complete its bit lock process and then recognize Ordered Sets within 2 ms after receiving the first bit of the first valid Ordered Set on its Receiver pin.
- The LF and FS values received in the two consecutive TS0/TS1 Ordered Sets must be stored for use during Phase 2 if the Upstream Port wants to adjust the Downstream Port's Transmitter coefficients.

[^0]
[^0]:    90. An earlier version of this specification permitted the Reject Coefficient Values bit to be clear for this case. This is not recommended, but is permitted.
    91. An earlier version of this specification permitted the Transmitter Preset bits to be undefined and the Reject Coefficient Values bit to be clear for this case. This is not recommended, but is permitted

- Next state is Loopback.Entry after a 12 ms timeout if perform_equalization_for_loopback is 1b.
- Else, next state is Recovery.Speed after a 12 ms timeout.
- successful_speed_negotiation is set to 0 b.
- If the data rate is $8.0 \mathrm{GT} / \mathrm{s}$, the Equalization $8.0 \mathrm{GT} / \mathrm{s}$ Complete bit of the Link Status 2 Register is set to 1 b .
- If the data rate is $16.0 \mathrm{GT} / \mathrm{s}$, the Equalization $16.0 \mathrm{GT} / \mathrm{s}$ Complete bit of the $16.0 \mathrm{GT} / \mathrm{s}$ Status Register is set to 1 b .
- If the data rate is $32.0 \mathrm{GT} / \mathrm{s}$, the Equalization $32.0 \mathrm{GT} / \mathrm{s}$ Complete bit of the $32.0 \mathrm{GT} / \mathrm{s}$ Status Register is set to 1 b .
- If the data rate is $64.0 \mathrm{GT} / \mathrm{s}$, the Equalization $64.0 \mathrm{GT} / \mathrm{s}$ Complete bit of the $64.0 \mathrm{GT} / \mathrm{s}$ Status Register is set to 1 b .


# 4.2.7.4.2.2.2 Phase 1 of Transmitter Equalization 

- Transmitter sends TS0/TS1 Ordered Sets using the Transmitter settings determined in Phase 0. In the TS0/TS1 Ordered Sets, the EC field is set to 01b, and the FS, LF, and (in TS1 Ordered Sets only) Post-cursor Coefficient fields of each Lane are set to values corresponding to the Lane's current Transmitter settings.
- If Recovery.Equalization was entered from Loopback.Entry and perform_equalization_for_loopback_64GT is 1b, Loopback Follower must advertise 64.0 GT/s support in the transmitted TS0/TS1 Ordered Sets (i.e., Data Rate Identifier must use the Flit Mode Encoding).
- Next phase is Phase 2 if all configured Lanes receive two consecutive TS0/TS1 Ordered Sets with EC=10b
- If the data rate is $8.0 \mathrm{GT} / \mathrm{s}$, the Equalization $8.0 \mathrm{GT} / \mathrm{s}$ Phase 1 Successful bit of the Link Status 2 Register are set to 1 b .
- If the data rate is $16.0 \mathrm{GT} / \mathrm{s}$, the Equalization $16.0 \mathrm{GT} / \mathrm{s}$ Phase 1 Successful bit of the $16.0 \mathrm{GT} / \mathrm{s}$ Status Register is set to 1b.
- If the data rate is $32.0 \mathrm{GT} / \mathrm{s}$ and perform_equalization_for_loopback is 0 b , the Equalization $32.0 \mathrm{GT} / \mathrm{s}$ Phase 1 Successful bit of the $32.0 \mathrm{GT} / \mathrm{s}$ Status Register is set to 1 b .
- If the data rate is $64.0 \mathrm{GT} / \mathrm{s}$ and perform_equalization_for_loopback is 0 b , the Equalization $64.0 \mathrm{GT} / \mathrm{s}$ Phase 1 Successful bit of the $64.0 \mathrm{GT} / \mathrm{s}$ Status Register is set to 1 b .
- Next state is Loopback.Entry after a 12 ms timeout if perform_equalization_for_loopback is 1b.
- Next state is Recovery.RcvrLock if all configured Lanes receive eight consecutive TS0/TS1 Ordered Sets with EC=00b and perform_equalization_for_loopback is 0 b .
- If the data rate is $8.0 \mathrm{GT} / \mathrm{s}$, the Equalization $8.0 \mathrm{GT} / \mathrm{s}$ Phase 1 Successful and Equalization $8.0 \mathrm{GT} / \mathrm{s}$ Complete bits of the Link Status 2 Register are set to 1b
- If the data rate is $16.0 \mathrm{GT} / \mathrm{s}$, the Equalization $16.0 \mathrm{GT} / \mathrm{s}$ Phase 1 Successful and Equalization $16.0 \mathrm{GT} / \mathrm{s}$ Complete bits of the $16.0 \mathrm{GT} / \mathrm{s}$ Status Register are set to 1 b .
- If the data rate is $32.0 \mathrm{GT} / \mathrm{s}$, the Equalization $32.0 \mathrm{GT} / \mathrm{s}$ Phase 1 Successful and Equalization $32.0 \mathrm{GT} / \mathrm{s}$ Complete bits of the $32.0 \mathrm{GT} / \mathrm{s}$ Status Register are set to 1 b .
- If the data rate is $64.0 \mathrm{GT} / \mathrm{s}$, the Equalization $64.0 \mathrm{GT} / \mathrm{s}$ Phase 1 Successful and Equalization $64.0 \mathrm{GT} / \mathrm{s}$ Complete bits of the $64.0 \mathrm{GT} / \mathrm{s}$ Status Register are set to 1 b .
- Else, next state is Recovery.Speed after a 12 ms timeout if perform_equalization_for_loopback is 0 b
- successful_speed_negotiation is set to 0 b .
- If the data rate is $8.0 \mathrm{GT} / \mathrm{s}$, the Equalization $8.0 \mathrm{GT} / \mathrm{s}$ Complete bit of the Link Status 2 Register for the current data rate of operation is set to 1 b .

- If the data rate is $16.0 \mathrm{GT} / \mathrm{s}$, the Equalization $16.0 \mathrm{GT} / \mathrm{s}$ Complete bit of the $16.0 \mathrm{GT} / \mathrm{s}$ Status Register is set to 1 b .
- If the data rate is $32.0 \mathrm{GT} / \mathrm{s}$, the Equalization $32.0 \mathrm{GT} / \mathrm{s}$ Complete bit of the $32.0 \mathrm{GT} / \mathrm{s}$ Status Register is set to 1 b .
- If the data rate is $64.0 \mathrm{GT} / \mathrm{s}$, the Equalization $64.0 \mathrm{GT} / \mathrm{s}$ Complete bit of the $64.0 \mathrm{GT} / \mathrm{s}$ Status Register is set to 1 b .


# 4.2.7.4.2.2.3 Phase 2 of Transmitter Equalization 

- Transmitter sends TS0/TS1 Ordered Sets with EC = 10b
- The Port must evaluate and arrive at the optimal settings independently on each Lane. When perform_equalization_for_loopback is 1b, the equalization procedure is only performed on the Lane under test. To evaluate a new preset or coefficient setting that is legal, as per the rules in § Section 4.2.4 and § Chapter 8. :
- Request a new preset by setting the Transmitter Preset bits to the desired value and set the Use Preset bit to 1b. Alternatively, request a new set of coefficients by setting the Pre-cursor, Cursor, and Post-cursor Coefficient fields to the desired values and set the Use Preset bit to 0b. Once a request is made, it must be continuously requested for at least $1 \mu \mathrm{~s}$ or until the evaluation of the request is completed, whichever is later.
- Wait for the required time ( 500 ns plus the roundtrip delay including the logic delays through the Upstream Port) to ensure that, if accepted, the Downstream Port is transmitting using the requested settings. Obtain Block Alignment and then evaluate the incoming Ordered Sets. Note: The Upstream Port may simply ignore anything it receives during this waiting period as the incoming bit stream may be illegal during the transition to the requested settings. Hence the requirement to validate Block Alignment after this waiting period. If Block Alignment cannot be obtained after an implementation specific amount of time (in addition to the required waiting period specified above) it is recommended to proceed to perform Receiver evaluation on the incoming bit stream regardless.
- If two consecutive TS1 Ordered Sets are received with the Transmitter Preset bits (for a preset request) or the Pre-cursor, Cursor, and Post-Cursor Coefficient fields (for a coefficients request) identical to what was requested and the Reject Coefficient Values bit is Clear, then the requested setting was accepted and, depending on the results of Receiver evaluation, can be considered as a candidate final setting.
- If two consecutive TS1 Ordered Sets are received with the Transmitter Preset bits (for a preset request) or the Pre-Cursor, Cursor, and Post-Cursor Coefficient fields (for a coefficients request) identical to what was requested and the Reject Coefficient Values bit is Set, then the requested setting was rejected and must not be considered as a candidate final setting.
- If, after an implementation specific amount of time following the start of Receiver evaluation, no consecutive TS1s with the Transmitter Preset bits (for a preset request) or the Pre-Cursor, Cursor, and Post-Cursor Coefficient fields (for a coefficients request) identical to what was requested are received, then the requested setting must not be considered as a candidate final setting.
- The Upstream Port is responsible for setting the Reset EIEOS Interval Count bit in the TS0/TS1 Ordered Sets it transmits according to its evaluation criteria and requirements. The Use Preset bit of the received TS1 Ordered Sets must not be used to determine whether a request is accepted or rejected.

# IMPLEMENTATION NOTE: RESET EIEOS AND COEFFICIENT/PRESET REQUESTS 5 

A Port may set Reset EIEOS Interval Count to 1b when it wants a longer PRBS pattern and subsequently clear it when it needs to obtain Block Alignment.

All TS0/TS1 Ordered Sets transmitted in this phase are requests. The first request maybe a new preset or a new coefficient request or a request to maintain the current link partner transmitter settings by reflecting the settings received in the two consecutive TS1 Ordered Sets with EC=10b that cause the transition to Phase 2.

- At 32.0 GT/s and below data rates, the total amount of time spent per preset or coefficients request from transmission of the request to the completion of the evaluation must be less than 2 ms . Implementations that need a longer evaluation time at the final stage of optimization may continue requesting the same setting beyond the 2 ms limit but must adhere to the timeout in this phase ( 24 ms for $8.0,16.0$, and $32.0 \mathrm{GT} / \mathrm{s}$ and 48 ms for $64.0 \mathrm{GT} / \mathrm{s}$ ) and must not take this exception more than two times. If the requester is unable to receive Ordered Sets within the timeout period, it may assume that the requested setting does not work in that Lane.
- At 64.0 GT/s and higher data rates, a device is permitted to evaluate each preset or coefficients request for an arbitrary amount of time. Evaluation must be carefully managed such that the search for an acceptable preset or coefficients can be successful. The total time spent in this Phase must still adhere to the timeout.
- All new preset or coefficient settings must be presented on all configured Lanes simultaneously. Any given Lane is permitted to continue to transmit the current preset or coefficients as its new value if it does not want to change the setting at that time.
- If perform_equalization_for_loopback is 1b and the Lane under test is operating at its optimal setting and two consecutive TS1 Ordered Sets with the Retimer Equalization Extend bit set to 0b are received, next phase is Phase 3.
- If perform_equalization_for_loopback is 0 b and all configured Lanes are operating at their optimal settings and either the data rate of operation is $8.0 \mathrm{GT} / \mathrm{s}$ or all Lanes receive two consecutive TS1 Ordered Sets with the Retimer Equalization Extend bit set to 0b, next phase is Phase 3.
- If the data rate of operation is $8.0 \mathrm{GT} / \mathrm{s}$ : The Equalization $8.0 \mathrm{GT} / \mathrm{s}$ Phase 2 Successful bit of the Link Status 2 Register are set to 1b.
- If the data rate of operation is $16.0 \mathrm{GT} / \mathrm{s}$ : The Equalization $16.0 \mathrm{GT} / \mathrm{s}$ Phase 2 Successful bit of the $16.0 \mathrm{GT} / \mathrm{s}$ Status Register is set to 1b.
- If the data rate of operation is $32.0 \mathrm{GT} / \mathrm{s}$ : The Equalization $32.0 \mathrm{GT} / \mathrm{s}$ Phase 2 Successful bit of the $32.0 \mathrm{GT} / \mathrm{s}$ Status Register is set to 1b.
- If the data rate of operation is $64.0 \mathrm{GT} / \mathrm{s}$ : The Equalization $64.0 \mathrm{GT} / \mathrm{s}$ Phase 2 Successful bit of the $64.0 \mathrm{GT} / \mathrm{s}$ Status Register is set to 1b.
- Next state is Loopback. Entry after a timeout of 24 ms with a tolerance of -0 ms and +2 ms if perform_equalization_for_loopback is 1 b and current data rate is less than $64.0 \mathrm{GT} / \mathrm{s}$.
- Next state is Loopback. Entry after a timeout of 48 ms with a tolerance of -0 ms and +2 ms if perform_equalization_for_loopback is 1 b and current data rate is $64.0 \mathrm{GT} / \mathrm{s}$.

- Else, if the current data rate is less than 64.0 GT/s: next state is Recovery.Speed after a timeout of 24 ms with a tolerance of -0 ms and +2 ms
- successful_speed_negotiation is set to 0 b.
- If the data rate of operation is 8.0 GT/s: The Equalization 8.0 GT/s Complete bit of the Link Status 2 Register is set to 1 b.
- If the data rate of operation is 16.0 GT/s: The Equalization 16.0 GT/s Complete bit of the 16.0 GT/s Status Register is set to 1b.
- If the data rate of operation is 32.0 GT/s: The Equalization 32.0 GT/s Complete bit of the 32.0 GT/s Status Register is set to 1b.
- Else, if the current data rate is 64.0 GT/s: next state is Recovery.Speed after a timeout of 48 ms with a tolerance of -0 ms and +2 ms
- successful_speed_negotiation is set to 0 b.
- The Equalization 64.0 GT/s Complete bit of the 64.0 GT/s Status Register is set to 1b.


# 4.2.7.4.2.2.4 Phase 3 of Transmitter Equalization 

- The Transmitter sends TS0 Ordered Sets with $\mathrm{EC}=11 \mathrm{~b}$ if the data rate is 64.0 GT/s and all Lanes have not received two consecutive TS1 Ordered Sets with EC=11b since entering this Phase; else it sends TS1 Ordered Sets.
- Transmitter sends TS0/TS1 Ordered Sets with EC = 11b and the coefficient settings, set on each configured Lane independently, as follows:
- If two consecutive TS1 Ordered Sets with EC=11b have been received since entering Phase 3, or two consecutive TS1 Ordered Sets with EC=11b and a preset or set of coefficients (as specified by the Use Preset bit) different than the last two consecutive TS1 Ordered Sets with EC=11b:
- If the preset or coefficients requested in the most recent two consecutive TS Ordered Sets are legal and supported (see § Section 4.2.4 and § Chapter 8. ):
- Change the transmitter settings to the requested preset or coefficients such that the new settings are effective at the Transmitter pins within 500 ns of when the end of the second TS1 Ordered Set requesting the new setting was received at the Receiver pin. The change of Transmitter settings must not cause any illegal voltage level or parameter at the Transmitter pin for more than 1 ns.
- In the transmitted TS1 Ordered Sets, the Transmitter Preset bits are set to the requested preset (for a preset request), the Pre-cursor, Cursor, and Post-cursor Coefficient fields are set to the Transmitter settings (for a preset or a coefficients request), and the Reject Coefficient Values bit is Clear.
- Else (the requested preset or coefficients are illegal or unsupported): Do not change the Transmitter settings used, but reflect the requested preset or coefficient values in the transmitted TS1 Ordered Sets and set the Reject Coefficient Values bit to 1b.
- Else: the preset and coefficients currently being used by the Transmitter.
- The Transmitter preset value initially transmitted on entry to Phase 3 can be the Transmitter preset value transmitted in Phase 0 for the same Data Rate or the Transmitter preset setting currently being used by the Transmitter.
- Next state is Loopback. Entry if perform_equalization_for_loopback is 1b, the current data rate is less than $64.0 \mathrm{GT} / \mathrm{s}$, and one of the following conditions is satisfied:
a. The Lane under test receives two consecutive TS1 Ordered Sets with EC=00b.

b. A timeout of 32 ms with a tolerance of -0 ms and +4 ms .

- Next state is Loopback.Entry if perform_equalization_for_loopback is 1b, the current data rate is equal to $64.0 \mathrm{GT} / \mathrm{s}$, and one of the following conditions is satisfied:
a. The Lane under test receives two consecutive TS1 Ordered Sets with EC=00b.
b. A timeout of 64 ms with a tolerance of -0 ms and +4 ms .
- Next state is Recovery.RcvrLock if all configured Lanes receive two consecutive TS1 Ordered Sets with EC=00b.
- If the data rate is $8.0 \mathrm{GT} / \mathrm{s}$, the Equalization $8.0 \mathrm{GT} / \mathrm{s}$ Phase 3 Successful and Equalization $8.0 \mathrm{GT} / \mathrm{s}$ Complete bits of the Link Status 2 Register are set to 1b.
- If the data rate is $16.0 \mathrm{GT} / \mathrm{s}$, the Equalization $16.0 \mathrm{GT} / \mathrm{s}$ Phase 3 Successful and Equalization $16.0 \mathrm{GT} / \mathrm{s}$ Complete bits of the $16.0 \mathrm{GT} / \mathrm{s}$ Status Register are set to 1 b .
- If the data rate is $32.0 \mathrm{GT} / \mathrm{s}$, the Equalization $32.0 \mathrm{GT} / \mathrm{s}$ Phase 3 Successful and Equalization $32.0 \mathrm{GT} / \mathrm{s}$ Complete bits of the $32.0 \mathrm{GT} / \mathrm{s}$ Status Register are set to 1 b .
- If the data rate is $64.0 \mathrm{GT} / \mathrm{s}$, the Equalization $64.0 \mathrm{GT} / \mathrm{s}$ Phase 3 Successful and Equalization $64.0 \mathrm{GT} / \mathrm{s}$ Complete bits of the $64.0 \mathrm{GT} / \mathrm{s}$ Status Register are set to 1 b .
- Else, if the current data rate is less than $64.0 \mathrm{GT} / \mathrm{s}$ : next state is Recovery.Speed after a timeout of 32 ms with a tolerance of -0 ms and +4 ms
- successful_speed_negotiation is set to 0 b .
- If the data rate is $8.0 \mathrm{GT} / \mathrm{s}$, the Equalization $8.0 \mathrm{GT} / \mathrm{s}$ Complete bit of the Link Status 2 Register is set to 1 b .
- If the data rate is $16.0 \mathrm{GT} / \mathrm{s}$, the Equalization $16.0 \mathrm{GT} / \mathrm{s}$ Complete bit of the $16.0 \mathrm{GT} / \mathrm{s}$ Status Register is set to 1 b .
- If the data rate is $32.0 \mathrm{GT} / \mathrm{s}$, the Equalization $32.0 \mathrm{GT} / \mathrm{s}$ Complete bit of the $32.0 \mathrm{GT} / \mathrm{s}$ Status Register is set to 1 b .
- Else, if current data rate is $64.0 \mathrm{GT} / \mathrm{s}$ : next state is Recovery.Speed after a timeout of 64 ms with a tolerance of -0 ms and +4 ms
- successful_speed_negotiation is set to 0 b .
- The Equalization $64.0 \mathrm{GT} / \mathrm{s}$ Complete bit of the $64.0 \mathrm{GT} / \mathrm{s}$ Status Register is set to 1 b .


# 4.2.7.4.3 Recovery.Speed 

- The Transmitter enters Electrical Idle and stays there until the Receiver Lanes have entered Electrical Idle, and then additionally remains there for at least 800 ns on a successful speed negotiation (i.e., successful_speed_negotiation $=1 \mathrm{~b}$ ) or at least $6 \mu \mathrm{~s}$ on an unsuccessful speed negotiation (i.e., successful_speed_negotiation $=0 \mathrm{~b}$ ), but stays there no longer than an additional 1 ms . The frequency of operation is permitted to be changed to the new data rate only after the Receiver Lanes have entered Electrical Idle. If the negotiated data rate is $5.0 \mathrm{GT} / \mathrm{s}$, and if operating in full swing mode, -6 dB de-emphasis level must be selected for operation if the select_deemphasis variable is 0 b and -3.5 dB de-emphasis level must be selected for operation if the select_deemphasis variable is 1 b . Note that if the link is already operating at the highest data rate supported by both Ports, Recovery.Speed is executed but the data rate is not changed.

An EIOSQ must be sent prior to entering Electrical Idle.
The DC common mode voltage is not required to be within specification.
An Electrical Idle condition exists on the Lanes if an EIOS is received on any of the configured Lanes or Electrical Idle is detected/inferred as described in $\S$ Section 4.2.5.4 .

- On entry to this substate following a successful speed negotiation (i.e., successful_speed_negotiation $=1 b$ ), an Electrical Idle condition may be inferred on the Receiver Lanes if a TS1 or TS2 Ordered Set has not been received in any configured Lane in a time interval specified in § Table 4-48. (This covers the case where the Link is operational and both sides have successfully received TS Ordered Sets. Hence, a lack of a TS1 or TS2 Ordered Set in the specified interval can be interpreted as entry to Electrical Idle.)
- Else on entry to this substate following an unsuccessful speed negotiation (i.e., successful_speed_negotiation $=0 b$ ) if an exit from Electrical Idle has not been detected at least once in any configured Lane in a time interval specified in § Table 4-48. (This covers the case where at least one side is having trouble receiving TS Ordered Sets that was transmitted by the other agent, and hence a lack of exit from Electrical Idle in a longer interval can be treated as equivalent to entry to Electrical Idle.)
- Next state is Recovery.RcvrLock after the Transmitter Lanes are no longer required to be in Electrical Idle as described in the condition above.
- If this substate has been entered from Recovery.RcvrCfg following a successful speed change negotiation (i.e., successful_speed_negotiation $=1 b$ ), the new data rate is changed on all the configured Lanes to the highest common data rate advertised by both sides of the Link. The changed_speed_recovery variable is set to 1b.
- Else if this substate is being entered for a second time since entering Recovery from L0 or L1 (i.e., changed_speed_recovery = 1b), the new data rate will be the data rate at which the LTSSM entered Recovery from L0 or L1. The changed_speed_recovery variable will be reset to 0b.
- Else if the latest encoding used before entering Recovery.Speed was $1 \mathrm{~b} / 1 \mathrm{~b}$, the new data rate will be 32.0 GT/s. The changed_speed_recovery variable remains reset at 0 b .
- Else the new data rate will be $2.5 \mathrm{GT} / \mathrm{s}$. The changed_speed_recovery variable remains reset at 0 b .

Note: This represents the case where the frequency of operation in L0 was greater than $2.5 \mathrm{GT} / \mathrm{s}$ and one side could not operate at that frequency and timed out in Recovery.RcvrLock the first time it entered that substate from L0 or L1.

- Next state is Detect after a 48 ms timeout if the Link Speed at which Recovery.Speed was entered was < $64.0 \mathrm{GT} / \mathrm{s}$.
- Note: This transition is not possible under normal conditions.
- Next state is Detect after a 96 ms timeout or 48 ms timeout if the Link Speed at which Recovery.Speed was entered was $\geq 64.0 \mathrm{GT} / \mathrm{s}$.
- Note: The 96 ms timeout is strongly recommended because the 48 ms timeout could cause an unintended timeout to Detect at $64.0 \mathrm{GT} / \mathrm{s}$. This timeout to Detect can occur due to the $64.0 \mathrm{GT} / \mathrm{s}$ Recovery. Equalization Phase 2 timeout ( 64 ms ) being larger than the Phase 1 timeout ( 12 ms ) + Recovery.Speed timeout ( 48 ms ).
- The directed_speed_change variable will be reset to 0 b . The new data rate must be reflected in the Current Link Speed field of the Link Status Register.
- On a Link bandwidth change, if successful_speed_negotiation is set to 1 b and the Autonomous Change bit (bit 6 of Symbol 4) in the eight consecutive TS2 Ordered Sets received while in Recovery.RcvrCfg is set to 1 b or the speed change was initiated by the Downstream Port for autonomous reasons (non-reliability and not due to the setting of the Link Retrain bit), the Link Autonomous Bandwidth Status bit of the Link Status Register is set to 1b.
- Else: on a Link bandwidth change, the Link Bandwidth Management Status bit of the Link Status Register is set to 1 b .

# 4.2.7.4.4 Recovery.RcvrCfg 

In Non-Flit Mode, Transmitter sends TS2 Ordered Sets on all configured Lanes using the same Link and Lane numbers that were set after leaving Configuration. In Flit Mode, Transmitter sends TS2 Ordered Sets on all configured Lanes with the Link number field sets as follows: if the LTSSM is initiating a Link width change by transitioning to Configuration from this State and the Lane will be removed from the Link, then the Link number field is set to PAD; otherwise it is set as the Link number. In 1b/1b TS2 Ordered Sets, if an equalization request is being communicated, Symbols 1,9 represent Equalization Byte 0 (instead of Link Number), the Request Equalization bit is set to 1 b and the other fields are set as described in $\S$ Section 4.2.4 and $\S$ Table 4-37. The LTSSM must not initiate a width change if speed_change is set to 1 b or the LTSSM went through Recovery. Equalization followed by Recovery.RcvrLock prior to entering this substate. The speed_change bit (bit 7 of data rate identifier Symbol in TS2 Ordered Set) must be set to 1 b if the directed_speed_change variable is already set to 1 b . The N_FTS value in the transmitted TS2 Ordered Sets should reflect the number at the current data rate for Non-Flit Mode of operation. In Flit Mode, the appropriate Training Control bit of the TS2 Ordered set must be set, if the Port intends to drive the Link to Hot Reset, Disabled, or Loopback state immediately after exiting this sub-state.

Training Control bit is not a bit field in 1b/1b.
The Downstream Port must transmit EQ TS2 Ordered Sets (TS2 Ordered Sets with Symbol 6 bit 7 set to 1b) on each configured Lane with the Transmitter Preset and Receiver Preset Hint fields set to the values specified by the Upstream 8.0 GT/s Port Transmitter Preset and the Upstream 8.0 GT/s Port Receiver Preset Hint fields from the corresponding Lane Equalization Control Register Entry if all of the following conditions are satisfied:
a. The Downstream Port advertised 8.0 GT/s data rate support in Recovery.RcvrLock, and 8.0 GT/s data rate support has been advertised in the Configuration.Complete or Recovery.RcvrCfg substates by the Upstream Port since exiting the Detect state, and eight consecutive TS1 or TS2 Ordered Sets were received on any configured Lane prior to entry to this substate with speed_change bit set to 1b
b. The equalization_done_8GT_data_rate variable is 0 b or if the Perform Equalization bit in the Link Control 3 Register is Set or if an implementation specific mechanism determined equalization needs to be performed, following procedures described in $\S$ Section 4.2.4
c. The current data rate of operation is $2.5 \mathrm{GT} / \mathrm{s}$ or $5.0 \mathrm{GT} / \mathrm{s}$

The Downstream Port must transmit EQ TS2 Ordered Sets (TS2 Ordered Sets with Symbol 6 bit 7 set to 1b) on each configured Lane with the Transmitter Preset bits set to the values specified by the Upstream Port 32.0 GT/s Transmitter Preset bits from the corresponding 32.0 GT/s Lane Equalization Control Register Entry if all of the following conditions are satisfied:
a. The Downstream Port advertised 32.0 GT/s data rate support in Recovery.RcvrLock, and 32.0 GT/s data rate support has been advertised in the Configuration.Complete or Recovery.RcvrCfg substates by the Upstream Port since exiting the Detect state, and eight consecutive TS1 or TS2 Ordered Sets were received on any configured Lane prior to entry to this substate with speed_change bit set to 1b
b. The equalization_done_32GT_data_rate variable is 0 b or if the Perform Equalization bit in the Link Control 3 Register is Set or if an implementation specific mechanism determined equalization needs to be performed, following procedures described in $\S$ Section 4.2.4
c. The equalization_done_8GT_data_rate and equalization_done_16GT_data_rate variables are 1b each
d. Equalization Bypass to Highest NRZ Rate was negotiated between the components during Configuration state
e. The current data rate of operation is $2.5 \mathrm{GT} / \mathrm{s}$ or $5.0 \mathrm{GT} / \mathrm{s}$

The Downstream Port must transmit 128b/130b EQ TS2 Ordered Sets (TS2 Ordered Sets with Symbol 7 bit 7 set to 1b) on each configured Lane with the Transmitter Preset bits set to the values specified by the Upstream Port 16.0 GT/s Transmitter

Preset bits from the corresponding 16.0 GT/s Lane Equalization Control Register Entry if all of the following conditions are satisfied:
a. The Downstream Port advertised 16.0 GT/s data rate support in Recovery.RcvrLock, and 16.0 GT/s data rate support has been advertised in the Configuration.Complete or Recovery.RcvrCfg substates by the Upstream Port since exiting the Detect state, and eight consecutive TS1 or TS2 Ordered Sets were received on any configured Lane prior to entry to this substate with speed_change bit set to 1b
b. The equalization_done_16GT_data_rate variable is 0 b or if the Perform Equalization bit in the Link Control 3 Register is set or an implementation specific mechanism determined equalization needs to be performed, following procedures described in $\S$ Section 4.2.4
c. The current data rate of operation is $8.0 \mathrm{GT} / \mathrm{s}$

The Downstream Port must transmit 128b/130b EQ TS2 Ordered Sets (TS2 Ordered Sets with Symbol 7 bit 7 set to 1b) on each configured Lane with the Transmitter Preset bits set to the values specified by the Upstream Port 32.0 GT/s Transmitter Preset bits from the corresponding 32.0 GT/s Lane Equalization Control Register Entry if all of the following conditions are satisfied:
a. The Downstream Port advertised 32.0 GT/s data rate support in Recovery.RcvrLock, and 32.0 GT/s data rate support has been advertised in the Configuration.Complete or Recovery.RcvrCfg substates by the Upstream Port since exiting the Detect state, and eight consecutive TS1 or TS2 Ordered Sets were received on any configured Lane prior to entry to this substate with speed_change bit set to 1b
b. The equalization_done_32GT_data_rate variable is 0 b or the Perform Equalization bit in the Link Control 3 Register is set or an implementation specific mechanism determined equalization needs to be performed, following procedures described in $\S$ Section 4.2.4
c. The current data rate of operation is $16.0 \mathrm{GT} / \mathrm{s}$

The Downstream Port must transmit 128b/130b EQ TS2 Ordered Sets (TS2 Ordered Sets with Symbol 7 bit 7 set to 1b) on each configured Lane with the Transmitter Preset bits set to the values specified by the Upstream Port 64.0 GT/s Transmitter Preset bits from the corresponding 64.0 GT/s Lane Equalization Control Register Entry if all of the following conditions are satisfied:
a. The Downstream Port advertised 64.0 GT/s data rate support in Recovery.RcvrLock, and 64.0 GT/s data rate support has been advertised in the Configuration.Complete or Recovery.RcvrCfg substates by the Upstream Port since exiting the Detect state, and eight consecutive TS1 or TS2 Ordered Sets were received on any configured Lane prior to entry to this substate with speed_change bit set to 1b
b. The equalization_done_64GT_data_rate variable is 0 b or the Perform Equalization bit in the Link Control 3 Register is set or an implementation specific mechanism determined equalization needs to be performed, following procedures described in $\S$ Section 4.2.4
c. The current data rate of operation is $32.0 \mathrm{GT} / \mathrm{s}$

The Upstream Port is permitted to transmit 128b/130b EQ TS2 Ordered Sets with the 16.0 GT/s Transmitter Preset bits set to implementation specific values if all of the following conditions are satisfied:
a. The Upstream Port advertised 16.0 GT/s data rate support in Recovery.RcvrLock, and 16.0 GT/s data rate support has been advertised in the Configuration.Complete or Recovery.RcvrCfg substates, or optionally, but strongly recommended, in the Recovery.RcvrLock substate by the Downstream Port since exiting the Detect state, and eight consecutive TS1 or TS2 Ordered Sets were received on any configured Lane prior to entry to this substate with speed_change bit set to 1b
b. The equalization_done_16GT_data_rate variable is 0 b or if directed by an implementation specific mechanism, following procedures described in $\S$ Section 4.2.4

c. The current data rate of operation is $8.0 \mathrm{GT} / \mathrm{s}$

The Upstream Port that intends to bypass equalization to the highest data rate of $32.0 \mathrm{GT} / \mathrm{s}$ or higher must transmit 8b/ 10b EQ TS2 Ordered Sets with the $32.0 \mathrm{GT} / \mathrm{s}$ Transmitter Preset bits set to implementation specific values if all of the following conditions are satisfied:
a. The equalization bypass to the highest NRZ rate was negotiated during the Configuration state
b. Either the Upstream Port requires precoding, or the Upstream Port intends to provide the Downstream Port's starting $32.0 \mathrm{GT} / \mathrm{s}$ Transmitter Preset for equalization
c. The Upstream Port advertised 32.0 GT/s data rate support in Recovery.RcvrLock, and 32.0 GT/s data rate support has been advertised in the Configuration.Complete or Recovery.RcvrCfg substates by the Downstream Port since exiting the Detect state, and eight consecutive TS1 or TS2 Ordered Sets were received on any configured Lane prior to entry to this substate with speed_change bit set to 1b
d. The equalization_done_32GT_data_rate variable is 0 b or if directed by an implementation specific mechanism, following procedures described in $\S$ Section 4.2.4
e. The current data rate of operation is $2.5 \mathrm{GT} / \mathrm{s}$ or $5.0 \mathrm{GT} / \mathrm{s}$

The Upstream Port is permitted to transmit 128b/130b EQ TS2 Ordered Sets with the 32.0 GT/s Transmitter Preset bits set to implementation specific values if all of the following conditions are satisfied:
a. The Upstream Port advertised 32.0 GT/s data rate support in Recovery.RcvrLock, and 32.0 GT/s data rate support has been advertised in the Configuration.Complete or Recovery.RcvrCfg substates, or optionally, but strongly recommended, in the Recovery.RcvrLock substate by the Downstream Port since exiting the Detect state, and eight consecutive TS1 or TS2 Ordered Sets were received on any configured Lane prior to entry to this substate with speed_change bit set to 1b
b. The equalization_done_32GT_data_rate variable is 0 b or if directed
c. The current data rate of operation is $16.0 \mathrm{GT} / \mathrm{s}$

The Upstream Port is permitted to transmit 128b/130b EQ TS2 Ordered Sets with the 64.0 GT/s Transmitter Preset bits set to implementation specific values if all of the following conditions are satisfied:
a. The Upstream Port advertised 64.0 GT/s data rate support in Recovery.RcvrLock, and 64.0 GT/s data rate support has been advertised in the Configuration.Complete, Recovery.RcvrLock or Recovery.RcvrCfg substates by the Downstream Port since exiting the Detect state, and eight consecutive TS1 or TS2 Ordered Sets were received on any configured Lane prior to entry to this substate with speed_change bit set to 1b
b. The equalization_done_64GT_data_rate variable is 0 b or if directed
c. The current data rate of operation is $32.0 \mathrm{GT} / \mathrm{s}$

# IMPLEMENTATION NOTE: ISSUES WITH SOFTWARE INITIATED SPEED CHANGE 

In prior versions of the specification, the EQ TS2 Ordered Sets from the Upstream Port may not be registered by the Downstream Port in the case where hardware autonomous equalization was not adopted. The Downstream Port enters Recovery and advertises a higher data rate ( $16.0 \mathrm{GT} / \mathrm{s}$ and above) for the first time with the software initiated speed change; the Upstream Port did not observe the new speed in Configuration.Complete. So if it was acting on the new speed based on observation in Recovery.RcvrCfg (as was required in prior versions of this specification), it may decide to switch from TS2 to EQ TS2 Ordered Sets while in Recovery.RcvrCfg. The Downstream Port may have satisfied its requirements with 8 consecutive TS2 Ordered Sets and missed the Preset request (for $16.0 \mathrm{GT} / \mathrm{s}$ or higher data rate) or Precoding request (for $32.0 \mathrm{GT} / \mathrm{s}$ or higher data rate) in the subsequent EQ TS2 Ordered Sets.

The situation described above can be avoided if the Upstream Port decides to send EQ TS2 Ordered Sets based on the higher speed being advertised by the Downstream Port while it is in Recovery.RcvrLock or if software requests re-equalization at the same data rate through the configuration register in the Downstream Port.

When using 128b/130b or 1b/1b encoding, Upstream and Downstream Ports use the Request Equalization, Equalization Request Data Rate, and Quiesce Guarantee bits of their transmitted TS2 Ordered Sets to communicate equalization requests as described in $\S$ Section 4.2.4. When not requesting equalization, the Request Equalization, Equalization Request Data Rate, and Quiesce Guarantee bits must be set to 0b.

The start_equalization_w_preset variable is reset to 0b upon entry to this substate.

- On entry to this substate, a Downstream Port must set the select_deemphasis variable equal to the Selectable De-emphasis field in the Link Control 2 Register or adopt some implementation specific mechanism to set the select_deemphasis variable, including using the value requested by the Upstream Port in the eight consecutive TS1 Ordered Sets it received. A Downstream Port advertising $5.0 \mathrm{GT} / \mathrm{s}$ data rate support must set the Selectable De-emphasis bit (Symbol 4 bit 6) of the TS2 Ordered Sets it transmits identical to the select_deemphasis variable. An Upstream Port must set its Autonomous Change bit (Symbol 4 bit 6) to 1b in the TS2 Ordered Set if it intends to change the Link bandwidth for autonomous reasons.
- For devices that support Link width upconfigure, it is recommended that the Electrical Idle detection circuitry be activated in the set of currently inactive Lanes in this substate, the Recovery. Idle substate, and Configuration.Linkwidth.Start substates, if the directed_speed_change variable is reset to 0 b . This is done so that during a Link upconfigure, the side that does not initiate the upconfiguration does not miss the first EIEOSQ sent by the initiator during the Configuration.Linkwidth.Start substate.
- Next state is Recovery.Speed if all of the following conditions are true:
- One of the following conditions is satisfied:
i. Eight consecutive TS2 Ordered Sets are received on any configured Lane with identical data rate identifiers, identical values in Symbol 6, and the speed_change bit set to 1b and eight consecutive TS2 Ordered Sets are standard TS2 Ordered Sets if either 8b/10b or 128b/130b encoding is used
ii. Eight consecutive EQ TS2 or 128b/130b EQ TS2 Ordered Sets are received on all configured Lanes with identical data rate identifiers, identical value in Symbol 6, and the speed_change bit set to 1b
iii. Eight consecutive EQ TS2 or 128b/130b EQ TS2 Ordered Sets are received on any configured Lane with identical data rate identifiers, identical value in Symbol 6, and the speed_change

bit set to 1 b and 1 ms has expired since the receipt of the eight consecutive EQ Ordered Sets on any configured Lane
iv. Eight consecutive and identical TS2 Ordered Sets are received on any configured Lane with the speed_change bit set to 1 b when $1 \mathrm{~b} / 1 \mathrm{~b}$ encoding is used

- Either the current data rate is greater than $2.5 \mathrm{GT} / \mathrm{s}$ or greater than $2.5 \mathrm{GT} / \mathrm{s}$ data rate identifiers are set both in the transmitted and the (eight consecutive) received TS2 Ordered Sets
- For 8b/10b encoding, at least 32 TS2 Ordered Sets, without being interrupted by any intervening EIEOS, are transmitted with the speed_change bit set to 1 b after receiving one TS2 Ordered Set with the speed_change bit set to 1 b in the same configured Lane. For 128b/130b and 1b/1b encoding, at least 128 TS2 Ordered Sets are transmitted with the speed_change bit set to 1 b after receiving one TS2 Ordered Set with the speed_change bit set to 1 b in the same configured Lane.

The data rate(s) advertised on the received eight consecutive TS2 Ordered Sets with the speed_change bit set is noted as the data rate(s) that can be supported by the other Port. The Autonomous Change bit (Symbol 4 bit 6) in these received eight consecutive TS2 Ordered Sets is noted by the Downstream Port for possible logging in the Link Status Register in Recovery. Speed substate. Upstream Ports must register the Selectable De-emphasis bit (bit 6 of Symbol 4) advertised in these eight consecutive TS2 Ordered Sets in the select_deemphasis variable. The new speed to change to in Recovery.Speed is the highest data rate that can be supported by both Ports on the Link.

For an Upstream Port, if the current data rate of operation is $2.5 \mathrm{GT} / \mathrm{s}$ or $5.0 \mathrm{GT} / \mathrm{s}$ and these eight consecutive TS2 Ordered Sets are EQ TS2 Ordered Sets advertising $8.0 \mathrm{GT} / \mathrm{s}$ as the highest data rate supported, it must set the start_equalization_w_preset variable to 1b and update the Upstream Port 8.0 GT/s Transmitter Preset and Upstream Port 8.0 GT/s Receiver Preset Hint fields of the Lane Equalization Control Register Entry with the values received in the eight consecutive EQ TS2 Ordered Sets for the corresponding Lane.

For an Upstream Port, if the current data rate of operation is $2.5 \mathrm{GT} / \mathrm{s}$ or $5.0 \mathrm{GT} / \mathrm{s}$ and these eight consecutive TS2 Ordered Sets are EQ TS2 Ordered Sets advertising $32.0 \mathrm{GT} / \mathrm{s}$ as the highest data rate supported and equalization bypass to the highest NRZ rate was negotiated between the components during the Configuration state, it must set the start_equalization_w_preset variable to 1b and update the Upstream Port 32.0 GT/s Transmitter Preset field of the 32.0 GT/s Lane Equalization Control Register Entry with the values received in the eight consecutive EQ TS2 Ordered Sets for the corresponding Lane.

For an Upstream Port, if the current data rate of operation is $8.0 \mathrm{GT} / \mathrm{s}, 16.0 \mathrm{GT} / \mathrm{s}$ support is advertised by both ends, and these eight consecutive TS2 Ordered Sets are 128b/130b EQ TS2 Ordered Sets, it must set the start_equalization_w_preset variable to 1b and update the Upstream Port 16.0 GT/s Transmitter Preset field of the 16.0 GT/s Lane Equalization Control Register Entry with the values received in the eight consecutive 128b/ 130b EQ TS2 Ordered Sets for the corresponding Lane.

For an Upstream Port, if the current data rate of operation is $16.0 \mathrm{GT} / \mathrm{s}, 32.0 \mathrm{GT} / \mathrm{s}$ support is advertised by both ends, and these eight consecutive TS2 Ordered Sets are 128b/130b EQ TS2 Ordered Sets, it must set the start_equalization_w_preset variable to 1b and update the Upstream Port 32.0 GT/s Transmitter Preset field of the 32.0 GT/s Lane Equalization Control Register Entry with the values received in the eight consecutive 128b/ 130b EQ TS2 Ordered Sets for the corresponding Lane.

For an Upstream Port, if the current data rate of operation is $32.0 \mathrm{GT} / \mathrm{s}, 64.0 \mathrm{GT} / \mathrm{s}$ support is advertised by both ends, and these eight consecutive TS2 Ordered Sets are 128b/130b EQ TS2 Ordered Sets, it must set the start_equalization_w_preset variable to 1b and update the Upstream Port 64.0 GT/s Transmitter Preset field of the 64.0 GT/s Lane Equalization Control Register Entry with the values received in the eight consecutive 128b/ 130b EQ TS2 Ordered Sets for the corresponding Lane.

Any configured Lanes which do not receive EQ TS2 or 128b/130b EQ TS2 Ordered Sets meeting this criteria will use implementation dependent preset values when first operating at $8.0,16.0,32.0$, or $64.0 \mathrm{GT} / \mathrm{s}$ prior to

performing link equalization. A Downstream Port must set the start_equalization_w_preset variable to 1b if any of the following are true:

- the equalization_done_8GT_data_rate variable is 0b
- 16.0 GT/s support is advertised by both ends and the equalization_done_16GT_data_rate variable is 0b
- 32.0 GT/s support is advertised by both ends and the equalization_done_32GT_data_rate variable is 0b
- 64.0 GT/s support is advertised by both ends and the equalization_done_64GT_data_rate variable is 0b
- the Perform Equalization bit in Link Control 3 Register is Set
- an implementation specific mechanism determined that equalization needs to be performed, following procedures described in § Section 4.2.4 .

A Downstream Port must record the 16.0 GT/s, 32.0 GT/s, or 64.0 GT/s Transmitter Preset settings advertised in the eight consecutive TS2 Ordered Sets received if they are 128b/130b EQ TS2 Ordered Sets, and 16.0 GT/s, $32.0 \mathrm{GT} / \mathrm{s}$, or $64.0 \mathrm{GT} / \mathrm{s}$ support is advertised by both ends. The variable successful_speed_negotiation is set to 1b. Note that if the Link is already operating at the highest data rate supported by both Ports, Recovery.Speed is executed but the data rate is not changed. If $128 \mathrm{~b} / 130 \mathrm{~b}$ or $1 \mathrm{~b} / 1 \mathrm{~b}$ encoding is used and the Request Equalization bit is Set in the eight consecutive TS2 Ordered Sets, the Port must handle it as an equalization request as described in § Section 4.2.4 .

- Next state is Recovery. Idle if the following two conditions are both true:
- Eight consecutive TS2 Ordered Sets are received on all configured Lanes with the same Link and Lane number that match what is being transmitted on those same Lanes (see § Section 4.2.7 for more on Matching Link and Lane Numbers for 1b/1b Encoding) with identical data rate identifiers within each Lane and one of the following two sub-conditions are true:
- the speed_change bit is 0 b in the received eight consecutive TS2 Ordered Sets
- current data rate is $2.5 \mathrm{GT} / \mathrm{s}$ and either no $5.0 \mathrm{GT} / \mathrm{s}$, or higher, data rate identifiers are set in the received eight consecutive TS2 Ordered Sets, or no $5.0 \mathrm{GT} / \mathrm{s}$, or higher, data rate identifiers are being transmitted in the TS2 Ordered Sets
- 16 TS2 Ordered Sets are sent after receiving one TS2 Ordered Set without being interrupted by any intervening EIEOS. The changed_speed_recovery variable and the directed_speed_change variable are reset to 0 b on entry to Recovery. Idle.
- In Flit Mode, if the received eight consecutive TS2 Ordered Sets have Hot_Reset_Request, Disable_Link_Request, or Loopback_Request asserted on any configured Lane, the corresponding directed bit must be set.


# IMPLEMENTATION NOTE: 

The above requirement ensures that both the components will immediately exit from Recovery. Idle to the corresponding Hot Reset/Disable/Loopback state without the follower having to send a data stream and waiting till the next scheduled SKP Ordered Set boundary.

- If the N_FTS value was changed, the new value must be used for future L0s states.
- When using 8b/10b encoding, Lane-to-Lane de-skew must be completed before leaving Recovery.RcvrCfg.

- The device must note the data rate identifier advertised on any configured Lane in the eight consecutive TS2 Ordered Sets described in this state transition. This will override any previously recorded value.
- When using 128b/130b or 1b/1b encoding and if the Request Equalization bit is Set in the eight consecutive TS2 Ordered Sets, the device must note it and follow the rules in § Section 4.2.4.
- Next state is Configuration in Non-Flit Mode if eight consecutive TS1 Ordered Sets are received on any configured Lanes with Link or Lane numbers that do not match what is being transmitted on those same Lanes and 16 TS2 Ordered Sets are sent after receiving one TS1 Ordered Set, either 8b/10b or 128b/130b encoding is used, and one of the following two conditions apply:
- the speed_change bit is 0 b on the received TS1 Ordered Sets
- current data rate is $2.5 \mathrm{GT} / \mathrm{s}$ and either no $5.0 \mathrm{GT} / \mathrm{s}$, or higher, data rate identifiers are set in the received eight consecutive TS1 Ordered Sets, or no $5.0 \mathrm{GT} / \mathrm{s}$, or higher, data rate identifiers are being transmitted in the TS2 Ordered Sets

The changed_speed_recovery variable and the directed_speed_change variable are reset to 0b if the LTSSM transitions to Configuration.

- If the N_FTS value was changed, the new value must be used for future L0s states.
- Next state is Configuration in Flit Mode if all the following conditions are true:
- 1 msec has elapsed after receiving one TS1 or TS2 Ordered Set in any configured Lane in this sub-state.
- One of the following conditions is true:
- Eight consecutive TS1 Ordered Sets are received after receiving a TS2 Ordered Set on any configured Lane
- Eight consecutive TS1 Ordered Sets are received with the Link or Lane number set to PAD and no TS2 Ordered Set was received on any configured Lane
- Eight consecutive TS2 Ordered Sets are received with Link number PAD on any configured Lane or a PAD is being transmitted in the TS2 Ordered Sets in any configured Lane (see § Section 4.2.7 for more on Matching Link and Lane Numbers for 1b/1b Encoding)
- At least 16 TS2 Ordered Sets have been transmitted after receiving either of the following:
- One TS1 Ordered Set with Link or Lane number set to PAD
- One TS2 Ordered Set
- The speed_change bit is 0 b on the received TS1 or TS2 Ordered Sets.

The changed_speed_recovery variable and the directed_speed_change variable are reset to 0b if the LTSSM transitions to Configuration.

# IMPLEMENTATION NOTE: 

## REDUCING LINK WIDTH DUE TO ERRORS IN FLIT MODE

With Flit Mode, since there is no upconfig support, the reason to make the transition for Recovery $\rightarrow$ Configuration is to reduce the Link width due to errors. In that case, the Port that wants to reduce the Link width should send PAD in the Link Number field on those Lanes it does not want to be part of the configured Link.

- Next state is Recovery.Speed if the speed of operation has changed to a mutually negotiated data rate since entering Recovery from L0 or L1 (i.e., changed_speed_recovery = 1b) and an EIOS has been detected or an

Electrical Idle condition has been inferred/detected on any of the configured Lanes and no configured Lane received a TS2 Ordered Set since entering this substate (Recovery.RcvrCfg). The new data rate to operate after leaving Recovery.Speed will be reverted back to the speed of operation during entry to Recovery from L0 or L1.

As described in § Section 4.2.5.4, an Electrical Idle condition may be inferred if a TS1 or TS2 Ordered Set has not been received in a time interval specified in § Table 4-48.

- Next state is Recovery.Speed if the speed of operation has not changed to a mutually negotiated data rate since entering Recovery from L0 or L1 (i.e., changed_speed_recovery = 0b) and the current speed of operation is greater than $2.5 \mathrm{GT} / \mathrm{s}$ and an EIOS has been detected or an Electrical Idle condition has been detected/inferred on any of the configured Lanes and no configured Lane received a TS2 Ordered Set since entering this substate (Recovery.RcvrCfg). The new data rate to operate after leaving Recovery.Speed will be $2.5 \mathrm{GT} / \mathrm{s}$ if $8 \mathrm{~b} / 10 \mathrm{~b}$ or $128 \mathrm{~b} / 130 \mathrm{~b}$ encoding is used. The new data rate to operate after leaving Recovery.Speed will be $32.0 \mathrm{GT} / \mathrm{s}$ if $1 \mathrm{~b} /$ 1 b encoding is used.

As described in § Section 4.2.5.4, an Electrical Idle condition may be inferred if a TS1 or TS2 Ordered Set has not been received in a time interval specified in § Table 4-48.

Note: This transition implies that the other side was unable to achieve Symbol lock or Block alignment at the speed with which it was operating. Hence both sides will go back to the $2.5 \mathrm{GT} / \mathrm{s}$ speed of operation and neither device will attempt to change the speed again without exiting Recovery state. It should also be noted that even though a speed change is involved here, the changed_speed_recovery will be 0b.

- After a 48 ms timeout;
- The next state is Detect if the current data rate is $2.5 \mathrm{GT} / \mathrm{s}$ or $5.0 \mathrm{GT} / \mathrm{s}$.
- The next state is Recovery.Idle if the idle_to_rlock_transitioned variable is less than FFh and the current data rate is $8.0 \mathrm{GT} / \mathrm{s}$ or higher.
i. The changed_speed_recovery variable and the directed_speed_change variable are reset to 0 b on entry to Recovery.Idle.
- Else the next state is Detect.


# 4.2.7.4.5 Recovery.Idle 

- Next state is Disabled if directed.
- The clause "if directed" applies to a Downstream or optional crosslink Port that is instructed by a higher Layer to assert Disable_Link_Request in the Training Sets it transmits on the Link.

The clause, "if directed", also applies to an Upstream Port in Flit Mode that transitioned to this state with Disable_Link_Request set in the Training Control field in any configured Lane in the eight consecutive TS2 Ordered Sets that resulted in the transition to this state.

- Next state is Hot Reset if directed.
- The clause "if directed" applies to a Downstream or optional crosslink Port that is instructed by a higher Layer to assert Hot_Reset_Request in the Training Sets it transmits on the Link.

The clause, "if directed", also applies to an Upstream or optional crosslink Port in Flit Mode that transitioned to this state with Hot_Reset_Request asserted in the Training Control field in any configured Lane in the eight consecutive TS2 Ordered Sets that resulted in the transition to this state.

- Next state is Configuration if directed.
- The clause "if directed" applies to a Port that is instructed by a higher Layer to optionally re-configure the Link (i.e., different width Link).

- Next state is Loopback if directed to this state, and the Transmitter is capable of being a Loopback Lead, which is determined by implementation specific means.
- The clause "if directed" applies to a Port that is instructed by a higher Layer to assert Loopback_Request in the Training Sets it transmits on the Link, and the Port becomes the Loopback Lead.
- Next state is Disabled immediately after any configured Lane has Disable_Link_Request asserted in two consecutively received TS1 Ordered Sets.
- This behavior is only applicable to Upstream and optional crosslink Ports in Non-Flit Mode.
- Next state is Hot Reset immediately after any configured Lane has Hot_Reset_Request asserted in two consecutively received TS1 Ordered Sets.
- This behavior is only applicable to Upstream and optional crosslink Ports in Non-Flit Mode.
- Next state is Configuration if two consecutive TS1 Ordered Sets are received on any configured Lane with a Lane number set to PAD. See § Section 4.2.7 for more on Matching Link and Lane Numbers for 1b/1b Encoding.
- Note: A Port that optionally transitions to Configuration to change the Link configuration is guaranteed to send Lane numbers set to PAD on all Lanes.
- Note: It is recommended that in Non-Flit Mode, the LTSSM initiate a Link width up/downsizing using this transition to reduce the time it takes to change the Link width. In Flit Mode, the Recovery.RcvrCfg to Configuration transition should be used.
- Next state is Loopback if one of the following conditions is true:
- The Port is operating in Non-Flit Mode and any configured Lane has Loopback_Request asserted in two consecutive TS1 Ordered Sets.
- The port is operating in Flit Mode and the received eight consecutive TS2 Ordered Sets that resulted in the transition to this state had Loopback_Request asserted in the Training Control field in any configured Lane.
- The device receiving the Ordered Set with Loopback_Request asserted becomes the Loopback Follower.
- When using 8b/10b encoding, the Transmitter sends Idle data Symbols on all configured Lanes in Non-Flit Mode and IDLE Flits across all configured Lanes in Flit Mode.
- When using 128b/130b encoding in Non-Flit Mode:
- If the data rate is $8.0 \mathrm{GT} / \mathrm{s}$, the Transmitter sends one SDS Ordered Set on all configured Lanes to start a Data Stream and then sends Idle data Symbols on all configured Lanes. The first Idle data Symbol transmitted on Lane 0 is the first Symbol of the Data Stream.
- If the data rate is $16.0 \mathrm{GT} / \mathrm{s}$ or higher, the Transmitter sends one Control SKP Ordered Set followed immediately by one SDS Ordered Set on all configured Lanes to start a Data Stream and then sends Idle data Symbols on all configured Lanes. The first Idle data Symbol transmitted on Lane 0 is the first Symbol of the Data Stream.
- If directed to other states, Idle Symbols do not have to be sent, and must not be sent with 128b/130b encoding, before transitioning to the other states (i.e., Disabled, Hot Reset, Configuration, or Loopback)

# IMPLEMENTATION NOTE: EDS USAGE 

In 128b/130b encoding in Non-Flit Mode, on transition to Configuration or Loopback or Hot Reset or Disabled, an EDS must be sent if a Data Stream is active (i.e., an SDS Ordered Set has been sent). It is possible that the side that is not initiating Link Upconfigure has already transmitted SDS and transmitting Data Stream (Logical IDL) when it receives the TS1 Ordered Sets. In that situation, it will send EDS in the set of Lanes that are active before sending the TS1 Ordered Sets in Configuration.

- When using 1b/1b encoding or 128b/130b encoding in Flit Mode:
- Transmitter sends one SDS Ordered Set sequence followed by a Control SKP Ordered Set on all configured Lanes followed by IDLE Flits to start a Data Stream.
- If directed to other states, Idle Flits do not have to be sent, and must not be sent before transitioning to the other states (i.e., Disabled, Hot Reset, Configuration, or Loopback)
- When using 8b/10b encoding in Non-Flit Mode, next state is L0 if eight consecutive Symbol Times of Idle data are received on all configured Lanes and 16 Idle data Symbols are sent after receiving one Idle data Symbol.
- If software has written a 1b to the Retrain Link bit in the Link Control Register since the last transition to L0 from Recovery or Configuration, the Downstream Port must set the Link Bandwidth Management Status bit of the Link Status Register to 1b.
- When using 128b/130b encoding in Non-Flit Mode, next state is L0 if eight consecutive Symbol Times of Idle data are received on all configured Lanes, 16 Idle data Symbols are sent after receiving one Idle data Symbol, and this state was not entered by a timeout from Recovery.RcvrCfg
- The Idle data Symbols must be received in Data Blocks.
- Lane-to-Lane de-skew must be completed before Data Stream processing starts.
- If software has written a 1b to the Retrain Link bit in the Link Control Register since the last transition to L0 from Recovery or Configuration, the Downstream Port must set the Link Bandwidth Management Status bit of the Link Status Register to 1b.
- The idle_to_rlock_transitioned variable is reset to 00 h on transition to L0.
- In Flit Mode, the next state is L0 if two consecutive IDLE Flits are received and the minimum number of IDLE Flits are sent after receiving one IDLE Flit and this state was not entered by a timeout from Recovery.RcvrCfg. The minimum number of IDLE Flits to send is 4 with $8 \mathrm{~b} / 10 \mathrm{~b}$ or $128 \mathrm{~b} / 130 \mathrm{~b}$ encoding and 8 with $1 \mathrm{~b} / 1 \mathrm{~b}$ encoding.
- Lane-to-Lane de-skew must be completed before Data Stream processing starts.
- If software has written a 1b to the Retrain Link bit in the Link Control Register since the last transition to L0 from Recovery or Configuration, the Downstream Port must set the Link Bandwidth Management Status bit of the Link Status Register to 1b.
- The idle_to_rlock_transitioned variable is reset to 00 h on transition to L0
- Otherwise, after a 2 ms timeout:
- If the idle_to_rlock_transitioned variable is less than FFh, the next state is Recovery.RcvrLock.
- If the data rate is $8.0 \mathrm{GT} / \mathrm{s}$ or higher, the idle_to_rlock_transitioned variable is incremented by 1b upon transitioning to Recovery.RcvrLock.
- If the data rate is $5.0 \mathrm{GT} / \mathrm{s}$ (or, if supported in $2.5 \mathrm{GT} / \mathrm{s}$ ), the idle_to_rlock_transitioned variable is set to FFh, upon transitioning to Recovery.RcvrLock.
- Else the next state is Detect

![img-69.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-69.jpeg)

Figure 4-71 Recovery Substate Machine

# 4.2.7.5 LO 

This is the normal operational state. It includes the LOp state, where some Lanes can be in idle state.

- LinkUp = 1b (status is set true).
- On receipt of an STP or SDP Symbol, the idle_to_rlock_transitioned variable is reset to 00 h.
- For an Upstream Port, the directed_speed_change variable must not be set to 1 b if it has never recorded greater than $2.5 \mathrm{GT} / \mathrm{s}$ data rate support advertised in Configuration.Complete or Recovery.RcvrCfg substates by the Downstream Port since exiting the Detect state.
- For a Downstream Port, the directed_speed_change variable must not be set to 1 b if it has never recorded greater than $2.5 \mathrm{GT} / \mathrm{s}$ data rate support advertised in Configuration.Complete or Recovery.RcvrCfg substates by the Upstream Port since exiting the Detect state. If greater than $2.5 \mathrm{GT} / \mathrm{s}$ data rate support has been noted, the Downstream Port must set the directed_speed_change variable to 1b if the Retrain Link bit of the Link Control Register is set to 1b and the Target Link Speed field in the Link Control 2 Register is not equal to the current Link speed.
- A Port supporting greater than $2.5 \mathrm{GT} / \mathrm{s}$ data rates must participate in the speed change even if the Link is not in DL_Active state if it is requested by the other side through the TS Ordered Sets.
- Next state is Recovery if directed to change speed (directed_speed_change variable = 1b) by a higher layer and any of the following three conditions are satisfied:
- both sides support greater than $2.5 \mathrm{GT} / \mathrm{s}$ data rates and the Link is in DL_Active state
- both sides support $8.0 \mathrm{GT} / \mathrm{s}$ or higher data rates, in order to perform Transmitter Equalization at a data rate supported by both sides, in which case the changed_speed_recovery bit is reset to 0 b
- an alternate protocol was selected by the Downstream Port and the current data rate of operation is not an operational data rate in the negotiated alternate protocol
- Next state is Recovery if directed to change Link width.
- The upper layer must not direct a Port to increase the Link width if the other Port did not advertise the capability to upconfigure the Link width during the Configuration state or if the Link is currently operating at the maximum possible width it negotiated on initial entry to the LO state.
- Normally, the upper layer will not reduce width if upconfigure_capable is reset to 0 b other than for reliability reasons, since the Link will not be able to go back to the original width if upconfigure_capable is 0 b . A Port must not initiate reducing the Link width for reasons other than reliability if the Hardware Autonomous Width Disable bit in the Link Control Register is set to 1b.
- The decision to initiate an increase or decrease in the Link width, as allowed by the specification, is implementation specific.

- Next state is Recovery if a TS1 or TS2 Ordered Set is received on any configured Lane or an EIEOS is received on any configured Lane in $128 \mathrm{~b} / 130 \mathrm{~b}$ or $1 \mathrm{~b} / 1 \mathrm{~b}$ encoding.
- Next state is Recovery if directed to this state. If Electrical Idle is detected/inferred on all Lanes without receiving an EIOS on any Lane, the Port may transition to the Recovery state or may remain in L0. In the event that the Port is in L0 and the Electrical Idle condition occurs without receiving an EIOS, errors may occur and the Port may be directed to transition to Recovery.
- As described in § Section 4.2.5.4, an Electrical Idle condition may be inferred on all Lanes under any one of the following conditions: (i) absence of a Flow Control Update DLLP in any $128 \mu \mathrm{~s}$ window, (ii) absence of a SKP Ordered Set in any of the configured Lanes in any $128 \mu \mathrm{~s}$ window, or (iii) absence of a Flow Control Update DLLP, an Optimized_Update_FC, or a SKP Ordered Set in any of the configured Lanes in any $128 \mu \mathrm{~s}$ window.
- The clause "if directed" applies to a Port that is instructed by a higher Layer to transition to Recovery including the Retrain Link bit in the Link Control Register being set.
- The Transmitter may complete any TLP or DLLP in progress.
- Next state is L0s for only the Transmitter if directed to this state and the Transmitter implements L0s. See § Section 4.2.7.6.2 .
- The clause "if directed" applies to a Port that is instructed by a higher Layer to initiate L0s (see § Section 5.4.1.1.1).
- Note: This is a point where the TX and RX may diverge into different LTSSM states.
- Next state is L0s for only the Receiver if an EIOS is received on any Lane, the Receiver implements L0s, and the Port is not directed to L1 or L2 states by any higher layers. See § Section 4.2.7.6.1 .
- Note: This is a point where the TX and RX may diverge into different LTSSM states.
- Next state is Recovery if an EIOS is received on any Lane, the Receiver does not implement L0s, the Port is not directed to L1 or L2 states by any higher layers, and the EIOS is not expected as part of an L0p transition to a lower width. See § Section 4.2.7.6.1 and § Section 4.2.6.7.
- Next state is L1:
i. If directed and
ii. an EIOS is received on any Lane and
iii. an EIOSQ is transmitted on all Lanes.
- The clause "if directed" is defined as both ends of the Link having agreed to enter L1 immediately after the condition of both the receipt and transmission of the EIOS(s) is met. A transition to L1 can be initiated by PCI-PM (see § Section 5.3.2.1) or by ASPM (see § Section 5.4.1.3.1).
- Note: When directed by a higher Layer one side of the Link always initiates and exits to L1 by transmitting the EIOS(s) on all Lanes, followed by a transition to Electrical Idle. ${ }^{92}$ The same Port then waits for the receipt of an EIOS on any Lane, and then immediately transitions to L1. Conversely, the side of the Link that first receives the EIOS(s) on any Lane must send an EIOSQ on all Lanes and immediately transition to L1.
- Next state is L2:
i. If directed and

[^0]
[^0]:    92. The common mode being driven must meet the Absolute Delta Between DC Common Mode During L0 and Electrical Idle ( $\mathrm{V}_{\text {TS-CM-DC-ACTIVE-IDLE-DELTA }}$ ) specification (see § Table 8-7).

ii. an EIOS is received on any Lane
and
iii. an EIOSQ is transmitted on all Lanes.

- The clause "if directed" is defined as both ends of the Link having agreed to enter L2 immediately after the condition of both the receipt and transmission of the EIOS(s) is met (see § Section 5.3.2.3 for more details).
- Note: When directed by a higher Layer, one side of the Link always initiates and exits to L2 by transmitting EIOS on all Lanes followed by a transition to Electrical Idle. ${ }^{93}$ The same Port then waits for the receipt of EIOS on any Lane, and then immediately transitions to L2. Conversely, the side of the Link that first receives an EIOS on any Lane must send an EIOSQ on all Lanes and immediately transition to L2.


# 4.2.7.6 LOs 

The LOs substate machine is shown in § Figure 4-72.

### 4.2.7.6.1 Receiver LOs

A Receiver must implement LOs if its Port advertises support for LOs, as indicated by the ASPM Support field in the Link Capabilities Register. It is permitted for a Receiver to implement LOs even if its Port does not advertise support for LOs.

### 4.2.7.6.1.1 Rx_LOs. Entry

- Next state is Rx_LOs.Idle after a T $_{\text {TX-IDLE-MIN }}$ (§ Table 8-7) timeout.
- Note: This is the minimum time the Transmitter must be in an Electrical Idle condition.


### 4.2.7.6.1.2 Rx_LOs.Idle

- Next state is Rx_LOs.FTS if the Receiver detects an exit from Electrical Idle on any Lane of the configured Link.
- Next state is Rx_LOs.FTS after a 100 ms timeout if the current data rate is $8.0 \mathrm{GT} / \mathrm{s}$ or higher and the Port's Receivers do not meet the $Z_{\text {RX-DC }}$ specification for $2.5 \mathrm{GT} / \mathrm{s}$ (see § Table 8-12). All Ports are permitted to implement the timeout and transition to Rx_LOs.FTS when the data rate is $8.0 \mathrm{GT} / \mathrm{s}$ or higher.


### 4.2.7.6.1.3 Rx_LOs.FTS

- The next state is L0 if a SKP Ordered Set is received in 8b/10b encoding or the SDS Ordered Set is received for 128b/130b encoding on all configured Lanes of the Link.
- The Receiver must be able to accept valid data immediately after the SKP Ordered Set for 8b/10b encoding.

[^0]
[^0]:    93. The common mode being driven does not need to meet the Absolute Delta Between DC Common Mode During L0 and Electrical Idle (V ${ }_{\text {TX-CM-DC-ACTIVE-IDLE-DELTA) }}$ ) specification (see § Table 8-7).

- The Receiver must be able to accept valid data immediately after the SDS Ordered Set for 128b/130b encoding.
- Lane-to-Lane de-skew must be completed before leaving Rx_L0s.FTS.
- Otherwise, next state is Recovery after the N_FTS timeout.
- When using 8b/10b encoding: The N_FTS timeout shall be no shorter than 40*[N_FTS+3]*UI (The 3 * 40 UI is derived from six Symbols to cover a maximum SKP Ordered Set + four Symbols for a possible extra FTS+2 Symbols of design margin), and no longer than twice this amount. When the Extended Synch bit is Set the Receiver N_FTS timeout must be adjusted to no shorter than 40*[2048]*UI (2048 FTSs) and no longer than 40* [4096]*UI (4096 FTSs). Implementations must take into account the worst case Lane to Lane skew, their design margins, as well as the four to eight consecutive EIE Symbols in speeds other than $2.5 \mathrm{GT} / \mathrm{s}$ when choosing the appropriate timeout value within the specification's defined range.
- When using 128b/130b encoding: The N_FTS timeout shall be no shorter than 130*[N_FTS+5+12+Floor(N_FTS/32)]*UI and no longer than twice this amount for $8.0 \mathrm{GT} / \mathrm{s}$ and 16.0 GT/s data rates. For $32.0 \mathrm{GT} / \mathrm{s}$ and above data rates, the N_FTS timeout shall be no shorter than 130*[N_FTS+10+12+2*Floor(N_FTS/32)]*UI and no longer than twice this amount. The 5+Floor(N_FTS/32) accounts for the first EIEOS, the last EIEOS, the SDS, the periodic EIEOS and an additional EIEOS in case an implementation chooses to send two EIEOS followed by an SDS when N_FTS is divisible by 32 for $8.0 \mathrm{GT} / \mathrm{s}$ and $16.0 \mathrm{GT} / \mathrm{s}$ data rates and correspondingly doubled for the $32.0 \mathrm{GT} / \mathrm{s}$ and higher data rates. The 12 is there to account for the number of SKP Ordered Sets that will be transmitted if the Extended Synch bit is Set. When the Extended Synch bit is Set, the timeout should be the same as the normal case with N_FTS equal to 4096.
- The Transmitter must also transition to Recovery, but is permitted to complete any TLP or DLLP in progress.
- It is recommended that the N_FTS field be increased when transitioning to Recovery to prevent future transitions to Recovery from Rx_L0s.FTS.


# 4.2.7.6.2 Transmitter L0s 

A Transmitter must implement L0s if its Port advertises support for L0s, as indicated by the ASPM Support field in the Link Capabilities Register. It is permitted for a Transmitter to implement L0s even if its Port does not advertise support for L0s.

### 4.2.7.6.2.1 Tx_L0s.Entry $\S$

- Transmitter sends an EIOSQ and enters Electrical Idle.
- The DC common mode voltage must be within specification by $T_{\text {TX-IDLE-SET-TO-IDLE- }}{ }^{94}$
- Next state is Tx_L0s.Idle after a $T_{\text {TX-IDLE-MIN }}(\$ \text { Table 8-7) timeout. } \square$


### 4.2.7.6.2.2 Tx_L0s.Idle

- Next state is Tx_L0s.FTS if directed.

[^0]
[^0]:    94. The common mode being driven must meet the Absolute Delta Between DC Common Mode During L0 and Electrical Idle ( $V_{\text {TX-CM-DC-ACTIVE-IDLE-DELTA }}$ ) specification (see § Table 8-7).

# IMPLEMENTATION NOTE: INCREASE OF N_FTS DUE TO TIMEOUT IN RX_LOS.FTS 

The Transmitter sends the N_FTS Fast Training Sequences by going through Tx_L0s.FTS substate to enable the Receiver to reacquire its bit and Symbol lock or Block alignment. In the absence of the N_FTS Fast Training Sequence, the Receiver will timeout in Rx_L0s.FTS substate and may increase the N_FTS number it advertises in the Recovery state.

### 4.2.7.6.2.3 Tx_L0s.FTS

- Transmitter must send N_FTS Fast Training Sequences on all configured Lanes.
- Four to eight EIE Symbols must be sent prior to transmitting the N_FTS (or 4096 if the Extended Synch bit is Set) number of FTS in $5.0 \mathrm{GT} / \mathrm{s}$ data rates. An EIEOSQ must be sent prior to transmitting the N_FTS (or 4096 if the Extended Synch bit is Set) number of FTS with 128b/130b encoding. In $2.5 \mathrm{GT} / \mathrm{s}$ speed, up to one full FTS may be sent before the N_FTS (or 4096 if the Extended Synch bit is Set) number of FTSs are sent.
- SKP Ordered Sets must not be inserted before all FTSs as defined by the agreed upon N_FTS parameter are transmitted.
- If the Extended Synch bit is Set, the Transmitter must send 4096 Fast Training Sequences, inserting SKP Ordered Sets according to the requirements in § Section 4.2.5.6 .
- When using 8b/10b encoding, the Transmitter must send a single SKP Ordered Set on all configured Lanes.
- When using 128b/130b encoding, the Transmitter must send one EIEOSQ followed by one SDS Ordered Set on all configured Lanes. Note: The first Symbol transmitted on Lane 0 after the SDS Ordered Set is the first Symbol of the Data Stream.
- Next state must be L0, after completing the above required transmissions.


## IMPLEMENTATION NOTE: NO SKP ORDERED SET REQUIREMENT WHEN EXITING LOS AT 16.0 GT/S OR HIGHER DATA RATES

Unlike in other LTSSM states, when exiting Tx_L0s.FTS no Control SKP Ordered Set is transmitted before transmitting the SDS. This results in the Data Parity information associated with the last portion of the previous datastream being discarded. Not sending the Control SKP Ordered Set reduces complexity and improves exit latency.

![img-70.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-70.jpeg)

Figure 4-72 L0s Substate Machine

# 4.2.7.7 L1 

The L1 substate machine is shown in $\S$ Figure 4-73.

### 4.2.7.7.1 L1.Entry

- All configured Transmitters are in Electrical Idle.
- The DC common mode voltage must be within specification by $T_{\text {TX-IDLE-SET-TO-IDLE- }}$
- The next state is L1.Idle after a $T_{\text {TX-IDLE-MIN }}$ (\$ Table 8-7) timeout.
- Note: This guarantees that the Transmitter has established the Electrical Idle condition.


### 4.2.7.7.2 L1.Idle

- Transmitter remains in Electrical Idle.

- The DC common mode voltage must be within specification, except as allowed by L1 PM Substates, when applicable. ${ }^{95}$
- A substate of L1 is entered when the conditions for L1 PM Substates are satisfied (see § Section 5.5).
- The L1 PM Substate must be L1.0 when L1.Idle is entered or exited.
- Next state is Recovery if exit from Electrical Idle is detected on any Lane of a configured Link, or directed after remaining in this substate for a minimum of 40 ns in speeds other than $2.5 \mathrm{GT} / \mathrm{s}$.
- Ports are not required to arm the Electrical Idle exit detectors on all Lanes of the Link.
- Note: A minimum stay of 40 ns is required in this substate in speeds other than $2.5 \mathrm{GT} / \mathrm{s}$ to account for the delay in the logic levels to arm the Electrical Idle detection circuitry in case the Link enters L1 and immediately exits the L1 state.
- A Port is allowed to set the directed_speed_change variable to 1b following identical rules described in L0 for setting this variable. When making such a transition, the changed_speed_recovery variable must be reset to 0 b . A Port may also go through Recovery back to L0 and then set the directed_speed_change variable to 1b on the transition from L0 to Recovery.
- A Port is also allowed to enter Recovery from L1 if directed to change the Link width. The Port must follow identical rules for changing the Link width as described in the L0 state.
- Next state is Recovery after a 100 ms timeout if the current data rate is $8.0 \mathrm{GT} / \mathrm{s}$ or higher and the Port's Receivers do not meet the $Z_{R X-D C}$ specification for $2.5 \mathrm{GT} / \mathrm{s}$. All Ports are permitted, but not encouraged, to implement the timeout and transition to Recovery when the data rate is $8.0 \mathrm{GT} / \mathrm{s}$ or higher.
- This timeout is not affected by the L1 PM Substates mechanism.


# IMPLEMENTATION NOTE: 100 MS TIMEOUT IN L1 

Ports that meet the $Z_{R X-D C}$ specification for $2.5 \mathrm{GT} / \mathrm{s}$ while in the L1.Idle state and are therefore not required to implement the 100 ms timeout and transition to Recovery should avoid implementing it, since it will reduce the power savings expected from the L1 state.

![img-71.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-71.jpeg)

Figure 4-73 L1 Substate Machine

# 4.2.7.8 L2 

The L2 substate machine is shown in § Figure 4-74.

### 4.2.7.8.1 L2.Idle

- All Receivers must meet the $\mathrm{Z}_{\text {RX-DC }}$ specification for $2.5 \mathrm{GT} / \mathrm{s}$ within 1 ms (see § Table 8-12).
- All configured Transmitters must remain in Electrical Idle for a minimum time of $\mathrm{T}_{\text {TX-IDLE-MIN }}$.
- The DC common mode voltage does not have to be within specification.
- The Receiver needs to wait a minimum of $\mathrm{T}_{\text {TX-IDLE-MIN }}$ to start looking for Electrical Idle Exit.
- For Downstream Lanes:
- For all Downstream Ports, the next state is Detect if a Beacon is received on at least Lane 0 or if directed.
- Main power must be restored before entering Detect.
- The clause "if directed" is defined as a higher layer decides to exit to Detect.
- For a Switch, if a Beacon is received on at least Lane 0 of any of its Downstream Ports and the Upstream Port is in L2.Idle, the Upstream Port must be directed to L2.TransmitWake.
- For Upstream Lanes:
- The next state is Detect if Electrical Idle Exit is detected on any predetermined set of Lanes.
- The predetermined set of Lanes must include but is not limited to any Lane which has the potential of negotiating to Lane 0 of a Link. For multi-Lane Links the number of Lanes in the predetermined set must be greater than or equal to two.
- A Switch must transition any Downstream Lanes to Detect.
- Next state is L2.TransmitWake for an Upstream Port if directed to transmit a Beacon.

- Note: Beacons may only be transmitted on Upstream Ports in the direction of the Root Complex.


# 4.2.7.8.2 L2.TransmitWake 

This state only applies to Upstream Ports.

- Transmit the Beacon on at least Lane 0.
- Next state is Detect if Electrical Idle exit is detected on any Upstream Port's Receiver that is in the direction of the Root Complex.
- Note: Power is guaranteed to be restored when Upstream Receivers see Electrical Idle exited, but it may also be restored prior to Electrical Idle being exited.


## L2

![img-72.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-72.jpeg)

OM13806A
Figure 4-74 L2 Substate Machine

### 4.2.7.9 Disabled

- It is recommended to Clear LinkUp upon entry to Disabled, without waiting for the EIOSQ to be transmitted or the EIOS to be received.
- All Lanes transmit 16 to 32 TS1 Ordered Sets with Disable_Link_Request asserted and then transition to Electrical Idle.
- An EIOSQ must be sent prior to entering Electrical Idle.
- The DC common mode voltage does not have to be within specification. ${ }^{96}$
- If an EIOSQ was transmitted and an EIOS was received on any Lane (even while transmitting TS1 with Disable_Link_Request asserted), then:
- LinkUp = 0b (False), unless already Cleared, as recommended above.

[^0]
[^0]:    96. The common mode being driven does need to meet the Absolute Delta Between DC Common Mode During L0 and Electrical Idle ( $\mathrm{V}_{\text {TS-CM-DC-ACTIVE-IDLE-DELTA }}$ ) specification (see § Table 8-7).

- At this point, the Lanes are considered Disabled.
- For Upstream Ports: All Receivers must meet the $\mathrm{Z}_{\mathrm{RX}-\mathrm{DC}}$ specification for $2.5 \mathrm{GT} / \mathrm{s}$ within 1 ms (see § Table 8-12).
- For Upstream Ports: The next state is Detect when Electrical Idle exit is detected on at least one Lane.
- For Downstream Ports: The next state is Detect when directed (e.g., when the Link Disable bit is reset to 0b by software).
- For Upstream Ports: If no EIOS is received after a 2 ms timeout, the next state is Detect.


# 4.2.7.10 Loopback 

The Loopback substate machine is shown in § Figure 4-75.

### 4.2.7.10.1 Loopback. Entry

- LinkUp = 0b (False)
- The Link and Lane numbers received in the TS1 or TS2 Ordered Sets are ignored by the Receiver while in this substate.
- Loopback Lead requirements:
- If the Loopback Lead was directed, in an implementation specific manner, to perform a $64.0 \mathrm{GT} / \mathrm{s}$ equalization procedure on one active Lane, to be referred to as the 'Lane under test', before entering Loopback. Entry with LinkUp set to 0b, the perform_equalization_for_loopback_64GT variable must be set to 1 b .
- If Loopback. Entry was entered from Recovery. Equalization and the current data rate is $32.0 \mathrm{GT} / \mathrm{s}$ and perform_equalization_for_loopback_64GT is 1 b and the equalization_done_64GT_data_rate variable is 0 b , determine the highest common data rate of the data rates supported by the Lead and the highest data rates advertised by the Loopback Follower in the TS1s that it transmitted in Phase 1 of Recovery. Equalization on the 'Lane Under Test'. If the highest common data rate is $64.0 \mathrm{GT} / \mathrm{s}$, transmit 16 consecutive TS1 Ordered Sets with Loopback_Request asserted, followed by an EIOSQ, and then transition to Electrical Idle for 1 ms . During the period of Electrical Idle, change the data rate to $64.0 \mathrm{GT} / \mathrm{s}$.

The 16 consecutive TS1 Ordered Sets transmitted on the Lane under test prior to the rate change to $64.0 \mathrm{GT} / \mathrm{s}$ must have the bits listed below as follows:

- The Enhanced Link Behavior Control bits must be set to 01b. The equalization procedure must be performed on the same 'Lane under test' for both equalization procedures.
- The Transmit Modified Compliance Pattern in Loopback bit must be set to 1b if the Loopback Follower is required to transmit the Modified Compliance Pattern on the Lanes that are not under test.
- If Loopback. Entry was entered from Configuration.Linkwidth.Start, the highest common data rate is $64.0 \mathrm{GT} / \mathrm{s}$ when LinkUp = 0b, the Loopback Lead intends to operate at $64.0 \mathrm{GT} / \mathrm{s}$ and the Loopback Lead has prior knowledge that the Loopback Follower also supports $64.0 \mathrm{GT} / \mathrm{s}$. Otherwise, determine the highest common data rate of the data rates supported by the Lead and the data rates received in two consecutive TS1 or TS2 Ordered Sets on any active Lane at the time the transition to Loopback. Entry occurred. If the current data rate is not the highest common data rate:
- Transmit 16 consecutive TS1 Ordered Sets with Loopback_Request asserted, followed by an EIOSQ, and then transition to Electrical Idle for 1 ms . During the period of Electrical Idle, if

the perform_equalization_for_loopback_64GT variable is 1 b and the highest common data rate is $64.0 \mathrm{GT} / \mathrm{s}$, change the data rate to $32.0 \mathrm{GT} / \mathrm{s}$. Otherwise, change the data rate to the highest common data rate.

- If LinkUp is 0b, the Supported Link Speeds field of the Data Rate Identifier must use the Flit Mode data rate encoding if the Flit Mode Supported field in the PCI Express Capabilities Register is 1 b and $64.0 \mathrm{GT} / \mathrm{s}$ is supported and the consecutive TS2 Ordered Sets received on the last transition from Polling.Configuration had the Flit Mode Supported bit set to 1b.
- The Loopback Lead may be directed, in an implementation specific manner, to perform a $32.0 \mathrm{GT} / \mathrm{s}$ equalization procedure on one active Lane, to be referred to as the 'Lane under test', before entering Loopback.Entry. If the highest common data rate is $32.0 \mathrm{GT} / \mathrm{s}$, the equalization_done_32GT_data_rate variable is 0 b , and the equalization procedure is to be executed, the 16 consecutive TS1 Ordered Sets transmitted on the Lane under test prior to the data rate change to the highest common data rate must have the bits listed below as follows:
- The Enhanced Link Behavior Control bits must be set to 01b.
- The Transmit Modified Compliance Pattern in Loopback bit must be set to 1 b if the Loopback Follower is required to transmit the Modified Compliance Pattern on the Lanes that are not under test.


# IMPLEMENTATION NOTE: <br> LANE UNDER TEST USAGE EXPECTATIONS 

The method whereby one active Lane is defined as the 'Lane under test' and is affected by the NEXT/FEXT aggressor Lanes (see § Section 8.5.1.1) so that measurements are performed on the Lane under test (after a speed change and completion of an equalization procedure at a rate of $32.0 \mathrm{GT} / \mathrm{s}$ or above) is defined for system configurations where a test apparatus, such as (but not limited to) a BERT, acts as the Loopback Lead. In such a system configuration, the expectation of this test method is that the Loopback Lead is able to provide the necessary stimulus for the state traversals and protocol negotiations required to establish and exercise the 'Lane under test' without any specific guidance from this specification.

This test mode is only defined for use while LinkUp = 0b (prior to entering Loopback.Entry). The test apparatus must be cognizant of the capabilities of the 'Lane under test'. A mechanism to "re-do" equalization when this test procedure is performed is not defined. The Loopback Lead must only send TS1s with Flit Mode Encoding in Loopback if it received TS2s with the Flit Mode Supported bit set to 1b in Polling.Configuration - these TS2s indicate that the Loopback Follower will properly interpret TS1s with Flit Mode Data Rate Encoding.

- If the highest common data rate is $5.0 \mathrm{GT} / \mathrm{s}$, the follower's transmitter de-emphasis is controlled by setting the Selectable De-emphasis bit of the transmitted TS1 Ordered Sets to the desired value $(1 b=-3.5 \mathrm{~dB}, 0 b=-6 \mathrm{~dB})$.
- For data rates of $5.0 \mathrm{GT} / \mathrm{s}$ and above, the Lead is permitted to choose its own transmitter settings in an implementation specific manner, regardless of the settings it transmitted to the follower.
- Note: If Loopback is entered after LinkUp has been set to 1b, it is possible for one Port to enter Loopback from Recovery and the other to enter Loopback from Configuration. The

Port that entered from Configuration might attempt to change data rate while the other Port does not. If this occurs, the results are undefined. The test set-up must avoid such conflicting directed clauses.

- Transmit TS1 Ordered Sets with Loopback_Request asserted.
- If Loopback.Entry was entered from Recovery.Equalization, the EC field of the transmitted TS1 Ordered Sets must be set to 00b.
- The Lead is also permitted to assert Compliance_Receive_Request of TS1 Ordered Sets transmitted in Loopback.Entry, including those transmitted before a data rate change. If it asserts Compliance_Receive_Request, it must not deassert it again while in the Loopback.Entry state. This usage model might be helpful for test and validation purposes when one or both Ports have difficulty obtaining bit lock, Symbol lock, or Block alignment after a data rate change. The ability to assert Compliance_Receive_Request is implementation specific.
- Next state is Recovery.Equalization if the data rate was changed to 32.0 or 64.0 GT/s and 16 consecutive TS1 Ordered Sets were sent on any Lane with the Enhanced Link Behavior Control bits set to 01b.
- The perform_equalization_for_loopback variable is set to 1b.
- Next state is Loopback.Active after 2 ms if Compliance_Receive_Request of the transmitted TS1 Ordered Sets is asserted.
- Next state is Loopback.Active if Loopback.Entry was entered from Recovery.Equalization and the Lane under test receives two consecutive TS1 Ordered Sets with Loopback_Request asserted.
- Next state is Loopback.Active if Compliance_Receive_Request of the transmitted TS1 Ordered Sets is deasserted and an implementation specific set of Lanes receive two consecutive TS1 Ordered Sets with Loopback_Request asserted.

If the data rate was changed and the equalization procedure was not performed at either $32.0 \mathrm{GT} / \mathrm{s}$ or $64.0 \mathrm{GT} / \mathrm{s}$, the Lead must take into account the amount of time the follower can be in Electrical Idle and transmit a sufficient number of TS1 Ordered Sets for the follower to acquire Symbol lock or Block alignment before proceeding to Loopback.Active. These TS1 Ordered Sets may be used to specify Transmitter settings for the Loopback Follower when the data rate of operation is $8.0 \mathrm{GT} / \mathrm{s}$ or above by setting the value of the EC field appropriately for the follower's Port direction (10b or 11b) and requesting a preset or a set of valid coefficients.

# IMPLEMENTATION NOTE: <br> LANE NUMBERING WITH 128B/130B ENCODING IN LOOPBACK 

If the current data rate uses 128b/130b encoding and Lane numbers have not been negotiated, it is possible that the Lead and follower will not be able to decode received information because their Lanes are using different scrambling LFSR seed values (since the LFSR seed values are determined by the Lane numbers). This situation can be avoided by allowing the Lead and follower to negotiate Lane numbers before directing the Lead to Loopback, directing the Lead to assert Compliance_Receive_Request during Loopback.Entry, or by using some other method of ensuring that the LFSR seed values match.

- Next state is Loopback.Exit after an implementation specific timeout of less than 100 ms.

- Loopback Follower requirements:
- If Loopback.Entry was entered from Configuration.Linkwidth.Start with LinkUp set to 0b, the TS1 Ordered Sets that directed the follower to this state advertised 64.0 GT/s support and had Enhanced Link Behavior Control set to 01b and the follower intends to operate at 64.0 GT/s, perform_equalization_for_loopback_64GT must be set to 1b.
- If Loopback.Entry was entered from Recovery. Equalization and the current data rate is 32.0 GT/s and perform_equalization_for_loopback_64GT is 1b and the equalization_done_64GT_data_rate variable is 0 b , and $64.0 \mathrm{GT} / \mathrm{s}$ is advertised by the Loopback Follower in the TS1s that it transmitted in Phase 1 of Recovery. Equalization on the 'Lane under test':
- Transmit an EIOSQ, and then transition to Electrical Idle for 2 ms . During the period of Electrical Idle, change the data rate to $64.0 \mathrm{GT} / \mathrm{s}$.
- If the Loopback Follower is a Downstream Port, transmit 16 consecutive TS1 Ordered Sets on the 'Lane under test' prior to transmitting the EIOSQ. The TS1 Ordered Sets must have the Equalization Control bits set to 00b.
- Next state is Recovery. Equalization.
- The 'Lane under test', perform_equalization_for_loopback variable, transmit_modified_compliance_pattern_in_loopback variable and the Link and Lane numbers for both the $32.0 \mathrm{GT} / \mathrm{s}$ and $64.0 \mathrm{GT} / \mathrm{s}$ equalization procedures must be the same.
- If Loopback.Entry was entered from Configuration.Linkwidth.Start, determine the highest common data rate of the data rates supported by the follower and the data rates received in the two consecutive TS1 Ordered Sets that directed the follower to this state. If the current data rate is not the highest common data rate:
- Transmit an EIOSQ, and then transition to Electrical Idle for 2 ms . During the period of Electrical Idle, if the perform_equalization_for_loopback_64GT variable is 1b and the highest common data rate is $64.0 \mathrm{GT} / \mathrm{s}$, change the data rate to $32.0 \mathrm{GT} / \mathrm{s}$. Otherwise, change the data rate to the highest common data rate.
- If operating in full swing mode and the highest common data rate is $5.0 \mathrm{GT} / \mathrm{s}$, set the transmitter's de-emphasis to the setting specified by the Selectable De-emphasis bit received in the TS1 Ordered Sets that directed the follower to this state. The de-emphasis is -3.5 dB if the Selectable De-emphasis bit was 1b, and it is -6 dB if the Selectable De-emphasis bit was 0b.
- If the highest common data rate is $8.0 \mathrm{GT} / \mathrm{s}$ or higher and EQ TS1 Ordered Sets directed the follower to this state, set the transmitter to the settings specified by the Preset field of the EQ TS1 Ordered Sets. See § Section 4.2.4.2 . If the highest common data rate is $8.0 \mathrm{GT} / \mathrm{s}$ or higher but standard TS1 Ordered Sets directed the follower to this state, the follower is permitted to use its default transmitter settings.
- Next state is Recovery. Equalization if Loopback.Entry was entered from Configuration.Linkwidth.Start, the highest common data rate is $32.0 \mathrm{GT} / \mathrm{s}$ or higher and the Enhanced Link Behavior Control bits of the TS1 Ordered Sets that directed the follower to this state were 01b.
- The perform_equalization_for_loopback variable is set to 1b.
- The transmit_modified_compliance_pattern_in_loopback variable is set to 1b if the Transmit Modified Compliance Pattern in Loopback bit is Set to 1b in the TS1 Ordered Sets that directed the follower to this state.
- When Recovery. Equalization is entered from Loopback.Entry, the Lane that received two consecutive TS1 Ordered Sets with the Enhanced Link Behavior Control bits set to 01b in Configuration.Linkwidth.Start is the Lane under test for the purposes of Loopback and Recovery. Equalization.

- The Loopback Follower must select a valid Link number in an implementation specific manner. (See § Section 4.2.2.4 for more on assigning Lane numbers and other Scrambler requirements.) The test measurement equipment that facilitates this state transition must ensure, in an implementation specific manner, that it uses a matching Lane number and LFSR seed value.
- Next state is Loopback.Active if Compliance_Receive_Request in the TS1 Ordered Sets that directed the follower to this state was asserted.
- The follower's transmitter does not need to transition to transmitting looped-back data on any boundary, and it is permitted to truncate any Ordered Set in progress.
- Else, the follower transmits TS1 Ordered Sets with Link and Lane numbers set to PAD.
- If Loopback.Entry was entered from Recovery.Equalization:
- The EC field of the transmitted TS1 Ordered Sets must be set to 00b.
- The next state is Loopback.Active after two consecutive TS1 Ordered Sets with Loopback_Request asserted are received by the Lane under test.
- Else, the next state is Loopback.Active if one of the following conditions is true:
- The data rate is $2.5 \mathrm{GT} / \mathrm{s}$ or $5.0 \mathrm{GT} / \mathrm{s}$ and Symbol lock is obtained on all active Lanes.
- The data rate is $8.0 \mathrm{GT} / \mathrm{s}$ or higher and two consecutive TS1 Ordered Sets are received on all active Lanes. The equalization settings specified by the received TS1 Ordered Sets must be evaluated and applied to the transmitter if the value of the EC field is appropriate for the follower's Port direction (10b or 11b) and the requested setting is a preset or a set of valid coefficients. (Note: This is the equivalent behavior for the Recovery. Equalization state.) Optionally, the follower can accept both EC field values. If the settings are applied, they must take effect within 500 ns of being received, and they must not cause the transmitter to violate any electrical specification for more than 1 ns . Unlike Recovery.Equalization, the new settings are not reflected in the TS1 Ordered Sets that the follower transmits.
- When using 8b/10b encoding, the follower's transmitter must transition to transmitting looped-back data on a Symbol boundary, but it is permitted to truncate any Ordered Set in progress. When using 128b/130b or 1b/1b encoding, the follower's transmitter does not need to transition to transmitting looped-back data on any boundary and is permitted to truncate any Ordered Set in progress.


# 4.2.7.10.2 Loopback.Active $\S$ 

- The Loopback Lead must send valid encoded data. The Loopback Lead must not transmit EIOS as data until it wants to exit Loopback. When operating with 128b/130b encoding, Loopback Leads must follow the requirements of $\S$ Section 4.2.2.6.
- When operating with 1b/1b encoding, the Loopback Lead must follow the requirements of $\S$ Section 4.2.3.1, when it starts a Data Stream. The Loopback Lead is permitted to substitute the CRC and FEC bytes with any bytes of its choice. If the Link width has been negotiated by entering LO since leaving the Detect State, that width is to be used; else the width must be assumed to be x 1 .
- A Loopback Follower that entered Loopback from Recovery. Equalization must transmit the Modified Compliance Pattern on all Lanes that detected Receivers in Detect.Active but are not under test if the transmit_modified_compliance_pattern_in_loopback variable is set to 1b, otherwise those Lanes must be

transitioned into Electrical Idle. The Lane under test must follow Loopback Follower rules described below. State transitions must be based only on Link activity on the Lane under test.

- A Loopback Follower is required to retransmit the received encoded information as received, with the polarity inversion determined in Polling applied, while continuing to perform clock tolerance compensation:
- When operating with 1b/1b encoding: The Loopback Follower must track when the Data Stream transition happens and subsequently distinguish an Ordered Set from Data Stream bytes as defined in § Section 4.2.3.1, using the Ordered Set insertion interval of § Table 4-30 as follows:
- If the Link width has been negotiated by entering L0 since leaving the Detect State, that width is to be used; else the width must be assumed to be $x 1$
- For Upstream Lanes, the SRIS mode is determined from the TS1 Ordered Set (Symbol 4, Bit 7) received in the Configuration state whereas for Downstream Lanes it comes from the SRIS Clocking bit in the Link Control Register.
- SKPs must be added or deleted on a per-Lane basis as outlined in § Section 4.2.8 with the exception that SKPs do not have to be simultaneously added or removed across Lanes of a configured Link.
- For 8b/10b encoding, if a SKP Ordered Set retransmission requires adding a SKP Symbol to accommodate timing tolerance correction, the SKP Symbol is inserted in the retransmitted Symbol stream anywhere adjacent to a SKP Symbol in the SKP Ordered Set following the COM Symbol. The inserted SKP Symbol must be of the same disparity as the received SKPs Symbol(s) in the SKP Ordered Set.
- For 8b/10b encoding, if a SKP Ordered Set retransmission requires dropping a SKP Symbol to accommodate timing tolerance correction, the SKP Symbol is simply not retransmitted.
- For 128b/130b encoding, if a SKP Ordered Set retransmission requires adding SKP Symbols to accommodate timing tolerance correction, four SKP Symbols are inserted in the retransmitted Symbol stream prior to the SKP_END Symbol in the SKP Ordered Set.
- For 128b/130b encoding, if a SKP Ordered Set retransmission requires dropping SKP Symbols to accommodate timing tolerance correction, four SKP Symbols prior to the SKP_END Symbol in the SKP Ordered Set are simply not retransmitted.
- For 1b/1b encoding, if a SKP Ordered Set retransmission requires adding SKP Symbols to accommodate timing tolerance correction, eight SKP Symbols are inserted in the retransmitted Symbol stream prior to the SKP_END Symbol in the SKP Ordered Set.
- For 1b/1b encoding, if a SKP Ordered Set retransmission requires dropping SKP Symbols to accommodate timing tolerance correction, eight SKP Symbols prior to the SKP_END Symbol in the SKP Ordered Set are simply not retransmitted.
- No modifications of the received encoded data (except for polarity inversion determined in Polling) are allowed by the Loopback Follower even if it is determined to be an invalid encoding (i.e., no legal translation to a control or data value possible for 8b/10b encoding or invalid Sync Header or invalid Ordered Set for 128b/130b encoding).
- Next state of the Loopback Follower is Loopback.Exit if one of the following conditions apply:
- If directed or if four consecutive EIOSs are received on any Lane. The Requirements for detecting an EIOS are specified in § Section 4.2.5.3.
- Optionally, if current Link speed is $2.5 \mathrm{GT} / \mathrm{s}$ and an EIOS is received or Electrical Idle is detected/ inferred on any Lane.
- Note: As described in § Section 4.2.5.4, an Electrical Idle condition may be inferred if any of the configured Lanes remained electrically idle continuously for $128 \mu \mathrm{~s}$ by not detecting an exit from Electrical Idle in the entire $128 \mu \mathrm{~s}$ window.
- A Loopback Follower must be able to detect an Electrical Idle condition on any Lane within 1 ms of the EIOS being received by the Loopback Follower.

- Note: During the time after an EIOS is received and before Electrical Idle is actually detected by the Loopback Follower, the Loopback Follower may receive a bit stream that is undefined by the encoding scheme, which may be looped back by the transmitter.
- The $\mathrm{T}_{\text {TX-IDLE-SET-TO-IDLE }}$ parameter does not apply in this case since the Loopback Follower may not even detect Electrical Idle until as much as 1 ms after the EIOS.
- The next state of the Loopback Lead is Loopback.Exit if directed.


# 4.2.7.10.3 Loopback.Exit 

- The Loopback Lead sends an EIOS for Ports that support only the $2.5 \mathrm{GT} / \mathrm{s}$ data rate and eight consecutive EIOSs for Ports that support greater than $2.5 \mathrm{GT} / \mathrm{s}$ data rate, and optionally for Ports that only support the $2.5 \mathrm{GT} / \mathrm{s}$ data rate, irrespective of the current Link speed, and enters Electrical Idle on all Lanes for 2 ms .
- The Loopback Lead must transition to a valid Electrical Idle condition ${ }^{97}$ on all Lanes within $\mathrm{T}_{\text {TX-IDLE-SET-TO-IDLE }}$ after sending the last EIOS.
- Note: The EIOS can be useful in signifying the end of transmit and compare operations that occurred by the Loopback Lead. Any data received by the Loopback Lead after any EIOS is received should be ignored since it is undefined.
- The Loopback Follower must enter Electrical Idle on all Lanes for 2 ms .
- Before entering Electrical Idle the Loopback Follower must Loopback all Symbols that were received prior to detecting Electrical Idle. This ensures that the Loopback Lead may see the EIOS to signify the logical end of any Loopback send and compare operations.
- The next state of the Loopback Lead and Loopback Follower is Detect.

![img-73.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-73.jpeg)

Figure 4-75 Loopback Substate Machine

# 4.2.7.11 Hot Reset 

- Lanes that were directed by a higher Layer to initiate Hot Reset:
- All Lanes in the configured Link transmit TS1 Ordered Sets with Hot_Reset_Request asserted and the configured Link and Lane numbers.
- If two consecutive TS1 Ordered Sets are received on any Lane with Hot_Reset_Request asserted and configured Link and Lane numbers, then:
- LinkUp = 0b (False)
- If no higher Layer is directing the Physical Layer to remain in Hot Reset, the next state is Detect
- Otherwise, all Lanes in the configured Link continue to transmit TS1 Ordered Sets with Hot_Reset_Request asserted and the configured Link and Lane numbers.
- Otherwise, after a 2 ms timeout next state is Detect.

- Lanes that were not directed by a higher Layer to initiate Hot Reset (i.e., received two consecutive TS1 Ordered Sets with Hot_Reset_Request asserted on any configured Lanes):
- LinkUp = 0b (False)
- If any Lane of an Upstream Port of a Switch receives two consecutive TS1 Ordered Sets with Hot_Reset_Request asserted, all configured Downstream Ports must transition to Hot Reset as soon as possible.
- Any optional crosslinks on the Switch are an exception to this rule and the behavior is system specific.
- All Lanes in the configured Link transmit TS1 Ordered Sets with Hot_Reset_Request asserted and the configured Link and Lane numbers.
- If two consecutive TS1 Ordered Sets were received with Hot_Reset_Request asserted and the configured Link and Lane numbers, the state continues to be Hot Reset and the 2 ms timer is reset.
- Otherwise, the next state is Detect after a 2 ms timeout.

Generally, Lanes of a Downstream or optional crosslink Port will be directed to Hot Reset, and Lanes of an Upstream or optional crosslink Port will enter Hot Reset by receiving two consecutive TS1 Ordered Sets with Hot_Reset_Request asserted on any configured Lanes, from Recovery. Idle state.

# 4.2.8 Clock Tolerance Compensation 

SKP Ordered Sets (defined in § Section 4.2.8.1, § Section 4.2.8.2, and § Section 4.2.8.3) are used to compensate for differences in frequencies between bit rates at two ends of a Link. The Receiver Physical Layer logical sub-block must include elastic buffering which performs this compensation. The interval between SKP Ordered Set transmissions is derived from the Transmit, Receiver, and Refclk specifications specified in § Table 8-6, § Table 8-12, and § Table 8-19.

The specification supports shared reference clocking architectures (common Refclk) where there is no difference between the Tx and Rx Refclk rates, and two kinds of reference clocking architectures where the Tx and Rx Refclk rates differ. Separate Reference Clocks With No SSC - SRNS, and Separate Reference Clocks with Independent SSC - SRIS. The maximum difference with SRNS is 600 ppm which can result in a clock shift once every 1666 clocks. The maximum difference with SRIS is 5600 ppm which can result in a clock shift every 178 clocks.

Specific form factor specifications are permitted to require the use of only SRIS, only SRNS, or to provide a mechanism for clocking architecture selection. Upstream Ports are permitted to implement support for any combination of SRIS and SRNS (including no support for either), but must conform to the requirements of any associated form factor specification. Downstream Ports supporting SRIS must also support SRNS unless the port is only associated with a specific form factor(s) which modifies these requirements. Port configuration to satisfy the requirements of a specific associated form factor is implementation specific. Specific guidance for form factor specifications is provided in § Section 8.6.8 .

If the Receiver is capable of operating with SKP Ordered Sets being generated at the rate used in SRNS even though the Port is running in SRIS, the Port is permitted to Set its bit for the appropriate data rate in the Lower SKP OS Reception Supported Speeds Vector field of the Link Capabilities 2 Register. If the transmitter is capable of operating with SKP Ordered Sets being generated at the rate used in SRNS even though the Port is running in SRIS, the Port is permitted to Set its bit for the appropriate data rate in the Lower SKP OS Generation Supported Speeds Vector field of the Link Capabilities 2 register. System software must check that the bit is Set in the Lower SKP OS Reception Supported Speeds Vector field before setting the appropriate data rate's bit in the link partner's Enable Lower SKP OS Generation Vector field of the Link Control 3 Register. Any software transparent Extension Devices (such as a repeater) present on a Link must also support lower SKP OS Generation for system software to set the bit in the Enable Lower SKP OS Generation Vector field. Software determination of such support in such extension devices is implementation specific. When the bit for the data rate that the link is running in is Set in the Enable Lower SKP OS Generation Vector field, the transmitter schedules SKP Ordered Set generation

in L0 at the rate used in SRNS, regardless of which clocking architecture the link is running in. In other LTSSM states, SKP Ordered Set scheduling is at the appropriate rate for the clocking architecture.

Components supporting SRIS may need more entries in their elastic buffers than designs supporting SRNS only. This requirement takes into account the extra time it may take to schedule a SKP Ordered Set if the latter falls immediately after a maximum payload sized packet.

# 4.2.8.1 SKP Ordered Set for 8b/10b Encoding 

When using 8b/10b encoding, a transmitted SKP Ordered Set is a COM Symbol followed by three SKP Symbols, except as is allowed for a Loopback Follower in the Loopback.Active LTSSM state. A received SKP Ordered Set is a COM Symbol followed by one to five SKP Symbols. See § Section 4.3.6.7 for Retimer rules on SKP Ordered Set modification.

### 4.2.8.2 SKP Ordered Set for 128b/130b Encoding

When using 128b/130b encoding, a transmitted SKP Ordered Set is 16 Symbols, and a received SKP Ordered Set can be $8,12,16,20$, or 24 Symbols. See § Section 4.3.6.7 for Retimer rules on SKP Ordered Set modification.

There are two SKP Ordered Set formats defined for 128b/130b encoding as shown in § Table 4-62 and § Table 4-63. Both formats contain one to five groups of four SKP Symbols followed by a final group of four Symbols indicated by a SKP_END or SKP_END_CTL Symbol. When operating at 8.0 GT/s in Non-Flit Mode, only the Standard SKP Ordered Set is used. When operating at $16.0 \mathrm{GT} / \mathrm{s}$ or $32.0 \mathrm{GT} / \mathrm{s}$ in Non-Flit Mode, both the Standard and Control SKP Ordered Sets are used. When operating at $8.0,16.0,32.0 \mathrm{GT} / \mathrm{s}$ in Flit Mode, both the Standard SKP Ordered Sets and Control SKP Ordered Sets are used. All statements in this specification that do not refer to a specific SKP Ordered Set format apply to both formats. When a SKP Ordered Set is transmitted, all Lanes must transmit the same format of SKP Ordered Set - all Lanes must transmit the Standard SKP Ordered Set, or all Lanes must transmit the Control SKP Ordered Set.

The Standard SKP Ordered Set contains information following the SKP_END Symbol that is based on the LTSSM state and the sequence of Blocks. When in the Polling.Compliance state, the Symbols contain the Lane's error status information (see § Section 4.2.7.2.2 for more information). Otherwise, the Symbols contain the Lane's scrambling LFSR value, and a Data Parity bit when the SKP Ordered Set follows a Data Block. The Control SKP Ordered Set contains three Data Parity bits and additional information following the SKP_END_CTL Symbol.

When operating at $8.0 \mathrm{GT} / \mathrm{s}$ in Non-Flit Mode, the Data Parity bit of the Standard SKP Ordered Set is the even parity of the payload of all Data Blocks communicated by a Lane and is computed for each Lane independently ${ }^{98}$. Upstream and Downstream Port Transmitters compute the parity as follows:

- Parity is initialized when an SDS Ordered Set is transmitted.
- Parity is updated with each bit of a Data Block's payload after scrambling has been performed.
- The Data Parity bit of a Standard SKP Ordered Set transmitted immediately following a Data Block is set to the current parity.
- Parity is initialized after a Standard SKP Ordered Set is transmitted.

Upstream and Downstream Port Receivers compute and act on the parity as follows:

- Parity is initialized when an SDS Ordered Set is received.
- Parity is updated with each bit of a Data Block's payload before de-scrambling has been performed.
- When a Standard SKP Ordered Set is received immediately following a Data Block, each Lane compares the received Data Parity bit to its calculated parity. If a mismatch is detected, the Receiver must set the bit of the

Port's Lane Error Status register that corresponds to the Lane's default Lane number. The mismatch is not a Receiver Error and must not cause a Link retrain.

- Parity is initialized when a Standard SKP Ordered Set is received.

When operating at a data rate of 16.0 or $32.0 \mathrm{GT} / \mathrm{s}$ in Non-Flit Mode or $8.0,16.0$ or $32.0 \mathrm{GT} / \mathrm{s}$ in Flit Mode, the Data Parity bits of both the Standard SKP Ordered Set in non-Flit-Mode and the Control SKP Ordered Set is the even parity of the payload of all Data Blocks communicated by a Lane and is computed for each Lane independently. Upstream and Downstream Port Transmitters compute the parity as follows:

- Parity is initialized when the LTSSM is in Recovery.Speed.
- Parity is initialized when an SDS Ordered Set is transmitted.
- Parity is updated with each bit of a Data Block's payload after scrambling has been performed.
- Thus, in Flit Mode, Parity is computed post FEC.
- The Data Parity bit of a Standard SKP Ordered Set transmitted immediately following a Data Block is set to the current parity.
- The Data Parity, First Retimer Data Parity, and Second Retimer Data Parity bits of a Control SKP Ordered Set are all set to the current parity.
- Parity is initialized after a Control SKP Ordered Set is transmitted. However, parity is not initialized when a Standard SKP Ordered Set is transmitted.

Upstream and Downstream Port Receivers compute and act on the parity as follows:

- Parity is initialized when the LTSSM is in Recovery.Speed.
- Parity is initialized when an SDS Ordered Set is received.
- Parity is updated with each bit of a Data Block's payload before de-scrambling has been performed.
- Thus, in Flit Mode, Parity is compared prior to FEC decoding.
- When a Control SKP Ordered Set is received, each Lane compares the received Data Parity bit to its calculated parity. It is strongly recommended that this check be performed for Control SKP Ordered Sets immediately following a Data Block only. If a mismatch is detected, the Receiver must set the bit of the Port's 16.0 GT/s Local Data Parity Mismatch Status Register that corresponds to the Lane's default Lane number. The mismatch is not a Receiver Error and must not cause a Link retrain.
- When a Control SKP Ordered Set is received, each Lane compares the received First Retimer Data Parity bit to its calculated parity. It is strongly recommended that this check be performed for Control SKP Ordered Sets immediately following a Data Block only. If a mismatch is detected, the Receiver must set the bit of the Port's 16.0 GT/s First Retimer Data Parity Mismatch Status Register that corresponds to the Lane's default Lane number. The mismatch is not a Receiver Error and must not cause a Link retrain.
- When a Control SKP Ordered Set is received, each Lane compares the received Second Retimer Data Parity bit to its calculated parity. It is strongly recommended that this check be performed for Control SKP Ordered Sets immediately following a Data Block only. If a mismatch is detected, the Receiver must set the bit of the Port's 16.0 GT/s Second Retimer Data Parity Mismatch Status Register that corresponds to the Lane's default Lane number. The mismatch is not a Receiver Error and must not cause a Link retrain.
- When a Standard SKP Ordered Set is received immediately following a Data Block, the Receiver is permitted to compare the received Data Parity bit to its calculated parity bit. However, the results of such a comparison must not affect the state of the Lane Error Status Register.
- Parity is initialized when a Control SKP Ordered Set is received. However, parity is not initialized when a Standard SKP Ordered Set is received.

See § Section 4.3.6.7 for the definition of First Retimer and Second Retimer, and for Retimer Pseudo Port requirements for parity computation and modification of the First Retimer Data Parity and Second Retimer Data Parity bits of Control SKP Ordered Sets.

# IMPLEMENTATION NOTE: LFSR IN STANDARD SKP ORDERED SET 

The LFSR value is transmitted to enable trace tools to be able to function even if they need to reacquire block alignment in the midst of a bit stream. Since trace tools cannot force the link to enter Recovery, they can reacquire bit lock, if needed, and monitor for the SKP Ordered Set to obtain Block alignment and perform Lane-to-Lane de-skew. The LFSR value from the SKP Ordered Set can be loaded into its LFSR to start interpreting the bit stream. It must be noted that with a bit stream one may alias to a SKP Ordered Set on a non-Block boundary. The trace tools can validate their Block alignment by using implementation specific means such as receiving a fixed number of valid packets or Sync Headers or subsequent SKP Ordered Sets.

Table 4-62 Standard SKP Ordered Set with 128b/130b Encoding

| Symbol Number | Value | Description |
| :--: | :--: | :--: |
| 0 through $\left(4^{*} \mathrm{~N}-1\right)$ | AAh for $8.0 \mathrm{GT} / \mathrm{s}$ and $16.0 \mathrm{GT} / \mathrm{s}$ data rates | SKP Symbol. <br> Symbol 0 is the SKP Ordered Set identifier. |
| [N can be <br> 1 through 5] | 99h for $32.0 \mathrm{GT} / \mathrm{s}$ and higher data rates |  |
| $4^{*} \mathrm{~N}$ | E1h | SKP_END Symbol <br> Signifies the end of the SKP Ordered Set after three more Symbols. |
| $4^{*} \mathrm{~N}+1$ | $00-\mathrm{FFh}$ | (i) If LTSSM state is Polling.Compliance: AAh <br> (ii) Else if prior block was a Data Block: <br> $\operatorname{Bit}[7]=$ Data Parity <br> $\operatorname{Bit}[6: 0]=\operatorname{LFSR}[22: 16]$ <br> (iii) Else: <br> $\operatorname{Bit}[7]=-\operatorname{LFSR}[22]$ <br> $\operatorname{Bit}[6: 0]=\operatorname{LFSR}[22: 16]$ |
| $4^{*} \mathrm{~N}+2$ | $00-\mathrm{FFh}$ | (i) If the LTSSM state is Polling.Compliance: Error_Status[7:0] <br> (ii) Else LFSR[15:8] |
| $4^{*} \mathrm{~N}+3$ | $00-\mathrm{FFh}$ | (i) If the LTSSM state is Polling.Compliance: -Error_Status[7:0] <br> (ii) Else: LFSR[7:0] |

The Control SKP Ordered Set is different from the Standard SKP Ordered Set in the last 4 Symbols. It is used to communicate the parity bits, as computed by each Retimer, in addition to the Data Parity bit computed by the Upstream/ Downstream Port. It may also be used for Lane Margining at a Retimer's Receiver, as described below.

Table 4-63 Control SKP Ordered Set with 128b/130b Encoding

| Symbol Number | Value | Description |
| :--: | :--: | :--: |
| 0 through <br> $\left(4^{*} \mathrm{~N}-1\right)$ <br> [N can be <br> 1 through 5] | AAh for 8.0 GT/s and 16.0 GT/s data rates | SKP Symbol. <br> Symbol 0 is the SKP Ordered Set identifier. |
|  | 99h for 32.0 GT/s and higher data rates |  |
| $4^{*}$ N | 78 h | SKP_END_CTL Symbol. <br> Signifies the end of the Control SKP Ordered Set after three more Symbols. |
| $4^{*} \mathrm{~N}+1$ | $00-\mathrm{FFh}$ | Bit 7: Data Parity <br> Bit 6: First Retimer Data Parity <br> Bit 5: Second Retimer Data Parity <br> Bits [4:0]: Margin CRC [4:0] |
| $4^{*} \mathrm{~N}+2$ | $00-\mathrm{FFh}$ | Bit 7: Margin Parity <br> Bits [6:0]: Refer to $\S$ Section 4.2.18.1 |
| $4^{*} \mathrm{~N}+3$ | $00-\mathrm{FFh}$ | Bits [7:0]: Refer to $\S$ Section 4.2.18.1 |

The 'Margin CRC[4:0]' is computed from Bits [6:0] in Symbols 4N+2 (referred to as d[6:0] in the equations below, where $\mathrm{d}[0]$ is Bit 0 of Symbol $4 \mathrm{~N}+2, \mathrm{~d}[1]$ is Bit 1 of Symbol $4 \mathrm{~N}+2, \ldots \mathrm{~d}[6]$ is Bit 6 of Symbol $4 \mathrm{~N}+2$ ) and Bits [7:0] of Symbol $4 \mathrm{~N}+3$ (referred to as d[14:7], where d[7] is Bit 0 of Symbol $4 \mathrm{~N}+3, \mathrm{~d}[8]$ is Bit 1 of Symbol $4 \mathrm{~N}+3, . . \mathrm{d}[14]$ is Bit 7 of Symbol $4 \mathrm{~N}+3$ ) as follows:

$$
\begin{aligned}
& \text { Margin CRC[0] = d[0] ^ { \wedge } \mathrm { d } [ 3] ^ { \wedge } \mathrm { d } [ 5] ^ { \wedge } \mathrm { d } [ 6] ^ { \wedge } \mathrm { d } [ 9] ^ { \wedge } \mathrm { d } [ 1 0] ^ { \wedge } \mathrm { d } [ 1 1] ^ { \wedge } \mathrm { d } [ 1 2] ^ { \wedge } \mathrm { d } [ 1 3] } \\
& \text { Margin CRC[1] = d[1] ^ { \wedge } \mathrm { d } [ 4] ^ { \wedge } \mathrm { d } [ 6] ^ { \wedge } \mathrm { d } [ 7] ^ { \wedge } \mathrm { d } [ 1 0] ^ { \wedge } \mathrm { d } [ 1 1] ^ { \wedge } \mathrm { d } [ 1 2] ^ { \wedge } \mathrm { d } [ 1 3] ^ { \wedge } \mathrm { d } [ 1 4] } \\
& \text { Margin CRC[2] = d[0] ^ { \wedge } \mathrm { d } [ 2] ^ { \wedge } \mathrm { d } [ 3] ^ { \wedge } \mathrm { d } [ 6] ^ { \wedge } \mathrm { d } [ 7] ^ { \wedge } \mathrm { d } [ 8] ^ { \wedge } \mathrm { d } [ 9] ^ { \wedge } \mathrm { d } [ 1 0] ^ { \wedge } \mathrm { d } [ 1 4] } \\
& \text { Margin CRC[3] = d[1] ^ { \wedge } \mathrm { d } [ 3] ^ { \wedge } \mathrm { d } [ 4] ^ { \wedge } \mathrm { d } [ 7] ^ { \wedge } \mathrm { d } [ 8] ^ { \wedge } \mathrm { d } [ 9] ^ { \wedge } \mathrm { d } [ 1 0] ^ { \wedge } \mathrm { d } [ 1 1] } \\
& \text { Margin CRC[4] = d[2] ^ { \wedge } \mathrm { d } [ 4] ^ { \wedge } \mathrm { d } [ 5] ^ { \wedge } \mathrm { d } [ 8] ^ { \wedge } \mathrm { d } [ 9] ^ { \wedge } \mathrm { d } [ 1 0] ^ { \wedge } \mathrm { d } [ 1 1] ^ { \wedge } \mathrm { d } [ 1 2]}
\end{aligned}
$$

'Margin Parity' is the even parity of Bits [4:0] of Symbol 4N+1, Bits [6:0] of Symbol 4N+2, and Bits [7:0] of Symbol 4N+3 (i.e., Margin Parity = Margin CRC[0] ^ Margin CRC[1] ^ Margin CRC[2] ^ Margin CRC[3] ^ Margin CRC[4] ^ d[0] ^ d[1] ^ d[2] ^ $\mathrm{d}[3] \wedge \mathrm{d}[4] \wedge \mathrm{d}[5] \wedge \mathrm{d}[6] \wedge \mathrm{d}[7] \wedge \mathrm{d}[8] \wedge \mathrm{d}[9] \wedge \mathrm{d}[10] \wedge \mathrm{d}[11] \wedge \mathrm{d}[12] \wedge \mathrm{d}[13] \wedge \mathrm{d}[14]}$ ).
'Margin Parity' only applies to 128b/130b encoding. 1b/1b Control SKP Ordered Sets do not contain a 'Margin Parity' field.

The rules for generating and checking the Margin CRC and Margin Parity are described in $\S$ Section 4.2.1.3.

# IMPLEMENTATION NOTE: ERROR PROTECTION IN CONTROL SKP ORDERED SET 

The 21 bits in Symbol 4N+1 (Bits [4:0]), Symbol 4N+2 (Bits[7:0]) and Symbol 4N+3 (Bits[7:0]) is protected by 5 bits of CRC and one bit of parity, leaving 15 bits for information passing. The parity bit provides detection against odd number of bit-flips (e.g., 1-bit, 3-bit), whereas the CRC provides guaranteed detection of 1-bit and 2-bit flips; thus resulting in a triple bit flip detection guarantee over the 21 bits as well as guaranteed detection of burst errors of length 5. The 5-bit CRC is derived from the primitive polynomial: $x^{5}+x^{2}+1$.

Since these 21 bits are not part of a TLP, repeated delivery of the same content provides delivery guarantee. This is achieved through architected registers. Downstream commands are sent from the Downstream Port, reflecting the contents of an architected register whereas the upstream status that passes the error checking is updated into a status register in the Downstream Port. Software thus has a mechanism to issue a command and wait for the status to be reflected back before issuing a new command. Thus, these 15 bits of information act as a micro-packet.

### 4.2.8.3 SKP Ordered Set for 1b/1b Encoding

- Only Control SKP Ordered Sets are transmitted in 1b/1b Encoding.
- A transmitted SKP Ordered Set is 40 symbols (40B), and a received SKP Ordered Set can be 24, 32, 40, 48 or 56 symbols (24B, 32B, 40B, 48B or 56B).
- The transmitted SKP Ordered Set consists of the SKPs (F00F_F00F), followed by a SKP_END (FFF0_00F0), followed by PHY Payload (8B), as shown in § Table 4-64.
- The PHY Payload field of the 1b/1b SKP Ordered Set is illustrated in § Table 4-65, § Figure 4-76, § Figure 4-77, and § Figure 4-78.
- The Payload Type and Parity fields are replicated four times, spaced more than 16 bits apart.
- The Receiver can implement a majority voting to correct these fields if three or more sets match. If two sets of value are 0 b and two sets are 1 b , there is a tie. A tie in the parity can be considered to mismatch. A tie in the Payload Type results in ignoring the PHY payload field.
- The Payload field is replicated twice.
- For Margin payload with its own CRC, the Receiver can choose whichever copy passes CRC (and if both pass CRC, can perform a comparison before acting on it).

The Data Parity bit is the even parity of the payload of all Data Blocks communicated by a Lane and is computed for each Lane independently. Upstream and Downstream Port Transmitters compute the parity as follows:

- Parity is initialized when the LTSSM is in Recovery.Speed.
- Parity is initialized when an SDS Ordered Set is transmitted.
- Parity is initialized after a SKP Ordered Set is transmitted.
- Parity is updated with each bit of a Data Block's payload after scrambling has been performed. Thus, gray coding and precoding, if any, does not affect the Parity calculation and Parity is computed post FEC.
- The Data Parity bit of a SKP Ordered Set transmitted immediately following a Data Block is set to the current parity.

- The Data Parity, First Retimer Data Parity, and Second Retimer Data Parity bits of a SKP Ordered Set are all set to the current parity.

Upstream and Downstream Port Receivers compute and act on the parity as follows:

- Parity is initialized when the LTSSM is in Recovery.Speed.
- Parity is initialized when an SDS Ordered Set is received.
- Parity is updated with each bit of a Data Block's payload before de-scrambling has been performed. Thus, this is performed after gray coding and precoding, if any, by the Receiver and Parity is compared pre FEC.
- When a SKP Ordered Set is received, each Lane compares the received Data Parity bit to its calculated parity. It is strongly recommended that this check be performed for Control SKP Ordered Sets immediately following a Data Block only. If a mismatch is detected, the Receiver must set the bit of the Port's 16.0 GT/s Local Data Parity Mismatch Status Register that corresponds to the Lane's default Lane number. The mismatch is not a Receiver Error and must not cause a Link retrain.
- When a SKP Ordered Set is received, each Lane compares the received First Retimer Data Parity bit to its calculated parity. It is strongly recommended that this check be performed for Control SKP Ordered Sets immediately following a Data Block only. If a mismatch is detected, the Receiver must set the bit of the Port's 16.0 GT/s First Retimer Data Parity Mismatch Status Register that corresponds to the Lane's default Lane number. The mismatch is not a Receiver Error and must not cause a Link retrain.
- When a SKP Ordered Set is received, each Lane compares the received Second Retimer Data Parity bit to its calculated parity. It is strongly recommended that this check be performed for Control SKP Ordered Sets immediately following a Data Block only. If a mismatch is detected, the Receiver must set the bit of the Port's 16.0 GT/s Second Retimer Data Parity Mismatch Status Register that corresponds to the Lane's default Lane number. The mismatch is not a Receiver Error and must not cause a Link retrain.
- Parity is initialized when a SKP Ordered Set is received. See § Section 4.3.6.7 for the definition of First Retimer and Second Retimer, and for Retimer Pseudo Port requirements for parity computation and modification of the First Retimer Data Parity and Second Retimer Data Parity bits of Control SKP Ordered Sets.

Table 4-64 Control SKP Ordered Set with 1b/1b Encoding

| Symbol Number | Value | Description |
| :--: | :--: | :--: |
| $0,4,8,12,16,20$ | F0h | SKP Symbol |
| $1,5,9,13,17,21$ | 0Fh |  |
| $\begin{gathered} 2,6,10,14,18 \\ 22 \end{gathered}$ | F0h |  |
| $\begin{gathered} 3,7,11,15,19 \\ 23 \end{gathered}$ | 0Fh |  |
| 24,28 | FFh | SKP_END |
| 25,29 | F0h |  |
| 26,30 | 00h |  |
| 27,31 | F0h |  |
| 32 | F0h if TSO Ordered Sets are being transmitted, as defined in § Section 4.2.7.4.2, else Phy Payload[7:0] <br> See § Table 4-65, § Figure 4-76, § Figure 4-77, and § Figure 4-78. | PHY Payload |

| Symbol Number | Value | Description |
| :--: | :--: | :--: |
| 33 | F0h if TSO Ordered Sets are being transmitted, as defined in $\S$ Section 4.2.7.4.2, else Phy Payload[15:8] <br> See § Table 4-65, § Figure 4-76, § Figure 4-77, and § Figure 4-78. |  |
| 34 | F0h if TSO Ordered Sets are being transmitted, as defined in $\S$ Section 4.2.7.4.2, else Phy Payload[23:16] <br> See § Table 4-65, § Figure 4-76, § Figure 4-77, and § Figure 4-78. |  |
| 35 | F0h if TSO Ordered Sets are being transmitted, as defined in $\S$ Section 4.2.7.4.2, else Phy Payload[31:24] <br> See § Table 4-65, § Figure 4-76, § Figure 4-77, and § Figure 4-78. |  |
| 36 | F0h if TSO Ordered Sets are being transmitted, as defined in $\S$ Section 4.2.7.4.2, else Phy Payload[39:32] <br> See § Table 4-65, § Figure 4-76, § Figure 4-77, and § Figure 4-78. |  |
| 37 | F0h if TSO Ordered Sets are being transmitted, as defined in $\S$ Section 4.2.7.4.2, else Phy Payload[47:40] <br> See § Table 4-65, § Figure 4-76, § Figure 4-77, and § Figure 4-78. |  |
| 38 | F0h if TSO Ordered Sets are being transmitted, as defined in $\S$ Section 4.2.7.4.2, else Phy Payload[55:48] <br> See § Table 4-65, § Figure 4-76, § Figure 4-77, and § Figure 4-78. |  |
| 39 | F0h if TSO Ordered Sets are being transmitted, as defined in $\S$ Section 4.2.7.4.2, else Phy Payload[63:56] <br> See § Table 4-65, § Figure 4-76, § Figure 4-77, and § Figure 4-78. |  |

![img-74.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-74.jpeg)

Figure 4-76 Margin PHY Payload for Control SKP Ordered Set with 1b/1b Encoding

![img-75.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-75.jpeg)

Figure 4-77 LFSR PHY Payload for Control SKP Ordered Set with 1b/1b Encoding
![img-76.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-76.jpeg)

Figure 4-78 Polling.Compliance PHY Payload for Control SKP Ordered Set with 1b/1b Encoding

Table 4-65 PHY Payload for Control SKP Ordered Set with 1b/1b Encoding

| Field | Bit Position(s) (Replicated Bit Position(s)) | Description |
| :--: | :--: | :--: |
| Phy <br> Payload <br> Type | 0 (20) (40) (60) | If the LTSSM state is Polling.Compliance: <br> this bit is Set to 1b <br> Else: <br> 0b Margin Payload <br> 1b LFSR <br> See $\S$ Section 4.2.8.4 for Phy Payload Type field usage. |
| Port <br> Parity | 1 (21) (41) (61) | If the LTSSM state is Polling.Compliance: <br> this bit is Set to 1b <br> Else: <br> even parity of all the bits in the Data Blocks on that Lane from the last SKP Ordered Set |
| Retimer 1 Parity | 2 (22) (42) (62) | If the LTSSM state is Polling.Compliance: <br> this bit is Set to 1b <br> Else: <br> Port sets this bit with Port Parity; First Retimer, if present, overwrites with its own calculated even parity of all the bits in the Data Blocks on that Lane from the last SKP ordered Set |
| Retimer 2 Parity | 3 (23) (43) (63) | If the LTSSM state is Polling.Compliance: <br> this bit is Set to 1b <br> Else: <br> Port sets this bit with Port Parity; Second Retimer, if present, overwrites with its own calculated even parity of all the bits in the Data Blocks on that Lane from the last SKP Ordered Set |
| Payload [23:0] | $\begin{gathered} \text { \{31:24, 19:4) } \\ \text { (159:44, } \\ 39: 32 \text { ) } \end{gathered}$ | If the LTSSM state is Polling.Compliance: \{ Error_Status[7:0], <br> -Error_Status[7], Error_Status[6], <br> -Error_Status[5], Error_Status[4], <br> -Error_Status[3], Error_Status[2], <br> -Error_Status[1], Error_Status[0], 22h \} <br> Else If PHY Payload Type == 0b Margin: <br> \{ Margin Payload[7:0], Usage Model, <br> Margin Type[2:0], Receiver Number[2:0], <br> Margin CRC[4:0], Reserved[3:0] \} <br> Else: <br> \{Even Parity of LFSR[22:0], LFSR[22:0] \} <br> All of these are in little-endian format. Thus, for example, the 8 bits of Margin Payload occupies bits 31:24 and 59:52 |

# 4.2.8.4 Rules for Transmitters 

- All Lanes shall transmit Symbols at the same frequency (the difference between bit rates is 0 ppm within all multi-Lane Links).
- When transmitted, all Lanes of a multi-Lane Link must simultaneously transmit SKP Ordered Sets of the same length and type (Control or Standard), except as allowed for a Loopback Follower in the Loopback.Active LTSSM State (see $\S$ Section 4.2.5.11 and $\S$ Table 8-7 for the definition of simultaneous in this context).
- The transmitted SKP Ordered Set when using 8b/10b encoding must follow the definition in $\S$ Section 4.2.8.1 .

- The transmitted SKP Ordered Set when using 128b/130b encoding must follow the definition in § Section 4.2.8.2 .
- The transmitted SKP Ordered Set when using 1b/1b-encoding must follow the definition in § Section 4.2.8.3 .
- When using 8b/10b encoding:
- If the Link is not operating in SRIS, or the bit corresponding to the current Link speed is Set in the Enable Lower SKP OS Generation Vector field and the LTSSM is in L0, a SKP Ordered Set must be scheduled for transmission at an interval between 1180 and 1538 Symbol Times.
- If the Link is operating in SRIS and either the bit corresponding to the current Link speed is Clear in the Enable Lower SKP OS Generation Vector field or the LTSSM is not in L0, a SKP Ordered Set must be scheduled for transmission at an interval of less than 154 Symbol Times.
- When using 128b/130b encoding:
- If the Link is not operating in SRIS, or the bit corresponding to the current Link speed is Set in the Enable Lower SKP OS Generation Vector field and the LTSSM is in L0, a SKP Ordered Set must be scheduled for transmission at an interval between 370 and 375 Blocks, in Non-Flit Mode or while not sending Data Stream in Flit Mode. Loopback Followers must meet this requirement until they start looping back the incoming bit stream.
- If the Link is operating in SRIS and either the bit corresponding to the current Link speed is Clear in the Enable Lower SKP OS Generation Vector field or the LTSSM is not in L0, a SKP Ordered Set must be scheduled for transmission at an interval less than 38 Blocks, in Non-Flit Mode or while not sending Data Stream in Flit Mode. Loopback Followers must meet this requirement until they start looping back the incoming bit stream.
- When the LTSSM is in the Loopback state and the Link is not operating in SRIS, the Loopback Lead must schedule two SKP Ordered Sets to be transmitted, at most two Blocks apart from each other, at an interval between 370 to 375 blocks. For $32.0 \mathrm{GT} / \mathrm{s}$, the Loopback Lead is permitted to have an EIEOSQ between the two SKP Ordered Sets.
- When the LTSSM is in the Loopback state and the Link is operating in SRIS, the Loopback Lead must schedule two SKP Ordered Sets to be transmitted, at most two Blocks apart from each other, at an interval of less than 38 Blocks. For $32.0 \mathrm{GT} / \mathrm{s}$, the Loopback Lead is permitted to have an EIEOSQ between the two SKP Ordered Sets.
- SKP Ordered Set transmission rules are specified in § Section 4.2.3.4.2.5 when all the following conditions are true:
- The Link is operating in Flit Mode.
- The LTSSM is not in the Loopback state.
- The transmitter is either transmitting a Data Stream or is transmitting a SKPOS just prior to a Data Stream.
- The Control SKP Ordered Set is transmitted only at the following times:
- In Non-Flit Mode when the data rate is 16.0 or $32.0 \mathrm{GT} / \mathrm{s}$ and in Flit Mode when the data rate is $8.0,16.0$, or $32.0 \mathrm{GT} / \mathrm{s}$ and one of the following conditions is met:
- A Data Stream is being transmitted.

SKP Ordered Sets transmitted within a Data Stream must alternate between the Standard SKP Ordered Set and the Control SKP Ordered Set except for when undergoing an LOp upsize. In LOp when an inactive Lane is transitioning to active the Link must send a Control SKP Ordered Set on all Lanes prior to transmitting the Data Stream on the transitioning Lanes. During an LOp upsize, active lanes are permitted to transmit Control SKP Ordered Sets instead of Standard SKP Ordered Sets to reduce the latency of the that LOp upsize.

- The LTSSM enters the Configuration. Idle state or Recovery. Idle state.

See § Section 4.2.7.3.6 and § Section 4.2.7.4.5 for more information. Transmission of this instance of the Control SKP Ordered Set is not subject to any minimum scheduling interval requirements described above. Transmitters are permitted, but not required, to reset their SKP Ordered Set scheduling interval timer after transmitting this instance of the Control SKP Ordered Set.

- The first SKP Ordered Set is being sent after an LOp upsizing.

A Control SKP Ordered Set must be transmitted on all Lanes - the Lanes that are active and the Lanes that are being activated.

- When using 1b/1b encoding: only Control SKP Ordered Sets are sent. The following rules must be followed, except when transmitting Compliance Modified Compliance patterns:
- If the Link is not operating in SRIS, or the bit corresponding to the current Link speed is Set in the Enable Lower SKP OS Generation Vector field and the LTSSM is in L0, a SKP Ordered Set must be scheduled for transmission at an interval of 740 to 750 Blocks from the prior SKP Ordered Set, while a Data Stream is not in progress. Loopback Followers must meet this requirement until they start looping back the incoming bit stream.
- Behavior is undefined if the Enable Lower SKP OS Generation Vector field setting is changed in FM at a data rate other than $2.5 \mathrm{GT} / \mathrm{s}$.
- If the Link is operating in SRIS and either the bit corresponding to the current Link speed is Clear in the Enable Lower SKP OS Generation Vector field or the LTSSM is not in L0, a SKP Ordered Set must be scheduled for transmission at an interval of less than 76 Blocks, while a Data Stream is not in progress. Loopback Followers must meet this requirement until they start looping back the incoming bit stream.
- When the LTSSM is in the Loopback state and the Link is not operating in SRIS:
- If the Loopback Lead is operating in a Data Stream:
- A single SKP Ordered Set is sent at the interval specified in § Table 4-30.
- If the Loopback Lead is not operating in a Data Stream:
- A single SKP Ordered Set must be sent at an interval of 740 to 750 blocks from the prior SKP Ordered Set.
- Optionally, two back-to-back SKP Ordered Sets are allowed to be scheduled for transmission when operating at $64.0 \mathrm{GT} / \mathrm{s}$.
- When the LTSSM is in the Loopback state and the Link is operating in SRIS:
- If the Loopback Lead is operating in a Data Stream:
- A single SKP Ordered Set is sent at the interval specified in § Table 4-30.
- If the Loopback Lead is not operating in a Data Stream:
- A single SKP Ordered Set must be sent at an interval of less than 76 Blocks.
- Optionally, two back-to-back SKP Ordered Sets are allowed to be scheduled for transmission when operating at $64.0 \mathrm{GT} / \mathrm{s}$.
- During the Data Stream, just prior to transitioning to transmitting the Data Stream, or immediately after terminating the Data Stream, SKP Ordered Set transmission rules must be followed as specified in § Section 4.2.3.1.5 .
- Phy Payload Type must be set as follows:
- If the LTSSM state is Polling.Compliance: 1b.

- Else: For Lane 0, alternate between 0b and 1b in consecutive Control SKP OS, with any starting value after an exit from electrical idle. Any other Lane must send the same value as Lane 0 . Receivers must not depend on this alternation.
- Scheduled SKP Ordered Sets shall be transmitted if a packet or Ordered Set is not already in progress, otherwise they are accumulated and then inserted consecutively at the next packet or Ordered Set boundary. Note: When operating in Flit Mode at 128b/130b encoding and not in the Loopback LTSSM state, or 1b/1b encoding in any LTSSM state, SKP Ordered Sets cannot be transmitted in consecutive Blocks within a Data Stream. See § Section 4.2.3.4.2.5 for more information.
- SKP Ordered Sets do not count as an interruption when monitoring for consecutive Symbols or Ordered Sets (e.g., eight consecutive TS1 Ordered Sets in Polling.Active).
- When using 8b/10b encoding: SKP Ordered Sets must not be transmitted while the Compliance Pattern or the Modified Compliance Pattern (see § Section 4.2.9) is in progress during Polling.Compliance if the Compliance SOS bit of the Link Control 2 register is 0b. If the Compliance SOS bit of the Link Control 2 register is 1b, two consecutive SKP Ordered Sets must be sent (instead of one) for every scheduled SKP Ordered Set time interval while the Compliance Pattern or the Modified Compliance Pattern is in progress when using 8b/10b encoding.
- When using 128b/130b or 1b/1b encoding: The Compliance SOS register bit has no effect. While in Polling.Compliance, Transmitters must not transmit any SKP Ordered Sets other than those specified as part of the Modified Compliance Pattern in § Section 4.2.12.
- Any and all time spent in a state when the Transmitter is electrically idle does not count in the scheduling interval used to schedule the transmission of SKP Ordered Sets.
- It is recommended that any counter(s) or other mechanisms used to schedule SKP Ordered Sets be reset any time when the Transmitter is electrically idle.


# IMPLEMENTATION NOTE: SKP OS IN FLIT MODE 1B/1B ENCODING 

While operating in Flit Mode at 1b/1b encoding, SKP Ordered Sets cannot be sent in consecutive Blocks within a Data Stream because Receivers expect Ordered Sets to be sent only at specific Flit boundaries. See § Table 4-30 for more information.

### 4.2.8.5 Rules for Receivers

- Receivers shall recognize received SKP Ordered Sets as defined in § Section 4.2.8.1 when using 8b/10b encoding, as defined in § Section 4.2.8.2 when using 128b/130b encoding, and as defined in § Section 4.2.8.3 when using the $1 \mathrm{~b} / 1 \mathrm{~b}$ encoding.
- The length of the received SKP Ordered Sets shall not vary from Lane-to-Lane in a multi-Lane Link, except as may occur during Loopback.Active.
- Receivers must be tolerant to receive and process SKP Ordered Sets sent by a transmitter, as defined by the appropriate rules in § Section 4.2.4.1, § Section 4.2.8.1, § Section 4.2.8.2, and § Section 4.2.8.3
- Note: Since Transmitters in electrical idle are not required to reset their mechanism for time-based scheduling of SKP Ordered Sets, Receivers shall be tolerant to receive the first time-scheduled SKP Ordered Set following electrical idle in less than the average time interval between SKP Ordered Sets.
- For 8.0, 16.0, and 32.0 GT/s data rates, in L0 state, Receivers must check that each SKP Ordered Set is preceded by a Data Block with an EDS token.
- Receivers shall be tolerant to receive and process consecutive SKP Ordered Sets in 2.5 GT/s and 5.0 GT/s data rates.

- Receivers shall be tolerant to receive and process SKP Ordered Sets that have a maximum separation dependent on the largest Rx_MPS_Limit a component supports. For $2.5 \mathrm{GT} / \mathrm{s}$ and $5.0 \mathrm{GT} / \mathrm{s}$ data rates, the formula for the maximum number of Symbols ( N ) between SKP Ordered Sets is: $\mathrm{N}=1538+$ Rx_MPS_Limit (in bytes) +28 . For example, if Rx_MPS_Limit is 4096 bytes, $\mathrm{N}=$ $1538+4096+28=5662$.
- When using 1b/1b encoding, each Receiver is permitted to insert or delete 8 Bytes of SKP at an aligned 8 byte boundary. Thus, a received SKP Ordered Set can be $24,32,40,48$ or 56 bytes.


# IMPLEMENTATION NOTE: SKP ORDERED SETS IN A DATA STREAM IN FLIT MODE 

- For 1b/1b, Receivers can predict when SKP OS will occur.
- For 128b/130b, Receivers can predict when SKP OS will occur. This is needed since the EDS Token is not used in Flit Mode.
- For 8b/10b, Receivers need to look for COM SKP. SKP OS will occur at a period specified in § Section 4.2.8.4 .

When upconfiguring Lanes in L0p:

- For 8b/10b, there is no CTL SKP OS but there also is no retimer parity bits that need to be initialized.
- For 128b/130b, the CTL SKP OS is needed to restart the parity computations
- For 1b/1b, CTL SKP OS are always sent to restart the parity computations. Identical values in Phy Payload type are required for simplicity (see § Section 4.2.8.4)


### 4.2.9 Compliance Pattern in 8b/10b Encoding

During Polling, the Polling.Compliance substate must be entered from Polling.Active based on the conditions described in § Section 4.2.7.2.1. The compliance pattern consists of the sequence of 8b/10b Symbols K28.5, D21.5, K28.5, and D10.2 repeating. The Compliance sequence is as follows:

| Symbol | K28.5 | D21.5 | K28.5 | D10.2 |
| :--: | :--: | :--: | :--: | :--: |
| Current Disparity | Negative | Positive | Positive | Negative |
| Pattern | 0011111010 | 1010101010 | 1100000101 | 0101010101 |

The first Compliance sequence Symbol must have negative disparity. It is permitted to create a disparity error to align the running disparity to the negative disparity of the first Compliance sequence Symbol.

For any given device that has multiple Lanes, every eighth Lane is delayed by a total of four Symbols. A two Symbol delay occurs at both the beginning and end of the four Symbol Compliance Pattern sequence. A x1 device, or a xN device operating a Link in x1 mode, is permitted to include the Delay Symbols with the Compliance Pattern.

This delay sequence on every eighth Lane is then:

| Symbol: | D | D | K28.5 | D21.5 | K28.5 | D10.2 | D | D |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- |

Where D is a K28.5 Symbol. The first D Symbol has negative disparity to align the delay disparity with the disparity of the Compliance sequence.

After the eight Symbols are sent, the delay Symbols are advanced to the next Lane, until the delay Symbols have been sent on all eight lanes. Then the delay Symbols cycle back to Lane 0, and the process is repeated. It is permitted to advance the delay sequence across all eight lanes, regardless of the number of lanes detected or supported. An illustration of this process is shown below:

| Lane 0 | D | D | K28.5- | D21.5 | K28.5+ | D10.2 | D | D | K28.5- | D21.5 | K28.5+ | D10.2 |
| :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: |
| Lane 1 | K28.5- | D21.5 | K28.5+ | D10.2 | K28.5- | D21.5 | K28.5+ | D10.2 | D | D | K28.5- | D21.5 |
| Lane 2 | K28.5- | D21.5 | K28.5+ | D10.2 | K28.5- | D21.5 | K28.5+ | D10.2 | K28.5- | D21.5 | K28.5+ | D10.2 |
| Lane 3 | K28.5- | D21.5 | K28.5+ | D10.2 | K28.5- | D21.5 | K28.5+ | D10.2 | K28.5- | D21.5 | K28.5+ | D10.2 |
| Lane 4 | K28.5- | D21.5 | K28.5+ | D10.2 | K28.5- | D21.5 | K28.5+ | D10.2 | K28.5- | D21.5 | K28.5+ | D10.2 |
| Lane 5 | K28.5- | D21.5 | K28.5+ | D10.2 | K28.5- | D21.5 | K28.5+ | D10.2 | K28.5- | D21.5 | K28.5+ | D10.2 |
| Lane 6 | K28.5- | D21.5 | K28.5+ | D10.2 | K28.5- | D21.5 | K28.5+ | D10.2 | K28.5- | D21.5 | K28.5+ | D10.2 |
| Lane 7 | K28.5- | D21.5 | K28.5+ | D10.2 | K28.5- | D21.5 | K28.5+ | D10.2 | K28.5- | D21.5 | K28.5+ | D10.2 |
| Lane 8 | D | D | K28.5- | D21.5 | K28.5+ | D10.2 | D | D | K28.5- | D21.5 | K28.5+ | D10.2 |
| Lane 9 | K28.5- | D21.5 | K28.5+ | D10.2 | K28.5- | D21.5 | K28.5+ | D10.2 | D | D | K28.5- | D21.5 |
| Key: | K28.5- | COM when disparity is negative, specifically: "0011111010" |  |  |  |  |  |  |  |  |  |  |
|  | K28.5+ | COM when disparity is positive, specifically: "1100000101" |  |  |  |  |  |  |  |  |  |  |
|  | D21.5 | Out of phase data Symbol, specifically: "1010101010" |  |  |  |  |  |  |  |  |  |  |
|  | D10.2 | Out of phase data Symbol, specifically: "0101010101" |  |  |  |  |  |  |  |  |  |  |
|  | D | Delay Symbol K28.5 (with appropriate disparity) |  |  |  |  |  |  |  |  |  |  |

This sequence of delays ensures interference between adjacent Lanes, enabling measurement of the compliance pattern under close to worst-case Inter-Symbol Interference and crosstalk conditions.

# 4.2.10 Modified Compliance Pattern in 8b/10b Encoding 

The Modified Compliance Pattern consists of the same basic Compliance Pattern sequence (see § Section 4.2.9 ) with one change. Two identical error status Symbols followed by two K28.5 are appended to the basic Compliance sequence of 8b/10b Symbols (K28.5, D21.5, K28.5, and D10.2) to form the Modified Compliance Sequence of (K28.5, D21.5, K28.5, D10.2, error status Symbol, error status Symbol, K28.5, K28.5). The first Modified Compliance Sequence Symbol must have negative disparity. It is permitted to create a disparity error to align the running disparity to the negative disparity of the first Modified Compliance Sequence Symbol. For any given device that has multiple Lanes, every eighth Lane is moved by a total of eight Symbols. Four Symbols of K28.5 occurs at the beginning and another four Symbols of K28.7 occurs at the end of the eight Symbol Modified Compliance Pattern sequence. The first D Symbol has negative disparity to align the delay disparity with the disparity of the Modified Compliance Sequence. After the 16 Symbols are sent, the delay Symbols are advanced to the next Lane, until the delay Symbols have been sent on all eight lanes. Then the delay Symbols cycle back to Lane 0, and the process is repeated. It is permitted to advance the delay sequence across all eight lanes, regardless of the number of lanes detected or supported. A x1 device, or a xN device operating a Link in x1 mode, is permitted to include the Delay symbols with the Modified Compliance Pattern.

An illustration of the Modified Compliance Pattern is shown in § Table 4-69. Note: This table was "wrapped" to allow it to fit on the page.

Table 4-69 Illustration of Modified Compliance Pattern 5

| Lane0 | D | D | D | D | K28.5- | D21.5 | K28.5+ | D10.2 | ERR | $\rightarrow$ next row |
| :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: |
|  | prev row $\rightarrow$ | ERR | K28.5- | K28.5+ | K28.7- | K28.7- | K28.7- | K28.7- | K28.5- | D21.5 |
| Lane1 | K28.5- | D21.5 | K28.5+ | D10.2 | ERR | ERR | K28.5- | K28.5+ | K28.5- | $\rightarrow$ next row |
|  | prev row $\rightarrow$ | D21.5 | K28.5+ | D10.2 | ERR | ERR | K28.5- | K28.5+ | D | D |
| Lane2 | K28.5- | D21.5 | K28.5+ | D10.2 | ERR | ERR | K28.5- | K28.5+ | K28.5- | $\rightarrow$ next row |
|  | prev row $\rightarrow$ | D21.5 | K28.5+ | D10.2 | ERR | ERR | K28.5- | K28.5+ | K28.5- | D21.5 |
| Lane3 | K28.5- | D21.5 | K28.5+ | D10.2 | ERR | ERR | K28.5- | K28.5+ | K28.5- | $\rightarrow$ next row |
|  | prev row $\rightarrow$ | D21.5 | K28.5+ | D10.2 | ERR | ERR | K28.5- | K28.5+ | K28.5- | D21.5 |
| Lane4 | K28.5- | D21.5 | K28.5+ | D10.2 | ERR | ERR | K28.5- | K28.5+ | K28.5- | $\rightarrow$ next row |
|  | prev row $\rightarrow$ | D21.5 | K28.5+ | D10.2 | ERR | ERR | K28.5- | K28.5+ | K28.5- | D21.5 |
| Lane5 | K28.5- | D21.5 | K28.5+ | D10.2 | ERR | ERR | K28.5- | K28.5+ | K28.5- | $\rightarrow$ next row |
|  | prev row $\rightarrow$ | D21.5 | K28.5+ | D10.2 | ERR | ERR | K28.5- | K28.5+ | K28.5- | D21.5 |
| Lane6 | K28.5- | D21.5 | K28.5+ | D10.2 | ERR | ERR | K28.5- | K28.5+ | K28.5- | $\rightarrow$ next row |
|  | prev row $\rightarrow$ | D21.5 | K28.5+ | D10.2 | ERR | ERR | K28.5- | K28.5+ | K28.5- | D21.5 |
| Lane7 | K28.5- | D21.5 | K28.5+ | D10.2 | ERR | ERR | K28.5- | K28.5+ | K28.5- | $\rightarrow$ next row |
|  | prev row $\rightarrow$ | D21.5 | K28.5+ | D10.2 | ERR | ERR | K28.5- | K28.5+ | K28.5- | D21.5 |
| Lane8 | D | D | D | D | K28.5- | D21.5 | K28.5+ | D10.2 | ERR | $\rightarrow$ next row |
|  | prev row $\rightarrow$ | ERR | K28.5- | K28.5+ | K28.7- | K28.7- | K28.7- | K28.7- | K28.5- | D21.5 |
| Lane9 | K28.5- | D21.5 | K28.5+ | D10.2 | ERR | ERR | K28.5- | K28.5+ | K28.5- | $\rightarrow$ next row |
|  | prev row $\rightarrow$ | D21.5 | K28.5+ | D10.2 | ERR | ERR | K28.5- | K28.5+ | D | D |
| Key: | K28.5- | COM when disparity is negative, specifically: "0011111010" |  |  |  |  |  |  |  |  |
|  | K28.5+ | COM when disparity is positive, specifically: "1100000101" |  |  |  |  |  |  |  |  |
|  | D21.5 | Out of phase data Symbol specifically: "1010101010" |  |  |  |  |  |  |  |  |
|  | D10.2 | Out of phase data Symbol, specifically: "0101010101" |  |  |  |  |  |  |  |  |
|  | D | Delay Symbol K28.5 (with appropriate disparity) |  |  |  |  |  |  |  |  |
|  | ERR | error status Symbol (with appropriate disparity) |  |  |  |  |  |  |  |  |
|  | K28.7- | EIE when disparity is negative, specifically "0011111000" |  |  |  |  |  |  |  |  |
|  | $\rightarrow$ next row prev row $\rightarrow$ | This table was wrapped so it fits on the page. The column after $\rightarrow$ next row is the one following prev row $\rightarrow$ |  |  |  |  |  |  |  |  |

The reason two identical error Symbols are inserted instead of one is to ensure disparity of the $8 \mathrm{~b} / 10 \mathrm{~b}$ sequence is not impacted by the addition of the error status Symbol.

All other Compliance Pattern rules are identical (i.e., the rules for adding delay Symbols) so as to preserve all the crosstalk characteristics of the Compliance Pattern.

The error status Symbol is an 8b/10b data Symbol, maintained on a per-Lane basis, and defined in 8-bit domain in the following way:

- Receiver Error Count (Bits 6:0) - Incremented on every Receiver error after the Pattern Lock bit becomes asserted.
- Pattern Lock (Bit 7) - Asserted when the Lane locks to the incoming Modified Compliance Pattern.


# 4.2.11 Compliance Pattern in 128b/130b Encoding 

The compliance pattern consists of the following repeating sequence of 36 or 37 Blocks:

1. One block with a Sync Header of 01b followed by a 128-bit unscrambled payload of 64 1's followed by 64 0's
2. One block with a Sync Header of 01b followed by a 128-bit unscrambled payload of the following:

|  | Lane No modulo 8 $=0$ | Lane No modulo 8 $=1$ | Lane No modulo 8 $=2$ | Lane No modulo 8 $=3$ | Lane No modulo 8 $=4$ | Lane No modulo 8 $=5$ | Lane No modulo 8 $=6$ | Lane No modulo 8 $=7$ |
| :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: |
| Symbol 0 | 55 h | FFh | FFh | FFh | 55 h | FFh | FFh | FFh |
| Symbol 1 | 55 h | FFh | FFh | FFh | 55 h | FFh | FFh | FFh |
| Symbol 2 | 55 h | 00h | FFh | FFh | 55 h | FFh | FFh | FFh |
| Symbol 3 | 55 h | 00h | FFh | FFh | 55 h | FFh | F0h | F0h |
| Symbol 4 | 55 h | 00h | FFh | C0h | 55 h | FFh | 00h | 00h |
| Symbol 5 | 55 h | 00h | C0h | 00h | 55 h | E0h | 00h | 00h |
| Symbol 6 | 55 h | 00h | 00h | 00h | 55 h | 00h | 00h | 00h |
| Symbol 7 | (P,-P) | (P,-P) | (P,-P) | (P,-P) | (P,-P) | (P,-P) | (P,-P) | (P,-P) |
| Symbol 8 | 00h | 1Eh | 2Dh | 3Ch | 4Bh | 5Ah | 69h | 78h |
| Symbol 9 | 00h | 55h | 00h | 00h | 00h | 55h | 00h | F0h |
| Symbol 10 | 00h | 55h | 00h | 00h | 00h | 55h | 00h | 00h |
| Symbol 11 | 00h | 55h | 00h | 00h | 00h | 55h | 00h | 00h |
| Symbol 12 | 00h | 55h | 0Fh | 0Fh | 00h | 55h | 07h | 00h |
| Symbol 13 | 00h | 55h | FFh | FFh | 00h | 55h | FFh | 00h |
| Symbol 14 | 00h | 55h | FFh | FFh | 7Fh | 55h | FFh | 00h |
| Symbol 15 | 00h | 55h | FFh | FFh | FFh | 55h | FFh | 00h |
| Key: | $\begin{aligned} & \mathbf{P} \\ & \sim \mathbf{P} \end{aligned}$ | Indicates the 4-bit encoding of the Transmitter preset value being used. Indicates the bit-wise inverse of $P$. |  |  |  |  |  |  |

3. One block with a Sync Header of 01b followed by a 128-bit unscrambled payload of the following:

|  | Lane No modulo 8 $=0$ | Lane No modulo 8 $=1$ | Lane No modulo 8 $=2$ | Lane No modulo 8 $=3$ | Lane No modulo 8 $=4$ | Lane No modulo 8 $=5$ | Lane No modulo 8 $=6$ | Lane No modulo 8 $=7$ |
| :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: |
| Symbol 0 | FFh | FFh | 55h | FFh | FFh | FFh | 55h | FFh |
| Symbol 1 | FFh | FFh | 55h | FFh | FFh | FFh | 55h | FFh |
| Symbol 2 | FFh | FFh | 55h | FFh | FFh | FFh | 55h | FFh |
| Symbol 3 | F0h | F0h | 55h | F0h | F0h | F0h | 55h | F0h |
| Symbol 4 | 00h | 00h | 55h | 00h | 00h | 00h | 55h | 00h |
| Symbol 5 | 00h | 00h | 55h | 00h | 00h | 00h | 55h | 00h |
| Symbol 6 | 00h | 00h | 55h | 00h | 00h | 00h | 55h | 00h |
| Symbol 7 | (P,-P) | (P,-P) | (P,-P) | (P,-P) | (P,-P) | (P,-P) | (P,-P) | (P,-P) |
| Symbol 8 | 00h | 1Eh | 2Dh | 3Ch | 4Bh | 5Ah | 69h | 78h |
| Symbol 9 | 00h | 00h | 00h | 55h | 00h | 00h | 00h | 55h |
| Symbol 10 | 00h | 00h | 00h | 55h | 00h | 00h | 00h | 55h |
| Symbol 11 | 00h | 00h | 00h | 55h | 00h | 00h | 00h | 55h |
| Symbol 12 | FFh | 0Fh | 0Fh | 55h | 0Fh | 0Fh | 0Fh | 55h |
| Symbol 13 | FFh | FFh | FFh | 55h | FFh | FFh | FFh | 55h |
| Symbol 14 | FFh | FFh | FFh | 55h | FFh | FFh | FFh | 55h |
| Symbol 15 | FFh | FFh | FFh | 55h | FFh | FFh | FFh | 55h |
| Key: | $\mathbf{P}$ <br> $\mathbf{- P}$ | Indicates the 4-bit encoding of the Transmitter preset being used. <br> Indicates the bit-wise inverse of $P$. |  |  |  |  |  |  |

4. One EIEOSQ
5. 32 Data Blocks, each with a payload of 16 Idle data Symbols (00h) scrambled

# IMPLEMENTATION NOTE: FIRST TWO BLOCKS OF THE COMPLIANCE PATTERN 5 

The first block is a very low frequency pattern to help with measurement of the preset settings. The second block is to notify the Lane number and preset encoding the compliance pattern is using along with ensuring the entire compliance pattern is DC Balanced.

The payload in each Data Block is the output of the scrambler in that Lane (i.e., input data is 0b). The Lane numbers used to determine the scrambling LFSR seed value depend on how Polling.Compliance is entered. (See § Section 4.2.2.4 for more on assigning Lane numbers and other Scrambler requirements.) The Data Blocks of the compliance pattern do not form a Data Stream and hence are exempt from the requirement of transmitting an SDS Ordered Set or EDS Token during Ordered Set Block to Data Block transition and vice-versa.

# IMPLEMENTATION NOTE: <br> ORDERED SETS IN COMPLIANCE AND MODIFIED COMPLIANCE PATTERNS IN 128B/130B ENCODING 

The various Ordered Sets (e.g., EIEOS and SKP OS) follow the Ordered Set definition corresponding to the current Data Rate of operation. For example, at 32.0 GT/s Data Rate, the EIEOS is the 32.0 GT/s EIEOS; at 16.0 GT/s Data Rate, the EIEOS is the 16.0 GT/s EIEOS; whereas at 8.0 GT/s Data Rate, the EIEOS is the 8.0 GT/s EIEOS defined earlier. As defined in $\S$ Section 4.2.8 , the SKP Ordered Set is the Standard SKP Ordered Set.

### 4.2.12 Modified Compliance Pattern in 128b/130b Encoding

The modified compliance pattern, when not operating in SRIS, consists of repeating the following sequence of 65792 or 65793 Blocks:

1. One EIEOSQ
2. 256 Data Blocks, each with a payload of 16 Idle data Symbols (00h), scrambled
3. 255 sets of the following sequence:
i. One SKP Ordered Set
ii. 256 Data Blocks, each with a payload of 16 Idle data Symbols (00h), scrambled

The modified compliance pattern, when operating in SRIS, consists of repeating the following sequence of 67585 or 67586 Blocks:

1. One EIEOSQ
2. 2048 sets of the following sequence:
i. One SKP Ordered Set
ii. 32 Data Blocks, each with a payload of 16 Idle data Symbols (00h), scrambled

The payload in each Data Block is the output of the scrambler in that Lane (i.e., input data is 0b). The Lane numbers used to determine the scrambling LFSR seed value depend on how Polling.Compliance is entered. (See § Section 4.2.2.4 for more on assigning Lane numbers.) The Data Blocks of the modified compliance pattern do not form a Data Stream and hence are exempt from the requirement of transmitting an SDS Ordered Set or EDS Token during Ordered Set Block to Data Block transition and vice-versa.

### 4.2.13 Jitter Measurement Pattern in 128b/130b

The jitter measurement pattern consists of repeating the following Block:

- Sync Header of 01b followed by a 128-bit unscrambled payload of 16 Symbols of 55h

This generates a pattern of alternating 1 s and 0 s for measuring the transmitter's jitter.

# 4.2.14 Compliance Pattern in 1b/1b Encoding 

The Compliance Pattern consists of the following repeating sequence of 137 Blocks. Gray-coding and precoding are not performed during the compliance pattern.

1. One block, unscrambled: 64 Uls of 11b each (voltage level 3 throughout)
2. One block, unscrambled: 64 Uls of 00 b each (voltage level 0 throughout)
3. Two unscrambled blocks of Toggle Pattern (Ch repeated 32 times for each block)
4. Two blocks with an unscrambled payload of the following: This is in hex format starting with the most significant Symbol. For example, in Lane 1, Block 5
(38_DA_CC_C4_E2_3F_1D_35_3B_25_63_CC_B2_CC_FF_FF), Symbol 0 is FFh and Symbol 15 is 38 . Note that these are inserted for establishing DC balance.
Lane 0, 8:
Block 5: FF_FF_FF_FF_FF_FF_FF_FF_FF_FF_FF_FF_FF_FF_FF
Block 6: 5F_26_CC_65_C2_3B_C5_3F_FF_FF_FF_FF_FF_FF_FF_FF_FF

## Lane 1, 9:

Block 5: 38_DA_CC_C4_E2_3F_1D_35_3B_25_63_CC_B2_CC_FF_FF
Block 6: B1_CB_0D_33_C5_D4_EC_32_A2_AC_CC_53_DC_C6_38_B4

## Lane 2, 10:

Block 5: 52_3D_D4_99_EC_0F_3C_4E_56_00_00_00_00_00_00_00
Block 6: A5_2A_69_C3_C9_C3_93_2F_30_CF_1C_C3_37_C0_D0_ED

## Lane 3, 11:

Block 5: E8_00_00_00_00_00_00_00_00_00_00_00_00_00_00_00_00

Block 6: AC_71_6C_3C_CC_93_73_52_8E_6C_DC_0C_E7_C4_E2_D0

## Lane 4, 12:

Block 5: 93_6C_C8_3A_63_93_70_F6_6F_FF_FF_FF_FF_FF_FF_FF
Block 6: 6A_65_DC_1D_A4_DD_28_F1_C3_2E_4F_2C_5C_2D_D6_C2

## Lane 5, 13:

Block 5: 33_C3_9C_6D_60_CF_71_8D_C3_35_D2_8E_3C_6D_0D_DD
Block 6: 5E_C4_8C_ED_6C_4E_53_33_6D_C2_D5_3C_33_28_FC_S3

## Lane 6, 14:

Block 5: 00_00_00_00_00_00_00_00_00_00_00_00_00_00_00_00

Block 6: 63_6B_31_37_20_00_00_00_00_00_00_00_00_00_00_00

## Lane 7, 15:

Block 5: D9_C3_33_CC_A0_D3_DC_FF_FF_FF_FF_FF_FF_FF_FF_FF
Block 6: 5D_2D_CD_0E_C3_23_E1_F0_8F_1D_32_8E_B3_31_39_C2
5. One EIEOSQ (unscrambled) - this resets the scrambler
6. 64 Blocks, each comprising of 16 Symbols of 00 h scrambled.
7. One block, unscrambled: 64 Uls of 10b each (voltage level 2 throughout). The scrambler does not advance.
8. One block, unscrambled: 64 Uls of 01 b each (voltage level 1 throughout). The scrambler does not advance.
9. 64 Blocks, each comprising of 16 Symbols of 00 h scrambled.

The payload in each scrambled Block is the output of the scrambler in that Lane (i.e., input data is 0b). The Lane numbers used to determine the scrambling LFSR seed value depend on how Polling.Compliance is entered. (See § Section 4.2.2.4 for more on assigning Lane numbers and other Scrambler requirements.) The scrambled Blocks of the compliance pattern do not form a Data Stream and hence are exempt from the requirement of transmitting an SDS Ordered Set or the FEC / CRC / Flit formation requirements.

# 4.2.15 Modified Compliance Pattern in 1b/1b Encoding 

The modified compliance pattern, when not operating in SRIS, consists of repeating the following sequence of 65792 Blocks:

1. One EIEOSQ (that resets the scrambler)
2. 256 Blocks, each comprising of 16 Symbols of 00h scrambled
3. 255 sets of the following sequence:
a. One SKP Ordered Set
b. 256 Data Blocks, each comprising of 16 Symbols of 00h scrambled

The modified compliance pattern, when operating in SRIS, consists of repeating the following sequence of 67585 Blocks:

1. One EIEOSQ (that resets the scrambler)
2. 2048 sets of the following sequence:
a. One SKP Ordered Set
b. 32 Blocks, each comprising of 16 Symbols of 00h scrambled

The payload in each scrambled Block is the output of the scrambler in that Lane (i.e., input data is 0b), which are then gray-coded, and precoded, if performed, as shown in § Figure 4-22. The Lane numbers used to determine the scrambling LFSR seed value depend on how Polling.Compliance is entered. (See § Section 4.2.2.4 for more on assigning Lane numbers.) The scrambled Blocks of the modified compliance pattern do not form a Data Stream and hence are exempt from the requirement of transmitting an SDS Ordered Set or the FEC / CRC / Flit formation requirements.

### 4.2.16 Jitter Measurement Pattern in 1b/1b Encoding

The jitter measurement pattern consists of repeating the following 52 UI, consisting of the following 4 sets of 13 UI each:

```
{ 00b, 01b, 00b, 11b, 00b, 10b, 01b, 10b, 11b, 01b, 11b, 10b, 10b,
    00b, 01b, 00b, 11b, 00b, 10b, 01b, 10b, 11b, 01b, 11b, 10b, 00b,
    00b, 01b, 00b, 11b, 00b, 10b, 01b, 10b, 11b, 01b, 11b, 11b, 10b,
    00b, 01b, 00b, 11b, 00b, 10b, 01b, 10b, 11b, 01b, 01b, 11b, 10b }
```

# IMPLEMENTATION NOTE: JITTER PATTERN RATIONALE 

The base pattern used above for voltage levels is: $\{0,1,0,3,0,2,1,2,3,1,3,2\}$. This pattern, when repeated, covers all 12 voltage level transitions while being fully DC balanced and using the minimum number of UI.

However, for implementations that use interleaved bit steams, this 12 UI base pattern may not test all the circuits during all the transitions. To address this, a 13th UI is introduced to ensure coverage even with interleaved bitstreams ( 13 is a prime number). This insertion is done by keeping the same set of transitions and cycling across the 4 sets of values over 52 UI , as shown above. Thus:

- Voltage level 2 (10b) is repeated in the 12th and 13th UI of the first row;
- voltage level $0(00 b)$ is repeated in the 13th UI of the second row and the 1st UI of the third row;
- voltage level 3 (11b) is repeated in the 11th and 12th UI of the third row; and
- voltage level 1 (01b) is repeated in the 10th and 11th UI of the last row.

Across these 52 UI, DC balance is maintained and the DC imbalance between the rows has been minimized by the choice of the sequence of the repeated voltage level.

### 4.2.17 Toggle Patterns in 1b/1b encoding

Two types of Toggle Patterns are defined for the best single edge jitter measurement accuracy:

## High Swing Toggle Pattern

This comprises of alternating UIs between 00b and 11b (i.e., back to back symbols of 33h unscrambled, effectively alternating between voltage levels 0 and 3 in successive UIs).

## Low Swing Toggle Pattern

This comprises of alternating UIs between 01b and 10b (i.e., back to back symbols of 66h unscrambled, effectively alternating between voltage levels 1 and 2 in successive UIs).

### 4.2.18 Lane Margining at Receiver

Lane Margining at Receiver, as defined in this section, is mandatory for all Ports supporting a data rate of $16.0 \mathrm{GT} / \mathrm{s}$ or higher, including Pseudo Ports (Retimers). Lane Margining at Receiver enables system software to obtain the margin information of a given Receiver while the Link is in the L0 state. The margin information includes both voltage and time, in either direction from the current Receiver position. For all Ports that implement Lane Margining at Receiver, Lane Margining at Receiver for timing is required, while support of Lane Margining at Receiver for voltage is optional at $16.0 \mathrm{GT} / \mathrm{s}$ and required at $32.0 \mathrm{GT} / \mathrm{s}$ and higher data rates.

Lane Margining at Receiver begins when a Margin Command is received, the Link is operating at $16.0 \mathrm{GT} / \mathrm{s}$ Data Rate or higher, and the Link is in L0 state. Lane Margining at Receiver ends when either a Go to Normal Settings command is received, the Link changes speed, or the Link exits either the L0 or Recovery states. Lane Margining at Receiver optionally ends when certain error thresholds are exceeded. Lane Margining at Receiver is permitted to be suspended while the Link is in Recovery for independent samplers.

Lane Margining at Receiver is not supported by Links operating at $2.5 \mathrm{GT} / \mathrm{s}, 5.0 \mathrm{GT} / \mathrm{s}$, or $8.0 \mathrm{GT} / \mathrm{s}$.

Software uses the per-Lane Margining Lane Control Register and Margining Lane Status Register in each Port (Downstream or Upstream) for sending Margin Commands and obtaining margin status information for the corresponding Receiver associated with the Port. For the Retimers, the commands to get information about the Receiver's capabilities and status and the commands to margin the Receiver are conveyed in the Control SKP Ordered Sets in the Downstream direction. The status and error reporting of the target Retimer Receiver is conveyed in the Control SKP Ordered Sets in the Upstream direction. Software controls margining in the Receiver of a Retimer by writing to the appropriate bits in the Margining Lane Control Register in the Downstream Port. The Downstream Port also updates the status information conveyed by the Retimer(s) in the Link through the Control SKP Ordered Set into its Margining Lane Status Register.

# 4.2.18.1 Receiver Number, Margin Type, Usage Model, and Margin Payload Fields 

The contents of the four command fields of the Margining Lane Control Register in the Downstream Port are always reflected in the identical fields in the Downstream Control SKP Ordered Sets. The contents of the Upstream Control SKP Ordered Set received in the Downstream Port is always reflected in the corresponding status fields of the Margining Lane Status Register in the Downstream Port. The following table provides the bit placement of these fields in the Control SKP Ordered Set.

Table 4-72 Margin Command Related Fields in the Control SKP Ordered Set

| Symbol | Description |  |
| :--: | :--: | :--: |
|  | Usage Model = 0b | Usage Model = 1b |
| $4^{*} \mathrm{~N}+2$ | Bit 7: Margin Parity (see § Table 4-63) | Reserved |
|  | Bit 6: Usage Model = 0b: Lane Margining at Receiver |  |
|  | Bits [5:3]: Margin Type |  |
|  | Bits [2:0]: Receiver Number |  |
| $4^{*} \mathrm{~N}+3$ | Bits [7:0]: Margin Payload | Reserved |

Usage Model: An encoding of 0 b indicates that the usage model is Lane Margining at Receiver. An encoding of 1 b in this field is reserved for future usages.

If the Usage Model field is 1b, Bits [5:0] of Symbol 4N+2 and Bits [7:0] of Symbol 4N+3 are Reserved.
When evaluating received Control SKP Ordered Set for Margin Commands, all Receivers that do not comprehend the usage associated with Usage Model = 1b are required to ignore Bits[5:0] of Symbol 4N+2 and Bits[7:0] of Symbol 4N+3 of the Control SKP Ordered Set, if the Usage Model field is 1b.

## IMPLEMENTATION NOTE: POTENTIAL FUTURE USAGE OF CONTROL SKP ORDERED SET

The intended usage for the 15 bits of information in the Control SKP Ordered Set, as defined in § Table 4-72 is Lane Margining at Receiver. However a single bit (Bit 6 of Symbol 4N+2) is Reserved for any future usage beyond Lane Margining at Receiver. If such a usage is defined in the future, this bit will be set to 1 b and the remaining 14 bits can be defined as needed by the new usage model. Alternatively, Symbol 4 N could use a different encoding than 78 h for any future usage, permitting all bits in Symbols $4 \mathrm{~N}+1,4 \mathrm{~N}+2$, and $4 \mathrm{~N}+3$ to be defined for that usage model.

Receiver Number: Receivers are identified in § Figure 4-79. The following Receiver Number encodings are used in the Downstream Port for Margin Commands targeting that Downstream Port or a Retimer below that Downstream Port:

000b
Broadcast (Downstream Port Receiver and all Retimer Pseudo Port Receivers)
001b
Rx(A) (Downstream Port Receiver)
010b
Rx(B) (Retimer X or Z Upstream Pseudo Port Receiver)
011b
Rx(C) (Retimer X or Z Downstream Pseudo Port Receiver)
100b
Rx(D) (Retimer Y Upstream Pseudo Port Receiver)
101b
Rx(E) (Retimer Y Downstream Pseudo Port Receiver)
110b
Reserved
111b
Reserved
The following Receiver Number encodings are used in the Upstream Port for Margin Commands targeting that Upstream Port:

000b Broadcast (Upstream Port Receiver)
001b Reserved
010b Reserved
011b Reserved
100b Reserved
101b Reserved
110b Rx (F) (Upstream Port Receiver)
111b Reserved

![img-77.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-77.jpeg)
(Various System Topologies with or without Retimers)
Figure 4-79 Receiver Number Assignment

Margin Type and Margin Payload: The Margin Type field together with a valid Receiver Number(s), associated with the Margin Type encoding, and specific Margin Payload field define various commands used for margining (referred to as Margin Command). \$ Table 4-73 defines the encodings of valid Margin Commands along with the corresponding responses, used in both the Control SKP Ordered Sets as well as the Margining Lane Control Register and Margining Lane Status Register. Margin commands that are always broadcast will use the broadcast encoding for the Receiver Number, even when only one Receiver is the target (e.g., USP or a DSP in a Link with no Retimers). The Receiver Number field in the response to a Margin Command other than No Command reflects the number of the Receiver that is responding, even for a Margin Command that is broadcast. The Margin Commands go Downstream whereas the responses go Upstream in the Control SKP Ordered Sets. The responses reflect the Margin Type to which the target Receiver is responding. The Receiver Number field of the response corresponds to the target Receiver that is responding. All unused encodings in $\S$ Table 4-73 are Reserved and must not be considered to be a valid Margin Command.

The parameters used here (e.g., $\mathrm{M}_{\text {SampleCount }}$ ) are defined in $\S$ Section 8.4.4. Each data rate has an independent set of parameters and the values in $\S$ Table 4-73 reflect the current data rate. Any relationship between values for different data rates is implementation specific. For example, the timing/voltage step sizes might differ between $64.0 \mathrm{GT} / \mathrm{s}$ in PAM-4 mode and $16.0 \mathrm{GT} / \mathrm{s}$ or $32.0 \mathrm{GT} / \mathrm{s}$ in NRZ mode; $N$ voltage steps at $64.0 \mathrm{GT} / \mathrm{s}$ is likely to be a different eye height from $N$ voltage steps at $16.0 \mathrm{GT} / \mathrm{s}$ or $32.0 \mathrm{GT} / \mathrm{s}$.

In PAM-4 mode, the Step Margin commands apply to all 3 eyes simultaneously.

Table 4-73 Margin Commands and Corresponding Responses

| Command |  |  |  | Response |  |
| :--: | :--: | :--: | :--: | :--: | :--: |
| Margin Command | Margin <br> Type[2:0] | Valid <br> Receiver <br> Number(s) | Margin <br> Payload[7:0] | Margin <br> Type[2:0] | Margin Payload[7:0] |
| No Command | 111b | 000b | 9Ch <br> (No Command is also an independent command in Upstream direction. The expected Response is No Command with the Receiver Number = 000b.) |  |  |
| Access Retimer Register | 001b | $\begin{gathered} 010 \mathrm{~b}, \\ 100 \mathrm{~b} \end{gathered}$ | Register offset in bytes: <br> 00h - 87h, <br> A0h - FFh | 001b | Register value, if supported. It is recommended that the Target Receiver on Retimer return 00h if it does not support accessing its registers. It is permitted that the Retimer not respond. |
| Report Margin Control Capabilities | 001b | $\begin{gathered} 001 \mathrm{~b} \\ \text { through } \\ 110 \mathrm{~b} \end{gathered}$ | 88h | 001b | Margin Payload[7:5] = Reserved; <br> Margin Payload[4:0] = $\left\{\mathrm{M}_{\text {IndErrorSampler }}\right.$, <br> M $\text { M}_{\text {SampleReportingMethod }}$, M IndLeftRightTiming, <br> M IndUpDownVoltage, M VoltageSupported\} |
| Report <br> $\boldsymbol{M}_{\text {NumVoltageSteps }}$ | 001b | $\begin{gathered} 001 \mathrm{~b} \\ \text { through } \\ 110 \mathrm{~b} \end{gathered}$ | 89h | 001b | Margin Payload[7] = Reserved <br> Margin Payload[6:0] = M $\text { M }_{\text {NumVoltageSteps }}$ |
| Report <br> $\boldsymbol{M}_{\text {NumTimingSteps }}$ | 001b | $\begin{gathered} 001 \mathrm{~b} \\ \text { through } \\ 110 \mathrm{~b} \end{gathered}$ | 8Ah | 001b | Margin Payload[7:6] = Reserved <br> Margin Payload[5:0] = M $\text { M }_{\text {NumTimingSteps }}$ |
| Report <br> $\boldsymbol{M}_{\text {MaxTimingOffset }}$ | 001b | $\begin{gathered} 001 \mathrm{~b} \\ \text { through } \\ 110 \mathrm{~b} \end{gathered}$ | 8Bh | 001b | Margin Payload[7] = Reserved <br> Margin Payload[6:0] = M $\text { M }_{\text {MaxTimingOffset }}$ |
| Report <br> $\boldsymbol{M}_{\text {MaxVoltageOffset }}$ | 001b | $\begin{gathered} 001 \mathrm{~b} \\ \text { through } \\ 110 \mathrm{~b} \end{gathered}$ | 8Ch | 001b | Margin Payload[7] = Reserved <br> Margin Payload[6:0] = M $\text { M }_{\text {MaxVoltageOffset }}$ |
| Report <br> $\boldsymbol{M}_{\text {SamplingRateVoltage }}$ | 001b | $\begin{gathered} 001 \mathrm{~b} \\ \text { through } \\ 110 \mathrm{~b} \end{gathered}$ | 8Dh | 001b | Margin Payload[7:6] = Reserved <br> Margin Payload[5:0] = $\left\{\mathrm{M}_{\text {SamplingRateVoltage }}[5: 0]\right\}$ |
| Report <br> $\boldsymbol{M}_{\text {SamplingRateTiming }}$ | 001b | $\begin{gathered} 001 \mathrm{~b} \\ \text { through } \\ 110 \mathrm{~b} \end{gathered}$ | 8Eh | 001b | Margin Payload[7:6] = Reserved <br> Margin Payload[5:0] = $\left\{\mathrm{M}_{\text {SamplingRateTiming }}[5: 0]\right\}$ |

| Command |  |  |  | Response |  |
| :--: | :--: | :--: | :--: | :--: | :--: |
| Margin Command | Margin <br> Type[2:0] | Valid <br> Receiver <br> Number(s) | Margin <br> Payload[7:0] | Margin <br> Type[2:0] | Margin Payload[7:0] |
| Report <br> $\boldsymbol{M}_{\text {SampleCount }}$ | 001b | 001b <br> through <br> 110b | 8Fh | 001b | Margin Payload[7] = Reserved <br> Margin Payload[6:0] = M $_{\text {SampleCount }}$ |
| Report $\boldsymbol{M}_{\text {MaxLanes }}$ | 001b | 001b <br> through <br> 110b | 90h | 001b | Margin Payload[7:5] = Reserved <br> Margin Payload[4:0] = M $_{\text {MaxLanes }}$ |
| Report Reserved | 001b | 001b <br> through <br> 110b | 91-9Fh | 001b | Margin Payload[7:0] = Reserved |
| Set Error Count Limit | 010b | 001b <br> through <br> 110b | Margin <br> Payload[7:6] <br> $=11 b$ <br> Margin <br> Payload[5:0] <br> $=$ Error <br> Count Limit | 010b | Margin Payload[7:6] = 11b <br> Margin Payload[5:0] = Error Count Limit registered by the target Receiver |
| Go to Normal Settings | 010b | 000b <br> through <br> 110b | 0Fh | 010b | 0Fh |
| Clear Error Log | 010b | 000b <br> through <br> 110b | 55h | 010b | 55h |
| Step Margin to timing offset to right/left of default | 011b | 001b <br> through <br> 110b | See <br> $\S$ Section <br> 4.2.18.1.2 | 011b | Margin Payload[7:6] = <br> Step Margin Execution Status (see § Section 4.2.18.1.1) <br> Margin Payload[5:0] = M $_{\text {ErrorCount }}$ |
| Step Margin to voltage offset to up/down of default | 100b | 001b <br> through <br> 110b | See $\S$ Section <br> 4.2.18.1.2 | 100b | Margin Payload[7:6] = <br> Step Margin Execution Status (see § Section 4.2.18.1.1) <br> Margin Payload[5:0] = M $_{\text {ErrorCount }}$ |
| Vendor Defined | 101b | 001b <br> through <br> 110b | Vendor <br> Defined | 101b | Vendor Defined |

Note:

| Command |  |  | Response |  |  |
| :--: | :--: | :--: | :--: | :--: | :--: |
| Margin Command | Margin <br> Type[2:0] | Valid <br> Receiver <br> Number(s) | Margin <br> Payload[7:0] | Margin <br> Type[2:0] | Margin Payload[7:0] |

1. The term Step Margin command is used to refer to either a Step Margin to timing offset to right/left of default or a Step Margin to voltage offset to up/down of default command.

# 4.2.18.1.1 Step Margin Execution Status 

The Step Margin Execution Status used in § Table 4-73 is a 2-bit field defined as follows:
11b
NAK. Indicates that an unsupported Lane Margining command was issued. For example, timing margin beyond $\pm 0.2 \mathrm{UI} . \mathrm{M}_{\text {ErrorCount }}$ is 0 .

10b
Margining in progress. The Receiver is executing a Step Margin command. $\mathrm{M}_{\text {ErrorCount }}$ reflects the number of errors detected as defined in $\S$ Section 8.4.4 .

## 01b

Set up for margin in progress. This indicates the Receiver is getting ready but has not yet started executing a Step Margin command. $\mathrm{M}_{\text {ErrorCount }}$ is 0 .

00b
Too many errors - Receiver autonomously went back to its default settings. $\mathrm{M}_{\text {ErrorCount }}$ reflects the number of errors detected as defined in $\S$ Section 8.4.4 . Note that $\mathrm{M}_{\text {ErrorCount }}$ might be greater than Error Count Limit.

### 4.2.18.1.2 Margin Payload for Step Margin Commands

For the Step Margin to timing offset to right/left of default command, the Margin Payload field is defined as follows:

- Margin Payload [7]: Reserved.
- If M IndLeftRightTiming for the targeted Receiver is Set:
- Margin Payload [6] indicates whether the Margin Command is right vs. left. A 0b indicates to move the Receiver to the right of the normal setting whereas a 1 b indicates to move the Receiver to the left of the normal setting.
- Margin Payload [5:0] indicates the number of steps to the left or right of the normal setting.
- If M IndLeftRightTiming for the targeted Receiver is Clear:
- Margin Payload [6]: Reserved
- Margin Payload [5:0] indicates the number of steps beyond the normal setting.

For the Step Margin to voltage offset to up/down of default command, the Margin Payload field is defined as follows:

- If M IndUpDownVoltage for the targeted Receiver is Set:

- Margin Payload [7] indicates whether the Margin Command is up vs. down. A 0b indicates to move the Receiver up from the normal setting whereas a 1 b indicates to move the Receiver down from the normal setting.
- Margin Payload [6:0] indicates the number of steps up or down from the normal setting.
- If M ${ }_{\text {IndUpDownVoltage }}$ for the targeted Receiver is Clear:
- Margin Payload [7]: Reserved
- Margin Payload [6:0] indicates the number of steps beyond the normal setting.


# 4.2.18.2 Margin Command and Response Flow 

Each Receiver advertises its capabilities as defined in § Section 8.4.4. The Receiver being margined must report the number of errors that are consistent with data samples occurring at the indicated location for margining. For simplicity, the Margin Commands and requirements are described in terms of moving the data sampler location though the actual margining method may be implementation specific. For example, the timing margin could be implemented on the actual data sampler or an independent error sampler. Further, the timing margin can be implemented by injecting an appropriate amount of stress/jitter to the data sample location, or by actually moving the data/error sample location. When an independent data/error sampler is used, the errors encountered with the independent data/error sampler must be reported in $\mathrm{M}_{\text {ErrorCount }}$ even though the Link may not experience any errors. To margin a Receiver, Software moves the target Receiver to a voltage/timing offset from its default sampling position.

The following rules must be followed:

- Every Retimer Upstream Pseudo Port Receiver and the Downstream Port Receiver must compute the Margin CRC and Margin Parity bits and compare against the received Margin CRC and Margin Parity bits. Any mismatch must result in ignoring the contents of Symbols $4 \mathrm{~N}+2$ and $4 \mathrm{~N}+3$. A Downstream Port Receiver must report Margin CRC and Margin Parity errors in the Lane Error Status Register (see § Section 7.7.3.3).
- The Upstream Port Receiver is permitted to ignore the Margin CRC bits, Margin Parity bits, and all bits in the Symbols $4 \mathrm{~N}+2$ and $4 \mathrm{~N}+3$ of the Control SKP Ordered Set. If it checks Margin CRC and Margin Parity, any mismatch must be reported in the Lane Error Status Register.
- The Downstream Port must transmit Control SKP Ordered Sets in each Lane, with the Margin Type, Receiver Number, Usage Model, and Margin Payload fields reflecting the corresponding control fields in the Margining Lane Control Register. Any Control SKP Ordered Set transmitted more than $10 \mu$ s after the Configuration Write Completion must reflect the Margining Lane Control Register values written by that Configuration Write.
- This requirement applies regardless of the values in the Margining Lane Control Register.
- This requirement applies regardless of the number of Retimer(s) in the Link.
- For Control SKP Ordered Sets received by the Upstream Pseudo Port, a Retimer Receiver is the target of a valid Margin Command, if all of the following conditions are true:
- the Margin Type is not No Command
- the Receiver Number is the number assigned to the Receiver, or Margin Type is either Clear Error Log or Go to Normal Settings and the Receiver Number is 'Broadcast'.
- the Usage Model field is Ob
- the Margin Type, Receiver Number, and Margin Payload fields are consistent with the definitions in § Table 4-72 and § Table 4-73
- the Margin CRC check and Margin Parity check pass.
- For Upstream and Downstream Ports, a Receiver is the target of a valid Margin Command, if all of the following conditions are true for its Margining Lane Control Register:

- the Margin Type is not No Command
- the Receiver Number is the number assigned to the Receiver or Margin Type is either Clear Error Log or Go to Normal Settings and the Receiver Number is 'Broadcast'
- the Usage Model field is Ob
- the Margin Type, the Receiver Number, and Margin Payload fields are consistent with the definitions in § Table 4-72 and § Table 4-73
- The Upstream Port must transmit the Control SKP Ordered Set with No Command.
- A target Receiver must apply and respond to the Margin Command within 1 ms of receiving the valid Margin Command if the Link is still in L0 state and operating at $16.0 \mathrm{GT} / \mathrm{s}$ or higher Data Rate.
- A target Receiver in a Retimer must send a response in the Control SKP Ordered Set in the Upstream Direction within 1 ms of receiving the Margin Command.
- A target Receiver in the Upstream Port must update the Status field of the Lane Margin Command and Status register within 1 ms of receiving the Margin Command.
- A target Receiver in the Downstream Port must update the Status field of the Lane Margin Command and Status register within 1 ms of receiving the Margin Command if the command is not broadcast or no Retimer(s) are present
- For a valid Margin Type, other than No Command, that is broadcast and received by a Retimer:
- A Retimer, in position X (see § Figure 4-79), forwards the response unmodified in the Upstream Control SKP Ordered Set, if the command has been applied, else it sends the No Command.
- The Receiver Number field of the response must be set to an encoding of one of the Retimer's Pseudo Ports.
- The Retimer must respond only after both Pseudo Ports have completed the Margin Command.
- The Retimer must overwrite Bits [4:0] of Symbol 4N+1, Bits[7, 5:0] of Symbol 4N+2 and Bits [7:0] in Symbol $4 \mathrm{~N}+3$ as it forwards the Control SKP Ordered Set in the Upstream direction if it is the target Receiver of a Margin Command and is executing the command.
- On receipt of a Control SKP Ordered Set, the Downstream Port must reflect the Margining Lane Status Register from the corresponding fields in the received Control SKP Ordered Set within $1 \mu \mathrm{~s}$, if it passes the Margin CRC and Margin Parity checks and one of the following conditions apply:
- In the Margining Lane Control Register: Receiver Number is 010b through 101b
- In the Margining Lane Control Register: Receiver Number is 000b, Margin Command is Clear Error Log, No Command, or Go to Normal Settings, and there are Retimer(s) in the Link
- Optionally, if the Margining Lane Control Register Usage Model field is 1b
- Optionally, if the Margining Lane Control Register Receiver Number field is 110b or 111b

The Margining Lane Status Register fields are updated regardless of the Usage Model bit in the received Control SKP Ordered Set.

- A component must advertise the same value for each parameter defined in § Table 8-13 in § Section 8.4.4 across all its Receivers. A component must not change any parameter value except for $\mathrm{M}_{\text {SampleCount }}$ and $\mathrm{M}_{\text {ErrorCount }}$ defined in § Table 8-13 in § Section 8.4.4 while LinkUp = 1b.
- A target Receiver that receives a valid Step Margin command must continue to apply that offset until any of the following occur:
- it receives a valid Go to Normal Settings command
- it receives a subsequent valid Step Margin command with different Margin Type or Margin Payload field

- M ${ }_{\text {IndErrorSampler }}$ is 0 b and $\mathrm{M}_{\text {ErrorCount }}$ exceeds Error Count Limit
- Optionally, $\mathrm{M}_{\text {IndErrorSampler }}$ is 1 b and $\mathrm{M}_{\text {ErrorCount }}$ exceeds Error Count Limit.
- If a Step Margin command terminates because $\mathrm{M}_{\text {ErrorCount }}$ exceeds Error Count Limit, the target Receiver must automatically return to its default sample position and indicate this in the Margin Payload field (Step Margin Execution Status $=00 \mathrm{~b}$ ). Note: termination for this reason is optional if $\mathrm{M}_{\text {IndErrorSampler }}$ is 1 b .
- If $\mathrm{M}_{\text {IndErrorSampler }}$ is 0 b , an error is detected when:
- The target Receiver is a Port that enters Recovery or detects a Data Parity mismatch while in LO
- The target Receiver is a Pseudo Port that enters Forwarding training sets or detects a Data Parity mismatch while forwarding non-training sets.
- If $\mathrm{M}_{\text {IndErrorSampler }}$ is 1 b , an error is detected when:
- The target Receiver is a Port and a bit error is detected while in LO
- The target Receiver is a Pseudo Port and a bit error is detected while the Retimer is forwarding non-training sets
- If $\mathrm{M}_{\text {IndErrorSampler }}$ is 0 b and either (1) the target Receiver is a Port that enters Recovery or (2) the target Receiver is a Pseudo Port that enters Forwarding training sets:
- The target Receiver must go back to the default sample position
- If the target Receiver is a Port that is still performing margining, it must resume the margin position within $128 \mu \mathrm{~s}$ of entering LO
- If the target Receiver is a Pseudo Port that is still performing margining, it must resume the margin position within $128 \mu \mathrm{~s}$ of Forwarding non-training sets
- A target Receiver is required to clear its accumulated error count on receiving Clear Error Log command, while it continues to margin (if it is the target Receiver of a Step Margin command still in progress), if it was doing so.
- For a target Receiver of a Set Error Count Limit command, the new value is used for all future Step Margin commands until a new Set Error Count Limit command is received.
- If no Set Error Count Limit is received by a Receiver since entering LO, the default value is 4.
- Behavior is undefined if a Set Error Count Limit command is received while a Step Margin command is in effect.
- Once a target Receiver reports a Step Margin Execution Status of 11b (NAK) or 00b ('Too many errors'), it must continue to report the same status as long as the Step Margin command is in effect.
- A target Receiver must not report a Step Margin Execution Status of 01b ('Set up for margin in progress') for more than 100 ms after it receives a new valid Step Margin command
- A target Receiver that reports a Step Margin Execution Status other than 01b, cannot report 01b subsequently unless it receives a new valid Step Margin command.
- Reserved bits in the Margin Payload field must follow these rules:
- The Downstream or Upstream Port must transmit 0s for Reserved bits
- The retimer must forward Reserved bits unmodified
- All Receivers must ignore Reserved bits
- Reserved encodings of the Margin Type, Receiver Number, or Margin Payload fields must follow these rules:
- The retimer must forward Reserved encodings unmodified
- All Receivers must treat Reserved encodings as if they are not the target of the Margin Command
- A Vendor Defined Margin Command or response, that is not defined by a retimer is ignored and forwarded normally.

- A target Receiver on a Retimer must return 00 h on the response payload on Access Retimer Register command, if it does not support register access. If a Retimer supports Access Retimer Register command, the following must be observed:
- It must return a non-zero value for the DWORD at locations 80 h and 84 h respectively.
- It must not place any registers corresponding to Margin Payload locations 88 h through 9Fh.


# 4.2.18.3 Flit Mode 8.0 GT/s Margining Behavior 

Lane Margining is defined for 16.0 GT/s and higher data rates. Lane Margining is not supported at 2.5, 5.0, and 8.0 GT/s. In Non-Flit Mode, Control SKP Ordered Sets only present at 16.0 GT/s and higher data rates so margin commands at slower speeds are not possible. In Flit Mode, Control SKP Ordered Sets are also used at 8.0 GT/s.

The following behavior is recommended in Flit Mode at $8.0 \mathrm{GT} / \mathrm{s}$ :

- Upstream and Downstream Ports must send Control SKP Ordered Sets as defined, but the margin command should always be No Command, regardless of the contents of the Margining Lane Control Register.
- Upstream Ports, Downstream Ports, and Retimer Upstream Ports should ignore the margin command in received Control SKP Ordered Sets.
- The Margining Lane Status Register value is unpredictable.
- Upstream and Downstream Ports are permitted to compute the Margin CRC and Margin Parity bits and compare against the received Margin CRC and Margin Parity bits. If checked, any mismatch must be reported as Margin CRC and Margin Parity errors in the Lane Error Status Register (see § Section 7.7.3.3).


### 4.2.18.4 Receiver Margin Testing Requirements

Software must ensure that the following conditions are met before performing Lane Margining at Receiver:

- The current Link data rate must be $16.0 \mathrm{GT} / \mathrm{s}$ or higher.
- The current Link width must include the Lanes that are to be tested.
- The Upstream Port's Function(s) must be programmed to a D-state that prevents the Port from entering the L1 Link state. See § Section 5.2 for more information.
- The ASPM Control field of the Link Control register must be set to 00b (Disabled) in both the Downstream Port and Upstream Port.
- The state of the Hardware Autonomous Speed Disable bit of the Link Control 2 register and the Hardware Autonomous Width Disable bit of the Link Control register must be saved to be restored later in this procedure.
- If writeable, the Hardware Autonomous Speed Disable bit of the Link Control 2 register must be Set in both the Downstream Port and Upstream Port. (If hardwired to 0b, the autonomous speed change mechanism is not implemented and is therefore inherently disabled.)
- If writeable, the Hardware Autonomous Width Disable bit of the Link Control register must be Set in both the Downstream Port and Upstream Port. (If hardwired to 0b, the autonomous width change mechanism is not implemented and is therefore inherently disabled.)

While margining, software must ensure the following:

- All Margin Commands must have the Usage Model field in the Margining Lane Control Register set to 0b. While checking for the status of an outstanding Margin Command, software must check that the Usage Model field of the status part of the Margining Lane Status Register is set to 0b.
- Software must read the capabilities offered by a Receiver and margin it within the constraints of the capabilities it offers. The commands issued and the process followed to determine the margin must be consistent with the definitions provided in § Section 4.2.18 and § Section 8.4.4. For example, if the Port does not support voltage testing, then software must not initiate a voltage test. In addition, if a Port supports testing of 2 Lanes simultaneously, then software must test only 1 or 2 Lanes at the same time and not more than 2 Lanes.
- For Receivers where $M_{\text {IndErrorSampler }}$ is 1 b , any combination of such Receivers are permitted to be margined in parallel.
- For Receivers where $M_{\text {IndErrorSampler }}$ is 0 b , at most one such Receiver is permitted to be margined at a time. However, margining may be performed on multiple Lanes simultaneously, as long as it is within the maximum number of Lanes the device supports.
- Software must ensure that the Margin Command it provides in the Margining Lane Control Register is a valid one, as defined in § Section 4.2.18.1. For example, the Margin Type must have a defined encoding and the Receiver Number and Margin Payload consistent with it.
- After issuing a command by writing to the Margining Lane Control Register atomically, software must check for the completion of this command. This is done by atomically reading the Margining Lane Status Register and checking that the status fields match the expected response for the issued command (see § Table 4-72 and § Table 4-73). It is strongly recommended that software continue to reread the Margining Lane Status Register if it does not find the expected Receiver Number. If 10 ms has elapsed after a new Margin Command was issued and the values read do not match the expected response, software is permitted to assume that the Receiver will not respond, and declare that the target Receiver failed margining. For a broadcast command other than No Command the Receiver Number in the response must correspond to one of the Pseudo Ports in Retimer Y or Retimer Z, if Retimers are present, or the Downstream Port if they are not, as described in § Figure 4-79.
- Any two reads of the Margining Lane Status Register should be spaced at least $10 \mu \mathrm{~s}$ apart to make sure they are reading results from different Control SKP Ordered Sets.
- Software must broadcast No Command and wait for it to complete, or for 10 ms to elapse without observing that completion, prior to issuing a new Margin Type or Receiver Number or Margin Payload in the Margining Lane Control Register.
- At the end of margining in a given direction (voltage/ timing and up/down/left/right), software must broadcast Go to Normal Settings, No Command, Clear Error Log, and No Command in series in the Downstream and Upstream Ports, after ensuring each command has been acknowledged by the target Receiver.
- If the Data Rate has changed during margining, margining results (if any) are not accurate and software must exit the margining procedure. Software must set the Margining Lane Control Register to No Command to avoid starting margining if the Data Rate later changes to $16.0 \mathrm{GT} / \mathrm{s}$ or higher.
- Software is permitted to issue a Clear Error Log command periodically while margining is in progress, to gather error information over a long period of time.
- Software must not attempt to margin both timing and voltage of a target Receiver simultaneously. Results are undefined if a Receiver receives commands that would place both voltage and timing margin locations away from the default sample position at the same time.
- Software should allow margining to run for at least $10^{8}$ bits margined by the Receiver under test before switching to the next margin step location (unless the error limit is exceeded).
- Software must account for the 'set up for margin in progress' status while measuring the margin time or the number of bits sampled by the Receiver.

- If a target Receiver is reporting 'set up for margin in progress' for 200 ms after issuing one of the Step Margin commands, Software is permitted to assume that the Receiver will not respond and declare that the target Receiver failed margining.
- If a Receiver reports a 'NAK' in the Margin Payload status field and the corresponding Step Margin command was valid and within the allowable range (as defined in $\S$ Section 4.2.18 and $\S$ Section 8.4.4), Software is permitted to declare that the target Receiver failed margining.
- When the margin testing procedure is completed, the state of the Hardware Autonomous Speed Disable bit and the Hardware Autonomous Width Disable bit must be restored to the previously saved values.

# IMPLEMENTATION NOTE: EXAMPLE SOFTWARE FLOW FOR LANE MARGINING AT RECEIVER 5 

For getting the invariant parameters the following steps may be followed. Once obtained, the same parameters can be used across multiple sets of margining tests as long as LinkUp=1b continues to be true. For each component in the Link, do the following Steps. Software can do these steps in parallel for different components on different Lanes of the Link.

## Step A1:

Issue Report Margin Control Capabilities (Margin Type = 001b, Margin Payload = 88h, Receiver Number = target device in the Margining Lane Control Register)

## Step A2:

Read the Margining Lane Status Register.
a. If Margin Type $=001 b$ and Receiver Number $=$ target Receiver: Go to Step A3
b. Else: If 10 ms has expired since command issued, declare Receiver failed margining and exit; else wait for $>10 \mu \mathrm{~s}$ and Go to Step A2

## Step A3:

Store the information provided Margin Payload status field for use during margining.

## Step A4:

Broadcast No Command (Margin Type = 111b, Receiver Number = 000b, and Margin Payload = 9Ch in the Margining Lane Control Register) and wait for those to be reflected back in the Margining Lane Status Register. If 10 ms expires without getting the command completion handshake, declare the Receiver failed margining and exit.

## Step A5:

Repeat Step A1 through Step A4 for Report $\mathrm{M}_{\text {NumVoltageSteps, Report }} \mathrm{M}_{\text {NumTimingSteps, Report }}$
$\mathrm{M}_{\text {MaxTimingOffset, Report }} \mathrm{M}_{\text {MaxVoltageOffset, Report }} \mathrm{M}_{\text {SamplingRateVoltage, and Report }} \mathrm{M}_{\text {SamplingRateTiming. It may }}$ be noted that this step can be executed in parallel across different Lanes for different Margin Type.

Margining on each Lane across the Link can be a sequence of separate commands. Prior to launching the sequence, software should read the maximum number of Lanes it is allowed to run margining simultaneously. The steps would be similar to Step A1 through Step A4 above with the Report $\mathrm{M}_{\text {MaxLanes }}$ command. After that software can simultaneously margin up to that many Lanes of the Link. On each Link, each Receiver is margined based on its capability, subject to the constraints described here, after ensuring the Link is operating at full width in $16.0 \mathrm{GT} / \mathrm{s}$ or higher Data Rate and the hardware autonomous width and speed change as well as ASPM power states have been disabled.

If software desires to set an Error Count Limit value different than default of 4 or whatever was programmed last, it executes the following Steps prior to going to Step C1 below.

## Step B1:

Issue Set Error Count Limit (Margin Type = 010b, the target Receiver Number, and Margin Payload = \{11b, Error Count Limit\} in the Margining Lane Control Register)

## Step B2:

Read the Margining Lane Status Register.

a. If Margin Type $=010 b$, Receiver Number $=$ target Receiver, and Margin Payload $=$ Margin Payload control field (Bits [14:7]), go to Step B4
b. Else: If 10 ms has expired since command issued, go to Step B3; else wait for $>10 \mu \mathrm{~s}$ and Go to Step B2

# Step B3: 

Margining has failed. Invoke the system checks to find out if the Link degraded in width/speed due to reliability reasons.

## Step B4:

Broadcast No Command and wait for those to be reflected back in the status fields. If 10 ms expires without getting the command completion handshake, declare the Receiver failed margining and exit.

The following steps is an example flow of one margin point for a given Receiver executing Step Margin to timing offset to right/left of default starting with 15 steps to the right:

## Step C1:

Write Margin Type $=011 b$, the target Receiver Number, and Margin Payload $=\{0000 b, 1111 b\}$ in the Margining Lane Control Register

## Step C2:

Read the Margining Lane Status Register.
a. If Margin Type $=011 b$ and Receiver Number $=$ target Receiver, Go to Step C3
b. Else If 10 ms has expired since command issued, declare Receiver has failed margining and go to Step C7
c. Wait for $>10 \mu \mathrm{~s}$ and Go to Step C2

## Step C3:

In the Margining Lane Status Register:
a. If Margin Payload[7:6] = 11b:
i. If we exceeded the 0.2 UI, that is the margin;
ii. Else report margin failure at this point and go to Step C7;
b. Else if Margin Payload[7:6] = 00b:
i. report margin failure at this point and go to Step C7
c. Else if Margin Payload[7:6] = 01b:
i. If 200 ms has elapsed since entering Step C3, report that the Receiver failed margining test and exit;
ii. else wait 1 ms , read the Margining Lane Status Register and go to Step C3
d. Else go to Step C4

## Step C4:

Wait for the desired amount of time for margining to happen while sampling the Margining Lane Status Register periodically for the number of errors reported in the Margin Payload field (Bits [5:0] - $\mathrm{M}_{\text {ErrorCount }}$ ).

For longer runs, issue the No Command followed by the Clear Error Log commands, (using procedures similar to Step B1 through Step B4, with the corresponding expected status field) if the length of time will cause the error count to exceed the Set Error Count Limit even when staying within the expected BER target.

If the aggregate error count remains within the expected error count and the Margin Payload[7:6] in the status field remains 10b till the end, the Receiver has the required Margin at the timing margin step; else it fails that timing margin step go to Step C7.

# Step C5: 

Broadcast No Command and wait for those to be reflected back in the status fields. If 10 ms expires without getting the command completion handshake, declare the Receiver failed margining and exit.

## Step C6:

Go to Step C1, incrementing the number of timing steps through the Margin Payload control field (Bits[5:0]) if we want to test against a higher margin amount; else go to Step C8 noting the margin value that the Receiver passed

## Step C7:

Margin failed; The previous margin step the Receiver passed in Step C6 is the margin of the Receiver

## Step C8:

Broadcast No Command, Clear Error Log, No Command, Go to Normal Settings series of commands (using a procedure similar to Step B1 through Step B4 with the corresponding expected status fields)

### 4.3 Retimers 5

This Section defines the requirements for Retimers that are Physical Layer protocol aware and that interoperate with any pair of components with any compliant channel on each side of the Retimer. An important capability of a Physical Layer protocol aware Retimer is to execute the Phase $2 / 3$ of the equalization procedure in each direction. A maximum of two Retimers are permitted between an Upstream and a Downstream Port.

The two Retimer limit is based on multiple considerations, most notably limits on modifying SKP Ordered Sets and limits on the time spent in Phase $2 / 3$ of the equalization procedure. To ensure interoperability, platform designers must ensure that the two Retimer limit is honored for all PCI Express Links, including those involving form factors as well as those involving active cables. Form factor specifications may define additional Retimer rules that must be honored for their form factors. Assessing interoperability with any Extension Device not based on the Retimer definition in this section is outside the scope of this specification.

Many architectures of Extension Devices are possible, i.e., analog only Repeater, protocol unaware Retimer, etc. This specification describes a Physical Layer protocol aware Retimer. It may be possible to use other types of Extension Devices in closed systems if proper analysis is done for the specific channel, Extension Device, and end-device pair - but a specific method for carrying out this analysis is outside the scope of this specification.

Retimers have two Pseudo Ports, one facing Upstream, and the other facing Downstream. The Transmitter of each Pseudo Port must derive its clock from a 100 MHz reference clock. The reference clock(s) must meet the requirements of § Section 8.6. A Retimer supports one or more reference clocking architectures as defined in § Section 8.6 Electrical Sub-block.

In most operations Retimers simply forward received Ordered Sets, DLLPs, TLPs, Logical Idle, and Electrical Idle. Retimers are completely transparent to the Data Link Layer and Transaction Layer. System software shall not enable L0s on any Link where a Retimer is present. Support of Beacon by Retimers is optional and beyond the scope of this specification.

When using 128b/130b encoding the Retimer executes the protocol so that each Link Segment undergoes independent Link equalization as described in § Section 4.3.6 .

The Pseudo Port orientation (Upstream or Downstream) is determined dynamically, while the Link partners are in Configuration. Both crosslink and regular Links are supported.

# 4.3.1 Retimer Requirements 

The following is a high level summary of Retimer requirements:

- Retimers are required to comply with all the electrical specification described in § Chapter 8. Electrical Sub-block. Retimers must operate in one of two modes:
- Retimers' Receivers operate at $8.0 \mathrm{GT} / \mathrm{s}$ and above with an impedance that meets the range defined by the $Z_{\text {RX-DC }}$ parameter for $2.5 \mathrm{GT} / \mathrm{s}$.
- Retimers' Receivers operate at $8.0 \mathrm{GT} / \mathrm{s}$ and above with an impedance that does not meet the range defined by the $Z_{\text {RX-DC }}$ parameter for $2.5 \mathrm{GT} / \mathrm{s}$. In this mode the $Z_{\text {RX-DC }}$ parameter for $2.5 \mathrm{GT} / \mathrm{s}$ must be met with in 1 ms of receiving an EIOS or inferring Electrical Idle and while the Receivers remain in Electrical Idle.
- Forwarded Symbols must always be de-skewed when more than one Lane is forwarding Symbols (including upconfigure cases).
- Determine Port orientation dynamically.
- Determine Data Stream Mode (Flit Mode or Non-Flit Mode) dynamically.
- Perform Lane polarity inversion (if needed).
- Interoperate with the Link equalization procedure for Phase 2 and Phase 3, when using 128b/130b or 1b/1b encoding, on each Link Segment.
- Interoperate with de-emphasis negotiation at $5.0 \mathrm{GT} / \mathrm{s}$, on each Link Segment.
- Interoperate with Link Upconfigure.
- Interoperate with LOp.
- Pass loopback data between the Loopback Lead and Loopback Follower.
- Optionally execute Follower Loopback on one Pseudo Port when using 8b/10b or 128b/130b encoding
- Execute Follower Loopback on one Pseudo Port when using 1b/1b
- Generate the Compliance Pattern on each Pseudo Port.
- Load board method (i.e., time out in Polling.Active).
- Forward Modified Compliance Pattern when the Link enters Polling.Compliance via Compliance_Receive_Request in TS1 Ordered Sets.
- Forward Compliance or Modified Compliance Patterns when Ports enter Polling.Compliance via the Enter Compliance bit in the Link Control 2 register is set to 1b in both the Upstream Port and the Downstream Port and Retimer Enter Compliance is set to 1b (accessed in an implementation specific manner) in the Retimer.
- Adjust the data rate of operation in concert with the Upstream and Downstream Ports of the Link.
- Adjust the Link width in concert with the Upstream and Downstream Ports of the Link.
- Capture Lane numbers during Configuration.
- Lane numbers are required when using 128b/130b and 1b/1b encoding for the scrambling seed.
- Capture the Flit Mode Supported bit during Polling and Configuration during Link training.
- The Flit Mode Supported bit is used to determine the Data Stream Mode.
- Dynamically adjust Retimer Receiver impedance to match end Component Receiver impedance.

- Infer entering Electrical Idle at all data rates.
- Modify certain fields of Ordered Sets while forwarding.
- Perform clock compensation via addition or removal of SKP Symbols.
- Support L1.
- Optionally Support L1 PM Substates.
- If 32.0 GT/s capable, then interoperate with Link equalization to the highest data rate.
- If 32.0 GT/s capable, then interoperate with No Equalization Needed mode.
- If 32.0 GT/s capable, then interoperate with the use of Modified TS1/TS2 Ordered Sets.
- Forward 1b/1b Control SKP Ordered Sets that have Phy Payload Type equal to 0b. Thus, 1b/1b Control SKP Ordered Sets with Margin Payload will be forwarded.


# 4.3.2 Supported Retimer Topologies 

§ Figure 4-80 shows the topologies supported by Retimers defined in this specification. There may be one or two Retimers between the Upstream and Downstream Ports on a Link. Each Retimer has two Pseudo Ports, which determine their Downstream/Upstream orientation dynamically. Each Retimer has an Upstream Path and a Downstream Path. Both Pseudo Ports must always operate at the same data rate, when in Forwarding mode. Thus, each Path will also be at the same data rate. A Retimer is permitted to support any width option defined by this specification as its maximum width. The behavior of the Retimer in each high level operating mode is:

- Forwarding mode:
- Symbols, Electrical Idle, and exit from Electrical Idle; are forwarded on each Upstream and Downstream Path.
- Execution mode:
- The Upstream Pseudo Port acts as an Upstream Port of a Component. The Downstream Pseudo Port acts as a Downstream Port of a Component. This mode is used in the following cases:
- Polling.Compliance.
- Phase 2 and Phase 3 of the Link equalization procedure.
- Optionally Follower Loopback.

![img-78.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-78.jpeg)

Figure 4-80 Supported Retimer Topologies

# 4.3.3 Variables 

The following variables are set to the following specified values following a Fundamental Reset or whenever the Retimer receives Link and Lane number equal to PAD on two consecutive TS2 Ordered Sets on all Lanes that are receiving TS2 Ordered Sets on both Upstream and Downstream Pseudo Ports within a $1 \mu$ s time window from the last Symbol of the second TS2 Ordered Set on the first Lane to the last Symbol of the second TS2 Ordered Set on the last Lane.

- RT_port_orientation $=$ undefined
- RT_captured_lane_number $=$ PAD
- RT_captured_link_number $=$ PAD
- RT_G3_EQ_complete $=0 b$
- RT_G4_EQ_complete $=0 b$
- RT_G5_EQ_complete $=0 b$
- RT_G6_EQ_complete $=0 b$

- $\boldsymbol{R T} \_$LinkUp $=0 b$
- $\boldsymbol{R T} \_$number $=$ undefined
- $\boldsymbol{R T} \_$next_data_rate $=2.5 \mathrm{GT} / \mathrm{s}$
- RT_error_data_rate $=2.5 \mathrm{GT} / \mathrm{s}$
- RT_flit_mode_enabled $=0 b$


# 4.3.4 Receiver Impedance Propagation Rules 

The Retimer Transmitters and Receivers shall meet the requirements in $\S$ Section 4.2.5.9.1 while Fundamental Reset is asserted. When Fundamental Reset is deasserted the Retimer is permitted to take up to 100 ms to begin active determination of its Receiver impedance. A Retimer that supports only Link speeds $5.0 \mathrm{GT} / \mathrm{s}$ or less must do this within 20 ms . During this interval the Receiver impedance remains as required during Fundamental Reset. Once this interval has expired Receiver impedance on Retimer Lanes is determined as follows:

- Within 1.0 ms of the Upstream or Downstream Port's Receiver meeting the $\mathrm{Z}_{\text {RX-DC }}$ parameter, the low impedance is back propagated, (i.e., the Retimer's Receiver shall meet the $\mathrm{Z}_{\mathrm{RX}-\mathrm{DC}}$ parameter on the corresponding Lane on the other Pseudo Port). Each Lane operates independently and this requirement applies at all times.
- The Retimer must keep its Transmitter in Electrical Idle until the $\mathrm{Z}_{\mathrm{RX}-\mathrm{DC}}$ condition has been detected. This applies on an individual Lane basis.


### 4.3.5 Switching Between Modes

The Retimer operates in two basic modes, Forwarding mode or Execution mode. When switching between these modes the switch must occur on an Ordered Set boundary for all Lanes of the Transmitter at the same time. No other Symbols shall be between the last Ordered Set transmitted in the current mode and the first Symbol transmitted in the new mode.

When using 128b/130b or 1b/1b the Transmitter must maintain the correct scrambling seed and LFSR value when switching between modes.

When switching between Forwarding and Execution modes, the Retimer must ensure that at least 16 TS0/TS1 Ordered Sets and at most 64 TS0/TS1 Ordered Sets are transmitted between the last EIEOS transmitted in the previous mode and the first EIEOS transmitted in the new mode.

When switching to and from the Execution Link Equalization mode the Retimer must ensure a Transmitter does not send two SKP Ordered Sets in a row, and that the maximum allowed interval is not exceeded between SKP Ordered Sets, see § Section 4.2.8.4.

### 4.3.6 Forwarding Rules

These rules apply when the Retimer is in Forwarding mode. The Retimer is in Forwarding mode after the deassertion of Fundamental Reset.

- If the Retimer's Receiver detects an exit from Electrical Idle on a Lane the Retimer must enter Forwarding mode and forward the Symbols on that Lane to the opposite Pseudo Port as described in § Section 4.3.6.3.

- The Retimer must continue to forward the received Symbols on a given Lane until it enters Execution mode or until an EIOS is received, or until Electrical Idle is inferred on that Lane. This requirement applies even if the Receiver loses Symbol lock or Block Alignment. See § Section 4.3.6.5 for rules regarding Electrical Idle entry.
- A Retimer shall forward all Symbols unchanged, except as described in § Section 4.3.6.9 and § Section 4.3.6.7.
- When operating at 64.0 GT/s data rate, a Retimer must follow the requirements of $\S$ Section 4.2.3.2 in order to identify SKP OS, EIEOS, and EIOS received.
- When operating at 2.5 GT/s data rate, if any Lane of a Pseudo Port receives TS1 Ordered Sets with Link and Lane numbers set to PAD for 5 ms or longer, and the other Pseudo Port does not detect an exit from Electrical Idle on any Lane in that same window, and either of the following occurs:
- The following sequence occurs:
- An EIOS is received on any Lane that was receiving TS1 Ordered Sets
- followed by a period of Electrical Idle, for less than 5 ms
- followed by Electrical Idle Exit that cannot be forwarded according to § Section 4.3.6.3
- Note: this is interpreted as the Port attached to the Receiver going into Electrical Idle followed by a data rate change for a Compliance Pattern above $2.5 \mathrm{GT} / \mathrm{s}$.
- Compliance Pattern at $2.5 \mathrm{GT} / \mathrm{s}$ is received on any Lane that was receiving TS1 Ordered Sets.

Then the Retimer enters the Execution mode CompLoadBoard state, and follows § Section 4.3.7.1 .

- If any Lane on the Upstream Pseudo Port receives two consecutive TS0/TS1 Ordered Sets with the EC field equal to 10 b , when using $128 \mathrm{~b} / 130 \mathrm{~b}$ or $1 \mathrm{~b} / 1 \mathrm{~b}$ encoding, then the Retimer enters Execution mode Equalization, and follows § Section 4.3.7.2 .
- If the Retimer is configured to support Execution mode Follower Loopback and if any Lane on either Pseudo Port receives two consecutive TS1 Ordered Sets or two consecutive TS2 Ordered Sets with Loopback_Request asserted then the Retimer enters Execution mode Follower Loopback, and follows § Section 4.3.7.3.


# 4.3.6.1 Forwarding Type Rules 

A Retimer must determine what type of Symbols it is forwarding. The rules for inferring Electrical Idle are a function of the type of Symbols the Retimer is forwarding. If a Path forwards two consecutive TS0, TS1, or TS2 Ordered Sets, on any Lane, then the Path is forwarding training sets. If a Path forwards eight consecutive Symbol Times of Idle data on all Lanes that are forwarding Symbols then the Path is forwarding non-training sets. When a Retimer transitions from forwarding training sets to forwarding non-training sets, the variable RT_error_data_rate is set to $2.5 \mathrm{GT} / \mathrm{s}$ if $8 \mathrm{~b} / 10 \mathrm{~b}$ or $128 \mathrm{~b} / 130 \mathrm{~b}$ encoding is being used and set to $32.0 \mathrm{GT} / \mathrm{s}$ if $1 \mathrm{~b} / 1 \mathrm{~b}$ encoding is being used.

### 4.3.6.2 Orientation, Lane Numbers, and Data Stream Mode Rules

The Retimer must determine the Port orientation, Lane assignment, Lane polarity, and Data stream Mode dynamically as the Link trains.

- When RT_LinkUp=0, the first Pseudo Port to receive two consecutive TS1 Ordered Sets with a non-PAD Lane number on any Lane, has its RT_port_orientation variable set to Upstream Port, and the other Pseudo Port has its RT_port_orientation variable set to Downstream Port.
- The Retimer plays no active part in Lane number determination. The Retimer must capture the Lane numbers with the RT_captured_lane_number variable at the end of the Configuration state, between the Link Components. This applies on the first time through Configuration, i.e., when the RT_LinkUp variable is set to 0b. Subsequent trips through Configuration during Link width configure must not change the Lane numbers.

Lane numbers are required for the scrambling seed when using 128b/130b or 1b/1b. Link numbers are required in some cases when the Retimer is in Execution mode. Link numbers and Lane numbers are captured with the RT_captured_lane_number, and RT_captured_link_number variables whenever the first two consecutive TS2 Ordered Sets that contain non-PAD Lane and non-PAD Link numbers are received after the RT_LinkUp variable is set to 0b. A Retimer must function normally if Lane reversal occurs. When the Retimer has captured the Lane numbers and Link numbers the RT_LinkUp variable is set to 1b. In addition, if the Disable Scrambling bit in the TS2 Ordered Sets is set to 1b, in either case above, then the Retimer determines that scrambling is disabled when using 8b/10b encoding.

- Lane polarity is determined any time the Lane exits Electrical Idle, and achieves Symbol lock at $2.5 \mathrm{GT} / \mathrm{s}$ as described in § Section 4.2.5.5 :
- If polarity inversion is determined the Receiver must invert the received data. The Transmitter must never invert the transmitted data.
- The Retimer plays an active part of Data Stream Mode determination. If the Retimer supports Flit Mode operation, for each Pseudo Port, it must capture the value of the Flit Mode Supported bit of the Data Rate Identifier field in the eight consecutive TS2 Ordered Sets received with Link and Lane numbers set to PAD when the RT_LinkUp variable is set to 0b. If the Flit Mode Supported bit is 1b in eight consecutive TS2 Ordered Sets received by both Pseudo Ports, the RT_flit_mode_enabled variable must be set to 1b and each Pseudo Port must follow Flit Mode rules (as specified in § Section 4.2 ) to identify transitions between Ordered Set Data and Data Streams. If the Retimer does not support Flit Mode operation, its RT_flit_mode_enabled variable must remain set to 0 b and it must set bit 0 of the Data Rate Identifier (Symbol 0) to 0 b in all TS Ordered Sets that it forwards (as described in § Section 4.3.6.7).
- When using 8b/10b with Flit Mode, NOP Flits (instead of Idle data) identify the start of the data stream.
- When using 128b/130b or 1b/1b with Flit Mode, SDS Ordered Sets identify the start of the data stream.
- The Retimer's place in the system topology is determined when eight consecutive TS2 Ordered Sets are received with (non-PAD) matching Link and Lane numbers and identical data rate identifiers. If the Retimer Present bits are set to 01b on the Upstream Pseudo Port, the RT_number must be set to 10b, otherwise RT_number must be set to 01b. The RT_number is used to determine Pseudo Ports B, C, D and E. This identification is needed for Execution Mode Follower Loopback with 1b/1b encoding.


# 4.3.6.3 Electrical Idle Exit Rules 

At data rates other than $2.5 \mathrm{GT} / \mathrm{s}$, EIEOS are sent within the training sets to ensure that the analog circuit detects an exit from Electrical Idle. Receiving an EIEOS is required when using 128b/130b or 1b/1b encoding to achieve Block Alignment. When the Retimer starts forwarding data after detecting an Electrical Idle exit, the Retimer starts transmitting on a training set boundary. The first training sets it forwards must be an EIEOS, when operating at data rates higher than $2.5 \mathrm{GT} / \mathrm{s}$. The first EIEOS sent will be in place of the TS0, TS1, or TS2 Ordered Set that it would otherwise forward.

If no Lanes meet $Z_{\text {RX-DC }}$ on a Pseudo Port, and the following sequence occurs:

- An exit from Electrical Idle is detected on any Lane of that Pseudo Port.
- And then if not all Lanes infer Electrical Idle, via absence of exit from Electrical Idle in a 12 ms window on that Pseudo Port and the other Pseudo Port is not receiving Ordered Sets on any Lane in that same 12 ms window.

Then the same Pseudo Port, where no Lanes meet $Z_{\text {RX-DC }}$, sends the Electrical Idle Exit pattern described below for $5 \mu \mathrm{~s}$ on all Lanes.

If operating at $2.5 \mathrm{GT} / \mathrm{s}$ and the following occurs:

- any Lane detects an exit from Electrical Idle
- and then receives two consecutive TS1 Ordered Sets with Lane and Link numbers equal to PAD
- and the other Pseudo Port is not receiving Ordered Sets on any Lane

Then Receiver Detection is performed on all Lanes of the Pseudo Port that is not receiving Ordered Sets. If no Receivers were detected then:

- The result is back propagated as described in § Section 4.3.4, within 1.0 ms.
- The same Pseudo Port that received the TS1 Ordered Sets with Lane and Link numbers equal to PAD, sends the Electrical Idle Exit pattern described below for $5 \mu \mathrm{~s}$ on all Lanes.

If a Lane detects an exit from Electrical Idle then the Lane must start forwarding when all of the following are true:

- Data rate is determined, see § Section 4.3.6.4, current data rate is changed to RT_next_data_rate if required.
- Lane polarity is determined, see § Section 4.3.6.2 .
- Two consecutive TS0, TS1, or TS2 Ordered Sets are received.
- Two consecutive TS0, TS1, or TS2 Ordered Sets are received on all Lanes that detected an exit from Electrical Idle or the max Retimer Exit Latency has occurred, see § Table 4-74.
- Lane De-skew is achieved on all Lanes that received two consecutive TS0, TS1, or TS2 Ordered Sets.
- If a data rate change has occurred then $6 \mu \mathrm{~s}$ has elapsed since Electrical Idle Exit was detected.

All Ordered Sets used to establish forwarding must be discarded. Only Lanes that have detected a Receiver on the other Pseudo Port, as described in § Section 4.3.4, are considered for forwarding.

Otherwise after a 3.0 ms timeout, if the other Pseudo Port is not receiving Ordered Sets then Receiver Detection is performed on all Lanes of the Pseudo Port that is not receiving Ordered Sets, the result is back propagated as described in § Section 4.3.4, and if no Receivers were detected:

- Then the same Pseudo Port that was unable to receive two consecutive TS0, TS1, or TS2 Ordered Sets on any Lane sends the Electrical Idle Exit pattern described below for $5 \mu \mathrm{~s}$ on all Lanes.
- Else the Electrical Idle Exit pattern described below is forwarded on all Lanes that detected an exit from Electrical Idle.
- When using 8b/10b encoding:
- The Modified Compliance Pattern with the error status Symbol set to 00h.
- When using 128b/130b encoding:
- One EIEOS or one EIEOSQ (recommended).
- 32 Data Blocks, each with a payload of 16 Idle data Symbols (00h), scrambled, for Symbols 0 to 13.
- Symbol 14 and 15 of each Data Block either contain Idle data Symbols (00h), scrambled, or DC Balance, determined by applying the same rules in § Section 4.2.5.1 to these Data Blocks.
- When using 1b/1b encoding:
- Four consecutive EIEOS, uninterrupted by any other Ordered Set including the Control SKP Ordered Set.
- 32 Data Blocks, each with a payload of 16 Idle data Symbols (00h), scrambled, for Symbols 0-6, 8-14.
- Symbol 7 and 15 of each Data Block either contain Idle data Symbols (00h), scrambled, or DC Balance, determined by applying the same rules in § Section 4.2.5.1 to these Data Blocks.

- This Path now is forwarding the Electrical Idle Exit pattern. In this state Electrical Idle is inferred by the absence of Electrical Idle Exit, see § Table 4-75. The Path continues forwarding the Electrical Idle Exit pattern until Electrical Idle is inferred on any lane, or a 48 ms time out occurs. If a 48 ms time out occurs then:
- The RT_LinkUp variable is set to 0 b .
- The Pseudo Port places its Transmitter in Electrical Idle
- The RT_next_data_rate and the RT_error_data_rate must be set to 2.5 GT/s for both Pseudo Ports
- Receiver Detection is performed on the Pseudo Port that was sending the Electrical Idle Exit pattern and timed out, the result is back propagated as described in $\S$ Section 4.3.4.

The Transmitter, on the opposite Pseudo Port that was sending the Electrical Idle Exit Pattern and timed out, sends the Electrical Idle Exit Pattern described above for $5 \mu \mathrm{~s}$.

# IMPLEMENTATION NOTE: ELECTRICAL IDLE EXIT 8 

Forwarding Electrical Idle Exit occurs in error cases where a Retimer is unable to decode training sets. Upstream and Downstream Ports use Electrical Idle Exit (without decoding any Symbols) during Polling.Compliance, and Recovery.Speed. If the Retimer does not forward Electrical Idle Exit then the Upstream and Downstream Ports will misbehave in certain conditions. For example, this may occur after a speed change to a higher data rate. In this event forwarding Electrical Idle Exit is required to keep the Upstream and Downstream Ports in lock step at Recovery.Speed, so that the data rate will return to the previous data rate, rather than a Link Down condition from a time out to Detect.

When a Retimer detects an exit from Electrical Idle and starts forwarding data, the time this takes is called the Retimer Exit Latency, and allows for such things as data rate change (if required), clock and data recovery, Symbol lock, Block Alignment, Lane-to-Lane de-skew, Receiver tuning, etc. The Maximum Retimer Exit Latency is specified below for several conditions:

- The data rate before and after Electrical Idle and Electrical Idle exit detect does not change.
- Data rate change to a data rate that uses $8 \mathrm{~b} / 10 \mathrm{~b}$ encoding.
- Data rate change to a data rate that uses 128b/130b encoding for the first time.
- Data rate change to a data rate that uses 128b/130b encoding not for the first time.
- Data rate change to a data rate that uses $1 \mathrm{~b} / 1 \mathrm{~b}$ encoding for the first time.
- Data rate change to a data rate that uses $1 \mathrm{~b} / 1 \mathrm{~b}$ encoding not for the first time.
- How long both transmitters have been in Electrical Idle when a data rate change occurs.

Retimers are permitted to change their data rate while in Electrical Idle, and it is recommended that Retimers start the data rate change while in Electrical Idle to minimize Retimer Exit latency.

Table 4-74 Maximum Retimer Exit Latency

| Condition | Link in Electrical Idle for $X \mu \mathrm{~s}$, where: |  |
| :-- | :--: | :--: |
|  | $X<500 \mu \mathrm{~s}$ | $X \geq 500 \mu \mathrm{~s}$ |
| No data rate change, $2.5 \mathrm{GT} / \mathrm{s}$ | $8 \mu \mathrm{~s}$ | $8 \mu \mathrm{~s}$ |
| No data rate change, $5.0 \mathrm{GT} / \mathrm{s}$ or higher | $4 \mu \mathrm{~s}$ | $4 \mu \mathrm{~s}$ |

| Condition | Link in Electrical Idle for $X \mu \mathrm{~s}$, where: |  |
| :-- | :--: | :--: |
|  | $X<500 \mu \mathrm{~s}$ | $X \geq 500 \mu \mathrm{~s}$ |
| When forwarding TS1 Ordered Sets at $2.5 \mathrm{GT} / \mathrm{s}$ with Lane and Link number equal to PAD. | 1 ms | 1 ms |
| Any data rate change to $8 \mathrm{~b} / 10 \mathrm{~b}$ encoding data rate | $504-X \mu \mathrm{~s}$ | $4 \mu \mathrm{~s}$ |
| First data rate change to $128 \mathrm{~b} / 130 \mathrm{~b}$ encoding date rate | $1.5-X \mathrm{~ms}$ | 1 ms |
| Subsequent data rate change to $128 \mathrm{~b} / 130 \mathrm{~b}$ encoding date rate | $504-X \mu \mathrm{~s}$ | $4 \mu \mathrm{~s}$ |
| First data rate change to $1 \mathrm{~b} / 1 \mathrm{~b}$ encoding data rate | $1.5-X \mathrm{~ms}$ | 1 ms |
| Subsequent data rate change to $1 \mathrm{~b} / 1 \mathrm{~b}$ encoding data rate | $504-X \mu \mathrm{~s}$ | $4 \mu \mathrm{~s}$ |

# 4.3.6.4 Data Rate Change and Determination Rules 

The data rate of the Retimer is set to $2.5 \mathrm{GT} / \mathrm{s}$ after deassertion of Fundamental Reset.
Both Pseudo Ports of the Retimer must operate at the same data rate. If a Pseudo Port places its Transmitter in Electrical Idle, then the Symbols that it has just completed transmitting determine the variables RT_next_data_rate and RT_error_data_rate. Only when both Pseudo Ports have all Lanes in Electrical Idle shall the Retimer change the data rate. If both Pseudo Ports do not make the same determination of these variables, then both variables must be set to $2.5 \mathrm{GT} / \mathrm{s}$.

- If both Pseudo Ports were forwarding non-training sequences, then the RT_next_data_rate must be set to the current data rate. The RT_error_data_rate must be set to $2.5 \mathrm{GT} / \mathrm{s}$ if $8 \mathrm{~b} / 10 \mathrm{~b}$ or $128 \mathrm{~b} / 130 \mathrm{~b}$ encoding is being used. The RT_error_data_rate is set to $32.0 \mathrm{GT} / \mathrm{s}$ if $1 \mathrm{~b} / 1 \mathrm{~b}$ encoding is being used. Note: this covers the case where the Link has entered L1 from L0.
- If both Pseudo Ports were forwarding TS2 Ordered Sets with the speed_change bit set to 1b and either:
- the data rate, when forwarding those TS2s, is greater than $2.5 \mathrm{GT} / \mathrm{s}$ or,
- the highest common data rate received in the data rate identifiers in both directions is greater than $2.5 \mathrm{GT} / \mathrm{s}$,
then RT_next_data_rate must be set to the highest common data rate and the RT_error_data_rate is set to current data rate. Note: this covers the case where the Link has entered Recovery. Speed from Recovery. RcvrCfg and is changing the data rate according to the highest common data rate.
- Else the RT_next_data_rate must be set to the RT_error_data_rate. The RT_error_data_rate is set to $2.5 \mathrm{GT} / \mathrm{s}$ if $8 \mathrm{~b} / 10 \mathrm{~b}$ or $128 \mathrm{~b} / 130 \mathrm{~b}$ encoding is being used. The RT_error_data_rate is set to $32.0 \mathrm{GT} / \mathrm{s}$ if $1 \mathrm{~b} / 1 \mathrm{~b}$ encoding is being used. Note this covers the two error cases:
- This indicates that the Link was unable to operate at the current data rate (greater than $2.5 \mathrm{GT} / \mathrm{s}$ ) and the Link will operate at either the $2.5 \mathrm{GT} / \mathrm{s}$ data rate or the $32.0 \mathrm{GT} / \mathrm{s}$ data rate or
- This indicates that the Link was unable to operate at the new negotiated data rate and will revert back to the old data rate with which it entered Recovery from L0 or L1.


### 4.3.6.5 Electrical Idle Entry Rules

The Rules for Electrical Idle entry in Forwarding mode are a function of whether the Retimer is forwarding training sets or non-training sets. The determination of this is described in $\S$ Section 4.3.6.1.

Before a Transmitter enters Electrical Idle, it must always send the Electrical Idle Ordered Set Sequence (EIOSQ), unless otherwise specified.

If the Retimer is forwarding training sets then:

- If an EIOS is received on a Lane, then the EIOSQ is forwarded on that Lane and only that Lane places its Transmitter in Electrical Idle.
- If Electrical Idle is inferred on a Lane, then that Lane places its Transmitter in Electrical Idle, after EIOSQ is transmitted on that Lane.

Else if the Retimer is forwarding non-training sets then:

- If operating in Flit Mode and EIOS are received on some Lanes while some other Lanes receive SKP OS (i.e.,L0p Link width down-size), then Lanes that are receiving EIOS must forward the EIOSQ and must place their Transmitters into Electrical Idle. Lanes that are forwarding Symbols, but are not receiving EIOS, must continue forwarding Symbols and must not place their Transmitters into Electrical Idle. Else if an EIOS is received on any Lane, then the EIOSQ is forwarded on all Lanes that are currently forwarding Symbols and all Lanes place their Transmitters in Electrical Idle.
- If Electrical Idle is inferred on a Lane, then that Lane places its Transmitter in Electrical Idle, and EIOSQ is not transmitted on that Lane.
- When operating at 64.0 GT/s, a Retimer must follow the requirements of $\S$ Section 4.2.3.2 in order to identify SKP OS, EIEOS, and EIOS received.

The Retimer is required to infer Electrical Idle. The criteria for a Retimer inferring Electrical Idle are described in § Table $4-75$.

Table 4-75 Inferring Electrical Idle

| State | $2.5 \mathrm{GT} / \mathrm{s}$ | $5.0 \mathrm{GT} / \mathrm{s}$ | $8.0 \mathrm{GT} / \mathrm{s}$ | $16.0 \mathrm{GT} / \mathrm{s}$ or higher |
| :--: | :--: | :--: | :--: | :--: |
| Forwarding: <br> Non Training <br> Sequence | Absence of a SKP <br> Ordered Set in a $128 \mu \mathrm{~s}$ <br> window | Absence of a SKP Ordered <br> Set in a $128 \mu \mathrm{~s}$ window | Absence of a SKP Ordered <br> Set in a $128 \mu \mathrm{~s}$ window | Absence of a SKP Ordered <br> Set in a $128 \mu \mathrm{~s}$ window |
| Forwarding: <br> Training <br> Sequence | Absence of a TS1 or TS2 <br> Ordered Set in a 1280 UI <br> interval | Absence of a TS1 or TS2 <br> Ordered Set in a 1280 UI <br> interval | Absence of a TS1 or TS2 <br> Ordered Set in a 4680 UI <br> interval | Absence of a TS0, TS1, or <br> TS2 Ordered Set in a <br> 4680 UI interval |
| Forwarding: <br> Electrical Idle <br> Exit <br> Executing: <br> Force Timeout | Absence of an exit from <br> Electrical Idle in a 2000 UI <br> interval | Absence of an exit from <br> Electrical Idle in a <br> 16000 UI interval | Absence of an exit from <br> Electrical Idle in a <br> 16000 UI interval | Absence of an exit from <br> Electrical Idle in a 16000 UI <br> interval |
| Forwarding: <br> Loopback <br> Executing: <br> Loopback <br> Follower | Absence of an exit from <br> Electrical Idle in a $128 \mu \mathrm{~s}$ <br> window | N/A | N/A | N/A |

# 4.3.6.6 Transmitter Settings Determination Rules 

When a data rate change to $64.0 \mathrm{GT} / \mathrm{s}$ occurs the Retimer transmitter settings are determined as follows:

- If the RT_G6_EQ_complete variable is set to 1b:
- The Transmitter must use the coefficient settings agreed upon at the conclusion of the last equalization procedure applicable to $64.0 \mathrm{GT} / \mathrm{s}$ operation.
- Else:
- An Upstream Pseudo Port must use the 128b/130b Transmitter preset values it registered from the eight consecutive 128b/130b EQ TS2 Ordered Sets received while operating at $32.0 \mathrm{GT} / \mathrm{s}$ in its Transmitter preset setting as soon as it starts transmitting at the $64.0 \mathrm{GT} / \mathrm{s}$ data rate and must ensure that it meets the preset definition in $\S$ Section 4.2.4.2. Lanes that received a Reserved or unsupported Transmitter preset value must use an implementation specific method to choose a supported Transmitter preset setting for use as soon it starts transmitting at $64.0 \mathrm{GT} / \mathrm{s}$.
- A Downstream Pseudo Port determines its Transmitter Settings in an implementation specific manner when it starts transmitting at $64.0 \mathrm{GT} / \mathrm{s}$.

The RT_G6_EQ_complete variable is set to 1b when:

- Two consecutive TS0 Ordered Sets are received with EC = 01b at $64.0 \mathrm{GT} / \mathrm{s}$.

The RT_G6_EQ_complete variable is set to 0 b when any of the following occur:

- The RT_LinkUp variable is set to 0 b .
- The Pseudo Port is operating at $32.0 \mathrm{GT} / \mathrm{s}$ and eight consecutive 128b/130b EQ TS2 Ordered Sets are received on any Lane of the Upstream Pseudo Port. The value in the 128b/130b Transmitter Preset field is registered for later use at $64.0 \mathrm{GT} / \mathrm{s}$ for that Lane.

When a data rate change to $32.0 \mathrm{GT} / \mathrm{s}$ occurs the Retimer transmitter settings are determined as follows:

- If the RT_G5_EQ_complete variable is set to 1b:
- The Transmitter must use the coefficient settings agreed upon at the conclusion of the last equalization procedure applicable to $32.0 \mathrm{GT} / \mathrm{s}$ operation.
- Else:
- An Upstream Pseudo Port must use the 128b/130b Transmitter preset values it registered from the eight consecutive 128b/130b EQ TS2 Ordered Sets received while operating at $16.0 \mathrm{GT} / \mathrm{s}$ in its Transmitter preset setting as soon as it starts transmitting at the $32.0 \mathrm{GT} / \mathrm{s}$ data rate and must ensure that it meets the preset definition in $\S$ Section 4.2.4.2. Lanes that received a Reserved or unsupported Transmitter preset value must use an implementation specific method to choose a supported Transmitter preset setting for use as soon it starts transmitting at $32.0 \mathrm{GT} / \mathrm{s}$.
- A Downstream Pseudo Port determines its Transmitter Settings in an implementation specific manner when it starts transmitting at $32.0 \mathrm{GT} / \mathrm{s}$.

The RT_G5_EQ_complete variable is set to 1b when:

- Two consecutive TS1 Ordered Sets are received with EC = 01b at $32.0 \mathrm{GT} / \mathrm{s}$.

The RT_G5_EQ_complete variable is set to 0 b when any of the following occur:

- RT_LinkUp variable is set to 0 b.

- The Pseudo Port is operating at 16.0 GT/s and eight consecutive 128b/130b EQ TS2 Ordered Sets are received on any Lane of the Upstream Pseudo Port. The value in the 128b/130b Transmitter Preset field is registered for later use at $32.0 \mathrm{GT} / \mathrm{s}$ for that Lane.

When a data rate change to $16.0 \mathrm{GT} / \mathrm{s}$ occurs the Retimer transmitter settings are determined as follows:

- If the RT_G4_EQ_complete variable is set to 1b:
- The Transmitter must use the coefficient settings agreed upon at the conclusion of the last equalization procedure applicable to $16.0 \mathrm{GT} / \mathrm{s}$ operation.
- Else:
- An Upstream Pseudo Port must use the 128b/130b Transmitter preset values it registered from the received eight consecutive 128b/130b EQ TS2 Ordered Sets in its Transmitter preset setting as soon as it starts transmitting at the $16.0 \mathrm{GT} / \mathrm{s}$ data rate and must ensure that it meets the preset definition in § Section 8.3.3.3. Lanes that received a Reserved or unsupported Transmitter preset value must use an implementation specific method to choose a supported Transmitter preset setting for use as soon it starts transmitting at $16.0 \mathrm{GT} / \mathrm{s}$.
- A Downstream Pseudo Port determines its Transmitter Settings in an implementation specific manner when it starts transmitting at $16.0 \mathrm{GT} / \mathrm{s}$.

The RT_G4_EQ_complete variable is set to 1 b when:

- Two consecutive TS1 Ordered Sets are received with $E C=01 b$ at $16.0 \mathrm{GT} / \mathrm{s}$.

The RT_G4_EQ_complete variable is set to 0 b when any of the following occur:

- The RT_LinkUp variable is set to 0 b.
- Eight consecutive 128b/130b EQ TS2 Ordered Sets are received on any Lane of the Upstream Pseudo Port. The value in the 128b/130b Transmitter Preset field is registered for later use at $16.0 \mathrm{GT} / \mathrm{s}$ for that Lane.

When a data rate change to $8.0 \mathrm{GT} / \mathrm{s}$ occurs the Retimer transmitter settings are determined as follows:

- If the RT_G3_EQ_complete variable is set to 1b:
- The Transmitter must use the coefficient settings agreed upon at the conclusion of the last equalization procedure applicable to $8.0 \mathrm{GT} / \mathrm{s}$ operation.
- Else:
- An Upstream Pseudo Port must use the 8.0 GT/s Transmitter preset values it registered from the received eight consecutive EQ TS2 Ordered Sets in its Transmitter preset setting as soon as it starts transmitting at the $8.0 \mathrm{GT} / \mathrm{s}$ data rate and must ensure that it meets the preset definition in $\S$ Section 8.3.3. Lanes that received a Reserved or unsupported Transmitter preset value must use an implementation specific method to choose a supported Transmitter preset setting for use as soon it starts transmitting at $8.0 \mathrm{GT} / \mathrm{s}$. The Upstream Pseudo Port may optionally use the $8.0 \mathrm{GT} / \mathrm{s}$ Receiver preset hint values it registered in those EQ TS2 Ordered Sets.
- A Downstream Pseudo Port determines its Transmitter preset settings in an implementation specific manner when it starts transmitting at $8.0 \mathrm{GT} / \mathrm{s}$.

The RT_G3_EQ_complete variable is set to 1 b when:

- Two consecutive TS1 Ordered Sets are received with $E C=01 b$ at $8.0 \mathrm{GT} / \mathrm{s}$.

The RT_G3_EQ_complete variable is set to 0 b when any of the following occur:

- The RT_LinkUp variable is set to 0b.
- Eight consecutive EQ TS1 or eight consecutive EQ TS2 Ordered Sets are received on any Lane of the Upstream Pseudo Port. The value in the 8.0 GT/s Transmitter Preset and optionally the 8.0 GT/s Receiver Preset Hint fields are registered for later use at $8.0 \mathrm{GT} / \mathrm{s}$ for that Lane.

When a data rate change to $5.0 \mathrm{GT} / \mathrm{s}$ occurs the Retimer transmitter settings are determined as follows:

- The Upstream Pseudo Port must sets its Transmitters to either -3.5 dB or -6.0 dB , according to the Selectable De-emphasis bit (bit 6 of Symbol 4) received in eight consecutive TS2 Ordered Sets, in the most recent series of TS2 Ordered sets, received prior to entering Electrical Idle.
- The Downstream Pseudo Port sets its Transmitters to either -3.5 dB or -6.0 dB in an implementation specific manner.


# 4.3.6.7 Ordered Set Modification Rules 

Ordered Sets are forwarded, and certain fields are modified according to the following rules:

- The Retimer shall not modify any fields except those specifically allowed/required for modification in this specification.
- Transmitter Precode Request: the Retimer shall overwrite the Transmitter Precode Request field in TS1 and TS2 Ordered Sets in both directions. The new value represents whether one pseudo port is requesting to enable precoding for the current data rate.
- Transmitter Precoding On: the Retimer shall overwrite Transmitter Precoding On field in TS1 Ordered Sets in both directions. The new value represents whether one pseudo port's precoding is on for the current data rate.
- LF: the Retimer shall overwrite the LF field in TS0/TS1 Ordered Sets transmitted in both directions. The new value is determined in an implementation specific manner by the Retimer.
- FS: the Retimer shall overwrite the FS field in TS0/TS1 Ordered Sets transmitted in both directions. The new value is determined in an implementation specific manner by the Retimer.
- Respective Pre-Cursor Coefficients: the Retimer shall overwrite the respective Pre-Cursor Coefficient field in TS0/TS1 Ordered Sets transmitted in both directions. The new value is determined by the current Transmitter settings.
- Cursor Coefficient: the Retimer shall overwrite the Cursor Coefficient field in TS0/TS1 Ordered Sets transmitted in both directions. The new value is determined by the current Transmitter settings.
- Post-Cursor Coefficient: the Retimer shall overwrite the Post-Cursor Coefficient field in the TS0/TS1 Ordered Sets transmitted in both directions. The new value is determined by the current Transmitter settings.
- Parity: the Retimer shall overwrite the Parity bit of forwarded TS0, TS1, TS2, or Modified TS1/TS2 Ordered Sets if it modifies any field used in parity calculation.
- Transmitter Preset: the Retimer shall overwrite the Transmitter Preset field in TS0/TS1 Ordered Sets transmitted in both directions. If the Transmitter is using a Transmitter preset setting then the value is equal to the current setting, else it is recommended that the Transmitter Preset field be set to the most recent Transmitter preset setting that was used for the current data rate.

The Retimer is permitted to do the following:

- overwrite the Transmitter Preset field in EQ TS1 Ordered Sets in either direction
- overwrite the 8.0 GT/s Transmitter Preset field in EQ TS2 Ordered Sets in the Downstream direction.

- overwrite the 128b/130b Transmitter Preset field in 128b/130b EQ TS2 Ordered Sets, in the Downstream direction.

The new values for the 8.0 GT/s Transmitter Preset and 128b/130b Transmitter Preset fields are determined in an implementation specific manner by the Retimer.

During phase 0 of Equalization to 16.0 GT/s (i.e., the current Data Rate is $8.0 \mathrm{GT} / \mathrm{s}$ ), phase 0 of Equalization to $32.0 \mathrm{GT} / \mathrm{s}$ (i.e., the current Data Rate is $16.0 \mathrm{GT} / \mathrm{s}$ ), or phase 0 of Equalization to $64.0 \mathrm{GT} / \mathrm{s}$ (i.e., the current Data Rate is $32.0 \mathrm{GT} / \mathrm{s}$ ) the Retimer is permitted to do the following in the Upstream direction:

- Forward received TS2 Ordered Sets.
- Convert TS2 Ordered Sets to 128b/130b EQ TS2 Ordered Sets, the value for the 128b/130b Transmitter Preset field is determined in an implementation specific manner by the Retimer.
- Forward received 128b/130b EQ TS2 Ordered Sets with modification, the value for the 128b/130b Transmitter Preset field is determined in an implementation specific manner by the Retimer.
- Convert 128b/130b EQ TS2 Ordered Sets to TS2 Ordered Sets.
- Receiver Preset Hint: the Retimer is permitted to do the following:
- overwrite the Receiver Preset Hint field in EQ TS1 Ordered Sets in either direction
- overwrite the 8.0 GT/s Receiver Preset Hint field in EQ TS2 Ordered Sets in the Downstream direction.

The new values, for the Receiver Preset Hint and 8.0 GT/s Receiver Preset Hint fields are determined in an implementation specific manner by the Retimer.

- SKP Ordered Set: The Retimer is permitted to adjust the length of SKP Ordered Sets transmitted in both directions. The Retimer must perform the same adjustment on all Lanes. When operating with 8b/10b encoding, the Retimer is permitted to add or remove one SKP Symbol of a SKP Ordered Set. When operating with 128b/130b encoding, a Retimer is permitted to add or remove 4 SKP Symbols of a SKP Ordered Set. When operating with 1b/1b encoding, only Control SKP Ordered Sets are sent.
- Control SKP Ordered Set: The Retimer must modify the First Retimer Data Parity, or the Second Retimer Data Parity, of the Control SKP Ordered Set when the Retimer is in forwarding mode at $16.0 \mathrm{GT} / \mathrm{s}$ or above, according to its received parity. The received even parity is computed independently on each Lane as follows:
- Parity is initialized when a data rate change occurs.
- Parity is initialized when a SDS Ordered Set is received.
- Parity is updated with each bit of a Data Block's payload before de-scrambling has been performed.
- Parity is initialized when a Control SKP Ordered Set is received. However, parity is NOT initialized when a Standard SKP Ordered Set is received.

If a Pseudo Port detects the Retimer Present bit was 0 b in the most recently received two consecutive TS2 or EQ TS2 Ordered Sets received by that Pseudo Port when operating at $2.5 \mathrm{GT} / \mathrm{s}$ then that Pseudo Port Receiver modifies the First Retimer Data Parity as it forwards the Control SKP Ordered Set, else that Pseudo Port Receiver modifies the Second Retimer Data Parity as it forwards the Control SKP Ordered Set.

The Retimer must modify symbols $4^{*} \mathrm{~N}+1,4^{*} \mathrm{~N}+2$, and $4^{*} \mathrm{~N}+3$ of the Control SKP Ordered Set in the Upstream direction as described in § Section 4.2.18.

See § Section 4.2.8.2 for Control SKP Ordered Set definition.

- When operating with 1b/1b encoding, a Retimer is permitted to add or remove 8 Bytes of SKP at an aligned 8 byte boundary.

- Selectable De-emphasis: the Retimer is permitted to overwrite the Selectable De-emphasis field in the TS1 or TS2 Ordered Set in both directions. The new value is determined in an implementation specific manner by the Retimer.
- The Data Rate Identifier: The Retimer must set the Data Rate Supported bits of the Data Rate Identifier Symbol consistent with the data rates advertised in the received Ordered Sets and its own max supported Data Rate, i.e., it clears to 0 b all Symbol 4 bits[5:0] Data Rates that it does not support. A Retimer must support all data rates below and including its maximum supported data rate. A Retimer makes its determination of maximum supported Data Rate once, after fundamental reset. A Retimer that does not support Flit Mode must set Symbol 4 , bit 0 to 0 b.
- DC Balance: When operating with 128b/130b and 1b/1b encoding, the Retimer tracks the DC Balance of its Pseudo Port transmitters and transmits DC Balance Symbols as described in § Section 4.2.5.1 .
- Retimer Present: When operating at $2.5 \mathrm{GT} / \mathrm{s}$, the Retimer must Set the Retimer Present bit in all forwarded Ordered Sets with a defined Retimer Present bit.
- Two Retimers Present: If the Retimer supports $16.0 \mathrm{GT} / \mathrm{s}$ or higher, then when operating at $2.5 \mathrm{GT} / \mathrm{s}$, the Retimer must Set the Two Retimers Present bit in all forwarded Ordered Sets with a defined Two Retimers Present bit, if it receives an Ordered Set that has a defined Retimer Present bit and the Retimer Present bit is Set. If the Retimer does not support $16.0 \mathrm{GT} / \mathrm{s}$ or higher, then when operating at $2.5 \mathrm{GT} / \mathrm{s}$, the Retimer is permitted to Set the Two Retimers Present bit of all forwarded Ordered Sets with a defined Two Retimers Present bit, if it receives an Ordered Set that has a defined Retimer Present bit and the Retimer Present bit is Set.
- Loopback: When optionally supporting Follower Loopback in Execution mode Loopback_Request must be deasserted when forwarding training sets.
- Enhanced Link Behavior Control: If the Retimer supports $32.0 \mathrm{GT} / \mathrm{s}$ or higher, then when operating at $2.5 \mathrm{GT} / \mathrm{s}$, the Retimer must set the Enhanced Link Behavior Control bits of all forwarded TS1, TS2, EQ TS1 and EQ TS2 Ordered Sets as follows:
- Set to 11b when Retimer supports Modified TS1/TS2 Ordered Sets and the Enhanced Link Behavior Control bits set to 11b in the Ordered Sets received for forwarding.
- Set to 10b when Retimer supports no equalization and the Enhanced Link Behavior Control bits is set to 10 b in the Ordered Sets received for forwarding.
- Set to 01b when Retimer supports Equalization Bypass to Highest NRZ Rate and the Enhanced Link Behavior Control field is set to 01b in the Ordered Sets received for forwarding.
- Otherwise, set to 00b.


# 4.3.6.8 DLLP, TLP, Logical Idle, and Flit Modification Rules 

DLLPs, TLPs, Logical Idle, and Flits are forwarded with no modifications to any of the Symbols unless otherwise specified.

### 4.3.6.9 8b/10b Encoding Rules

The Retimer shall meet the requirements in § Section 4.2.1.1.3 except as follows:

- When the Retimer is forwarding and an 8b/10b decode error or a disparity error is detected in the received data, the Symbol with an error is replaced with the D21.3 Symbol with incorrect disparity in the forwarded data.

# IMPLEMENTATION NOTE: 

## FORWARDING D21.3 SYMBOL WITH INCORRECT DISPARITY 5

Detection of $8 \mathrm{~b} / 10 \mathrm{~b}$ decode errors and disparity errors takes place in the Receiver. Whether replacement of the Symbol in error takes place in the Receiver or in the Transmitter, the Symbol forwarded by the Retimer after Scrambling will be the D21.3 Symbol with incorrect disparity.

- This clause in § Section 4.2.1.1.3 does not apply: If a received Symbol is found in the column corresponding to the incorrect running disparity or if the Symbol does not correspond to either column, the Physical Layer must notify the Data Link Layer that the received Symbol is invalid. This is a Receiver Error, and is a reported error associated with the Port (see § Section 6.2).


## IMPLEMENTATION NOTE: RETIMER TRANSMITTER DISPARITY 6

The Retimer must modify certain fields of the TS1 and TS2 Ordered Sets (e.g., Receiver Preset Hint, Transmitter Preset), therefore the Retimer must recalculate the running disparity. Simply using the disparity of the received Symbol may lead to an error in the running disparity. For example, some 8b/10b codes have 6 ones and 4 zeros for positive disparity, while other codes have 5 ones and 5 zeros.

### 4.3.6.10 8b/10b Scrambling Rules

A Retimer is required to determine if scrambling is disabled when using 8b/10b encoding as described in § Section 4.3.6.2 .

### 4.3.6.11 Hot Reset Rules

If any Lane of the Upstream Pseudo Port receives two consecutive TS1 Ordered Sets with Hot_Reset_Request asserted and then both Pseudo Ports either receive an EIOS or infer Electrical Idle on any Lane, that is receiving TS1 Ordered Sets, the Retimer does the following:

What does "that is receiving TS1 Ordered Sets" mean?
I think this paragraph should be rewritten:
If any Lane of the Upstream Pseudo Port receives two consecutive TS1 Ordered Sets with Hot_Reset_Request asserted followed by both Pseudo Ports either receiving an EIOS or inferring Electrical Idle on any Lane, the Retimer does the following:

- Clears variable RT_LinkUp = 0b.
- Places its Transmitters in Electrical Idle on both Pseudo Ports.
- Set the RT_next_data_rate variable to $2.5 \mathrm{GT} / \mathrm{s}$.
- Set the RT_error_data_rate variable to $2.5 \mathrm{GT} / \mathrm{s}$.
- Waits for an exit from Electrical Idle on any Lane on either Pseudo Port.

The Retimer does not perform Receiver Detection on either Pseudo Port.

# 4.3.6.12 Disable Link Rules 

If any Lane of the Upstream Pseudo Port receives two consecutive TS1 Ordered Sets with Disable_Link_Request asserted and then both Pseudo Ports either receive an EIOS or infer Electrical Idle on any Lane, that is receiving TS1 Ordered Sets, the Retimer does the following:

What does "that is receiving TS1 Ordered Sets" mean?
I think this paragraph should be rewritten:
If any Lane of the Upstream Pseudo Port receives two consecutive TS1 Ordered Sets with Disable_Link_Request asserted followed by both Pseudo Ports either receiving an EIOS or inferring Electrical Idle on any Lane, the Retimer does the following:

- Clears variable RT_LinkUp = 0b.
- Places its Transmitters in Electrical Idle on both Pseudo Ports.
- Set the RT_next_data_rate variable to $2.5 \mathrm{GT} / \mathrm{s}$.
- Set the RT_error_data_rate variable to $2.5 \mathrm{GT} / \mathrm{s}$.
- Waits for an exit from Electrical Idle on any Lane on either Pseudo Port.

The Retimer does not perform Receiver Detection on either Pseudo Port.

### 4.3.6.13 Loopback

The Retimer must operate in Follower Loopback Execution mode when operating at 8b/10b or 128b/130b encoding and any Lane receives two consecutive TS1 Ordered Sets with Loopback_Request asserted and the ability to execute Follower Loopback is configured in an implementation specific way.

The Retimer must operate in Follower Loopback Execution mode when operating at 1b/1b encoding and any Lane receives two consecutive TS1 Ordered Sets with Training Control bits [3:2] set to 01b (Assert Loopback) and with Training Control bits [1:0] matching the RT_number. See $\S$ Section 4.3.7.3 for Follower Loopback in Execution mode.

- When RT_number is 01b, the Retimer represents Pseudo-Ports B and C of the system topology (which are the ports being targeted for Follower Loopback Execution mode when Training Control = 0101b).
- When RT_number is 10b, the Retimer represents Pseudo-Ports D and E of the system topology (which are the ports being targeted for Follower Loopback Execution mode when Training Control = 0110b).

The Retimer follows these additional rules if one of the following conditions is met:

- Any Lane receives two consecutive TS1 Ordered Sets with Loopback_Request asserted and the ability to execute Follower Loopback is not configured in an implementation specific way.
- Retimer is operating at 1b/1b encoding and any Lane receives two consecutive TS1 Ordered Sets with Loopback_Request asserted and the conditions to enable Follower Loopback in Execution mode are not met. The setting does not configure Follower Loopback.

The purpose of these rules is to allow interoperation when a Retimer (or two Retimers) exist between a Loopback Lead and a Loopback Follower

- The Pseudo Port that received the TS1 Ordered Sets with Loopback_Request asserted acts as the Loopback Follower (the other Pseudo Port acts as Loopback Lead). The Upstream Path is defined as the Pseudo Port that is the Loopback Lead to the Pseudo Port that is the Loopback Follower. The other Path is the Downstream Path.
- Once established, if a Lane loses the ability to maintain Symbol Lock or Block alignment, then the Lane must continue to transmit Symbols while in this state.
- When using 8b/10b encoding and Symbol lock is lost, the Retimer must attempt to re-achieve Symbol Lock.
- When using 128b/130b encoding and Block Alignment is lost, the Retimer must attempt to re-achieve Block Alignment via SKP Ordered Sets.
- When using 1b/1b encoding and Block or Flit Alignment is lost, the Retimer must attempt to re-achieve Block and Flit Alignment via SKP Ordered Sets.
- If Loopback was entered while the Link Components were in Configuration.Linkwidth.Start, then determine the highest common data rate of the data rates supported by the Link via the data rates received in two consecutive TS1 Ordered Sets or two consecutive TS2 Ordered Sets on any Lane, that was receiving TS1 or TS2 Ordered Sets, at the time the transition to Forwarding.Loopback occurred. If the current data rate is not the highest common data rate, then:
- Wait for any Lane to receive EIOS, and then place the Transmitters in Electrical Idle for that Path.
- When all Transmitters are in Electrical Idle, adjust the data rate as previously determined.
- If the new data rate is $5.0 \mathrm{GT} / \mathrm{s}$, then the Selectable De-emphasis is determined the same as way as described in § Section 4.2.7.10.1.
- If the new data rate uses $128 \mathrm{~b} / 130 \mathrm{~b}$ or $1 \mathrm{~b} / 1 \mathrm{~b}$ encoding, then the Transmitter preset setting is determined the same as way as described in § Section 4.2.7.10.1 .
- In the Downstream Path; wait for Electrical Idle exit to be detected on each Lane and then start forwarding when two consecutive TS1 Ordered Sets have been received, on a Lane by Lane basis. This is considered the first time to this data rate for the Retimer Exit Latency.
- In the Upstream Path; if Compliance_Receive_Request in the TS1 Ordered Sets that directed the follower to this state was not asserted, then wait for Electrical Idle exit to be detected on each Lane, and start forwarding when two consecutive TS1 Ordered Sets have been received, on a Lane by Lane basis. This is considered the first time to this data rate for the Retimer Exit Latency.
- In the Upstream Path; if Compliance_Receive_Request in the TS1 Ordered Sets that directed the follower to this state was asserted, then wait for Electrical Idle exit to be detected on each Lane, and start forwarding immediately, on a Lane by Lane basis. This is considered the first time to this data rate for the Retimer Exit Latency.
- If four EIOS (one EIOS if the current data rate is $2.5 \mathrm{GT} / \mathrm{s}$ ) are received on any Lane then:
- Transmit eight EIOS on every Lane that is transmitting TS1 Ordered Sets on the Pseudo Port that did not receive the EIOS and place the Transmitters in Electrical Idle.
- When both Pseudo Ports have placed their Transmitters in Electrical Idle then:
- Set the RT_next_data_rate variable to $2.5 \mathrm{GT} / \mathrm{s}$.
- Set the RT_error_data_rate variable to $2.5 \mathrm{GT} / \mathrm{s}$.
- The additional rules for Loopback no longer apply unless the rules for entering this section are met again.

# 4.3.6.14 Compliance Receive Rules 

The Retimer follows these additional rules if any Lane receives eight consecutive TS1 Ordered Sets (or their complement) with Compliance_Receive_Request asserted and Loopback_Request deasserted. The purpose of the following rules is to support Link operation with a Retimer when Compliance_Receive_Requestis asserted and Loopback_Request is deasserted in TS1 Ordered Sets, transmitted by the Upstream or Downstream Port, while the Link is in Polling_Active.

- Pseudo Port A is defined as the first Pseudo Port that receives eight consecutive TS1 Ordered Sets (or their complement) with Compliance_Receive_Request asserted and Loopback_Request deasserted. Pseudo Port B is defined as the other Pseudo Port.
- The Retimer determines the highest common data rate of the Link by examining the data rate identifiers in the TS1 Ordered Sets received on each Pseudo Port, and the maximum data rate supported by the Retimer.
- If the highest common data rate is equal to $5.0 \mathrm{GT} / \mathrm{s}$ then:
- The Retimer must change its data rate to $5.0 \mathrm{GT} / \mathrm{s}$ as described in $\S$ Section 4.3.6.4 .
- The Retimer Pseudo Port A must set its de-emphasis according to the selectable de-emphasis bit received in the eight consecutive TS1 Ordered Sets.
- The Retimer Pseudo Port B must set its de-emphasis in an implementation specific manner.
- If the highest common data rate is equal to $8.0 \mathrm{GT} / \mathrm{s}$ or higher then:
- The Retimer must change its data rate to as applicable, as described in $\S$ Section 4.3.6.4 .
- Lane numbers are determined as described in $\S$ Section 4.2.12 .
- The Retimer Pseudo Port A must set its Transmitter coefficients on each Lane to the Transmitter preset value advertised in Symbol 6 of the eight consecutive TS1 Ordered Sets and this value must be used by the Transmitter (use of the Receiver preset hint value advertised in those TS1 Ordered Sets is optional). If the common data rate is $8.0 \mathrm{GT} / \mathrm{s}$ or higher, any Lanes that did not receive eight consecutive TS1 Ordered Sets with Transmitter preset information can use any supported Transmitter preset setting in an implementation specific manner.
- The Retimer Pseudo Port B must set its Transmitter and Receiver equalization in an implementation specific manner.
- The Retimer must forward the Modified Compliance Pattern when it has locked to the pattern. This occurs independently on each Lane in each direction. If a Lane's Receiver loses Symbol Lock or Block Alignment, the associated Transmitter (i.e., same Lane on opposite Pseudo Port) Continues to forward data.
- Once locked to the pattern, the Retimer keeps an internal count of received Symbol errors, on a per-Lane basis. The pattern lock and Lane error is permitted to be readable in an implementation specific manner, on a per-Lane basis.
- When operating with 128b/130b or 1b/1b encoding, Symbols with errors are forwarded unmodified by default, or may optionally be corrected to remove error pollution. The default behavior must be supported and the method of selecting the optional behavior, if supported, is implementation specific.
- When operating with 8b/10b encoding, Symbols with errors are replaced with the D21.3 Symbol with incorrect disparity by default, or may optionally be corrected to remove error pollution. The default behavior must be supported and the method of selecting the optional behavior, if supported, is implementation specific.
- The error status Symbol when using 8b/10b encoding or the Error_Status field when using 128b/130b or 1b/1b encoding is forwarded unmodified by default, or may optionally be redefined as it is transmitted by the Retimer. The default behavior must be supported and the method of selecting the optional behavior, if supported, is implementation specific.

- If any Lane receives an EIOS on either Pseudo Port then:
- Transmit EIOSQ on every Lane of the Pseudo Port that did not receive EIOS and place the Transmitters in Electrical Idle. Place the Transmitters of the other Pseudo Port in Electrical Idle; EIOS is not transmitted by the other Pseudo Port.
- Set the RT_next_data_rate variable to $2.5 \mathrm{GT} / \mathrm{s}$.
- Set the RT_error_data_rate variable to $2.5 \mathrm{GT} / \mathrm{s}$.
- The Compliance Receive additional rules no longer apply unless the rules for entering this section are met again.


# 4.3.6.15 Enter Compliance Rules 

The Retimer follows these additional rules if the Retimer is exiting Electrical Idle after entering Electrical Idle as a result of Hot Reset, and the Retimer Enter Compliance bit is Set in the Retimer. The purpose of the following rules is to support Link operation with a Retimer when the Link partners enter compliance as a result of the Enter Compliance bit in the Link Control 2 Register set to 1 b in both Link Components and a Hot Reset occurring on the Link. Retimers do not support Link operation if the Link partners enter compliance when they exit detect if the entry into detect was not caused by a Hot Reset.

Retimers must support the following register fields in an implementation specific manner:

- Retimer Target Link Speed
- One field per Retimer
- Type $=$ RWS
- Size $=3$ bits
- Default $=001 b$
- Encoding:
- $001 b=2.5 \mathrm{GT} / \mathrm{s}$
- $010 b=5.0 \mathrm{GT} / \mathrm{s}$
- $011 b=8.0 \mathrm{GT} / \mathrm{s}$
- $100 b=16.0 \mathrm{GT} / \mathrm{s}$
- $101 b=32.0 \mathrm{GT} / \mathrm{s}$
- $110 b=64.0 \mathrm{GT} / \mathrm{s}$
- Retimer Transmit Margin
- One field per Pseudo Port
- Type $=$ RWS
- Size $=3$ bits
- Default $=000 b$
- Encoding:
- $000 b=$ Normal Operating Range
- 001b-111b = As defined in § Section 8.3.4, not all encodings are required to be implemented
- Retimer Enter Compliance
- One bit per Retimer

- Type $=$ RWS
- Size $=1$ bit
- Default $=0 b$
- Encoding:
- $0 b=$ do not enter compliance
- $1 b=$ enter compliance
- Retimer Enter Modified Compliance
- One bit per Retimer
- Type $=$ RWS
- Size $=1$ bit
- Default $=0 b$
- Encoding:
- $0 b=$ do not enter modified compliance
- $1 b=$ enter modified compliance
- Retimer Compliance Preset/De-emphasis
- One field per Pseudo Port
- Type $=$ RWS
- Size $=4$ bits
- Default $=0000 b$
- Encoding when Retimer Target Link Speed is 5.0 GT/s:
- 0000b -6.0 dB
- 0001b -3.5 dB
- Encoding when Retimer Target Link Speed is 8.0 GT/s or higher: the Transmitter Preset.

A Retimer must examine the values in the above registers when the Retimer exits from Hot Reset. If the Retimer Enter Compliance bit is Set the following rules apply:

- The Retimer adjusts its data rate as defined by Retimer Target Link Speed. No data is forwarded until the data rate change has occurred.
- The Retimer configures its Transmitters according to Retimer Compliance Preset/De-emphasis on a per Pseudo Port basis.
- The Retimer must forward the Compliance or Modified Compliance Pattern when it has locked to the pattern. The Retimer must search for the Compliance Pattern if the Retimer Enter Modified Compliance bit is Clear or search for the Modified Compliance Pattern if the Retimer Enter Modified Compliance bit is Set. This occurs independently on each Lane in each direction.
- When using 8b/10b encoding, a particular Lane's Receiver independently determines a successful lock to the incoming Modified Compliance Pattern or Compliance Pattern by looking for any one occurrence of the Modified Compliance Pattern or Compliance Pattern.
- An occurrence is defined above as the sequence of 8b/10b Symbols defined in § Section 4.2.9.
- In the case of the Modified Compliance Pattern, the error status Symbols are not to be used for the lock process since they are undefined at any given moment.
- Lock must be achieved within 1.0 ms of receiving the Modified Compliance Pattern.

- When using 128b/130b or 1b/1b encoding each Lane determines Pattern Lock independently when it achieves Block Alignment as described in § Section 4.2.2.2.1 .
- Lock must be achieved within 1.5 ms of receiving the Modified Compliance Pattern or Compliance Pattern.
- When 128b/130b or 1b/1b encoding is used, Symbols with errors are forwarded unmodified by default, or may optionally be corrected to remove error pollution. The default behavior must be supported and the method of selecting the optional behavior, if supported, is implementation specific.
- When 8b/10b encoding is used, Symbols with errors are replaced with the D21.3 Symbol with incorrect disparity by default, or may optionally be corrected to remove error pollution. The default behavior must be supported.
- Once locked, the Retimer keeps an internal count of received Symbol errors, on a per-Lane basis. If the Retimer is forwarding the Modified Compliance Pattern then the error status Symbol when using 8b/10b encoding or the Error_Status field when using 128b/130b encoding is forwarded unmodified by default, or may optionally be redefined as it is transmitted by the Retimer. The default behavior must be supported and the method of selecting the optional behavior, if supported, is implementation specific. The Retimer is permitted to make the pattern lock and Lane error information available in an implementation specific manner, on a per-Lane basis.
- If an EIOS is received on any Lane then:
- All Lanes in that direction transmit 8 EIOS and then all Transmitters in that direction are placed in Electrical Idle.
- When both directions have sent 8 EIOS and placed their Transmitters in Electrical Idle the data rate is changed to $2.5 \mathrm{GT} / \mathrm{s}$.
- Set the RT_next_data_rate variable to $2.5 \mathrm{GT} / \mathrm{s}$.
- Set the RT_error_data_rate variable to $2.5 \mathrm{GT} / \mathrm{s}$.
- The Retimer Enter Compliance bit and Retimer Enter Modified Compliance bit are both set to 0b.
- The above additional rules no longer apply unless the rules for entering this section and clause are met again.


# 4.3.7 Execution Mode Rules 

In Execution mode, Retimers directly control all information transmitted by the Pseudo Ports rather than forwarding information.

### 4.3.7.1 CompLoadBoard Rules

While the Retimer is in the CompLoadBoard (Compliance Load Board) state both Pseudo Ports are executing the protocol as regular Ports, generating Symbols as specified in the following sub-sections on each Port, rather than forwarding from one Pseudo Port to the other.

Retimers must support the following register field in an implementation specific manner:

- Retimer Compliance SOS
- One bit per Retimer
- Type = RWS
- Size $=1$ bit
- Default $=0 b$

- Encoding:
- $0 b=$ Send no SKP Ordered Sets between sequences when sending the Compliance Pattern or Modified Compliance Pattern with 8b/10b encoding.
- $1 b=$ Send two SKP Ordered Sets between sequences when sending the Compliance Pattern with 8b/10b encoding.


# IMPLEMENTATION NOTE: PASSIVE LOAD ON TRANSMITTER 

This state is entered when a passive load is placed on one Pseudo Port, and the other Pseudo Port is receiving traffic.

### 4.3.7.1.1 CompLoadBoard.Entry

- RT_LinkUp = 0b.
- The Pseudo Port that received Compliance Pattern (Pseudo Port A) does the following:
- The data rate remains at $2.5 \mathrm{GT} / \mathrm{s}$.
- The Transmitter is placed in Electrical Idle.
- The Receiver ignores incoming Symbols.
- The other Pseudo Port (Pseudo Port B) does the following:
- The data rate remains at $2.5 \mathrm{GT} / \mathrm{s}$.
- The Transmitter is placed in Electrical Idle. Receiver Detection is performed on all Lanes as described in § Section 8.4.5.7.
- The Receiver ignores incoming Symbols.
- If Pseudo Port B's Receiver Detection determines there are no Receivers attached on any Lanes, then the next state for both Pseudo Ports is CompLoadBoard.Exit.
- Else the next state for both Pseudo Ports is CompLoadBoard.Pattern.


### 4.3.7.1.2 CompLoadBoard.Pattern

When The Retimer enters CompLoadBoard.Pattern the following occur:

- Pseudo Port A does the following:
- The Transmitter remains in Electrical Idle.
- The Receiver ignores incoming Symbols.
- Pseudo Port B does the following:
- The Transmitter sends out the Compliance Pattern on all Lanes that detected a Receiver at the data rate and de-emphasis/preset level determined as described in § Section 4.2.7.2.2, (i.e., each consecutive entry into CompLoadBoard advances the pattern), except that the Setting is not set to Setting \#1 during Polling.Configuration. Setting \#26 and later are not used if Pseudo Port B has received a TS1 or TS2 Ordered Set (or their complement) since the exit of Fundamental Reset. If the

new data rate is not $2.5 \mathrm{GT} / \mathrm{s}$, the Transmitter is placed in Electrical Idle prior to the data rate change. The period of Electrical Idle must be greater than 1 ms but it is not to exceed 2 ms .

- If using 8b/10b encoding and the Retimer Compliance SOS bit (see § Section 4.3.6.15) is Set, send two SKP Ordered Sets between sequences of the Compliance Pattern.
- If Pseudo Port B detects an Electrical Idle exit of any Lane that detected a Receiver, then the next state for both Pseudo Ports is CompLoadBoard.Exit.


# 4.3.7.1.3 CompLoadBoard.Exit 

When The Retimer enters CompLoadBoard.Exit the following occur:

- The Pseudo Port A:
- Data rate remains at $2.5 \mathrm{GT} / \mathrm{s}$.
- The Transmitter sends the Electrical Idle Exit pattern described in § Section 4.3.6.3, on the Lane(s) where Electrical Idle exit was detected on Pseudo Port B for 1 ms . Then the Transmitter is placed in Electrical Idle.
- The Receiver ignores incoming Symbols.
- Pseudo Port B:
- If the Transmitter is transmitting at a rate other than $2.5 \mathrm{GT} / \mathrm{s}$ the Transmitter sends eight consecutive EIOS.
- The Transmitter is placed in Electrical Idle. If the Transmitter was transmitting at a rate other than $2.5 \mathrm{GT} / \mathrm{s}$ the period of Electrical Idle must be at least 1.0 ms .
- Data rate is changed to $2.5 \mathrm{GT} / \mathrm{s}$, if not already at $2.5 \mathrm{GT} / \mathrm{s}$.
- Both Pseudo Ports are placed in Forwarding mode.


## IMPLEMENTATION NOTE: TS1 ORDERED SETS IN FORWARDING MODE

Once in Forwarding mode one of two things will likely occur:

- TS1 Ordered Sets are received and forwarded from Pseudo Port's B Receiver to Pseudo Port's A Transmitter. Link training continues.
- Or: TS1 Ordered Sets are not received because 100 MHz pulses are being received on a lane from the compliance load board, advancing the Compliance Pattern. In this case the Retimer must transition from Forwarding mode to CompLoadBoard when the device attached to Pseudo Port A times out from Polling.Active to Polling.Compliance. The Retimer advances the Compliance Pattern on each entry to CompLoadBoard.


### 4.3.7.2 Link Equalization Rules

When in the Execution mode performing Link Equalization, the Pseudo Ports act as regular Ports, generating Symbols on each Port rather than forwarding from one Pseudo Port to the other. When the Retimer is in Execution mode it must use the Lane and Link numbers stored in RT_captured_lane_number and RT_captured_link_number.

This mode is entered while the Upstream and Downstream Ports on the Link are in negotiation to enter Phase 2 of the Equalization procedure following the procedure for switching to Execution mode described in § Section 4.3.5 .

# 4.3.7.2.1 Downstream Lanes 

The LF and FS values received in two consecutive TS0 or TS1 Ordered Sets when the Upstream Port is in Phase 1 must be stored for use during Phase 3, if the Downstream Pseudo Port wants to adjust the Upstream Port's Transmitter.

### 4.3.7.2.1.1 Phase 1

Transmitter behaves as described in § Section 4.2.7.4.2.1.1 except as follows:

- If the data rate of operation is $64.0 \mathrm{GT} / \mathrm{s}$ or above, the Retimer Equalization Extend bit of the transmitted TS0 Ordered Sets is set to 1 b when the Upstream Pseudo Port state is Phase 0 . The EC field is initially set to 00 b . After two consecutive TS0 Ordered Sets are received with Retimer Equalization Extend bit set to 0b, the EC field is set to 01b. The Retimer Equalization Extend bit of the transmitted TS0 Ordered Sets it is set to 0 b when the Upstream Pseudo Port state is Phase 1. The 24 ms timeout is decreased to 22 ms .


### 4.3.7.2.1.2 Phase 2

Transmitter behaves as described in § Section 4.2.7.4.2.1.2 except as follows:

- If the data rate of operation is $16.0 \mathrm{GT} / \mathrm{s}$ or above, the Retimer Equalization Extend bit of the transmitted TS1 Ordered Sets is set to 1 b when the Upstream Pseudo Port state is Phase 2 Active, and it is set to 0 b when the Upstream Pseudo Port state is Phase 2 Passive.
- Next phase is Phase 3 Active if all configured Lanes receive two consecutive TS1 Ordered Sets with EC=11b.
- Else, if the data rate of operation is less than $64.0 \mathrm{GT} / \mathrm{s}$ : next state is Force Timeout after a 32 ms timeout with a tolerance of -0 ms and +4 ms .
- Else, if the data rate of operation is $64.0 \mathrm{GT} / \mathrm{s}$ : next state is Force Timeout after a 64 ms timeout with a tolerance of -0 ms and +4 ms .


### 4.3.7.2.1.3 Phase 3 Active

If the data rate of operation is $8.0 \mathrm{GT} / \mathrm{s}$ then the transmitter behaves as described in § Section 4.2.7.4.2.1.3 except the 24 ms timeout is 2.5 ms and as follows:

- Next phase is Phase 3 Passive if all configured Lanes are operating at their optimal settings.
- Else, next state is Force Timeout after a timeout of 2.5 ms with a tolerance of -0 ms and +0.1 ms

If the data rate of operation is $16.0 \mathrm{GT} / \mathrm{s}$ or $32.0 \mathrm{GT} / \mathrm{s}$ then the transmitter behaves as described in § Section 4.2.7.4.2.1.3 except the 24 ms timeout is 22 ms and as follows:

- The Retimer Equalization Extend bit of transmitted TS1 Ordered Sets is set to 0b.
- Next phase is Phase 3 Passive if all configured Lanes are operating at their optimal settings and all configured Lanes receive two consecutive TS1 Ordered Sets with the Retimer Equalization Extend bit set to 0b.
- Else, next state is Force Timeout after a timeout of 22 ms with a tolerance of -0 ms and +1.0 ms .

If the data rate of operation is 64.0 GT/s then the transmitter behaves as described in § Section 4.2.7.4.2.1.3 except the 48 ms timeout is 46 ms and as follows:

- The Retimer Equalization Extend bit of transmitted TS0 or TS1 Ordered Sets is set to 0b.
- Next phase is Phase 3 Passive if all configured Lanes are operating at their optimal settings and all configured Lanes receive two consecutive TS1 Ordered Sets with the Retimer Equalization Extend bit set to 0b.
- Else, next state is Force Timeout after a timeout of 46 ms with a tolerance of -0 ms and +1.0 ms .


# 4.3.7.2.1.4 Phase 3 Passive 

- Transmitter sends TS1 Ordered Sets with EC = 11b, Retimer Equalization Extend = 0b, and the Transmitter Preset field and the Coefficients fields must not be changed from the final value transmitted in Phase 3 Active.
- The transmitter switches to Forwarding mode when the Upstream Pseudo Port exits Phase 3.


### 4.3.7.2.2 Upstream Lanes

The LF and FS values received in two consecutive TS0/TS1 Ordered Sets when the Downstream Port is in Phase 1 must be stored for use during Phase 2, if the Upstream Pseudo Port wants to adjust the Downstream Port's Transmitter.

### 4.3.7.2.2.1 Phase 0

Transmitter follows Phase 0 rules for Upstream Lanes in § Section 4.2.7.4.2.2.1 except as follows:

- If the data rate of operation is 64.0 GT/s or above, the Retimer Equalization Extend bit of the transmitted TS0 Ordered Sets is set to 1 b when the Downstream Pseudo Port state is Phase 1 and is transmitting TS0 Ordered Sets with the EC = 00b otherwise it is set to 0 b ; the 12 ms timeout is 10 ms .


### 4.3.7.2.2.2 Phase 1 Active

Transmitter follows Phase 1 rules for Upstream Lanes in § Section 4.2.7.4.2.2.2.

### 4.3.7.2.2.3 Phase 2 Active

If the data rate of operation is 8.0 GT/s then the transmitter behaves as described in § Section 4.2.7.4.2.2.3 except the 24 ms timeout is decreased to 2.5 ms and as follows:

- Next state is Phase 2 Passive if all configured Lanes are operating at their optimal settings.
- Else, next state is Force Timeout after a 2.5 ms timeout with a tolerance of -0 ms and +0.1 ms

If the data rate of operation is $16.0 \mathrm{GT} / \mathrm{s}$ or $32.0 \mathrm{GT} / \mathrm{s}$ then the transmitter behaves as described in § Section 4.2.7.4.2.2.3 except the 24 ms timeout is 22 ms and as follows:

- The Retimer Equalization Extend bit of transmitted TS1 Ordered Sets is set to 0b.
- Next phase is Phase 2 Passive if all configured Lanes are operating at their optimal settings and all configured Lanes receive two consecutive TS1 Ordered Sets with the Retimer Equalization Extend bit set to 0b.

- Else, next state is Force Timeout after a 22 ms timeout with a tolerance of -0 ms and +1.0 ms .

If the data rate of operation is 64.0 GT/s then the transmitter behaves as described in $\S$ Section 4.2.7.4.2.2.3 except the 48 ms timeout is 46 ms and as follows:

- The Retimer Equalization Extend bit of transmitted TSO Ordered Sets is set to 0b.
- Next phase is Phase 2 Passive if all configured Lanes are operating at their optimal settings and all configured Lanes receive two consecutive TS1 Ordered Sets with the Retimer Equalization Extend bit set to 0b.
- Else, next state is Force Timeout after a 46 ms timeout with a tolerance of -0 ms and +1.0 ms .


# 4.3.7.2.2.4 Phase 2 Passive 

- Transmitter sends TSO Ordered Sets with EC = 10b, Retimer Equalization Extend = 0b, and the Transmitter Preset field and the Coefficients fields must not be changed from the final value transmitted in Phase 2 Active.
- If the data rate of operation is $8.0 \mathrm{GT} / \mathrm{s}$, the next state is Phase 3 when the Downstream Pseudo Port has completed Phase 3 Active.
- If the data rate of operation is $16.0 \mathrm{GT} / \mathrm{s}$ or above, the next state is Phase 3 when the Downstream Pseudo Port has started Phase 3 Active.


### 4.3.7.2.2.5 Phase 3

Transmitter follows Phase 3 rules for Upstream Lanes in § Section 4.2.7.4.2.2.4 except as follows:

- If the data rate of operation is $16.0 \mathrm{GT} / \mathrm{s}$ or above, the Retimer Equalization Extend bit of the transmitted TS1 Ordered Sets is set to 1 b when the Downstream Pseudo Port state is Phase 3 Active, and it is set to 0 b when the Downstream Pseudo Port state is Phase 3 Passive.
- If all configured Lanes receive two consecutive TS1 Ordered Sets with EC=00b then the Retimer switches to Forwarding mode.
- Else, if the data rate of operation is less than $64.0 \mathrm{GT} / \mathrm{s}$ : next state is Force Timeout after a timeout of 32 ms with a tolerance of -0 ms and +4 ms .
- Else, if the data rate of operation is $64.0 \mathrm{GT} / \mathrm{s}$ : next state is Force Timeout after a timeout of 64 ms with a tolerance of -0 ms and +4 ms .


### 4.3.7.2.3 Force Timeout

- The Electrical Idle Exit Pattern described in $\S$ Section 4.3.6.3 is transmitted by both Pseudo Ports at the current data rate for a minimum of 1.0 ms .
- If on any Lane, a Receiver receives an EIOS or infers Electrical Idle via not detecting an exit from Electrical Idle (see § Table 4-75) then, the Transmitters on all Lanes of the opposite Pseudo Port send an EIOSQ and are then placed in Electrical Idle.
- If both Paths have placed their Transmitters in Electrical Idle then, the RT_next_data_rate is set to the RT_error_data_rate, and the RT_error_data_rate is set to $2.5 \mathrm{GT} / \mathrm{s}$, on both Pseudo Ports, and the Retimer enters Forwarding mode.
- The Transmitters of both Pseudo Ports must be in Electrical Idle for at least $6 \mu \mathrm{~s}$, before forwarding data.

- Else after a 96 ms timeout, the RT_next_data_rate is set to $2.5 \mathrm{GT} / \mathrm{s}$ and the RT_error_data_rate is set to $2.5 \mathrm{GT} /$ s, on both Pseudo Ports, and the Retimer enters Forwarding mode.


# IMPLEMENTATION NOTE: <br> PURPOSE OF FORCE TIMEOUT STATE 6 

The purpose of this state is to ensure both Link Components are in Recovery.Speed at the same time so they go back to the previous data rate.

### 4.3.7.3 Follower Loopback 

Retimers optionally support Follower Loopback in Execution mode at 8b/10b and 128b/130b encoding. Follower Loopback in Execution mode must be supported at 1b/1b. By default, Retimers are configured to forward loopback between Loopback Lead and Loopback Follower. At 8b/10b and 128b/130b, Retimers are permitted to allow configuration in an implementation specific manner to act as a Loopback Follower on either Pseudo Port; at 1b/1b Loopback Follower on either Pseudo Port is mandatory. The other Pseudo Port that is not the Loopback Follower, places its Transmitter in Electrical Idle, and ignores any data on its Receivers.

### 4.3.7.3.1 Follower Loopback.Entry

The Pseudo Port that is not operating as the Loopback Follower does the following:

- The Transmitter is placed in Electrical Idle.
- The Receiver ignores incoming Symbols.

The Pseudo Port that is operating as the Loopback Follower behaves as the Loopback Follower as described in § Section 4.2.7.10.1 with the following exceptions:

- The statement "LinkUp = 0b (False)" is replaced by "RT_LinkUp = 0b".
- The statement "If Loopback.Entry was entered from Configuration.Linkwidth.Start" is replaced by "If Follower.Loopback.Entry was entered when RT_LinkUp =0b".
- References to Loopback.Active become Follower Loopback.Active.


### 4.3.7.3.2 Follower Loopback.Active 

The Pseudo Port that is not operating as the Loopback Follower does the following:

- The Transmitter remains in Electrical Idle.
- The Receiver continues to ignore incoming Symbols.

The Pseudo Port that is operating the Loopback Follower behaves as the Loopback Follower as described in § Section 4.2.7.10.2 with the following exception:

- References to Loopback.Exit become Follower Loopback.Exit.

# 4.3.7.3.3 Follower Loopback.Exit 

The Pseudo Port that is not operating as the Loopback Follower must do the following:

- Maintain the Transmitter in Electrical Idle.
- Set the data rate to $2.5 \mathrm{GT} / \mathrm{s}$.
- The Receiver continues to ignore incoming Symbols.

The Pseudo Port that is operating as the Loopback Follower must behave as the Loopback Follower as described in § Section 4.2.7.10.3 with the following exception:

- The clause "The next state of the Loopback Lead and Loopback Follower is Detect" becomes "The Data rate is set to $2.5 \mathrm{GT} / \mathrm{s}$ and then both Pseudo Ports are placed in Forwarding mode".


### 4.3.8 Retimer Latency

This Section defines the requirements on allowed Retimer Latency.

### 4.3.8.1 Measurement

Latency must be measured when the Retimer is in Forwarding mode and the Link is in LO, and is defined as the time from when the last bit of a Symbol is received at the input pins of one Pseudo Port to when the equivalent bit is transmitted on the output pins of the other Pseudo Port.

Retimer vendors are strongly encouraged to specify the latency of the Retimer in their data sheets.
Retimers are permitted to have different latencies at different data rates, and when this is the case the latency MUST@FLIT be specified per data rate.

### 4.3.8.2 Maximum Limit on Retimer Latency

Retimer latency shall be less than the following limit, when not operating in SRIS.
Table 4-76 Retimer Latency Limit not SRIS (Symbol times)

|  | $2.5 \mathrm{GT} / \mathrm{s}$ | $5.0 \mathrm{GT} / \mathrm{s}$ | $8.0 \mathrm{GT} / \mathrm{s}$ | $16.0 \mathrm{GT} / \mathrm{s}$ | $32.0 \mathrm{GT} / \mathrm{s}$ | $64.0 \mathrm{GT} / \mathrm{s}$ |
| :--: | :--: | :--: | :--: | :--: | :--: | :--: |
| Maximum Latency | 32 | 32 | 64 | 128 | 256 | 512 |

### 4.3.8.3 Impacts on Upstream and Downstream Ports

Retimers will add to the channel latency. The round trip delay is 4 times the specified latency when two Retimers are present. It is recommended that designers of Upstream and Downstream Ports consider Retimer latency when determining the following characteristics:

- Data Link Layer Retry Buffer size
- Transaction Layer Receiver buffer size and Flow Control Credits

- Data Link Layer REPLAY_TIMER Limits

Additional buffering (replay or FC ) may be required to compensate for the additional channel latency.

# 4.3.9 SRIS 

Retimers are permitted but not required to support SRIS. Retimers that support SRIS must provide a mechanism for enabling the higher rate of SKP Ordered Set transmission, as Retimers must generate SKP Ordered Sets while in Execution mode. Retimers that are enabled to support SRIS will incur additional latency in the elastic store between receive and transmit clock domains. The additional latency is required to handle the case where a Tx_MPS_Limit TLP is transmitted and SKP Ordered Sets, which are scheduled, are not sent. The additional latency is a function of Link width and Max_Payload_Size. This additional latency is not included in $\S$ Table 4-76.

A SRIS capable Retimer must provide an implementation specific mechanism to configure its supported Max_Payload_Size while in SRIS, which must be greater than or equal to the largest Tx_MPS_Limit for the Transmitter in the Port that the Pseudo Port is receiving. Retimer latency must be less than the following limit for the current supported Max_Payload_Size, with SRIS.

Table 4-77 Retimer Latency Limit SRIS (Symbol times)

| Max_Payload_Size | $2.5 \mathrm{GT} / \mathrm{s}$ | $5.0 \mathrm{GT} / \mathrm{s}$ | $8.0 \mathrm{GT} / \mathrm{s}$ | $16.0 \mathrm{GT} / \mathrm{s}$ | $32.0 \mathrm{GT} / \mathrm{s}$ | $64.0 \mathrm{GT} / \mathrm{s}$ |
| :--: | :--: | :--: | :--: | :--: | :--: | :--: |
| 128 Bytes | 34 (max) | 34 (max) | 66 (max) | 130 (max) | 258 (max) | 514 (max) |
| 256 Bytes | 36 (max) | 36 (max) | 68 (max) | 132 (max) | 260 (max) | 516 (max) |
| 512 Bytes | 39 (max) | 39 (max) | 71 (max) | 135 (max) | 263 (max) | 519 (max) |
| 1024 Bytes | 46 (max) | 46 (max) | 78 (max) | 142 (max) | 270 (max) | 526 (max) |
| 2048 Bytes | 59 (max) | 59 (max) | 91 (max) | 155 (max) | 283 (max) | 539 (max) |
| 4096 Bytes | 86 (max) | 86 (max) | 118 (max) | 182 (max) | 310 (max) | 566 (max) |

# IMPLEMENTATION NOTE: RETIMER LATENCY WITH SRIS CALCULATION: § 

§ Table 4-77 is calculated assuming that the link is operating at $\times 1$ Link width. The max Latency is the sum of § Table 4-76 and the additional latency required in the elastic store for SRIS clock compensation. The SRIS additional latency in symbol times required for SRIS clock compensation is described in the following equation:
![img-79.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-79.jpeg)

Equation 4-3 Retimer Latency with SRIS

Where:

## SRIS Link Payload Size

is the value programmed in the Retimer.

## TLP Overhead

Represents the additional TLP components which consume Link bandwidth (TLP Prefix, header, LCRC, framing Symbols) and is treated here as a constant value of 28 Symbols.

## Link Width

The operating width of the Link.

## SKP_rate

The rate that a transmitter schedules SKP Ordered Sets when using 8b/10b encoding, 154, see § Section 4.2.8.4. When using the 128b/130b encoding the effective rate is the same.

The nominal latency would be $1 / 2$ of the SRIS additional latency, and is the nominal fill of the elastic store. This makes a worse case assumption that every blocked SKP Ordered Set requires an additional symbol of latency in the elastic store. When an Rx_MPS_Limit size TLP is transmitted, the actual fill of the elastic store could go to zero, or two times the nominal fill depending on the relative clock frequencies. Link width down configure may occur at any time, a lane fails for example, and this down configure may occur faster than the Retimer is able to adjust its nominal elastic store. By default Retimer's will configure its nominal fill based on $\times 1$ link width, regardless of the actual current link width.

Retimers that optionally support SRIS, may optionally support a dynamic elastic store. Dynamic elastic store changes the nominal buffer fill as the link width changes. Retimers are permitted to delay the Link LTSSM transitions, only while the Link down configures, in Configuration, for up to $40 \mu \mathrm{~s}$. Retimers are permitted to delay the TS1 Order Set to TS2 Ordered Set transition between Configuration.Lanenum.Accept and Configuration.Complete to increase their elastic store.

# 4.3.10 L1 PM Substates Support 

The following Section describes the Retimer's requirements to support the optional L1 PM Substates.
The Retimer enters L1.1 when CLKREQ\# is sampled as deasserted. The following occur:

- REFCLK to the Retimer is turned off.
- The PHY remains powered.
- The Retimer places all Transmitters in Electrical Idle on both Pseudo Ports (if not already in Electrical Idle, the expected state). Transmitters maintain their common mode voltage.
- The Retimer must ignore any Electrical Idle exit from all Receivers on both Pseudo Ports.

The Retimer exits L1.1 when CLKREQ\# is sampled as asserted. The following occur:

- REFCLK to the Retimer is enabled.
- Normal operation of the Electrical Idle exit circuit is resumed on all Lanes of both Pseudo Ports of the Retimer.
- Normal exit from Electrical Idle exit behavior is resumed, See § Section 4.3.6.3 .

Retimers do not support L1.2, but if they support L1.1 and the removal of the reference clock then they must not interfere with the attached components' ability to enter L1.2.

Retimer vendors must document specific implementation requirements applying to CLKREQ\#. For example, a Retimer implementation that does not support the removal of the reference clock might require an implementation to pull CLKREQ\# low.

# IMPLEMENTATION NOTE: CLKREQ\# CONNECTION TOPOLOGY WITH A RETIMER SUPPORTING L1 PM SUBSTATES 6 

In this platform configuration Downstream Port (A) has only a single CLKREQ\# signal. The Upstream and Downstream Ports' CLKREQ\# (A and C), and the Retimer's CLKREQB\# signals are connected to each other. In this case, Downstream Port (A), must assert CLKREQ\# signal whenever it requires a reference clock. Component A, Component B, and the Retimer have their REFCLKs removed/restored at the same time.
![img-80.jpeg](03_Knowledge/Tech/PCIe/04_Physical_Layer/img-80.jpeg)

Figure 4-81 Retimer CLKREQ\# Connection Topology

### 4.3.11 Retimer Configuration Parameters 6

Retimers must provide an implementation specific mechanism to configure each of the parameters in this section.

The parameters are split into two groups: parameters that are configurable globally for the Retimer and parameters that are configurable for each physical Retimer Pseudo Port.

If a per Pseudo Port parameter only applies to an Upstream or a Downstream Pseudo Port the Retimer is not required to provide an implementation specific mechanism to configure the parameter for the other type of Pseudo Port.

# 4.3.11.1 Global Parameters 

- Port Orientation Method. This controls whether the Port Orientation is determined dynamically as described in § Section 4.3.6.2, or statically based on vendor assignment of Upstream and Downstream Pseudo Ports. If the Port Orientation is set to static the Retimer is not required to dynamically adjust the Port Orientation as described in § Section 4.3.6.2. The default behavior is for the Port Orientation to be dynamically determined.
- Maximum Data Rate. This controls the maximum data rate that the Retimer sets in the Data Rate Identifier field of training sets that the Retimer transmits. Retimers that support only the $2.5 \mathrm{GT} / \mathrm{s}$ speed are permitted not to provide this configuration parameter.
- SRIS Enable. This controls whether the Retimer is configured for SRIS and transmits SKP Ordered Sets at the SRIS mode rate when in Execution mode. Retimers that do not support SRIS and at least one other clocking architecture are not required to provide this configuration parameter.
- SRIS Link Payload Size. This controls the maximum payload size the Retimer supports while in SRIS. The value must be selectable from all the Maximum Payload Sizes shown in § Table 4-77. The default value of this parameter is to support a maximum payload size of 4096 bytes. Retimers that do not support SRIS are not required to provide this configuration parameter.

The following are examples of cases where it might be appropriate to configure the SRIS Link Payload Size to a smaller value than the default:

- A Retimer is part of a motherboard connected to Root Port that supports a maximum payload size less than 4096 bytes.
- A Retimer is part of an adapter connected to an Upstream Port (e.g., Endpoint) that supports a maximum payload size less than 4096 bytes.
- A Retimer is located Downstream of the Downstream Port of a Switch integrated as part of a system, the Root Port supports a maximum payload size less than 4096 bytes and the system does not support peer to peer traffic.
- Enhanced Link Behavior Control. This controls the ability for the Retimer to either bypass equalization to the highest data rate or completely bypass equalization when it supports $32.0 \mathrm{GT} / \mathrm{s}$.


### 4.3.11.2 Per Physical Pseudo Port Parameters

- Port Orientation. This is applicable only when the Port Orientation Method is configured for static determination. This is set for either Upstream or Downstream. Each Pseudo Port must be configured for a different orientation, or the behavior is undefined.
- Selectable De-emphasis. When the Downstream Pseudo Port is operating at $5.0 \mathrm{GT} / \mathrm{s}$ this controls the transmit de-emphasis of the Link to either -3.5 dB or -6 dB in specific situations and the value of the Selectable De-emphasis field in training sets transmitted by the Downstream Pseudo Port. See § Section 4.2.7 for detailed usage information. When the Link Segment is not operating at the $5.0 \mathrm{GT} / \mathrm{s}$ speed, the setting of this bit has no effect. Retimers that support only the $2.5 \mathrm{GT} / \mathrm{s}$ speed are permitted not to provide this configuration parameter.
- Rx Impedance Control. This controls whether the Retimer dynamically applies and removes $50 \Omega$ terminations or statically has $50 \Omega$ terminations present. The value must be selectable from Dynamic, Off, and On. The default behavior is Dynamic.

- Tx Compliance Disable. This controls whether the Retimer transmits the Compliance Pattern in the CompLoadBoard.Pattern state. The default behavior is for the Retimer to transmit the Compliance Pattern in the CompLoadBoard.Pattern state. If TX Compliance Pattern is set to disabled, the Retimer Transmitters remain in Electrical Idle and do not transmit Compliance Pattern in CompLoadBoard.Pattern - all other behavior in the CompLoadBoard state is the same.
- Pseudo Port Follower Loopback. This controls whether the Retimer operates in a Forwarding mode during loopback on the Link or enters Follower Loopback on the Pseudo Port. The default behavior is for the Retimer to operate in Forwarding mode during loopback. Retimers that do not support optional Follower Loopback are permitted not to provide this configuration parameter. This configuration parameter shall only be enabled for one physical Port. Retimer behavior is undefined if the parameter is enabled for more than one physical Port.
- Downstream Pseudo Port 8GT TX Preset. This controls the initial TX preset used by the Downstream Pseudo Port transmitter for $8.0 \mathrm{GT} / \mathrm{s}$ transmission. The default value is implementation specific. The value must be selectable from all applicable values in § Table 4-32.
- Downstream Pseudo Port 16GT TX Preset. This controls the initial TX preset used by the Downstream Pseudo Port transmitter for $16.0 \mathrm{GT} / \mathrm{s}$ transmission. The default value is implementation specific. The value must be selectable from all applicable values in § Table 4-32.
- Downstream Pseudo Port 32GT TX Preset. This controls the initial TX preset used by the Downstream Pseudo Port transmitter for $32.0 \mathrm{GT} / \mathrm{s}$ transmission. The default value is implementation specific. The value must be selectable for all applicable values in § Table 4-32.
- Downstream Pseudo Port 64GT TX Preset. This controls the initial TX preset used by the Downstream Pseudo Port transmitter for $64.0 \mathrm{GT} / \mathrm{s}$ transmission. The default value is implementation specific. The value must be selectable for all applicable values in § Table 4-32.
- Downstream Pseudo Port 8GT Requested TX Preset. This controls the initial transmitter preset value used in the EQ TS2 Ordered Sets transmitted by the Downstream Pseudo Port for use at $8.0 \mathrm{GT} / \mathrm{s}$. The default value is implementation specific. The value must be selectable from all values in § Table 4-32.
- Downstream Pseudo Port 16GT Requested TX Preset. This controls the initial transmitter preset value used in the 128b/130b EQ TS2 Ordered Sets transmitted by the Downstream Pseudo Port for use at $16.0 \mathrm{GT} / \mathrm{s}$. The default value is implementation specific. The value must be selectable from all values in § Table 4-32.
- Downstream Pseudo Port 32GT Requested TX Preset. This controls the initial transmitter preset value used in the 128b/130b EQ TS2 Ordered Sets transmitted by the Downstream Pseudo Port for use at $32.0 \mathrm{GT} / \mathrm{s}$. The default value is implementation specific. The value must be selectable from all values in § Table 4-32.
- Downstream Pseudo Port 64GT Requested TX Preset. This controls the initial transmitter preset value used in the 128b/130b EQ TS2 Ordered Sets transmitted by the Downstream Pseudo Port for use at $64.0 \mathrm{GT} / \mathrm{s}$. The default value is implementation specific. The value must be selectable from all values in § Table 4-32.
- Downstream Pseudo Port 8GT RX Hint. This controls the Receiver Preset Hint value used in the EQ TS2 Ordered Sets transmitted by the Downstream Pseudo Port for use at $8.0 \mathrm{GT} / \mathrm{s}$. The default value is implementation specific. The value must be selectable from all values in § Table 4-33.


# 4.3.12 In Band Register Access 

- Retimers operating at $16.0 \mathrm{GT} / \mathrm{s}$ or higher may optionally support inband read only access. Control SKP Ordered Sets at $16.0 \mathrm{GT} / \mathrm{s}$ or higher provide the mechanism via the Margin Command 'Access Retimer Register', see § Table 4-73. Retimers that support inband read only access must return a non-zero value for the DWORD at Registers offsets 80 h and 84 h . Retimers that do not support inband read only access must return a zero value.
- Register offsets between A0h and FFh are designated as Vendor Defined register space.
- Register offsets from 00h to 7Fh and 85H to 9Fh are Reserved for PCI-SIG future use.

Page 674

