# 7. Software Initialization and Configuration 

The PCI Express Configuration model supports two Configuration Space access mechanisms:

- PCI-compatible Configuration Access Mechanism (CAM) (see § Section 7.2.1)
- PCI Express Enhanced Configuration Access Mechanism (ECAM) (see § Section 7.2.2)

The PCI-compatible mechanism supports 100\% binary compatibility with Conventional PCI or later aware operating systems and their corresponding bus enumeration and configuration software.

The enhanced mechanism is provided to increase the size of available Configuration Space and to optimize access mechanisms.

### 7.1 Configuration Topology

To maintain compatibility with PCI software configuration mechanisms, all PCI Express elements have a PCI-compatible Configuration Space. Each PCI Express Link originates from a logical PCI-PCI Bridge and is mapped into Configuration Space as the secondary bus of this Bridge. The Root Port is a PCI-PCI Bridge structure that originates a PCI Express Link from a PCI Express Root Complex (see § Figure 7-1).

A PCI Express Switch not using FPB Routing ID mechanisms is represented by multiple PCI-PCI Bridge structures connecting PCI Express Links to an internal logical PCI bus (see § Figure 7-2). The Switch Upstream Port is a PCI-PCI Bridge; the secondary bus of this Bridge represents the Switch's internal routing logic. Switch Downstream Ports are PCI-PCI Bridges bridging from the internal bus to buses representing the Downstream PCI Express Links from a PCI Express Switch. Only the PCI-PCI Bridges representing the Switch Downstream Ports may appear on the internal bus. Endpoints, represented by Type 0 Configuration Space Headers, are not permitted to appear on the internal bus.

A PCI Express Endpoint is mapped into Configuration Space as a single Function in a Device, which might contain multiple Functions or just that Function. PCI Express Endpoints and Legacy Endpoints are required to appear within one of the Hierarchy Domains originated by the Root Complex, meaning that they appear in Configuration Space in a tree that has a Root Port as its head. Root Complex Integrated Endpoints (RCiEPs) and Root Complex Event Collectors do not appear within one of the Hierarchy Domains originated by the Root Complex. These appear in Configuration Space as peers of the Root Ports.

Unless otherwise specified, requirements in the Configuration Space definition for a device apply to Single-Function Devices as well as to each Function individually of a Multi-Function Device.
![img-0.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-0.jpeg)

Figure 7-1 PCI Express Root Complex Device Mapping

![img-1.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-1.jpeg)

Figure 7-2 PCI Express Switch Device Mapping ${ }^{155}$

# IMPLEMENTATION NOTE: <br> CHANGING A DEVICE'S OS DRIVER BINDINGS \& RESOURCES 

Under certain circumstances, it is highly useful for a device to change one or more of its architected registers that help determine which OS-managed resources are allocated to the device and which OS drivers get bound to it. Here are two key examples:

- A device might change the Class Code Register value in one or more of its Functions
- Entire Functions might be added or removed after device firmware is updated

Software can direct devices to change their architected registers through a variety of mechanisms outside the scope of this specification, including implementation specific ones and ones defined by external standards bodies. It is recommended that these mechanisms follow the guidance of this Implementation Note.

If a device outside the RC has possibly been enumerated by the OS, it is strongly recommended that software use a mechanism directing the device to change its registers when coming out of a Conventional Reset. From a hardware perspective, this is similar to a hot remove followed by a hot add, providing a clean trigger point for architected registers to change in compliance with this specification, plus it guarantees the architected default hardware state for OS I/O infrastructure software and OS drivers to rely on. It is strongly recommended that software use OS-specific interfaces to perform the Conventional Reset and/or coordinate the reset and subsequent enumeration with the OS. If not feasible via OS-specific interfaces, software may be able to perform a Conventional Reset directly via several ways, including the Secondary Bus Reset bit or the Link Disable bit in the Downstream Port above the device.

If software knows that a device outside the RC has not been enumerated by the OS, software may choose to direct the device to change its registers without undergoing a reset, thus avoiding unnecessary delay.

### 7.2 PCI Express Configuration Mechanisms

PCI Express extends the Configuration Space to 4096 bytes per Function as compared to 256 bytes allowed by [PCI]. PCI Express Configuration Space is divided into a PCI-compatible region, which consists of the first 256 bytes of a Function's Configuration Space, and a PCI Express Extended Configuration Space which consists of the remaining Configuration Space (see § Figure 7-3). The PCI-compatible Configuration Space can be accessed using either the mechanism defined

[^0]
[^0]:    155. Future PCI Express Switches may be implemented as a single Switch device component (without the PCI-PCI Bridges) that is not limited by legacy compatibility requirements imposed by existing PCI software.

in $\S$ Section 7.2.1 or $\S$ Section 7.2.2 . Accesses made using either access mechanism are equivalent. The PCI Express Extended Configuration Space can only be accessed by using the ECAM mechanism defined in $\S$ Section 7.2.2. ${ }^{156}$
![img-2.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-2.jpeg)

Figure 7-3 PCI Express Configuration Space Layout

# 7.2.1 PCI-compatible Configuration Mechanism 5 

The PCI-compatible PCI Express Configuration Mechanism supports the PCI Configuration Space programming model defined in the [PCI]. By adhering to this model, systems incorporating PCI Express interfaces remain compliant with conventional PCI bus enumeration and configuration software.

In the same manner as PCI device Functions, PCI Express device Functions are required to provide a Configuration Space for software-driven initialization and configuration. Except for the differences described in this chapter, the PCI Express Configuration Space headers are organized to correspond with the format and behavior defined in the [PCI] (Section 6.1).

The PCI-compatible Configuration Access Mechanism uses the same Request format as the ECAM. For PCI-compatible Configuration Requests, the Extended Register Address field must be all zeros.

[^0]
[^0]:    156. The mechanism defined in $\S$ Section 7.2 .1 and the ECAM mechanism defined in $\S$ Section 7.2 .2 and operate independently from each other; there is no implied ordering between the two.

# 7.2.2 PCI Express Enhanced Configuration Access Mechanism (ECAM) 

For systems that are PC-compatible, or that do not implement a processor-architecture-specific firmware interface standard that allows access to the Configuration Space, the Enhanced Configuration Access Mechanism (ECAM) is required as defined in this section.

For systems that implement a processor-architecture-specific firmware interface standard that allows access to the Configuration Space, the operating system uses the standard firmware interface, and the hardware access mechanism defined in this section is not required.

In all systems, device drivers are encouraged to use the application programming interface (API) provided by the operating system to access the Configuration Space of its device and not directly use the hardware mechanism.

The ECAM utilizes a flat memory-mapped address space to access device configuration registers. In this case, the memory address determines the configuration register accessed and the memory data updates (for a write) or returns the contents of (for a read) the addressed register. The mapping from memory address space to PCI Express Configuration Space address is defined in § Table 7-1.

The size and base address for the range of memory addresses mapped to the Configuration Space are determined by the design of the host bridge and the firmware. They are reported by the firmware to the operating system in an implementation specific manner. The size of the range is determined by the number of bits that the host bridge maps to the Bus Number field in the configuration address. In § Table 7-1, this number of bits is represented as $n$, where $1 \leq n \leq 8$. A host bridge that maps $n$ memory address bits to the Bus Number field supports Bus Numbers from 0 to $2^{n}-1$, inclusive, and the base address of the range is aligned to a $2^{(n+20)}$-byte memory address boundary. Any bits in the Bus Number field that are not mapped from memory address bits must be Clear.

For example, if a system maps three memory address bits to the Bus Number field, the following are all true:

- $n=3$.
- Address bits A[63:23] are used for the base address, which is aligned to a $2^{23}$-byte ( 8 MB ) boundary.
- Address bits A[22:20] are mapped to bits [2:0] in the Bus Number field.
- Bits [7:3] in the Bus Number field are set to Clear.
- The system is capable of addressing Bus Numbers between 0 and 7, inclusive.

A minimum of one memory address bit $(n=1)$ must be mapped to the Bus Number field. Systems are encouraged to map additional memory address bits to the Bus Number field as needed to support a larger number of buses. Systems that support more than 4 GB of memory addresses are encouraged to map eight bits of memory address $(n=8)$ to the Bus Number field. Note that in systems that include multiple host bridges with different ranges of Bus Numbers assigned to each host bridge, the highest Bus Number for the system is limited by the number of bits mapped by the host bridge to which the highest bus number is assigned. In such a system, the highest Bus Number assigned to a particular host bridge would be greater, in most cases, than the number of buses assigned to that host bridge. In other words, for each host bridge, the number of bits mapped to the Bus Number field, $n$, must be large enough that the highest Bus Number assigned to each particular bridge must be less than or equal to $2^{n}-1$ for that bridge.

In some processor architectures, it is possible to generate memory accesses that cannot be expressed in a single Configuration Request, for example due to crossing a DW aligned boundary, or because a locked access is used. A Root Complex implementation is not required to support the translation to Configuration Requests of such accesses.

| Table 7-1 Enhanced Configuration Address Mapping $\cdot$ |  |
| :--: | :-- |
| Memory Address ${ }^{157}$ | PCI Express Configuration Space |
| A[(20+n-1):20] | Bus Number $1 \leq n \leq 8$ |
| A[19:15] | Device Number |
| A[14:12] | Function Number |
| A[11:8] | Extended Register Number |
| A[7:2] | Register Number |
| A[1:0] | Along with size of the access, used to generate Byte Enables |

Note: for Requests targeting Extended Functions in an ARI Device, A[19:12] represents the (8-bit) Function Number, which replaces the (5-bit) Device Number and (3-bit) Function Number fields above.

The system hardware must provide a method for the system software to guarantee that a write transaction using the ECAM is completed by the completer before system software execution continues.

# IMPLEMENTATION NOTE: ORDERING CONSIDERATIONS FOR THE ENHANCED CONFIGURATION ACCESS MECHANISM 

The ECAM converts memory transactions from the host CPU into Configuration Requests on the PCI Express fabric. This conversion potentially creates ordering problems for the software, because writes to memory addresses are typically posted transactions but writes to Configuration Space are not posted on the PCI Express fabric.

Generally, software does not know when a posted transaction is completed by the completer. In those cases in which the software must know that a posted transaction is completed by the completer, one technique commonly used by the software is to read the location that was just written. For systems that follow the PCI ordering rules throughout, the read transaction will not complete until the posted write is complete. However, since the PCI ordering rules allow non-posted write and read transactions to be reordered with respect to each other, the CPU must wait for a non-posted write to complete on the PCI Express fabric to be guaranteed that the transaction is completed by the completer.

As an example, software may wish to configure a device Function's Base Address register by writing to the device using the ECAM, and then read a location in the memory-mapped range described by this Base Address register. If the software were to issue the memory-mapped read before the ECAM write was completed, it would be possible for the memory-mapped read to be re-ordered and arrive at the device before the Configuration Write Request, thus causing unpredictable results.

To avoid this problem, processor and host bridge implementations must ensure that a method exists for the software to determine when the write using the ECAM is completed by the completer.

This method may simply be that the processor itself recognizes a memory range dedicated for mapping ECAM accesses as unique, and treats accesses to this range in the same manner that it would treat other accesses that generate non-posted writes on the PCI Express fabric, i.e., that the transaction is not posted from the processor's viewpoint. An alternative mechanism is for the host bridge (rather than the processor) to recognize the memory-mapped Configuration Space accesses and not to indicate to the processor that this write has been accepted until the non-posted Configuration Transaction has completed on the PCI Express fabric. A third alternative would be for the processor and host bridge to post the memory-mapped write to the ECAM and for the host bridge to provide a separate register that the software can read to determine when the Configuration Write Request has completed on the PCI Express fabric. Other alternatives are also possible.

## IMPLEMENTATION NOTE: GENERATING CONFIGURATION REQUESTS

Because Root Complex implementations are not required to support the generation of Configuration Requests from accesses that cross DW boundaries, or that use locked semantics, software should take care not to cause the generation of such accesses when using the memory-mapped ECAM unless it is known that the Root Complex implementation being used will support the translation.

# 7.2.2.1 Host Bridge Requirements 

For those systems that implement the ECAM, the PCI Express Host Bridge is required to translate the memory-mapped PCI Express Configuration Space accesses from the host processor to PCI Express configuration transactions. The use of Host Bridge PCI class code is Reserved for backwards compatibility; Host Bridge Configuration Space is opaque to standard PCI Express software and may be implemented in an implementation specific manner that is compatible with PCI Host Bridge Type 0 Configuration Space. A PCI Express Host Bridge is not required to signal errors through a Root Complex Event Collector. This support is optional for PCI Express Host Bridges.

### 7.2.2.2 PCI Express Device Requirements

Devices must support an additional 4 bits for decoding configuration register access, i.e., they must decode the Extended Register Address[3:0] field of the Configuration Request header.

## IMPLEMENTATION NOTE: DEVICE-SPECIFIC REGISTERS IN CONFIGURATION SPACE

It is strongly recommended that PCI Express devices place no registers in Configuration Space other than those in headers or Capability structures architected by applicable PCI specifications.

Device-specific registers that have legitimate reasons to be placed in Configuration Space (e.g., they need to be accessible before Memory Space is allocated) should be placed in a Vendor-Specific Capability structure (\$ Section 7.9.4 ), a Vendor-Specific Extended Capability structure (\$ Section 7.9.5 , or \$ Section 7.9.6).

Device-specific registers accessed in the run-time environment by drivers should be placed in Memory Space that is allocated by one or more Base Address registers. Even though PCI-compatible or PCI Express Extended Configuration Space may have adequate room for run-time device-specific registers, placing them there is highly discouraged for the following reasons:

- Not all Operating Systems permit drivers to access Configuration Space directly.
- Some platforms provide access to Configuration Space only via firmware calls, which typically have substantially lower performance compared to mechanisms for accessing Memory Space.
- Even on platforms that provide direct access to a memory-mapped PCI Express Enhanced Configuration Mechanism, performance for accessing Configuration Space will typically be significantly lower than for accessing Memory Space since:
- Configuration Reads and Writes must usually be DWORD or smaller in size,
- Configuration Writes are usually not posted by the platform, and
- Some platforms support only one outstanding Configuration Write at a time.

# IMPLEMENTATION NOTE: CONFIGURATION SPACE READ SIDE EFFECTS 

During a read access, any observable interaction that occurs besides the desired value being returned is called a read side effect. System software that has no specific knowledge of the Function being accessed may issue read requests to anywhere within the Function's Configuration Space. It is highly undesirable that any such access has any read side effects. No such side effects are required in any of the Configuration Space registers defined in this specification. It is strongly recommended that any implementation of those registers, as well as any vendor-defined Configuration Space registers, be free of any read side effects.

### 7.2.3 Root Complex Register Block (RCRB)

A Root Port or RCiEP may be associated with an optional 4096-byte block of memory mapped registers referred to as the Root Complex Register Block (RCRB). These registers are used in a manner similar to Configuration Space and can include PCI Express Extended Capabilities and other implementation specific registers that apply to the Root Complex. The structure of the RCRB is described in § Section 7.6.2 .

Multiple Root Ports or internal devices are permitted to be associated with the same RCRB. The RCRB memory-mapped registers must not reside in the same address space as the memory-mapped Configuration Space or Memory Space.

A Root Complex implementation is not required to support accesses to an RCRB that cross DWORD aligned boundaries or accesses that use locked semantics.

## IMPLEMENTATION NOTE: ACCESSING ROOT COMPLEX REGISTER BLOCK

Because Root Complex implementations are not required to support accesses to a RCRB that cross DW boundaries, or that use locked semantics, software should take care not to cause the generation of such accesses when accessing a RCRB unless the Root Complex will support the access.

### 7.3 Configuration Transaction Rules

### 7.3.1 Device Number

With non-ARI Devices, PCI Express components are restricted to implementing a single Device Number on their primary interface (Upstream Port), but are permitted to implement up to eight independent Functions within that Device Number. Each internal Function is selected based on decoded address information that is provided as part of the address portion of Configuration Request packets.

Except when FPB Routing ID mechanisms are used (see § Section 6.26 ), Downstream Ports that do not have ARI Forwarding enabled must associate only Device 0 with the device attached to the Logical Bus representing the Link from the Port. Configuration Requests targeting the Bus Number associated with a Link specifying Device Number 0 are delivered to the device attached to the Link; Configuration Requests specifying all other Device Numbers (1-31) must be terminated by the Switch Downstream Port or the Root Port with an Unsupported Request Completion Status (equivalent to Master Abort in PCI).

Non-ARI Devices must capture their assigned Device Number as discussed in § Section 2.2.6.2 . Non-ARI Devices must respond to all Type 0 Configuration Read Requests, regardless of the Device Number specified in the Request.

Switches, and components wishing to incorporate more than eight Functions at their Upstream Port, are permitted to implement one or more "virtual switches" represented by multiple Type 1 Configuration Space Headers (PCI-PCI Bridge) as illustrated in § Figure 7-2. These virtual switches serve to allow fan-out beyond eight Functions. FPB provides a "flattening" mechanism that, when enabled, causes the virtual bridges of the Downstream Ports to appear in configuration space at RID addresses following the RID of the Upstream Port (see § Section 6.26). Since Switch Downstream Ports are permitted to appear on any Device Number, in this case all address information fields (Bus, Device, and Function Numbers) must be completely decoded to access the correct register. Any Configuration Request targeting an unimplemented Bus, Device, or Function must return a Completion with Unsupported Request Completion Status.

With an ARI Device, its Device Number is implied to be 0 rather than specified by a field within an ID. The traditional 5-bit Device Number and 3-bit Function Number fields in its associated Routing IDs, Requester IDs, and Completer IDs are interpreted as a single 8-bit Function Number. See § Section 6.13 . Any Type 0 Configuration Request targeting an unimplemented Function in an ARI Device must be handled as an Unsupported Request.

If an ARI Downstream Port has ARI Forwarding enabled, the logic that determines when to turn a Type 1 Configuration Request into a Type 0 Configuration Request no longer enforces a restriction on the traditional Device Number field being 0 .

The following section provides details of the Configuration Space addressing mechanism.

# 7.3.2 Configuration Transaction Addressing 

PCI Express Configuration Requests use the following addressing fields:

- Destination Segment (Flit Mode only) - Selects one of multiple Segments that may be implemented within a Root Complex. See § Section 2.2.1.2 for a list of Segment rules.
- Bus Number - PCI Express maps logical PCI Bus Numbers onto PCI Express Links such that PCI-compatible configuration software views the Configuration Space of a PCI Express Hierarchy as a PCI hierarchy including multiple bus segments.
- Device Number - Device Number association is discussed in § Section 7.3.1 and in § Section 6.26. When an ARI Device is targeted and the Downstream Port immediately above it is enabled for ARI Forwarding, the Device Number is implied to be 0 , and the traditional Device Number field is used instead as part of an 8-bit Function Number field. See § Section 6.13 .
- Function Number - PCI Express also supports Multi-Function Devices using the same discovery mechanism as PCI. A Multi-Function Device must fully decode the Function Number field. A Single-Function Device MUST@FLIT also fully decode the Function Number field. With ARI Devices, discovery and enumeration of Extended Functions require ARI-aware software. See § Section 6.13 .
- Extended Register Number and Register Number - Specify the Configuration Space address of the register being accessed (concatenated such that the Extended Register Number forms the more significant bits).


### 7.3.3 Configuration Request Routing Rules

For Endpoints, the following rules apply:

- If Configuration Request Type is 1 ,
- and the TLP is not an IDE TLP

- and it is targeting a Device's captured Bus Number (See § Section 9.2.1.2 for SRIOV devices that consume multiple Bus numbers)
- Follow the rules for handling Unsupported Requests
- If Configuration Request Type is 0 , or if Configuration Request Type is 1 and the TLP is an IDE TLP associated with a Selective IDE Stream in the Secure state,
- Determine if the Request addresses a valid local Configuration Space of an implemented Function
- If so, process the Request
- If not, follow rules for handling Unsupported Requests

For Root Ports, Switches, and PCI Express-PCI Bridges, the following rules apply:

- Propagation of Configuration Requests from Downstream to Upstream as well as peer-to-peer are not supported
- Configuration Requests are initiated only by the Host Bridge, including those passed through the SFI CAM mechanism
- If Configuration Request Type is 0 , or if Configuration Request Type is 1 and the TLP is an IDE TLP associated with a Selective IDE Stream in the Secure state,
- Determine if the Request addresses a valid local Configuration Space of an implemented Function
- If so, process the Request
- If not, follow rules for handling Unsupported Requests
- If Configuration Request Type is 1, apply the following tests, in sequence, to the Bus Number and Device Number fields:
- If in the case of a PCI Express-PCI Bridge, equal to the Bus Number assigned to secondary PCI bus or, in the case of a Switch or Root Complex, equal to the Bus Number and decoded Device Numbers assigned to one of the Root (Root Complex) or Downstream Ports (Switch), or if required based on the FPB Routing ID mechanism,
- Transform the Request to Type 0 by changing the value in the Type[4:0] field of the Request (see § Table 2-3) - all other fields of the Request remain unchanged
- Forward the Request to that Downstream Port (or PCI bus, in the case of a PCI Express-PCI Bridge)
- If not equal to the Bus Number of any of Downstream Ports or secondary PCI bus, but in the range of Bus Numbers assigned to either a Downstream Port or a secondary PCI bus, or if required based on the FPB Routing ID mechanism,
- Forward the Request to that Downstream Port interface without modification
- Else (none of the above)
- The Request is invalid - follow the rules for handling Unsupported Requests
- PCI Express-PCI Bridges must terminate as Unsupported Requests any Configuration Requests for which the Extended Register Address field is non-zero that are directed towards a PCI bus that does not support Extended Configuration Space.

Note: This type of access is a consequence of a programming error.
Additional rule specific to Root Complexes:

- Configuration Requests addressing a Destination Segment and Bus Numbers assigned to devices within the Root Complex are processed by the Root Complex

- The assignment of Segment Numbers and Bus Numbers to the devices within a Root Complex may be done in an implementation specific way.

For all types of devices:
Configuration Reads and Writes to unimplemented registers are not considered to be errors. Unless errors defined elsewhere in this specification are detected and need to be reported, such Requests must return a Completion with Successful Completion status, with reads returning a data value of all 0's and writes discarding the write data without effect.

All other Configuration Space addressing fields are decoded as described elsewhere in this specification.

# 7.3.4 PCI Special Cycles 

PCI Special Cycles (see the [PCI] for details) are not directly supported by PCI Express. PCI Special Cycles may be directed to PCI bus segments behind PCI Express-PCI Bridges using Type 1 configuration cycles as described in the [PCI].

### 7.4 Configuration Register Types

Configuration register fields are assigned one of the attributes described in § Table 7-2. All PCI Express components, with the exception of the Root Complex and system-integrated devices, initialize register fields to specified default values. Root Complexes and system-integrated devices initialize register fields as required by the firmware for a particular system implementation.

Table 7-2 Register and Register Bit-Field Types

| Register <br> Attribute | Description |
| :--: | :--: |
| HwInit | Hardware Initialized - Register bits are permitted, as an implementation option, to be hard-coded, initialized by system/device firmware, or initialized by hardware mechanisms such as pin strapping or nonvolatile storage. ${ }^{158}$ Initialization by system firmware is permitted only for system-integrated devices. Bits must be fixed in value and read-only after initialization. After Initialization, values are only permitted to change following Conventional Reset (see § Section 6.6.1) and subsequent re-initialization. HwInit register bits are not modified by an FLR. |
| RO | Read-only - Register bits are read-only and cannot be altered by software. Where explicitly defined, these bits are used to reflect changing hardware state, and as a result bit values can be observed to change at run time. ${ }^{159}$ Register bit default values and bits that cannot change value at run time, are permitted to be hard-coded, initialized by system/ device firmware, or initialized by hardware mechanisms such as pin strapping or nonvolatile storage. Initialization by system firmware is permitted only for system-integrated devices. <br> If the optional feature that would Set the bits is not implemented, the bits must be hardwired to Zero. |
| RW | Read-Write - Register bits are read-write and are permitted to be either Set or Cleared by software to the desired state. If the optional feature that is associated with the bits is not implemented, the bits are permitted to be hardwired to Zero. |
| RW1C | Write-1-to-clear status - Register bits indicate status when read. A Set bit indicates a status event which is Cleared by writing a 1b. Writing a 0b to RW1C bits has no effect. |

[^0]
[^0]:    158. For historical reasons, readers may observe inconsistencies in this document in the use of HwInit and RO. As this document is revised we will attempt to ensure that new definitions conform to the definitions given here.
    159. For historical reasons, readers may observe inconsistencies in this document in the use of HwInit and RO. As this document is revised we will attempt to ensure that new definitions conform to the definitions given here.

| Register <br> Attribute | Description |
| :--: | :--: |
|  | If the optional feature that would Set the bit is not implemented, the bit must be read-only and hardwired to Zero. |
| ROS | Sticky - Read-only - Register bits are read-only and cannot be altered by software. If the optional feature that would Set the bit is not implemented, the bit is hardwired to Zero. Bits are neither initialized nor modified by hot reset or FLR. ${ }^{160}$ <br> Where noted, devices that consume auxiliary power must preserve sticky register bit values when auxiliary power consumption (via either Aux Power PM Enable or PME_En) is enabled. In these cases, register bits are neither initialized nor modified by Hot, Warm, or Cold Reset (see § Section 6.6). |
| RWS | Sticky - Read-Write - Register bits are read-write and are Set or Cleared by software to the desired state. Bits are neither initialized nor modified by hot reset or FLR. ${ }^{161}$ <br> If the optional feature that is associated with the bits is not implemented, the bits are permitted to be hardwired to Zero. <br> Where noted, devices that consume auxiliary power must preserve sticky register bit values when auxiliary power consumption (via either Aux Power PM Enable or PME_En) is enabled. In these cases, register bits are neither initialized nor modified by Hot, Warm, or Cold Reset (see § Section 6.6). |
| RW1CS | Sticky - Write-1-to-clear status - Register bits indicate status when read. A Set bit indicates a status event which is Cleared by writing a 1b. Writing a 0b to RW1CS bits has no effect. If the optional feature that would Set the bit is not implemented, the bit is read-only and hardwired to Zero. Bits are neither initialized nor modified by hot reset or FLR. ${ }^{162}$ <br> Where noted, devices that consume auxiliary power must preserve sticky register bit values when auxiliary power consumption (via either Aux Power PM Enable or PME_En) is enabled. In these cases, register bits are neither initialized nor modified by Hot, Warm, or Cold Reset (see § Section 6.6). |
| RsvdP | Reserved and Preserved - Reserved for future RW implementations. Register bits are read-only and must return zero when read. Software must preserve the value read for writes to bits. |
| RsvdZ | Reserved and Zero - Reserved for future RW1C implementations. Register bits are read-only and must return zero when read. Software must use 0b for writes to bits. |

For SR-IOV devices, many registers or fields in VFs are required to be reserved or hardwired to Zero. Before the Single Root I/O Virtualization and Sharing (SR-IOV) Specification was merged into the PCI Express Base Specification, the SR-IOV specification contained many tables summarizing requirements differences for PFs and VFs, relative to the Base specification. These tables contained dedicated columns for PF attributes and VF attributes, though there were relatively few differences for PF attributes.

To provide a clear, consolidated, and concise indication of PF and VF attribute differences from other Function types, this specification eliminated most of those tables. Instead, special field types from the following table indicate VF attribute
160. Bits/fields with the "Sticky" attribute must be implemented such that no Function-specific software or firmware is required to maintain the observed state of the bit/field. Particularly for power management scenarios, it is permitted, but not recommended, to use Function-specific software or firmware to restore the correct values, provided this is done before the system hardware or system software could observe incorrect values. How this could be done is outside the scope of this document.
161. Bits/fields with the "Sticky" attribute must be implemented such that no Function-specific software or firmware is required to maintain the observed state of the bit/field. Particularly for power management scenarios, it is permitted, but not recommended, to use Function-specific software or firmware to restore the correct values, provided this is done before the system hardware or system software could observe incorrect values. How this could be done is outside the scope of this document.

differences, and any additional attribute or semantic differences with PFs and VFs are covered within the register description column or elsewhere.

Table 7-3 Special Field Types to Indicate VF Attributes

| Register Attribute | Description |
| :--: | :-- |
| VF ROZ | VF RO-Zero - VF register bits must have RO semantics and be hardwired to Zero. |
| VF RsvdP | VF RsvdP - VF register bits must have RsvdP semantics. |
| VF RsvdZ | VF RsvdZ - VF register bits must have RsvdZ semantics. |

# 7.5 PCI and PCIe Capabilities Required by the Base Spec for all Ports 

The following registers and capabilities are required by this specification in all Functions, including PFs and VFs.
Except where noted, VF register fields and bits have the same attributes as other Functions. For VF fields marked RsvdP, the associated PF's setting applies to the VF.

### 7.5.1 PCI-Compatible Configuration Registers

The first 256 bytes of a Function's Configuration Space form the PCI-compatible region. This region completely aliases the conventional PCI Configuration Space of the Function. Legacy PCI devices can also be accessed with the ECAM without requiring any modifications to the device hardware or device driver software.

Layout of the Configuration Space and format of individual configuration registers are depicted following the little-endian convention.

### 7.5.1.1 Type 0/1 Common Configuration Space

§ Figure 7-4 details allocation for common register fields of Type 0 and Type 1 Configuration Space Headers for PCI Express Device Functions. Fields labeled Type Specific vary between different Configuration Space header types.

![img-3.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-3.jpeg)

Figure 7-4 Common Configuration Space Header

These registers are defined for both Type 0 and Type 1 Configuration Space Headers. The PCI Express-specific interpretation of these registers is defined in this section.

# 7.5.1.1.1 Vendor ID Register (Offset 00h) 

For non-VFs, the Vendor ID register is HwInit and the value in this register identifies the manufacturer of the Function. In keeping with PCI-SIG procedures, valid vendor identifiers must be allocated by the PCI-SIG to ensure uniqueness. Each vendor must have at least one Vendor ID. It is recommended that software read the Vendor ID register to determine if a Function is present, where a value of FFFFh indicates that no Function is present.

For VFs, this field must return FFFFh when read. VI software should return the Vendor ID value from the associated PF as the Vendor ID value for the VF.

# 7.5.1.1.2 Device ID Register (Offset 02h) 

For non-VFs, the Device ID register is HwInit and the value in this register identifies the particular Function. The Device ID must be allocated by the vendor. The Device ID, in conjunction with the Vendor ID and Revision ID, are used as one mechanism for software to determine which driver should be loaded. The vendor must ensure that the chosen values do not result in the use of an incompatible device driver.

For VFs, this field must return FFFFh when read. VI software should return the VF Device ID (see § Section 9.3.3.11) value from the associated PF as the Device ID for the VF.

## IMPLEMENTATION NOTE: LEGACY PCI PROBING SOFTWARE

Returning FFFFh for Device ID and Vendor ID values allows some legacy software to ignore VFs. See § Section 7.5.1.1.1.

### 7.5.1.1.3 Command Register (Offset 04h)

§ Table 7-4 defines the Command Register and the layout of the register is shown in § Figure 7-5. Individual bits in the Command Register may or may not be implemented depending on the feature set supported by the Function. For PCI Express to PCI/PCI-X Bridges, refer to the (PCIe-to-PCI-PCI-X-Bridge) for requirements for this register.
![img-4.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-4.jpeg)

Figure 7-5 Command Register

Table 7-4 Command Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 0 | I/O Space Enable - Controls a Function's response to I/O Space accesses. When this bit is Clear, all received I/O accesses are caused to be handled as Unsupported Requests. When this bit is Set, the Function is enabled to decode the address and further process I/O Space accesses. For a Function with a Type 1 Configuration Space Header, this bit controls the response to I/O Space accesses received on its Primary Side. <br> Default value of this bit is 0 b . <br> This bit is permitted to be hardwired to Zero if a Function does not support I/O Space accesses. <br> This bit does not apply to VFs and must be hardwired to Zero. | RW <br> VF ROZ |
| 1 | Memory Space Enable - Controls a Function's response to Memory Space accesses. When this bit is Clear, all received Memory Space accesses are caused to be handled as Unsupported Requests. When this bit is Set, the Function is enabled to decode the address and further process Memory Space accesses. For a Function with a Type 1 Configuration Space Header, this bit controls the response to Memory Space accesses received on its Primary Side. <br> Default value of this bit is 0 b . <br> This bit is permitted to be hardwired to 0 b if a Function does not support Memory Space accesses. <br> This bit does not apply to VFs and must be hardwired to Zero. VF Memory Space is controlled by the VF MSE bit in the SR-IOV Control Register. | RW <br> VF ROZ |
| 2 | Bus Master Enable - Controls the ability of a Function to issue Memory ${ }^{163}$ and I/O Read/Write Requests, and the ability of a Port to forward Memory and I/O Read/Write Requests in the Upstream direction | RW |
|  | - Functions with a Type 0 Configuration Space Header: <br> When this bit is Set, the Function is allowed to issue Memory or I/O Requests. <br> When this bit is Clear, the Function is not allowed to issue any Memory or I/O Requests. <br> Note that as MSI/MSI-X interrupt Messages are in-band memory writes, setting the Bus Master Enable bit to 0b disables MSI/MSI-X interrupt Messages as well. <br> Transactions for a VF that has its Bus Master Enable Set must not be blocked by transactions for VFs that have their Bus Master Enable Cleared. <br> Requests other than Memory or I/O Requests are not controlled by this bit. <br> Default value of this bit is 0 b . <br> This bit is hardwired to 0 b if a Function does not generate Memory or I/O Requests. <br> - Functions with a Type 1 Configuration Space Header: <br> This bit controls the initiating of and the forwarding of Memory or I/O Requests by a Port in the Upstream direction. When this bit is 0b, Memory and I/O Requests received at a Root Port or the Downstream side of a Switch Port must be handled as Unsupported Requests (UR), and for Non-Posted Requests a Completion with UR Completion Status must be returned. This bit does not affect forwarding of Completions in either the Upstream or Downstream direction. <br> The forwarding of Requests other than Memory or I/O Requests is not controlled by this bit. Default value of this bit is 0 b . |  |
| 3 | Special Cycle Enable - This bit was originally described in the [PCI]. Its functionality does not apply to PCI Express and the bit must be hardwired to 0b. | RO |

[^0]
[^0]:    163. The AtomicOp Requester Enable bit in the Device Control 2 register must also be Set in order for an AtomicOp Requester to initiate AtomicOp Requests, which are Memory Requests.

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 4 | Memory Write and Invalidate - This bit was originally described in the [PCI] and the [PCI-to-PCI-Bridge]. Its functionality does not apply to PCI Express and the bit must be hardwired to 0b. For PCI Express to PCI/PCI-X Bridges, refer to the [PCIe-to-PCI-PCI-X-Bridge] for requirements for this register. | RO |
| 5 | VGA Palette Snoop - This bit was originally described in the [PCI] and the [PCI-to-PCI-Bridge]. Its functionality does not apply to PCI Express and the bit must be hardwired to 0b. | RO |
| 6 | Parity Error Response - See § Section 7.5.1.1.14 . <br> This bit controls the logging of poisoned TLPs in the Master Data Parity Error bit in the Status Register. <br> An RCIEP that is not associated with a Root Complex Event Collector is permitted to hardwire this bit to 0b. <br> Default value of this bit is 0 b. | RW <br> VF RsvdP |
| 7 | IDSEL Stepping/Wait Cycle Control - This bit was originally described in the [PCI]. Its functionality does not apply to PCI Express and the bit must be hardwired to 0b. | RO |
| 8 | SERR\# Enable - See § Section 7.5.1.1.14 . <br> When Set, this bit enables reporting upstream of Non-fatal and Fatal errors detected by the Function. Note that errors are reported if enabled either through this bit or through the PCI Express specific bits in the Device Control Register (see § Section 7.5.3.4). <br> In addition, for Functions with Type 1 Configuration Space Headers, this bit controls transmission by the primary interface of ERR_NONFATAL and ERR_FATAL error Messages forwarded from the secondary interface. This bit does not affect the transmission of forwarded ERR_COR messages. <br> An RCIEP that is not associated with a Root Complex Event Collector is permitted to hardwire this bit to 0b. <br> Default value of this bit is 0 b . | RW <br> VF RsvdP |
| 9 | Fast Back-to-Back Transactions Enable - This bit was originally described in the [PCI]. Its functionality does not apply to PCI Express and the bit must be hardwired to 0b. | RO |
| 10 | Interrupt Disable - Controls the ability of a Function to generate INTx emulation interrupts. When Set, Functions are prevented from asserting INTx interrupts. <br> Any INTx emulation interrupts already asserted by the Function must be deasserted when this bit is Set. <br> As described in § Section 2.2.8.1, INTx interrupts use virtual wires that must, if asserted, be deasserted using the appropriate Deassert_INTx message(s) when this bit is Set. <br> Only the INTx virtual wire interrupt(s) associated with the Function(s) for which this bit is Set are affected. <br> For Functions with a Type 0 Configuration Space Header that generate INTx interrupts, this bit is required. For Functions with a Type 0 Configuration Space Header that do not generate INTx interrupts, this bit is optional. If not implemented, this bit must be hardwired to 0b. <br> For Functions with a Type 1 Configuration Space Header that generate INTx interrupts on their own behalf, this bit is required. This bit has no effect on interrupts forwarded from the secondary side. <br> For Functions with a Type 1 Configuration Space Header that do not generate INTx interrupts on their own behalf this bit is optional. If not implemented, this bit must be hardwired to 0 b . <br> Default value of this bit is 0 b . <br> This bit does not apply to VFs and must be hardwired to Zero. | RW <br> VF ROZ |

# 7.5.1.1.4 Status Register (Offset 06h) 

\$ Table 7-5 defines the Status Register and the layout of the register is shown in $\$$ Figure 7-6. Functions may not need to implement all bits, depending on the feature set supported by the Function. For PCI Express to PCI/PCI-X Bridges, refer to the [PCIe-to-PCI-PCI-X-Bridge] for requirements for this register.
![img-5.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-5.jpeg)

Figure 7-6 Status Register

Table 7-5 Status Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 0 | Immediate Readiness - This optional bit, when Set, indicates the Function is guaranteed to be ready to successfully complete valid Configuration Requests at any time. It is permitted for this indication to be based on implementation specific knowledge of how long it takes the host to become ready to issue Configuration Requests. <br> When this bit is Set, for accesses to this Function, software is exempt from all requirements to delay configuration accesses following any type of reset, including but not limited to the timing requirements defined in $\S$ Section 6.6 . <br> How this guarantee is established is beyond the scope of this document. <br> It is permitted that system software/firmware provide mechanisms that supersede the indication provided by this bit, however such software/firmware mechanisms are outside the scope of this specification. <br> This bit does not apply to VFs and must be hardwired to Zero. | RO <br> VF ROZ |
| 3 | Interrupt Status - When Set, indicates that an INTx emulation interrupt is pending internally in the Function. | RO <br> VF ROZ |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | Note that INTx emulation interrupts forwarded by Functions with a Type 1 Configuration Space Header from the secondary side are not reflected in this bit. <br> Setting the Interrupt Disable bit has no effect on the state of this bit. <br> Functions that do not generate INTx interrupts are permitted to hardwire this bit to 0 b. <br> Default value of this bit is 0 b . <br> This bit does not apply to VFs and must be hardwired to Zero. |  |
| 4 | Capabilities List - Indicates the presence of an Extended Capability list item. Since all PCI Express device Functions are required to implement the PCI Express Capability structure, this bit must be hardwired to 1b. | RO |
| 5 | 66 MHz Capable - This bit was originally described in the [PCI]. Its functionality does not apply to PCI Express and the bit must be hardwired to 0 b. | RO |
| 7 | Fast Back-to-Back Transactions Capable - This bit was originally described in the [PCI]. Its functionality does not apply to PCI Express and the bit must be hardwired to 0 b. | RO |
| 8 | Master Data Parity Error - See § Section 7.5.1.1.14 <br> This bit is Set by a Function with a Type 0 Configuration Space Header if the Parity Error Response bit in the Command Register is 1 b and either of the following two conditions occurs: <br> - Function receives a Poisoned Completion <br> - Function transmits a Poisoned Request <br> This bit is Set by a Function with a Type 1 Configuration Space Header if the Parity Error Response bit in the Command Register is 1 b and either of the following two conditions occurs: <br> - Port receives a Poisoned Completion going Downstream <br> - Port transmits a Poisoned Request Upstream <br> If the Parity Error Response bit is 0 b, this bit is never Set. <br> Default value of this bit is 0 b . | RW1C |
| 10:9 | DEVSEL Timing - This field was originally described in the [PCI]. Its functionality does not apply to PCI Express and the field must be hardwired to 00b. | RO |
| 11 | Signaled Target Abort - See § Section 7.5.1.1.14. <br> This bit is Set when a Function completes a Posted or Non-Posted Request as a Completer Abort error. This applies to a Function with a Type 1 Configuration Space Header when the Completer Abort was generated by its Primary Side. <br> Functions with a Type 0 Configuration Space Header that do not signal Completer Abort are permitted to hardwire this bit to 0 b. <br> Default value of this bit is 0 b . | RW1C |
| 12 | Received Target Abort - See § Section 7.5.1.1.14. <br> On a Function with a Type 0 Configuration Space Header, this bit is Set when a Requester receives a Completion with Completer Abort Completion Status. <br> On a Function with a Type 1 Configuration Space Header, this bit is Set when its Primary Side receives a Completion with Completer Abort Completion Status. <br> Functions with a Type 0 Configuration Space Header that do not make Non-Posted Requests on their own behalf are permitted to hardwire this bit to 0 b. | RW1C |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | Default value of this bit is 0 b. |  |
| 13 | Received Master Abort - See § Section 7.5.1.1.14 . <br> On a Function with a Type 0 Configuration Space Header, this bit is Set when a Requester receives a Completion with Unsupported Request Completion Status. <br> On a Function with a Type 1 Configuration Space Header, the bit is Set when its Primary Side receives a Completion with Unsupported Request Completion Status. <br> Functions with a Type 0 Configuration Space Header that do not make Non-Posted Requests on their own behalf are permitted to hardwire this bit to 0 b. <br> Default value of this bit is 0 b . | RW1C |
| 14 | Signaled System Error - See § Section 7.5.1.1.14 . <br> This bit is Set when a Function sends an ERR_FATAL or ERR_NONFATAL Message, and the SERR\# Enable bit in the Command Register is 1 b . <br> Functions with a Type 0 Configuration Space Header that do not send ERR_FATAL or ERR_NONFATAL Messages are permitted to hardwire this bit to 0 b. <br> Default value of this bit is 0 b . | RW1C |
| 15 | Detected Parity Error - See § Section 7.5.1.1.14 . <br> This bit is Set by a Function whenever it receives a Poisoned TLP, regardless of the state of the Parity Error Response bit in the Command Register. On a Function with a Type 1 Configuration Space Header, the bit is Set when the Poisoned TLP is received by its Primary Side. <br> Default value of this bit is 0 b . | RW1C |

# 7.5.1.1.5 Revision ID Register (Offset 08h) $\S$ 

The Revision ID Register is HwInit and the value in this register specifies a Function specific revision identifier. The value is chosen by the vendor. Zero is an acceptable value. The Device ID, in conjunction with the Vendor ID and Revision ID, are used as one mechanism for software to determine which driver should be loaded. The vendor must ensure that the chosen values do not result in the use of an incompatible device driver.

The value reported in the VF may be different than the value reported in the PF.

### 7.5.1.1.6 Class Code Register (Offset 09h) $\S$

The Class Code Register is read-only and is used to identify the generic operation of the Function and, in some cases, a specific register level programming interface. The register layout is shown in § Figure 7-7 and described in § Table 7-6. Encodings for base class, sub-class, and programming interface are provided in the [PCI-Code-and-ID]. All unspecified encodings are Reserved.

The field in a PF and its associated VFs must return the same value when read.

| 23 | 16 | 15 | 8 | 7 | 0 |
| :--: | :--: | :--: | :--: | :--: | :--: |
| Base Class Code |  | Sub-Class Code |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 |

Figure 7-7 Class Code Register

Table 7-6 Class Code Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $7: 0$ | Programming Interface - This field identifies a specific register-level programming interface (if any) so that device independent software can interact with the Function. <br> Encodings for this field are provided in the [PCI-Code-and-ID]. All unspecified encodings are Reserved. | RO |
| $15: 8$ | Sub-Class Code - Specifies a base class sub-class, which identifies more specifically the operation of the Function. <br> Encodings for sub-class are provided in the [PCI-Code-and-ID]. All unspecified encodings are Reserved. | RO |
| $23: 16$ | Base Class Code - A code that broadly classifies the type of operation the Function performs. <br> Encodings for base class, are provided in the [PCI-Code-and-ID]. All unspecified encodings are Reserved. | RO |

# 7.5.1.1.7 Cache Line Size Register (Offset 0Ch) 

The Cache Line Size register is programmed by the system firmware or the operating system to system cache line size. However, note that legacy PCI-compatible software may not always be able to program this register correctly especially in the case of Hot-Plug devices. This read-write register is implemented for legacy compatibility purposes but has no effect on any PCI Express device behavior. For PCI Express to PCI/PCI-X Bridges, refer to the [PCIe-to-PCI-PCI-X-Bridge] for requirements for this register. The default value of this register is 00 h .

This bit does not apply to VFs and must be hardwired to Zero.

### 7.5.1.1.8 Latency Timer Register (Offset 0Dh)

This register is also referred to as Primary Latency Timer for Type 1 Configuration Space Header Functions. The Latency Timer was originally described in the [PCI] and the [PCI-to-PCI-Bridge]. Its functionality does not apply to PCI Express. This register must be hardwired to 00 h .

### 7.5.1.1.9 Header Type Register (Offset 0Eh)

This register identifies the layout of the second part of the predefined header (beginning at byte 10 h in Configuration Space) and also whether or not the Device might contain multiple Functions. The register layout is shown in $\S$ Figure 7-8 and $\S$ Table 7-7 describes the bits in the register.

This entire register does not apply to VFs and must be hardwired to Zero.

![img-6.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-6.jpeg)

Figure 7-8 Header Type Register

Table 7-7 Header Type Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $6: 0$ | Header Layout - This field identifies the layout of the second part of the predefined header. <br> For Functions that implement a Type 0 Configuration Space Header the encoding 000 0000b must be used. <br> For Functions that implement a Type 1 Configuration Space Header the encoding 000 0001b must be used. <br> The encoding 000 0010b is Reserved. This encoding was originally described in the [PC-Card] and is used in previous versions of the programming model. Careful consideration should be given to any attempt to repurpose it. <br> All other encodings are Reserved. | RO <br> VF ROZ |
| 7 | Multi-Function Device - When Set, indicates that the Device may contain multiple Functions, but not necessarily. Software is permitted to probe for Functions other than Function 0. When Clear, software must not probe for Functions other than Function 0 unless explicitly indicated by another mechanism, such as an ARI or SR-IOV Extended Capability structure. Except where stated otherwise, it is recommended that this bit be Set if there are multiple Functions, and Clear if there is only one Function. <br> The presence of Shadow Functions does not affect this bit. <br> For an SR-IOV device, this bit is Set in non-VFs only if there are multiple non-VFs. VFs do not affect the value of bit 7 . | RO <br> VF ROZ |

# 7.5.1.1.10 BIST Register (Offset 0Fh) 

This register is used for control and status of BIST. Functions that do not support BIST must hardwire the register to 00 h . VFs shall not support BIST. A Function whose BIST is invoked must not prevent normal operation of the PCI Express Link. § Table 7-8 describes the bits in the register and § Figure 7-9 shows the register layout.

For an SR-IOV device, if the VF Enable bit is Set in any PF, then software should not invoke BIST in any Function associated with that device.

![img-7.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-7.jpeg)

Figure 7-9 BIST Register

Table 7-8 BIST Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 3:0 | Completion Code - This field encodes the status of the most recent test. A value of 0000 b means that the Function has passed its test. Non-zero values mean the Function failed. Function-specific failure codes can be encoded in the non-zero values. <br> This field's value is only meaningful when BIST Capable is Set and Start BIST is Clear. <br> Default value of this field is 0000 b . <br> This field must be hardwired to 0000 b if BIST Capable is Clear. | $\begin{gathered} \text { RO } \\ \text { VF ROZ } \end{gathered}$ |
| 6 | Start BIST - If BIST Capable is Set, Set this bit to invoke BIST. The Function resets the bit when BIST is complete. Software is permitted to fail the device if this bit is not Clear (BIST is not complete) 2 seconds after it had been Set. <br> Writing this bit to 0 b has no effect. <br> This bit must be hardwired to 0 b if BIST Capable is Clear. | ```RW/RO (see description) VF ROZ``` |
| 7 | BIST Capable - When Set, this bit indicates that the Function supports BIST. When Clear, the Function does not support BIST. | HwInit <br> VF ROZ |

# 7.5.1.1.11 Capabilities Pointer (Offset 34h) 

This register is used to point to a linked list of capabilities implemented by this Function. Since all PCI Express Functions are required to implement the PCI Express Capability structure, which must be included somewhere in this linked list; this register must be non-zero. The bottom two bits are Reserved and must be set to 00b. Software must mask these bits off before using this register as a pointer in Configuration Space to the first entry of a linked list of new capabilities. This register is HwInit.

### 7.5.1.1.12 Interrupt Line Register (Offset 3Ch)

The Interrupt Line register communicates interrupt line routing information. The register is read/write and must be implemented by any Function that uses an interrupt pin (see following description). Values in this register are programmed by system software and are system architecture specific. The Function itself does not use this value; rather the value in this register is used by device drivers and operating systems. If Interrupt Pin Register is 00 h , this register is permitted to be hardwired to 0 b . Otherwise, the default value is implementation specific.

For VFs, this register does not apply and must be hardwired to Zero.

# 7.5.1.1.13 Interrupt Pin Register (Offset 3Dh) 

The Interrupt Pin register is a read-only register that identifies the legacy interrupt Message(s) the Function uses (see § Section 6.1 for further details). Valid values are $01 \mathrm{~h}, 02 \mathrm{~h}, 03 \mathrm{~h}$, and 04 h that map to legacy interrupt Messages for INTA, INTB, INTC, and INTD respectively. A value of 00 h indicates that the Function uses no legacy interrupt Message(s). The values 05 h through FFh are Reserved.

PCI Express defines one legacy interrupt Message for a Single-Function Device and up to four legacy interrupt Messages for a Multi-Function Device. For a Single-Function Device, only INTA may be used.

Any Function on a Multi-Function Device can use any of the INTx Messages. If a device implements a single legacy interrupt Message, it must be INTA; if it implements two legacy interrupt Messages, they must be INTA and INTB; and so forth. For a Multi-Function Device, all Functions may use the same INTx Message or each may have its own (up to a maximum of four Functions) or any combination thereof. A single Function can never generate an interrupt request on more than one INTx Message.

For VFs, this register does not apply and must be hardwired to Zero.

### 7.5.1.1.14 Error Registers

The Error Control/Status register bits in the Command and Status registers (see § Section 7.5.1.1.3 and § Section 7.5.1.1.4 respectively) and the Bridge Control Register and Secondary Status Register of Type 1 Configuration Space Header Functions (see § Section 7.5.1.3.10 and § Section 7.5.1.3.7 respectively) control PCI-compatible error reporting for both PCI and PCI Express device Functions. Mapping of PCI Express errors onto PCI errors is also discussed in § Section 6.2.7.1 . In addition to the PCI-compatible error control and status, PCI Express error reporting may be controlled separately from PCI device Functions through the PCI Express Capability structure described in § Section 7.5.3. The PCI-compatible error control and status register fields do not have any effect on PCI Express error reporting enabled through the PCI Express Capability structure. PCI Express device Functions may implement optional advanced error reporting as described in § Section 7.8.4 .

For PCI Express Root Ports represented by a Type 1 Configuration Space Header:

- The primary side Error Control/Status registers apply to errors detected on the internal logic associated with the Root Complex.
- The secondary side Error Control/Status registers apply to errors detected on the Link originating from the Root Port.

For PCI Express Switch Upstream Ports represented by a Type 1 Configuration Space Header:

- The primary side Error Control/Status registers apply to errors detected on the Upstream Link of the Switch.
- The secondary side Error Control/Status registers apply to errors detected on the internal logic of the Switch.

For PCI Express Switch Downstream Ports represented by a Type 1 Configuration Space Header:

- The primary side Error Control/Status registers apply to errors detected on the internal logic of the Switch.
- The secondary side Error Control/Status registers apply to errors detected on the Downstream Link originating from the Switch Port.

# 7.5.1.2 Type 0 Configuration Space Header $\S$ 

\$ Figure 7-10 details allocation for register fields of Type 0 Configuration Space Header for PCI Express device Functions.
![img-8.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-8.jpeg)

Figure 7-10 Type 0 Configuration Space Header $\S$
\$ Section 7.5.1.1 details the PCI Express-specific registers that are valid for all Configuration Space Header types. The PCI Express-specific interpretation of registers specific to Type 0 Configuration Space Header is defined in this section.

### 7.5.1.2.1 Base Address Registers (Offset 10h - 24h) $\S$

System software must build a consistent address map before booting the machine to an operating system. This means it has to determine how much memory is in the system, and how much address space the Functions in the system require. After determining this information, system software can map the Functions into reasonable locations and proceed with

system boot. In order to do this mapping in a device-independent manner, the base registers for this mapping are placed in the predefined header portion of Configuration Space. It is strongly recommended that power-up firmware/software also support the optional Enhanced Configuration Access Mechanism (ECAM).

For VFs, these registers must be hardwired to Zero. See § Section 9.2.1.1.1 and § Section 9.3.3.14.
Bit 0 in all Base Address registers is read-only and used to determine whether the register maps into Memory or I/O Space. Base Address registers that map to Memory Space must return a 0b in bit 0 (see § Figure 7-11). Base Address registers that map to I/O Space must return a 1b in bit 0 (see § Figure 7-12).
![img-9.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-9.jpeg)

Figure 7-11 Base Address Register for Memory 9
![img-10.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-10.jpeg)

Figure 7-12 Base Address Register for I/O 9

Base Address registers that map into I/O Space are always 32 bits wide with bit 0 hardwired to 1b. Bit 1 is Reserved and must return 0b on reads and the other bits are used to map the Function into I/O Space.

Base Address registers that map into Memory Space can be 32 bits or 64 bits wide (to support mapping into a 64-bit address space) with bit 0 hardwired to 0b. It is strongly recommended for each Memory BAR in a PCI Express component to be 64 bits wide. Each Memory BAR in a PCI Express component is permitted to be 32 bits wide.

# IMPLEMENTATION NOTE: GUIDANCE ON MEMORY BAR SIZES 

A key reason for making Memory BARs 64 bits wide is to avoid possible shortages of 32-bit MMIO space. Typical systems limit that space to 1 GB , and some support even less. If a 32-bit Memory BAR consumes 64 MB , only sixteen such BARs would consume the entire 1 GB of space, which is inadequate for some platforms. Memory BAR alignment constraints can further reduce the available space when different-sized Memory BARs are comingled in MMIO space.

A key reason for making Memory BARs 32 bits wide has been when a single Function requires greater than three MMIO ranges, since only three 64-bit BARs will fit inside the Base Address Registers area within a Type 0 Configuration Space Header. This led to some Functions using 32-bit Memory BARs. It is strongly recommended instead to combine multiple MMIO ranges under a single 64-bit BAR, properly aligned and separated to satisfy applicable processor page-size requirements.

Existing PCle components may have used 32-bit Memory BARs for a variety of other reasons. It is strongly recommended that new designs use 64-bit Memory BARs wherever possible.

For Memory Base Address registers, bits 2 and 1 have an encoded meaning as shown in § Table 7-9. The historical definition of bit 3 is now deprecated, and bit 3 is undefined. However, for backward compatibility with legacy system software, it is strongly recommended that bit 3 be Set for 64-bit Memory BARs and Clear for 32-bit Memory BARs. Bits 3-0 are read-only.

If a Host Bridge supports processor Memory Write byte merging ${ }^{164}$, this feature must be disabled unless mechanisms outside the scope of this specification prevent the feature from merging such writes that target any Function's Memory BAR range (regardless of the BAR's bit 3 value) that cannot tolerate them.

Table 7-9 Memory Base Address Register Bits 2:1 Encoding

| Bits 2:1(b) | Meaning |
| :--: | :-- |
| 00 | Base register is 32 bits wide and can be mapped anywhere in the 32 address bit Memory Space. |
| 01 | Reserved ${ }^{165}$ |
| 10 | Base register is 64 bits wide and can be mapped anywhere in the 64 address bit Memory Space. |
| 11 | Reserved |

The number of upper bits that a Function actually implements depends on how much of the address space the Function will respond to. A 32-bit Base Address register supports a single, implementation specific, memory size that is a power of 2, from 16 bytes to 256 Bytes (I/O Space) or 128 Bytes to 2 GB (Memory Space). Each BAR must implement all appropriate upper address bits as Read-Write (i.e., a BAR must be able to be configured to any appropriately aligned address in the associated address space). A Function that wants a 1 MB memory address space (using a single 32-bit Base Address register) must implement the top 12 bits of the Address register as Read-Write, hardwiring the other address bits to 0's. The default value of Read-Write bits in BARs is implementation specific. The attributes for some of the bits in the BAR are affected by the Resizable BAR Capability, if it is implemented.

To determine how much address space a Function requires, system software should write a value of all 1's to each BAR register and then read the value back. Low-order bits of the Base Address field in each BAR must return 0's to indicate how much address space is required. Unimplemented Base Address registers must be hardwired to zero.

[^0]
[^0]:    164. Refer to [PCI] for the definition and examples of byte merging.
    165. The encoding to support memory space below 1 MB was supported in an earlier version of the PCI Local Bus Specification. System software should recognize this encoding and handle it appropriately.

This design implies that all address spaces used are a power of two in size and are naturally aligned. Functions are free to consume more address space than required, but decoding down to a 4 KB space for memory is suggested for Functions that need less than that amount. For instance, a Function that has 64 bytes of registers to be mapped into Memory Space may consume up to 4 KB of address space in order to minimize the number of bits in the address decoder. Functions that do consume more address space than they use are not required to respond to the unused portion of that address space if the Function's programming model never accesses the unused space. The Function is permitted to return Unsupported Request for accesses targetting the unused locations. Functions that map control functions into I/O Space must not consume more than 256 bytes per I/O Base Address register or per each entry in the Enhanced Allocation Capability. The upper 16 bits of the I/O Base Address register may be hardwired to zero for Functions intended for 16-bit I/O systems, such as PC compatibles. However, a full 32-bit decode of I/O addresses must still be done.

A Type 0 Configuration Space Header has six DWORD locations allocated for Base Address registers starting at offset 10 h in Configuration Space. A Type 1 Configuration Space Header has only two DWORD locations. A Function may use any of the locations to implement Base Address registers. An implemented 64-bit Base Address register consumes two consecutive DWORD locations. Software looking for implemented Base Address registers must start at offset 10 h and continue upwards through offset 24 h . A typical Function requires one memory range for its control functions.

Some graphics Functions use two ranges, one for control functions and another for a frame buffer. A Function that wants to map control functions into both memory and I/O Spaces at the same time must implement two Base Address registers (one memory and one I/O) but such implementations are strongly discouraged in Functions that do not need to support legacy programming models. Depending on the operating system, the driver for that Function might only use one space in which case the other space will be unused. Functions are strongly recommended to always map control functions into Memory Space. When possible, it is strongly recommended for Functions not to request I/O Space resources.

# IMPLEMENTATION NOTE: I/O BARS SHOULD BE AVOIDED WHEN POSSIBLE 

I/O Space is a limited resource in all systems. The use of such resources should be avoided when possible, and otherwise minimized.

Due to the 4-KB minimum granularity of any bridge's I/O forwarding range, a Function that requests the minimum 256 bytes in an I/O BAR will still force the system to allocate at least 4 KB of I/O Space to the bridge under which that Function resides. If a hierarchy domain contains multiple bridges, then the system may be forced to allocate even more I/O Space to satisfy a Function's I/O BAR(s).

Each Function has a limited number of BARs. Each implemented I/O BAR either reduces the number or size of possible Memory BARs. With a Legacy Endpoint, if the platform is unable to allocate I/O Space for any implemented I/O BARs, then the platform might not enable the Legacy Endpoint, even if the Legacy Endpoint can operate without allocated I/O Space. If any PCI Express Endpoints implement I/O BARs and the platform allocates I/O Space for them, this may contribute to a shortage of I/O Space for any Legacy Endpoints that are present. For these reasons, implementing I/O BARs should be avoided when possible.

The minimum Memory Space address range requested by a BAR is 128 bytes. The attributes for some of the bits in the BAR are affected by the Resizable BAR Capability, if it is implemented.

# IMPLEMENTATION NOTE: ORGANIZATION OF MMIO SPACE BY ATTRIBUTES 

Processor architectures typically assign specific attributes to memory resources. These attributes impact the functionality and performance of memory operations and are outside the scope of this document. However, by following certain guidance in relation to these attributes, the interoperability and usability of PCI Express components can be significantly improved. This guidance applies to all situations, including but not limited to host processors, where code execution triggers the generation of Request TLPs and allows software/firmware developers the ability to control such aspects as sequencing, operation size, and address alignment. The concepts also apply to special-purpose hardware for generating Request TLPs, but it is generally assumed that the designers of such hardware have a more thorough control of Request TLP generation and understanding of Completer expectations, as compared to creators of software/firmware, where this is abstracted.

Processor memory attributes are typically assigned at the page level. This is the granularity at which software/ firmware can reason about security properties and about a restricted programming model ${ }^{166}$. Devices are strongly encouraged to organize MMIO space allocated via BARs as required to ensure that memory ranges with different access attribute requirements are located in different naturally aligned blocks, with a minimum block size of 4 KB and a recommended block size of at least 64 KB .

Some processor memory attributes may result in a TLP sequence that is closely correlated with the processor instruction sequence while other processor memory attributes may permit techniques like write combining, speculation of reads, and reordering of memory operations when creating TLPs from an instruction sequence.

Regardless of the attributes, it is strongly recommended that Read Side Effects are not implemented for any MMIO address unless the system aspects of such Read Side Effects are understood and managed.

Processor architectures are encouraged to clearly document the mechanisms for configuring memory attributes for MMIO ranges.

Device-specific software is expected to understand the device requirements of each range and choose an acceptable memory attribute. When device peer-to-peer operations are supported, the same considerations apply to the involved devices as to hosts.

Previous revisions of this specification indicated that access properties were correlated with the BAR register and address range chosen to define the MMIO space. Since TLPs must follow the same set of rules regardless of BAR programming it has always been permitted for host/device software/hardware to determine and use appropriate memory access attributes. Because 64-bit BARs provide significantly better ability to manage system MMIO resources, devices are strongly encouraged to use 64-bit BARs.

### 7.5.1.2.2 Cardbus CIS Pointer Register (Offset 28h)

This register was originally described in the [PC-Card]. This register does not apply to PCI Express and must be hardwired to Zero.

### 7.5.1.2.3 Subsystem Vendor ID Register/Subsystem ID Register (Offset 2Ch/2Eh)

The Subsystem Vendor ID and Subsystem ID registers are used to uniquely identify the adapter or subsystem where the PCI Express component resides. They provide a mechanism for vendors to distinguish their products from one another

even though the assemblies may have the same PCI Express component on them (and, therefore, the same Vendor ID and Device ID).

Implementation of these registers is required for all Functions except those that have a Base Class 06h with Sub Class 00h-04h (00h, 01h, 02h, 03h, 04h), or a Base Class 08h with Sub Class 00h-03h (00h, 01h, 02h, 03h). Subsystem Vendor IDs can be obtained from the PCI SIG and are used to identify the vendor of the adapter, motherboard, or subsystem ${ }^{167}$. A Subsystem Vendor ID (SVID) must be a Vendor ID assigned by the PCI-SIG to the vendor of the subsystem. In keeping with PCI-SIG procedures, valid vendor identifiers must be obtained from the PCI-SIG to ensure uniqueness.

Values for the Subsystem ID are vendor assigned. Subsystem ID values, in conjunction with the Subsystem Vendor ID, form a unique identifier for the PCI product. Subsystem ID and Device ID values are distinct and unrelated to each other, and software should not assume any relationship between them.

Values in these registers must be loaded before the Function becomes Configuration-Ready. How these values are loaded is not specified but could be done during the manufacturing process or loaded from external logic (e.g., strapping options, serial ROMs, etc.). These values must not be loaded using Expansion ROM software because Expansion ROM software is not guaranteed to be run during POST in all systems.

If a device is designed to be used exclusively on the system board, the system vendor may use system specific software to initialize these registers after each power-on.

The Subsystem Vendor ID register in a PF and its associated VFs must return the same value when read.
The Subsystem ID register in a PF and its associated VFs are permitted to return different values when read.

# IMPLEMENTATION NOTE: SUBSYSTEM VENDOR ID AND SUBSYSTEM ID 

The Subsystem Vendor ID and Subsystem ID fields, taken together, allow software to uniquely identify a PCI circuit board product. Vendors should therefore not reuse Subsystem ID values across multiple product types that share a common Subsystem Vendor ID. It is acceptable, although not preferred, to reuse the Subsystem ID value on products with the same Subsystem Vendor ID in cases where the products are in the same family and generation, and differ only in capacity or performance. Note also that it is acceptable for vendors to use multiple unique Subsystem ID values over time for a single product type, such as to indicate some internal difference such as component selection.

### 7.5.1.2.4 Expansion ROM Base Address Register (Offset 30h)

Some Functions, especially those that are intended for use on add-in cards, require local EPROMs for Expansion ROM (refer to the [Firmware] for a definition of ROM contents). This register is defined to handle the base address and size information for this Expansion ROM. The register layout is shown in § Figure 7-13 and § Table 7-10 describes the bits in the register.

For VFs, the Expansion ROM Base Address register is not supported and must be hardwired to Zero. The VI may choose to provide access to a PF's Expansion ROM Base Address register for its associated VFs via emulation.

Functions that support an expansion ROM must allow that ROM to be accessed with any combination of byte enables.

[^0]
[^0]:    167. A company requires only one Vendor ID. That value can be used in either the Vendor ID register of Configuration Space (e.g., offset 00h) or the Subsystem Vendor ID register of Configuration Space (e.g., offset 2Ch). It is used in the Vendor ID register (e.g., offset 00h) if the company built the silicon. It is used in the Subsystem Vendor ID register (e.g., offset 2Ch) if the company built the assembly. If a company builds both the silicon and the assembly, then the same value would be used in both registers.

![img-11.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-11.jpeg)

Figure 7-13 Expansion ROM Base Address Register

Table 7-10 Expansion ROM Base Address Register

| Bit Location | Description | Attributes |
| :--: | :--: | :--: |
| 0 | Expansion ROM Enable - This bit controls whether or not the Function accepts accesses to its Expansion ROM via the Expansion ROM Base Address Register. Functions that support an Expansion ROM accessible through this register must implement this bit. If the Function has an Enhanced Allocation Capability that includes an EA entry for an Expansion ROM, this bit must be hardwired to 0 b (see § Section 7.5.1.2.4). Functions that do not support an Expansion ROM are permitted to hardwire this bit to 0b. When this bit is 0b, the Function's Expansion ROM address space via the Expansion ROM Base Address Register is disabled. When the bit is 1b, address decoding is enabled using the Expansion ROM Base Address field in this register. This optionally allows a Function to be used with or without an Expansion ROM depending on system configuration. The Memory Space Enable bit in the Command register has precedence over the Expansion ROM Enable bit. A Function must claim accesses to its Expansion ROM via the Expansion ROM Base Address Register only if both the Memory Space Enable bit and the Expansion ROM Enable bit are Set. The default value of this bit is 0 b. <br> In order to minimize the number of address decoders needed, a Function is permitted to share a decoder between the Expansion ROM Base Address Register and other Base Address registers or entries in the Enhanced Allocation Capability ${ }^{168}$. When Expansion ROM Enable is Set, the decoder is used for accesses to the Expansion ROM and device independent software must not access the Function through any other Base Address Registers or entries in the Enhanced Allocation Capability. Address decode sharing is not permitted for PFs or if the Function contains an Enhanced Allocation Capability with an EA entry for an Expansion ROM. | RO/RW |
| $3: 1$ | Expansion ROM Validation Status - Expansion ROM Validation is optional. When this field is non-zero, it indicates the status of hardware validation of the Expansion ROM contents. <br> - An Expansion ROM is considered valid if it passes an implementation specific integrity check. <br> - An Expansion ROM is considered valid-warn if the implementation specific integrity check passes but indicates an implementation specific warning condition. <br> - A valid or valid-warn Expansion ROM is also considered trusted if passes an optional implementation specific trust test (e.g., signed by a trusted certificate). <br> - Hardware validation must include the contents of the Expansion ROM. This validation status is also permitted to cover additional internal information (e.g., internal firmware). Validation does not include Vital Product Data (see § Section 6.27 ). <br> - It is optional whether an implementation is capable of returning Validation Status values $011 \mathrm{~b}, 101 \mathrm{~b}, 110 \mathrm{~b}$, or 111 b . <br> Defined encodings are: | HwInit/ROS |

[^0]
[^0]:    168. Note that it is the address decoder that is shared, not the registers themselves. The Expansion ROM Base Address Register and other Base Address Registers or entries in the Enhanced Allocation Capability must be able to hold unique values at the same time.

| Bit Location | Description | Attributes |
| :--: | :--: | :--: |
|  | 000b <br> 001b <br> 010b <br> 100b <br> 101b <br> 110b <br> 111b <br> 110b <br> 111b <br> 7:4 | Validation not supported <br> Validation in Progress <br> Validation Pass Valid contents, trust test was not performed <br> Validation Pass Valid and trusted contents <br> Validation Fail Invalid contents <br> Validation Fail Valid but untrusted contents (e.g., Out of Date, Expired or Revoked Certificate) <br> Warning Pass Validation Passed with implementation specific warning. Valid contents, trust test was not performed <br> Warning Pass Validation Passed with implementation specific warning. Valid and trusted contents <br> - If the Function does not support validation, this field must be hardwired to 000b. <br> - If the Function supports validation and has an Enhanced Allocation Capability with an EA entry for an Expansion ROM, this field is HwInit and its value must be between 010b and 111b (see § Section 7.8.5.3 ). <br> - Otherwise, this field is Read Only Sticky and has a default value of 001b. When validation completes, this field must contain a value between 010b and 111b inclusive. <br> - Software is permitted to assume validation will never complete if this field contains 001b and 1 minute has passed after de-assertion of Fundamental Reset. This field is only reset by Fundamental Reset, and is not affected by other resets. |  |
|  | Expansion ROM Validation Details - contains optional, implementation specific details associated with Expansion ROM Validation. <br> - If the Function does not support validation, this field is RsvdP. <br> - This field is optional. When validation is supported and this field is not implemented, this field must be hardwired to 0000b. Any unused bits in this field are permitted to be hardwired to 0 b . <br> - If validation is in progress (Expansion ROM Validation Status is 001b), non-zero values of this field represent implementation specific indications of the phase of the validation progress (e.g., 50\% complete). The value 0000b indicates that no validation progress information is provided. <br> - If validation is completed (Expansion ROM Validation Status 010b to 111b inclusive), non-zero values in this field represent additional implementation specific information. The value 0000b indicates that no information is provided. <br> - If the Function supports validation and has an Enhanced Allocation Capability with an EA entry for an Expansion ROM, this field is HwInit. <br> - Otherwise, this field is Read Only Sticky. This field is only reset by Fundamental Reset, and is not affected by other resets. <br> - This field must not change value once the validation process completes. <br> - It is recommended that system software include the value of this field when it reports validation status (e.g., error log). | HwInit/ROS/RsvdP |
| 31:11 | Expansion ROM Base Address - contains the upper bits 21 bits of the starting memory address of the Expansion ROM. The lower 11 bits of the Expansion ROM Base Address Register are masked off (set to zero) by software to form a 32-bit address. | RW/RO |

| Bit Location | Description | Attributes |
| :--: | :--: | :--: |
|  | This field functions like the address portion of a 32-bit Base Address register. This field corresponds to the upper 21 bits of the Expansion ROM Base Address. The number of bits (out of these 21) that a Function actually implements depends on how much Expansion ROM address space the Function requires. For instance, a Function that requires a 64 KB area to map its Expansion ROM would implement the top 16 bits in this field as writeable, leaving the bottom 5 bits (out of these 21) hardwired to 0 b . The amount of address space a Function requests must not be greater than 16 MB . Functions that support an Expansion ROM accessible through this register must implement this field. If the Function has an Enhanced Allocation Capability that includes an EA entry for an Expansion ROM, this field must be hardwired to 0 (see § Section 7.8.5.3) Functions that do not support an Expansion ROM are permitted to hardwire this field to 0 . <br> Device independent configuration software can determine how much address space the Function requires by writing a value of all 1's to this field and then reading the value back. Low order bits of this field must return 0 's in all don't-care bits, effectively specifying the size and alignment requirements. The amount of address space a Function requests must not be greater than 16 MB . |  |  |

# 7.5.1.2.5 Min_Gnt Register/Max_Lat Register (Offset 3Eh/3Fh) 

These registers do not apply to PCI Express and must be hardwired to Zero.

### 7.5.1.3 Type 1 Configuration Space Header

§ Figure 7-14 details allocation for register fields of Type 1 Configuration Space Header for Switch and Root Ports.

![img-12.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-12.jpeg)

Figure 7-14 Type 1 Configuration Space Header
$\S$ Section 7.5.1.1 details the PCI Express-specific registers that are valid for all Configuration Space Header types. The PCI Express-specific interpretation of registers specific to Type 1 Configuration Space Header is defined in this section. Register interpretations described in this section apply to PCI-PCI Bridge structures representing Switch and Root Ports; other device Functions such as PCI Express to PCI/PCI-X Bridges with Type 1 Configuration Space headers are not covered by this section.

TLP routing is determined by the following registers, along with FPB (if implemented):

- Primary Bus Number
- Secondary Bus Number
- Subordinate Bus Number
- I/O Base
- I/O Limit

- Memory Base
- Memory Limit
- 64-bit Memory Base
- 64-bit Memory Limit
- 64-bit Base Upper 32 Bits
- 64-bit Limit Upper 32 Bits
- I/O Base Upper 16 Bits
- I/O Base Limit 16 Bits


# 7.5.1.3.1 Type 1 Base Address Registers (Offset 10h-14h) 

These registers are defined in § Section 7.5.1.2.1 . However the number of BARs available within the Type 1 Configuration Space Header is different than that of the Type 0 Configuration Space Header.

### 7.5.1.3.2 Primary Bus Number Register (Offset 18h) 

Except as noted, this register is not used by PCI Express Functions but must be implemented as read-write and the default value must be 00 h , for compatibility with legacy software. PCI Express Functions capture the Bus (and Device) Number as described (including exceptions) in § Section 2.2.6. Refer to [PCIe-to-PCI-PCI-X-Bridge] for exceptions to this requirement.

### 7.5.1.3.3 Secondary Bus Number Register (Offset 19h)

The Secondary Bus Number register is used to record the bus number of the PCI bus segment to which the secondary interface of the bridge is connected. Configuration software programs the value in this register. The Bridge uses this register to determine when and how to respond to an ID-routed TLP observed on its primary interface, notably when to forward the TLP to its secondary interface, in certain cases after performing some conversion. See § Section 7.3.3 for Configuration Request routing and conversion rules. This register must be implemented as read/write and the default value must be 00 h .

### 7.5.1.3.4 Subordinate Bus Number Register (Offset 1Ah)

The Subordinate Bus Number register is used to record the bus number of the highest numbered PCI bus segment which is behind (or subordinate to) the bridge. Configuration software programs the value in this register. The Bridge uses this register to determine when and how to respond to an ID-routed TLP observed on its primary interface, notably when to forward the TLP to its secondary interface. See § Section 7.3.3 for Configuration Request routing rules. This register must be implemented as read-write and the default value must be 00 h .

### 7.5.1.3.5 Secondary Latency Timer (Offset 1Bh)

This register does not apply to PCI Express. It must be read-only and hardwired to 00h. For PCI Express to PCI/PCI-X Bridges, refer to the [PCIe-to-PCI-PCI-X-Bridge] for requirements for this register.

# 7.5.1.3.6 I/O Base/I/O Limit Registers(Offset 1Ch/1Dh) 

The I/O Base and I/O Limit registers are optional and define an address range that is used by the bridge to determine when to forward I/O transactions from one interface to the other.

If a bridge does not implement an I/O address range, then both the I/O Base and I/O Limit registers must be implemented as read-only registers that return zero when read. If a bridge supports an I/O address range, then these registers must be initialized by configuration software so default states are not specified.

If a bridge implements an I/O address range, the upper 4 bits of both the I/O Base and I/O Limit registers are writable and correspond to address bits Address[15:12]. For the purpose of address decoding, the bridge assumes that the lower 12 address bits, Address[11:0], of the I/O base address (not implemented in the I/O Base register) are zero. Similarly, the bridge assumes that the lower 12 address bits, Address[11:0], of the I/O limit address (not implemented in the I/O Limit register) are FFFh. Thus, the bottom of the defined I/O address range will be aligned to a 4 KB boundary and the top of the defined I/O address range will be one less than a 4 KB boundary.

The I/O Limit register can be programmed to a smaller value than the I/O Base register, if there are no I/O addresses on the secondary side of the bridge. In this case, the bridge will not forward any I/O transactions from the primary bus to the secondary and will forward all I/O transactions from the secondary bus to the primary bus.

The lower four bits of both the I/O Base and I/O Limit registers are read-only, contain the same value, and encode the I/O addressing capability of the bridge according to $\S$ Table 7-11.

Table 7-11 I/O Addressing
Capability

| Bits 3:0 | I/O Addressing Capability |
| :--: | :--: |
| 0h | 16-bit I/O addressing |
| 1h | 32-bit I/O addressing |
| 2h-Fh | Reserved |

If the low four bits of the I/O Base and I/O Limit registers have the value 0000b, then the bridge supports only 16-bit I/O addressing (for ISA compatibility), and, for the purpose of address decoding, the bridge assumes that the upper 16 address bits, Address[31:16], of the I/O base and I/O limit address (not implemented in the I/O Base and I/O Limit registers) are zero. Note that the bridge must still perform a full 32-bit decode of the I/O address (i.e., check that Address[31:16] are 0000h). In this case, the I/O address range supported by the bridge will be restricted to the first 64 KB of I/O Space ( 00000000 h to 0000 FFFFh).

If the low four bits of the I/O Base and I/O Limit registers are 0001b, then the bridge supports 32-bit I/O address decoding, and the I/O Base Upper 16 Bits and the I/O Limit Upper 16 Bits hold the upper 16 bits, corresponding to Address[31:16], of the 32-bit I/O Base and I/O Limit addresses respectively. In this case, system configuration software is permitted to locate the I/O address range supported by the bridge anywhere in the 4 GB I/O Space. Note that the 4 KB alignment and granularity restrictions still apply when the bridge supports 32-bit I/O addressing.

These registers must be initialized by configuration software, so default states are not specified.

### 7.5.1.3.7 Secondary Status Register (Offset 1Eh)

§ Table 7-12 defines the Secondary Status Register and § Figure 7-15 provides the register layout. For PCI Express to PCI/ PCI-X Bridges, refer to the [PCle-to-PCI-PCI-X-Bridge] for requirements for this register.

![img-13.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-13.jpeg)

Figure 7-15 Secondary Status Register

Table 7-12 Secondary Status Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 5 | 66 MHz Capable - This bit was originally described in the [PCI-to-PCI-Bridge]. Its functionality does not apply to PCI Express and the bit must be hardwired to 0 b. | RO |
| 7 | Fast Back-to-Back Transactions Capable - This bit was originally described in the [PCI-to-PCI-Bridge]. Its functionality does not apply to PCI Express and the bit must be hardwired to 0 b. | RO |
| 8 | Master Data Parity Error - See § Section 7.5.1.1.14 . <br> This bit is Set by a Function with a Type 1 Configuration Space Header if the Parity Error Response Enable bit in the Bridge Control Register is Set and either of the following two conditions occurs: <br> Port receives a Poisoned Completion coming Upstream <br> Port transmits a Poisoned Request Downstream <br> If the Parity Error Response Enable bit is Clear, this bit is never Set. <br> Default value of this bit is 0 b . | RW1C |
| 10:9 | DEVSEL Timing - This field was originally described in the [PCI-to-PCI-Bridge]. Its functionality does not apply to PCI Express and the field must be hardwired to 00 b. | RO |
| 11 | Signaled Target Abort - See § Section 7.5.1.1.14 . <br> This bit is Set when the Secondary Side for Type 1 Configuration Space Header Function (for Requests completed by the Type 1 header Function itself) completes a Posted or Non-Posted Request as a Completer Abort error. <br> Default value of this bit is 0 b . | RW1C |
| 12 | Received Target Abort - See § Section 7.5.1.1.14 . <br> This bit is Set when the Secondary Side for Type 1 Configuration Space Header Function (for Requests initiated by the Type 1 header Function itself) receives a Completion with Completer Abort Completion Status. | RW1C |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | Default value of this bit is 0 b. |  |
| 13 | Received Master Abort - See § Section 7.5.1.1.14. <br> This bit is Set when the Secondary Side for Type 1 Configuration Space Header Function (for Requests initiated by the Type 1 header Function itself) receives a Completion with Unsupported Request Completion Status. <br> Default value of this bit is 0 b . | RW1C |
| 14 | Received System Error - See § Section 7.5.1.1.14. <br> This bit is Set when the Secondary Side for a Type 1 Configuration Space Header Function receives an ERR_FATAL or ERR_NONFATAL Message. <br> Default value of this bit is 0 b . | RW1C |
| 15 | Detected Parity Error - See § Section 7.5.1.1.14. <br> This bit is Set by a Function with a Type 1 Configuration Space Header when a Poisoned TLP is received by its Secondary Side, regardless of the state the Parity Error Response Enable bit in the Bridge Control Register. <br> Default value of this bit is 0 b . | RW1C |

# 7.5.1.3.8 Memory Base Register/Memory Limit Register(Offset 20h/22h) 

The Memory Base and Memory Limit registers define a memory mapped address range which is used by the bridge to determine when to forward memory transactions from one interface to the other (see the [PCI-to-PCI-Bridge] for additional details).

The upper 12 bits of both the Memory Base and Memory Limit registers are read/write and correspond to the upper 12 address bits, Address[31:20], of 32-bit addresses. For the purpose of address decoding, the bridge assumes that the lower 20 address bits, Address[19:0], of the memory base address (not implemented in the Memory Base register) are zero. Similarly, the bridge assumes that the lower 20 address bits, Address[19:0], of the memory limit address (not implemented in the Memory Limit register) are F FFFFh. Thus, the bottom of the defined memory address range will be aligned to a 1 MB boundary and the top of the defined memory address range will be one less than a 1 MB boundary.

The Memory Limit register must be programmed to a smaller value than the Memory Base register if there is no memory-mapped address space on the secondary side of the bridge.

The bottom four bits of both the Memory Base and Memory Limit registers are read-only and return zeros when read.
These registers must be initialized by configuration software, so default states are not specified.

### 7.5.1.3.9 64-bit Memory Base/64-bit Memory Limit Registers (Offset 24h/26h) and 64-bit Base Upper 32 Bits/64-bit Limit Upper 32 Bits Registers (Offset 28h/2Ch)

The 64-bit Memory Base and 64-bit Memory Limit registers define a memory address range that is used by the bridge to determine when to forward memory transactions from one interface to the other.

If not implemented, both the 64-bit Memory Base and 64-bit Memory Limit registers must be read-only and return zero when read.

If the bridge implements these registers, the upper 12 bits of each register are read/write and correspond to Address[31:20], of a 64-bit address. For the purpose of address decoding, the bridge assumes that the lower 20 address bits, Address[19:0], of the 64-bit base address are zero. Similarly, the bridge assumes that the lower 20 address bits, Address[19:0], of the 64-bit limit address are F FFFFh. Thus, the bottom of the memory address range will be aligned to a 1 MB boundary and the top of the defined memory address range will be one less than a 1 MB boundary.

The 64-bit Base Upper 32 Bits and 64-bit Limit Upper 32 Bits registers (defined below) correspond to Address[63:32] of the Base and Limit addresses, respectively.

If it is intended that these registers not be used to indicate memory mapped to the secondary side of the bridge, System Software must program the 64-bit Memory Limit register to a smaller value than the 64-bit Memory Base register.

The bottom 4 bits of both the 64-bit Memory Base and 64-bit Memory Limit registers must be read-only, contain the same value, and encode whether or not the bridge supports 64-bit addresses. If these four bits have the value 0 h , then the 64-bit Base/Limit Upper 32 registers are ignored and treated as containing all zeros. If these four bits have the value 01h, then the bridge supports 64-bit addresses and the 64-bit Base Upper 32 Bits and 64-bit Limit Upper 32 Bits registers hold the rest of the 64-bit base and limit addresses respectively. All other encodings are Reserved.

These registers must be initialized by configuration software, so default states are not specified.

# 7.5.1.3.10 64-bit Base Upper 32 Bits/64-bit Limit Upper 32 Bits Registers (Offset 28h/2Ch) 

If not implemented, then both 64-bit Base Upper 32 Bits and 64-bit Limit Upper 32 Bits registers must be read-only and return zero when read. If a bridge implements these registers, then both of these registers must be implemented as read/ write registers that must be initialized by configuration software. They specify the upper 32 bits, corresponding to Address[63:32], of the 64-bit base and limit addresses.

These registers must be initialized by configuration software, so default states are not specified.

### 7.5.1.3.11 I/O Base Upper 16 Bits/I/O Limit Upper 16 Bits Registers (Offset 30h/32h)

The I/O Base Upper 16 Bits and I/O Limit Upper 16 Bits registers are optional extensions to the I/O Base and I/O Limit registers. If the I/O Base and I/O Limit registers indicate support for 16-bit I/O address decoding, then the I/O Base Upper 16 Bits and I/O Limit Upper 16 Bits registers are implemented as read-only registers which return zero when read.

If the I/O Base and I/O Limit registers indicate support for 32-bit I/O addressing, then the I/O Base Upper 16 Bits and I/O Limit Upper 16 Bits registers must be initialized by configuration software so default states are not specified.

If 32-bit I/O address decoding is supported, the I/O Base Upper 16 Bits and the I/O Limit Upper 16 Bits registers specify the upper 16 bits, corresponding to Address[31:16], of the 32-bit base and limit addresses respectively, that specify the I/O address range (see the [PCI-to-PCI-Bridge] for additional details).

These registers must be initialized by configuration software, so default states are not specified.

### 7.5.1.3.12 Expansion ROM Base Address Register (Offset 38h)

This register is defined in $\S$ Section 7.5.1.2.4. However the offset of the register within the Type 1 Configuration Space Header is different than that of the Type 0 Configuration Space Header.

# 7.5.1.3.13 Bridge Control Register (Offset 3Eh) 

The Bridge Control Register provides extensions to the Command Register that are specific to a Function with a Type 1 Configuration Space Header. The Bridge Control Register provides many of the same controls for the secondary interface that are provided by the Command Register for the primary interface. There are some bits that affect the operation of both interfaces of the bridge.
§ Table 7-13 defines the Bridge Control Register and § Figure 7-16 depicts register layout. For PCI Express to PCI/PCI-X Bridges, refer to the [PCle-to-PCI-PCI-X-Bridge] for requirements for this register.
![img-14.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-14.jpeg)

Figure 7-16 Bridge Control Register

Table 7-13 Bridge Control Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 0 | Parity Error Response Enable - See § Section 7.5.1.1.14 . <br> This bit controls the logging of poisoned TLPs in the Master Data Parity Error bit in the Secondary Status Register. <br> Default value of this bit is Ob. | RW |
| 1 | SERR\# Enable - See § Section 7.5.1.1.14 . <br> This bit controls forwarding of ERR_COR, ERR_NONFATAL and ERR_FATAL from secondary to primary. Default value of this bit is Ob. | RW |
| 2 | ISA Enable - Modifies the response by the bridge to ISA I/O addresses. This applies only to I/O addresses that are enabled by the I/O Base and I/O Limit registers and are in the first 64 KB of I/O address space ( 00000000 h to 0000 FFFFh). If this bit is Set, the bridge will block any forwarding from primary to secondary of I/O transactions addressing the last 768 bytes in each 1 KB block. In the opposite direction | RW |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | (secondary to primary), I/O transactions will be forwarded if they address the last 768 bytes in each 1 KB block. <br> 0b forward downstream all I/O addresses in the address range defined by the I/O Base and I/O Limit registers <br> 1b forward upstream ISA I/O addresses in the address range defined by the I/O Base and I/O Limit registers that are in the first 64 KB of PCI I/O address space (top 768 bytes of each 1 KB block <br> Default value of this bit is 0 b . |  |
| 3 | VGA Enable - Modifies the response by the bridge to VGA compatible addresses. If the VGA Enable bit is Set, the bridge will positively decode and forward the following accesses on the primary interface to the secondary interface (and, conversely, block the forwarding of these addresses from the secondary to primary interface): <br> - Memory accesses in the range 000A 0000h to 000B FFFFh <br> - I/O addresses in the first 64 KB of the I/O address space (Address[31:16] are 0000h) where Address[9:0] are in the ranges 3B0h to 3BBh and 3C0h to 3DFh (inclusive of ISA address aliases determined by the setting of VGA 16-bit Decode) <br> If the VGA Enable bit is Set, forwarding of these accesses is independent of the I/O address range and memory address ranges defined by the I/O Base and Limit registers, the Memory Base and Limit registers, and the 64-bit Memory Base and 64-bit Memory Limit registers of the bridge. Forwarding of these accesses is also independent of the setting of the ISA Enable bit (in the Bridge Control Register) when the VGA Enable bit is Set. Forwarding of these accesses is qualified by the I/O Space Enable and Memory Space Enable bits in the Command Register. <br> 0b do not forward VGA compatible memory and I/O addresses from the primary to the secondary interface (addresses defined above) unless they are enabled for forwarding by the defined I/O and memory address ranges <br> 1b forward VGA compatible memory and I/O addresses (addresses defined above) from the primary interface to the secondary interface (if the I/O Space Enable and Memory Space Enable bits are set) independent of the I/O and memory address ranges and independent of the ISA Enable bit <br> Functions that do not support VGA are permitted to hardwire this bit to 0 b. <br> Default value of this bit is 0 b . | RW |
| 4 | VGA 16-bit Decode - This bit only has meaning if bit 3 (VGA Enable) of this register is also Set, enabling VGA I/O decoding and forwarding by the bridge. <br> This bit enables system configuration software to select between 10-bit and 16-bit I/O address decoding for all VGA I/O register accesses that are forwarded from primary to secondary. <br> 0b execute 10-bit address decodes on VGA I/O accesses <br> 1b execute 16-bit address decodes on VGA I/O accesses <br> Functions that do not support VGA are permitted to hardwire this bit to 0 b . Default value of this bit is 0 b . | RW |
| 5 | Master Abort Mode - This bit was originally described in the [PCI-to-PCI-Bridge]. Its functionality does not apply to PCI Express and the bit must be hardwired to 0 b. | RO |
| 6 | Secondary Bus Reset - Setting this bit triggers a Hot Reset on the Secondary Side PCI Express Port. Software must ensure a minimum reset duration of 1 ms , (corresponding to $T_{\text {rst }}$ in [PCI]). Software and systems must honor first-access-following-reset timing requirements defined in $\S$ Section 6.6 , unless | RW |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | the Readiness Notifications mechanism (see $\S$ Section 6.22 ) is used or if the Immediate Readiness bit in the relevant Function's Status register is Set. <br> Port configuration registers must not be changed, except as required to update Port status. <br> See Implementation Note: Delays in Data Link Layer Link Active Reflecting Link Control Operations for related information. <br> Default value of this bit is Ob. |  |
| 7 | Fast Back-to-Back Transactions Enable - This bit was originally described in the [PCI-to-PCI-Bridge]. Its functionality does not apply to PCI Express and the bit must be hardwired to Ob. | RO |
| 8 | Primary Discard Timer - This bit was originally described in the [PCI-to-PCI-Bridge]. Its functionality does not apply to PCI Express and the bit must be hardwired to Ob. | RO |
| 9 | Secondary Discard Timer - This bit was originally described in the [PCI-to-PCI-Bridge]. Its functionality does not apply to PCI Express and the bit must be hardwired to Ob. | RO |
| 10 | Discard Timer Status - This bit was originally described in the [PCI-to-PCI-Bridge]. Its functionality does not apply to PCI Express and the bit must be hardwired to Ob. | RO |
| 11 | Discard Timer SERR\# Enable - This bit was originally described in the [PCI-to-PCI-Bridge]. Its functionality does not apply to PCI Express and must be hardwired to Ob. | RO |

# 7.5.2 PCI Power Management Capability Structure 

This section describes the registers making up the PCI Power Management Interface structure.
§ Figure 7-17 illustrates the organization of the PCI Power Management Capability structure. This structure is required for all non-VF PCI Express Functions. It is optional for VFs.
![img-15.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-15.jpeg)

Figure 7-17 PCI Power Management Capability Structure

Note: The 8-bit Power Management Data Register (Offset 07h) is optional for both Type 0 and Type 1 Functions.
PCI Express device Functions are required to support D0 and D3 device states; PCI-PCI Bridge structures representing PCI Express Ports as described in $\S$ Section 7.1 are required to indicate PME Message passing capability due to the in-band nature of PME messaging for PCI Express.

The PME_Status bit for the PCI-PCI Bridge structure representing PCI Express Ports, however, is only Set when the PCI-PCI Bridge Function is itself generating a PME. The PME_Status bit is not Set when the Bridge is propagating a PME Message but the PCI-PCI Bridge Function itself is not internally generating a PME.

# 7.5.2.1 Power Management Capabilities Register (Offset 00h) 

\$ Figure 7-18 details allocation of register fields for Power Management Capabilities Register and \$ Table 7-14 describes the requirements for this register.
![img-16.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-16.jpeg)

Figure 7-18 Power Management Capabilities Register

Table 7-14 Power Management Capabilities Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $7: 0$ | Capability_ID - This field returns 01h to indicate that this is the PCI Power Management Capability. Each Function may have only one item in its capability list with Capability_ID set to 01h. | RO |
| $15: 8$ | Next Capability Pointer - This field provides an offset into the Function's Configuration Space pointing to the location of next item in the capabilities list. If there are no additional items in the capabilities list, this field is set to 00 h . | RO |
| $18: 16$ | Version - Must be hardwired to 011b for Functions compliant to this specification. | RO |
| 19 | PME Clock - Does not apply to PCI Express and must be hardwired to 0b. | RO |
| 20 | Immediate_Readiness_on_Return_to_DO - If this bit is a "1", this Function is guaranteed to be ready to successfully complete valid accesses immediately after being set to DO. These accesses include Configuration cycles, and if the Function returns to DO active, they also include Memory and I/O Cycles. <br> When this bit is " 1 ", for accesses to this Function, software is exempt from all requirements to delay accesses following a transition to DO, including but not limited to the 10 ms delay; the delays described in $\S$ Section 5.9 . <br> How this guarantee is established is beyond the scope of this document. <br> It is permitted that system software/firmware provide mechanisms that supersede the indication provided by this bit, however such software/firmware mechanisms are outside the scope of this specification. | RO |
| 21 | Device Specific Initialization - The DSI bit indicates whether special initialization of this Function is required. <br> When Set indicates that the Function requires a device specific initialization sequence following a transition to the $\mathrm{DO}_{\text {uninitialized }}$ state. | RO |
| $24: 22$ | Aux_Current ${ }^{169}$ - This 3 bit field reports the Vaux auxiliary current requirements for the Function. | RO |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | If this Function implements the Power Management Data Register, this field must be hardwired to 000b. If PME_Support is 0 xxxxb (PME assertion from D3 ${ }_{\text {Cold }}$ is not supported) and the Aux Power PM Enable feature is not implemented, this field must be hardwired to 000b. <br> For Functions where PME_Support is 1 xxxxb (PME assertion from D3 ${ }_{\text {Cold }}$ is supported), and which do not implement the Power Management Data Register, the following encodings apply : <br> Encoding Vaux Max. Power Required |  |
|  | 111b 1238 mW (e.g., 3.3 V at 375 mA ) |  |
|  | 110b 1056 mW (e.g., 3.3 V at 320 mA ) |  |
|  | 101b 891 mW (e.g., 3.3 V at 270 mA ) |  |
|  | 100b 726 mW (e.g., 3.3 V at 220 mA ) |  |
|  | 011b 528 mW (e.g., 3.3 V at 160 mA ) |  |
|  | 010b 330 mW (e.g., 3.3 V at 100 mA ) |  |
|  | 001b 182 mW (e.g., 3.3 V at 55 mA ) |  |
|  | 000b 0 mW (no Vaux power or self powered) |  |
|  | For encoding 000b, when the add-in card is self powered (e.g., it contains a battery), it is recommended that the Power Budgeting Extended Capability be used to report the thermal requirements of the add-in card. <br> Note: Additional Aux power is permitted to be allocated using the firmware based mechanism (see the Request D3 ${ }_{\text {Cold }}$ Aux Power Limit _DSM call as defined in [Firmware]). Additional Aux power is also permitted to be allocated by selecting a PM Sub State in the Power Limit mechanism (see § Section 7.8.1.3). |  |
|  | D1_Support - If this bit is Set, this Function supports the D1 Power Management State. <br> Functions that do not support D1 must always return a value of 0 b for this bit. | RO |
| 26 | D2_Support - If this bit is Set, this Function supports the D2 Power Management State. <br> Functions that do not support D2 must always return a value of 0 b for this bit. | RO |
| $31: 27$ | PME_Support - This 5-bit field indicates the power states in which the Function may generate a PME and/or forward PME Messages. <br> A value of 0 b for any bit indicates that the Function is not capable of asserting PME while in that power state. <br> bit(27) X XXX1b PME can be generated from D0 <br> bit(28) X XX1Xb PME can be generated from D1 <br> bit(29) X X1XXb PME can be generated from D2 <br> bit(30) X 1XXXb PME can be generated from D3 ${ }_{\text {Hot }}$ <br> bit(31) 1 XXXXb PME can be generated from D3 ${ }_{\text {Cold }}$ <br> Bit 31 (PME can be asserted from D3 ${ }_{\text {Cold }}$ ) represents a special case. Functions that Set this bit require some sort of auxiliary power source. Implementation specific mechanisms are recommended to validate that the power source is available before setting this bit. <br> Each bit that corresponds to a supported D-state must be Set for PCI-PCI Bridge structures representing Ports on Root Complexes/Switches to indicate that the Bridge will forward PME Messages. Bit 31 must only be Set if the Port is still able to forward PME Messages when main power is not available. | RO |

[^0]
[^0]:    169. Earlier versions of this specification defined power levels as current (mA) at 3.3 V (hence the field name "Aux_Current"). To support form factors with different Aux Power voltage levels, the definition was changed to the equivalent wattage values (mW).

# 7.5.2.2 Power Management Control/Status Register (Offset 04h) 

This register is used to manage the PCI Function's power management state as well as to enable/monitor PMEs.
The PME Context includes the value of the PME_Status and PME_En bits, implementation specific state needed during D3 ${ }_{\text {cold }}$ to implement the wakeup functionality (e.g., recognized a Wake on LAN packet and generate a PME Message), as well as any additional implementation specific state that must be preserved during a transition to the DO unnititalized state.

If a Function supports PME generation from D3 ${ }_{\text {cold }}$, its PME Context is not affected by Reset. This is because the Function's PME functionality itself may have been responsible for the wake event which caused the transition back to D0. Therefore, the PME Context must be preserved for the system software to process.

If PME generation is not supported from D3 ${ }_{\text {cold }}$, then all PME Context is initialized with the assertion of Reset.
§ Figure 7-19 details allocation of the register fields for the Power Management Control/Status Register and § Table 7-15 describes the requirements for this register.
![img-17.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-17.jpeg)

Figure 7-19 Power Management Control/Status Register

Table 7-15 Power Management Control/Status Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $1: 0$ | PowerState - This 2-bit field is used both to determine the current power state of a Function and to set the Function into a new power state. The definition of the field values is given below. | RW |
|  | 00b | D0 |
|  | 01b | D1 |
|  | 10b | D2 |
|  | 11b | $\mathrm{D3}_{\text {Hot }}$ |
|  | If software attempts to write an unsupported, optional state to this field, the write operation must complete normally; however, the data is discarded and no state change occurs. |  |
|  | Default value of this field is 00 b . |  |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 3 | No_Soft_Reset - This bit indicates the state of the Function after writing the PowerState field to transition the Function from $\mathrm{D} 3_{\text {Hot }}$ to DO. This bit MUST@FLIT be Set. <br> When Set, this transition preserves internal Function state. The Function is in DO Active and no additional software intervention is required. <br> When Clear, this transition results in undefined internal Function state. <br> Regardless of this bit, Functions that transition from $\mathrm{D} 3_{\text {Hot }}$ to DO by Fundamental Reset must return to DO uninitialized with only PME context preserved if PME is supported and enabled. <br> If a VF implements the PCI Power Management Capability, the VF's value of this field must be identical to the associated PF's value. | RO |
| 8 | PME_En - When Set, the Function is permitted to generate a PME. When Clear, the Function is not permitted to generate a PME. <br> If PME_Support is 1 xxxxb (PME generation from D3 ${ }_{\text {Cold }}$ ) or the Function consumes auxiliary power and auxiliary power is available this bit is RWS and the bit is not modified by Conventional Reset or FLR <br> If PME_Support is 0 xxxxb, this field is not sticky (RW) and defaults to Ob in response to a Conventional Reset or an FLR. <br> If PME_Support is 00000 b, this bit is permitted to be hardwired to Ob. | RW/RWS |
| 12:9 | Data_Select - This 4-bit field is used to select which data is to be reported through the Power Management Data Register and Data_Scale field. <br> If the Power Management Data Register is not implemented, this field must be hardwired to Zero. <br> Refer to $\S$ Section 7.5.2.3 for more details. <br> The default of this field is Zero. | RW <br> VF ROZ |
| 14:13 | Data_Scale - This field indicates the scaling factor to be used when interpreting the value of the Data register. The value and meaning of this field will vary depending on which data value has been selected by the Data_Select field. <br> This field is a required component of the Power Management Data Register (offset 7) and must be implemented if the Power Management Data Register is implemented. <br> If the Power Management Data Register is not implemented, this field must be hardwired to Zero. <br> Refer to $\S$ Section 7.5.2.3 for more details. | RO <br> VF ROZ |
| 15 | PME_Status - This bit is Set when the Function would normally generate a PME signal. The value of this bit is not affected by the value of the PME_En bit. <br> If PME_Support bit 31 of the Power Management Capabilities Register is Clear, this bit is permitted to be hardwired to Ob. <br> Functions that consume auxiliary power must preserve the value of this sticky register when auxiliary power is available. In such Functions, this register value is not modified by Conventional Reset or FLR. | RW1CS |
| 23:22 | Undefined Undefined - these bits were defined in previous specifications. They should be ignored by software. | RO |

# 7.5.2.3 Power Management Data Register (Offset 07h) 

The Power Management Data Register is an optional, 8-bit read-only register that provides a mechanism for the Function to report state dependent operating power consumed or dissipation.

If the Power Management Data Register is implemented, then the Data_Select and Data_Scale fields must also be implemented. If this register is not implemented, it must be hardwired to 00h.

Software may check for the presence of the Power Management Data Register by writing different values into the Data_Select field, looking for non-zero return data in the Power Management Data Register and/or Data_Scale field. Any non-zero Power Management Data Register/Data_Select read data indicates that the Power Management Data Register complex has been implemented.
![img-18.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-18.jpeg)

Figure 7-20 Power Management Data Register

Table 7-16 Power Management Data Register 5

| Bit Location | Register Description |  | Attributes |
| :--: | :--: | :--: | :--: |
| $7: 0$ | Data - This register is used to report the state dependent data requested by the Data_Select field. The value of this register is scaled by the value reported by the Data_Scale field. <br> For VFs, this register is not supported and must be hardwired to Zero. |  | RO <br> VF ROZ |

The Power Management Data Register is used by writing the proper value to the Data_Select field in the PMCSR and then reading the Data_Scale field and the Power Management Data Register. The binary value read from Data is then multiplied by the scaling factor indicated by Data_Scale to arrive at the value for the desired measurement. § Table 7-17 shows which measurements are defined and how to interpret the values of each register.

Table 7-17 Power Consumption/Dissipation Reporting 6

| Value in <br> Data_Select | Data Reported | Data_Scale <br> Interpretation | Units/ <br> Accuracy |
| :--: | :--: | :--: | :--: |
| 0 | D0 Power Consumed | $0=$ Unknown <br> $1=0.1 x$ <br> $2=0.01 x$ <br> $3=0.001 x$ | Watts |
| 1 | D1 Power Consumed |  |  |
| 2 | D2 Power Consumed |  |  |
| 3 | D3 Power Consumed |  |  |
| 4 | D0 Power Dissipated |  |  |
| 5 | D1 Power Dissipated |  |  |
| 6 | D2 Power Dissipated |  |  |
| 7 | D3 Power Dissipated |  |  |
| 8 | Common logic power consumption (Multi-Function Devices, Function 0 only) <br> Function 0 of a Multi-Function Device: <br> Power consumption that is not associated with a specific Function. |  |  |

| Value in <br> Data_Select | Data Reported | Data_Scale <br> Interpretation | Units/ <br> Accuracy |
| :--: | :--: | :--: | :--: |
| All other Functions: <br> Reserved |  |  |  |
| 9-15 | Reserved | Reserved | TBD |

The "Power Consumed" values defined above must include all power consumed from the power planes through the connector pins. If the add-in card provides power to external devices, that power must be included as well. It must not include any power derived from a battery or an external source. This information is useful for management of the power supply or battery.

The "Power Dissipated" values must provide the amount of heat which will be released into the interior of the computer chassis. This excludes any power delivered to external devices but must include any power derived from a battery or external power source and dissipated inside the computer chassis. This information is useful for fine grained thermal management.

Multi-Function Devices are recommended to report the power consumed by each Function in each corresponding Function's Configuration Space. In a Multi-Function Device, power consumption for circuitry common to multiple Functions is reported in Function 0's Configuration Space through the Power Management Data Register once the Data_Select field of Function 0's Power Management Control/Status Register has been programmed to 1000b. For a Multi-Function Device, power consumption of the device is the sum of this value and, for every Function of the device, the reported value associated with the Function's current Power State.

Multiple component add-in cards implementing power reporting (i.e., multiple components behind a switch or bridge) must have the switch/bridge report the power it uses by itself. Each Function of each component on the add-in card is responsible for reporting the power consumed by that Function.

# IMPLEMENTATION NOTE: 

NEW DESIGNS SHOULD USE POWER BUDGETING EXTENDED CAPABILITY

Both the Power Budgeting Extended Capability and the PCI Power Management Capability report power consumption. The Power Budgeting Extended Capability mechanism is required in some situations (by this specification or the associated form factor specification). The Power Budgeting Extended Capability mechanism provides additional information beyond that which is provided by the Data register of the PCI Power Management Capability. It is strongly recommended that designs implement the Power Budgeting Extended Capability instead of the mechanism in this section, and that new designs hardwire the Data, Data_Select, and Data_Scale fields to 0.

### 7.5.3 PCI Express Capability Structure

PCI Express defines a Capability structure in PCI-compatible Configuration Space (first 256 bytes) as shown in § Figure 7-3. This structure allows identification of a PCI Express device Function and indicates support for new PCI Express features. The PCI Express Capability structure is required for PCI Express device Functions. The Capability structure is a mechanism for enabling PCI software transparent features requiring support on legacy operating systems. In addition to identifying a PCI Express device Function, the PCI Express Capability structure is used to provide access to PCI Express specific Control/Status registers and related Power Management enhancements.
§ Figure 7-21 details allocation of register fields in the PCI Express Capability structure.

The PCI Express Capabilities, Device Capabilities, Device Status, and Device Control registers are required for all PCI Express device Functions. Device Capabilities 2, Device Status 2, and Device Control 2 registers are required for all PCI Express device Functions that implement capabilities requiring those registers. For device Functions that do not implement the Device Capabilities 2, Device Status 2, and Device Control 2 registers, these spaces must be hardwired to 0b.

The Link Capabilities, Link Status, and Link Control registers are required for all Root Ports, Switch Ports, Bridges, and Endpoints that are not RCIEPs. For Functions that do not implement the Link Capabilities, Link Status, and Link Control registers, these spaces must be hardwired to 0 . Link Capabilities 2, Link Status 2, and Link Control 2 registers are required for all Root Ports, Switch Ports, Bridges, and Endpoints (except for RCIEPs) that implement capabilities requiring those registers. For Functions that do not implement the Link Capabilities 2, Link Status 2, and Link Control 2 registers, these spaces must be hardwired to 0b.

The Slot Capabilities, Slot Status, and Slot Control registers are required in certain Switch Downstream and Root Ports. The Slot Capabilities Register is required if the Slot Implemented bit is Set (see § Section 7.5.3.2). The Slot Status and Slot Control registers are required if Slot Implemented is Set or if Data Link Layer Link Active Reporting Capable is Set (see § Section 7.5.3.6). Switch Downstream and Root Ports are permitted to implement these registers, even when they are not required, and in this case the behavior of most of the fields in these registers is undefined. See § Section 7.5.3.9, § Section 7.5.3.10, and § Section 7.5.3.11 for details. For Functions that do not implement the Slot Capabilities, Slot Status, and Slot Control registers, these spaces must be hardwired to 0b, with the exception of the Presence Detect State bit in the Slot Status Register of Downstream Ports, which must be hardwired to 1b (see § Section 7.5.3.11). Slot Capabilities 2, Slot Status 2, and Slot Control 2 registers are required for Switch Downstream and Root Ports if the Function implements capabilities requiring those registers. For Functions that do not implement the Slot Capabilities 2, Slot Status 2, and Slot Control 2 registers, these spaces must be hardwired to 0b.

Root Ports and Root Complex Event Collectors must implement the Root Capabilities, Root Status, and Root Control registers. For Functions that do not implement the Root Capabilities, Root Status, and Root Control registers, these spaces must be hardwired to 0b.
![img-19.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-19.jpeg)

Figure 7-21 PCI Express Capability Structure

# 7.5.3.1 PCI Express Capability List Register (Offset 00h) 

The PCI Express Capability List Register enumerates the PCI Express Capability structure in the PCI Configuration Space Capability list. § Figure 7-22 details allocation of register fields in the PCI Express Capability List Register; § Table 7-18 provides the respective bit definitions.

![img-20.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-20.jpeg)

Figure 7-22 PCI Express Capability List Register

Table 7-18 PCI Express Capability List Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| $7: 0$ | Capability ID - Indicates the PCI Express Capability structure. This field must return a Capability ID of <br> 10h indicating that this is a PCI Express Capability structure. | RO |
| $15: 8$ | Next Capability Pointer - This field contains the offset to the next PCI Capability structure or 00h if no <br> other items exist in the linked list of Capabilities. | RO |

# 7.5.3.2 PCI Express Capabilities Register (Offset 02h) 

The PCI Express Capabilities Register identifies PCI Express device Function type and associated capabilities. § Figure 7-23 details allocation of register fields in the PCI Express Capabilities Register; § Table 7-19 provides the respective bit definitions.
![img-21.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-21.jpeg)

Figure 7-23 PCI Express Capabilities Register

Table 7-19 PCI Express Capabilities Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| $3: 0$ | Capability Version - Indicates PCI-SIG defined PCI Express Capability structure version number. | RO |
|  | A version of the specification that changes the PCI Express Capability structure in a way that is not <br> otherwise identifiable (e.g., through a new Capability field) is permitted to increment this field. All such |  |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | changes to the PCI Express Capability structure must be software-compatible. Software must check for Capability Version numbers that are greater than or equal to the highest number defined when the software is written, as Functions reporting any such Capability Version numbers will contain a PCI Express Capability structure that is compatible with that piece of software. <br> Must be hardwired to 2 h for Functions compliant to this specification. |  |
| $7: 4$ | Device/Port Type ${ }^{170}$ - Indicates the specific type of this PCI Express Function. Note that different Functions in a Multi-Function Device can generally be of different types. <br> Defined encodings for Functions that implement a Type 00h PCI Configuration Space header are: | RO |
|  | 0000b PCI Express Endpoint |  |
|  | 0001b Legacy PCI Express Endpoint |  |
|  | 1001b RCiEP |  |
|  | 1010b Root Complex Event Collector |  |
|  | Defined encodings for Functions that implement a Type 01h PCI Configuration Space header are: |  |
|  | 0100b Root Port of PCI Express Root Complex |  |
|  | 0101b Upstream Port of PCI Express Switch |  |
|  | 0110b Downstream Port of PCI Express Switch |  |
|  | 0111b PCI Express to PCI/PCI-X Bridge |  |
|  | 1000b PCI/PCI-X to PCI Express Bridge |  |
|  | All other encodings are Reserved. |  |
|  | Note that the different Endpoint types have notably different requirements in § Section 1.3.2 regarding I/O resources, Extended Configuration Space, and other capabilities. |  |
| 8 | Slot Implemented - When Set, this bit indicates that the Link associated with this Port is connected to a slot (as compared to being connected to a system-integrated device or being disabled). <br> This bit is valid for Downstream Ports. This bit is undefined for Upstream Ports. | HwInit |
| 13:9 | Interrupt Message Number - When MSI/MSI-X is implemented, this field indicates which MSI/MSI-X vector is used for the interrupt message generated in association with any of the status bits of this Capability structure. This vector is also used for: <br> - Native PME Software Model (see § Section 6.1.6 and § Section 6.7.3.4) <br> - Link Activation (see § Section 5.5.6) <br> - Flit Error Counter Interrupts (see § Section 7.7.8.4) | RO |
|  | For MSI, the value in this field indicates the offset between the base Message Data and the interrupt message that is generated. Hardware is required to update this field so that it is correct if the number of MSI Messages assigned to the Function changes when software writes to the Multiple Message Enable field in the Message Control Register for MSI. <br> For MSI-X, the value in this field indicates which MSI-X Table entry is used to generate the interrupt message. The entry must be one of the first 32 entries even if the Function implements more than 32 entries. For a given MSI-X implementation, the entry must remain constant. <br> If both MSI and MSI-X are implemented, they are permitted to use different vectors, though software is permitted to enable only one mechanism at a time. If MSI-X is enabled, the value in this field must indicate the vector for MSI-X. If MSI is enabled or neither is enabled, the value in this field must indicate the vector for MSI. If software enables both MSI and MSI-X at the same time, the value in this field is undefined. |  |

[^0]
[^0]:    170. This field would be better named 'Function Type' but for historical reasons is named Device/Port Type.

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 14 | Undefined - The value read from this bit is undefined. In previous versions of this specification, this bit <br> was used to indicate support for TCS Routing. System software should ignore the value read from this <br> bit. System software is permitted to write any value to this bit. | RO |
| 15 | Flit Mode Supported - When Set, indicates support for Flit Mode. Must be Set by all implementations <br> that support Flit Mode. Must be Clear by implementations that do not support Flit Mode. See Flit Mode <br> Supported. | HwInit |

# 7.5.3.3 Device Capabilities Register (Offset 04h) 

The Device Capabilities Register identifies PCI Express device Function specific capabilities. § Figure 7-24 details allocation of register fields in the Device Capabilities Register; § Table 7-20 provides the respective bit definitions.
![img-22.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-22.jpeg)

Figure 7-24 Device Capabilities Register

Table 7-20 Device Capabilities Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 2:0 | Max_Payload_Size Supported - This field indicates the maximum payload size that the Function can <br> support for TLPs. This field MUST@FLIT indicate a minimum of 512 bytes. | RO |
|  | If the Rx_MPS_Fixed bit is Set, the Function's Rx_MPS_Limit is fixed with the value indicated by this <br> (Max_Payload_Size Supported) field. Otherwise, the Rx_MPS_Limit is determined by the <br> Max_Payload_Size field (the "MPS setting") in one or more Functions. See § Section 2.2.2 for important <br> details regarding Multi-Function Devices. |  |
|  | Defined encodings are: |  |
|  | 000b | 128 bytes max payload size |
|  | 001b | 256 bytes max payload size |
|  | 010b | 512 bytes max payload size |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | 011b 1024 bytes max payload size |  |
|  | 100b 2048 bytes max payload size |  |
|  | 101b 4096 bytes max payload size |  |
|  | 110b | Reserved |
|  | 111b | Reserved |
|  | The Functions of a Multi-Function Device are permitted to report different values for this field. |  |
| $4: 3$ | Phantom Functions Supported - This field indicates the support for use of unclaimed Function Numbers to extend the number of outstanding transactions allowed by logically combining unclaimed Function Numbers (called Phantom Functions) with the Tag identifier (see § Section 2.2.6.2 for a description of Tag Extensions). | RO <br> VF ROZ |
|  | For a PF with its VF Enable bit Set, the use of Phantom Function numbers is not permitted and this field must return Zero when read. |  |
|  | For VFs, this field is not supported and must be hardwired to Zero. |  |
|  | For every Function in an ARI Device, this field must be hardwired to Zero. |  |
|  | The remainder of this field description applies only to non-ARI Multi-Function Devices. |  |
|  | This field indicates the number of most significant bits of the Function Number portion of Requester ID that are logically combined with the Tag identifier. |  |
|  | Defined encodings are: |  |
|  | 00b No Function Number bits are used for Phantom Functions. Multi-Function Devices are permitted to implement up to 8 independent Functions. |  |
|  | 01b The most significant bit of the Function number in Requester ID is used for Phantom Functions; a Multi-Function Device is permitted to implement Functions 0-3. Functions 0, 1,2 , and 3 are permitted to use Function Numbers $4,5,6$, and 7 respectively as Phantom Functions. |  |
|  | 10b The two most significant bits of Function Number in Requester ID are used for Phantom Functions; a Multi-Function Device is permitted to implement Functions 0-1. Function 0 is permitted to use Function Numbers 2, 4, and 6 for Phantom Functions. Function 1 is permitted to use Function Numbers 3, 5, and 7 as Phantom Functions. |  |
|  | 11b All 3 bits of Function Number in Requester ID used for Phantom Functions. The device must have a single Function 0 that is permitted to use all other Function Numbers as Phantom Functions. |  |
|  | Note that Phantom Function support for the Function must be enabled by the Phantom Functions Enable field in the Device Control Register before the Function is permitted to use the Function Number field in the Requester ID for Phantom Functions. |  |
| 5 | Extended Tag Field Supported - This bit, in combination with the 10-Bit Tag Requester Supported bit and the 14-Bit Tag Requester Supported bit, indicates the maximum supported size of the Tag field as a Requester. This bit must be Set if the 10-Bit Tag Requester Supported bit or the 14-Bit Tag Requester Supported bit is Set. | RO |
|  | Defined encodings are: |  |
|  | 0b 5-bit Tag Requester capability supported |  |
|  | 1b 8-bit Tag Requester capability supported |  |
|  | Note that 8-bit Tag field generation must be enabled by the Extended Tag Field Enable bit in the Device Control Register of the Requester Function before 8-bit Tags can be generated by the Requester. See § Section 2.2.6.2 for interactions with enabling the use of 10-Bit or 14-Bit Tags. |  |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 8:6 | Endpoint L0s Acceptable Latency - This field indicates the acceptable total latency that an Endpoint can withstand due to the transition from L0s state to the L0 state. It is essentially an indirect measure of the Endpoint's internal buffering. <br> Power management software uses the reported L0s Acceptable Latency number to compare against the L0s exit latencies reported by all components comprising the data path from this Endpoint to the Root Complex Root Port to determine whether ASPM L0s entry can be used with no loss of performance. <br> Defined encodings are: | RO |
|  | 000b | Maximum of 64 ns |
|  | 001b | Maximum of 128 ns |
|  | 010b | Maximum of 256 ns |
|  | 011b | Maximum of 512 ns |
|  | 100b | Maximum of $1 \mu \mathrm{~s}$ |
|  | 101b | Maximum of $2 \mu \mathrm{~s}$ |
|  | 110b | Maximum of $4 \mu \mathrm{~s}$ |
|  | 111b | No limit |
|  | For Functions other than Endpoints, this field is Reserved and must be hardwired to 000b. |  |
| 11:9 | Endpoint L1 Acceptable Latency - This field indicates the acceptable latency that an Endpoint can withstand due to the transition from L1 state to the L0 state. It is essentially an indirect measure of the Endpoint's internal buffering. <br> Power management software uses the reported L1 Acceptable Latency number to compare against the L1 Exit Latencies reported (see below) by all components comprising the data path from this Endpoint to the Root Complex Root Port to determine whether ASPM L1 entry can be used with no loss of performance. <br> Defined encodings are: | RO |
|  | 000b | Maximum of $1 \mu \mathrm{~s}$ |
|  | 001b | Maximum of $2 \mu \mathrm{~s}$ |
|  | 010b | Maximum of $4 \mu \mathrm{~s}$ |
|  | 011b | Maximum of $8 \mu \mathrm{~s}$ |
|  | 100b | Maximum of $16 \mu \mathrm{~s}$ |
|  | 101b | Maximum of $32 \mu \mathrm{~s}$ |
|  | 110b | Maximum of $64 \mu \mathrm{~s}$ |
|  | 111b | No limit |
|  | For Functions other than Endpoints, this field is Reserved and must be hardwired to 000b. |  |
| 14:12 | Undefined - The value read from these bits are undefined. In previous versions of this specification, this bit was used to indicate that a Attention Button, Attention Indicator, or Power Indicator, is implemented on the adapter and electrically controlled by the component on the adapter. System software must ignore the value read from this bit. System software is permitted to write any value to this bit. | RO |
| 15 | Role-Based Error Reporting - When Set, this bit indicates that the Function implements Role-Based Error Reporting. This bit must be Set by all Functions conforming to [PCIe-1.1] or later revisions. | RO |
| 16 | ERR_COR Subclass Capable - When Set, this bit indicates that the Function supports the ERR_COR Subclass field in ERR_COR Messages, allowing different subclasses to be distinguished. See § Section 2.2.8.3. | RO |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | Downstream Ports that implement the System Firmware Intermediary (SFI) capability must Set this bit. Downstream Ports that implement Downstream Port Containment (DPC) are strongly encouraged to Set this bit. |  |
| 17 | Rx_MPS_Fixed - When Set, the Function's Rx_MPS_Limit is fixed with the value indicated by the Max_Payload_Size Supported field. Otherwise, the Rx_MPS_Limit is determined by the Max_Payload_Size field (the "MPS setting") in one or more Functions. See § Section 2.2.2 for important details regarding Multi-Function Devices. This bit MUST@FLIT be Set. | HwInit |
| 25:18 | Captured Slot Power Limit Value (Upstream Ports only) - In combination with the Captured Slot Power Limit Scale value, specifies the upper limit on power available to the adapter. <br> Power limit (in Watts) is calculated by multiplying the value in this field by the value in the Captured Slot Power Limit Scale field except when the Captured Slot Power Limit Scale field equals 00b (1.0x) and the Captured Slot Power Limit Value exceeds EFh, then alternative encodings are used (see § Section 7.5.3.9). <br> This value is set by the Set_Slot_Power_Limit Message or hardwired to 00h (see § Section 6.9). The default value is 00 h . <br> For VFs, the field value when read is undefined. | RO |
| 27:26 | Captured Slot Power Limit Scale (Upstream Ports only) - Specifies the scale used for the Slot Power Limit Value. <br> Range of Values: | RO |
|  | 00b 1.0x <br> 01b 0.1x <br> 10b 0.01x <br> 11b 0.001x <br> This value is set by the Set_Slot_Power_Limit Message or hardwired to 00b (see § Section 6.9). The default value is 00 b . <br> For VFs, the field value when read is undefined. | RO |
| 28 | Function Level Reset Capability - A value of 1 b indicates the Function supports the optional Function Level Reset mechanism described in § Section 6.6.2 . <br> This bit applies to Endpoints only. For all other Function types this bit must be hardwired to Zero. For PFs and VFs, the feature is mandatory and this bit must be Set. | RO |
| 29 | Mixed_MPS_Supported - When Set, the Function must have an implementation specific mechanism capable of supporting different MPS settings for different targets. This bit MUST@FLIT be Set if the Function supports P2P Memory Transactions and the Function's Max_Payload_Size Supported field indicates an MPS value greater than 512 bytes. If not mandatory, supporting Mixed MPS capability may still be beneficial if this Function does P2P with targets or over paths whose supported MPS is significantly less than this Function's supported MPS; e.g., 128 bytes vs. 512 bytes. <br> The implementation specific mechanism must handle both Request and Completion TLPs, and is permitted to base its determination of P2P targets on Memory Space ranges, Bus Number ranges, or implementation specific means; e.g., data mover channels. <br> For SR-IOV devices, this field in each VF must have the same value its associated PF. If this field is Set, the implementation specific mechanism must use the same P2P target-specific MPS setting for each VF as its associated PF. This parallels the requirement for the Max_Payload_Size field in the Device Control Register. | HwInit |
| 30 | TEE-IO Supported - When Set, this bit indicates that the Function implements the TEE-IO functionality as described by the TEE Device Interface Security Protocol (TDISP). See § Chapter 11. . | HwInit |

# 7.5.3.4 Device Control Register (Offset 08h) 

The Device Control Register controls PCI Express device specific parameters. \$ Figure 7-25 details allocation of register fields in the Device Control Register; \$ Table 7-21 provides the respective bit definitions.

For VF fields indicated as RsvdP, the PF setting applies to the VF.
![img-23.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-23.jpeg)

Figure 7-25 Device Control Register

Table 7-21 Device Control Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 0 | Correctable Error Reporting Enable - This bit, in conjunction with other bits, controls sending ERR_COR Messages (see \$ Section 6.2.5, \$ Section 6.2.6, and \$ Section 6.2.11.2 for details). For a Multi-Function Device, this bit controls error reporting for each Function from point-of-view of the respective Function. <br> For a Root Port, the reporting of correctable errors is internal to the root. No external ERR_COR Message is generated. <br> An RCIEP that is not associated with a Root Complex Event Collector is permitted to hardwire this bit to 0b. <br> Default value of this bit is 0 b. | RW <br> VF RsvdP |
| 1 | Non-Fatal Error Reporting Enable - This bit, in conjunction with other bits, controls sending ERR_NONFATAL Messages (see \$ Section 6.2.5 and \$ Section 6.2.6 for details). For a Multi-Function Device, this bit controls error reporting for each Function from point-of-view of the respective Function. <br> For a Root Port, the reporting of Non-fatal errors is internal to the root. No external ERR_NONFATAL Message is generated. <br> An RCIEP that is not associated with a Root Complex Event Collector is permitted to hardwire this bit to 0 b. <br> Default value of this bit is 0 b. | RW <br> VF RsvdP |
| 2 | Fatal Error Reporting Enable - This bit, in conjunction with other bits, controls sending ERR_FATAL Messages (see \$ Section 6.2.5 and \$ Section 6.2.6 for details). For a Multi-Function Device, this bit controls error reporting for each Function from point-of-view of the respective Function. | RW <br> VF RsvdP |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | For a Root Port, the reporting of Fatal errors is internal to the root. No external ERR_FATAL Message is generated. <br> An RCiEP that is not associated with a Root Complex Event Collector is permitted to hardwire this bit to 0b. <br> Default value of this bit is 0 b . |  |
| 3 | Unsupported Request Reporting Enable - This bit, in conjunction with other bits, controls the signaling of Unsupported Request Errors by sending error Messages (see § Section 6.2.5 and § Section 6.2.6 for details). For a Multi-Function Device, this bit controls error reporting for each Function from point-of-view of the respective Function. <br> An RCiEP that is not associated with a Root Complex Event Collector is permitted to hardwire this bit to 0b. <br> Default value of this bit is 0 b . | RW <br> VF RsvdP |
| 4 | Enable Relaxed Ordering - If this bit is Set, the Function is permitted to set the Relaxed Ordering bit in the Attributes field of transactions it initiates that do not require strong write ordering (see § Section 2.2.6.4 and § Section 2.4). <br> A Function is permitted to hardwire this bit to 0 b if it never sets the Relaxed Ordering attribute in transactions it initiates as a Requester. <br> When not hardwired to 0 b , the default value of this bit is 1 b . | RW <br> VF RsvdP |
| 7:5 | Max_Payload_Size - For specified cases, this field determines the maximum TLP payload size (the MPS setting) for the Function. Values permitted to be programmed are indicated by the Max_Payload_Size Supported field. <br> As a Receiver, if the Rx_MPS_Fixed bit is Set, the Rx_MPS_Limit is fixed with the value indicated by the Max_Payload_Size Supported field. Otherwise, the Rx_MPS_Limit is determined by the MPS setting in one or more Functions. See § Section 2.2.2 for important details regarding Multi-Function Devices. <br> As a Transmitter, the Function must not generate TLPs with payloads exceeding the MPS setting, with the exception of Functions in a Multi-Function Device, or Functions with implemention-specific mechanisms capable of supporting different MPS settings for different targets. See § Section 2.2.2 for important details. <br> Defined encodings for this field are: | RW <br> VF RsvdP |
|  | 000b 128 bytes MPS <br> 001b 256 bytes MPS <br> 010b 512 bytes MPS <br> 011b 1024 bytes MPS <br> 100b 2048 bytes MPS <br> 101b 4096 bytes MPS <br> 110b Reserved <br> 111b Reserved <br> Functions that support only the 128-byte MPS are permitted to hardwire this field to 000 b . <br> System software is not required to program the same value for this field for all the Functions of a Multi-Function Device. <br> Default value of this field is 000 b . | RW <br> VF RsvdP |
| 8 | Extended Tag Field Enable - This bit, in combination with the 10-Bit Tag Requester Enable bit and the 14-Bit Tag Requester Enable bit, determines how many Tag field bits a Requester is permitted to use for non-UIO Requests. | RW <br> VF RsvdP |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | The following applies when the 10-Bit Tag Requester Enable bit and the 14-Bit Tag Requester Enable bit are both Clear. If the Extended Tag Field Enable bit is Set, the Function is permitted to use an 8-bit Tag field as a Requester. If the bit is Clear, the Function is restricted to using a 5-bit Tag field. <br> See § Section 2.2.6.2 for required behavior when one or both of these larger-Tag Requester Enable bits are Set. <br> If software changes the value of the Extended Tag Field Enable bit while the Function has outstanding Non-Posted Requests, the result is undefined. <br> Functions that do not implement this capability hardwire this bit to 0b. <br> Default value of this bit is implementation specific. |  |
| 9 | Phantom Functions Enable - This bit, in combination with the 10-Bit Tag Requester Enable bit and the 14-Bit Tag Requester Enable bit, determines how many outstanding Non-Posted Requests a Requester is permitted to generate. See § Section 2.2.6.2 for complete details. <br> When Set, this bit enables a Function to use unclaimed Functions as Phantom Functions to extend the number of outstanding transaction identifiers. If the bit is Clear, the Function is not allowed to use Phantom Functions. <br> Behavior is undefined when this bit is Set in Functions with enabled Shadow Functions. <br> Software should not change the value of this bit while the Function has outstanding Non-Posted Requests; otherwise, the result is undefined. <br> Functions that do not implement this capability hardwire this bit to 0b. <br> Default value of this bit is 0 b . | RW <br> VF RsvdP |
| 10 | Aux Power PM Enable - When Set this bit, enables a Function to draw auxiliary power independent of PME Aux power. Functions that require auxiliary power on legacy operating systems should continue to indicate PME Aux power requirements. Auxiliary power is allocated as requested in the Aux_Current field of the Power Management Capabilities Register (PMC), independent of the PME_En bit in the Power Management Control/Status Register (PMCSR) (see § Chapter 5.). For Multi-Function Devices, a component is allowed to draw auxiliary power if at least one of the Functions has this bit set. <br> Note: Functions that consume auxiliary power must preserve the value of this sticky register when auxiliary power is available. In such Functions, this bit is not modified by Conventional Reset. <br> Functions that do not implement this capability hardwire this bit to 0b. <br> Additional Aux power is permitted to be allocated using the firmware based mechanism (see the Request D3 ${ }_{\text {Cold }}$ Aux Power Limit_DSM call as defined in [Firmware]). <br> Additional Aux power is also permitted to be allocated by selecting a PM Sub State in the Power Limit mechanism (see § Section 7.8.1.3). | RWS <br> VF RsvdP |
| 11 | Enable No Snoop - If this bit is Set, the Function is permitted to Set the No Snoop bit in the Requester Attributes of transactions it initiates that do not require hardware enforced cache coherency (see § Section 2.2.6.5). Note that setting this bit to 1 b should not cause a Function to Set the No Snoop attribute on all transactions that it initiates. Even when this bit is Set, a Function is only permitted to Set the No Snoop attribute on a transaction when it can guarantee that the address of the transaction is not stored in any cache in the system. <br> This bit is permitted to be hardwired to 0 b if a Function would never Set the No Snoop attribute in transactions it initiates. <br> Default value of this bit is 1 b . | RW <br> VF RsvdP |
| 14:12 | Max_Read_Request_Size - This field sets the maximum Read Request size for the Function as a Requester. The Function must not generate Read Requests with a size exceeding the set value. Defined encodings for this field are: | RW <br> VF RsvdP |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | 000b 001b 010b 011b 100b 101b 110b 111b 110b 111b 111b 111b Default value of this field is 010b. | 128 bytes maximum Read Request size 256 bytes maximum Read Request size 512 bytes maximum Read Request size 1024 bytes maximum Read Request size 2048 bytes maximum Read Request size 4096 bytes maximum Read Request size Reserved Reserved  |
|  | Functions that do not generate Read Requests larger than 128 bytes and Functions that do not generate Read Requests on their own behalf are permitted to implement this field as Read Only (RO) with a value of 000 b . <br> Default value of this field is 010 b . |  |
| 15 | Bridge Configuration Retry Enable / Initiate Function Level Reset - this bit has a different meaning based on Function type: <br> - PCI Express to PCI/PCI-X Bridges: <br> Bridge Configuration Retry Enable - When Set, this bit enables PCI Express to PCI/PCI-X bridges to return Request Retry Status (RRS) in response to Configuration Requests that target devices below the bridge. Refer to [PCle-to-PCI-PCI-X-Bridge] for further details. <br> Default value of this bit is 0 b . <br> - Endpoints with Function Level Reset Capability set to 1b: <br> Initiate Function Level Reset - A write of 1b initiates Function Level Reset to the Function. The value read by software from this bit is always 0 b . <br> PFs and VFs must support FLR. Note: performing FLR on a PF Clears its VF Enable bit, which causes its VFs no longer to exist after the FLR completes. <br> - All others: <br> Reserved - Must hardwire the bit to 0b. | PCI <br> Express to <br> PCI/PCI-X <br> Bridges: <br> RW <br> FLR <br> Capable <br> Endpoints: <br> RW <br> All others: <br> RsvdP |

# IMPLEMENTATION NOTE: 

## SOFTWARE UR REPORTING COMPATIBILITY WITH 1.0A DEVICES

With [PCIe-1.0a] device Functions, ${ }^{171}$ if the Unsupported Request Reporting Enable bit is Set, the Function when operating as a Completer will send an uncorrectable error Message (if enabled) when a UR error is detected. On platforms where an uncorrectable error Message is handled as a System Error, this will break PC-compatible Configuration Space probing, so software/firmware on such platforms may need to avoid setting the Unsupported Request Reporting Enable bit.

With device Functions implementing Role-Based Error Reporting, setting the Unsupported Request Reporting Enable bit will not interfere with PC-compatible Configuration Space probing, assuming that the severity for UR is left at its default of non-fatal. However, setting the Unsupported Request Reporting Enable bit will enable the Function to report UR errors ${ }^{172}$ detected with posted Requests, helping avoid this case for potential silent data corruption.

On platforms where robust error handling and PC-compatible Configuration Space probing is required, it is suggested that software or firmware have the Unsupported Request Reporting Enable bit Set for Role-Based Error Reporting Functions, but clear for [PCIe-1.0a] Functions. Software or firmware can distinguish the two classes of Functions by examining the Role-Based Error Reporting bit in the Device Capabilities Register.

[^0]
[^0]:    171. In this context, [PCIe-1.0a] devices Functions are devices that do not implement Role-Based Error Reporting.
    172. With Role-Based Error Reporting devices, setting the SERR\# Enable bit in the Command Register also implicitly enables UR reporting.

# IMPLEMENTATION NOTE: USE OF MAX_PAYLOAD_SIZE 

The Max_Payload_Size (MPS) mechanism enables software to control the maximum payload in TLPs sent by Endpoints to balance latency versus bandwidth trade-offs, particularly for isochronous traffic.

If software chooses to program the MPS of various System Elements to non-default values, it must take care to ensure that each TLP with a data payload does not exceed the MPS setting of any System Element along the TLP's path. Otherwise, the TLP will be rejected by the System Element whose MPS setting is too small.

No specific algorithm to configure MPS is required by this specification, but software should base its algorithm upon factors such as the following:

- the MPS capability of each System Element within a Hierarchy
- awareness of when System Elements are added or removed through Hot-Plug operations
- knowing which System Elements send TLPs to each other, what type of traffic is carried, what type of transactions are used, and if TLP sizes are constrained by other mechanisms

For the case of system firmware that configures System Elements in preparation for running legacy operating system environments, system firmware may need to avoid programming MPS settings above the default of 128 bytes, which is the minimum supported by Endpoints.

For example, if the operating system environment does not implement services for optimizing MPS settings, system firmware probably should not program a non-default MPS for a Hierarchy that supports Hot-Plug operations. Otherwise, if no software is present to manage MPS settings when a new element is added, improper operation may result. Note that a newly added element may not even support a MPS setting as large as the rest of the Hierarchy, in which case software may need to deny enabling the new element or reduce the MPS settings of other elements, which may require quiescing all traffic carrying data payloads.

For ARI Devices and other MFDs, it's challenging to describe concisely what determines a Function's MPS limit for received TLPs. For this reason, the formal term Rx_MPS_Limit was introduced. It is used in many instances where former revisions of this specification used Max_Payload_Size in the context of a Receiver. It covers several special cases where the MPS limit is determined by the MPS settings in other Functions of an MFD. See § Section 2.2.2 for details.

For ARI Devices and other MFDs, it's also challenging to describe concisely what determines a Function's MPS limit for transmitted TLPs. For this reason, the formal term Tx_MPS_Limit was introduced. It is used in several instances where former revisions of this specification used Max_Payload_Size in the context of a Transmitter. It covers several special cases where the MPS limit is determined by the MPS settings in other Functions of an MFD. See § Section 2.2.2 for details.

# IMPLEMENTATION NOTE: RX_MPS_FIXED ENHANCEMENT FOR MAX_PAYLOAD_SIZE 

The Rx_MPS_Fixed field was added to the Device Capabilities Register in the 6.0 Revision of this specification. As required in § Section 7.5.3.3, the Rx_MPS_Fixed capability bit MUST@FLIT be Set.

When Rx_MPS_Fixed is Set, the Receiver MPS limit for that Function is the value of the Function's Max_Payload_Size Supported capability field, the highest MPS setting that the Function supports. The Rx_MPS_Fixed mechanism enables the MPS limit for the Function's Receiver and Transmitter to be independent, which in certain cases enables software to change MPS settings without having to quiesce all traffic carrying data payloads.

For example, in configurations where active Functions lack this enhancement, if software increases the MPS setting of a given Function, any TLPs with data payloads that the Function sends to another Function may exceed its MPS setting, resulting in Malformed TLP errors. Similarly, if software decreases the MPS setting of a given Function, any TLPs with data payloads that other Functions send to it may exceed its MPS setting, again resulting in Malformed TLP errors. Without Rx_MPS_Fixed, the only general solution is to quiesce said traffic during reconfiguration.

## IMPLEMENTATION NOTE: MIXED MAX_PAYLOAD_SIZE CONFIGURATIONS

The simplest way for System Software to configure a non-default Max_Payload_Size (MPS) setting for a Hierarchy is to scan all Functions, determine the smallest Max_Payload_Size Supported capability, and configure the MPS setting in all Functions to this value. This guarantees that no Function will send a TLP with a payload size that the target Function can't handle. However, this simple policy may be unnecessarily restrictive, given that not all Functions send each other Memory Space transactions. In fact, many Endpoints only exchange Memory Space transactions with the host, and don't exchange any P2P TLPs with other Endpoints.

To support the use case for "mixed MPS configurations", a Function that has its Mixed_MPS_Supported bit Set is permitted to transmit TLPs with payloads exceeding its MPS setting, though it must never exceed its Max_Payload_Size Supported capability. For the case where host memory supports Rx_MPS_Fixed, System Software may configure the MPS setting in each Endpoint based solely on its path to host memory and the Max_Payload_Size Supported capability of host memory. Then, for any Endpoints that support P2P with other Endpoints, driver software can make adjustments necessary for the P2P traffic, including routing element MPS capability along P2P paths. If the Endpoint's Mixed_MPS_Supported bit is Set, indicating that it supports an implementation specific mechanism capable of supporting different MPS settings for different targets, the driver software may configure that mechanism to optimize the MPS setting for P2P target Endpoints. If the Endpoint does not support this type of mechanism, or if the mechanism is unable to accommodate all of the Endpoint's P2P MPS requirements, the driver software may reduce its MPS setting if needed to accommodate its P2P traffic.

Mixed MPS configurations are especially useful for cases where a set of Endpoints exchange a high volume of very large P2P TLPs between each other; e.g., a set of high-end accelerators or SSDs connected by one or more high-end switches. Such configurations might use a much larger MPS setting (e.g., 2048 bytes) for the high-end switches and accelerators/SSDs than supported by most hosts (e.g., 512 bytes).

# IMPLEMENTATION NOTE: USE OF MAX_READ_REQUEST_SIZE 

The Max_Read_Request_Size mechanism allows improved control of bandwidth allocation in systems where Quality of Service (QoS) is important for the target applications. For example, an arbitration scheme based on counting Requests (and not the sizes of those Requests) provides imprecise bandwidth allocation when some Requesters use much larger sizes than others. The Max_Read_Request_Size mechanism can be used to force more uniform allocation of bandwidth, by restricting the upper size of Read Requests.

### 7.5.3.5 Device Status Register (Offset OAh)

The Device Status Register provides information about PCI Express device (Function) specific parameters. § Figure 7-26 details allocation of register fields in the Device Status Register; § Table 7-22 provides the respective bit definitions.
![img-24.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-24.jpeg)

Figure 7-26 Device Status Register

Table 7-22 Device Status Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 0 | Correctable Error Detected - This bit indicates status of correctable errors detected. Errors are logged in this register regardless of whether error reporting is enabled or not in the Device Control Register. For a Multi-Function Device, each Function indicates status of errors as perceived by the respective Function. <br> For Functions supporting Advanced Error Handling, errors are logged in this register regardless of the settings of the Correctable Error Mask register. <br> Default value of this bit is Ob. | RW1C |
| 1 | Non-Fatal Error Detected - This bit indicates status of Non-fatal errors detected. Errors are logged in this register regardless of whether error reporting is enabled or not in the Device Control Register. For a Multi-Function Device, each Function indicates status of errors as perceived by the respective Function. <br> For Functions supporting Advanced Error Handling, errors are logged in this register regardless of the settings of the Uncorrectable Error Mask register. <br> Default value of this bit is Ob. | RW1C |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 2 | Fatal Error Detected - This bit indicates status of Fatal errors detected. Errors are logged in this register regardless of whether error reporting is enabled or not in the Device Control Register. For a Multi-Function Device, each Function indicates status of errors as perceived by the respective Function. <br> For Functions supporting Advanced Error Handling, errors are logged in this register regardless of the settings of the Uncorrectable Error Mask register. <br> Default value of this bit is Ob. | RW1C |
| 3 | Unsupported Request Detected - This bit indicates that the Function received an Unsupported Request. Errors are logged in this register regardless of whether error reporting is enabled or not in the Device Control Register. For a Multi-Function Device, each Function indicates status of errors as perceived by the respective Function. <br> Default value of this bit is Ob. | RW1C |
| 4 | AUX Power Detected - Functions that require auxiliary power report this bit as Set if auxiliary power is detected by the Function. <br> For VFs, this bit is not supported and must be hardwired to Zero. | RO <br> VF ROZ |
| 5 | Transactions Pending - <br> Endpoints: <br> When Set, this bit indicates that the Function has issued Non-Posted Requests that have not been completed. A Function reports this bit cleared only when all outstanding Non-Posted Requests have completed or have been terminated by the Completion Timeout mechanism. This bit must also be cleared upon the completion of an FLR. <br> Root and Switch Ports: <br> When Set, this bit indicates that a Port has issued Non-Posted Requests on its own behalf (using the Port's own, or its Shadow Function's, Requester ID) which have not been completed. The Port reports this bit cleared only when all such outstanding Non-Posted Requests have completed or have been terminated by the Completion Timeout mechanism. Note that Root and Switch Ports implementing only the functionality required by this document do not issue Non-Posted Requests on their own behalf, and therefore are not subject to this case. Root and Switch Ports that do not issue Non-Posted Requests on their own behalf hardwire this bit to Ob. | RO <br>  |
| 6 | Emergency Power Reduction Detected - This bit is Set when the Function is in the Emergency Power Reduction State. Whenever any condition is present that would cause the Emergency Power Reduction State to be entered, the Function remains in the Emergency Power Reduction State and writes to this bit have no effect. See § Section 6.24 for additional details. <br> Multi-Function Devices associated with an Upstream Port must Set this bit in all Functions that support Emergency Power Reduction State. <br> For VFs, this bit is not supported and must be hardwired to Zero. <br> Except for VFs, this bit is RsvdZ if the Emergency Power Reduction Supported field is 00b (see § Section 7.5.3.15). <br> This bit is RsvdZ in Functions that are not associated with an Upstream Port. <br> Default value is Ob. | RW1C <br> VF ROZ |

# 7.5.3.6 Link Capabilities Register (Offset OCh) 

The Link Capabilities Register identifies PCI Express Link specific capabilities. § Figure 7-27 details allocation of register fields in the Link Capabilities Register; § Table 7-23 provides the respective bit definitions.

![img-25.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-25.jpeg)

Figure 7-27 Link Capabilities Register 6

Table 7-23 Link Capabilities Register 6

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 3:0 | Max Link Speed - This field indicates the maximum Link speed of the associated Port. <br> The encoded value specifies a Bit Location in the Supported Link Speeds Vector (in the Link Capabilities 2 Register) that corresponds to the maximum Link speed. <br> Defined encodings are: | RO |
|  | 0001b Supported Link Speeds Vector field bit 0 |  |
|  | 0010b Supported Link Speeds Vector field bit 1 |  |
|  | 0011b Supported Link Speeds Vector field bit 2 |  |
|  | 0100b Supported Link Speeds Vector field bit 3 |  |
|  | 0101b Supported Link Speeds Vector field bit 4 |  |
|  | 0110b Supported Link Speeds Vector field bit 5 |  |
|  | 0111b Supported Link Speeds Vector field bit 6 |  |
|  | All other encodings are reserved. |  |
|  | Multi-Function Devices associated with an Upstream Port must report the same value in this field for all Functions. |  |
| 9:4 | Maximum Link Width - This field indicates the maximum Link width (xN - corresponding to N Lanes) implemented by the component. This value is permitted to exceed the number of Lanes routed to the slot (Downstream Port), adapter connector (Upstream Port), or in the case of component-to-component connections, the actual wired connection width. <br> Defined encodings are: | RO |
|  | 000001 b | $x 1$ |
|  | 00010 b | $x 2$ |
|  | 000100 b | $x 4$ |
|  | 001000 b | $x 8$ |
|  | 010000 b | $x 16$ |
|  | All other encodings are Reserved. |  |
|  | Multi-Function Devices associated with an Upstream Port must report the same value in this field for all Functions. |  |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 11:10 | ASPM Support / Active State Power Management Support - This field indicates the level of ASPM supported on the given PCI Express Link. See § Section 5.4.1 for ASPM support requirements. <br> Defined encodings are: | RO |
|  | 00b No ASPM Support |  |
|  | 01b L0s Supported |  |
|  | 10b L1 Supported |  |
|  | 11b L0s and L1 Supported |  |
|  | Multi-Function Devices associated with an Upstream Port must report the same value in this field for all Functions. |  |
| 14:12 | L0s Exit Latency - This field indicates the L0s exit latency for the given PCI Express Link. The value reported indicates the length of time this Port requires to complete transition from L0s to L0. If L0s is not supported, the value is undefined; however, see the Implementation Note "Potential Issues With Legacy Software When L0s is Not Supported" in § Section 5.4.1.1 for the recommended value. <br> Defined encodings are: | RO |
|  | 000b Less than 64 ns |  |
|  | 001b 64 ns to less than 128 ns |  |
|  | 010b 128 ns to less than 256 ns |  |
|  | 011b 256 ns to less than 512 ns |  |
|  | 100b 512 ns to less than $1 \mu \mathrm{~s}$ |  |
|  | 101b $1 \mu \mathrm{~s}$ to less than $2 \mu \mathrm{~s}$ |  |
|  | 110b $2 \mu \mathrm{~s}-4 \mu \mathrm{~s}$ |  |
|  | 111b More than $4 \mu \mathrm{~s}$ |  |
|  | Note that exit latencies may be influenced by PCI Express reference clock configuration depending upon whether a component uses a common or separate reference clock. <br> Multi-Function Devices associated with an Upstream Port must report the same value in this field for all Functions. |  |
| 17:15 | L1 Exit Latency - This field indicates the L1 Exit Latency for the given PCI Express Link. The value reported indicates the length of time this Port requires to complete transition from ASPM L1 to L0. If ASPM L1 is not supported, the value is undefined. <br> Defined encodings are: | RO |
|  | 000b Less than $1 \mu \mathrm{~s}$ |  |
|  | 001b $1 \mu \mathrm{~s}$ to less than $2 \mu \mathrm{~s}$ |  |
|  | 010b $2 \mu \mathrm{~s}$ to less than $4 \mu \mathrm{~s}$ |  |
|  | 011b $4 \mu \mathrm{~s}$ to less than $8 \mu \mathrm{~s}$ |  |
|  | 100b $8 \mu \mathrm{~s}$ to less than $16 \mu \mathrm{~s}$ |  |
|  | 101b $16 \mu \mathrm{~s}$ to less than $32 \mu \mathrm{~s}$ |  |
|  | 110b $32 \mu \mathrm{~s}-64 \mu \mathrm{~s}$ |  |
|  | 111b More than $64 \mu \mathrm{~s}$ |  |
|  | Note that exit latencies may be influenced by PCI Express reference clock configuration depending upon whether a component uses a common or separate reference clock. <br> Multi-Function Devices associated with an Upstream Port must report the same value in this field for all Functions. |  |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 18 | Clock Power Management - For Upstream Ports, a value of 1 b in this bit indicates that the component tolerates the removal of any reference clock(s) via the "clock request" (CLKREQ\#) mechanism when the Link is in the L1 and L2/L3 Ready Link states. A value of 0 b indicates the component does not have this capability and that reference clock(s) must not be removed in these Link states. <br> L1 PM Substates defines other semantics for the CLKREQ\# signal, which are managed independently of Clock Power Management. <br> This Capability is applicable only in form factors that support "clock request" (CLKREQ\#) capability. <br> For a Multi-Function Device associated with an Upstream Port, each Function indicates its capability independently. Power Management configuration software must only permit reference clock removal if all Functions of the Multi-Function Device indicate a 1b in this bit. For ARI Devices, all Functions must indicate the same value in this bit. <br> For Downstream Ports, this bit must be hardwired to 0b. | RO |
| 19 | Surprise Down Error Reporting Capable - For a Downstream Port, this bit must be Set if the component supports the optional capability of detecting and reporting a Surprise Down error condition. <br> For Upstream Ports and components that do not support this optional capability, this bit must be hardwired to 0b. | RO |
| 20 | Data Link Layer Link Active Reporting Capable - For a Downstream Port, this bit must be hardwired to 1 b if the component supports the optional capability of reporting the DL_Active state of the Data Link Control and Management State Machine. For a hot-plug capable Downstream Port (as indicated by the Hot-Plug Capable bit of the Slot Capabilities Register) or a Downstream Port that supports Link speeds greater than $5.0 \mathrm{GT} / \mathrm{s}$, this bit must be hardwired to 1 b . <br> For Upstream Ports and components that do not support this optional capability, this bit must be hardwired to 0 b . | RO |
| 21 | Link Bandwidth Notification Capability - A value of 1 b indicates support for the Link Bandwidth Notification status and interrupt mechanisms. This capability is required for all Root Ports and Switch Downstream Ports supporting Links wider than x1 and/or multiple Link speeds. <br> This field is not applicable and is Reserved for Endpoints, PCI Express to PCI/PCI-X bridges, and Upstream Ports of Switches. <br> Functions that do not implement the Link Bandwidth Notification Capability must hardwire this bit to 0b. | RO |
| 22 | ASPM Optionality Compliance - This bit must be set to 1 b in all Functions. Components implemented against certain earlier versions of this specification will have this bit set to 0b. <br> Software is permitted to use the value of this bit to help determine whether to enable ASPM or whether to run ASPM compliance tests. | HwInit |
| $31: 24$ | Port Number - This field indicates the PCI Express Port number for the given PCI Express Link. <br> Multi-Function Devices associated with an Upstream Port must report the same value in this field for all Functions. | HwInit |

# IMPLEMENTATION NOTE: USE OF THE ASPM OPTIONALITY COMPLIANCE BIT 

Correct implementation and utilization of ASPM can significantly reduce Link power. However, ASPM feature implementations can be complex, and historically, some implementations have not been compliant to the specification. To address this, some of the ASPM optionality and ASPM entry requirements from earlier revisions of this document have been loosened. However, clear pass/fail compliance testing for ASPM features is also supported and expected.

The ASPM Optionality Compliance bit was created as a tool to establish clear expectations for hardware and software. This bit is Set to indicate hardware that conforms to the current specification, and this bit must be Set in components compliant to this specification.

System software as well as compliance software can assume that if this bit is Set, that the associated hardware conforms to the current specification. Hardware should be fully capable of supporting ASPM configuration management without needing component-specific treatment by system software.

For older hardware that does not have this bit Set, it is strongly recommended for system software to provide mechanisms to enable ASPM on components that work correctly with ASPM, and to disable ASPM on components that don't.

### 7.5.3.7 Link Control Register (Offset 10h)

The Link Control Register controls PCI Express Link specific parameters. § Figure 7-28 details allocation of register fields in the Link Control Register; § Table 7-24 provides the respective bit definitions.

For VF fields indicated as RsvdP, the associated PF's setting applies to the VF.

![img-26.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-26.jpeg)

Figure 7-28 Link Control Register

Table 7-24 Link Control Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 1:0 | ASPM Control / Active State Power Management Control - This field controls the level of ASPM enabled on the given PCI Express Link. See § Section 5.4.1.4 for requirements on when and how to enable ASPM. <br> Defined encodings are: | RW <br> VF RsvdP |
|  | 00b | Disabled |
|  | 01b | L0s Entry Enabled |
|  | 10b | L1 Entry Enabled |
|  | 11b | L0s and L1 Entry Enabled |

Note: "L0s Entry Enabled" enables the Transmitter to enter L0s. If L0s is supported, the Receiver must be capable of entering L0s even when the Transmitter is disabled from entering L0s (00b or 10b).
In Flit Mode, LOs is not supported, bit 0 of this field is ignored and has no effect (i.e., encodings 01b and 00b are equivalent as are encodings 11 b and 10b).
ASPM L1 must be enabled by software in the Upstream component on a Link prior to enabling ASPM L1 in the Downstream component on that Link. When disabling ASPM L1, software must disable ASPM L1 in the Downstream component on a Link prior to disabling ASPM L1 in the Upstream component on that Link. ASPM L1 must only be enabled on the Downstream component if both components on a Link support ASPM L1.
For Multi-Function Devices (including ARI Devices), it is recommended that software program the same value for this field in all Functions. For non-ARI Multi-Function Devices, only capabilities enabled in all Functions are enabled for the component as a whole.
For ARI Devices, ASPM Control is determined solely by the setting in Function 0, regardless of Function 0's D-state. The settings in the other Functions always return whatever value software programmed for each, but otherwise are ignored by the component.

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | Default value of this field is 00 b unless otherwise required by a particular form factor. |  |
| 2 | PTM Propagation Delay Adaptation Interpretation B - For a device that supports PTM, if PTM Propagation Delay Adaptation Capable in the PTM Capability Register is Set, then, for an Upstream Port, this bit when Set selects interpretation B of the Propagation Delay[31:0] field for received PTM ResponseD Messages, and for a Downstream Port, this bit when Set selects interpretation B of the Propagation Delay[31:0] field for PTM ResponseD Messages transmitted by the Port; otherwise this bit when Clear selects interpretation A for both cases. For a device that supports PTM, if its PTM Propagation Delay Adaptation Capable in the PTM Capability Register is Clear, Ports must hardwire this bit to 0b. For Multi-Function Devices associated with an Upstream Port of a device that supports PTM, this bit must be implemented in the same Function that contains the PTM Extended Capability structure and RsvdP in all other Functions. Default value is implementation specific, but is recommended to be 0b. For a device that does not support PTM, for all Ports in that device this bit must be RsvdP. | RW / RsvdP |
| 3 | Read Completion Boundary (RCB) - field is meaningful in Root Ports, Endpoints and Bridges. When meaningful, defined encodings are: <br> 0b 64 byte <br> 1b 128 byte <br> Root Ports: <br> Endpoints and Bridges: <br> RCB contains the RCB value for the Root Port. Refer to $\S$ Section 2.3.1.1 for the definition of the parameter RCB. <br> This bit is hardwired for a Root Port and returns its RCB support capabilities. <br> Read Completion Boundary (RCB) - Optionally Set by configuration software to indicate the RCB value of the Root Port Upstream from the Endpoint or Bridge. Refer to $\S$ Section 2.3.1.1 for the definition of the parameter RCB. <br> Configuration software must only Set this bit if the Root Port Upstream from the Endpoint or Bridge reports an RCB value of 128 bytes (a value of 1 b in the Read Completion Boundary bit). <br> Default value of this bit is 0 b . <br> Functions that do not implement this feature must hardwire the bit to 0b. <br> Switch Ports: <br> Not applicable - must hardwire the bit to 0 b | Root Ports: <br> RO <br> Endpoints and <br> Bridges: <br> RW <br> VF RsvdP <br> Switch <br> Ports: <br> RO |
| 4 | Link Disable - This bit disables the Link by directing the LTSSM to the Disabled state when Set; this bit is Reserved on Endpoints, PCI Express to PCI/PCI-X bridges, and Upstream Ports of Switches. <br> See Implementation Note: Delays in Data Link Layer Link Active Reflecting Link Control Operations for related information. <br> Writes to this bit are immediately reflected in the value read from the bit, regardless of actual Link state. <br> After clearing this bit, software must honor timing requirements defined in $\S$ Section 6.6.1 with respect to the first Configuration Read following a Conventional Reset. <br> Default value of this bit is 0 b . | RW |
| 5 | Retrain Link - A write of 1 b to this bit initiates Link retraining by directing the Physical Layer LTSSM to the Recovery state. If the LTSSM is already in Recovery or Configuration, re-entering Recovery is permitted but not required. If the Port is in DPC when a write of 1 b to this bit occurs, the result is undefined. Reads of this bit always return 0 b . <br> It is permitted to write 1 b to this bit while simultaneously writing modified values to other fields in this register. If the LTSSM is not already in Recovery or Configuration, the resulting Link training must | RW |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | use the modified values. If the LTSSM is already in Recovery or Configuration, the modified values are not required to affect the Link training that's already in progress. <br> This bit is not applicable and is Reserved for Endpoints, PCI Express to PCI/PCI-X bridges, and Upstream Ports of Switches. <br> This bit always returns 0 b when read. |  |
| 6 | Common Clock Configuration - When Set, this bit indicates that this component and the component at the opposite end of this Link are operating with a distributed common reference clock. <br> A value of 0 b indicates that this component and the component at the opposite end of this Link are operating with asynchronous reference clock. <br> For non-ARI Multi-Function Devices, software must program the same value for this bit in all Functions. If not all Functions are Set, then the component must as a whole assume that its reference clock is not common with the Upstream component. <br> For ARI Devices, Common Clock Configuration is determined solely by the setting in Function 0. The settings in the other Functions always return whatever value software programmed for each, but otherwise are ignored by the component. <br> Components utilize this Common Clock Configuration information to report the correct L0s and L1 Exit Latencies. <br> After changing the value in this bit in both components on a Link, software must trigger the Link to retrain by writing a 1 b to the Retrain Link bit of the Downstream Port. <br> Default value of this bit is 0 b . | RW <br> VF RsvdP |
| 7 | Extended Synch - When Set, this bit forces the transmission of additional Ordered Sets when exiting the L0s state (see § Section 4.2.5.6 ) and when in the Recovery state (see § Section 4.2.7.4.1 ). This mode provides external devices (e.g., logic analyzers) monitoring the Link time to achieve bit and Symbol lock before the Link enters the L0 state and resumes communication. <br> For Multi-Function Devices if any Function has this bit Set, then the component must transmit the additional Ordered Sets when exiting L0s or when in Recovery. <br> Default value for this bit is 0 b . | RW <br> VF RsvdP |
| 8 | Enable Clock Power Management - Applicable only for Upstream Ports and with form factors that support a "Clock Request" (CLKREQ\#) mechanism, this bit operates as follows: <br> 0b <br> 1b <br> 1b <br> 1b <br> 1b <br> 1b. <br> Default value of this bit is 0 b , unless specified otherwise by the form factor specification. | RW <br> VF RsvdP |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 9 | Hardware Autonomous Width Disable - When Set, this bit disables hardware from changing the Link width for reasons other than attempting to correct unreliable Link operation by reducing Link width. <br> For a Multi-Function Device associated with an Upstream Port, the bit in Function 0 is of type RW, and only Function 0 controls the component's Link behavior. In all other Functions of that device, this bit is of type RsvdP. <br> Components that do not implement the ability autonomously to change Link width are permitted to hardwire this bit to 0 b. <br> Default value of this bit is 0 b . | RW/RsvdP <br> (see <br> description) <br> VF RsvdP |
| 10 | Link Bandwidth Management Interrupt Enable - When Set, this bit enables the generation of an interrupt to indicate that the Link Bandwidth Management Status bit has been Set. <br> This bit is not applicable and is Reserved for Endpoints, PCI Express-to-PCI/PCI-X bridges, and Upstream Ports of Switches. <br> Functions that do not implement the Link Bandwidth Notification Capability must hardwire this bit to 0b. Default value of this bit is 0 b . | RW |
| 11 | Link Autonomous Bandwidth Interrupt Enable - When Set, this bit enables the generation of an interrupt to indicate that the Link Autonomous Bandwidth Status bit has been Set. <br> This bit is not applicable and is Reserved for Endpoints, PCI Express-to-PCI/PCI-X bridges, and Upstream Ports of Switches. <br> Functions that do not implement the Link Bandwidth Notification Capability must hardwire this bit to 0b. Default value of this bit is 0 b . | RW |
| 12 | SRIS Clocking - This bit, in conjunction with Common Clock Configuration, indicates the clocking mode used on the Link. <br> This bit is meaningful in Downstream Ports that support Flit Mode. In all other Functions, this bit is RsvdP. <br> If Common Clock Configuration is Set, this bit has no effect and the SRIS Clocking bit in the TS1s must be Ob (Symbol 4, bit 7). <br> If Common Clock Configuration is Clear, this bit is sent in the SRIS Clocking bit of TS1s (Symbol 4, bit 7). | RW |
|  | Clocking Mode | Common Clock Configuration | SRIS Clocking |
|  | Common Clock | 1 | $x$ |
|  | SRNS | 0 | 0 |
|  | SRIS | 0 | 1 |
|  | Default is Ob. |  |  |
| 13 | Flit Mode Disable - when Set, the Port is not permitted to set the Flit Mode Supported bit in training sets it sends. This bit has no effect on the Flit Mode Supported bit in the PCI Express Capabilities Register and thus has no effect on behavior required by MUST@FLIT. <br> Since Flit Mode is required at 64.0 GT/s or higher, disabling Flit Mode also has the effect of disabling data rates of $64.0 \mathrm{GT} / \mathrm{s}$ or higher. <br> This bit is mandatory in Downstream Ports where Flit Mode Supported is Set. <br> For Functions associated with an Upstream Port, this bit is optionally implemented in Function 0 and is not implemented in all other Functions. When not implemented, this bit must be hardwired to Zero. | RW |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | Changing this bit while the Link is Up has no effect. The updated value will take effect on the next transition to Link Up. <br> This bit can be used as a workaround for faulty Flit Mode implementations. As such, it might be set by System Firmware, Device Firmware. As such, System Software should not clear this bit. <br> This bit is not implemented in RCiEPs. <br> In Downstream Ports, the default is Zero. In Upstream Ports, the default is implementation specific (e.g., it might be Set by device firmware). |  |
| 15:14 | DRS Signaling Control - Indicates the mechanism used to report reception of a DRS message. Must be implemented for Downstream Ports with the DRS Supported bit Set in the Link Capabilities 2 Register. Encodings are: | RW/RsvdP |
|  | 00b DRS not Reported: If DRS Supported is Set, receiving a DRS Message will set DRS Message Received in the Link Status 2 Register but will otherwise have no effect |  |
|  | 01b DRS Interrupt Enabled: If the DRS Message Received bit in the Link Status 2 Register transitions from 0 to 1 , and interrupts are enabled, an interrupt must be generated. If either MSI or MSI-X is enabled, an MSI or MSI-X interrupt is generated using the vector in Interrupt Message Number (\$ Section 7.5.3.2 ) |  |
|  | 10b DRS to FRS Signaling Enabled: If the DRS Message Received bit in the Link Status 2 Register transitions from 0 to 1 , the Port must send an FRS Message Upstream with the FRS Reason field set to DRS Message Received. |  |
|  | Behavior is undefined if this field is set to 10b and the FRS Supported bit in the Device Capabilities 2 Register is Clear. |  |
|  | Behavior is undefined if this field is set to 11b. |  |
|  | Downstream Ports with the DRS Supported bit Clear in the Link Capabilities 2 Register must hardwire this field to 00b. <br> This field is Reserved for Upstream Ports. <br> Default value of this field is 00b. |  |

# IMPLEMENTATION NOTE: SOFTWARE COMPATIBILITY WITH ARI DEVICES 

With the ASPM Control field, Common Clock Configuration bit, and Enable Clock Power Management bit in the Link Control Register, there are potential software compatibility issues with ARI Devices since these controls operate strictly off the settings in Function 0 instead of the settings in all Functions.

With compliant software, there should be no issues with the Common Clock Configuration bit, since software is required to set this bit the same in all Functions.

With the Enable Clock Power Management bit, there should be no compatibility issues with software that sets this bit the same in all Functions. However, if software does not set this bit the same in all Functions, and relies on each Function having the ability to prevent Clock Power Management from being enabled, such software may have compatibility issues with ARI Devices.

With the ASPM Control field, there should be no compatibility issues with software that sets this bit the same in all Functions. However, if software does not set this bit the same in all Functions, and relies on each Function in DO state having the ability to prevent ASPM from being enabled, such software may have compatibility issues with ARI Devices.

# IMPLEMENTATION NOTE: AVOIDING RACE CONDITIONS WHEN USING THE RETRAIN LINK BIT 

When software changes Link control parameters and writes a 1b to the Retrain Link bit in order to initiate Link training using the new parameter settings, special care is required in order to avoid certain race conditions. At any instant the LTSSM may transition to the Recovery or Configuration state due to normal Link activity, without software awareness. If the LTSSM is already in Recovery or Configuration when software writes updated parameters to the Link Control Register, as well as a 1b, to the Retrain Link bit, the LTSSM might not use the updated parameter settings with the current Link training, and the current Link training might not achieve the results that software intended.

To avoid this potential race condition, it is strongly recommended that software use the following algorithm or something similar:

1. Software sets the relevant Link control parameters to the desired settings without writing a 1b to the Retrain Link bit.
2. Software polls the Link Training bit in the Link Status Register until the value returned is 0 b .
3. Software writes a 1b to the Retrain Link bit without changing any other fields in the Link Control Register.

The above algorithm guarantees that Link training will be based on the Link control parameter settings that software intends.

# IMPLEMENTATION NOTE: USE OF THE SLOT CLOCK CONFIGURATION AND COMMON CLOCK CONFIGURATION BITS 

In order to determine the common clocking configuration of components on opposite ends of a Link that crosses a connector, two pieces of information are required. The following description defines these requirements.

The first necessary piece of information is whether the Downstream Port that connects to the slot uses a clock that has a common source and therefore constant phase relationship to the clock signal provided on the slot. This information is provided by the system side component through a hardware initialized bit (Slot Clock Configuration) in its Link Status Register. Note that some electromechanical form factor specifications may require the Port that connects to the slot use a clock that has a common source to the clock signal provided on the slot.

The second necessary piece of information is whether the component on the adapter uses the clock supplied on the slot or one generated locally on the adapter. The adapter design and layout will determine whether the component is connected to the clock source provided by the slot. A component going onto this adapter should have some hardware initialized method for the adapter design/designer to indicate the configuration used for this particular adapter design. This information is reported by Slot Clock Configuration in the Link Status Register of each Function in the Upstream Port. Note that some electromechanical form factor specifications may require the Port on the adapter to use the clock signal provided on the connector.

System firmware or software will read the Slot Clock Configuration from the components on both ends of a physical Link. If the Slot Clock Configuration bit is Set for both components, this firmware/software will Set the Common Clock Configuration bit on both components connected to the Link. Each component uses this bit to determine the length of time required to re-synch its Receiver to the opposing component's Transmitter when exiting LOs.

The time required to re-synch is reported as a time value in the LOs Exit Latency in the Link Capabilities Register (offset 0Ch) and is sent to the opposing Transmitter as part of the initialization process as N_FTS. Components would be expected to require much longer synch times without common clocking and would therefore report a longer LOs Exit Latency in bits 12-14 of the Link Capabilities Register and would send a larger number for N_FTS during training. This forces a requirement that whatever software changes this bit should force a Link retrain in order to get the correct N_FTS set for the Receivers at both ends of the Link.

### 7.5.3.8 Link Status Register (Offset 12h)

The Link Status Register provides information about PCI Express Link specific parameters. § Figure 7-29 details allocation of register fields in the Link Status Register; § Table 7-26 provides the respective bit definitions.

For a VF, all fields are RsvdZ and the associated PF's setting for each field applies to the VF.

![img-27.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-27.jpeg)

Figure 7-29 Link Status Register

Table 7-26 Link Status Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 3:0 | Current Link Speed - This field indicates the negotiated Link speed of the given PCI Express Link. | RO |
|  | The encoded value specifies a Bit Location in the Supported Link Speeds Vector (in the Link Capabilities 2 Register) that corresponds to the current Link speed. | VF RsvdZ |
|  | Defined encodings are: |  |
|  | 0001b Supported Link Speeds Vector field bit 0 |  |
|  | 0010b Supported Link Speeds Vector field bit 1 |  |
|  | 0011b Supported Link Speeds Vector field bit 2 |  |
|  | 0100b Supported Link Speeds Vector field bit 3 |  |
|  | 0101b Supported Link Speeds Vector field bit 4 |  |
|  | 0110b Supported Link Speeds Vector field bit 5 |  |
|  | 0111b Supported Link Speeds Vector field bit 6 |  |
|  | All other encodings are Reserved. |  |
|  | The value in this field is undefined when the Link is not up. |  |
| 9:4 | Negotiated Link Width - This field indicates the negotiated width of the given PCI Express Link. This includes the Link Width determined during initial link training as well changes that occur after initial link training (e.g., LOp). | RO VF RsvdZ |
|  | Defined encodings are: |  |
|  | 000001 b | $x 1$ |
|  | 00010 b | $x 2$ |
|  | 000100 b | $x 4$ |
|  | 001000 b | $x 8$ |
|  | 010000 b | $x 16$ |
|  | All other encodings are Reserved. The value in this field is undefined when the Link is not up. |  |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 10 | Undefined - The value read from this bit is undefined. In previous versions of this specification, this bit was used to indicate a Link Training Error. System software must ignore the value read from this bit. System software is permitted to write any value to this bit. | RO <br> VF RsvdZ |
| 11 | Link Training - This read-only bit indicates that the Physical Layer LTSSM is in the Configuration or Recovery state, or that 1b was written to the Retrain Link bit but Link training has not yet begun. Hardware clears this bit when the LTSSM exits the Configuration/Recovery state. <br> This bit is not applicable and Reserved for Endpoints, PCI Express to PCI/PCI-X bridges, and Upstream Ports of Switches, and must be hardwired to 0b. | RO <br> VF RsvdZ |
| 12 | Slot Clock Configuration - This bit indicates that the component uses the same physical reference clock that the platform provides on the connector. If the device uses an independent clock irrespective of the presence of a reference clock on the connector, this bit must be clear. <br> For a Multi-Function Device, each Function must report the same value for this bit. | HwInit VF RsvdZ |
| 13 | Data Link Layer Link Active - This bit indicates the status of the Data Link Control and Management State Machine. It returns a 1b to indicate the DL_Active state, 0b otherwise. <br> See Implementation Note: Delays in Data Link Layer Link Active Reflecting Link Control Operations for related information. <br> This bit must be implemented if the Data Link Layer Link Active Reporting Capable bit is 1b. Otherwise, this bit must be hardwired to 0b. | RO <br> VF RsvdZ |
| 14 | Link Bandwidth Management Status - This bit is Set by hardware to indicate that either of the following has occurred without the Port transitioning through DL_Down status: <br> - A Link retraining has completed following a write of 1 b to the Retrain Link bit. <br> Note: This bit is Set following any write of 1 b to the Retrain Link bit, including when the Link is in the process of retraining for some other reason. <br> - Hardware has changed Link speed or width to attempt to correct unreliable Link operation, either through an LTSSM timeout or a higher level process. <br> This bit must be set if the Physical Layer reports a speed or width change was initiated by the Downstream component that was not indicated as an autonomous change. <br> This bit is not applicable and is Reserved for Endpoints, PCI Express-to-PCI/PCI-X bridges, and Upstream Ports of Switches. <br> Functions that do not implement the Link Bandwidth Notification Capability must hardwire this bit to 0b. The default value of this bit is 0 b . | RW1C <br> VF RsvdZ |
| 15 | Link Autonomous Bandwidth Status - This bit is Set by hardware to indicate that hardware has autonomously changed Link speed or width, without the Port transitioning through DL_Down status, for reasons other than to attempt to correct unreliable Link operation. <br> This bit must be set if the Physical Layer reports a speed or width change was initiated by the Downstream component that was indicated as an autonomous change. <br> This bit is not applicable and is Reserved for Endpoints, PCI Express-to-PCI/PCI-X bridges, and Upstream Ports of Switches. <br> Functions that do not implement the Link Bandwidth Notification Capability must hardwire this bit to 0b. The default value of this bit is 0 b . | RW1C <br> VF RsvdZ |

# IMPLEMENTATION NOTE: 

## DELAYS IN DLL LINK ACTIVE REFLECTING LINK CONTROL OPERATIONS

When software changes Link control parameters such as Setting the Secondary Bus Reset bit in the Bridge Control Register or the Link Disable bit in the Link Control Register, the Downstream Port will eventually transition to the DL_Down state, but there may be a significant delay with this occurring and being reflected by the Data Link Layer Link Active bit in the Link Status Register being Cleared. Often this occurs within a few ms, but in certain cases it may take tens of ms or longer. When software is waiting for Data Link Layer Link Active to become Clear, in some environments it may be best for software to set up a Data Link Layer State Changed interrupt instead of polling Data Link Layer Link Active continuously until it Clears

### 7.5.3.9 Slot Capabilities Register (Offset 14h)

The Slot Capabilities Register identifies PCI Express slot specific capabilities. § Figure 7-30 details allocation of register fields in the Slot Capabilities Register; § Table 7-27 provides the respective bit definitions.

If this register is implemented but the Slot Implemented bit is Clear, the field behavior of this entire register is undefined.
![img-28.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-28.jpeg)

Figure 7-30 Slot Capabilities Register

Table 7-27 Slot Capabilities Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 0 | Attention Button Present - When Set, this bit indicates that an Attention Button for this slot is <br> electrically controlled by the chassis. | HwInit |
| 1 | Power Controller Present - When Set, this bit indicates that a software programmable Power <br> Controller is implemented for this slot/adapter (depending on form factor). | HwInit |
| 2 | MRL Sensor Present - When Set, this bit indicates that an MRL Sensor is implemented on the chassis <br> for this slot. | HwInit |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 3 | Attention Indicator Present - When Set, this bit indicates that an Attention Indicator is electrically controlled by the chassis. | HwInit |
| 4 | Power Indicator Present - When Set, this bit indicates that a Power Indicator is electrically controlled by the chassis for this slot. | HwInit |
| 5 | Hot-Plug Surprise - When Set, this bit indicates that an adapter present in this slot might be removed from the system without any prior notification. This is a form factor specific capability. This bit is an indication to the operating system to allow for such removal without impacting continued software operation. <br> If the SFI HPS Suppress bit in the SFI Control Register is Clear, a read of the Hot-Plug Surprise bit returns the HwInit value. If the SFI HPS Suppress bit is Set, a read returns 0b. See See § Section 7.9.22.3 . | HwInit/RO <br> (see description) |
| 6 | Hot-Plug Capable - When Set, this bit indicates that this slot is capable of supporting hot-plug operations. | HwInit |
| $14: 7$ | Slot Power Limit Value - In combination with the Slot Power Limit Scale value, specifies the upper limit on power supplied by the slot (see $\S$ Section 6.9 ) or by other means to the adapter. <br> Power limit (in Watts) is calculated by multiplying the value in this field by the value in the Slot Power Limit Scale field except when the Slot Power Limit Scale field equals 00b (1.0x) and Slot Power Limit Value exceeds EFh, the following alternative encodings are used: | HwInit |
|  | F0h | $>239 \mathrm{~W}$ and $\leq 250 \mathrm{~W}$ Slot Power Limit |
|  | F1h | $>250 \mathrm{~W}$ and $\leq 275 \mathrm{~W}$ Slot Power Limit |
|  | F2h | $>275 \mathrm{~W}$ and $\leq 300 \mathrm{~W}$ Slot Power Limit |
|  | F3h | $>300 \mathrm{~W}$ and $\leq 325 \mathrm{~W}$ Slot Power Limit |
|  | F4h | $>325 \mathrm{~W}$ and $\leq 350 \mathrm{~W}$ Slot Power Limit |
|  | F5h | $>350 \mathrm{~W}$ and $\leq 375 \mathrm{~W}$ Slot Power Limit |
|  | F6h | $>375 \mathrm{~W}$ and $\leq 400 \mathrm{~W}$ Slot Power Limit |
|  | F7h | $>400 \mathrm{~W}$ and $\leq 425 \mathrm{~W}$ Slot Power Limit |
|  | F8h | $>425 \mathrm{~W}$ and $\leq 450 \mathrm{~W}$ Slot Power Limit |
|  | F9h | $>450 \mathrm{~W}$ and $\leq 475 \mathrm{~W}$ Slot Power Limit |
|  | FAh | $>475 \mathrm{~W}$ and $\leq 500 \mathrm{~W}$ Slot Power Limit |
|  | FBh | $>500 \mathrm{~W}$ and $\leq 525 \mathrm{~W}$ Slot Power Limit |
|  | FCh | $>525 \mathrm{~W}$ and $\leq 550 \mathrm{~W}$ Slot Power Limit |
|  | FDh | $>550 \mathrm{~W}$ and $\leq 575 \mathrm{~W}$ Slot Power Limit |
|  | FEh | $>575 \mathrm{~W}$ and $\leq 600 \mathrm{~W}$ Slot Power Limit |
|  | FFh | Reserved for Slot Power Limit Values above 600 W |
|  | This register must be implemented if the Slot Implemented bit is Set. <br> Writes to this register also cause the Port to send the Set_Slot_Power_Limit Message. <br> The default value prior to hardware/firmware initialization is 00000000 b . |  |
| $16: 15$ | Slot Power Limit Scale - Specifies the scale used for the Slot Power Limit Value (see § Section 6.9 ). <br> Range of Values: | HwInit |
|  | 00b | $1.0 x$ |
|  | 01b | $0.1 x$ |
|  | 10b | $0.01 x$ |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | 11b 0.001x <br> This register must be implemented if the Slot Implemented bit is Set. <br> Writes to this register also cause the Port to send the Set_Slot_Power_Limit Message. <br> The default value prior to hardware/firmware initialization is 00b. |  |
| 17 | Electromechanical Interlock Present - When Set, this bit indicates that an Electromechanical <br> Interlock is implemented on the chassis for this slot. | HwInit |
| 18 | No Command Completed Support - When Set, this bit indicates that this slot does not generate <br> software notification when an issued command is completed by the Hot-Plug Controller. This bit is <br> only permitted to be Set if the hot-plug capable Port is able to accept writes to all fields of the Slot <br> Control Register without delay between successive writes. | HwInit |
| $31: 19$ | Physical Slot Number - This field indicates the physical slot number attached to this Port. This field <br> must be hardware initialized to a value that assigns a slot number that is unique within the chassis, <br> regardless of the form factor associated with the slot. This field must be initialized to Zero for Ports <br> connected to devices that are either integrated on the system board or integrated within the same <br> silicon as the Switch device or Root Port. | HwInit |

# 7.5.3.10 Slot Control Register (Offset 18h) 

The Slot Control Register controls PCI Express Slot specific parameters. § Figure 7-31 details allocation of register fields in the Slot Control Register; § Table 7-28 provides the respective bit definitions.

Attention Indicator Control, Power Indicator Control, and Power Controller Control fields of the Slot Control Register do not have a defined default value. If these fields are implemented, it is the responsibility of either system firmware or operating system software to (re)initialize these fields after a reset of the Link.

In hot-plug capable Downstream Ports, a write to the Slot Control Register must cause a hot-plug command to be generated (see $\S$ Section 6.7.3.2 for details on hot-plug commands). A write to the Slot Control Register in a Downstream Port that is not hot-plug capable must not cause a hot-plug command to be executed.

If this register is implemented but the Slot Implemented bit is Clear, the field behavior of this entire register with the exception of the Data Link Layer State Changed Enable bit is undefined.

![img-29.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-29.jpeg)

Figure 7-31 Slot Control Register

Table 7-28 Slot Control Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 0 | Attention Button Pressed Enable - When Set to 1b, this bit enables software notification on an attention button pressed event (see § Section 6.7.3). <br> If the Attention Button Present bit in the Slot Capabilities Register is 0b, this bit is permitted to be read-only with a value of 0 b. <br> Default value of this bit is 0 b. | RW |
| 1 | Power Fault Detected Enable - When Set, this bit enables software notification on a power fault event (see § Section 6.7.3). <br> If a Power Controller that supports power fault detection is not implemented, this bit is permitted to be read-only with a value of 0 b. <br> Default value of this bit is 0 b. | RW |
| 2 | MRL Sensor Changed Enable - When Set, this bit enables software notification on a MRL sensor changed event (see § Section 6.7.3). <br> If the MRL Sensor Present bit in the Slot Capabilities Register is Clear, this bit is permitted to be read-only with a value of 0 b. <br> Default value of this bit is 0 b. | RW |
| 3 | Presence Detect Changed Enable - When Set, this bit enables software notification on a presence detect changed event (see § Section 6.7.3). <br> If the Hot-Plug Capable bit in the Slot Capabilities Register is 0b, this bit is permitted to be read-only with a value of 0 b. | RW |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 4 | Default value of this bit is 0 b. |  |
|  | Command Completed Interrupt Enable - If Command Completed notification is supported (if the No Command Completed Support bit in the Slot Capabilities Register is 0b), when Set, this bit enables software notification when a hot-plug command is completed by the Hot-Plug Controller. <br> If Command Completed notification is not supported, this bit must be hardwired to 0b. <br> Default value of this bit is 0 b . | RW |
| 5 | Hot-Plug Interrupt Enable - When Set, this bit enables generation of an interrupt on enabled hot-plug events. <br> If the Hot-Plug Capable bit in the Slot Capabilities Register is Clear, this bit is permitted to be read-only with a value of 0 b. <br> Default value of this bit is 0 b . | RW |
| 7:6 | Attention Indicator Control - If an Attention Indicator is implemented, writes to this field set the Attention Indicator to the written state. <br> Reads of this field must reflect the value from the latest write, even if the corresponding hot-plug command is not complete, unless software issues a write without waiting, if required to, for the previous command to complete in which case the read value is undefined. <br> Defined encodings are: | RW |
|  | 00b | Reserved |
|  | 01b | On |
|  | 10b | Blink |
|  | 11b | Off |
|  | Note: The default value of this field must be one of the non-Reserved values. If the Attention Indicator Present bit in the Slot Capabilities Register is 0b, this bit is permitted to be read-only with a value of 00b. | RW |
| 9:8 | Power Indicator Control - If a Power Indicator is implemented, writes to this field set the Power Indicator to the written state. Reads of this field must reflect the value from the latest write, even if the corresponding hot-plug command is not complete, unless software issues a write without waiting, if required to, for the previous command to complete in which case the read value is undefined. <br> Defined encodings are: | RW |
|  | 00b | Reserved |
|  | 01b | On |
|  | 10b | Blink |
|  | 11b | Off |
|  | Note: The default value of this field must be one of the non-Reserved values. If the Power Indicator Present bit in the Slot Capabilities Register is 0b, this bit is permitted to be read-only with a value of 00b. |  |
| 10 | Power Controller Control - If a Power Controller is implemented, this bit when written sets the power state of the slot per the defined encodings. Reads of this bit must reflect the value from the latest write, even if the corresponding hot-plug command is not complete, unless software issues a write, if required to, without waiting for the previous command to complete in which case the read value is undefined. <br> Note that in some cases the power controller may autonomously remove slot power or not respond to a power-up request based on a detected fault condition, independent of the Power Controller Control setting. <br> The defined encodings are: | RW |
|  | 0b | Power On |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | 1b Power Off <br> If the Power Controller Present bit in the Slot Capabilities Register is Clear, then writes to this bit have no effect and the read value of this bit is undefined. |  |
| 11 | Electromechanical Interlock Control - If an Electromechanical Interlock is implemented, a write of 1b to this bit causes the state of the interlock to toggle. A write of 0 b to this bit has no effect. A read of this bit always returns a 0 b. | RW |
| 12 | Data Link Layer State Changed Enable - If the Data Link Layer Link Active Reporting Capable is 1b, this bit enables software notification when Data Link Layer Link Active bit is changed. <br> If the Data Link Layer Link Active Reporting Capable bit is 0b, this bit is permitted to be read-only with a value of 0 b. <br> Default value of this bit is 0 b . | RW |
| 13 | Auto Slot Power Limit Disable - When Set, this disables the automatic sending of a Set_Slot_Power_Limit Message when a Link transitions from a non-DL_Up status to a DL_Up status. <br> Downstream Ports that don't support DPC are permitted to hardwire this bit to 0 . <br> Default value of this bit is implementation specific. | RW |
| 14 | In-Band PD Disable - When Set, this bit disables the in-band presence detect mechanism from affecting the Presence Detect State bit, allowing that bit to report out-of-band presence detect exclusively. Otherwise, the Presence Detect State bit reflects the logical OR of the in-band and out-of-band presence detect mechanisms. <br> In addition, the In-Band PD Disable bit governs the Component Presence state for the Downstream Component Presence field in the Link Status 2 Register. See § Section 7.5.3.20 . <br> This bit must be implemented if the In-Band PD Disable Supported bit is 1b. Otherwise, this bit must be hardwired to 0 b. <br> Default value of this bit is 0 b . | RW |

# 7.5.3.11 Slot Status Register (Offset 1Ah) $\S$ 

The Slot Status Register provides information about PCI Express Slot specific parameters. § Figure 7-32 details allocation of register fields in the Slot Status Register; § Table 7-29 provides the respective bit definitions. Register fields for status bits not implemented by the device have the RsvdZ attribute.

If this register is implemented but the Slot Implemented bit is Clear, the field behavior of this entire register with the exception of the Data Link Layer State Changed bit is undefined.

![img-30.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-30.jpeg)

Figure 7-32 Slot Status Register

Table 7-29 Slot Status Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 0 | Attention Button Pressed - If an Attention Button is implemented, this bit is Set when the attention button is pressed. If an Attention Button is not supported, this bit must not be Set. | RW1C |
| 1 | Power Fault Detected - If a Power Controller that supports power fault detection is implemented, this bit is Set when the Power Controller detects a power fault at this slot. Note that, depending on hardware capability, it is possible that a power fault can be detected at any time, independent of the Power Controller Control setting or the occupancy of the slot. If power fault detection is not supported, this bit must not be Set. | RW1C |
| 2 | MRL Sensor Changed - If an MRL sensor is implemented, this bit is Set when a MRL Sensor State change is detected. If an MRL sensor is not implemented, this bit must not be Set. | RW1C |
| 3 | Presence Detect Changed - This bit is Set when the value reported in the Presence Detect State bit is changed. | RW1C |
| 4 | Command Completed - If Command Completed notification is supported (if the No Command Completed Support bit in the Slot Capabilities Register is 0b), this bit is Set when a hot-plug command has completed and the Hot-Plug Controller is ready to accept a subsequent command. The Command Completed status bit is Set as an indication to host software that the Hot-Plug Controller has processed the previous command and is ready to receive the next command; it provides no guarantee that the action corresponding to the command is complete. <br> If Command Completed notification is not supported, this bit must be hardwired to 0b. | RW1C |
| 5 | MRL Sensor State - This bit reports the status of the MRL sensor if implemented. <br> Defined encodings are: <br> 0b MRL Closed <br> 1b MRL Open | RO |
| 6 | Presence Detect State - This bit indicates the presence of an adapter in the slot. When the In-Band PD Disable bit is Clear, this is reflected by the logical "OR" of the Physical Layer in-band presence detect | RO |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | mechanism and, if present, any out-of-band presence detect mechanism defined for the slot's corresponding form factor. Note that the in-band presence detect mechanism requires that power be applied to an adapter for its presence to be detected. Consequently, form factors that require a power controller for hot-plug must implement an out-of-band presence detect mechanism. When the In-Band PD Disable bit is Set, the in-band presence detect mechanism has no effect on this bit. |  |
|  | Defined encodings are: |  |
|  | 0b Adapter not Present |  |
|  | 1b Adapter Present |  |
|  | This bit must be implemented on all Downstream Ports that implement slots. For Downstream Ports not connected to slots (where the Slot Implemented bit of the PCI Express Capabilities Register is 0b), this bit must be hardwired to 1 b . |  |
| 7 | Electromechanical Interlock Status - If an Electromechanical Interlock is implemented, this bit indicates the status of the Electromechanical Interlock. | RO |
|  | Defined encodings are: |  |
|  | 0b Electromechanical Interlock Disengaged |  |
|  | 1b Electromechanical Interlock Engaged |  |
| 8 | Data Link Layer State Changed - This bit is Set when the value reported in the Data Link Layer Link Active bit of the Link Status Register is changed. | RW1C |
|  | In response to a Data Link Layer State Changed event, software must read the Data Link Layer Link Active bit of the Link Status Register to determine if the Link is active before initiating configuration cycles to the hot plugged device. |  |

# IMPLEMENTATION NOTE: NO SLOT POWER CONTROLLER 

For slots that do not implement a power controller, software must ensure that system power planes are enabled to provide power to slots prior to reading Presence Detect State.

### 7.5.3.12 Root Control Register (Offset 1Ch)

The Root Control Register controls PCI Express Root Complex specific parameters. § Figure 7-33 details allocation of register fields in the Root Control Register; § Table 7-30 provides the respective bit definitions.

![img-31.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-31.jpeg)

Figure 7-33 Root Control Register

Table 7-30 Root Control Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 0 | System Error on Correctable Error Enable - If Set, this bit indicates that a System Error should be generated if a correctable error (ERR_COR) is reported by any of the devices in the Hierarchy Domain associated with this Root Port, or by the Root Port itself. The mechanism for signaling a System Error to the system is system specific. <br> Root Complex Event Collectors provide support for the above-described functionality for RCIEPs. <br> Default value of this bit is Ob. | RW |
| 1 | System Error on Non-Fatal Error Enable - If Set, this bit indicates that a System Error should be generated if a Non-fatal error (ERR_NONFATAL) is reported by any of the devices in the Hierarchy Domain associated with this Root Port, or by the Root Port itself. The mechanism for signaling a System Error to the system is system specific. <br> Root Complex Event Collectors provide support for the above-described functionality for RCIEPs. <br> Default value of this bit is Ob. | RW |
| 2 | System Error on Fatal Error Enable - If Set, this bit indicates that a System Error should be generated if a Fatal error (ERR_FATAL) is reported by any of the devices in the Hierarchy Domain associated with this Root Port, or by the Root Port itself. The mechanism for signaling a System Error to the system is system specific. <br> Root Complex Event Collectors provide support for the above-described functionality for RCIEPs. <br> Default value of this bit is Ob. | RW |
| 3 | PME Interrupt Enable - When Set, this bit enables PME interrupt generation upon receipt of a PME Message as reflected in the PME Status bit (see § Table 7-32). A PME interrupt is also generated if the PME Status bit is Set when this bit is changed from Clear to Set (see § Section 5.3.3). <br> Default value of this bit is Ob. | RW |
| 4 | Configuration RRS Software Visibility Enable - When Set, this bit enables the Root Port to indicate to software when Request Retry Status (RRS) Completion Status is received in response to a Configuration Request (see § Section 2.3.1). <br> Root Ports that do not implement this capability must hardwire this bit to Ob. <br> Default value of this bit is Ob. | RW |

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 5 | No NFM Subtree Below This Root Port - When Clear, indicates that the RC must take ownership of <br> non-UIO Non-Posted Requests passing peer-to-peer through the RC targeting this RP as the Egress Port. <br> It is strongly recommended that system software Set this bit if it is determined that no NFM subtree(s) <br> exist below this Root Port. RC implementations are strongly recommended to avoid taking ownership <br> when not required to do so. <br> Root Ports must handle the Clearing of this bit without disruption to Non-Posted Requests the RC has <br> taken ownership of. <br> Root Ports that do not implement this capability must hardwire this bit to 0b. <br> Default value of this bit is 0b. | RW |

# 7.5.3.13 Root Capabilities Register (Offset 1Eh) 

The Root Capabilities Register identifies PCI Express Root Port specific capabilities. § Figure 7-34 details allocation of register fields in the Root Capabilities Register; § Table 7-31 provides the respective bit definitions.
![img-32.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-32.jpeg)

Figure 7-34 Root Capabilities Register

Table 7-31 Root Capabilities Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 0 | Configuration RRS Software Visibility - When Set, this bit indicates that the Root Port is capable of <br> indicating to software when Request Retry Status (RRS) Completion Status is received in response to a <br> Configuration Request (see § Section 2.3.1). | RO |

### 7.5.3.14 Root Status Register (Offset 20h)

The Root Status Register provides information about PCI Express device specific parameters. § Figure 7-35 details allocation of register fields in the Root Status Register; § Table 7-32 provides the respective bit definitions.

![img-33.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-33.jpeg)

Figure 7-35 Root Status Register

Table 7-32 Root Status Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $15: 0$ | PME Requester ID - This field indicates the PCI Requester ID of the last PME Requester. This field is only valid when the PME Status bit is Set. | RO |
| 16 | PME Status - This bit indicates that PME was asserted by the PME Requester indicated in the PME Requester ID field. Subsequent PMEs are kept pending until the status register is cleared by software by writing a 1b. <br> Default value of this bit is 0 b. | RW1C |
| 17 | PME Pending - This bit indicates that another PME is pending when the PME Status bit is Set. When the PME Status bit is cleared by software; the PME is delivered by hardware by setting the PME Status bit again and updating the PME Requester ID field appropriately. The PME Pending bit is cleared by hardware if no more PMEs are pending. | RO |

# 7.5.3.15 Device Capabilities 2 Register (Offset 24h) 

![img-34.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-34.jpeg)

Figure 7-36 Device Capabilities 2 Register

Table 7-33 Device Capabilities 2 Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 3:0 | Completion Timeout Ranges Supported - This field indicates device Function support for the optional Completion Timeout programmability mechanism. This mechanism allows system software to modify the Completion Timeout Value. <br> This field is applicable only to Root Ports, Endpoints that issue Non-Posted Requests on their own behalf, and PCI Express to PCI/PCI-X Bridges that take ownership of Non-Posted Requests issued on PCI Express. For all other Functions this field is Reserved and must be hardwired to 0000b. <br> Four time value ranges are defined (A, B, C, D), each with two selectable sub-ranges (for which the time ranges are defined in the description of the Completion Timeout Value field in the Device Control 2 register): <br> The value in this field indicates the timeout value ranges supported: | HwInit |
|  | 0000b | Completion Timeout programming not supported - See $\S$ Section 2.8 for requirements. |
|  | 0001b | Range A |
|  | 0010b | Range B |
|  | 0011b | Ranges A and B |
|  | 0110b | Ranges B and C |
|  | 0111b | Ranges A, B, and C |
|  | 1110b | Ranges B, C, and D |
|  | 1111b | Ranges A, B, C, and D |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 4 | All other values are Reserved. <br> For VFs, this field value must be identical to the associated PF's field value. |  |
|  | Completion Timeout Disable Supported - A value of 1b indicates support for the Completion Timeout Disable mechanism. <br> The Completion Timeout Disable mechanism is required for Endpoints that issue Non-Posted Requests on their own behalf and PCI Express to PCI/PCI-X Bridges that take ownership of Non-Posted Requests issued on PCI Express. <br> For VFs, this bit value must be identical to the associated PF's bit value. <br> This mechanism is optional for Root Ports. <br> For all other Functions this field is Reserved and must be hardwired to 0b. | RO |
| 5 | ARI Forwarding Supported - Applicable only to Switch Downstream Ports and Root Ports; must be 0 b for other Function types. This bit must be set to 1 b if a Switch Downstream Port or Root Port supports this optional capability. See $\S$ Section 6.13 for additional details. | RO |
| 6 | AtomicOp Routing Supported - Applicable only to Switch Upstream Ports, Switch Downstream Ports, and Root Ports; must be 0b for other Function types. This bit must be set to 1b if the Port supports this optional capability. See $\S$ Section 6.15 for additional details. | RO |
| 7 | 32-bit AtomicOp Completer Supported - Applicable to Functions with Memory Space BARs as well as all Root Ports; must be 0b otherwise. Includes FetchAdd, Swap, and CAS AtomicOps. This bit must be set to 1 b if the Function supports this optional capability. See $\S$ Section 6.15.3.1 for additional RC requirements. <br> For VFs, this bit value must be identical to the associated PF's bit value. | RO |
| 8 | 64-bit AtomicOp Completer Supported - Applicable to Functions with Memory Space BARs as well as all Root Ports; must be 0b otherwise. Includes FetchAdd, Swap, and CAS AtomicOps. This bit must be set to 1 b if the Function supports this optional capability. See $\S$ Section 6.15.3.1 for additional RC requirements. <br> For VFs, this bit value must be identical to the associated PF's bit value. | RO |
| 9 | 128-bit CAS Completer Supported - Applicable to Functions with Memory Space BARs as well as all Root Ports; must be 0b otherwise. This bit must be set to 1 b if the Function supports this optional capability. See $\S$ Section 6.15 for additional details. <br> For VFs, this bit value must be identical to the associated PF's bit value. | RO |
| 10 | No RO-enabled PR-PR Passing - If this bit is Set, the routing element never carries out the passing permitted by $\S$ Table 2-42 entry A2b that is associated with the Relaxed Ordering Attribute field being Set. <br> This bit applies only for Switches and RCs that support peer-to-peer traffic between Root Ports. This bit applies only to Posted Requests being forwarded through the Switch or RC and does not apply to traffic originating or terminating within the Switch or RC itself. All Ports on a Switch or RC must report the same value for this bit. <br> For all other functions, this bit must be 0b. | Hwinit |
| 11 | LTR Mechanism Supported - A value of 1b indicates support for the optional Latency Tolerance Reporting (LTR) mechanism. <br> Root Ports, Switches and Endpoints are permitted to implement this capability. <br> For a Multi-Function Device associated with an Upstream Port, each Function must report the same value for this bit. | RO |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 13:12 | For Bridges and other Functions that do not implement this capability, this bit must be hardwired to 0 b. |  |
|  | TPH Completer Supported - Value indicates Completer support for TPH or Extended TPH. Applicable only to Root Ports and Endpoints. For all other Functions, this field is Reserved. <br> Defined Encodings are: <br> 00b TPH and Extended TPH Completer not supported. <br> 01b TPH Completer supported; Extended TPH Completer not supported. <br> 10b Reserved. <br> 11b Both TPH and Extended TPH Completer supported. <br> See § Section 6.17 for details. | RO |
| 15:14 | Undefined-formerly used for Lightweight Notification (LN), which is now deprecated | RO |
| 16 | 10-Bit Tag Completer Supported - If this bit is Set, the Function supports 10-Bit Tag Completer capability; otherwise, the Function does not. See § Section 2.2.6.2 . <br> For VFs, this bit value must be identical to the associated PF's bit value. | HwInit |
| 17 | 10-Bit Tag Requester Supported - If this bit is Set, the Function supports 10-Bit Tag Requester capability; otherwise, the Function does not. <br> This bit must not be Set if the 10-Bit Tag Completer Supported bit is Clear. <br> If the Function is an RCIEP, this bit must be Clear if the RC does not support 10-Bit Tag Completer capability for Requests coming from this RCIEP. <br> For VFs, this bit value must equal the VF 10-Bit Tag Requester Supported bit value in the SR-IOV Capabilities Register. <br> Note that 10-Bit Tag field generation must be enabled by the 10-Bit Tag Requester Enable bit in the Device Control 2 Register of the Requester Function before 10-Bit Tags can be generated by the Requester. See § Section 2.2.6.2 . | HwInit |
| 19:18 | OBFF Supported - This field indicates if OBFF is supported and, if so, what signaling mechanism is used. <br> 00b OBFF Not Supported <br> 01b OBFF supported using Message signaling only <br> 10b OBFF supported using WAKE\# signaling only <br> 11b OBFF supported using WAKE\# and Message signaling <br> The value reported in this field must indicate support for WAKE\# signaling only if: <br> - for a Downstream Port, driving the WAKE\# signal for OBFF is supported and the connector or component connected Downstream is known to receive that same WAKE\# signal <br> - for an Upstream Port, receiving the WAKE\# signal for OBFF is supported and, if the component is on an add-in-card, that the component is connected to the WAKE\# signal on theconnector. <br> Root Ports, Switch Ports, and Endpoints are permitted to implement this capability. <br> For a Multi-Function Device associated with an Upstream Port, each Function must report the same value for this field. <br> For Bridges and Ports that do not implement this capability, this field must be hardwired to 00b. | HwInit |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 20 | Extended Fmt Field Supported - If Set, the Function supports the 3-bit definition of the Fmt field when operating in Non-Flit Mode. If Clear, the Function supports a 2-bit definition of the Fmt field. See § Section 2.2 . <br> Must be Set for Functions that support End-End TLP Prefixes (NFM) or OHC-E (FM). All Functions in an Upstream Port must have the same value for this bit. Each Downstream Port of a component may have a different value for this bit. <br> MUST@FLIT be Set. | RO |
| 21 | End-End TLP Prefix Supported - Indicates whether End-End TLP Prefix support (NFM) / OHC-E (FM) is offered by a Function. Values are: <br> 0b No Support <br> 1b Support is provided to receive TLPs containing End-End TLP Prefixes (NFM) and optionally OHC-E (FM). <br> All Ports of a Switch must have the same value for this bit. <br> The definition of this bit is ambiguous for designs that choose only to support End-End TLP Prefixes in NFM and do not support OHC-E in FM. This bit is static and does not change value with current link operation (FM vs. NFM). Software cannot rely on this bit to infer if OHC-E is support by a Function. <br> The definition of this bit is also ambiguous for RPs that choose to support End-End TLP Prefixes (NFM) / OHC-E (FM) as a terminus only without forwarding. Software cannot rely on this bit to infer if End-End TLP Prefix forwarding / OHC-E forwarding is supported in a RP or not. | HwInit |
| 23:22 | Max End-End TLP Prefixes - Indicates the maximum number of End-End TLP Prefixes supported by this Function (NFM) or the maximum size of OHC-E supported (FM). See § Section 2.2.10.4 for important details. Values are: <br> 01b 1 End-End TLP Prefix / OHC-E1 <br> 10b 2 End-End TLP Prefixes / OHC-E2 <br> 11b 3 End-End TLP Prefixes / OHC-E4 <br> 00b 4 End-End TLP Prefixes / OHC-E4 <br> If End-End TLP Prefix Supported is Clear, this field is RsvdP. <br> Different Root Ports that have the End-End TLP Prefix Supported bit Set are permitted to report different values for this field. <br> For Switches where End-End TLP Prefix Supported is Set, this field must be 00b indicating support for up to four End-End TLP Prefixes. <br> The definition of this bit is ambiguous for designs that only chose to support End-End TLP Prefixes in NFM and do not support OHC-E in FM. This bit is static and does not change value based on current link operation (FM vs. NFM). Refer to § Section 2.2.11 for how hardware must handle received TLPs with OHC-E in the scenario that they don't support it. | HwInit |
| 25:24 | Emergency Power Reduction Supported - Indicates support level of the optional Emergency Power Reduction State feature. A Function can enter Emergency Power Reduction State autonomously, or based on one of two mechanisms defined by the associated Form Factor Specification. Functions that are in the Emergency Power Reduction State consume less power. The Emergency Power Reduction mechanism permits a chassis to request add-in cards to rapidly enter Emergency Power Reduction State without involving system software. See § Section 6.24 for additional details. <br> Values are: <br> 00b Emergency Power Reduction State not supported <br> 01b Emergency Power Reduction State is supported and is triggered by Device Specific mechanism(s) | HwInit |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | 10b Emergency Power Reduction State is supported and is triggered either by the mechanism defined in the corresponding Form Factor specification or by Device Specific mechanism(s) |  |
|  | 11b | Reserved |
|  | This field is RsvdP in Functions that are not associated with an Upstream Port. |  |
|  | For Multi-Function Devices associated with an Upstream Port, all Functions that report a non-Zero value for this field, must report the same non-Zero value for this field. |  |
|  | For VFs, this field value must be identical to the associated PF's field value. |  |
|  | Default value is 00 b. |  |
|  | After reset, once this field returns a non-Zero value, it must continue to return the same non-Zero value, until the next reset. |  |
| 26 | Emergency Power Reduction Initialization Required - If Set, the Function requires complete or partial initialization upon exit from the Emergency Power Reduction State. If Clear, the Function requires no software intervention to return to normal operation upon exit from the Emergency Power Reduction State. See § Section 6.24 for additional details. | Hwinit |
|  | For Multi-Function Devices associated with an Upstream Port, all Functions must report the same value for this bit. |  |
|  | For VFs, this bit value must be identical to the associated PF's bit value. |  |
|  | This bit is RsvdP in Functions that are not associated with an Upstream Port. |  |
|  | Default value is 0 b. |  |
|  | After reset, when this field returns a non-Zero value, it must continue to return the same non-Zero value. |  |
| 28 | DMWr Complete Supported - Applicable to Functions with Memory Space BARs as well as all Root Ports; This bit must be Set if the Function can serve as a DMWr Completer. See § Section 6.32 for additional details. | Hwinit |
| 30:29 | DMWr Lengths Supported - Applicable to Functions with either the DMWr Request Routing Supported bit Set or the DMWR Completer Supported bit Set (or both). This field indicates the largest DMWr TLP that this Function can receive. | Hwinit/RsvdP |
|  | Defined Encodings are: |  |
|  | 00b DMWr TLPs up to 64 bytes are supported |  |
|  | 01b DMWr TLPs up to 128 bytes are supported |  |
|  | 10b | Reserved |
|  | 11b | Reserved |
|  | When applicable, all Functions in a Multi-Function Device associated with an Upstream Port must report the same value in this field. |  |
|  | This field is RsvdP if both DMWr Completer Supported and DMWr Request Routing Supported are Clear. |  |
| 31 | FRS Supported - When Set, indicates support for the optional Function Readiness Status (FRS) capability. <br> Must be Set for all Functions that support generation or reception capabilities of FRS Messages. <br> Must not be Set by Switch Functions that do not generate FRS Messages on their own behalf. | Hwinit |

# IMPLEMENTATION NOTE: USE OF THE NO RO-ENABLED PR-PR PASSING BIT 

The No RO-enabled PR-PR Passing bit allows platforms to utilize PCI Express switching elements on the path between a requester and completer for requesters that could benefit from a slightly less relaxed ordering model. An example is a device that cannot ensure that multiple overlapping posted writes to the same address are outstanding at the same time. The method by which such a device is enabled to utilize this mode is beyond the scope of this specification.

### 7.5.3.16 Device Control 2 Register (Offset 28h)

![img-35.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-35.jpeg)

Figure 7-37 Device Control 2 Register

Table 7-34 Device Control 2 Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 3:0 | Completion Timeout Value - In device Functions that support Completion Timeout programmability, this field allows system software to modify the Completion Timeout Value. <br> This field is applicable to Root Ports, Endpoints that issue Non-Posted Requests on their own behalf, and PCI Express to PCI/PCI-X Bridges that take ownership of Non-Posted Requests issued on PCI Express. For VFs, the associated PF's value applies, and this field must be RsvdP. For all other Functions, this field must be hardwired to Zero. <br> A Function that does not support this optional capability must hardwire this field to 0000b. Functions that support Completion Timeout programmability must support the values given below corresponding to the programmability ranges indicated in the Completion Timeout Ranges Supported field. | RW <br> VF RsvdP |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | Defined encodings: |  |
|  | 0000b Default range: $50 \mu \mathrm{~s}$ to 50 ms ; the Function MUST@FLIT implement a timeout value in the range 40 ms to 50 ms . <br> For Functions that do not support Flit Mode, it is strongly recommended that the Completion Timeout mechanism not expire in less than 10 ms . <br> Values available if Range A is supported: |  |
|  | 0001b $50 \mu \mathrm{~s}$ to $100 \mu \mathrm{~s}$ |  |
|  | 0010b 1 ms to 10 ms |  |
|  | Values available if Range B is supported: |  |
|  | 0101b 16 ms to 55 ms ; MUST@FLIT 40 ms to 55 ms |  |
|  | 0110b 65 ms to 210 ms |  |
|  | Values available if Range C is supported: |  |
|  | 1001b 260 ms to 900 ms |  |
|  | 1010b 1 s to 3.5 s |  |
|  | Values available if the Range D is supported: |  |
|  | 1101b 4 s to 13 s |  |
|  | 1110b 17 s to 64 s |  |
|  | Values not defined above are Reserved. <br> Software is permitted to change the value in this field at any time. For Requests already pending when the Completion Timeout Value is changed, hardware is permitted to use either the new or the old value for the outstanding Requests, and is permitted to base the start time for each Request either on when this value was changed or on when each request was issued. <br> The default value for this field is 0000 b . |  |
| 4 | Completion Timeout Disable - When Set, this bit disables the Completion Timeout mechanism. <br> For non-VFs, this bit is required for all Functions that support the Completion Timeout Disable capability. For VFs, the associated PF's value applies, and this field must be RsvdP. Otherwise, Functions that do not support this optional capability are permitted to hard wire this bit to Zero. Software is permitted to Set or Clear this bit at any time. When Set, the Completion Timeout detection mechanism is disabled. If there are outstanding Requests when the bit is cleared, it is permitted but not required for hardware to apply the completion timeout mechanism to the outstanding Requests. If this is done, it is permitted to base the start time for each Request on either the time this bit was cleared or the time each Request was issued. <br> The default value for this bit is 0 b . | RW <br> VF RsvdP |
| 5 | ARI Forwarding Enable - When set, the Downstream Port disables its traditional Device Number field being 0 enforcement when turning a Type 1 Configuration Request into a Type 0 Configuration Request, permitting access to Extended Functions in an ARI Device immediately below the Port. See $\S$ Section 6.13 . <br> Default value of this bit is 0 b . Must be hardwired to 0 b if the ARI Forwarding Supported bit is 0 b . This bit is not applicable and Reserved for Upstream Ports. | RW / RsvdP |
| 6 | AtomicOp Requester Enable - Applicable only to Endpoints and Root Ports; must be hardwired to 0b for other Function types. For Endpoints, the Function is allowed to initiate AtomicOp Requests only if this bit and the Bus Master Enable bit in the Command register are both Set. For Root Ports, the CPU is allowed to initiate AtomicOp Requests on this Link only when this bit is Set and AtomicOp Egress Blocking is Clear (see § Section 6.15). | RW <br> VF RsvdP |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | For VFs, the associated PF's value applies, and this bit must be RsvdP. For non-VFs, this bit is required to be RW if the Endpoint or Root Port is capable of initiating AtomicOp Requests, but otherwise is permitted to be hardwired to Zero. <br> This bit does not serve as a capability bit. This bit is permitted to be RW even if no AtomicOp Requester capabilities are supported by the Endpoint or Root Port. <br> Default value of this bit is Ob. |  |
| 7 | AtomicOp Egress Blocking - Applicable and mandatory for Switch Upstream Ports, Switch Downstream Ports, and Root Ports that implement AtomicOp routing capability; otherwise must be hardwired to 0 b . <br> When this bit is Set, AtomicOp Requests that target going out this Egress Port must be blocked. See $\S$ Section 6.15.2 . <br> Default value of this bit is Ob. | RW |
| 8 | IDO Request Enable - If this bit is Set, the Function is permitted to set the ID-Based Ordering (IDO) bit (Attr[2]) of Requests it initiates (see § Section 2.2.6.3 and § Section 2.4). <br> Endpoints, including RC Integrated Endpoints, and Root Ports are permitted to implement this capability. <br> For VFs, the associated PF's value applies, and this bit must be RsvdP. Otherwise, a Function is permitted to hardwire this bit to Zero if it never sets the IDO attribute in Requests. <br> Default value of this bit is Ob. | RW <br> VF RsvdP |
| 9 | IDO Completion Enable - If this bit is Set, the Function is permitted to set the ID-Based Ordering (IDO) bit (Attr[2]) of Completions it returns (see § Section 2.2.6.3 and § Section 2.4). <br> Endpoints, including RC Integrated Endpoints, and Root Ports are permitted to implement this capability. <br> For VFs, the associated PF's value applies, and this bit must be RsvdP. Otherwise, a Function is permitted to hardwire this bit to Zero if it never sets the IDO attribute in Completions. <br> Default value of this bit is Ob. | RW <br> VF RsvdP |
| 10 | LTR Mechanism Enable - When Set to 1b, this bit enables Upstream Ports to send LTR messages and Downstream Ports to process LTR Messages. <br> For a Multi-Function Device associated with an Upstream Port of a device that implements LTR, the bit in Function 0 is RW, and only Function 0 controls the component's Link behavior. In all other Functions of that device, this bit is RsvdP. <br> Functions that do not implement the LTR mechanism are permitted to hardwire this bit to Ob. <br> Default value of this bit is Ob. <br> For Downstream Ports, this bit must be reset to the default value if the Port goes to DL_Down status. | RW/RsvdP |
| 11 | Emergency Power Reduction Request - If Set, all Functions in the component that support Emergency Power Reduction State must enter the Emergency Power Reduction State. If Clear these Functions must exit the Emergency Power Reduction State if no other reasons exist to preclude exiting this state. See § Section 6.24 for additional details. <br> This bit is implemented in the lowest numbered (non-VF) Function associated with an Upstream Port that has a non-Zero value in the Emergency Power Reduction Supported field. This bit is RsvdP in all other Functions, including VFs. <br> Default is Ob. | RW/RsvdP <br> VF RsvdP |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 12 | 10-Bit Tag Requester Enable - This bit, in combination with the Extended Tag Field Enable bit and the 14-Bit Tag Requester Enable bit, determines how many Tag field bits a Requester is permitted to use. When the 10-Bit Tag Requester Enable bit is Set, the Requester is permitted to use 10-Bit Tags for non-UIO Requests. See § Section 2.2.6.2 for complete details. <br> If software changes the value of this bit while the Function has outstanding Non-Posted Requests, the result is undefined. <br> For VFs, the value in the VF 10-Bit Tag Requester Enable bit in the associated PF's SR-IOV Control Register applies, and this bit must be RsvdP. <br> Non-VF Functions that do not implement 10-Bit Tag Requester capability are permitted to hardwire this bit to Zero. <br> Default value of this bit is 0 b . | RW <br> VF RsvdP |
| 14:13 | OBFF Enable - This field enables the OBFF mechanism and selects the signaling method. <br> 00b <br> 01b <br> 10b <br> 11b <br> See § Section 6.19 for an explanation of the above encodings. <br> This field is required for all Ports that support the OBFF Capability. <br> For a Multi-Function Device associated with an Upstream Port of a Device that implements OBFF, the field in Function 0 is of type RW, and only Function 0 controls the Component's behavior. In all other Functions of that Device, this field is of type RsvdP. <br> Ports that do not implement OBFF are permitted to hardwire this field to 00 b. <br> Default value of this field is 00 b . | RW/RsvdP (see description) |
| 15 | End-End TLP Prefix Blocking - Controls whether the routing function is permitted to forward TLPs containing an End-End TLP Prefix (NFM) / OHC-E (FM). Values are: <br> 0b <br> 1b <br> 1b <br> 1b <br> 1b <br> 1b <br> 1b <br> 1b <br> 1b <br> 1b <br> 1b <br> 1b <br> 1b <br> 1b <br> 1b <br> in all other cases. | ```RW (see description)``` |

# 7.5.3.17 Device Status 2 Register (Offset 2Ah) 

This section is a placeholder. There are no capabilities that require this register.

This register must be treated by software as RsvdZ.

# 7.5.3.18 Link Capabilities 2 Register (Offset 2Ch) 

![img-36.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-36.jpeg)

Figure 7-38 Link Capabilities 2 Register

Table 7-35 Link Capabilities 2 Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 7:1 | Supported Link Speeds Vector - This field indicates the supported Link speed(s) of the associated Port. For each bit, a value of 1 b indicates that the corresponding Link speed is supported; otherwise, the Link speed is not supported. See $\S$ Section 8.2.1 for further requirements. <br> Bit definitions within this field are: <br> Bit 0 $\quad 2.5 \mathrm{GT} / \mathrm{s}$ <br> Bit 1 $\quad 5.0 \mathrm{GT} / \mathrm{s}$ <br> Bit 2 $\quad 8.0 \mathrm{GT} / \mathrm{s}$ <br> Bit 3 $\quad 16.0 \mathrm{GT} / \mathrm{s}$ <br> Bit 4 $\quad 32.0 \mathrm{GT} / \mathrm{s}$ <br> Bit 5 $\quad 64.0 \mathrm{GT} / \mathrm{s}$ <br> Bit 6 RsvdP <br> Multi-Function Devices associated with an Upstream Port must report the same value in this field for all Functions. | Hwinit/RsvdP |
| 8 | Crosslink Supported - When set to 1b, this bit indicates that the associated Port supports crosslinks (see $\S$ Section 4.2.7.3.1). When set to 0 b on a Port that supports Link speeds of $8.0 \mathrm{GT} / \mathrm{s}$ or higher, this bit indicates that the associated Port does not support crosslinks. When set to 0 b on a Port that only supports Link speeds of $2.5 \mathrm{GT} / \mathrm{s}$ or $5.0 \mathrm{GT} / \mathrm{s}$, this bit provides no information regarding the Port's level of crosslink support. <br> It is recommended that this bit be Set in any Port that supports crosslinks even though doing so is only required for Ports that also support operating at $8.0 \mathrm{GT} / \mathrm{s}$ or higher Link speeds. <br> Note: Software should use this bit when referencing fields whose definition depends on whether or not the Port supports crosslinks (see § Section 7.7.3.4). <br> Multi-Function Devices associated with an Upstream Port must report the same value in this field for all Functions. | RO |
| 15:9 | Lower SKP OS Generation Supported Speeds Vector - If this field is non-Zero, it indicates that the Port, when operating at the indicated speed(s) supports SRIS and also supports software control of the SKP Ordered Set transmission scheduling rate. | Hwinit/RsvdP |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | Bit definitions within this field are: |  |
|  | Bit 0 | $2.5 \mathrm{GT} / \mathrm{s}$ |
|  | Bit 1 | $5.0 \mathrm{GT} / \mathrm{s}$ |
|  | Bit 2 | $8.0 \mathrm{GT} / \mathrm{s}$ |
|  | Bit 3 | $16.0 \mathrm{GT} / \mathrm{s}$ |
|  | Bit 4 | $32.0 \mathrm{GT} / \mathrm{s}$ |
|  | Bit 5 | $64.0 \mathrm{GT} / \mathrm{s}$ |
|  | Bit 6 | RsvdP |
|  | Multi-Function Devices associated with an Upstream Port must report the same value in this field for all Functions. <br> Behavior is undefined if a bit is Set in this field and the corresponding bit is not Set in the Supported Link Speeds Vector. |  |
| 22:16 | Lower SKP OS Reception Supported Speeds Vector - If this field is non-Zero, it indicates that the Port, when operating at the indicated speed(s) supports SRIS and also supports receiving SKP OS at the rate defined for SRNS while running in SRIS. <br> Bit definitions within this field are: | HwInit/RsvdP |
|  | Bit 0 | $2.5 \mathrm{GT} / \mathrm{s}$ |
|  | Bit 1 | $5.0 \mathrm{GT} / \mathrm{s}$ |
|  | Bit 2 | $8.0 \mathrm{GT} / \mathrm{s}$ |
|  | Bit 3 | $16.0 \mathrm{GT} / \mathrm{s}$ |
|  | Bit 4 | $32.0 \mathrm{GT} / \mathrm{s}$ |
|  | Bit 5 | $64.0 \mathrm{GT} / \mathrm{s}$ |
|  | Bit 6 | RsvdP |
|  | Multi-Function Devices associated with an Upstream Port must report the same value in this field for all Functions. <br> Behavior is undefined if a bit is Set in this field and the corresponding bit is not Set in the Supported Link Speeds Vector. |  |
| 23 | Retimer Presence Detect Supported - When set to 1b, this bit indicates that the associated Port supports detection and reporting of Retimer presence. <br> This bit MUST@FLIT be Set. <br> This bit must be set to 1 b in a Port when the Supported Link Speeds Vector of the Link Capabilities 2 Register indicates support for a Link speed of $16.0 \mathrm{GT} / \mathrm{s}$ or higher. <br> It is permitted to be set to 1 b regardless of the supported Link speeds. <br> Multi-Function Devices associated with an Upstream Port must report the same value in this field for all Functions. | HwInit/RsvdP |
| 24 | Two Retimers Presence Detect Supported - When set to 1b, this bit indicates that the associated Port supports detection and reporting of two Retimers presence. <br> This bit MUST@FLIT be Set. <br> This bit must be set to 1 b in a Port when the Supported Link Speeds Vector of the Link Capabilities 2 Register indicates support for a Link speed of $16.0 \mathrm{GT} / \mathrm{s}$ or higher. <br> It is permitted to be set to 1 b regardless of the supported Link speeds if the Retimer Presence Detect Supported bit is also set to 1b. | HwInit/RsvdP |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | Multi-Function Devices associated with an Upstream Port must report the same value in this field for <br> all Functions. |  |
| 31 | DRS Supported - When Set, indicates support for the optional Device Readiness Status (DRS) <br> capability. <br> Must be Set in Downstream Ports that support DRS. <br> Must be Set in Downstream Ports that support FRS. <br> For Upstream Ports that support DRS, this bit MUST@FLIT be Set in Function 0. For all other <br> Functions associated with an Upstream Port, this bit must be Clear. ${ }^{173}$ <br> Must be Clear in Functions that are not associated with a Port. <br> RsvdP in all other Functions. | HwInit/RsvdP |

# IMPLEMENTATION NOTE: 

## SOFTWARE MANAGEMENT OF LINK SPEEDS WITH EARLIER HARDWARE

Hardware components compliant to versions prior to [PCIe-3.0] either did not implement the Link Capabilities 2 Register, or the register was Reserved.

For software to determine the supported Link speeds for components where the Link Capabilities 2 Register is either not implemented, or the value of its Supported Link Speeds Vector is 0000000 b , software can read bits 3:0 of the Link Capabilities Register (now defined to be the Max Link Speed field), and interpret the value as follows:

0001b
$2.5 \mathrm{GT} / \mathrm{s}$ Link speed supported

0010b
$5.0 \mathrm{GT} / \mathrm{s}$ and $2.5 \mathrm{GT} / \mathrm{s}$ Link speeds supported
For such components, the encoding of the values for the Current Link Speed field (in the Link Status Register) and Target Link Speed field (in the Link Control 2 Register) is the same as above.

## IMPLEMENTATION NOTE: <br> SOFTWARE MANAGEMENT OF LINK SPEEDS WITH FUTURE HARDWARE

It is strongly encouraged that software primarily utilize the Supported Link Speeds Vector instead of the Max Link Speed field, so that software can determine the exact set of supported speeds on current and future hardware. This can avoid software being confused if a future specification defines Links that do not require support for all slower speeds.

# 7.5.3.19 Link Control 2 Register (Offset 30h) 

![img-37.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-37.jpeg)

Figure 7-39 Link Control 2 Register

Table 7-36 Link Control 2 Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 3:0 | Target Link Speed - For Downstream Ports, this field sets an upper limit on Link operational speed by restricting the values advertised by the Upstream component in its training sequences. <br> The encoded value specifies a Bit Location in the Supported Link Speeds Vector (in the Link Capabilities 2 Register) that corresponds to the desired target Link speed. <br> Defined encodings are: | RWS/RsvdP (see description) |
|  | 0001b Supported Link Speeds Vector field bit 0 |  |
|  | 0010b Supported Link Speeds Vector field bit 1 |  |
|  | 0011b Supported Link Speeds Vector field bit 2 |  |
|  | 0100b Supported Link Speeds Vector field bit 3 |  |
|  | 0101b Supported Link Speeds Vector field bit 4 |  |
|  | 0110b Supported Link Speeds Vector field bit 5 |  |
|  | 0111b Supported Link Speeds Vector field bit 6 |  |
|  | Others All other encodings are Reserved. |  |
|  | If a value is written to this field that does not correspond to a supported speed (as indicated by the Supported Link Speeds Vector), the result is undefined. |  |
|  | If either of the Enter Compliance or Enter Modified Compliance bits are implemented, then this field must also be implemented. |  |
|  | The default value of this field is the highest Link speed supported by the component (as reported in the Max Link Speed field of the Link Capabilities Register) unless the corresponding platform/form factor requires a different default value. |  |
|  | For both Upstream and Downstream Ports, this field is used to set the target compliance mode speed when software is using the Enter Compliance bit to force a Link into compliance mode. |  |
|  | For Upstream Ports, if the Enter Compliance bit is Clear, this field is permitted to have no effect. |  |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | For a Multi-Function Device associated with an Upstream Port, the field in Function 0 is of type RWS, and only Function 0 controls the component's Link behavior. In all other Functions of that device, this field is of type RsvdP. <br> Components that support only the $2.5 \mathrm{GT} / \mathrm{s}$ speed are permitted to hardwire this field to 0000 b . |  |
| 4 | Enter Compliance - Software is permitted to force a Link to enter Compliance mode (at the speed indicated in the Target Link Speed field and the de-emphasis/preset level indicated by the Compliance Preset/De-emphasis bit) by setting this bit to 1 b in both components on a Link and then initiating a Hot Reset on the Link. <br> Default value of this bit following Fundamental Reset is 0 b. <br> For a Multi-Function Device associated with an Upstream Port, the bit in Function 0 is of type RWS, and only Function 0 controls the component's Link behavior. In all other Functions of that device, this bit is of type RsvdP. <br> Components that support only the $2.5 \mathrm{GT} / \mathrm{s}$ speed are permitted to hardwire this bit to 0 b . <br> This bit is intended for debug, compliance testing purposes only. System firmware and software is allowed to modify this bit only during debug or compliance testing. In all other cases, the system must ensure that this bit is Set to the default value. | RWS/RsvdP <br> (see description) |
| 5 | Hardware Autonomous Speed Disable - When Set, this bit disables hardware from changing the Link speed for device-specific reasons other than attempting to correct unreliable Link operation by reducing Link speed. Initial transition to the highest supported common link speed is not blocked by this bit. <br> For a Multi-Function Device associated with an Upstream Port, the bit in Function 0 is of type RWS, and only Function 0 controls the component's Link behavior. In all other Functions of that device, this bit is of type RsvdP. <br> Functions that do not implement the associated mechanism are permitted to hardwire this bit to 0 b. Default value of this bit is 0 b . | RWS/RsvdP <br> (see description) |
| 6 | Selectable De-emphasis - When the Link is operating at $5.0 \mathrm{GT} / \mathrm{s}$ speed, this bit is used to control the transmit de-emphasis of the link in specific situations. See § Section 4.2.7 for detailed usage information. <br> Encodings: <br> 1b -3.5 dB <br> 0b $-6 \mathrm{~dB}$ <br> When the Link is not operating at $5.0 \mathrm{GT} / \mathrm{s}$ speed, the setting of this bit has no effect. Components that support only the $2.5 \mathrm{GT} / \mathrm{s}$ speed are permitted to hardwire this bit to 0 b . <br> This bit is not applicable and Reserved for Endpoints, PCI Express to PCI/PCI-X bridges, and Upstream Ports of Switches. | HwInit |
| 9:7 | Transmit Margin - This field controls the value of the non-deemphasized voltage level at the Transmitter pins. This field is reset to 000 b on entry to the LTSSM Polling. Configuration substate (see § Chapter 4. for details of how the Transmitter voltage level is determined in various states). <br> Encodings: <br> 000b Normal operating range <br> 001b-111b As defined in § Section 8.3.4 not all encodings are required to be implemented. <br> For a Multi-Function Device associated with an Upstream Port, the field in Function 0 is of type RWS, and only Function 0 controls the component's Link behavior. In all other Functions of that device, this field is of type RsvdP. | RWS/RsvdP <br> (see description) |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | Default value of this field is 000 b. <br> Components that support only the $2.5 \mathrm{GT} / \mathrm{s}$ speed are permitted to hardwire this bit to 000 b. <br> This field is intended for debug, compliance testing purposes only. System firmware and software is allowed to modify this field only during debug or compliance testing. In all other cases, the system must ensure that this field is set to the default value. |  |
| 10 | Enter Modified Compliance - When this bit is Set to 1b, the device transmits Modified Compliance Pattern if the LTSSM enters Polling.Compliance substate. <br> Components that support only the $2.5 \mathrm{GT} / \mathrm{s}$ speed are permitted to hardwire this bit to 0 b . <br> For a Multi-Function Device associated with an Upstream Port, the bit in Function 0 is of type RWS, and only Function 0 controls the component's Link behavior. In all other Functions of that device, this bit is of type RsvdP. <br> Default value of this bit is 0 b . <br> This bit is intended for debug, compliance testing purposes only. System firmware and software is allowed to modify this bit only during debug or compliance testing. In all other cases, the system must ensure that this bit is Set to the default value. | RWS/RsvdP <br> (see description) |
| 11 | Compliance SOS - When set to 1b, the LTSSM is required to send SKP Ordered Sets between sequences when sending the Compliance Pattern or Modified Compliance Pattern. <br> For a Multi-Function Device associated with an Upstream Port, the bit in Function 0 is of type RWS, and only Function 0 controls the component's Link behavior. In all other Functions of that device, this bit is of type RsvdP. <br> The default value of this bit is 0 b . <br> This bit is applicable when the Link is operating at $2.5 \mathrm{GT} / \mathrm{s}$ or $5.0 \mathrm{GT} / \mathrm{s}$ data rates only. <br> Components that support only the $2.5 \mathrm{GT} / \mathrm{s}$ speed are permitted to hardwire this bit to 0 b . | RWS/RsvdP <br> (see description) |
| 15:12 | Compliance Preset/De-emphasis - <br> For $8.0 \mathrm{GT} / \mathrm{s}$ and higher Data Rate: This field sets the Transmitter Preset in Polling.Compliance state if the entry occurred due to the Enter Compliance bit being 1b. The encodings are defined in § Section 4.2.4.2. Results are undefined if a reserved preset encoding is used when entering Polling.Compliance in this way. <br> For $5.0 \mathrm{GT} / \mathrm{s}$ Data Rate: This field sets the de-emphasis level in Polling.Compliance state if the entry occurred due to the Enter Compliance bit being 1b. <br> Defined Encodings are: <br> 0001b -3.5 dB <br> 0000b -6 dB <br> When the Link is operating at $2.5 \mathrm{GT} / \mathrm{s}$, the setting of this field has no effect. Components that support only $2.5 \mathrm{GT} / \mathrm{s}$ speed are permitted to hardwire this field to 0000 b . <br> For a Multi-Function Device associated with an Upstream Port, the field in Function 0 is of type RWS, and only Function 0 controls the component's Link behavior. In all other Functions of that device, this field is of type RsvdP. <br> The default value of this field is 0000 b . <br> This field is intended for debug and compliance testing purposes. System firmware and software is allowed to modify this field only during debug or compliance testing. In all other cases, the system must ensure that this field is set to the default value. | RWS/RsvdP <br> (see description) |

# IMPLEMENTATION NOTE: SELECTABLE DE-EMPHASIS USAGE 

Selectable De-emphasis setting is applicable only to Root Ports and Switch Downstream Ports. The De-emphasis setting is implementation specific and depends on the platform or enclosure in which the Root Port or the Switch Downstream Port is located. System firmware or hardware strapping is used to configure the Selectable De-emphasis value. In cases where system firmware cannot be used to set the de-emphasis value (for example, a hot plugged Switch), hardware strapping must be used to set the de-emphasis value.

### 7.5.3.20 Link Status 2 Register (Offset 32h)

![img-38.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-38.jpeg)

Figure 7-40 Link Status 2 Register

Table 7-37 Link Status 2 Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 0 | Current De-emphasis Level - When the Link is operating at 5.0 GT/s speed, this bit reflects the level of de-emphasis. | RO <br> VF RsvdZ |
|  | Encodings: |  |
|  | 1b | $-3.5 \mathrm{~dB}$ |
|  | 0b | $-6 \mathrm{~dB}$ |
|  | The value in this bit is undefined when the Link is not operating at $5.0 \mathrm{GT} / \mathrm{s}$ speed. |  |
|  | For VFs, the associated PF's value applies, and this field must be RsvdZ. Otherwise, components that support only the $2.5 \mathrm{GT} / \mathrm{s}$ speed are permitted to hardwire this bit to Zero. |  |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 1 | For components that support speeds greater than $2.5 \mathrm{GT} / \mathrm{s}$, Multi-Function Devices associated with an Upstream Port must report the same value in this field for all Functions of the Port. |  |
|  | Equalization 8.0 GT/s Complete - When set to 1b, this bit indicates that the Transmitter Equalization procedure at the $8.0 \mathrm{GT} / \mathrm{s}$ data rate has completed. Details of the Transmitter Equalization process and when this bit needs to be set to 1 b is provided in $\S$ Section 4.2.7.4.2 . <br> The default value of this bit is 0 b . <br> For Multi-Function Upstream Port, this bit must be implemented in Function 0 and RsvdZ in other Functions. Components that only support speeds below $8.0 \mathrm{GT} / \mathrm{s}$ are permitted to hardwire this bit to 0 b . | ROS |
| 2 | Equalization 8.0 GT/s Phase 1 Successful - When set to 1b, this bit indicates that Phase 1 of the 8.0 GT/s Transmitter Equalization procedure has successfully completed. Details of the Transmitter Equalization process and when this bit needs to be set to 1 b is provided in $\S$ Section 4.2.7.4.2 . <br> The default value of this bit is 0 b . <br> For Multi-Function Upstream Port, this bit must be implemented in Function 0 and RsvdZ in other Functions. Components that only support speeds below $8.0 \mathrm{GT} / \mathrm{s}$ are permitted to hardwire this bit to 0 b . | ROS |
| 3 | Equalization 8.0 GT/s Phase 2 Successful - When set to 1b, this bit indicates that Phase 2 of the 8.0 GT/s Transmitter Equalization procedure has successfully completed. Details of the Transmitter Equalization process and when this bit needs to be set to 1 b is provided in $\S$ Section 4.2.7.4.2 . <br> The default value of this bit is 0 b . <br> For Multi-Function Upstream Port, this bit must be implemented in Function 0 and RsvdZ in other Functions. Components that only support speeds below $8.0 \mathrm{GT} / \mathrm{s}$ are permitted to hardwire this bit to 0 b . | ROS |
| 4 | Equalization 8.0 GT/s Phase 3 Successful - When set to 1b, this bit indicates that Phase 3 of the 8.0 GT/s Transmitter Equalization procedure has successfully completed. Details of the Transmitter Equalization process and when this bit needs to be set to 1 b is provided in $\S$ Section 4.2.7.4.2 . <br> The default value of this bit is 0 b . <br> For Multi-Function Upstream Port, this bit must be implemented in Function 0 and RsvdZ in other Functions. Components that only support speeds below $8.0 \mathrm{GT} / \mathrm{s}$ are permitted to hardwire this bit to 0 b . | ROS |
| 5 | Link Equalization Request 8.0 GT/s - This bit is Set by hardware to request the 8.0 GT/s Link equalization process to be performed on the Link. Refer to $\S$ Section 4.2.4 and $\S$ Section 4.2.7.4.2 for details. <br> The default value of this bit is 0 b . <br> For Multi-Function Upstream Port, this bit must be implemented in Function 0 and RsvdZ in other Functions. Components that only support speeds below $8.0 \mathrm{GT} / \mathrm{s}$ are permitted to hardwire this bit to 0 b . | RW1CS |
| 6 | Retimer Presence Detected - When set to 1b, this bit indicates that a Retimer was present during the most recent Link negotiation. Refer to $\S$ Section 4.2.7.3.5.1 for details. <br> The default value of this bit is 0 b . <br> This bit is required for Ports that have the Retimer Presence Detect Supported bit of the Link Capabilities 2 Register set to 1 b . <br> Ports that have the Retimer Presence Detect Supported bit set to 0 b are permitted to hardwire this bit to 0 b . | ROS/RsvdZ |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | For Multi-Function Devices associated with an Upstream Port, this bit must be implemented in Function 0 and is RsvdZ in all other Functions. |  |
| 7 | Two Retimers Presence Detected - When set to 1b, this bit indicates that two Retimers were present during the most recent Link negotiation. Refer to $\S$ Section 4.2.7.3.5.1 for details. <br> The default value of this bit is 0 b . <br> This bit is required for Ports that have the Two Retimers Presence Detect Supported bit of the Link Capabilities 2 Register set to 1b. <br> Ports that have the Two Retimers Presence Detect Supported bit set to 0b are permitted to hardwire this bit to 0b. <br> For Multi-Function Devices associated with an Upstream Port, this bit must be implemented in Function 0 and RsvdZ in all other Functions. | ROS/RsvdZ |
| 9:8 | Crosslink Resolution - This field indicates the state of the Crosslink negotiation. It must be implemented if Crosslink Supported is Set and the Port supports $16.0 \mathrm{GT} / \mathrm{s}$ or higher data rate. It is permitted to be implemented in all other Ports. If Crosslink Supported is Clear, this field may be hardwired to 01 b or 10 b . <br> Encoding is: <br> 00b Crosslink Resolution is not supported. No information is provided regarding the status of the Crosslink negotiation. <br> 01b Crosslink negotiation resolved as an Upstream Port. <br> 10b Crosslink negotiation resolved as a Downstream Port. <br> 11b Crosslink negotiation is not completed. <br> Once a value of 01 b or 10 b is returned in this field, that value must continue to be returned while the Link is Up. | RO |
| 10 | Flit Mode Status - When Flit Mode Supported is Set, this bit when Set indicates that the Link is or will be operating in Flit Mode. <br> For Downstream Ports, this bit is only meaningful when Downstream Component Presence is either 011b, 100b, or 101b. In all other states, this bit must contain Zero. <br> For Upstream Ports, this bit is meaningful when the Link is Up. When the Link is Down, the value is implementation specific. <br> This bit is RsvdZ if Flit Mode Supported is Clear. | RO / RsvdZ |
| $14: 12$ | Downstream Component Presence - This field indicates the presence and DRS status for the Downstream Component, if any, connected to the Link; defined values are: <br> 000b Link Down - Presence Not Determined <br> 001b Link Down - Component Not Present indicates the Downstream Port (DSP) has determined that a Downstream Component is not present <br> 010b Link Down - Component Present indicates the DSP has determined that a Downstream Component is present, but the Data Link Layer is not active <br> 011b Link Down - Flit Mode Negotiation Completed indicates that the DSP's LTSSM has determined whether or not the Link will be operating in Flit Mode, but the Data Link Layer is not yet active. The Flit Mode Status bit is meaningful in this state. <br> 100b Link Up - Component Present indicates the DSP has determined that a Downstream Component is present, but no DRS Message has been received since the Data Link Layer became active. The Flit Mode Status bit is meaningful in this state. | RO/RsvdZ |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | 101b Link Up - Component Present and DRS Received indicates the DSP has received a DRS Message since the Data Link Layer became active. The Flit Mode Status bit is meaningful in this state. |  |
|  | 110b | Reserved |
|  | 111b | Reserved |
|  | The "Component Present" portion of the Downstream Component Presence field state must be determined by the logical "OR" of the Physical Layer in-band presence detect (in-band PD) mechanism and any out-of-band presence detect (OOB PD) mechanism supported by the Link. I.e., the Component Present state is true if either mechanism indicates a component is present. If no OOB PD mechanism is supported, then the Component Present state must be determined solely by the in-band PD mechanism. If the in-Band PD Disable bit in the Slot Control Register is Set, the in-band PD mechanism must always indicate that no component is present. |  |
|  | For this field, the Component Present state is not always logically consistent with the Link Up state. As covered in the following paragraph, race conditions can result in Link Up being true while Component Present is false. This temporary condition ${ }^{174}$ cannot be accurately indicated using the field's architected encodings. It is strongly recommended that this condition be indicated using the encoding 001b (Link Down - Component Not Present). |  |
|  | When a slot supports OOB PD, in-band PD is disabled, and an async removal or async hot-add is performed ${ }^{175}$, race conditions may result in the DSP's LTSSM indicating that the Link is up while the OOB PD mechanism indicates that no component is present. For an async removal, this is usually caused by the LTSSM not detecting Link Down immediately. For an async hot-add, this is usually caused by the OOB PD mechanism not immediately indicating that the component is present. For either case, it's less likely to cause software issues by the field value being 001b during this condition. |  |
|  | Component Presence, Link Up, and DRS Received states indicated by this field must reflect their maskable states, which are controlled by the SFI PD State Mask, SFI DLL State Mask, or SFI DRS Mask bits in the SFI Control Register. See § Section 7.9.22.3. |  |
|  | This field must be implemented in any Downstream Port where the DRS Supported bit is Set in the Link Capabilities 2 Register. This field must be implemented in any Downstream Port where the Flit Mode Supported bit is Set. |  |
|  | This field is RsvdZ for all other Functions. |  |
|  | Default value of this field is 000 b . |  |
| 15 | DRS Message Received - This bit must be Set whenever the Port receives a DRS Message. | RW1C/RsvdZ |
|  | This bit must be Cleared in DL_Down. |  |
|  | This bit must be implemented in any Downstream Port where the DRS Supported bit is Set in the Link Capabilities 2 Register. |  |
|  | This bit is RsvdZ for all other Functions. |  |
|  | Default value of this bit is 0 b . |  |

[^0]
[^0]:    174. This is a temporary condition and not an indefinite one. Notably, if the slot does not support OOB PD, and software attempts to Set the In-Band PD Disable bit, the bit will remain Clear since the In-Band PD Disable Supported bit must be Clear and the In-Band PD Disable bit must be hardwired to 0b 175. See IMPLEMENTATION NOTE: IN-BAND PRESENCE DETECT MECHANISM DEPRECATED FOR ASYNC HOT-PLUG.

# 7.5.3.21 Slot Capabilities 2 Register (Offset 34h) 

![img-39.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-39.jpeg)

Figure 7-41 Slot Capabilities 2 Register

Table 7-38 Slot Capabilities 2 Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :-- |
| 0 | In-Band PD Disable Supported - When Set, this bit indicates that this slot supports disabling the <br> reporting of the in-band presence detect state, as controlled by the In-Band PD Disable bit in the Slot <br> Control Register. If the slot does not support an out-of-band presence detect mechanism, this bit must <br> be Clear. | HwInit |

### 7.5.3.22 Slot Control 2 Register (Offset 38h) 

This section is a placeholder. There are no capabilities that require this register.
This register must be treated by software as RsvdP.

### 7.5.3.23 Slot Status 2 Register (Offset 3Ah) 

This section is a placeholder. There are no capabilities that require this register.
This register must be treated by software as RsvdZ.

### 7.6 PCI Express Extended Capabilities

PCI Express Extended Capability registers are located in Configuration Space at offsets 256 or greater as shown in § Figure 7-42 or in the Root Complex Register Block (RCRB). These registers when located in the Configuration Space are accessible using only the PCI Express Enhanced Configuration Access Mechanism (ECAM).

PCI Express Extended Capability structures are allocated using a linked list of optional or required PCI Express Extended Capabilities following a format resembling PCI Capability structures. The first DWORD of the Capability structure identifies the Capability and version and points to the next Capability as shown in § Figure 7-42.

Each Capability structure must be DWORD aligned.

![img-40.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-40.jpeg)

Figure 7-42 PCI Express Extended Configuration Space Layout

# 7.6.1 Extended Capabilities in Configuration Space 

Extended Capabilities in Configuration Space always begin at offset 100 h with a PCI Express Extended Capability header (\$ Section 7.6.3 ). Absence of any Extended Capabilities is required to be indicated by an Extended Capability header with a Capability ID of 0000h, a Capability Version of 0 h, and a Next Capability Offset of 000 h .

### 7.6.2 Extended Capabilities in the Root Complex Register Block

Extended Capabilities in a Root Complex Register Block always begin at offset 000 h with a PCI Express Extended Capability header (\$ Section 7.6.3 ). Absence of any Extended Capabilities is required to be indicated by an Extended Capability header with a Capability ID of FFFFh and a Next Capability Offset of 000 h .

### 7.6.3 PCI Express Extended Capability Header

All PCI Express Extended Capabilities must begin with a PCI Express Extended Capability Header. § Figure 7-43 details the allocation of register fields of a PCI Express Extended Capability Header; § Table 7-39 provides the respective bit definitions.
![img-41.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-41.jpeg)

Figure 7-43 PCI Express Extended Capability Header

Table 7-39 PCI Express Extended Capability Header

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 15:0 | PCI Express Extended Capability ID - This field is a PCI-SIG defined ID number that indicates the nature <br> and format of the Extended Capability. | RO |
| 19:16 | Capability Version - This field is a PCI-SIG defined version number that indicates the version of the <br> Capability structure present. | RO |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | A version of the specification that changes the Extended Capability in a way that is not otherwise identifiable (e.g., through a new Capability field) is permitted to increment this field. All such changes to the Capability structure must be software-compatible. Software must check for Capability Version numbers that are greater than or equal to the highest number defined when the software is written, as Functions reporting any such Capability Version numbers will contain a Capability structure that is compatible with that piece of software. |  |
| $31: 20$ | Next Capability Offset - This field contains the offset to the next PCI Express Capability structure or 000h if no other items exist in the linked list of Capabilities. <br> For Extended Capabilities implemented in Configuration Space, this offset is relative to the beginning of PCI-compatible Configuration Space and thus must always be either 000 h (for terminating list of Capabilities) or greater than 0FFh. <br> The bottom 2 bits of this offset are Reserved and must be implemented as 00 b although software must mask them to allow for future uses of these bits. | RO |

# 7.7 PCI and PCIe Capabilities Required by the Base Spec in Some Situations 

The following capabilities are required by this specification for some Functions. For example, Functions that support specific data rates, functions that generate interrupts, etc.

### 7.7.1 MSI Capability Structures

All PCI Express Endpoint Functions that are capable of generating interrupts must implement MSI or MSI-X or both.
The MSI Capability structure is described in this section. The MSI-X Capability structure is described in § Section 7.7.2 .
The MSI Capability structure is illustrated in § Figure 7-44 and § Figure 7-45. Each device Function that supports MSI (in a Multi-Function Device) must implement its own MSI Capability structure. More than one MSI Capability structure per Function is prohibited, but a Function is permitted to have both an MSI and an MSI-X Capability structure.
![img-42.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-42.jpeg)

Figure 7-44 MSI Capability Structure for 32-bit Message Address

![img-43.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-43.jpeg)

Figure 7-45 MSI Capability Structure for 64-bit Message Address 8
![img-44.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-44.jpeg)

Figure 7-46 MSI Capability Structure for 32-bit Message Address and PVM 9

| 31 | 30 | 29 | 28 | 27 | 26 | 25 | 24 | 23 | 22 | 21 | 20 | 19 | 18 | 17 | 16 | 15 | 14 | 13 | 12 | 11 | 10 | 9 | 8 | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
| :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: |
| Message Control | Next Capability Pointer | Capability ID |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| Message Address |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| Message Upper Address |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| Extended Message Data (if implemented) | Message Data |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| Mask Bits |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| Pending Bits |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |

Figure 7-46 MSI Capability Structure for 32-bit Message Address and PVM 8

| 31 | 30 | 29 | 28 | 27 | 26 | 25 | 24 | 23 | 22 | 21 | 20 | 19 | 18 | 17 | 16 | 15 | 14 | 13 | 12 | 11 | 10 | 9 | 8 | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
| :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: |
| Message Control | Next Capability Pointer | Capability ID |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| Message Address |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| Message Upper Address |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| Extended Message Data (or RsvdP) | Message Data |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| Mask Bits |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| Pending Bits |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |

(and, optionally, when 64-bit message addresses are used, the Message Upper Address Register for MSI). A read of the address specified by the contents of the Message Address register produces undefined results.

A Function supporting MSI implements one of four MSI Capability structure layouts illustrated in § Figure 7-44 to § Figure 7-47, depending upon which optional features are supported. A Legacy Endpoint that implements MSI is required to support either the 32-bit or 64-bit Message Address version of the MSI Capability structure. A PCI Express Endpoint that implements MSI is required to support the 64-bit Message Address version of the MSI Capability structure. The Message Control Register for MSI indicates the Function's capabilities and provides system software control over MSI.

Each field is further described in the following sections.

# 7.7.1.1 MSI Capability Header (Offset 00h) 

The MSI Capability Header enumerates the MSI Capability structure in the PCI Configuration Space Capability list. § Figure 7-48 details allocation of register fields in the MSI Capability Header; § Table 7-40 provides the respective bit definitions.
![img-45.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-45.jpeg)

Figure 7-48 MSI Capability Header

Table 7-40 MSI Capability Header

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| $7: 0$ | Capability ID - Indicates the MSI Capability structure. This field must return a Capability ID of 05h <br> indicating that this is an MSI Capability structure. | RO |
| $15: 8$ | Next Capability Pointer - This field contains the offset to the next PCI Capability structure or 00h if no <br> other items exist in the linked list of Capabilities. | RO |

### 7.7.1.2 Message Control Register for MSI (Offset 02h)

This register provides system software control over MSI. By default, MSI is disabled. If MSI and MSI-X are both disabled, the Function requests servicing using INTx interrupts (if supported). System software can enable MSI by Setting bit 0 of this register. System software is permitted to modify the Message Control Register for MSI's read-write bits and fields. A device driver is not permitted to modify the Message Control Register for MSI's read-write bits and fields.

![img-46.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-46.jpeg)

Figure 7-49 Message Control Register for MSI

Table 7-41 Message Control Register for MSI

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 0 | MSI Enable - If Set and the MSI-X Enable bit in the Message Control Register for MSI-X (see § Section 7.7.2.2) is Clear, the Function is permitted to use MSI to request service and is prohibited from using INTx interrupts. System configuration software Sets this bit to enable MSI. Refer to § Section 7.5.1.1.3 for control of INTx interrupts. <br> If Clear, the Function is prohibited from using MSI to request service. <br> Software changing this bit during active operation may result in the Function dropping pending interrupt conditions or failing to recognize new interrupt conditions. See § Section 6.1.4.5. <br> Default value of this bit is Ob. | RW |
| 3:1 | Multiple Message Capable - System software reads this field to determine the number of requested vectors. The number of requested vectors must be aligned to a power of two (if a Function requires three vectors, it requests four by initializing this field to 010b). The encoding is defined as: <br> 000b 1 vector requested <br> 001b 2 vectors requested <br> 010b 4 vectors requested <br> 011b 8 vectors requested <br> 100b 16 vectors requested <br> 101b 32 vectors requested <br> 110b Reserved <br> 111b Reserved | RO |
| 6:4 | Multiple Message Enable - software writes to this field to indicate the number of allocated vectors. The number of allocated vectors is aligned to a power of two. As an example, if a Function requests four vectors (indicated by a Multiple Message Capable encoding of 010b), software can allocate either four, two, or one vector by writing a 010b, 001b, or 000b to this field, respectively. <br> Behavior is undefined if the number of vectors allocated is greater than the number of vectors requested. <br> Behavior is undefined if this field is changed while MSI Enable is Set. | RW |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | When MSI Enable is Set, a Function will be allocated at least 1 vector. The encoding is defined as: |  |
|  | 000b | 1 vector allocated |
|  | 001b | 2 vectors allocated |
|  | 010b | 4 vectors allocated |
|  | 011b | 8 vectors allocated |
|  | 100b | 16 vectors allocated |
|  | 101b | 32 vectors allocated |
|  | 110b | Reserved |
|  | 111b | Reserved |
|  | Function behavior is undefined if software changes the value of this field while the MSI Enable bit is Set. Default value of this field is 000 b . |  |
| 7 | 64-bit Address Capable - If Set, the Function is capable of sending a 64-bit Message Address. If Clear, the Function is not capable of sending a 64-bit Message Address. This bit must be Set if the Function is a PCI Express Endpoint, as indicated by the value in the Device/Port Type field. This bit MUST@FLIT be Set. | RO |
| 8 | Per-Vector Masking Capable - If Set, the Function supports MSI Per-Vector Masking. If Clear, the Function does not support MSI Per-Vector Masking. This bit must be Set if the Function is a PF or VF within an SR-IOV Device. | RO |
| 9 | Extended Message Data Capable - If Set, the Function is capable of providing Extended Message Data. If Clear, the Function does not support providing Extended Message Data. | RO |
| 10 | Extended Message Data Enable - If Set, the Function is enabled to provide Extended Message Data. If Clear, the Function is not enabled to provide Extended Message Data. <br> Default value of this bit is 0 b . <br> This bit must be read-write if the Extended Message Data Capable bit is 1b; otherwise it must be hardwired to 0 b. | RW/RO |

# 7.7.1.3 Message Address Register for MSI (Offset 04h) 

![img-47.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-47.jpeg)

Figure 7-50 Message Address Register for MSI

Table 7-42 Message Address Register for MSI

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| $1: 0$ | Reserved Reserved - Always returns 0 on read. Write operations have no effect. | RsvdP |

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| $31: 2$ | Message Address - System-specified message address. | RW |
|  | If the MSI Enable bit is Set, the contents of this register specify the DWORD-aligned address <br> (Address[31:02]) for the MSI transaction. Address[1:0] are set to 00b. <br> Default value of this field is undefined. |  |

# 7.7.1.4 Message Upper Address Register for MSI (Offset 08h) 

![img-48.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-48.jpeg)

Figure 7-51 Message Upper Address Register for MSI

Table 7-43 Message Upper Address Register for MSI

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| $31: 0$ | Message Upper Address - System-specified message upper address. | RW |
|  | This register is implemented only if the Function supports a 64-bit message address (64-bit Address <br> Capable is Set). |  |
|  | This register is implemented only if the Function supports a 64-bit message address (64-bit Address <br> Capable is Set). This register is required for PCI Express Endpoints (as indicated by the value in the <br> Device/Port Type field) and is optional for other Function types. |  |
|  | If the MSI Enable bit is Set, the contents of this register (if non-zero) specify the upper 32-bits of a 64-bit <br> message address (Address[63:32]). If the contents of this register are zero, the Function uses the 32 bit <br> address specified by the Message Address register. |  |
|  | Default value of this field is undefined. |  |

### 7.7.1.5 Message Data Register for MSI (Offset 08h or 0Ch) 

![img-49.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-49.jpeg)

Figure 7-52 Message Data Register for MSI

Table 7-44 Message Data Register for MSI

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 15:0 | Message | RW |

| Bit Location | Register Description | Attributes |
| :-- | :-- | :-- |
| Message Data - System-specified message data. <br> If the MSI Enable bit is Set, the Function sends a DWORD Memory Write transaction using Message Data <br> for the lower 16 bits. All 4 Byte Enables are Set. |  |  |
| The Multiple Message Enable field defines the number of low order message data bits the Function is <br> permitted to modify to generate its system software allocated vectors. For example, a Multiple Message <br> Enable encoding of 010b indicates the Function has been allocated four vectors and is permitted to <br> modify message data bits 1 and 0 (a Function modifies the lower message data bits to generate the <br> allocated number of vectors). If the Multiple Message Enable field is 000b, the Function is not permitted to <br> modify the message data. When Multiple Message Enable is non-zero, behavior is undefined if the <br> corresponding low order bits of this register are not 0b. <br> Default value of this field is undefined. |  |

# 7.7.1.6 Extended Message Data Register for MSI (Optional) 

![img-50.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-50.jpeg)

Figure 7-53 Extended Message Data Register for MSI

Table 7-45 Extended Message Data Register for MSI

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 15:0 | Extended Message Data - System-specified message data. <br> This register is optional. For the MSI Capability structures without Per-vector Masking, it must be implemented if the Extended Message Data Capable bit is Set; otherwise, it is outside the MSI Capability structure and undefined. For the MSI Capability structures with Per-vector Masking, it must be implemented if the Extended Message Data Capable bit is Set; otherwise, it is RsvdP. <br> If the Extended Message Data Enable bit is Set, the DWORD Memory Write transaction uses Extended Message Data for the upper 16 bits; otherwise, it uses 0000 h for the upper 16 bits. <br> Default value of this field is 0000 h . | RW/undefined/ RsvdP |

### 7.7.1.7 Mask Bits Register for MSI (Offset OCh or 10h 6

This register is optional. It is present if Per-Vector Masking Capable is Set (see § Section 7.7.1.2). The offset of this register within the capability depends on the value of the 64-bit Address Capable bit (see § Section 7.7.1.2).

The Mask Bits and Pending Bits registers enable software to disable or defer message sending on a per-vector basis.
MSI vectors are numbered 0 through $\mathrm{N}-1$, where N is the number of vectors allocated by software. Each vector is associated with a correspondingly numbered bit in the Mask Bits and Pending Bits registers.

The Multiple Message Capable field indicates how many vectors (with associated Mask and Pending bits) are implemented. All unimplemented Mask and Pending bits are Reserved.

The Multiple Message Enable field controls how many vectors are allocated for use. The value of each implemented Mask bit and Pending bit that is currently not allocated must be ignored by hardware; i.e., the value must not affect the generation of interrupts.
![img-51.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-51.jpeg)

Figure 7-54 Mask Bits Register for MSI

Table 7-46 Mask Bits Register for MSI

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 31:0 | Mask Bits - For each Mask bit that is Set, the Function is prohibited from sending the associated <br> message. <br> Default is 0. | RW |

# 7.7.1.8 Pending Bits Register for MSI (Offset 10h or 14h) 

This register is optional. It is present if Per-Vector Masking Capable is Set (see § Section 7.7.1.2).
The offset of this register within the capability depends on the value of the 64-bit Address Capable bit (see § Section 7.7.1.2 )

See § Section 7.7.1.7 for additional requirements on this register.
![img-52.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-52.jpeg)

Figure 7-55 Pending Bits Register for MSI

Table 7-47 Pending Bits Register for MSI

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 31:0 | Pending Bits - For each Pending bit that is Set, the Function has a pending associated message. | RO |
|  | Default is 0. |  |

### 7.7.2 MSI-X Capability and Table Structure

The MSI-X Capability structure is illustrated in § Figure 7-56. More than one MSI-X Capability structure per Function is prohibited, but a Function is permitted to have both an MSI Capability structure and an MSI-X Capability structure.

In contrast to the MSI Capability structure, which directly contains all of the control/status information for the Function's vectors, the MSI-X Capability structure instead points to an MSI-X Table structure and an MSI-X PBA structure (Pending Bit Array structure), each residing in Memory Space (see § Figure 7-57 and § Figure 7-58).

Each structure is mapped by a Base Address Register (BAR) belonging to the Function, located beginning at 10 h in Configuration Space, or an entry in the Enhanced Allocation capability. A BAR Indicator register (BIR) indicates which BAR(or BEI when using Enhanced Allocation), and a QWORD-aligned Offset indicates where the structure begins relative to the base address associated with the BAR. The BAR is permitted to be either 32-bit or 64-bit, but must map Memory Space. A Function is permitted to map both structures with the same BAR, or to map each structure with a different BAR.

The MSI-X Table structure, illustrated in § Figure 7-57, typically contains multiple entries, each consisting of several fields: Message Address, Message Upper Address, Message Data, and Vector Control. Each entry is capable of specifying a unique vector.

The Pending Bit Array (PBA) structure, illustrated in § Figure 7-58, contains the Function's Pending Bits, one per Table entry, organized as a packed array of bits within QWORDs. The last QWORD will not necessarily be fully populated.
![img-53.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-53.jpeg)

Figure 7-56 MSI-X Capability Structure

![img-54.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-54.jpeg)

Figure 7-57 MSI-X Table Structure 5

| 63 | 0 |  |
| :--: | :--: | :--: |
| Pending Bits 0 through 63 | QWORD 0 | Base |
| Pending Bits 64 through 127 | QWORD 1 | Base $+1 * 8$ |
| *** | *** | *** |
| Pending Bits ((N-1) div 64)*64 through N-1 | QWORD ((N-1) div 64) | Base $+((N-1)$ div 64)*8 |

Figure 7-58 MSI-X PBA Structure 6

To request service using a given MSI-X Table entry, a Function performs a DWORD Memory Write transaction using the contents of the Message Data field entry for data, the contents of the Message Upper Address field for the upper 32 bits of address, and the contents of the Message Address field entry for the lower 32 bits of address. A memory read transaction from the address targeted by the MSI-X message produces undefined results.

If a Base Address Register or entry in the Enhanced Allocation capability that maps address space for the MSI-X Table or MSI-X PBA also maps other usable address space that is not associated with MSI-X structures, locations (e.g., for CSRs) used in the other address space must not share any naturally aligned 4-KB address range with one where either MSI-X structure resides. This allows system software where applicable to use different processor attributes for MSI-X structures and the other address space. (Some processor architectures do not support having different processor attributes associated with the same naturally aligned 4-KB physical address range.) The MSI-X Table and MSI-X PBA are permitted to co-reside within a naturally aligned 4-KB address range, though they must not overlap with each other.

With SR-IOV devices, alignment requirements like those in the preceeding paragraph still apply, but they must be based on the System Page Size value from the PF's SR-IOV Extended Capability instead using a fixed 4-KB value.

# IMPLEMENTATION NOTE: DEDICATED BARS AND ADDRESS RANGE ISOLATION 

To enable system software to map MSI-X structures onto different processor pages for improved access control, it is recommended that a Function dedicate separate Base Address Registers for the MSI-X Table and MSI-X PBA, or else provide more than the minimum required isolation with address ranges.

If dedicated separate Base Address Registers is not feasible, it is recommended that a Function dedicate a single Base Address Register for the MSI-X Table and MSI-X PBA.

If a dedicated Base Address Register is not feasible, it is recommended that a Function isolate the MSI-X structures from the non-MSI-X structures with aligned 8 KB ranges rather than the mandatory aligned 4 KB ranges.

For example, if a Base Address Register needs to map 2 KB for an MSI-X Table containing 128 entries, 16 bytes for an MSI-X PBA containing 128 bits, and 64 bytes for registers not related to MSI-X, the following is an acceptable implementation. The Base Address Register requests 8 KB of total address space, maps the first 64 bytes for the non MSI-X registers, maps the MSI-X Table beginning at an offset of 4 KB , and maps the MSI-X PBA beginning at an offset of 6 KB .

A preferable implementation for a shared Base Address Register is for it to request 16 KB of total address space, map the first 64 bytes for the non MSI-X registers, map the MSI-X Table beginning at an offset of 8 KB , and map the MSI-X PBA beginning at an offset of 12 KB .

## IMPLEMENTATION NOTE: <br> MSI-X MEMORY SPACE STRUCTURES IN READ/WRITE MEMORY

The MSI-X Table and MSI-X PBA structures are defined such that they can reside in general purpose read/write memory on a device, for ease of implementation and added flexibility. To achieve this, none of the contained fields are required to be read-only, and there are also restrictions on transaction alignment and sizes.

For all accesses to MSI-X Table and MSI-X PBA fields, software must use aligned full DWORD or aligned full QWORD transactions; otherwise, the result is undefined.

MSI-X Table entries and Pending bits are each numbered 0 through N-1, where N-1 is indicated by the Table Size field in the Message Control Register for MSI-X. For a given arbitrary MSI-X Table entry $k$, its starting address can be calculated with the formula:

entry starting address $=$ Table base $+k \times 16$

For the associated Pending bit $k$, its address for QWORD access and bit number within that QWORD can be calculated with the formulas:

QWORD address $=$ PBA base $+(k$ div 64$) \times 8$

QWORD bit\# $=k \bmod 64$

# Equation 7-2 MSI-X PBA QWORD Access 

Software that chooses to read Pending bit $K$ with DWORD accesses can use these formulas:

DWORD address $=$ PBA base $+(k$ div 32$) \times 4$

DWORD bit\# $=k \bmod 32$

Each field in the MSI-X Capability, MSI-X Table, and MSI-X PBA structures is further described in the following sections. Within the MSI-X Capability structure, Reserved registers and bits always return 0 when read, and write operations have no effect. Within the MSI-X Table and PBA structures, Reserved fields have special rules.

### 7.7.2.1 MSI-X Capability Header (Offset 00h)

The MSI-X Capability Header enumerates the MSI-X Capability structure in the PCI Configuration Space Capability list. § Figure 7-56 details allocation of register fields in the MSI-X Capability Header; § Table 7-48 provides the respective bit definitions.
![img-55.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-55.jpeg)

Figure 7-59 MSI-X Capability Header

Table 7-48 MSI-X Capability Header
Bit Location Register Description Attributes

| 7:0 | Capability ID - Indicates the MSI-X Capability structure. This field must return a Capability ID of 11h <br> indicating that this is an MSI-X Capability structure. | RO |
| :-- | :-- | :--: |
| 15:8 | Next Capability Pointer - This field contains the offset to the next PCI Capability structure or 00h if no <br> other items exist in the linked list of Capabilities. | RO |

# 7.7.2.2 Message Control Register for MSI-X (Offset 02h) 

By default, MSI-X is disabled. If MSI and MSI-X are both disabled, the Function requests servicing via INTx interrupts (if supported). System software can enable MSI-X by Setting bit 15 of this register. System software is permitted to modify the Message Control register's read-write bits and fields. A device driver is not permitted to modify the Message Control register's read-write bits and fields.
![img-56.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-56.jpeg)

Figure 7-60 Message Control Register for MSI-X

Table 7-49 Message Control Register for MSI-X

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $10: 0$ | Table Size - System software reads this field to determine the MSI-X Table Size N, which is encoded as N -1. For example, a returned value of 00000000011 b indicates a table size of 4. | RO |
| $13: 11$ | Reserved Reserved - Always returns 0 on a read, and a write operation has no effect. | RsvdP |
| 14 | Function Mask - If Set, all of the vectors associated with the Function are masked, regardless of their per-vector Mask bit values. <br> If Clear, each vector's Mask bit determines whether the vector is masked or not. <br> Setting or Clearing the MSI-X Function Mask bit has no effect on the value of the per-vector Mask bits. <br> Default value of this bit is 0 b. | RW |
| 15 | MSI-X Enable - If Set and the MSI Enable bit in the Message Control Register for MSI (see § Section 7.7.1.2 ) is Clear, the Function is permitted to use MSI-X to request service and is prohibited from using INTx interrupts (if implemented). System configuration software Sets this bit to enable MSI-X. <br> If Clear, the Function is prohibited from using MSI-X to request service. <br> Software changing this bit during active operation may result in the Function dropping pending interrupt conditions or failing to recognize new interrupt conditions. See § Section 6.1.4.5. <br> Default value of this bit is 0 b . | RW |

# 7.7.2.3 Table Offset/Table BIR Register for MSI-X (Offset 04h) 

![img-57.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-57.jpeg)

Figure 7-61 Table Offset/Table BIR Register for MSI-X

Table 7-50 Table Offset/Table BIR Register for MSI-X

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 2:0 | Table BIR - Indicates which one of a Function's Base Address Registers, located beginning at 10 h in Configuration Space, or entry in the Enhanced Allocation capability with a matching BAR Equivalent Indicator (BEI), is used to map the Function's MSI-X Table into Memory Space. | RO |
|  | Defined encodings are: |  |
|  | 0 | Base Address Register 10h |
|  | 1 | Base Address Register 14h |
|  | 2 | Base Address Register 18h |
|  | 3 | Base Address Register 1Ch |
|  | 4 | Base Address Register 20h |
|  | 5 | Base Address Register 24h |
|  | 6 | Reserved |
|  | 7 | Reserved |
|  | For a 64-bit Base Address Register, the Table BIR indicates the lower DWORD. For Functions with Type 1 Configuration Space headers, BIR values 2 through 5 are also Reserved. |  |
| $31: 3$ | Table Offset - Used as an offset from the address contained by one of the Function's Base Address Registers to point to the base of the MSI-X Table. The lower 3 Table BIR bits are masked off (set to zero) by software to form a 32-bit QWORD-aligned offset. | RO |
|  | For VFs, the Table Offset value is relative to the VF's Memory address space. |  |

### 7.7.2.4 PBA Offset/PBA BIR Register for MSI-X (Offset 08h)

![img-58.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-58.jpeg)

Figure 7-62 PBA Offset/PBA BIR Register for MSI-X

Table 7-51 PBA Offset/PBA BIR Register for MSI-X

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $2: 0$ | PBA BIR - Indicates which one of a Function's Base Address Registers, located beginning at 10 h in Configuration Space, or entry in the Enhanced Allocation capability with a matching BEI, is used to map the Function's MSI-X PBA into Memory Space. <br> The PBA BIR value definitions are identical to those for the Table BIR. | RO |
| $31: 3$ | PBA Offset - Used as an offset from the address contained by one of the Function's Base Address Registers to point to the base of the MSI-X PBA. The lower 3 PBA BIR bits are masked off (set to zero) by software to form a 32-bit QWORD-aligned offset. <br> For VFs, the PBA Offset value is relative to the VF's Memory address space. | RO |

# 7.7.2.5 Message Address Register for MSI-X Table Entries 

![img-59.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-59.jpeg)

Figure 7-63 Message Address Register for MSI-X Table Entries

Table 7-52 Message Address Register for MSI-X Table Entries

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $1: 0$ | Reserved | RO or RW |
|  | Reserved - For proper DWORD alignment, software must always write zeros to these two bits; otherwise the result is undefined. <br> Default value of this field is 00 b . <br> These bits are permitted to be read-only or read-write. |  |
| $31: 2$ | Message Address - System-specified message lower address. | RW |
|  | For MSI-X messages, the contents of this field from an MSI-X Table entry specifies the lower portion of the DWORD-aligned address for the Memory Write transaction. <br> Default value of this field is undefined. |  |

# 7.7.2.6 Message Upper Address Register for MSI-X Table Entries 

![img-60.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-60.jpeg)

Figure 7-64 Message Upper Address Register for MSI-X Table Entries

Table 7-53 Message Upper Address Register for MSI-X Table Entries

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 31:0 | Message Upper Address - System-specified message upper address bits. | RW |
|  | If this field is zero, 32-bit address messages are used. If this field is non-zero, 64-bit address messages <br> are used. |  |
|  | Default value of this field is undefined. |  |

### 7.7.2.7 Message Data Register for MSI-X Table Entries

![img-61.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-61.jpeg)

Figure 7-65 Message Data Register for MSI-X Table Entries

Table 7-54 Message Data Register for MSI-X Table Entries

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 31:0 | Message Data - System-specified message data. | RW |
|  | For MSI-X messages, the contents of this field from an MSI-X Table entry specifies the 32-bit data payload <br> of the DWORD Memory Write transaction. All 4 Byte Enables are Set. |  |
|  | In contrast to message data used for MSI messages, the low-order message data bits in MSI-X messages <br> are not modified by the Function. |  |
|  | This field is read-write. |  |
|  | Default value of this field is undefined. |  |

### 7.7.2.8 Vector Control Register for MSI-X Table Entries

If a Function implements a TPH Requester Extended Capability structure and an MSI-X Capability structure, the Function can optionally use the Vector Control Register for MSI-X Table Entries in each entry to store a Steering Tag. See § Section 6.17 .

![img-62.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-62.jpeg)

Figure 7-66 Vector Control Register for MSI-X Table Entries

Table 7-55 Vector Control Register for MSI-X Table Entries

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 0 | Mask Bit - When this bit is Set, the Function is prohibited from sending a message using this MSI-X Table entry. However, any other MSI-X Table entries programmed with the same vector will still be capable of sending an equivalent message unless they are also masked. <br> Default value of this bit is 1 b (entry is masked) | RW |
| $15: 1$ | Reserved <br> Reserved - By default, the value of these bits must be 0 . However, for potential future use, software must preserve the value of these Reserved bits when modifying the value of other Vector Control bits. If software modifies the value of these Reserved bits, the result is undefined. <br> These bits are permitted to be RsvdP or read-write. | RW or RsvdP |
| $23: 16$ | ST Lower - If the Function implements a TPH Requester Extended Capability structure, and the ST Table Location indicates a value of 10b, then this field contains the lower 8 bits of a Steering Tag and must be read-write. <br> Otherwise, this field is permitted to be read-write or RsvdP, and for potential future use, software must preserve the value of these Reserved bits when modifying the value of other Vector Control bits, or the result is undefined. <br> Default value of this field is 00 h . | RW/RsvdP |
| $31: 24$ | ST Upper - If the Function implements a TPH Requester Extended Capability structure, and the ST Table Location indicates a value of 10b, and the Extended TPH Requester Supported bit is Set, then this field contains the upper 8 bits of a Steering Tag and must be read-write. <br> Otherwise, this field is permitted to be read-write or RsvdP, and for potential future use, software must preserve the value of these Reserved bits when modifying the value of other Vector Control bits, or the result is undefined. <br> Default value of this field is 00 h . | RW/RsvdP |

# 7.7.2.9 Pending Bits Register for MSI-X PBA Entries 

Figure 7-67 Pending Bits Register for MSI-X PBA Entries

Table 7-56 Pending Bits Register for MSI-X PBA Entries

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 63:0 | Pending Bits - For each Pending Bit that is Set, the Function has a pending message for the associated <br> MSI-X Table entry. <br> Pending bits that have no associated MSI-X Table entry are Reserved. By default, the value of Reserved <br> Pending bits must be Ob. <br> Software should never write, and should only read Pending Bits. If software writes to Pending Bits, the <br> result is undefined. <br> Default value of each Pending Bit is Ob. <br> These bits are permitted to be read-only or read-write. | RO or RW |

# 7.7.3 Secondary PCI Express Extended Capability 

The Secondary PCI Express Extended Capability structure must be implemented in any Function or RCRB where any of the following are true:

- The Supported Link Speeds Vector field indicates that the Link supports Link Speeds of 8.0 GT/s or higher (see § Section 7.5.3.18 or § Section 7.9.9.2).
- Any bit in the Lower SKP OS Generation Supported Speeds Vector field is Set (see § Section 7.5.3.18).
- When Lane based errors are reported in the Lane Error Status register (discussed in § Section 4.2.7).

To support future additions to this capability, this capability is permitted in any Function or RCRB associated with a Link. For a Multi-Function Device associated with an Upstream Port, this capability is permitted only in Function 0 of the Device.

![img-63.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-63.jpeg)

Figure 7-68 Secondary PCI Express Extended Capability Structure

# 7.7.3.1 Secondary PCI Express Extended Capability Header (Offset 00h) 

![img-64.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-64.jpeg)

Figure 7-69 Secondary PCI Express Extended Capability Header

Table 7-57 Secondary PCI Express Extended Capability Header

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| $15: 0$ | PCI Express Extended Capability ID - This field is a PCI-SIG defined ID number that indicates the nature <br> and format of the Extended Capability. <br> PCI Express Extended Capability ID for the Secondary PCI Express Extended Capability is 0019h. | RO |
| $19: 16$ | Capability Version - This field is a PCI-SIG defined version number that indicates the version of the <br> Capability structure present. <br> Must be 1h for this version of the specification. | RO |
| $31: 20$ | Next Capability Offset - This field contains the offset to the next PCI Express Extended Capability <br> structure or 000h if no other items exist in the linked list of Capabilities. | RO |

### 7.7.3.2 Link Control 3 Register (Offset 04h)

![img-65.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-65.jpeg)

Figure 7-70 Link Control 3 Register

Table 7-58 Link Control 3 Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :-- |
| 0 | Perform Equalization - When this bit is 1 b and a 1 b is written to the Retrain Link bit with the Target Link <br> Speed field set to 8.0 GT/s or higher, the Downstream Port must perform Link Equalization. Refer to <br> $\S$ Section 4.2.4 and $\S$ Section 4.2.7.4.2 for details. <br> This bit is RW for Downstream Ports and for Upstream Ports when Crosslink Supported is 1b (see $\S$ Section <br> 7.5.3.18). This bit is not applicable and is RsvdP for Upstream Ports when the Crosslink Supported bit is <br> 0b. <br> The default value is 0 b. <br> If the Port does not support $8.0 \mathrm{GT} / \mathrm{s}$, this bit is permitted to be hardwired to 0 b. | RW/RsvdP |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 1 | Link Equalization Request Interrupt Enable - When Set, this bit enables the generation of an interrupt to indicate that the Link Equalization Request 8.0 GT/s bit, the Link Equalization Request 16.0 GT/s bit, the Link Equalization Request 32.0 GT/s bit, or the Link Equalization Request 64.0 GT/s bit has been Set. <br> The interrupt vector is Interrupt Message Number (see § Section 7.5.3.2). <br> This bit is RW for Downstream Ports and for Upstream Ports when Crosslink Supported is 1b (see § Section 7.5.3.18). This bit is not applicable and is RsvdP for Upstream Ports when the Crosslink Supported bit is 0b. <br> The default value for this bit is 0 b . <br> If the Port does not support $8.0 \mathrm{GT} / \mathrm{s}$, this bit is permitted to be hardwired to 0 b . | RW/RsvdP |
| 9:15 | Enable Lower SKP OS Generation Vector - When the Link is in L0 and the bit in this field corresponding to the Current Link Speed is Set, SKP Ordered Sets are scheduled at the rate defined for SRNS, overriding the rate required based on the clock tolerance architecture. See § Section 4.2.8 and § Section 4.2.8.4 for additional requirements. <br> Bit definitions within this field are: | RW/RsvdP |
|  | Bit 0 | 2.5 GT/s |
|  | Bit 1 | $5.0 \mathrm{GT} / \mathrm{s}$ |
|  | Bit 2 | $8.0 \mathrm{GT} / \mathrm{s}$ |
|  | Bit 3 | $16.0 \mathrm{GT} / \mathrm{s}$ |
|  | Bit 4 | $32.0 \mathrm{GT} / \mathrm{s}$ |
|  | Bit 5 | $64.0 \mathrm{GT} / \mathrm{s}$ |
|  | Bit 6 | RsvdP |
|  | Each unreserved bit in this field must be RW if the corresponding bit in the Lower SKP OS Generation Supported Speeds Vector is Set, otherwise the bit must be RW or hardwired to 0 . <br> Behavior is undefined if a bit is Set in this field and the corresponding bit in the Lower SKP OS Generation Supported Speeds Vector is not Set. <br> The default value of this field is 0000000 b . |  |

# 7.7.3.3 Lane Error Status Register (Offset 08h) 

The Lane Error Status Register consists of a 32-bit vector, where each bit indicates if the Lane with the corresponding Lane number detected an error. This Lane number is the default Lane number which is invariant to Link width and Lane reversal negotiation that occurs during Link training.
![img-66.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-66.jpeg)

Figure 7-71 Lane Error Status Register

Table 7-59 Lane Error Status Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 31:0 | Lane Error Status Bits - Each bit indicates if the corresponding Lane detected a Lane-based error. A value of 1 b indicates that a Lane based-error was detected on the corresponding Lane Number (see $\S$ Section 4.2.2.3.3, $\S$ Section 4.2.2.3.4, $\S$ Section 4.2.7, and $\S$ Section 4.2.8.2 for details). <br> The default value of each bit is 0 b . <br> For Ports that are narrower than 32 Lanes, the unused upper bits [31: Maximum Link Width] are RsvdZ. <br> For Ports that do not support $8.0 \mathrm{GT} / \mathrm{s}$ and do not set these bits based on 8b/10b errors (optional, see $\S$ Section 4.2.7), this field is permitted to be hardwired to 0 . | RW1CS |

# 7.7.3.4 Lane Equalization Control Register (Offset 0Ch) 

The Lane Equalization Control Register consists of control fields required for per-Lane 8.0 GT/s equalization and the number of entries in this register are sized by Maximum Link Width (see $\S$ Section 7.5.3.6). Each entry contains the values for the Lane with the corresponding default Lane number which is invariant to Link width and Lane reversal negotiation that occurs during Link training.

If the Port does not support $8.0 \mathrm{GT} / \mathrm{s}$, this register is permitted to be hardwired to 0 .
![img-67.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-67.jpeg)

Figure 7-72 Lane Equalization Control Register
![img-68.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-68.jpeg)

Figure 7-73 Lane Equalization Control Register Entry

Table 7-60 Lane Equalization Control Register Entry

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 3:0 | Downstream Port 8.0 GT/s Transmitter Preset - Transmitter preset value used for 8.0 GT/s equalization by this Port when the Port is operating as a Downstream Port. This field is ignored when | $\begin{gathered} \text { HwInit/RsvdP } \\ \text { (see } \\ \text { description) } \end{gathered}$ |

| Bit Location | Register Description |  | Attributes |
| :--: | :--: | :--: | :--: |
|  | the Port is operating as an Upstream Port. See § Chapter 8. for details. The field encodings are defined in § Section 4.2.4.2 . <br> For an Upstream Port if Crosslink Supported is 0b, this field is RsvdP. Otherwise, this field is HwInit. See § Section 7.5.3.18. <br> The default value is 1111 b . |  |  |
| $6: 4$ | Downstream Port 8.0 GT/s Receiver Preset Hint - Receiver preset hint value that may be used as a suggested setting for 8.0 GT/s receiver equalization by this Port when the Port is operating as a Downstream Port. This field is ignored when the Port is operating as an Upstream Port. See § Chapter 8. for details. The field encodings are defined in § Section 4.2.4.2 . <br> For an Upstream Port if Crosslink Supported is 0b, this field is RsvdP. Otherwise, this field is HwInit. See § Section 7.5.3.18. <br> The default value is 111 b . |  | HwInit/RsvdP (see description) |
| $11: 8$ | Upstream Port 8.0 GT/s Transmitter Preset - Field contains the Transmitter preset value sent or received during 8.0 GT/s Link Equalization. Field usage varies as follows: |  | HwInit/RO (see description) |
|  | Operating Port Direction | Crosslink Supported | Usage |
| A | Downstream Port | Any | Field contains the value sent on the associated Lane during Recovery.RcvrCfg. <br> Field is HwInit. |
| B | Upstream Port | 0b | Field is intended for debug and diagnostics. It contains the value captured from the associated Lane during Link Equalization. <br> This value MUST@FLIT be captured from EQ TS2 or equalization requests with Use_Preset Set are received. This value should not be affected by equalization requests with Use_Preset Clear. <br> Field is RO. <br> Note: When crosslinks are supported, case C (below) applies and this captured information is not visible to software. Vendors are encouraged to provide an alternate mechanism to obtain this information. |
| C | Upstream Port | 1b | Field is not used or affected by the current Link Equalization. <br> Field value will be used if a future crosslink negotiation switches the Operating Port Direction so that case A (above) applies. <br> Field is HwInit. |

See § Section 4.2.4 and § Chapter 8. for details. The field encodings are defined in § Section 4.2.4.2.
The default value is 1111 b .

| Bit Location | Register Description |  | Attributes |
| :--: | :--: | :--: | :--: |
| 14:12 | Upstream Port 8.0 GT/s Receiver Preset Hint - Field contains the Receiver preset hint value sent or received during 8.0 GT/s Link Equalization. Field usage varies as follows: |  | ![img-69.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-69.jpeg) |
|  | Operating Port Direction | Crosslink Supported | Usage |
| A | Downstream Port | Any | Field contains the value sent on the associated Lane during Recovery.RcvrCfg. <br> Field is HwInit. |
| B | Upstream Port | 0b | Field is intended for debug and diagnostics. It contains the value captured from the associated Lane during Link Equalization. <br> This value MUST@FLIT be captured from EQ TS2 or equalization requests with Use_Preset Set are received. This value should not be affected by equalization requests with Use_Preset Clear. <br> Field is RO. <br> Note: When crosslinks are supported, case C (below) applies and this captured information is not visible to software. Vendors are encouraged to provide an alternate mechanism to obtain this information. |
| C | Upstream Port | 1b | Field is not used or affected by the current Link Equalization. <br> Field value will be used if a future crosslink negotiation switches the Operating Port Direction so that case A (above) applies. <br> Field is HwInit. |

See § Section 4.2.4 and § Chapter 8. for details. The field encodings are defined in § Section 4.2.4.2 .
The default value is 111 b .

# 7.7.4 Data Link Feature Extended Capability 

The Data Link Feature Capability is an optional Extended Capability that is required for Downstream Ports that support one or more of the associated features. Since the Scaled Flow Control Feature is required for Ports that support 16.0 GT/ s, this capability is required for Downstream Ports that support $16.0 \mathrm{GT} / \mathrm{s}$ (see $\S$ Section 3.4.2). It is optional in other Downstream Ports. It is optional in Functions associated with an Upstream Port. In Multi-Function Devices associated with an Upstream Port, this capability is individually optional for each non-VF Function, and all implemented instances of this capability must report identical information in all fields of this capability. It is not applicable in Functions that are not associated with a Port (e.g., RCiEPs, Root Complex Event Collectors). The Data Link Feature Extended Capability is shown in § Figure 7-74.

![img-70.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-70.jpeg)

Figure 7-74 Data Link Feature Extended Capability

# 7.7.4.1 Data Link Feature Extended Capability Header (Offset 00h) 

\$ Figure 7-75 details allocation of register fields in the Data Link Feature Extended Capability Header; \$ Table 7-63 provides the respective bit definitions.
![img-71.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-71.jpeg)

Figure 7-75 Data Link Feature Extended Capability Header

Table 7-63 Data Link Feature Extended Capability Header

| Bit Location | Description | Attributes |
| :--: | :--: | :--: |
| $15: 0$ | PCI Express Extended Capability ID - This field is a PCI-SIG defined ID number that indicates the nature and format of the Extended Capability. <br> Extended Capability ID for Data Link Feature is 0025 h. | RO |
| $19: 16$ | Capability Version - This field is a PCI-SIG defined version number that indicates the version of the Capability structure present. <br> Must be 1 h for this version of the specification. | RO |
| $31: 20$ | Next Capability Offset - This field contains the offset to the next PCI Express Capability structure or 000h if no other items exist in the linked list of Capabilities. <br> For Extended Capabilities implemented in Configuration Space, this offset is relative to the beginning of PCI-compatible Configuration Space and thus must always be either 000 h (for terminating list of Capabilities) or greater than 0 FFh . <br> The bottom 2 bits of this offset are Reserved and must be implemented as 00b although software must mask them to allow for future uses of these bits. | RO |

# 7.7.4.2 Data Link Feature Capabilities Register (Offset 04h) 

§ Figure 7-76 details allocation of register fields in the Data Link Feature Capabilities register; § Table 7-64 provides the respective bit definitions.

When this Port sends a Data Link Feature DLLP, the Feature Support field in Symbols 1, 2, and 3 of that DLLP contains bits [22:16], [15:8], and [7:0] of this register respectively (See § Figure 3-14).
![img-72.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-72.jpeg)

Figure 7-76 Data Link Feature Capabilities Register

Table 7-64 Data Link Feature Capabilities Register

| Bit Location | Description | Attributes |
| :--: | :--: | :--: |
| 22:0 | Local Data Link Feature Supported - This field contains the Feature Supported value used when this Port sends a Data Link Feature DLLP (see § Figure 3-14). Defined features are: | HwInit/RsvdP |
|  | Bit 0 | Local Scaled Flow Control Supported - Data Link Feature |
|  |  | This bit indicates that this Port supports the Scaled Flow Control Feature (see § Section 3.4.2). |
|  | Bit 1 | Local Immediate Readiness - Data Link Parameter |
|  |  | This bit indicates that all non-Virtual Functions in this Port have Immediate Readiness Set (see § Section 7.5.1.1.4). |
|  |  | This bit MUST@FLIT be meaningful. In Non-Flit Mode, this bit is meaningful when Set, but when Clear indicates either that some non-Virtual Function has Immediate Readiness Clear or that this Port is not providing this information. |
|  | Bits 4:2 | Local Extended VC Count - Data Link Parameter |
|  |  | This is the maximum number of Virtual Channels that can simultaneously be enabled, taking into account the Extended VC Count field in the Multi-Function Virtual Channel Extended Capability or the Virtual Channel Extended Capability (with Capability ID 0002h), and the SVC Extended VC Count field in the Streamlined Virtual Channel Extended Capability. |
|  |  | This field is meaningful in Flit Mode. In Non-Flit Mode, this field must be zero. |
|  | Bits 7:5 | Local LOp Exit Latency - Data Link Parameter |
|  |  | This field indicates this Port's knowledge of LOp Exit Latency. The value reported is the larger of Port LOp Exit Latency and Retimer LOp Exit Latency. The actual time required to widen the Link is the larger of Local LOp Exit Latency and Remote LOp Exit Latency. |
|  |  | These values are a hint that approximates the typical exit latency. This value is used by the implementation specific LOp policy mechanism to help determine when it is reasonable to use LOp (and to what widths). The underlying implementation is permitted to take longer as permitted by § Section 4.2.6.7. |
|  |  | The Downstream Port's Retimer LOp Exit Latency should include retimers that are part of the "system". |

| Bit Location | Description | Attributes |
| :--: | :--: | :--: |
|  | The Upstream Port's Retimer LOp Exit Latency should include retimers that are part of the "add-in card". |  |
|  | Defined encodings are: |  |
|  | 000b | Less than $1 \mu \mathrm{~s}$ |
|  | 001b | Less than $2 \mu \mathrm{~s}$ |
|  | 010b | Less than $4 \mu \mathrm{~s}$ |
|  | 011b | Less than $8 \mu \mathrm{~s}$ |
|  | 100b | Less than $16 \mu \mathrm{~s}$ |
|  | 101b | Less than $32 \mu \mathrm{~s}$ |
|  | 110b | Less than $64 \mu \mathrm{~s}$ |
|  | 111b | More than $64 \mu \mathrm{~s}$ |
|  | This field is meaningful in Flit Mode. In Non-Flit Mode, this field is Reserved. |  |
|  | Bits 22:8 RsvdP |  |
|  | Other bits in this field are RsvdP. |  |
| 31 | Data Link Feature Exchange is Enabled - If Set, indicates that this Port will enter the DL_Feature negotiation state (see § Section 3.2.1). | HwInit |

# 7.7.4.3 Data Link Feature Status Register (Offset 08h) 

§ Figure 7-77 details allocation of register fields in the Data Link Feature Status Register; § Table 7-65 provides the respective bit definitions.
![img-73.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-73.jpeg)

Figure 7-77 Data Link Feature Status Register

Table 7-65 Data Link Feature Status Register

| Bit Location | Description | Attributes |
| :--: | :--: | :--: |
| 22:0 | Remote Data Link Feature Supported - These bits indicate that the Remote Port supports the corresponding Data Link Feature. These bits capture all information from the Feature Supported field of the Data Link Feature DLLP even when this Port doesn't support the corresponding feature. <br> This field is Cleared on entry to state DL_Inactive (see § Section 3.2.1). <br> Features currently defined are: | RO |
|  | Bit 0 | Remote Scaled Flow Control Supported - Data Link Feature |
|  |  | This bit indicates that the Remote Port supports the Scaled Flow Control Feature (see § Section 3.4.2). |
|  | Bit 1 | Remote Immediate Readiness - Data Link Parameter |

| Bit Location | Description | Attributes |
| :--: | :--: | :--: |
|  | This bit indicates that all non-Virtual Functions in the Remote Port have Immediate Readiness Set (see § Section 7.5.1.1.4). <br> In Flit Mode, this bit is always meaningful. In Non-Flit Mode, this bit is meaningful when Set, but when Clear indicates either that some non-Virtual Function has Immediate Readiness Clear or that the Remote Port is not providing this information. |  |
|  | Bits 4:2 <br> Extended VC Count - Data Link Parameter <br> This is the maximum number of Virtual Channels that can simultaneously be enabled, taking into account the Extended VC Count field in the Multi-Function Virtual Channel Extended Capability or the Virtual Channel Extended Capability (with Capability ID 0002h), and the SVC Extended VC Count field in the Streamlined Virtual Channel Extended Capability. <br> This field is meaningful in Flit Mode. In Non-Flit Mode, this field must be zero. |  |
|  | Bits 7:5 | Remote LOp Exit Latency - Data Link Parameter <br> This field indicates the remote Port's LOp Exit Latency. The value reported indicates the length of time the remote Port requires to complete widening a link using LOp. If the remote Port does not support LOp, this field must contain 000b. <br> These values are a hint that approximates the typical exit latency. This value is used by the implementation specific LOp policy mechanism to help determine when it is reasonable to use LOp (and to what widths). The underlying implementation is permitted to take longer as permitted by $\S$ Section 4.2.6.7. |
|  |  | Defined encodings are: |
|  | 000b | Less than $1 \mu \mathrm{~s}$ |
|  | 001b | Less than $2 \mu \mathrm{~s}$ |
|  | 010b | Less than $4 \mu \mathrm{~s}$ |
|  | 011b | Less than $8 \mu \mathrm{~s}$ |
|  | 100b | Less than $16 \mu \mathrm{~s}$ |
|  | 101b | Less than $32 \mu \mathrm{~s}$ |
|  | 110b | Less than $64 \mu \mathrm{~s}$ |
|  | 111b | More than $64 \mu \mathrm{~s}$ |
|  | This field is meaningful in Flit Mode. In Non-Flit Mode, this field is Reserved. |  |
|  | Bits 22:8 <br> Default is 000000 h | Reserved |
| 31 | Remote Data Link Feature Supported Valid - This bit indicates that the Port has received a Data Link Feature DLLP in state DL_Feature (see § Section 3.2.1) and that the Remote Data Link Feature Supported field is meaningful. This bit is Cleared on entry to state DL_Inactive (see § Section 3.2.1). <br> Default is Ob. | RO |

# 7.7.5 Physical Layer 16.0 GT/s Extended Capability 

The Physical Layer 16.0 GT/s Extended Capability structure must be implemented in:

- A Function associated with a Downstream Port where the Supported Link Speeds Vector field indicates support for a Link speed of $16.0 \mathrm{GT} / \mathrm{s}$.

- A Function of a Single-Function Device associated with an Upstream Port where the Supported Link Speeds Vector field indicates support for a Link speed of $16.0 \mathrm{GT} / \mathrm{s}$.
- Function 0 (and only Function 0) of a Multi-Function Device associated with an Upstream Port where the Supported Link Speeds Vector field indicates support for a Link speed of $16.0 \mathrm{GT} / \mathrm{s}$.

This capability is permitted to be implemented in any of the Functions listed above even if the $16.0 \mathrm{GT} / \mathrm{s}$ Link speed is not supported. Implementing this capability is strongly recommended for $8.0 \mathrm{GT} / \mathrm{s}$ only Flit Mode components. In Non-Flit Mode, when the $16.0 \mathrm{GT} / \mathrm{s}$ Link speed is not supported and in Flit Mode, when the $8.0 \mathrm{GT} / \mathrm{s}$ Link speed is not supported, the behavior of registers other than the Capability Header is undefined. In Flit Mode, operating at $8.0 \mathrm{GT} / \mathrm{s}$, the Capability Header, 16.0 GT/s Local Data Parity Register, 16.0 GT/s First Retimer Data Parity Register, and 16.0 GT/s Second Retimer Data Parity Register are meaningful.
§ Figure 7-79 details allocation of register fields in the Physical Layer 16.0 GT/s Extended Capability structure.
![img-74.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-74.jpeg)

Figure 7-78 Physical Layer 16.0 GT/s Extended Capability

# 7.7.5.1 Physical Layer 16.0 GT/s Extended Capability Header (Offset 00h) 

![img-75.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-75.jpeg)

Figure 7-79 Physical Layer 16.0 GT/s Extended Capability Header

Table 7-66 Physical Layer 16.0 GT/s Extended Capability Header

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $15: 0$ | PCI Express Extended Capability ID - This field is a PCI-SIG defined ID number that indicates the nature and format of the Extended Capability. <br> The Extended Capability ID for the Physical Layer 16.0 GT/s Capability is 0026h. | RO |
| $19: 16$ | Capability Version - This field is a PCI-SIG defined version number that indicates the version of the Capability structure present. <br> Must be 1 h for this version of the specification. | RO |
| $31: 20$ | Next Capability Offset - This field contains the offset to the next PCI Express Capability structure or 000h if no other items exist in the linked list of Capabilities. <br> For Extended Capabilities implemented in Configuration Space, this offset is relative to the beginning of PCI-compatible Configuration Space and thus must always be either 000 h (for terminating list of Capabilities) or greater than 0FFh. | RO |

### 7.7.5.2 16.0 GT/s Capabilities Register (Offset 04h) 

![img-76.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-76.jpeg)

Figure 7-80 16.0 GT/s Capabilities Register

Table 7-67 16.0 GT/s Capabilities Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| $31: 0$ | RsvdP RsvdP | RsvdP |

# 7.7.5.3 16.0 GT/s Control Register (Offset 08h) 

![img-77.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-77.jpeg)

Figure 7-81 16.0 GT/s Control Register

Table 7-68 16.0 GT/s Control Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :-- |
| 31:0 | RsvdP RsvdP | RsvdP |

### 7.7.5.4 16.0 GT/s Status Register (Offset 0Ch)

![img-78.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-78.jpeg)

Figure 7-82 16.0 GT/s Status Register

Table 7-69 16.0 GT/s Status Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :-- |
| 0 | Equalization 16.0 GT/s Complete - When Set, this bit indicates that the 16.0 GT/s Transmitter <br> Equalization procedure has completed. Details of the Transmitter Equalization process and when <br> this bit needs to be set to 1 b is provided in $\S$ Section 4.2.7.4.2 . <br> The default value of this bit is 0 b. <br> For a Multi-Function Upstream Port, this bit must be implemented in Function 0 and RsvdZ in other <br> Functions. | ROS/RsvdZ |
| 1 | Equalization 16.0 GT/s Phase 1 Successful - When set to 1b, this bit indicates that Phase 1 of the <br> 16.0 GT/s Transmitter Equalization procedure has successfully completed. Details of the Transmitter <br> Equalization process and when this bit needs to be set to 1 b is provided in $\S$ Section 4.2.7.4.2 . <br> The default value of this bit is 0 b. <br> For a Multi-Function Upstream Port, this bit must be implemented in Function 0 and RsvdZ in other <br> Functions. | ROS/RsvdZ |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 2 | Equalization 16.0 GT/s Phase 2 Successful - When set to 1b, this bit indicates that Phase 2 of the 16.0 GT/s Transmitter Equalization procedure has successfully completed. Details of the Transmitter Equalization process and when this bit needs to be set to 1 b is provided in $\S$ Section 4.2.7.4.2 . <br> The default value of this bit is 0 b . <br> For a Multi-Function Upstream Port, this bit must be implemented in Function 0 and RsvdZ in other Functions. | ROS/RsvdZ |
| 3 | Equalization 16.0 GT/s Phase 3 Successful - When set to 1b, this bit indicates that Phase 3 of the 16.0 GT/s Transmitter Equalization procedure has successfully completed. Details of the Transmitter Equalization process and when this bit needs to be set to 1 b is provided in $\S$ Section 4.2.7.4.2 . <br> The default value of this bit is 0 b . <br> For a Multi-Function Upstream Port, this bit must be implemented in Function 0 and RsvdZ in other Functions. | ROS/RsvdZ |
| 4 | Link Equalization Request 16.0 GT/s - This bit is Set by hardware to request the 16.0 GT/s Link equalization process to be performed on the Link. Refer to § Section 4.2.4 and § Section 4.2.7.4.2 for details. <br> The default value of this bit is 0 b . <br> For a Multi-Function Upstream Port, this bit must be implemented in Function 0 and RsvdZ in other Functions. | RW1CS/RsvdZ |

# 7.7.5.5 16.0 GT/s Local Data Parity Mismatch Status Register (Offset 10h) 

The 16.0 GT/s Local Data Parity Mismatch Status Register is a 32-bit vector where each bit indicates if the local Receiver detected a Data Parity mismatch on the Lane with the corresponding Lane number. This Lane number is the default Lane number which is invariant to Link width and Lane reversal negotiation that occurs during Link training.

This register collects parity errors for 16.0 GT/s and higher data rates as well as 8.0 GT/s data rate in Flit Mode. When tracking errors for a specific Link Speed, software should clear this register on speed changes.
![img-79.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-79.jpeg)

Table 7-70 16.0 GT/s Local Data Parity Mismatch Status Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $31: 0$ | Local Data Parity Mismatch Status - Each bit indicates if the corresponding Lane detected a Data Parity mismatch. A value of 1 b indicates that a mismatch was detected on the corresponding Lane Number. See $\S$ Section 4.2.8.2 for more information. <br> The default value of each bit is 0 b . <br> For Ports that are narrower than 32 Lanes, the unused upper bits [31: Maximum Link Width] are RsvdZ. | RW1CS/RsvdZ |

# 7.7.5.6 16.0 GT/s First Retimer Data Parity Mismatch Status Register (Offset 14h) 

The 16.0 GT/s First Retimer Data Parity Mismatch Status register is a 32-bit vector where each bit indicates if the first Retimer of a Path (see § Figure 4-80 for more information) detected a Data Parity mismatch on the Lane with the corresponding Lane number. This Lane number is the default Lane number which is invariant to Link width and Lane reversal negotiation that occurs during Link training.

This register collects parity errors for $16.0 \mathrm{GT} / \mathrm{s}$ and higher data rates as well as $8.0 \mathrm{GT} / \mathrm{s}$ data rate in Flit Mode. When tracking errors for a specific Link Speed, software should clear this register on speed changes.
![img-80.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-80.jpeg)

Figure 7-84 16.0 GT/s First Retimer Data Parity Mismatch Status Register

Table 7-71 16.0 GT/s First Retimer Data Parity Mismatch Status Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 31:0 | First Retimer Data Parity Mismatch Status - Each bit indicates if the corresponding Lane detected <br> a Data Parity mismatch. A value of 1 b indicates that a mismatch was detected on the corresponding <br> Lane Number. See § Section 4.2.8.2 for more information. <br> The default value of each bit is 0 b . <br> The value of this field is undefined when no Retimers are present. <br> For Ports that are narrower than 32 Lanes, the unused upper bits [31: Maximum Link Width] are <br> RsvdZ. | RW1CS/RsvdZ |

### 7.7.5.7 16.0 GT/s Second Retimer Data Parity Mismatch Status Register (Offset 18h)

The 16.0 GT/s Second Retimer Data Parity Mismatch Status Register is a 32-bit vector where each bit indicates if the second Retimer of a Path (see § Figure 4-80 for more information) detected a Data Parity mismatch on the Lane with the corresponding Lane number. This Lane number is the default Lane number which is invariant to Link width and Lane reversal negotiation that occurs during Link training.

This register collects parity errors for $16.0 \mathrm{GT} / \mathrm{s}$ and higher data rates as well as $8.0 \mathrm{GT} / \mathrm{s}$ data rate in Flit Mode. When tracking errors for a specific Link Speed, software should clear this register on speed changes.
![img-81.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-81.jpeg)

Figure 7-85 16.0 GT/s Second Retimer Data Parity Mismatch Status Register

Table 7-72 16.0 GT/s Second Retimer Data Parity Mismatch Status Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 31:0 | Second Retimer Data Parity Mismatch Status - Each bit indicates if the corresponding Lane detected a Data Parity mismatch. A value of 1 b indicates that a mismatch was detected on the corresponding Lane Number. See $\S$ Section 4.2.8.2 for more information. <br> The default value of each bit is 0 b. <br> The value of this field is undefined when no Retimers are present or only one Retimer is present. <br> For Ports that are narrower than 32 Lanes, the unused upper bits [31: Maximum Link Width] are RsvdZ. | RW1CS/RsvdZ |

# 7.7.5.8 Physical Layer 16.0 GT/s Reserved (Offset 1Ch) 

This register is RsvdP.

### 7.7.5.9 16.0 GT/s Lane Equalization Control Register (Offsets 20h to 3Ch)

The Equalization Control register consists of control fields required for per-Lane 16.0 GT/s equalization. It contains entries for at least the number of Lanes defined by the Maximum Link Width (see $\S$ Section 7.5.3.6 or $\S$ Section 7.9.9.2), must be implemented in whole DW granularity (e.g., if the Maximum Link Width is $\times 1$, the register will still contain entries for 4 Lanes with the entries for Lanes 1, 2 and 3 being undefined), and it is permitted to contain up to 32 entries regardless of the Maximum Link Width. The value of entries beyond the Maximum Link Width is undefined.

Each entry contains the values for the Lane with the corresponding default Lane number which is invariant to Link width and Lane reversal negotiation that occurs during Link training.
![img-82.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-82.jpeg)

Figure 7-86 16.0 GT/s Lane Equalization Control Register Entry

Table 7-73 16.0 GT/s Lane Equalization Control Register Entry

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 3:0 | Downstream Port 16.0 GT/s Transmitter Preset - Transmitter Preset used for 16.0 GT/s equalization by this Port when the Port is operating as a Downstream Port. This field is ignored when the Port is operating as an Upstream Port. See § Chapter 8. for details. The field encodings are defined in § Section 4.2.4.2 . <br> For an Upstream Port if Crosslink Supported is 0b, this field is RsvdP. Otherwise, this field is HwInit. See § Section 7.5.3.18. <br> The default value is 1111 b . | HwInit/RsvdP (see description) |

| Bit Location | Register Description |  | Attributes |
| :--: | :--: | :--: | :--: |
| 7:4 | Upstream Port 16.0 GT/s Transmitter Preset - Field contains the Transmit Preset value sent or received during 16.0 GT/s Link Equalization. Field usage varies as follows: |  |  |
|  | Operating Port Direction | Crosslink Supported | Usage |
| A | Downstream Port | Any | Field contains the value sent on the associated Lane during Recovery.RcvrCfg. <br> Field is HwInit. |
| B | Upstream Port | 0b | Field is intended for debug and diagnostics. It contains the value captured from the associated Lane during Link Equalization. <br> This value MUST@FLIT be captured from 128b/130b EQ TS2 or equalization requests with Use_Preset Set are received. This value should not be affected by equalization requests with Use_Preset Clear. <br> Field is RO. <br> When crosslinks are supported, case C (below) applies and this captured information is not visible to software. Vendors are encouraged to provide an alternate mechanism to obtain this information. |
| C | Upstream Port | 1b | Field is not used or affected by the current Link Equalization. <br> Field value will be used if a future crosslink negotiation switches the Operating Port Direction so that case A (above) applies. <br> Field is HwInit. |

See § Section 4.2.4 and § Chapter 8. for details. The field encodings are defined in § Section 4.2.4.2 .
The default value is 1111 b .

# 7.7.6 Physical Layer 32.0 GT/s Extended Capability 

The Physical Layer 32.0 GT/s Extended Capability structure must be implemented in Ports where one or more of the following features are supported:

- The Supported Link Speeds Vector field indicates support for a Link speed of $32.0 \mathrm{GT} / \mathrm{s}$.
- The Function supports sending and/or receiving Modified TS1/TS2 Ordered Sets.

When implemented, this structure must be implemented in:

- A Function associated with a Downstream Port

- A Function of a Single-Function Device associated with an Upstream Port
- Function 0 (and only Function 0) of a Multi-Function Device associated with an Upstream Port

This capability is permitted to be implemented in any of the Functions listed above even if the 32.0 GT/s Link speed is not supported. When the 32.0 GT/s Link speed is not supported, the behavior of registers other than the Capability Header is undefined.
§ Figure 7-87 details allocation of register fields in the Physical Layer 32.0 GT/s Extended Capability structure.
Note that parity errors for 32.0 GT/s are recorded in 16.0 GT/s Local Data Parity Mismatch Status Register, 16.0 GT/s First Retimer Data Parity Mismatch Status Register, and 16.0 GT/s Second Retimer Data Parity Mismatch Status Register. When tracking errors for a specific Link Speed, software should clear those registers on speed changes.
![img-83.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-83.jpeg)

Figure 7-87 Physical Layer 32.0 GT/s Extended Capability

# 7.7.6.1 Physical Layer 32.0 GT/s Extended Capability Header (Offset 00h) 

![img-84.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-84.jpeg)

Figure 7-88 Physical Layer 32.0 GT/s Extended Capability Header

Table 7-75 Physical Layer 32.0 GT/s Extended Capability Header

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $15: 0$ | PCI Express Extended Capability ID - This field is a PCI-SIG defined ID number that indicates the nature and format of the Extended Capability. <br> The Extended Capability ID for the Physical Layer 32.0 GT/s Capability is 002Ah. | RO |
| $19: 16$ | Capability Version - This field is a PCI-SIG defined version number that indicates the version of the Capability structure present. <br> Must be 1 h for this version of the specification. | RO |
| $31: 20$ | Next Capability Offset - This field contains the offset to the next PCI Express Capability structure or 000h if no other items exist in the linked list of Capabilities. <br> For Extended Capabilities implemented in Configuration Space, this offset is relative to the beginning of PCI-compatible Configuration Space and thus must always be either 000 h (for terminating list of Capabilities) or greater than 0FFh. | RO |

### 7.7.6.2 32.0 GT/s Capabilities Register (Offset 04h)

![img-85.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-85.jpeg)

Figure 7-89 32.0 GT/s Capabilities Register

Table 7-76 32.0 GT/s Capabilities Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :-- |
| 0 | Equalization Bypass to Highest NRZ Rate Supported - When Set, this Port supports controlling whether <br> the Port negotiates to skip equalization for speeds other than the highest common supported speed. <br> See § Section 4.2.4 for details. <br> Must be 1b for Ports that support $32.0 \mathrm{GT} / \mathrm{s}$ or higher data rates. | HwInit |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 1 | No Equalization Needed Supported - When Set, this Port supports controlling whether or not Equalization is needed. | HwInit |
| 8 | Modified TS Usage Mode 0 Supported - PCI Express - This bit indicates that this Port supports PCI Express (Modified TS Usage 000b). This bit must be 1b. | RO |
| 9 | Modified TS Usage Mode 1 Supported - Training Set Message - This bit indicates that this Port supports sending and recieving vendor specific Training Set Messages (Modified TS Usage 001b). See § Section 4.2.5.2 for details. | HwInit |
| 10 | Modified TS Usage Mode 2 Supported - Alternate Protocol - This bit indicates that this Port supports negotiating to use alternate protocols (Modified TS Usage 010b). See § Section 4.2.5.2 for details. | HwInit |
| 15:11 | Modified TS Reserved Usage Modes - Reserved bits for future Usage Modes defined by the PCISIG. Must be 00000 b. | RO |

# 7.7.6.3 32.0 GT/s Control Register (Offset 08h) $\S$ 

![img-86.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-86.jpeg)

Figure 7-90 32.0 GT/s Control Register

Table 7-77 32.0 GT/s Control Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 0 | Equalization Bypass to Highest NRZ Rate Disable - When Clear, this Port is permitted to indicate during Link Training that it wishes to train to the highest common link NRZ data rate and skip equalization of intermediate data rates. See $\S$ Section 4.2.4 for details. <br> If Equalization Bypass to Highest NRZ Rate Supported is Set, this bit is RWS with a default value of 0b. If Equalization Bypass to Highest NRZ Rate Supported is Clear, this bit is permitted to be hardwired to Ob. | RWS/RO |
| 1 | No Equalization Needed Disable - When Clear, this Port is permitted to indicate that it does not require equalization. When Set, this Port must always indicate that it requires equalization. See § Section 4.2.4 for details. <br> If No Equalization Needed Supported is Set, this bit is RWS with a default value of Ob. <br> If No Equalization Needed Supported is Clear, this bit is permitted to be hardwired to Ob. | RWS/RO |
| 10:8 | Modified TS Usage Mode Selected - Thie field indicates which Usage Mode will be used by this Downstream Port the next time the Link enters L0 LTSSM State. See § Section 4.2.5.2 for details. <br> Behavior is undefined if this field indicates a Usage Mode that is not supported (i.e., associated Modified TS Usage Mode Supported bit is Clear). <br> Unused bits in this field are permitted to be hardwired to Ob. If the only supported usage mode is PCI Express, this field is permitted to be hardwired to 000b. | RWS/RO/RsvdP |

| Bit Location | Register Description | Attributes |
| :-- | :-- | :-- |
|  | This field is present in Downstream Ports. In Upstream Ports, this field is RsvdP. <br> Default is 000b. |  |

# 7.7.6.4 32.0 GT/s Status Register (Offset 0Ch) 

![img-87.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-87.jpeg)

Figure 7-91 32.0 GT/s Status Register

Table 7-78 32.0 GT/s Status Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 0 | Equalization 32.0 GT/s Complete - When Set, this bit indicates that the 32.0 GT/s Transmitter <br> Equalization procedure has completed. Details of the Transmitter Equalization process and when this bit needs to be set to 1 b is provided in $\S$ Section 4.2.7.4.2. <br> The default value of this bit is 0 b . <br> For a Multi-Function Upstream Port, this bit must be implemented in Function 0 and RsvdZ in other Functions. | ROS/RsvdZ |
| 1 | Equalization 32.0 GT/s Phase 1 Successful - When set to 1b, this bit indicates that Phase 1 of the 32.0 GT/s Transmitter Equalization procedure has successfully completed. Details of the Transmitter Equalization process and when this bit needs to be set to 1 b is provided in $\S$ Section 4.2.7.4.2 . <br> The default value of this bit is 0 b . <br> For a Multi-Function Upstream Port, this bit must be implemented in Function 0 and RsvdZ in other Functions. | ROS/RsvdZ |
| 2 | Equalization 32.0 GT/s Phase 2 Successful - When set to 1b, this bit indicates that Phase 2 of the 32.0 GT/s Transmitter Equalization procedure has successfully completed. Details of the Transmitter Equalization process and when this bit needs to be set to 1 b is provided in $\S$ Section 4.2.7.4.2 . <br> The default value of this bit is 0 b . <br> For a Multi-Function Upstream Port, this bit must be implemented in Function 0 and RsvdZ in other Functions. | ROS/RsvdZ |
| 3 | Equalization 32.0 GT/s Phase 3 Successful - When set to 1b, this bit indicates that Phase 3 of the 32.0 GT/s Transmitter Equalization procedure has successfully completed. Details of the Transmitter Equalization process and when this bit needs to be set to 1 b is provided in $\S$ Section 4.2.7.4.2 . | ROS/RsvdZ |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 4 | The default value of this bit is 0 b. <br> For a Multi-Function Upstream Port, this bit must be implemented in Function 0 and RsvdZ in other Functions. |  |
|  | Link Equalization Request 32.0 GT/s - This bit is Set by hardware to request the 32.0 GT/s Link equalization process to be performed on the Link. Refer to $\S$ Section 4.2.4 and $\S$ Section 4.2.7.4.2 for details. <br> The default value of this bit is 0 b. <br> For a Multi-Function Upstream Port, this bit must be implemented in Function 0 and RsvdZ in other Functions. | RW1CS/RsvdZ |
| 5 | Modified TS Received - If Set, Received Modified TS Data 1 Register and Received Modified TS Data 2 Register contain meaningful data. <br> This bit is Cleared when the Link is Down. This bit is Set when the Modified TS1/TS2 Ordered Set is received (See § Section 4.2.7.3.3 ). Default is 0 b. | RO |
| 7:6 | Received Enhanced Link Behavior Control - This field contains the Enhanced Link Behavior Control bits from the most recent TS1 or TS2 received in the Polling or Configuration states. See § Section 4.2.5.1, § Table 4-34 and § Table 4-35. <br> This field is Cleared on DL_Down. <br> Default is 00b. | RO |
| 8 | Transmitter Precoding On - This field indicates whether the Receiver asked this transmitter to enable Precoding. See § Section 4.2.2.5. This bit is cleared on DL_Down. <br> Default is 0b. | RO |
| 9 | Transmitter Precode Request - When Set, this Port will request the transmitter to use Precoding by setting the Transmitter Precode Request bit in the TS1s/TS2s it transmits prior to entry to Recovery.Speed (see § Section 4.2.2.5). <br> Default is Implementation Specific. | RO |
| 10 | No Equalization Needed Received - When Set, this Port either received a Modified TS1/TS2 with the No Equalization Needed bit Set or received a non-modified TS1/TS2 was received with the No Equalization Needed encoding (also reported in the Received Enhanced Link Behavior Control field). Default is 0b. | RO |

# 7.7.6.5 Received Modified TS Data 1 Register (Offset 10h) 

This register contains the values received in the Modified TS1/TS2 Ordered Set (see § Table 4-36).
If PCI Express (Usage Mode 0) is the only one supported by a Port, this register is permitted to be hardwired to 00000000 h .

| ![img-88.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-88.jpeg) |  |  |
| :--: | :--: | :--: |
|  | Receives Modified TS Vendor ID | Receives Modified TS Informatio 1 |
|  |  |  |

Figure 7-92 Received Modified TS Data 1 Register

Table 7-79 Received Modified TS Data 1 Register

| Bit <br> Location | Description | Attributes |
| :--: | :--: | :--: |
| $2: 0$ | Received Modified TS Usage Mode - If Modified TS Received is Set, this field contains the Modified TS Usage field from the Modified TS1/TS2 Ordered Set (see § Section 4.2.7.3.6). If Modified TS Received is Clear, this field contains 000b. <br> Unused bits in this field are permitted to be hardwired to 0b. If PCI Express (Usage Mode 0) is the only one supported, this field is permitted to be hardwired to 000b. <br> Default is 000b. | RO |
| $15: 3$ | Received Modified TS Information 1 - If Modified TS Received is Set, this field contains the Modified TS Information 1 field from the Modified TS1/TS2 Ordered Set (see § Section 4.2.7.3.6). If Modified TS Received is Clear, this field contains 0000000000000 b. <br> Bits 15:8 contain the value of Symbol 9. <br> Bits 7:3 contain bits 7:3 of Symbol 8. <br> If PCI Express (Usage Mode 0) is the only one supported, this field is permitted to be hardwired to 0000000000000 b. <br> Default is 0000000000000 b. | RO |
| $31: 16$ | Received Modified TS Vendor ID - If Modified TS Received is Set, this field contains the Training Set Message Vendor ID or Alternate Protocol Vendor ID field from the Modified TS1/TS2 Ordered Set received (see § Section 4.2.7.3.6). If Modified TS Received is Clear, this field contains 0000h. <br> Bits 15:8 contain the value of Symbol 11. <br> Bits 7:0 contain the value of Symbol 10. <br> If PCI Express (Usage Mode 0) is the only one supported, this field is permitted to be hardwired to 0000 h. Default is 0000 h . | RO |

# 7.7.6.6 Received Modified TS Data 2 Register (Offset 14h) 

This register contains the values received in Symbols 12 through 14 of the Modified TS1/TS2 (see § Table 4-36).
If Modified TS Usage Mode 1 Supported - Training Set Message and Modified TS Usage Mode 2 Supported - Alternate Protocol are both Clear, this register is permitted to be hardwired to 00000000 h.

![img-89.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-89.jpeg)

Figure 7-93 Received Modified TS Data 2 Register

Table 7-80 Received Modified TS Data 2 Register

| Bit Location | Description | Attributes |
| :--: | :--: | :--: |
| 23:0 | Received Modified TS Information 2 - If Modified TS Received is Set, this field contains the Modified TS Information 2 field from the received Modified TS1/TS2 Ordered Set (\$ Section 4.2.7.3.6). If Modified TS Received is Clear, this field contains 000000 h. <br> Bits 23:16 contain the value of Symbol 14. <br> Bits 16:8 contain the value of Symbol 13. <br> Bits 7:0 contain the value of Symbol 12. <br> If PCI Express (Usage Mode 0) is the only one supported, this field is permitted to be hardwired to 000000 h. Default is 000000 h . | RO |
| 25:24 | Alternate Protocol Negotiation Status - Indicates the status of the Alternate Protocol Negotiation. <br> Encodings are: <br> 00b Alternate Protocol Negotiation not supported <br> 01b Alternate Protocol Negotiation disabled <br> 10b Alternate Protocol Negotiation failed - Alternate Protocol Negotiation was attempted and did not locate a protocol that was supported on both ends of the Link. <br> 11b Alternate Protocol Negotiation succeeded - Alternate Protocol Negotiation located one or more protocols that were supported on both ends of the Link and the Downstream Port selected one of those protocols for use. <br> If 11b, Alternate Protocol Negotiation completed successfully. If not 11b, Alternate Protocol Negotiation has not completed successfully. If Modified TS Usage Mode 1 Supported - Training Set Message and Modified TS Usage Mode 2 Supported - Alternate Protocol are both Clear, this field is permitted to be hardwired to 00b. <br> If Modified TS Usage Mode 2 Supported - Alternate Protocol is Clear, this field is hardwired to 00b. <br> If Modified TS Usage Mode 2 Supported - Alternate Protocol is Set and Modified TS Usage Mode Selected does not equal 2, this field must return a non-11b value. This field is cleared to 00b on entering Detect. <br> Default is 00b. | RO |

# 7.7.6.7 Transmitted Modified TS Data 1 Register (Offset 18h) 

This register contains the values transmitted in the Modified TS1/TS2 Ordered Set (see § Table 4-36).
If PCI Express (Usage Mode 0) is the only one supported by a Port, this register is permitted to be hardwired to 00000000 h .

![img-90.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-90.jpeg)

Figure 7-94 Transmitted Modified TS Data 1 Register

Table 7-81 Transmitted Modified TS Data 1 Register

| Bit <br> Location | Description | Attributes |
| :--: | :--: | :--: |
| $2: 0$ | Transmitted Modified TS Usage Mode - If Modified TS Received is Set, this field contains the Modified TS Usage field from the Modified TS2 Ordered Set transmitted during the Configuration.Complete LTSSM State (see § Section 4.2.7.3.6). <br> Unused bits in this field are permitted to be hardwired to 0b. If PCI Express (Usage Mode 0) is the only one supported, this field is permitted to be hardwired to 000b. <br> Default is 000b. | RO |
| $15: 3$ | Transmitted Modified TS Information 1 - If Modified TS Received is Set, this field contains the Modified TS Information 1 field from Modified TS2 Ordered Set transmitted during the Configuration.Complete LTSSM State (see § Section 4.2.7.3.6). <br> Bits 15:8 contain the value of Symbol 9. <br> Bits 7:3 contain bits 7:3 of Symbol 8. <br> If PCI Express (Usage Mode 0) is the only one supported, this field is permitted to be hardwired to 000000000 0000b. <br> Default is 000000000 0000b. | RO |
| $31: 16$ | Transmitted Modified TS Vendor ID - If Modified TS Received is Set, this field contains the Training Set Message Vendor ID or Alternate Protocol Vendor ID field from the Modified TS2 Ordered Set transmitted during the Configuration.Complete LTSSM State (see § Section 4.2.7.3.6). <br> Bits 15:8 contain the value of Symbol 11. <br> Bits 7:0 contain the value of Symbol 10. <br> If PCI Express (Usage Mode 0) is the only one supported, this field is permitted to be hardwired to 0000 h . Default is 0000 h . | RO |

# 7.7.6.8 Transmitted Modified TS Data 2 Register (Offset 1Ch) 

This register contains the values received in Symbols 12 through 14 of the Modified TS1/TS2 (see § Table 4-36).
If Modified TS Usage Mode 1 Supported - Training Set Message and Modified TS Usage Mode 2 Supported - Alternate Protocol are both Clear, this register is permitted to be hardwired to 00000000 h.

![img-91.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-91.jpeg)

Figure 7-95 Transmitted Modified TS Data 2 Register

Table 7-82 Transmitted Modified TS Data 2 Register

| Bit <br> Location | Description | Attributes |
| :--: | :--: | :--: |
| 23:0 | Transmitted Modified TS Information 2 - If Modified TS Received is Set, this field contains the Modified TS Information 2 field from the Modified TS2 Ordered Set transmitted during the Configuration.Complete LTSSM State (see § Section 4.2.7.3.6). <br> Bits 23:16 contain the value of Symbol 14. <br> Bits 16:8 contain the value of Symbol 13. <br> Bits 7:0 contain the value of Symbol 12. <br> If PCI Express (Usage Mode 0) is the only one supported, this field is permitted to be hardwired to 000000 h. Default is 000000 h . | RO |
| 25:24 | Alternate Protocol Negotiation Status - Indicates the status of the Alternate Protocol Negotiation. <br> Encodings are: <br> 00b Alternate Protocol Negotiation not supported <br> 01b Alternate Protocol Negotiation disabled <br> 10b Alternate Protocol Negotiation failed - Alternate Protocol Negotiation was attempted and did not locate a protocol that was supported on both ends of the Link. <br> 11b Alternate Protocol Negotiation succeeded - Alternate Protocol Negotiation located one or more protocols that were supported on both ends of the Link and the Downstream Port selected one of those protocols for use. <br> If 11b, Alternate Protocol Negotiation completed successfully. If not 11b, Alternate Protocol Negotiation has not completed successfully. If Modified TS Usage Mode 1 Supported - Training Set Message and Modified TS Usage Mode 2 Supported - Alternate Protocol are both Clear, this field is permitted to be hardwired to 00b. <br> If Modified TS Usage Mode 2 Supported - Alternate Protocol is Clear, this field is hardwired to 00b. <br> If Modified TS Usage Mode 2 Supported - Alternate Protocol is Set and Modified TS Usage Mode Selected does not equal 2, this field must return a non-11b value. <br> This field is cleared to 00b on Detect. <br> Default is 00b. | RO |

# 7.7.6.9 32.0 GT/s Lane Equalization Control Register (Offset 20h) 

The 32.0 GT/s Equalization Control register consists of control fields required for per-Lane 32.0 GT/s equalization. It contains entries for at least the number of Lanes defined by the Maximum Link Width (see § Section 7.5.3.6 or § Section 7.9.9.2 ), must be implemented in whole DW granularity (e.g., if the Maximum Link Width is $\times 1$, the register will still contain entries for 4 Lanes with the entries for Lanes 1,2 and 3 being undefined), and it is permitted to contain up to 32 entries regardless of the Maximum Link Width. The value of entries beyond the Maximum Link Width is undefined.

Each entry contains the values for the Lane with the corresponding default Lane number which is invariant to Link width and Lane reversal negotiation that occurs during Link training.
![img-92.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-92.jpeg)

Figure 7-96 32.0 GT/s Lane Equalization Control Register Entry

Table 7-83 32.0 GT/s Lane Equalization Control Register Entry

| Bit Location | Register Description |  | Attributes |
| :--: | :--: | :--: | :--: |
| 3:0 | Downstream Port 32.0 GT/s Transmitter Preset - Transmitter Preset used for 32.0 GT/s equalization by this Port when the Port is operating as a Downstream Port. This field is ignored when the Port is operating as an Upstream Port. See § Chapter 8. for details. The field encodings are defined in § Section 4.2.4.2 . <br> For an Upstream Port if Crosslink Supported is 0b, this field is RsvdP. Otherwise, this field is HwInit. See § Section 7.5.3.18. <br> The default value is 1111 b . |  | HwInit/RsvdP (see description) |
| 7:4 | Upstream Port 32.0 GT/s Transmitter Preset - Field contains the Transmit Preset value sent or received during 32.0 GT/s Link Equalization. Field usage varies as follows: |  | HwInit/RO (see description) |
|  | Operating Port Direction | Crosslink Supported | Usage |
|  | A | Downstream Port | Any | Field contains the value sent on the associated Lane during Recovery.RcvrCfg. <br> Field is HwInit. |
|  | B | Upstream Port | 0b | Field is intended for debug and diagnostics. It contains the value captured from the associated Lane during Link Equalization. <br> This value MUST@FLIT be captured from 128b/130b EQ TS2 or equalization requests with Use_Preset Set are received. This value should not be affected by equalization requests with Use_Preset Clear. <br> Field is RO. <br> When crosslinks are supported, case C (below) applies and this captured information is not visible to software. Vendors are encouraged to provide an alternate mechanism to obtain this information. |
|  | C | Upstream Port | 1b | Field is not used or affected by the current Link Equalization. <br> Field value will be used if a future crosslink negotiation switches the Operating Port Direction so that case A (above) applies. <br> Field is HwInit. |

| Bit Location | Register Description | Attributes |
| :-- | :-- | :-- |
|  | See § Section 4.2.4 and § Chapter 8. for details. The field encodings are defined in § Section 4.2.4.2 . <br> The default value is 1111 b. |  |

# 7.7.7 Physical Layer 64.0 GT/s Extended Capability 

The Physical Layer 64.0 GT/s Extended Capability structure must be implemented in Ports where one or more of the following features are supported:

- The Supported Link Speeds Vector field indicates support for a Link speed of $64.0 \mathrm{GT} / \mathrm{s}$.

When implemented, this structure must be implemented in:

- A Function associated with a Downstream Port
- A Function of a Single-Function Device associated with an Upstream Port
- Function 0 (and only Function 0) of a Multi-Function Device associated with an Upstream Port

This capability is permitted to be implemented in any of the Functions listed above even if the 64.0 GT/s Link speed is not supported. When the $64.0 \mathrm{GT} / \mathrm{s}$ Link speed is not supported, the behavior of registers other than the Capability Header is undefined.
§ Figure 7-97 details allocation of register fields in the Physical Layer 64.0 GT/s Extended Capability structure.
Note that parity errors for $64.0 \mathrm{GT} / \mathrm{s}$ are recorded in $16.0 \mathrm{GT} / \mathrm{s}$ Local Data Parity Mismatch Status Register, $16.0 \mathrm{GT} / \mathrm{s}$ First Retimer Data Parity Mismatch Status Register, and 16.0 GT/s Second Retimer Data Parity Mismatch Status Register. When tracking errors for a specific Link Speed, software should clear those registers on speed changes.
![img-93.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-93.jpeg)

Figure 7-97 Physical Layer 64.0 GT/s Extended Capability

# 7.7.7.1 Physical Layer 64.0 GT/s Extended Capability Header (Offset 00h) 

![img-94.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-94.jpeg)

Figure 7-98 Physical Layer 64.0 GT/s Extended Capability Header

Table 7-85 Physical Layer 64.0 GT/s Extended Capability Header

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $15: 0$ | PCI Express Extended Capability ID - This field is a PCI-SIG defined ID number that indicates the nature and format of the Extended Capability. <br> The Extended Capability ID for the Physical Layer 64.0 GT/s Capability is 0031h. | RO |
| $19: 16$ | Capability Version - This field is a PCI-SIG defined version number that indicates the version of the Capability structure present. <br> Must be 1 h for this version of the specification. | RO |
| $31: 20$ | Next Capability Offset - This field contains the offset to the next PCI Express Capability structure or 000h if no other items exist in the linked list of Capabilities. <br> For Extended Capabilities implemented in Configuration Space, this offset is relative to the beginning of PCI-compatible Configuration Space and thus must always be either 000 h (for terminating list of Capabilities) or greater than 0FFh. | RO |

### 7.7.7.2 64.0 GT/s Capabilities Register (Offset 04h) 

![img-95.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-95.jpeg)

Figure 7-99 64.0 GT/s Capabilities Register

Table 7-86 64.0 GT/s Capabilities Register

| Bit Location | Register Description | Attributes |
| :-- | :-- | :-- |

# 7.7.7.3 64.0 GT/s Control Register (Offset 08h) 

![img-96.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-96.jpeg)

Figure 7-100 64.0 GT/s Control Register

Table 7-87 64.0 GT/s Control Register

Bit Location Register Description

### 7.7.7.4 64.0 GT/s Status Register (Offset 0Ch) 

![img-97.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-97.jpeg)

Figure 7-101 64.0 GT/s Status Register

Table 7-88 64.0 GT/s Status Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 0 | Equalization 64.0 GT/s Complete - When Set, this bit indicates that the 64.0 GT/s Transmitter <br> Equalization procedure has completed. Details of the Transmitter Equalization process and when this bit needs to be set to 1 b is provided in $\S$ Section 4.2.7.4.2. <br> The default value of this bit is Ob. <br> For a Multi-Function Upstream Port, this bit must be implemented in Function 0 and RsvdZ in other Functions. | ROS/RsvdZ |
| 1 | Equalization 64.0 GT/s Phase 1 Successful - When set to 1b, this bit indicates that Phase 1 of the 64.0 GT/s Transmitter Equalization procedure has successfully completed. Details of the Transmitter Equalization process and when this bit needs to be set to 1 b is provided in $\S$ Section 4.2.7.4.2. <br> The default value of this bit is Ob. <br> For a Multi-Function Upstream Port, this bit must be implemented in Function 0 and RsvdZ in other Functions. | ROS/RsvdZ |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 2 | Equalization 64.0 GT/s Phase 2 Successful - When set to 1b, this bit indicates that Phase 2 of the 64.0 GT/s Transmitter Equalization procedure has successfully completed. Details of the Transmitter Equalization process and when this bit needs to be set to 1 b is provided in $\S$ Section 4.2.7.4.2 . <br> The default value of this bit is 0 b . <br> For a Multi-Function Upstream Port, this bit must be implemented in Function 0 and RsvdZ in other Functions. | ROS/RsvdZ |
| 3 | Equalization 64.0 GT/s Phase 3 Successful - When set to 1b, this bit indicates that Phase 3 of the 64.0 GT/s Transmitter Equalization procedure has successfully completed. Details of the Transmitter Equalization process and when this bit needs to be set to 1 b is provided in $\S$ Section 4.2.7.4.2 . <br> The default value of this bit is 0 b . <br> For a Multi-Function Upstream Port, this bit must be implemented in Function 0 and RsvdZ in other Functions. | ROS/RsvdZ |
| 4 | Link Equalization Request 64.0 GT/s - This bit is Set by hardware to request the 64.0 GT/s Link equalization process to be performed on the Link. Refer to § Section 4.2.4 and § Section 4.2.7.4.2 for details. <br> The default value of this bit is 0 b . <br> For a Multi-Function Upstream Port, this bit must be implemented in Function 0 and RsvdZ in other Functions. | RW1CS/RsvdZ |
| 5 | Transmitter Precoding On - This field indicates whether the Receiver asked this transmitter to enable Precoding. See § Section 4.2.3.1.4. This bit is cleared on DL_Down. <br> Default is 0b. | RO |
| 6 | Transmitter Precode Request - When Set, this Port will request the transmitter to use Precoding by setting the Transmitter Precode Request bit in the TS1s/TS2s it transmits prior to entry to Recovery.Speed (see § Section 4.2.3.1.4). <br> Default is Implementation Specific. | RO |
| 7 | No Equalization Needed Received - When Set, this Port either received a Modified TS1/TS2 with the No Equalization Needed bit Set or received a non-modified TS1/TS2 was received with the No Equalization Needed encoding (also reported in the Received Enhanced Link Behavior Control field). <br> Default is 0b. | RO |

# 7.7.7.5 64.0 GT/s Lane Equalization Control Register (Offset 10h) 

The 64.0 GT/s Equalization Control register consists of control fields required for per-Lane 64.0 GT/s equalization. It contains entries for at least the number of Lanes defined by the Maximum Link Width (see § Section 7.5.3.6 or § Section 7.9.9.2 ), must be implemented in whole DW granularity (e.g., if the Maximum Link Width is $\times 1$, the register will still contain entries for 4 Lanes with the entries for Lanes 1, 2 and 3 being undefined), and it is permitted to contain up to 32 entries regardless of the Maximum Link Width. The value of entries beyond the Maximum Link Width is undefined.

Each entry contains the values for the Lane with the corresponding default Lane number which is invariant to Link width and Lane reversal negotiation that occurs during Link training.

![img-98.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-98.jpeg)

Figure 7-102 64.0 GT/s Lane Equalization Control Register Entry

Table 7-89 64.0 GT/s Lane Equalization Control Register Entry

| Bit Location | Register Description |  | Attributes |
| :--: | :--: | :--: | :--: |
| 3:0 | Downstream Port 64.0 GT/s Transmitter Preset - Transmitter Preset used for 64.0 GT/s equalization by this Port when the Port is operating as a Downstream Port. This field is ignored when the Port is operating as an Upstream Port. See § Chapter 8. for details. The field encodings are defined in § Table 4-32. <br> For an Upstream Port if Crosslink Supported is 0b, this field is RsvdP. Otherwise, this field is HwInit. See § Section 7.5.3.18. <br> The default value is 1111 b . |  | HwInit/RsvdP (see description) |
| 7:4 | Upstream Port 64.0 GT/s Transmitter Preset - Field contains the Transmit Preset value sent or received during 64.0 GT/s Link Equalization. Field usage varies as follows: |  | HwInit/RO (see description) |
|  | Operating Port Direction | Crosslink Supported | Usage |
|  | A | Downstream Port | Any | Field contains the value sent on the associated Lane during Recovery.RcvrCfg. <br> Field is HwInit. |
|  | B | Upstream Port | 0b | Field is intended for debug and diagnostics. It contains the value captured from the associated Lane during Link Equalization. <br> This value must be captured from 128b/130b EQ TS2 or equalization requests with Use_Preset Set are received. This value should not be affected by equalization requests with Use_Preset Clear. <br> Field is RO. <br> When crosslinks are supported, case C (below) applies and this captured information is not visible to software. Vendors are encouraged to provide an alternate mechanism to obtain this information. |
|  | C | Upstream Port | 1b | Field is not used or affected by the current Link Equalization. <br> Field value will be used if a future crosslink negotiation switches the Operating Port Direction so that case A (above) applies. <br> Field is HwInit. |
|  | See § Section 4.2.4 and § Chapter 8. for details. The field encodings are defined in § Table 4-32. The default value is 1111 b . |  |  |

# 7.7.8 Flit Logging Extended Capability 

This capability MUST be implemented in Ports and RCRBs that support Flit Mode. For Functions associated with an Upstream Port, this capability MUST be implemented in Function 0 and MUST not be implemented in any other Function of that Upstream Port.

This capability is only used in Flit Mode. The capability has no effect in Non-Flit Mode.
§ Figure 7-103 details allocation of the register bits in the Flit Logging Extended Capability structure.
The Lane numbers in FBER Measurement Status 3 Register through FBER Measurement Status 10 Register are strongly recommended to be the default Lane numbers which are invariant to Link width and Lane reversal negotiation that occurs during Link training.
![img-99.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-99.jpeg)

Figure 7-103 Flit Logging Extended Capability Structure

# 7.7.8.1 Flit Logging Extended Capability Header (Offset 00h) 

\$ Figure 7-104 details allocation of the register fields in the Flit Logging Extended Capability Header; \$ Table 7-91 provides the respective bit definitions.
![img-100.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-100.jpeg)

Figure 7-104 Flit Logging Extended Capability Header

Table 7-91 Flit Logging Extended Capability Header

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 15:0 | Flit Logging Extended Capability ID - This field is a PCI-SIG defined ID number that indicates the nature and format of the Extended Capability. <br> The Extended Capability ID for the Flit Logging Extended Capability is 0032h. | RO |
| 19:16 | Capability Version - This field is a PCI-SIG defined version number that indicates the version of the Capability structure present. <br> Must be 1 h for this version of the specification. | RO |
| 31:20 | Next Capability Offset - This field contains the offset to the next PCI Express Capability structure or 000h if no other items exist in the linked list of Capabilities. <br> For Extended Capabilities implemented in Configuration Space, this offset is relative to the beginning of PCI-compatible Configuration Space and thus must always be either 000 h (for terminating list of Capabilities) or greater than 0 FFh . | RO |

### 7.7.8.2 Flit Error Log 1 Register (Offset 04h)

The Flit Error Log 1 Register and Flit Error Log 2 Register are Link level registers and contain information about the Flit errors corrected and/or detected by the FEC and/or CRC in a received Flit. The Flit Error Log is a FIFO of an implementation specific and unspecified size (size 1 is permitted). These registers contain the oldest log entry. Clearing the Flit Error Log Valid removes the oldest log entry from the FIFO and loads these registers with the next oldest log entry (if there is one). See § Section 4.2.3.1.2, § Section 4.2.3.1.3, § Appendix J., and § Appendix K. for details.

Errors logged in the Flit Error Log 1 register and the Flit Error Log 2 register are interpreted as shown in Table 7-x.
Table 7-92 Flit Error Log Interpretation

| Flit Error <br> Log Valid | FEC <br> Uncorrectable <br> Error in Flit | Unrecognized <br> Flit | Syndrome Parity and Check for <br> ECC Groups 0, 1, and 2 | Flit Error Log Entry Interpretation | Notes |
| :--: | :--: | :--: | :--: | :--: | :--: |
| 1b | 0b | 0b | All 00h | Reserved | Note 1 |
| 1b | 0b | 0b | At least one <br> $!=00$ h | Good Flit, correctable error |  |

| Flit Error <br> Log Valid | FEC <br> Uncorrectable <br> Error in Flit | Unrecognized <br> Flit | Syndrome Parity and Check for <br> ECC Groups 0, 1, and 2 | Flit Error Log Entry Interpretation | Notes |
| :--: | :--: | :--: | :--: | :--: | :--: |
| 1b | 0b | 1b | All 00h | Unrecognized Flit with no <br> accompanying FEC correctable error |  |
| 1b | 0b | 1b | At least one <br> $!=00 \mathrm{~h}$ | Unrecognized Flit with <br> accompanying FEC correctable error |  |
| 1b | 1b | $x$ | All 00h | Uncorrectable error due to CRC, FEC <br> OK |  |
| 1b | 1b | $x$ | At least one <br> $!=00 \mathrm{~h}$ | Uncorrectable error due to FEC, CRC, <br> or both |  |
| 0b | $x$ | $x$ | Any | No Log Entry Present |  |

Notes:

1. Software should silently discard this log entry
![img-101.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-101.jpeg)

Figure 7-105 Flit Error Log 1 Register

Table 7-93 Flit Error Log 1 Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 0 | Flit Error Log Valid - This bit is Set to 1b when an error is logged in this register and the Flit Error Log 2 Register. <br> Writing 1b to this bit either clears this bit or, if More Entries for Flit Error Log Register are Valid (i.e., Bit 13) is Set, loads the Flit Error Log 1 Register and Flit Error Log 2 Register with the next oldest log entry Default Zero. | RW1CS |
| 3:1 | Flit Error Link Width - Link Width when error was logged (taking into account any narrowing due to LOp). Encoding is: | ROS |
|  | 000b | $x 1$ |
|  | 001b | $x 2$ |
|  | 010b | $x 4$ |
|  | 011b | $x 8$ |

| Bit Location | Register Description |  | Attributes |
| :--: | :--: | :--: | :--: |
|  | 100b <br> Others <br> Default is Zero. | x16 <br> Reserved |  |
| 7:4 | Flit Offset from the Last Logged Flit in Error - This is the offset from the last Flit whose error has been recorded in the prior entry of the Flit Error Log Register, if any. <br> - If this is the very first error that gets logged or this is the only copy of the Flit Error Log Register, this value must be 0 h . <br> - If the previous Flit was in error and logged, this value must be 1 h . <br> - If the last logged Flit was more than 15 Flits away, this value must be Fh. <br> This field only reflects errors that were logged. If the previous Flit was in error but was not logged, that error has no effect on this value. <br> Default is Zero. | ROS |  |
| 12:8 | Consecutive Flit Error after the Last Flit Error - Initially, this field is Zero. If there are any errors (either correctable or uncorrectable by FEC) in any of the 5 consecutive Flits immediately following the Flit recorded in this log entry, the corresponding bits are set to 1 b ; otherwise they remain 0 b . This field can change value after Flit Error Log Valid is Set and more Flits are received. If More Entries for Flit Error Log Register is Set, some bits of this field may not be meaningful and software can determine the accurate complete Flit error status from this field and subsequent log entries using the following example as a model. <br> Consider consecutive log entries $A, B$ and $C$, where $A$ is older than $B$ and $B$ is older than $C$ : <br> - If Flit Offset from the Last Logged Flit in Error in B is $>5$, then this field in log entry $A$ is accurate (since there were more than 5 intervening Flits between $A$ and $B$ ). <br> - If Flit Offset from the Last Logged Flit in Error in B is $\leq 5$, then some bits of this field in A must be determined by software using B (and C, if applicable, depending on the distance between A and C). <br> - If Flit Offset from the Last Logged Flit in Error in B = 2, then entry A is for two Flits earlier. For entry A: <br> - Bit 0 represents the intervening Flit (which might have been in error but not logged) and <br> - Bits 4:1 are not meaningful and must be determined by software using B (and C, if applicable, depending on the distance between A and C). Bit 1 is 1 b (because B exists), and bits 4:2 are bits 2:0 of B. <br> - If in turn, Flit Offset from the Last Logged Flit in Error in C is $\leq 5$, some of the bits in B are not meaningful and must be determined by software using C (and possibly the next entry D, if applicable and available). <br> Default is Zero. | ROS |  |
| 13 | More Entries for Flit Error Log Register are Valid - when Set, it indicates that the Port has additional valid copies of the Flit Error Log Register for subsequent Flits. A port that implements only one set of Flit Error Log Register is permitted to hardwire this to Zero. <br> If this bit is Set, clearing the Flit Error Log Valid bit loads the next oldest Flit Error Log Register entry. This bit can change value when Flit Error Log Valid bit is Set and an additional error is being logged. <br> Default is Zero. | ROS |  |

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 14 | Unrecognized Flit - when Set indicates receipt of a Flit that passes CRC after FEC decode but uses a <br> Reserved encoding in the Flit Usage or Flit_Status fields. <br> Default is Zero | ROS |
| 15 | FEC Uncorrectable Error in Flit - When set to 1b indicates either a CRC mismatch or one of the three <br> FEC groups detecting an error it could not correct | ROS |
| $23: 16$ | Syndrome Parity for ECC Group 0 - Synd_Parity in § Chapter 4. . <br> Default is Zero. | ROS |
| $31: 24$ | Syndrome Check for ECC Group 0 - Synd_Check in § Chapter 4. . <br> Default is Zero. | ROS |

# 7.7.8.3 Flit Error Log 2 Register (Offset 08h) 

The Flit Error Log 1 Register and Flit Error Log 2 Register are Link level registers and contain information about the Flit errors corrected and/or detected by the FEC and/or CRC in a received Flit.
![img-102.jpeg](03_Knowledge/Tech/PCIe/07_Software/img-102.jpeg)

Figure 7-106 Flit Error Log 2 Register

Table 7-94 Flit Error Log 2 Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| $7: 0$ | Syndrome Parity for ECC Group 1 - Synd_Parity in § Chapter 4. . <br> Default is Zero. | ROS |
| $15: 8$ | Syndrome Check for ECC Group 1 - Synd_Check in § Chapter 4. . <br> Default is Zero. | ROS |
| $23: 16$ | Syndrome Parity for ECC Group 2 - Synd_Parity in § Chapter 4. . <br> Default is Zero. | ROS |
| $31: 24$ | Syndrome Check for ECC Group 2 - Synd_Check in § Chapter 4. . <br> Default is Zero. | ROS |

# 7.7.8.4 Flit Error Counter Control Register (Offset 0Ch) 

The Flit Error Counter registers are Link wide and count the number of Flit and/or Ordered Set errors occurring on a Link operating in Flit mode.
![img-103.jpeg](img-103.jpeg)

Figure 7-107 Flit Error Counter Control Register

Table 7-95 Flit Error Counter Control Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 0 | Flit Error Counter Enable - Setting this bit enables and starts the Flit Error Counter in the Link. Clearing this bit stops the Flit Error Counter from incrementing. When Clear, it is strongly recommended that Flit Error Counter does not decrement. <br> Default is Zero. | RW |
| 1 | Flit Error Counter Interrupt Enable - Generate an interrupt when Interrupt Generated based on Trigger Event Count transitions from 0b to 1b. <br> The interrupt vector is Interrupt Message Number (see § Section 7.5.3.2). <br> Default is Zero. | RW |
| $3: 2$ | Events to count - <br> 00b FEC-correctable Flit (see § Section 4.2.3.4.2), Invalid Flit (see § Section 4.2.3.4.2), or Framing Error (see § Section 4.2.2.3.4 and § Section 4.2.3.2) <br> 01b FEC-correctable Flit <br> 10b Invalid Flit <br> 11b All events in 00b plus: <br> - a 1b/1b TS Ordered Set on any Lane with only one valid half (see § Section 4.2.5.1) <br> - an invalid Ordered Set on any Lane <br> Default is Zero. | RW |
| 11:4 | Trigger Event on Error Count - Generate an event (interrupt, if enabled) if this field is non-zero and the Flit Error Counter field in Flit Error Counter Status Register exceeds this value. <br> Default is Zero. | RW |

# 7.7.8.5 Flit Error Counter Status Register (Offset OEh) 

![img-104.jpeg](img-104.jpeg)

Figure 7-108 Flit Error Counter Status Register

Table 7-96 Flit Error Counter Status Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 2:0 | Link Width when Error Counter Started - This field tracks the link width when the error counter started or restarted counting. The encodings are as follows: <br> 000b <br> 001b <br> 010b <br> 011b <br> 100b <br> Others <br> Default is Zero. | ROS |
| 3 | Interrupt Generated based on Trigger Event Count - hardware Sets this bit when an interrupt condition is generated based on the trigger event. While this bit is Set, no new interrupts will be generated based on the trigger event. <br> Cleared on 0b to 1b transition of Flit Error Counter Enable. <br> It is strongly recommended that software transition Flit Error Counter Enable from 0b to 1b after the interrupt is serviced. <br> Default is Zero. | RW1CS |
| 15:8 | Flit Error Counter - Increments by 1 when enabled and a countable event has occurred, as defined in the Flit Error Counter Control Register. <br> Decrements by 1 at a fixed rate, if non-zero, based on Encoding and Link Width as follows: <br> $\mathbf{1 b / 1 b}$ <br> $\frac{10^{6}}{(\text { Link Width } \times 2)}$ UI ( $\pm 5 \mathrm{~ns})$ <br> $\frac{8 \mathrm{~b} / 10 \mathrm{~b}}{\text { Link Width }}$ <br> $\frac{10^{12}}{\text { Link Width }}$ <br> $\frac{10^{12}}{\text { Link Width }}$ UI ( $\pm 5 \mathrm{~ns})$ <br> $\frac{10^{12}}{\text { Link Width }}$ UI ( $\pm 5 \mathrm{~ns})$ | ROS |
|  | Cleared on 0b to 1b transition of Flit Error Counter Enable. <br> Does not roll over. <br> Default is Zero. |  |

# 7.7.8.6 FBER Measurement Control Register (Offset 10h) 

The FBER Measurement Control register enables direct FBER measurement with status reported in the FBER Measurement Status Registers. For Retimers, the control is provided through Margin Command in the Control SKP Ordered Set from the Downstream Port (see § Chapter 4. ).
![img-105.jpeg](img-105.jpeg)

Figure 7-109 FBER Measurement Control Register

Table 7-97 FBER Measurement Control Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 0 | FBER Measurement Enable - Setting this bit enables and starts the FBER measurement in the Link. Clearing this bit stops FBER measurement. <br> Default is Zero. | RW |
| 1 | Clear FBER Counters - Writing a 1b to this bit clears the FBER counters. <br> This bit always return Zero when read | RW |
| $3: 2$ | Granularity of per-Lane Error reported - <br> 00b count all bit errors corrected by FEC in valid Flits, <br> 01b count all even bit errors in each UI corrected by FEC in valid Flits, <br> 10b count all odd bit errors in each UI corrected by FEC in valid Flits, <br> 11b count only mismatches in the Control SKP OS as a single correctable bit error <br> FBER measurement results are undefined if this field contains 01b or 10b and the Link is not operating in PAM4. <br> Default is Zero. | RW |
| 4 | Report Longest Burst vs First Burst - This bit is now deprecated. Behavior is undefined if this bit is Set. Default is Zero. | RW |

### 7.7.8.7 FBER Measurement Status 1 Register (Offset 14h)

FBER Measurement Status 1 Register through FBER Measurement Status 10 Register contain a collection of per-Link and per-Lane counters:

- Flit Counter - per-Link
- Invalid Flit Counter - per-Link
- Correctable Error Counters - per-Lane (Adding these together produces a per-Link counter)

A write of 1b to either the Clear FBER Counters or the FBER Measurement Enable bit of the FBER Measurement Control Register resets the value of all of these counters to their default values. All of these counters saturate (i.e., when they reach their maximum value, they do not roll over).
![img-106.jpeg](img-106.jpeg)

Figure 7-110 FBER Measurement Status 1 Register

Table 7-98 FBER Measurement Status 1 Register 5

| Bit Location | Register Description | Attributes |
| :-- | :-- | :-- |
| $31: 0$ | Flit Counter - meaningful when FBER Measurement Enable is Set <br> Increments by 1 for every Flit received. <br> Default is Zero. | ROS |

# 7.7.8.8 FBER Measurement Status 2 Register (Offset 18h) 

![img-107.jpeg](img-107.jpeg)

Figure 7-111 FBER Measurement Status 2 Register 6

Table 7-99 FBER Measurement Status 2 Register 5

| Bit Location | Register Description | Attributes |
| :-- | :-- | :-- |
| $15: 0$ | Invalid Flit Counter - when FBER Measurement Enable is Set: Increments by 1 for every invalid Flit <br> received. <br> Otherwise, behavior is undefined. <br> Default is 0000h. | ROS |

# 7.7.8.9 FBER Measurement Status 3 Register (Offset 1Ch) 

![img-108.jpeg](img-108.jpeg)

Figure 7-112 FBER Measurement Status 3 Register

Table 7-100 FBER Measurement Status 3 Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 15:0 | Lane \#0 Correctable Counter - counts Per-Lane Correctable Bit Errors or SKP Parity Mismatches. | RO |
|  | If FBER Measurement Enable is Set: this 16-bit counter that counts the number of FEC-correctable bit errors per Flit (up to 24) or the number of SKP OS Parity mismatch in a Port, as per the value in Granularity of per-Lane Error Reported bit in the FBER Measurement Control Register. <br> This counter does not roll-over. <br> Default is Zero. |  |
| 31:16 | Lane \#1 Correctable Counter - Behavior is identical to Lane \#0 Correctable Counter. | RO |

### 7.7.8.10 FBER Measurement Status 4 Register (Offset 20h)

![img-109.jpeg](img-109.jpeg)

Figure 7-113 FBER Measurement Status 4 Register

Table 7-101 FBER Measurement Status 4 Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 15:0 | Lane \#2 Correctable Counter - Behavior is identical to Lane \#0 Correctable Counter. | RO |
| 31:16 | Lane \#3 Correctable Counter - Behavior is identical to Lane \#0 Correctable Counter. | RO |

# 7.7.8.11 FBER Measurement Status 5 Register (Offset 24h) 

![img-110.jpeg](img-110.jpeg)

Figure 7-114 FBER Measurement Status 5 Register

Table 7-102 FBER Measurement Status 5 Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 15:0 | Lane \#4 Correctable Counter - Behavior is identical to Lane \#0 Correctable Counter. | RO |
| 31:16 | Lane \#5 Correctable Counter - Behavior is identical to Lane \#0 Correctable Counter. | RO |

### 7.7.8.12 FBER Measurement Status 6 Register (Offset 28h) 

![img-111.jpeg](img-111.jpeg)

Figure 7-115 FBER Measurement Status 6 Register

Table 7-103 FBER Measurement Status 6 Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 15:0 | Lane \#6 Correctable Counter - Behavior is identical to Lane \#0 Correctable Counter. | RO |
| 31:16 | Lane \#7 Correctable Counter - Behavior is identical to Lane \#0 Correctable Counter. | RO |

### 7.7.8.13 FBER Measurement Status 7 Register (Offset 2Ch) 

![img-112.jpeg](img-112.jpeg)

Figure 7-116 FBER Measurement Status 7 Register

Table 7-104 FBER Measurement Status 7 Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| $15: 0$ | Lane \#8 Correctable Counter - Behavior is identical to Lane \#0 Correctable Counter. | RO |
| $31: 16$ | Lane \#9 Correctable Counter - Behavior is identical to Lane \#0 Correctable Counter. | RO |

# 7.7.8.14 FBER Measurement Status 8 Register (Offset 30h) 

![img-113.jpeg](img-113.jpeg)

Figure 7-117 FBER Measurement Status 8 Register

Table 7-105 FBER Measurement Status 8 Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| $15: 0$ | Lane \#10 Correctable Counter - Behavior is identical to Lane \#0 Correctable Counter. | RO |
| $31: 16$ | Lane \#11 Correctable Counter - Behavior is identical to Lane \#0 Correctable Counter. | RO |

### 7.7.8.15 FBER Measurement Status 9 Register (Offset 34h)

![img-114.jpeg](img-114.jpeg)

Figure 7-118 FBER Measurement Status 9 Register

Table 7-106 FBER Measurement Status 9 Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| $15: 0$ | Lane \#12 Correctable Counter - Behavior is identical to Lane \#0 Correctable Counter. | RO |
| $31: 16$ | Lane \#13 Correctable Counter - Behavior is identical to Lane \#0 Correctable Counter. | RO |

# 7.7.8.16 FBER Measurement Status 10 Register (Offset 38h) 

| 31 | 16 | 15 |
| :--: | :--: | :--: |
| Lane \#15 Correctable Counter | Lane \#14 Correctable Counter |  |
| 1 | 1 | 1 |

Figure 7-119 FBER Measurement Status 10 Register

Table 7-107 FBER Measurement Status 10 Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| $15: 0$ | Lane \#14 Correctable Counter - Behavior is identical to Lane \#0 Correctable Counter. | RO |
| $31: 16$ | Lane \#15 Correctable Counter - Behavior is identical to Lane \#0 Correctable Counter. | RO |

### 7.7.9 Device 3 Extended Capability Structure

The Device 3 Extended Capability structure must be implemented in any Function or RCRB that implements any mechanism that requires the registers in this Extended Capability. It is permitted for this Extended Capability to be implemented in Functions or RCRBs that do not require any of the registers in this Extended Capability.
§ Figure 7-120 details allocation of the register bits in the Device 3 Extended Capability structure.
![img-115.jpeg](img-115.jpeg)

Figure 7-120 Device 3 Extended Capability Structure

### 7.7.9.1 Device 3 Extended Capability Header (Offset 00h)

§ Figure 7-121 details allocation of the register fields in the Device 3 Extended Capability Header; § Table 7-108 provides the respective bit definitions.

![img-116.jpeg](img-116.jpeg)

Figure 7-121 Device 3 Extended Capability Header

Table 7-108 Device 3 Extended Capability Header

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| $15: 0$ | Device 3 Extended Capability ID - Indicates the Device 3 Extended Capability structure. This field must <br> return a Capability ID of 002Fh indicating that this is a Device 3 Extended Capability structure. | RO |
| $19: 16$ | Capability Version - This field is a PCI-SIG defined version number that indicates the version of the <br> Capability structure present. <br> Must be 1h for this version of the specification. | RO |
| $31: 20$ | Next Capability Offset - The offset to the next PCI Extended Capability structure or 000h if no other <br> items exist in the linked list of capabilities. | RO |

# 7.7.9.2 Device Capabilities 3 Register (Offset 04h) 

§ Figure 7-122 details the allocation of register bits of the Device Capability 3 register; § Table 7-109 provides the respective bit definitions.
![img-117.jpeg](img-117.jpeg)

Figure 7-122 Device Capabilities 3 Register

Table 7-109 Device Capabilities 3 Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 0 | DMWr Request Routing Supported - Applicable only to Switch Upstream Ports, Switch Downstream <br> Ports, and Root Ports; must be 0b for other Function types. This bit must be Set if the Port supports this <br> optional capability. See § Section 6.32 for additional details. | HwInit |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 1 | 14-Bit Tag Completer Supported - If this bit is Set, the Function supports 14-Bit Tag Completer capability; otherwise, the Function does not. See $\S$ Section 2.2.6.2 for additional details. <br> This bit MUST@FLIT be Set. <br> For VFs, this bit value must be identical to the associated PF's bit value. | HwInit |
| 2 | 14-Bit Tag Requester Supported - If this bit is Set, the Function supports 14-Bit Tag Requester capability; otherwise, the Function does not. <br> This bit must not be Set if the 14-Bit Tag Completer Supported bit is Clear. <br> If the Function is an RCIEP, this bit must be Clear if the RC does not support 14-Bit Tag Completer capability for Requests coming from this RCIEP. <br> For VFs, this bit value must equal the VF 14-Bit Tag Requester Supported bit value in the SR-IOV Capabilities Register. See § Section 9.3.3.2.3 for additional details. <br> Note that 14-Bit Tag field generation must be enabled by the 14-Bit Tag Requester Enable bit in the Device Control 3 register of the Requester Function before 14-Bit Tags can be generated by the Requester. See § Section 2.2.6.2 for additional details. | HwInit |
| 3 | LOp Supported - If Set, the Port supports LOp. This bit must be clear if Flit Mode Supported is Clear. <br> All Functions associated with an Upstream Port must return the same value of this bit. | HwInit |
| $6: 4$ | Port LOp Exit Latency - indicates this Port's LOp Exit Latency. The value reported indicates the length of time this Port requires to complete widening a link using LOp. If LOp Supported is clear, this field must contain 000b. <br> All Functions associated with an Upstream Port must return the same value of this field. <br> Local LOp Exit Latency is computed as the maximum of Port LOp Exit Latency and Retimer LOp Exit Latency. Local LOp Exit Latency is transmitted in the LOp Exit Latency field of the Data Link Feature DLLP. The effective LOp Exit Latency of a Link is computed as the maximum of Local LOp Exit Latency and Remote LOp Exit Latency. <br> Defined encodings are: | HwInit |
|  | 000b Less than $1 \mu \mathrm{~s}$ <br> 001b $1 \mu \mathrm{~s}$ to less than $2 \mu \mathrm{~s}$ <br> 010b $2 \mu \mathrm{~s}$ to less than $4 \mu \mathrm{~s}$ <br> 011b $4 \mu \mathrm{~s}$ to less than $8 \mu \mathrm{~s}$ <br> 100b $8 \mu \mathrm{~s}$ to less than $16 \mu \mathrm{~s}$ <br> 101b $16 \mu \mathrm{~s}$ to less than $32 \mu \mathrm{~s}$ <br> 110b $32 \mu \mathrm{~s}-64 \mu \mathrm{~s}$ <br> 111b More than $64 \mu \mathrm{~s}$ |  |
| $9: 7$ | Retimer LOp Exit Latency - indicates this worst case LOp Exit Latency for retimers "associated" with this Port. The value reported indicates the length of time a Retimer requires to complete widening a link using LOp. If LOp Supported is clear, this field must contain 000b. <br> All Functions associated with an Upstream Port must return the same value of this field. <br> Local LOp Exit Latency is computed as the maximum of Port LOp Exit Latency and Retimer LOp Exit Latency. Local LOp Exit Latency is transmitted in the LOp Exit Latency field of the Data Link Feature DLLP. The effective LOp Exit Latency of a Link is computed as the maximum of Local LOp Exit Latency and Remote LOp Exit Latency. <br> Defined encodings are: <br> 000b Less than $1 \mu \mathrm{~s}$ | HwInit |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | 001b | $1 \mu \mathrm{~s}$ to less than $2 \mu \mathrm{~s}$ |
|  | 010b | $2 \mu \mathrm{~s}$ to less than $4 \mu \mathrm{~s}$ |
|  | 011b | $4 \mu \mathrm{~s}$ to less than $8 \mu \mathrm{~s}$ |
|  | 100b | $8 \mu \mathrm{~s}$ to less than $16 \mu \mathrm{~s}$ |
|  | 101b | $16 \mu \mathrm{~s}$ to less than $32 \mu \mathrm{~s}$ |
|  | 110b | $32 \mu \mathrm{~s}-64 \mu \mathrm{~s}$ |
|  | 111b | More than $64 \mu \mathrm{~s}$ |
| 10 | UIO Mem RdWr Completer Supported - When Set, indicates the Function supports UIO Memory Read and UIO Memory Write as a Completer. | HwInit |
| 11 | UIO Mem RdWr Requester Supported - When Set, indicates the Function supports UIO Memory Read and/or UIO Memory Write as a Requester. | HwInit |
| 14:12 | OHC-E Support - Indicates the maximum number of OHC-E DWs supported by this Function as a receiver in Flit Mode. See § Section 2.2.11 for important details. Values are: <br> 000b OHC-E support is not indicated. | HwInit / RsvdP |
|  | 001b | OHC-E1 supported as targeted completer. For switches, this encoding additionally indicates all OHC-Ex forwarding is supported. |
|  | 010b | OHC-E1 and OHC-E2 supported as targeted completer. For switches, this encoding additionally indicates all OHC-Ex forwarding is supported. |
|  | 011b | OHC-E1, OHC-E2 and OHC-E4 supported as targeted completer. For switches, this encoding additionally indicates all OHC-Ex forwarding is supported. |
|  | 100b | For Switches, OHC-E not supported as targeted completer but all OHC-Ex forwarding is supported. Reserved for others. |
|  | 101b-110b | Reserved |
|  | 111b | OHC-E not supported as targeted completer. For switches, this encoding also indicates OHC-Ex forwarding is not supported. |
|  | 000b encoding is present for backward compatibility purposes. It's strongly recommended that newer devices use a non-zero value of this field so SW can correctly enumerate the OHC-E capability of the function. <br> This field can be present in RP, RCIEP, Switch USP and Endpoint. |  |
|  | For RPs, this field indicates support for OHC-E on TLPs for which the RP is the targeted completer i.e., on TLPs that are not forwarded to any peer RP or a RCIEP. Different Root Ports are permitted to report different values for this field. |  |
|  | For Switches this field is present in the Switch USP function and reports the combined OHC-E capability of the USP and all Downstream Ports under that USP. |  |
|  | This field is RsvdP if Flit Mode Supported is Clear. |  |

# 7.7.9.3 Device Control 3 Register (Offset 08h) 

§ Figure 7-123 details the allocation of register bits of the Device Control 3 register; § Table 7-110 provides the respective bit definitions.

# IMPLEMENTATION NOTE: USE OF UIO REQUEST 256B BOUNDARY DISABLE 

UIO is intended to be suitable for routing its Requests directly to memory controllers. For memory architectures that support interleaving, it is intended that a single UIO Request not target multiple memory controllers. When Clear, the UIO Request 256B Boundary Disable bit prevents UIO Requests from crossing naturally aligned 256-byte address boundaries, supporting interleaving granularities of that size and integer multiples of it.

Flit Mode Link efficiency for 256-byte UIO Requests is relatively high, and it increases only a few percent when maximum-sized 4-KB Requests are used. However, for cases where using larger UIO Requests is desired in order to increase Link efficiency and/or lower TLP rates, software may Set the UIO Request 256B Boundary Disable bit to enable larger Requests. Software should only do this if it knows there is no requirement for this Requester to honor 256-byte boundaries.
![img-118.jpeg](img-118.jpeg)

Figure 7-123 Device Control 3 Register

Table 7-110 Device Control 3 Register

| Bit <br> Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 0 | DMWr Requester Enable - Applicable only to Endpoints, Root Ports and RCRBs; must be hardwired to 0b for other Function types. The Function is allowed to initiate DMWr Requests only if this bit and the Bus Master Enable bit in the Command register are both Set. <br> This bit is required to be RW if the Endpoint or Root Port is capable of initiating DMWr Requests, but otherwise is permitted to be hardwired to 0 b. <br> This bit does not serve as a capability bit. This bit is permitted to be RW even if no DMWr Requester capabilities are supported by the Endpoint or Root Port. <br> Default value of this bit is Ob. | RW |
| 1 | DMWr Egress Blocking - Applicable and mandatory for Switch Upstream Ports, Switch Downstream Ports, and Root Ports that implement DMWr routing; otherwise must be hardwired to 0b. <br> When this bit is Set, DMWr Requests that target going out this Egress Port must be blocked. See $\S$ Section 6.32 . <br> Default value of this bit is Ob. | RW/RO (see description) |
| 2 | 14-Bit Tag Requester Enable - This bit, in combination with the Extended Tag Field Enable bit and 10-Bit Tag Requester Enable bit, determines how many Tag field bits a Requester is permitted to use for non-UIO | RW/RO (see description) |

| Bit <br> Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | Requests. When the 14-Bit Tag Requester Enable bit is Set, the Requester is permitted to use 14-Bit Tags. See § Section 2.2.6.2 for complete details. <br> If software changes the value of this bit while the Function has outstanding Non-Posted Requests, the result is undefined. <br> For VFs, this bit is not supported and is RsvdP. The value in the VF 14-Bit Tag Requester Enable bit in the associated PF's SR-IOV Control Register applies to all its VFs. <br> Non-VF Functions that do not implement 14-Bit Tag Requester capability are permitted to hardwire this bit to 0b. <br> Default value of this bit is 0 b . | VF RsvdP |
| 3 | LOp Enable - Determines behavior of this Port when sending or responding to Link Management DLLPs of type LOp DLLP. <br> This bit has no effect on Link Management DLLPs where the Link Mgmt Type field is other than LOp DLLP. <br> This bit has no effect if Hardware Autonomous Width Disable is 1b. <br> Default is 1 b . | RW |
| $6: 4$ | Target Link Width - writes to this field initiate a directed LOp Link Width change to the indicated width. Encodings are: <br> 000b <br> 001b <br> 010b <br> 011b <br> 100b <br> 111b <br> Others <br> This field has no effect on subsequent autonomous Link Width changes. This field has no effect on subsequent Link Width changes due to link reliability. <br> This field does not represent maximum Link Width support. <br> This field is RsvdP if Flit Mode Supported is Clear. This field is permitted in RCRBs. <br> This field has no effect if LOp Enable is Clear. <br> This field has no effect if Hardware Autonomous Width Disable is 1b. <br> Behavior is undefined if this field is set to a reserved encoding or to a width that is greater than the Link width on the most recent entry to L0. <br> Default is 111 b . | RW/RsvdP |
| 7 | UIO Mem RdWr Requester Enable - The Function is permitted to initiate UIO Memory Read and UIO Memory Write only if this bit and the Bus Master Enable bit in the Command Register are both Set. <br> This bit is required to be RW if UIO Mem RdWr Requester Supported is Set, but otherwise is permitted to be hardwired to 0b. <br> Default value of this bit is 0 b . | RW/RO <br> (see <br> description) |
| 8 | UIO Request 256B Boundary Disable - When Clear, a UIO Request from this Function must not specify an Address/Length combination that causes a Memory Space access to cross a naturally aligned 256-byte boundary. When Set, a Request from this Function may cross a naturally aligned 256B boundary. The | RW/RO <br> (see <br> description) |

| Bit <br> Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | setting of this bit has no impact on the separate requirement that all Memory Requests must not specify an Address/Length combination that causes a Memory Space access to cross a naturally aligned 4-KB boundary (see § Section 2.2.7). <br> Mechanisms outside the scope of this specification may enable more advanced boundary policies, such as using larger or smaller boundaries than 256B, or boundaries associated with specific address ranges. However, such policies must never violate the boundary requirements stated in this description. See the Implementation Note: Use of UIO Request 256B Boundary Disable. <br> This bit is permitted to be hardwired to 0b if this Function's UIO Mem RdWr Requester Supported bit is Clear. Default value of this bit is 0 b . |  |

# 7.7.9.4 Device Status 3 Register (Offset 0Ch) 

§ Figure 7-124 details allocation of the register fields in the Device Status 3 Register; § Table 7-111 provides the respective bit definitions.
![img-119.jpeg](img-119.jpeg)

Figure 7-124 Device Status 3 Register

Table 7-111 Device Status 3 Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 2:0 | Initial Link Width - This field contains the Link Width determined during initial link training. Encodings are: | RO |
|  | 000b | $x 1$ Link |
|  | 001b | $x 2$ Link |
|  | 010b | $x 4$ Link |
|  | 011b | $x 8$ Link |
|  | 100b | $x 16$ Link |
|  | Others | Reserved |
|  | Default is determined during initial link training. |  |
|  | Note that the current Link Width is visible in the Negotiated Link Width field. |  |
| 3 | Segment Captured - This bit indicates if the Function has captured a valid Segment value from a Configuration Write Request as described in § Section 2.2.6.2. When the Destination Segment field is captured from a Configuration Write Request in FM this bit must be set to the value of the DSV bit | RO |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | received with the Request. This bit must be cleared when a Configuration Write Request is received in NFM. <br> Note that this bit will be set when every Link on the path from the Function to the RC is in FM. This bit will be clear if any Link between the Function and the RC is in NFM. Functions should only initiate Route by ID Message Requests targeting Hierarchies other than their own when this bit is Set. <br> This bit is permitted to be hardwired to 0 b in devices that don't support FM. <br> FM Requesters and Completers within an RC capture their Segment value in an implementation specific way and must then Set this bit. <br> The value in a Switch Downstream Port must be identical to the value in the associated Switch Upstream Port. <br> Default is Zero in Functions that capture their Segment value. |  |
| 4 | Remote LOp Supported - This bit indicates that the remote end of the Link supports LOp. Default is zero. | RO |

# 7.7.10 Lane Margining at the Receiver Extended Capability 9 

The Lane Margining at the Receiver Extended Capability structure must be implemented in:

- A Function associated with a Downstream Port where the Supported Link Speeds Vector field indicates support for a Link speed of $16.0 \mathrm{GT} / \mathrm{s}$ or higher.
- A Function of a Single-Function Device associated with an Upstream Port where the Supported Link Speeds Vector field indicates support for a Link speed of $16.0 \mathrm{GT} / \mathrm{s}$ or higher.
- Function 0 (and only Function 0 ) of a Multi-Function Device associated with an Upstream Port where the Supported Link Speeds Vector field indicates support for a Link speed of $16.0 \mathrm{GT} / \mathrm{s}$ or higher.
§ Figure 7-125 shows the layout of the Margining Extended Capability. This capability contains a pair of per-Port registers followed by a set of per-Lane registers.

The number of per-Lane entries is determined by the Maximum Link Width (see § Section 7.5.3.6 or § Section 7.9.9.2). Up to 32 entries are permitted regardless of the Maximum Link Width. The value of entries beyond the Maximum Link Width is undefined.

Each per-Lane entry contains the values for that Lane. Lane numbering uses the default Lane number and is thus invariant to Link width and Lane reversal negotiation that occurs during Link training.

![img-120.jpeg](img-120.jpeg)

Figure 7-125 Lane Margining at the Receiver Extended Capability

# 7.7.10.1 Lane Margining at the Receiver Extended Capability Header (Offset 00h) 

![img-121.jpeg](img-121.jpeg)

Figure 7-126 Lane Margining at the Receiver Extended Capability Header

Table 7-112 Lane Margining at the Receiver Extended Capability Header

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $15: 0$ | PCI Express Extended Capability ID - This field is a PCI-SIG defined ID number that indicates the nature and format of the Extended Capability. <br> The Extended Capability ID for the Lane Margining at the Receiver Extended Capability is 0027h. | RO |
| 19:16 | Capability Version - This field is a PCI-SIG defined version number that indicates the version of the Capability structure present. <br> Must be 1 h for this version of the specification. | RO |
| $31: 20$ | Next Capability Offset - This field contains the offset to the next PCI Express Capability structure or 000h if no other items exist in the linked list of Capabilities. <br> For Extended Capabilities implemented in Configuration Space, this offset is relative to the beginning of PCI-compatible Configuration Space and thus must always be either 000h (for terminating list of Capabilities) or greater than 0FFh. | RO |

### 7.7.10.2 Margining Port Capabilities Register (Offset 04h)

![img-122.jpeg](img-122.jpeg)

Figure 7-127 Margining Port Capabilities Register

Table 7-113 Margining Port Capabilities Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :-- |
| 0 | Margining uses Driver Software - If Set, indicates that Margining is partially implemented using Device <br> Driver software. Margining Software Ready indicates when this software is initialized. If Clear, Margining | HwInit |

| Bit Location | Register Description | Attributes |
| :-- | :-- | :-- |
|  | does not require device driver software. In this case the value read from Margining Software Ready is <br> undefined. |  |

# 7.7.10.3 Margining Port Status Register (Offset 06h) 

![img-123.jpeg](img-123.jpeg)

Figure 7-128 Margining Port Status Register

Table 7-114 Margining Port Status Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 0 | Margining Ready - Indicates when the Margining feature is ready to accept margining commands. <br> Behavior is undefined if this bit is Clear and, for any Lane, any of the Receiver Number, Margin Type, Usage Model, or Margin Payload fields are written (see § Section 7.7.10.4). <br> If Margining uses Driver Software is Set, Margining Ready must be Set no later than 100 ms after the later of Margining Software Ready becoming Set or the link training to $16.0 \mathrm{GT} / \mathrm{s}$ or higher. <br> If Margining uses Driver Software is Clear, Margining Ready must be Set no later than 100 ms after the Link trains to $16.0 \mathrm{GT} / \mathrm{s}$ or higher. <br> Default value is implementation specific. | RO |
| 1 | Margining Software Ready - When Margining uses Driver Software is Set, then this bit, when Set, indicates that the required software has performed the required initialization. <br> The value of this bit is undefined if Margining uses Driver Software is Clear. The default value of this bit is implementation specific. | RO |

### 7.7.10.4 Margining Lane Control Register (Offset 08h)

The Margining Lane Control Register consists of control fields required for per-Lane margining.
The number of entries in this register are sized by Maximum Link Width (see § Section 7.5.3.6).
See § Section 4.2.8.2 for details of this register.

![img-124.jpeg](img-124.jpeg)

Figure 7-129 Lane N: Margining Control Register Entry

Table 7-115 Lane N: Margining Control Register Entry

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $2: 0$ | Receiver Number - See § Section 4.2.18.1 for details. <br> The default value is 000 b . <br> This field must be reset to the default value if the Port goes to DL_Down status. | RW (see description) |
| $5: 3$ | Margin Type - See § Section 4.2.18.1 for details. <br> The default value is 111 b . <br> This field must be reset to the default value if the Port goes to DL_Down status. | RW (see description) |
| 6 | Usage Model - See § Section 4.2.18.1 for details. <br> The default value is 0 b . <br> This field must be reset to the default value if the Port goes to DL_Down status. | RW (see description) |
| $15: 8$ | Margin Payload - See § Section 4.2.18.1 for details. <br> This field's value is used in conjunction with the Margin Type field, as described in § Section 4.2.18.1 . <br> The default value is 9 Ch . <br> This field must be reset to the default value if the Port goes to DL_Down status. | RW (see description) |

# 7.7.10.5 Margining Lane Status Register (Offset 0Ah) 

The Margining Lane Status register consists of status fields required for per-Lane margining. The number of entries in this register are sized by Maximum Link Width (see § Section 7.5.3.6). See § Section 4.2.8.2 for details of this register.

![img-125.jpeg](img-125.jpeg)

Figure 7-130 Lane N: Margining Lane Status Register Entry

Table 7-116 Lane N: Margining Lane Status Register Entry

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $2: 0$ | Receiver Number Status - See $\S$ Section 4.2.18.1 for details. <br> The default value is 000 b . <br> For Downstream Ports, this field must be reset to the default value if the Port goes to DL_Down status. | RO (see description) |
| $5: 3$ | Margin Type Status - See $\S$ Section 4.2.18.1 for details. <br> The default value is 000 b . <br> This field must be reset to the default value if the Port goes to DL_Down status. | RO (see description) |
| 6 | Usage Model Status - See $\S$ Section 4.2.18.1 for details. <br> The default value is 0 b . <br> This field must be reset to the default value if the Port goes to DL_Down status. | RO (see description) |
| $15: 8$ | Margin Payload Status - See $\S$ Section 4.2.18.1 for details. <br> This field is only meaningful, when the Margin Type is a defined encoding other than 'No Command'. The default value is 00 h . <br> This field must be reset to the default value if the Port goes to DL_Down status. | RO (see description) |

# 7.7.11 ACS Extended Capability 

The ACS Extended Capability is an optional capability that provides enhanced access controls (see $\S$ Section 6.12 ). This capability may be implemented by a Root Port, a Switch Downstream Port, or a Multi-Function Device Function. It is never applicable to a PCI Express to PCI Bridge or Root Complex Event Collector. It is not applicable to a Switch Upstream Port unless that Switch Upstream Port is a Function in a Multi-Function Device.

If an SR-IOV Capable Device other than one in a Root Complex implements internal peer-to-peer transactions, ACS is required, and ACS P2P Egress Control must be supported.

Implementation of ACS in RCIEPs is permitted but not required. It is explicitly permitted that within a single Root Complex, some RCIEPs implement ACS and some do not. It is strongly recommended that Root Complex implementations ensure that all accesses originating from RCIEPs (PFs and VFs) without ACS capability are first subjected to processing by a Translation Agent (TA) in the Root Complex before further decoding and processing. The details are outside the scope of this specification.

![img-126.jpeg](img-126.jpeg)

Figure 7-131 ACS Extended Capability

# 7.7.11.1 ACS Extended Capability Header (Offset 00h) 

![img-127.jpeg](img-127.jpeg)

Figure 7-132 ACS Extended Capability Header

Table 7-117 ACS Extended Capability Header

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 15:0 | PCI Express Extended Capability ID - This field is a PCI-SIG defined ID number that indicates the nature and format of the Extended Capability. <br> PCI Express Extended Capability ID for the ACS Extended Capability is 000Dh. | RO |
| 19:16 | Capability Version - This field is a PCI-SIG defined version number that indicates the version of the Capability structure present. <br> Must be 1 h for this version of the specification. | RO |
| $31: 20$ | Next Capability Offset - This field contains the offset to the next PCI Express Extended Capability structure or 000 h if no other items exist in the linked list of Capabilities. | RO |

# 7.7.11.2 ACS Capability Register (Offset 04h) 

![img-128.jpeg](img-128.jpeg)

Figure 7-133 ACS Capability Register

Table 7-118 ACS Capability Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 0 | ACS Source Validation - Required for Root Ports and Switch Downstream Ports; must be hardwired to 0b otherwise. If 1b, indicates that the component implements ACS Source Validation. | RO |
| 1 | ACS Translation Blocking - Required for Root Ports and Switch Downstream Ports; must be hardwired to 0b otherwise. If 1b, indicates that the component implements ACS Translation Blocking. | RO |
| 2 | ACS P2P Request Redirect - Required for Root Ports that support peer-to-peer traffic with other Root Ports; required for Switch Downstream Ports; required for Multi-Function Device Functions that support peer-to-peer traffic with other Functions; must be hardwired to 0b otherwise. If 1b, indicates that the component implements ACS P2P Request Redirect. | RO |
| 3 | ACS P2P Completion Redirect - Required for all Functions that support ACS P2P Request Redirect; must be hardwired to 0b otherwise. If 1b, indicates that the component implements ACS P2P Completion Redirect. | RO |
| 4 | ACS Upstream Forwarding - Required for Root Ports if the RC supports Redirected Request Validation; required for Switch Downstream Ports; must be hardwired to 0b otherwise. If 1b, indicates that the component implements ACS Upstream Forwarding. | RO |
| 5 | ACS P2P Egress Control - Except as stated below, optional for Root Ports, Switch Downstream Ports, and Multi-Function Device Functions; otherwise this bit must be hardwired to Zero. If Set, indicates that the component implements ACS P2P Egress Control. <br> For an SR-IOV Device not in a Root Complex, this bit is required to be Set for Functions if peer-to-peer transactions within the Device are supported. | RO |
| 6 | ACS Direct Translated P2P - Required for Root Ports that support Address Translation Services (ATS) and also support peer-to-peer traffic with other Root Ports; required for Switch Downstream Ports; required for Multi-Function Device Functions that support Address Translation Services (ATS) and also support peer-to-peer traffic with other Functions; must be hardwired to 0b otherwise. If 1b, indicates that the component implements ACS Direct Translated P2P. | RO |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 7 | ACS Enhanced Capability - Required for Root Ports and Switch Downstream Ports that support the ACS Enhanced Capability mechanisms. <br> If Set, indicates that the component supports all of the following mechanisms that are applicable: <br> - ACS I/O Request Blocking <br> - ACS DSP Memory Target Access <br> - ACS USP Memory Target Access <br> - ACS Unclaimed Request Redirect | RO |
| 15:8 | Egress Control Vector Size - Encodings 01h-FFh directly indicate the number of applicable bits in the Egress Control Vector; the encoding 00h indicates 256 bits. <br> If the ACS P2P Egress Control bit is 0b, the value of the size field is undefined, and the Egress Control Vector Register is not required to be present. | HwInit |

# 7.7.11.3 ACS Control Register (Offset 06h) 

![img-129.jpeg](img-129.jpeg)

Figure 7-134 ACS Control Register

Table 7-119 ACS Control Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 0 | ACS Source Validation Enable - When Set, the component validates the Bus Number from the <br> Requester ID of Upstream Requests against the secondary/subordinate Bus Numbers. <br> Default value of this bit is 0b. Must be hardwired to 0b if the ACS Source Validation functionality is not <br> implemented. | RW |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 1 | ACS Translation Blocking Enable - When Set, the component blocks all Upstream Memory Requests whose Address Type (AT) field is not set to the default value. <br> Default value of this bit is 0b. Must be hardwired to 0b if the ACS Translation Blocking functionality is not implemented. | RW |
| 2 | ACS P2P Request Redirect Enable - In conjunction with ACS P2P Egress Control and ACS Direct Translated P2P mechanisms, determines when the component redirects peer-to-peer Requests Upstream (see § Section 6.12.3). Note that with Downstream Ports, this bit only applies to Upstream Requests arriving at the Downstream Port, and whose normal routing targets a different Downstream Port. <br> Default value of this bit is 0b. Must be hardwired to 0b if the ACS P2P Request Redirect functionality is not implemented. | RW |
| 3 | ACS P2P Completion Redirect Enable - Determines when the component redirects peer-to-peer Completions Upstream; applicable only to Completions ${ }^{176}$ whose Relaxed Ordering Attribute is clear. <br> Default value of this bit is 0b. Must be hardwired to 0b if the ACS P2P Completion Redirect functionality is not implemented. | RW |
| 4 | ACS Upstream Forwarding Enable - When Set, the component forwards Upstream any Request or Completion TLPs it receives that were redirected Upstream by a component lower in the hierarchy. Note that this bit only applies to Upstream TLPs arriving at a Downstream Port, and whose normal routing targets the same Downstream Port. <br> Default value of this bit is 0b. Must be hardwired to 0b if the ACS Upstream Forwarding functionality is not implemented. | RW |
| 5 | ACS P2P Egress Control Enable - In conjunction with the Egress Control Vector plus the ACS P2P Request Redirect and ACS Direct Translated P2P mechanisms, determines when to allow, disallow, or redirect peer-to-peer Requests (see § Section 6.12.3). <br> Default value of this bit is 0b. Must be hardwired to 0b if the ACS P2P Egress Control functionality is not implemented. | RW |
| 6 | ACS Direct Translated P2P Enable - When Set, overrides the ACS P2P Request Redirect and ACS P2P Egress Control mechanisms with peer-to-peer Memory Requests whose Address Type (AT) field indicates a Translated address (see § Section 6.12.3). <br> This bit is ignored if ACS Translation Blocking Enable is 1b. <br> Default value of this bit is 0b. Must be hardwired to 0b if the ACS Direct Translated P2P functionality is not implemented. | RW |
| 7 | ACS I/O Request Blocking Enable - if Set, Upstream I/O Requests received by the Downstream Port must be handled as ACS Violations. <br> This bit is required for Root Ports and Switch Downstream Ports if the ACS Enhanced Capability bit is Set; otherwise it must be RsvdP. The default value of this bit is 0 b. | RW/RsvdP |
| $9: 8$ | ACS DSP Memory Target Access Control - This field controls how a Downstream Port handles Upstream Memory Requests attempting to access any Memory BAR Space on an applicable Root Port or Switch Downstream Port (including the Ingress Port). See § Section 6.12.1.1. <br> Defined Encodings are: | RW/RsvdP |
|  | 00b | Direct Request access enabled |
|  | 01b | Request blocking enabled |
|  | 10b | Request redirect enabled |

[^0]
[^0]:    176. This includes Read Completions, AtomicOp Completions, and other Completions with or without Data.

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | 11b Reserved <br> This field is required for Root Ports and Switch Downstream Ports if the ACS Enhanced Capability bit is Set and there is applicable Memory BAR Space to protect; otherwise it must be RsvdP. The default value of this field is 00 b . |  |
| 11:10 | ACS USP Memory Target Access Control - This field controls how a Switch Downstream Port handles Upstream Memory Requests attempting to access any Memory BAR Space on the Switch Upstream Port. See § Section 6.12.1.1. <br> Defined Encodings are: <br> 00b Direct Request access enabled <br> 01b Request blocking enabled <br> 10b Request redirect enabled <br> 11b Reserved <br> This field is required for Switch Downstream Ports if the ACS Enhanced Capability bit is Set and there is applicable Memory BAR Space to protect; otherwise it must be RsvdP. The default value of this field is 00b. | RW/RsvdP |
| 12 | ACS Unclaimed Request Redirect Control - Controls how a Switch Downstream Port handles incoming Requests targeting Memory Space within the Memory aperture of the Switch Upstream Port that is not within a Memory aperture or Memory BAR Space of any Downstream Port within the Switch. <br> When Set, the Switch must forward such Requests Upstream out of the Switch. <br> When Clear, the Switch Downstream Port must handle such Requests as an Unsupported Request (UR). <br> This bit is required for Switch Downstream Ports if the ACS Enhanced Capability bit is Set; otherwise it must be RsvdP. The default value of this bit is 0 b. | RW/RsvdP |

# 7.7.11.4 Egress Control Vector Register (Offset 08h) 

The Egress Control Vector is a read-write register that contains a bit-array. The number of bits in the register is specified by the Egress Control Vector Size field, and the register spans multiple DWORDs if required. If the ACS P2P Egress Control bit in the ACS Capability Register is 0b, the Egress Control Vector Size field is undefined and the Egress Control Vector Register is not required to be present.

For the general case of an Egress Control Vector spanning multiple DWORDs, the DWORD offset and bit number within that DWORD for a given arbitrary bit $K$ are specified by the formulas ${ }^{177}$ :

$$
\begin{aligned}
& \text { DWORD offset }=08 \mathrm{~h}+(K \operatorname{div} 32) \times 4 \\
& \text { DWORD bit\# }=K \bmod 32
\end{aligned}
$$

Equation 7-4 Egress Control Vector Access

Bits in a DWORD beyond those specified by the Egress Control Vector Size field are RsvdP.
For Root Ports and Switch Downstream Ports, each bit in the bit-array always corresponds to a Port Number. Otherwise, for Functions ${ }^{178}$ within a Multi-Function Device, each bit in the bit-array corresponds to one or more Function Numbers,

[^0]
[^0]:    177. Div is an integer divide with truncation. Mod is the remainder from an integer divide.
    178. Including Switch Upstream Ports.

or a Function Group Number. For example, access to Function 2 is controlled by bit number 2 in the bit-array. For both Port Number cases and Function Number cases, the bit corresponding to the Function that implements this Extended Capability structure must be hardwired to 0 b. ${ }^{179}$

If an ARI Device implements ACS Function Groups (ACS Function Groups Capability is Set), its Egress Control Vector Size is required to be a power-of-2 from 8 to 256, and all of its implemented Egress Control Vector bits must be RW. With ARI Devices, multiple Functions can be associated with a single bit, so for each Function, its associated bit determines how Requests from it targeting other Functions (if any) associated with the same bit are handled.

If ACS Function Groups are enabled in an ARI Device (ACS Function Groups Enable is Set), the first 8 Egress Control Vector bits in each Function are associated with Function Group Numbers instead of Function Numbers. In this case, access control is enforced between Function Groups instead of Functions, and any implemented Egress Control Vector bits beyond the first 8 are unused.

Independent of whether an ARI Device implements ACS Function Groups, its Egress Control Vector Size is not required to cover the entire Function Number range of all Functions implemented by the Device. If ACS Function Groups are not enabled, Function Numbers are mapped to implemented Egress Control Vector bits by taking the modulo of the Egress Control Vector Size, which is constrained to be a power-of-2.

With RCs, some Port Numbers may refer to internal Ports instead of Root Ports. For Root Ports in such RCs, each bit in the bit-array that corresponds to an internal Port must be hardwired to 0 b.
![img-130.jpeg](img-130.jpeg)

Table 7-120 Egress Control Vector Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 31:0 | Egress Control Vector - An N-bit bit-array configured by software, where N is given by the value in the Egress Control Vector Size field. When a given bit is Set, peer-to-peer Requests targeting the associated Port, Function, or Function Group are blocked or redirected (if enabled) (see § Section 6.12.3). <br> § Figure 7-135 shows a single DWORD register. This register is always an integral number of DWORDs. <br> Default value of each bit is 0 b. | RW |

The following examples illustrate how the vector might be configured:

- For an 8-Port Switch, each Port will have a separate vector indicating which Downstream Egress Ports it may forward Requests to.
Port 1 being not allowed to communicate with any other Downstream Ports would be configured as: 1111 1100b with bit 0 corresponding to the Upstream Port (hardwired to 0b) and bit 1 corresponding to the Ingress Port (hardwired to 0b).

Port 2 being allowed to communicate with Ports 3, 5, and 7 would be configured as: 0101 0010b.

- For a 4-Function device, each Function will have a separate vector that indicates which Function it may forward Requests to.

[^0]
[^0]:    179. For ARI Devices, the bit must be RW. See subsequent description.

Function 0 being not allowed to communicate with any other Functions would be configured as: 1110b with bit 0 corresponding to Function 0 (hardwired to 0b).

Function 1 being allowed to communicate with Functions 2 and 3 would be configured as: 0001b with bit 1 corresponding to Function 1 (hardwired to 0b).

# 7.8 Common PCI and PCIe Capabilities 

This section, contains a description of common PCI and PCIe capabilities that are individually optional in this but may be required by other PCISIG specifications.

### 7.8.1 Power Budgeting Extended Capability

The Power Budgeting Extended Capability allows the system to allocate power to devices that are added to the system at runtime. Through this Capability, a device can report the power it consumes on a variety of power rails, in a variety of device power-management states, in a variety of operating conditions. The system can use this information to ensure that the system is capable of providing the proper power and cooling levels to the device. Failure to indicate proper device power consumption may risk device or system failure.

Implementation of the Power Budgeting Extended Capability is optional for PCI Express devices that are implemented either in a form-factor which does not require Hot-Plug support, or that are integrated on the system board. PCI Express form-factor specifications may require support for power budgeting. Power Budgeting reports device power consumption assuming the device is given appropriate permission (e.g., from Set_Slot_Power_Limit message) and that the external power connections for the device are operating.

The Power Budgeting Extended Capability is permitted to be present in PFs, but VFs must not implement it. If a PF contains the capability, it must report values that cover all associated VFs.
§ Figure 7-136 details allocation of register fields in the Power Budgeting Extended Capability.
![img-131.jpeg](img-131.jpeg)

Figure 7-136 Power Budgeting Extended Capability

### 7.8.1.1 Power Budgeting Extended Capability Header (Offset 00h)

§ Figure 7-137 details allocation of register fields in the Power Budgeting Extended Capability Header; § Table 7-121 provides the respective bit definitions. Refer to § Section 7.6.3 for a description of the PCI Express Extended Capability header. The Extended Capability ID for the Power Budgeting Extended Capability is 0004h.

![img-132.jpeg](img-132.jpeg)

Figure 7-137 Power Budgeting Extended Capability Header

Table 7-121 Power Budgeting Extended Capability Header

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $15: 0$ | PCI Express Extended Capability ID - This field is a PCI-SIG defined ID number that indicates the nature and format of the Extended Capability. <br> Extended Capability ID for the Power Budgeting Extended Capability is 0004h. | RO |
| $19: 16$ | Capability Version - This field is a PCI-SIG defined version number that indicates the version of the Capability structure present. <br> Must be 1 h for this version of the specification. | RO |
| $31: 20$ | Next Capability Offset - This field contains the offset to the next PCI Express Capability structure or 000h if no other items exist in the linked list of Capabilities. <br> For Extended Capabilities implemented in Configuration Space, this offset is relative to the beginning of PCI-compatible Configuration Space and thus must always be either 000 h (for terminating list of Capabilities) or greater than 0FFh. | RO |

# 7.8.1.2 Power Budgeting Data Select Register (Offset 04h) 

The Power Budgeting Data Select Register is an 8-bit read-write register that indexes the Power Budgeting Data reported through the Power Budgeting Data Register and selects the DWORD of Power Budgeting Data that is to appear in the Power Budgeting Data Register. Values for this register start at zero to select the first DWORD of Power Budgeting Data; subsequent DWORDs of Power Budgeting Data are selected by increasing index values. The default value of this register is undefined.

### 7.8.1.3 Power Budgeting Control Register (Offset 06h)

The Power Budgeting Control Register permits system software to enable extended power budgeting and to grant additional power to a Device above that defined by default for the associated form-factor.
§ Figure 7-138 details allocation of register fields in the Aux Power Control register; § Table 7-122 provides the respective bit definitions.

![img-133.jpeg](img-133.jpeg)

Figure 7-138 Power Budgeting Control Register

Table 7-122 Power Budgeting Control Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 0 | Extended Power Budgeting Enable - If Set, Power Budgeting is permitted to return non-zero values in the Power Budgeting Data Register bits 31:21. If Clear, those bits must return all zeros for all values of the Power Budgeting Data Select Register. <br> If Set, the Power Budgeting Sense Detect Register is permitted to return non-zero values. If Clear, that register must return all zeros. <br> This bit is hardwired to 0b when Extended Power Budgeting Supported is Clear. <br> Default is zero. | RW |
| 1 | Power Limit Enable - If Set, the Power Limit PM Sub State field is meaningful. <br> The value of this field in the lowest numbered Function with Power Limit Supported Set applies to all Functions of the Device. When present, the value of this bit in all other Functions is ignored by hardware. <br> When Power Limit Supported is Clear, this bit is permitted to be hardwired to zero. <br> It is recommended that system software / firmware configure this field identically in all Functions. Doing so provides a standard mechanism for a device driver to understand its Function's power configuration. <br> Default is zero. | RWS/RsvdP |
| $4: 2$ | Power Limit PM Sub State - If Power Limit Enable is Set, this field, in conjunction with the Out of Band Power Limit Enable and Out of Band Power Limit PM Sub State fields, indicates the PM Sub State used by the Device. <br> The value of this field in the lowest numbered Function with Power Limit Supported Set applies to all Functions of the Device. When present, the value of this field in all other Functions is ignored by hardware. <br> When Power Limit Supported is Clear, this field is permitted to be hardwired to zero. <br> It is recommended that system software / firmware configure this field identically in all Functions. Doing so provides a standard mechanism for a device driver to understand its Function's power configuration. <br> Default is zero. | RWS/RsvdP |
| 5 | Out of Band Power Limit Enable - If Set, the Out of Band Power Limit PM Sub State field is meaningful. | Hwinit/RsvdP |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | When this field is present, all Functions of the Device must contain the same value. <br> When Power Limit Supported is Clear, this bit is permitted to be hardwired to zero. <br> It is permitted that this field change after the Function is Configuration Ready. This could happen, for example, if this field is configured via MCTP over PCIe. Mechanisms used to delay access to this field until it is meaningful are outside the scope of this specification (e.g., using the SFI mechanism or using _DSM calls to grant system software access to the fields). <br> Default is zero. |  |
| 8:6 | Out of Band Power Limit PM Sub State - If Out of Band Power Limit Enable is Set, this field, in conjunction with the Power Limit Enable and Power Limit PM Sub State fields, indicates the PM Sub State used by the Device. <br> When this field is present, all Functions of the Device must contain the same value. <br> When Power Limit Supported is Clear, this bit is permitted to be hardwired to zero. <br> It is permitted that this field change after the Function is Configuration Ready. This could happen, for example, if this field is configured via MCTP over PCIe. Mechanisms used to delay access to this field until it is meaningful are outside the scope of this specification (e.g., using the SFI mechanism or using _DSM calls to grant system software access to the fields). <br> Default is zero. | HwInit/RsvdP |

# 7.8.1.4 Power Budgeting Data Register (Offset 08h) 

This read-only register returns the DWORD of Power Budgeting Data selected by the Power Budgeting Data Select Register. Each DWORD of the Power Budgeting Data describes the power usage of the device in a particular operating condition. Power Budgeting Data for different operating conditions is not required to be returned in any particular order, as long as incrementing the Power Budgeting Data Select Register causes information for a different operating condition to be returned. If the Power Budgeting Data Select Register contains a value greater than or equal to the number of operating conditions for which the device provides power information, this register must return all zeros. The default value of this register is undefined. § Figure 7-139 details allocation of register fields in the Power Budgeting Data Register; § Table 7-123 provides the respective bit definitions.

In earlier versions of this specification, bits 31:21 of this register were RsvdP. In order to ensure that the new uses of these bits do not confuse existing software:

- Extended Power Budgeting entries are hidden when Extended Power Budgeting Enable is Clear (the default). When Extended Power Budgeting Enable is Clear and Power Budgeting Data Select selects an Extended Power Budgeting entry, the Data register must return 0000 0000h.
- Extended Power Budgeting Data entries must be located after non-extended Power Budgeting Data entries (i.e., all entries where bits 31:21 are zero must use a smaller Power Budgeting Data Select value than any entry where bits 31:21 are non-zero).

The Base Power and Data Scale fields describe the power usage of the device; the Power Rail, Type, PM State, and PM Sub State fields describe the conditions under which the device has this power usage.

![img-134.jpeg](img-134.jpeg)

Figure 7-139 Power Budgeting Data Register 9

Table 7-123 Power Budgeting Data Register 9

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 7:0 | Base Power - Specifies in watts the base power value in the given operating condition. This value must be multiplied by the data scale to produce the actual power consumption value except if Extended Power Budgeting Enable is Clear, the Data Scale[1:0] field equals 00b (1.0x) and Base Power exceeds EFh, the following alternative encodings are used: | RO |
|  | F0h | $>239 \mathrm{~W}$ and $\leq 250 \mathrm{~W}$ Slot Power Limit |
|  | F1h | $>250 \mathrm{~W}$ and $\leq 275 \mathrm{~W}$ Slot Power Limit |
|  | F2h | $>275 \mathrm{~W}$ and $\leq 300 \mathrm{~W}$ Slot Power Limit |
|  | F3h | $>300 \mathrm{~W}$ and $\leq 325 \mathrm{~W}$ Slot Power Limit |
|  | F4h | $>325 \mathrm{~W}$ and $\leq 350 \mathrm{~W}$ Slot Power Limit |
|  | F5h | $>350 \mathrm{~W}$ and $\leq 375 \mathrm{~W}$ Slot Power Limit |
|  | F6h | $>375 \mathrm{~W}$ and $\leq 400 \mathrm{~W}$ Slot Power Limit |
|  | F7h | $>400 \mathrm{~W}$ and $\leq 425 \mathrm{~W}$ Slot Power Limit |
|  | F8h | $>425 \mathrm{~W}$ and $\leq 450 \mathrm{~W}$ Slot Power Limit |
|  | F9h | $>450 \mathrm{~W}$ and $\leq 475 \mathrm{~W}$ Slot Power Limit |
|  | FAh | $>475 \mathrm{~W}$ and $\leq 500 \mathrm{~W}$ Slot Power Limit |
|  | FBh | $>500 \mathrm{~W}$ and $\leq 525 \mathrm{~W}$ Slot Power Limit |
|  | FCh | $>525 \mathrm{~W}$ and $\leq 550 \mathrm{~W}$ Slot Power Limit |
|  | FDh | $>550 \mathrm{~W}$ and $\leq 575 \mathrm{~W}$ Slot Power Limit |
|  | FEh | $>575 \mathrm{~W}$ and $\leq 600 \mathrm{~W}$ Slot Power Limit |
|  | FFh | Reserved for values greater than 600 W |
| 9:8 | Data Scale[1:0] - Specifies the scale to apply to the Base Power value. The power consumption of the device is determined by multiplying the contents of the Base Power field with the value corresponding to the encoding returned by this field, except as noted above. | RO |
|  | Note that Data Scale[2] and Data Scale[1:0] are not contiguous within this register. |  |
|  | Defined encodings are: |  |
|  | 000b | $1.0 x$ |
|  | 001b | $0.1 x$ |

| Bit Location | Register Description |  | Attributes |
| :--: | :--: | :--: | :--: |
|  | 010b | 0.01x |  |
|  | 011b | 0.001x |  |
|  | 100b | $10 x$ |  |
|  | 101b | $100 x$ |  |
|  | Others | Reserved |  |
| 12:10 | PM Sub State - Specifies the power management sub state of the operating condition being described. |  | RO |
|  | Defined encodings are: |  |  |
|  | 000b | Default Sub State |  |
|  | 001b - 111b | Device Specific Sub State |  |
| 14:13 | PM State - Specifies the power management state of the operating condition being described. |  | RO |
|  | Defined encodings are: |  |  |
|  | 00b | D0 |  |
|  | 01b | D1 |  |
|  | 10b | D2 |  |
|  | 11b | D3 |  |
|  | A device returns 11b in this field and Auxiliary or PME Aux in the Type field to specify the $\mathrm{D} 3_{\text {Cold }} \mathrm{PM}$ State. An encoding of 11 b along with any other Type field value specifies the $\mathrm{D} 3_{\text {Hot }}$ state. |  |  |
| 17:15 | Type - Specifies the type of the operating condition being described. Defined encodings are: |  | RO |
|  | 000b | PME Aux -- Sustained Power consumed in D3 ${ }_{\text {Cold }}$ when PME_En is Set and Aux Power PM Enable is Clear |  |
|  | 001b | Auxiliary -- Sustained Power consumed in D3 ${ }_{\text {Cold }}$ when Aux Power PM Enable is Set |  |
|  | 010b | Idle -- Sustained Power consumed when the Function or Device has been idle for 20 seconds or more |  |
|  | 011b | Sustained Power |  |
|  | 100b | Sustained Power in Emergency Power Reduction State (see § Section 6.24 ) |  |
|  | 101b | Maximum Power in Emergency Power Reduction State (see § Section 6.24 ) |  |
|  | 111b | Maximum Power |  |
|  | Others | All other encodings are Reserved. |  |
|  | The following measurement definitions apply to this field unless the form-factor specification explicitly states otherwise: |  |  |
|  | - Sustained Power means the power consumed when the Device is performing at its maximum throughput, measured as an average over 1 second. |  |  |
|  | - Maximum Power means the power consumed when the Device is performing at its maximum throughput, measured over a $100 \mu \mathrm{~s}$ moving window. Note that Maximum Power can easily exceed sustained power by as much as $250 \%$. Maximum Power consumption is frequently associated with changes in Function D-state. |  |  |
| 20:18 | Power Rail - Specifies the thermal load or power rail of the operating condition being described. |  | RO |
|  | Defined encodings are: |  |  |
|  | 000b | Power (12V) |  |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | 001b | Power (3.3V) |
|  | 010b | Power (1.5V or 1.8 V ) |
|  | 100b | Power (48V) |
|  | 101b | Power (5V) |
|  | 111b | Thermal |
|  | Others | All other encodings are Reserved. |
| 21 | Data Scale[2] - Upper bit of Data Scale field. See Data Scale[1:0] for details. <br> This bit must be zero if Extended Power Budgeting Enable is Clear. | RO |
| $24: 22$ | Connector Number - Up to 8 connectors that supply power are supported on an add-in card (including the edge connector(s)). This field indicates which power connector is associated with this entry. <br> If Power Budgeting Sense Detect Supported is Set, an instance of this field must be implemented for every power connector that the add-in card supports. <br> Connector Numbers represent a single physical connector and are global across the add-in card. Connector Numbers must be consistent across all Functions in a Multi-Function Device. Connector Numbers must match when a single connector contains more than one power rail or when a single connector is associated with more than one Connector Type (e.g., Types 00 0110b and 00 0111b). <br> Connector Number values and the mapping of Connector Number to physical location are outside the scope of this specification. For form-factor specifications that specify connector placement, it is recommended that those specifications define connector numbering based on placement rules. <br> This field must be zero if Extended Power Budgeting Enable is Clear. <br> Software must ignore the value in this field if Extended Power Budgeting Present is Clear. | RO |
| 30:25 | Connector Type - Indicates the connector type. If Power Budgeting Sense Detect Supported is Set, an instance of this field must be implemented for every power connector that the adaptor supports. Values are: <br> 000000 b <br> 000001 b <br> 000010 b <br> 000011 b <br> 000100 b <br> 000101 b <br> 000101 b <br> 000110 b <br> 000111 b <br> 001000 b <br> 001001 b <br> 001011 b <br> 001011 b <br> 001101 b <br> 001100 b <br> 001101 b <br> 001000 b <br> 001001 b <br> 001010 b <br> 001011 b <br> 001100 b <br> 001011 b <br> 001100 b <br> 001101 b | Form-factor defined edge connector <br> Non-Connector power provided by the system (e.g., soldered down) <br> Non-Connector power provided by the option card (e.g., battery) <br> Non-Connector power not provided by the system or the option card (e.g., power supplied by an external chassis) <br> CEM 2x3 connector <br> CEM 2x4 connector with either $2 \times 3$ cable or $2 \times 4$ cable (see below) <br> CEM 2x4 connector with $2 \times 3$ cable (see below) <br> CEM 2x4 connector with $2 \times 4$ cable (see below) <br> CEM 12VHPWR connector, cable has both Sense0 and Sense1 Open <br> CEM 12VHPWR connector, cable has Sense0 Grounded and Sense1 Open <br> CEM 12VHPWR connector, has Sense0 Open and Sense1 Grounded <br> CEM 12VHPWR connector, has both Sense0 and Sense1 Grounded <br> CEM 48VHPWR connector, cable has both Sense0 and Sense1 Open <br> CEM 48VHPWR connector, cable has Sense0 Grounded and Sense1 Open | RO |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | 001110 b | CEM 48VHPWR connector, cable has Sense0 Open and Sense1 Grounded |
|  | 001111 b | CEM 48VHPWR connector, cable has both Sense0 and Sense1 Grounded |
|  | 010000 b | CEM 12V-2x6: 150 W or higher cable present |
|  | 010001 b | CEM 12V-2x6: 300 W or higher cable present |
|  | 010010 b | CEM 12V-2x6: 450 W or higher cable present |
|  | 010011 b | CEM 12V-2x6: 600 W cable present |
|  | 010100 b to 101111 b | Reserved for PCI-SIG use |
|  | 110000 b to 111111 b | Vendor Specific Power Connectors |
|  | Each CEM $2 \times 4$ connector must have either one entry with Connector Type 000101 b or two entries with Connector Types 000110 b and 000111 b . <br> Each $12 \mathrm{~V}-2 \times 6$ connector must have an entry for the lowest power cable it supports. Each $12 \mathrm{~V}-2 \times 6$ connector must have an entry for every cable that has a different power consumption value. <br> This field must be zero if Extended Power Budgeting Enable is Clear. <br> Software must ignore the value in this field if Extended Power Budgeting Present is Clear. |  |
| 31 | Extended Power Budgeting Present - Indicates that bits 30:22 contain Extended Power Budgeting Data. This bit must be 0b if Extended Power Budgeting Enable is Clear. | RO |

Except for Type $=000$ b and 001b, Power Budgeting data for the same operating condition and PM Sub State values represent simultaneous consumption. Functions must report a complete set of Power Budgeting data for each supported operating condition and PM Sub State combination.

Power Budgeting data with different PM Sub State values represent mutually exclusive consumption. For a given operating condition, a Function is in exactly one PM Sub State. When Power Limit Supported is Clear, implementation specific mechanisms are used to determine the current PM Sub State.

A device that implements the Power Budgeting Extended Capability is required to provide data values for DO Maximum and DO Sustained PM State and Type combinations for every power rail from which it consumes power; data for the DO Maximum and DO Sustained for Thermal must also be provided if these values are different from the sum of the values for an operating condition reported for DO Maximum and DO Sustained on the power rails.

Devices that support auxiliary power or PME from auxiliary power must provide data for the appropriate power Type (Auxiliary or PME Aux) on the appropriate Power Rail(s).

- If the reported PME Aux or Auxiliary value is greater than the default for the associated form-factor, the Function is limited to the form-factor values unless either PME_En or Aux Power PM Enable are Set.
- The PME Aux and Auxiliary entries are mutually exclusive. The values of PME_En and Aux Power PM Enable determine which entries are meaningful.

If the reported PME Aux or Auxiliary value is greater than the Aux_Current, the Function is limited by Aux_Current unless Aux Power PM Enable is Set and one of the following is true:

- Power Limit Enable is Set,
- Out of Band Power Limit Enable is Set, or
- the Request $\mathrm{D3}_{\text {Cold }}$ Aux Power Limit _DSM call was used to request additional power (for details, see [Firmware]).

If a device implements Emergency Power Reduction State, it must report Power Budgeting values for the following:

- Maximum Emergency Power Reduction State, PM State D0, all power rails used by the device
- Maximum Emergency Power Reduction State, PM State D0, Thermal (if different from the sum of the preceding values)
- Sustained Emergency Power Reduction State, PM State D0, all power rails used by the device
- Sustained Emergency Power Reduction State, PM State: D0, Thermal (if different from the sum of the preceding values)


# 7.8.1.5 Power Budgeting Capability Register (Offset 0Ch) 

This register indicates the power budgeting capabilities of a device. $\S$ Figure 7-140 details allocation of register fields in the Power Budgeting Capability Register; $\S$ Table 7-124 provides the respective bit definitions.
![img-135.jpeg](img-135.jpeg)

Figure 7-140 Power Budgeting Capability Register

Table 7-124 Power Budgeting Capability Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 0 | System Allocated - When Set, this bit indicates that the power budget for the device is included within the system power budget. Reported Power Budgeting Data for this device must be ignored by software for power budgeting decisions if this bit is Set. | HwInit |
| 1 | Extended Power Budgeting Supported - If Set, the Extended Power Budgeting Enable bit is meaningful. | HwInit |
| 2 | Power Budgeting Sense Detect Supported - If Set, the Power Budgeting Sense Detect Register is meaningful. <br> This bit must be Clear if Extended Power Budgeting Supported is Clear. | HwInit |
| 3 | Power Limit Supported - If Set, the Power Limit Enable, Power Limit PM Sub State, Out of Band Power Limit Enable, and Out of Band Power Limit PM Sub State fields are meaningful. <br> This bit must be Clear if Extended Power Budgeting Supported is Clear. | HwInit |
| $5: 4$ | Power Disable Supported - Indicates the supported use model for optional form-factor defined Power Disable functionality. Encodings are: <br> 00b Power Disable support not reported | HwInit |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | 01b | Power Disable is supported for removal of main power. The timings associated with this mode are optimized to support the use of Power Disable to recover a non-responsive device. |
|  | 10b | Power Disable with abbreviated assertion time is supported for removal of main power. The timings associated with this mode are optimized to using Power Disable to request the Device enter or exit D3 ${ }_{\text {Cold. }}$ |
|  | 11b | Reserved |
|  | For Multi-Function Devices associated with an Upstream Port, all Functions that contain this field must return the same value. |  |
| $7: 6$ | Power Loss Notification Supported - This field indicates Device support for the optional Power Loss Notification feature. Power Loss Notification is an optional form-factor feature that permits the platform to inform an add-in card of an upcoming loss of power and optionally for the add-in card to indicate that it is ready for that power loss. In the M. 2 form-factor, Power Loss Notification uses the optional PLN\# signal and Power Loss Acknowledgment uses the optional PLA_52\# and PLA_53\# signals. Other form-factors may define different mechanisms. <br> Encodings of this field are: | HwInit |
|  | 00b | Power Loss Notification support not reported |
|  | 01b | Power Loss Notification supported Power Loss Acknowledgement not supported |
|  | 10b | Power Loss Notification supported Power Loss Acknowledgement supported |
|  | 11b | Reserved |
|  | For Multi-Function Devices associated with an Upstream Port, all Functions that contain this field must return the same value. |  |

# 7.8.1.6 Power Budgeting Sense Detect Register (Offset 0Dh) 

Whenever the adapter is receiving any power, this register reports, for each implemented power connector, which sense wires are currently detected.

Any adapter that implements a Power Budgeting Extended Capability with Power Budgeting Sense Detect Supported Set, must provide Connector Sense Detect fields for each connector that it supports, and must hardwire the fields for unsupported connectors to all zeros.

This register is RsvdP if Power Budgeting Sense Detect Supported is Clear. This register must return all zeros if Extended Power Budgeting Enable is Clear.

This register is only meaningful in the lowest numbered Function that contains the Power Budgeting Extended Capability. This register is undefined in all other Functions even if the Power Budgeting Sense Detect Supported is Set.
§ Figure 7-141 details allocation of register fields in the Power Budgeting Sense Detect Register; § Table 7-125 provides the respective bit definitions. § Table 7-126 defines the encodings based on Connector Type values.

![img-136.jpeg](img-136.jpeg)

Figure 7-141 Power Budgeting Sense Detect Register

Table 7-125 Power Budgeting Sense Detect Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 2:0 | Connector Number 0 Sense Data | RO |
| 5:3 | Connector Number 1 Sense Data | RO |
| 8:6 | Connector Number 2 Sense Data | RO |
| 11:9 | Connector Number 3 Sense Data | RO |
| 14:12 | Connector Number 4 Sense Data | RO |
| 17:15 | Connector Number 5 Sense Data | RO |
| 20:18 | Connector Number 6 Sense Data | RO |
| 23:21 | Connector Number 7 Sense Data | RO |

Table 7-126 Power Budgeting Sense Detect Encodings

| Connecor Type | Encoding |  |
| :--: | :--: | :--: |
| 000000 b to 000011 b | Bit 0 | Main Power Detected. If Auxiliary power is not used, this bit is permitted to be hardwired to 1b. |
|  | Bit 1 | Aux Power Detected. If auxiliary power is not used, this bit is permitted to be hardwired to 0 b. When no dedicated Aux Power pin(s) are defined in the implemented form-factor, this bit has a form-factor specific meaning. |
|  | Bit 2 | Form-factor specific meaning |
| 000100 b | CEM 2x3 connector |  |
|  | 000b | Cable is not present, Sense not detected |
|  | 001b | Cable is present, Sense detected |
|  | Others | Reserved |

| Connecor Type | Encoding |
| :--: | :--: |
| 000101 b to 000111 b | CEM $2 \times 4$ connector |
|  | 000b Cable is not present, both Sense0 and Sense1 not detected |
|  | 001b 2x3 cable is present, Sense0 detected, Sense1 not detected |
|  | 010b Reserved condition, Sense0 not detected, Sense1 detected |
|  | 011b 2x4 cable is present, both Sense0 and Sense1 detected |
|  | Others Reserved |
| 001000 b to 001011 b | CEM 12VHPWR connector |
|  | 0xxb Cable is not present |
|  | 100b 12VHPWR cable is present, both Sense0 and Sense1 are Open |
|  | 101b 12VHPWR cable is present, Sense0 is Grounded, Sense1 Open |
|  | 110b 12VHPWR cable is present, Sense0 Open, Sense1 Grounded |
|  | 111b 12VHPWR cable is present, both Sense0 and Sense1 Grounded |
|  | Others Reserved |
| 001100 b to 001111 b | CEM 48VHPWR connector |
|  | 0xxb Cable is not present |
|  | 100b 48VHPWR cable is present, both Sense0 and Sense1 Open |
|  | 101b 48VHPWR cable is present, Sense0 Grounded, Sense1 Open |
|  | 110b 48VHPWR cable is present, Sense0 Open, Sense1 Grounded |
|  | 111b 48VHPWR cable is present, both Sense0 and Sense1 Grounded |
|  | Others Reserved |
| 010000 b | CEM 12V-2x6 connector, 150 W or higher cable |
|  | 000b Cable is not present |
|  | 100b 150 W 12V-2x6 cable is present |
|  | 101b 300 W 12V-2x6 cable is present |
|  | 110b 450 W 12V-2x6 cable is present |
|  | 111b 600 W 12V-2x6 cable is present |
|  | Others Reserved |
| 010001 b | CEM 12V-2x6 connector, 300 W or higher cable |
|  | 000b Cable is not present |
|  | 100b Cable is not present or 150 W 12V-2x6 cable is present ${ }^{180}$ |
|  | 101b 300 W 12V-2x6 cable is present |
|  | 110b 450 W 12V-2x6 cable is present |
|  | 111b 600 W 12V-2x6 cable is present |
|  | Others Reserved |

180. Detecting the 12V-2x6 150 W cable requires additional circuitry. This circuitry is optional when the add-in card always requires more than 150 W from the 12V-2x6 connector.

| Connecor Type |  | Encoding |
| :--: | :--: | :--: |
| 010010 b | CEM 12V-2x6 connector, 450 W or higher cable <br> 000b Cable is not present |  |
|  | 100b | Cable is not present or 150 W 12V-2x6 cable is present ${ }^{181}$ |
|  | 101b | 300 W 12V-2x6 cable is present ${ }^{182}$ |
|  | 110b | 450 W 12V-2x6 cable is present |
|  | 111b | 600 W 12V-2x6 cable is present |
|  | Others | Reserved |
| 010011 b | CEM 12V-2x6 connector, 600 W cable |  |
|  | 000b | Cable is not present |
|  | 100b | Cable is not present or 150 W 12V-2x6 cable is present ${ }^{183}$ |
|  | 101b | 300 W 12V-2x6 cable is present ${ }^{184}$ |
|  | 110b | 450 W 12V-2x6 cable is present ${ }^{185}$ |
|  | 111b | 600 W 12V-2x6 cable is present |
|  | Others | Reserved |
| 010100 b to 101111 h | Reserved for PCI-SIG use |  |
| 110000 b to 111111 b | Vendor Specific |  |

# 7.8.2 Latency Tolerance Reporting (LTR) Extended Capability 9 

The PCI Express Latency Tolerance Reporting (LTR) Extended Capability is an optional Extended Capability that allows software to provide platform latency information to components with Upstream Ports (Endpoints and Switches), and is required for Switch Upstream Ports and Endpoints if the Function supports the LTR mechanism. It is not applicable to Root Ports, Bridges, or Switch Downstream Ports.

For a Multi-Function Device associated with the Upstream Port of a component that implements the LTR mechanism, this Capability structure must be implemented only in Function 0, and must control the component's Link behavior on behalf of all the Functions of the Device.

RCIEPs implemented as Multi-Function Devices are permitted to implement this Capability structure in more than one Function of the Multi-Function Device.

[^0]
[^0]:    181. Detecting the 12V-2x6 150 W cable requires additional circuitry. This circuitry is optional when the add-in card always requires more than 150 W from the 12V-2x6 connector.
    182. This combination indicates the provided power is less than the connector requirements. The add-in card does not use this cable. This sense data encoding is used to tell software.
    183. Detecting the 12V-2x6 150 W cable requires additional circuitry. This circuitry is optional when the add-in card always requires more than 150 W from the 12V-2x6 connector.
    184. This combination indicates the provided power is less than the connector requirements. The add-in card does not use this cable. This sense data encoding is used to tell software.
    185. This combination indicates the provided power is less than the connector requirements. The add-in card does not use this cable. This sense data encoding is used to tell software.

![img-137.jpeg](img-137.jpeg)

Figure 7-142 LTR Extended Capability Structure 8

# 7.8.2.1 LTR Extended Capability Header (Offset 00h) 

![img-138.jpeg](img-138.jpeg)

Figure 7-143 LTR Extended Capability Header 9

Table 7-127 LTR Extended Capability Header 9

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| $15: 0$ | PCI Express Extended Capability ID - This field is a PCI-SIG defined ID number that indicates the nature <br> and format of the Extended Capability. <br> PCI Express Extended Capability for the LTR Extended Capability is 0018h. | RO |
| $19: 16$ | Capability Version - This field is a PCI-SIG defined version number that indicates the version of the <br> Capability structure present. <br> Must be 1h for this version of the specification. | RO |
| $31: 20$ | Next Capability Offset - This field contains the offset to the next PCI Express Extended Capability <br> structure or 000h if no other items exist in the linked list of Capabilities. | RO |

### 7.8.2.2 Max Snoop Latency Register (Offset 04h)

![img-139.jpeg](img-139.jpeg)

Figure 7-144 Max Snoop Latency Register 9

Table 7-128 Max Snoop Latency Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 9:0 | Max Snoop LatencyValue - Along with the Max Snoop LatencyScale field, this register specifies the maximum snoop latency that a device is permitted to request. Software should set this to the platform's maximum supported latency or less. It is strongly recommended that any updates to this field are reflected in LTR Message(s) sent by the device within 1 ms. <br> The default value for this field is 0000000000 b . | RW |
| 12:10 | Max Snoop LatencyScale - This register provides a scale for the value contained within the Max Snoop LatencyValue field. Encoding is the same as the LatencyScale fields in the LTR Message. See $\S$ Section 6.18 . It is strongly recommended that any updates to this field are reflected in LTR Message(s) sent by the device within 1 ms. <br> The default value for this field is 000 b . <br> Hardware operation is undefined if software writes a Not Permitted value to this field. | RW |

# 7.8.2.3 Max No-Snoop Latency Register (Offset 06h) 

![img-140.jpeg](img-140.jpeg)

Figure 7-145 Max No-Snoop Latency Register

Table 7-129 Max No-Snoop Latency Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 9:0 | Max No-Snoop LatencyValue - Along with the Max No-Snoop LatencyScale field, this register specifies the <br> maximum no-snoop latency that a device is permitted to request. Software should set this to the <br> platform's maximum supported latency or less. It is strongly recommended that any updates to this field <br> are reflected in LTR Message(s) sent by the device within 1 ms. <br> The default value for this field is 000000000 b . | RW |
| 12:10 | Max No-Snoop LatencyScale - This register provides a scale for the value contained within the Max <br> No-Snoop LatencyValue field. Encoding is the same as the LatencyScale fields in the LTR Message. See <br> $\S$ Section 6.18. It is strongly recommended that any updates to this field are reflected in LTR Message(s) <br> sent by the device within 1 ms. <br> The default value for this field is 000 b. <br> Hardware operation is undefined if software writes a Not Permitted value to this field. | RW |

### 7.8.3 L1 PM Substates Extended Capability

The L1 PM Substates Extended Capability is an optional Extended Capability, that is required if L1 PM Substates is implemented at a Port. The L1 PM Substates Extended Capability structure is defined as shown in § Figure 7-146.

For a Multi-Function Device associated with an Upstream Port implementing L1 PM Substates, this Extended Capability Structure must be implemented only in Function 0, and must control the Upstream Port's Link behavior on behalf of all the Functions of the device.
![img-141.jpeg](img-141.jpeg)

Figure 7-146 L1 PM Substates Extended Capability

# 7.8.3.1 L1 PM Substates Extended Capability Header (Offset 00h) 

![img-142.jpeg](img-142.jpeg)

Figure 7-147 L1 PM Substates Extended Capability Header

Table 7-130 L1 PM Substates Extended Capability Header

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $15: 0$ | PCI Express Extended Capability ID - This field is a PCI-SIG defined ID number that indicates the nature and format of the Extended Capability. <br> Extended Capability ID for L1 PM Substates is 001Eh. | RO |
| 19:16 | Capability Version - This field is a PCI-SIG defined version number that indicates the version of the Capability structure present. <br> This field must be 2 h if the L1 PM Substates Status Register is implemented and must be 1 h otherwise. | RO |
| $31: 20$ | Next Capability Offset - This field contains the offset to the next PCI Express Capability structure or 000h if no other items exist in the linked list of Capabilities. <br> For Extended Capabilities implemented in Configuration Space, this offset is relative to the beginning of PCI-compatible Configuration Space and thus must always be either 000 h (for terminating list of Capabilities) or greater than 0FFh. <br> The bottom 2 bits of this offset are Reserved and must be implemented as 00b although software must mask them to allow for future uses of these bits. | RO |

# 7.8.3.2 L1 PM Substates Capabilities Register (Offset 04h) 

![img-143.jpeg](img-143.jpeg)

Figure 7-148 L1 PM Substates Capabilities Register

Table 7-131 L1 PM Substates Capabilities Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 0 | PCI-PM L1.2 Supported - When Set this bit indicates that PCI-PM L1.2 is supported. | Hwinit |
| 1 | PCI-PM L1.1 Supported - When Set this bit indicates that PCI-PM L1.1 is supported, and must be Set by all Ports implementing L1 PM Substates. | Hwinit |
| 2 | ASPM L1.2 Supported - When Set this bit indicates that ASPM L1.2 is supported. | Hwinit |
| 3 | ASPM L1.1 Supported - When Set this bit indicates that ASPM L1.1 is supported. | Hwinit |
| 4 | L1 PM Substates Supported - When Set this bit indicates that this Port supports L1 PM Substates. | Hwinit |
| 5 | Link Activation Supported - For Downstream Ports, when Set, this bit indicates that this Port supports Link Activation. See $\S$ Section 5.5.6 for details. <br> This bit is of type RsvdP for Upstream Ports. | Hwinit/RsvdP |
| $15: 8$ | Port Common_Mode_Restore_Time - Time (in $\mu \mathrm{s}$ ) required for this Port to re-establish common mode as described in $\S$ Table 5-11. <br> Required for all Ports for which either the PCI-PM L1.2 Supported bit is Set, ASPM L1.2 Supported bit is Set, or both are Set, otherwise this field is of type RsvdP. | Hwinit/RsvdP (See description) |
| 17:16 | Port T_POWER_ON Scale - Specifies the scale used for the Port T_POWER_ON Value field in the L1 PM Substates Capabilities Register. <br> Range of Values | Hwinit/RsvdP |
|  | 00b | $2 \mu \mathrm{~s}$ |
|  | 01b | $10 \mu \mathrm{~s}$ |
|  | 10b | $100 \mu \mathrm{~s}$ |
|  | 11b | Reserved |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | Required for all Ports for which either the PCI-PM L1.2 Supported bit is Set, ASPM L1.2 Supported bit is Set, or both are Set, otherwise this field is of type RsvdP. <br> Default value is 00 b |  |
| 23:19 | Port T_POWER_ON Value - Along with the Port T_POWER_ON Scale field in the L1 PM Substates Capabilities Register sets the time (in $\mu \mathrm{s}$ ) that this Port requires the port on the opposite side of Link to wait in L1.2.Exit after sampling CLKREQ\# asserted before actively driving the interface. <br> The value of Port T_POWER_ON is calculated by multiplying the value in this field by the scale value in the Port T_POWER_ON Scale field in the L1 PM Substates Capabilities Register. <br> Default value is 00101 b <br> Required for all Ports for which either the PCI-PM L1.2 Supported bit is Set, ASPM L1.2 Supported bit is Set, or both are Set, otherwise this field is of type RsvdP. | HwInit/RsvdP |

# 7.8.3.3 L1 PM Substates Control 1 Register (Offset 08h) 

![img-144.jpeg](img-144.jpeg)

Figure 7-149 L1 PM Substates Control 1 Register

Table 7-132 L1 PM Substates Control 1 Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 0 | PCI-PM L1.2 Enable - When Set this bit enables PCI-PM L1.2. | RW |
|  | Required for both Upstream and Downstream Ports. For Ports for which the PCI-PM L1.2 Supported bit is <br> Clear this bit is permitted to be hardwired to 0. |  |
|  | For compatibility with possible future extensions, software must not enable L1 PM Substates unless <br> the L1 PM Substates Supported bit in the L1 PM Substates Capabilities Register is Set. <br> Default value is Ob. | RW |
| 1 | PCI-PM L1.1 Enable - When Set this bit enables PCI-PM L1.1. |  |
|  | Required for both Upstream and Downstream Ports. <br> For compatibility with possible future extensions, software must not enable L1 PM Substates unless <br> the L1 PM Substates Supported bit in the L1 PM Substates Capabilities Register is Set. <br> Default value is Ob. |  |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 2 | ASPM L1.2 Enable - When Set this bit enables ASPM L1.2. <br> Required for both Upstream and Downstream Ports. <br> For Ports for which the ASPM L1.2 Supported bit is Clear this bit is permitted to be hardwired to 0 . <br> For compatibility with possible future extensions, software must not enable L1 PM Substates unless the L1 PM Substates Supported bit in the L1 PM Substates Capabilities Register is Set. <br> Default value is Ob. | RW |
| 3 | ASPM L1.1 Enable - When Set this bit enables ASPM L1.1. <br> Required for both Upstream and Downstream Ports. <br> For Ports for which the ASPM L1.1 Supported bit is Clear this bit is permitted to be hardwired to 0 . <br> For compatibility with possible future extensions, software must not enable L1 PM Substates unless the L1 PM Substates Supported bit in the L1 PM Substates Capabilities Register is Set. <br> Default value is Ob. | RW |
| 4 | Link Activation Interrupt Enable - When set this bit enables the generation of an interrupt to indicate the completion of the Link Activation process. See § Section 5.5.6 for details. <br> Required for Downstream Ports when the Link Activation Supported bit is Set, otherwise it is permitted to be hardwired to Ob. <br> Must be RsvdP for Upstream Ports. <br> Default value is Ob. | RW/RsvdP |
| 5 | Link Activation Control - When this bit is Set, the Port must initiate the Link Activation process. See § Section 5.5.6 for details. <br> Required for Downstream Ports when the Link Activation Supported bit is Set, otherwise it is permitted to be hardwired to Ob. <br> Must be RsvdP for Upstream Ports. <br> Default value is Ob. | RW/RsvdP |
| 15:8 | Common_Mode_Restore_Time - Sets value of TCOMMONMODE (in $\mu \mathrm{s}$ ), which must be used by the Downstream Port for timing the re-establishment of common mode, as described in § Table 5-11. <br> This field must only be modified when the ASPM L1.2 Enable and PCI-PM L1.2 Enable bits are both Clear. The Port behavior is undefined if this field is modified when either the ASPM L1.2 Enable and/or PCI-PM L1.2 Enable bit(s) are Set. <br> Required for Downstream Ports for which either the PCI-PM L1.2 Supported bit is Set, ASPM L1.2 Supported bit is Set, or both are Set, otherwise this field is of type RsvdP. <br> This field is of type RsvdP for Upstream Ports. <br> Default value is implementation specific. | RW/RsvdP (See <br> Description) |
| 25:16 | LTR_L1.2_THRESHOLD_Value - Along with the LTR_L1.2_THRESHOLD_Scale, this field indicates the LTR threshold used to determine if entry into L1 results in L1.1 (if enabled) or L1.2 (if enabled). <br> The default value for this field is 0000000000 b. <br> This field must only be modified when the ASPM L1.2 Enable bit is Clear. The Port behavior is undefined if this field is modified when the ASPM L1.2 Enable bit is Set. <br> Required for all Ports for which the ASPM L1.2 Supported bit is Set, otherwise this field is of type RsvdP. | RW/RsvdP (See <br> Description) |
| 31:29 | LTR_L1.2_THRESHOLD_Scale - This field provides a scale for the value contained within the LTR_L1.2_THRESHOLD_Value. Encoding is the same as the LatencyScale fields in the LTR Message (see § Section 6.18). | RW/RsvdP (See description) |

| Bit Location | Register Description | Attributes |
| :-- | :-- | :-- |
|  | The default value for this field is 000 b. |  |
| Hardware operation is undefined if software writes a Not-Permitted value to this field. |  |  |
| This field must only be modified when the ASPM L1.2 Enable bit is Clear. The Port behavior is undefined <br> if this field is modified when the ASPM L1.2 Enable bit is Set. |  |  |
| Required for all Ports for which the ASPM L1.2 Supported bit is Set, otherwise this field is of type RsvdP. |  |  |

# 7.8.3.4 L1 PM Substates Control 2 Register (Offset 0Ch) 

![img-145.jpeg](img-145.jpeg)

Figure 7-150 L1 PM Substates Control 2 Register

Table 7-133 L1 PM Substates Control 2 Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $1: 0$ | T_POWER_ON Scale - Specifies the scale used for T_POWER_ON Value. | RW/RsvdP |
|  | Range of Values: |  |
|  | 00b | $2 \mu \mathrm{~s}$ |
|  | 01b | $10 \mu \mathrm{~s}$ |
|  | 10b | $100 \mu \mathrm{~s}$ |
|  | 11b | Reserved |

Required for all Ports that support L1.2, otherwise this field is of type RsvdP.
This field must only be modified when the ASPM L1.2 Enable and PCI-PM L1.2 Enable bits are both Clear. The Port behavior is undefined if this field is modified when either the ASPM L1.2 Enable and/or PCI-PM L1.2 Enable bit(s) are Set.

Default value is 00b
RW/RsvdP

7:3 T_POWER_ON Value - Along with the T_POWER_ON Scale sets the minimum amount of time (in $\mu \mathrm{s}$ ) that the Port must wait in L1.2. Exit after sampling CLKREQ\# asserted before actively driving the interface.

T_POWER_ON is calculated by multiplying the value in this field by the value in the T_POWER_ON Scale field.

This field must only be modified when the ASPM L1.2 Enable and PCI-PM L1.2 Enable bits are both Clear. The Port behavior is undefined if this field is modified when either the ASPM L1.2 Enable and/or PCI-PM L1.2 Enable bit(s) are Set.

Default value is 00101 b
Required for all Ports that support L1.2, otherwise this field is of type RsvdP.

# 7.8.3.5 L1 PM Substates Status Register (Offset 10h) 

Hardware must implement this register if the Capability Version in the L1 PM Substates Extended Capability Header is 2 h or greater. This register is not present if the Capability Version is 1 h .
![img-146.jpeg](img-146.jpeg)

Figure 7-151 L1 PM Substates Status Register

Table 7-134 L1 PM Substates Status Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :-- |
| 0 | Link Activation Status - Indicates the status of Link Activation. See \$ Section 5.5.6 for details. | RW1C/RsvdZ |
|  | Required for Downstream Ports when the Link Activation Supported bit is Set, otherwise it is hardwired <br> to Ob. |  |
|  | Must be RsvdZ for Upstream Ports. |  |
|  | Default value is Ob. |  |

### 7.8.4 Advanced Error Reporting Extended Capability

The PCI Express Advanced Error Reporting (AER) Capability is an optional Extended Capability that may be implemented by PCI Express device Functions supporting advanced error control and reporting. The Advanced Error Reporting Extended Capability structure definition has additional interpretation for Root Ports and Root Complex Event Collectors; software must interpret the Device/Port Type field in the PCI Express Capabilities register to determine the availability of additional registers for Root Ports and Root Complex Event Collectors.

In an SR-IOV device, if AER is not implemented in a PF, it must not be implemented in its associated VFs. If AER is implemented in the PF, it is optional in its VFs.

In an SR-IOV device, the Header Log space for a PF is independent of any for its associated VFs and must be implemented with dedicated storage space. VFs that implement AER may share Header Log space among VFs associated with a single PF. Shared Header Log space must have storage for at least one header. See § Section 6.2.4.2.1 for further details.
§ Figure 7-152 and § Figure 7-153 show the PCI Express Advanced Error Reporting Extended Capability structure. In § Figure 7-153, the last 6 DW are optional. Implementations are permitted to implement between 0 and 6 additional DW of Header Log (see Header Log Size for details).

Note that if an error reporting bit field is marked as optional in the error registers, the bits must be implemented or not implemented as a group across the Status, Mask and Severity registers. In other words, a Function is required to implement the same error bit fields in corresponding Status, Mask and Severity registers. Bits corresponding to bit fields that are not implemented must be hardwired to 0 , unless otherwise specified.

![img-147.jpeg](img-147.jpeg)

Figure 7-152 Advanced Error Reporting Extended Capability - Functions that do not support Flit Mode Structure

![img-148.jpeg](img-148.jpeg)

# 7.8.4.1 Advanced Error Reporting Extended Capability Header (Offset 00h) 

§ Figure 7-154 details the allocation of register fields of an Advanced Error Reporting Extended Capability header; § Table $7-135$ provides the respective bit definitions.

Refer to § Section 7.6.3 for a description of the PCI Express Extended Capability header. The Extended Capability ID for the Advanced Error Reporting Extended Capability is 0001 h .
![img-149.jpeg](img-149.jpeg)

Figure 7-154 Advanced Error Reporting Extended Capability Header

Table 7-135 Advanced Error Reporting Extended Capability Header

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $15: 0$ | PCI Express Extended Capability ID - This field is a PCI-SIG defined ID number that indicates the nature and format of the Extended Capability. <br> The Extended Capability ID for the Advanced Error Reporting Extended Capability is 0001h. | RO |
| $19: 16$ | Capability Version - This field is a PCI-SIG defined version number that indicates the version of the Capability structure present. <br> This field must be 3 h if Flit Mode Supported is Set. This field must be 2 h or 3 h if End-End TLP Prefix Supported is Set (see § Section 7.5.3.15). Otherwise this field must be 1h, 2h, or 3h. | RO |
| $31: 20$ | Next Capability Offset - This field contains the offset to the next PCI Express Capability structure or 000h if no other items exist in the linked list of Capabilities. <br> For Extended Capabilities implemented in Configuration Space, this offset is relative to the beginning of PCI-compatible Configuration Space and thus must always be either 000 h (for terminating list of Capabilities) or greater than 0FFh. | RO |

### 7.8.4.2 Uncorrectable Error Status Register (Offset 04h)

The Uncorrectable Error Status Register indicates error detection status of individual errors on a PCI Express device Function. An individual error status bit that is Set indicates that a particular error was detected; software may clear an error status by writing a 1 b to the respective bit. Refer to $\S$ Section 6.2 for further details. Register bits not implemented by the Function are hardwired to 0b. § Figure 7-155 details the allocation of register fields of the Uncorrectable Error Status Register; § Section 7.8.4.2 provides the respective bit definitions.

For SR-IOV devices, applicable errors categorized as non-Function-specific must be logged in PFs and non-IOV Functions, but not logged in VFs. VFs must log only Function-specific errors, so for VFs the intended attribute for applicable non-Function-specific errors is VF ROZ. This is mandatory for some, but is only strongly recommended for others since earlier versions of this specification required them to be RW1CS. Certain other errors are applicable only for Root Port,

Switch Port, or Function 0 Endpoint Functions, so for VFs their intended attribute is VF ROZ, and they have the same issue with earlier versions of this specification. .
![img-150.jpeg](img-150.jpeg)

Figure 7-155 Uncorrectable Error Status Register

Table 7-136 Uncorrectable Error Status Register

| Bit Location | Register Description | Attributes | Default |
| :--: | :-- | :-- | :-- |
| 0 | Undefined Undefined-The value read from this bit is undefined. In previous versions of <br> this specification, this bit was used to indicate a Link Training Error. System software must <br> ignore the value read from this bit. System software is permitted to write any value to this <br> bit. | Undefined | Undefined |
| 4 | Data Link Protocol Error Status | RW1CS <br> VF ROZ | 0 b |
| 5 | Surprise Down Error Status (Optional - Note 1) | RW1CS <br> VF ROZ | 0 b |
| 12 | Poisoned TLP Received Status | RW1CS | 0 b |
| 13 | Flow Control Protocol Error Status (Optional - Note 1) | RW1CS <br> VF ROZ | 0 b |
| 14 | Completion Timeout Status | RW1CS | 0 b |

| Bit Location | Register Description | Attributes | Default |
| :--: | :--: | :--: | :--: |
| 15 | Completer Abort Status (Optional - Note 1) | RW1CS | 0b |
| 16 | Unexpected Completion Status | RW1CS | 0b |
| 17 | Receiver Overflow Status (Optional - Note 1) | $\begin{aligned} & \text { RW1CS } \\ & \text { VF ROZ } \end{aligned}$ | 0b |
| 18 | Malformed TLP Status | RW1CS <br> VF ROZ | 0b |
| 19 | ECRC Error Status (Optional - Note 1) | RW1CS <br> VF ROZ | 0b |
| 20 | Unsupported Request Error Status | RW1CS | 0b |
| 21 | ACS Violation Status (Optional - Note 1) | RW1CS | 0b |
| 22 | Uncorrectable Internal Error Status (Optional) | RW1CS | 0b |
| 23 | MC Blocked TLP Status (Optional - Note 1) | RW1CS | 0b |
| 24 | AtomicOp Egress Blocked Status (Optional - Note 1) | $\begin{aligned} & \text { RW1CS } \\ & \text { VF ROZ } \\ & \text { (Note 2) } \end{aligned}$ | 0b |
| 25 | TLP Prefix Blocked Error Status (Optional - Note 1) | $\begin{aligned} & \text { RW1CS } \\ & \text { VF ROZ } \\ & \text { (Note 2) } \end{aligned}$ | 0b |
| 26 | Poisoned TLP Egress Blocked Status (Optional - Note 1) | $\begin{aligned} & \text { RW1CS } \\ & \text { VF ROZ } \\ & \text { (Note 2) } \end{aligned}$ | 0b |
| 27 | DMWr Request Egress Blocked Status (Optional - Note 1) | $\begin{aligned} & \text { RW1CS } \\ & \text { VF ROZ } \\ & \text { (Note 2) } \end{aligned}$ | 0b |
| 28 | IDE Check Failed Status (Optional - Note 1) | $\begin{aligned} & \text { RW1CS } \\ & \text { VF ROZ } \\ & \text { (Note 2) } \end{aligned}$ | 0b |
| 29 | Misrouted IDE TLP Status (Optional - Note 1) | $\begin{aligned} & \text { RW1CS } \\ & \text { VF ROZ } \\ & \text { (Note 2) } \end{aligned}$ | 0b |
| 30 | PCRC Check Failed Status (Optional - Note 1) | $\begin{aligned} & \text { RW1CS } \\ & \text { VF ROZ } \\ & \text { (Note 2) } \end{aligned}$ | 0b |
| 31 | TLP Translation Egress Blocked Status (Optional - Note 1) | $\begin{aligned} & \text { RW1CS } \\ & \text { VF ROZ } \\ & \text { (Note 2) } \end{aligned}$ | 0b |

Notes:

1. Must implement if the corresponding Uncorrectable Error Mask bit is implemented. Otherwise, hardwire to 0 .
2. VF ROZ is strongly recommended for VF Functions, but for backward compatibility with previous versions of this specification, RW1CS is permitted if the VF implements the corresponding Uncorrectable Error Mask Register bit.

# 7.8.4.3 Uncorrectable Error Mask Register (Offset 08h) 

The Uncorrectable Error Mask Register controls reporting of individual errors by the device Function to the PCI Express Root Complex via a PCI Express error Message. A masked error (respective bit Set in the mask register) is not recorded or reported in the Header Log, TLP Prefix Log, or First Error Pointer, and is not reported to the PCI Express Root Complex by this Function. Refer to $\S$ Section 6.2 for further details. There is a mask bit per error bit of the Uncorrectable Error Status register. Register fields for bits not implemented by the Function are hardwired to 0b. § Figure 7-156 details the allocation of register fields of the Uncorrectable Error Mask Register; § Table 7-137 provides the respective bit definitions.

For VF fields marked as VF RsvdP, the associated PF's setting applies to the VF. For VF fields marked as VF ROZ, the error is not applicable to a VF.
![img-151.jpeg](img-151.jpeg)

Figure 7-156 Uncorrectable Error Mask Register

Table 7-137 Uncorrectable Error Mask Register

| Bit Location | Register Description | Attributes | Default |
| :--: | :--: | :--: | :--: |
| 0 | Undefined Undefined - The value read from this bit is undefined. In previous versions of this specification, this bit was used to mask a Link Training Error. System software must ignore the value read from this bit. System software must only write a value of 1 b to this bit. | Undefined | Undefined |
| 4 | Data Link Protocol Error Mask | RWS <br> VF ROZ | 0 b |
| 5 | Surprise Down Error Mask (Surprise Down Error Reporting Capable - Note 1) | RWS <br> VF ROZ | 0 b |
| 12 | Poisoned TLP Received Mask | RWS <br> VF RsvdP | 0 b |
| 13 | Flow Control Protocol Error Mask (Optional) | RWS <br> VF ROZ | 0 b |
| 14 | Completion Timeout Mask ${ }^{187}$ | RWS <br> VF RsvdP | 0 b |
| 15 | Completer Abort Mask (Optional) | RWS <br> VF RsvdP | 0 b |
| 16 | Unexpected Completion Mask | RWS <br> VF RsvdP | 0 b |
| 17 | Receiver Overflow Mask (Optional) | RWS <br> VF ROZ | 0 b |
| 18 | Malformed TLP Mask | RWS <br> VF ROZ | 0 b |
| 19 | ECRC Error Mask (ECRC Check Capable - Note 1) | RWS <br> VF ROZ | 0 b |
| 20 | Unsupported Request Error Mask | RWS <br> VF RsvdP | 0 b |
| 21 | ACS Violation Mask (ACS Extended Capability - Note 2) | RWS <br> VF RsvdP | 0 b |
| 22 | Uncorrectable Internal Error Mask (Optional) | RWS | 1 b |
| 23 | MC Blocked TLP Mask (Multicast Extended Capability - Note 2) | RWS | 0 b |
| 24 | AtomicOp Egress Blocked Mask (AtomicOp Egress Blocking - Note 3) | RWS <br> VF ROZ <br> Note 6 | 0 b |

187. For Switch Ports, required if the Switch Port issues Non-Posted Requests on its own behalf (vs. only forwarding such Requests generated by other devices). If the Switch Port does not issue such Requests, then the Completion Timeout mechanism is not applicable and this bit must be hardwired to 0 b.

| Bit Location | Register Description | Attributes | Default |
| :--: | :--: | :--: | :--: |
| 25 | TLP Prefix Blocked Error Mask (End-End TLP Prefix Supported - Note 3, OHC-E Support - Note 8) | RWS <br> VF ROZ <br> Note 6 | 0 b |
| 26 | Poisoned TLP Egress Blocked Mask (Poisoned TLP Egress Blocking Supported - Note 3) | RWS <br> VF ROZ <br> Note 6 | 1 b |
| 27 | DMWr Request Egress Blocked Mask (DMWr Egress Blocking - Note 3) | RWS <br> VF ROZ <br> Note 6 | 0 b |
| 28 | IDE Check Failed Mask (IDE Extended Capability - Note 4) | RWS <br> VF ROZ <br> Note 6 | 0 b |
| 29 | Misrouted IDE TLP Mask (IDE Extended Capability - Note 4) | RWS <br> VF ROZ <br> Note 6 | 0 b |
| 30 | PCRC Check Failed Mask (PCRC Supported - Note 5) | RWS <br> VF ROZ <br> Note 6 | 0 b |
| 31 | TLP Translation Egress Blocked Mask (Routing elements that translate between FM and NFM in either direction must implement this bit (see § Section 2.2.1.2)) | RWS <br> VF ROZ <br> Note 6 | 0 b |

Notes:

1. When Set in a non-VF Function, this AER mask bit must be implemented. Otherwise, for non-VF Functions, it is optional.
2. When a Function implements this Extended Capability (i.e., ACS/Multicast), that Function must implement this AER mask bit.
3. When Set in a non-VF Function, that Function must implement this AER mask bit.
4. When Function 0 implements the IDE Extended Capability, and if Function 0 implements AER, then Function 0 must implement this AER mask bit.
5. When PCRC Supported is Set in Function 0, and if Function 0 implements AER, then Function 0 must implement this AER mask bit.
6. VF ROZ is strongly recommended for VF Functions, but for backward compatibility with previous versions of this specification, RWS is permitted.
7. Placeholder
8. For Root Ports and Switch Ports, where the associated OHC-E Support field is $111 \mathrm{~b}, 001 \mathrm{~b}, 010 \mathrm{~b}, 011 \mathrm{~b}$ or 100 b , that Port must implement this AER mask bit.

# 7.8.4.4 Uncorrectable Error Severity Register (Offset OCh) 

The Uncorrectable Error Severity Register controls whether an individual error is reported as a Non-fatal or Fatal error. An error is reported as fatal when the corresponding error bit in the severity register is Set. If the bit is Clear, the corresponding error is considered non-fatal. Refer to § Section 6.2 for further details. Register fields for bits not

implemented by the Function are hardwired to an implementation specific value. § Figure 7-157 details the allocation of register fields of the Uncorrectable Error Severity Register; § Table 7-138 provides the respective bit definitions.

For VF fields marked as VF RsvdP, the associated PF's setting applies to the VF. For VF fields marked as VF ROZ, the error is not applicable to a VF.
![img-152.jpeg](img-152.jpeg)

Figure 7-157 Uncorrectable Error Severity Register

Table 7-138 Uncorrectable Error Severity Register

| Bit Location | Register Description | Attributes | Default |
| :--: | :-- | :--: | :-- |
| 0 | Undefined Undefined - The value read from this bit is undefined. In previous versions of <br> this specification, this bit was used to Set the severity of a Link Training Error. System <br> software must ignore the value read from this bit. System software is permitted to write <br> any value to this bit. | Undefined | Undefined |
| 4 | Data Link Protocol Error Severity | RWS | 1b |
| 5 | Surprise Down Error Severity (Optional - Note 1) | VF ROZ | 1b |
| 12 | Poisoned TLP Received Severity | RWS | 0b |
| 13 | Flow Control Protocol Error Severity (Optional - Note 1) | VF RsvdP | 1b |

| Bit Location | Register Description | Attributes | Default |
| :--: | :--: | :--: | :--: |
| 14 | Completion Timeout Error Severity ${ }^{188}$ | RWS <br> VF RsvdP | 0 b |
| 15 | Completer Abort Error Severity (Optional - Note 1) | RWS <br> VF RsvdP | 0 b |
| 16 | Unexpected Completion Error Severity | RWS <br> VF RsvdP | 0 b |
| 17 | Receiver Overflow Severity (Optional - Note 1) | RWS <br> VF ROZ | 1 b |
| 18 | Malformed TLP Severity | RWS <br> VF ROZ | 1 b |
| 19 | ECRC Error Severity (Optional - Note 1) | RWS <br> VF ROZ | 0 b |
| 20 | Unsupported Request Error Severity | RWS <br> VF RsvdP | 0 b |
| 21 | ACS Violation Severity (Optional - Note 1) | RWS <br> VF RsvdP | 0 b |
| 22 | Uncorrectable Internal Error Severity (Optional - Note 1) | RWS | 1 b |
| 23 | MC Blocked TLP Severity (Optional - Note 1) | RWS | 0 b |
| 24 | AtomicOp Egress Blocked Severity (Optional - Note 1) | RWS <br> VF ROZ <br> Note 2 | 0 b |
| 25 | TLP Prefix Blocked Error Severity (Optional - Note 1) | RWS <br> VF ROZ <br> Note 2 | 0 b |
| 26 | Poisoned TLP Egress Blocked Severity (Optional - Note 1) | RWS <br> VF ROZ <br> Note 2 | 0 b |
| 27 | DMWr Request Egress Blocked Severity (Optional - Note 1) | RWS <br> VF ROZ <br> Note 2 | 0 b |
| 28 | IDE Check Failed Severity (Optional - Note 1) | RWS <br> VF ROZ <br> Note 2 | 1 b |
| 29 | Misrouted IDE TLP Severity (Optional - Note 1) | RWS | 0 b |

[^0]
[^0]:    188. For Switch Ports, required if the Switch Port issues Non-Posted Requests on its own behalf (vs. only forwarding such Requests generated by other devices). If the Switch Port does not issue such Requests, then the Completion Timeout mechanism is not applicable and this bit must be hardwired to 0b.

| Bit Location | Register Description | Attributes | Default |
| :--: | :--: | :--: | :--: |
|  |  | VF ROZ <br> Note 2 |  |
| 30 | PCRC CHeck Failed Severity (Optional - Note 1) | RWS <br> VF ROZ <br> Note 2 | 0 b |
| 31 | TLP Translation Egress Blocked Severity (Optional - Note 1) | RWS <br> VF ROZ <br> Note 2 | 0 b |

Notes:

1. Must implement if the corresponding Uncorrectable Error Mask Register bit is implemented. Otherwise, hardwire to 0.
2. VF ROZ is strongly recommended for VF Functions, but for backward compatibility with previous versions of this specification, RWS is permitted if the VF implements the corresponding Uncorrectable Error Mask Register bit.

# 7.8.4.5 Correctable Error Status Register (Offset 10h) 

The Correctable Error Status register reports error status of individual correctable error sources on a PCI Express device Function. When an individual error status bit is Set, it indicates that a particular error occurred; software may clear an error status by writing a 1 b to the respective bit. Refer to $\S$ Section 6.2 for further details. Register bits not implemented by the Function are hardwired to 0b. § Figure 7-158 details the allocation of register fields of the Correctable Error Status register; § Table 7-139 provides the respective bit definitions.

For SR-IOV devices, errors categorized as non-Function-specific must be logged in PFs and non-IOV Functions, but not logged in VFs. VFs must log only Function-specific errors.
![img-153.jpeg](img-153.jpeg)

Figure 7-158 Correctable Error Status Register

Table 7-139 Correctable Error Status Register

| Bit Location | Register Description | Attributes | Default |
| :--: | :-- | :-- | :-- |
| 0 | Receiver Error Status | RW1CS | 0 b |
|  |  | VF ROZ |  |

| Bit Location | Register Description | Attributes | Default |
| :--: | :--: | :--: | :--: |
| 6 | Bad TLP Status | RW1CS <br> VF ROZ | 0b |
| 7 | Bad DLLP Status | RW1CS <br> VF ROZ | 0b |
| 8 | REPLAY_NUM Rollover Status | RW1CS <br> VF ROZ | 0b |
| 12 | Replay Timer Timeout Status | RW1CS <br> VF ROZ | 0b |
| 13 | Advisory Non-Fatal Error Status | RW1CS | 0b |
| 14 | Corrected Internal Error Status (Optional) | RW1CS | 0b |
| 15 | Header Log Overflow Status (Optional) <br> If the VF implements Header Log sharing (see $\S$ Section 6.2.4.2.1), this bit must be hardwired to Zero. | $\begin{gathered} \text { RW1CS / } \\ \text { 0b } \end{gathered}$ | 0b |

# 7.8.4.6 Correctable Error Mask Register (Offset 14h) 

The Correctable Error Mask Register controls reporting of individual correctable errors by this Function to the PCI Express Root Complex via a PCI Express error Message. A masked error (respective bit Set in the mask register) is not reported to the PCI Express Root Complex by this Function. Refer to $\S$ Section 6.2 for further details. There is a mask bit per error bit in the Correctable Error Status register. Register fields for bits not implemented by the Function are hardwired to 0b. $\S$ Figure 7-159 details the allocation of register fields of the Correctable Error Mask Register; $\S$ Table $7-140$ provides the respective bit definitions.

For VF fields marked as VF RsvdP, the associated PF's setting applies to the VF.
![img-154.jpeg](img-154.jpeg)

Figure 7-159 Correctable Error Mask Register

[^0]
[^0]:    189. For historical reasons, implementation of this bit is optional. If not implemented, this bit must be RsvdZ, and bit 0 of the Correctable Error Mask Register must also not be implemented. Note that some checking for Receiver Errors is required in all cases (see $\S$ Section 4.2.1.1.3, $\S$ Section 4.2.5.8, and $\S$ Section 4.2.7).

Table 7-140 Correctable Error Mask Register

| Bit Location | Register Description | Attributes | Default |
| :--: | :--: | :--: | :--: |
| 0 | Receiver Error Mask ${ }^{190}$ | RWS <br> VF RsvdP | 0b |
| 6 | Bad TLP Mask | RWS <br> VF RsvdP | 0b |
| 7 | Bad DLLP Mask | RWS <br> VF RsvdP | 0b |
| 8 | REPLAY_NUM Rollover Mask | RWS <br> VF RsvdP | 0b |
| 12 | Replay Timer Timeout Mask | RWS <br> VF RsvdP | 0b |
| 13 | Advisory Non-Fatal Error Mask - This bit is Set by default to enable compatibility with software that does not comprehend Role-Based Error Reporting. | RWS <br> VF RsvdP | 1b |
| 14 | Corrected Internal Error Mask (Optional) | RWS | 1b |
| 15 | Header Log Overflow Mask (Optional) <br> If the VF implements Header Log sharing (see $\S$ Section 6.2.4.2.1), this bit is RsvdP. | RWS / <br> RsvdP | 1b |

# 7.8.4.7 Advanced Error Capabilities and Control Register (Offset 18h) 

§ Figure 7-160 details allocation of register fields in the Advanced Error Capabilities and Control register; § Table 7-141 provides the respective bit definitions. Handling of multiple errors is discussed in $\S$ Section 6.2.4.2.

For VF fields marked as VF RsvdP, the associated PF's setting applies to the VF. For VF fields marked as VF ROZ, the error is not applicable to a VF.
190. For historical reasons, implementation of this bit is optional. If not implemented, this bit must be RsvdP, and bit 0 of the Correctable Error Status register must also not be implemented. Note that some checking for Receiver Errors is required in all cases (see $\S$ Section 4.2.1.1.3, $\S$ Section 4.2.5.8, and $\S$ Section 4.2.7).

![img-155.jpeg](img-155.jpeg)

Figure 7-160 Advanced Error Capabilities and Control Register

Table 7-141 Advanced Error Capabilities and Control Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $4: 0$ | First Error Pointer - The First Error Pointer is a field that identifies the bit position of the first error reported in the Uncorrectable Error Status register. Refer to $\S$ Section 6.2 for further details. | ROS |
| 5 | ECRC Generation Capable - If Set, this bit indicates that the Function is capable of generating ECRC (see § Section 2.7). | RO |
| 6 | ECRC Generation Enable - When Set, ECRC generation is enabled (see § Section 2.7). <br> Functions that do not implement the associated mechanism are permitted to hardwire this bit to 0 b. Default value of this bit is 0 b . | RWS <br> VF RsvdP |
| 7 | ECRC Check Capable - If Set, this bit indicates that the Function is capable of checking ECRC (see § Section 2.7). | RO |
| 8 | ECRC Check Enable - When Set, ECRC checking is enabled (see § Section 2.7). Functions that do not implement the associated mechanism are permitted to hardwire this bit to 0 b. Default value of this bit is 0 b . | RWS <br> VF RsvdP |
| 9 | Multiple Header Recording Capable - If Set, this bit indicates that the Function is capable of recording more than one error header. Refer to $\S$ Section 6.2 for further details. <br> If the VF implements Header Log sharing (see § Section 6.2.4.2.1), this bit must be hardwired to Zero. | RO / 0b |
| 10 | Multiple Header Recording Enable - When Set, this bit enables the Function to record more than one error header. <br> Functions that do not implement the associated mechanism are permitted to hardwire this bit to 0 b . If the VF implements Header Log sharing (see § Section 6.2.4.2.1), this bit is RsvdP. Default value of this bit is 0 b . | RWS / RsvdP |
| 11 | TLP Prefix Log Present - If End-End TLP Prefix Supported is Clear, this bit is RsvdP. <br> If Flit Mode Supported is Set, First Error Pointer is valid, and Logged TLP was Flit Mode is Set, this bit must be 0 . | ROS / RsvdP |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | If this bit is Set and First Error Pointer is valid, the TLP Prefix Log Register (offset 38h to 44h, also known as Header Log Register DW5-8) contains valid Non-Flit Mode End-End TLP Prefix information. <br> If this bit is Clear or First Error Pointer not valid, the TLP Prefix Log Register does not contain End-End TLP Prefix information (the overlapping field, Header Log Register DW5-8, may contain Flit Mode TLP Header information as specified elsewhere in this section). <br> Default value of this bit is 0 . <br> If the VF implements Header Log Sharing (see § Section 6.2.4.2.1), this bit must be Zero when the Header Log contains all 1s due to an overflow condition. |  |
| 12 | Completion Timeout Prefix/Header Log Capable - If Set, this bit indicates that the Function records the prefix/header of Request TLPs that experience a Completion Timeout error. | Hwinit |
| $17: 13$ | Header Log Size - This field indicates the number of DW of Header Log that are implemented. <br> If Flit Mode Supported is Set, see text for requirements. <br> If Flit Mode Supported is Clear and End-End TLP Prefix Supported is Set, this value must either be 0 or must be greater than or equal to 8 . <br> If this field is 0 and Flit Mode Supported is Clear, the size of the header log depends on End-End TLP Prefix Supported. If End-End TLP Prefix Supported is Clear, the Header Log is 4 DW, otherwise the Header Log is 8 DW. | Hwinit/RsvdP |
| 18 | Logged TLP was Flit Mode -- If Flit Mode Supported is Set, First Error Pointer is valid, and this bit is Set, the logged TLP was captured in Flit Mode otherwise the TLP was captured in Non-Flit Mode. | ROS |
| $23: 19$ | Logged TLP Size -- If Flit Mode Supported is Set and First Error Pointer is valid, this field contains the number of DW that were logged in the Header Log Register and, if appropriate, the TLP Prefix Log Register. <br> If Flit Mode Supported is Set, First Error Pointer is valid, the VF implements Header Log Sharing (see $\S$ Section 6.2.4.2.1), and a Header Log overflow condition occurred, this field must be 0 (in addition to the Header Log containing all 1s). | ROS |

# 7.8.4.8 Header Log Register (Offset 1Ch) 

The Header Log Register contains the header for the TLP corresponding to a detected error; refer to $\S$ Section 6.2 for further details. $\S$ Section 6.2 also describes the conditions where the packet header is recorded. This register is 16 bytes and adheres to the format of the headers defined throughout this specification.

The header is captured such that, when read using DW accesses, the fields of the header are laid out in the same way the headers are presented in this document. Therefore, byte 0 of the header is located in byte 3 of the Header Log Register, byte 1 of the header is in byte 2 of the Header Log Register and so forth. For 12-byte headers, only bytes 0 through 11 of the Header Log Register are used and values in bytes 12 through 15 are undefined.

See § Section 6.2.4.2.1 for further requirements when VFs share Header Log space.
In certain cases where a Malformed TLP is reported, the Header Log Register may contain TLP Prefix information. See § Section 6.2.4.4 for details.
§ Figure 7-161 details allocation of register fields in the Header Log Register; § Table 7-142 provides the respective bit definitions.

When Flit Mode Supported is Set and the link is operating in Flit Mode, the Header Log Register extends into additional DWs as indicated by the Header Log Size field. Software must parse the Type and OHC fields to determine the size and layout of a TLP recorded in the Header Log Register. Hardware is not required to support logging of TLP Headers larger

than the largest size supported by the Port. Hardware is not required to support logging of OHC types not supported by the Port. TLP Trailers are not logged in the Header Log Register. The required minimum size of the Header Log Register is determined by the largest Header Base Size implemented by the Port (up to the maximum defined of 7 DW - See § Table 2-5), plus the largest number of OHC implemented by the Port (up to the maximum defined of 7 DW ). Hardware must hardwire to zero the DW of the Header Log Register beyond those required to log the largest supported TLP Header and the overall length of the Advanced Error Reporting Extended Capability is reduced accordingly. As in Non-Flit Mode, Local TLP Prefixes are not logged.

When the link is operating in Non-Flit Mode, End-End TLP Prefixes are logged in the TLP Prefix Log Register.

| 31 | 2423 | 1615 | 87 | 0 |
| :--: | :--: | :--: | :--: | :--: |
| Header byte 0 |  | Header Log Register (1st DW) |  |  |
| Header Byte 4 | Header Byte 5 | Header Byte 1 | Header Byte 2 | Header Byte 3 |
| Header Byte 8 | Header 4 | Header Log Register (2nd DW) |  |  |
| Header Byte 12 | Header Byte 5 | Header Byte 6 | Header Byte 7 |  |
| Header Byte 14 | Header Log Register (3rd DW) |  |  |  |
| Header Byte 9 | Header Byte 9 | Header Byte 10 | Header Byte 1 |  |
| Header 12 | Header 12 | Header Byte 14 | Header Byte 15 |  |

OM14549A
Figure 7-161 Header Log Register

Table 7-142 Header Log Register

| Bit Location | Register Description | Attributes | Default |
| :--: | :-- | :--: | :--: |
| 127:0 | Header of TLP associated with error | ROS | 0 |

# 7.8.4.9 Root Error Command Register (Offset 2Ch) 

The Root Error Command Register allows further control of Root Complex response to Correctable, Non-Fatal, and Fatal error Messages than the basic Root Complex capability to generate system errors in response to error Messages (either received or internally generated). Bit fields (see § Figure 7-162) enable or disable generation of interrupts (claimed by the Root Port or Root Complex Event Collector) in addition to system error Messages according to the definitions in § Table 7-143.

For both Root Ports and Root Complex Event Collectors, in order for a received error Message or an internally generated error Message to generate an interrupt enabled by this register, the error Message must be enabled for "transmission" by the Root Port or Root Complex Event Collector (see § Section 6.2.4.1 and § Section 6.2.8.1).

For Functions other than Root Ports and Root Complex Event Collectors: when End-End TLP Prefix Supported is Set or Flit Mode Supported is Set, this register is RsvdP, otherwise Clear, this register is not required to be implemented.

![img-156.jpeg](img-156.jpeg)

Figure 7-162 Root Error Command Register

Table 7-143 Root Error Command Register

| Bit Location | Register Description | Attributes | Default |
| :--: | :--: | :--: | :--: |
| 0 | Correctable Error Reporting Enable - When Set, this bit enables the generation of an interrupt when a correctable error is reported by any of the Functions in the Hierarchy Domain associated with this Root Port. <br> Root Complex Event Collectors provide support for the above described functionality for RCiEPs. <br> Refer to § Section 6.2 for further details. | RW | $0 b$ |
| 1 | Non-Fatal Error Reporting Enable - When Set, this bit enables the generation of an interrupt when a Non-fatal error is reported by any of the Functions in the Hierarchy Domain associated with this Root Port. <br> Root Complex Event Collectors provide support for the above described functionality for RCiEPs. <br> Refer to § Section 6.2 for further details. | RW | $0 b$ |
| 2 | Fatal Error Reporting Enable - When Set, this bit enables the generation of an interrupt when a Fatal error is reported by any of the Functions in the Hierarchy Domain associated with this Root Port. <br> Root Complex Event Collectors provide support for the above described functionality for RCiEPs. <br> Refer to § Section 6.2 for further details. | RW | $0 b$ |

System error generation in response to PCI Express error Messages may be turned off by system software using the PCI Express Capability structure described in § Section 7.5.3 when advanced error reporting via interrupts is enabled. Refer to § Section 6.2 for further details.

# 7.8.4.10 Root Error Status Register (Offset 30h) 

The Root Error Status Register reports status of error Messages (ERR_COR, ERR_NONFATAL, and ERR_FATAL) received by the Root Port, and of errors detected by the Root Port itself (which are treated conceptually as if the Root Port had sent an error Message to itself). In order to update this register, error Messages received by the Root Port and/or internally generated error Messages must be enabled for "transmission" by the primary interface of the Root Port. ERR_NONFATAL and ERR_FATAL Messages are grouped together as uncorrectable. Each correctable and uncorrectable (Non-fatal and Fatal) error source has a first error bit and a next error bit associated with it respectively. When an error is received by a Root Complex, the respective first error bit is Set and the Requester ID is logged in the Error Source Identification Register. A Set individual error status bit indicates that a particular error category occurred; software may clear an error status by writing a 1 b to the respective bit. If software does not clear the first reported error before another error Message is received of the same category (correctable or uncorrectable), the corresponding next error status bit will be

set but the Requester ID of the subsequent error Message is discarded. The next error status bits may be cleared by software by writing a 1 b to the respective bit as well. Refer to $\S$ Section 6.2 for further details. This register is updated regardless of the settings of the Root Control Register and the Root Error Command Register. § Figure 7-163 details allocation of register fields in the Root Error Status Register; § Table 7-144 provides the respective bit definitions. Root Complex Event Collectors provide support for the above-described functionality for RCIEPs (and for the Root Complex Event Collector itself). In order to update this register, error Messages received by the Root Complex Event Collector from its associated RCIEPs and/or internally generated error Messages must be enabled for "transmission" by the Root Complex Event Collector.

For Functions other than Root Ports and Root Complex Event Collectors: when End-End TLP Prefix Supported is Set or Flit Mode Supported is Set, this register is RsvdZ, otherwise this register is not required to be implemented.
![img-157.jpeg](img-157.jpeg)

Figure 7-163 Root Error Status Register

Table 7-144 Root Error Status Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 0 | ERR_COR Received - Set when a Correctable error Message is received and this bit is not already Set. <br> Default value of this bit is 0 b. | RW1CS |
| 1 | Multiple ERR_COR Received - Set when a Correctable error Message is received and ERR_COR Received is already Set. <br> Default value of this bit is 0 b. | RW1CS |
| 2 | ERR_FATAL/NONFATAL Received - Set when either a Fatal or a Non-fatal error Message is received and this bit is not already Set. <br> Default value of this bit is 0 b. | RW1CS |
| 3 | Multiple ERR_FATAL/NONFATAL Received - Set when either a Fatal or a Non-fatal error is received and ERR_FATAL/NONFATAL Received is already Set. <br> Default value of this bit is 0 b. | RW1CS |
| 4 | First Uncorrectable Fatal - Set when the first Uncorrectable error Message received is for a Fatal error. <br> Default value of this field is 0 b. | RW1CS |
| 5 | Non-Fatal Error Messages Received - Set when one or more Non-Fatal Uncorrectable error Messages have been received. <br> Default value of this bit is 0 b. | RW1CS |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 6 | Fatal Error Messages Received - Set when one or more Fatal Uncorrectable error Messages have been received. <br> Default value of this bit is 0 b. | RW1CS |
| $8: 7$ | ERR_COR Subclass - If the Function is ERR_COR Subclass capable and the ERR_COR Received bit is not already Set, this field is loaded with the value of the ERR_COR Subclass field in the received ERR_COR Message. See § Section 2.2.8.3 . The value in this field is only valid when the ERR_COR Received bit is Set. If the Function is not ERR_COR Subclass capable, this field is Reserved. <br> If the Function is ERR_COR Subclass capable and a SIG_SFW ERR_COR Message is received, system firmware should be signaled using a system-specific mechanism. <br> Default value of this field is 00 b. | ROS/RsvdZ |
| $31: 27$ | Advanced Error Interrupt Message Number - When MSI/MSI-X is implemented, this register indicates which MSI/MSI-X vector is used for the interrupt message generated in association with any of the status bits of this Capability. <br> For MSI, the value in this register indicates the offset between the base Message Data and the interrupt message that is generated. Hardware is required to update this field so that it is correct if the number of MSI Messages assigned to the Function changes when software writes to the Multiple Message Enable field in the Message Control Register for MSI. <br> For MSI-X, the value in this register indicates which MSI-X Table entry is used to generate the interrupt message. The entry must be one of the first 32 entries even if the Function implements more than 32 entries. For a given MSI-X implementation, the entry must remain constant. <br> If both MSI and MSI-X are implemented, they are permitted to use different vectors, though software is permitted to enable only one mechanism at a time. If MSI-X is enabled, the value in this register must indicate the vector for MSI-X. If MSI is enabled or neither is enabled, the value in this register must indicate the vector for MSI. If software enables both MSI and MSI-X at the same time, the value in this register is undefined. | RO |

# 7.8.4.11 Error Source Identification Register (Offset 34h) 

The Error Source Identification Register identifies the source (Requester ID) of first correctable and uncorrectable (Non-fatal/Fatal) errors reported in the Root Error Status Register. Refer to § Section 6.2 for further details. This register is updated regardless of the settings of the Root Control Register and the Root Error Command Register. § Figure 7-164 details allocation of register fields in the Error Source Identification Register; § Table 7-145 provides the respective bit definitions.

For Functions other than Root Ports and Root Complex Event Collectors: when End-End TLP Prefix Supported is Set or Flit Mode Supported is Set, this register is RsvdP, otherwise this register is not required to be implemented.
![img-158.jpeg](img-158.jpeg)

Figure 7-164 Error Source Identification Register

Table 7-145 Error Source Identification Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $15: 0$ | ERR_COR Source Identification - Loaded with the Requester ID indicated in the received ERR_COR <br> Message when the ERR_COR Received bit is not already set. <br> Default value of this field is 0000 h. | ROS |
| $31: 16$ | ERR_FATAL/NONFATAL Source Identification - Loaded with the Requester ID indicated in the received <br> ERR_FATAL or ERR_NONFATAL Message when the ERR_FATAL/NONFATAL Received bit is not already set. <br> Default value of this field is 0000 h. | ROS |

# 7.8.4.12 TLP Prefix Log Register (Offset 38h) 

The TLP Prefix Log Register captures the End-End TLP Prefix(s) for the TLP corresponding to the detected error; refer to § Section 6.2 for further details. The TLP Prefix Log Register is only meaningful when First Error Pointer is valid and the TLP Prefix Log Present bit is Set (see § Section 7.8.4.7).

The TLP Prefixes are captured such that, when read using DW accesses, the fields of the TLP Prefix are laid out in the same way the fields of the TLP Prefix are described. Therefore, byte 0 of a TLP Prefix is located in byte 3 of the associated TLP Prefix Log Register; byte 1 of a TLP Prefix is located in byte 2; and so forth.

The First TLP Prefix Log Register contains the first End-End TLP Prefix from the TLP (see § Section 6.2.4.4). The Second TLP Prefix Log Register contains the second End-End TLP Prefix and so forth. If the TLP contains fewer than four End-End TLP Prefixes, the remaining TLP Prefix Log Registers contain zero. A TLP that contains more End-End TLP Prefixes than are indicated by the Function's Max End-End TLP Prefixes field must be handled as an error (see § Section 2.2.10.4 for specifics). To allow software to detect this condition, the supported number of End-End TLP Prefixes are logged in this register, the first overflow End-End TLP Prefix is logged in the first DW of the Header Log register and the remaining DWs of the Header Log register are undefined (see § Section 6.2.4.4).

The TLP Prefix Log Registers beyond the number supported by the Function are hardwired to zero. For example, if a Functions, Max End-End TLP Prefixes field contains 10b (indicating 2 DW of buffering) then the third and fourth TLP Prefix Log Registers are hardwired to zero. If the End-End TLP Prefix Supported bit (§ Section 7.5.3.15) is Clear, the TLP Prefix Log Register is not required to be implemented.

For VFs that share Header Log space, this register's contents are undefined when the Header Log contains all 1s due to an overflow condition. See § Section 6.2.4.2.1 for further requirements when VFs share Header Log space.

When Flit Mode Supported is Set and the link is operating in Flit Mode, this register is not present and the Header Log Register extends into this space (see additional DWs as indicated by the Header Log Size field).

When the link is operating in Non-Flit Mode, End-End TLP Prefixes are logged in the TLP Prefix Log Register.

![img-159.jpeg](img-159.jpeg)

Figure 7-165 TLP Prefix Log Register

Table 7-146 TLP Prefix Log Register

| Bit Location | Register Description | Attributes | Default |
| :--: | :--: | :--: | :--: |
| 127:0 | TLP Prefix Log | ROS | 0 |

# 7.8.5 Enhanced Allocation Capability Structure (EA) 

Each function that supports the Enhanced Allocation mechanism must implement the Enhanced Allocation capability structure.

Each field is defined in the following sections. Reserved registers must return 0 when read and write operations must have no effect. Read-only registers return valid data when read, and write operations must have no effect.

### 7.8.5.1 Enhanced Allocation Capability First DW (Offset 00h)

The first DW of the Enhanced Allocation capability is illustrated in § Figure 7-166, and is documented in § Table 7-147.
![img-160.jpeg](img-160.jpeg)

Figure 7-166 First DW of Enhanced Allocation Capability

Table 7-147 First DW of Enhanced Allocation Capability

| Bit Location | Register Description | Attributes |
| :--: | :-- | :-- |
| $7: 0$ | Capability ID - Must be set to 14 h to indicate Enhanced Allocation capability. This field is read only. | HwInit |
| $15: 8$ | Next Capability Pointer - Pointer to the next item in the capabilities list. Must be NULL for the final item <br> in the list. This field is read only. | HwInit |

| Bit Location | Register Description | Attributes |
| :--: | :-- | :-- |
| 21:16 | Num Entries - Number of entries following the first DW of the capability. Value of 000000 b is permitted <br> and means there are no entries. <br> This field is read only. | HwInit |

# 7.8.5.2 Enhanced Allocation Capability Second DW (Offset 04h) [Type 1 Functions Only] 

For Type 1 Functions only, there is a second DW in the capability, preceding the first entry. This second DW must be included in the Enhanced Allocation Capability whenever this capability is implemented in a Type 1 Function. The second DW of the Enhanced Allocation capability is illustrated in § Figure 7-167, and is documented in § Table 7-148.
![img-161.jpeg](img-161.jpeg)

Figure 7-167 Second DW of Enhanced Allocation Capability

Table 7-148 Second DW of Enhanced Allocation Capability

| Bit Location | Register Description | Attributes |
| :--: | :-- | :-- |
| $7: 0$ | Fixed Secondary Bus Number - If at least one Function that uses EA is located behind this Function, then <br> this field must be set to indicate the Bus Number for the secondary interface of this Function. If no <br> Function that uses EA is located behind this Function, then this field must be set to 00 h. | HwInit |
| $15: 8$ | Fixed Subordinate Bus Number - If at least one Function that uses EA is located behind this Function, <br> then this field must be set to indicate the highest Bus Number below this Function. If no Function that <br> uses-EA is located behind this Function, then this field must be set to 00 h. | HwInit |

### 7.8.5.3 Enhanced Allocation Per-Entry Format (Offset 04h or 08h)

An Enhanced Allocation Entry consists of a First DW followed by between 2 and 4 DW of Base / MaxOffset information.

- For Type 0 Functions, Enhanced Allocation Entries start at offset 04h of this capability.
- For Type 1 Functions, Enhanced Allocation Entries start at offset 08h of this capability.
- Subsequent Enhanced Allocation Entries immediately follow each other.

The first DW of each entry in the Enhanced Allocation capability is illustrated in § Figure 7-168, and is defined in § Table $7-149$.

![img-162.jpeg](img-162.jpeg)

Figure 7-168 First DW of Each Entry for Enhanced Allocation Capability

Table 7-149 First DW of Each Entry for Enhanced Allocation Capability

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 2:0 | Entry Size (ES) - Number of DW following the initial DW in this entry. <br> When processing this capability, software is required to use the value in this field to determine the size of this entry, and if this entry is not the final entry, the start of the following entry in the capability. This requirement must be strictly followed by software, even if the indicated entry size does not correspond to any entry defined in this specification. <br> Value of 000 b indicates only the first DW (containing the Entry Size field) is included in the entry. | HwInit |
| 7:4 | BAR Equivalent Indicator (BEI) - This field indicates the equivalent BAR for this entry. <br> Specific rules for use of this field are given in the text following this table. | HwInit |
|  | BEI <br> Value | Description |
|  | 0 | Entry is equivalent to BAR at location 10h |
|  | 1 | Entry is equivalent to BAR at location 14h |
|  | 2 | Entry is equivalent to BAR at location 18h |
|  | 3 | Entry is equivalent to BAR at location 1Ch |
|  | 4 | Entry is equivalent to BAR at location 20h |
|  | 5 | Entry is equivalent to BAR at location 24h |
|  | 6 | Permitted to be used by a Function with a Type 1 Configuration Space Header only, optionally used to indicate a resource that is located behind the Function |
|  | 7 | Equivalent Not Indicated |
|  | 8 | Expansion ROM Base Address |
|  | $9-14$ | Entry relates to VF BARs 0-5 respectively |
|  | 15 | Reserved - Software must treat values in this range as "Equivalent Not Indicated" |
| 15:8 | Primary Properties - Indicates the entry properties as defined in § Table 7-151. | HwInit |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 23:16 | Secondary Properties - Optionally used to indicate a different but compatible entry property, using properties as defined in $\S$ Table 7-151. | HwInit |
| 30 | Writable (W) - The value 1b indicates that the Base and MaxOffset fields for this entry are RW and that the Field Size bits for this entry are either RW or HwInit. The value 0b indicates those fields are HwInit. See $\S$ Table 7-151 for additional requirements on the value of this field. | HwInit |
| 31 | Enable (E) - 1b indicates this entry is enabled, 0b indicates this entry is disabled. <br> If system software disables this entry, the resource indicated must still be associated with this function, and it is not permitted to reallocate this resource to any other entity. <br> This field is permitted to be implemented as HwInit for functions that require the allocation of the associated resource, or as RW for functions that can allow system software to disable this resource, for example if BAR mechanisms are to be used instead of this resource. | RW/HwInit |

Rules for use of BEI field:

- A Type 0 Function is permitted to use EA to allocate resources for itself, and such resources must indicate a BEI value of $0-5,7$ or 8 .
- A Physical Function (Type 0 Function that supports SR-IOV) is permitted to use EA to allocate resources for its associated Virtual Functions, and such resources must indicate a BEI value of 9-14.
- A Type 1 Function (bridge) is permitted to use EA to allocate resources for itself, and such resources must indicate a BEI value of 0,1 or 7 .
- A Type 1 Function is permitted but not required to indicate resources mapped behind that Function, but if such resources are indicated by the Type 1 Function, the entry must indicate a BEI value of 6 .
- For a 64-bit Base Address Register, the BEI indicates the equivalent BAR location for lower DWORD.
- For Memory BARs where the Primary or Secondary Properties is 00 h or 01 h , it is permitted to assign the same BEI in the range of 0 to 5 once for a range where Base + MaxOffset is below 4 GB , and again for a range where Base + MaxOffset is greater than 4 GB; It is not otherwise permitted to assign the same BEI in the range 0 to 5 for more than one entry.
- For Virtual Function BARs where the Primary or Secondary Properties is 03 h or 04 h it is permitted to assign the same BEI in the range of 9 to 14 once for a range where Base + MaxOffset is below 4 GB , and again for a range where Base + MaxOffset is greater than 4 GB; It is not otherwise permitted to assign the same BEI in the range 9 to 14 for more than one VF entry.
- For all cases where two entries with the same BEI are permitted, Software must enable use of only one of the two ranges at a time for a given Function.
- It is permitted for an arbitrary number of entries to assign a BEI of 6 or 7 .
- At most one entry is permitted with a BEI of 8 ; if such an entry is present, behavior of the Expansion ROM Base Address Register is changed (see § Section 7.5.1.2.4).
- For Type 1 Functions, BEI values 2 through 5 are reserved.
§ Figure 7-169 illustrates the format of a complete Enhanced Allocation entry for a Type 0 Function. For the Base and MaxOffset fields, bit 1 indicates if the field is a 32b (0) or 64b (1) field.

![img-163.jpeg](img-163.jpeg)

Figure 7-169 Format of Entry for Enhanced Allocation Capability

The value in the Base field ([63:2] or [31:2]) indicates the DW address of the start of the resource range. Bits [1:0] of the address are not included in the Base field, and must always be interpreted as 00b.

The value in the Base field plus the value in the MaxOffset field ([63:2] or [31:2]) indicates the address of the last included DW of the resource range. Bits [1:0] of the MaxOffset are not included in the MaxOffset field, and must always be interpreted as 11b.

For the Base and MaxOffset fields, when bits [63:32] are not provided then those bits must be interpreted as all 0's.
Although it is permitted for a Type 0 Function to indicate the use of a range that is not naturally aligned and/or not a power of two in size, some system software may fail if this is done. Particularly for ranges that are mapped to legacy BARs by indicating a BEI in the range of 0 to 5 , it is strongly recommended that the Base and MaxOffset fields for a Type 0 Function indicate a naturally aligned region.

The Primary Properties[7:0] field must be set by hardware to identify the type of resource indicated by the entry. It is strongly recommended that hardware set the Secondary Properties[7:0] to indicate an alternate resource type which can be used by software when the Primary Properties[7:0] field value is not comprehended by that software, for example when older system software is used with new hardware that implements resources using a value for Primary Properties that was reserved at the time the older system software was implemented. When this is done, hardware must ensure that software operating using the resource according to the value indicated in the Secondary Properties field will operate in a functionally correct way, although it is not required that this operation will result in optimal system performance or behavior.

The Primary Properties[7:0] and Secondary Properties[7:0] fields are defined in § Table 7-151. This table also defines whether or not the entry is permitted to be writeable. The Writeable bit in any entry must be 0 b unless both the Primary and Secondary properties of that entry allow otherwise.

Table 7-151 Enhanced Allocation Entry Field Value Definitions for both the Primary Properties and Secondary Properties Fields

| Value (h) | Resource Definition | Writeable <br> permitted |
| :--: | :-- | :--: |
| $00-01$ | Memory Space | No |
| 02 | I/O Space. | No |
| $03-04$ | For use only by Physical Functions to indicate resources for Virtual Function use, Memory Space. | No |

| Value (h) | Resource Definition |  | Writeable <br> permitted |
| :--: | :-- | :--: | :--: |
| $05-06$ | For use only by Type 1 Functions to indicate Memory, for Allocation Behind that Bridge. | No |  |
| 07 | For use only by Type 1 Functions to indicate I/O Space for Allocation Behind that Bridge. | No |  |
| $08-F C$ | Reserved for future use; System firmware/software must not write to this entry, and must not attempt to <br> interpret this entry or to use this resource. <br> When software reads a Primary Properties value that is within this range, is it strongly recommended that <br> software treat this resource according to the value in the Secondary Properties field, if that field contains a <br> non-reserved value. | Yes |  |
| FD | Memory Space Resource Unavailable For Use - System firmware/software must not write to this entry, and <br> must not attempt to use the resource described by this entry for any purpose. | No |  |
| FE | I/O Space Resource Unavailable For Use - System firmware/software must not write to this entry, and must <br> not attempt to use the resource described by this entry for any purpose. | No |  |
| FF | Entry Unavailable For Use - System firmware/software must not write to this entry, and must not attempt to <br> interpret this entry as indicating any resource. <br> Hardware MUST@FLIT use this value in the Secondary Properties field to indicate that, for proper <br> operation, the hardware requires the use of the resource definition indicated in the Primary Properties field | No |  |

The following figures illustrate the layout of Enhanced Allocation entries for various cases.
![img-164.jpeg](img-164.jpeg)

Figure 7-170 Example Entry with 64b Base and 64b MaxOffset

![img-165.jpeg](img-165.jpeg)

Figure 7-171 Example Entry with 64b Base and 32b MaxOffset

| E | W | RsvdP | Secondary <br> Properties | Primary Properties | BEI | R | 011 |
| :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: |
| Base[31:2] |  |  |  |  |  | 0 | R |
|  |  |  |  |  |  | 1 | R |
|  |  |  | MaxOffset[31:2] |  |  |  | R |
|  |  |  | MaxOffset[63:32] |  |  |  |  |

Figure 7-172 Example Entry with 32b Base and 64b MaxOffset

| E | W | RsvdP | Secondary <br> Properties | Primary Properties | BEI | R | 010 |
| :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: |
| Base[31:2] |  |  |  |  |  | 0 | R |
|  |  |  | MaxOffset[31:2] |  |  |  | R |

Figure 7-173 Example Entry with 32b Base and 32b MaxOffset

# 7.8.6 Resizable BAR Extended Capability 

The Resizable BAR Extended Capability is an optional capability that allows hardware to communicate resource sizes, and system software, after determining the optimal size, to communicate this optimal size back to the hardware. Hardware communicates the resource sizes that are acceptable for operation via the Resizable BAR Capability and Control registers. Hardware must support at least one size in the range from 1 MB to 512 GB.

# IMPLEMENTATION NOTE: RESIZABLE BAR BACKWARD COMPATIBILITY WITH SOFTWARE 

The Resizable BAR Extended Capability initially supported 20 sizes, ranging from 1 MB to 512 GB, and was later expanded with 16 larger sizes. The hardware requirement to support at least one of the initial sizes ensures backward compatibility with software that comprehends only the initial sizes.

Software determines, through a proprietary mechanism, what the optimal size is for the resource, and programs that size via the BAR Size field of the Resizable BAR Control register. Hardware immediately reflects the size inference in the read-only bits of the appropriate Base Address register. Hardware must Clear any bits that change from RW to read-only, so that subsequent reads return zero. Software must clear the Memory Space Enable bit in the Command register before writing the BAR Size field. After writing the BAR Size field, the contents of the corresponding BAR are undefined. To ensure that it contains a valid address after resizing the BAR, system software must reprogram the BAR, and Set the Memory Space Enable bit (unless the resource is not allocated).

The Resizable BAR Capability and Control registers are permitted to indicate the ability to operate at 4 GB or greater only if the associated BAR is a 64-bit BAR.

This capability is applicable to Functions that have Base Address registers only. The capability is permitted to be present in PFs. Since VFs do not implement standard BARs, the capability must not be present in a VF. The PF's Resizable BAR settings do not affect any settings in the SR-IOV Extended Capability.

It is strongly recommended that a Function not advertise any supported BAR sizes that are larger than the space it would effectively utilize if allocated.

# IMPLEMENTATION NOTE: USING THE CAPABILITY DURING RESOURCE ALLOCATION 

System software that allocates resources can use this capability to resize the resources inferred by the Function's BAR's read-only bits. Previous versions of this software determined the resource size by writing FFFF_FFFFh or FFFF_FFFF_FFFF_FFFFh to the BAR, reading back the value, and determining the size by the number of bits that are Set. Following this, the base address is written to the BAR.

System software uses this capability in place of the above mentioned method of determining the resource size, and prior to assigning the base address to the BAR. Potential usable resource sizes are reported by the Function via its Resizable BAR Capability and Control registers. It is intended that the software allocate the largest of the reported sizes that it can, since allocating less address space than the largest reported size can result in lower performance. Software then writes the size to the Resizable BAR Control register for the appropriate BAR for the Function. Following this, the base address is written to the BAR.

For interoperability reasons, it is possible that hardware will set the default size of the BAR to a low size; that is, a size lower than the largest reported in the Resizable BAR Capability and Control registers. Software that does not use this capability to size resources will likely result in sub-optimal resource allocation, where the resources are smaller than desirable, or not allocatable because there is no room for them.

With the Resizable BAR capability, the amount of address space consumed by a device can change. In a resource constrained environment, the allocation of more address space to a device may result in allocation of less of the address space to other memory-mapped hardware, like system RAM. System software responsible for allocating resources in this kind of environment is recommended to distribute the limited address space appropriately.

The Resizable BAR Capability structure defines a PCI Express Extended Capability, which is located in PCI Express Extended Configuration Space, that is, above the first 256 bytes, and is shown below in § Figure 7-174. This structure allows devices with this capability to be identified and controlled. A Capability and a Control register is implemented for each BAR that is resizable. Since a maximum of six BARs may be implemented by any Function, the Resizable BAR Capability structure can range from 12 bytes long (for a single BAR) to 52 bytes long (for all six BARs).
![img-166.jpeg](img-166.jpeg)

Figure 7-174 Resizable BAR Extended Capability

# 7.8.6.1 Resizable BAR Extended Capability Header (Offset 00h) 

![img-167.jpeg](img-167.jpeg)

Figure 7-175 Resizable BAR Extended Capability Header

Table 7-152 Resizable BAR Extended Capability Header

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $15: 0$ | PCI Express Extended Capability ID - This field is a PCI-SIG defined ID number that indicates the nature and format of the extended capability. <br> The PCI Express Extended Capability ID for the Resizable BAR Capability is 0015h. | RO |
| $19: 16$ | Capability Version - This field is a PCI-SIG defined version number that indicates the version of the capability structure present. <br> Must be 1 h for this version of the specification. | RO |
| $31: 20$ | Next Capability Offset - This field contains the offset to the next PCI Express Extended Capability structure or 000 h if no other items exist in the linked list of Capabilities. | RO |

### 7.8.6.2 Resizable BAR Capability Register

For backward compatibility with software, hardware must Set at least one bit in the range from 4 to 23 . See the associated Implementation Note in $\S$ Section 7.8.6 .

![img-168.jpeg](img-168.jpeg)

Figure 7-176 Resizable BAR Capability Register 5

Table 7-153 Resizable BAR Capability Register 6

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 4 | Function supports 1 MB BAR - When Set, indicates that the Function supports operating with the BAR sized to $1 \mathrm{MB}\left(2^{20}\right.$ bytes $)$ | RO |
| 5 | Function supports 2 MB BAR - When Set, indicates that the Function supports operating with the BAR sized to $2 \mathrm{MB}\left(2^{21}\right.$ bytes $)$ | RO |
| 6 | Function supports 4 MB BAR - When Set, indicates that the Function supports operating with the BAR sized to $4 \mathrm{MB}\left(2^{22}\right.$ bytes $)$ | RO |
| 7 | Function supports 8 MB BAR - When Set, indicates that the Function supports operating with the BAR sized to $8 \mathrm{MB}\left(2^{23}\right.$ bytes $)$ | RO |
| 8 | Function supports 16 MB BAR - When Set, indicates that the Function supports operating with the BAR sized to $16 \mathrm{MB}\left(2^{24}\right.$ bytes $)$ | RO |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 9 | Function supports 32 MB BAR - When Set, indicates that the Function supports operating with the BAR sized to $32 \mathrm{MB}\left(2^{25}\right.$ bytes $)$ | RO |
| 10 | Function supports 64 MB BAR - When Set, indicates that the Function supports operating with the BAR sized to $64 \mathrm{MB}\left(2^{26}\right.$ bytes $)$ | RO |
| 11 | Function supports 128 MB BAR - When Set, indicates that the Function supports operating with the BAR sized to $128 \mathrm{MB}\left(2^{27}\right.$ bytes $)$ | RO |
| 12 | Function supports 256 MB BAR - When Set, indicates that the Function supports operating with the BAR sized to $256 \mathrm{MB}\left(2^{28}\right.$ bytes $)$ | RO |
| 13 | Function supports 512 MB BAR - When Set, indicates that the Function supports operating with the BAR sized to $512 \mathrm{MB}\left(2^{29}\right.$ bytes $)$ | RO |
| 14 | Function supports 1 GB BAR - When Set, indicates that the Function supports operating with the BAR sized to $1 \mathrm{~GB}\left(2^{30}\right.$ bytes $)$ | RO |
| 15 | Function supports 2 GB BAR - When Set, indicates that the Function supports operating with the BAR sized to $2 \mathrm{~GB}\left(2^{31}\right.$ bytes $)$ | RO |
| 16 | Function supports 4 GB BAR - When Set, indicates that the Function supports operating with the BAR sized to $4 \mathrm{~GB}\left(2^{32}\right.$ bytes $)$ | RO |
| 17 | Function supports 8 GB BAR - When Set, indicates that the Function supports operating with the BAR sized to $8 \mathrm{~GB}\left(2^{33}\right.$ bytes $)$ | RO |
| 18 | Function supports 16 GB BAR - When Set, indicates that the Function supports operating with the BAR sized to $16 \mathrm{~GB}\left(2^{34}\right.$ bytes $)$ | RO |
| 19 | Function supports 32 GB BAR - When Set, indicates that the Function supports operating with the BAR sized to $32 \mathrm{~GB}\left(2^{35}\right.$ bytes $)$ | RO |
| 20 | Function supports 64 GB BAR - When Set, indicates that the Function supports operating with the BAR sized to $64 \mathrm{~GB}\left(2^{36}\right.$ bytes $)$ | RO |
| 21 | Function supports 128 GB BAR - When Set, indicates that the Function supports operating with the BAR sized to $128 \mathrm{~GB}\left(2^{37}\right.$ bytes $)$ | RO |
| 22 | Function supports 256 GB BAR - When Set, indicates that the Function supports operating with the BAR sized to $256 \mathrm{~GB}\left(2^{38}\right.$ bytes $)$ | RO |
| 23 | Function supports 512 GB BAR - When Set, indicates that the Function supports operating with the BAR sized to $512 \mathrm{~GB}\left(2^{39}\right.$ bytes $)$ | RO |
| 24 | Function supports 1 TB BAR - When Set, indicates that the Function supports operating with the BAR sized to $1 \mathrm{~TB}\left(2^{40}\right.$ bytes $)$ | RO |
| 25 | Function supports 2 TB BAR - When Set, indicates that the Function supports operating with the BAR sized to $2 \mathrm{~TB}\left(2^{41}\right.$ bytes $)$ | RO |
| 26 | Function supports 4 TB BAR - When Set, indicates that the Function supports operating with the BAR sized to $4 \mathrm{~TB}\left(2^{42}\right.$ bytes $)$ | RO |

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 27 | Function supports 8 TB BAR - When Set, indicates that the Function supports operating with the BAR <br> sized to 8 TB (245 bytes) | RO |
| 28 | Function supports 16 TB BAR - When Set, indicates that the Function supports operating with the BAR <br> sized to 16 TB (244 bytes) | RO |
| 29 | Function supports 32 TB BAR - When Set, indicates that the Function supports operating with the BAR <br> sized to 32 TB (245 bytes) | RO |
| 30 | Function supports 64 TB BAR - When Set, indicates that the Function supports operating with the BAR <br> sized to 64 TB (246 bytes) | RO |
| 31 | Function supports 128 TB BAR - When Set, indicates that the Function supports operating with the BAR <br> sized to 128 TB (247 bytes) | RO |

# 7.8.6.3 Resizable BAR Control Register 

![img-169.jpeg](img-169.jpeg)

Figure 7-177 Resizable BAR Control Register 5

Table 7-154 Resizable BAR Control Register 5

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 2:0 | BAR Index - This encoded value points to the beginning of the BAR. | RO |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | 0 | BAR located at offset 10h |
|  | 1 | BAR located at offset 14h |
|  | 2 | BAR located at offset 18h |
|  | 3 | BAR located at offset 1 Ch |
|  | 4 | BAR located at offset 20h |
|  | 5 | BAR located at offset 24h |
|  | Others | All other encodings are Reserved. |
|  | For a 64-bit Base Address register, the BAR Index indicates the lower DWORD. |  |
|  | This value indicates which BAR supports a negotiable size. |  |
| 7:5 | Number of Resizable BARs - Indicates the total number of resizable BARs)in the capability structure for the Function. See § Figure 7-174. <br> The value of this field must be in the range of 01 h to 06 h . The field is valid in Resizable BAR Control register (0) (at offset 008h), and is RsvdP for all others. | RO/RsvdP |
| 13:8 | BAR Size - This is an encoded value. | RW |
|  | 0 | $1 \mathrm{MB}\left(2^{20}\right.$ bytes) |
|  | 1 | $2 \mathrm{MB}\left(2^{21}\right.$ bytes) |
|  | 2 | $4 \mathrm{MB}\left(2^{22}\right.$ bytes) |
|  | 3 | $8 \mathrm{MB}\left(2^{23}\right.$ bytes) |
|  | 43 | $8 \mathrm{EB}\left(2^{63}\right.$ bytes) |
|  | The default value of this field is equal to the default size of the address space that the BAR resource is requesting via the BAR's read-only bits. For backward compatibility with software, the default value must be in the range from 0 to 19. <br> When this register field is programmed, the value is immediately reflected in the size of the resource, as encoded in the number of read-only bits in the BAR. <br> Software must only write values that correspond to those indicated as supported in the Resizable BAR Capability and Control registers. Writing an unsupported value will produce undefined results. BAR Size bits that never need to be Set in order to indicate every supported size are permitted to be hardwired to 0 . |  |
| 16 | Function supports 256 TB BAR - When Set, indicates that the Function supports operating with the BAR sized to $256 \mathrm{TB}\left(2^{48}\right.$ bytes) | RO |
| 17 | Function supports 512 TB BAR - When Set, indicates that the Function supports operating with the BAR sized to $512 \mathrm{TB}\left(2^{49}\right.$ bytes) | RO |
| 18 | Function supports 1 PB BAR - When Set, indicates that the Function supports operating with the BAR sized to $1 \mathrm{~PB}\left(2^{50}\right.$ bytes) | RO |
| 19 | Function supports 2 PB BAR - When Set, indicates that the Function supports operating with the BAR sized to $2 \mathrm{~PB}\left(2^{51}\right.$ bytes) | RO |
| 20 | Function supports 4 PB BAR - When Set, indicates that the Function supports operating with the BAR sized to $4 \mathrm{~PB}\left(2^{52}\right.$ bytes) | RO |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 21 | Function supports 8 PB BAR - When Set, indicates that the Function supports operating with the BAR <br> sized to $8 \mathrm{~PB}\left(2^{53}\right.$ bytes $)$ | RO |
| 22 | Function supports 16 PB BAR - When Set, indicates that the Function supports operating with the BAR <br> sized to $16 \mathrm{~PB}\left(2^{54}\right.$ bytes $)$ | RO |
| 23 | Function supports 32 PB BAR - When Set, indicates that the Function supports operating with the BAR <br> sized to $32 \mathrm{~PB}\left(2^{55}\right.$ bytes $)$ | RO |
| 24 | Function supports 64 PB BAR - When Set, indicates that the Function supports operating with the BAR <br> sized to $64 \mathrm{~PB}\left(2^{56}\right.$ bytes $)$ | RO |
| 25 | Function supports 128 PB BAR - When Set, indicates that the Function supports operating with the BAR <br> sized to $128 \mathrm{~PB}\left(2^{57}\right.$ bytes $)$ | RO |
| 26 | Function supports 256 PB BAR - When Set, indicates that the Function supports operating with the BAR <br> sized to $256 \mathrm{~PB}\left(2^{58}\right.$ bytes $)$ | RO |
| 27 | Function supports 512 PB BAR - When Set, indicates that the Function supports operating with the BAR <br> sized to $512 \mathrm{~PB}\left(2^{59}\right.$ bytes $)$ | RO |
| 28 | Function supports 1 EB BAR - When Set, indicates that the Function supports operating with the BAR <br> sized to $1 \mathrm{EB}\left(2^{60}\right.$ bytes $)$ | RO |
| 29 | Function supports 2 EB BAR - When Set, indicates that the Function supports operating with the BAR <br> sized to $2 \mathrm{EB}\left(2^{61}\right.$ bytes $)$ | RO |
| 30 | Function supports 4 EB BAR - When Set, indicates that the Function supports operating with the BAR <br> sized to $4 \mathrm{EB}\left(2^{62}\right.$ bytes $)$ | RO |
| 31 | Function supports 8 EB BAR - When Set, indicates that the Function supports operating with the BAR <br> sized to $8 \mathrm{EB}\left(2^{63}\right.$ bytes $)$ | RO |

# 7.8.7 VF Resizable BAR Extended Capability 9 

The VF Resizable BAR Extended Capability is permitted to be implemented only in PFs that implement at least one VF BAR, and affects the size and base of a PF's VF BARs. Since VFs do not implement the BARs themselves the capability must not be present in a VF. A PF may implement both a VF Resizable BAR Extended Capability and a Resizable BAR capability, as each capability operates independently.

The VF Resizable BAR Extended Capability is an optional capability that permits PFs to be able to have their VF's BARs resized. The VF Resizable BAR Extended Capability permits hardware to communicate the resource sizes that are acceptable for operation via the VF Resizable BAR Extended Capability and Control registers and system software to communicate the optimal size back to the hardware via the VF BAR Size field of the VF Resizable BAR Control register.

Hardware immediately reflects the size inference in the read-only bits of the appropriate VF BAR. The size inferred is the greater of the values decoded from the System Page Size and VF BAR Size fields. Hardware must Clear any bits that change from read-write to read-only, so that subsequent reads return zero. Software must clear the VF MSE bit in the SR-IOV Control Register before writing the VF BAR Size field. After writing the VF BAR Size field, the contents of the corresponding VF BAR are undefined. To ensure that it contains a valid address after resizing the VF BAR, system software must reprogram the VF BAR, and Set the VF MSE bit (unless the resource is not allocated).

The VF Resizable BAR Extended Capability and Control registers are permitted to indicate the ability to operate at 4 GB or greater only if the associated VF BAR is a 64-bit BAR.

It is strongly recommended that a Function not advertise any supported VF BAR size values in this capability that are larger than the space it would effectively utilize if allocated.

# IMPLEMENTATION NOTE: USING THE CAPABILITY DURING RESOURCE ALLOCATION 

System software uses this capability in a similar way to the Resizable BAR capability. System software must first configure the System Page Size register (see $\S$ Section 9.2.1.1.1). Potential usable memory aperture sizes are reported by the PF, and read, from the VF Resizable BAR Extended Capability and Control registers. It is intended that the software allocate the largest of the reported sizes that it can, since allocating less address space than the largest reported size can result in lower performance. Software then writes the size to the VF Resizable BAR Control register for the appropriate VF BAR for the Function. Following this, the base address is written to the VF BAR.

For interoperability reasons, it is possible that hardware will set the default size of the VF BAR to a low size; a size lower than the largest reported in the VF Resizable BAR Capability Register. Software that does not use this capability to size resources will likely result in sub-optimal resource allocation, where the resources are smaller than desirable, or not allocatable because there is no room for them. It is recommended that system software responsible for allocating resources in a resource constrained environment distribute the limited address space to all memory-mapped hardware, including system RAM, appropriately.

The VF Resizable BAR Extended Capability structure defines a PCI Express Extended Capability which is located in PCI Express Extended Configuration Space, that is, above the first 256 bytes, and is shown below in § Figure 7-178. This structure allows PFs with this capability to be identified and controlled. A Capability register and a Control register are implemented for each VF BAR that is resizable. Since a maximum of 6 VF BARs may be implemented by any PF, the VF Resizable BAR Capability structure can range from 12 bytes long (for a single VF BAR) to 52 bytes long (for all 6 VF BARs).
![img-170.jpeg](img-170.jpeg)

Figure 7-178 VF Resizable BAR Extended Capability

# 7.8.7.1 VF Resizable BAR Extended Capability Header (Offset 00h) 

![img-171.jpeg](img-171.jpeg)

Figure 7-179 VF Resizable BAR Extended Capability Header

Table 7-155 VF Resizable BAR Extended Capability Header

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $15: 0$ | PCI Express Extended Capability ID - This field is a PCI-SIG defined ID number that indicates the nature and format of the extended capability. <br> PCI Express Extended Capability ID for the VF Resizable BAR Extended Capability is 0024h. | RO |
| $19: 16$ | Capability Version - This field is a PCI-SIG defined version number that indicates the version of the capability structure present. <br> Must be 1 h for this version of the specification. | RO |
| $31: 20$ | Next Capability Offset - This field contains the offset to the next PCI Express Extended Capability structure or 000 h if no other items exist in the linked list of capabilities | RO |

### 7.8.7.2 VF Resizable BAR Capability Register (Offset 04h) 

The VF Resizable BAR Capability Register field descriptions are the same as the definitions in the Resizable BAR Capability Register in § Table 7-153. Where those descriptions say 'BAR', this register's description is for 'VF BAR'. Where those descriptions say 'Function', this register's description is for 'PF'. Otherwise, the field descriptions, the number of bits, their positions, and their attributes are the same. Consequently $\S$ Figure 7-176 similarly allocates the register fields in this register.

### 7.8.7.3 VF Resizable BAR Control Register (Offset 08h) 

The VF Resizable BAR Control register bits 31:16 follow the same definitions as the Resizable BAR Control register in § Table 7-154.

![img-172.jpeg](img-172.jpeg)

Figure 7-180 VF Resizable BAR Control Register

Table 7-156 VF Resizable BAR Control Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $2: 0$ | VF BAR Index - This encoded value points to the beginning of this particular VF BAR located in the SR-IOV Extended Capability. | RO |
|  | 0 VF BAR located at offset 24 h |  |
|  | 1 VF BAR located at offset 28 h |  |
|  | 2 VF BAR located at offset 2 Ch |  |
|  | 3 VF BAR located at offset 30 h |  |
|  | 4 VF BAR located at offset 34 h |  |
|  | 5 VF BAR located at offset 38 h |  |
|  | others All other encodings are reserved. |  |
|  | For a 64-bit Base Address register, the VF BAR Index indicates the lower DWORD. |  |
|  | This value indicates which VF BAR supports a negotiable size. |  |
| $7: 5$ | Number of VF Resizable BARs - Indicates the total number of resizable VF BARs in the capability structure for the Function. See § Figure 7-178. | RO/RsvdP |
|  | The value of this field must be in the range of 01 h to 06 h . The field is valid in VF Resizable BAR Control register (0) (at offset 08 h ), and is RsvdP for all others. |  |
| $13: 8$ | VF BAR Size - This is an encoded value. | RW |
|  | 0 |  |
|  | 1 MB ( $2^{20}$ bytes) |  |
|  | 2 MB ( $2^{21}$ bytes) |  |
|  | 4 MB ( $2^{22}$ bytes) |  |
|  | 3 |  |
|  | 8 MB ( $2^{23}$ bytes) |  |
|  | ... |  |
|  | 43 |  |
|  | 8 EB ( $2^{63}$ bytes) |  |
|  | The default value of this field is equal to the default size of the address space that the VF BAR resource is requesting via the VF BAR's read-only bits. |  |
|  | Software must only write values that correspond to those indicated as supported in the VF Resizable BAR Capability and Control registers. Writing an unsupported value will produce undefined results. |  |
|  | When this register field is programmed, the value is immediately reflected in the size of the resource, as encoded in the number of read-only bits in the VF BAR. |  |

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| $31: 16$ | These bits are identical to the Resizable BAR Control Register bits [31:16] defined in \$ Figure 7-177. <br> Where those descriptions say 'BAR', this register's description is for 'VF BAR'. Where those descriptions <br> say 'Function', this register's description is for 'PF'. | See |
|  |  | $\S$ Figure |
|  |  | 7-177 |

# 7.8.8 ARI Extended Capability 

ARI is an optional capability, except as stated below. This capability must be implemented by each Function in an ARI Device. It is not applicable to a Root Port, a Switch Downstream Port, an RCIEP, or a Root Complex Event Collector.

For SR-IOV devices not in a Root Complex, implementing the ARI Extended Capability in each Function is mandatory.
![img-173.jpeg](img-173.jpeg)

Figure 7-181 ARI Extended Capability

### 7.8.8.1 ARI Extended Capability Header (Offset 00h)

![img-174.jpeg](img-174.jpeg)

Figure 7-182 ARI Extended Capability Header

Table 7-157 ARI Extended Capability Header

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 15:0 | PCI Express Extended Capability ID - This field is a PCI-SIG defined ID number that indicates the nature <br> and format of the extended capability. <br> PCI Express Extended Capability ID for the ARI Extended Capability is 000Eh. | RO |
| 19:16 | Capability Version - This field is a PCI-SIG defined version number that indicates the version of the <br> capability structure present. <br> Must be 1h for this version of the specification. | RO |
| 31:20 | Next Capability Offset - This field contains the offset to the next PCI Express Extended Capability <br> structure or 000h if no other items exist in the linked list of Capabilities. | RO |

# 7.8.8.2 ARI Capability Register (Offset 04h) 

![img-175.jpeg](img-175.jpeg)

Figure 7-183 ARI Capability Register

Table 7-158 ARI Capability Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 0 | MFVC Function Groups Capability (M) - Applicable only for Function 0; must be Zero for all other Functions. If Set, indicates that the ARI Device supports Function Group level arbitration via its Multi-Function Virtual Channel (MFVC) Capability structure. <br> Any SR-IOV Device that implements the MFVC Extended Capability with the optional Function Arbitration Table and consumes more than one Bus Number must Set this bit in its Function 0. | RO |
| 1 | ACS Function Groups Capability (A) - Applicable only for Function 0; must be Zero for all other Functions. If Set, indicates that the ARI Device supports Function Group level granularity for ACS P2P Egress Control via its ACS Capability structures. <br> Any SR-IOV Device that implements the ACS Capability with the optional Egress Control Vector and consumes more than one Bus Number must Set this bit in its Function 0. | RO |
| $15: 8$ | Next Function Number - With non-VFs, this field indicates the Function Number of the next higher numbered Function in the Device, or 00 h if there are no higher numbered Functions. Function 0 starts this linked list of Functions. <br> The presence of Shadow Functions does not affect this field. <br> For VFs, this field is undefined since VFs are located using First VF Offset (see § Section 9.3.3.9) and VF Stride (see § Section 9.3.3.10). | RO |

# 7.8.8.3 ARI Control Register (Offset 06h) 

![img-176.jpeg](img-176.jpeg)

Figure 7-184 ARI Control Register

Table 7-159 ARI Control Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 0 | MFVC Function Groups Enable (M) - Applicable only for Function 0; must be hardwired to 0b for all other Functions. When set, the ARI Device must interpret entries in its Function Arbitration Table as Function Group Numbers rather than Function Numbers. <br> Default value of this bit is 0b. Must be hardwired to 0b if the MFVC Function Groups Capability bit is 0b. | RW |
| 1 | ACS Function Groups Enable (A) - Applicable only for Function 0; must be hardwired to 0b for all other Functions. When set, each Function in the ARI Device must associate bits within its Egress Control Vector with Function Group Numbers rather than Function Numbers. <br> Default value of this bit is 0b. Must be hardwired to 0b if the ACS Function Groups Capability bit is 0b. | RW |
| 6:4 | Function Group - Assigns a Function Group Number to this Function. <br> Default value of this field is 000b. Must be hardwired to 000b if in Function 0, the MFVC Function Groups Capability bit and ACS Function Groups Capability bit are both 0b. | RW |

### 7.8.9 PASID Extended Capability Structure

The presence of a PASID Extended Capability indicates that one or more Endpoint Functions support sending and receiving TLPs containing a PASID TLP Prefix in NFM or containing OHC with PASID in FM. Separate support and enables are provided for the various optional features.

This capability is only permitted to be implemented in to Endpoints Functions (including RCIEPs). A PF is permitted to implement the PASID capability, but VFs must not implement it. For Root Ports, support and control is outside the scope of this specification.

In earlier revisions of this specification, it was ambiguous whether a single PASID capability or multiple PASID capabilities are supported for an MFD. For backward compatibility, both models are supported. In the PASID Capability and Control register bit definitions, the phrase "applicable Endpoint Function" refers to the following rules:

- If an SFD contains a PASID capability, it must apply to the SFD's single Endpoint Function.
- If an MFD contains a single PASID capability, it must apply to all Endpoint Functions in the MFD, including all VFs regardless of their PF association.

- If an MFD contains multiple PASID capabilities, each PASID capability that exists must apply only to the Endpoint Function in which it resides, with the exception that if a PF contains a PASID capability, that PASID capability must apply to all VFs associated with that PF.

When a PASID capability applies to multiple Endpoint Functions in a device, the device sends the requesting Function's ID in the Requester ID field of the TLP containing the PASID.

This capability is independent of both the ATS and PRI features defined in § Chapter 10. . Endpoint Functions that contain a PASID Extended Capability need not support ATS or PRI. Endpoint Functions that support ATS or PRI need not support PASID.
§ Figure 7-185 details allocation of the register bits in the PASID Extended Capability structure.
![img-177.jpeg](img-177.jpeg)

Figure 7-185 PASID Extended Capability Structure

# 7.8.9.1 PASID Extended Capability Header (Offset 00h) § 

§ Figure 7-186 details allocation of the register fields in the PASID Extended Capability Header; § Table 7-160 provides the respective bit definitions.
![img-178.jpeg](img-178.jpeg)

Figure 7-186 PASID Extended Capability Header

Table 7-160 PASID Extended Capability Header

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| $15: 0$ | PASID Extended Capability ID - Indicates the PASID Extended Capability structure. This field must return <br> a Capability ID of 001Bh indicating that this is a PASID Extended Capability structure. | RO |
| $19: 16$ | Capability Version - This field is a PCI-SIG defined version number that indicates the version of the <br> Capability structure present. <br> Must be 1h for this version of the specification. | RO |
| $31: 20$ | Next Capability Offset - The offset to the next PCI Extended Capability structure or 000h if no other <br> items exist in the linked list of capabilities. | RO |

# 7.8.9.2 PASID Capability Register (Offset 04h) 

\$ Figure 7-187 details the allocation of register bits of the PASID Capability register; \$ Table 7-161 provides the respective bit definitions.
![img-179.jpeg](img-179.jpeg)

Figure 7-187 PASID Capability Register

Table 7-161 PASID Capability Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 1 | Execute Permission Supported - If Set, an applicable Endpoint Function supports sending TLPs that have the Execute Requested bit Set. <br> If Clear, the Endpoint Function will never Set the Execute Requested bit. <br> It is strongly recommended that this bit be hardwired to 0b. | RO |
| 2 | Privileged Mode Supported - If Set, an applicable Endpoint Function supports operating in Privileged and Non-Privileged modes, and supports sending requests that have the Privileged Mode Requested bit Set. <br> If Clear, the Endpoint Function will never Set the Privileged Mode Requested bit. | RO |
| 3 | Translated Requests with PASID Supported - If Set, indicates that an applicable Endpoint Function supports Translated Requests with PASID (see \$ Section 10.1.3). This bit is only permitted to be Set if the Endpoint Function supports ATS. | RO |
| 12:8 | Max PASID Width - Indicates the width of the PASID field supported by an applicable Endpoint Function. The value $n$ indicates support for PASID values 0 through $2^{\text {n }}-1$ (inclusive). The value 0 indicates support for a single PASID (0). The value 20 indicates support for all PASID values (20 bits). This field must be between 0 and 20 (inclusive). | RO |

### 7.8.9.3 PASID Control Register (Offset 06h)

\$ Figure 7-188 details the allocation of register bits of the PASID Control register; \$ Table 7-162 provides the respective bit definitions.

![img-180.jpeg](img-180.jpeg)

Figure 7-188 PASID Control Register

Table 7-162 PASID Control Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 0 | PASID Enable - If Set, an applicable Endpoint Function is permitted to send and receive TLPs that contain a PASID TLP Prefix. If Clear, the Endpoint Function is not permitted to do so. <br> Behavior is undefined if an applicable Endpoint Function supports ATS and this bit changes value when the Enable (E) bit in that Function's ATS Control Register is Set (see § Section 10.5.1.3). <br> Default is Ob. | RW |
| 1 | Execute Permission Enable - If Set, an applicable Endpoint Funciton is permitted to send Requests that have the Execute Requested bit Set. If Clear, the Endpoint is not permitted to do so. <br> Behavior is undefined if an applicable Endpoint Function" supports ATS and this bit changes value when the Enable bit in that Function's ATS Control Register is Set (see § Section 10.5.1.3). <br> If Execute Permission Supported is Clear, this bit is RsvdP. <br> Default is Ob. | RW/RsvdP (see description) |
| 2 | Privileged Mode Enable - If Set, an applicable Endpoint Function is permitted to send Requests that have the Privileged Mode Requested bit Set. If Clear, the Endpoint Function is not permitted to do so. <br> Behavior is undefined if an applicable Endpoint Function supports ATS and this bit changes value when the Enable bit in that Function's ATS Control Register is Set (see § Section 10.5.1.3). <br> If Privileged Mode Supported is Clear, this bit is RsvdP. <br> Default is Ob. | RW/RsvdP (see description) |
| 3 | Translated Requests with PASID Enable - When Set, the ATC associated with an applicable Endpoint Function is permitted to issue Translated Requests with a PASID TLP Prefix. If the ATC obtained a translation using a Translation Request with PASID, the corresponding Translated Request must carry a PASID that matches the PASID used to obtain the translation. Similarly, if the ATC obtained a translation using a Translation Request without a PASID, the corresponding Translated Request must not carry a PASID. <br> When Clear, the ATC associated with the Endpoint Function is prohibited from issuing Translated Requests with a PASID. <br> Behavior is undefined if an applicable Endpoint Function supports ATS this bit changes value when the Enable (E) bit in that Function's ATS Control Register is Set (see § Section 10.5.1.3). <br> If Translated Requests with PASID Supported bit is Clear, this bit is RsvdP. See (see § Section 10.1.3) for details. <br> Default is Ob. | RW/RsvdP (see description) |

# 7.8.10 FRS Queueing Extended Capability 

The FRS Queueing Extended Capability is required for Root Ports and Root Complex Event Collectors that support the optional normative FRS Queueing capability. See § Section 6.22. This extended capability is only permitted in Root Ports and Root Complex Event Collectors.

If this capability is present in a Function, that Function must also implement either MSI, MSI-X, or both.
![img-181.jpeg](img-181.jpeg)

Figure 7-189 FRS Queueing Extended Capability

### 7.8.10.1 FRS Queueing Extended Capability Header (Offset 00h)

![img-182.jpeg](img-182.jpeg)

Figure 7-190 FRS Queueing Extended Capability Header

Table 7-163 FRS Queueing Extended Capability Header

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 15:0 | PCI Express Extended Capability ID - This field is a PCI-SIG defined ID number that indicates the nature and format of the extended capability. <br> PCI Express Extended Capability ID for the FRS Queueing Extended Capability is 0021h. | RO |
| 19:16 | Capability Version - This field is a PCI-SIG defined version number that indicates the version of the capability structure present. <br> Must be 1 h for this version of the specification. | RO |
| $31: 20$ | Next Capability Offset - This field contains the offset to the next PCI Express Extended Capability structure or 000 h if no other items exist in the linked list of capabilities. | RO |

# 7.8.10.2 FRS Queueing Capability Register (Offset 04h) 

![img-183.jpeg](img-183.jpeg)

Figure 7-191 FRS Queueing Capability Register

Table 7-164 FRS Queueing Capability Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $11: 0$ | FRS Queue Max Depth - Indicates the implemented queue depth, with valid values ranging from 001 h (queue depth of 1) to FFFh (queue depth of 4095) <br> The value of FRS Message Queue Depth must not exceed this value. <br> The value 000 h is Reserved. | HwInit |
| $20: 16$ | FRS Interrupt Message Number - When MSI/MSI-X is implemented, this register indicates which MSI/ MSI-X vector is used for the interrupt message generated in association with FRS Message Received or FRS Message Overflow. <br> For MSI, the value in this register indicates the offset between the base Message Data and the interrupt message that is generated. Hardware is required to update this field so that it is correct if the number of MSI Messages assigned to the Function changes when software writes to the Multiple Message Enable field in the Message Control Register for MSI. <br> For MSI-X, the value in this register indicates which MSI-X Table entry is used to generate the interrupt message. The entry must be one of the first 32 entries even if the Function implements more than 32 entries. For a given MSI-X implementation, the entry must remain constant. <br> If both MSI and MSI-X are implemented, they are permitted to use different vectors, though software is permitted to enable only one mechanism at a time. If MSI-X is enabled, the value in this register must indicate the vector for MSI-X. If MSI is enabled or neither is enabled, the value in this register must indicate the vector for MSI. If software enables both MSI and MSI-X at the same time, the value in this register is undefined. | RO |

### 7.8.10.3 FRS Queueing Status Register (Offset 08h)

![img-184.jpeg](img-184.jpeg)

Figure 7-192 FRS Queueing Status Register

Table 7-165 FRS Queueing Status Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :-- |
| 0 | FRS Message Received - This bit is Set when a new FRS Message is Received or generated by this Root <br> Port or Root Complex Event Collector. <br> Root Ports must Clear this bit when the Link is DL_Down. <br> Default value of this bit is Ob. | RW1C |
| 1 | FRS Message Overflow - This bit is Set if the FRS Message queue is full and a new FRS Message is <br> received or generated by this Root Port or Root Complex Event Collector. <br> Root Ports must Clear this bit when the Link is DL_Down. <br> Default value of this bit is Ob. | RW1C |

# 7.8.10.4 FRS Queueing Control Register (Offset OAh) 

![img-185.jpeg](img-185.jpeg)

Figure 7-193 FRS Queueing Control Register

Table 7-166 FRS Queueing Control Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :-- |
| 0 | FRS Interrupt Enable - When Set and MSI or MSI-X is enabled, the Port must issue an MSI/MSI-X interrupt <br> to indicate the Ob to lb transition of either the FRS Message Received or the FRS Message Overflow bits. <br> Default value of this bit is Ob. | RW |

### 7.8.10.5 FRS Message Queue Register (Offset OCh)

The FRS Message Queue Register contains fields from the oldest FRS message in the queue. It also indicates the number of FRS messages in the queue.

A write of any value that includes byte 0 to this register removes the oldest FRS Message from the queue and updates these fields. A write to this register when the queue is empty has no effect.
![img-186.jpeg](img-186.jpeg)

Figure 7-194 FRS Message Queue Register

Table 7-167 FRS Message Queue Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 15:0 | FRS Message Queue Function ID - Recorded from the Requester ID of the oldest FRS Message Received or generated by this Root Port or Root Complex Event Collector and still in the queue. <br> Undefined if FRS Message Queue Depth is 000 h. | RO |
| 19:16 | FRS Message Queue Reason - Recorded from the FRS Reason of the oldest FRS Message Received or generated by this Root Port or Root Complex Event Collector and still in the queue. <br> Undefined if FRS Message Queue Depth is 000 h. | RO |
| $31: 20$ | FRS Message Queue Depth - indicates the current number of FRS Messages in the queue. <br> The value of 000 h indicates an empty queue. <br> Default value of this field is 000 h . | RO |

# 7.8.11 Flattening Portal Bridge (FPB) Capability 

The Flattening Portal Bridge (FPB) Capability is an optional Capability that is required for any bridge Function that implements FPB. The FPB Capability structure is shown in $\S$ Figure 7-195.
![img-187.jpeg](img-187.jpeg)

Figure 7-195 FPB Capability Structure

If a Switch implements FPB then each of its Ports of the Switch must implement an FPB Capability Structure. A Root Complex is permitted to implement the FPB Capability Structure on some or on all of its Root Ports. A Root Complex is permitted to implement the FPB Capability for internal logical busses.

# 7.8.11.1 FPB Capability Header (Offset 00h) 

![img-188.jpeg](img-188.jpeg)

Figure 7-196 FPB Capability Header

Table 7-168 FPB Capability Header

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| $7: 0$ | Capability ID - Must be set to 15h | RO |
| $15: 8$ | Next Pointer - Pointer to the next item in the capabilities list. Must be 00h for the final item in the list. | RO |

### 7.8.11.2 FPB Capabilities Register (Offset 04h) 

§ Figure 7-197 details allocation of register fields for FPB Capabilities register and § Table 7-169 describes the requirements for this register.
![img-189.jpeg](img-189.jpeg)

Figure 7-197 FPB Capabilities Register

Table 7-169 FPB Capabilities Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 0 | FPB RID Decode Mechanism Supported - If Set, indicates that the FPB RID Vector mechanism is <br> supported. | HwInit |
| 1 | FPB MEM Low Decode Mechanism Supported - If Set, indicates that the FPB MEM Low Vector <br> mechanism is supported. | HwInit |
| 2 | FPB MEM High Decode Mechanism Supported - If Set, indicates that the FPB Mem High mechanism <br> is supported. | HwInit |

| Bit Location | Register Description |  | Attributes |
| :--: | :--: | :--: | :--: |
| $7: 3$ | FPB Num Sec Dev - For Upstream Ports of Switches only, this field indicates the quantity of Device Numbers associated with the Secondary Side of the Upstream Port bridge. The quantity is determined by adding one to the numerical value of this field. <br> Although it is recommended that Switch implementations assign Downstream Ports using all 8 allowed Functions per allocated Device Number, such that all Downstream Ports are assigned within a contiguous range of Device and Function Numbers, it is, however, explicitly permitted to assign Downstream Ports to Function Numbers that are not contiguous within the indicated range of Device Numbers, and system software is required to scan for Switch Downstream Ports at every Function Number within the indicated quantity of Device Numbers associated with the Secondary Side of the Upstream Port. <br> This field is Reserved for Downstream Ports. | Hwinit/RsvdP |
| $10: 8$ | FPB RID Vector Size Supported - Indicates the size of the FPB RID Vector implemented in hardware, and constrains the allowed values software is permitted to write to the FPB RID Vector Granularity field. <br> Defined encodings are: |  | Hwinit |
|  | Value | Size | Allowed Granularities in RID units |
|  | 000b | 256 bits | $8,64,256$ |
|  | 010b | 1 K bits | 8,64 |
|  | 101b | 8 K bits | 8 |
|  | All other encodings are Reserved. <br> If the FPB RID Decode Mechanism Supported bit is Clear, then the value in this field is undefined and must be ignored by software. |  |  |
| $18: 16$ | FPB MEM Low Vector Size Supported - Indicates the size of the FPB MEM Low Vector implemented in hardware, and constrains the allowed values software is permitted to write to the FPB MEM Low Vector Start field. <br> Defined encodings are: |  | Hwinit |
|  | Value | Size | Allowed Granularities in MB units |
|  | 000b | 256 bits | $1,2,4,8,16$ |
|  | 001b | 512 bits | $1,2,4,8$ |
|  | 010b | 1 K bits | $1,2,4$ |
|  | 011b | 2 K bits | 1,2 |
|  | 100b | 4 K bits | 1 |
|  | All other encodings are Reserved. <br> If the FPB MEM Low Decode Mechanism Supported bit is Clear, then the value in this field is undefined and must be ignored by software. |  |  |
| $26: 24$ | FPB MEM High Vector Size Supported - Indicates the size of the FPB MEM High Vector implemented in hardware. <br> Defined encodings are: |  | Hwinit |

| Bit Location | Register Description |  | Attributes |
| :--: | :--: | :--: | :--: |
|  |  | Value | Size |
|  |  | 000b | 256 bits |
|  |  | 001b | 512 bits |
|  |  | 010b | 1 K bits |
|  |  | 011b | 2 K bits |
|  |  | 100b | 4 K bits |
|  |  | 101b | 8 K bits |
|  | All other encodings are Reserved. |  |  |
|  | All defined Granularities are allowed for all defined vector sizes. |  |  |
|  | If the FPB MEM High Decode Mechanism Supported bit is Clear, then the value in this field is undefined and must be ignored by software. |  |  |

# 7.8.11.3 FPB RID Vector Control 1 Register (Offset 08h) 

§ Figure 7-198 details allocation of register fields for FPB RID Control 1 register and § Table 7-173 describes the requirements for this register.
![img-190.jpeg](img-190.jpeg)

Figure 7-198 FPB RID Vector Control 1 Register

Table 7-173 FPB RID Vector Control 1 Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :-- |
| 0 | FPB RID Decode Mechanism Enable - When Set, enables the FPB RID Decode mechanism <br> If the FPB RID Decode Mechanism Supported bit is Clear, then it is permitted for hardware to implement this <br> bit as RO, and in this case the value in this field is undefined. <br> Default value of this bit is Ob. | RW/RO |
| 7:4 | FPB RID Vector Granularity - The value written by software to this field controls the granularity of the <br> FPB RID Vector and the required alignment of the FPB RID Vector Start field (below). <br> Defined encodings are: | RW/RO |
|  | Value | Granularity |
|  | 0000b | 8 RIDs |

| Bit Location | Register Description |  | Attributes |
| :--: | :--: | :--: | :--: |
|  |  | Value | Granularity |
|  |  | 0011b | 64 RIDs |
|  |  | 0101b | 256 RIDs |

All other encodings are Reserved.
Based on the implemented FPB RID Vector size, hardware is permitted to implement as RW only those bits of this field that can be programmed to non-zero values, in which case the upper order bits are permitted but not required to be hardwired to 0 .

If the FPB RID Decode Mechanism Supported bit is Clear, then it is permitted for hardware to implement this field as RO, and the value in this field is undefined.

For Downstream Ports, if the ARI Forwarding Enable bit in the Device Control 2 Register and the FPB RID Decode Mechanism Enable bit are Set, then software must program 0101b into this field, if this field is programmable.
Default value for this field is 0000 b .
31:19 FPB RID Vector Start - The value written by software to this field controls the offset at which the FPB RID Vector is applied.

The value represents a RID offset in units of 8 RIDs, such that bit 0 of the FPB RID Vector represents the range of RIDs starting from the value represented in this register up to that value plus the FPB RID Vector Granularity minus 1, and bit 1 represents range from this register value plus granularity up to that value plus FPB RID Vector Granularity minus 1, etc.

Software must program this field to a value that is naturally aligned (meaning the lower order bits must be 0 's) according to the value in the FPB RID Vector Granularity Field as indicated here:

| FPB RID Vector Granularity | Start Alignment Constraint |
| :--: | :--: |
| 0000 b | $<$ no constraint> |
| 0011 b | $\ldots 000 b$ |
| 0101 b | $\ldots 00000 b$ |

All other encodings are Reserved.
If this requirement is violated, the hardware behavior is undefined.
For Downstream Ports, if the ARI Forwarding Enable bit in the Device Control 2 Register and the FPB RID Decode Mechanism Enable bit are Set, then software must program bits 23:19 of this field to a value of 00000 b , and the hardware behavior is undefined if any other value is programmed.

If the FPB RID Decode Mechanism Supported bit is Clear, then it is permitted for hardware to implement this field as RO, and the value in this field is undefined.

Default value for this field is 0000000000000 b .

# 7.8.11.4 FPB RID Vector Control 2 Register (Offset 0Ch) $\S$ 

§ Figure 7-199 details allocation of register fields for FPB RID Vector Control 2 register and § Table 7-176 describes the requirements for this register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 15:3 | RID Secondary Start - The value written by software to this field controls the RID offset at which Type 1 Configuration Requests passing downstream through the bridge must be converted to Type 0. <br> Bits[2:0] of the RID offset are fixed by hardware as 000b and cannot be modified. <br> For Downstream Ports, if the ARI Forwarding Enable bit in the Device Control 2 register is Set, then software must write bits 7:3 of this field to 00000 b. <br> If the FPB RID Decode Mechanism Supported bit is Clear, then it is permitted for hardware to implement this field as RO, and the value in this field is undefined. <br> Default value for this field is 00000000000000 b. | RW/RO |

# 7.8.11.5 FPB MEM Low Vector Control Register (Offset 10h) 

\$ Figure 7-200 details allocation of register fields for FPB MEM Low Vector Control Register and \$ Table 7-177 describes the requirements for this register.
![img-191.jpeg](img-191.jpeg)

Figure 7-200 FPB MEM Low Vector Control Register

Table 7-177 FPB MEM Low Vector Control Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :-- |
| 0 | FPB MEM Low Decode Mechanism Enable - When Set, enables the FPB MEM Low Decode mechanism. | RW/RO |
|  | If the FPB MEM Low Decode Mechanism Supported bit is Clear, then it is permitted for hardware to <br> implement this bit as RO, and in this case the value in this field is undefined. <br> Default value of this bit is Ob. |  |
| 7:4 | FPB MEM Low Vector Granularity - The value written by software to this field controls the granularity of <br> the FPB MEM Low Vector, and the required alignment of the FPB MEM Low Vector Start field (below). <br> Defined encodings are: | RW/RO |

| Bit Location | Register Description |  | Attributes |
| :--: | :--: | :--: | :--: |
|  |  | Value | Granularity |
|  |  | 0000b | 1 MB |
|  |  | 0001b | 2 MB |
|  |  | 0010b | 4 MB |
|  |  | 0011b | 8 MB |
|  |  | 0100b | 16 MB |

All other encodings are Reserved.
Based on the implemented FPB MEM Low Vector size, hardware is permitted to implement as RW only those bits of this field that can be programmed to non-zero values, in which case the upper order bits are permitted but not required to be hardwired to 0 .
If the FPB MEM Low Decode Mechanism Supported bit is Clear, then it is permitted for hardware to implement this field as RO, and the value in this field is undefined.
Default value for this field is 0000 b .
31:20 FPB MEM Low Vector Start - The value written by software to this field sets bits 31:20 of the base address at which the FPB MEM Low Vector is applied.
Software must program this field to a value that is naturally aligned (meaning the lower order bits must be 0 's) according to the value in the FPB MEM Low Vector Granularity field as indicated here:

| FPB MEM Low Vector Granularity | Constraint |
| :--: | :--: |
| 0000b | $<$ no constraint> |
| 0001b | ...0b |
| 0010b | ...00b |
| 0011b | ...000b |
| 0100b | ...0000b |

If this requirement is violated, the hardware behavior is undefined.
If the FPB MEM Low Decode Mechanism Supported bit is Clear, then it is permitted for hardware to implement this field as RO, and the value in this field is undefined.
Default value for this field is 000 h .

# 7.8.11.6 FPB MEM High Vector Control 1 Register (Offset 14h) $\S$ 

§ Figure 7-201 details allocation of register fields for FPB MEM High Vector Control 1 Register and § Table 7-180 describes the requirements for this register.

![img-192.jpeg](img-192.jpeg)

Figure 7-201 FPB MEM High Vector Control 1 Register

Table 7-180 FPB MEM High Vector Control 1 Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 0 | FPB MEM High Decode Mechanism Enable - When Set, enables the FPB MEM High Decode mechanism. <br> If the FPB MEM High Decode Mechanism Supported bit is Clear, then it is permitted for hardware to implement this bit as RO, and in this case the value in this field is undefined. <br> Default value of this bit is Ob. | RW/RO |
| $7: 4$ | FPB MEM High Vector Granularity - The value written by software to this field controls the granularity of the FPB MEM High Vector, and the required alignment of the FPB MEM High Vector Start Lower field (below). <br> Software is permitted to select any allowed Granularity from the table below regardless of the value in the FPB MEM High Vector Size Supported field. <br> Defined encodings are: | RW/RO |
|  | | |
|  | | |
|  | | |
|  | | |
|  | | |
|  | | All other encodings are Reserved. <br> Based on the implemented FPB MEM High Vector size, hardware is permitted to implement as RW only those bits of this field that can be programmed to non-zero values, in which case the upper order bits are permitted but not required to be hardwired to 0 . <br> If the FPB MEM High Decode Mechanism Supported bit is Clear, then it is permitted for hardware to implement this field as RO, and the value in this field is undefined. <br> Default value for this field is 0000 b . | RW/RO |
| $31: 28$ | FPB MEM High Vector Start Lower - The value written by software to this field sets the lower bits of the base address at which the FPB MEM High Vector is applied. | RW/RO |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| Software must program this field to a value that is naturally aligned (meaning the lower order bits must be 0 's) according to the value in the FPB MEM High Vector Granularity Field as indicated here: |  |  |
| FPB MEM High Vector Granularity | Constraint |  |
| 0000b | <no constraint> |  |
| 0001b | ...0b |  |
| 0010b | ... 00 b |  |
| 0011b | ... 000 b |  |
| 0100b | ... 0000 b |  |
| 0101b | ... 00000 b |  |
| 0110b | ... 000000 b |  |
| 0111b | ... 0000000 b |  |

If this requirement is violated, the hardware behavior is undefined.
If the FPB MEM High Decode Mechanism Supported bit is Clear, then it is permitted for hardware to implement this field as RO, and the value in this field is undefined.
Default value for this field is 0 h .

# 7.8.11.7 FPB MEM High Vector Control 2 Register (Offset 18h) 

§ Figure 7-202 details allocation of register fields for FPB MEM High Vector Control 2 Register and § Table 7-183 describes the requirements for this register.
![img-193.jpeg](img-193.jpeg)

Figure 7-202 FPB MEM High Vector Control 2 Register

Table 7-183 FPB MEM High Vector Control 2 Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $31: 0$ | FPB MEM High Vector Start Upper - The value written by software to this field sets bits 63:32 of the base address at which the FPB MEM High Vector is applied. <br> Software must program this field to a value that is naturally aligned (meaning the lower order bits must be 0 's) according to the value in the FPB MEM High Vector Granularity Field as indicated here: | RW/RO |

| Bit Location | Register Description |  | Attributes |
| :--: | :--: | :--: | :--: |
|  |  |  |  |
|  | FPB MEM High Vector Granularity | Constraint |  |
|  | 0000b | <no constraint> |  |
|  | 0001b | <no constraint> |  |
|  | 0010b | <no constraint> |  |
|  | 0011b | <no constraint> |  |
|  | 0100b | <no constraint> |  |
|  | 0101b | ...0b |  |
|  | 0110b | ...00b |  |
|  | 0111b | ...000b |  |
|  | If this requirement is violated, the hardware behavior is undefined |  |  |
|  | If the FPB MEM High Decode Mechanism Supported bit is Clear, then it is permitted for hardware to implement this field as RO, and the value in this field is undefined. |  |  |
|  | Default value for this field is 00000000 h . |  |  |

# 7.8.11.8 FPB Vector Access Control Register (Offset 1Ch) 

\$ Figure 7-203 details allocation of register fields for FPB Vector Access Control register and \$ Table 7-185 describes the requirements for this register.
![img-194.jpeg](img-194.jpeg)

Figure 7-203 FPB Vector Access Control Register

Table 7-185 FPB Vector Access Control Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $7: 0$ | FPB Vector Access Offset - The value in this field indicates the offset of the DWORD portion of the FPB RID, MEM Low or MEM High, Vector that can be read or written by means of the FPB Vector Access Data register. <br> The selection of RID, MEM Low or MEM High is made by the value written to the FPB Vector Select field. The bits of this field map to the offset according to the value in the corresponding FPB RID, MEM Low, or MEM High Vector Size Supported field as shown here: | RW/RO |

| Bit Location | Register Description |  | Attributes |
| :--: | :--: | :--: | :--: |
|  |  | Vector Size Supported | Offset Bits | Vector Access Offset |
|  |  | 000b | 2:0 | 2:0 (7:3 unused) |
|  |  | 001b | 3:0 | 3:0 (7:4 unused) |
|  |  | 010b | 4:0 | 4:0 (7:5 unused) |
|  |  | 011b | 5:0 | 5:0 (7:6 unused) |
|  |  | 100b | 6:0 | 6:0 (7 unused) |
|  |  | 101b | 7:0 | 7:0 |

All other encodings are Reserved.
Bits in this field that are unused per the table above must be written by software as 0 b , and are permitted but not required to be implemented as RO.
Default value for this field is 00 h
15:14 FPB Vector Select - The value written to this field selects the Vector to be accessed at the indicated FPB Vector Access Offset. Software must only write this field with values that correspond to supported FPB mechanisms, otherwise the results are undefined.
Defined encodings are:
00b RID
01b MEM Low
10b MEM High
11b Reserved
Default value for this field is 00 b

# 7.8.11.9 FPB Vector Access Data Register (Offset 20h) 

§ Figure 7-204 details allocation of register fields for FPB Vector Access Data Register and § Table 7-187 describes the requirements for this register.
![img-195.jpeg](img-195.jpeg)

Figure 7-204 FPB Vector Access Data Register

Table 7-187 FPB Vector Access Data Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 31:0 | FPB Vector Access Data - Reads from this register return the DW of data from the FPB Vector at the location determined by the value in the FPB Vector Access Offset Register. Writes to this register replace the | RW |

| Bit Location | Register Description | Attributes |
| :-- | :-- | :-- |
|  | DW of data from the FPB Vector at the location determined by the value in the FPB Vector Access Offset <br> Register. |  |
|  | Behavior of this field is undefined if software programs unsupported values for FPB Vector Select or FPB <br> Vector Access Offset fields, however hardware is required to complete the access to this register normally. <br> Default value for this field is 00000000 h |  |

# 7.8.12 Flit Performance Measurement Extended Capability 

This capability is optional. This capability is permitted in Downstream Ports, in Function 0 of an Upstream Port, and in RCRBs. This capability is not permitted in other Functions.

This capability is only used in Flit Mode. The capability has no effect in Non-Flit Mode.
The registers LTSSM Performance Measurement Status 1 Register through LTSSM Performance Measurement Status 5 Register are optional. The number implemented is contained in LTSSM Tracking Register Count. Unimplemented registers do not exist (i.e., the capability becomes shorter than shown in § Figure 7-205)
§ Figure 7-205 details allocation of the register bits in the Flit Performance Measurement Extended Capability structure.
![img-196.jpeg](img-196.jpeg)

Figure 7-205 Flit Performance Measurement Extended Capability Structure

### 7.8.12.1 Flit Performance Measurement Extended Capability Header (Offset 00h)

§ Figure 7-206 details allocation of the register fields in the Flit Performance Measurement Extended Capability Header; § Table 7-188 provides the respective bit definitions.

![img-197.jpeg](img-197.jpeg)

Figure 7-206 Flit Performance Measurement Extended Capability Header

Table 7-188 Flit Performance Measurement Extended Capability Header

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 15:0 | Flit Performance Measurement Extended Capability ID - This field is a PCI-SIG defined ID number that indicates the nature and format of the Extended Capability. <br> The Extended Capability ID for the Flit Performance Measurement Extended Capability is 0033h. | RO |
| 19:16 | Capability Version - This field is a PCI-SIG defined version number that indicates the version of the Capability structure present. <br> Must be 1 h for this version of the specification. | RO |
| $31: 20$ | Next Capability Offset - This field contains the offset to the next PCI Express Capability structure or 000h if no other items exist in the linked list of Capabilities. <br> For Extended Capabilities implemented in Configuration Space, this offset is relative to the beginning of PCI-compatible Configuration Space and thus must always be either 000h (for terminating list of Capabilities) or greater than 0FFh. | RO |

# 7.8.12.2 Flit Performance Measurement Capability Register (Offset 04h) 

![img-198.jpeg](img-198.jpeg)

Figure 7-207 Flit Performance Measurement Capability Register

Table 7-189 Flit Performance Measurement Capability Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| $9: 0$ | Flit Performance Interrupt Vector - contains the MSI or MSI-X Vector number used by this mechanism. <br> If both MSI and MSI-X are implemented, this field is permitted to change value based on which one is <br> enabled. Additionally, when MSI is enabled, this field is permitted to change value based on the value of <br> Multiple Message Enable | RO |
| $12: 10$ | LTSSM Tracking Register Count - Indicates the number of simultaneous LTSSM tracking events that are <br> supported. <br> Value must be between 0 and 5. | HwInit |

# 7.8.12.3 Flit Performance Measurement Control Register (Offset 08h) 

The status register in capability indicates how many events can be simultaneously tracked for the LTSSM state transition tracker. Software must ensure that it does not enable more bits than the Port can enable.

Behavior is undefined if bits 31:1 of this register are changed while Flit Latency Measurement is running (Flit Latency Measurement Enable is 1b and either Flit Response Type is non-zero and Flit Latency Tracking Status is 00b or 01b, or LTSSM State Transition Tracker is non-zero and any of the enabled LTSSM State Transition Tracking Status fields are 00b or 01b).
![img-199.jpeg](img-199.jpeg)

Figure 7-208 Flit Performance Measurement Control Register

Table 7-190 Flit Performance Measurement Control Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 0 | Flit Latency Measurement Enable - Setting this bit to 1b enables and starts measuring the Ack/ Nak/ Replay latency of a Flit. Writing a 0 b to this bit when a measurement is in progress stops the measurement and sets Flit Latency Tracking Status to 10b. Writing this bit to 1b when it is already 1b has no effect. <br> Unit of measurement is 8 ns . <br> Default is Zero. | RW |
| 3:1 | Flit Response Type - Setting the associated bit to 1b enables measuring the Nak to Replay, Flit to Nak, or Flit to Ack latency of a Flit, depending on which bit was written. Behavior is undefined if this field changes value while a measurement is in progress. Behavior is undefined if this field contains a Reserved encoding and Flit Latency Measurement Enable is 1b. | RW |
|  | 001b <br> 010b <br> 100b <br> Others <br> Default is Zero. | Flit to Ack Latency - this measures the time period from sending an original Flit to receiving an Ack for precisely that Flit at the same Link Width. It does not include Flits that were replayed or Flits that were implicitly Ack'ed by receiving the Ack for a subsequent Flit. <br> Flit to Nak Latency - this measures the time period from sending an original Flit to receiving an Nak for precisely that Flit at the same Link Width. It does not include Flits that were replayed or Flits that were implicitly Nak'ed by receiving a Nak for an earlier Flit. <br> Nak to Replay Latency - this measures the time period from sending the first Flit containing a Nak for a given sequence number to receiving the first replay of the requested Flit at the same Link Width <br> Reserved |  |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $5: 4$ | Reserved - This field is permitted to be implemented as either RsvdP or RW with no effects. If implemented as RW, default is Zero. | RsvdP / <br> RW |
| 10:6 | Number of instances to track | RW |
|  | 0 0000b track the worst-case delay |  |
|  | Others track cumulative delay of the indicated number of Flits |  |
|  | Behavior is undefined if this field changes value while a measurement is in progress. |  |
|  | When this field is Zero, measurement completes when Flit Latency Measurement Enable is cleared. When this field is non-Zero, measurement completes when the indicated number of Flits have been tracked. |  |
|  | Default is Zero. |  |
| 13:11 | Interrupt if delay for any tracked Flit exceeds this encoded value | RW |
|  | 000b 000b - do not generate an interrupt |  |
|  | 001b 100 ns |  |
|  | 010b 200 ns |  |
|  | 011b 300 ns |  |
|  | Others Reserved |  |
|  | Behavior is undefined if this field changes value while a measurement is in progress. Default is Zero. |  |
| 18:14 | LTSSM State Transition Tracker - Each bit counts as one independent event: | RW |
|  | Bit 14 L0 to Recovery due to a Framing Error / software directed while in L0. |  |
|  | Bit 15 L0p - Electrical Idle to start of Data Stream on Lane on an upconfig. |  |
|  | Bit 16 L1.0 to L0. |  |
|  | Bit 17 L1.1 to L0. |  |
|  | Bit 18 L1.2 to L0. |  |
|  | Behavior is undefined if the number of bits set in this field is greater than LTSSM Tracking Register Count. Default is Zero. |  |
| 23:19 | Number of instances to track for LTSSM transition | RW |
|  | 0 0000b track the worst-case delay |  |
|  | Others aggregate delay of the number presented here |  |
|  | Default is Zero. |  |
| 26:24 | LTSSM State Transition Tracker Interrupt - Interrupt if any of the events covered by the low 3 bits of LTSSM State Transition Tracker (bits 16:14 of this register) exceeds this encoded value: | RW |
|  | 000b no interrupt generated |  |
|  | 001b 6.4 ms |  |
|  | 010b 12.8 ms |  |
|  | 011b 19.2 ms |  |
|  | Others Reserved |  |
|  | Default is Zero. |  |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 29:27 | LTSSM State Transition Tracker L12 PM Substate Interrupt - Interrupt if any of the events covered by upper 2 bits of LTSSM State Transition Tracker (bits 18:17 of this register) exceeds this value: | RW |
|  | 000b | no interrupt generated |
|  | 001b | 1 sec |
|  | 010b | 2 sec |
|  | 011b | 3 sec |
|  | 100b | 4 sec |
|  | 101b | 5 sec |
|  | 110b | 10 sec |
|  | 111b | Reserved |
|  | Default is Zero. |  |

# 7.8.12.4 Flit Performance Measurement Status Register (Offset 0Ch) 

![img-200.jpeg](img-200.jpeg)

Figure 7-209 Flit Performance Measurement Status Register

Table 7-191 Flit Performance Measurement Status Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $1: 0$ | Flit Latency Tracking Status |  |
|  | 00b | Not started |
|  | 01b | Started |
|  | 10b | Completed |
|  | 11b | Completed with Error (counter overflow) |
|  | Default is Zero. |  |
| $6: 2$ | Flit Latency Tracking - This field indicates the exact number of Flits which have been tracked and recorded in Flit Latency Tracking Counter. This field does not roll over. |  |
|  | When Number of instances to track is non-Zero, this field will be less than or equal to Number of instances to track. |  |
|  | When Number of instances to track is Zero, this field may contain any value. |  |
|  | If Flit Latency Tracking Status is 11b, this field is undefined. |  |
|  | Default is Zero. |  |
| 7 | Interrupt generated based on trigger event - this bit is Set to 1b if an interrupt is generated based on the trigger event count due to Flit Latency Tracking. While this bit is Set to 1b, no new interrupts will be generated based on the trigger event. | RW1C |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | Default is Zero. |  |
| 23:8 | Flit Latency Tracking Counter <br> If Number of instances to track is non-Zero, this field contains the sum of the latency values measures for the tracked Flits. Software can divide this value by the Flit Latency Tracking field to compute the average latency. <br> If Number of instances to track is Zero, this field contains the largest latency measured for the tracked Flits. <br> If Flit Latency Tracking Status is 11b, this field is undefined. <br> The measurement unit is $8 \mathrm{~ns}{ }^{191}$. <br> Default is Zero. | RO |

# IMPLEMENTATION NOTE: FLIT PERFORMANCE MEASUREMENT OPERATION 5 

Flit Performance Measurement allows software to measure the Link Latency for the selected Flit types. These measurements reflect the timer period from when the tracked Flit is sent to when the tracking complete Flit is received. It is strongly recommended that these two events be consistent with each other (e.g., measure from when the first bit of a Flit was transmitted to when the first bit of a Flit was received). When performing a measurement, software should disable Link width changes by configuring Target Link Width and Hardware Autonomous Width Disable. Not doing this can result in inaccurate measurement values.

### 7.8.12.5 LTSSM Performance Measurement Status Register (Offsets 10h to 20h)

Up to 5 instances of the following register are supported. Each register instance supports measurement of one LTSSM state transition tracking. If multiple entries are supported the order of association is based on the bits being enabled in the control register. Software must not enable additional bits for LTSSM state transition tracking while measurement of some events in that category is in progress.
![img-201.jpeg](img-201.jpeg)

Figure 7-210 LTSSM Performance Measurement Status Register

Table 7-192 LTSSM Performance Measurement Status Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| $1: 0$ | LTSSM State Transition Tracking Status | ROS |

[^0]
[^0]:    191. Earlier versions of this specification had incorrect values for the measurement unit (either $64 \mu \mathrm{~s}$ or $8 \mu \mathrm{~s}$ depending on version). Since expected latency is much lower software can detect such implementations by noticing this value contains Zero.

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | 00b <br> 01b <br> 10b <br> 11b <br> Cleared on 0b to 1b transition of Flit Latency Measurement Enable. Default is Zero. |  |
| 6:2 | LTSSM State Transition Tracking - number of LTSSM state transitions of the measured type tracked so far. <br> This number does not roll over. <br> Cleared on 0b to 1b transition of Flit Latency Measurement Enable. <br> Default is Zero. | ROS |
| 7 | Interrupt generated based on trigger event count due to LTSSM State Transition Tracking - this bit is Set when an interrupt is generated based on the trigger event. While this bit is Set, no new interrupts will be generated based on the trigger event. <br> Default is Zero. | RW1CS |
| 23:8 | LTSSM State Transition Tracking Counter <br> The measurement unit is 64 usec. <br> Cleared on 0b to 1b transition of Flit Latency Measurement Enable. <br> Default is Zero. | ROS |

# 7.8.13 Flit Error Injection Extended Capability 

This capability is optional. This capability is permitted in Downstream Ports, in Function 0 of an Upstream Port, and in RCRBs. This capability is not permitted in other Functions.

This capability is only used in Flit Mode. The capability has no effect in Non-Flit Mode.
§ Figure 7-211 details allocation of the register bits in the Flit Error Injection Extended Capability structure.

![img-202.jpeg](img-202.jpeg)

Figure 7-211 Flit Error Injection Extended Capability Structure

# 7.8.13.1 Flit Error Injection Extended Capability Header (Offset 00h) 

\$ Figure 7-212 details allocation of the register fields in the Flit Error Injection Extended Capability Header; \$ Table 7-193 provides the respective bit definitions.
![img-203.jpeg](img-203.jpeg)

Figure 7-212 Flit Error Injection Extended Capability Header

Table 7-193 Flit Error Injection Extended Capability Header

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 15:0 | Flit Error Injection Extended Capability ID - This field is a PCI-SIG defined ID number that indicates the nature and format of the Extended Capability. <br> The Extended Capability ID for the Flit Error Injection Extended Capability is 0034h. | RO |
| 19:16 | Capability Version - This field is a PCI-SIG defined version number that indicates the version of the Capability structure present. <br> Must be 1 h for this version of the specification. | RO |

| Bit Location | Register Description | Attributes |
| :-- | :-- | :--: |
| $31: 20$ | Next Capability Offset - This field contains the offset to the next PCI Express Capability structure or 000h <br> if no other items exist in the linked list of Capabilities. | RO |
|  | For Extended Capabilities implemented in Configuration Space, this offset is relative to the beginning of <br> PCI-compatible Configuration Space and thus must always be either 000h (for terminating list of <br> Capabilities) or greater than 0FFh. |  |

# 7.8.13.2 Flit Error Injection Capability Register (Offset 04h) 

![img-204.jpeg](img-204.jpeg)

Figure 7-213 Flit Error Injection Capability Register

Table 7-194 Flit Error Injection Capability Register

| Bit Location | Register Description | Attributes |
| :-- | :-- | :--: |
| $31: 0$ | Reserved | RsvdP |

### 7.8.13.3 Flit Error Injection Control 1 Register (Offset 08h)

Link level, optional register, both on Tx side as well as Rx side. Behavior is undefined if bits 31:1 of this register change value when error injection is running (Flit Error Injection Enable is 1b and Flit Error Injection Status is 00b or 01b).
![img-205.jpeg](img-205.jpeg)

Figure 7-214 Flit Error Injection Control 1 Register

Table 7-195 Flit Error Injection Control 1 Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 0 | Flit Error Injection Enable - Setting this bit enables and starts the error injection in the Link. Clearing to <br> this bit stops the error injection. | RW |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | Default Zero. |  |
| 1 | Inject Errors on Transmitted Flits - Setting this bit to 1b enables error injection in the Transmitted Flits. A Port that does not implement this functionality must hardwire this bit to 0 b. Default is Zero. | RW |
| 2 | Inject Errors on Received Flits - Setting this bit enables error injection in the Received Flits. A Port is permitted to not inject the exact error described but mimic an error injection effect to achieve the desired effect such as logging FEC-correctable errors or causing NAKs after CRC check. A Port that does not implement this functionality must hardwire this bit to 0 b. Default is Zero. | RW |
| $15: 3$ | Flit Error Injection Enable Data Rate - These bits enable the Flit error injection for the corresponding data rates when enabled | $\begin{aligned} & \text { RW / } \\ & \text { RsvdP } \end{aligned}$ |
|  | Bit 3 | $2.5 \mathrm{GT} / \mathrm{s}$ |
|  | Bit 4 | $5.0 \mathrm{GT} / \mathrm{s}$ |
|  | Bit 5 | $8.0 \mathrm{GT} / \mathrm{s}$ |
|  | Bit 6 | $16.0 \mathrm{GT} / \mathrm{s}$ |
|  | Bit 7 | $32.0 \mathrm{GT} / \mathrm{s}$ |
|  | Bit 8 | $64.0 \mathrm{GT} / \mathrm{s}$ |
|  | Bits 15:9 | RsvdP |
|  | Default is Zero. |  |
| $20: 16$ | Number of Errors Injected - This represents the number of errors to be injected on the Transmitted and/or Received Flits independently. A value of 0 indicates that error injection continues till the injection mechanism is disabled. <br> Default is Zero. | RW |
| $28: 21$ | Spacing Between Injected Errors - This represents the next Flit on which error will be injected after the current sequence of Flit error injection completes. A non-0 value indicates the exact number of Flits after which the error is injected; a 0 value will inject the errors after a pseudo-random number of Flits between 1 to 127, chosen with equal probability. This is used on the Transmit and/or Received side independently. <br> Default is Zero. | RW |
| $31: 29$ | Injection on Flit Type - | RW |
|  | 000b | Inject on any Flit Type |
|  | 001b | Inject on any non-IDLE Flit |
|  | 010b | Inject only on Payload Flit |
|  | 011b | Inject only on NOP Flit |
|  | 100b | Inject only on IDLE Flit |
|  | 101b | If Error Type Being Injected is 11b, Inject only on a Payload Flit and then subsequently on the same sequence number for the Consecutive Error Injection times. The entire repeat will be considered as one instance of error injection for the purposes of counting towards the number of errors injected. Reserved encoding if Error Type Being Injected is other than 11b. |
|  | 110b | If Error Type Being Injected is 11b, Inject only on a Payload Flit along with subsequent injection on one selected Payload Flit with the same sequence number for Consecutive Error Injection times. Exactly one sequence number is selected for consecutive error injection |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | among all the outstanding Payload Flits injected with FEC-uncorrectable errors. The entire repeat will be considered as one instance of error injection for the purposes of counting towards the number of errors injected. Reserved encoding if Error Type Being Injected is other than 11b. |  |
|  | 111b Reserved |  |
|  | Default is Zero |  |

# 7.8.13.4 Flit Error Injection Control 2 Register (Offset 0Ch) 

Link level, optional register, both on Tx side as well as Rx side. Behavior is undefined if this register changes value when error injection is running (Flit Error Injection Enable is 1b and Flit Error Injection Status is 00b or 01b).
![img-206.jpeg](img-206.jpeg)

Figure 7-215 Flit Error Injection Control 2 Register

Table 7-196 Flit Error Injection Control 2 Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 2:0 | Consecutive Error Injection - The number of consecutive Flits that will be injected with the error, irrespective of the type of Flit on which the error is supposed to be initially injected. For the Injection of Flit Type encoding of 101b and 110b, this field has additional meaning, as described above. Even if multiple consecutive Flits will be injected with an error because of this, the entire sequence will count as one towards the number of errors injected. | RW |
|  | 000b <br> 001b to 110b <br> 111b <br> Default is Zero. | No consecutive error injection |
|  |  | One to six consecutive error injections |
|  |  | A pseudo-random number between 7 and 15, each selected with equal probability |
| 4:3 | Error Type Being Injected - | RW |
|  | 00b Random between FEC-correctable or FEC-uncorrectable |  |
|  | 01b FEC-Correctable error injected only in one FEC group (rotate across the groups in subsequent injections) |  |
|  | 10b FEC-Correctable error injected in all 3 FEC groups simultaneously |  |
|  | 11b FEC-Uncorrectable error injected |  |
|  | Default is Zero. |  |
| 11:5 | Error Offset within Flit - For FEC-correctable error(s): Byte offset within FEC-group where error will be injected. If this value is greater than the number of bytes in the FEC group, an error must be injected on any byte in the FEC-group with equal probability using a pseudo-random number generator. | RW |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | For uncorrectable error(s): Distance between subsequent injected error bytes with the initial starting position at byte 0 . If at least 8 bytes have not been injected with an error, the Port must inject errors in some of the FEC bytes to get to 8 bytes in error. <br> Default is Zero. |  |
| 19:12 | Error Magnitude - magnitude of error injected in each byte where error has been injected <br> 00h <br> Others <br> Default is Zero. | RW |

# 7.8.13.5 Flit Error Injection Status Register (Offset 10h) 

![img-207.jpeg](img-207.jpeg)

Figure 7-216 Flit Error Injection Status Register

Table 7-197 Flit Error Injection Status Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 1:0 | Flit Error Tx Injection Status |  |
|  | 00b | Not injected any error yet |
|  | 01b | At least one error is injected, but not completed |
|  | 10b | Error injection completed |
|  | 11b | Error case - error injection aborted, either Flit Error Injection Enable was cleared while injection was incomplete or optionally Flit Error Injection Control 1 [31:1] or Flit Error Injection Control 2 was changed while Injection was enabled and not complete. |
|  | This field is cleared on the 0 b to 1 b transition of Flit Error Injection Enable. Default is Zero. |  |
| 3:2 | Flit Error Rx Injection Status |  |
|  | 00b | Not injected any error yet |
|  | 01b | At least one error is injected, but not completed |
|  | 10b | Error injection completed |
|  | 11b | Error case - error injection aborted, either Flit Error Injection Enable was cleared while injection was incomplete or optionally Flit Error Injection Control 1 [31:1] or Flit Error Injection Control 2 was changed while Injection was enabled and not complete. |
|  | This field is cleared on the 0 b to 1 b transition of Flit Error Injection Enable. Default is Zero. |  |

# 7.8.13.6 Ordered Set Error Injection Control 1 Register (Offset 14h) 

Link level, optional register, both on Tx side as well as Rx side. A Port that does not implement the functionality must hardwire these bits to 0 b. Behavior is undefined if bits $63: 1$ of this register change value when Ordered Set Injection Enable is Set and Ordered Set Error Injection Status is 00b or 01b.
![img-208.jpeg](img-208.jpeg)

Figure 7-217 Ordered Set Error Injection Control 1 Register

Table 7-198 Ordered Set Error Injection Control 1 Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 0 | Ordered Set Error Injection Enable - Setting this bit enables and starts Error Injection on the Link. Clearing this bit stops the error injection. | RWS |
|  | Behavior is undefined if Ordered Set Error Injection Enable is Set and Inject Errors on Transmitted Ordered Sets and Inject Errors on Received Ordered Sets are both Clear. |  |
|  | Default is Zero. |  |
| 1 | Inject Errors on Transmitted Ordered Sets - Setting this bit to 1b enables error injection in the Transmitted Ordered Sets. A Port that does not implement this functionality must hardwire this bit to 0b. | RWS |
|  | Behavior is undefined if Ordered Set Error Injection Enable, Inject Errors on Transmitted Ordered Sets, and Inject Errors on Received Ordered Sets are all Set. |  |
|  | Default is Zero. |  |
| 2 | Inject Errors on Received Ordered Sets - Setting this bit enables error injection in the Received Ordered Sets. A Port is permitted to not inject the exact error described but treat the Ordered Set as invalid. A Port that does not implement this functionality must hardwire this bit to 0b. | RWS |
|  | Behavior is undefined if Ordered Set Error Injection Enable, Inject Errors on Transmitted Ordered Sets, and Inject Errors on Received Ordered Sets are all Set. |  |
|  | Default is Zero. |  |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $7: 3$ | Number of Errors injected - This represents the number of errors to be injected. A value of 0 indicates that error injection continues till the injection mechanism is disabled. <br> Default is Zero. | RWS |
| $15: 8$ | Spacing Between Injected Errors - This represents the next OS on which error will be injected after the current OS error injection completes. A non-0 value indicates the exact number of OSs after which the error is injected; a 0 value will inject the errors after a pseudo-random number of OSs between 1 to 127, chosen with equal probability. This is used on the Transmit and/or Received side independently. <br> Default is Zero. | RWS |
| 16 | Inject Error on TS0 OS - When Set, injects errors on TS0 OS. | RWS |
| 17 | Inject Error on TS1 OS - When Set, injects errors on TS1 OS. | RWS |
| 18 | Inject Error on TS2 OS - When Set, injects errors on TS2 OS. | RWS |
| 19 | Inject Error on SKP OS - When Set, injects errors on SKP OS. | RWS |
| 20 | Inject Error on EIEOS OS - When Set, injects errors on EIEOS OS. | RWS |
| 21 | Inject Error on EIOS OS - When Set, injects errors on EIOS OS. | RWS |
| 22 | Inject Error on SDS OS - When Set, injects errors on SDS OS. | RWS |
| 23 | Inject Error in Polling State - When Set, injects errors in the Polling LTSSM state. | RWS |
| 24 | Inject Error in Configuration State - When Set, injects errors in the Configuration LTSSM state. | RWS |
| 25 | Inject Error in L0 state - When Set, injects errors in the L0 LTSSM state. | RWS |
| 26 | Inject Error in non-EQ Recovery state, - When Set, injects errors in the Recovery LTSSM states except for the Recovery. Equalization substate. | RWS |
| 27 | Inject Error in Recovery. Equalization Phase 0 and 1 - When Set, injects errors Recovery. Equalization Phase 0 and Phase 1. | RWS |
| 28 | Inject Error in Recovery. Equalization Phase 2 - When Set, injects errors Recovery. Equalization Phase 2. | RWS |
| 29 | Inject Error in Recovery. Equalization Phase 3 - When Set, injects errors Recovery. Equalization Phase 3. | RWS |

# 7.8.13.7 Ordered Set Error Injection Control 2 Register (Offset 18h) 

![img-209.jpeg](img-209.jpeg)

Figure 7-218 Ordered Set Error Injection Control 2 Register

Table 7-199 Ordered Set Error Injection Control 2 Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| $15: 0$ | Error Injection Bytes - Individual bytes where errors (any magnitude) will be injected; all 0s indicates a <br> byte will be chosen based on a pseudo-random generator between 1 and 16. For SKP OS, each bit covers <br> 2.5 Bytes instead of one byte | RWS |
| $31: 16$ | Lane Number for Error Injection - A value of 1 b in one or more bit positions indicates that the <br> corresponding Lane number will participate in error injection when enabled. Bit 0 of this field <br> corresponds to Lane 0. | RWS |

# 7.8.13.8 Ordered Set Error Tx Injection Status Register (Offset 1Ch) 

This register contains a set of fields for Tx Ordered Set Error Injection. The description for Tx Injection Status TS0 applies to all fields in this register.
![img-210.jpeg](img-210.jpeg)

Figure 7-219 Ordered Set Tx Error Injection Status Register

Table 7-200 Ordered Set Tx Error Injection Status Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $1: 0$ | Tx Injection Status TS0- Each two bit field is encoded as follows: | ROS |
|  | 00b Not injected any error yet |  |
|  | 01b | At least one error is injected, but not completed |
|  | 10b | Error injection completed |
|  | 11b | Error case - error injection aborted, either Ordered Set Error Injection Enable was cleared <br> while injection was incomplete or optionally any bit in Ordered Set Error Injection Control <br> 1[31:1] or Ordered Set Injection Control 2 was changed while Injection was enabled and <br> not complete. |
|  | This field is cleared on the 0 b to 1 b transition of Ordered Set Error Injection Enable. |  |
|  | Default is 00b. |  |
| $3: 2$ | Tx Injection Status TS1 | ROS |

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| $5: 4$ | Tx Injection Status TS2 | ROS |
| $7: 6$ | Tx Injection Status SKP | ROS |
| $9: 8$ | Tx Injection Status EIEOS | ROS |
| $11: 10$ | Tx Injection Status EIOS | ROS |
| $13: 12$ | Tx Injection Status SDS | ROS |
| $15: 14$ | Tx Injection Status Polling | ROS |
| $17: 16$ | Tx Injection Status Configuration | ROS |
| $19: 18$ | Tx Injection Status LO | ROS |
| $21: 20$ | Tx Injection Status non-EQ Recovery | ROS |
| $23: 22$ | Tx Injection Status Recovery.Equalization Phase 0 and 1 | ROS |
| $25: 24$ | Tx Injection Status Recovery.Equalization Phase 2 | ROS |
| $27: 26$ | Tx Injection Status Recovery.Equalization Phase 3 | ROS |

# 7.8.13.9 Ordered Set Error Rx Injection Status Register (Offset 20h) 

This register contains a set of fields for Rx Ordered Set Error Injection. The description for Rx Injection Status TS0 applies to all fields in this register.
![img-211.jpeg](img-211.jpeg)

Figure 7-220 Ordered Set Rx Error Injection Status Register

Table 7-201 Ordered Set Rx Error Injection Status Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| $1: 0$ | Rx Injection Status TS0 - Each two bit field is encoded as follows: | ROS |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | 00b <br> 01b <br> 10b <br> 11b | Not injected any error yet <br> At least one error is injected, but not completed <br> Error injection completed <br> Error case - error injection aborted, either Ordered Set Error Injection Enable was cleared while injection was incomplete or optionally any bit in Ordered Set Error Injection Control 1[31:1] or Ordered Set Injection Control 2 was changed while Injection was enabled and not complete. <br> This field is cleared on the 0b to 1b transition of Ordered Set Error Injection Enable. <br> Default is 00b. |
| 3:2 | Rx Injection Status TS1 | ROS |
| 5:4 | Rx Injection Status TS2 | ROS |
| 7:6 | Rx Injection Status SKP | ROS |
| 9:8 | Rx Injection Status EIEOS | ROS |
| 11:10 | Rx Injection Status EIOS | ROS |
| 13:12 | Rx Injection Status SDS | ROS |
| 15:14 | Rx Injection Status Polling | ROS |
| 17:16 | Rx Injection Status Configuration | ROS |
| 19:18 | Rx Injection Status LO | ROS |
| 21:20 | Rx Injection Status non-EQ Recovery | ROS |
| 23:22 | Rx Injection Status Recovery. Equalization Phase 0 and 1 | ROS |
| 25:24 | Rx Injection Status Recovery. Equalization Phase 2 | ROS |
| 27:26 | Rx Injection Status Recovery. Equalization Phase 3 | ROS |

# 7.8.14 NOP Flit Extended Capability 

The NOP Flit Extended Capability is an optional Extended Capability that provides control over NOP Flit usage by a transmitting port.

This capability is permitted in Downstream Ports, in Function 0 of an Upstream Port, and in RCRBs. This capability is not permitted in other Functions.

VFs must not implement this capability.
The NOP Flit Extended Capability structure is shown in § Figure 7-221.

![img-212.jpeg](img-212.jpeg)

Figure 7-221 NOP Flit Extended Capability

# 7.8.14.1 NOP Flit Extended Capability Header 

\$ Figure 7-222 details allocation of register fields in the NOP Flit Extended Capability Header; $\S$ Table 7-202 provides the respective bit definitions.
![img-213.jpeg](img-213.jpeg)

Figure 7-222 NOP Flit Extended Capability Header

Table 7-202 NOP Flit Extended Capability Header

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $15: 0$ | PCI Express Extended Capability ID - This field is a PCI-SIG defined ID number that indicates the nature and format of the Extended Capability. <br> Extended Capability ID for the NOP Flit Extended Capability is 0037h. | HwInit |
| $19: 16$ | Capability Version - This field is a PCI-SIG defined version number that indicates the version of the Capability structure present. <br> Must be 1 h. | HwInit |
| $31: 20$ | Next Capability Offset - This field contains the offset to the next PCI Express Capability structure or 000h if no other items exist in the linked list of Capabilities. <br> For Extended Capabilities implemented in Configuration Space, this offset is relative to the beginning of PCI-compatible Configuration Space and thus must always be either 000 h (for terminating list of Capabilities) or greater than 0FFh. | HwInit |

# 7.8.14.2 NOP Flit Capabilities Register 

§ Figure 7-223 details allocation of register fields in the NOP Flit Capabilities Register; § Table 7-203 provides the respective bit definitions.
![img-214.jpeg](img-214.jpeg)

Figure 7-223 NOP Flit Capabilites Register

Table 7-203 NOP Flit Capabilites Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :-- |
| 0 | NOP.Debug TX Support - Indicates transmitter support for sending NOP.Debug Flits | HwInit |
| 1 | NOP.Vendor TX Support - Indicates transmitter support for sending NOP.Vendor Flits | HwInit |

### 7.8.14.3 NOP Flit Control 1 Register

§ Figure 7-224 details allocation of register fields in the NOP Flit Control 1 Register; § Table 7-204 provides the respective bit definitions.
![img-215.jpeg](img-215.jpeg)

Figure 7-224 NOP Flit Control 1 Register

Table 7-204 NOP Flit Control 1 Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :-- |
| 0 | NOP.Debug TX Enable - When Set, this bit enables capable transmitters of sending NOP.Debug Flits. <br> When Clear, the transmitter must not send any NOP.Debug Flits. | RWS / <br> RsvdP |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 1 | This bit is RsvdP when the NOP.Debug TX Support bit is Clear. <br> Default value of this bit is implementation specific. |  |
|  | NOP.Vendor TX Enable - When Set, this bit enables capable transmitters of sending NOP.Vendor Flits. When Clear, the transmitter must not send any NOP.Vendor Flits. <br> This bit is RsvdP when the NOP.Vendor TX Support bit is Clear. <br> Default value of this bit is implementation specific. | RWS / RsvdP |
| 8:2 | Debug Opcodes Enable - When the NOP.Debug TX Enable bit is Set, this field controls which PCI-SIG defined Debug Opcodes may be sent by the transmitter. If this field is Zero, the transmitter may send any PCI-SIG defined Debug Opcode; otherwise, the transmitter may only send the PCI-SIG defined Debug Opcode encoding programmed into this field. Control over non-PCI-SIG defined Debug Opcodes is vendor specific. <br> This bit is RsvdP when the NOP.Debug TX Support bit is Clear. <br> Default value of this field is Zero. | RWS / RsvdP |
| 13:10 | Debug Flit Maximum Rate Hint - Controls the desired maximum rate of NOP.Debug Flit injection by the transmitter for periodic Debug Opcodes not triggered by hardware events. Non-periodic NOP.Debug Flits that are triggered by hardware events are not limited by this setting and may be scheduled independently. A transmitter is permitted to inject at a lower or higher rate than the maximum rate in this field. <br> Defined encodings are: | RWS / RsvdP |
|  | 0h Link rate (one every Flit) |  |
|  | 1h Link rate / 2 (one every two Flits) |  |
|  | 2h Link rate / 3 (one every three Flits) |  |
|  | 3h Link rate / 4 (one every four Flits) |  |
|  | 4h Link rate / 5 (one every five Flits) |  |
|  | 5h Link rate / 6 (one every six Flits) |  |
|  | 6h Link rate / 7 (one every seven Flits) |  |
|  | 7h Link rate / 8 (one every eight Flits) |  |
|  | 8h Link rate / 9 (one every nine Flits) |  |
|  | 9h Link rate / 10 (one every ten Flits) |  |
|  | Others All other encodings are Reserved. <br> This field is RsvdP when the NOP.Debug TX Support bit is Clear. <br> Default value of this field is 3 h . |  |
| 23:16 | Number of NOP Streams - When either or both the NOP.Debug TX Enable bit or the NOP.Vendor TX Enable bit are Set, this field controls the number of NOP Stream IDs the Transmitter may use for sending NOP Flits. The field's value is the total number of NOP Streams minus one. A value of 0 indicates support for one NOP Stream. <br> The upper end NOP Stream ID value is defined as NOP Stream ID Start + Number of NOP Streams, with an upper limit of FFh. For example, if the Number of NOP Streams field contains 5 h and the NOP Stream ID Start field contains FEh, the range of Transmitter usable NOP Stream IDs would only be FEh and FFh (i.e., two NOP Stream IDs), even though the Number of NOP Streams field value was programmed to be greater than that. <br> This field is only used when originating NOP Flits and has no effect on forwarding NOP Flits between Ports. | RWS / RsvdP |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 31:24 | NOP Stream ID Start - When either or both the NOP.Debug TX Enable bit or the NOP.Vendor TX Enable bit are Set, this field controls the lower end of the range of NOP Stream IDs that the Transmitter may use for sending NOP Flits. <br> This field is only used when originating NOP Flits and has no effect on forwarding NOP Flits between Ports. <br> This field is RsvdP when the NOP.Vendor TX Support and the NOP.Debug TX Support bits are both Clear. Default value of this field is FFh. | RWS / RsvdP |

# 7.8.14.4 NOP Flit Control 2 Register 

§ Figure 7-225 details allocation of register fields in the NOP Flit Control 2 Register; § Table 7-205 provides the respective bit definitions.
![img-216.jpeg](img-216.jpeg)

Figure 7-225 NOP Flit Control 2 Register

Table 7-205 NOP Flit Control 2 Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 0 | Request NOP.Debug Flits - When NOP.Debug TX Enable is Set, this bit requests NOP.Debug Flits to be <br> initiated by a transmitter. A write of 1 b to this bit initiates the request so that the transmitter samples <br> the Request Priority, the Debug Opcode Requested, the Number of NOP.Debug Flits Requested, and the <br> Vendor ID Requested fields and attempts to fulfill the request on a best effort basis. <br> It is permitted to write 1 b to this bit while simultaneously writing modified values to other fields in <br> this register. The resulting request must use the modified values. <br> Hardware behavior is undefined if this is written while the NOP.Debug Flit Request in Progress bit is <br> Set. <br> This bit will always return 0b when read. <br> This bit is RsvdP when NOP.Debug TX Support is Clear. <br> Default value of this bit is Zero. | RWS / <br> RsvdP (see <br> description) |
| 1 | Request Priority - When the NOP.Debug TX Enable bit is Set, this bit controls the priority of the <br> requested NOP.Debug Flits. If this bit is Set, the transmitter must prioritize the requested NOP.Debug | RWS / <br> RsvdP |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | Flits over any periodic NOP.Debug Flit transmissions. If this bit is Clear, the transmitter need not prioritize the requested NOP.Debug Flits over any periodic NOP.Debug Flit transmissions. <br> This bit is RsvdP when NOP.Debug TX Support is Clear. <br> Default value of this bit is Zero. |  |
| 8:2 | Debug Opcodes Requested - When the NOP.Debug TX Enable bit is Set, this field controls the number of NOP.Debug Flits requested for transmission. <br> This bit is RsvdP when the NOP.Debug TX Support bit is Clear. <br> Default value of this field is Zero. | RWS / RsvdP |
| 13:10 | Number of NOP.Debug Flits Requested - When the NOP.Debug TX Enable bit is Set, this field controls the number of NOP.Debug Flits requested for transmission. <br> This bit is RsvdP when the NOP.Debug TX Support bit is Clear. <br> Default value of this field is Zero. | RWS / <br> RsvdP |
| 31:16 | Vendor ID Requested - When the NOP.Debug TX Enable bit is Set, this field controls which Vendor ID associated with the Debug Opcode is requested for transmission. <br> This field is RsvdP when the NOP.Debug TX Support bit is Clear. <br> Default value of this field is Zero. | RWS / <br> RsvdP |

# 7.8.14.5 NOP Flit Status Register 

§ Figure 7-226 details allocation of register fields in the NOP Flit Status Register; § Table 7-206 provides the respective bit definitions.
![img-217.jpeg](img-217.jpeg)

Figure 7-226 NOP Flit Status Register

Table 7-206 NOP Flit Status Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 0 | NOP.Debug Flit Request in Progress - When Set, this bit indicates that the Transmitter has started to fulfill the requested NOP.Debug Flits and that the request has not yet been fully completed. A Transmitter reports this bit Clear only when the request has been fully completed or the request has been cancelled. This bit must also be Cleared when the NOP.Debug TX Enable bit is Cleared. <br> Ports that do not implement the ability to transmit the requested NOP.Debug Flits are permitted to hardwire this bit to 0 b. <br> This bit is RsvdZ when the NOP.Debug TX Support bit is Clear. <br> Default value of this bit is 0 . | RO / <br> RsvdZ |

# 7.9 Additional PCI and PCIe Capabilities 

This section, contains a description of additional PCI and PCIe capabilities that are individually optional in this but may be required by other PCISIG specifications.

### 7.9.1 Virtual Channel Extended Capability

The Virtual Channel Extended Capability (VC Extended Capability) is an optional Extended Capability required for devices that have Ports (or for individual Functions) that support functionality beyond the default Traffic Class (TCO) over the default Virtual Channel (VCO). This may apply to devices with only one VC that support TC filtering or to devices that support multiple VCs. Note that a PCI Express device that supports only TCO over VCO does not require VC Extended Capability and associated registers. § Figure 7-227 provides a high level view of the Virtual Channel Extended Capability structure. This structure controls Virtual Channel assignment for PCI Express Links and may be present in any device (or RCRB) that contains (controls) a Port, or any device that has a Multi-Function Virtual Channel (MFVC) Capability structure. Some registers/fields in the Virtual Channel Extended Capability structure may have different interpretation for Endpoints, Switch Ports, Root Ports and RCRB. Software must interpret the Device/Port Type field in the PCI Express Capabilities register to determine the availability and meaning of these registers/fields.

The number of (extended) Virtual Channels is indicated by the Extended VC Count field in the Port VC Capability Register 1. Software must interpret this field to determine the availability of extended VC Resource registers.

The VC Extended Capability structure is permitted in the Extended Configuration Space of all Single-Function Devices or in RCRBs.

Each VF uses the Virtual Channel of its associated PF. VFs themselves must not contain any Virtual Channel Capabilities.
A Multi-Function Device at an Upstream Port is permitted to contain a Multi-Function Virtual Channel (MFVC) Capability structure (see § Section 7.9.2). If a Multi-Function Device contains an MFVC Capability structure, any or all of its Functions with the exception of VFs are permitted to contain a VC Extended Capability structure. Per-Function VC Extended Capability structures are also permitted for devices inside a Switch that contain only Switch Downstream Port Functions, or for RCIEPs. Otherwise, only Function 0 is permitted to contain a VC Extended Capability structure.

To preserve software backward compatibility, two Extended Capability IDs are permitted for VC Extended Capability structures: 0002h and 0009h. Any VC Extended Capability structure in a device that also contains an MFVC Capability structure must use the Extended Capability ID 0009h. A VC Extended Capability structure in a device that does not contain an MFVC Capability structure must use the Extended Capability ID 0002h.
![img-218.jpeg](img-218.jpeg)

Figure 7-227 Virtual Channel Extended Capability Structure

The following sections describe the registers/fields of the Virtual Channel Extended Capability structure.

# 7.9.1.1 Virtual Channel Extended Capability Header (Offset 00h) 

Refer to § Section 7.6.3 for a description of the PCI Express Extended Capability header. A Virtual Channel Extended Capability must use one of two Extended Capability IDs: 0002 h or 0009 h. Refer to § Section 7.9.1 for rules governing when each should be used. § Figure 7-228 details allocation of register fields in the Virtual Channel Extended Capability Header; § Table 7-207 provides the respective bit definitions.
![img-219.jpeg](img-219.jpeg)

Figure 7-228 Virtual Channel Extended Capability Header

Table 7-207 Virtual Channel Extended Capability Header

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $15: 0$ | PCI Express Extended Capability ID - This field is a PCI-SIG defined ID number that indicates the nature and format of the Extended Capability. <br> Extended Capability ID for the Virtual Channel Extended Capability is either 0002h or 0009h. | RO |
| $19: 16$ | Capability Version - This field is a PCI-SIG defined version number that indicates the version of the Capability structure present. <br> Must be 1 h for this version of the specification. | RO |
| $31: 20$ | Next Capability Offset - This field contains the offset to the next PCI Express Capability structure or 000h if no other items exist in the linked list of Capabilities. <br> For Extended Capabilities implemented in Configuration Space, this offset is relative to the beginning of PCI-compatible Configuration Space and thus must always be either 000 h (for terminating list of Capabilities) or greater than 0FFh. | RO |

### 7.9.1.2 Port VC Capability Register 1 (Offset 04h)

The Port VC Capability Register 1 describes the configuration of the Virtual Channels associated with a PCI Express Port. § Figure 7-229 details allocation of register fields in the Port VC Capability Register 1; § Table 7-208 provides the respective bit definitions.

![img-220.jpeg](img-220.jpeg)

Figure 7-229 Port VC Capability Register 1

Table 7-208 Port VC Capability Register 1

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $2: 0$ | Extended VC Count - Indicates the number of (extended) Virtual Channels in addition to the default VC supported by the device. This field is valid for all Functions. <br> This value indicates the number of (extended) VC Resource Capability, Control, and Status registers that are present in Configuration Space in addition to the required VC Resource registers for the default VC. <br> The minimum value of this field is 0 (for devices that only support the default VC and only have 1 set of VC Resource Registers for that VC). The maximum value is 7 . | RO |
| $6: 4$ | Low Priority Extended VC Count - Indicates the number of (extended) Virtual Channels in addition to the default VC belonging to the low-priority VC (LPVC) group that has the lowest priority with respect to other VC resources in a strict-priority VC Arbitration. This field is valid for all Functions. <br> The minimum value of this field is 000 b and the maximum value is Extended VC Count. | RO |
| $9: 8$ | Reference Clock - Indicates the reference clock for Virtual Channels that support time-based WRR Port Arbitration. This field is valid for RCRBs, Switch Ports, and Root Ports that support peer-to-peer traffic. It is not valid for Root Ports that do not support peer-to-peer traffic, Endpoints, and Switches or Root Complexes not implementing WRR, and must be hardwired to 00b. <br> Defined encodings are: <br> 100 ns reference clock <br> 01b - 11b Reserved | RO |
| $11: 10$ | Port Arbitration Table Entry Size - Indicates the size (in bits) of Port Arbitration table entry in the Function. This field is valid only for RCRBs, Switch Ports, and Root Ports that support peer-to-peer traffic. It is not valid and must be hardwired to 00b for Root Ports that do not support peer-to-peer traffic and Endpoints. <br> Defined encodings are: <br> 00b The size of Port Arbitration table entry is 1 bit. <br> 01b The size of Port Arbitration table entry is 2 bits. <br> 10b The size of Port Arbitration table entry is 4 bits. <br> 11b The size of Port Arbitration table entry is 8 bits. | RO |

# 7.9.1.3 Port VC Capability Register 2 (Offset 08h) 

The Port VC Capability Register 2 provides further information about the configuration of the Virtual Channels associated with a PCI Express Port. § Figure 7-230 details allocation of register fields in the Port VC Capability Register 2; § Table $7-209$ provides the respective bit definitions.
![img-221.jpeg](img-221.jpeg)

Figure 7-230 Port VC Capability Register 2

Table 7-209 Port VC Capability Register 2

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $7: 0$ | VC Arbitration Capability - Indicates the types of VC Arbitration supported by the Function for the LPVC group. This field is valid for all Functions that report a Low Priority Extended VC Count field greater than 0. For all other Functions, this field must be hardwired to 00 h. <br> Each Bit Location within this field corresponds to a VC Arbitration Capability defined below. When more than 1 bit in this field is Set, it indicates that the Port can be configured to provide different VC arbitration services. <br> Defined bit positions are: | RO |
|  | Bit 0 Hardware fixed arbitration scheme, e.g., Round Robin |  |
|  | Bit 1 Weighted Round Robin (WRR) arbitration with 32 phases |  |
|  | Bit 2 WRR arbitration with 64 phases |  |
|  | Bit 3 WRR arbitration with 128 phases |  |
|  | Bits 4-7 | Reserved |
| $31: 24$ | VC Arbitration Table Offset - Indicates the location of the VC Arbitration Table. This field is valid for all Functions. <br> This field contains the zero-based offset of the table in DQWORDS (16 bytes) from the base address of the Virtual Channel Extended Capability structure. A value of 0 indicates that the table is not present. | RO |

### 7.9.1.4 Port VC Control Register (Offset 0Ch)

§ Figure 7-231 details allocation of register fields in the Port VC Control Register; § Table 7-210 provides the respective bit definitions.

![img-222.jpeg](img-222.jpeg)

Figure 7-231 Port VC Control Register 5

Table 7-210 Port VC Control Register 6

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 0 | Load VC Arbitration Table - Used by software to update the VC Arbitration Table. This bit is valid for all Functions when the selected VC Arbitration uses the VC Arbitration Table. <br> Software sets this bit to request hardware to apply new values programmed into VC Arbitration Table; clearing this bit has no effect. Software checks the VC Arbitration Table Status bit to confirm that new values stored in the VC Arbitration Table are latched by the VC arbitration logic. <br> This bit always returns 0b when read. | RW |
| $3: 1$ | VC Arbitration Select - Used by software to configure the VC arbitration by selecting one of the supported VC Arbitration schemes indicated by the VC Arbitration Capability field in the Port VC Capability Register 2. This field is valid for all Functions. <br> The permissible values of this field are numbers corresponding to one of the asserted bits in the VC Arbitration Capability field. <br> This field cannot be modified when more than one VC in the LPVC group is enabled. | RW |
| 4 | All VCs Enabled - Setting this bit indicates that all VCs that will be used by the Port have been enabled. Setting this bit allows hardware to allocate assigned buffer resources across the enabled VCs. <br> Setting this bit is optional. If this bit remains Clear and some VC Resources are never enabled, performance may be affected but the Link and all enabled VCs must operate correctly. <br> Behavior is undefined if this bit is Set and any VC Enable bit in this capability changes value. Default value of this bit is 0 b . | RW |

# 7.9.1.5 Port VC Status Register (Offset 0Eh) 

The Port VC Status Register provides status of the configuration of Virtual Channels associated with a Port. § Figure 7-232 details allocation of register fields in the Port VC Status Register; § Table 7-211 provides the respective bit definitions.

![img-223.jpeg](img-223.jpeg)

Figure 7-232 Port VC Status Register

Table 7-211 Port VC Status Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 0 | VC Arbitration Table Status - Indicates the coherency status of the VC Arbitration Table. This bit is valid <br> for all Functions when the selected VC uses the VC Arbitration Table. <br> This bit is Set by hardware when any entry of the VC Arbitration Table is written by software. This bit is <br> Cleared by hardware when hardware finishes loading values stored in the VC Arbitration Table after <br> software sets the Load VC Arbitration Table bit in the Port VC Control Register. <br> Default value of this bit is 0b. |  |

# 7.9.1.6 VC Resource Capability Register 

The VC Resource Capability Register describes the capabilities and configuration of a particular Virtual Channel resource. \$ Figure 7-233 details allocation of register fields in the VC Resource Capability Register; \$ Table 7-212 provides the respective bit definitions.
![img-224.jpeg](img-224.jpeg)

Figure 7-233 VC Resource Capability Register

Table 7-212 VC Resource Capability Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 7:0 | Port Arbitration Capability - Indicates types of Port Arbitration supported by the VC resource. This field <br> is valid for all Switch Ports, Root Ports that support peer-to-peer traffic, and RCRBs, but not for <br> Endpoints or Root Ports that do not support peer-to-peer traffic. <br> Each Bit Location within this field corresponds to a Port Arbitration Capability defined below. When more <br> than 1 bit in this field is Set, it indicates that the VC resource can be configured to provide different <br> arbitration services. | RO |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | Software selects among these capabilities by writing to the Port Arbitration Select field (see \$ Section 7.9.1.7). |  |
|  | Defined bit positions are: |  |
|  | Bit 0 | Non-configurable hardware-fixed arbitration scheme, e.g., Round Robin (RR) |
|  | Bit 1 | Weighted Round Robin (WRR) arbitration with 32 phases |
|  | Bit 2 | WRR arbitration with 64 phases |
|  | Bit 3 | WRR arbitration with 128 phases |
|  | Bit 4 | Time-based WRR with 128 phases |
|  | Bit 5 | WRR arbitration with 256 phases |
|  | Bits 6-7 | Reserved |
| 14 | Undefined Undefined - The value read from this bit is undefined. In previous versions of this specification, this bit was used to indicate Advanced Packet Switching. System software must ignore the value read from this bit. | RO |
| 15 | Reject Snoop Transactions - When Clear, transactions with or without the No Snoop bit Set within the TLP header are allowed on this VC. When Set, any transaction for which the No Snoop attribute is applicable but is not Set within the TLP header is permitted to be rejected as an Unsupported Request. Refer to $\S$ Section 2.2.6.5 for information on where the No Snoop attribute is applicable. This bit is valid for Root Ports and RCRB; it is not valid for Endpoints or Switch Ports. | HwInit |
| $22: 16$ | Maximum Time Slots - Indicates the maximum number of time slots (minus one) that the VC resource is capable of supporting when it is configured for time-based WRR Port Arbitration. For example, a value 000 0000b in this field indicates the supported maximum number of time slots is 1 and a value of 111 1111b indicates the supported maximum number of time slots is 128 . This field is valid for all Switch Ports, Root Ports that support peer-to-peer traffic, and RCRBs, but is not valid for Endpoints or Root Ports that do not support peer-to-peer traffic. In addition, this field is valid only when the Port Arbitration Capability field indicates that the VC resource supports time-based WRR Port Arbitration. | HwInit |
| $31: 24$ | Port Arbitration Table Offset - Indicates the location of the Port Arbitration Table associated with the VC resource. This field is valid for all Switch Ports, Root Ports that support peer-to-peer traffic, and RCRBs, but is not valid for Endpoints or Root Ports that do not support peer-to-peer traffic. <br> This field contains the zero-based offset of the table in DQWORDS (16 bytes) from the base address of the Virtual Channel Extended Capability structure. A value of 00 h indicates that the table is not present. | RO |

# 7.9.1.7 VC Resource Control Register $\S$ 

§ Figure 7-234 details allocation of register fields in the VC Resource Control Register; § Table 7-213 provides the respective bit definitions.

![img-225.jpeg](img-225.jpeg)

Figure 7-234 VC Resource Control Register

Table 7-213 VC Resource Control Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $7: 0$ | TC/VC Map - This field indicates the TCs that are mapped to the VC resource. This field is valid for all Functions. <br> Bit locations within this field correspond to TC values. For example, when bit 7 is Set in this field, TC7 is mapped to this VC resource. When more than 1 bit in this field is Set, it indicates that multiple TCs are mapped to the VC resource. <br> In order to remove one or more TCs from the TC/VC Map of an enabled VC, software must ensure that no new or outstanding transactions with the TC labels are targeted at the given Link. <br> Default value of this field is FFh for the first VC resource and is 00 h for other VC resources. <br> Note: <br> Bit 0 of this field is read-only. It must be Set for the default VCO and Clear for all other enabled VCs. | RW <br> (see the note for exceptions) |
| 16 | Load Port Arbitration Table - When Set, this bit updates the Port Arbitration logic from the Port Arbitration Table for the VC resource. This bit is valid for all Switch Ports, Root Ports that support peer-to-peer traffic, and RCRBs, but is not valid for Endpoints or Root Ports that do not support peer-to-peer traffic. In addition, this bit is only valid when the Port Arbitration Table is used by the selected Port Arbitration scheme (that is indicated by a Set bit in the Port Arbitration Capability field selected by Port Arbitration Select). <br> Software sets this bit to signal hardware to update Port Arbitration logic with new values stored in Port Arbitration Table; clearing this bit has no effect. Software uses the Port Arbitration Table Status bit to confirm whether the new values of Port Arbitration Table are completely latched by the arbitration logic. <br> This bit always returns 0 b when read. <br> Default value of this bit is Ob. | RW |
| 19:17 | Port Arbitration Select - This field configures the VC resource to provide a particular Port Arbitration service. This field is valid for RCRBs, Root Ports that support peer-to-peer traffic, and Switch Ports, but is not valid for Endpoints or Root Ports that do not support peer-to-peer traffic. <br> The permissible value of this field is a number corresponding to one of the asserted bits in the Port Arbitration Capability field of the VC resource. | RW |
| $26: 24$ | VC ID - This field assigns a VC ID to the VC resource (see note for exceptions). This field is valid for all Functions. <br> This field cannot be modified when the VC is already enabled. <br> Note: <br> For the first VC resource (default VC), this field is read-only and must be hardwired to 000b. | RW |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 29:27 | Shared Flow Control Usage Limit - this field controls what percentage of the available Shared Flow Control a given FC/VC is permitted to consume. <br> This limit is applied independently for each Flow Control credit type. For example, if this field contains 101b and Shared Flow Control Usage Limit Enable is Set, a Posted TLP may not pass the Tx Gate if doing so would cause that VC to consume more than $62.5 \%$ of the available Shared Posted Header credits or if doing so would cause that VC to consume more than $62.5 \%$ of the available Shared Data credits. <br> If Shared Flow Control Usage Limit Enable is Clear, this field is ignored and this VC is permitted to consume all of the shared credits. <br> When Shared Flow Control Usage Limit Enable is Set, and this field contains 000b, this VC is not permitted to consume any shared credits. <br> Behavior is undefined when all VCs have Shared Flow Control Usage Limit Enable Set and the sum of the Shared Flow Control Limit values for all VCs is less than 100\%. <br> Encodings are: | RW / RO / <br> RsvdP |
|  | 000b | $0 \%$ |
|  | 001b | $12.5 \%$ |
|  | 010b | $25 \%$ |
|  | 011b | $37.5 \%$ |
|  | 100b | $50 \%$ |
|  | 101b | $62.5 \%$ |
|  | 110b | $75 \%$ |
|  | 111b | $87.5 \%$ |

Behavior is undefined if this field changes value while VC Enable and Shared Flow Control Usage Limit Enable are both Set.

This field is RsvdP when Flit Mode Supported is Clear.
When Extended VC Count is 0 , this field is permitted to be hardwired to any value.
When this field is RW, the default value is implementation specific.
Shared Flow Control Usage Limit Enable - When Set, this bit enables use of the Shared Flow Control
$R W / R O /$ Usage Limit value above at the transmitter for this Virtual Channel.

Behavior is undefined of the value of this bit changes while VC Enable is Set.
This bit is RsvdP when Flit Mode Supported is Clear.
When Extended VC Count is 0 , this bit is permitted to be hardwired to 0 b.
When this bit is RW, the default value is implementation specific.
VC Enable - This bit, when Set, enables a Virtual Channel. The Virtual Channel is disabled when this bit is cleared. This bit is valid for all Functions.

Software must use the VC Negotiation Pending bit to check whether the VC negotiation is complete.
For VCO, the attribute is RO. If no SVC capability is implemented in this Port, this bit's value must be 1b; otherwise, this bit's value must always be the same value as the Use VC/MFVC bit in the SVC Port Status Register. See $\S$ Section 6.3.5 .

For other VCs, if no SVC capability is implemented in this Port or if the Use VC/MFVC bit is Set, the default value of this bit is 0 b and the attribute is RW; otherwise, this bit must be RO with a value of 0 b .

To enable a Virtual Channel in a Port using VC mechanisms, the VC Enable bit for that Virtual Channel must be Set. The corresponding Virtual Channel in the Link partner Port must be enabled as well, and that Virtual Channel may be in SVC, VC, or MFVC capabilities. To disable a Virtual Channel, Virtual

| Bit Location | Register Description | Attributes |
| :-- | :-- | :-- |
|  | Channel must be disabled in both components on the Link. Software must ensure that no traffic is <br> using a Virtual Channel at the time it is disabled. Software must fully disable a Virtual Channel in both <br> components on a Link before re-enabling the Virtual Channel. |  |
|  | When this bit is forced to be RO with a value of Ob due to the Use VC/MFVC bit being Clear, its associated <br> VC is disabled, rendering most of its control registers to be ineffective. |  |

# 7.9.1.8 VC Resource Status Register $\S$ 

§ Figure 7-235 details allocation of register fields in the VC Resource Status Register; § Table 7-214 provides the respective bit definitions.
![img-226.jpeg](img-226.jpeg)

Figure 7-235 VC Resource Status Register

Table 7-214 VC Resource Status Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 0 | Port Arbitration Table Status - This bit indicates the coherency status of the Port Arbitration Table associated with the VC resource. This bit is valid for RCRBs, Root Ports that support peer-to-peer traffic, and Switch Ports, but is not valid for Endpoints or Root Ports that do not support peer-to-peer traffic. In addition, this bit is valid only when the Port Arbitration Table is used by the selected Port Arbitration for the VC resource. <br> This bit is Set by hardware when any entry of the Port Arbitration Table is written to by software. This bit is Cleared by hardware when hardware finishes loading values stored in the Port Arbitration Table after software sets the Load Port Arbitration Table bit. <br> Default value of this bit is Ob. | RO |
| 1 | VC Negotiation Pending - This bit indicates whether the Virtual Channel negotiation (initialization or disabling) is in pending state. This bit is valid for all Functions. <br> The value of this bit is defined only when the Link is in the DL_Active state and the Virtual Channel is enabled (its VC Enable bit is Set). <br> When this bit is Set by hardware, it indicates that the VC resource has not completed the process of negotiation. This bit is Cleared by hardware after the VC negotiation is complete (on exit from the FC_INIT2 state). For VC0, this bit is permitted to be hardwired to Ob. <br> Before using a Virtual Channel, software must check whether the VC Negotiation Pending bits for that Virtual Channel are Clear in both components on the Link. | RO |

# 7.9.1.9 VC Arbitration Table 

The VC Arbitration Table is a read-write register array that is used to store the arbitration table for VC Arbitration. This register array is valid for all Functions when the selected VC Arbitration uses a WRR table. Functions that do not support WRR VC arbitration are not required to implement a VC Arbitration Table. If it exists, the VC Arbitration Table is located by the VC Arbitration Table Offset field.

The VC Arbitration Table is a register array with fixed-size entries of 4 bits. $\S$ Figure 7-236 depicts the table structure of an example VC Arbitration Table with 32 phases. Each 4-bit table entry corresponds to a phase within a WRR arbitration period. The definition of table entry is depicted in $\S$ Table 7-215. The lower 3 bits (bits 0-2) contain the VC ID value, indicating that the corresponding phase within the WRR arbitration period is assigned to the Virtual Channel indicated by the VC ID (must be a valid VC ID that corresponds to an enabled VC).

The highest bit (bit 3) of the table entry is Reserved. The length of the table depends on the selected VC Arbitration as shown in § Table 7-216.

When the VC Arbitration Table is used by the default VC Arbitration method, the default values of the table entries must be all zero to ensure forward progress for the default VC (with VC ID of 0 ).
![img-227.jpeg](img-227.jpeg)

Figure 7-236 Example VC Arbitration Table with 32 Phases

Table 7-215 Definition of the 4-bit Entries in the VC Arbitration Table

| Bit Location | Description | Attributes |
| :--: | :-- | :-- |
| $2: 0$ | VC ID | RW |
| 3 | RsvdP | RW |

Table 7-216 Length of the VC Arbitration Table
VC Arbitration Select VC Arbitration Table Length

| 001 b | 32 entries |
| :--: | :-- |
| 010 b | 64 entries |
| 011 b | 128 entries |

### 7.9.1.10 Port Arbitration Table

The Port Arbitration Table register is a read-write register array that is used to store the WRR or time-based WRR arbitration table for Port Arbitration for the VC resource. This register array is valid for all Switch Ports, Root Ports that support peer-to-peer traffic, and RCRBs, but is not valid for Endpoints or Root Ports that do not support peer-to-peer traffic. It is only present when one or more asserted bits in the Port Arbitration Capability field indicate that the component

supports a Port Arbitration scheme that uses a programmable arbitration table. Furthermore, it is only valid when one of the above-mentioned bits in the Port Arbitration Capability field is selected by the Port Arbitration Select field.

The Port Arbitration Table represents one Port arbitration period. § Figure 7-237 shows the structure of an example Port Arbitration Table with 128 phases and 2-bit table entries. Each table entry containing a Port Number corresponds to a phase within a Port arbitration period. For example, a table with 2-bit entries can be used by a Switch component with up to four Ports. A Port Number written to a table entry indicates that the phase within the Port Arbitration period is assigned to the selected PCI Express Port (the Port Number must be a valid one).

- When the WRR Port Arbitration is used for a VC of any Egress Port, at each arbitration phase, the Port Arbiter serves one transaction from the Ingress Port indicated by the Port Number of the current phase. When finished, it immediately advances to the next phase. A phase is skipped, i.e., the Port Arbiter simply moves to the next phase immediately if the Ingress Port indicated by the phase does not contain any transaction for the VC (note that a phase cannot contain the Egress Port's Port Number).
- When the Time-based WRR Port Arbitration is used for a VC of any given Port, at each arbitration phase aligning to a virtual timeslot, the Port Arbiter serves one transaction from the Ingress Port indicated by the Port Number of the current phase. It advances to the next phase at the next virtual timeslot. A phase indicates an "idle" timeslot, i.e., the Port Arbiter does not serve any transaction during the phase, if:
- the phase contains the Egress Port's Port Number, or
- the Ingress Port indicated by the phase does not contain any transaction for the VC.
- The Port Arbitration Table Entry Size field in the Port VC Capability Register 1 determines the table entry size. The length of the table is determined by the Port Arbitration Select field as shown in § Table 7-217.
- When the Port Arbitration Table is used by the default Port Arbitration for the default VC, the default values for the table entries must contain at least one entry for each of the other PCI Express Ports of the component to ensure forward progress for the default VC for each Port. The table may contain RR or RR-like fair Port Arbitration for the default VC.
![img-228.jpeg](img-228.jpeg)

Figure 7-237 Example Port Arbitration Table with 128 Phases and 2-bit Table Entries

Table 7-217 Length of Port Arbitration Table

| Port Arbitration Select | Port Arbitration Table Length |
| :--: | :--: |
| 001b | 32 entries |
| 010b | 64 entries |
| 011b | 128 entries |
| 100b | 128 entries |
| 101b | 256 entries |

# 7.9.2 Multi-Function Virtual Channel Extended Capability 

The Multi-Function Virtual Channel Extended Capability (MFVC Capability) is an optional Extended Capability that permits enhanced QoS management in a Multi-Function Device, including TC/VC mapping, optional VC arbitration, and optional Function arbitration for Upstream Requests. When implemented, the MFVC Extended Capability structure must be present in the Extended Configuration Space of Function 0 of the Multi-Function Device's Upstream Port. § Figure 7-238 provides a high level view of the MFVC Extended Capability structure. This MFVC Extended Capability structure controls Virtual Channel assignment at the PCI Express Upstream Port of the Multi-Function Device, while a VC Extended Capability structure, if present in a Function, controls the Virtual Channel assignment for that individual Function.

The number of (extended) Virtual Channels is indicated by the MFVC Extended VC Count field in the Port VC Capability Register 1. Software must interpret this field to determine the availability of extended MFVC VC Resource registers.

A Multi-Function Device is permitted to have an MFVC Extended Capability structure even if none of its Functions have a VC Extended Capability structure. However, an MFVC Extended Capability structure is permitted only in Function 0 in the Upstream Port of a Multi-Function Device.
![img-229.jpeg](img-229.jpeg)

Figure 7-238 MFVC Capability Structure

The following sections describe the registers/fields of the MFVC Extended Capability structure.

### 7.9.2.1 MFVC Extended Capability Header (Offset 00h)

Refer to § Section 7.6.3 for a description of the PCI Express Extended Capability header. The Extended Capability ID for the MFVC Extended Capability is 0008h. § Figure 7-239 details allocation of register fields in the MFVC Extended Capability header; $\S$ Table 7-218 provides the respective bit definitions.
![img-230.jpeg](img-230.jpeg)

Figure 7-239 MFVC Extended Capability Header

Table 7-218 MFVC Extended Capability Header

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $15: 0$ | PCI Express Extended Capability ID - This field is a PCI-SIG defined ID number that indicates the nature <br> and format of the Extended Capability. <br> The Extended Capability ID for the MFVC Extended Capability is 0008h. | RO |
| $19: 16$ | Capability Version - This field is a PCI-SIG defined version number that indicates the version of the <br> Capability structure present. <br> Must be 1 h for this version of the specification. | RO |
| $31: 20$ | Next Capability Offset - This field contains the offset to the next PCI Express Capability structure or 000h <br> if no other items exist in the linked list of Capabilities. <br> For Extended Capabilities implemented in Configuration Space, this offset is relative to the beginning of <br> PCI-compatible Configuration Space and thus must always be either 000h (for terminating list of <br> Capabilities) or greater than 0FFh. | RO |

# 7.9.2.2 MFVC Port VC Capability Register 1 (Offset 04h) 

The MFVC Port VC Capability Register 1 describes the configuration of the Virtual Channels associated with a PCI Express Port of the Multi-Function Device. § Figure 7-240 details allocation of register fields in the MFVC Port VC Capability Register 1; § Table 7-219 provides the respective bit definitions.
![img-231.jpeg](img-231.jpeg)

Figure 7-240 MFVC Port VC Capability Register 1

Table 7-219 MFVC Port VC Capability Register 1

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $2: 0$ | Extended VC Count - Indicates the number of (extended) Virtual Channels in addition to the default VC <br> supported by the device. <br> This value indicates the number of (extended) MFVC VC Resource Capability, Control, and Status <br> registers that are present in Configuration Space in addition to the required MFVC VC Resource registers <br> for the default VC. <br> The minimum value of this field is 0 (for devices that only support the default VC and only have 1 set of <br> MFVC VC Resource registers for that VC). The maximum value is 7 . | RO |
| $6: 4$ | Low Priority Extended VC Count - Indicates the number of (extended) Virtual Channels in addition to <br> the default VC belonging to the low-priority VC (LPVC) group that has the lowest priority with respect to <br> other VC resources in a strict-priority VC Arbitration. <br> The minimum value of this field is 000 b and the maximum value is Extended VC Count. | RO |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $9: 8$ | Reference Clock - Indicates the reference clock for Virtual Channels that support time-based WRR <br> Function Arbitration. <br> Defined encodings are: <br> 00b 100 ns reference clock <br> 01b - 11b Reserved | RO |
| 11:10 | Function Arbitration Table Entry Size - Indicates the size (in bits) of Function Arbitration table entry in <br> the device. <br> Defined encodings are: <br> 00b Size of Function Arbitration table entry is 1 bit <br> 01b Size of Function Arbitration table entry is 2 bits <br> 10b Size of Function Arbitration table entry is 4 bits <br> 11b Size of Function Arbitration table entry is 8 bits | RO |

# 7.9.2.3 MFVC Port VC Capability Register 2 (Offset 08h) 

The MFVC Port VC Capability Register 2 provides further information about the configuration of the Virtual Channels associated with a PCI Express Port of the Multi-Function Device. § Figure 7-241 details allocation of register fields in the MFVC Port VC Capability Register 2; § Table 7-220 provides the respective bit definitions.
![img-232.jpeg](img-232.jpeg)

Figure 7-241 MFVC Port VC Capability Register 2

Table 7-220 MFVC Port VC Capability Register 2

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $7: 0$ | VC Arbitration Capability - Indicates the types of VC Arbitration supported by the device for the LPVC <br> group. This field is valid for all devices that report a Low Priority Extended VC Count greater than 0. <br> Each Bit Location within this field corresponds to a VC Arbitration Capability defined below. When more <br> than 1 bit in this field is Set, it indicates that the device can be configured to provide different VC <br> arbitration services. <br> Defined bit positions are: | RO |
|  | Bit 0 Hardware fixed arbitration scheme, e.g., Round Robin |  |
|  | Bit 1 Weighted Round Robin (WRR) arbitration with 32 phases |  |
|  | Bit 2 WRR arbitration with 64 phases |  |
|  | Bit 3 WRR arbitration with 128 phases |  |
|  | Bits 4-7 Reserved |  |

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| $31: 24$ | VC Arbitration Table Offset - Indicates the location of the MFVC VC Arbitration Table. | RO |
|  | This field contains the zero-based offset of the table in DQWORDS (16 bytes) from the base address of <br> the MFVC Extended Capability structure. A value of 00 h indicates that the table is not present. |  |

# 7.9.2.4 MFVC Port VC Control Register (Offset 0Ch) 

§ Figure 7-242 details allocation of register fields in the Port VC Control register; § Table 7-221 provides the respective bit definitions.
![img-233.jpeg](img-233.jpeg)

Figure 7-242 MFVC Port VC Control Register

Table 7-221 MFVC Port VC Control Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 0 | Load VC Arbitration Table - Used by software to update the MFVC VC Arbitration Table. This bit is valid <br> when the selected VC Arbitration uses the MFVC VC Arbitration Table. <br> Software Sets this bit to request hardware to apply new values programmed into MFVC VC Arbitration <br> Table; Clearing this bit has no effect. Software checks the VC Arbitration Table Status bit in the MFVC <br> Port VC Status register to confirm that new values stored in the MFVC VC Arbitration Table are latched by <br> the VC arbitration logic. <br> This bit always returns 0b when read. | RW |
| $3: 1$ | VC Arbitration Select - Used by software to configure the VC arbitration by selecting one of the <br> supported VC Arbitration schemes indicated by the VC Arbitration Capability field in the MFVC Port VC <br> Capability Register 2. <br> The permissible values of this field are numbers corresponding to one of the asserted bits in the VC <br> Arbitration Capability field. <br> This field cannot be modified when more than one VC in the LPVC group is enabled. | RW |
| 4 | All VCs Enabled - Setting this bit indicates that all VCs that will be used by the Port have been enabled. <br> Setting this bit allows hardware to allocate assigned buffer resources across the enabled VCs. <br> Setting this bit is optional. If this bit remains Clear and some VC Resources are never enabled, <br> performance may be affected but the Link and all enabled VCs must operate correctly. <br> Behavior is undefined if this bit is Set and any VC Enable bit in this capability changes value. <br> Default value of this bit is 0b. |  |

# 7.9.2.5 MFVC Port VC Status Register (Offset OEh) 

The MFVC Port VC Status Register provides status of the configuration of Virtual Channels associated with a Port of the Multi-Function Device. § Figure 7-243 details allocation of register fields in the MFVC Port VC Status Register; § Table $7-222$ provides the respective bit definitions.
![img-234.jpeg](img-234.jpeg)

Figure 7-243 MFVC Port VC Status Register

Table 7-222 MFVC Port VC Status Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 0 | VC Arbitration Table Status - Indicates the coherency status of the MFVC VC Arbitration Table. This bit is <br> valid when the selected VC uses the MFVC VC Arbitration Table. <br> This bit is Set by hardware when any entry of the MFVC VC Arbitration Table is written by software. This <br> bit is Cleared by hardware when hardware finishes loading values stored in the MFVC VC Arbitration <br> Table after software sets the Load VC Arbitration Table bit in the MFVC Port VC Control Register. <br> Default value of this bit is Ob. | RO |

### 7.9.2.6 MFVC VC Resource Capability Register

The MFVC VC Resource Capability Register describes the capabilities and configuration of a particular Virtual Channel resource. § Figure 7-244 details allocation of register fields in the MFVC VC Resource Capability Register; § Table 7-223 provides the respective bit definitions.
![img-235.jpeg](img-235.jpeg)

Figure 7-244 MFVC VC Resource Capability Register

Table 7-223 MFVC VC Resource Capability Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 7:0 | Function Arbitration Capability - Indicates types of Function Arbitration supported by the VC resource. | RO |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | Each Bit Location within this field corresponds to a Function Arbitration Capability defined below. When more than 1 bit in this field is Set, it indicates that the VC resource can be configured to provide different arbitration services. <br> Software selects among these capabilities by writing to the Function Arbitration Select field (see \$ Section 7.9.2.7). <br> Defined bit positions are: |  |
|  | Bit 0 | Non-configurable hardware-fixed arbitration scheme, e.g., Round Robin (RR) |
|  | Bit 1 | Weighted Round Robin (WRR) arbitration with 32 phases |
|  | Bit 2 | WRR arbitration with 64 phases |
|  | Bit 3 | WRR arbitration with 128 phases |
|  | Bit 4 | Time-based WRR with 128 phases |
|  | Bit 5 | WRR arbitration with 256 phases |
|  | Bits 6-7 | Reserved |
| 22:16 | Maximum Time Slots - Indicates the maximum number of time slots (minus 1) that the VC resource is capable of supporting when it is configured for time-based WRR Function Arbitration. For example, a value of 0000000 b in this field indicates the supported maximum number of time slots is 1 and a value of 1111111 b indicates the supported maximum number of time slots is 128 . <br> This field is valid only when the Function Arbitration Capability indicates that the VC resource supports time-based WRR Function Arbitration. | HwInit |
| $31: 24$ | Function Arbitration Table Offset - Indicates the location of the Function Arbitration Table associated with the VC resource. <br> This field contains the zero-based offset of the table in DQWORDS (16 bytes) from the base address of the MFVC Extended Capability structure. A value of 00 h indicates that the table is not present. | RO |

# 7.9.2.7 MFVC VC Resource Control Register $\$$ 

\$ Figure 7-245 details allocation of register fields in the MFVC VC Resource Control Register; \$ Table 7-224 provides the respective bit definitions.
![img-236.jpeg](img-236.jpeg)

Figure 7-245 MFVC VC Resource Control Register $\$$

Table 7-224 MFVC VC Resource Control Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $7: 0$ | TC/VC Map - This field indicates the TCs that are mapped to the VC resource. <br> Bit Locations within this field correspond to TC values. For example, when bit 7 is Set in this field, TC7 is mapped to this VC resource. When more than 1 bit in this field is Set, it indicates that multiple TCs are mapped to the VC resource. <br> In order to remove one or more TCs from the TC/VC Map of an enabled VC, software must ensure that no new or outstanding transactions with the TC labels are targeted at the given Link. <br> Default value of this field is FFh for the first VC resource and is 00 h for other VC resources. <br> Note: <br> Bit 0 of this field is read-only. It must be hardwired to 1 b for the default VC0 and hardwired to 0 b for all other enabled VCs. | RW (see the note for exceptions) |
| 16 | Load Function Arbitration Table - When Set, this bit updates the Function Arbitration logic from the Function Arbitration Table for the VC resource. This bit is only valid when the Function Arbitration Table is used by the selected Function Arbitration scheme (that is indicated by a Set bit in the Function Arbitration Capability field selected by Function Arbitration Select). <br> Software sets this bit to signal hardware to update Function Arbitration logic with new values stored in the Function Arbitration Table; clearing this bit has no effect. Software uses the Function Arbitration Table Status bit to confirm whether the new values of Function Arbitration Table are completely latched by the arbitration logic. <br> This bit always returns 0 b when read. <br> Default value of this bit is 0 b . | RW |
| $19: 17$ | Function Arbitration Select - This field configures the VC resource to provide a particular Function Arbitration service. <br> The permissible value of this field is a number corresponding to one of the asserted bits in the Function Arbitration Capability field of the VC resource. | RW |
| $26: 24$ | VC ID - This field assigns a VC ID to the VC resource (see note for exceptions). <br> This field cannot be modified when the VC is already enabled. <br> Note: <br> For the first VC resource (default VC), this field is a read-only field that must be hardwired to 000b. | RW |
| $29: 27$ | Shared Flow Control Usage Limit - this field controls what percentage of the available Shared Flow Control a given FC/VC is permitted to consume. <br> This limit is applied independently for each Flow Control credit type. For example, if this field contains 101b and Shared Flow Control Usage Limit Enable is Set, a Posted TLP may not pass the Tx Gate if doing so would cause that VC to consume more than $62.5 \%$ of the available Shared Posted Header credits or if doing so would cause that VC to consume more than $62.5 \%$ of the available Shared Data credits. <br> If Shared Flow Control Usage Limit Enable is Clear, this field is ignored and this VC is permitted to consume all of the shared credits. <br> When Shared Flow Control Usage Limit Enable is Set, and this field contains 000b, this VC is not permitted to consume any shared credits. <br> Behavior is undefined when all VCs have Shared Flow Control Usage Limit Enable Set and the sum of the Shared Flow Control Limit values for all VCs is less than 100\%. <br> Encodings are: <br> 000b $0 \%$ | RW / RO / RsvdP |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | 001b | $12.5 \%$ |
|  | 010b | $25 \%$ |
|  | 011b | $37.5 \%$ |
|  | 100b | $50 \%$ |
|  | 101b | $62.5 \%$ |
|  | 110b | $75 \%$ |
|  | 111b | $87.5 \%$ |
|  | Behavior is undefined if this field changes value while VC Enable and Shared Flow Control Usage Limit Enable are both Set. <br> This field is RsvdP when Flit Mode Supported is Clear. <br> When Extended VC Count is 0 , this field is permitted to be hardwired to 000b. <br> When this field is RW, the default value is implementation specific. |  |
| 30 | Shared Flow Control Usage Limit Enable - When Set, this bit enables use of the Shared Flow Control Usage Limit value above at the transmitter for this Virtual Channel. <br> Behavior is undefined of the value of this bit changes while VC Enable is Set. <br> This bit is RsvdP when Flit Mode Supported is Clear. <br> When Extended VC Count is 0 , this bit is permitted to be hardwired to 0 b . When this bit is RW, the default value is implementation specific. | RW / RO / RsvdP |
| 31 | VC Enable - When Set, this bit enables a Virtual Channel. The Virtual Channel is disabled when this bit is cleared. <br> Software must use the VC Negotiation Pending bit to check whether the VC negotiation is complete. <br> For VC0, the attribute is RO. If no SVC capability is implemented in this Port, this bit's value must be 1b; otherwise, this bit's value must always be the same value as the Use VC/MFVC bit in the SVC Port Status Register. See § Section 6.3.5 . <br> For other VCs, if no SVC capability is implemented in this Port or if the Use VC/MFVC bit is Set, the default value of this bit is 0 b and the attribute is RW; otherwise, this bit must be RO with a value of 0 b . <br> To enable a Virtual Channel, in a Port using MFVC mechanisms, the VC Enable bit for that Virtual Channel must be Set. The corresponding Virtual Channel in the Link partner Port must be enabled as well, and that Virtual Channel may be in SVC, VC, or MFVC capabilities. To disable a Virtual Channel, the Virtual Channel must be disabled in both components on the Link. Software must ensure that no traffic is using a Virtual Channel at the time it is disabled. Software must fully disable a Virtual Channel in both components on a Link before re-enabling the Virtual Channel. <br> When this bit is forced to be RO with a value of 0 b due to the Use VC/MFVC bit being Clear, its associated VC is disabled, rendering most of its control registers to be ineffective. | RW/HwInit |

# 7.9.2.8 MFVC VC Resource Status Register 

§ Figure 7-246 details allocation of register fields in the MFVC VC Resource Status Register; § Table 7-225 provides the respective bit definitions.

![img-237.jpeg](img-237.jpeg)

Figure 7-246 MFVC VC Resource Status Register

Table 7-225 MFVC VC Resource Status Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 0 | Function Arbitration Table Status - This bit indicates the coherency status of the Function Arbitration Table associated with the VC resource. This bit is valid only when the Function Arbitration Table is used by the selected Function Arbitration for the VC resource. <br> This bit is Set by hardware when any entry of the Function Arbitration Table is written to by software. This bit is Cleared by hardware when hardware finishes loading values stored in the Function Arbitration Table after software sets the Load Function Arbitration Table bit. <br> Default value of this bit is Ob. | RO |
| 1 | VC Negotiation Pending - This bit indicates whether the Virtual Channel negotiation (initialization or disabling) is in pending state. <br> When this bit is Set by hardware, it indicates that the VC resource is still in the process of negotiation. This bit is Cleared by hardware after the VC negotiation is complete. For a non-default Virtual Channel, software may use this bit when enabling or disabling the VC. For the default VC, this bit indicates the status of the process of Flow Control initialization. <br> Before using a Virtual Channel, software must check whether the VC Negotiation Pending bits for that Virtual Channel are Clear in both components on a Link. | RO |

# 7.9.2.9 MFVC VC Arbitration Table 

The definition of the MFVC VC Arbitration Table in the MFVC Extended Capability structure is identical to that in the VC Extended Capability structure (see § Section 7.9.1.9).

### 7.9.2.10 Function Arbitration Table

The Function Arbitration Table register in the MFVC Extended Capability structure takes the same form as the Port Arbitration Table register in the VC Extended Capability structure (see § Section 7.9.1.10).

The Function Arbitration Table register is a read-write register array that is used to store the WRR or time-based WRR arbitration table for Function Arbitration for the VC resource. It is only present when one or more asserted bits in the Function Arbitration Capability field indicate that the Multi-Function Device supports a Function Arbitration scheme that uses a programmable arbitration table. Furthermore, it is only valid when one of the above-mentioned bits in the Function Arbitration Capability field is selected by the Function Arbitration Select field.

The Function Arbitration Table represents one Function arbitration period. Each table entry containing a Function Number or Function Group ${ }^{\text {TM }}$ Number corresponds to a phase within a Function Arbitration period. The table entry size requirements are as follows:

- The table entry size for non-ARI devices must support enough values to specify all implemented Functions plus at least one value that does not correspond to an implemented Function. For example, a table with 2-bit entries can be used by a Multi-Function Device with up to three Functions.
- The table entry size for ARI Devices must be either 4 bits or 8 bits.
- If MFVC Function Groups are enabled, each entry maps to a single Function Group. Arbitration between multiple Functions within a Function Group is implementation specific, but must guarantee forward progress.
- If MFVC Function Groups are not enabled and 4-bit entries are implemented, a given entry maps to all Functions whose Function Number modulo 8 matches its value. Similarly, if 8-bit entries are implemented, a given entry maps to all Functions whose Function Number modulo 128 matches its value. If a given entry maps to multiple Functions, arbitration between those Functions is implementation specific, but must guarantee forward progress.

A Function Number or Function Group Number written to a table entry indicates that the phase within the Function Arbitration period is assigned to the selected Function or Function Group (the Function Number or Function Group Number must be a valid one).

- When the WRR Function Arbitration is used for a VC of the Egress Port of the Multi-Function Device, at each arbitration phase the Function Arbiter serves one transaction from the Function or Function Group indicated by the Function Number or Function Group Number of the current phase. When finished, it immediately advances to the next phase. A phase is skipped, i.e., the Function Arbiter simply moves to the next phase immediately if the Function or Function Group indicated by the phase does not contain any transaction for the VC.
- When the Time-based WRR Function Arbitration is used for a VC of the Egress Port of the Multi-Function Device, at each arbitration phase aligning to a virtual timeslot, the Function Arbiter serves one transaction from the Function or Function Group indicated by the Function Number or Function Group Number of the current phase. It advances to the next phase at the next virtual timeslot. A phase indicates an "idle" timeslot, i.e., the Function Arbiter does not serve any transaction during the phase, if:
- the phase contains the Number of a Function or a Function Group that does not exist, or
- the Function or Function Group indicated by the phase does not contain any transaction for the VC.

The Function Arbitration Table Entry Size field in the MFVC Port VC Capability Register 1 determines the table entry size. The length of the table is determined by the Function Arbitration Select field as shown in § Table 7-226.

When the Function Arbitration Table is used by the default Function Arbitration for the default VC, the default values for the table entries must contain at least one entry for each of the active Functions or Function Groups in the Multi-Function Device to ensure forward progress for the default VC for the Multi-Function Device's Upstream Port. The table may contain RR or RR-like fair Function Arbitration for the default VC.

Table 7-226 Length of Function Arbitration Table

| Function Arbitration Select | Function Arbitration Table Length |
| :--: | :--: |
| 001b | 32 entries |
| 010b | 64 entries |
| 011b | 128 entries |
| 100b | 128 entries |

[^0]
[^0]:    192. If an ARI Device supports MFVC Function Groups capability and ARI-aware software enables it, arbitration is based on Function Groups instead of Functions. See § Section 7.8.8 .

| Function Arbitration Select | Function Arbitration Table Length |
| :--: | :--: |
| 101b | 256 entries |

# 7.9.3 Device Serial Number Extended Capability 

The Device Serial Number Extended Capability is an optional Extended Capability that may be implemented by any PCI Express device Function. The Device Serial Number is a read-only 64-bit value that is unique for a given PCI Express device. $\S$ Figure 7-247 details allocation of register fields in the Device Serial Number Extended Capability structure.

It is permitted but not recommended for RCIEPs to implement this Capability.
RCIEPs that implement this Capability are permitted but not required to return the same Device Serial Number value as that reported by other RCIEPs of the same Root Complex.

All Multi-Function Devices other than RCIEPs that implement this Capability must implement it for Function 0; other Functions that implement this Capability must return the same Device Serial Number value as that reported by Function 0 .

RCIEPs are permitted to implement or not implement this Capability on an individual basis, independent of whether they are part of a Multi-Function Device.

A PCI Express component other than a Root Complex containing multiple Devices such as a PCI Express Switch that implements this Capability must return the same Device Serial Number for each device.

The Device Serial Number Extended Capability is permitted to be present in PFs. If a PF contains the capability, its value applies to all associated VFs. VFs are permitted but not recommended to implement this capability. VFs that implement this capability must return the same Device Serial Number value as that reported by their associated PF.
![img-238.jpeg](img-238.jpeg)

Figure 7-247 Device Serial Number Extended Capability Structure

### 7.9.3.1 Device Serial Number Extended Capability Header (Offset 00h)

§ Figure 7-248 details allocation of register fields in the Device Serial Number Extended Capability Header; § Table 7-227 provides the respective bit definitions. Refer to $\S$ Section 7.6.3 for a description of the PCI Express Extended Capability header. The Extended Capability ID for the Device Serial Number Extended Capability is 0003h.

![img-239.jpeg](img-239.jpeg)

Figure 7-248 Device Serial Number Extended Capability Header

Table 7-227 Device Serial Number Extended Capability Header

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $15: 0$ | PCI Express Extended Capability ID - This field is a PCI-SIG defined ID number that indicates the nature and format of the Extended Capability. <br> Extended Capability ID for the Device Serial Number Extended Capability is 0003h. | RO |
| $19: 16$ | Capability Version - This field is a PCI-SIG defined version number that indicates the version of the Capability structure present. <br> Must be 1 h for this version of the specification. | RO |
| $31: 20$ | Next Capability Offset - This field contains the offset to the next PCI Express Capability structure or 000h if no other items exist in the linked list of Capabilities. <br> For Extended Capabilities implemented in Configuration Space, this offset is relative to the beginning of PCI-compatible Configuration Space and thus must always be either 000 h (for terminating list of Capabilities) or greater than 0FFh. | RO |

# 7.9.3.2 Serial Number Register (Offset 04h) 

The Serial Number register is a 64-bit field that contains the IEEE defined 64-bit extended unique identifier [EUI-64].
§ Figure 7-249 details allocation of register fields in the Serial Number register; § Table 7-228 provides the respective bit definitions.

| PCI Express Device Serial Number |  |  |
| :--: | :--: | :--: |
| Figure 7-249 Serial Number Register |  |  |
| Table 7-228 Serial Number Register |  |  |
| Bit Location | Register Description | Attributes |
| 63:0 | PCI Express Device Serial Number - This field contains the IEEE defined 64-bit Extended Unique Identifier [EUI-64]. This identifier includes a 24-bit company id value assigned by IEEE registration authority and a 40-bit extension identifier assigned by the manufacturer. <br> PCI Express Device Serial Number[07:00] = EUI[63:56] <br> PCI Express Device Serial Number[15:08] = EUI[55:48] <br> PCI Express Device Serial Number[23:16] = EUI[47:40] <br> PCI Express Device Serial Number[31:24] = EUI[39:32] <br> PCI Express Device Serial Number[39:32] = EUI[31:24] | RO |

| Bit Location | Register Description | Attributes |
| :-- | :-- | :-- |
|  | PCI Express Device Serial Number[47:40] = EUI[23:16] <br> PCI Express Device Serial Number[55:48] = EUI[15:08] <br> PCI Express Device Serial Number[63:56] = EUI[07:00] |  |

# 7.9.4 Vendor-Specific Capability 

The Vendor-Specific Capability is a capability structure in PCI-compatible Configuration Space (first 256 bytes) as shown in § Figure 7-250.

The Vendor-Specific Capability allows device vendors to use the Capability mechanism for vendor-specific information. The layout of the information is vendor-specific, except for the first three bytes, as explained below.

A single PCI Express Function is permitted to contain multiple VSEC structures.
![img-240.jpeg](img-240.jpeg)

Figure 7-250 Vendor-Specific Capability

Table 7-229 Vendor-Specific Capability

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| $7: 0$ | Capability ID - Indicates the PCI Express Capability structure. This field must return a Capability ID of <br> 09h indicating that this is a Vendor-Specific Capability structure. | RO |
| $15: 8$ | Next Capability Pointer - This field contains the offset to the next PCI Capability structure or 00h if no <br> other items exist in the linked list of Capabilities. | RO |
| $23: 16$ | Capability Length - This field provides the number of bytes in the Capability structure (including the <br> three bytes consumed by the Capability ID, Next Capability Pointer, and Capability Length field). | RO |
| $31: 24$ | Vendor Specific Information | Vendor <br> Specific |

### 7.9.5 Vendor-Specific Extended Capability

The Vendor-Specific Extended Capability (VSEC Capability) is an optional Extended Capability that is permitted to be implemented by any PCI Express Function or RCRB. This allows PCI Express component vendors to use the Extended Capability mechanism to expose vendor-specific registers.

A single PCI Express Function or RCRB is permitted to contain multiple VSEC structures.
An example usage is a set of vendor-specific features that are intended to go into an on-going series of components from that vendor. A VSEC structure can tell vendor-specific software which features a particular component supports, including components developed after the software was released.
§ Figure 7-251 details allocation of register fields in the VSEC structure. The structure of the Vendor-Specific Extended Capability Header and the Vendor-Specific Header is architected by this specification.

With a PCI Express Function, the structure and definition of the vendor-specific Registers area is determined by the vendor indicated by the Vendor ID field located at byte offset 00 h in PCI-compatible Configuration Space. With an RCRB, a VSEC is permitted only if the RCRB also contains an RCRB Header Extended Capability structure, which contains a Vendor ID field indicating the vendor.
![img-241.jpeg](img-241.jpeg)

Figure 7-251 VSEC Capability Structure

# 7.9.5.1 Vendor-Specific Extended Capability Header (Offset 00h) 

§ Figure 7-252 details allocation of register fields in the Vendor-Specific Extended Capability Header; § Table 7-230 provides the respective bit definitions. Refer to § Section 7.6.3 for a description of the PCI Express Extended Capability Header. The Extended Capability ID for the Vendor-Specific Extended Capability is 000Bh.
![img-242.jpeg](img-242.jpeg)

Figure 7-252 Vendor-Specific Extended Capability Header

Table 7-230 Vendor-Specific Extended Capability Header

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 15:0 | PCI Express Extended Capability ID - This field is a PCI-SIG defined ID number that indicates the nature and format of the Extended Capability. | RO |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | Extended Capability ID for the Vendor-Specific Extended Capability is 000Bh. |  |
| $19: 16$ | Capability Version - This field is a PCI-SIG defined version number that indicates the version of the Capability structure present. <br> Must be 1 h for this version of the specification. | RO |
| $31: 20$ | Next Capability Offset - This field contains the offset to the next PCI Express Capability structure or 000h if no other items exist in the linked list of Capabilities. <br> For Extended Capabilities implemented in Configuration Space, this offset is relative to the beginning of PCI-compatible Configuration Space and thus must always be either 000 h (for terminating list of Capabilities) or greater than 0FFh. | RO |

# 7.9.5.2 Vendor-Specific Header (Offset 04h) $\S$ 

§ Figure 7-253 details allocation of register fields in the Vendor-Specific Header; § Table 7-231 provides the respective bit definitions.

Vendor-specific software must qualify the associated Vendor ID of the PCI Express Function or RCRB before attempting to interpret the values in the VSEC ID or VSEC Rev fields.
![img-243.jpeg](img-243.jpeg)

Figure 7-253 Vendor-Specific Header

Table 7-231 Vendor-Specific Header $\S$

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $15: 0$ | VSEC ID - This field is a vendor-defined ID number that indicates the nature and format of the VSEC structure. <br> Software must qualify the Vendor ID before interpreting this field. | RO |
| $19: 16$ | VSEC Rev - This field is a vendor-defined version number that indicates the version of the VSEC structure. <br> Software must qualify the Vendor ID and VSEC ID before interpreting this field. | RO |
| $31: 20$ | VSEC Length - This field indicates the number of bytes in the entire VSEC structure, including the Vendor-Specific Extended Capability Header, the Vendor-Specific Header, and the vendor-specific registers. | RO |

# 7.9.6 Designated Vendor-Specific Extended Capability (DVSEC) 

The Designated Vendor-Specific Extended Capability (DVSEC Capability) is an optional Extended Capability that is permitted to be implemented by any PCI Express Function or RCRB. This allows PCI Express component vendors to use the Extended Capability mechanism to expose vendor-specific registers that can be present in components by a variety of vendors.

A single PCI Express Function or RCRB is permitted to contain multiple DVSEC Capability structures.
An example usage is a set of vendor-specific features that are intended to go into an on-going series of components from a collection of vendors. A DVSEC Capability structure can tell vendor-specific software which features a particular component supports, including components developed after the software was released.
§ Figure 7-254 details allocation of register fields in the DVSEC Capability structure. The structure of the PCI Express Extended Capability Header and the Designated Vendor-Specific header is architected by this specification.

The DVSEC Vendor-Specific Register area begins at offset 0Ah.
![img-244.jpeg](img-244.jpeg)

Figure 7-254 Designated Vendor-Specific Extended Capability

### 7.9.6.1 Designated Vendor-Specific Extended Capability Header (Offset 00h)

§ Figure 7-255 details allocation of register fields in the Designated Vendor-Specific Extended Capability Header; § Table 7-232 provides the respective bit definitions. Refer to § Section 7.9.3 for a description of the PCI Express Extended Capability Header. The Extended Capability ID for the Designated Vendor-Specific Extended Capability is 0023h.
![img-245.jpeg](img-245.jpeg)

Figure 7-255 Designated Vendor-Specific Extended Capability Header

Table 7-232 Designated Vendor-Specific Extended Capability Header
![img-246.jpeg](img-246.jpeg)

# 7.9.6.2 Designated Vendor-Specific Header 1 (Offset 04h) 

\$ Figure 7-256 details allocation of register fields in the Designated Vendor-Specific Header 1; \$ Table 7-233 provides the respective bit definitions.

Vendor-specific software must qualify the DVSEC Vendor ID before attempting to interpret the DVSEC Revision field.
![img-247.jpeg](img-247.jpeg)

Figure 7-256 Designated Vendor-Specific Header 1

Table 7-233 Designated Vendor-Specific Header 1

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 15:0 | DVSEC Vendor ID - This field is the Vendor ID associated with the vendor that defined the contents of <br> this capability. | RO |
| 19:16 | DVSEC Revision - This field is a vendor-defined version number that indicates the version of the DVSEC <br> structure. <br> Software must qualify the DVSEC Vendor ID and DVSEC ID before interpreting this field. | RO |
| 31:20 | DVSEC Length - This field indicates the number of bytes in the entire DVSEC structure, including the PCI <br> Express Extended Capability Header, the DVSEC Header 1, DVSEC Header 2, and DVSEC vendor-specific <br> registers. | RO |

# 7.9.6.3 Designated Vendor-Specific Header 2 (Offset 08h) 

\$ Figure 7-257 details allocation of register fields in the Designated Vendor-Specific Header 2; \$ Table 7-234 provides the respective bit definitions.

Vendor-specific software must qualify the DVSEC Vendor ID before attempting to interpret the DVSEC ID field.
![img-248.jpeg](img-248.jpeg)

Figure 7-257 Designated Vendor-Specific Header 2

Table 7-234 Designated Vendor-Specific Header 2

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 15:0 | DVSEC ID - This field is a vendor-defined ID that indicates the nature and format of the DVSEC structure. | RO |
|  | Software must qualify the DVSEC Vendor ID before interpreting this field. |  |

### 7.9.7 RCRB Header Extended Capability

The PCI Express RCRB Header Extended Capability is an optional Extended Capability that may be implemented in an RCRB to provide a Vendor ID and Device ID for the RCRB and to permit the management of parameters that affect the behavior of Root Complex functionality associated with the RCRB.
![img-249.jpeg](img-249.jpeg)

Figure 7-258 RCRB Header Extended Capability Structure

# 7.9.7.1 RCRB Header Extended Capability Header (Offset 00h) 

\$ Figure 7-259 details allocation of register fields in the RCRB Header Extended Capability Header. \$ Table 7-235 provides the respective bit definitions. Refer to $\S$ Section 7.6.3 for a description of the PCI Express Enhanced Capabilities header. The Extended Capability ID for the RCRB Header Extended Capability is 000Ah.

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 15:0 | PCI Express Extended Capability ID - This field is a PCI-SIG defined ID number that indicates the nature and format of the Extended Capability. <br> Extended Capability ID for the RCRB Header Extended Capability is 000Ah. | RO |
| 19:16 | Capability Version - This field is a PCI-SIG defined version number that indicates the version of the Capability structure present. <br> Must be 1 h for this version of the specification. | RO |
| $31: 20$ | Next Capability Offset - This field contains the offset to the next PCI Express Capability structure or 000h if no other items exist in the linked list of Capabilities. <br> For Extended Capabilities implemented in Configuration Space, this offset is relative to the beginning of PCI-compatible Configuration Space and thus must always be either 000 h (for terminating list of Capabilities) or greater than 0FFh. | RO |

### 7.9.7.2 RCRB Vendor ID and Device ID register (Offset 04h)

\$ Figure 7-260 details allocation of register fields in the RCRB Vendor ID and Device ID register; \$ Table 7-236 provides the respective bit definitions.
![img-250.jpeg](img-250.jpeg)

Figure 7-260 RCRB Vendor ID and Device ID register

Table 7-236 RCRB Vendor ID and Device ID register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| $15: 0$ | Vendor ID - PCI-SIG assigned. Analogous to the equivalent field in PCI-compatible Configuration Space. <br> This field provides a means to associate an RCRB with a particular vendor. | RO |
| $31: 16$ | Device ID - Vendor assigned. Analogous to the equivalent field in PCI-compatible Configuration Space. <br> This field provides a means for a vendor to classify a particular RCRB. | RO |

# 7.9.7.3 RCRB Capabilities register (Offset 08h) 

$\S$ Figure 7-261 details allocation of register fields in the RCRB Capabilities register; § Table 7-237 provides the respective bit definitions.
![img-251.jpeg](img-251.jpeg)

Figure 7-261 RCRB Capabilities register

Table 7-237 RCRB Capabilities register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 0 | Configuration RRS Software Visibility - When Set, this bit indicates that the Root Complex is capable of <br> returning Request Retry Status (RRS) Completion Status in response to a Configuration Request for all <br> Root Ports and integrated devices associated with this RCRB (see § Section 2.3.1). | RO |

### 7.9.7.4 RCRB Control register (Offset 0Ch) $\S$

§ Figure 7-262 details allocation of register fields in the RCRB Control register; § Table 7-238 provides the respective bit definitions.
![img-252.jpeg](img-252.jpeg)

Figure 7-262 RCRB Control register

Table 7-238 RCRB Control register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 0 | Configuration RRS Software Visibility Enable - When Set, this bit enables the Root Complex to return <br> Request Retry Status (RRS) Completion Status in response to a Configuration Reuquest for all Root Ports <br> and integrated devices associated with this RCRB (see § Section 2.3.1). | RW |

| Bit Location | Register Description | Attributes |
| :-- | :-- | :-- |
|  | RCRBs that do not implement this capability must hardwire this bit to 0 b. |  |
|  | Default value of this bit is 0 b. |  |

# 7.9.8 Root Complex Link Declaration Extended Capability 

The Root Complex Link Declaration Extended Capability is an optional Capability that is permitted to be implemented by Root Ports, RCiEPs, or RCRBs to declare a Root Complex's internal topology.

A Root Complex consists of one or more following elements:

- PCI Express Root Port
- A default system Egress Port or an internal sink unit such as memory (represented by an RCRB)
- Internal Data Paths/Links (represented by an RCRB on either side of an internal Link)
- Integrated devices
- Functions

A Root Complex Component is a logical aggregation of the above described Root Complex elements. No single element can be part of more than one Root Complex Component. Each Root Complex Component must have a unique Component ID.

A Root Complex is represented either as an opaque Root Complex or as a collection of one or more Root Complex Components.

The Root Complex Link Declaration Extended Capability is permitted to be present in a Root Complex element's Configuration Space or RCRB. It declares Links from the respective element to other elements of the same Root Complex Component or to an element in another Root Complex Component. The Links are required to be declared bidirectional such that each valid data path from one element to another has corresponding Link Entries in the Configuration Space (or RCRB) of both elements.

The Root Complex Link Declaration Extended Capability is permitted to also declare an association between a Configuration Space element (Root Port or RCiEP) and an RCRB Header Extended Capability (see § Section 7.9.7) contained in an RCRB that affects the behavior of the Configuration Space element. Note that an RCRB Header association is not declared bidirectional; the association is only declared by the Configuration Space element and not by the target RCRB.

## IMPLEMENTATION NOTE: TOPOLOGIES TO AVOID

Topologies that create more than one data path between any two Root Complex elements (either directly or through other Root Complex elements) may not be able to support bandwidth allocation in a standard manner. The description of how traffic is routed through such a topology is implementation specific, meaning that general purpose-operating systems may not have enough information about such a topology to correctly support bandwidth allocation. In order to circumvent this problem, these operating systems may require that a single RCRB element (of type Internal Link) not declare more than one Link to a Root Complex Component other than the one containing the RCRB element itself.

The Root Complex Link Declaration Extended Capability, as shown in § Figure 7-263, consists of the PCI Express Extended Capability header and Root Complex Element Self Description followed by one or more Root Complex Link Entries.
![img-253.jpeg](img-253.jpeg)

Figure 7-263 Root Complex Link Declaration Extended Capability

# 7.9.8.1 Root Complex Link Declaration Extended Capability Header (Offset 00h) 

The Extended Capability ID for the Root Complex Link Declaration Extended Capability is 0005 h.
![img-254.jpeg](img-254.jpeg)

Figure 7-264 Root Complex Link Declaration Extended Capability Header

Table 7-239 Root Complex Link Declaration Extended Capability Header

| Bit <br> Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 15:0 | PCI Express Extended Capability ID - This field is a PCI-SIG defined ID number that indicates the nature and format of the Extended Capability. <br> The Extended Capability ID for the Root Complex Link Declaration Extended Capability is 0005h. | RO |
| 19:16 | Capability Version - This field is a PCI-SIG defined version number that indicates the version of the Capability structure present. <br> Must be 1 h for this version of the specification. | RO |
| $31: 20$ | Next Capability Offset - This field contains the offset to the next PCI Express Capability structure or 000h if no other items exist in the linked list of Capabilities. <br> For Extended Capabilities implemented in Configuration Space, this offset is relative to the beginning of PCI-compatible Configuration Space and thus must always be either 000 h (for terminating list of Capabilities) or greater than 0FFh. <br> The bottom 2 bits of this offset are Reserved and must be implemented as 00 b although software must mask them to allow for future uses of these bits. | RO |

# 7.9.8.2 Element Self Description Register (Offset 04h) 

The Element Self Description Register provides information about the Root Complex element containing the Root Complex Link Declaration Extended Capability.
![img-255.jpeg](img-255.jpeg)

Figure 7-265 Element Self Description Register

Table 7-240 Element Self Description Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 3:0 | Element Type - This field indicates the type of the Root Complex Element. Defined encodings are: <br> 0h Configuration Space Element <br> 1h System Egress Port or internal sink (memory) <br> 2h Internal Root Complex Link <br> 3h-Fh Reserved | RO |
| 15:8 | Number of Link Entries - This field indicates the number of Link Entries following the Element Self Description. This field must report a value of 01 h or higher. | HwInit |
| 23:16 | Component ID - This field identifies the Root Complex Component that contains this Root Complex Element. Component IDs must start at 01h, as a value of 00 h is Reserved. | HwInit |

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| $31: 24$ | Port Number - This field specifies the Port Number associated with this element with respect to the <br> Root Complex Component that contains this element. <br> An element with a Port Number of 00h indicates the default Egress Port to configuration software. | HwInit |

# 7.9.8.3 Link Entries 

Link Entries start at offset 10h of the Root Complex Link Declaration Extended Capability structure. Each Link Entry consists of a Link description followed by a 64-bit Link Address at offset 08h from the start of Link Entry identifying the target element for the declared Link. A Link Entry declares an internal Link to another Root Complex Element.
![img-256.jpeg](img-256.jpeg)

Figure 7-266 Link Entry

### 7.9.8.3.1 Link Description Register

The Link Description Register is located at offset 00h from the start of a Link Entry and is defined as follows:
![img-257.jpeg](img-257.jpeg)

Figure 7-267 Link Description Register

Table 7-241 Link Description Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :-- |
| 0 | Link Valid - When Set, this bit indicates that the Link Entry specifies a valid Link. Link Entries that do not <br> have either this bit Set or the Associate RCRB Header bit Set (or both) are ignored by software. | HwInit |
| 1 | Link Type - This bit indicates the target type of the Link and defines the format of the Link Address field. <br> Defined Link Type values are: | HwInit |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | 0b <br> 1b | Link points to memory-mapped space ${ }^{193}$ (for RCRB). The Link Address specifies the 64-bit base address of the target RCRB. <br> Link points to Configuration Space (for a Root Port or RCIEP). The Link Address specifies the configuration address (PCI Segment Group, Bus, Device, Function) of the target element. |
| 2 | Associate RCRB Header - When Set, this bit indicates that the Link Entry associates the declaring element with an RCRB Header Extended Capability in the target RCRB. Link Entries that do not have either this bit Set or the Link Valid bit Set (or both) are ignored by software. <br> The Link Type bit must be Clear when this bit is Set. | HwInit |
| 23:16 | Target Component ID - This field identifies the Root Complex Component that is targeted by this Link Entry. Components IDs must start at 01h, as a value of 00 h is Reserved | HwInit |
| $31: 24$ | Target Port Number - This field specifies the Port Number associated with the element targeted by this Link Entry; the Target Port Number is with respect to the Root Complex Component (identified by the Target Component ID) that contains the target element. | HwInit |

# 7.9.8.3.2 Link Address 

The Link Address is a HwInit field located at offset 08 h from the start of a Link Entry that identifies the target element for the Link Entry. For a Link of Link Type 0 in its Link Description, the Link Address specifies the memory-mapped base address of RCRB. For a Link of Link Type 1 in its Link Description, the Link Address specifies the Configuration Space address of a PCI Express Root Port or an RCIEP.

### 7.9.8.3.2.1 Link Address for Link Type 0

For a Link pointing to a memory-mapped RCRB (Link Type bit $=0$ ), the first DWORD specifies the lower 32 bits of the RCRB base address of the target element as shown below; bits $11: 0$ are hardwired to 000 h and Reserved for future use. The second DWORD specifies the high order 32 bits (63:32) of the RCRB base address of the target element.
![img-258.jpeg](img-258.jpeg)

Figure 7-268 Link Address for Link Type 0

### 7.9.8.3.2.2 Link Address for Link Type 1

For a Link pointing to the Configuration Space of a Root Complex element (Link Type bit = 1), bits in the first DWORD specify the Bus, Device, and Function Number of the target element. As shown in § Figure 7-269, bits 2:0 (N) encode the number of bits n associated with the Bus Number, with $\mathrm{N}=000 \mathrm{~b}$ specifying $n=8$ and all other encodings specifying
193. The memory-mapped space for accessing an RCRB is not the same as Memory Space, and must not overlap with Memory Space.

$n=$ <value of N>. Bits 11:3 are Reserved and hardwired to 0 . Bits 14:12 specify the Function Number, and bits 19:15 specify the Device Number. Bits $(19+n): 20$ specify the Bus Number, with $1 \leq n \leq 8$.

Bits 31:(20 + $n$ ) of the first DWORD together with the second DWORD optionally identify the target element's hierarchy for systems implementing the PCI Express Enhanced Configuration Access Mechanism by specifying bits 63:(20 + $n$ ) of the memory-mapped Configuration Space base address of the PCI Express hierarchy associated with the targeted element; single hierarchy systems that do not implement more than one memory mapped Configuration Space are allowed to report a value of zero to indicate default Configuration Space.

A Configuration Space base address [63:(20 + $n$ )] equal to zero indicates that the Configuration Space address defined by bits $(19+n): 12$ (Bus Number, Device Number, and Function Number) exists in the default PCI Segment Group; any non-zero value indicates a separate Configuration Space base address.

Software must not use $n$ outside the context of evaluating the Bus Number and memory-mapped Configuration Space base address for this specific target element. In particular, $n$ does not necessarily indicate the maximum Bus Number supported by the associated PCI Segment Group.
![img-259.jpeg](img-259.jpeg)

Figure 7-269 Link Address for Link Type 1

Table 7-242 Link Address for Link Type 1

| Bit Location | Register Description | Attributes |
| :--: | :-- | :-- |
| $2: 0$ | $\boldsymbol{N}$-Encoded number of Bus Number bits | HwInit |
| $14: 12$ | Function Number | HwInit |
| $19: 15$ | Device Number | HwInit |
| $(19+n): 20$ | Bus Number | HwInit |
| $63:(20+n)$ | PCI Express Configuration Space Base Address $(1 \leq n \leq 8)$ | HwInit |
|  | Note: |  |
|  | A Root Complex that does not implement multiple Configuration Spaces is allowed to report this field as |  |
|  | 0. |  |

# 7.9.9 Root Complex Internal Link Control Extended Capability 

The Root Complex Internal Link Control Extended Capability is an optional Capability that controls an internal Root Complex Link between two distinct Root Complex Components. This Capability is valid for RCRBs that declare an Element Type field as Internal Root Complex Link in the Element Self-Description register of the Root Complex Link Declaration Capability structure.

The Root Complex Internal Link Control Extended Capability structure is defined as shown in § Figure 7-270.

| 31 | 30 | 29 | 28 | 27 | 26 | 25 | 24 | 23 | 22 | 21 | 20 | 19 | 18 | 17 | 16 | 15 | 14 | 13 | 12 | 11 | 10 | 9 | 8 | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 | Byte Offset |
| :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: |
| PCI Express Extended Capability Header |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Root Complex Link Capabilities Register |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Root Complex Link Status Register |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Root Complex Link Control Register |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

Figure 7-270 Root Complex Internal Link Control Extended Capability

# 7.9.9.1 Root Complex Internal Link Control Extended Capability Header (Offset 00h) 

The Extended Capability ID for the Root Complex Internal Link Control Extended Capability is 0006h.
![img-260.jpeg](img-260.jpeg)

Figure 7-271 Root Complex Internal Link Control Extended Capability Header

Table 7-243 Root Complex Internal Link Control Extended Capability Header

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 15:0 | PCI Express Extended Capability ID - This field is a PCI-SIG defined ID number that indicates the nature and format of the Extended Capability. <br> The Extended Capability ID for the Root Complex Internal Link Control Extended Capability is 0006h. | RO |
| 19:16 | Capability Version - This field is a PCI-SIG defined version number that indicates the version of the Capability structure present. <br> Must be 1 h for this version of the specification. | RO |
| $31: 20$ | Next Capability Offset - This field contains the offset to the next PCI Express Capability structure or 000h if no other items exist in the linked list of Capabilities. <br> For Extended Capabilities implemented in Configuration Space, this offset is relative to the beginning of PCI-compatible Configuration Space and thus must always be either 000 h (for terminating list of Capabilities) or greater than 0 FFh . <br> The bottom 2 bits of this offset are Reserved and must be implemented as 00 b although software must mask them to allow for future uses of these bits. | RO |

### 7.9.9.2 Root Complex Link Capabilities Register (Offset 04h)

The Root Complex Link Capabilities Register identifies capabilities for this Link.

![img-261.jpeg](img-261.jpeg)

Figure 7-272 Root Complex Link Capabilities Register

Table 7-244 Root Complex Link Capabilities Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 3:0 | Max Link Speed - This field indicates the maximum Link speed of the associated Link. <br> The encoded value specifies a bit location in the Supported Link Speeds Vector (in the Root Complex Link Capabilities Register) that corresponds to the maximum Link speed. <br> Defined encodings are: <br> 0001b Supported Link Speeds Vector field bit 0 <br> 0010b Supported Link Speeds Vector field bit 1 <br> 0011b Supported Link Speeds Vector field bit 2 <br> 0100b Supported Link Speeds Vector field bit 3 <br> 0101b Supported Link Speeds Vector field bit 4 <br> 0110b Supported Link Speeds Vector field bit 5 <br> 0111b Supported Link Speeds Vector field bit 6 <br> Others All other encodings are reserved. <br> A Root Complex that does not support this feature must report 0000b in this field. | RO |
| 9:4 | Maximum Link Width - This field indicates the maximum width of the given Link. <br> Defined encodings are: <br> 000001 b $\times 1$ <br> 000010 b $\times 2$ <br> 000100 b $\times 4$ <br> 001000 b $\times 8$ <br> 010000 b $\times 16$ <br> All other encodings are Reserved. A Root Complex that does not support this feature must report 000000 b in this field. | RO |
| 11:10 | Active State Power Management (ASPM) Support - This field indicates the level of ASPM supported on the given Link. <br> Defined encodings are: <br> 00b No ASPM Support <br> 01b LOs Supported <br> 10b L1 Supported <br> 11b LOs and L1 Supported | RO |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 14:12 | L0s Exit Latency - This field indicates the L0s exit latency for the given Link. The value reported indicates the length of time this Port requires to complete transition from L0s to L0. If L0s is not supported, the value is undefined. <br> Defined encodings are: <br> 000b Less than 64 ns <br> 001b 64 ns to less than 128 ns <br> 010b 128 ns to less than 256 ns <br> 011b 256 ns to less than 512 ns <br> 100b 512 ns to less than $1 \mu \mathrm{~s}$ <br> 101b $1 \mu \mathrm{~s}$ to less than $2 \mu \mathrm{~s}$ <br> 110b $2 \mu \mathrm{~s}$ to $4 \mu \mathrm{~s}$ <br> 111b More than $4 \mu \mathrm{~s}$ | RO |
| 17:15 | L1 Exit Latency - This field indicates the L1 exit latency for the given Link. The value reported indicates the length of time this Port requires to complete transition from ASPM L1 to L0. If ASPM L1 is not supported, the value is undefined. <br> Defined encodings are: <br> 000b Less than $1 \mu \mathrm{~s}$ <br> 001b $1 \mu \mathrm{~s}$ to less than $2 \mu \mathrm{~s}$ <br> 010b $2 \mu \mathrm{~s}$ to less than $4 \mu \mathrm{~s}$ <br> 011b $4 \mu \mathrm{~s}$ to less than $8 \mu \mathrm{~s}$ <br> 100b $8 \mu \mathrm{~s}$ to less than $16 \mu \mathrm{~s}$ <br> 101b $16 \mu \mathrm{~s}$ to less than $32 \mu \mathrm{~s}$ <br> 110b $32 \mu \mathrm{~s}$ to $64 \mu \mathrm{~s}$ <br> 111b More than $64 \mu \mathrm{~s}$ | RO |
| 24:18 | Supported Link Speeds Vector - This field indicates the supported Link speed(s) of the associated Link. For each bit, a value of 1 b indicates that the corresponding Link speed is supported; otherwise, the Link speed is not supported. See $\S$ Section 8.2.1 for further requirements. <br> Bit definitions within this field are: <br> Bit 0 $2.5 \mathrm{GT} / \mathrm{s}$ <br> Bit 1 $5.0 \mathrm{GT} / \mathrm{s}$ <br> Bit 2 $8.0 \mathrm{GT} / \mathrm{s}$ <br> Bit 3 $16.0 \mathrm{GT} / \mathrm{s}$ <br> Bit 4 $32.0 \mathrm{GT} / \mathrm{s}$ <br> Bit 5 $64.0 \mathrm{GT} / \mathrm{s}$ <br> Bit 6 RsvdP | RO |

# IMPLEMENTATION NOTE: <br> SUPPORTED LINK SPEEDS WITH EARLIER HARDWARE 

Hardware components compliant to versions prior to the [PCle-3.0] did not implement the Supported Link Speeds Vector field and instead returned 0000 000b in bits 24:18.

For software to determine the supported Link speeds for components where this field is contains 0000 000b, software can read bits 3:0 of the Root Complex Link Capabilities Register (now defined to be the Max Link Speed field), and interpret the value as follows:

0001b
$2.5 \mathrm{GT} / \mathrm{s}$ Link speed supported
0010b
$5.0 \mathrm{GT} / \mathrm{s}$ and $2.5 \mathrm{GT} / \mathrm{s}$ Link speeds supported
For such components, the same encoding is also used for the values for the Current Link Speed field (in the Root Complex Link Status Register).

## IMPLEMENTATION NOTE: <br> SOFTWARE MANAGEMENT OF LINK SPEEDS WITH FUTURE HARDWARE

It is strongly encouraged that software primarily utilize the Supported Link Speeds Vector instead of the Max Link Speed field, so that software can determine the exact set of supported speeds on current and future hardware. This can avoid software being confused if a future specification defines Links that do not require support for all slower speeds.

### 7.9.9.3 Root Complex Link Control Register (Offset 08h)

The Root Complex Link Control Register controls parameters for this internal Link.
![img-262.jpeg](img-262.jpeg)

Figure 7-273 Root Complex Link Control Register

Table 7-245 Root Complex Link Control Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $1: 0$ | Active State Power Management (ASPM) Control - This field controls the level of ASPM enabled on the given Link. | RW |
|  | Defined encodings are: |  |
|  | 00b | Disabled |
|  | 01b | L0s Entry Enabled |
|  | 10b | L1 Entry Enabled |
|  | 11b | L0s and L1 Entry Enabled |
|  | Note: "L0s Entry Enabled" enables the Transmitter to enter L0s. If L0s is supported, the Receiver must be capable of entering L0s even when the Transmitter is disabled from entering L0s (00b or 10b). |  |
|  | In Flit Mode, L0s is not supported, bit 0 of this field is ignored and has no effect (i.e., encodings 01b and 00b are equivalent as are encodings 11 b and 10 b ). |  |
|  | Default value of this field is implementation specific. |  |
|  | Software must not enable LOs in either direction on a given Link unless components on both sides of the Link each support L0s, as indicated by their ASPM Support field values. Otherwise, the result is undefined. |  |
|  | ASPM L1 must be enabled by software in the Upstream component on a Link prior to enabling ASPM L1 in the Downstream component on that Link. When disabling ASPM L1, software must disable ASPM L1 in the Downstream component on a Link prior to disabling ASPM L1 in the Upstream component on that Link. ASPM L1 must only be enabled on the Downstream component if both components on a Link support ASPM L1. |  |
|  | A Root Complex that does not support this feature for the given internal Link must hardwire this field to 00b. |  |
| 7 | Extended Synch - This bit when Set forces the transmission of additional Ordered Sets when exiting the LOs state (see § Section 4.2.5.6) and when in the Recovery state (see § Section 4.2.7.4.1). This mode provides external devices (e.g., logic analyzers) monitoring the Link time to achieve bit and Symbol lock before the Link enters the L0 state and resumes communication. | RW |
|  | A Root Complex that does not support this feature for the given internal Link must hardwire this bit to 0 b . |  |
|  | In Flit Mode, this bit is ignored and has no effect since L0s is not supported. |  |
|  | Default value for this bit is 0 b . |  |

# 7.9.9.4 Root Complex Link Status Register (Offset 0Ah) 

The Root Complex Link Status Register provides information about Link specific parameters.

![img-263.jpeg](img-263.jpeg)

Figure 7-274 Root Complex Link Status Register

Table 7-246 Root Complex Link Status Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 3:0 | Current Link Speed - This field indicates the negotiated Link speed of the given Link. <br> The encoded value specifies a bit location in the Supported Link Speeds Vector (in the Root Complex Link Capabilities Register) that corresponds to the current Link speed. <br> Defined encodings are: | RO |
|  | 0001b Supported Link Speeds Vector field bit 0 |  |
|  | 0010b Supported Link Speeds Vector field bit 1 |  |
|  | 0011b Supported Link Speeds Vector field bit 2 |  |
|  | 0100b Supported Link Speeds Vector field bit 3 |  |
|  | 0101b Supported Link Speeds Vector field bit 4 |  |
|  | 0110b Supported Link Speeds Vector field bit 5 |  |
|  | 0111b Supported Link Speeds Vector field bit 6 |  |
|  | All other encodings are Reserved. |  |
|  | The value in this field is undefined when the Link is not up. A Root Complex that does not support this feature must report 0000b in this field. |  |
| 9:4 | Negotiated Link Width - This field indicates the negotiated width of the given Link. This includes the Link Width determined during initial link training as well changes that occur after initial link training (e.g., L0p) | RO |
|  | Defined encodings are: |  |
|  | 00001 b | $x 1$ |
|  | 00010 b | $x 2$ |
|  | 000100 b | $x 4$ |
|  | 001000 b | $x 8$ |
|  | 010000 b | $x 16$ |
|  | All other encodings are Reserved. The value in this field is undefined when the Link is not up. A Root Complex that does not support this feature must hardwire this field to 00 0000b. |  |

# 7.9.10 Root Complex Event Collector Endpoint Association Extended Capability 

The Root Complex Event Collector Endpoint Association Extended Capability is implemented by Root Complex Event Collectors. It declares the RCIEPs supported by the Root Complex Event Collector. A Root Complex Event Collector must

implement the Root Complex Event Collector Endpoint Association Extended Capability; no other PCI Express Device Function is permitted to implement this Capability.

The Root Complex Event Collector Endpoint Association Extended Capability, as shown in § Figure 7-275, consists of the PCI Express Extended Capability header followed by a DWORD bitmap enumerating RCIEPs on the same Bus, and optionally an additional range of Bus Numbers that may contain RCIEPs associated with the Root Complex Event Collector. Functions other than RCIEPs (e.g., Root Ports) contained in the range described by this Capability are not associated with this Root Complex Event Collector.
![img-264.jpeg](img-264.jpeg)

Figure 7-275 Root Complex Event Collector Endpoint Association Extended Capability

# 7.9.10.1 Root Complex Event Collector Endpoint Association Extended Capability Header (Offset 00h) 

The Extended Capability ID for the Root Complex Event Collector Endpoint Association Extended Capability is 0007h. § Figure 7-276 details allocation of fields in the Root Complex Event Collector Endpoint Association Extended Capability Header; § Table 7-247 provides the respective bit definitions.
![img-265.jpeg](img-265.jpeg)

Figure 7-276 Root Complex Event Collector Endpoint Association Extended Capability Header

Table 7-247 Root Complex Event Collector Endpoint Association Extended Capability Header

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $15: 0$ | PCI Express Extended Capability ID - This field is a PCI-SIG defined ID number that indicates the nature and format of the Extended Capability. <br> The Extended Capability ID for the Root Complex Event Collector Endpoint Association Extended Capability is 0007 h. | RO |
| 19:16 | Capability Version - This field is a PCI-SIG defined version number that indicates the version of the Capability structure present. <br> Must be 2 h if the Extended Capability contains the RCEC Associated Bus Numbers Register (see § Section 7.9.10.3). Must be 1 h otherwise. | RO |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $31: 20$ | Next Capability Offset - This field contains the offset to the next PCI Express Capability structure or 000 h if no other items exist in the linked list of Capabilities. <br> For Extended Capabilities implemented in Configuration Space, this offset is relative to the beginning of PCI-compatible Configuration Space and thus must always be either 000 h (for terminating list of Capabilities) or greater than 0FFh. <br> The bottom 2 bits of this offset are Reserved and must be implemented as 00b although software must mask them to allow for future uses of these bits. | RO |

# 7.9.10.2 Association Bitmap for RCIEPs (Offset 04h) 

The Association Bitmap for RCIEPs is a read-only register that sets the bits corresponding to the Device Numbers of RCIEPs associated with the Root Complex Event Collector on the same Bus Number as the Event Collector itself. The bit corresponding to the Device Number of the Root Complex Event Collector must always be Set.

### 7.9.10.3 RCEC Associated Bus Numbers Register (Offset 08h)

The RCEC Associated Bus Numbers Register is a read-only register that indicates an additional range of Bus Numbers containing RCIEPs associated with this Root Complex Event Collector. It is permitted for Functions other than RCIEPs, including Root Ports, to appear within the Association Bus Range. Only RCIEPs in the range are associated with this Root Complex Event Collector. This register is present if the Capability Version is 2 h or greater.

This register does not indicate association between an Event Collector and any Virtual Functions within the Association Bus Range (see § Section 9.2.1.2). This register does not indicate association between an Event Collector and any Function on the same Bus Number as the Event Collector itself, however it is permitted for the Association Bus Range to include the Bus Number of the Root Complex Event Collector.
![img-266.jpeg](img-266.jpeg)

Figure 7-277 RCEC Associated Bus Numbers Register

Table 7-248 RCEC Associated Bus Numbers Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $15: 8$ | RCEC Next Bus - This field contains the lowest additional bus number containing RCIEPs associated with this Root Complex Event Collector. If all of the Devices associated with this Root Complex Event Collector are on the same bus as the Event Collector, then this field must be set to FFh. | HwInit |
| $23: 16$ | RCEC Last Bus - This field contains the highest additional bus number containing RCIEPs associated with this Root Complex Event Collector. <br> If all of the Devices associated with this Root Complex Event Collector are on the same bus as the Event Collector, then this field must be set to 00 h . | HwInit |

# IMPLEMENTATION NOTE: 

## RCEC ASSOCIATED BUS NUMBER COMPATIBILITY WITH LEGACY SOFTWARE

Legacy software may not support the use of the RCEC Associated Bus Numbers Register as a mechanism to associate Devices with a RCEC. Such software may see events in the RCEC from Devices on different bus numbers that it does not consider to be associated with the Root Complex Event Collector. System Software is strongly encouraged to report all events seen on the Root Complex Event Collector, regardless of whether or not it can determine association.

### 7.9.11 Multicast Extended Capability

Multicast is an optional normative functionality that is controlled by the Multicast Extended Capability structure. The Multicast Extended Capability is applicable to Root Ports, RCRBs, Switch Ports, Endpoint Functions, and RCiEPs. It is not applicable to PCI Express to PCI/PCI-X Bridges.

Multicast support is optional in SR-IOV devices. If a VF implements a Multicast capability, its associated PF must implement a Multicast capability.

In the cases of a Switch or Root Complex or a component that contains multiple Functions, multiple copies of this Capability structure are required - one for each Endpoint Function, Switch Port, or Root Port that supports Multicast. To provide implementation efficiencies, certain fields within each of the Multicast Extended Capability structures within a component must be programmed the same and results are indeterminate if this is not the case. The fields and registers that must be configured with the same values include MC_Enable, MC_Num_Group, MC_Base_Address and MC_Index_Position. These same fields in an Endpoint's Multicast Extended Capability structure must match those configured into a Multicast Extended Capability structure of the Switch or Root Complex above the Endpoint or in which the RCiEP is integrated.

![img-267.jpeg](img-267.jpeg)

Figure 7-278 Multicast Extended Capability Structure 5

# 7.9.11.1 Multicast Extended Capability Header (Offset 00h) 

\$ Figure 7-279 details allocation of the fields in the Multicast Extended Capability Header and \$ Table 7-249 provides the respective bit definitions.
![img-268.jpeg](img-268.jpeg)

Figure 7-279 Multicast Extended Capability Header 5

Table 7-249 Multicast Extended Capability Header 5

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 15:0 | PCI Express Extended Capability ID - This field is a PCI-SIG defined ID number that indicates the nature and format of the Extended Capability. | RO |

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
|  | PCI Express Extended Capability ID for the Multicast Extended Capability is 0012h. |  |
| $19: 16$ | Capability Version - This field is a PCI-SIG defined version number that indicates the version of the <br> Capability structure present. <br> Must be 1h for this version of the specification. | RO |
| $31: 20$ | Next Capability Offset - This field contains the offset to the next PCI Express Extended Capability <br> structure or 000h if no other items exist in the linked list of Capabilities. | RO |

# 7.9.11.2 Multicast Capability Register (Offset 04h) 

§ Figure 7-280 details allocation of the fields in the Multicast Capability Register and § Table 7-250 provides the respective bit definitions.
![img-269.jpeg](img-269.jpeg)

Figure 7-280 Multicast Capability Register

Table 7-250 Multicast Capability Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| $5: 0$ | MC_Max_Group - Value indicates the maximum number of Multicast Groups that the component <br> supports, encoded as M-1. A value of 00h indicates that one Multicast Group is supported. <br> For VFs, this field is RsvdP. The value from the associated PF applies. | RO |
|  |  | VF RsvdP |
| $13: 8$ | MC_Window_Size_Requested - In Endpoints, the log $_{2}$ of the Multicast Window size requested. RsvdP in <br> Switch and Root Ports. <br> For VFs, this field is RsvdP. The value from the associated PF applies. | RO |
| 15 | MC_ECRC_Regeneration_Supported - If Set, indicates that ECRC regeneration is supported. <br> This bit must not be Set unless the Function supports Advanced Error Reporting, and the ECRC Check <br> Capable bit in the Advanced Error Capabilities and Control Register is also Set. However, if ECRC <br> regeneration is supported, its operation is not contingent upon the setting of the ECRC Check Enable bit in <br> the Advanced Error Capabilities and Control Register. This bit is applicable to Switch and Root Ports and <br> is RsvdP in all other Functions. | RO/RsvdP |

# 7.9.11.3 Multicast Control Register (Offset 06h) 

\$ Table 7-251 details allocation of the fields in the Multicast Control Register and \$ Table 7-251 provides the respective bit definitions.
![img-270.jpeg](img-270.jpeg)

Figure 7-281 Multicast Control Register

Table 7-251 Multicast Control Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 5:0 | MC_Num_Group - Value indicates the number of Multicast Groups configured for use, encoded as N-1. The default value of 000000 b indicates that one Multicast Group is configured for use. Behavior is undefined if value exceeds MC_Max_Group. This parameter indirectly defines the upper limit of the Multicast address range. This field is ignored if MC_Enable is Clear. Default value is 000000 b. <br> For VFs, this field is RsvdP. The value from the associated PF applies. | RW <br> VF RsvdP |
| 15 | MC_Enable - When Set, the Multicast mechanism is enabled for the component. Default value is 0 b. | RW |

### 7.9.11.4 MC_Base_Address Register (Offset 08h) $\quad$

The MC_Base_Address Register contains the MC_Base_Address and the MC_Index_Position. \$ Figure 7-282 details allocation of the fields in the MC_Base_Address Register and \$ Table 7-252 provides the respective bit definitions.
![img-271.jpeg](img-271.jpeg)

Figure 7-282 MC_Base_Address Register

Table 7-252 MC_Base_Address Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 5:0 | MC_Index_Position - The location of the LSB of the Multicast Group number within the address. Behavior is undefined if this value is less than 12 and MC_Enable is Set. Default is 0. <br> For VFs, this field is RsvdP. The value from the associated PF applies. | RW <br> VF RsvdP |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 63:12 | MC_Base_Address - The base address of the Multicast address range. The behavior is undefined if MC_Enable is Set and bits in this field corresponding to address bits that contain the Multicast Group number or address bits less than MC_Index_Position are non-zero. Default is 0. <br> For VFs, this field is RsvdP. The value from the associated PF applies. | RW <br> VF RsvdP |

# 7.9.11.5 MC_Receive Register (Offset 10h) 

The MC_Receive Register provides a bit vector denoting which Multicast groups the Function should accept, or in the case of Switch and Root Complex Ports, forward Multicast TLPs. This register is required in all Functions that implement the MC Capability structure.
\$ Figure 7-283 details allocation of the fields in the MC_Receive Register and \$ Table 7-253 provides the respective bit definitions.
![img-272.jpeg](img-272.jpeg)

Figure 7-283 MC_Receive Register

Table 7-253 MC_Receive Register

| Bit Location | Register Description | Attributes |
| :-- | :-- | :--: |
| MC_Max_Group:0 | MC_Receive - For each bit that's Set, this Function gets a copy of any Multicast TLPs for the <br> associated Multicast Group. Bits above MC_Num_Group are ignored by hardware. Default value of <br> each bit is 0b. | RW |
| All other bits | Reserved | RsvdP |

### 7.9.11.6 MC_Block_All Register (Offset 18h) 

The MC_Block_All Register provides a bit vector denoting which Multicast groups the Function should block. This register is required in all Functions that implement the MC Capability structure.
\$ Figure 7-284 details allocation of the fields in the MC_Block_All Register and \$ Table 7-254 provides the respective bit definitions.
![img-273.jpeg](img-273.jpeg)

Figure 7-284 MC_Block_All Register

Table 7-254 MC_Block_All Register

| Bit Location | Register Description | Attributes |
| :-- | :-- | :--: |
| MC_Max_Group:0 | MC_Block_All - For each bit that is Set, this Function is blocked from sending TLPs to the associated <br> Multicast Group. Bits above MC_Num_Group are ignored by hardware. Default value of each bit is 0b. | RW |
| All other bits | Reserved | RsvdP |

# 7.9.11.7 MC_Block_Untranslated Register (Offset 20h) 

The MC_Block_Untranslated Register is used to determine whether or not a TLP that includes an Untranslated Address should be blocked. This register is required in all Functions that implement the MC Capability structure. However, an Endpoint Function that does not implement the ATS capability may implement this register as RsvdP.
§ Figure 7-285 details allocation of the fields in the MC_Block_Untranslated Register and § Table 7-255 provides the respective bit definitions.
![img-274.jpeg](img-274.jpeg)

Figure 7-285 MC_Block_Untranslated Register

Table 7-255 MC_Block_Untranslated Register

| Bit Location | Register Description | Attributes |
| :-- | :-- | :--: |
| MC_Max_Group:0 | MC_Block_Untranslated - For each bit that is Set, this Function is blocked from sending TLPs <br> containing Untranslated Addresses to the associated MCG. Bits above MC_Num_Group are ignored by <br> hardware. Default value of each bit is Ob. | RW |
| All other bits | Reserved | RsvdP |

### 7.9.11.8 MC_Overlay_BAR Register (Offset 28h) $\S$

The MC_Overlay_BAR Register is required in Switch and Root Complex Ports that support the Multicast Extended Capability and not implemented in Endpoints. Software must interpret the Device/Port Type field in the PCI Express Capabilities Register to determine if the MC_Overlay_BAR Register is present in a Function.

The MC_Overlay_BAR specifies the base address of a window in unicast space onto which Multicast TLPs going out an Egress Port are overlaid by a process of address replacement. This allows a single BAR in an Endpoint attached to the Switch or Root Port to be used for both unicast and Multicast traffic. At a Switch Upstream Port, it allows the Multicast address range, or a portion of it, to be overlayed onto host memory.
§ Figure 7-286 details allocation of the fields in the MC_Overlay_BAR Register and § Table 7-256 provides the respective bit definitions.

|  |  | 6.5 |  |
| :--: | :--: | :--: | :--: |
|  | MC_Overlay_BAR [31:6] | MC_Overlay_Size |  |
|  | MC_Overlay_BAR [63:32] |  |  |
|  |  | 4.010 |  |

Figure 7-286 MC_Overlay_BAR Register

Table 7-256 MC_Overlay_BAR Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $5: 0$ | MC_Overlay_Size - If 6 or greater, specifies the size in bytes of the overlay aperture as a power of 2. If less than 6 , disables the overlay mechanism. Default value is 000000 b . | RW |
| $63: 6$ | MC_Overlay_BAR - Specifies the base address of the window onto which MC TLPs passing through this Function will be overlaid. Default value is 0 . | RW |

# 7.9.12 Dynamic Power Allocation Extended Capability (DPA Capability) 

The DPA Capability structure is shown in $\S$ Figure 7-287.
![img-275.jpeg](img-275.jpeg)

Figure 7-287 Dynamic Power Allocation Extended Capability Structure

# 7.9.12.1 DPA Extended Capability Header (Offset 00h) 

![img-276.jpeg](img-276.jpeg)

Figure 7-288 DPA Extended Capability Header

Table 7-257 DPA Extended Capability Header

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| $15: 0$ | PCI Express Extended Capability ID - This field is a PCI-SIG defined ID number that indicates the nature <br> and format of the Extended Capability. <br> PCI Express Extended Capability ID for the DPA Extended Capability is 0016h. | RO |
| $19: 16$ | Capability Version - This field is a PCI-SIG defined version number that indicates the version of the <br> Capability structure present. <br> Must be 1h for this version of the specification. | RO |
| $31: 20$ | Next Capability Offset - This field contains the offset to the next PCI Express Extended Capability <br> structure or 000h if no other items exist in the linked list of Capabilities. | RO |

### 7.9.12.2 DPA Capability Register (Offset 04h)

![img-277.jpeg](img-277.jpeg)

Figure 7-289 DPA Capability Register

Table 7-258 DPA Capability Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| $4: 0$ | Substate_Max - Value indicates the maximum substate number, which is the total number of supported <br> substates minus one. A value of 00000 b indicates support for one substate. | RO |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 9:8 | Transition Latency Unit (Tlunit) - A substate's Transition Latency Value is multiplied by the Transition Latency Unit to determine the maximum Transition Latency for the substate. <br> Defined encodings are | RO |
|  | 00b 1 ms |  |
|  | 01b 10 ms |  |
|  | 10b 100 ms |  |
|  | 11b | Reserved |
| 13:12 | Power Allocation Scale (PAS) - The encodings provide the scale to determine power allocation per substate in Watts. The value corresponding to the substate in the Substate Power Allocation field is multiplied by this field to determine the power allocation for the substate. <br> Defined encodings are | RO |
|  | 00b 10.0x |  |
|  | 01b 1.0x |  |
|  | 10b 0.1x |  |
|  | 11b 0.01x |  |
| 23:16 | Transition Latency Value $\mathbf{0}$ (XIcy0) - This value is multiplied by the Transition Latency Unit to determine the maximum Transition Latency for the substate | RO |
| $31: 24$ | Transition Latency Value 1 (XIcy1) - This value is multiplied by the Transition Latency Unit to determine the maximum Transition Latency for the substate. | RO |

# 7.9.12.3 DPA Latency Indicator Register (Offset 08h) 

![img-278.jpeg](img-278.jpeg)

Figure 7-290 DPA Latency Indicator Register

Table 7-259 DPA Latency Indicator Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $31: 0$ | Transition Latency Indicator Bits - Each bit indicates which Transition Latency Value is associated with the corresponding substate. A value of 0 b indicates Transition Latency Value 0 ; a value of 1 b indicates Transition Latency Value 1. <br> Only bits [Substate_Max:0] are defined. Bits above Substate_Max are RsvdP. | RO |

# 7.9.12.4 DPA Status Register (Offset 0Ch) 

![img-279.jpeg](img-279.jpeg)

Figure 7-291 DPA Status Register

Table 7-260 DPA Status Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 4:0 | Substate Status - Indicates current substate for this Function. <br> Default is 0 0000b. | RO |
| 8 | Substate Control Enabled - Used by software to disable the Substate Control field in the DPA Control <br> Register. Hardware sets this bit following a Conventional Reset or FLR. Software clears this bit by writing <br> a 1b to it. Software is unable to set this bit directly. <br> When this bit is Set, the Substate Control field determines the current substate. <br> When this bit is Clear, the Substate Control field has no effect on the current substate. <br> Default value is 1b. | RW1C |

### 7.9.12.5 DPA Control Register (Offset 0Eh) 

![img-280.jpeg](img-280.jpeg)

Figure 7-292 DPA Control Register

Table 7-261 DPA Control Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 4:0 | Substate Control - Used by software to configure the Function substate. Software writes the substa <br> value in this field to initiate a substate transition. <br> When the Substate Control Enabled bit in the DPA Status Register is Set, this field determines the Function <br> substate. <br> When the Substate Control Enabled bit in the DPA Status Register is Clear, this field has no effect on the <br> Function substate. | RW |

| Bit Location | Register Description | Attributes |
| :-- | :-- | :-- |
| Default value is 0 0000b. |  |  |

# 7.9.12.6 DPA Power Allocation Array 

![img-281.jpeg](img-281.jpeg)

Figure 7-293 DPA Power Allocation Array

Each Substate Power Allocation register indicates the power allocation value for its associated substate. The number of Substate Power Allocation registers implemented must be equal to the number of substates supported by Function, which is Substate_Max plus one.
![img-282.jpeg](img-282.jpeg)

Figure 7-294 Substate Power Allocation Register (0 to Substate_Max)

Table 7-262 Substate Power Allocation Register (0 to Substate_Max)

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 7:0 | Substate Power Allocation - The value in this field is multiplied by the Power Allocation Scale to <br> determine power allocation in Watts for the associated substate. | RO |

### 7.9.13 TPH Requester Extended Capability

The TPH Requester Extended Capability structure is required for all Functions that are capable of generating Request TLPs with TPH. For a Multi-Function Device, this capability must be present in each Function that is capable of generating Request TLPs with TPH.

The capability is optional for PFs and VFs. However, if a VF associated with a given PF contains the capability, all VFs associated with that PF must contain the capability.

For fields in the TPH Requester Capability Register (offset 04h), all VFs associated with a given PF must have the same values in all fields, but the PF's fields may have values different from those in its VFs.

![img-283.jpeg](img-283.jpeg)

Figure 7-295 TPH Extended Capability Structure

# 7.9.13.1 TPH Requester Extended Capability Header (Offset 00h) 

![img-284.jpeg](img-284.jpeg)

Figure 7-296 TPH Requester Extended Capability Header

Table 7-263 TPH Requester Extended Capability Header

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 15:0 | PCI Express Extended Capability ID - This field is a PCI-SIG defined ID number that indicates the nature and format of the Extended Capability. <br> PCI Express Extended Capability ID for the TPH Requester Extended Capability is 0017h. | RO |
| 19:16 | Capability Version - This field is a PCI-SIG defined version number that indicates the version of the Capability structure present. <br> Must be 1 h for this version of the specification. | RO |
| $31: 20$ | Next Capability Offset - This field contains the offset to the next PCI Express Extended Capability structure or 000 h if no other items exist in the linked list of Capabilities. | RO |

### 7.9.13.2 TPH Requester Capability Register (Offset 04h)

![img-285.jpeg](img-285.jpeg)

Figure 7-297 TPH Requester Capability Register

Table 7-264 TPH Requester Capability Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 0 | No ST Mode Supported - If set indicates that the Function supports the No ST Mode of operation. <br> This mode is required to be supported by all Functions that implement this Capability structure. This bit must have a value of 1 b . | RO |
| 1 | Interrupt Vector Mode Supported - If set indicates that the Function supports the Interrupt Vector Mode of operation. | RO |
| 2 | Device Specific Mode Supported - If set indicates that the Function supports the Device Specific Mode of operation. | RO |
| 8 | Extended TPH Requester Supported - If Set indicates that the Function is capable of generating Requests with additional TPH information using the TPH TLP Prefix. <br> See § Section 2.2.7.1.1 for additional details. | RO |
| 10:9 | ST Table Location - Value indicates if and where the ST Table is located. <br> Defined Encodings are: <br> 00b ST Table is not present <br> 01b ST Table is located in the TPH Requester Extended Capability structure <br> 10b ST Table is located in the MSI-X Table (see § Section 7.7.2) <br> 11b Reserved <br> A Function that only supports the No ST Mode of operation must have a value of 00 b in this field. <br> A Function may report a value of 10 b only if it implements an MSI-X Capability. | RO |
| 26:16 | ST Table Size - Value indicates the maximum number of ST Table entries the Function may use. Software reads this field to determine the ST Table Size N, which is encoded as N-1. For example, a returned value of 00000000011 b indicates a table size of four entries. <br> There is an upper limit of 64 entries when the ST Table is located in the TPH Requester Extended Capability structure. <br> When the ST Table is located in the MSI-X Table, this value is limited by the size of the MSI-X Table. <br> This field is only applicable for Functions that implement an ST Table as indicated by the ST Table Location field. Otherwise, the value in this field is undefined. | RO |

# 7.9.13.3 TPH Requester Control Register (Offset 08h) 

![img-286.jpeg](img-286.jpeg)

Figure 7-298 TPH Requester Control Register

Table 7-265 TPH Requester Control Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 2:0 | ST Mode Select - selects the ST Mode of operation. | RW |
|  | Defined encodings are: |  |
|  | 000b No ST Mode |  |
|  | 001b | Interrupt Vector Mode |
|  | 010b | Device Specific Mode |
|  | others | reserved for future use |
|  | Functions that support only the No ST Mode of operation must hardwire this field to 000b. |  |
|  | Function operation is undefined if software enables a mode of operation that does not correspond to a mode supported by the Function. |  |
|  | The default value of this field is 000 b . |  |
|  | See § Section 6.17.3 for details on ST modes of operation. |  |
| 9:8 | TPH Requester Enable - Controls the ability to issue Request TLPs using either TPH or Extended TPH. | RW |
|  | Defined encodings are: |  |
|  | 00b | Function operating as a Requester is not permitted to issue Requests with TPH or Extended TPH |
|  | 01b | Function operating as a Requester is permitted to issue Requests with TPH and is not permitted to issue Requests with Extended TPH |
|  | 10b | Reserved |
|  | 11b | Function operating as a Requester is permitted to issue Requests with TPH and Extended TPH |
|  | Functions that advertise that they do not support Extended TPH are permitted to hardwire bit 9 of this field to 0 b . |  |
|  | The default value of this field is 00 b . |  |

# 7.9.13.4 TPH ST Table (Starting from Offset 0Ch) 

![img-287.jpeg](img-287.jpeg)

Figure 7-299 TPH ST Table

The TPH ST Table must be implemented in the TPH Requester Extended Capability structure if the value of the ST Table Location field is 01b. For all other values, the ST Entry registers must not be implemented. Each implemented ST Entry is 16 bits. The number of ST Entry registers implemented must be equal to the number of ST Table entries supported by the Function, which is the value of the ST Table Size field plus one.

| 15 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

![img-288.jpeg](img-288.jpeg)

Figure 7-301 DPC Extended Capability - Non-Flit Mode

![img-289.jpeg](img-289.jpeg)

Figure 7-302 DPC Extended Capability - Flit Mode

# 7.9.14.1 DPC Extended Capability Header (Offset 00h) 

![img-290.jpeg](img-290.jpeg)

Figure 7-303 DPC Extended Capability Header

Table 7-267 DPC Extended Capability Header

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $15: 0$ | PCI Express Extended Capability ID - This field is a PCI-SIG defined ID number that indicates the nature and format of the extended capability. <br> PCI Express Extended Capability ID for the DPC Extended Capability is 001Dh. | RO |
| $19: 16$ | Capability Version - This field is a PCI-SIG defined version number that indicates the version of the capability structure present. <br> Must be 1 h for this version of the specification. | RO |
| $31: 20$ | Next Capability Offset - This field contains the offset to the next PCI Express Extended Capability structure or 000 h if no other items exist in the linked list of capabilities. | RO |

### 7.9.14.2 DPC Capability Register (Offset 04h)

![img-291.jpeg](img-291.jpeg)

Figure 7-304 DPC Capability Register

Table 7-268 DPC Capability Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $4: 0$ | DPC Interrupt Message Number - When MSI/MSI-X is implemented, this field indicates which MSI/MSI-X vector is used for the interrupt message generated in association with the DPC Capability structure. | RO |
|  | For MSI, the value in this field indicates the offset between the base Message Data and the interrupt message that is generated. Hardware is required to update this field so that it is correct if the number of MSI Messages assigned to the Function changes when software writes to the Multiple Message Enable field in the Message Control Register for MSI. |  |
|  | For MSI-X, the value in this field indicates which MSI-X Table entry is used to generate the interrupt message. The entry must be one of the first 32 entries even if the Function implements more than 32 entries. For a given MSI-X implementation, the entry must remain constant. |  |
|  | If both MSI and MSI-X are implemented, they are permitted to use different vectors, though software is permitted to enable only one mechanism at a time. If MSI-X is enabled, the value in this field must indicate the vector for MSI-X. If MSI is enabled or neither is enabled, the value in this field must indicate the vector for MSI. If software enables both MSI and MSI-X at the same time, the value in this field is undefined. |  |
| 5 | RP Extensions for DPC - If Set, this bit indicates that a Root Port supports a defined set of DPC Extensions that are specific to Root Ports. Switch Downstream Ports must not Set this bit. | RO |
| 6 | Poisoned TLP Egress Blocking Supported - If Set, this bit indicates that the Root Port or Switch Downstream Port supports the ability to block the transmission of a poisoned TLP from its Egress Port. Root Ports that support RP Extensions for DPC must Set this bit. | RO |
| 7 | DPC Software Triggering Supported - If Set, this bit indicates that a Root Port or Switch Downstream Port supports the ability for software to trigger DPC. Root Ports that support RP Extensions for DPC must Set this bit. | RO |
| $11: 8$ | RP PIO Log Size[3:0] - This field indicates how many DWORDs are allocated for the RP PIO log registers, comprised by the RP PIO Header Log, the RP PIO ImpSpec Log, and RP PIO TLP Prefix Log. <br> - If the Root Port does not support RP Extensions for DPC, the value of this field must be Zero. <br> - If the Root Port supports RP Extensions for DPC but does not support Flit Mode, the value of this field must be 4 or greater. <br> - If the Root Port supports both RP Extensions for DPC and Flit Mode, see § Section 6.2.11.3 for requirements. <br> See § Section 7.9.14.11, § Section 7.9.14.12, and § Section 7.9.14.13. | RO |
| 12 | DL_Active ERR_COR Signaling Supported - If Set, this bit indicates that the Root Port or Switch Downstream Port supports the ability to signal with ERR_COR when the Link transitions to the DL_Active state. Root Ports that support RP Extensions for DPC must Set this bit. | RO |
| 13 | RP PIO Log Size[4] - This bit is an extension of RP PIO Log Size[3:0] for use in Flit Mode. If Flit Mode is not supported, this bit is RsvdP. | RO/RsvdP |

# 7.9.14.3 DPC Control Register (Offset 06h) 

![img-292.jpeg](img-292.jpeg)

Figure 7-305 DPC Control Register

Table 7-269 DPC Control Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $1: 0$ | DPC Trigger Enable - This field enables DPC and controls the conditions that cause DPC to be triggered. <br> Defined encodings are: <br> 00b DPC is disabled <br> 01b DPC is enabled and is triggered when the Downstream Port detects an unmasked uncorrectable error or when the Downstream Port receives an ERR_FATAL Message <br> 10b DPC is enabled and is triggered when the Downstream Port detects an unmasked uncorrectable error or when the Downstream Port receives an ERR_NONFATAL or ERR_FATAL Message <br> 11b Reserved <br> Default value of this field is 00 b. | RW |
| 2 | DPC Completion Control - This bit controls the Completion Status for Completions formed during DPC. See § Section 2.9.3 . <br> Defined encodings are: <br> 0b Completer Abort (CA) Completion Status <br> 1b Unsupported Request (UR) Completion Status <br> Default value of this bit is 0 b . | RW |
| 3 | DPC Interrupt Enable - When Set, this bit enables the generation of an interrupt to indicate that DPC has been triggered. See § Section 6.2.11.1. <br> Default value of this bit is 0 b . | RW |
| 4 | DPC ERR_COR Enable - When Set, this bit enables the sending of an ERR_COR Message to indicate that DPC has been triggered. See § Section 6.2.11.2. <br> Default value of this bit is 0 b . | RW |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 5 | Poisoned TLP Egress Blocking Enable - This bit must be RW if the Poisoned TLP Egress Blocking Supported bit is Set; otherwise, it is permitted to be hardwired to 0b. Software must not Set this bit unless the Poisoned TLP Egress Blocking Supported bit is Set. <br> When Set, this bit enables the associated Egress Port to block the transmission of poisoned TLPs. See $\S$ Section 2.7.2.1. <br> Default value of this bit is 0 b . | RW/RO |
| 6 | DPC Software Trigger - This bit must be RW if the DPC Software Triggering Supported bit is Set; otherwise, it is permitted to be hardwired to 0 b. <br> If DPC is enabled and the DPC Trigger Status bit is Clear, when software writes 1b to this bit, DPC is triggered. Otherwise, software writing a 1b to this bit has no effect. <br> It is permitted to write 1 b to this bit while simultaneously writing updated values to other fields in this register, notably the DPC Trigger Enable field. For this case, the DPC Software Trigger semantics are based on the updated value of the DPC Trigger Enable field. <br> This bit always returns 0 b when read. | RW/RO |
| 7 | DL_Active ERR_COR Enable - This bit must be RW if the DL_Active ERR_COR Signaling Supported bit is Set; otherwise, it is permitted to be hardwired to 0b. Software must not Set this bit unless the DL_Active ERR_COR Signaling Supported bit is Set. <br> When Set, this bit enables the associated Downstream Port to signal with ERR_COR when the Link transitions to the DL_Active state. See $\S$ Section 6.2.11.5. <br> Default value of this bit is 0 b . | RW/RO |
| 8 | DPC SIG_SFW Enable - This bit must be implemented if the ERR_COR Subclass Capable bit in the Device Capabilities Register is Set; otherwise, it is permitted to be hardwired to 0b. If the ERR_COR Subclass Capable bit is Clear and software Sets this bit, the behavior is undefined. <br> When Set, this bit enables sending an ERR_COR Message to indicate a DPC event that's been enabled for ERR_COR signaling. See $\S$ Section 6.2.11.2 and $\S$ Section 6.2.11.5. This is an additional and alternative way to enable overall DPC ERR_COR signaling beyond the Correctable Error Reporting Enable bit in the Device Control Register. This bit does not affect a Function's ability to send ERR_COR Messages other than the ECS SIG_SFW subclass. <br> Default value of this bit is 0 b . | RW/RO |

# 7.9.14.4 DPC Status Register (Offset 08h) 

![img-293.jpeg](img-293.jpeg)

Figure 7-306 DPC Status Register

Table 7-270 DPC Status Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 0 | DPC Trigger Status - When Set, this bit indicates that DPC has been triggered, and by definition the Port is "in DPC". DPC is event triggered. <br> While this bit is Set, hardware must direct the LTSSM to the Disabled State. This bit must be cleared before the LTSSM can be released from the Disabled State, after which the Port is no longer in DPC, and the LTSSM must transition to the Detect State. See § Section 6.2.11 for requirements on how long software must leave the Downstream Port in DPC. Once these requirements are met, software is permitted to clear this bit regardless of the state of other status bits associated with the triggering event. <br> After clearing this bit, software must honor timing requirements defined in § Section 6.6.1 with respect to the first Configuration Read following a Conventional Reset. <br> Default value of this bit is Ob. | RW1CS |
| 2:1 | DPC Trigger Reason - This field indicates why DPC has been triggered. Defined encodings are: <br> 00b DPC was triggered due to an unmasked uncorrectable error <br> 01b DPC was triggered due to receiving an ERR_NONFATAL <br> 10b DPC was triggered due to receiving an ERR_FATAL <br> 11b DPC was triggered due to a reason that is indicated by the DPC Trigger Reason Extension field. <br> This field is valid only when the DPC Trigger Status bit is Set; otherwise the value of this field is undefined. | ROS |
| 3 | DPC Interrupt Status - This bit is Set if DPC is triggered while the DPC Interrupt Enable bit is Set. This may cause the generation of an interrupt. See § Section 6.2.11.1. <br> Default value of this bit is Ob. | RW1CS |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 4 | DPC RP Busy - When the DPC Trigger Status bit is Set and this bit is Set, the Root Port is busy with internal activity that must complete before software is permitted to Clear the DPC Trigger Status bit. If software Clears the DPC Trigger Status bit while this bit is Set, the behavior is undefined. <br> This field is valid only when the DPC Trigger Status bit is Set; otherwise the value of this field is undefined. <br> This bit is applicable only for Root Ports that support RP Extensions for DPC, and is Reserved for Switch Downstream Ports. <br> Default value of this bit is undefined. | RO/RsvdZ |
| 6:5 | DPC Trigger Reason Extension - This field serves as an extension to the DPC Trigger Reason field. When that field is valid and has a value of 11 b , this field indicates why DPC has been triggered. Defined encodings are: <br> 00b DPC was triggered due to an RP PIO error <br> 01b DPC was triggered due to the DPC Software Trigger bit <br> 10b Reserved <br> 11b Reserved <br> This field is valid only when the DPC Trigger Status bit is Set and the value of the DPC Trigger Reason field is 11 b ; otherwise the value of this field is undefined. | ROS |
| 12:8 | RP PIO First Error Pointer - The value of this field identifies a bit position in the RP PIO Status Register, and this field is considered valid when that bit is Set. When this field is valid, and software writes a 1 b to the indicated RP PIO Status bit (thus clearing it), this field must revert to its default value. <br> This field is applicable only for Root Ports that support RP Extensions for DPC, and otherwise is Reserved. <br> If this field is not Reserved, its default value is 11111 b , indicating a permanently Reserved RP PIO Status bit, thus guaranteeing that this field is not considered valid. | ROS/RsvdZ |
| 13 | DPC SIG_SFW Status - If the Function supports ERR_COR Subclass capability, this bit must be implemented; otherwise, it must be hardwired to 0b. If implemented, this bit is Set when a SIG_SFW ERR_COR Message is sent to signal a DPC event. See § Section 6.2.11.2 and § Section 6.2.11.5 . <br> Default value of this bit is 0 b | RW1CS/RsvdZ |

# 7.9.14.5 DPC Error Source ID Register (Offset OAh) 

![img-294.jpeg](img-294.jpeg)

Figure 7-307 DPC Error Source ID Register

Table 7-271 DPC Error Source ID Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 15:0 | DPC Error Source ID - When the DPC Trigger Reason field indicates that DPC was triggered due to the <br> reception of an ERR_NONFATAL or ERR_FATAL, this register contains the Requester ID of the received <br> Message. Otherwise, the value of this register is undefined. | ROS |

# 7.9.14.6 RP PIO Status Register (Offset 0Ch) 

This register is present only in Root Ports that support RP Extensions for DPC. See § Section 6.2.11.3.
![img-295.jpeg](img-295.jpeg)

Figure 7-308 RP PIO Status Register

Table 7-272 RP PIO Status Register

| Bit Location | Register Description | Attributes | Default |
| :--: | :-- | :--: | :-- |
| 0 | Cfg UR Cpl - Configuration Request received UR Completion | RW1CS | 0b |
| 1 | Cfg CA Cpl - Configuration Request received CA Completion | RW1CS | 0b |
| 2 | Cfg CTO - Configuration Request Completion Timeout | RW1CS | 0b |
| 8 | I/O UR Cpl - I/O Request received UR Completion | RW1CS | 0b |
| 9 | I/O CA Cpl - I/O Request received CA Completion | RW1CS | 0b |
| 10 | I/O CTO - I/O Request Completion Timeout | RW1CS | 0b |
| 16 | Mem UR Cpl - Memory Request received UR Completion | RW1CS | 0b |
| 17 | Mem CA Cpl - Memory Request received CA Completion | RW1CS | 0b |
| 18 | Mem CTO - Memory Request Completion Timeout | RW1CS | 0b |
| 31 | Permanently_Reserved Permanently_Reserved, since the default RP PIO First Error Pointer <br> field value points to it. | RsvdZ | 0b |

# 7.9.14.7 RP PIO Mask Register (Offset 10h) 

This register is present only in Root Ports that support RP Extensions for DPC. See § Section 6.2.11.3.
![img-296.jpeg](img-296.jpeg)

Figure 7-309 RP PIO Mask Register

Table 7-273 RP PIO Mask Register

| Bit Location | Register Description | Attributes | Default |
| :--: | :-- | :--: | :--: |
| 0 | Cfg UR Cpl - Configuration Request received UR Completion | RWS | 1 b |
| 1 | Cfg CA Cpl - Configuration Request received CA Completion | RWS | 1 b |
| 2 | Cfg CTO - Configuration Request Completion Timeout | RWS | 1 b |
| 8 | I/O UR Cpl - I/O Request received UR Completion | RWS | 1 b |
| 9 | I/O CA Cpl - I/O Request received CA Completion | RWS | 1 b |
| 10 | I/O CTO - I/O Request Completion Timeout | RWS | 1 b |
| 16 | Mem UR Cpl - Memory Request received UR Completion | RWS | 1 b |
| 17 | Mem CA Cpl - Memory Request received CA Completion | RWS | 1 b |
| 18 | Mem CTO - Memory Request Completion Timeout | RWS | 1 b |

### 7.9.14.8 RP PIO Severity Register (Offset 14h)

This register is present only in Root Ports that support RP Extensions for DPC. See § Section 6.2.11.3.

![img-297.jpeg](img-297.jpeg)

Figure 7-310 RP PIO Severity Register 5

Table 7-274 RP PIO Severity Register 5

| Bit Location | Register Description | Attributes | Default |
| :--: | :-- | :--: | :--: |
| 0 | Cfg UR Cpl - Configuration Request received UR Completion | RWS | 0 b |
| 1 | Cfg CA Cpl - Configuration Request received CA Completion | RWS | 0 b |
| 2 | Cfg CTO - Configuration Request Completion Timeout | RWS | 0 b |
| 8 | I/O UR Cpl - I/O Request received UR Completion | RWS | 0 b |
| 9 | I/O CA Cpl - I/O Request received CA Completion | RWS | 0 b |
| 10 | I/O CTO - I/O Request Completion Timeout | RWS | 0 b |
| 16 | Mem UR Cpl - Memory Request received UR Completion | RWS | 0 b |
| 17 | Mem CA Cpl - Memory Request received CA Completion | RWS | 0 b |
| 18 | Mem CTO - Memory Request Completion Timeout | RWS | 0 b |

# 7.9.14.9 RP PIO SysError Register (Offset 18h) 

This register is present only in Root Ports that support RP Extensions for DPC. See § Section 6.2.11.3.

![img-298.jpeg](img-298.jpeg)

Figure 7-311 RP PIO SysError Register

Table 7-275 RP PIO SysError Register

| Bit Location | Register Description | Attributes | Default |
| :--: | :-- | :--: | :--: |
| 0 | Cfg UR Cpl - Configuration Request received UR Completion | RWS | 0 b |
| 1 | Cfg CA Cpl - Configuration Request received CA Completion | RWS | 0 b |
| 2 | Cfg CTO - Configuration Request Completion Timeout | RWS | 0 b |
| 8 | I/O UR Cpl - I/O Request received UR Completion | RWS | 0 b |
| 9 | I/O CA Cpl - I/O Request received CA Completion | RWS | 0 b |
| 10 | I/O CTO - I/O Request Completion Timeout | RWS | 0 b |
| 16 | Mem UR Cpl - Memory Request received UR Completion | RWS | 0 b |
| 17 | Mem CA Cpl - Memory Request received CA Completion | RWS | 0 b |
| 18 | Mem CTO - Memory Request Completion Timeout | RWS | 0 b |

# 7.9.14.10 RP PIO Exception Register (Offset 1Ch) 

This register is present only in Root Ports that support RP Extensions for DPC. See § Section 6.2.11.3.

![img-299.jpeg](img-299.jpeg)

Figure 7-312 RP PIO Exception Register

Table 7-276 RP PIO Exception Register

| Bit Location | Register Description | Attributes | Default |
| :--: | :-- | :--: | :--: |
| 0 | Cfg UR Cpl - Configuration Request received UR Completion | RWS | 0 b |
| 1 | Cfg CA Cpl - Configuration Request received CA Completion | RWS | 0 b |
| 2 | Cfg CTO - Configuration Request Completion Timeout | RWS | 0 b |
| 8 | I/O UR Cpl - I/O Request received UR Completion | RWS | 0 b |
| 9 | I/O CA Cpl - I/O Request received CA Completion | RWS | 0 b |
| 10 | I/O CTO - I/O Request Completion Timeout | RWS | 0 b |
| 16 | Mem UR Cpl - Memory Request received UR Completion | RWS | 0 b |
| 17 | Mem CA Cpl - Memory Request received CA Completion | RWS | 0 b |
| 18 | Mem CTO - Memory Request Completion Timeout | RWS | 0 b |

# 7.9.14.11 RP PIO Header Log Register (Offset 20h) 

This register is implemented only in Root Ports that support RP Extensions for DPC. The RP PIO Header Log Register contains the header from the Request TLP associated with a recorded RP PIO error. Refer to § Section 6.2.11.3 for further details. In Non-Flit Mode, this register is 16 bytes. In Flit Mode, this register is between 52 and 76 bytes and is split into two portions at Offset 20h and Offset 34h. In both Flit Mode and Non-Flit Mode, this register is formatted identically to the Header Log register in AER. See § Section 7.8.4.8 .

![img-300.jpeg](img-300.jpeg)

Figure 7-313 RP PIO Header Log Register

Table 7-277 RP PIO Header Log Register

| Bit Location | Register Description | Attributes | Default |
| :--: | :--: | :--: | :--: |
| 127:0 | TLP Header - of the TLP associated with the error | ROS | 0 |

# 7.9.14.12 RP PIO ImpSpec Log Register (Offset 30h) 

This register is permitted to be implemented only in Root Ports that support RP Extensions for DPC. The RP PIO ImpSpec Log Register, if implemented, contains implementation specific information associated with the recorded error, e.g., indicating the source of the Request TLP. Space is allocated for this register if the value of the RP PIO Log Size field is 5 or greater. If space is allocated for the register, but the register is not implemented, the bits must be hardwired to 0 b.
![img-301.jpeg](img-301.jpeg)

Figure 7-314 RP PIO ImpSpec Log Register

Table 7-278 RP PIO ImpSpec Log Register

| Bit Location | Register Description | Attributes | Default |
| :--: | :--: | :--: | :--: |
| 31:0 | RP PIO ImpSpec Log | ROS | 0 |

### 7.9.14.13 RP PIO TLP Prefix Log Register (Offset 34h)

This register is permitted to be implemented only in Root Ports that support RP Extensions for DPC.
In Non-Flit Mode, the RP PIO TLP Prefix Log Register contains any End-End TLP Prefixes from the TLP corresponding to a recorded RP PIO error. Refer to $\S$ Section 6.2.11.3 for further details.

In Flit Mode, the RP PIO TLP Prefix Log Register does not exist and this configuration space is a continuation of the RP PIO Header Log Register.

If the Root Port supports tracking Non-Posted Requests that contain End-End TLP Prefixes, this register must be implemented, and must be of sufficient size to record the maximum number of End-End TLP Prefixes for any tracked Request. See § Section 2.9.3. The allocated size in DWORDs of the RP PIO TLP Prefix Log Register is the RP PIO Log Size minus 5 if the RP PIO Log Size is 9 or less, or 4 if the RP PIO Log Size is greater than 9. The implemented size of the TLP Prefix Log must be less than or equal to the Root Port's Max End-End TLP Prefixes field value. For the case where the Root Port never transmits Non-Posted Requests containing End-End TLP Prefixes, the allocated and implemented size of the TLP Prefix Log is permitted to be 0 . Any DWORDs allocated but not implemented must be hardwired to zero.

This register is formatted identically to the TLP Prefix Log register in AER, although this register's allocated size is variable, whereas the register in AER is always 4 DWORDs. See § Section 7.8.4.12. The First TLP Prefix Log register contains the first End-End TLP Prefix from the TLP, the Second TLP Prefix Log register contains the second End-End TLP Prefix, and so forth. If the TLP contains fewer TLP Prefixes than this register accommodates, any remaining TLP Prefix Log registers must contain zero.

| 31 |  | 2423 | 1615 |  | 87 |  | 0 |
| :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: |
| Byte 0 |  |  | First PIO TLP Prefix Log Register |  | Byte 3 |  |  |
|  |  |  | Byte 1 | Byte 2 |  |  |  |
|  | Byte 0 |  | Second PIO TLP Prefix Log Register |  |  |  | Byte 3 |
|  |  |  | Byte 1 | Byte 2 |  |  |  |
|  |  |  | Third PIO TLP Prefix Log Register |  |  |  |  |
|  | Byte 0 |  | Byte 1 | Byte 2 |  |  | Byte 3 |
|  |  |  | Fourth PIO TLP Prefix Log Register |  |  |  |  |
|  | Byte 0 |  | Byte 1 | Byte 2 |  |  |  |

Figure 7-315 RP PIO TLP Prefix Log Register

Table 7-279 RP PIO TLP Prefix Log Register

| Bit Location | Register Description | Attributes | Default |
| :--: | :-- | :--: | :--: |
| 127:0 | RP PIO TLP Prefix Log | ROS | 0 |

# 7.9.15 Precision Time Measurement Extended Capability (PTM Extended Capability) $\S$ 

The Precision Time Measurement Extended Capability is an optional Extended Capability for discovering and controlling the distribution of a PTM Hierarchy. For Root Complexes, this Capability is required in any Root Port, RCIEP, or RCRB that supports PTM. For Functions associated with an Upstream Port that support PTM, this Capability is required in exactly one Function of that Upstream Port and that Capability controls the PTM behavior of all PTM capable Functions associated with that Upstream Port. For Switch Downstream Ports, PTM behavior is controlled by the same PTM Capability that controls the associated Switch Upstream Port. The PTM Capability is not permitted in Bridges, Switch Downstream Ports, and Root Complex Event Collectors.

For Switches, a single instance of this Capability controls behavior for the entire Switch. If the Upstream Port of the Switch is associated with an MFD, it is not required that the controlling Function be the Function corresponding to the Switch Upstream Port. For a given Switch, if this Capability is present, all Downstream Ports of the Switch must implement the requirements defined in $\S$ Section 6.21.3.2.

![img-302.jpeg](img-302.jpeg)

Figure 7-316 PTM Extended Capability Structure 5

# 7.9.15.1 PTM Extended Capability Header (Offset 00h) 

![img-303.jpeg](img-303.jpeg)

Figure 7-317 PTM Extended Capability Header 6

Table 7-280 PTM Extended Capability Header 5

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $15: 0$ | PCI Express Extended Capability ID - This field is a PCI-SIG defined ID number that indicates the nature and format of the Extended Capability. <br> PCI Express Extended Capability ID for the Precision Time Measurement Capability is 001Fh. | RO |
| $19: 16$ | Capability Version - This field is a PCI-SIG defined version number that indicates the version of the Capability structure present. <br> Must be 1 h for this version of the specification. | RO |
| $31: 20$ | Next Capability Offset - This field contains the offset to the next PCI Express Extended Capability structure or 000 h if no other items exist in the linked list of Capabilities. | RO |

### 7.9.15.2 PTM Capability Register (Offset 04h) 5

This register describes a Function's support for Precision Time Measurement. Not all fields within this register apply to all Functions capable of implementing PTM.

![img-304.jpeg](img-304.jpeg)

Figure 7-318 PTM Capability Register

Table 7-281 PTM Capability Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 0 | PTM Requester Capable - Indicates the Function implements the PTM Requester role (see § Section 6.21.3.1). <br> Endpoints and RCIEPs are permitted to Set this bit to indicate that they implement the PTM Requester role. <br> Switch Upstream Ports must Set this bit if the Switch contains one or more of the following: <br> - A Downstream Port that implements the PTM Responder role. <br> - An additional Function that implements the PTM Requester role. | HwInit |
| 1 | PTM Responder Capable - Root Ports and RCRBs are permitted to, and Switches supporting PTM must, Set this bit to indicate they implement the PTM Responder role (see § Section 6.21.3.2). If PTM Root Capable is Set, then this bit must be Set. | HwInit |
| 2 | PTM Root Capable - Root Ports, RCRBs, and Switches are permitted to Set this bit if they are capable of being a source of PTM Master Time (see § Section 6.21.1). <br> All other Functions must hardwire this bit to 0b. | HwInit |
| 3 | ePTM Capable - If Set, indicates that this device supports Enhanced Precision Time Measurement (ePTM). This bit MUST@FLIT be Set in all PTM Devices. | HwInit |
| 4 | PTM Propagation Delay Adaptation Capable - When Set, this field indicates the Port supports the PTM Propagation Delay Adaptation Capability, controlled via the PTM Propagation Delay Adaptation Interpretation B bit in the Link Control Register. For a Switch, when Set in the Upstream Port of the Switch, indicates that the Upstream Port and all Downstream Ports of the Switch support the PTM Propagation Delay Adaptation Capability, controlled per Port via the PTM Propagation Delay Adaptation Interpretation B bit in the Link Control Register of each Port. | HwInit |
| 15:8 | Local Clock Granularity - Encodings are: <br> 0000 0000b <br> Time Source does not implement a local clock. It simply propagates timing information obtained from further Upstream in the PTM Hierarchy when responding to PTM Request messages. <br> 0000 0001b to 1111 1110b <br> 1111 1111b <br> Indicates the period of this Time Source's local clock in ns. <br> 1111 1111b Indicates the period of this Time Source's local clock is greater than 254 ns. | HwInit/RsvdP |

| Bit Location | Register Description | Attributes |
| :-- | :-- | :-- |
|  | If the PTM Root Select bit is Set, this local clock is used to provide PTM Master Time. Otherwise, the <br> Time Source uses this local clock to locally track PTM Master Time received from further Upstream <br> within a PTM Hierarchy. <br> This field is RsvdP if the PTM Root Capable bit is Ob. |  |

# 7.9.15.3 PTM Control Register (Offset 08h) 

This register controls a Function's participation in the Precision Time Measurement mechanism. Not all fields within this register apply to all Functions capable of implementing PTM.
![img-305.jpeg](img-305.jpeg)

Figure 7-319 PTM Control Register

Table 7-282 PTM Control Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 0 | PTM Enable - When Set, this Function is permitted to participate in the PTM mechanism according to its selected role(s) (see § Section 6.21.2). <br> Default value is Ob. | RW |
| 1 | Root Select - When Set, if the PTM Enable bit is also Set, this Time Source is the PTM Root. <br> Within each PTM Hierarchy, it is recommended that system software select only the furthest Upstream Time Source to be the PTM Root. <br> Default value is Ob. If the value of the PTM Root Capable bit is Ob, this bit is permitted to be hardwired to Ob. | RW/RO |
| $15: 8$ | Effective Granularity - For Functions implementing the PTM Requester Role, this field provides information relating to the expected accuracy of the PTM clock, but does not otherwise affect the PTM mechanism. <br> For Endpoints, system software must program this field to the value representing the maximum Local Clock Granularity reported by the PTM Root and all intervening PTM Time Sources. <br> For RCIEPs, system software must set this field to the value reported in the Local Clock Granularity field by the associated PTM Time Source. <br> Permitted values: <br> 0000 0000b <br> Unknown PTM granularity - one or more Switches between this Function and the PTM Root reported a Local Clock Granularity value of 0000 0000b. <br> 0000 0001b to 1111 1110b Indicates the effective PTM granularity in ns. | RW/RO |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | 1111 1111b <br> Default value is 0000 0000b. If PTM Requester Capable is Clear, this field is permitted to be hardwired to 0000 0000b. |  |

# 7.9.16 Readiness Time Reporting Extended Capability $\S$ 

The Readiness Time Reporting Extended Capability provides an optional mechanism for describing the time required for a Device or Function to become Configuration-Ready. In the indicated situations, software is permitted to issue Requests to the Device or Function after waiting for the time advertised in this capability and need not wait for the (longer) times required elsewhere.

Software is permitted to issue requests upon the earliest of:

- Receiving a Readiness Notifications message (see § Section 6.22 ).
- Waiting the appropriate time as specified in this document or in applicable specifications including the [PCI] and the $[P C I-P M]$.
- Waiting the time indicated in the associated field of this capability.
- Waiting the time defined by system software or firmware ${ }^{194}$.

Software is permitted to cache values from this capability and to use those cached values as long as the same device operating in the same manner has not changed.

This capability is permitted to be implemented in all Functions.
The capability is optional for PFs and VFs. However, if a VF associated with a given PF contains the capability, all VFs associated with that PF must contain the capability and report the same time values.

For VFs, see § Section 5.10.1). Other Functions must be Configuration-Ready if:

- The Immediate Readiness bit is Clear and at least Reset Time has elapsed after the completion of Conventional Reset
- If the Immediate Readiness bit is Set, Reset Time does not apply, and is Reserved
- The Function is associated with an Upstream Port and at least DL_Up Time has elapsed after the Downstream Port above that Function reported Data Link Layer Link Active (see § Section 7.5.3.8).
- The Function supports Function Level Reset and at least FLR Time has elapsed after that Function was issued a Function Level Reset.
- Immediate_Readiness_on_Return_to_D0 is Clear and at least $\mathrm{D3}_{\text {Hot }}$ to DO Time has elapsed after that Function was directed to the DO state from $\mathrm{D3}_{\text {Hot }}$.
- If the Immediate_Readiness_on_Return_to_D0 bit is Set, $\mathrm{D3}_{\text {Hot }}$ to DO Time does not apply, and is Reserved

When Immediate_Readiness_on_Return_to_D0 is Clear, a Function must be Configuration-Ready when at least $\mathrm{D}_{3}{ }_{\text {Hot }}$ to DO Time has elapsed after the Function was directed to the DO state from $\mathrm{D}_{3}{ }_{\text {Hot }}$. In addition, the Function must be in either the DO uninitialized or DO active state, depending on the value of the No_Soft_Reset bit.

If the above conditions do not apply, Function behavior is not determined by the Readiness Time Reporting Extended Capability, and the Function must respond as defined elsewhere (including, for example, no response or a response with Configuration Retry Status).

The time values reported are determined by implementation specific mechanisms. A valid bit is defined in this capability to permit a device to defer reporting time values, for example to allow hardware initialization through driver-based mechanisms. If the valid bit remains Clear and 1 minute has elapsed after device driver(s) have started, software is permitted to assume that no values will be reported.

Registers and fields in the Readiness Time Reporting Extended Capability are shown in § Figure 7-320. Time values are encoded in floating point as shown in § Figure 7-321. The actual time value is Value $\times$ Multiplier[Scale]. For example, the value A1Eh represents about 1 second (actually 1.006 sec ) and the value 80Ah represents about 10 ms (actually 10.240 ms ).
![img-306.jpeg](img-306.jpeg)

Figure 7-320 Readiness Time Reporting Extended Capability

| Scale | Multiplier |
| :--: | :--: |
| 0 | 1 ns |
| 1 | 32 ns |
| 2 | $1,024 \mathrm{~ns}$ |
| 3 | $32,768 \mathrm{~ns}$ |
| 4 | $1,048,576 \mathrm{~ns}$ |
| 5 | $33,554,432 \mathrm{~ns}$ |
| 6 | Reserved |
| 7 | Reserved |
| Multiplier $=32^{\text {Scale }}$ |  |

![img-307.jpeg](img-307.jpeg)

Figure 7-321 Readiness Time Encoding

# 7.9.16.1 Readiness Time Reporting Extended Capability Header (Offset 00h) 

§ Figure 7-322 and § Table 7-284 detail allocation of fields in the Extended Capability header.

![img-308.jpeg](img-308.jpeg)

Figure 7-322 Readiness Time Reporting Extended Capability Header

Table 7-284 Readiness Time Reporting Extended Capability Header

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 15:0 | PCI Express Extended Capability ID - This field is a PCI-SIG defined ID number that indicates the nature and format of the Extended Capability. <br> Extended Capability ID for the Readiness Time Reporting Extended Capability is 0022h. | RO |
| 19:16 | Capability Version - This field is a PCI-SIG defined version number that indicates the version of the Capability structure present. <br> Must be 1 h for this version of the specification. | RO |
| $31: 20$ | Next Capability Offset - This field contains the offset to the next PCI Express Capability structure or 000h if no other items exist in the linked list of Capabilities. <br> For Extended Capabilities implemented in Configuration Space, this offset is relative to the beginning of PCI-compatible Configuration Space and thus must always be either 000 h (for terminating list of Capabilities) or greater than 0FFh. | RO |

# 7.9.16.2 Readiness Time Reporting 1 Register (Offset 04h) 

\$ Figure 7-323 and $\S$ Table 7-285 detail allocation of fields in the Readiness Time Reporting 1 Register.
![img-309.jpeg](img-309.jpeg)

Figure 7-323 Readiness Time Reporting 1 Register

Table 7-285 Readiness Time Reporting 1 Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $11: 0$ | Reset Time - is the time a non-VF Function requires to become Configuration-Ready after the completion of Conventional Reset. For VF semantics, see $\S$ Section 9.3.3.3.1. <br> This field is RsvdP if the Immediate Readiness bit is Set. <br> This field is undefined when the Valid bit is Clear. <br> This field must be less than or equal to the encoded value A1Eh. | HwInit/RsvdP |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 23:12 | DL_Up Time - is the time the Function requires to become Configuration-Ready after the Downstream Port above the Function reports Data Link Layer Link Active. <br> This field is RsvdP in Functions that are not associated with an Upstream Port. <br> For VFs, this field is not applicable and is RsvdP. <br> This field is undefined when the valid bit is Clear. <br> This field must be less than or equal to the encoded value A1Eh. | HwInit/RsvdP <br> VF RsvdP |
| 31 | Valid - If Set, indicates that all time values in this capability are valid. If Clear, indicates that the time values in this capability are not yet available. <br> Time values may depend on device configuration. Device specific mechanisms, possibly involving the device driver(s), could be involved in determining time values. <br> If this bit remains Clear and 1 minute has elapsed after all associated device driver(s) have started, software is permitted to assume that this bit will never be set. | HwInit |

# 7.9.16.3 Readiness Time Reporting 2 Register (Offset 08h) 

$\S$ Figure 7-324 and $\S$ Table 7-286 detail allocation of fields in the Readiness Time Reporting 2 Register.
![img-310.jpeg](img-310.jpeg)

Figure 7-324 Readiness Time Reporting 2 Register

Table 7-286 Readiness Time Reporting 2 Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $11: 0$ | FLR Time - is the time that the Function requires to become Configuration-Ready after it was issued an FLR. <br> This field is RsvdP when the Function Level Reset Capability bit is Clear (see § Section 7.5.3.3). <br> This field is undefined when the valid bit is Clear. <br> This field must be less than or equal to the encoded value A1Eh. | HwInit/RsvdP |
| 23:12 | D3 $3_{\text {Hot }}$ to D0 Time - If Immediate_Readiness_on_Return_to_D0 is Clear, D3 ${ }_{\text {Hot }}$ to D0 Time is the time that a non-VF Function requires after it is directed from $\mathrm{D3}_{\text {Hot }}$ to D0 before it is Configuration-Ready and has returned to either $\mathrm{DO}_{\text {uninitialized }}$ or $\mathrm{DO}_{\text {active }}$ state. For VF semantics, see $\S$ Section 5.10.1. <br> This field is RsvdP if the Immediate_Readiness_on_Return_to_D0 bit is Set. <br> For a VF that does not implement the PCI Power Management Capability, this field is undefined. <br> This field is undefined when the valid bit is Clear. <br> This field must be less than or equal to the encoded value 80Ah. | HwInit/RsvdP |

# 7.9.17 Hierarchy ID Extended Capability 

The Hierarchy ID Extended Capability provides an optional mechanism for passing a unique identifier to Functions within a Hierarchy. At most one instance of this capability is permitted in a Function. This capability is not applicable to Bridges, Root Complex Event Collectors, and RCRBs.

This capability takes three forms:
In Upstream Ports:

- This capability is permitted any Function associated with an Upstream Port.
- This capability is optional in Switch Upstream Ports. Support in Switch Upstream and Downstream Ports is independently optional.
- This capability is mandatory in Functions that use the Hierarchy ID Message. This includes use by the Function's driver.
- Functions, other than VFs, that have Hierarchy ID Writeable Clear, must report the Message Requester ID, Hierarchy ID, System GUID Authority ID, and System GUID fields from the most recently received Hierarchy ID Message.
- All VFs that have Hierarchy ID Writeable Clear, must report the same Hierarchy ID Valid, Message Requester ID, Hierarchy ID, System GUID Authority ID, and System GUID values as their associated PF.
- PFs must implement this capability if any of their VFs implement this capability.
- Functions that have Hierarchy ID Writeable Set must report the Hierarchy ID Valid, Message Requester ID, Hierarchy ID, System GUID Authority ID, and System GUID values programmed by software.

In Downstream Ports:

- This capability is permitted in any Downstream Port. It is recommended that it be implemented in Root Ports.
- When present in a Switch Downstream Port, this capability must be implemented in all Downstream Ports of the Switch. Support in Switch Upstream and Downstream Ports is independently optional.
- In Downstream Ports, the Hierarchy ID, System GUID Authority ID, and System GUID fields are Read / Write and contain the values to send in the Hierarchy ID Message.
- A Hierarchy ID capability is not affected by Hierarchy ID Messages forwarded through the associated Downstream Port.


## In RCIEPs:

- VFs that have Hierarchy ID Writeable Clear must report the same Message Requester ID, Hierarchy ID, System GUID Authority ID, and System GUID values as their associated PF.
- PFs must implement this capability if any of their VFs implement this capability.
- Functions, other than VFs, that have Hierarchy ID Writeable Clear, must report the same Hierarchy ID Valid, Message Requester ID, Hierarchy ID, System GUID Authority ID, and System GUID values. The source of this information is outside the scope of this specification.
- Functions that have Hierarchy ID Writeable Set must report the Hierarchy ID Valid, Message Requester ID, Hierarchy ID, System GUID Authority ID, and System GUID values programmed by software.
§ Figure 7-325 details the layout of the Hierarchy ID Extended Capability.

![img-311.jpeg](img-311.jpeg)

Figure 7-325 Hierarchy ID Extended Capability

# 7.9.17.1 Hierarchy ID Extended Capability Header (Offset 00h) 

\$ Figure 7-326 and $\S$ Table 7-287 detail allocation of fields in the Hierarchy ID Extended Capability Header.
![img-312.jpeg](img-312.jpeg)

Figure 7-326 Hierarchy ID Extended Capability Header

Table 7-287 Hierarchy ID Extended Capability Header

| Bit Location | Description | Attributes |
| :--: | :--: | :--: |
| 15:0 | Extended Capability ID - This field is a PCI-SIG defined ID number that indicates the nature and format of the Extended Capability. <br> PCI Express Extended Capability ID for the Hierarchy ID Extended Capability is 0028h. | RO |
| 19:16 | Capability Version - This field is a PCI-SIG defined version number that indicates the version of the Capability structure present. <br> Must be 1 h for this version of the specification. | RO |
| 31:20 | Next Capability Offset - This field contains the offset to the next PCI Express Extended Capability structure or 000 h if no other items exist in the linked list of Capabilities. For Extended Capabilities in configuration space, this offset is relative to the beginning of PCI-compatible Configuration Space and thus must always be either 000 h (for terminating the list of Capabilities) or greater than 0FFh. | RO |

# 7.9.17.2 Hierarchy ID Status Register (Offset 04h) 

\$ Figure 7-327 and \$ Table 7-288 detail allocation of fields in the Hierarchy ID Status Register.
![img-313.jpeg](img-313.jpeg)

Figure 7-327 Hierarchy ID Status Register

Table 7-288 Hierarchy ID Status Register

| Bit Location | Description | Attributes |
| :--: | :--: | :--: |
| 15:0 | Message Requester ID - In an Upstream Port, this field contains the Requester ID from the most recently received Hierarchy ID Message. This field is meaningful only if Hierarchy ID Valid is 1b. This value identifies the Downstream Port (within this Hierarchy) that sent the Hierarchy ID Message. This information is not considered part of the Hierarchy ID as it can vary within the Hierarchy (e.g., different Root Ports of one Root Complex), but helps in debug situations to identify the provenance of the Hierarchy ID information. <br> In a Downstream Port, this field is RsvdZ. <br> For RCIEPs, this field is RsvdZ. <br> This field defaults to 0000h. | RO/RsvdZ |
| 28 | Hierarchy ID Writeable - This bit is Set to indicate that the Hierarchy ID Data and GUID registers are read/ write. This bit is Clear to indicate that the Hierarchy ID and GUID registers are read only. <br> In Downstream Ports this bit is hardwired to 1b. <br> In Upstream Ports, Functions that are not VFs must hardwire this bit to 0b. <br> RCIEPs that are not VFs, must hardwire this bit to either 0b or 1b. <br> VFs in an Upstream Port and Root Complex Integrated VFs are permitted to either: <br> - hardwire this bit to 0b or <br> - implement this bit as read / write with a default value of 0 b . | RW/RO |
| 29 | Hierarchy ID VF Configurable - This bit indicates that Hierarchy ID Writeable can be configured. <br> If Hierarchy ID Writeable is implemented as read / write, this bit is 1b. Otherwise this bit is 0b. | RO |
| 30 | Hierarchy ID Pending - In Downstream Ports this requests the transmittion of a Hierarchy ID Message. Setting it requests transmission of a message based on the Hierarchy Data and GUID registers in this capability. This bit is cleared when either the transmit request is satisfied or the Link enters DL_Down. Behavior is undefined if the Hierarchy Data or GUID registers in this capability are written while this bit is Set. <br> In Downstream Ports, this bit is Read / Write defaulting to 0b. <br> In all other Functions, this bit is RsvdZ. | RW/RsvdZ |

| Bit Location | Description | Attributes |
| :--: | :--: | :--: |
| 31 | Hierarchy ID Valid - This bit indicates that the remaining fields in this capability are meaningful. <br> In Downstream Ports, this bit is hardwired to 1b. <br> In all other Functions, the following rules apply: <br> - If Hierarchy ID Writeable is Set, this bit is read/write, default 0b. <br> - If Hierarchy ID Writeable is Clear, this bit is read only, default 0b. <br> - In VFs, this bit contains the same value as the associated PF. <br> - In Functions other than VFs that are associated with an Upstream Port, this bit is Set when a Hierarchy ID Message is received, and Cleared when the Link is DL_Down. <br> - In RCIEPs other than VFs, this bit contains a system provided value. The mechanism for determining this value is outside the scope of this specification. | RW/RO |

# 7.9.17.3 Hierarchy ID Data Register (Offset 08h) $\S$ 

§ Figure 7-328 and § Table 7-289 detail allocation of fields in the Hierarchy ID Data Register.
![img-314.jpeg](img-314.jpeg)

Figure 7-328 Hierarchy ID Data Register

Table 7-289 Hierarchy ID Data Register

| Bit Location | Description | Attributes |
| :--: | :--: | :--: |
| $7: 0$ | System GUID Authority ID - This field corresponds to the System GUID Authority ID field in the Hierarchy ID Message. See § Section 6.25 for details. <br> This field is meaningful only if Hierarchy ID Valid is 1b. <br> If Hierarchy ID Writeable is Set, this field is read-write and contains the value programmed by software. <br> If Hierarchy ID Writeable is Clear, this field is read only. The value is determined using the rules defined in § Section 7.9.17. <br> This field defaults to 00h. | RO/RW |
| $31: 16$ | Hierarchy ID - This field corresponds to the Hierarchy ID field in the Hierarchy ID Message. See § Section 6.25 for details. <br> This field is meaningful only if Hierarchy ID Valid is 1b. <br> If Hierarchy ID Writeable is Set, this field is read-write and contains the value programmed by software. <br> If Hierarchy ID Writeable is Clear, this field is read only. The value is determined using the rules defined in § Section 7.9.17. <br> This field defaults to 0000h. | RO/RW |

# 7.9.17.4 Hierarchy ID GUID 1 Register (Offset 0Ch) 

\$ Figure 7-329 and $\S$ Table 7-290 detail allocation of fields in the Hierarchy ID GUID 1 Register.
![img-315.jpeg](img-315.jpeg)

Figure 7-329 Hierarchy ID GUID 1 Register

Table 7-290 Hierarchy ID GUID 1 Register

| Bit Location | Description | Attributes |
| :--: | :--: | :--: |
| 15:0 | System GUID 1 - This field corresponds to bits [143:128] of the System GUID in the Hierarchy ID Message. See $\S$ Section 6.25 for details. <br> This field is meaningful only if Hierarchy ID Valid is 1b. <br> If Hierarchy ID Writeable is Set, this field is read-write and contains the value programmed by software. <br> If Hierarchy ID Writeable is Clear, this field is read only. The value is determined using the rules defined in $\S$ Section 7.9.17. <br> This field defaults to 0000h. | RO/RW |

### 7.9.17.5 Hierarchy ID GUID 2 Register (Offset 10h) $\$$

$\S$ Figure 7-330 and $\S$ Table 7-291 detail allocation of fields in the Hierarchy ID GUID 2 Register.
![img-316.jpeg](img-316.jpeg)

Figure 7-330 Hierarchy ID GUID 2 Register

Table 7-291 Hierarchy ID GUID 2 Register

| Bit Location | Description | Attributes |
| :--: | :--: | :--: |
| 31:0 | System GUID 2 - This field corresponds to bits [127:96] of the System GUID field in the Hierarchy ID Message. See $\S$ Section 6.25 for details. <br> This field is meaningful only if Hierarchy ID Valid is 1b. <br> If Hierarchy ID Writeable is Set, this field is read-write and contains the value programmed by software. <br> If Hierarchy ID Writeable is Clear, this field is read only. The value is determined using the rules defined in $\S$ Section 7.9.17. <br> This field defaults to 00000000 h . | RO/RW |

# 7.9.17.6 Hierarchy ID GUID 3 Register (Offset 14h) 

\$ Figure 7-331 and $\S$ Table 7-292 detail allocation of fields in the Hierarchy ID GUID 3 Register.
![img-317.jpeg](img-317.jpeg)

Figure 7-331 Hierarchy ID GUID 3 Register

Table 7-292 Hierarchy ID GUID 3 Register

| Bit Location | Description | Attributes |
| :--: | :--: | :--: |
| 31:0 | System GUID 3 - This field corresponds to bits [95:64] of the System GUID field in the Hierarchy ID Message. See $\S$ Section 6.25 for details. <br> This field is meaningful only if Hierarchy ID Valid is 1b. <br> If Hierarchy ID Writeable is Set, this field is read-write and contains the value programmed by software. <br> If Hierarchy ID Writeable is Clear, this field is read only. The value is determined using the rules defined in $\S$ Section 7.9.17. <br> This field defaults to 00000000 h. | RO/RW |

### 7.9.17.7 Hierarchy ID GUID 4 Register (Offset 18h) $\S$

§ Figure 7-332 and § Table 7-293 detail allocation of fields in the Hierarchy ID GUID 4 Register.
![img-318.jpeg](img-318.jpeg)

Figure 7-332 Hierarchy ID GUID 4 Register

Table 7-293 Hierarchy ID GUID 4 Register

| Bit Location | Description | Attributes |
| :--: | :--: | :--: |
| 31:0 | System GUID 4 - This field corresponds to bits [63:32] of the System GUID field in the Hierarchy ID Message. See $\S$ Section 6.25 for details. <br> This field is meaningful only if Hierarchy ID Valid is 1b. <br> If Hierarchy ID Writeable is Set, this field is read-write and contains the value programmed by software. <br> If Hierarchy ID Writeable is Clear, this field is read only. The value is determined using the rules defined in $\S$ Section 7.9.17. <br> This field defaults to 00000000 h . | RO/RW |

# 7.9.17.8 Hierarchy ID GUID 5 Register (Offset 1Ch) 

\$ Figure 7-333 and $\S$ Table 7-294 detail allocation of fields in the Hierarchy ID GUID 5 Register.
![img-319.jpeg](img-319.jpeg)

Figure 7-333 Hierarchy ID GUID 5 Register

Table 7-294 Hierarchy ID GUID 5 Register

| Bit Location | Description | Attributes |
| :--: | :--: | :--: |
| 31:0 | System GUID 5 - This field corresponds to bits [31:0] of the System GUID field in the Hierarchy ID Message. See § Section 6.25 for details. <br> This field is meaningful only if Hierarchy ID Valid is 1b. <br> If Hierarchy ID Writeable is Set, this field is read-write and contains the value programmed by software. <br> If Hierarchy ID Writeable is Clear, this field is read only. The value is determined using the rules defined in § Section 7.9.17. <br> This field defaults to 00000000 h. | RO/RW |

### 7.9.18 Vital Product Data Capability (VPD Capability)

Support of VPD is optional. All Functions are permitted to contain the capability. This includes all Functions of a Multi-Function Device associated with an Upstream Port as well as RCIEPs. This also includes PFs and VFs.

Vital Product Data (VPD) is information that uniquely identifies hardware and, potentially, software elements of a system. The VPD can provide the system with information on various Field Replaceable Units such as part number, serial number, and other detailed information. The objective from a system point of view is to make this information available to the system owner and service personnel. VPD typically resides in a storage device (for example, a serial EEPROM) associated with the Function.

VFs and PFs that implement the VPD Capability must ensure that there can be no "data leakage" between VFs and/or PFs via the VPD Capability.

Details of the VPD Data is defined in § Section 6.27 .
Access to the VPD is provided using the Capabilities List in Configuration Space. The VPD Capability structure is shown in § Figure 7-334.

![img-320.jpeg](img-320.jpeg)

Figure 7-334 VPD Capability Structure 6

The following protocols are used transfer data between the VPD Data field and the VPD storage component.

- To read VPD information:

1. Issue single write to the VPD Address Register writing the flag bit (F) to Ob and VPD Address with the address to read.
2. The hardware device will set $F$ to 1 b when 4 bytes of data from the storage component have been transferred to VPD Data.
3. Software can monitor F and, after it becomes 1 b , read the VPD information from VPD Data.

Behavior is undefined if either the VPD Address or VPD Data is written, prior to the flag bit becoming 1b.

- To write VPD information to the read/write portion of the VPD space:

1. Write the data to VPD Data
2. Then issue a single write to the VPD Address Register with F set to 1 b and VPD Address set to the address where the VPD Data is to be stored.
3. The software then monitors F and when it is set to 0 b (by device hardware), the VPD Data (all 4 bytes) has been transferred from VPD Data to the storage component.

If either the VPD Address or VPD Data is written, prior to F being becoming Ob , the results of the write operation to the storage component are unpredictable.

Behavior is undefined if a read or write of the storage component is requested and VPD Address is outside the range of the storage component.

The VPD (both the read only items and the read/write fields) is stored information and will have no direct control of any device operations.

# 7.9.18.1 VPD Address Register 

The VPD Address Register is used to request a read or write of the VPD storage component.

| $15 \mid 14$ |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: |
| F | VPD Address |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |  |

Figure 7-335 VPD Address Register

Table 7-295 VPD Address Register

| Bit Location | Description | Attributes |
| :--: | :--: | :--: |
| $14: 0$ | VPD Address - DWORD-aligned byte address of the VPD to be accessed. Behavior is undefined if the lowest 2 bits of this field are non-zero. The lowest two bits of the field must be either RW, or RO with a value of 00 b . The remaining bits of the field must be RW. <br> Default is implementation specific. | RW/RO <br> (see <br> description) |
| 15 | F - The F bit is always written along with VPD Address. The value of F indicates the direction of transfer being requested ( $0 \mathrm{~b}=$ read, $1 \mathrm{~b}=$ write). When the transfer is complete, the F bit value changes to indicate completion ( $1 \mathrm{~b}=$ read complete, $0 \mathrm{~b}=$ write complete). <br> Default is implementation specific. | RW |

# 7.9.18.2 VPD Data Register 

![img-321.jpeg](img-321.jpeg)

Figure 7-336 VPD Data Register

Table 7-296 VPD Data Register

| Bit Location | Description | Attributes |
| :--: | :--: | :--: |
| $31: 0$ | VPD Data - VPD Data can be read through this register. The least significant byte of this register (at offset 04 h in this capability structure) corresponds to the byte of VPD at the address specified by VPD Address. Behavior is undefined for any read or write of this register with Byte Enables other than 1111b. Default is implementation specific. | RW |

### 7.9.19 Native PCIe Enclosure Management Extended Capability (NPEM Extended Capability)

The Native PCIe Enclosure Management Extended (NPEM) Capability is an optional extended capability that is permitted to be implemented by Root Ports, Switch Downstream Ports, and Endpoints.

![img-322.jpeg](img-322.jpeg)

Figure 7-337 NPEM Extended Capability

# 7.9.19.1 NPEM Extended Capability Header (Offset 00h) 

![img-323.jpeg](img-323.jpeg)

Figure 7-338 NPEM Extended Capability Header

Table 7-297 NPEM Extended Capability Header

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $15: 0$ | PCI Express Extended Capability ID - This field is a PCI-SIG defined ID number that indicates the nature and format of the extended capability. <br> PCI Express Extended Capability ID for the NPEM Extended Capability is 0029h. | RO |
| $19: 16$ | Capability Version - This field is a PCI-SIG defined version number that indicates the version of the capability structure present. <br> Must be 1 h for this version of the specification. | RO |
| $31: 20$ | Next Capability Offset - This field contains the offset to the next PCI Express Extended Capability structure or 000 h if no other items exist in the linked list of capabilities. | RO |

### 7.9.19.2 NPEM Capability Register (Offset 04h)

The NPEM Capability Register contains an overall NPEM Capable bit and a bit map of states supported in the implementation. Implementations are required to support OK, Locate, Fail, and Rebuild states if NPEM Capable bit is Set. All other states are optional.

![img-324.jpeg](img-324.jpeg)

Figure 7-339 NPEM Capability Register

Table 7-298 NPEM Capability Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 0 | NPEM Capable - When Set, this bit indicates that the enclosure has NPEM functionality. | HwInit |
| 1 | NPEM Reset Capable - A value of 1 b indicates support for the optional NPEM Reset mechanism described in $\S$ Section 6.28. This capability is independently optional. | HwInit |
| 2 | NPEM OK Capable - When Set, this bit indicates that enclosure has the ability to indicate the NPEM OK state. This bit must be Set if NPEM Capable is also Set. | HwInit |
| 3 | NPEM Locate Capable - When Set, this bit indicates that enclosure has the ability to indicate the NPEM Locate state. This bit must be Set if NPEM Capable is also Set. | HwInit |
| 4 | NPEM Fail Capable - When Set, this bit indicates that enclosure has the ability to indicate the NPEM Fail state. This bit must be Set if NPEM Capable is also Set. | HwInit |
| 5 | NPEM Rebuild Capable - When Set, this bit indicates that enclosure has the ability to indicate the NPEM Rebuild state. This bit must be Set if NPEM Capable is also Set. | HwInit |
| 6 | NPEM PFA Capable - When Set, this bit indicates that enclosure has the ability to indicate the NPEM PFA state. This capability is independently optional. | HwInit |
| 7 | NPEM Hot Spare Capable - When Set, this bit indicates that enclosure has the ability to indicate the NPEM Hot Spare state. This capability is independently optional. | HwInit |
| 8 | NPEM In A Critical Array Capable - When Set, this bit indicates that enclosure has the ability to indicate the NPEM In A Critical Array state. This capability is independently optional. | HwInit |
| 9 | NPEM In A Failed Array Capable - When Set, this bit indicates that enclosure has the ability to indicate the NPEM In A Failed Array state. This capability is independently optional. | HwInit |
| 10 | NPEM Invalid Device Type Capable - When Set, this bit indicates that enclosure has the ability to indicate the NPEM_Invalid_ Device_Type state. This capability is independently optional. | HwInit |

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 11 | NPEM Disabled Capable - When Set, this bit indicates that enclosure has the ability to indicate the <br> NPEM_Disabled state. This capability is independently optional. | HwInit |
| $31: 24$ | Enclosure-specific Capabilities - The definition of enclosure-specific bits is outside the scope of this <br> specification. | HwInit |

# 7.9.19.3 NPEM Control Register (Offset 08h) 

The NPEM Control Register contains an overall NPEM Enable bit and a bit map of states that software controls.
Use of Enclosure-specific bits is outside the scope of this specification.
All writes to this register, including writes that do not change the register value, are NPEM commands and should eventually result in a command completion indication in the NPEM Status Register.
![img-325.jpeg](img-325.jpeg)

Figure 7-340 NPEM Control Register

Table 7-299 NPEM Control Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 0 | NPEM Enable - When Set, this bit enables the NPEM capability. When Clear, this bit disables the NPEM <br> capability. <br> Default value of this bit is Ob. <br> When enabled, this capability operates as defined in this specification. When disabled, the other bits in <br> this capability have no effect and any associated indications are outside the scope of this specification. | RW |
| 1 | NPEM Initiate Reset - If NPEM Reset Capable bit is 1b, then a write of 1b to this bit initiates NPEM Reset. If <br> NPEM Reset Capable bit is Ob, then this bit is permitted to be read-only with a value of Ob. <br> The value read by software from this bit must always be Ob. | RW/RO |
| 2 | NPEM OK Control - When Set, this bit specifies that the NPEM OK indication be turned ON. When Clear, <br> this bit specifies that the NPEM OK indication be turned OFF. | RW/RO |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 3 | If NPEM OK Capable bit in NPEM Capability Register is 0b, this bit is permitted to be read-only with a value of 0 b. Default value of this bit is 0 b |  |
|  | NPEM Locate Control - When Set, this bit specifies that the NPEM Locate indication be turned ON. When Clear, this bit specifies that the NPEM Locate indication be turned OFF. <br> If NPEM Locate Capable bit in the NPEM Capability Register is 0b, this bit is permitted to be read-only with a value of 0 b. <br> Default value of this bit is 0 b | RW/RO |
| 4 | NPEM Fail Control - When Set, this bit specifies that the NPEM Fail indication be turned ON. When Clear, this bit specifies that the NPEM Fail indication be turned OFF. <br> If NPEM Fail Capable bit in the NPEM Capability Register is 0b, this bit is permitted to be read-only with a value of 0 b. <br> Default value of this bit is 0 b | RW/RO |
| 6 | NPEM PFA Control - When Set, this bit specifies that the NPEM PFA indication be turned ON. When Clear, this bit specifies that the NPEM PFA indication be turned OFF. <br> If NPEM PFA Capable bit in NPEM Capability Register is 0b, this bit is permitted to be read-only with a value of 0 b. <br> Default value of this bit is 0 b | RW/RO |
| 7 | NPEM Not Spare Control - When Set, this bit specifies that the NPEM Hot Spare indication be turned ON. When Clear, this bit specifies that the NPEM Hot Spare indication be turned OFF. <br> If NPEM Hot Spare Capable bit in NPEM Capability Register is 0b, this bit is permitted to be read-only with a value of 0 b. <br> Default value of this bit is 0 b | RW/RO |
| 8 | NPEM In A Critical Array Control - When Set, this bit specifies that the NPEM In A Critical Array indication be turned ON. When Clear, this bit specifies that the NPEM In A Critical Array indication be turned OFF. <br> If NPEM In A Critical Array Capable bit in NPEM Capability Register is 0b, this bit is permitted to be read-only with a value of 0 b. <br> Default value of this bit is 0 b | RW/RO |
| 9 | NPEM In A Failed Array Control - When Set, this bit specifies that the NPEM In A Failed Array indication be turned ON. When Clear, this bit specifies that the NPEM In A Failed Array indication be turned OFF. <br> If NPEM In A Failed Array Capable bit in NPEM Capability Register is 0b, this bit is permitted to be read-only with a value of 0 b. <br> Default value of this bit is 0 b | RW/RO |
| 10 | NPEM Invalid Device Type Control - When Set, this bit specifies that the NPEM Invalid Device Type indication be turned ON. When Clear, this bit specifies that the NPEM Invalid Device Type indication be turned OFF. | RW/RO |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 11 | If NPEM Invalid Device Type Capable bit in NPEM Capability Register is 0b, this bit is permitted to be read-only with a value of 0 b. Default value of this bit is 0 b |  |
|  | NPEM Disabled Control - When Set, this bit specifies that the NPEM Disabled indication be turned ON. When Clear, this bit specifies that the NPEM Disabled indication be turned OFF. <br> If NPEM Disabled Capable bit in NPEM Capability Register is 0b, this bit is permitted to be read-only with a value of 0 b. <br> Default value of this bit is 0 b | RW/RO |
| 31:24 | Enclosure-specific Controls - The definition of enclosure-specific bits is outside the scope of this specification. Enclosure-specific software is permitted to change the value of this field. Other software must preserve the existing value when writing this register. <br> Default value of this field is 00 h | RW/RO |

# 7.9.19.4 NPEM Status Register (Offset 0Ch) 

![img-326.jpeg](img-326.jpeg)

Figure 7-341 NPEM Status Register

Table 7-300 NPEM Status Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 0 | NPEM Command Completed - This bit is Set when an NPEM command has completed, and the NPEM controller is ready to accept a subsequent command. <br> This bit is permitted to be hardwired to 1 b if the enclosure is able to accept writes that update any portion of the NPEM Control register without any delay between successive writes. <br> Default value of this bit is 0 b . <br> Software must wait for an NPEM command to complete before issuing the next NPEM command. However, if this bit is not set within 1 second limit on command execution, software is permitted to repeat the NPEM command or issue the next NPEM command. If software issues a write before the Port has completed processing of the previous command and before the 1 second time limit has expired, the Port is permitted to either accept or discard the write. Such a write is considered a programming error, and could result in a discrepancy between the NPEM Control Register and the enclosure element state. To recover from such a programming error and return the enclosure to a consistent state, software must issue a write to the NPEM Control Register which conforms to the NPEM command completion rules. | RW1C / RO |
| 31:24 | Enclosure-specific Status - The definition of enclosure specific bits is outside the scope of this specification. Enclosure specific software is permitted to write non-zero values to this field. Other software must write 00 h to this field. | RsvdZ/RO/RW1C |

| Bit Location | Register Description | Attributes |
| :-- | :-- | :-- |
|  | The default value of this field is enclosure-specific. <br> This field is permitted to be hardwired to 00h. |  |

# 7.9.20 Alternate Protocol Extended Capability $\S$ 

The Alternate Protocol Extended Capability structure is optional in components that implement Alternate Protocol Negotiation. It is only permitted in:

- A Function associated with a Downstream Port.
- Function 0 (and only Function 0) of a Device associated with an Upstream Port.
§ Figure 7-342 details allocation of register fields in the Alternate Protocol Extended Capability structure.
![img-327.jpeg](img-327.jpeg)

Figure 7-342 Alternate Protocol Extended Capability $\S$

### 7.9.20.1 Alternate Protocol Extended Capability Header (Offset 00h) $\S$

![img-328.jpeg](img-328.jpeg)

Figure 7-343 Alternate Protocol Extended Capability Header $\S$

Table 7-301 Alternate Protocol Extended Capability Header $\S$

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 15:0 | PCI Express Extended Capability ID - This field is a PCI-SIG defined ID number that indicates the nature and format of the Extended Capability. | RO |

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
|  | The Extended Capability ID for the Alternate Protocol Capability is 002Bh. |  |
| $19: 16$ | Capability Version - This field is a PCI-SIG defined version number that indicates the version of the <br> Capability structure present. <br> Must be 1h for this version of the specification. | RO |
| $31: 20$ | Next Capability Offset - This field contains the offset to the next PCI Express Capability structure or 000h <br> if no other items exist in the linked list of Capabilities. <br> For Extended Capabilities implemented in Configuration Space, this offset is relative to the beginning of <br> PCI-compatible Configuration Space and thus must always be either 000h (for terminating list of <br> Capabilities) or greater than 0FFh. | RO |

# 7.9.20.2 Alternate Protocol Capabilities Register (Offset 04h) 

![img-329.jpeg](img-329.jpeg)

Figure 7-344 Alternate Protocol Capabilities Register

Table 7-302 Alternate Protocol Capabilities Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| $7: 0$ | Alternate Protocol Count - Indicates the number of Alternate Protocols or protocols that support <br> Training Set Messages on one or more Lanes of this Link. <br> The value of this field must be greater than or equal to 0. | HwInit |
| 8 | Alternate Protocol Selective Enable Supported - If Set, the Alternate Protocol Selective Enable Mask <br> Register is present. If Clear, the Alternate Protocol Selective Enable Mask Register is not present and <br> Alternate Protocol Negotiation is controlled soley by the Alternate Protocol Negotiation Global Enable bit. <br> In Upstream Ports, this bit is hardwired to Ob. <br> In Downstream Ports, this bit is HwInit with an implementation specific default value. | RO/HwInit |

### 7.9.20.3 Alternate Protocol Control Register (Offset 08h)

![img-330.jpeg](img-330.jpeg)

Figure 7-345 Alternate Protocol Control Register

Table 7-303 Alternate Protocol Control Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $7: 0$ | Alternate Protocol Index Select - This field determines which Lane and which Alternate Protocol of that Lane is visible in Alternate Protocol Data 1 Register and Alternate Protocol Data 2 Register. <br> The default value of this field is 00 h . Unused bits in this field are permitted to be hardwired to 0 b . If Alternate Protocol Count is 01 h , this field is permitted to be hardwired to 00 h . <br> Behavior is undefined if this field is greater than Alternate Protocol Count. <br> Specific Alternate Protocol Index Select values are permitted to be disabled without renumbering other protocol index values. Disabled entries return an Alternate Protocol Vendor ID of FFFFh. | RW |
| 8 | Alternate Protocol Negotiation Global Enable - When this bit is Set, Alternate Protocol Negotiation is enabled for this Link. When this bit is Clear, Alternate Protocol Negotiation is disabled for this Link. <br> This bit is RW for Downstream Ports. It is HwInit for Upstream Ports. <br> Default is 0 b. | RW/HwInit (see description) |

# 7.9.20.4 Alternate Protocol Data 1 Register (Offset 0Ch) 

![img-331.jpeg](img-331.jpeg)

Figure 7-346 Alternate Protocol Data 1 Register

Table 7-304 Alternate Protocol Data 1 Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $2: 0$ | Alternate Protocol Usage Information - This field contains the Modified TS Usage associated alternate protocol associated with the Alternate Protocol Index Select value. <br> If Alternate Protocol Vendor ID is FFFFh, the value of this field is undefined. | RO |
| $15: 5$ | Alternate Protocol Details - This field contains the Alternate Protocol Details associated alternate protocol associated with the Alternate Protocol Index Select value. <br> If Alternate Protocol Vendor ID is FFFFh, the value of this field is undefined. | RO |
| $31: 16$ | Alternate Protocol Vendor ID - This field contains the Vendor ID associated alternate protocol associated with the Alternate Protocol Index Select value. <br> Bits 7:0 of this field contain bits 7:0 of Vendor ID (Symbol 10). <br> Bits 15:8 of this field contain bits 15:8 of Vendor ID (Symbol 11). <br> If Alternate Protocol Index Select is greater than or equal to Alternate Protocol Count, this field contains FFFFh. <br> If Alternate Protocol Index Select is associated with a disabled alternate protocol, this field contains FFFFh. | RO |

# 7.9.20.5 Alternate Protocol Data 2 Register (Offset 10h) 

![img-332.jpeg](img-332.jpeg)

Figure 7-347 Alternate Protocol Data 2 Register

Table 7-305 Alternate Protocol Data 2 Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 23:0 | Modified TS Information 2 - This field contains the value for symbols 12 throught 14 for the alternate protocol associated with the Alternate Protocol Index Select value. <br> If Alternate Protocol Vendor ID is FFFFh, the value of this field is undefined. <br> Bits 7:0 contain the value of Symbol 12. <br> Bits 16:8 contain the value of Symbol 13. <br> Bits 23:16 contain the value of Symbol 14. | RO |

### 7.9.20.6 Alternate Protocol Selective Enable Mask Register (Offset 14h)

This register is present if Alternate Protocol Selective Enable Supported is Set.
This register consists of a bit mask of size Alternate Protocol Count bits. Each bit corresponds to a valid value of Alternate Protocol Index Select. This register is an integral number of DWORDs in size.

When Alternate Protocol Negotiation Global Enable is Set, a particular bit in this register is Set, and the corresponding Alternate Protocol is not disabled (see Alternate Protocol Index Select), the next Alternate Protocol negotiation is permitted to consider using that Alternate Protocol. When a particular bit in this register is Clear, the next Alternate Protocol negotiation is not permitted to consider using the corresponding Alternate Protocol.

Changes to this field will affect the next Alternate Protocol negotiation and have no effect on current operation of the Link (regardless of current protocol).
![img-333.jpeg](img-333.jpeg)

Figure 7-348 Alternate Protocol Selective Enable Mask Register

Table 7-306 Alternate Protocol Selective Enable Mask Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 0 | Alternate Protocol Selective Enable Mask - PCI Express - The PCI Express Protocol is always index 00h. <br> The default value of this bit is 1 b (i.e., PCI Express is always enabled by default). | RWS |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | This bit is permitted to be hardwired to 1 b. |  |
| $31: 1$ | Alternate Protocol Selective Enable Mask - Others - Other bits in this register represent protocols other than PCI Express. The default values of these "other" bits is implementation specific. <br> The width of this field is shown here as 32 bits. The actual width depends on Alternate Protocol Count. <br> Bits in this field corresponding to disabled Alternate Protocol Index values are permitted to be hardwired to 0 b. <br> Bits in this field corresponding to Alternate Protocol Index Select values above Alternate Protocol Count are permitted to be hardwired to 0 b. | RWS |

# 7.9.21 Conventional PCI Advanced Features Capability (AF) 

This capability is optional. It is permitted only in Conventional PCI Functions that are integrated into a Root Complex. A Function may contain at most one instance of this capability.
§ Figure 7-349 shows the layout of this capability.
Note: Due to document production limitations, this figure shows an 8 byte capability while the actual capability is only 6 bytes long. Bytes 6 and 7 in the figure are not part of the capability.
![img-334.jpeg](img-334.jpeg)

Figure 7-349 Conventional PCI Advanced Features Capability (AF)

### 7.9.21.1 Advanced Features Capability Header (Offset 00h)

![img-335.jpeg](img-335.jpeg)

Figure 7-350 Advanced Features Capability Header

Table 7-307 Advanced Features Capability Header

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 7:0 | CAP_ID - The value of 13 h in this field identifies the Function as being AF capable. | RO |

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| $15: 8$ | NXT_PTR - Pointer to the next item in the capabilities list. Must be 00h for the final item in the list. | RO |
| $23: 16$ | LENGTH - AF Structure Length (Bytes). Shall return a value of 06h. | RO |

# 7.9.21.2 AF Capabilities Register (Offset 03h) 

![img-336.jpeg](img-336.jpeg)

Figure 7-351 AF Capabilities Register

Table 7-308 AF Capabilities Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 0 | TP_CAP - Set to indicate support for the Transactions Pending (TP) bit. TP_CAP must be Set if FLR_CAP is <br> Set. | HwInit |
| 1 | FLR_CAP - Set to indicate support for Function Level Reset (INITIATE_FLR). | HwInit |
| $7: 2$ | Reserved Reserved - Shall be implemented as read only returning a value of 000 0000b. | RO |

### 7.9.21.3 Conventional PCI Advanced Features Control Register (Offset 04h)

![img-337.jpeg](img-337.jpeg)

Figure 7-352 Conventional PCI Advanced Features Control Register

Table 7-309 Conventional PCI Advanced Features Control Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 0 | Function Level Reset (INITIATE_FLR) - A write of 1b initiates a Function Level Reset (FLR). Registers and <br> state information that do not apply to Conventional PCI are exempt from the FLR requirements in this <br> specification (see § Section 6.6.2). <br> The value read by software from this bit shall always be 0b. | RW |

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| $7: 1$ | Reserved Reserved - Shall be implemented as read only returning a value of 000 0000b. | RO |

# 7.9.21.4 AF Status Register (Offset 05h) 

![img-338.jpeg](img-338.jpeg)

Figure 7-353 AF Status Register

Table 7-310 AF Status Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 0 | Transactions Pending (TP) - A value of 1 b indicates that the Function has issued one or more <br> non-posted transactions which have not been completed, including non-posted transactions that a <br> target has terminated with Retry. <br> A value 0b indicates that all non-posted transactions have been completed. | RO |
| 7:1 | Reserved Reserved - Shall be implemented as read only returning a value of 000 0000b. | RO |

### 7.9.22 SFI Extended Capability

The SFI (System Firmware Intermediary) Extended Capability is an optional capability that provides system firmware with enhanced control over primarily hot-plug mechanisms, and enables system firmware to operate as an intermediary between certain events and the operating system (see $\S$ Section 6.7.4). This capability may be implemented by a Root Port or a Switch Downstream Port. It is not applicable to any other Device/Port type.

If a Downstream Port implements the SFI Extended Capability, that Port must support ERR_COR Subclass capability, and indicate so by Setting the ERR_COR Subclass Capable bit in the Device Capabilities Register. See see § Section 7.5.3.3.

![img-339.jpeg](img-339.jpeg)

Figure 7-354 SFI Extended Capability

# 7.9.22.1 SFI Extended Capability Header (Offset 00h) 

\$ Figure 7-355 and $\S$ Table 7-311 detail allocation of fields in the Extended Capability header.
![img-340.jpeg](img-340.jpeg)

Figure 7-355 SFI Extended Capability Header

Table 7-311 SFI Extended Capability Header

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $15: 0$ | PCI Express Extended Capability ID - This field is a PCI-SIG defined ID number that indicates the nature and format of the Extended Capability. <br> Extended Capability ID for the SFI Extended Capability is 002Ch. | RO |
| $19: 16$ | Capability Version - This field is a PCI-SIG defined version number that indicates the version of the Capability structure present. <br> Must be 1 h for this version of the specification. | RO |
| $31: 20$ | Next Capability Offset - This field contains the offset to the next PCI Express Capability structure or 000h if no other items exist in the linked list of Capabilities. <br> For Extended Capabilities implemented in Configuration Space, this offset is relative to the beginning of PCI-compatible Configuration Space and thus must always be either 000 h (for terminating list of Capabilities) or greater than 0FFh. | RO |

# 7.9.22.2 SFI Capability Register (Offset 04h) 

![img-341.jpeg](img-341.jpeg)

Figure 7-356 SFI Capability Register

Table 7-312 SFI Capability Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :-- |
| 0 | SFI OOB PD Supported - When Set, this bit indicates that this slot supports reporting the out-of-band <br> presence detect state. If this Downstream Port has no implemented slot (as indicated by the Slot <br> Implemented bit in the PCI Express Capabilities Register), then the value of this bit must be Ob. | HwInit |

### 7.9.22.3 SFI Control Register (Offset 06h) 

![img-342.jpeg](img-342.jpeg)

Figure 7-357 SFI Control Register

Table 7-313 SFI Control Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 0 | SFI PD State Mask - When Set, this bit masks the Presence Detect State bit in the Slot Status Register, <br> making its value Ob, regardless of the actual presence detect state. Otherwise, its value indicates the <br> actual state. | RW |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 1 | If the value of the Presence Detect State bit changes when the SFI PD State Mask bit value changes, this must cause a Presence Detect Changed event (see § Section 6.7.3). <br> Default value of this bit is 0 b . |  |
|  | SFI DLL State Mask - When Set, this bit masks the Data Link Layer Link Active bit in the Link Status Register, making its value 0b, regardless of the actual Data Link Layer state. Otherwise, its value indicates the actual state. <br> If the value of the Data Link Layer Link Active State bit changes when the SFI DLL State Mask bit value changes, this must cause a Data Link Layer State Changed event (see § Section 6.7.3). <br> Default value of this bit is 0 b . | RW |
| 2 | SFI OOB PD Changed Enable - When Set, this bit enables sending an ERR_COR Message for the SFI OOB PD Changed event. See § Section 6.7.4.1 for other necessary conditions. <br> This bit must be RW if the SFI OOB PD Supported bit is Set; otherwise, it is permitted to be hardwired to 0 b. If the SFI OOB PD Supported bit is Clear and software Sets this bit, the behavior is undefined. <br> Default value of this bit is 0 b . | RW/RO |
| 3 | SFI DLL State Changed Enable - When Set, this bit enables sending an ERR_COR Message for the SFI DLL State Changed event. See § Section 6.7.4.1 for other necessary conditions. <br> Default value of this bit is 0 b . | RW |
| 5:4 | SFI DPF Control - This field controls the level of Downstream Port Filtering (DPF) enabled on the Downstream Port, governing which Request TLPs targeting Downstream Components get filtered; that is, handled as if the Link is in DL_Down. See § Section 6.7.4.2 . <br> Defined encodings are: | RW |
|  | 00b <br> 01b <br> 10b <br> 11b <br> Default value of this field is 00 b . | Disabled <br> Filter all Request TLPs <br> Filter only Configuration Request TLPs <br> Reserved <br> Default value of this field is 00 b . |
| 6 | SFI HPS Suppress - When Set, this bit forces the Hot-Plug Surprise (HPS) bit in the Slot Capabilities Register to be Clear and disables associated Hot-Plug Surprise functionality. See § Section 6.7.4.4 . <br> Default value of this bit is 0 b . | RW |
| 7 | SFI DRS Mask - When Set, this bit masks the DRS Message Received bit in the Link Status 2 Register, making its value 0b, regardless of the actual DRS Message Received state. Otherwise, its value indicates the actual state. <br> If the value of the DRS Message Received bit changes from Clear to Set when the SFI DRS Mask bit is Cleared, this must trigger any notification enabled by the DRS Signaling Control field in the Link Control Register (see § Section 7.5.3.7). <br> Default value of this bit is 0 b . | RW |
| 8 | SFI DRS Signaling Enable - When Set, this bit enables sending an ERR_COR Message for the SFI DRS Received event. See § Section 6.7.4.1 for other necessary conditions. <br> Default value of this bit is 0 b . | RW |
| 9 | SFI DRS Trigger - If the SFI DRS Mask bit is Clear, when software writes a 1b to this bit, the Downstream Port must behave as if a DRS Message was received. Otherwise, software writing a 1b to this bit has no effect. | RW |

| Bit Location | Register Description | Attributes |
| :-- | :-- | :-- |
|  | It is permitted to write 1 b to this bit while simultaneously writing updated values to other fields in this <br> register, notably the SFI DRS Mask bit. For this case, the SFI DRS Trigger semantics are based on the <br> updated value of the SFI DRS Mask bit. |  |
|  | This bit always returns 0 b when read. |  |

# 7.9.22.4 SFI Status Register (Offset 08h) 

![img-343.jpeg](img-343.jpeg)

Figure 7-358 SFI Status Register

Table 7-314 SFI Status Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 0 | SFI PD State - This bit always indicates the actual presence detect state associated with the Presence Detect State bit in the Slot Status Register, even when the value of that bit is being masked by the SFI PD State Mask bit. | RO |
| 1 | SFI OOB PD State - This bit indicates the out-of-band presence detect state, independent of the in-band presence detect state. <br> This bit must be implemented if the SFI OOB PD Supported bit is Set; otherwise, it is permitted to be hardwired to 0 b. | RO |
| 2 | SFI OOB PD Changed - This bit is Set when the value reported in the SFI OOB PD State bit is changed. | RW1C |
| 3 | SFI DLL State - This bit always indicates the actual link state associated with the Data Link Layer Link Active bit in the Link Status Register, even when the value of that bit is being masked by the SFI DLL State Mask bit. | RO |
| 4 | SFI DLL State Changed - This bit is Set when the value reported in the SFI DLL State bit is changed. | RW1C |
| 5 | SFI DRS Received - This bit always indicates the actual state associated with the DRS Message Received bit in the Link Status 2 Register, even when the value of that bit is being masked by the SFI DRS Mask bit. <br> Clearing the SFI DRS Received bit (by writing a 1b to it) must also cause the actual state associated with the DRS Message Received bit to be Cleared. | RW1C |

# 7.9.22.5 SFI CAM Address Register (Offset 0Ch) 

![img-344.jpeg](img-344.jpeg)

Figure 7-359 SFI CAM Address Register

Table 7-315 SFI CAM Address Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 27:0 | SFI CAM Address - This field specifies the target Bus, Device, and Function Numbers, along with the <br> Extended Register Number and Register Number, in the format specified by \$ Table 7-1. | RW |

### 7.9.22.6 SFI CAM Data Register (Offset 10h)

![img-345.jpeg](img-345.jpeg)

Figure 7-360 SFI CAM Data Register

Table 7-316 SFI CAM Data Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 31:0 | SFI CAM Data - When this field is read, the SFI CAM generates and transmits a Configuration Read <br> Request on the Link below this Port. When this field is written, the SFI CAM generates and transmits a <br> Configuration Write Request on the Link below this Port. In both cases, the target of the Configuration <br> Request is determined by the value of the SFI CAM Address Register. See § Section 6.7.4.3. | RW |

### 7.9.23 Subsystem ID and Subsystem Vendor ID Capability

The Subsystem ID and Subsystem Vendor ID Capability is an optional capability used to uniquely identify the add-in card or subsystem where the PCI device resides. It provides a mechanism for add-in card vendors to distinguish their add-in cards from one another even though the add-in cards may have the same PCI bridge on them (and, therefore, the same Vendor ID and Device ID). The format of the capability is shown in § Figure 7-361. The fields are described in § Table $7-317$ and $\S$ Table 7-318.

This capability is only permitted in Functions with Type 1 Configuration Space Headers.

| 31 | 30 | 29 | 28 | 27 | 26 | 25 | 24 | 23 | 22 | 21 | 20 | 19 | 18 | 17 | 16 | 15 | 14 | 13 | 12 | 11 | 10 | 9 | 8 | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 | Byte Offset |
| :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: |
|  | Reserved | Next Capability Pointer | Capability ID |  |  |  |  |  |  |
|  | SSID | SSVID |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |

Figure 7-361 Subsystem ID and Subsystem Vendor ID Capability

# 7.9.23.1 Subsystem ID and Subsystem Vendor ID Capability Header (Offset 00h) 

![img-346.jpeg](img-346.jpeg)

Figure 7-362 Subsystem ID and Subsystem Vendor ID Capability Header

Table 7-317 Subsystem ID and Subsystem Vendor ID Capability Header

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| $7: 0$ | Capability ID - Indicates the PCI Express Capability structure. This field must return a Capability ID of <br> 00h indicating that this is a Subsystem ID and Subsystem Vendor ID Capability structure. | RO |
| $15: 8$ | Next Capability Pointer - This field contains the offset to the next PCI Capability structure or 00h if no <br> other items exist in the linked list of Capabilities. | RO |

### 7.9.23.2 Subsystem ID and Subsystem Vendor ID Capability Data (Offset 04h) 

![img-347.jpeg](img-347.jpeg)

Figure 7-363 Subsystem ID and Subsystem Vendor ID Capability Data

Table 7-318 Subsystem ID and Subsystem Vendor ID Capability Data

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| $15: 0$ | SSVID - The SSVID identifies the manufacturer of the add-in card or subsystem. The SSVID is assigned by <br> PCI-SIG to insure uniqueness (the Vendor ID is used as the SSVID also). This field is read-only. | HwInit |

| Bit Location | Register Description | Attributes |
| :--: | :-- | :-- |
| 31:16 | SSID - The SSID identifies the particular add-in card or subsystem and is assigned by the vendor. This <br> field is read-only. | HwInit |

# 7.9.24 Data Object Exchange Extended Capability $\S$ 

The Data Object Exchange (DOE) Extended Capability is an optional Extended Capability for discovering and controlling a mechanism for the exchange of data objects (see $\S$ Section 6.30 ). It is permitted for a Function to implement more than one instance of this Extended Capability.
§ Figure 7-364 illustrates the Data Object Exchange Extended Capability structure.
![img-348.jpeg](img-348.jpeg)

Figure 7-364 Data Object Exchange Extended Capability

### 7.9.24.1 DOE Extended Capability Header (Offset 00h) $\S$
![img-349.jpeg](img-349.jpeg)

Figure 7-365 DOE Extended Capability Header $\S$

Table 7-319 DOE Extended Capability Header $\S$

| Bit Location | Register Description | Attributes |
| :--: | :-- | :-- |
| 15:0 | PCI Express Extended Capability ID - This field is a PCI-SIG defined ID number that indicates the nature <br> and format of the Extended Capability. | RO |
|  | The Extended Capability ID for the Data Object Exchange Extended Capability is 002Eh. |  |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 19:16 | Capability Version - This field is a PCI-SIG defined version number that indicates the version of the Capability structure present. <br> Must be 2 h for this version of the specification. <br> New implementations compliant to the older version of this specification must indicate Capability Version 1h. | RO |
| $31: 20$ | Next Capability Offset - This field contains the offset to the next PCI Express Extended Capability structure or 000 h if no other items exist in the linked list of Capabilities. | RO |

# 7.9.24.2 DOE Capabilities Register (Offset 04h) 

![img-350.jpeg](img-350.jpeg)

Figure 7-366 DOE Capabilities Register

Table 7-320 DOE Capabilities Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 0 | DOE Interrupt Support - When Set, this bit indicates DOE support of software notification of DOE events using MSI/MSI-X. | HwInit |
| $11: 1$ | DOE Interrupt Message Number - When the DOE Interrupt Support bit is Set, this field indicates which MSI/MSI-X vector is used for the interrupt message generated in association with DOE. <br> For MSI, the value in this field indicates the offset between the base Message Data and the interrupt message that is generated. Hardware is required to update this field so that it is correct if the number of MSI Messages assigned to the Function changes when software writes to the Multiple Message Enable field in the Message Control Register for MSI. <br> For MSI-X, the value in this field indicates which MSI-X Table entry is used to generate the interrupt message. For a given MSI-X implementation, the entry must remain constant. <br> If both MSI and MSI-X are implemented, they are permitted to use different vectors, though software is permitted to enable only one mechanism at a time. If MSI-X is enabled, the value in this field must indicate the vector for MSI-X. If MSI is enabled or neither is enabled, the value in this field must indicate the vector for MSI. If software enables both MSI and MSI-X at the same time, the value in this field is undefined. <br> When the DOE Interrupt Support bit is Clear the value in this field is undefined. | RO |
| 12 | DOE Attention Mechanism Support - This bit, when Set, indicates the DOE instance supports the optional DOE Attention mechanism. | HwInit |
| 13 | DOE Async Message Support - This bit, when Set, indicates the DOE instance supports the optional DOE Async Message mechanism. | HwInit |

# 7.9.24.3 DOE Control Register (Offset 08h) 

![img-351.jpeg](img-351.jpeg)

Figure 7-367 DOE Control Register

Table 7-321 DOE Control Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 0 | DOE Abort - A write of 1b to this bit must cause all data object transfer operations associated with this DOE instance to be aborted. <br> Reads from this bit must always return 0b. | RW (see description) |
| 1 | DOE Interrupt Enable - When this bit is Set, the DOE Interrupt Support bit is Set, and MSI/MSI-X is enabled, the DOE instance must issue an MSI/MSI-X interrupt as defined in § Section 6.30.3 . <br> When DOE Interrupt Support is Clear, this bit is permitted to be Reserved. <br> Default value of this bit is 0 b. | RW/RsvdP |
| 2 | DOE Attention Not Needed - When DOE Attention Mechanism Support is Set, this bit when Set enables the DOE instance to enter and stay in a state where it is not immediately available for use. When this bit is Clear the DOE instance must remain in a responsive state. <br> When DOE Attention Mechanism Support is Clear, this bit is permitted to be Reserved. <br> Default value of this bit is 0 b. | RW/RsvdP |
| 3 | DOE Async Message Enable - If DOE Async Message Support is Set, this bit, when Set, enables the use of the DOE Async Message mechanism. <br> When DOE Async Message Support is Clear, this bit is permitted to be Reserved. <br> Default value of this bit is 0 b. | RW/RsvdP |
| 31 | DOE Go - A write of 1b to this bit indicates to the DOE instance that it can start consuming the data object transferred through the DOE Write Data Mailbox Register. <br> Behavior is undefined if the DOE Go bit is Set before the entire data object has been written to the DOE Write Data Mailbox Register. <br> Behavior is undefined if the DOE Go bit is written with 1b when the DOE Busy bit is Set. <br> Reads from this bit must always return 0b. | RW (see description) |

# 7.9.24.4 DOE Status Register (Offset 0Ch) 

![img-352.jpeg](img-352.jpeg)

Figure 7-368 DOE Status Register

Table 7-322 DOE Status Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 0 | DOE Busy - When Set, this bit indicates the DOE instance is temporarily unable to receive a new data object through the DOE Write Data Mailbox Register. <br> The DOE instance must Set this bit when processing a received data object, and Clear this bit when it is able to receive a new data object. <br> The DOE instance must Set this bit following an abort or reset if, as a result of the abort/reset, it is temporarily unable to receive a data object, and then must Clear this bit when it is able to receive a new data object. | RO |
| 1 | DOE Interrupt Status - If DOE Interrupt Support is Set, then this bit must be Set when an interrupt-triggering event occurs. <br> If DOE Interrupt Support is Clear, this bit is Reserved. <br> Default value of this bit is Ob. | RW1C/RsvdZ |
| 2 | DOE Error - This bit, when Set, indicates that there has been an internal error associated with a data object received, or that a data object has been received for which the DOE instance is unable to provide a response. <br> The DOE instance must Clear this bit, if it is not already Clear, when 1 b is written to the DOE Abort bit in the DOE Control Register. Writing 1b to the DOE Abort bit is the only mechanism for software to Clear this bit. <br> The transition of this bit from Clear to Set is an interrupt triggering event. <br> Default value of this bit is Ob. | RO |
| 3 | DOE Async Message Status - If DOE Async Message Support is Set, this bit, when Set, indicates the DOE instance has one or more asynchronous messages to transfer. <br> The transition of this bit from Clear to Set is an interrupt triggering event. <br> If DOE Async Message Support is Clear, this bit is Reserved. <br> Default value of this bit is Ob. | RO/RsvdZ |
| 4 | DOE At Attention - When DOE Attention Mechanism Support is Set, this bit, when Set, indicates the DOE interface is presently in a state of readiness. <br> The transition of this bit from Clear to Set is an interrupt triggering event. | RO |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | When DOE Attention Mechanism Support is Clear, this bit is Reserved. |  |
| 31 | Data Object Ready - When Set, this bit indicates the DOE instance has a data object available to be read by system firmware/software. <br> If there is no additional data object ready for transfer, the DOE instance must clear this bit after the entire data object has been transferred, as indicated by software writing to the DOE Read Data Mailbox Register after reading the final DW of the data object. <br> The DOE instance must clear this bit, if not already clear, upon a write of 1 b to the DOE Abort bit in the DOE Control Register. <br> The transition of this bit from Clear to Set is an interrupt triggering event. <br> Default value of this bit is 0 b. | RO |

# 7.9.24.5 DOE Write Data Mailbox Register (Offset 10h) 

![img-353.jpeg](img-353.jpeg)

Figure 7-369 DOE Write Data Mailbox Register

Table 7-323 DOE Write Data Mailbox Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 31:0 | DOE Write Data Mailbox - The DOE instance receives data objects via writes to this register. <br> A successfully completed write to this register adds one DW to the incoming data object. <br> Setting the DOE Go bit in the DOE Control Register indicates to the DOE Instance that the final DW of the data object has been written to this register. <br> Reads of this register must return all 0's. | RW (see description) |

### 7.9.24.6 DOE Read Data Mailbox Register (Offset 14h) 

![img-354.jpeg](img-354.jpeg)

Figure 7-370 DOE Read Data Mailbox Register

Table 7-324 DOE Read Data Mailbox Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 31:0 | DOE Read Data Mailbox - If the Data Object Ready bit is Set, a read of this register returns the current DW of the data object. | RW (see description) |
|  | A write of any value to this register indicates a successful transfer of the current data object DW, and the DOE instance must return the next DW in the data object upon the next read of this register as long as the Data Object Ready bit remains Set. |  |
|  | It is permitted for multiple data objects to be read from this register back-to-back. When this scenario occurs, the Data Object Ready bit will remain Set until this register is written after the final DW is read. |  |
|  | A write of any value to this register when the Data Object Ready bit is Clear must have no effect. |  |
|  | The value read from this register when the Data Object Ready bit is Clear must be 00000000 h . |  |

# 7.9.25 Shadow Functions Extended Capability 

Unimplemented Functions possess Transaction ID resources by virtue of their Bus/Device/Function Number space, and therefore associated Requester ID space, and associated Tags, even though there is no Function implemented there to use them. The Shadow Functions Extended Capability is an optional capability that permits a Requester to use the Transaction ID resources of another otherwise unimplemented Function to generate more outstanding Requests than it would otherwise be able to using only the Transaction ID resources of the Function it is associated with. The Requester generates some of its Requests via the Function it is associated with and generates other Requests via the Shadow Function. If the Requester exceeds the Transaction ID resources of a single Function, it is permitted to implement this capability and split its Transaction ID space across that Function and additional Shadow Functions defined by this capability.

A Requester implementing a Shadow Function uses the characteristics and attributes of the Function containing this capability. Requests made via the associated Function will use the associated Function's BDF to populate the Requester ID. Requests made via the Shadow Function will use the BDF calculated from the value in the Shadow Function Number field of the corresponding Shadow Function Instance register entry to populate the Requester ID. Other characteristics and attributes of the Shadow Function are taken from the associated Function's Configuration Space.

The Shadow Function Number field in the Shadow Function Instance register entry for each Shadow Function is used to calculate the value of the Bus/Device/Function number (Bus/Function number for ARI devices) (BDF) for that Shadow Function. That BDF space assigned to the Shadow Function must be available, that is it corresponds to an otherwise unimplemented Function.

Additional requirements for implementing Shadow Functions are:

- Any access to the Configuration Space region of the BDF associated with the Shadow Function, without errors that would have different behavior, must be responded to with a Completion with UR status.
- For non-ARI Devices, the Shadow Function must reside in the same Device as the Function it is shadowing. ARI must be supported if the Shadow Function Number is greater than 7.
- A Function is permitted to have more than one Shadow Function.
- A Function is permitted to have at most one instance of this capability.
- This capability is permitted to be implemented in any Function capable of operating as a Requester.
- For VFs, the Shadow Functions must be assigned in a manner that accommodates the VF Discovery algorithm (see § Section 9.2.1.2).
- Requesters are permitted to generate Posted Requests that are not Message Signaled Interrupt (MSI/MSI-X) Requests using the Transaction ID space of a Shadow Function.

- Requesters are not permitted to generate Message Signaled Interrupt (MSI/MSI-X) Requests using the Transaction ID space of a Shadow Function.
- Functions utilizing Shadow Functions must be aware that accesses utilizing the Shadow Function's Transaction ID resources appear to the rest of the system with the same semantics as if the access was from any independent Function and deal with those implications.
- The software for the Translation Agent is responsible for maintaining the integrity of address translation resources. Behavior is undefined if address translation resources are not updated before the Shadow Function's Requester makes a Request.
- Translation Requests issued by a Shadow Function are cached in the ATC associated with the main Function. When enabled, Functions are permitted to use translations across the "main" and Shadow Functions regardless of which Function issued the associated Translation Request. See § Section 10.2 .
- The software for handling Page Request Messages is responsible for coordinating usage across Shadow Functions. See § Section 10.4.1 and § Section 10.5.2.5 .
- Behavior is undefined if software enabling FPB configures a Shadow Function to use the same Requester ID as another Function.
- For a Multi-Function Device that supports ACS P2P Egress Control, any enabled Shadow Functions must be taken into account when configuring the Egress Control Vector to allow P2P traffic between the Requester and its Shadow Functions, and other Functions in the Device.


# IMPLEMENTATION NOTE: <br> SHADOW FUNCTION NUMBER PROGRAMMING § 

The value programmed into the Shadow Function Number field should place the Shadow Function on the same Bus Number as the Function declaring it. Otherwise, ACS Source Validation might not operate appropriately, Completions targeting the Shadow Function might not be routed correctly, or other misbehaviors might occur.

Multiple Shadow Functions for a Function are permitted to be assigned by this Capability. The Number of Shadow Functions field in the Shadow Functions Capability register defines the number of Shadow Functions assigned and the number of Shadow Function Instance register entries in the Capability and therefore the length of the Capability structure.
§ Figure 7-371 shows the Shadow Functions Extended Capability structure.

$N=$ the value of the Number of Shadow Functions field.
![img-355.jpeg](img-355.jpeg)

Figure 7-371 Shadow Functions Extended Capability Structure

# 7.9.25.1 Shadow Functions Extended Capability Header (Offset 00h) 

\$ Figure 7-372 details allocation of the register fields in the Shadow Functions Extended Capability Header; \$ Table 7-325 provides the respective bit definitions.
![img-356.jpeg](img-356.jpeg)

Figure 7-372 Shadow Functions Extended Capability Header

Table 7-325 Shadow Functions Extended Capability Header

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 15:0 | Shadow Functions Extended Capability ID - Indicates the Shadow Functions Extended Capability structure. This field must return a Capability ID of 0020 h indicating that this is a Shadow Functions Extended Capability structure. | RO |
| 19:16 | Capability Version - This field is a PCI-SIG defined version number that indicates the version of the Capability structure present. <br> Must be 1 h for this version of the specification. | RO |
| 31:20 | Next Capability Offset - The offset to the next PCI Extended Capability structure or 000 h if no other items exist in the linked list of capabilities. | RO |

# 7.9.25.2 Shadow Functions Capability Register (Offset 04h) 

\$ Figure 7-373 details the allocation of register bits of the Shadow Functions Capability register; \$ Table 7-326 provides the respective bit definitions.
![img-357.jpeg](img-357.jpeg)

Figure 7-373 Shadow Functions Capability Register

Table 7-326 Shadow Functions Capability Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :-- |
| $7: 0$ | Number of Shadow Functions - This is one less than the number of Shadow Functions implemented by <br> this Function. This defines the number of Shadow Function Instance register entries that are in the <br> Capability, and therefore the length of the Capability structure. <br> The default value for this field is 00 h. | HwInit |

### 7.9.25.3 Shadow Functions Control Register (Offset 08h) $\S$

§ Figure 7-374 details the allocation of register bits of the Shadow Functions Control register; § Table 7-327 provides the respective bit definitions.
![img-358.jpeg](img-358.jpeg)

Figure 7-374 Shadow Functions Control Register

Table 7-327 Shadow Functions Control Register

| Bit <br> Location | Register Description | Attributes |
| :--: | :-- | :-- |
| 0 | Shadow Functions Enable - When Set, permits the Requester to generate Requests using the Transaction ID <br> resources of all of the Shadow Functions defined by this Capability. See $\S$ Section 7.9.25 for limitations on <br> the type of Requests permitted. <br> When Clear, the Requester is not permitted to generate Requests using the Transaction ID resources of any <br> of the Shadow Functions defined by this Capability. <br> Behavior is undefined when this bit is Set in Functions with the Phantom Functions Enabled bit Set. | RW |

| Bit <br> Location | Register Description | Attributes |
| :-- | :-- | :-- |
| Behavior is undefined if the value of this bit is changed while the Function has outstanding Non-Posted <br> Requests. <br> Default is Ob. |  |  |

# 7.9.25.4 Shadow Functions Instance Register Entry 

§ Figure 7-375 details the allocation of register bits of the Shadow Functions Control register; § Table 7-328 provides the respective bit definitions.
![img-359.jpeg](img-359.jpeg)

Figure 7-375 Shadow Functions Instance Register Entry

Table 7-328 Shadow Functions Instance Register Entry

| Bit <br> Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 15:0 | Shadow Function Number - This is the Bus/Device/Function offset (Bus/Function offset for ARI Devices) of the Shadow Function. Add this value to BDF of the Function with this capability using unsigned, 16-bit arithmetic, ignoring any carry. | HwInit |

### 7.9.26 IDE Extended Capability

All Ports that implement IDE must implement the IDE Extended Capability. The IDE Extended Capability must consist of the IDE Extended Capability Header, the IDE Capability Register, and the IDE Control Register, followed by zero to 8 Link IDE register blocks, followed by zero to 255 Selective IDE register blocks (see § Figure 7-376). All Ports that implement IDE must implement the IDE Extended Capability. The IDE Extended Capability must consist of the IDE Extended Capability Header, the IDE Capability Register, and the IDE Control Register, followed by zero to 8 Link IDE register blocks, followed by zero to 255 Selective IDE register blocks (see § Figure 7-376).

It is permitted to implement this extended capability in Functions associated with Downstream Ports, and in Function 0 associated with an Upstream Port. Multi-Function Devices associated with Upstream Ports, including cases where one or more Functions represent the Upstream Port of a Switch, must be implemented such that Function 0 implements this extended capability representing the Multi-Function Device as a whole.

![img-360.jpeg](img-360.jpeg)

Figure 7-376 IDE Extended Capability Structure 5

# 7.9.26.1 IDE Extended Capability Header (Offset 00h) 

![img-361.jpeg](img-361.jpeg)

Figure 7-377 IDE Extended Capability Header 6

Table 7-329 IDE Extended Capability Header 5

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $15: 0$ | PCI Express Extended Capability ID - This field is a PCI-SIG defined ID number that indicates the nature and format of the Extended Capability. <br> The Extended Capability ID for the Integrity and Data Encryption (IDE) Exchange Extended Capability is 0030h. | HwInit |
| 19:16 | Capability Version - This field is a PCI-SIG defined version number that indicates the version of the Capability structure present. <br> Must be 1 h for this version of the specification. | HwInit |
| $31: 20$ | Next Capability Offset - This field contains the offset to the next PCI Express Extended Capability structure or 000 h if no other items exist in the linked list of Capabilities. | HwInit |

# 7.9.26.2 IDE Capability Register (Offset 04h) 

![img-362.jpeg](img-362.jpeg)

Figure 7-378 IDE Capability Register

Table 7-330 IDE Capability Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 0 | Link IDE Stream Supported - When Set, indicates that the Port supports Link IDE Streams, and that one or more Link IDE Stream Registers block(s) immediately follow the IDE Control Register, per the value in the Number of TCs Supported for Link IDE field. <br> When Clear, there must be no Link IDE Stream Register blocks present. | HwInit / RsvdP |
| 1 | Selective IDE Streams Supported - When Set, indicates that the Port support Selective IDE Streams, and that one or more Selective IDE Stream Register block(s) are implemented, per the value in the Number of Selective IDE Streams Supported field. <br> When Clear, there must be no Selective IDE Stream Register blocks present. | HwInit / RsvdP |
| 2 | Flow-Through IDE Stream Supported - For a Switch or Root Port, when Set indicates support for passing Selective IDE Streams to all other Switch or Root Ports. <br> If this bit is Set and both Link IDE Stream Supported and Selective IDE Streams Supported are Clear, then no Link IDE register blocks or Selective IDE register blocks are required. <br> Reserved for Endpoints. | HwInit / RsvdP |
| 3 | Partial Header Encryption Supported - If Link IDE Stream Supported or Selective IDE Streams Supported are Set, then this bit, when Set, indicates the Port supports partial header encryption. Undefined if Link IDE Stream Supported and Selective IDE Streams Supported are both Clear. | HwInit |
| 4 | Aggregation Supported - If Link IDE Stream Supported or Selective IDE Streams Supported are Set, then this bit, when Set, indicates the Port supports aggregation. <br> Undefined if Link IDE Stream Supported and Selective IDE Streams Supported are both Clear. | HwInit |
| 5 | PCRC Supported - When Set, indicates that the Port supports the generation and checking of PCRC. | HwInit |
| 6 | IDE_KM Protocol Supported - When Set, indicates that the Port supports the IDE_KM protocol in the responder role as defined in $\S$ Section 6.33.3 | HwInit |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 7 | Selective IDE for Configuration Requests Supported - For a Root Port, Switch Upstream Port, or Endpoint Upstream Port, if Selective IDE Streams Supported is Set, then this bit, if Set, indicates that the Port supports the assocation of Configuration Requests with Selective IDE Streams. <br> For a Switch Upstream Port, when Set, this bit indicates the Switch supports Selective IDE for Configuration Requests targeting all Functions of the Switch. <br> This bit is Reserved for Switch Downstream Ports. <br> If Selective IDE Streams Supported is Clear, this bit is Reserved. | HwInit / RsvdP |
| 12:8 | Supported Algorithms - Indicates the supported algorithms for securing IDE TLPs, encoded as: <br> 00000b AES-GCM 256 key size, 96b MAC <br> Others Reserved | HwInit |
| 15:13 | Number of TCs Supported for Link IDE - If Link IDE Stream Supported is Set, indicates the number of TCs supported for Link IDE Streams encoded as: <br> 000b One TC supported <br> 001b 2 TCs supported <br> 010b 3 TCs supported <br> 011b 4 TCs supported <br> 100b 5 TCs supported <br> 101b 6 TCs supported <br> 110b 7 TCs supported <br> 111b 8 TCs supported <br> If Link IDE Stream Supported is Clear, this field is undefined. | HwInit |
| 23:16 | Number of Selective IDE Streams Supported - If Selective IDE Streams Supported is Set then this field indicates number of Selective IDE Streams Supported such that $0=1$ Stream. <br> A corresponding number of Selective IDE Stream Register Block(s) must be implemented. If Link IDE Stream Supported is Clear, then these blocks must immediately follow the IDE Control Register. If Link IDE Stream Supported is Set, then these blocks must immediately follow the Link IDE Stream Control and Status Registers. <br> If Selective IDE Streams Supported is Clear, this field is undefined. | HwInit / RsvdP |
| 24 | TEE-Limited Stream Supported - When Set, indicates that the TEE-Limited Stream control mechanism is supported. <br> If Selective IDE Streams Supported is Clear, this bit is Reserved. | HwInit / RsvdP |

# 7.9.26.3 IDE Control Register (Offset 08h) 

![img-363.jpeg](img-363.jpeg)

Figure 7-379 IDE Control Register

Table 7-331 IDE Control Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 2 | Flow-Through IDE Stream Enabled - For Switch Ports and Root Ports, Enables the Port for flow-through <br> operation of TLPs associated with Selective IDE Streams. <br> Reserved for Upstream Ports associated with Endpoints. | RW / <br> RsvdP |

### 7.9.26.4 Link IDE Register Block 

A Link IDE register block must consist of one Link IDE Stream Control Register followed by one Link IDE Stream Status Register. If the Link IDE Stream Supported bit in the IDE Capability Register is Set, then this register block must be instantiated once for each Traffic Class (TC) supported as indicated in the Number of TCs Supported for Link IDE field.

### 7.9.26.4.1 Link IDE Stream Control Register

![img-364.jpeg](img-364.jpeg)

Figure 7-380 Link IDE Stream Control Register

Table 7-332 Link IDE Stream Control Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 0 | Link IDE Stream Enable - When Set, enables Link IDE Stream such that IDE operation will start when triggered by means of the IDE_KM protocol (see § Section 6.33.3). When Cleared, must immediately transition the Stream to Insecure. <br> Software must not modify the PCRC Enable bit while this bit is Set; otherwise, the result is undefined. <br> It is permitted for the default value to be 1 b if and only if implementation specific means can ensure that the Link IDE Stream will default into a state where operation in the Secure state is possible, otherwise the default value must be 0 b . | RW |
| $3: 2$ | Tx Aggregation Mode NPR - If Aggregation Supported is Set then this field selects the level of aggregation for Transmitted Non-Posted Requests for this Stream, encoded as: <br> 00b No aggregation <br> 01b Up to 2 Non-Posted Requests <br> 10b Up to 4 Non-Posted Requests <br> 11b Up to 8 Non-Posted Requests <br> Reserved If Aggregation Supported is Clear. <br> Default value is 00 b | $\begin{aligned} & \text { RW / } \\ & \text { RsvdP } \end{aligned}$ |
| $5: 4$ | Tx Aggregation Mode PR - If Aggregation Supported is Set then this field selects the level of aggregation for Transmitted Posted Requests for this Stream, encoded as: <br> 00b No aggregation <br> 01b Up to 2 Posted Requests <br> 10b Up to 4 Posted Requests <br> 11b Up to 8 Posted Requests <br> Reserved If Aggregation Supported is Clear. <br> Default value is 00 b | RW/ RsvdP |
| $7: 6$ | Tx Aggregation Mode CPL - If Aggregation Supported is Set then this field selects the level of aggregation for Trasmitted Completions for this Stream, encoded as: <br> 00b No aggregation <br> 01b Up to 2 Completions <br> 10b Up to 4 Completions <br> 11b Up to 8 Completions <br> Reserved If Aggregation Supported is Clear. <br> Default value is 00 b | RW/ RsvdP |
| 8 | PCRC Enable - When Set, Transmitted IDE TLPs associated with this Stream that include $P$ content must include PCRC, and Received TLPs must be checked for PCRC failure. <br> Reserved if PCRC Supported is Clear. <br> Default value is 0 b . | RW/ RsvdP |
| $13: 10$ | Partial Header Encryption Mode - Selects the mode to be used for partial header encryption of IDE TLPs for this IDE Stream. Must be programmed to the same value in both the Partner Ports. Must be configured while Link IDE Stream Enable is Clear. When Link IDE Stream Enable is Set, the setting is sampled, and this field becomes RO with reads returning the sampled value. <br> 0000b No partial header encryption | RW/RO/ RsvdP |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | 0001b <br> 0010b <br> 0011b <br> 0100b <br> Others <br> If Partial Header Encryption Supported is Clear, this field is Reserved. | Address[17:2] Encrypted, and, if present, the First DW BE and Last DW BE fields Address[25:2] Encrypted, and, if present, the First DW BE and Last DW BE fields Address[41:2] Encrypted, and, if present, the First DW BE and Last DW BE fields Reserved <br> If present, the First DW BE and Last DW BE fields <br> RW / RO |
| 18:14 | Selected Algorithm - Selects the algorithm to be used for securing IDE TLPs for this IDE Stream. Must be programmed to the same value in both the Upstream and Downstream Ports. Must be configured while Link IDE Stream Enable is Clear. When Link IDE Stream Enable is Set, the setting is sampled, and this field becomes RO with reads returning the sampled value. <br> 0 0000b AES-GCM 256 key size, 96b MAC <br> Others Reserved |  |
| 21:19 | TC - System firmware/software must program this field to indicate the TC associated with this Link IDE Register block. <br> Default value is 000 b | RW / <br> RsvdP |
| $31: 24$ | Stream ID - Indicates the Stream ID associated with this Link IDE Stream. Software must program the same Stream ID into both Ports associated with a given Link IDE Stream. Default value is 00 h . | RW |

# 7.9.26.4.2 Link IDE Stream Status Register 

![img-365.jpeg](img-365.jpeg)

Figure 7-381 Link IDE Stream Status Register

Table 7-333 Link IDE Stream Status Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $3: 0$ | Link IDE Stream State - When Link IDE Stream Enable is Set, this field indicates the state of the Port. Encodings: | RO |
|  | 0000b <br> 0010b <br> Others <br> When Link IDE Stream Enable is Clear, the value of this field must be 0000b. |  |
| 31 | Received IDE Fail Message - When Set, indicates that one or more IDE Fail Message(s) have been Received for this Stream. | RW1C |

# 7.9.26.5 Selective IDE Stream Register Block 

A Selective IDE Stream register block must consist of one Selective IDE Stream Capability Register, followed by one Selective IDE Stream Control Register, followed by one Selective IDE Stream Status Register, followed by one Selective IDE RID Association register Block, followed by zero or more Selective IDE Address Association Register Block(s) . If the Selective IDE Streams Supported bit in the IDE Capability Register is Set, then this register block must be instantiated once for each Selective IDE Stream supported as indicated in the Number of Selective IDE Streams Supported field.

### 7.9.26.5.1 Selective IDE Stream Capability Register

![img-366.jpeg](img-366.jpeg)

Figure 7-382 Selective IDE Stream Capability Register

Table 7-334 Selective IDE Stream Capability Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 3:0 | Number of Address Association Register Blocks - Indicates the number of Selective IDE Address <br> Association register blocks for this Selective IDE Stream. <br> The number of Selective IDE Address Association register blocks for a given IDE Stream is hardware <br> implementation specific, and is permitted to be any number between 0 and 15. | RO |

### 7.9.26.5.2 Selective IDE Stream Control Register

![img-367.jpeg](img-367.jpeg)

Figure 7-383 Selective IDE Stream Control Register

Table 7-335 Selective IDE Stream Control Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 0 | Selective IDE Stream Enable - When Set, enables this IDE Stream such that IDE operation will start when triggered by means of the IDE_KM protocol (see $\S$ Section 6.33.3). When Cleared, must immediately transition the Stream to Insecure. Software must configure the following before Setting this bit, and must not modify them while this bit is Set; otherwise, the result is undefined: <br> - Selected Algorithm (below) <br> - PCRC Enable <br> - Requester ID Limit in IDE RID Association Register 1 <br> - Requester ID Base, and Segment Base if applicable, in IDE RID Association Register 2 <br> - V bit in IDE RID Association Register 2 <br> If this bit is Set when the V bit is Clear, the IDE Stream must transition to Insecure. <br> When Cleared, must immediately transition the Stream to Insecure. <br> It is strongly recommended that the IDE Address Association Registers, and the Default Stream bit (if applicable), also be programmed prior to Setting this bit. <br> Default value is Ob. | RW <br> RsvdP |
| $3: 2$ | Tx Aggregation Mode NPR - If Aggregation Supported is Set then this field selects the level of aggregation for Transmitted Non-Posted Requests for this Stream, encoded as: <br> 00b No aggregation <br> 01b Up to 2 Non-Posted Requests <br> 10b Up to 4 Non-Posted Requests <br> 11b Up to 8 Non-Posted Requests <br> Reserved If Aggregation Supported is Clear. <br> Default value is 00b | RW / <br> RsvdP |
| $5: 4$ | Tx Aggregation Mode PR - If Aggregation Supported is Set then this field selects the level of aggregation for Transmitted Posted Requests for this Stream, encoded as: <br> 00b No aggregation <br> 01b Up to 2 Posted Requests <br> 10b Up to 4 Posted Requests <br> 11b Up to 8 Posted Requests <br> Reserved If Aggregation Supported is Clear. <br> Default value is 00b | RW / <br> RsvdP |
| $7: 6$ | Tx Aggregation Mode CPL - If Aggregation Supported is Set then this field selects the level of aggregation for Transmitted Completions for this Stream, encoded as: <br> 00b No aggregation <br> 01b Up to 2 Completions <br> 10b Up to 4 Completions <br> 11b Up to 8 Completions <br> Reserved If Aggregation Supported is Clear. <br> Default value is 00b | RW / <br> RsvdP |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 8 | PCRC Enable - When Set, Transmitted IDE TLPs associated with this Stream that include $P$ content must include PCRC, and Received TLPs must be checked for PCRC failure. <br> Reserved if PCRC Supported is Clear. <br> Default value is Ob. | $\begin{gathered} \text { RW / } \\ \text { RsvdP } \end{gathered}$ |
| 9 | Selective IDE for Configuration Requests Enable - <br> For Root Ports, if Selective IDE for Configuration Requests Supported is Set, then this bit, when Set, must cause the Port to transmit as IDE TLPs associated with this Selective IDE Stream all Configuration Requests for which the destination RID is greater than or equal to the RID Base and less than or equal to the RID Limit in the Selective IDE RID Association Register Block. <br> For Ports other than Root Ports, this bit is Reserved. <br> If Selective IDE for Configuration Requests Supported is Clear, this bit is Reserved. <br> Default value is Ob. | RW <br> RsvdP |
| 13:10 | Partial Header Encryption Mode - Selects the mode to be used for partial header encryption of IDE TLPs for this IDE Stream. Must be programmed to the same value in both the Partner Ports. Must be configured while Selective IDE Stream Enable is Clear. When Selective IDE Stream Enable is Set, the setting is sampled, and this field becomes RO with reads returning the sampled value. <br> 0000b No partial header encryption <br> 0001b <br> 0010b <br> 0011b <br> 0100b <br> Others <br> If Partial Header Encryption Supported is Clear, this field is Reserved. | RW / RO / <br> RsvdP |
| 18:14 | Selected Algorithm - Selects the algorithm to be used for securing IDE TLPs for this IDE Stream. Must be programmed to the same value in both Partner Ports. Must be configured while Selective IDE Stream Enable is Clear. When Selective IDE Stream Enable is Set, the setting is sampled, and this field becomes RO with reads returning the sampled value. <br> 0 0000b AES-GCM 256 key size, 96b MAC <br> Others Reserved | RW / RO |
| 21:19 | TC - System firmware/software must program this field to indicate the TC associated with this Selective IDE Register block. <br> Default value is 000b | RW |
| 22 | Default Stream - When Set, TLPs using the Traffic Class indicated in the TC field are associated with this Stream, unless the TLP matches some other Selective IDE Stream for the indicated TC. A Default Stream must have the hierarchy domain's Root Port as its Partner Port; otherwise, the result is undefined <br> It is not permitted to configure more than one Default Stream to be associated with the same TC. If this is done, hardware must select one of the Streams to be associated with the TC - the selection is implementation specific. <br> Applicable for Endpoint Upstream Ports only. Reserved for other Port types. <br> Default value is Ob. | RW <br> RsvdP |
| 23 | TEE-Limited Stream - When Set, requires that, for Requests, only those that have the T bit Set are permitted to be associated with this Stream. | RW / RO / <br> RsvdP |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | Must be configured while Selective IDE Stream Enable is Clear, during which time this bit is RW. When Selective IDE Stream Enable is Set set to 1b, the setting is sampled, and this field bit becomes RO with reads returning the sampled value, during the time when Selective IDE Stream Enable remains Set. <br> Reserved if TEE-Limited Stream Supported is Clear. <br> Default value is Ob. |  |
| $31: 24$ | Stream ID - Indicates the Stream ID associated with this Selective IDE Stream. Software must program the same Stream ID into both Ports associated with a given Selective IDE Stream. Default value is 00h. | RW |

# 7.9.26.5.3 Selective IDE Stream Status Register 

![img-368.jpeg](img-368.jpeg)

Figure 7-384 Selective IDE Stream Status Register

Table 7-336 Selective IDE Stream Status Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $3: 0$ | Selective IDE Stream State - When Selective IDE Stream Enable is Set, this field indicates the state of the Port. Encodings: | RO |
|  | 0000b <br> 0010b <br> Others $\quad$ Reserved - Software must handle reserved values as indicating unknown state When Selective IDE Stream Enable is Clear, the value of this field must be 0000b. |  |
| 31 | Received IDE Fail Message - When Set, indicates that one or more IDE Fail Message(s) have been Received for this Stream. | RW1C |

### 7.9.26.5.4 Selective IDE RID Association Register Block

A Selective IDE RID Association register must consist of one IDE RID Association Register 1 followed by one IDE RID Association Register 2.

# 7.9.26.5.4.1 IDE RID Association Register 1 

![img-369.jpeg](img-369.jpeg)

Figure 7-385 IDE RID Association Register 1 (Offset +00h)

Table 7-337 IDE RID Association Register 1 (Offset +00h)
Bit Location Register Description Attributes
23:8 RID Limit - Indicates the highest value RID in the range associated with this Stream ID at the IDE Partner Port.
The Segment Number associated with this field is contained in Segment Base in the IDE RID Association Register 2.

### 7.9.26.5.4.2 IDE RID Association Register 2

![img-370.jpeg](img-370.jpeg)

Figure 7-386 IDE RID Association Register 2 (Offset +04h)

Table 7-338 IDE RID Association Register 2 (Offset +04h)

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 0 | Valid (V) - When Set, indicates the Segment Base, RID Base and RID Limit fields have been programmed. <br> Default is 0b | RW |
| 23:8 | RID Base - Indicates the lowest value RID in the range associated with this Stream ID at the IDE Partner <br> Port. <br> The Segment Number associated with this field is contained in Segment Base. | RW |
| 31:24 | Segment Base - In Flit Mode, Indicates the Segment value associated with this Stream ID at the IDE <br> Partner Port. <br> Reserved if Flit Mode is not supported. <br> If this Selective IDE Stream is within an FM subtree whose Segment Captured bits are Clear, software must <br> set this field to 00h, regardless of the Segment Number value associated with the subtree's RP. <br> Default value is 00h. | RW / <br> RsvdP |

# 7.9.26.5.5 Selective IDE Address Association Register Block 

A Selective IDE Address Association register must consist of one IDE Address Association Register 1, followed by one IDE Address Association Register 2, followed by one IDE Address Association Register 3.

### 7.9.26.5.5.1 IDE Address Association Register 1

![img-371.jpeg](img-371.jpeg)

Figure 7-387 IDE Address Association Register 1 (Offset +00h)

Table 7-339 IDE Address Association Register 1 (Offset +00h)

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| $31: 20$ | Memory Limit Lower - Corresponds to Address bits [31:20]. Address bits [19:0] are implicitly F_FFFFh. | RW |
| $19: 8$ | Memory Base Lower - Corresponds to Address bits [31:20]. Address[19:0] bits are implicitly 0_0000h. | RW |
| 0 | V (Valid) - When Set, indicates this IDE Stream Association Block is valid, that the address range defined <br> by Memory Base and Memory Limit corresponding to a range of memory addresses assigned to the IDE <br> Partner Port, and that all Transmitted Address Routed TLPs within this address range must be <br> associated with this IDE Stream, subject to rules stated in $\S$ Section 6.33.4 . <br> Hardware behavior is undefined if overlapping address ranges are assigned for different IDE Streams. <br> Default is 0 b | RW |

### 7.9.26.5.5.2 IDE Address Association Register 2

![img-372.jpeg](img-372.jpeg)

Figure 7-388 IDE Address Association Register 2 (Offset +04h)

Table 7-340 IDE Address Association Register 2 (Offset +04h)

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| $31: 0$ | Memory Limit Upper - Corresponds to Address bits [63:32] | RW |

# 7.9.26.5.5.3 IDE Address Association Register 3 

![img-373.jpeg](img-373.jpeg)

Figure 7-389 IDE Address Association Register 3 (Offset +04h)

Table 7-341 IDE Address Association Register 3 (Offset +04h)

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| $31: 0$ | Memory Base Upper - Corresponds to Address bits [63:32] | RW |

### 7.9.27 Null Capability

The Null Capability is a capability structure in PCI-compatible Configuration Space (first 256 bytes) as shown in § Figure $7-390$.

The Null Capability contains no registers. This capability is present in the linked list (Next Capability Pointer), but should otherwise be ignored by software. The layout of the information is shown in § Figure 7-390.

A single PCI Express Function is permitted to contain multiple Null Capability structures.
![img-374.jpeg](img-374.jpeg)

Figure 7-390 Null Capability

Table 7-342 Null Capability

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| $7: 0$ | Capability ID - Indicates the PCI Express Capability structure. This field must return a Capability ID of <br> 00h indicating that this is a Null Capability structure. | RO |
| $15: 8$ | Next Capability Pointer - This field contains the offset to the next PCI Capability structure or 00h if no <br> other items exist in the linked list of Capabilities. | RO |

# 7.9.28 Null Extended Capability 

The Null Extended Capability is an optional Extended Capability that is permitted to be implemented by any PCI Express Function or RCRB. This capability contains no registers. This capability is present in the linked list (Next Capability Offset) but should otherwise be ignored by software.

A single PCI Express Function or RCRB is permitted to contain multiple Null Extended Capability structures.
§ Figure 7-391 details allocation of register fields in the Null Extended Capability; § Table 7-343 provides the respective bit definitions. The Extended Capability ID for the Null Extended Capability is 0000h.
![img-375.jpeg](img-375.jpeg)

Figure 7-391 Null Extended Capability

Table 7-343 Null Extended Capability

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 15:0 | PCI Express Extended Capability ID - This field is a PCI-SIG defined ID number that indicates the nature <br> and format of the Extended Capability. <br> Extended Capability ID for the Null Extended Capability is 0000h. | RO |
| 19:16 | Capability Version - This field is a PCI-SIG defined version number that indicates the version of the <br> Capability structure present. <br> This field is permitted to contain any value. | RO |
| 31:20 | Next Capability Offset - This field contains the offset to the next PCI Express Capability structure or 000h <br> if no other items exist in the linked list of Capabilities. <br> For Extended Capabilities implemented in Configuration Space, this offset is relative to the beginning of <br> PCI-compatible Configuration Space and thus must always be either 000h (for terminating list of <br> Capabilities) or greater than 0FFh. | RO |

### 7.9.29 Streamlined Virtual Channel Extended Capability (SVC)

The Streamlined Virtual Channel (SVC) Extended Capability is an optional Extended Capability required for Ports that support capabilities associated with this structure, including UIO. It is permitted, but not required, for Functions in a Port to implement the SVC Extended Capability as well as the MFVC Extended Capability and/or VC Capabilities. See § Section 6.3.5 .

UIO requires the use of the SVC capability and is not supported by the VC or MFVC capabilities. UIO is supported only in Flit Mode, but in Non-Flit Mode the SVC capability can be used by non-UIO traffic.

For an Upstream Port, the SVC Extended Capability structure is permitted to be implemented only in Function 0, and that instance applies to all Functions associated with that Port. The SVC Extended Capability structure is permitted to be implemented in any Downstream Port, or in an RCRB. If the SVC Extended Capability structure is implemented in a USP

containing one or more Switch USP Functions, it must be implemented in all associated Switch DSP Functions. A Root Complex is permitted to implement the Extended Capability structure in some Root Ports and not others.

The number of (extended) Virtual Channels is indicated by the SVC Extended VC Count field in the SVC Port VC Capability Register 1. Software must interpret this field to determine the availability of extended SVC Resource registers.
![img-376.jpeg](img-376.jpeg)

Figure 7-392 Streamlined Virtual Channel Extended Capability Structure 5

# 7.9.29.1 Streamlined Virtual Channel Extended Capability Header (Offset 00h) 

§ Figure 7-393 details allocation of register fields in the Streamlined Virtual Channel Extended Capability Header; § Table $7-344$ provides the respective bit definitions.
![img-377.jpeg](img-377.jpeg)

Figure 7-393 Streamlined Virtual Channel Extended Capability Header 6

Table 7-344 Streamlined Virtual Channel Extended Capability Header 5

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 15:0 | PCI Express Extended Capability ID - This field is a PCI-SIG defined ID number that indicates the nature and format of the Extended Capability. <br> Extended Capability ID for the Streamlined Virtual Channel Extended Capability is 0035h. | RO |
| 19:16 | Capability Version - This field is a PCI-SIG defined version number that indicates the version of the Capability structure present. <br> Must be 1 h for this version of the specification. | RO |
| 31:20 | Next Capability Offset - This field contains the offset to the next PCI Express Capability structure or 000h if no other items exist in the linked list of Capabilities. | RO |

| Bit Location | Register Description | Attributes |
| :-- | :-- | :-- |
|  | For Extended Capabilities implemented in Configuration Space, this offset is relative to the beginning of <br> PCI-compatible Configuration Space and thus must always be either 000h (for terminating list of <br> Capabilities) or greater than 0FFh. |  |

# 7.9.29.2 SVC Port Capability Register 1 (Offset 04h) 

The SVC Port Capability Register 1 describes the configuration of the Virtual Channels associated with a PCI Express Port.
§ Figure 7-394 details allocation of register fields in the SVC Port Capability Register 1; § Table 7-345 provides the respective bit definitions.
![img-378.jpeg](img-378.jpeg)

Figure 7-394 SVC Port Capability Register 1

Table 7-345 SVC Port Capability Register 1

| Bit Location | Register Description | Attributes |
| :--: | :-- | :-- |
| 2:0 | SVC Extended VC Count - Indicates the number of Virtual Channels supported in addition to VCO. | HwInit |
|  | This value indicates the number of SVC Resource Capability, Control, and Status registers present in this <br> structure in addition to those for VCO. <br> The minimum value of this field is 0 , for devices that only support the default VC. |  |

### 7.9.29.3 SVC Port Capability Register 2 (Offset 08h)

This register is RsvdP.

### 7.9.29.4 SVC Port Control Register (Offset 0Ch)

§ Table 7-346 details allocation of register fields in the SVC Port Control Register; § Table 7-346 provides the respective bit definitions.

![img-379.jpeg](img-379.jpeg)

Figure 7-395 SVC Port Control Register

Table 7-346 SVC Port Control Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :--: |
| 0 | VC Enablement Completed - Setting this bit indicates that software has completed enabling all VCs that <br> are to be used by the Port. <br> Setting this bit is optional. If this bit remains Clear, the Port and all enabled VCs must operate correctly. <br> Default value of this bit is Ob. | RW |

# 7.9.29.5 SVC Port Status Register (Offset 10h) 

\$ Table 7-347 details allocation of register fields in the SVC Port Status Register; \$ Table 7-347 provides the respective bit definitions.
![img-380.jpeg](img-380.jpeg)

Figure 7-396 SVC Port Status Register

Table 7-347 SVC Port Status Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :-- |
| 0 | Use VC/MFVC - This bit enables or disables multiple specific VCs in SVC, VC, and MFVC capabilities as <br> required for \$ Section 6.3.5. <br> When this bit is Set, the VC Enable bit for VCD in each VC/MFVC capability (VC Resource Control <br> Register or MFVC VC Resource Control Register) must be Set, and the SVC VC Enable bit for each VC in <br> its SVC Resource Control Register must be Clear. <br> When this bit is Cleared, the VC Enable bit for each VC resource in each VC/MFVC capability (VC <br> Resource Control Register or MFVC VC Resource Control Register) must immediately be Cleared, and <br> the SVC VC Enable bit for VCD in its SVC Resource Control Register must immediately be Set. <br> If this Port implements any VC or MFVC capabilities, this bit must have a default value of 1b, and if <br> Cleared, it must remain Clear until the next Conventional Reset. <br> If this Port implements no VC or MFVC capabilities, this bit must be Ob. |  |

# 7.9.29.6 SVC Resource Capability Register 

§ Figure 7-397 details allocation of register fields in the SVC Resource Capability Register; § Table 7-348 provides the respective bit definitions.
![img-381.jpeg](img-381.jpeg)

Figure 7-397 SVC Resource Capability Register

Table 7-348 SVC Resource Capability Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 11:8 | SVC VC Protocols Supported - Indicates UIO and non-UIO Transaction support for this VC, encoded as: | HwInit/RsvdP |
|  | 0000b | Supports same TLP Types and protocols as VCO |
|  | 0001b | Supports same TLP Types and protocols as VCO, except for those that are restricted by this document to using only VCO |
|  | 0010b | It is permitted to enable UIO on this VC resource; it is not permitted to use non-UIO TLP Types on this VC resource. |
|  | 0011b | It is permitted to enable UIO on this VC resource, or to use as a 0001b VC resource, but not both at the same time. |
|  | 0100b to 1110b | Reserved |
|  | 1111b | Vendor-defined use (outside the scope of this specification) |
|  | For VCO, must be 0000b. |  |
|  | For VC3, if UIO is supported, must be 0010b or 0011b. |  |
|  | For VC4, if UIO and VC4 are supported, must be 0010b or 0011b. |  |
| 14:12 | SVC VC ID - This field indicates the VC ID to the VC resource. For the first of SVC Resource Capability Register, this field must be 000b. For other SVC Resource Capability Registers, this field may contain any non-zero value. This field value must be unique across all SVC Resource Capability Registers. | HwInit/RsvdP |

### 7.9.29.7 SVC Resource Control Register

§ Figure 7-398 details allocation of register fields in the SVC Resource Control Register; § Table 7-349 provides the respective bit definitions.

![img-382.jpeg](img-382.jpeg)

Figure 7-398 SVC Resource Control Register

Table 7-349 SVC Resource Control Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $7: 0$ | SVC TC/VC Map - This field indicates the TCs that are mapped to the VC resource. This field is valid for all Functions. <br> Bit locations within this field correspond to TC values. <br> In order to remove one or more TCs from the TC/VC Map of an enabled VC, software must ensure that no new or outstanding Requests with the TC labels are targeted at the given Link. <br> Bit 0 of this field must be read-only. It must be Set for the default VCO and Clear for all other enabled VCs. Default value of this field must be consistent with $\S$ Table 2-46. | RW / RO |
| $11: 8$ | SVC VC Protocol Selected - Determines the TLP Types and Protocols to be used with this VC, encoded as: <br> 0000b <br> 0001b <br> 0010b <br> 0011b to 1110b <br> 1111b <br> For VCO, must be hardwired to 0000b. Default value is implementation specific. | RW / RO / RsvdP |
| 29:27 | SVC Shared Flow Control Usage Limit - This field controls what percentage of the available Shared Flow Control a given FC/VC is permitted to consume. <br> This limit is applied independently for each Flow Control credit type. For example, if this field contains 101b and SVC Shared Flow Control Usage Limit Enable is Set, a Posted TLP may not pass the Tx Gate if doing so would cause that VC to consume more than $62.5 \%$ of the available Shared Posted Header credits or if doing so would cause that VC to consume more than $62.5 \%$ of the available Shared Data credits. <br> If SVC Shared Flow Control Usage Limit Enable is Clear, this field must be ignored, and this VC is permitted to consume all of the shared credits, unless the Transmitter has implementation-specific policy mechanisms to constrain shared credit use. <br> When SVC Shared Flow Control Usage Limit Enable is Set, and this field contains 000b, this VC is not permitted to consume any shared credits. <br> Behavior is undefined when all VCs have SVC Shared Flow Control Usage Limit Enable Set and the sum of the SVC Shared Flow Control Limit values for all VCs is less than 100\%. <br> Encodings are: <br> 000b $0 \%$ <br> 001b $12.5 \%$ | RW / RO / RsvdP |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
|  | 010b | $25 \%$ |
|  | 011b | $37.5 \%$ |
|  | 100b | $50 \%$ |
|  | 101b | $62.5 \%$ |
|  | 110b | $75 \%$ |
|  | 111b | $87.5 \%$ |
|  | Behavior is undefined if this field changes value while SVC VC Enable and SVC Shared Flow Control Usage Limit Enable are both Set. <br> When SVC Extended VC Count is 0 , this field is permitted to be hardwired to any value. <br> When this field is RW, the default value is implementation specific. |  |
| 30 | SVC Shared Flow Control Usage Limit Enable - When Set, this bit enables use of control of Shared Flow Control consumption at the transmitter for this Virtual Channel. <br> Behavior is undefined of the value of this bit changes while SVC VC Enable is Set. <br> This bit is RsvdP when Flit Mode Supported is Clear. <br> When SVC Extended VC Count is 0 , this bit is permitted to be hardwired to 0 b . When this bit is RW, the default value is implementation specific. | $\begin{aligned} & \text { RW / RO / } \\ & \text { RsvdP } \end{aligned}$ |
| 31 | SVC VC Enable - This bit, when Set, enables this Virtual Channel. The Virtual Channel is disabled when this bit is cleared. <br> Software must use the SVC VC Negotiation Pending bit to check whether the VC negotiation is complete. <br> For VCO, the attribute is RO, and this bit must always have the opposite value from the Use VC/MFVC bit in the SVC Port Status Register. See $\S$ Section 6.3.5 . <br> For other VCs, the default value of this bit is 0 b and the attribute is RW. <br> To enable a Virtual Channel in a Port using SVC mechanisms, the SVC VC Enable bit for that Virtual Channel must be Set. The corresponding Virtual Channel in the Link partner Port must be enabled as well, and that Virtual Channel may be in an SVC, VC, or MFVC capability. To disable a Virtual Channel, the Virtual Channel must be disabled in both components on the Link. Software must ensure that no traffic is using a Virtual Channel at the time it is disabled. Software must fully disable a Virtual Channel in both components on a Link before re-enabling the Virtual Channel. | RW / RO |

# 7.9.29.8 SVC Resource Status Register 

§ Table 7-350 details allocation of register fields in the VC Resource Status Register; § Table 7-350 provides the respective bit definitions.
![img-383.jpeg](img-383.jpeg)

Figure 7-399 SVC Resource Status Register

Table 7-350 SVC Resource Status Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 1 | SVC VC Negotiation Pending - This bit indicates whether the Virtual Channel negotiation (initialization or disabling) is in pending state. This bit is valid for all Functions. <br> The value of this bit is defined only when the Link is in the DL_Active state and the corresponding SVC VC Enable bit is Set. <br> This bit is Set by hardware to indicate that the VC resource has not completed the process of negotiation. This bit is Cleared by hardware after the VC negotiation is complete (on exit from the FC_INIT2 state). For VC0, this bit is permitted to be hardwired to 0b. <br> Before using a Virtual Channel, software must check whether the SVC VC Negotiation Pending bits for that Virtual Channel are Clear in both components on the Link. | RO |

# 7.9.30 MMIO Register Block Locator Extended Capability (MRBL) 

The MMIO Register Block Locator Extended Capability (MRBL) is an optional Extended Capability for discovering register blocks in Memory Space that can be used to exchange various types of data structures between system software and a Function (See § Section 6.35 § Section 6.35 ).

It is permitted to implement the MRBL Extended Capability in any type of Function. A single PCI Express Function is permitted to contain at most one instance of this capability.

The number of register blocks included the MRBL structure is described in the MRBL Capabilities Register (§ Section 7.9.30.2 § Section 7.9.30.2). A Function that implements the MRBL Extended Capability shall support at least one MRBL Locator Register (§ Section 7.9.30.3).

Each register block is described by a MRBL Locator Register (§ Section 7.9.30.3 ) to specify the location and type of the registers within Memory Space. Each register block must be contained within the address range covered by the associated BAR. § Figure 7-400 illustrates the MRBL Extended Capability structure.
![img-384.jpeg](img-384.jpeg)

Figure 7-400 MRBL Extended Capability

# 7.9.30.1 MRBL Extended Capability Header (Offset 00h) 

\$ Figure 7-401 details allocation of register fields in the MRBL Extended Capability Header; \$ Table 7-351 provides the respective bit definitions. Refer to $\S$ Section 7.6.3 for a description of the PCI Express Extended Capability Header. The Extended Capability ID for the MRBL Extended Capability is 0036h.
![img-385.jpeg](img-385.jpeg)

Figure 7-401 MRBL Extended Capability Header

Table 7-351 MRBL Extended Capability Header

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| $15: 0$ | PCI Express Extended Capability ID - This field is a PCI-SIG defined ID number that indicates the nature and format of the Extended Capability. <br> Extended Capability ID for the MMIO Register Block Locator Extended Capability is 0036h. | RO |
| $19: 16$ | Capability Version - This field is a PCI-SIG defined version number that indicates the version of the Capability structure present. <br> Must be 1 h for this version of the specification. | RO |
| $31: 20$ | Next Capability Offset - This field contains the offset to the next PCI Express Capability structure or 000h if no other items exist in the linked list of Capabilities. <br> For Extended Capabilities implemented in Configuration Space, this offset is relative to the beginning of PCI-compatible Configuration Space and thus must always be either 000 h (for terminating list of Capabilities) or greater than 0FFh. | RO |

### 7.9.30.2 MRBL Capabilities Register (Offset 04h)

\$ Figure 7-402 details allocation of register fields in the MRBL Capabilities Register; \$ Table 7-352 provides the respective bit definitions.
![img-386.jpeg](img-386.jpeg)

Figure 7-402 MRBL Capabilities Register

Table 7-352 MRBL Capabilities Register

| Bit Location | Register Description | Attributes |
| :--: | :-- | :-- |
| 11:0 | MRBL Structure Length - This field indicates the overall size of the MRBL Extended Capability in bytes: <br> $08 \mathrm{~h}+(\mathrm{n} * 08 \mathrm{~h})$ where n is the number of MRBL Locator Registers implemented. | HWInit |

# 7.9.30.3 MRBL Locator Register (Offset Varies) 

§ Figure 7-403 details allocation of register fields in the MRBL Locator Register; § Table 7-353 provides the respective bit definitions.
![img-387.jpeg](img-387.jpeg)

Figure 7-403 MRBL Locator Register

Table 7-353 MRBL Locator Register

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 2:0 | Register BIR - Indicates which one of a Function's Base Address Registers, or entry in the Enhanced Allocation capability with a matching BAR Equivalent Indicator (BEI), is used for this register block. | HWInit |
|  | Defined encodings are: |  |
|  | 0 | Base Address Register 10h |
|  | 1 | Base Address Register 14h |
|  | 2 | Base Address Register 18h |
|  | 3 | Base Address Register 1Ch |
|  | 4 | Base Address Register 20h |
|  | 5 | Base Address Register 24h |
|  | 6 | Reserved |
|  | 7 | Reserved |
|  | For a 64-bit Base Address Register, the Register BIR indicates the lower DWORD. For Functions with Type 1 Configuration Space headers, BIR values 2 through 5 are Reserved. |  |
| 15:8 | Register Block ID - Identifies the type of registers contained in this register block. | HWInit |
|  | Defined encodings are: |  |
|  | 00h | Empty/invalid register block |
|  | 01h | MMIO Capabilities Register Block (MCAP) (§ Section 6.35.1 ) |
|  | 02h-FEh | Reserved |
|  | FFh | MMIO Designated Vendor-Specific Register Block (MDVS) (§ Section 6.35.2 ) |
| 31:16 | Register Block Offset Low - Contains bits [31:16] of the register block address offset within the BAR/BEI indicated by Register BIR. Offset bits [15:0] are 0000h. | HWInit |
|  | The value in this field must be ignored if Register Block ID is 00h. |  |

| Bit Location | Register Description | Attributes |
| :--: | :--: | :--: |
| 63:32 | Register Block Offset High - Contains bits [63:32] of the register block address offset within the BAR/BEI indicated by Register BIR. <br> The value in this field must be ignored if Register Block ID is 00h. | HWInit |

6.3-1.0-PUB - PCI Express ${ }^{\circledR}$ Base Specification Revision 6.3

