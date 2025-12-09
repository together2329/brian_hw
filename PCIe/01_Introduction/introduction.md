# 1. Introduction 

This chapter presents an overview of the PCI Express architecture and key concepts. PCI Express is a high-performance, general purpose I/O interconnect defined for a wide variety of future computing and communication platforms. Key attributes, such as usage model, load-store architecture, and software interfaces, are maintained from PCI Local Bus, whereas PCI Local Bus's parallel bus implementation is replaced by a highly scalable, fully serial interface. PCI Express takes advantage of advances in point-to-point interconnects, Switch-based technology, and packetized protocol to deliver new levels of performance and features. Power Management, Quality of Service (QoS), Hot-Plug/hot-swap support, data integrity, and error handling are among some of the advanced features supported by PCI Express.

### 1.1 An Evolving I/O Interconnect 

The high-level requirements for this evolving I/O interconnect are as follows:

- Supports multiple market segments and emerging applications:
- Unifying I/O architecture for desktop, mobile, workstation, server, communications platforms, and embedded devices
- Ability to deliver low cost, high volume solutions:
- Cost at or below PCI cost structure at the system level
- Support multiple platform interconnect usages:
- Chip-to-chip, board-to-board via connector or cabling
- A variety of mechanical form factors:
- [M.2], [CEM] (Card Electro-Mechanical), [U.2], [OCuLink]
- PCI-compatible software model:
- Ability to enumerate and configure PCI Express hardware using PCI system configuration software implementations with no modifications
- Ability to boot existing operating systems with no modifications
- Ability to support existing I/O device drivers with no modifications
- Ability to configure/enable new PCI Express functionality by adopting the PCI configuration paradigm


## - Performance:

- Low-overhead, low-latency communications to maximize application payload bandwidth and Link efficiency
- High-bandwidth per pin to minimize pin count per device and connector interface
- Scalable performance via aggregated Lanes and signaling frequency


## - Advanced features:

- Comprehend different data types and ordering rules
- Power management and budgeting
- Ability to identify power management capabilities of a Device of a specific Function
- Ability to transition a Device or Function into a specific power state
- Ability to receive notification of the current power state of a Device of Function
- Ability to generate a request to wakeup from a power-off state of the main power supply

- Ability to sequence Device power-up to allow graceful platform policy in power budgeting
- Ability to support differentiated services, i.e., different (QoS)
- Ability to have dedicated Link resources per QoS data flow to improve fabric efficiency and effective application-level performance in the face of head-of-line blocking
- Ability to configure fabric QoS arbitration policies within every component
- Ability to tag end-to-end QoS with each packet
- Ability to create end-to-end isochronous (time-based, injection rate control) solutions
- Hot-Plug support
- Ability to support existing PCI Hot-Plug solutions
- Ability to support native Hot-Plug solutions (no sideband signals required)
- Ability to support async removal
- Ability to support a unified software model for all form factors
- Data Integrity
- Ability to support Link-level data integrity for all types of transaction and Data Link packets
- Ability to support end-to-end data integrity for high availability solutions
- Error handling
- Ability to support PCI-Compatible error handling
- Ability to support advanced error reporting and handling to improve fault isolation and recovery solutions
- Process Technology Independence
- Ability to support different DC common mode voltages at Transmitter and Receiver
- Ease of Testing
- Ability to test electrical compliance via simple connection to test equipment


# 1.2 PCI Express Link 

A Link represents a dual-simplex communications channel between two components. The fundamental PCI Express Link consists of two, low-voltage, differentially driven signal pairs: a Transmit pair and a Receive pair as shown in § Figure 1-1. A PCI Express Link consists of a PCIe PHY as defined in § Chapter 4. .
![img-0.jpeg](03_Knowledge/Tech/PCIe/01_Introduction/img-0.jpeg)

Figure 1-1 PCI Express Link

The primary Link attributes for PCI Express Link are:

- The basic Link - PCI Express Link consists of dual unidirectional differential Links, implemented as a Transmit pair and a Receive pair. A data clock is embedded using an encoding scheme (see § Chapter 4. ) to achieve very high data rates.
- The Signaling method - Each major revision of PCI Express signaling has evolved one (or more) characteristics to increase bandwidth. Throughout this specification, the term GT/s is used to refer to the number of encoded bits transferred in a second on a direction of a Lane. The actual effective data rate is dependent on a combination of modulation method, encoding method, and data rate. § Table 1-1 provides a summary of Max Data Rate, Modulation Scheme, Encoding Method, and Effective Max Data Rate with the accounting of only encoding overhead for all the six major revisions of PCI Express. ${ }^{7}$ See § Chapter 4. for more information about the combined signaling method and § Chapter 8. for electrical specification details for each major PCI Express revision.

Table 1-1 PCIe Signaling Characteristics

| Data Rate | Modulation | Encoding | Effective Data Rate <br> (after removing Encoding overhead) | Base Specification Revision |  |  |  |  |  |
| :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: |
|  |  |  |  | 6.x | 5.x | 4.x | 3.0 | 2.0 | 1.0 |
| $2.5 \mathrm{GT} / \mathrm{s}$ | NRZ | 8b/10b | 2 Gbit/s | $\checkmark$ | $\checkmark$ | $\checkmark$ | $\checkmark$ | $\checkmark$ | $\checkmark$ |
| $5.0 \mathrm{GT} / \mathrm{s}$ | NRZ | 8b/10b | 4 Gbit/s | $\checkmark$ | $\checkmark$ | $\checkmark$ | $\checkmark$ | $\checkmark$ |  |
| $8.0 \mathrm{GT} / \mathrm{s}$ | NRZ | 128b/130b | $\sim 8$ Gbit/s | $\checkmark$ | $\checkmark$ | $\checkmark$ | $\checkmark$ |  |  |
| $16.0 \mathrm{GT} / \mathrm{s}$ | NRZ | 128b/130b | $\sim 16$ Gbit/s | $\checkmark$ | $\checkmark$ | $\checkmark$ |  |  |  |
| $32.0 \mathrm{GT} / \mathrm{s}$ | NRZ | 128b/130b | $\sim 32$ Gbit/s | $\checkmark$ | $\checkmark$ |  |  |  |  |
| $64.0 \mathrm{GT} / \mathrm{s}$ | PAM4 | 1b/1b | 64 Gbit/s | $\checkmark$ |  |  |  |  |  |

- Lanes - A Link must support at least one Lane - each Lane represents a set of differential signal pairs (one pair for transmission, one pair for reception). To scale bandwidth, a Link may aggregate multiple Lanes denoted by xN where N may be any of the supported Link widths. A x8 Link operating at the $2.5 \mathrm{GT} / \mathrm{s}$ data rate represents an aggregate bandwidth of 20 Gigabits/second of raw bandwidth in each direction. This specification describes operations for $x 1, x 2, x 4, x 8$, and $x 16$ Lane widths.
- Data Stream - PCI Express uses Data Stream in Flit Mode and Data Stream in Non-Flit Mode (see § Section 4.2, including § Table 4-1 and § Table 4-2). Support of Data Stream in Non-Flit Mode is mandatory, while support of Data Stream in Flit Mode is mandatory only if a data rate that exceeds $32.0 \mathrm{GT} / \mathrm{s}$ is supported.
- Initialization - During hardware initialization, each PCI Express Link is set up following a negotiation of Link width, data rate, and Flit mode by the two agents at each end of the Link. No firmware or operating system software is involved.
- Symmetry - Each Link must support a symmetric number of Lanes in each direction, i.e., a x16 Link indicates there are 16 differential signal pairs in each direction.


# 1.3 PCI Express Fabric Topology 

A fabric is composed of point-to-point Links that interconnect a set of components - an example fabric topology is shown in § Figure 1-2. This figure illustrates a single fabric instance with two Hierarchies composed of a Root Complex (RC), multiple Endpoints, and multiple Switches, interconnected via PCI Express Links.

[^0]
[^0]:    2. Terms like "PCIe Gen3" are ambiguous and should be avoided. For example, "gen3" could mean (1) compliant with Base 3.0, (2) compliant with Base 3.1 (last revision of 3.x), (3) compliant with Base 3.0 and supporting $8.0 \mathrm{GT} / \mathrm{s}$, (4) compliant with Base 3.0 or later and supporting $8.0 \mathrm{GT} / \mathrm{s}, \ldots$.

![img-1.jpeg](03_Knowledge/Tech/PCIe/01_Introduction/img-1.jpeg)

Figure 1-2 Example PCI Express Topology

# 1.3.1 Root Complex 

- An RC denotes the root of an I/O hierarchy that connects the CPU/memory subsystem to the I/O.
- As illustrated in § Figure 1-2, an RC may support one or more PCI Express Ports. Each interface defines a separate hierarchy domain. Each hierarchy domain may be composed of a single Endpoint or a sub-hierarchy containing one or more Switch components and Endpoints.
- The capability to route peer-to-peer transactions between hierarchy domains through an RC is optional and implementation dependent. An RC is permitted to "take ownership" of Requests that pass peer-to-peer between Root Ports, reforming and potentially splitting a Request such that it may appear to the ultimate Completer that the RC was the origin of the Request, and subsequently the RC must reform the Completion(s)

being returned to the original Requester. Alternately, an RC implementation may incorporate a real or virtual Switch internally within the Root Complex to enable full peer-to-peer support in a software transparent way. Unlike the rules for a Switch, an RC is generally permitted to split a packet into smaller packets when routing transactions peer-to-peer between hierarchy domains (except as noted below), e.g., split a single packet with a 256-byte payload into two packets of 128 bytes payload each. The resulting packets are subject to the normal packet formation rules contained in this specification (e.g., Max_Payload_Size, Read Completion Boundary (RCB), etc.). Component designers should note that splitting a packet into smaller packets may have negative performance consequences, especially for a transaction addressing a device behind a PCI Express to PCI/PCI-X bridge.

Exception: An RC that supports UIO peer-to-peer routing is permitted to split UIO Memory Write Requests only at naturally aligned 64B boundaries.

Exception: An RC that supports peer-to-peer routing of Deferrable Memory Write Requests is not permitted to split a Deferrable Memory Write Request packet into smaller packets (see § Section 6.32).

Exception: An RC that supports peer-to-peer routing of Vendor-Defined Messages is not permitted to split a Vendor-Defined Message packet into smaller packets except at 128-byte boundaries (i.e., all resulting packets except the last must be an integral multiple of 128 bytes in length) in order to retain the ability to forward the Message across a PCI Express to PCI/PCI-X Bridge.

- An RC must support generation of Configuration Requests as a Requester.
- An RC is permitted to support the generation of I/O Requests as a Requester.
- An RC is permitted to generate I/O Requests to either or both of locations 80 h and 84 h to a selected Root Port, without regard to that Root Port's PCI Bridge I/O decode configuration; it is recommended that this mechanism only be enabled when specifically needed.
- An RC must not support Lock semantics as a Completer.
- An RC is permitted to support generation of Locked Requests as a Requester.


# 1.3.2 Endpoints 

Endpoint refers to a type of Function that can be the Requester or Completer of a PCI Express transaction either on its own behalf or on behalf of a distinct non-PCI Express device (other than a PCI device or host CPU), e.g., a PCI Express attached graphics controller or a PCI Express-USB host controller. Endpoints are classified as either legacy, PCI Express, or Root Complex Integrated Endpoints (RCiEPs).

### 1.3.2.1 Legacy Endpoint Rules

- A Legacy Endpoint must be a Function with a Type 00h Configuration Space header.
- A Legacy Endpoint must support Configuration Requests as a Completer.
- A Legacy Endpoint may support I/O Requests as a Completer.
- A Legacy Endpoint is permitted to accept I/O Requests to either or both of locations 80h and 84h, without regard to that Endpoint's I/O decode configuration.
- A Legacy Endpoint may generate I/O Requests.
- A Legacy Endpoint may support Lock memory semantics as a Completer if that is required by the device's legacy software support requirements.
- A Legacy Endpoint must not issue a Locked Request.

- A Legacy Endpoint may implement Extended Configuration Space Capabilities, but such Capabilities may be ignored by software.
- A Legacy Endpoint operating as the Requester of a Memory Transaction is not required to be capable of generating addresses 4 GB or greater.
- A Legacy Endpoint is required to support MSI or MSI-X or both if an interrupt resource is requested. If MSI is implemented, a Legacy Endpoint is permitted to support either the 32-bit or 64-bit Message Address version of the MSI Capability structure.
- A Legacy Endpoint is permitted to support 32-bit addressing for Base Address Registers that request memory resources.
- A Legacy Endpoint must appear within one of the hierarchy domains originated by the Root Complex.


# 1.3.2.2 PCI Express Endpoint Rules 

- A PCI Express Endpoint must be a Function with a Type 00h Configuration Space header.
- A PCI Express Endpoint must support Configuration Requests as a Completer.
- A PCI Express Endpoint must not depend on operating system allocation of I/O resources claimed through BAR(s).
- A PCI Express Endpoint must not generate I/O Requests.
- A PCI Express Endpoint must not support Locked Requests as a Completer or generate them as a Requester. PCI Express-compliant device drivers and applications must be written to prevent the use of lock semantics when accessing a PCI Express Endpoint.
- A PCI Express Endpoint operating as the Requester of a Memory Transaction is required to be capable of generating addresses greater than 4 GB.
- A PCI Express Endpoint is required to support MSI or MSI-X or both if an interrupt resource is requested. If MSI is implemented, a PCI Express Endpoint must support the 64-bit Message Address version of the MSI Capability structure.
- For generating Memory Requests, 32-bit addressing support is required as described in § Section 2.2.4.1, and 64-bit addressing support is strongly recommended.
- It is strongly recommended for each Memory BAR in a PCI Express component to be 64 bits wide.
- The minimum memory address range requested by a BAR is 128 bytes.
- A PCI Express Endpoint must appear within one of the hierarchy domains originated by the Root Complex.


### 1.3.2.3 Root Complex Integrated Endpoint Rules

- A Root Complex Integrated Endpoint (RCiEP) is implemented on internal logic of Root Complexes that contains the Root Ports.
- An RCIEP must be a Function with a Type 00h Configuration Space header.
- An RCIEP must support Configuration Requests as a Completer.
- An RCIEP must not require I/O resources claimed through BAR(s).
- An RCIEP must not generate I/O Requests.
- An RCIEP must not support Locked Requests as a Completer or generate them as a Requester. PCI Express-compliant device drivers and applications must be written to prevent the use of lock semantics when accessing an RCIEP.

- An RCIEP operating as the Requester of a Memory Transaction is required to be capable of generating addresses equal to or greater than the Host is capable of handling as a Completer.
- An RCIEP is required to support MSI or MSI-X or both if an interrupt resource is requested. If MSI is implemented, an RCIEP is permitted to support either the 32-bit or 64-bit Message Address version of the MSI Capability structure.
- An RCIEP is permitted to support 32-bit addressing for Base Address Registers that request memory resources.
- An RCIEP must not implement Link Capabilities, Link Status, Link Control, Link Capabilities 2, Link Status 2, and Link Control 2 registers in the PCI Express Extended Capability.
- If an RCIEP is associated with an optional Root Complex Event Collector it must signal PME and error conditions through the Root Complex Event Collector.
- An RCIEP must not be associated with more than one Root Complex Event Collector.
- An RCIEP does not implement Active State Power Management.
- An RCIEP may not be hot-plugged independent of the Root Complex as a whole.
- An RCIEP must not appear in any of the hierarchy domains exposed by the Root Complex.
- An RCIEP must not appear in Switches.


# 1.3.3 Switch 

A Switch is defined as a logical assembly of multiple virtual PCI-to-PCI Bridge devices as illustrated in § Figure 1-3. All Switches are governed by the following base rules.
![img-2.jpeg](03_Knowledge/Tech/PCIe/01_Introduction/img-2.jpeg)

Figure 1-3 Logical Block Diagram of a Switch

- Switches appear to configuration software as two or more logical PCI-to-PCI Bridges.
- A Switch forwards transactions using PCI Bridge mechanisms; e.g., address-based routing except when engaged in a Multicast, as defined in § Section 6.14 .
- Except as noted in this document, a Switch must forward all types of Transaction Layer Packets (TLPs) between any set of Ports.
- Locked Requests must be supported as specified in § Section 6.5. Switches are not required to support Downstream Ports as initiating Ports for Locked Requests.
- Each enabled Switch Port must comply with the Flow Control specification within this document.
- A Switch is not allowed to split a packet into smaller packets, e.g., a single packet with a 256-byte payload must not be divided into two packets of 128 bytes payload each.

- Arbitration between Ingress Ports (inbound Link) of a Switch may be implemented using round robin or weighted round robin when contention occurs on the same Virtual Channel. This is described in more detail later within the specification.
- Endpoints (represented by Type 00h Configuration Space headers) must not appear to configuration software on the Switch's internal bus as peers of the virtual PCI-to-PCI Bridges representing the Switch Downstream Ports.


# 1.3.4 Root Complex Event Collector 

- A Root Complex Event Collector (RCEC) provides support for terminating error and PME messages from RCIEPs.
- A Root Complex Event Collector must follow all rules for an RCIEP (unless otherwise specified).
- A Root Complex Event Collector is not required to decode any memory or I/O resources.
- A Root Complex Event Collector is identified by its Device/Port Type value (see § Section 7.5.3.2 ).
- A Root Complex Event Collector has the Base Class 08h, Sub-Class 07h and Programming Interface 00h. ${ }^{3}$
- A Root Complex Event Collector resides on a Bus in the Root Complex. Multiple Root Complex Event Collectors are permitted to reside on a single Bus.
- A Root Complex Event Collector explicitly declares supported RCIEPs through the Root Complex Event Collector Endpoint Association Extended Capability.
- Root Complex Event Collectors are optional.


### 1.3.5 PCI Express to PCI/PCI-X Bridge

- A PCI Express to PCI/PCI-X Bridge provides a connection between a PCI Express fabric and a PCI/PCI-X hierarchy.


### 1.4 Hardware/Software Model for Discovery, Configuration and Operation

The PCI/PCIe hardware/software model includes architectural constructs necessary to discover, configure, and use a Function, without needing Function-specific knowledge. Key elements include:

- A configuration model which provides system software the means to discover hardware Functions available in a system
- Mechanisms to perform basic resource allocation for addressable resources such as memory space and interrupts
- Enable/disable controls for Function response to received Requests, and initiation of Requests
- Well-defined ordering and flow control models to support the consistent and robust implementation of hardware/software interfaces

The PCI Express configuration model supports two mechanisms:

[^0]
[^0]:    3. Since an earlier version of this specification used Sub-Class 06h for this purpose, an implementation is still permitted to use Sub-Class 06h, but this is strongly discouraged.

- PCI-compatible configuration mechanism: The PCI-compatible mechanism supports 100\% binary compatibility with Conventional PCI aware operating systems and their corresponding bus enumeration and configuration software.
- PCI Express enhanced configuration mechanism: The enhanced mechanism is provided to increase the size of available Configuration Space and to optimize access mechanisms.

Each PCI Express Link is mapped through a virtual PCI-to-PCI Bridge structure and has a Logical Bus associated with it. The virtual PCI-to-PCI Bridge structure may be part of a PCI Express Root Complex Port, a Switch Upstream Port, or a Switch Downstream Port. A Root Port is a virtual PCI-to-PCI Bridge structure that originates a PCI Express hierarchy domain from a PCI Express Root Complex. Devices are mapped into Configuration Space such that each will respond to a particular Device Number.

# 1.5 PCI Express Layering Overview 

This document specifies the architecture in terms of three discrete logical layers: the Transaction Layer, the Data Link Layer, and the Physical Layer. Each of these layers is divided into two sections: one that processes outbound (to be transmitted) information and one that processes inbound (received) information, as shown in § Figure 1-4.

The fundamental goal of this layering definition is to facilitate the reader's understanding of the specification. Note that this layering does not imply a particular PCI Express implementation.
![img-3.jpeg](03_Knowledge/Tech/PCIe/01_Introduction/img-3.jpeg)

Figure 1-4 High-Level Layering Diagram

PCI Express uses packets to communicate information between components. Packets are formed in the Transaction and Data Link Layers to carry the information from the transmitting component to the receiving component. As the transmitted packets flow through the other layers, they are extended with additional information necessary to handle packets at those layers. At the receiving side the reverse process occurs and packets get transformed from their Physical Layer representation to the Data Link Layer representation and finally (for Transaction Layer Packets) to the form that can be processed by the Transaction Layer of the receiving device. § Figure 1-5 shows the conceptual flow of transaction level packet information through the layers.
![img-4.jpeg](03_Knowledge/Tech/PCIe/01_Introduction/img-4.jpeg)

Figure 1-5 Packet Flow Through the Layers

Note that a simpler form of packet communication is supported between two Data Link Layers (connected to the same Link) for the purpose of Link management.

# 1.5.1 Transaction Layer 

The upper Layer of the architecture is the Transaction Layer. The Transaction Layer's primary responsibility is the assembly and disassembly of TLPs. TLPs are used to communicate transactions, such as read and write, as well as certain types of events. The Transaction Layer is also responsible for managing credit-based flow control for TLPs.

Every request packet requiring a response packet is implemented as a Split Transaction. Each packet has a unique identifier that enables response packets to be directed to the correct originator. The packet format supports different forms of addressing depending on the type of the transaction (Memory, I/O, Configuration, and Message). The Packets may also have attributes such as No Snoop, Relaxed Ordering, and ID-Based Ordering (IDO).

The Transaction Layer supports four address spaces: it includes the three PCI address spaces (memory, I/O, and configuration) and adds Message Space. This specification uses Message Space to support all prior sideband signals, such as interrupts, power-management requests, and so on, as in-band Message transactions. You could think of PCI Express Message transactions as "virtual wires" since their effect is to eliminate the wide array of sideband signals currently used in a platform implementation.

### 1.5.2 Data Link Layer 6

The middle Layer in the stack, the Data Link Layer, serves as an intermediate stage between the Transaction Layer and the Physical Layer. The primary responsibilities of the Data Link Layer include Link management and data integrity, including error detection and error correction.

The transmission side of the Data Link Layer accepts TLPs assembled by the Transaction Layer, calculates and applies a data protection code and TLP sequence number, and submits them to Physical Layer for transmission across the Link. The receiving Data Link Layer is responsible for checking the integrity of received TLPs and for submitting them to the Transaction Layer for further processing. On detection of TLP error(s), this Layer is responsible for requesting retransmission of TLPs until information is correctly received, or the Link is determined to have failed.

The Data Link Layer also generates and consumes packets that are used for Link management functions. To differentiate these packets from those used by the Transaction Layer (TLP), the term Data Link Layer Packet (DLLP) will be used when referring to packets that are generated and consumed at the Data Link Layer.

### 1.5.3 Physical Layer 6

The Physical Layer includes all circuitry for interface operation, including driver and input buffers, parallel-to-serial and serial-to-parallel conversion, PLL(s), and impedance matching circuitry. It also includes logical functions related to interface initialization and maintenance. The Physical Layer exchanges information with the Data Link Layer in an implementation specific format. This Layer is responsible for converting information received from the Data Link Layer into an appropriate serialized format and transmitting it across the PCI Express Link at a frequency and width compatible with the component connected to the other side of the Link.

The PCI Express architecture has "hooks" to support future performance enhancements via speed upgrades and advanced encoding techniques. The future speeds, encoding techniques or media may only impact the Physical Layer definition.

# 1.5.4 Layer Functions and Services 

### 1.5.4.1 Transaction Layer Services

The Transaction Layer, in the process of generating and receiving TLPs, exchanges Flow Control information with its complementary Transaction Layer on the other side of the Link. It is also responsible for supporting both software and hardware-initiated power management.

Initialization and configuration functions require the Transaction Layer to:

- Store Link configuration information generated by the processor or management device,
- Store Link capabilities generated by Physical Layer hardware negotiation of width and operational frequency.

A Transaction Layer's Packet generation and processing services require it to:

- Generate TLPs from device core Requests
- Convert received Request TLPs into Requests for the device core,
- Convert received Completion Packets into a payload, or status information, deliverable to the core,
- Detect unsupported TLPs and invoke appropriate mechanisms for handling them,
- If end-to-end data integrity is supported, generate the end-to-end data integrity CRC and update the TLP header accordingly.

Flow Control services:

- The Transaction Layer tracks Flow Control credits for TLPs across the Link.
- Transaction credit status is periodically transmitted to the remote Transaction Layer using transport services of the Data Link Layer.
- Remote Flow Control information is used to throttle TLP transmission.

Ordering rules:

- PCI/PCI-X compliant producer/consumer ordering model,
- Extensions to support Relaxed Ordering,
- Extensions to support ID-Based Ordering,
- Support for UIO ordering model.

Power management services:

- Software-controlled power management through mechanisms, as dictated by system software.
- Hardware-controlled autonomous power management minimizes power during full-on power states.

Virtual Channels and Traffic Class:

- The combination of Virtual Channel mechanism and Traffic Class identification is provided to support differentiated services and QoS support for certain classes of applications. They are also used to provide separate ordering domains for UIO and non-UIO Virtual Channels.

- Virtual Channels: Virtual Channels provide a means to support multiple independent logical data flows over given common physical resources of the Link. Conceptually this involves multiplexing different data flows onto a single physical Link.
- Traffic Class: The Traffic Class is a Transaction Layer Packet label that is transmitted unmodified end-to-end through the fabric. At every service point (e.g., Switch) within the fabric, Traffic Class labels are used to apply appropriate servicing policies. Each Traffic Class label defines a unique ordering domain - no ordering guarantees are provided for packets that contain different Traffic Class labels.


# 1.5.4.2 Data Link Layer Services 

The Data Link Layer is responsible for reliably exchanging information with its counterpart on the opposite side of the Link.

Initialization and power management services:

- Accept power state Requests from the Transaction Layer and convey to the Physical Layer
- Convey active/reset/disconnected/power managed state to the Transaction Layer

Data protection, error checking, and retry services:

- CRC generation
- Transmitted TLP storage for Data Link level retry
- Error checking
- TLP acknowledgement and retry Messages
- Error indication for error reporting and logging


### 1.5.4.3 Physical Layer Services 6

Interface initialization, maintenance control, and status tracking:

- Reset/Hot-Plug control/status
- Interconnect power management
- Width and Lane mapping negotiation
- Lane polarity inversion

Symbol and special Ordered Set generation:

- 8b/10b encoding/decoding
- Embedded clock tuning and alignment

Block and special Ordered Set generation:

- 128b/130b encoding/decoding
- 1b/1b encoding/decoding
- Link Equalization

Symbol transmission and alignment:

- Transmission circuits
- Reception circuits
- Elastic buffer at receiving side
- Multi-Lane de-skew (for widths $>x 1$ ) at receiving side

System Design For Testability (DFT) support features:

- Compliance Pattern (see § Section 4.2.9, § Section 4.2.11, and § Section 4.2.14)
- Modified Compliance Pattern (see § Section 4.2.10, § Section 4.2.12, and § Section 4.2.15)
- Jitter Measurement Pattern (see § Section 4.2.13 and § Section 4.2.16)
- Flit Error Injection (see § Section 7.8.13)


# 1.5.4.4 Inter-Layer Interfaces 

### 1.5.4.4.1 Transaction/Data Link Interface

The Transaction to Data Link interface provides:

- Byte or multi-byte data to be sent across the Link
- Local TLP-transfer handshake mechanism
- TLP boundary information
- Requested power state for the Link

The Data Link to Transaction interface provides:

- Byte or multi-byte data received from the PCI Express Link
- TLP framing information for the received byte
- Actual power state for the Link
- Link status information


### 1.5.4.4.2 Data Link/Physical Interface

The Data Link to Physical interface provides:

- Byte or multi-byte wide data to be sent across the Link
- Data transfer handshake mechanism
- TLP and DLLP boundary information for bytes
- Requested power state for the Link

The Physical to Data Link interface provides:

- Byte or multi-byte wide data received from the PCI Express Link
- TLP and DLLP framing information for data
- Indication of errors detected by the Physical Layer

- Actual power state for the Link
- Connection status information

