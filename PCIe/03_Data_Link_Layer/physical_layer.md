# 3. Data Link Layer Specification 

The Data Link Layer acts as an intermediate stage between the Transaction Layer and the Physical Layer. Its primary responsibility is to provide a reliable mechanism for exchanging Transaction Layer Packets (TLPs) between the two components on a Link.

### 3.1 Data Link Layer Overview

![img-0.jpeg](03_Knowledge/Tech/PCIe/03_Data_Link_Layer/img-0.jpeg)

OM13778A
Figure 3-1 Layering Diagram Highlighting the Data Link Layer

The Data Link Layer is responsible for reliably conveying TLPs supplied by the Transaction Layer across a PCI Express Link to the other component's Transaction Layer. Services provided by the Data Link Layer include:

Data Exchange:

- Accept TLPs for transmission from the Transmit Transaction Layer and convey them to the Transmit Physical Layer
- Accept TLPs received over the Link from the Physical Layer and convey them to the Receive Transaction Layer

Error Detection and Retry (Non-Flit Mode):

- TLP Sequence Number and LCRC generation
- Transmitted TLP storage for Data Link Layer Retry

- Data integrity checking for TLPs and Data Link Layer Packets (DLLPs)
- Positive and negative acknowledgement DLLPs
- Error indications for error reporting and logging mechanisms
- Link Acknowledgement Timeout replay mechanism

Initialization and power management:

- Track Link state and convey active/reset/disconnected state to Transaction Layer

DLLPs are:

- used for Link Management functions including TLP acknowledgement, power management, and exchange of Flow Control information.
- transferred between Data Link Layers of the two directly connected components on a Link

DLLPs are sent point-to-point, between the two components on one Link. TLPs are routed from one component to another, potentially through one or more intermediate components.

In Non-Flit Mode, Data integrity checking for DLLPs and TLPs is done using a CRC included with each packet sent across the Link. DLLPs use a 16-bit CRC and TLPs (which can be much longer than DLLPs) use a 32-bit LCRC. TLPs additionally include a sequence number, which is used to detect cases where one or more entire TLPs have been lost.

- Received DLLPs that fail the CRC check are discarded. The mechanisms that use DLLPs may suffer a performance penalty from this loss of information, but are self-repairing such that a successive DLLP will supersede any information lost.
- TLPs that fail the data integrity checks (LCRC and sequence number), or that are lost in transmission from one component to another, are re-sent by the Transmitter. The Transmitter stores a copy of all TLPs sent, re-sending these copies when required, and purges the copies only when it receives a positive acknowledgement of error-free receipt from the other component. If a positive acknowledgement has not been received within a specified time period, the Transmitter will automatically start re-transmission. The Receiver can request an immediate re-transmission using a negative acknowledgement.

In Flit Mode, both DLLPs and TLPs are sent using Flits. Flits contain the data integrity checks (LCRC, FEC, and sequence number). Replay occurs at the Flit level (see § Section 4.2.3.4 and § Section 4.2.3.4.2.1).

The Data Link Layer appears as an information conduit with varying latency to the Transaction Layer. On any given individual Link all TLPs fed into the Transmit Data Link Layer (1 and 3) will appear at the output of the Receive Data Link Layer (2 and 4) in the same order at a later time, as illustrated in § Figure 3-1. The latency will depend on a number of factors, including pipeline latencies, width and operational frequency of the Link, transmission of electrical signals across the Link, and delays caused by Data Link Layer Retry. As a result of these delays, the Transmit Data Link Layer (1 and 3) can apply backpressure to the Transmit Transaction Layer, and the Receive Data Link Layer (2 and 4) communicates the presence or absence of valid information to the Receive Transaction Layer.

# 3.2 Data Link Control and Management State Machine 

The Data Link Layer tracks the state of the Link. It communicates Link status with the Transaction and Physical Layers, and performs Link management through the Physical Layer. The Data Link Layer contains the Data Link Control and Management State Machine (DLCMSM) to perform these tasks. The states for this machine are described below, and are shown in § Figure 3-2.

States:

- DL_Inactive - Physical Layer reporting Link is non-operational or nothing is connected to the Port
- DL_Feature (optional) - Physical Layer reporting Link is operational, perform the Data Link Feature Exchange
- DL_Init - Physical Layer reporting Link is operational, initialize Flow Control for the default Virtual Channel
- DL_Active - Normal operation mode

Status Outputs:

- DL_Down - The Data Link Layer is not communicating with the component on the other side of the Link.
- DL_Up - The Data Link Layer is communicating with the component on the other side of the Link.
![img-1.jpeg](03_Knowledge/Tech/PCIe/03_Data_Link_Layer/img-1.jpeg)

Figure 3-2 Data Link Control and Management State Machine

# 3.2.1 Data Link Control and Management State Machine Rules 

Rules per state:

- DL_Inactive
- Initial state following PCI Express Hot, Warm, or Cold Reset (see § Section 6.6). Note that DL states are unaffected by an FLR (see § Section 6.6).

- Upon entry to DL_Inactive
- Reset all Data Link Layer state information to default values
- If the Port supports the optional Data Link Feature Exchange, the Remote Data Link Feature Supported, and Remote Data Link Feature Supported Valid fields must be cleared.
- Discard the contents of the Data Link Layer Retry Buffer (see § Section 3.6)
- While in DL_Inactive:
- Report DL_Down status to the Transaction Layer as well as to the rest of the Data Link Layer

Note: This will cause the Transaction Layer to discard any outstanding transactions and to terminate internally any attempts to transmit a TLP. For a Downstream Port, this is equivalent to a Hot-Remove. For an Upstream Port, having the Link go down is equivalent to a hot reset (see § Section 2.9 ).

- Discard TLP information from the Transaction and Physical Layers
- Do not generate or accept DLLPs
- Exit to DL_Feature if all of the following conditions are satisfied:
- the Port supports Data Link Feature Exchange
- either the Data Link Feature Exchange is Enabled bit in the Data Link Feature Extended Capability is Set or the Data Link Feature Extended Capability is not implemented
- the Transaction Layer indicates that the Link is not disabled by software
- the Physical Layer reports Physical LinkUp = 1b
- Exit to DL_Init if:
- The Port does not support the optional Data Link Feature Exchange, the Transaction Layer indicates that the Link is not disabled by software, and the Physical Layer reports Physical LinkUp = 1b or
- The Port supports the optional Data Link Feature Exchange, the Data Link Feature Exchange is Enabled bit is Clear, the Transaction Layer indicates that the Link is not disabled by software, and the Physical Layer reports Physical LinkUp = 1b


# - DL_Feature 

- While in DL_Feature:
- Perform the Data Link Feature Exchange protocol as described in § Section 3.3
- Report DL_Down status
- The Data Link Layer of a Port with DL_Down status is permitted to discard any received TLPs provided that it does not acknowledge those TLPs by sending one or more Ack DLLPs
- Exit to DL_Init if:
- Data Link Feature Exchange completes successfully, and the Physical Layer continues to report Physical LinkUp = 1b, or
- Data Link Feature Exchange determines that the remote Data Link Layer does not support the optional Data Link Feature Exchange protocol, and the Physical Layer continues to report Physical LinkUp = 1b
- Terminate the Data Link Feature Exchange protocol and exit to DL_Inactive if:
- Physical Layer reports Physical LinkUp = 0b

- DL_Init
- While in DL_Init:
- Initialize Flow Control for the default Virtual Channel, VCO, following the Flow Control initialization protocol described in § Section 3.4
- Report DL_Down status while in state FC_INIT1; DL_Up status while in state FC_INIT2
- The Data Link Layer of a Port with DL_Down status is permitted to discard any received TLPs provided that it does not acknowledge those TLPs by sending one or more Ack DLLPs
- Exit to DL_Active if:
- Flow Control initialization completes successfully, and the Physical Layer continues to report Physical LinkUp = 1b
- Terminate attempt to initialize Flow Control for VCO and exit to DL_Inactive if:
- Physical Layer reports Physical LinkUp = 0b


# - DL_Active 

- DL_Active is referred to as the normal operating state
- While in DL_Active:
- Accept and transfer TLP information with the Transaction and Physical Layers as specified in this chapter
- Generate and accept DLLPs as specified in this chapter
- Report DL_Up status to the Transaction and Data Link Layers
- Exit to DL_Inactive if:
- Physical Layer reports Physical LinkUp = 0b
- Downstream Ports that are Surprise Down Error Reporting Capable (see § Section 7.5.3.6) must treat this transition from DL_Active to DL_Inactive as a Surprise Down error, except in the following cases where this error detection is blocked:
- If the Secondary Bus Reset bit in the Bridge Control Register has been Set by software, then the subsequent transition to DL_Inactive must not be considered an error.
- If the Link Disable bit has been Set by software or if DPC has been triggered, then the subsequent transition to DL_Inactive must not be considered an error.
- If a Switch Downstream Port transitions to DL_Inactive due to an event above that Port, that transition to DL_Inactive must not be considered an error. Example events include the Switch Upstream Port propagating Hot Reset, the Switch Upstream Link transitioning to DL_Down, and the Secondary Bus Reset bit in the Switch Upstream Port being Set.
- If a PME_Turn_Off Message has been sent through this Port, then the subsequent transition to DL_Inactive must not be considered an error.
- Note that the DL_Inactive transition for this condition will not occur until a power off, a reset, or a request to restore the Link is sent to the Physical Layer.
- Note also that in the case where the PME_Turn_Off/PME_TO_Ack handshake fails to complete successfully, a Surprise Down error may be detected.
- If the Port is associated with a hot-pluggable slot (the Hot-Plug Capable bit in the Slot Capabilities register Set), and the Hot-Plug Surprise bit in the Slot Capabilities register is Set, then any transition to DL_Inactive must not be considered an error.

- If the Port is associated with a hot-pluggable slot (Hot-Plug Capable bit in the Slot Capabilities register Set), and Power Controller Control bit in Slot Control register is Set (Power-Off), then any transition to DL_Inactive must not be considered an error.

Error blocking initiated by one or more of the above cases must remain in effect until the Port exits DL_Active and subsequently returns to DL_Active with none of the blocking cases in effect at the time of the return to DL_Active.

Note that the transition out of DL_Active is simply the expected transition as anticipated per the error detection blocking condition.

If implemented, this is a reported error associated with the detecting Port (see § Section 6.2 ).

# IMPLEMENTATION NOTE: PHYSICAL LAYER THROTTLING 

Note that there are conditions where the Physical Layer may be temporarily unable to accept TLPs and DLLPs from the Data Link Layer. The Data Link Layer must comprehend this by providing mechanisms for the Physical Layer to communicate this condition, and for TLPs and DLLPs to be temporarily blocked by the condition.

### 3.3 Data Link Feature Exchange

The Data Link Feature Exchange protocol is required for Ports that support Flit Mode and for Ports that support 16.0 GT/s and higher data rates. It is optional for other Ports. Downstream Ports that implement this protocol must contain the Data Link Feature Extended Capability (see § Section 7.7.4). Upstream Ports that implement this protocol are optionally permitted to include the Data Link Feature Extended Capability. This capability contains four fields:

- The Local Data Link Feature Supported field indicates the Data Link Features supported by the local Port
- The Remote Data Link Feature Supported field indicates the Data Link Features supported by the remote Port
- The Remote Data Link Feature Supported Valid bit indicates that the Remote Data Link Feature Supported field contains valid data
- The Data Link Feature Exchange is Enabled field permits systems to disable the Data Link Feature Exchange. This can be used to work around legacy hardware that does not correctly ignore the DLLP.

The Data Link Feature Exchange protocol transmits a Port's Local Feature Supported information to the Remote Port and captures that Remote Port's Feature Supported information.

Rules for this protocol are:

- On entry to DL_Feature:
- It is permitted to Clear the Remote Data Link Feature Supported and Remote Data Link Feature Supported Valid fields
- While in DL_Feature:
- Transaction Layer must block transmission of TLPs
- Transmit the Data Link Feature DLLP

- The transmitted Feature Supported field must use the value in the Local Data Link Feature Supported field.
- The transmitted Feature Ack bit must use the value in the Remote Data Link Feature Supported Valid bit.
- The Data Link Feature DLLP must be transmitted at least once every $34 \mu \mathrm{~s}$. Time spent in the Recovery or Configuration LTSSM states does not contribute to this limit.
- Process received Data Link Feature DLLPs:
- If the Remote Data Link Feature Supported Valid bit is Clear, record the Feature Supported field from the received Data Link Feature DLLP in the Remote Data Link Feature Supported field and Set the Remote Data Link Feature Supported Valid bit.
- Exit DL_Feature if:
- An InitFC1 DLLP has been received.
- An MR-IOV MRInit DLLP (encoding 0000 0001b) has been received. MR-IOV is deprecated so this clause has no effect in new designs.
or
- While in DL_Feature, at least one Data Link Feature DLLP has been received with the Feature Ack bit Set.

A Data Link Feature is a field representing a protocol feature. Protocol features are either activated, not activated, or not supported. A Data Link Feature is activated when Remote Data Link Feature Supported Valid is Set and when the associated Feature Supported bit is Set in both the Local Data Link Feature Supported and Remote Data Link Feature Supported fields.

A Data Link Parameter is a field that communicates a value across the interface. Data Link Parameters have a parameter-specific mechanism for software to determine when the field value is meaningful. For example, the field might be meaningful if its value is non-zero or the field might be meaningful if some other field(s) have specific values.

Data Link Features and their corresponding bit locations are shown in § Table 3-1.
Table 3-1 Data Link Feature Supported Bit Definition

| Bit <br> Location | Description | Type |
| :--: | :-- | :-- |
| 0 | Scaled Flow Control - indicates support for Scaled Flow Control. <br> Must be Set in Ports that support 16.0 GT/s or higher data rates. <br> Must be Set if Flit Mode is enabled. | Data Link <br> Feature |
| 1 | Immediate Readiness - indicates that all non-Virtual Functions in the sending Port have Immediate Readiness <br> Set (see § Section 7.5.1.1.4). <br> In Flit Mode, this bit is always meaningful. In Non-Flit Mode, this bit is meaningful when Set, but when <br> Clear indicates either that some non-Virtual Function has Immediate Readiness Clear or that the sending Port <br> is not providing this information. | Data Link <br> Parameter |
| 4:2 | Extended VC Count - This field indicates the number of VC Resources supported by the sending Port. This is <br> the value of the Extended VC Count field in either the Multi-Function Virtual Channel Extended Capability or <br> the Virtual Channel Extended Capability (with Capability ID 0002h). <br> This field is meaningful in Flit Mode. In Non-Flit Mode, this field must be zero. | Data Link <br> Parameter |

| Bit <br> Location | Description | Type |
| :--: | :--: | :--: |
| 7:5 | Löp Exit Latency - This field indicates sending Port's LOp Exit Latency. The value reported indicates the length of time the sending Port requires to complete widening a link using LOp. If the sending Port does not support LOp, this field must contain 000b. <br> Defined encodings are: | Data Link Parameter |
|  | 000b | Less than $1 \mu \mathrm{~s}$ |
|  | 001b | $1 \mu \mathrm{~s}$ to less than $2 \mu \mathrm{~s}$ |
|  | 010b | $2 \mu \mathrm{~s}$ to less than $4 \mu \mathrm{~s}$ |
|  | 011b | $4 \mu \mathrm{~s}$ to less than $8 \mu \mathrm{~s}$ |
|  | 100b | $8 \mu \mathrm{~s}$ to less than $16 \mu \mathrm{~s}$ |
|  | 101b | $16 \mu \mathrm{~s}$ to less than $32 \mu \mathrm{~s}$ |
|  | 110b | $32 \mu \mathrm{~s}-64 \mu \mathrm{~s}$ |
|  | 111b | More than $64 \mu \mathrm{~s}$ |
|  | This field is meaningful in Flit Mode. In Non-Flit Mode, this field must be zero. |  |
| 22:8 | Reserved |  |

# 3.4 Flow Control Initialization Protocol 

Before starting normal operation following power-up or interconnect reset, it is necessary to initialize Flow Control for the default Virtual Channel, VCO (see § Section 6.6 ). In addition, when additional Virtual Channels (VCs) are enabled, the Flow Control initialization process must be completed for each newly enabled VC before it can be used (see § Section 2.6.1). This section describes the initialization process that is used for all VCs. Note that since VCO is enabled before all other VCs, no TLP traffic of any kind will be active prior to initialization of VCO. However, when additional VCs are being initialized there will typically be TLP traffic flowing on other, already enabled, VCs. Such traffic has no direct effect on the initialization process for the additional VC(s).

Shared Flow Control is enabled in Flit Mode. Shared Flow Control is disabled in Non-Flit Mode.
There are two states in the VC initialization process. These states are:

- FC_INIT1
- FC_INIT2

The rules for this process are given in the following section.

### 3.4.1 Flow Control Initialization State Machine Rules

- If at any time during initialization for VCs 1-7 the VC is disabled, the flow control initialization process for the VC is terminated
- Rules for state FC_INIT1:
- Entered when initialization of a VC (VCx) is required
- When the DL_Init state is entered (VCx = VCO)
- When VC (VCx = VC1-7) is enabled by software (see § Section 7.9.1 and § Section 7.9.2)

- While in FC_INIT1:
- Transaction Layer must block transmission of TLPs using VCx
- In Non-Flit Mode, transmit the following three InitFC1 DLLPs for VCx in the following relative order:
- InitFC1-P [Dedicated] (first)
- InitFC1-NP [Dedicated] (second)
- InitFC1-Cpl [Dedicated] (third)
- In Flit Mode, transmit the following six InitFC1 DLLPs for VCx in the following relative order:
- InitFC1-P [Dedicated] (first)
- InitFC1-NP [Dedicated] (second)
- InitFC1-Cpl [Dedicated] (third)
- InitFC1-P [Shared] (fourth)
- InitFC1-NP [Shared] (fifth)
- InitFC1-Cpl [Shared] (sixth)
- The three (or six) InitFC1 DLLPs must be transmitted at least once every $34 \mu \mathrm{~s}$.
- Time spent in the Recovery or Configuration LTSSM states does not contribute to this limit.
- It is strongly encouraged that the InitFC1 DLLP transmissions are repeated frequently, particularly when there are no other TLPs or DLLPs available for transmission.
- Set DataFC, DataScale, HdrFC, and HdrScale as shown in § Table 3-2 and § Table 3-3
- When DataFC or HdrFC is 0 , the following encodings of DataScale and HdrScale are used:
- Non-Flit Mode, no Scaled FC:
[Infinite.1]
DataScale/HdrScale $=00 b$


# [Reserved] 

DataScale/HdrScale $=01 b, 10 b$, or $11 b$

- Non-Flit Mode, Scaled FC:
[Infinite.2]
DataScale/HdrScale $=01 b, 10 b$, or $11 b$


## [Reserved]

DataScale/HdrScale $=00 b$

- Flit Mode:
[Infinite.3]
DataScale/HdrScale $=00 b$


## [Zero]

DataScale/HdrScale $=01 b$

## [Merged]

DataScale/HdrScale $=10 b$

## [Reserved]

DataScale/HdrScale $=11 b$

Table 3-2 InitFC1 / InitFC2 Options - Non-Flit Mode

| Row | Scaled <br> Flow <br> Control <br> Supported <br> and <br> Activated | Local and Remote Extended VC Count | Merged | InitFC Count | Dedicated / Shared | DataScale and HdrScale | DataFC and HdrFC | Notes |
| :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: |
| 1 | No Scaled FC | 0 <br> (Reserved) | Not Applicable | 3 | 0b <br> (Reserved) | [Infinite.1] |  | 1 |
|  |  |  |  |  |  | 00b | $\neq 0$ |  |
| 2 | Scaled FC | 0 <br> (Reserved) | Not Applicable | 3 | 0b <br> (Reserved) | [Infinite.2] |  | 1,2 |
|  |  |  |  |  |  | $\{01 b \mid 10 b \mid 11 b\}$ | $\neq 0$ |  |

Notes:

1. Backwards compatibility: In earlier versions of this specification, the DataScale and HdrScale bits are Reserved.
2. Backwards compatibility: In earlier versions of this specification, any non-zero DataScale/ HdrScale means [Infinite.2].

Table 3-3 InitFC1 / InitFC2 Options - Flit Mode

| Row | Local and Remote Extended VC Count | Merged | InitFC Count | Dedicated / Shared | Kind | DataScale and HdrScale | DataFC and HdrFC | Notes |
| :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: |
| 3 | Local $=0$ OR optionally (Local $\neq 0$ and Remote $=0$ ) | Not Merged | 6 | 0b <br> (shared) | $\begin{aligned} & \text { P, } \\ & \text { NP, } \\ & \text { Cpl } \end{aligned}$ | [Infinite.3] |  | 5,9 |
|  |  |  |  |  |  | $\{01 b \mid 10 b \mid 11 b\}$ | $\neq 0$ |  |
| 4 |  |  |  | 1b <br> (dedicated) | $\begin{aligned} & \text { P, } \\ & \text { NP, } \\ & \text { Cpl } \end{aligned}$ | [Zero] |  | 3,5,9 |
| 5 | Local $=0$ OR optionally (Local $\neq 0$ and Remote $=0$ ) | Merged | 6 | 0b <br> (shared) | $\begin{aligned} & \text { P, } \\ & \text { NP } \end{aligned}$ | [Infinite.3] |  | 8 |
|  |  |  |  |  |  | $\{01 b \mid 10 b \mid 11 b\}$ | $\neq 0$ |  |
| 6 |  |  |  |  | Cpl | [Merged] |  | 7,8 |
| 7 |  |  |  | 1b <br> (dedicated) | $\begin{aligned} & \text { P, } \\ & \text { Cpl } \end{aligned}$ | [Infinite.3] |  | 8,10 |
|  |  |  |  |  |  | $\{01 b \mid 10 b \mid 11 b\}$ | $\neq 0$ |  |
| 8 |  |  |  |  | NP | [Zero] |  | 4,8 |
| 9 | Local $\neq 0$ | Not Merged | 6 | 0b <br> (shared) | $\begin{aligned} & \text { P, } \\ & \text { NP, } \\ & \text { Cpl } \end{aligned}$ | [Infinite.3] |  | 5,6 |
|  |  |  |  |  |  | [Zero] |  |  |
|  |  |  |  |  |  | $\{01 b \mid 10 b \mid 11 b\}$ | $\neq 0$ |  |

| Row | Local and Remote Extended VC Count | Merged | InitFC Count | Dedicated / Shared | Kind | DataScale and HdrScale | DataFC and HdrFC | Notes |
| :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: |
| 10 |  |  |  | $\begin{gathered} 1 b \\ \text { (dedicated) } \end{gathered}$ | $\begin{gathered} \mathrm{P}, \\ \mathrm{NP}, \\ \text { Cpl } \end{gathered}$ | [Infinite.3] |  | 5 |
|  |  |  |  |  |  | $\{01 b \mid 10 b \mid 11 b\}$ | $\# 0$ |  |
| 11 | Local $\# 0$ | Merged | 6 | $\begin{gathered} 0 b \\ \text { (shared) } \end{gathered}$ | $\begin{gathered} \mathrm{P}, \\ \mathrm{NP} \end{gathered}$ | [Infinite.3] |  | 6,8 |
|  |  |  |  |  |  | $\{01 b \mid 10 b \mid 11 b\}$ | $\# 0$ |  |
| 12 |  |  |  |  | Cpl | [Merged] |  | 7,8 |
| 13 |  |  |  | 1b <br> (dedicated) | $\begin{gathered} \mathrm{P}, \\ \mathrm{NP}, \\ \text { Cpl } \end{gathered}$ | [Infinite.3] |  | 8,10 |
|  |  |  |  |  |  | $\{01 b \mid 10 b \mid 11 b\}$ | $\# 0$ |  |

Notes:
3. Since Extended VC Count is 0 , only 1 VC is possible. [Zero] dedicated credits allocated. All credits are Shared.
4. Since Extended VC Count is 0 , only 1 VC is possible. [Zero] Non-Posted dedicated credits are allocated and all Non-Posted credits are Shared.
5. When (Local $\# 0$ and Remote $=0$ ), rows 3-4 are recommended but rows 9-10 are permitted.
6. [Zero] shared credits indicates that no additional shared credits are being allocated. All shared credits are (were) allocated by other VCs (and are usable by this VC).

When more than one VC advertises shared credits with scale factor $01 b, 10 b$, or $11 b$, that scale factor must be able to express all allocated shared credits, regardless of VC. For example, if VC0 and VC1 each advertise 120 header credits (i.e., a total of 240 credits), they must do so using a scale factor other than $1(01 b)$ since that scale factor is limited to 127 outstanding credits.

Use of [Infinite.3] shared credits must be consistent across VCs. If one VC uses [Infinite.3] shared credits for a given credit type (P/NP/Cpl, Hdr/Data), all VCs must also use [Infinite.3] shared credits for that credit type.

Use of scale values (HdrScale or DataScale) 01b, 10b, or 11b for shared credits must be consistent across VCs. If one VC uses scale value $01 \mathrm{~b}, 10 \mathrm{~b}$, or 11 b for a given credit type ( P / NP/Cpl, Hdr/Data), all other VCs must either use the same scale value or must use [Zero] for that credit type.

When one VC uses [Zero] shared credits for a given credit type (P/NP/Cpl, Hdr/Data), at least one VC must use a scale value of $01 \mathrm{~b}, 10 \mathrm{~b}$, or 11 b for that credit type. For that credit type, shared credit UpdateFC DLLPs for all VCs must use this non-00b scale value, including VCs that advertised [Zero] during initialization.

It is permitted for all VCs to offer [Zero] shared credits resulting in only dedicated credits being available. Doing so means that every TLP will contain a Flit Mode Local TLP Prefix.
7. [Merged] for Shared Completion credits indicates that Shared Completions and Shared Posted credits share a common pool of credits. [Merged] is not permitted on Shared Posted or Shared Non-Posted credits. Dedicated credits are never merged.

| Row | Local and <br> Remote <br> Extended VC <br> Count | Merged | InitFC <br> Count | Dedicated <br> / Shared | Kind | DataScale and <br> HdrScale | DataFC <br> and <br> HdrFC | Notes |
| :-- | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: |

Use of [Merged] shared credits must be consistent across VCs. If one VC uses [Merged] shared credits, all VCs must also use [Merged] shared credits.

Use of [Merged] shared credits must be consistent between Hdr and Data. If CpIH uses [Merged] shared credits, CplD must also use [Merged] shared credits.

When [Merged] is used, and P Hdr shared credits are not [Infinite.3], UpdateFC DLLPs for CpIH must use the same scale factor as PH.

When [Merged] is used, and P Data shared credits are not [Infinite.3], UpdateFC DLLPs for CplD must use the same scale factor as PD.

When [Merged], UpdateFC DLLPs and Optimized_Update_FCs return credits as if [Merged] was not enabled (i.e., based on the type of TLP being freed even though there is a single shared credit pool). Doing this provides the transmitter visibility into remote buffer occupancy (Posted vs Completion) and allows it to implement vendor specific mechanisms to manage that occupancy.

When [Merged] is used and P Hdr shared credits are not [Infinite.3], and at least one VC must use non [Zero] P Hdr shared credits.

When [Merged] is used and P Data shared credits are not [Infinite.3], and at least one VC must use non [Zero] P Data shared credits.
8. When (Local $\neq 0$ and Remote $=0$ ), rows $5-8$ are recommended, but rows $11-13$ are permitted.
9. The Shared / Dedicated mechanism is defined so that shared credits are the common case. TLPs consuming dedicated credits use the Flit Mode Local TLP Prefix and thus consume an additional DW. In rows 3-4, all credits are shared.
10. To avoid deadlock, Posted and Completion credits must not be [Zero].

- Except as needed to ensure at least the required frequency of InitFC1 DLLP transmission, the Data Link Layer must not block other transmissions.
- Note that this includes all Physical Layer initiated transmissions (e.g., Ordered Sets), Ack and Nak DLLPs (when applicable), and TLPs using VCs that have previously completed initialization (when applicable)
- Process received InitFC1 and InitFC2 DLLPs:
- Record the indicated HdrFC and DataFC values
- If the Receiver supports Scaled Flow Control, record the indicated HdrScale and DataScale values.
- Set flag FI1 once FC unit values have been recorded for each of P, NP, and Cpl for VCx.
- In Non-Flit Mode flag FI1 is Set when the three dedicated FC unit values have been recorded.
- In Flit Mode, flag FI1 is Set when all six FC unit values have been recorded.
- Exit to FC_INIT2 if:
- Flag FI1 has been Set indicating that FC unit values have been recorded for each of P, NP, and Cpl for VCx

- Rules for state FC_INIT2:
- While in FC_INIT2:
- Transaction Layer must block transmission of TLPs using VCx
- In non-Flit Flit-Mode, transmit the following three InitFC2 DLLPs for VCx in the following relative order:
- InitFC2-P [Dedicated] (first)
- InitFC2-NP [Dedicated] (second)
- InitFC2-Cpl [Dedicated] (third)
- In Flit Mode, transmit the following six InitFC2 DLLPs for VCx in the following relative order:
- InitFC2-P [Dedicated] (first)
- InitFC2-NP [Dedicated] (second)
- InitFC2-Cpl [Dedicated] (third)
- InitFC2-P [Shared] (fourth)
- InitFC2-NP [Shared] (fifth)
- InitFC2-Cpl [Shared] (sixth)
- The three (six) InitFC2 DLLPs must be transmitted at least once every $34 \mu \mathrm{~s}$.
- Time spent in the Recovery or Configuration LTSSM states does not contribute to this limit.
- It is strongly encouraged that the InitFC2 DLLP transmissions are repeated frequently, particularly when there are no other TLPs or DLLPs available for transmission.
- Set DataFC, DataScale, HdrFC, and HdrScale as shown in § Table 3-2 and § Table 3-3
- Except as needed to ensure at least the required frequency of InitFC2 DLLP transmission, the Data Link Layer must not block other transmissions
- Note that this includes all Physical Layer initiated transmissions (for example, Ordered Sets), Ack and Nak DLLPs (when applicable), and TLPs using VCs that have previously completed initialization (when applicable)
- Process received InitFC1 and InitFC2 DLLPs:
- Ignore the received HdrFC, HdrScale, DataFC, and DataScale values
- Set flag FI2 on receipt of any InitFC2 DLLP for VCx
- Set flag FI2 on receipt of any TLP on VCx, any UpdateFC DLLP for VCx, or, in Flit Mode, any Optimized_Update_FC
- Signal completion and exit if:
- Flag FI2 has been Set
- If Scaled Flow Control is activated on the Link, the Transmitter must send 01b, 10b, or 11b for HdrScale and DataScale in all UpdateFC DLLPs for VCx.
- If the Scaled Flow Control is not supported or if Scaled Flow Control is not activated on the Link, the Transmitter must send 00b for HdrScale and DataScale in all UpdateFC DLLPs for VCx.

# IMPLEMENTATION NOTE: <br> EXAMPLE OF FLOW CONTROL INITIALIZATION 

§ Figure 3-3 illustrates an example of the Flow Control initialization protocol for VCO between a Switch and a Downstream component. In this example, each component advertises the minimum permitted values for each type of Flow Control credit. For both components the Rx_MPS_Limit is 1024 bytes, corresponding to a data payload credit advertisement of 040 h . All DLLPs are shown as received without error.

![img-2.jpeg](03_Knowledge/Tech/PCIe/03_Data_Link_Layer/img-2.jpeg)

Figure 3-3 VC0 Flow Control Initialization Example with 8b/10b Encoding-based Framing

# 3.4.2 Scaled Flow Control 

Link performance can be affected when there are insufficient flow control credits available to account for the Link round trip time. This effect becomes more noticeable at higher Link speeds and the limitation of 127 header credits and 2047 data credits can limit performance. The Scaled Flow Control mechanism is designed to address this limitation.

All Ports are permitted to support Scaled Flow Control. Ports that support $16.0 \mathrm{GT} / \mathrm{s}$ and higher data rates must support Scaled Flow Control. Scaled Flow Control activation does not affect the ability to operate at $16.0 \mathrm{GT} / \mathrm{s}$ and higher data rates.

The following rules apply when Scaled Flow Control is not activated for the Link:

- The InitFC1, InitFC2, and UpdateFC DLLPs must contain 00b in the HdrScale and DataScale fields.
- The HdrFC counter is 8 bits wide and the HdrFC field includes all bits of the counter.
- The DataFC counter is 12 bits wide and the DataFC field includes all bits of the counter.

The following rules apply when Scaled Flow Control is activated for the Link:

- The InitFC1 and InitFC2 DLLPs that are transmitted must contain 01b, 10b, or 11b in the HdrScale field. The value is determined by the maximum number of header credits that will be outstanding of the indicated credit type as defined in § Table 3-4.
- The InitFC1 and InitFC2 DLLPs that are transmitted must contain 01b, 10b, or 11b in the DataScale field. The value is determined by the maximum number of data payload credits that will be outstanding of the indicated credit type as defined in § Table 3-4.

Table 3-4 Scaled Flow Control Scaling Factors

| Scale <br> Factor | Scaled Flow Control Supported and Activated | Credit Type | Min Credits | Max Credits | Field Width | FC DLLP field |  |
| :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: |
|  |  |  |  |  |  | Transmitted | Received |
| 00b | No | Hdr | 1 | 127 | 8 bits | HdrFC | HdrFC |
|  |  | Data | 1 | 2,047 | 12 bits | DataFC | DataFC |
| 01b | Yes | Hdr | 1 | 127 | 8 bits | HdrFC | HdrFC |
|  |  | Data | 1 | 2,047 | 12 bits | DataFC | DataFC |
| 10b | Yes | Hdr | 4 | 508 | 10 bits | HdrFC >> 2 | HdrFC $<<2$ |
|  |  | Data | 4 | 8,188 | 14 bits | DataFC >> 2 | DataFC $<<2$ |
| 11b | Yes | Hdr | 16 | 2,032 | 12 bits | HdrFC >> 4 | HdrFC $<<4$ |
|  |  | Data | 16 | 32,752 | 16 bits | DataFC >> 4 | DataFC $<<4$ |

### 3.5 Data Link Layer Packets (DLLPs)

The following DLLPs are used to support Link operations:

- Data Link Feature DLLP: For negotiation of supported features

- Ack DLLP: TLP Sequence Number acknowledgement; used to indicate successful receipt of some number of TLPs (NFM only)
- Nak DLLP: TLP Sequence Number negative acknowledgement; used to initiate a Data Link Layer Retry (NFM only)
- InitFC1, InitFC2, and UpdateFC DLLPs; used for Flow Control
- DLLPs used for Power Management
- DLLPs used for Link Management (L0p)


# 3.5.1 Data Link Layer Packet Rules 

All DLLP fields marked Reserved (sometimes abbreviated as R) must be filled with all 0's when a DLLP is formed. Values in such fields must be ignored by Receivers. The handling of Reserved values in encoded fields is specified for each case.

In Non-Flit Mode, all DLLPs include the following fields:

- DLLP Type - Specifies the type of DLLP. The defined encodings are shown in § Table 3-5.
- 24 bits of DLLP Type specific information
- 16-bit CRC

In Flit Mode, DLLPs are transmitted in the DLP bytes of a Flit. They consist of:

- DLLP Type - Specifies the type of DLLP. The defined encodings are shown in § Table 3-5.
- 24 bits of DLLP Type specific information

See § Figure 3-4 and § Figure 3-5 below.
![img-3.jpeg](03_Knowledge/Tech/PCIe/03_Data_Link_Layer/img-3.jpeg)

Figure 3-4 DLLP Type and CRC Fields (Non-Flit Mode)
![img-4.jpeg](03_Knowledge/Tech/PCIe/03_Data_Link_Layer/img-4.jpeg)

Figure 3-5 DLLP Type Field (Flit Mode)

Table 3-5 DLLP Type Encodings

| Encodings (b) | DLLP Type (Note 3) | References |
| :--: | :--: | :--: |
| 00000000 | Ack (Non-Flit Node) | § Figure 3-6, |
|  | NOP2 (Flit Mode) | § Figure 3-8 |
| 00000001 | MRInit (Non-Flit Mode) (Deprecated) | See [MR-IOV] Note 1 |
|  | Reserved (Flit Mode) |  |
| 00000010 | Data Link Feature | § Figure 3-14, |
| 00000011 | Alternate Protocol Use 1 | Not used by PCI Express. Only permitted after an Alternate Protocol has been |
| 00000100 | Alternate Protocol Use 2 | negotiated (see § Section 4.2.5.2). Meaning is Alternate Protocol specific. For example, see [CXL-3.0]. |
| 00010000 | Nak (Non-Flit Mode) | § Figure 3-6, |
|  | Reserved (Flit Mode) |  |
| 00100000 | PM_Enter_L1 | § Figure 3-12, § Section 5.3.2.1 |
| 00100001 | PM_Enter_L23 | § Figure 3-12, § Section 5.3.2.3 |
| 00100011 | PM_Active_State_Request_L1 | § Figure 3-12, § Section 5.4.1.3.1 |
| 00100100 | PM_Request_Ack | § Figure 3-12, § Section 5.4.1.3.1, § Section 5.3.2.1 |
| 00101000 | Reserved (Non-Flit Mode) |  |
|  | Link Management (Flit Mode) | § Figure 3-15, § Table 4-54 |
| 00110000 | Vendor-Specific | § Figure 3-13, |
| 00110001 | NOP | § Figure 3-7, |
| $\begin{aligned} & 01000 \mathrm{v}_{1} \mathrm{v}_{1} \mathrm{v}_{0} \\ & 01001 \mathrm{v}_{1} \mathrm{v}_{1} \mathrm{v}_{0} \end{aligned}$ | InitFC1-P (v[2:0] specifies Virtual Channel) | § Figure 3-9, |
| $\begin{aligned} & 01010 \mathrm{v}_{0} \mathrm{v}_{1} \mathrm{v}_{0} \\ & 01011 \mathrm{v}_{1} \mathrm{v}_{1} \mathrm{v}_{0} \end{aligned}$ | InitFC1-NP |  |
| $\begin{aligned} & 01100 \mathrm{v}_{1} \mathrm{v}_{1} \mathrm{v}_{0} \\ & 01101 \mathrm{v}_{1} \mathrm{v}_{1} \mathrm{v}_{0} \end{aligned}$ | InitFC1-Cpl |  |
| $\begin{aligned} & 01110 \mathrm{v}_{1} \mathrm{v}_{1} \mathrm{v}_{0} \\ & \hline \end{aligned}$ | MRInitFC1 (Non-Flit-Mode) (Deprecated) | See [MR-IOV] Note 2 |
|  | Reserved (Flit Mode) |  |
| $\begin{aligned} & 11000 \mathrm{v}_{1} \mathrm{v}_{1} \mathrm{v}_{0} \\ & 11001 \mathrm{v}_{1} \mathrm{v}_{1} \mathrm{v}_{0} \end{aligned}$ | InitFC2-P | § Figure 3-10, |
| $\begin{aligned} & 11010 \mathrm{v}_{1} \mathrm{v}_{1} \mathrm{v}_{0} \\ & 11011 \mathrm{v}_{1} \mathrm{v}_{1} \mathrm{v}_{0} \end{aligned}$ | InitFC2-NP |  |

| Encodings <br> (b) | DLLP Type (Note 3) | References |
| :--: | :--: | :--: |
| $\begin{aligned} & 11100 \mathrm{v}_{2} \mathrm{v}_{1} \mathrm{v}_{0} \\ & 11101 \mathrm{v}_{2} \mathrm{v}_{1} \mathrm{v}_{0} \end{aligned}$ | InitFC2-Cpl |  |
| $11110 \mathrm{v}_{2} \mathrm{v}_{1} \mathrm{v}_{0}$ | MRInitFC2 (Non-Flit-Mode) (Deprecated) | See [MR-IOV] <br> Note 2 |
|  | Reserved (Flit Mode) |  |
| $\begin{aligned} & 10000 \mathrm{v}_{2} \mathrm{v}_{1} \mathrm{v}_{0} \\ & 10001 \mathrm{v}_{2} \mathrm{v}_{1} \mathrm{v}_{0} \end{aligned}$ | UpdateFC-P | $\S$ Figure 3-11, |
| $\begin{aligned} & 10010 \mathrm{v}_{2} \mathrm{v}_{1} \mathrm{v}_{0} \\ & 10011 \mathrm{v}_{2} \mathrm{v}_{1} \mathrm{v}_{0} \end{aligned}$ | UpdateFC-NP |  |
| $\begin{aligned} & 10100 \mathrm{v}_{2} \mathrm{v}_{1} \mathrm{v}_{0} \\ & 10101 \mathrm{v}_{2} \mathrm{v}_{1} \mathrm{v}_{0} \end{aligned}$ | UpdateFC-Cpl |  |
| $\begin{aligned} & 10110 \mathrm{v}_{2} \mathrm{v}_{1} \mathrm{v}_{0} \\ & \hline \end{aligned}$ | MRUpdateFC (Non-Flit Mode) (Deprecated) | See [MR-IOV] <br> Note 2 |
|  | Reserved (Flit Mode) |  |
| All other encodings | Reserved |  |

1. The deprecated MR-IOV protocol uses this encoding for the MRInit negotiation. The MR-IOV protocol assumes that non-MR-IOV components will silently ignore these DLLPs.
2. The deprecated MR-IOV protocol uses these encodings only after the successful completion of MRInit negotiation.
3. Received DLLPs not supported by the Receiver are silently ignored. See $\S$ Section 3.6.2.2 and $\S$ Section 3.6.2.3.

In § Figure 3-6 through § Figure 3-15 the 16-bit CRC is not shown. In Non-Flit Mode, the CRC is present as shown in § Figure 3-4.

- For Ack and Nak DLLPs (see § Figure 3-6):
- The AckNak_Seq_Num field is used to indicate what TLPs are affected
- Transmission and reception is handled by the Data Link Layer according to the rules provided in § Section 3.6 .
- These DLLPs are not used in Flit Mode. In Flit Mode, the Ack encoding is used for the NOP2.
- For InitFC1, InitFC2, and UpdateFC DLLPs:
- The HdrFC field contains the credit value for headers of the indicated type (P, NP, or Cpl).
- The DataFC field contains the credit value for data payload of the indicated type (P, NP, or Cpl).
- When Scaled Flow Control is supported, the HdrScale field contains the scaling factor for headers of the indicated type. Encodings are defined in § Table 3-6.
- When Scaled Flow Control is supported, the DataScale field contains the scaling factor for data payload of the indicated type. Encodings are defined in § Table 3-6.
- When Scaled Flow Control is not supported, the HdrScale and Data Scale fields are Reserved.

- If Scaled Flow Control is activated, the HdrScale and DataScale fields must be set to 01b, 10b, or 11b in all InitFC1, InitFC2, and UpdateFC DLLPs transmitted.
- In UpdateFCs, a Transmitter is only permitted to send non-zero values in the HdrScale and DataScale fields if it supports Scaled Flow Control, Scaled Flow control is activated, and it received non-zero values for HdrScale and DataScale in the InitFC1s and InitFC2s it received for this VC. In Flit Mode, the Optimized_Update_FC mechanism is supported in addition to the UpdateFC DLLP. Optimized_Update_FCs do not contain HdrScale and DataScale fields, so the Transmitter and Receiver must treat the HdrFC and DataFC fields using corresponding HdrScale and DataScale fields advertised during initialization. For debug as well as ease of use by debug tools such as Logic Analyzers, devices must send at least one DLLP every $10 \mu \mathrm{~s}$ with an UpdateFC DLLP per VC with the scaled credit information. It is strongly recommended that a Transmitter cycles through the VCs with finite non-0 credits in the Optimized_Update_FC as long as there is a credit to be released in the corresponding VC.
- The packet formats are shown in § Figure 3-9, § Figure 3-10, and § Figure 3-11.
- Transmission is triggered by the Data Link Layer when initializing Flow Control for a Virtual Channel (see § Section 3.4 ), and following Flow Control initialization by the Transaction Layer according to the rules in § Section 2.6 .
- Checked for integrity on reception by the Data Link Layer and if correct, the information content of the DLLP is passed to the Transaction Layer. If the check fails, the information must be discarded. Note: InitFC1 and InitFC2 DLLPs are used only for VC initialization

Table 3-6 HdrScale and DataScale Encodings

| HdrScale or <br> DataScale Value | Scaled Flow <br> Control <br> Supported | Scaling <br> Factor | HdrFC <br> Field | DataFC <br> Field |
| :--: | :--: | :--: | :--: | :--: |
| 00b | No | 1 | HdrFC[7:0] | DataFC[11:0] |
| 01b | Yes | 1 | HdrFC[7:0] | DataFC[11:0] |
| 10b | Yes | 4 | HdrFC[9:2] | DataFC[13:2] |
| 11b | Yes | 16 | HdrFC[11:4] | DataFC[15:4] |

- For Power Management (PM) DLLPs (see § Figure 3-12):
- Transmission is triggered by the component's power management logic according to the rules in § Chapter 5.
- Checked for integrity on reception by the Data Link Layer, then passed to the component's power management logic
- For Vendor-Specific DLLPs (see § Figure 3-13)
- It is recommended that receivers silently ignore Vendor-Specific DLLPs unless enabled by implementation specific mechanisms.
- It is recommended that transmitters not send Vendor-Specific DLLPs unless enabled by implementation specific mechanisms.
- For NOP DLLPs (see § Figure 3-7) and NOP2 DLLPs (see § Figure 3-8).
- Receivers shall discard this DLLP without action, unless otherwise specified, after checking it for data integrity. ${ }^{62}$

[^0]
[^0]:    62. This is a special case of the more general rule for unsupported DLLP Type encodings (see § Section 3.6.2.2 and § Section 3.6.2.3).

- For Data Link Feature DLLPs (see § Figure 3-14)
- The Feature Ack bit is Set to 1b to indicate that the transmitting Port has received a Data Link Feature DLLP.
- The Feature Supported field indicates the Data Link Features supported and/or attribute values for the transmitting Port. The individual bits of this field are defined in § Table 3-1.
- For Link Management DLLPs (see § Figure 3-15)
- In Non-Flit Mode, receivers shall discard this DLLP without action after checking it for data integrity. ${ }^{63}$
![img-5.jpeg](03_Knowledge/Tech/PCIe/03_Data_Link_Layer/img-5.jpeg)

Figure 3-6 Data Link Layer Packet Format for Ack and Nak (Non-Flit Mode)
![img-6.jpeg](03_Knowledge/Tech/PCIe/03_Data_Link_Layer/img-6.jpeg)

Figure 3-7 Data Link Layer Packet Format for NOP
![img-7.jpeg](03_Knowledge/Tech/PCIe/03_Data_Link_Layer/img-7.jpeg)

Figure 3-8 Data Link Layer Packet Format for NOP2 (Flit Mode)

![img-8.jpeg](03_Knowledge/Tech/PCIe/03_Data_Link_Layer/img-8.jpeg)

Figure 3-9 Data Link Layer Packet Format for InitFC1

See also § Table 3-2 and § Table 3-3. Note: In Base 6.0.1, the encoding of byte 0 , bit 3 in $\S$ Figure 3-9 was updated to match § Table 3-3.
![img-9.jpeg](03_Knowledge/Tech/PCIe/03_Data_Link_Layer/img-9.jpeg)

Figure 3-10 Data Link Layer Packet Format for InitFC2

See also § Table 3-2 and § Table 3-3. Note: In Base 6.0.1, the encoding of byte 0 , bit 3 in $\S$ Figure 3-10 was updated to match § Table 3-3.

![img-10.jpeg](03_Knowledge/Tech/PCIe/03_Data_Link_Layer/img-10.jpeg)

Figure 3-11 Data Link Layer Packet Format for UpdateFC 5

Note: In Base 6.0.1, the encoding of byte 0 , bit 3 in $\S$ Figure 3-11 was updated to match $\S$ Table 3-3.
![img-11.jpeg](03_Knowledge/Tech/PCIe/03_Data_Link_Layer/img-11.jpeg)

Figure 3-12 Data Link Layer Packet Format for Power Management 6
![img-12.jpeg](03_Knowledge/Tech/PCIe/03_Data_Link_Layer/img-12.jpeg)

Figure 3-13 Data Link Layer Packet Format for Vendor-Specific 6

![img-13.jpeg](03_Knowledge/Tech/PCIe/03_Data_Link_Layer/img-13.jpeg)

Figure 3-14 Data Link Layer Packet Format for Data Link Feature DLLP

![img-14.jpeg](03_Knowledge/Tech/PCIe/03_Data_Link_Layer/img-14.jpeg)

Figure 3-15 Data Link Packet Layer Format for Link Management (Flit Mode)

The following are the characteristics and rules associated with Data Link Layer Packets (DLLPs):

- DLLPs are differentiated from TLPs when they are presented to, or received from, the Physical Layer.
- DLLP data integrity is protected using a 16-bit CRC (NFM only)
- The CRC value is calculated using the following rules (see $\S$ Figure 3-16):
- The polynomial used for CRC calculation has a coefficient expressed as 100Bh
- The seed value (initial value for CRC storage registers) is FFFFh
- CRC calculation starts with bit 0 of byte 0 and proceeds from bit 0 to bit 7 of each byte
- Note that CRC calculation uses all bits of the DLLP, regardless of field type, including Reserved fields. The result of the calculation is complemented, then placed into the 16-bit CRC field of the DLLP as shown in § Table 3-7.

Table 3-7 Mapping of Bits into CRC Field

| CRC Result Bit | Corresponding Bit Position in the 16-Bit CRC Field |
| :--: | :--: |
| 0 | 7 |
| 1 | 6 |
| 2 | 5 |
| 3 | 4 |
| 4 | 3 |

| CRC Result Bit | Corresponding Bit Position in the 16-Bit CRC Field |
| :--: | :--: |
| 5 | 2 |
| 6 | 1 |
| 7 | 0 |
| 8 | 15 |
| 9 | 14 |
| 10 | 13 |
| 11 | 12 |
| 12 | 11 |
| 13 | 10 |
| 14 | 9 |
| 15 | 8 |

![img-15.jpeg](03_Knowledge/Tech/PCIe/03_Data_Link_Layer/img-15.jpeg)

Figure 3-16 Diagram of CRC Calculation for DLLPs

# 3.6 Data Integrity Mechanisms 8 

### 3.6.1 Introduction 9

The Transaction Layer provides TLP boundary information to the Data Link Layer. This allows the Data Link Layer to apply a TLP Sequence Number and a Link CRC (LCRC) for error detection to the TLP. The Receive Data Link Layer validates received TLPs by checking the TLP Sequence Number, LCRC code and any error indications from the Receive Physical Layer. In case any of these errors are in a TLP, Data Link Layer Retry is used for recovery.

The format of a TLP with the TLP Sequence Number and LCRC code applied is shown in § Figure 3-17.

![img-16.jpeg](03_Knowledge/Tech/PCIe/03_Data_Link_Layer/img-16.jpeg)
![img-17.jpeg](03_Knowledge/Tech/PCIe/03_Data_Link_Layer/img-17.jpeg)

OM13786A
Figure 3-17 TLP with LCRC and TLP Sequence Number Applied - Non-Flit Mode

On Ports that support Protocol Multiplexing, packets containing a non-zero value in Symbol +0 , bits 7:4 are PMUX Packets. For TLPs, these bits must be 0000b. See § Appendix G. for details.

On Ports that do not support Protocol Multiplexing, Symbol +0 , bits 7:4 are Reserved.

# 3.6.2 LCRC, Sequence Number, and Retry Management (TLP Transmitter) 

The TLP transmission path through the Data Link Layer (paths labeled 1 and 3 in § Figure 3-1) prepares each TLP for transmission by applying a sequence number, then calculating and appending a Link CRC (LCRC), which is used to ensure the integrity of TLPs during transmission across a Link from one component to another. TLPs are stored in a retry buffer, and are re-sent unless a positive acknowledgement of receipt is received from the other component. If repeated attempts to transmit a TLP are unsuccessful, the Transmitter will determine that the Link is not operating correctly, and will instruct the Physical Layer to retrain the Link (via the LTSSM Recovery state, § Section 4.2.7). If Link retraining fails, the Physical Layer will indicate that the Link is no longer up, causing the DLCMSM to move to the DL_Inactive state.

The mechanisms used to determine the TLP LCRC and the Sequence Number and to support Data Link Layer Retry are described in terms of conceptual counters and flags. This description does not imply nor require a particular implementation and is used only to clarify the requirements.

### 3.6.2.1 LCRC and Sequence Number Rules (TLP Transmitter)

The following counters and timer are used to explain the remaining rules in this section:

- The following 12-bit counters are used:
- NEXT_TRANSMIT_SEQ - Stores the packet sequence number applied to TLPs
- Set to 000 h in DL_Inactive state
- ACKD_SEQ - Stores the sequence number acknowledged in the most recently received Ack or Nak DLLP.
- Set to FFFh in DL_Inactive state
- The following 3-bit counter is used:
- REPLAY_NUM - Counts the number of times the Retry Buffer has been re-transmitted

- Set to 000b in DL_Inactive state
- The following timer is used:
- REPLAY_TIMER - Counts time that determines when a replay is required, according to the following rules:
- Started at the last Symbol of any TLP transmission or retransmission, if not already running
- For each replay, reset and restart REPLAY_TIMER when sending the last Symbol of the first TLP to be retransmitted
- Resets and restarts for each Ack DLLP received while there are more unacknowledged TLPs outstanding, if, and only if, the received Ack DLLP acknowledges some TLP in the retry buffer.
- Note: This ensures that REPLAY_TIMER is reset only when forward progress is being made
- Reset and hold until restart conditions are met for each Nak received (except during a replay) or when the REPLAY_TIMER expires
- Not advanced during Link retraining (holds its value when the LTSSM is in the Recovery or Configuration state). Refer to § Section 4.2.6.3 and § Section 4.2.6.4.
- If Protocol Multiplexing is supported, optionally not advanced during the reception of PMUX Packets (see § Appendix G. ).
- Resets and holds when there are no outstanding unacknowledged TLPs

The following rules describe how a TLP is prepared for transmission before being passed to the Physical Layer:

- The Transaction Layer indicates the start and end of the TLP to the Data Link Layer while transferring the TLP
- The Data Link Layer treats the TLP as a "black box" and does not process or modify the contents of the TLP
- Each TLP is assigned a 12-bit sequence number when it is accepted from the Transmit side of the Transaction Layer
- Upon acceptance of the TLP from the Transaction Layer, the packet sequence number is applied to the TLP by:
- prepending the 12-bit value in NEXT_TRANSMIT_SEQ to the TLP
- prepending 4 bits to the TLP, preceding the sequence number (see § Figure 3-18)
- If the equation:
(NEXT_TRANSMIT_SEQ -ACKD_SEQ) $\bmod 4096>=2048$
Equation 3-1 Tx SEQ Stall
is true, the Transmitter must cease accepting TLPs from the Transaction Layer until the equation is no longer true
- Following the application of NEXT_TRANSMIT_SEQ to a TLP accepted from the Transmit side of the Transaction Layer, NEXT_TRANSMIT_SEQ is incremented (except in the case where the TLP is nullified):

NEXT_TRANSMIT_SEQ = (NEXT_TRANSMIT_SEQ + 1) mod 4096
Equation 3-2 Tx SEQ Update 5
![img-18.jpeg](03_Knowledge/Tech/PCIe/03_Data_Link_Layer/img-18.jpeg)

OM13787A
Figure 3-18 TLP Following Application of TLP Sequence Number and 4 Bits

- TLP data integrity is protected during transfer between Data Link Layers using a 32-bit LCRC
- The LCRC value is calculated using the following mechanism (see § Figure 3-19):
- The polynomial used has coefficients expressed as 04C1 1DB7h
- The seed value (initial value for LCRC storage registers) is FFFF FFFFh
- The LCRC is calculated using the TLP following sequence number application (see § Figure 3-18)
- LCRC calculation starts with bit 0 of byte 0 (bit 8 of the TLP sequence number) and proceeds from bit 0 to bit 7 of each successive byte.
- Note that LCRC calculation uses all bits of the TLP, regardless of field type, including Reserved fields
- The remainder of the LCRC calculation is complemented, and the complemented result bits are mapped into the 32-bit LCRC field as shown in § Table 3-8.

Table 3-8 Mapping of Bits into LCRC Field

| LCRC Result Bit | Corresponding Bit Position in the 32-Bit LCRC Field |
| :--: | :--: |
| 0 | 7 |
| 1 | 6 |
| 2 | 5 |
| 3 | 4 |
| 4 | 3 |
| 5 | 2 |
| 6 | 1 |
| 7 | 0 |
| 8 | 15 |
| 9 | 14 |
| 10 | 13 |
| 11 | 12 |

| LCRC Result Bit | Corresponding Bit Position in the 32-Bit LCRC Field |
| :--: | :--: |
| 12 | 11 |
| 13 | 10 |
| 14 | 9 |
| 15 | 8 |
| 16 | 23 |
| 17 | 22 |
| 18 | 21 |
| 19 | 20 |
| 20 | 19 |
| 21 | 18 |
| 22 | 17 |
| 23 | 16 |
| 24 | 31 |
| 25 | 30 |
| 26 | 29 |
| 27 | 28 |
| 28 | 27 |
| 29 | 26 |
| 30 | 25 |
| 31 | 24 |

![img-19.jpeg](03_Knowledge/Tech/PCIe/03_Data_Link_Layer/img-19.jpeg)

Figure 3-19 Calculation of LCRC

The 32-bit LCRC field is appended to the TLP following the bytes received from the Transaction Layer (see § Figure 3-17).

To support cut-through routing of TLPs, a Transmitter is permitted to modify a transmitted TLP to indicate that the Receiver must ignore that TLP ("nullify" the TLP).

- A Transmitter is permitted to nullify a TLP being transmitted. To do this in a way that will robustly prevent misinterpretation or corruption, the Transmitter must do the following:
- Transmit all DWs of the TLP when the Physical Layer is using 128b/130b encoding (see § Section 4.2.2.3.1)
- Use the remainder of the calculated LCRC value without inversion (the logical inverse of the value normally used)
- Indicate to the Transmit Physical Layer that the TLP is nullified
- When this is done, the Transmitter does not increment NEXT_TRANSMIT_SEQ

The following rules describe the operation of the Data Link Layer Retry Buffer, from which TLPs are re-transmitted when necessary:

- Copies of Transmitted TLPs must be stored in the Data Link Layer Retry Buffer, except for nullified TLPs.

When a replay is initiated, either due to reception of a Nak or due to REPLAY_TIMER expiration, the following rules describe the sequence of operations that must be followed:

- If all TLPs transmitted have been acknowledged (the Retry Buffer is empty), terminate replay, otherwise continue.
Note: In Flit Mode, Replay occurs at the Flit Level. See § Section 4.2.3.4.2.1.7 .
- Increment REPLAY_NUM by 2 when operating in Non-Flit Mode. If the Data Rate is $32.0 \mathrm{GT} / \mathrm{s}$ or lower, increment REPLAY_NUM by 2 . When the replay is initiated by the reception of a Nak that acknowledged some TLPs in the retry buffer, REPLAY_NUM is reset. It is then permitted (but not required) to be incremented.
- If REPLAY_NUM rolls over from 110b or 111b to either 000b or 001b, the Transmitter signals the Physical Layer to retrain the Link, and waits for the completion of retraining before proceeding with the replay. This is a reported error associated with the Port (see § Section 6.2).

Note that Data Link Layer state, including the contents of the Retry Buffer, are not reset by this action unless the Physical Layer reports Physical LinkUp = 0b (causing the Data Link Control and Management State Machine to transition to the DL_Inactive state).

- If REPLAY_NUM does not roll over from 110b or 111b to either 000b or 001b, continue with the replay.
- Block acceptance of new TLPs from the Transmit Transaction Layer.
- Complete transmission of any TLP currently being transmitted.
- Retransmit unacknowledged TLPs, starting with the oldest unacknowledged TLP and continuing in original transmission order
- Reset and restart REPLAY_TIMER when sending the last Symbol of the first TLP to be retransmitted
- Once all unacknowledged TLPs have been re-transmitted, return to normal operation.
- If any Ack or Nak DLLPs are received during a replay, the Transmitter is permitted to complete the replay without regard to the Ack or Nak DLLP(s), or to skip retransmission of any newly acknowledged TLPs.
- Once the Transmitter has started to resend a TLP, it must complete transmission of that TLP in all cases.
- Ack and Nak DLLPs received during a replay must be processed, and may be collapsed

- Example: If multiple Acks are received, only the one specifying the latest Sequence Number value must be considered - Acks specifying earlier Sequence Number values are effectively "collapsed" into this one
- Example: During a replay, Nak is received, followed by an Ack specifying a later Sequence Number - the Ack supersedes the Nak, and the Nak is ignored.
Note: Since all entries in the Retry Buffer have already been allocated space in the Receiver by the Transmitter's Flow Control gating logic, no further flow control synchronization is necessary.
- Re-enable acceptance of new TLPs from the Transmit Transaction Layer.

A replay can be initiated by the expiration of REPLAY_TIMER, or by the receipt of a Nak. The following rule covers the expiration of REPLAY_TIMER:

- If the Transmit Retry Buffer contains TLPs for which no Ack or Nak DLLP has been received, and (as indicated by REPLAY_TIMER) no Ack or Nak DLLP has been received for a period exceeding the applicable REPLAY_TIMER Limit, the Transmitter initiates a replay.
- Simplified REPLAY_TIMER Limits are:
- A value from 24,000 to 31,000 (inclusive) Symbol Times (-0\%/+0\%) when the Extended Synch bit is Clear.
- A value from 80,000 to 100,000 (inclusive) Symbol Times (-0\%/+0\%) when the Extended Synch bit is Set.
- If the Extended Synch bit changes state while unacknowledged TLPs are outstanding, implementations are permitted to adjust their REPLAY_TIMER Limit when the Extended Synch bit changes state or the next time the REPLAY_TIMER is reset.
- Implementations that support $16.0 \mathrm{GT} / \mathrm{s}$ or higher data rates must use the Simplified REPLAY_TIMER Limits for operation at all data rates when operating in Non-Flit Mode.
- Implementations that only support data rates less than $16.0 \mathrm{GT} / \mathrm{s}$ are strongly recommended to use the Simplified REPLAY_TIMER Limits for operation at all data rates when operating in Non-Flit Mode, but they are permitted to use the REPLAY_TIMER Limits described in the [PCIe-3.1].
- The Replay Timeout rules defined in Replay Schedule Rule 0 in § Section 4.2.3.4.2.1.6 must be used for operation at all data rates in Flit Mode.

This is a Replay Timer Timeout error and it is a reported error associated with the Port (see § Section 6.2 ).

# IMPLEMENTATION NOTE: DETERMINING REPLAY_TIMER LIMIT VALUES § 

Replays are initiated primarily with a Nak DLLP, and the REPLAY_TIMER serves as a secondary mechanism. Since it is a secondary mechanism, the REPLAY_TIMER Limit has a relatively small effect on the average time required to convey a TLP across a Link. The Simplified REPLAY_TIMER Limits have been defined so that no adjustments are required for ASPM LOs, Retimers, or other items as in previous revisions of this specification.

TLP Transmitters and compliance tests must base replay timing as measured at the Port of the TLP Transmitter. Timing starts with either the last Symbol of a transmitted TLP, or else the last Symbol of a received Ack DLLP, whichever determines the oldest unacknowledged TLP. Timing ends with the First Symbol of TLP retransmission.

When measuring replay timing to the point when TLP retransmission begins, compliance tests must allow for any other TLP or DLLP transmission already in progress in that direction (thus preventing the TLP retransmission).

# IMPLEMENTATION NOTE: <br> RECOMMENDED PRIORITY OF SCHEDULED TRANSMISSIONS 

When multiple DLLPs of the same type are scheduled for transmission but have not yet been transmitted, it is possible in many cases to "collapse" them into a single DLLP. For example, if a scheduled Ack DLLP transmission is stalled waiting for another transmission to complete, and during this time another Ack is scheduled for transmission, it is only necessary to transmit the second Ack, since the information it provides will supersede the information in the first Ack.

In addition to any TLP from the Transaction Layer (or the Retry Buffer, if a replay is in progress), multiple DLLPs of different types may be scheduled for transmission at the same time, and must be prioritized for transmission. The following list shows the preferred priority order for selecting information for transmission. Note that the priority of the NOP DLLP and the Vendor-Specific DLLP is not listed, as usage of these DLLPs is completely implementation specific, and there is no recommended priority. Note that this priority order is a guideline, and that in all cases a fairness mechanism is strongly recommended to ensure that no type of traffic is blocked for an extended or indefinite period of time by any other type of traffic. Note that the Ack Latency Limit value and REPLAY_TIMER Limit specify requirements measured at the Port of the component, and the internal arbitration policy of the component must ensure that these externally measured requirements are met.

In Flit Mode, DLP information is contained in every Flit and can contain either a DLLP, Optimized_Update_FC, or a Flit_Marker. Currently defined Flit_Markers are related to a specific TLP and have the higest priority. Future Flit_Markers may have lower priorities.

| Recommended <br> Priority | Non-Flit Mode | Flit Mode |
| :--: | :-- | :-- |
| 1 | Completion of any transmission (TLP or DLLP) <br> currently in progress (highest priority). | n/a: DLP information is independent of TLPs |
| 2 | n/a: Poison and Nullify use TLP Framing | Poisoned TLP and Nullified TLP Flit_Markers |
| 3 | Nak DLLP Transmissions | n/a: Ack and Nak use dedicated DLP Symbols, not <br> DLLPs |
| 4 | Ack DLLP transmissions scheduled for transmission <br> as soon as possible due to: receipt of a duplicate <br> TLP -OR- expiration of the Ack latency timer (see <br> \$ Section 3.6.3.1). |  |
| 5 | Flow Control required to satisfy \$ Section 2.6 : <br> UpdateFC DLLPs | Flow Control required to satisfy \$ Section 2.6 : <br> UpdateFC DLLPs and/or Optimized_Update_FC |
| 6 | Retry Buffer re-transmissions | n/a: DLP information is independent of TLPs |
| 7 | TLPs from the Transaction Layer | Flow Control other than that required to satisfy <br> \$ Section 2.6 : <br> Optimized_Update_FC and/or UpdateFC DLLPs |
| 8 | Flow Control other than that required to satisfy <br> \$ Section 2.6 : <br> UpdateFC DLLPs |  |

# 3.6.2.2 Handling of Received DLLPs (Non-Flit Mode) 

Since Ack/Nak and Flow Control DLLPs affect TLPs flowing in the opposite direction across the Link, the TLP transmission mechanisms in the Data Link Layer are also responsible for Ack/Nak and Flow Control DLLPs received from the other component on the Link. These DLLPs are processed according to the following rules (see § Figure 3-20):

- If the Physical Layer indicates a Receiver Error, discard any DLLP currently being received and free any storage allocated for the DLLP. Note that reporting such errors to software is done by the Physical Layer (and, therefore, are not reported by the Data Link Layer).
- For all received DLLPs, the CRC value is checked by:
- Applying the same algorithm used for calculation of transmitted DLLPs to the received DLLP, not including the 16-bit CRC field of the received DLLP
- Comparing the calculated result with the value in the CRC field of the received DLLP
- If not equal, the DLLP is corrupt
- A corrupt received DLLP is discarded. This is a Bad DLLP error and is a reported error associated with the Port (see § Section 6.2 ).
- A received DLLP that is not corrupt, but that uses unsupported DLLP Type encodings is discarded without further action. This is not considered an error.
- Values in Reserved fields are ignored.
- Receivers must process all DLLPs received at the rate they are received
![img-20.jpeg](03_Knowledge/Tech/PCIe/03_Data_Link_Layer/img-20.jpeg)

Figure 3-20 Received DLLP Error Check Flowchart

- Received NOP DLLPs are discarded
- Note: NOP2 DLLPs do not exist in Non-Flit Mode, as that encoding encoding is used for the Ack DLLP.
- Received FC DLLPs are passed to the Transaction Layer
- Received PM DLLPs are passed to the component's power management control logic
- For Ack and Nak DLLPs, the following steps are followed (see § Figure 3-21):
- If the Sequence Number specified by the AckNak_Seq_Num does not correspond to an unacknowledged TLP, or to the value in ACKD_SEQ, the DLLP is discarded
- This is a Data Link Protocol Error, which is a reported error associated with the Port (see § Section 6.2).

Note that it is not an error to receive an Ack DLLP when there are no outstanding unacknowledged TLPs, including the time between reset and the first TLP transmission, as long as the specified Sequence Number matches the value in ACKD_SEQ.

- If the AckNak_Seq_Num does not specify the Sequence Number of the most recently acknowledged TLP, then the DLLP acknowledges some TLPs in the retry buffer:
- Purge from the retry buffer all TLPs from the oldest to the one corresponding to the AckNak_Seq_Num
- Load ACKD_SEQ with the value in the AckNak_Seq_Num field
- Reset REPLAY_NUM and REPLAY_TIMER
- If the DLLP is a Nak, initiate a replay (see above)

Note: Receipt of a Nak is not a reported error.
![img-21.jpeg](03_Knowledge/Tech/PCIe/03_Data_Link_Layer/img-21.jpeg)

Figure 3-21 Ack/Nak DLLP Processing Flowchart

The following rules describe the operation of the Data Link Layer Retry Buffer, from which TLPs are re-transmitted when necessary:

- Copies of Transmitted TLPs must be stored in the Data Link Layer Retry Buffer


# 3.6.2.3 Handling of Received DLLPs (Flit Mode) 

Since Flow Control DLLPs affect TLPs flowing in the opposite direction across the Link, the TLP transmission mechanisms in the Data Link Layer are also responsible for Flow Control DLLPs received from the other component on the Link. These DLLPs are processed according to the following rules:

- In Flit Mode, detection of corrupt DLLPs occurs at the Flit level and there is no corruption check for DLLPs in the Data Link Layer.
- In Flit Mode, replay occurs at the Flit level and the Ack and Nak DLLPs are not used.
- DLLPs and Optimized_Update_FCs are not stored in the Replay Buffer.
- When a Flit is replayed, the DLP information is likely to be different from the original value.
- Flit_Markers are associated with the TLP payload and are stored in the Replay Buffer.
- A received DLLP that uses unsupported DLLP Type encodings is discarded without further action. This is not considered an error.
- Non-zero values in Reserved fields are ignored.
- Receivers must process all DLLPs received at the rate they are received
- Received NOP DLLPs and NOP2 DLLPs are discarded
- Received FC DLLPs are passed to the Transaction Layer

- Received Optimized_Update_FCs are passed to the Transaction Layer
- Received PM DLLPs are passed to the component's power management control logic
- Received Link Management DLLPs are passed to the component's L0p control logic


# 3.6.3 LCRC and Sequence Number (TLP Receiver) (Non-Flit Mode) 

The TLP Receive path through the Data Link Layer (paths labeled 2 and 4 in § Figure 3-1) processes TLPs received by the Physical Layer by checking the LCRC and sequence number, passing the TLP to the Receive Transaction Layer if OK and requesting a replay if corrupted.

The mechanisms used to check the TLP LCRC and the Sequence Number and to support Data Link Layer Retry are described in terms of conceptual counters and flags. This description does not imply or require a particular implementation and is used only to clarify the requirements.

### 3.6.3.1 LCRC and Sequence Number Rules (TLP Receiver)

The following counter, flag, and timer are used to explain the remaining rules in this section:

- The following 12-bit counter is used:
- NEXT_RCV_SEQ - Stores the expected Sequence Number for the next TLP
- Set to 000 h in DL_Inactive state
- The following flag is used:


## - NAK_SCHEDULED

- Cleared when in DL_Inactive state
- The following timer is used:
- AckNak_LATENCY_TIMER - Counts time that determines when an Ack DLLP becomes scheduled for transmission, according to the following rules:
- Set to 0 in DL_Inactive state
- Restart from 0 each time an Ack or Nak DLLP is scheduled for transmission; Reset to 0 when all TLPs received have been acknowledged with an Ack DLLP
- If there are initially no unacknowledged TLPs and a TLP is then received, the AckNak_LATENCY_TIMER starts counting only when the TLP has been forwarded to the Receive Transaction Layer

The following rules are applied in sequence to describe how received TLPs are processed, and what events trigger the transmission of Ack and Nak DLLPs (see § Figure 3-22):

- If the Physical Layer indicates a Receiver Error, discard any TLP currently being received and free any storage allocated for the TLP. Note that reporting such errors to software is done by the Physical Layer (and so are not reported by the Data Link Layer).
- If a TLP was being received at the time the Receiver Error was indicated and the NAK_SCHEDULED flag is clear,
- Schedule a Nak DLLP for transmission immediately
- Set the NAK_SCHEDULED flag
- If the Physical Layer reports that the received TLP was nullified, and the LCRC is the logical NOT of the calculated value, discard the TLP and free any storage allocated for the TLP. This is not considered an error.

- If TLP was nullified but the LCRC does not match the logical NOT of the calculated value, the TLP is corrupt discard the TLP and free any storage allocated for the TLP.
- If the NAK_SCHEDULED flag is clear,
- Schedule a Nak DLLP for transmission immediately
- Set the NAK_SCHEDULED flag

This is a Bad TLP error and is a reported error associated with the Port (see § Section 6.2 ).

- The LCRC value is checked by:
- Applying the same algorithm used for calculation (above) to the received TLP, not including the 32-bit LCRC field of the received TLP
- Comparing the calculated result with the value in the LCRC field of the received TLP
- if not equal, the TLP is corrupt - discard the TLP and free any storage allocated for the TLP
- If the NAK_SCHEDULED flag is clear,
- schedule a Nak DLLP for transmission immediately
- set the NAK_SCHEDULED flag

This is a Bad TLP error and is a reported error associated with the Port (see § Section 6.2 ).

- If the TLP Sequence Number is not equal to the expected value, stored in NEXT_RCV_SEQ:
- Discard the TLP and free any storage allocated for the TLP
- If the TLP Sequence Number satisfies the following equation:
(NEXT_RCV_SEQ - TLP Sequence Number) mod $4096<=2048$
the TLP is a duplicate, and an Ack DLLP is scheduled for transmission (per transmission priority rules)
- Otherwise, the TLP is out of sequence (indicating one or more lost TLPs):
- if the NAK_SCHEDULED flag is clear,
- schedule a Nak DLLP for transmission immediately
- set the NAK_SCHEDULED flag
- This is a Bad TLP error and is a reported error associated with the Port (see § Section 6.2).
- if the NAK_SCHEDULED flag is Set, the Port is permitted to, but is not recommended to, report a Bad TLP error associated with the Port (see § Section 6.2 ) and this permission is shown in § Figure 3-20.
- If the TLP Sequence Number is equal to the expected value stored in NEXT_RCV_SEQ:
- The four bits, TLP Sequence Number, and LCRC (see § Figure 3-17) are removed and the remainder of the TLP is forwarded to the Receive Transaction Layer
- The Data Link Layer indicates the start and end of the TLP to the Transaction Layer while transferring the TLP
- The Data Link Layer treats the TLP as a "black box" and does not process or modify the contents of the TLP
- Note that the Receiver Flow Control mechanisms do not account for any received TLPs until the TLP(s) are forwarded to the Receive Transaction Layer
- NEXT_RCV_SEQ is incremented
- If Set, the NAK_SCHEDULED flag is cleared

![img-22.jpeg](03_Knowledge/Tech/PCIe/03_Data_Link_Layer/img-22.jpeg)

Figure 3-22 Receive Data Link Layer Handling of TLPs Flowchart

- A TLP Receiver must schedule an Ack DLLP such that it will be transmitted no later than when all of the following conditions are true:
- The Data Link Control and Management State Machine is in the DL_Active state
- TLPs have been forwarded to the Receive Transaction Layer, but not yet acknowledged by sending an Ack DLLP
- The AckNak_LATENCY_TIMER reaches or exceeds the value specified in § Table 3-10 for 2.5 GT/s operation, § Table 3-11 for 5.0 GT/s operation, § Table 3-12 for 8.0 GT/s and higher operation
- The Link used for Ack DLLP transmission is already in L0 or has transitioned to L0
- Note: if not already in L0, the Link must transition to L0 in order to transmit the Ack DLLP
- Another TLP or DLLP is not currently being transmitted on the Link used for Ack DLLP transmission
- The NAK_SCHEDULED flag is clear
- Note: The AckNak_LATENCY_TIMER must be restarted from 0 each time an Ack or Nak DLLP is scheduled for transmission
- Data Link Layer Ack DLLPs may be scheduled for transmission more frequently than required
- Data Link Layer Ack and Nak DLLPs specify the value (NEXT_RCV_SEQ - 1) in the AckNak_Seq_Num field
§ Table 3-10, § Table 3-11, and § Table 3-12 define the threshold values for the AckNak_LATENCY_TIMER, which for any specific case is called the Ack Latency Limit.

TLP Receivers and compliance tests must base Ack Latency timing as measured at the Port of the TLP Receiver, starting with the time the last Symbol of a TLP is received to the first Symbol of the Ack DLLP being transmitted.

When measuring until the Ack DLLP is transmitted, compliance tests must allow for any TLP or other DLLP transmission already in progress in that direction (thus preventing the Ack DLLP transmission). If LOs is enabled, compliance tests must allow for the LOs exit latency of the Link in the direction that the Ack DLLP is being transmitted. If the Extended Synch bit is Set, compliance tests must also allow for its effect on LOs exit latency.

TLP Receivers are not required to adjust their Ack DLLP scheduling based upon LOs exit latency or the value of the Extended Synch bit.

For a Multi-Function Device where different Functions have different Rx_MPS_Limit values, it is strongly recommended that the smallest Rx_MPS_Limit value across all Functions be used.

Table 3-10 Maximum Ack Latency Limits for 2.5 GT/s (Symbol Times) (-0\%/+0\%)

|  |  | Link Operating Width |  |  |  |  |
| :--: | :--: | :--: | :--: | :--: | :--: | :--: |
|  |  | x1 | x2 | x4 | x8 | x16 |
| Rx_MPS_Limit (bytes) | 128 | 237 | 128 | 73 | 67 | 48 |
|  | 256 | 416 | 217 | 118 | 107 | 72 |
|  | 512 | 559 | 289 | 154 | 86 | 86 |
|  | 1024 | 1071 | 545 | 282 | 150 | 150 |
|  | 2048 | 2095 | 1057 | 538 | 278 | 278 |
|  | 4096 | 4143 | 2081 | 1050 | 534 | 534 |

Table 3-11 Maximum Ack Latency Limits for 5.0 GT/s (Symbol Times) (-0\%/+0\%)

|  |  | Link Operating Width |  |  |  |  |
| :--: | :--: | :--: | :--: | :--: | :--: | :--: |
|  |  | x1 | x2 | x4 | x8 | x16 |
| Rx_MPS_Limit (bytes) | 128 | 288 | 179 | 124 | 118 | 99 |
|  | 256 | 467 | 268 | 169 | 158 | 123 |
|  | 512 | 610 | 340 | 205 | 137 | 137 |
|  | 1024 | 1122 | 596 | 333 | 201 | 201 |
|  | 2048 | 2146 | 1108 | 589 | 329 | 329 |
|  | 4096 | 4194 | 2132 | 1101 | 585 | 585 |

Table 3-12 Maximum Ack Latency Limits for 8.0 GT/s and higher data rates (Symbol Times)

|  |  | Link Operating Width |  |  |  |  |
| :--: | :--: | :--: | :--: | :--: | :--: | :--: |
|  |  | x1 | x2 | x4 | x8 | x16 |
| Rx_MPS_Limit (bytes) | 128 | 333 | 224 | 169 | 163 | 144 |
|  | 256 | 512 | 313 | 214 | 203 | 168 |
|  | 512 | 655 | 385 | 250 | 182 | 182 |
|  | 1024 | 1167 | 641 | 378 | 246 | 246 |
|  | 2048 | 2191 | 1153 | 634 | 374 | 374 |
|  | 4096 | 4239 | 2177 | 1146 | 630 | 630 |

# IMPLEMENTATION NOTE: RETRY BUFFER SIZING 

The Retry Buffer should be large enough to ensure that under normal operating conditions, transmission is never throttled because the retry buffer is full. In determining the optimal buffer size, one must consider the Ack Latency value, Ack delay caused by the Receiver already transmitting another TLP or DLLP, the delays caused by the physical Link interconnect, and the time required to process the received Ack DLLP.

Given two components $A$ and $B$, the LOs exit latency required by A's Receiver should be accounted for when sizing A's transmit retry buffer, as is demonstrated in the following example:

- A exits LOs on its Transmit path to B and starts transmitting a long burst of write Requests to B
- B initiates LOs exit on its Transmit path to A, but the LOs exit time required by A's Receiver is large
- Meanwhile, B is unable to send Ack DLLPs to A, and A stalls due to lack of Retry Buffer space
- The Transmit path from B to A returns to L0, B transmits an Ack DLLP to A, and the stall is resolved

This stall can be avoided by matching the size of a component's Transmitter Retry Buffer to the LOs exit latency required by the component's Receiver, or, conversely, by matching the Receiver LOs exit latency to the desired size of the Retry Buffer.

Ack Latency Limit values were chosen to allow implementations to achieve good performance without requiring an uneconomically large retry buffer. To enable consistent performance across a general purpose interconnect with differing implementations and applications, it is necessary to set the same requirements for all components without regard to the application space of any specific component. If a component does not require the full transmission bandwidth of the Link, it may reduce the size of its retry buffer below the minimum size required to maintain available retry buffer space with the Ack Latency Limit values specified.

Note that the Ack Latency Limit values specified ensure that the range of permitted outstanding TLP Sequence Numbers will never be the limiting factor causing transmission stalls.

Retimers add latency (see § Section 4.3.8 ) and operating in SRIS can add latency. Implementations are strongly encouraged to consider these effects when determining the optimal buffer size.

6.3-1.0-PUB - PCI Express ${ }^{\circledR}$ Base Specification Revision 6.3

