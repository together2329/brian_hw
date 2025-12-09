# 5. Power Management 

This chapter describes power management (PM) capabilities and protocols.

### 5.1 Overview

Power Management states are as follows:

- D states are associated with a particular Function
- D0 is the operational state and consumes the most power
- D1 and D2 are intermediate power saving states
- D3 ${ }_{\text {Hot }}$ is a very low power state
- D3 Cold is the power off state
- L states are associated with a particular Link
- L0 is the operational state
- L0p is a reduced power sub-state of L0 (see § Section 4.2.6.7)
- L0s, L1, L1.0, L1.1, and L1.2 are various lower power states

Other specifications define related power states (e.g., $S$ states). This specification does not describe relationships between those states and D/L states.

PM provides the following services:

- A mechanism to identify power management capabilities of a given Function
- The ability to transition a Function into a certain power management state
- Notification of the current power management state of a Function
- The option to wakeup the system on a specific event

PM is compatible with the PCI Bus Power Management Interface Specification and the Advanced Configuration and Power Interface Specification. This chapter also defines PCI Express Native Power Management extensions.

PM defines Link power management states that a PCI Express physical Link is permitted to enter in response to either software driven D-state transitions or active state Link power management activities. PCI Express Link states are not visible directly to legacy bus driver software, but are derived from the power management state of the components residing on those Links. Defined Link states are L0, L0s, L1, L2, and L3. The power savings increase as the Link state transitions from L0 through L3.

Components may wakeup the system using a wakeup mechanism followed by a power management event (PME) Message. PCI Express systems may provide the optional auxiliary power supply (Vaux) needed for wakeup operation from states where the main power supplies are off.

The specific definition and requirements associated with Vaux are form-factor specific, and throughout this document the terms "auxiliary power" and "Vaux" should be understood in reference to the specific form factor in use.

Unlike earlier mechanisms, the PCI Express-PM PME mechanism separates the following two PME tasks:

- Reactivation (wakeup) of the associated resources (i.e., re-establishing reference clocks and main power rails to the PCI Express components)
- Sending a PME Message to the Root Complex to provide the source of the wakeup event

Active State Power Management (ASPM) is an autonomous hardware-based, active state mechanism that enables power savings even when the connected components are in the DO state. After a period of idle Link time, an ASPM Physical-Layer protocol places the idle Link into a lower power state. Once in the lower-power state, transitions to the fully operative L0 state are triggered by traffic appearing on either side of the Link. ASPM may be disabled by software. Refer to § Section 5.4.1 for more information on ASPM.

# 5.2 Link State Power Management 

PCI Express defines Link power management states, replacing the bus power management states that were defined by the PCI Bus Power Management Interface Specification. Link states are not visible to PCI-PM legacy compatible software, and are either derived from the power management D-states of the corresponding components connected to that Link or by ASPM protocols (see § Section 5.4.1).

Note that the PCI Express Physical Layer may define additional intermediate states. Refer to § Chapter 4. for more detail on each state and how the Physical Layer handles transitions between states.

PCI Express-PM defines the following Link power management states:

- L0 (including the LOp sub-state) - Active state.

L0 support is required for both ASPM and PCI-PM compatible power management.
All PCI Express transactions and other operations are enabled.

- LOs - A low resume latency, energy saving "standby" state.

LOs support is optional for ASPM unless the applicable form factor specification for the Link explicitly requires LOs support.

All main power supplies, component reference clocks, and components' internal PLLs must be active at all times during LOs. TLP and DLLP transmission is disabled for a Port whose Link is in Tx_LOs.

The Physical Layer provides mechanisms for quick transitions from this state to the L0 state. When common (distributed) reference clocks are used on both sides of a Link, the transition time from LOs to L0 is desired to be less than 100 Symbol Times.

It is possible for the Transmit side of one component on a Link to be in LOs while the Transmit side of the other component on the Link is in L0.

- L1 - Higher latency, lower power "standby" state.

L1 support is required for PCI-PM compatible power management. L1 is optional for ASPM unless specifically required by a particular form factor.

When L1 PM Substates is enabled by setting one or more of the enable bits in the L1 PM Substates Control 1 Register this state is referred to as the L1.0 substate.

All main power supplies must remain active during L1. As long as they adhere to the advertised L1 exit latencies, implementations are explicitly permitted to reduce power by applying techniques such as, but not limited to, periodic rather than continuous checking for Electrical Idle exit, checking for Electrical Idle exit on only one Lane, and powering off of unneeded circuits. All platform-provided component reference clocks must remain active during L1, except as permitted by Clock Power Management (using CLKREQ\#) and/or L1 PM

Substates when enabled. A component's internal PLLs may be shut off during L1, enabling greater power savings at a cost of increased exit latency. ${ }^{99}$

The L1 state is entered whenever all Functions of a Downstream component on a given Link are programmed to a D-state other than D0. The L1 state also is entered if the Downstream component requests L1 entry (ASPM) and receives positive acknowledgement for the request.

Exit from L1 is initiated by an Upstream-initiated transaction targeting a Downstream component, or by the Downstream component's initiation of a transaction heading Upstream. Transition from L1 to L0 is desired to be a few microseconds.

TLP and DLLP transmission is disabled for a Link in L1.

- L1 PM Substates - optional L1.1 and L1.2 substates of the L1 low power Link state for PCI-PM and ASPM.

In the L1.1 substate, the Link common mode voltages are maintained. The L1.1 substate is entered when the Link is in the L1.0 substate and conditions for entry into L1.1 substate are met. See § Section 5.5.1 for details.

In the L1.2 substate, the Link common mode voltages are not required to be maintained. The L1.2 substate is entered when the Link is in the L1.0 substate and conditions for entry into L1.2 substate are met. See § Section 5.5.1 . for details.

Exit from all L1 PM Substates is initiated when the CLKREQ\# signal is asserted (see § Section 5.5.2.1 and § Section 5.5.3.3).

- L2/L3 Ready - Staging point for L2 or L3.

L2/L3 Ready transition protocol support is required.
L2/L3 Ready is a pseudo-state (corresponding to the LTSSM L2 state) that a given Link enters when preparing for the removal of power and clocks from the Downstream component or from both attached components. This process is initiated after PM software transitions a device into a D3 state, and subsequently calls power management software to initiate the removal of power and clocks. After the Link enters the L2/L3 Ready state the component(s) are ready for power removal. After main power has been removed, the Link will either transition to L2 if Vaux is provided and used, or it will transition to L3 if no Vaux is provided or used. Note that these are PM pseudo-states for the Link; under these conditions, the LTSSM will in, general, operate only on main power, and so will power off with main power removal.

The L2/L3 Ready state entry transition process must begin as soon as possible following the acknowledgment of a PME_Turn_Off Message, (i.e., the injection of a PME_TO_Ack TLP). The Downstream component initiates L2/L3 Ready entry by sending a PM_Enter_L23 DLLP. Refer to § Section 5.7 for further detail on power management system Messages.

TLP and DLLP transmission is disabled for a Link in L2/L3 Ready.
Note: Exit from L2/L3 Ready back to L0 will be through intermediate LTSSM states. Refer to § Chapter 4. for detailed information.

- L2 - Auxiliary-powered Link, deep-energy-saving state.

L2 support is optional, and dependent upon the presence of auxiliary power.
A component may only consume auxiliary power if enabled to do so as described in § Section 5.6 .
In L2, the component's main power supply inputs and reference clock inputs are shut off.
When in L2, any Link reactivation wakeup logic (Beacon or WAKE\#), PME context, and any other "keep alive" logic is powered by auxiliary power.

TLP and DLLP transmission is disabled for a Link in L2.

- L3-Link Off state.

When no power is present, the component is in the L3 state.

- LDn - A transitional Link Down pseudo-state prior to L0.

This pseudo-state is associated with the LTSSM states Detect, Polling, and Configuration, and, when applicable, Disabled, Loopback, and Hot Reset.

Refer to § Section 4.2 for further detail relating to entering and exiting each of the L-states between L0 and L2/L3 Ready (L2.Idle from the § Chapter 4. perspective). The L2 state is an abstraction for PM purposes distinguished by the presence of auxiliary power, and should not be construed to imply a requirement that the LTSSM remain active.

The electrical section specifies the electrical properties of drivers and Receivers when no power is applied. This is the L3 state but the electrical section does not refer to L3.
§ Figure 5-1 shows an overview of L-state transitions that may occur.
![img-0.jpeg](03_Knowledge/Tech/PCIe/05_Power_Management/img-0.jpeg)

Figure 5-1 Link Power Management State Flow Diagram

The L1 and L2/L3 Ready entry negotiations happen while in the L0 state. L1 and L2/L3 Ready are entered only after the negotiation completes. Link Power Management remains in L0 until the negotiation process is completed, unless LDn occurs. Note that these states and state transitions do not correspond directly to the actions of the Physical Layer LTSSM. For example in § Figure 5-1, L0 encompasses the LTSSM L0, Recovery, and, during LinkUp, Configuration states. Also, the LTSSM is typically powered by main power (not Vaux), so LTSSM will not be powered in either the L2 or the L3 state.

The following example sequence illustrates the multi-step Link state transition process leading up to entering a system sleep state:

1. System software directs all Functions of a Downstream component to $\mathrm{D} 3_{\text {Hot }}$.
2. The Downstream component then initiates the transition of the Link to L1 as required.
3. System software then causes the Root Complex to broadcast the PME_Turn_Off Message in preparation for removing the main power source.
4. This Message causes the subject Link to transition back to L0 in order to send it and to enable the Downstream component to respond with PME_TO_Ack.
5. After sending the PME_TO_Ack, the Downstream component initiates the L2/L3 Ready transition protocol.

# $\mathrm{L} 0 \rightarrow \mathrm{~L} 1 \rightarrow \mathrm{~L} 0 \rightarrow \mathrm{~L} 2 / \mathrm{L} 3$ Ready 

As the following example illustrates, it is also possible to remove power without first placing all Functions into $\mathrm{D} 3_{\text {Hot }}$ :

1. System software causes the Root Complex to broadcast the PME_Turn_Off Message in preparation for removing the main power source.
2. The Downstream components respond with PME_TO_Ack.
3. After sending the PME_TO_Ack, the Downstream component initiates the L2/L3 Ready transition protocol.

# L0 $\rightarrow$ L2/L3 Ready 

The L1 entry negotiation (whether invoked via PCI-PM or ASPM mechanisms) and the L2/L3 Ready entry negotiation map to a state machine which corresponds to the actions described later in this chapter. This state machine is reset to an idle state. For a Downstream component, the first action taken by the state machine, after leaving the idle state, is to start sending the appropriate entry DLLPs depending on the type of negotiation. If the negotiation is interrupted, for example by a trip through Recovery, the state machine in both components is reset back to the idle state. The Upstream component must always go to the idle state, and wait to receive entry DLLPs. The Downstream component must always go to the idle state and must always proceed to sending entry DLLPs to restart the negotiation.
§ Table 5-1 summarizes each L-state, describing when they are used, and the platform and component behaviors that correspond to each.

A "Yes" entry indicates that support is required (unless otherwise noted). "On" and "Off" entries indicate the required clocking and power delivery. "On/Off" indicates an optional design choice.

Table 5-1 Summary of PCI Express Link Power Management States

|  | L-State <br> Description | Used by S/W <br> Directed PM | Used by <br> ASPM | Platform <br> Reference <br> Clocks | Platform <br> Main <br> Power | Component <br> Internal <br> PLL | Platform <br> Vaux |
| :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: |
| L0 / L0p | Fully active Link | Yes (D0) | Yes (D0) | On | On | On | On/Off |
| L0s | Standby state | No | Yes ${ }^{1}$ (opt., <br> D0) | On | On | On | On/Off |
| L1 | Lower power standby | Yes (D1- <br> D3 $3_{\text {Hot }}$ ) | Yes (opt., D0) | On/Off ${ }^{6}$ | On | On/Off ${ }^{2}$ | On/Off |
| L2/L3 Ready <br> (pseudo-state) | Staging point for power <br> removal | Yes $^{3}$ | No | On/Off ${ }^{6}$ | On | On/Off | On/Off |
| L2 | Low power sleep state <br> (all clocks, main power off) | Yes $^{4}$ | No | Off | Off | Off | On $^{5}$ |
| L3 | Off (zero power) | n/a | n/a | Off | Off | Off | Off |
| LDn <br> (pseudo-state) | Transitional state preceding <br> L0 | Yes | N/A | On | On | On/Off | On/Off |

Notes:

1. L0s exit latency will be greatest in Link configurations with independent reference clock inputs for components connected to opposite ends of a given Link (vs. a common, distributed reference clock).
2. L1 exit latency will be greatest for components that internally shut off their PLLs during this state.
3. L2/L3 Ready entry sequence is initiated at the completion of the PME_Turn_Off/PME_TO_Ack protocol handshake. It is not directly affiliated with either a D-State transition or a transition in accordance with ASPM policies and procedures.
4. Depending upon the platform implementation, the system's sleep state may use the L2 state, transition to fully off (L3), or it may leave Links in the L2/L3 Ready state. L2/L3 Ready state transition protocol is initiated by the Downstream component following reception and TLP acknowledgement of the PME_Turn_Off TLP Message. While platform support for

|  | L-State <br> Description | Used by S/W <br> Directed PM | Used by <br> ASPM | Platform <br> Reference <br> Clocks | Platform <br> Main <br> Power | Component <br> Internal <br> PLL | Platform <br> Vaux |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- |

an L2 sleep state configuration is optional (depending on the availability of Vaux), component protocol support for transitioning the Link to the L2/L3 Ready state is required.
5. L2 is distinguished from the L3 state only by the presence and use of Vaux. After the completion of the L2/L3 Ready state transition protocol and before main power has been removed, the Link has indicated its readiness for main power removal.
6. Low-power mobile or handheld devices may reduce power by clock gating the reference clock(s) via the "clock request" (CLKREQ\#) mechanism. As a result, components targeting these devices should be tolerant of the additional delays required to re-energize the reference clock during the low-power state exit.

# 5.3 PCI-PM Software Compatible Mechanisms 

### 5.3.1 Device Power Management States (D-States) of a Function

While the concept of these power states is universal for all Functions in the system, the meaning, or intended functional behavior when transitioned to a given power management state, is dependent upon the type (or class) of the Function.

The D0 power management state is the normal operation state of the Function. Other states are various levels of reduced power, where the Function is either not operating or supports a limited set of operations. D1 and D2 are intermediate states that are intended to afford the system designer more flexibility in balancing power savings, restore time, and low power feature availability tradeoffs for a given device class. The D1 state could, for example, be supported as a slightly more power consuming state than D2, however one that yields a quicker restore time than could be realized from D2.

The D3 power management state constitutes a special category of power management state in that a Function could be transitioned into D3 either by software or by physically removing its power. In that sense, the two D3 variants have been designated as $\boldsymbol{D} \mathbf{3}_{\boldsymbol{H o t}}$ and $\boldsymbol{D} \mathbf{3}_{\boldsymbol{C o l d}}$ where the subscript refers to the presence or absence of main power respectively. Functions in $\mathrm{D} 3_{\text {Hot }}$ are permitted to be transitioned to the D0 state via software by writing to the Function's PMCSR register. Functions in the $\mathrm{D} 3_{\text {Cold }}$ state are permitted to be transitioned to the $\mathrm{D} 0_{\text {uninitialized }}$ state by reapplying main power and asserting Fundamental Reset.

All Functions must support the D0 and D3 states (both $\mathrm{D} 3_{\text {Hot }}$ and $\mathrm{D} 3_{\text {Cold }}$ ). The D1 and D2 states are optional.

# IMPLEMENTATION NOTE: SWITCH AND ROOT PORT VIRTUAL BRIDGE BEHAVIOR IN NON-DO STATES 5 

When a Type 1 Function associated with a Switch/Root Port (a "virtual bridge") is in a non-D0 power state, it will emulate the behavior of a conventional PCI bridge in its handling of Memory, I/O, and Configuration Requests and Completions. All Memory and I/O requests flowing Downstream are terminated as Unsupported Requests. All Type 1 Configuration Requests are terminated as Unsupported Requests, however Type 0 Configuration Request handling is unaffected by the virtual bridge D state. Completions flowing in either direction across the virtual bridge are unaffected by the virtual bridge D state.

Note that the handling of Messages is not affected by the PM state of the virtual bridge.

### 5.3.1.1 D0 State 6

All Functions must support the D0 state. D0 is divided into two distinct substates, the "un-initialized" substate and the "active" substate. When a component comes out of Conventional Reset all Functions of the component enter the $\boldsymbol{D} \boldsymbol{0}_{\text {uninitialized }}$ state. When a Function completes FLR, it enters the $\mathrm{D} 0_{\text {uninitialized }}$ state. After configuration is complete a Function enters the $\mathrm{D} 0_{\text {active }}$ state, the fully operational state for a PCI Express Function. A Function enters the $\boldsymbol{D} \boldsymbol{0}_{\text {active }}$ state whenever any single or combination of the Function's Memory Space Enable, I/O Space Enable, or Bus Master Enable bits have been Set ${ }^{100}$.

### 5.3.1.2 D1 State 8

D1 support is optional. While in the D1 state, a Function must not initiate any Request TLPs on the Link with the exception of Messages as defined in $\S$ Section 2.2.8. Configuration and Message Requests are the only TLPs accepted by a Function in the D1 state. All other received Requests must be handled as Unsupported Requests, and all received Completions may optionally be handled as Unexpected Completions. If an error caused by a received TLP (e.g., an Unsupported Request) is detected while in D1, and reporting is enabled, the Link must be returned to LO if it is not already in L0 and an error Message must be sent. If an error caused by an event other than a received TLP (e.g., a Completion Timeout) is detected while in D1, an error Message must be sent when the Function is programmed back to the D0 state.

Note that a Function's software driver participates in the process of transitioning the Function from D0 to D1. It contributes to the process by saving any functional state (if necessary), and otherwise preparing the Function for the transition to D1. As part of this quiescence process the Function's software driver must ensure that any mid-transaction TLPs (i.e., Requests with outstanding Completions), are terminated prior to handing control to the system configuration software that would then complete the transition to D1.

### 5.3.1.3 D2 State 9

D2 support is optional. When a Function is not currently being used and probably will not be used for some time, it may be put into D2. This state requires the Function to provide significant power savings while still retaining the ability to fully recover to its previous condition. While in the D2 state, a Function must not initiate any Request TLPs on the Link with the exception of Messages as defined in $\S$ Section 2.2.8. Configuration and Message requests are the only TLPs

accepted by a Function in the D2 state. All other received Requests must be handled as Unsupported Requests, and all received Completions may optionally be handled as Unexpected Completions. If an error caused by a received TLP (e.g., an Unsupported Request) is detected while in D2, and reporting is enabled, the Link must be returned to L0 if it is not already in L0 and an error Message must be sent. If an error caused by an event other than a received TLP (e.g., a Completion Timeout) is detected while in D2, an error Message must be sent when the Function is programmed back to the DO state.

Note that a Function's software driver participates in the process of transitioning the Function from D0 to D2. It contributes to the process by saving any functional state (if necessary), and otherwise preparing the Function for the transition to D2. As part of this quiescence process the Function's software driver must ensure that any mid-transaction TLPs (i.e., Requests with outstanding Completions), are terminated prior to handing control to the system configuration software that would then complete the transition to D2.

System software must restore the Function to the $\mathrm{DO}_{\text {active }}$ state before memory or I/O space can be accessed. Initiated actions such as bus mastering and interrupt request generation can only commence after the Function has been restored to $\mathrm{DO}_{\text {active }}$.

There is a minimum recovery time requirement of $200 \mu \mathrm{~s}$ between when a Function is programmed from D2 to D0 and the next Request issued to the Function. Behavior is undefined for Requests received in this recovery time window (see § Section 7.9.16).

# 5.3.1.4 D3 State 

D3 support is required, (both the $\mathrm{D3}_{\text {Cold }}$ and the $\mathrm{D3}_{\text {Hot }}$ states).
Functional context is required to be maintained by Functions in the $\mathrm{D} 3_{\text {Hot }}$ state if the No_Soft_Reset field in the PMCSR is Set. In this case, System Software is not required to re-initialize the Function after a transition from $\mathrm{D} 3_{\text {Hot }}$ to D0 (the Function will be in the $\mathrm{DO}_{\text {active }}$ state). If the No_Soft_Reset bit is Clear, functional context is not required to be maintained by the Function in the $\mathrm{D} 3_{\text {Hot }}$ state, however it is not guaranteed that functional context will be cleared and software must not depend on such behavior. As a result, in this case System Software is required to fully re-initialize the Function after a transition to D0 as the Function will be in the $\mathrm{DO}_{\text {uninitialized }}$ state.

The Function will be reset if the Link state has transitioned to the L2/L3 Ready state regardless of the value of the No_Soft_Reset bit.

## IMPLEMENTATION NOTE: TRANSITIONING TO L2/L3 READY

As described in § Section 5.2 , transition to the L2/L3 Ready state is initiated by platform power management software in order to begin the process of removing main power and clocks from the device. As a result, it is expected that a device will transition to $\mathrm{D} 3_{\text {Cold }}$ shortly after its Link transitions to L2/L3 Ready, making the No_Soft_Reset bit, which only applies to $\mathrm{D} 3_{\text {Hot }}$, irrelevant. While there is no guarantee of this correlation between L2/L3 Ready and D3 ${ }_{\text {Cold }}$, system software should ensure that the L2/L3 Ready state is entered only when the intent is to remove device main power. Device Functions, including those that are otherwise capable of maintaining functional context while in $\mathrm{D} 3_{\text {Hot }}$ (i.e., set the No_Soft_Reset bit), are required to re-initialize internal state as described in § Section 2.9.1 when exiting L2/L3 Ready due to the required DL_Down status indication.

Unless the Immediate_Readiness_on_Return_to_D0 bit in the PCI-PM Power Management Capabilities register is Set, System Software must allow a minimum recovery time following a $\mathrm{D} 3_{\text {Hot }} \rightarrow \mathrm{D} 0$ transition of at least 10 ms (see $\S$ Section 7.9.16), prior to accessing the Function. This recovery time may, for example, be used by the $\mathrm{D} 3_{\text {Hot }} \rightarrow \mathrm{D} 0$ transitioning

component to bootstrap any of its component interfaces (e.g., from serial ROM) prior to being accessible. Attempts to target the Function during the recovery time (including configuration request packets) will result in undefined behavior.

# 5.3.1.4.1 D3 ${ }_{\text {Hot }}$ State 

Configuration and Message requests are the only TLPs accepted by a Function in the $\mathrm{D} 3_{\text {Hot }}$ state. All other received Requests must be handled as Unsupported Requests, and all received Completions may optionally be handled as Unexpected Completions. If an error caused by a received TLP (e.g., an Unsupported Request) is detected while in D3 ${ }_{\text {Hot }}$, and reporting is enabled, the Link must be returned to L0 if it is not already in L0 and an error Message must be sent. If an error caused by an event other than a received TLP (e.g., a Completion Timeout) is detected while in D3 ${ }_{\text {Hot }}$, an error Message may optionally be sent when the Function is programmed back to the D0 state. Once in $\mathrm{D} 3_{\text {Hot }}$ the Function can later be transitioned into $\mathrm{D} 3_{\text {Cold }}$ (by removing power from its host component).

Note that a Function's software driver participates in the process of transitioning the Function from D0 to D3 ${ }_{\text {Hot }}$. It contributes to the process by saving any functional state that would otherwise be lost with removal of main power, and otherwise preparing the Function for the transition to $\mathrm{D} 3_{\text {Hot }}$. As part of this quiescence process the Function's software driver must ensure that any outstanding transactions (i.e., Requests with outstanding Completions), are terminated prior to handing control to the system configuration software that would then complete the transition to $\mathrm{D} 3_{\text {Hot }}$.

Note that $\mathrm{D} 3_{\text {Hot }}$ is also a useful state for reducing power consumption by idle components in an otherwise running system.

Functions that are in $\mathrm{D} 3_{\text {Hot }}$ are permitted to be transitioned by software (writing to their PMCSR PowerState field) to the DO active state or the DO uninitialized state. Functions that are in $\mathrm{D} 3_{\text {Hot }}$ must respond to Configuration Space accesses as long as power and clock are supplied so that they can be returned to DO by software. Note that the Function is not required to generate an internal hardware reset during or immediately following its transition from $\mathrm{D} 3_{\text {Hot }}$ to D0 (see usage of the No_Soft_Reset bit in the PMCSR).

If not requiring an internal reset, upon completion of the $\mathrm{D} 3_{\text {Hot }}$ to $\mathrm{D} 0_{\text {active }}$ state, no additional operating system intervention is required beyond writing the PowerState field. If the internal reset is required, devices return to DO uninitialized and a full reinitialization is required on the device. The full reinitialization sequence returns the device to DO active.

If the device supports PME events, and PME_En is Set, PME context must be preserved in D3 ${ }_{\text {Hot }}$. PME context must also be preserved in a PowerState command transition back to DO.

## IMPLEMENTATION NOTE: DEVICES NOT PERFORMING AN INTERNAL RESET 5

Bus controllers to non-PCIe buses and resume from $\mathrm{D} 3_{\text {Hot }}$ bus controllers on PCIe buses that serve as interfaces to non-PCIe buses, (e.g., CardBus, USB, and IEEE 1394) are examples of bus controllers that would benefit from not requiring an internal reset upon resume from $\mathrm{D} 3_{\text {Hot }}$. If this internal reset is not required, the bus controller would not need to perform a downstream bus reset upon resume from $\mathrm{D} 3_{\text {Hot }}$ on its secondary (non-PCIe) bus.

# IMPLEMENTATION NOTE: MULTI-FUNCTION DEVICE ISSUES WITH SOFT RESET 

With Multi-Function Devices (MFDs), certain control settings affecting overall device behavior are determined either by the collective settings in all Functions or strictly off the settings in Function 0 . Here are some key examples:

- With non-ARI MFDs, certain controls in the Device Control register and Link Control registers operate off the collective settings of all Functions (see § Section 7.5.3.4 and § Section 7.5.3.7).
- With ARI Devices, certain controls in the Device Control register and Link Control registers operate strictly off the settings in Function 0 (see § Section 7.5.3.4 and § Section 7.5.3.7).
- With all MFDs, certain controls in the Device Control 2 and Link Control 2 registers operate strictly off the settings in Function 0 (see § Section 7.5.3.16 and § Section 7.5.3.19).

Performing a soft reset on any Function (especially Function 0 ) may disrupt the proper operation of other active Functions in the MFD. Since some Operating Systems transition a given Function between $\mathrm{D} 3_{\text {Hot }}$ and DO with the expectation that other Functions will not be impacted, it is strongly recommended that every Function in an MFD be implemented with the No_Soft_Reset bit Set in the Power Management Control/Status register. This way, transitioning a given Function from $\mathrm{D} 3_{\text {Hot }}$ to DO will not disrupt the proper operation of other active Functions. For Functions that support Flit Mode, the No_Soft_Reset bit is required to be Set (see § Table 7-15).

It is also strongly recommended that every Endpoint Function in an MFD implement Function Level Reset (FLR) (i.e., Function Level Reset Capability is Set). FLR can be used to reset an individual Endpoint Function without impacting the settings that might affect other Functions, particularly if those Functions are active. As a result of FLR's quiescing, error recovery, and cleansing for reuse properties, FLR is also recommended for single-Function Endpoint devices.

### 5.3.1.4.2 D3 ${ }_{\text {Cold }}$ State

A Function transitions to the $\mathrm{D} 3_{\text {Cold }}$ state when its main power is removed. A power-on sequence with its associated Cold Reset transitions a Function from the $\mathrm{D} 3_{\text {Cold }}$ state to the $\mathrm{D} 0_{\text {uninititalized }}$ state, and the power-on defaults will be restored to the Function by hardware just as at initial power up. At this point, software must perform a full initialization of the Function in order to re-establish all functional context, completing the restoration of the Function to its $\mathrm{D0}_{\text {active }}$ state.

When PME_En is Set, Functions that support wakeup functionality from $\mathrm{D} 3_{\text {Cold }}$ must maintain their PME context in the PMCSR for inspection by PME service routine software during the course of the resume process. Retention of additional context is implementation specific.

## IMPLEMENTATION NOTE: PME CONTEXT

Examples of PME context include, but are not limited to, a Function's PME_Status bit, the requesting agent's Requester ID, Caller ID if supported by a modem, IP information for IP directed network packets that trigger a resume event, etc.

A Function's PME assertion is acknowledged when system software performs a "write 1 to clear" configuration transaction to the asserting Function's PME_Status bit of its PCI-PM compatible PMCSR.

An auxiliary power source must be used to support PME event detection within a Function, Link reactivation, and to preserve PME context from within D3 ${ }_{\text {Cold. }}$. Note that once the I/O Hierarchy has been brought back to a fully communicating state, as a result of the Link reactivation, the waking agent then propagates a PME Message to the root of the Hierarchy indicating the source of the PME event. Refer to $\S$ Section 5.3.3 for further PME specific detail.

# 5.3.2 PM Software Control of the Link Power Management State 

The power management state of a Link is determined by the D-state of its Downstream component.
§ Table 5-2 depicts the relationships between the power state of a component (with an Upstream Port) and its Upstream Link.

Table 5-2 Relation Between Power Management States of Link and Components

| Downstream Component D-State | Permissible Upstream Component D-State | Permissible Interconnect State |
| :--: | :--: | :--: |
| D0 | D0 | L0, L0s, L1 ${ }^{(1)}, \mathrm{L} 2 / \mathrm{L} 3$ Ready |
| D1 | D0-D1 | L1, L2/L3 Ready |
| D2 | D0-D2 | L1, L2/L3 Ready |
| D3 ${ }_{\text {Hot }}$ | D0- D3 ${ }_{\text {Hot }}$ | L1, L2/L3 Ready |
| D3 Cold | D0- D3 Cold | L2 ${ }^{(2)}, \mathrm{L} 3$ |

Notes:

1. Requirements for ASPM L0s and ASPM L1 support are form factor specific.
2. If Vaux is provided by the platform, the Link sleeps in L2. In the absence of Vaux, the L-state is L3.

The following rules relate to PCI-PM compatible power management:

- Devices in D0, D1, D2, and D3 ${ }_{\text {Hot }}$ must respond to the receipt of a PME_Turn_Off Message by the transmission of a PME_TO_Ack Message.
- In any device D state, following the execution of a PME_Turn_Off/PME_TO_Ack handshake sequence, a Downstream component must request a Link transition to L2/L3 Ready using the PM_Enter_L23 DLLP. Following the L2/L3 Ready entry transition protocol the Downstream component must be ready for loss of main power and reference clock.
- The Upstream Port of a Single-Function Device must initiate a Link state transition to L1 based solely upon its Function being programmed to D1, D2, or D3 ${ }_{\text {Hot }}$. In the case of the Switch, system software bears the responsibility of ensuring that any D-state programming of a Switch's Upstream Port is done in a compliant manner with respect to hierarchy-wide PM policies (i.e., the Upstream Port cannot be programmed to a D-state that is any less active than the most active Downstream Port and Downstream connected component/ Function(s)).
- The Upstream Port of a non-ARI Multi-Function Device must not initiate a Link state transition to L1 (on behalf of PCI-PM) until all of its Functions have been programmed to a non-D0 D-state.

- The Upstream Port of an ARI Device must not initiate a Link state transition to L1 (on behalf of PCI-PM) until at least one of its Functions has been programmed to a non-D0 state, and all of its Functions are either in a non-D0 state or the $\mathrm{D} 0_{\text {uninitialized }}$ state.
- With SR-IOV devices, the Link Power State is controlled solely by the setting in the PFs, regardless of the VFs' D-states. VF Power States do not affect the Link Power State.


# 5.3.2.1 Entry into the L1 State 

§ Figure 5-2 depicts the process by which a Link transitions into the L1 state as a direct result of power management software programming the Downstream connected component into a lower power state, (either D1, D2, or D3 ${ }_{\text {Hot }}$ state). This figure and the subsequent description outline the transition process for a single -Function Downstream component that is being programmed to a non-D0 state.
![img-1.jpeg](03_Knowledge/Tech/PCIe/05_Power_Management/img-1.jpeg)

Figure 5-2 Entry into the L1 Link State

The following text provides additional detail for the Link state transition process shown in § Figure 5-2.
PM Software Request:

1. PM software sends a Configuration Write Request TLP to the Downstream Function's PMCSR to change the Downstream Function's D-state (from D0 to D1 for example).

Downstream Component Link State Transition Initiation Process:
2. The Downstream component schedules the Completion corresponding to the Configuration Write Request to its PMCSR PowerState field and accounts for the completion credits required.
3. The Downstream component must then wait until it accumulates at least the minimum number of credits required to send the largest possible packet for any FC type for all enabled VCs (if it does not already have such credits). All Transaction Layer TLP scheduling is then suspended.
4. The Downstream component then waits until it receives an acknowledgement for the PMCSR Write Completion, and any other TLPs it had previously sent. The component must retransmit a TLP out of its appropriate Retry Buffer if required to do so by the Data Link Layer rules (when operating in Non Flit Mode) or the Flit Ack/Nak rules (when operating in Flit Mode).
5. Once all of the Downstream components' TLPs have been acknowledged, the Downstream component starts to transmit PM_Enter_L1 DLLPs. The Downstream component sends this DLLP repeatedly with no more than eight (when using 8b/10b encoding) or 32 (when using 128b/130b encoding) Symbol times of idle between subsequent transmissions of the PM_Enter_L1 DLLP, in Non-Flit Mode. The transmission of other DLLPs and SKP Ordered Sets is permitted at any time between PM_Enter_L1 transmissions, and do not contribute to this idle time limit.

The Downstream component continues to transmit the PM_Enter_L1 DLLP as described above until it receives a response from the Upstream component ${ }^{101}$ (PM_Request_Ack).

The Downstream component must continue to accept TLPs and DLLPs from the Upstream component, and continue to respond with DLLPs, including FC update DLLPs and Ack/Nak DLLPs, as required. Any TLPs that are blocked from transmission (including responses to TLP(s) received) must be stored for later transmission, and must cause the Downstream component to initiate L1 exit as soon as possible following L1 entry.

Upstream Component Link State Transition Process:
6. Upon receiving the PM_Enter_L1 DLLP, the Upstream component blocks the scheduling of all TLP transmissions.
7. The Upstream component then must wait until it receives an acknowledgement for the last TLP it had previously sent. The Upstream component must retransmit a TLP from its appropriate Retry Buffer if required to do so by the Data Link Layer rules (when operating in Non Flit Mode) or the Flit Ack/Nak rules (when operating in Flit Mode).
8. Once all of the Upstream component's TLPs have been acknowledged, the Upstream component must send PM_Request_Ack DLLPs Downstream, regardless of any outstanding Requests. The Upstream component sends this DLLP repeatedly with no more than eight (when using 8b/10b encoding) or 32 (when using 128b/ 130b encoding) Symbol times of idle between subsequent transmissions of the PM_Request_Ack DLLP, in Non-Flit Mode. The transmission of SKP Ordered Sets is permitted at any time between PM_Request_Ack transmissions, and does not contribute to this idle time limit.

The Upstream component continues to transmit the PM_Request_Ack DLLP as described above until it observes its receive Lanes enter into the Electrical Idle state. Refer to § Chapter 4. for more details on the Physical Layer behavior.

Completing the L1 Link State Transition:
9. Once the Downstream component has captured the PM_Request_Ack DLLP on its Receive Lanes (signaling that the Upstream component acknowledged the transition to L1 request), it then disables DLLP transmission and brings the Upstream directed physical Link into the Electrical Idle state.
10. When the Receive Lanes on the Upstream component enter the Electrical Idle state, the Upstream component stops sending PM_Request_Ack DLLPs, disables DLLP transmission, and brings its Transmit Lanes to Electrical Idle completing the transition of the Link to L1.

When two components' interconnecting Link is in L1 as a result of the Downstream component being programmed to a non-D0 state, both components suspend the operation of their Flow Control Update and, if implemented, UpdateFC FCP Timer (see § Section 2.6.1.2 ) counter mechanisms. Refer to § Chapter 4. for more detail on the Physical Layer behavior.

Refer to § Section 5.2 if the negotiation to L1 is interrupted.
Components on either end of a Link in L1 may optionally disable their internal PLLs in order to conserve more energy. Note, however, that platform supplied main power and reference clocks must continue to be supplied to components on both ends of an L1 Link in the L1.0 substate of L1.

Refer to § Section 5.5 for entry into the L1 PM Substates.
101. If at this point the Downstream component needs to initiate a transfer on the Link, it must first complete the transition to L1. Once in L1 it is then permitted to initiate an exit L1 to handle the transfer.

# 5.3.2.2 Exit from L1 State 

L1 exit can be initiated by the component on either end of a Link.
Upon exit from L1, it is recommended that the Downstream component send flow control update DLLPs for all enabled VCs and FC types starting within $1 \mu \mathrm{~s}$ of L1 exit.

The physical mechanism for transitioning a Link from L1 to L0 is described in detail in § Chapter 4. .
L1 exit must be initiated by a component if that component needs to transmit a TLP on the Link. An Upstream component must initiate L1 exit on a Downstream Port even if it does not have the flow control credits needed to transmit the TLP that it needs to transmit. Following L1 exit, the Upstream component must wait to receive the needed credit from the Downstream component. § Figure 5-3 outlines an example sequence that would trigger an Upstream component to initiate transition of the Link to the L0 state.
![img-2.jpeg](03_Knowledge/Tech/PCIe/05_Power_Management/img-2.jpeg)

Figure 5-3 Exit from L1 Link State Initiated by Upstream Component

Sequence of events:

1. Power management software initiates a configuration cycle targeting a PM configuration register (the PowerState field of the PMCSR in this example) within a Function that resides in the Downstream component (e.g., to bring the Function back to the DO state).
2. The Upstream component detects that a configuration cycle is intended for a Link that is currently in a low power state, and as a result, initiates a transition of that Link into the L0 state.
3. If the Link is in either L1.1 or L1.2 substates of L1, then the Upstream component initiates a transition of the Link into the L1.0 substate of L1.
4. In accordance with the $\S$ Chapter 4 . definition, both directions of the Link enter into Link training, resulting in the transition of the Link to the L0 state. The L1 $\rightarrow$ L0 transition is discussed in detail in $\S$ Chapter 4. .

5. Once both directions of the Link are back to the active L0 state, the Upstream Port sends the configuration Packet Downstream.

# 5.3.2.3 Entry into the L2/L3 Ready State 

Transition to the L2/L3 Ready state follows a process that is similar to the L1 entry process. There are some minor differences between the two that are spelled out below.

- L2/L3 Ready entry transition protocol does not immediately result in an L2 or L3 Link state. The transition to L2/L3 Ready is effectively a handshake to establish the Downstream component's readiness for power removal. L2 or L3 is ultimately achieved when the platform removes the components' power and reference clock.
- The time for L2/L3 Ready entry transition is indicated by the completion of the PME_Turn_Off/PME_TO_Ack handshake sequence. Any actions on the part of the Downstream component necessary to ready itself for loss of power must be completed prior to initiating the transition to L2/L3 Ready. Once all preparations for loss of power and clock are completed, L2/L3 Ready entry is initiated by the Downstream component by sending the PM_Enter_L23 DLLP Upstream.
- L2/L3 Ready entry transition protocol uses the PM_Enter_L23 DLLP.

Note that the PM_Enter_L23 DLLPs are sent continuously until an acknowledgement is received or power is removed.

- Refer to $\S$ Section 5.2 if the negotiation to L2/L3 Ready is interrupted.


### 5.3.3 Power Management Event Mechanisms

### 5.3.3.1 Motivation

The PCI Express PME mechanism is software compatible with the [PCI] PME mechanism. Power Management Events are generated by Functions as a means of requesting a PM state change. Power Management Events are typically utilized to revive the system or an individual Function from a low power state.

Power management software may transition a Hierarchy into a low power state, and transition the Upstream Links of these devices into the non-communicating L2 state. ${ }^{102}$ The PCI Express PME generation mechanism is, therefore, broken into two components:

- Waking a non-communicating Hierarchy (wakeup). This step is required only if the Upstream Link of the device originating the PME is in the non-communicating L2 state, since in that state the device cannot send a PM_PME Message Upstream.
- Sending a PM_PME Message to the root of the Hierarchy

PME indications that originate from PCI Express Endpoints or PCI Express Legacy Endpoints are propagated to the Root Complex in the form of TLP messages. PM_PME Messages identify the requesting agent within the Hierarchy (via the Requester ID of the PM_PME Message header). Explicit identification within the PM_PME Message is intended to facilitate quicker PME service routine response, and hence shorter resume time.

If an RCIEP is associated with a Root Complex Event Collector, any PME indications that originate from that RCIEP must be reported by that Root Complex Event Collector.

PME indications that originate from a Root Port itself are reported through the same Root Port.

[^0]
[^0]:    102. The L2 state is defined as "non-communicating" since component reference clock and main power supply are removed in that state.

# 5.3.3.2 Link Wakeup 

The Link wakeup mechanisms provide a means of signaling the platform to re-establish power and reference clocks to the components within its domain. There are two defined wakeup mechanisms: Beacon and WAKER. The Beacon mechanism uses in-band signaling to implement wakeup functionality. For components that support wakeup functionality, the form factor specification(s) targeted by the implementation determine the support requirements for the wakeup mechanism. Switch components targeting applications where Beacon is used on some Ports of the Switch and WAKER is used for other Ports must translate the wakeup mechanism appropriately (see the implementation note Example of WAKE\# to Beacon Translation in § Section 5.3.3.2 ). In applications where WAKE\# is the only wakeup mechanism used, the Root Complex is not required to support the receipt of Beacon.

The WAKE\# mechanism uses sideband signaling to implement wakeup functionality. WAKE\# is an "open drain" signal asserted by components requesting wakeup and observed by the associated power controller. WAKE\# is only defined for certain form factors, and the detailed specifications for WAKE\# are included in the relevant form factor specifications. Specific form factor specifications may require the use of either Beacon or WAKE\# as the wakeup mechanism.

When WAKE\# is used as a wakeup mechanism, once WAKE\# has been asserted, the asserting Function must continue to drive the signal low until main power has been restored to the component as indicated by Fundamental Reset going inactive.

The system is not required to route or buffer WAKE\# in such a way that an Endpoint is guaranteed to be able to detect that the signal has been asserted by another Function.

Before using any wakeup mechanism, a Function must be enabled by software to do so by setting the Function's PME_En bit in the PMCSR. The PME_Status bit is sticky, and Functions must maintain the value of the PME_Status bit through reset if auxiliary power is available and they are enabled for wakeup events (this requirement also applies to the PME_En bit in the PMCSR and the Aux Power PM Enable bit in the Device Control Register).

Systems that allow PME generation from $\mathrm{D} 3_{\text {Cold }}$ state must provide auxiliary power to support Link wakeup when the main system power rails are off. A component may only consume auxiliary power if software has enabled it to do so as described in $\S$ Section 5.6. Software is required to enable auxiliary power consumption in all components that participate in Link wakeup, including all components that must propagate the Beacon signal. In the presence of legacy system software, this is the responsibility of system firmware.

Regardless of the wakeup mechanism used, once the Link has been re-activated and trained, the requesting agent then propagates a PM_PME Message Upstream to the Root Complex. From a power management point of view, the two wakeup mechanisms provide the same functionality, and are not distinguished elsewhere in this chapter.

# IMPLEMENTATION NOTE: EXAMPLE OF WAKE\# TO BEACON TRANSLATION 

Switch components targeting applications that connect "Beacon domains" and "WAKE\# domains" must translate the wakeup mechanism appropriately. § Figure 5-4 shows two example systems, each including slots that use the WAKE\# wakeup mechanism. In Case 1, WAKE\# is input directly to the Power Management Controller, and no translation is required. In Case 2, WAKE\# is an input to the Switch, and in response to WAKE\# being asserted the Switch must generate a Beacon that is propagated to the Root Complex/Power Management Controller.
![img-3.jpeg](03_Knowledge/Tech/PCIe/05_Power_Management/img-3.jpeg)

Figure 5-4 Conceptual Diagrams Showing Two Example Cases of WAKE\# Routing

### 5.3.3.2.1 PME Synchronization

PCI Express-PM introduces a fence mechanism that serves to initiate the power removal sequence while also coordinating the behavior of the platform's power management controller and PME handling by PCI Express agents.

## PME_Turn_Off Broadcast Message

Before main component power and reference clocks are turned off, the Root Complex or Switch Downstream Port must issue a broadcast Message that instructs all agents Downstream of that point within the hierarchy to cease initiation of any subsequent PM_PME Messages, effective immediately upon receipt of the PME_Turn_Off Message.

Each PCI Express agent is required to respond with a TLP "acknowledgement" Message, PME_TO_Ack that is always routed Upstream. In all cases, the PME_TO_Ack Message must terminate at the PME_Turn_Off Message's point of origin. 103

A Switch must report an "aggregate" acknowledgement only after having received PME_TO_Ack Messages from each of its Downstream Ports. Once a PME_TO_Ack Message has arrived on each Downstream Port, the Switch must then send a PME_TO_Ack packet on its Upstream Port. The occurrence of any one of the following must reset the aggregation mechanism: the transmission of the PME_TO_Ack Message from the Upstream Port, the receipt of any TLP at the Upstream Port, the removal of main power to the Switch, or Fundamental Reset.

All components with an Upstream Port must accept and acknowledge the PME_Turn_Off Message regardless of the D state of the associated device or any of its Functions for a Multi-Function Device. Once a component has sent a PME_TO_Ack Message, it must then prepare for removal of its power and reference clocks by initiating a transition to the L2/L3 Ready state.

[^0]
[^0]:    103. Point of origin for the PME_Turn_Off Message could be all of the Root Ports for a given Root Complex (full platform sleep state transition), an individual Root Port, or a Switch Downstream Port.

A Switch must transition its Upstream Link to the L2/L3 Ready state after all of its Downstream Ports have entered the L2/ L3 Ready state.

The Links attached to the originator of the PME_Turn_Off Message are the last to assume the L2/L3 Ready state. This state transition serves as an indication to the power delivery manager ${ }^{104}$ that all Links within that portion of the Hierarchy have successfully retired all in flight PME Messages to the point of PME_Turn_Off Message origin and have performed any necessary local conditioning in preparation for power removal.

In order to avoid deadlock in the case where one or more devices do not respond with a PME_TO_Ack Message and then put their Links into the L2/L3 Ready state, the power manager must implement a timeout after waiting for a certain amount of time, after which it proceeds as if the Message had been received and all Links put into the L2/L3 Ready state. The recommended limit for this timer is in the range of 1 ms to 10 ms .

The power delivery manager must wait a minimum of 100 ns after observing all Links corresponding to the point of origin of the PME_Turn_Off Message enter L2/L3 Ready before removing the components' reference clock and main power. This requirement does not apply in the case where the above mentioned timer triggers.

# IMPLEMENTATION NOTE: PME_TO_ACK MESSAGE PROXY BY SWITCHES 

One of the PME_Turn_Off/PME_TO_Ack handshake's key roles is to ensure that all in flight PME Messages are flushed from the PCI Express fabric prior to sleep state power removal. This is guaranteed to occur because PME Messages and the PME_TO_Ack Messages both use the posted request queue within VCO and so all previously injected PME Messages will be made visible to the system before the PME_TO_Ack is received at the Root Complex. Once all Downstream Ports of the Root Complex receive a PME_TO_Ack Message the Root Complex can then signal the power manager that it is safe to remove power without loss of any PME Messages.

Switches create points of hierarchical expansion and, therefore, must wait for all of their connected Downstream Ports to receive a PME_TO_Ack Message before they can send a PME_TO_Ack Message Upstream on behalf of the sub-hierarchy that it has created Downstream. This can be accomplished very simply using common score boarding techniques. For example, once a PME_Turn_Off broadcast Message has been broadcast Downstream of the Switch, the Switch simply checks off each Downstream Port having received a PME_TO_Ack. Once the last of its active Downstream Ports receives a PME_TO_Ack, the Switch will then send a single PME_TO_Ack Message Upstream as a proxy on behalf of the entire sub-hierarchy Downstream of it. Note that once a Downstream Port receives a PME_TO_Ack Message and the Switch has scored its arrival, the Port is then free to drop the packet from its internal queues and free up the corresponding posted request queue FC credits.

### 5.3.3.3 PM_PME Messages

PM_PME Messages are posted Transaction Layer Packets (TLPs) that inform the power management software which agent within the Hierarchy requests a PM state change. PM_PME Messages, like all other Power Management system Messages, must use the general purpose Traffic Class, TCO.

PM_PME Messages are always routed in the direction of the Root Complex. To send a PM_PME Message on its Upstream Link, a device must transition the Link to the L0 state (if the Link was not in that state already). Unless otherwise noted, the device will keep the Link in the L0 state following the transmission of a PM_PME Message.

[^0]
[^0]:    104. Power delivery control within this context relates to control over the entire Link hierarchy, or over a subset of Links ranging down to a single Link and associated Endpoint for sub hierarchies supporting independently managed power and clock distribution.

# 5.3.3.3.1 PM_PME "Backpressure" Deadlock Avoidance 

A Root Complex is typically implemented with local buffering to store temporarily a finite number of PM_PME Messages that could potentially be simultaneously propagating through the Hierarchy. Given a limited number of PM_PME Messages that can be stored within the Root Complex, there can be backpressure applied to the Upstream directed posted queue in the event that the capacity of this temporary PM_PME Message buffer is exceeded.

Deadlock can occur according to the following example scenario:

1. Incoming PM_PME Messages fill the Root Complex's temporary storage to its capacity while there are additional PM_PME Messages still in the Hierarchy making their way Upstream.
2. The Root Complex, on behalf of system software, issues a Configuration Read Request targeting one of the PME requester's PMCSR (e.g., reading its PME_Status bit).
3. The corresponding split completion Packet is required, as per producer/consumer ordering rules, to push all previously posted PM_PME Messages ahead of it, which in this case are PM_PME Messages that have no place to go.
4. The PME service routine cannot make progress; the PM_PME Message storage situation does not improve.
5. Deadlock occurs.

Precluding potential deadlocks requires the Root Complex to always enable forward progress under these circumstances. This must be done by accepting any PM_PME Messages that posted queue flow control credits allow for, and discarding any PM_PME Messages that create an overflow condition. This required behavior ensures that no deadlock will occur in these cases; however, PM_PME Messages will be discarded and hence lost in the process.

To ensure that no PM_PME Messages are lost permanently, all agents that are capable of generating PM_PME must implement a PME Service Timeout mechanism to ensure that their PME requests are serviced in a reasonable amount of time.

If after $100 \mathrm{~ms}(+50 \% /-5 \%)$, the PME_Status bit of a requesting agent has not yet been cleared, the PME Service Timeout mechanism expires triggering the PME requesting agent to re-send the temporarily lost PM_PME Message. If at this time the Link is in a non-communicating state, then, prior to re-sending the PM_PME Message, the agent must reactivate the Link as defined in § Section 5.3.3.2.

### 5.3.3.4 PME Rules

- All device Functions must implement the PCI-PM Power Management Capabilities (PMC) register and the PMCSR in accordance with the PCI-PM specification. These registers reside in the PCI-PM compliant PCI Capability List format.
- PME capable Functions must implement the PME_Status bit, and underlying functional behavior, in their PMCSR.
- When a Function initiates Link wakeup, or issues a PM_PME Message, it must set its PME_Status bit.
- Switches must route a PM_PME received on any Downstream Port to their Upstream Port
- On receiving a PME_Turn_Off Message, the device must block the transmission of PM_PME Messages and transmit a PME_TO_Ack Message Upstream. The component is permitted to send a PM_PME Message after the Link is returned to an L0 state through LDn.
- Before a Link or a portion of a Hierarchy is transferred into a non-communicating state (i.e., a state from which it cannot issue a PM_PME Message), a PME_Turn_Off Message must be broadcast Downstream.

# 5.3.3.5 PM_PME Delivery State Machine 

The following diagram conceptually outlines the PM_PME delivery control state machine. This state machine determines the ability of a Link to service PME events by issuing PM_PME immediately vs. requiring Link wakeup.
![img-4.jpeg](03_Knowledge/Tech/PCIe/05_Power_Management/img-4.jpeg)

Figure 5-5 A Conceptual PME Control State Machine

## Communicating State:

At initial power-up and associated reset, the Upstream Link enters the Communicating state

- If PME_Status is asserted (assuming PME delivery is enabled), a PM_PME Message will be issued Upstream, terminating at the root of the Hierarchy. The next state is the PME Sent state
- If a PME_Turn_Off Message is received, the Link enters the Non-communicating state following its acknowledgment of the Message and subsequent entry into the L2/L3 Ready state.

Non-communicating State:

- Following the restoration of power and clock, and the associated reset, the next state is the Communicating state.
- If PME_Status is asserted, the Link will transition to the Link Reactivation state, and activate the wakeup mechanism.

- If PME_Status is cleared, the Function becomes PME Capable again. Next state is the Communicating state.
- If the PME_Status bit is not Clear by the time the PME service timeout expires, a PM_PME Message is re-sent Upstream. Refer to $\S$ Section 5.3.3.3.1 for an explanation of the timeout mechanism.
- If a PME Message has been issued but the PME_Status has not been cleared by software when the Link is about to be transitioned into a messaging incapable state (a PME_Turn_Off Message is received), the Link transitions into Link Reactivation state after sending a PME_TO_Ack Message. The device also activates the wakeup mechanism.

Link Reactivation State

- Following the restoration of power and clock, and the associated reset, the Link resumes a transaction-capable state. The device clears the wakeup signaling, if necessary, and issues a PM_PME Upstream and transitions into the PME Sent state.


# 5.4 Native PCI Express Power Management Mechanisms 

The following sections define power management features that require new software. While the presence of these features in new PCI Express designs will not break legacy software compatibility, taking the full advantage of them requires new code to manage them.

These features are enumerated and configured using PCI Express native configuration mechanisms as described in § Chapter 7. of this specification. Refer to § Chapter 7. for specific register locations, bit assignments, and access mechanisms associated with these PCI Express-PM features.

### 5.4.1 Active State Power Management (ASPM)

All Ports not associated with an Internal Root Complex Link or system Egress Port are required to support the minimum requirements defined herein for Active State Link PM. This feature must be treated as being orthogonal to the PCI-PM software compatible features from a minimum requirements perspective. For example, the Root Complex is exempt from the PCI-PM software compatible features requirements; however, it must implement the minimum requirements of ASPM.

Components in the DO state (i.e., fully active state) normally keep their Upstream Link in the active L0 state, as defined in § Section 5.3.2 . ASPM defines a protocol for components in the DO state to reduce Link power by placing their Links into a low power state and instructing the other end of the Link to do likewise. This capability allows hardware-autonomous, dynamic Link power reduction beyond what is achievable by software-only controlled (i.e., PCI-PM software driven) power management.

In Non-Flit Mode there are two low power "standby" Link states defined for ASPM, L0s and L1. In Flit Mode L0p effectively replaces L0s, and L1 remains as a "standby" Link state for ASPM.

The L0s low power Link state is optimized for short entry and exit latencies, while providing substantial power savings. If the L0s state is enabled in a device, it is recommended that the device bring its Transmit Link into the L0s state whenever that Link is not in use (refer to $\S$ Section 5.4.1.1.1 for details relating to the L0s invocation policy). Component support of the L0s Link state from within the DO device state is optional unless the applicable form factor specification for the Link explicitly requires it.

The L0p low power Link state is optimized for short entry and longer exit latencies, while providing substantial power savings and supporting Link operation while a Link width change is in progress.

The L1 Link state is optimized for maximum power savings at a cost of longer entry and exit latencies. L1 reduces Link power beyond the L0s state for cases where very low power is required and longer transition times are acceptable. ASPM support for the L1 Link state is optional unless specifically required by a particular form factor.

Optional L1 PM Substates L1.1 and L1.2 are defined. These substates can further reduce Link power for cases where very low idle power is required, and longer transition times are acceptable.

Each component must report its level of support for ASPM in the ASPM Support field. As applicable, each component shall also report its L0s and L1 exit latency (the time that it requires to transition from the L0s or L1 state to the L0 state). Endpoint Functions must also report the worst-case latency that they can withstand before risking, for example, internal FIFO overruns due to the transition latency from L0s or L1 to the L0 state. Power management software can use the provided information to then enable the appropriate level of ASPM.

The L1 exit latency also applies to L0p, but when used for L0p, indicates the time required to widen the Link. The Link remains operational during this time period, but at lower bandwidth.

# NOTE: L0p and ASPM 

A future draft of this specification may define a mechanism to report the worst case latency an Endpoint can withstand at L0p reduced bandwidth. This may involve multiple latency requirement values depending on the beginning and ending Link widths. Power management software could use this information to enable appropriate L0p Link widths for ASPM.

The L0s exit latency may differ significantly if the reference clock for opposing sides of a given Link is provided from the same source, or delivered to each component from a different source. PCI Express-PM software informs each device of its clock configuration via the Common Clock Configuration bit in its Capability structure's Link Control register. This bit serves as the determining factor in the L0s exit latency value reported by the device. ASPM may be enabled or disabled by default depending on implementation specific criteria and/or the requirements of the associated form factor specification(s). Software can enable or disable ASPM using a process described in § Section 5.4.1.4.1 .

Power management software enables or disables ASPM in each Port of a component by programming the ASPM Control field. Note that new BIOS code can effectively enable or disable ASPM functionality when running with a legacy operating system, but a PCI Express-aware operating system might choose to override ASPM settings configured by the BIOS.

## IMPLEMENTATION NOTE: ISOCHRONOUS TRAFFIC AND ASPM

Isochronous traffic requires bounded service latency. ASPM may add latency to isochronous transactions beyond expected limits. A possible solution would be to disable ASPM for devices that are configured with an Isochronous Virtual Channel.

For ARI Devices, ASPM Control is determined solely by the setting in Function 0, regardless of Function 0's D-state. The ASPM Control settings in other Functions are ignored by the component.

An Upstream Port of a non-ARI Multi-Function Device may be programmed with different values in their respective ASPM Control fields of each Function. The policy for such a component will be dictated by the most active common denominator among all D0 Functions according to the following rules:

- Functions in a non-D0 state (D1 and deeper) are ignored in determining the ASPM policy

- If any of the Functions in the DO state has its ASPM disabled (ASPM Control field = 00b) or if at least one of the Functions in the DO state is enabled for LOs only (ASPM Control field = 01b) and at least one other Function in the DO state is enabled for L1 only (ASPM Control field = 10b), then ASPM is disabled for the entire component
- Else, if at least one of the Functions in the DO state is enabled for LOs only (ASPM Control field = 01b), then ASPM is enabled for LOs only
- Else, if at least one of the Functions in the DO state is enabled for L1 only (ASPM Control field = 10b), then ASPM is enabled for L1 only
- Else, ASPM is enabled for both LOs and L1 states

Note that the components must be capable of changing their behavior during runtime as device Functions enter and exit low power device states. For example, if one Function within a Multi-Function Device is programmed to disable ASPM, then ASPM must be disabled for that device while that Function is in the DO state. Once the Function transitions to a non-DO state, ASPM can be enabled if all other Functions are enabled for ÄSPM.

# 5.4.1.1 LOs ASPM State 

## IMPLEMENTATION NOTE: <br> LOS ONLY WORKS IN NON-FLIT MODE WITH NO RETIMERS

Flit Mode does not support LOs.
Retimers do not support LOs.

Device support of the LOs low power Link state is optional unless the applicable form factor specification for the Link explicitly requires it.

# IMPLEMENTATION NOTE: POTENTIAL ISSUES WITH LEGACY SOFTWARE WHEN LOS IS NOT SUPPORTED 

In earlier versions of this specification, device support of LOs was mandatory, and software could legitimately assume that all devices support LOs. Newer hardware components that do not support LOs may encounter issues with such "legacy software". Such software might not even check the ASPM Support field in the Link Capabilities register, might not recognize the subsequently defined values ( 00 b and 10b) for the ASPM Support field, or might not follow the policy of enabling LOs only if components on both sides of the Link each support LOs.

Legacy software (either operating system or firmware) that encounters the previously reserved value 00b (No ASPM Support), will most likely refrain from enabling L1, which is intended behavior. Legacy software will also most likely refrain from enabling LOs for that component's Transmitter (also intended behavior), but it is unclear if such software will also refrain from enabling LOs for the component on the other side of the Link. If software enables LOs on one side when the component on the other side does not indicate that it supports LOs, the result is undefined. Situations where the resulting behavior is unacceptable may need to be handled by updating the legacy software, establishing a list of configurations for which the legacy software is directed not to enable LOs, or simply not supporting the problematic system configurations.

On some platforms, firmware controls ASPM, and the operating system may either preserve or override the ASPM settings established by firmware. This will be influenced by whether the operating system supports controlling ASPM, and in some cases by whether the firmware permits the operating system to take control of ASPM. Also, ASPM control with hot-plug operations may be influenced by whether native PCI Express hot-plug versus ACPI hot-plug is used. Addressing any legacy software issues with LOs may require updating the firmware, the operating system, or both.

When a component does not advertise that it supports LOs, as indicated by its ASPM Support field value being 00b or 10b, it is recommended that the component's LOs Exit Latency field return a value of 111b, indicating the maximum latency range. Advertising this maximum latency range may help discourage legacy software from enabling LOs if it otherwise would do so, and thus may help avoid problems caused by legacy software mistakenly enabling LOs on this component or the component on the other side of the Link.

Transaction Layer and Link Layer timers are not affected by a transition to the LOs state (i.e., they must follow the rules as defined in their respective chapters).

## IMPLEMENTATION NOTE: MINIMIZING LOS EXIT LATENCY

LOs exit latency depends mainly on the ability of the Receiver to quickly acquire bit and Symbol synchronization. Different approaches exist for high-frequency clocking solutions which may differ significantly in their LOs exit latency, and therefore in the efficiency of ASPM. To achieve maximum power savings efficiency with ASPM, LOs exit latency should be kept low by proper selection of the clocking solution.

# 5.4.1.1.1 Entry into the LOs State 

Entry into the LOs state is managed separately for each direction of the Link. It is the responsibility of each device at either end of the Link to initiate an entry into the LOs state on its transmitting Lanes. Software must not enable LOs in either direction on a given Link unless components on both sides of the Link each support LOs; otherwise, the result is undefined.

A Port that is disabled for the LOs state must not transition its transmitting Lanes to the LOs state. However, if the Port advertises that it supports LOs, Port must be able to tolerate having its Receiver Port Lanes enter LOs, (as a result of the device at the other end bringing its transmitting Lanes into LOs state), and then later returning to the LO state.

## LOs Invocation Policy

Ports that are enabled for LOs entry generally should transition their Transmit Lanes to the LOs state if the defined idle conditions (below) are met for a period of time, recommended not to exceed $7 \mu \mathrm{~s}$. Within this time period, the policy used by the Port to determine when to enter LOs is implementation specific. It is never mandatory for a Transmitter to enter LOs.

Definition of Idle
The definition of an "idle" Upstream Port varies with device Function category. An Upstream Port of a Multi-Function Device is considered idle only when all of its Functions are idle.

A non-Switch Port is determined to be idle if the following conditions are met:

- No TLP is pending to transmit over the Link, or no FC credits are available to transmit any TLPs
- No DLLPs are pending for transmission

A Switch Upstream Port Function is determined to be idle if the following conditions are met:

- None of the Switch's Downstream Port Receive Lanes are in the L0, Recovery, or Configuration state
- No pending TLPs to transmit, or no FC credits are available to transmit anything
- No DLLPs are pending for transmission

A Switch's Downstream Port is determined to be idle if the following conditions are met:

- The Switch's Upstream Port's Receive Lanes are not in the L0, Recovery, or Configuration state
- No pending TLPs to transmit on this Link, or no FC credits are available
- No DLLPs are pending for transmission

Refer to § Section 4.2 for details on LOs entry by the Physical Layer.

### 5.4.1.1.2 Exit from the LOs State

A component with its Transmitter in LOs must initiate LOs exit when it has a TLP or DLLP to transmit across the Link. Note that a transition from the LOs Link state does not depend on the status (or availability) of FC credits. The Link must be able to reach the LO state, and to exchange FC credits across the Link. For example, if all credits of some type were consumed when the Link entered LOs, then any component on either side of the Link must still be able to transition the Link to the LO state when new credits need to be sent across the Link. Note that it may be appropriate for a component to anticipate the end of the idle condition and initiate LOs transmit exit; for example, when an NP request is received.

Downstream Initiated Exit

The Upstream Port of a component is permitted to initiate an exit from the LOs low-power state on its Transmit Link, (Upstream Port Transmit Lanes in the case of a Downstream Switch), if it needs to communicate through the Link. The component initiates a transition to the L0 state on Lanes in the Upstream direction as described in § Section 4.2 .

If the Upstream component is a Switch (i.e., it is not the Root Complex), then it must initiate a transition on its Upstream Port Transmit Lanes (if the Upstream Port's Transmit Lanes are in a low-power state) as soon as it detects an exit from LOs on any of its Downstream Ports.

Upstream Initiated Exit
A Downstream Port is permitted to initiate an exit from LOs low power state on any of its Transmit Links if it needs to communicate through the Link. The component initiates a transition to the L0 state on Lanes in the Downstream direction as described in § Chapter 4.

If the Downstream component contains a Switch, it must initiate a transition on all of its Downstream Port Transmit Lanes that are in LOs at that time as soon as it detects an exit from LOs on its Upstream Port. Links that are already in the L0 state are not affected by this transition. Links whose Downstream component is in a low-power state (i.e., D1- D3 ${ }_{\text {Hot }}$ states) are also not affected by the exit transitions.

For example, consider a Switch with an Upstream Port in LOs and a Downstream device in a D1 state. A configuration request packet travels Downstream to the Switch, intending ultimately to reprogram the Downstream device from D1 to D0. The Switch's Upstream Port Link must transition to the L0 state to allow the packet to reach the Switch. The Downstream Link connecting to the device in D1 state will not transition to the L0 state yet; it will remain in the L1 state. The captured packet is checked and routed to the Downstream Port that shares a Link with the Downstream device that is in D1. As described in § Section 4.2 , the Switch now transitions the Downstream Link to the L0 state. Note that the transition to the L0 state was triggered by the packet being routed to that particular Downstream L1 Link, and not by the transition of the Upstream Port's Link to the L0 state. If the packet's destination was targeting a different Downstream Link, then that particular Downstream Link would have remained in the L1 state.

# 5.4.1.2 ASPM LOp State 

L0p is a substate of L0 that provides power savings with short entry latency and a longer exit latency. Local LOp exit latency and remote LOp exit latency are visible to software and are reported in the Local LOp Exit Latency and Remote LOp Exit Latency fields of the Data Link Feature Extended Capability.

L0p is supported in Flit Mode only and can be used only when supported by both Link partners. When supported, ASPM LOp is controlled by the Hardware Autonomous Width Disable bit in the Link Control Register and by several Device Control 3 Register fields. the See § Section 4.2.6.7 for more detail on LOp.

### 5.4.1.3 ASPM L1 State

A component may optionally support the ASPM L1 state; a state that provides greater power savings at the expense of longer exit latency. L1 exit latency is visible to software, and reported via the L1 Exit Latency field.

# IMPLEMENTATION NOTE: POTENTIAL ISSUES WITH LEGACY SOFTWARE WHEN ONLY L1 IS SUPPORTED 

In earlier versions of this specification, device support of LOs was mandatory, and there was no architected ASPM Support field value to indicate L1 support without LOs support. Newer hardware components that support only L1 may encounter issues with "legacy software", i.e., software that does not recognize the subsequently defined value for the ASPM Support field.

Legacy software that encounters the previously reserved value 10b (L1 Support), may refrain from enabling both LOs and L1, which unfortunately avoids using L1 with new components that support only L1. While this may result in additional power being consumed, it should not cause any functional misbehavior. However, the same issues with respect to legacy software enabling LOs exist for this 10b case as are described in the Implementation Note "Potential Issues With Legacy Software When LOs is Not Supported" in § Section 5.4.1.1.

When supported, L1 entry is controlled by the ASPM Control field. Software must enable ASPM L1 on the Downstream component only if it is supported by both components on a Link. Software must sequence the enabling and disabling of ASPM L1 such that the Upstream component is enabled before the Downstream component and disabled after the Downstream component.

### 5.4.1.3.1 ASPM Entry into the L1 State

An Upstream Port on a component enabled for L1 ASPM entry may initiate entry into the L1 Link state.
See § Section 5.5.1 for details on transitions into either the L1.1 or L1.2 substates.

## IMPLEMENTATION NOTE: INITIATING L1

This specification does not dictate when a component with an Upstream Port must initiate a transition to the L1 state. The interoperable mechanisms for transitioning into and out of L1 are defined within this specification; however, the specific ASPM policy governing when to transition into L1 is left to the implementer.

One possible approach would be for the Downstream device to initiate a transition to the L1 state once the device has both its Receiver and Transmitter in the LOs state (RxLOs and TxLOs) for a set amount of time. Another approach would be for the Downstream device to initiate a transition to the L1 state once the Link has been idle in L0 for a set amount of time. This is particularly useful if LOs entry is not enabled. Still another approach would be for the Downstream device to initiate a transition to the L1 state if it has completed its assigned tasks. Note that a component's L1 invocation policy is in no way limited by these few examples.

Three power management Messages provide support for the ASPM L1 state:

- PM_Active_State_Request_L1 (DLLP)
- PM_Request_Ack (DLLP)
- PM_Active_State_Nak (TLP)

Downstream components enabled for ASPM L1 entry negotiate for L1 entry with the Upstream component on the Link.
A Downstream Port must accept a request to enter L1 if all of the following conditions are true:

- The Port supports ASPM L1 entry, and ASPM L1 entry is enabled. ${ }^{105}$
- No TLP is scheduled for transmission
- No Ack or Nak DLLP is scheduled for transmission (Non-Flit Mode)
- No Flit Ack or Nak is scheduled for transmission (Flit Mode)

A Switch Upstream Port may request L1 entry on its Link provided all of the following conditions are true:

- The Upstream Port supports ASPM L1 entry and it is enabled
- All of the Switch's Downstream Port Links are in the L1 state (or deeper)
- No pending TLPs to transmit
- No pending DLLPs to transmit
- The Upstream Port's Receiver is idle for an implementation specific set amount of time

Note that it is legitimate for a Switch to be enabled for the ASPM L1 Link state on any of its Downstream Ports and to be disabled or not even supportive of ASPM L1 on its Upstream Port. In that case, Downstream Ports may enter the L1 Link state, but the Switch will never initiate an ASPM L1 entry transition on its Upstream Port.

# ASPM L1 Negotiation Rules (see § Figure 5-6 and § Figure 5-7): 

- In Non-Flit Mode, the Downstream component must not initiate ASPM L1 entry until it accumulates at least the minimum number of credits required to send the largest possible packet for any FC type.
- In Flit Mode, for any FC/VC that was initialized with non-zero and non-infinite dedicated credits, the Downstream component must not initiate ASPM L1 entry until it accumulates at least the minimum number of dedicated credits on that VC required to send the largest possible packet for that FC type.
- In Flit Mode, for any FC/VC that was initialized with zero dedicated credits, the Downstream component must not initiate ASPM L1 entry until it accumulates at least the minimum number of shared credits required to send the largest possible packet for that FC type.
- Upon deciding to enter a low-power Link state, the Downstream component must block movement of all TLPs from the Transaction Layer to the Data Link Layer for transmission (including completion packets). If any TLPs become available from the Transaction Layer for transmission during the L1 negotiation process, the transition to L1 must first be completed and then the Downstream component must initiate a return to L0. Refer to § Section 5.2 if the negotiation to L1 is interrupted.
- In Non-Flit Mode, the Downstream component must wait until it receives a Link Layer acknowledgement for the last TLP it had previously sent (i.e., the retry buffer is empty). The component must retransmit a TLP out of its Data Link Layer Retry buffer if required by the Data Link Layer rules.
- In Flit Mode, the Downstream component must wait until it receives a Flit acknowledgement for the last Flit of the last TLP it had previously sent (i.e., the retry buffer is empty). The component must retransmit Flit(s) out of its Retry buffer if required by the Flit Ack/Nak rules.
- The Downstream component then initiates ASPM negotiation by sending a PM_Active_State_Request_L1 DLLP onto its Transmit Lanes. The Downstream component sends this DLLP repeatedly with no more than eight (when using 8b/10b encoding) or 32 (when using 128b/130b encoding) Symbol times of idle between subsequent transmissions of the PM_Active_State_Request_L1 DLLP in Non-Flit Mode. The transmission of other DLLPs and SKP Ordered Sets must occur as required at any time between PM_Active_State_Request_L1

[^0]
[^0]:    105. Software must enable ASPM L1 for the Downstream component only if it is also enabled for the Upstream component.

transmissions, and do not contribute to this idle time limit. Transmission of SKP Ordered Sets during L1 entry follows the clock tolerance compensation rules in $\S$ Section 4.2.8 .

- The Downstream component continues to transmit the PM_Active_State_Request_L1 DLLP as described above until it receives a response from the Upstream device (see below). The Downstream component remains in this loop waiting for a response from the Upstream component.

During this waiting period, the Downstream component must not initiate any Transaction Layer transfers. It must still accept TLPs and DLLPs from the Upstream component, storing for later transmission any TLP responses required. It continues to respond with DLLPs, including FC update DLLPs, as needed by the Link Layer protocol.

If the Downstream component for any reason needs to transmit a TLP on the Link, it must first complete the transition to the low-power Link state. Once in a lower power Link state, the Downstream component must then initiate exit of the low-power Link state to handle the transfer. Refer to $\S$ Section 5.2 if the negotiation to L1 is interrupted.

- The Upstream component must immediately (while obeying all other rules in this specification) respond to the request with either an acceptance or a rejection of the request.
If the Upstream component is not able to accept the request, it must immediately (while obeying all other rules in this specification) reject the request.
- Refer to $\S$ Section 5.2 if the negotiation to L1 is interrupted.

Rules in case of rejection:

- In the case of a rejection, the Upstream component must schedule, as soon as possible, a rejection by sending the PM_Active_State_Nak Message to the Downstream component. Once the PM_Active_State_Nak Message is sent, the Upstream component is permitted to initiate any TLP or DLLP transfers.
- If the request was rejected, it is generally recommended that the Downstream component immediately transition its Transmit Lanes into the L0s state, provided L0s is enabled and that conditions for L0s entry are met.
- Prior to transmitting a PM_Active_State_Request_L1 DLLP associated with a subsequent ASPM L1 negotiation sequence, the Downstream component must either enter and exit L0s on its Transmitter, or it must wait at least $10 \mu \mathrm{~s}$ from the last transmission of the PM_Active_State_Request_L1 DLLP associated with the preceding ASPM L1 negotiation. This $10 \mu \mathrm{~s}$ timer must count only time spent in the LTSSM L0 and L0s states. The timer must hold in the LTSSM Recovery state. If the Link goes down and comes back up, the timer is ignored and the component is permitted to issue new ASPM L1 request after the Link has come back up.

# IMPLEMENTATION NOTE: ASPM L1 ACCEPT/REJECT CONSIDERATIONS FOR THE UPSTREAM COMPONENT 6 

When the Upstream component has responded to the Downstream component's ASPM L1 request with a PM_Request_Ack DLLP to accept the L1 entry request, the ASPM L1 negotiation protocol clearly and unambiguously ends with the Link entering L1. However, if the Upstream component responds with a PM_Active_State_Nak Message to reject the L1 entry request, the termination of the ASPM L1 negotiation protocol is less clear. Therefore, both components need to be designed to unambiguously terminate the protocol exchange. If this is not done, there is the risk that the two components will get out of sync with each other, and the results may be undefined. For example, consider the following case:

- The Downstream component requests ASPM L1 entry by transmitting a sequence of PM_Active_State_Request_L1 DLLPs.
- Due to a temporary condition, the Upstream component responds with a PM_Active_State_Nak Message to reject the L1 request.
- The Downstream component continues to transmit the PM_Active_State_Request_L1 DLLPs for some time before it is able to respond to the PM_Active_State_Nak Message.
- Meanwhile, the temporary condition that previously caused the Upstream component to reject the L1 request is resolved, and the Upstream component erroneously sees the continuing PM_Active_State_Request_L1 DLLPs as a new request to enter L1, and responds by transmitting PM_Request_Ack DLLPs Downstream.

At this point, the result is undefined, because the Downstream component views the L1 request as rejected and finishing, but the Upstream component views the situation as a second L1 request being accepted.

To avoid this situation, the Downstream component needs to provide a mechanism to distinguish between one ASPM L1 request and another. The Downstream component does this by entering L0s (when supported and enabled), or by waiting a minimum of $10 \mu \mathrm{~s}$ from the transmission of the last PM_Active_State_Request_L1 DLLP associated with the first ASPM L1 request before starting transmission of the PM_Active_State_Request_L1 DLLPs associated with the second request (as described above).

If the Upstream component is capable of exhibiting the behavior described above, then it is necessary for the Upstream component to recognize the end of an L1 request sequence by detecting a transition to L0s on its Receiver (when supported and enabled) or a break in the reception of PM_Active_State_Request_L1 DLLPs of $9.5 \mu \mathrm{~s}$ measured while in L0/L0s or more as a separation between ASPM L1 requests by the Downstream component.

If there is a possibility of ambiguity, the Upstream component should reject the L1 request to avoid potentially creating the ambiguous situation outlined above.

Rules in case of acceptance:

- If the Upstream component is ready to accept the request, it must block scheduling of any TLPs from the Transaction Layer.
- In Non-Flit Mode, the Upstream component then must wait until it receives a Data Link Layer acknowledgement for the last TLP it had previously sent. The Upstream component must retransmit a TLP if required by the Data Link Layer rules.

- In Flit Mode, the Upstream component then must wait until it receives a Data Link Layer acknowledgement for the last Flit of the last TLP it had previously sent. The Upstream component must retransmit Flit(s) if required by the Data Link Layer rules.
- Once all TLPs/Flits have been acknowledged, the Upstream component sends a PM_Request_Ack DLLP Downstream. The Upstream component sends this DLLP repeatedly with no more than eight (when using 8b/ 10b encoding) or 32 (when using 128b/130b encoding) Symbol times of idle between subsequent transmissions of the PM_Request_Ack DLLP in Non-Flit Mode. The transmission of SKP Ordered Sets must occur as required at any time between PM_Request_Ack transmissions, and do not contribute to this idle time limit. Transmission of SKP Ordered Sets during L1 entry follows the clock tolerance compensation rules in § Section 4.2.8 .
- The Upstream component continues to transmit the PM_Request_Ack DLLP as described above until it observes its Receive Lanes enter into the Electrical Idle state. Refer to § Chapter 4. for more details on the Physical Layer behavior.
- If the Upstream component needs, for any reason, to transmit a TLP on the Link after it sends a PM_Request_Ack DLLP, it must first complete the transition to the low-power state, and then initiate an exit from the low-power state to handle the transfer once the Link is back to L0. Refer to § Section 5.2 if the negotiation to L1 is interrupted.
- The Upstream component must initiate an exit from L1 in this case even if it does not have the required flow control credit to transmit the TLP(s).
- When the Downstream component detects a PM_Request_Ack DLLP on its Receive Lanes (signaling that the Upstream device acknowledged the transition to L1 request), the Downstream component then ceases sending the PM_Active_State_Request_L1 DLLP, disables DLLP, TLP transmission and brings its Transmit Lanes into the Electrical Idle state.
- When the Upstream component detects an Electrical Idle on its Receive Lanes (signaling that the Downstream component has entered the L1 state), it then ceases to send the PM_Request_Ack DLLP, disables DLLP, TLP transmission and brings the Downstream direction of the Link into the Electrical Idle state.

Notes:

1. The transaction Layer Completion Timeout mechanism is not affected by transition to the L1 state (i.e., it must keep counting).
2. Flow Control Update timers are frozen while the Link is in L1 state to prevent a timer expiration that will unnecessarily transition the Link back to the L0 state.
![img-5.jpeg](03_Knowledge/Tech/PCIe/05_Power_Management/img-5.jpeg)

Figure 5-6 L1 Transition Sequence Ending with a Rejection (L0s Enabled)

![img-6.jpeg](03_Knowledge/Tech/PCIe/05_Power_Management/img-6.jpeg)

Figure 5-7 L1 Successful Transition Sequence

# 5.4.1.3.2 Exit from the L1 State 

Components on either end of a Link may initiate an exit from the L1 Link state.
See § Section 5.5.1 for details on transitions into either the L1.1 or L1.2 substates.
Upon exit from L1, it is recommended that the Downstream component send flow control update DLLPs for all enabled VCs and FC types starting within $1 \mu \mathrm{~s}$ of L1 exit.

## Downstream Component Initiated Exit

An Upstream Port must initiate an exit from L1 on its Transmit Lanes if it needs to communicate through the Link. The component initiates a transition to the L0 state as described in § Chapter 4. . The Upstream component must respond by initiating a similar transition of its Transmit Lanes.

If the Upstream component is a Switch Downstream Port, (i.e., it is not a Root Complex Root Port), the Switch must initiate an L1 exit transition on its Upstream Port's Transmit Lanes, (if the Upstream Port's Link is in the L1 state), as soon as it detects the L1 exit activity on any of its Downstream Port Links. Since L1 exit latencies are relatively long, a Switch must not wait until its Downstream Port Link has fully exited to L0 before initiating an L1 exit transition on its Upstream Port Link. Waiting until the Downstream Link has completed the L0 transition will cause a Message traveling through several Switches to experience accumulating latency as it traverses each Switch.

A Switch is required to initiate an L1 exit transition on its Upstream Port Link after no more than $1 \mu \mathrm{~s}$ from the beginning of an L1 exit transition on any of its Downstream Port Links. Refer to § Section 4.2 for details of the Physical Layer signaling during L1 exit.

Consider the example in § Figure 5-8. The numbers attached to each Port represent the corresponding Port's reported Transmit Lanes L1 exit latency in units of microseconds.

Links 1, 2, and 3 are all in the L1 state, and Endpoint C initiates a transition to the L0 state at time T. Since Switch B takes $32 \mu \mathrm{~s}$ to exit L1 on its Ports, Link 3 will transition to the L0 state at T+32 (longest time considering T+8 for the Endpoint C, and T+32 for Switch B).

Switch B is required to initiate a transition from the L1 state on its Upstream Port Link (Link 2) after no more than $1 \mu \mathrm{~s}$ from the beginning of the transition from the L1 state on Link 3. Therefore, transition to the L0 state will begin on Link 2 at T+1. Similarly, Link 1 will start its transition to the L0 state at time T+2.

Following along as above, Link 2 will complete its transition to the L0 state at time T+33 (since Switch B takes longer to transition and it started at time T+1). Link 1 will complete its transition to the L0 state at time T+34 (since the Root Complex takes $32 \mu \mathrm{~s}$ to transition and it started at time T+2).

Therefore, among Links 1, 2, and 3, the Link to complete the transition to the L0 state last is Link 1 with a $34 \mu \mathrm{~s}$ delay. This is the delay experienced by the packet that initiated the transition in Endpoint C.

![img-7.jpeg](03_Knowledge/Tech/PCIe/05_Power_Management/img-7.jpeg)

Figure 5-8 Example of L1 Exit Latency Computation

Switches are not required to initiate an L1 exit transition on any other of their Downstream Port Links.
Upstream Component Initiated Exit
A Root Complex, or a Switch must initiate an exit from L1 on any of its Root Ports, or Downstream Port Links if it needs to communicate through that Link. The Switch or Root Complex must be capable of initiating L1 exit even if it does not have the flow control credits needed to transmit a given TLP. The component initiates a transition to the L0 state as described in § Chapter 4. . The Downstream component must respond by initiating a similar transition on its Transmit Lanes.

If the Downstream component contains a Switch, it must initiate a transition on all of its Downstream Links (assuming the Downstream Link is in an ASPM L1 state) as soon as it detects an exit from L1 state on its Upstream Port Link. Since L1 exit latencies are relatively long, a Switch must not wait until its Upstream Port Link has fully exited to L0 before initiating an L1 exit transition on its Downstream Port Links. If that were the case, a Message traveling through multiple Switches would experience accumulating latency as it traverses each Switch.

A Switch is required to initiate a transition from L1 state on all of its Downstream Port Links that are currently in L1 after no more than $1 \mu \mathrm{~s}$ from the beginning of a transition from L1 state on its Upstream Port. Refer to § Section 4.2 for details of the Physical Layer signaling during L1 exit. Downstream Port Links that are already in the L0 state do not participate in the exit transition. Downstream Port Links whose Downstream component is in a low power $\overline{\mathrm{D}}$-state ( $\mathrm{D} 1-\mathrm{D} 3_{\text {Hot }}$ ) are also not affected by the L1 exit transitions (i.e., such Links must not be transitioned to the L0 state).

# 5.4.1.4 ASPM Configuration 

All Functions must implement the following configuration bits in support of ASPM. Refer to § Chapter 7. for configuration register assignment and access mechanisms.

Each component reports its level of support for ASPM in the ASPM Support field below.

Table 5-3 Encoding of the ASPM Support
Field

| Field | Description |
| :--: | :--: |
| ASPM Support | 00b No ASPM support |
|  | 01b L0s supported |
|  | 10b L1 supported |
|  | 11b L0s and L1 supported |

Software must not enable LOs in either direction on a given Link unless components on both sides of the Link each support LOs; otherwise, the result is undefined.

Each component reports the source of its reference clock in its Slot Clock Configuration bit located in its Capability structure's Link Status register.

Table 5-4 Description of the Slot Clock Configuration Bit

| Bit | Description |
| :--: | :--: |
| Slot Clock <br> Configuration | This bit, when Set, indicates that the component uses the same physical reference clock that the platform provides on the connector. |
|  | This bit, when Clear, indicates the component uses an independent clock irrespective of the presence of a reference on the connector. |
|  | For Root and Switch Downstream Ports, this bit, when Set, indicates that the Downstream Port is using the same reference clock as the Downstream component or the slot. |
|  | For Switch and Bridge Upstream Ports, this bit when Set, indicates that the Upstream Port is using the same reference clock that the platform provides. |
|  | Otherwise it is Clear. |

Each component must support the Common Clock Configuration bit in its Capability structure's Link Control register. Software writes to this register bit to indicate to the device whether it is sharing the same clock source as the device on the other end of the Link.

Table 5-5 Description of the Common Clock Configuration Bit

| Bit | Description |
| :--: | :--: |
| Common Clock <br> Configuration | This bit, when Set, indicates that this component and the component at the opposite end of the Link are operating with a common clock source. |
|  | This bit, when Clear, indicates that this component and the component at the opposite end of the Link are operating with separate reference clock sources. |
|  | Default value of this bit is Ob. |

| Bit | Description |
| :-- | :-- |
| Components utilize this common clock configuration information to report the correct LOs and L1 Exit <br> Latencies. |  |

Each Port reports the LOs and L1 exit latency (the time that they require to transition their Receive Lanes from the LOs or L1 state to the L0 state) in the L0s Exit Latency and the L1 Exit Latency configuration fields, respectively. If a Port does not support LOs or ASPM L1, the value of the respective exit latency field is undefined.

Table 5-6 Encoding of the LOs Exit Latency Field

| Field | Description |
| :--: | :--: |
| LOs Exit Latency> | 000b Less than 64 ns <br> 001b 64 ns to less than 128 ns <br> 010b 128 ns to less than 256 ns <br> 011b 256 ns to less than 512 ns <br> 100b 512 ns to less than $1 \mu \mathrm{~s}$ <br> 101b $1 \mu \mathrm{~s}$ to less than $2 \mu \mathrm{~s}$ <br> 110b $2 \mu \mathrm{~s}$ to $4 \mu \mathrm{~s}$ <br> 111b More than $4 \mu \mathrm{~s}$ |
| Table 5-7 Encoding of the L1 Exit Latency Field |  |
| Field | Description |
| L1 Exit Latency | 000b Less than $1 \mu \mathrm{~s}$ <br> 001b $1 \mu \mathrm{~s}$ to less than $2 \mu \mathrm{~s}$ <br> 010b $2 \mu \mathrm{~s}$ to less than $4 \mu \mathrm{~s}$ <br> 011b $4 \mu \mathrm{~s}$ to less than $8 \mu \mathrm{~s}$ <br> 100b $8 \mu \mathrm{~s}$ to less than $16 \mu \mathrm{~s}$ <br> 101b $16 \mu \mathrm{~s}$ to less than $32 \mu \mathrm{~s}$ <br> 110b $32 \mu \mathrm{~s}$ to $64 \mu \mathrm{~s}$ <br> 111b More than $64 \mu \mathrm{~s}$ |

Endpoints also report the additional latency that they can absorb due to the transition from LOs state or L1 state to the L0 state. This is reported in the Endpoint LOs Acceptable Latency and Endpoint L1 Acceptable Latency fields, respectively.

Power management software, using the latency information reported by all components in the Hierarchy, can enable the appropriate level of ASPM by comparing exit latency for each given path from Root to Endpoint against the acceptable latency that each corresponding Endpoint can withstand.

Table 5-8 Encoding of the Endpoint LOs
Acceptable Latency Field

| Field | Description |
| :--: | :--: |
| Endpoint LOs Acceptable Latency | 000b Maximum of 64 ns |
|  | 001b Maximum of 128 ns |
|  | 010b Maximum of 256 ns |
|  | 011b Maximum of 512 ns |
|  | 100b Maximum of $1 \mu \mathrm{~s}$ |
|  | 101b Maximum of $2 \mu \mathrm{~s}$ |
|  | 110b Maximum of $4 \mu \mathrm{~s}$ |
|  | 111b No limit |

Table 5-9 Encoding of the Endpoint L1 Acceptable Latency Field

| Field | Description |
| :--: | :--: |
| Endpoint L1 Acceptable Latency | 000b Maximum of $1 \mu \mathrm{~s}$ |
|  | 001b Maximum of $2 \mu \mathrm{~s}$ |
|  | 010b Maximum of $4 \mu \mathrm{~s}$ |
|  | 011b Maximum of $8 \mu \mathrm{~s}$ |
|  | 100b Maximum of $16 \mu \mathrm{~s}$ |
|  | 101b Maximum of $32 \mu \mathrm{~s}$ |
|  | 110b Maximum of $64 \mu \mathrm{~s}$ |
|  | 111b No limit |

Power management software enables or disables ASPM in each component by programming the ASPM Control field.
Table 5-10 Encoding of the ASPM Control
Field

| Field | Description |
| :--: | :--: |
| ASPM Control | 00b Disabled |
|  | 01b LOs Entry Enabled |
|  | 10b L1 Entry Enabled |

| Field | Description |
| :--: | :--: |
|  | 11b LOs and L1 Entry enabled |

# ASPM Control $=00 b$ 

Port's Transmitter must not enter LOs.
Ports connected to the Downstream end of the Link must not issue a PM_Active_State_Request_L1 DLLP on its Upstream Link.

Ports connected to the Upstream end of the Link receiving a L1 request must respond with negative acknowledgement.

## ASPM Control $=01 b$

Port must bring a Link into LOs state if all conditions are met.
Ports connected to the Downstream end of the Link must not issue a PM_Active_State_Request_L1 DLLP on its Upstream Link.

Ports connected to the Upstream end of the Link receiving a L1 request must respond with negative acknowledgement.

## ASPM Control $=10 b$

Port's Transmitter must not enter LOs.
Ports connected to the Downstream end of the Link may issue PM_Active_State_Request_L1 DLLPs.
Ports connected to the Upstream end of the Link must respond with positive acknowledgement to a L1 request and transition into L1 if the conditions for the Root Complex Root Port or Switch Downstream Port in § Section 5.4.1.3.1 are met.

## ASPM Control $=11 b$

Port must bring a Link into the LOs state if all conditions are met.
Ports connected to the Downstream end of the Link may issue PM_Active_State_Request_L1 DLLPs.
Ports connected to the Upstream end of the Link must respond with positive acknowledgement to a L1 request and transition into L1 if the conditions for the Root Complex Root Port or Switch Downstream Port in § Section 5.4.1.3.1 are met.

### 5.4.1.4.1 Software Flow for Enabling or Disabling ASPM

Following is an example software algorithm that highlights how to enable or disable ASPM in a component.

- PCI Express components power up with an appropriate value in their Slot Clock Configuration bit. The method by which they initialize this bit is device-specific.
- PCI Express system software scans the Slot Clock Configuration bit in the components on both ends of each Link to determine if both are using the same reference clock source or reference clocks from separate sources. If the Slot Clock Configuration bits in both devices are Set, they are both using the same reference clock source, otherwise they're not.
- PCI Express software updates the Common Clock Configuration bits in the components on both ends of each Link to indicate if those devices share the same reference clock and triggers Link retraining by writing 1 b to the Retrain Link bit in the Link Control register of the Upstream component.

- Devices must reflect the appropriate L0s/L1 exit latency in their L0s/L1 Exit Latency fields, per the setting of the Common Clock Configuration bit.
- PCI Express system software then reads and calculates the L0s/L1 exit latency for each Endpoint based on the latencies reported by each Port. Refer to § Section 5.4.1.3.2 for an example.
- For each component with one or more Endpoint Functions, PCI Express system software examines the Endpoint LOs Acceptable Latency /Endpoint L1 Acceptable Latency, as reported by each Endpoint Function in its Link Capabilities Register, and enables or disables L0s /L1 entry (via the ASPM Control field in the Link Control Register) accordingly in some or all of the intervening device Ports on that hierarchy.


# 5.5 L1 PM Substates 

L1 PM Substates establish a Link power management regime that creates lower power substates of the L1 Link state (see § Figure 5-9), and associated mechanisms for using those substates. The L1 PM Substates are:

- L1.0 substate
- The L1.0 substate corresponds to the conventional L1 Link state. This substate is entered whenever the Link enters L1. The L1 PM Substate mechanism defines transitions from this substate to and from the L1.1 and L1.2 substates.
- The Upstream and Downstream Ports must be enabled to detect Electrical Idle exit as required in § Section 4.2.7.7.2 .
- L1.1 substate
- Link common mode voltages are maintained.
- Uses a bidirectional open-drain clock request (CLKREQ\#) signal for entry to and exit from this state.
- The Upstream and Downstream Ports are not required to be enabled to detect Electrical Idle exit.
- L1.2 substate
- Link common mode voltages are not required to be maintained.
- Uses a bidirectional open-drain clock request (CLKREQ\#) signal for entry to and exit from this state.
- The Upstream and Downstream Ports are not required to be enabled to detect Electrical Idle exit.

Ports that support L1 PM Substates must not require a reference clock while in L1 PM Substates other than L1.0.
Ports that support L1 PM Substates and also support SRIS mode are required to support L1 PM Substates while operating in SRIS mode. In such cases the CLKREQ\# signal is used by the L1 PM Substates protocol as defined in this section, but has no defined relationship to any local clocks used by either Port on the Link, and the management of such local clocks is implementation specific.

Ports that support the L1.2 substate for ASPM L1 must support Latency Tolerance Reporting (LTR).

![img-8.jpeg](03_Knowledge/Tech/PCIe/05_Power_Management/img-8.jpeg)

Figure 5-9 State Diagram for L1 PM Substates

- When enabled, the L1 PM Substates mechanism applies the following additional requirements to the CLKREQ\# signal: The CLKREQ\# signal must be supported as a bi-directional open drain signal by both the Upstream and Downstream Ports of the Link. Each Port must have a unique instance of the signal, and the Upstream and Downstream Port CLKREQ\# signals must be connected.
- It is permitted for the Upstream Port to deassert CLKREQ\# when the Link is in the PCI-PM L1 or ASPM L1 states, or when the Link is in the L2/L3 Ready pseudo-state; CLKREQ\# must be asserted by the Upstream Port when the Link is in any other state.
- All other specifications related to the CLKREQ\# signal that are not specifically defined or modified by L1 PM Substates continue to apply.

If these requirements cannot be satisfied in a particular system, then L1 PM Substates must not be enabled.

# IMPLEMENTATION NOTE: CLKREQ\# CONNECTION TOPOLOGIES 

For an Upstream component the connection topologies for the CLKREQ\# signal can vary. A few examples of CLKREQ\# connection topologies are described below. For the Downstream component these cases are essentially the same, however from the Upstream component's perspective, there are some key differences that are described below.

Example 1: Single Downstream Port with a single PLL connected to a single Upstream Port (see § Figure 5-10).
In this platform configuration the Upstream component (A) has only a single CLKREQ\# signal. The Upstream and Downstream Ports' CLKREQ\# (A and B) signals are connected to each other. In this case, Upstream component (A), must assert CLKREQ\# signal whenever it requires a reference clock.
![img-9.jpeg](03_Knowledge/Tech/PCIe/05_Power_Management/img-9.jpeg)

Figure 5-10 Downstream Port with a Single PLL

Example 2: Upstream component with multiple Downstream Ports, with a common shared PLL, connected to separate Downstream components (see § Figure 5-11).

In this example configuration, there are three instances of CLKREQ\# signal for the Upstream component (A), one per Downstream Port and a common shared CLKREQ\# signal for the Upstream component (A). In this topology the Downstream Port CLKREQ\# (CLKREQB\#, CLKREQC\#) signals are used to connect to the CLKREQ\# signal of the Upstream Port of the Downstream components (B and C). The common shared CLKREQ\# (CLKREQA\#) signal for the Upstream component is used to request the reference clock for the shared PLL. The PLL control logic in Upstream component (A) can only be turned off and CLKREQA\# be deasserted when both the Downstream Ports are in L1.1 or L1.2 Substates, and all internal (A) consumers of the PLL don't require a clock.
![img-10.jpeg](03_Knowledge/Tech/PCIe/05_Power_Management/img-10.jpeg)

Figure 5-11 Multiple Downstream Ports with a shared PLL

It is necessary for board implementers to consider what CLKREQ\# topologies will be supported by components in order to make appropriate board level connections to support L1 PM Substates and for the reference clock generation.

# IMPLEMENTATION NOTE: AVOIDING UNINTENDED INTERACTIONS BETWEEN L1 PM SUBSTATES AND THE LTSSM 

It is often the case that implementation techniques which save power will also increase the latency to return to normal operation. When implementing L1 PM Substates, it is important for the implementer to ensure that any added delays will not negatively interact with other elements of the platform. It is particularly important to ensure that LTSSM timeout conditions are not unintentionally triggered. Although typical implementations will not approach the latencies that would cause such interactions, the responsibility lies with the implementer to ensure that correct overall operation is achieved.

### 5.5.1 Entry conditions for L1 PM Substates and L1.0 Requirements

The Link is considered to be in PCI-PM L1.0 when the L1 PM Substate is L1.0 and the LTSSM entered L1 through PCI-PM compatible power management. The Link is considered to be in ASPM L1.0 when the L1 PM Substate is in L1.0 and LTSSM entered L1 through ASPM.

The following rules define how the L1.1 and L1.2 substates are entered:

- Both the Upstream and Downstream Ports must monitor the logical state of the CLKREQ\# signal.
- When in PCI-PM L1.0 and the PCI-PM L1.2 Enable bit is Set, the L1.2 substate must be entered when CLKREQ\# is deasserted.
- When in PCI-PM L1.0 and the PCI-PM L1.1 Enable bit is Set, the L1.1 substate must be entered when CLKREQ\# is deasserted and the PCI-PM L1.2 Enable bit is Clear.
- When in ASPM L1.0 and the ASPM L1.2 Enable bit is Set, the L1.2 substate must be entered when CLKREQ\# is deasserted and all of the following conditions are true:
- The reported snooped LTR value last sent or received by this Port is greater than or equal to the value set by the LTR_L1.2_THRESHOLD Value and Scale fields, or there is no snoop service latency requirement.
- The reported non-snooped LTR last sent or received by this Port value is greater than or equal to the value set by the LTR_L1.2_THRESHOLD Value and Scale fields, or there is no non-snoop service latency requirement.
- When in ASPM L1.0 and the ASPM L1.1 Enable bit is Set, the L1.1 substate must be entered when CLKREQ\# is deasserted and the conditions for entering the L1.2 substate are not satisfied.

When the entry conditions for L1.2 are satisfied, the following rules apply:

- Both the Upstream and Downstream Ports must monitor the logical state of the CLKREQ\# input signal.
- An Upstream Port must not deassert CLKREQ\# until the Link has entered L1.0.
- It is permitted for either Port to assert CLKREQ\# to prevent the Link from entering L1.2.
- A Downstream Port intending to block entry into L1.2 must assert CLKREQ\# before the Link enters L1.
- When CLKREQ\# is deasserted the Ports enter the L1.2.Entry substate of L1.2.

If a Downstream Port is in PCI-PM L1.0 and PCI-PM L1.1 Enable and/or PCI-PM L1.2 Enable are Set, or if a Downstream Port is in ASPM L1.0 and ASPM L1.1 Enable and/or ASPM L1.2 Enable are Set, and the Downstream Port initiates an exit to Recovery without having entered L1.1 or L1.2, the Downstream Port must assert CLKREQ\# until the Link exits Recovery.

# 5.5.2 L1.1 Requirements 

Both Upstream and Downstream Ports are permitted to deactivate mechanisms for electrical idle (EI) exit detection and Refclk activity detection if implemented, however both ports must maintain common mode.

### 5.5.2.1 Exit from L1.1

If either the Upstream or Downstream Port needs to initiate exit from L1.1, it must assert CLKREQ\# until the Link exits Recovery. The Upstream Port must assert CLKREQ\# on entry to Recovery, and must continue to assert CLKREQ\# until the next entry into L1, or other state allowing CLKREQ\# deassertion.

- Next state is L1.0 if CLKREQ\# is asserted.
- The Refclk will eventually be turned on as defined in the PCI Express Mini CEM spec, which may be delayed according to the LTR advertised by the Upstream Port.
§ Figure 5-12 illustrates entry into L1.1 with exit driven by the Upstream Port.
![img-11.jpeg](03_Knowledge/Tech/PCIe/05_Power_Management/img-11.jpeg)

Figure 5-12 Example: L1.1 Waveforms Illustrating Upstream Port Initiated Exit

§ Figure 5-13 illustrates entry into L1.1 with exit driven by the Downstream Port.

![img-12.jpeg](03_Knowledge/Tech/PCIe/05_Power_Management/img-12.jpeg)

Figure 5-13 Example: L1.1 Waveforms Illustrating Downstream Port Initiated Exit

# 5.5.3 L1.2 Requirements 

All Link and PHY state must be maintained during L1.2, or must be restored upon exit using implementation specific means, and the LTSSM and corresponding Port state upon exit from L1.2 must be indistinguishable from the L1.0 LTSSM and Port state.

L1.2 has additional requirements that do not apply to L1.1 These requirements are documented in this section.
L1.2 has three substates, which are defined below (see $\S$ Figure 5-14).

![img-13.jpeg](03_Knowledge/Tech/PCIe/05_Power_Management/img-13.jpeg)

Figure 5-14 L1.2 Substates

# 5.5.3.1 L1.2.Entry 

L1.2.Entry is a transitional state on entry into L1.2 to allow time for Refclk to turn off and to ensure both Ports have observed CLKREQ\# deasserted. The following rules apply to L1.2.Entry:

- Both Upstream and Downstream Ports continue to maintain common mode.
- Both Upstream and Downstream Ports may turn off their electrical idle (EI) exit detect circuitry.
- The Upstream and Downstream Ports must not assert CLKREQ\# in this state.
- Refclk must be turned off within $\mathrm{T}_{\text {L10_REFCLK_OFF }}$.
- Next state is L1.0 if CLKREQ\# is asserted, else the next state is L1.2.Idle after waiting for TPOWER_OFF.

Note that there is a boundary condition which can occur when one Port asserts CLKREQ\# shortly after the other Port deasserts CLKREQ\#, but before the first Port has observed CLKREQ\# deasserted. This is an unavoidable boundary condition that implementations must handle correctly. An example of this condition is illustrated in § Figure 5-15.

![img-14.jpeg](03_Knowledge/Tech/PCIe/05_Power_Management/img-14.jpeg)

Figure 5-15 Example: Illustration of Boundary Condition due to Different Sampling of CLKREQ\#

# 5.5.3.2 L1.2.Idle 

When requirements for the entry into L1.2.Idle state (see § Section 5.5.1) have been satisfied then the Ports enter the L1.2.Idle substate. The following rules apply in L1.2.Idle:

- Both Upstream and Downstream Ports may power-down any active logic, including circuits required to maintain common mode.
- The PHY of both Upstream and Downstream Ports may have their power removed.

The following rules apply for L1.2.Idle state when using the CLKREQ\#-based mechanism:

- If either the Upstream or Downstream Port needs to exit L1.2, it must assert CLKREQ\# after ensuring that $T_{L 1.2}$ has been met.
- If the Downstream Port is initiating exit from L1, it must assert CLKREQ\# until the Link exits Recovery. The Upstream Port must assert CLKREQ\# on entry to Recovery, and must continue to assert CLKREQ\# until the next entry into L1, or other state allowing CLKREQ\# deassertion.
- If the Upstream Port is initiating exit from L1, it must continue to assert CLKREQ\# until the next entry into L1, or other state allowing CLKREQ\# deassertion.
- Both the Upstream and Downstream Ports must monitor the logical state of the CLKREQ\# input signal.
- Next state is L1.2.Exit if CLKREQ\# is asserted.


### 5.5.3.3 L1.2.Exit

This is a transitional state on exit from L1.2 to allow time for both devices to power up. In L1.2.Exit, the following rules apply:

- The PHYs of both Upstream and Downstream Ports must be powered.
- It must not be assumed that common mode has been maintained.

# 5.5.3.3.1 Exit from L1.2 

- The following rules apply for L1.2.Exit using the CLKREQ\#-based mechanism:
- Both Upstream and Downstream Ports must power up any circuits required for L1.0, including circuits required to maintain common mode.
- The Upstream and Downstream Ports must not change their driving state of CLKREQ\# in this state.
- Refclk must be turned on no earlier than $T_{\text {L10_REFCLK_ON }}$ minimum time, and may take up to the amount of time allowed according to the LTR advertised by the Endpoint before becoming valid.
- Next state is L1.0 after waiting for $T_{\text {POWER_ON- }}$
- Common mode is permitted to be established passively during L1.0, and actively during Recovery. In order to ensure common mode has been established, the Downstream Port must maintain a timer, and the Downstream Port must continue to send TS1 training sequences until a minimum of TCOMMONMODE has elapsed since the Downstream Port has started transmitting TS1 training sequences and has detected electrical idle exit on any Lane of the configured Link.
§ Figure 5-16 illustrates the signal relationships and timing constraints associated with L1.2 entry and Upstream Port initiated exit.
§ Figure 5-17 illustrates the signal relationships and timing constraints associated with L1.2 entry and Downstream Port initiated exit.
![img-15.jpeg](03_Knowledge/Tech/PCIe/05_Power_Management/img-15.jpeg)

Figure 5-16 Example: L1.2 Waveforms Illustrating Upstream Port Initiated Exit

![img-16.jpeg](03_Knowledge/Tech/PCIe/05_Power_Management/img-16.jpeg)

Figure 5-17 Example: L1.2 Waveforms Illustrating Downstream Port Initiated Exit

# 5.5.4 L1 PM Substates Configuration 

L1 PM Substates is considered enabled on a Port when any combination of the ASPM L1.1 Enable, ASPM L1.2 Enable, PCI-PM L1.1 Enable and PCI-PM L1.2 Enable bits associated with that Port are Set.

An L1 PM Substate enable bit must only be Set in the Upstream and Downstream Ports on a Link when the corresponding supported capability bit is Set by both the Upstream and Downstream Ports on that Link, otherwise the behavior is undefined.

The Setting of any enable bit must be performed at the Downstream Port before the corresponding bit is permitted to be Set at the Upstream Port. If any L1 PM Substates enable bit is at a later time to be cleared, the enable bit(s) must be cleared in the Upstream Port before the corresponding enable bit(s) are permitted to be cleared in the Downstream Port.

If setting either or both of the enable bits for ASPM L1 PM Substates, both ports must be configured as described in this section while ASPM L1 is disabled.

If setting either or both of the enable bits for PCI-PM L1 PM Substates, both ports must be configured as described in this section while in DO.

Prior to setting either or both of the enable bits for L1.2, the values for $\mathrm{T}_{\text {POWER_ON }}$, Common_Mode_Restore_Time, and, if the ASPM L1.2 Enable bit is to be Set, the LTR_L1.2_THRESHOLD (both Value and Scale fields) must be programmed.

The $T_{\text {POWER_ON }}$ and Common_Mode_Restore_Time fields must be programmed to the appropriate values based on the components and AC coupling capacitors used in the connection linking the two components. The determination of these values is design implementation specific.

When both the ASPM L1.2 Enable and PCI-PM L1.2 Enable bits are cleared, it is not required to program the $T_{\text {POWER_ON }}$, Common_Mode_Restore_Time, and LTR_L1.2_THRESHOLD Value and Scale fields, and hardware must not rely on these fields to have any particular values.

When programming LTR_L1.2_THRESHOLD Value and Scale fields, identical values must be programmed in both Ports.

### 5.5.5 L1 PM Substates Timing Parameters

§ Table 5-11 defines the timing parameters associated with the L1.2 substates mechanism.

Table 5-11 L1.2 Timing Parameters

| Parameter | Description | Min | Max | Units |
| :--: | :--: | :--: | :--: | :--: |
| $\boldsymbol{T}_{\text {POWER_OFF }}$ | CLKREQ\# deassertion to entry into the L1.2.idle substate |  | 2 | $\mu \mathrm{~s}$ |
| $\boldsymbol{T}_{\text {COMMONMODE }}$ | Restoration of Refclk to restoration of common mode established through active transmission of TS1 training sequences (see § Section 5.5.3.3.1) | Programmable in range from 0 to 255 |  | $\mu \mathrm{s}$ |
| $T_{\text {L10_REFLK_OFF }}$ | CLKREQ\# deassertion to Refclk reaching idle electrical state when entering L1.2 | 0 | 100 | ns |
| $T_{\text {L10_REFLK_ON }}$ | CLKREQ\# assertion to Refclk valid when exiting L1.2 | TPOWER_ON | LTR value advertised by the Endpoint | $\mu \mathrm{s}$ |
| $T_{\text {POWER_ON }}$ | The minimum amount of time that each component must wait in L1.2.Exit after sampling CLKREQ\# asserted before actively driving the interface to ensure no device is ever actively driving into an unpowered component. | Set in the L1 PM Substates Control 2 Register (range from 0 to 3100) |  | $\mu \mathrm{s}$ |
| $T_{\text {L1.2 }}$ | Time a Port must stay in L1.2 when CLKREQ\# must remain inactive | 4 |  | $\mu \mathrm{s}$ |

# 5.5.6 Link Activation 

Link Activation is an optional mechanism to temporarily disable L1 Substates. Link Activation is used to bring a Link out of L1.1/L1.2, avoiding potential stalls. An example of one such stall is the stall associated with a Configuration Write to perform a $\mathrm{D} 3_{\text {Hot }}$ to D 0 transition. Link Activation can also be used to indirectly indicate to a Device that it should avoid long-latency internal power management during latency-sensitive or time critical operations.

The following rules apply to Link Activation:

- A Downstream Port is permitted to support Link Activation, as indicated by the Link Activation Supported bit in the L1 PM Substates Capabilities Register being Set.
- The Link Activation Control bit must have no effect on Port behavior unless one or more of the following bits are Set:
- PCI-PM L1.2 Enable
- PCI-PM L1.1 Enable
- When the Link Activation Control bit is Set, the Port that is about to enter L1 must assert, and while in L1 maintain as asserted, the CLKREQ\# signal.
- If the Link Activation Control bit is Clear, the Link Activation mechanism does not impose any additional requirements on the state of the CLKREQ\# signal.
- If the Port is enabled for edge-triggered interrupt signaling using MSI or MSI-X, an interrupt message must be sent every time the logical AND of the following conditions transitions from FALSE to TRUE:
- The associated vector is unmasked (not applicable if MSI does not support PVM)
- The Link Activation Interrupt Enable bit is Set
- The Link Activation Control bit is Set
- The Link Activation Status bit is Set. Note that Link Activation interrupts always use the MSI or MSI-X vector indicated by the interrupt Message Number field in the PCI Express Capabilities Register.

- If the Port is enabled for level-triggered interrupt signaling using the INTx messages, the virtual INTx wire must be asserted whenever and as long as the following conditions are satisfied:
- The Interrupt Disable bit in the Command Register is Clear.
- The Link Activation Interrupt Enable bit is Set
- The Link Activation Control bit is Set
- The Link Activation Status bit is Set
- The Link Activation Status bit must be Set every time the logical AND of the following conditions transitions from FALSE to TRUE:
- Either the PCI-PM L1.2 Enable bit or the PCI-PM L1.1 Enable bit (or both) are Set
- The Link Activation Control bit is Set
- The Link is not in an L1 Substate


# 5.6 Auxiliary Power Support 

The specific definition and requirements associated with auxiliary power are form factor specific, and the terms "auxiliary power" and "Vaux" should be understood in reference to the specific form factor in use. The specific mechanism(s) for supplying auxiliary power are not defined in this specification. The following text defines requirements that apply in all form factors.

Note that support for auxiliary power is optional. Some form factors do not support it. Also, some form factors have dedicated auxiliary power pins while other form factors use the main power pins in some fashion.

PCI Express PM provides a Aux Power PM Enable bit in the Device Control Register that provides the means for enabling a Function to draw the maximum allowance of auxiliary current independent of its level of support for PME generation.

A Function requests auxiliary power allocation by specifying a non-zero value in the Aux_Current field of the PMC register. Refer to § Chapter 7. for the Aux Power PM Enable register bit assignment, and access mechanism.

Allocation of auxiliary power using Aux Power PM Enable and PME_En is determined as follows:
Table 5-12 Aux Power Source and Availability

| Aux Power PM <br> Enable | PME_En | Aux Power <br> Detected | Aux Power Source | Aux Power Available |
| :--: | :--: | :--: | :-- | :-- |
| $x$ | $x$ | $0 b$ | None | None |
| $0 b$ | $0 b$ | $1 b$ | Form factor specific Aux Power rail / <br> pins | Form factor specific (e.g., 10 mW in <br> CEM) |
|  | $1 b$ | Form factor specific Aux Power rail / <br> pins | Aux_Current value (PMC) |  |
| $1 b$ | $x$ | Form factor specific Aux Power rail / <br> pins | Aux_Current value (PMC) |  |

## Aux Power PM Enable $=1 \mathbf{b}$ :

Auxiliary power is allocated as requested in the Aux_Current field of the PMC register, independent of the PME_En bit in the PMSCR. The PME_En bit still controls the ability to master PME.

Additional Aux power is permitted to be allocated using a firmware based mechanism (see the Request D3 ${ }_{\text {Cold }}$ Aux Power Limit_DSM call as defined in [Firmware]).

Additional Aux power is also permitted to be allocated by selecting a PM Sub State in the Power Limit mechanism (see § Section 7.8.1.3).

# Aux Power PM Enable $=0 \mathbf{b}:$ 

Auxiliary power allocation is controlled by the PME_En bit as defined in § Section 7.5.2.2.
Additional Aux power is permitted to be allocated using a firmware based mechanism (see the Request D3 ${ }_{\text {cold }}$ Aux Power Limit _DSM call as defined in [Firmware]).

Additional Aux power is also permitted to be allocated by selecting a PM Sub State in the Power Limit mechanism (see § Section 7.8.1.3).

The Aux Power PM Enable bit is sticky (see § Section 7.4 ) so its state is preserved in the D3 ${ }_{\text {cold }}$ state, and is not affected by the transitions from the $\mathrm{D3}_{\text {cold }}$ state to the $\mathrm{DO}_{\text {uninitialized }}$ state.

### 5.7 Power Management System Messages and DLLPs

§ Table 5-13 defines the location of each PM packet in the PCI Express stack.
Table 5-13 Power Management System Messages and
DLLPs

| Packet | Type |
| :--: | :--: |
| PM_Enter_L1 | DLLP |
| PM_Enter_L23 | DLLP |
| PM_Active_State_Request_L1 | DLLP |
| PM_Request_Ack | DLLP |
| PM_Active_State_Nak | Transaction Layer Message |
| PM_PME | Transaction Layer Message |
| PME_Turn_Off | Transaction Layer Message |
| PME_TO_Ack | Transaction Layer Message |

For information on the structure of the power management DLLPs, refer to § Section 3.5 .
Power Management Messages follow the general rules for all Messages. Power Management Message fields follow the following rules:

- Length field is Reserved.
- Attribute field must be set to the default values (all 0's).
- Address field is Reserved.
- Requester ID - see § Table 2-23 in § Section 2.2.8.2 .
- Traffic Class field must use the default class (TC0).

# 5.8 PCI Function Power State Transitions 

All PCI-PM power management state changes are explicitly controlled by software except for Fundamental Reset which brings all Functions to the DO $\mathrm{D}_{\text {unintialized }}$ state. $\S$ Figure 5-18 shows all supported state transitions. The unlabeled arcs represent a software initiated state transition (Set Power State operation).
![img-17.jpeg](03_Knowledge/Tech/PCIe/05_Power_Management/img-17.jpeg)

Figure 5-18 Function Power Management State Transitions

### 5.9 State Transition Recovery Time Requirements

§ Table 5-14 shows the minimum recovery times that system software must allow between the time that a Function is programmed to change state and the time that the function is next accessed (including Configuration Space), unless Readiness Notifications (see § Section 6.22 ) is used to indicate modified values to system software. For bridge Functions, this delay also constitutes a minimum delay between when the bridge's state is changed and when any Function on the logical bus that it originates can be accessed.

Table 5-14 PCI Function State Transition Delays

| Initial State | Next State | Minimum System Software Guaranteed Delays |
| :--: | :--: | :--: |
| D0 | D1 | 0 |
| D0 or D1 | D2 | $200 \mu \mathrm{~s}$ |
| D0, D1 or D2 | $\mathrm{D3}_{\text {Hot }}$ | 10 ms |
| D1 | D0 | 0 |
| D2 | D0 | $200 \mu \mathrm{~s}$ |
| $\mathrm{D3}_{\text {Hot }}$ | D0 | 10 ms |

### 5.10 SR-IOV Power Management

This section defines power management requirements that are unique to SR-IOV devices.
The PCI Power Management Capability as described elsewhere in § Chapter 5. is required for PFs.
For VFs, the PCI Power Management Capability is optional.

# 5.10.1 VF Device Power Management States 

If a VF does not implement the PCI Power Management Capability, then the VF behaves as if it had been programmed into the equivalent power state of its associated PF.

If a VF implements the PCI Power Management Capability, the functionality must be as defined in § Section 7.5.2 .
If a VF implements the PCI Power Management Capability, the Device behavior is undefined if the PF is placed in a lower power state than the VF. Software should avoid this situation by placing all VFs in lower power state before lowering their associated PF's power state.

A VF in the DO state is in the $\mathrm{DO}_{\text {active }}$ state when the VF has completed its internal initialization and either the VF's Bus Master Enable bit or the VF MSE bit in the SR-IOV Control Register (see § Section 9.3.3.3 ) Extended Capability is Set. The VF's internal initialization must have completed when any of the following conditions have occurred:

- The VF has responded successfully (without returning RRS) to a Configuration Request.
- After issuing an FLR to the VF, one of the following is true:
- At least 1.0 s has passed since the FLR was issued.
- The VF supports Function Readiness Status and, after the FLR was issued, an FRS Message from the VF with Reason Code FLR Completed has been received.
- At least FLR time has passed since the FLR was issued. FLR Time is either (1) the FLR Time value in the Readiness Time Reporting Extended Capability associated with the VF or (2) a value determined by system software / firmware ${ }^{106}$.
- After VF Enable has been Set in a PF, at least one of the following is true:
- At least 1.0 s has passed since VF Enable was Set.
- The PF supports Function Readiness Status and, after VF Enable was Set, an FRS Message from the PF with Reason Code VF Enabled has been received.
- The Reset Time period in the VF's Readiness Time Reporting Extended Capability has passed.
- A time period determined by platform firmware has passed.
- A time period determined by non-guest OS software has passed.
- After transitioning a VF from $\mathrm{D3}_{\text {Hot }}$ to DO, at least one of the following is true:
- At least 10 ms has passed since the request to enter DO was issued.
- The VF supports Function Readiness Status and, after the request to enter DO was issued, an FRS Message from the VF with Reason Code $\mathrm{D3}_{\text {Hot }}$ to DO Transition Completed has been received.
- At least $\mathrm{D3}_{\text {Hot }}$ to DO Time has passed since the request to enter DO was issued. $\mathrm{D3}_{\text {Hot }}$ to DO Time is either (1) the $\mathrm{D3}_{\text {Hot }}$ to DO Time in the Readiness Time Reporting Extended Capability associated with the VF or (2) a value determined by system software / firmware ${ }^{107}$.


### 5.10.2 PF Device Power Management States

The PF's power management state (D-state) has global impact on its associated VFs. If a VF does not implement the PCI Power Management Capability, then it behaves as if it is in an equivalent power state of its associated PF.

If a VF implements the PCI Power Management Capability, the Device behavior is undefined if the PF is placed in a lower power state than the VF. Software should avoid this situation by placing all VFs in lower power state before lowering their associated PF's power state.

When the PF is placed into the $\mathrm{D} 3_{\text {Hot }}$ state:

- If the No_Soft_Reset bit is Clear then the PF performs an internal reset on the $\mathrm{D} 3_{\text {Hot }}$ to DO transition and all its configuration state returns to the default values.

Note: Resetting the PF resets VF Enable which means that VFs no longer exist and any VF specific context is lost after the $\mathrm{D} 3_{\text {Hot }}$ to DO transition is complete.

- If the No_Soft_Reset bit is Set then the internal reset does not occur. The SR-IOV extended capability retains state, and associated VFs remain enabled.

When the PF is placed into the $\mathrm{D} 3_{\text {Cold }}$ state VFs no longer exist, any VF specific context is lost and PME events can only be initiated by the PF.

# IMPLEMENTATION NOTE: NO_SOFT_RESET STRONGLY RECOMMENDED 

It is strongly recommended that the No_Soft_Reset bit be Set in all Functions of a Multi-Function Device. As indicated in the bit definition, all implementations that support Flit Mode are required to Set the No_Soft_Reset bit. This recommendation applies to PFs.

### 5.11 PCI Bridges and Power Management 5

With power management under the direction of the operating system, each class of Functions must have a clearly defined criteria for feature availability as well as what functional context must be preserved when operating in each of the power management states. Some example Device-Class specifications have been proposed as part of the ACPI specification for various Functions ranging from audio to network add-in cards. While defining Device-Class specific behavioral policies for most Functions is outside the scope of this specification, defining the required behavior for PCI bridge functions is within the scope of this specification. The definitions here apply to all three types of PCIe Bridges:

- Host bridge, PCI Express to expansion bus bridge, or other ACPI enumerated bridge
- Switches
- PCI Express to PCI bridge
- PCI-to-CardBus bridge

The mechanisms for controlling the state of these Functions vary somewhat depending on which type of Originating Device is present. The following sections describe how these mechanisms work for the three types of bridges.

This section details the power management policies for PCI Express Bridge Functions. The PCI Express Bridge Function can be characterized as an Originating Device with a secondary bus downstream of it. This section describes the relationship of the bridge function's power management state to that of its secondary bus.

The shaded regions in $\S$ Figure 5-19 illustrate what is discussed in this section.

![img-18.jpeg](03_Knowledge/Tech/PCIe/05_Power_Management/img-18.jpeg)

Figure 5-19 PCI Express Bridge Power Management Diagram

As can be seen from § Figure 5-19, the PCI Express Bridge behavior described in this chapter is common, from the perspective of the operating system, to host bridges, Switches, and PCI Express to PCI bridges.

It is the responsibility of the system software to ensure that only valid, workable combinations of bus and downstream Function power management states are used for a given bus and all Functions residing on that bus.

# 5.11.1 Switches and PCI Express to PCI Bridges 

The power management policies for the secondary bus of a Switch or PCI Express to PCI bridge are identical to those defined for any Bridge Function.

The BPCC_En and B2_B3\# bus power/clock control fields in the Bridge Function's PMCSR_BSE register support the same functionality as for any other Bridges.

### 5.12 Power Management Events

There are two varieties of Power Management Events:

- Wakeup Events
- PME Generation

A Wakeup Event is used to request that power be turned on.
A PME Generation Event is used to identify to the system the Function requesting that power be turned on.
In conventional PCI, both events are associated with the PME\# signal. The PME\# signal is asserted by a Function to request a change in its power management state. When the PME_En bit is Set and the event occurs, the Function sets the PME_Status bit and asserts the PME\# signal. It keeps the PME\# signal asserted until either the PME_En bit or the PME_Status are Cleared (typically by software).

In PCI Express, the Wakeup Event is associated with the WAKE\# signal. If supported, the WAKE\# signal is defined in the associated form factor specification and is used by a Function to request a change in its PCI-PM power management state when the Function is in $\mathrm{D3}_{\text {Cold }}$ and PME_En is Set.

In PCI Express, after main power has been restored and the Link is trained, the Function(s) that initiated the wakeup (e.g., that asserted WAKE\#), sends a PM_PME Message to the Root Complex. The PM_PME Message provides the Root Complex with the identity of the requesting Function(s) without requiring software to poll for the PME_Status bit being Set.

Page 730

