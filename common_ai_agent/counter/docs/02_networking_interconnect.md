# Networking & Interconnect Layer

> **Last Updated: April 2026**
> Navigation: [u2190 AI Infra Overview](ai_infra_overview.md) | [Compute Layer u2192](01_compute_layer.md) | [Storage & Data u2192](03_storage_data.md)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Network-Bound Era](#2-the-network-bound-era)
3. [GPU Interconnect: NVLink & NVLink 5](#3-gpu-interconnect-nvlink--nvlink-5)
4. [Scale-Up Fabrics: Beyond a Single Node](#4-scale-up-fabrics-beyond-a-single-node)
5. [Scale-Out Networking: InfiniBand](#5-scale-out-networking-infiniband)
6. [Scale-Out Networking: RoCE v2 (RDMA over Converged Ethernet)](#6-scale-out-networking-roce-v2-rdma-over-converged-ethernet)
7. [InfiniBand vs RoCE v2: Decision Framework](#7-infiniband-vs-roce-v2-decision-framework)
8. [Open Fabrics: UALink & Ultra Ethernet Consortium](#8-open-fabrics-ualink--ultra-ethernet-consortium)
9. [Optical Interconnect Roadmap: 800G u2192 1.6T](#9-optical-interconnect-roadmap-800g--16t)
10. [MoE All-to-All Traffic Patterns](#10-moe-all-to-all-traffic-patterns)
11. [Network Topologies for AI Clusters](#11-network-topologies-for-ai-clusters)
12. [Networking Vendor Landscape](#12-networking-vendor-landscape)
13. [Cost Analysis: Network Fabric TCO](#13-cost-analysis-network-fabric-tco)
14. [Future Outlook 2026u20132028](#14-future-outlook-20262028)
15. [Key Takeaways](#15-key-takeaways)

---

## 1. Executive Summary

The AI industry has entered a **network-bound era**. As GPU compute capability doubles every generation, the interconnect fabric that moves data between GPUs has become the critical bottleneck determining real-world training throughput and inference latency.

**Key facts at a glance:**

| Metric | 2024 (H100 Era) | 2026 (Blackwell Era) | Trend |
|--------|-----------------|----------------------|-------|
| GPU NVLink BW per GPU | 900 GB/s (NVLink 4) | 1,800 GB/s (NVLink 5) | 2u00d7 per gen |
| Scale-out link per port | 400 Gb/s (NDR) | 800 Gb/s (XDR) | 2u00d7 per gen |
| Max cluster size (commercial) | ~32K GPUs | ~100K+ GPUs | 3u00d7 |
| Optical module generation | 800G LPO | 1.6T CPO (pilots) | 2u00d7 |
| Dominant scale-out protocol | InfiniBand | InfiniBand + UEC Ethernet | Fragmenting |

This document covers the full networking stack for AI infrastructure u2014 from on-node GPU interconnect (NVLink) to rack-scale fabrics (NVSwitch, UALink), cluster-scale networks (InfiniBand, RoCE v2, Ultra Ethernet), and the optical physical layer that underpins it all.

---

## 2. The Network-Bound Era

### 2.1 The Communication-Compute Gap

Modern LLM training is dominated by **collective communication operations** u2014 AllReduce, AllGather, and ReduceScatter u2014 that synchronize model state across thousands of GPUs. The time spent waiting for data to traverse the network now frequently exceeds the time spent on actual computation.

**Why this matters:**

- **GPU FLOPS grew 5u00d7** from A100 (312 TFLOPS FP16) to B200 (2,250 TFLOPS FP16), but network bandwidth only doubled (400u2192800 Gb/s per port).
- In a 64K-GPU training run, a single AllReduce over 200 GB of gradients requires the data to traverse multiple switch hops, each adding latency.
- **Network stragglers** u2014 where one slow link holds up the entire collective u2014 can reduce effective training throughput by 15u201330%.

### 2.2 Bandwidth Hierarchy in AI Clusters

The AI cluster networking stack is organized in a strict bandwidth hierarchy:

| Level | Scope | Technology | Typical BW (bidirectional) | Latency |
|-------|-------|-----------|---------------------------|---------|
| **L0** | Within GPU (HBMu2192SM) | HBM3e | 4.8u20138.0 TB/s | ~100 ns |
| **L1** | GPUu2194GPU (same node) | NVLink 5 | 1,800 GB/s | ~1 u03bcs |
| **L2** | GPUu2194GPU (same rack) | NVLink/NVSwitch | 1,800 GB/s (NVLink domain) | ~2u20135 u03bcs |
| **L3** | Nodeu2194Node (racku2194rack) | InfiniBand / RoCE | 400u2013800 Gb/s per NIC | ~5u201310 u03bcs |
| **L4** | Clusteru2194Cluster | Ethernet / WAN | 100u2013400 Gb/s | ~50 u03bcsu2013ms |

> **Rule of thumb:** Each hop down the hierarchy drops bandwidth by ~3u20135u00d7 and adds ~2u20135u00d7 latency. Optimizing L1 and L2 connectivity (NVLink domain size) is the single highest-leverage networking decision.

### 2.3 Communication Patterns by Workload

| Workload | Dominant Pattern | Data Volume per Step | Network Sensitivity |
|----------|-----------------|---------------------|-------------------|
| Dense LLM Pre-training | AllReduce (gradient sync) | 2u00d7 model-size u00d7 num-layers | High |
| MoE LLM Training | All-to-All (expert routing) | hidden_dim u00d7 seq_len u00d7 num_tokens | **Very High** |
| RLHF / Post-training | AllReduce + broadcast | Medium | Medium |
| Batch Inference | Minimal (pipeline-parallel) | Low | Lowu2013Medium |
| Online Inference (large batch) | KV-cache transfer | High (multi-GPU) | Mediumu2013High |

---

## 3. GPU Interconnect: NVLink & NVLink 5

### 3.1 NVLink Overview

NVLink is NVIDIA's proprietary high-bandwidth, energy-efficient direct GPU-to-GPU interconnect. It provides the fastest possible data path between GPUs, far exceeding PCIe bandwidth.

| Generation | Year | BW per GPU (bidirectional) | Lanes | Lane Speed | Max GPU Connections |
|-----------|------|---------------------------|-------|-----------|-------------------|
| NVLink 1 | 2016 | 160 GB/s | 4 u00d7 8 = 32 | 20 Gb/s | 4 |
| NVLink 2 | 2017 | 300 GB/s | 6 u00d7 8 = 48 | 25 Gb/s | 6 |
| NVLink 3 | 2020 | 600 GB/s | 12 u00d7 8 = 96 | 50 Gb/s | 12 |
| NVLink 4 (H100) | 2022 | 900 GB/s | 18 u00d7 8 = 144 | 50 Gb/s | 18 |
| **NVLink 5 (B200/B300)** | **2024u20132025** | **1,800 GB/s** | **18 u00d7 8 = 144** | **100 Gb/s** | **18** |

### 3.2 NVLink 5 Architecture

NVLink 5 doubles per-lane signaling rate from 50 Gb/s to 100 Gb/s while maintaining the same 18-link (144-lane) physical interface as NVLink 4. Key architectural features:

- **Bidirectional 1,800 GB/s aggregate bandwidth** u2014 equivalent to 14.4 Tb/s per GPU
- **7u00d7 PCIe Gen5 bandwidth** (PCIe Gen5 = 256 GB/s bidirectional u00d716)
- **Fully coherent memory access** across NVLink-connected GPUs (via NVSwitch)
- **Low-latency direct remote memory access** u2014 enables fine-grained communication without CPU involvement

### 3.3 NVSwitch: Expanding the NVLink Domain

NVSwitch is a purpose-built switching ASIC that connects all GPUs in a node (and potentially across nodes in a rack) into a single NVLink fabric.

| NVSwitch Gen | GPUs Supported | BW per Switch | Use Case |
|-------------|---------------|--------------|----------|
| NVSwitch 1 (DGX A100) | 8 GPUs | 7.2 TB/s | 8-GPU NVLink domain |
| NVSwitch 2 (DGX H100) | 8 GPUs (within node) | 12.8 TB/s | 8-GPU NVLink domain |
| **NVSwitch 3 (GB200 NVL72)** | **72 GPUs** | **51.2 TB/s** | **72-GPU NVLink domain** |

### 3.4 NVLink Domain: Why It Matters

The NVLink domain defines the set of GPUs that can communicate at full NVLink bandwidth without traversing a slower scale-out network. Expanding this domain is the most impactful way to improve training efficiency.

| System | NVLink Domain | GPUs in Domain | Memory Pool | Effective BW |
|--------|--------------|---------------|-------------|-------------|
| DGX H100 (8-GPU) | Single node | 8 | 640 GB HBM3 | 900 GB/s per pair |
| DGX B200 (8-GPU) | Single node | 8 | 1,152 GB HBM3e | 1,800 GB/s per pair |
| **GB200 NVL72** | **Full rack** | **72** | **13.4 TB HBM3e** | **1,800 GB/s per pair** |

The GB200 NVL72's 72-GPU NVLink domain means that models up to ~13 TB can be trained with **tensor parallelism** across all 72 GPUs without leaving the NVLink fabric. This eliminates the AllReduce bottleneck for dense models under 400B parameters at typical batch sizes.

### 3.5 NVLink & the Grace-Blackwell Architecture

The GB200 Grace-Blackwell superchip combines:
- **1u00d7 Grace CPU** (72-core ARM Neoverse V2) + **1u00d7 Blackwell GPU** connected via NVLink-C2C (900 GB/s)
- In the NVL72 rack: **36 Grace CPUs + 72 Blackwell GPUs** connected via 36 NVSwitches
- Total NVLink fabric: **130+ TB/s aggregate bandwidth** across the 72-GPU rack

This architecture treats the entire rack as a single compute unit with unified memory addressing u2014 a fundamental shift from the traditional "8-GPU node" model.

---

## 4. Scale-Up Fabrics: Beyond a Single Node

### 4.1 The Scale-Up / Scale-Out Distinction

| Dimension | Scale-Up | Scale-Out |
|-----------|----------|-----------|
| **Scope** | Within a rack (or NVLink domain) | Across racks / rows / clusters |
| **Technologies** | NVLink, NVSwitch, UALink (emerging) | InfiniBand, RoCE, Ethernet |
| **BW per link** | 900u20131,800 GB/s | 50u2013100 GB/s (400u2013800 Gb/s) |
| **Latency** | 1u20135 u03bcs | 5u201320 u03bcs |
| **Protocol** | Custom (coherent memory) | RDMA / UDP / TCP |
| **Key operation** | Tensor parallel, pipeline parallel | Data parallel, expert parallel |

### 4.2 NVIDIA NVLink Domain Expansion

NVIDIA has progressively expanded the NVLink domain:

```
2020: DGX A100 u2014 8 GPUs, NVLink 3 (600 GB/s)
2022: DGX H100 u2014 8 GPUs, NVLink 4 (900 GB/s)
2024: GB200 NVL72 u2014 72 GPUs, NVLink 5 (1,800 GB/s)
2025+: GB300 NVL576 u2014 576 GPUs (rumored, 8u00d7 NVL72)
```

### 4.3 UALink: The Open Scale-Up Alternative

UALink (Ultra Accelerator Link) is an open-standard interconnect led by the **UALink Consortium** (AMD, Broadcom, Google, Intel, Meta, Microsoft, Cisco u2014 notably not NVIDIA).

**UALink 1.0 Specification (released 2025):**

| Parameter | Value |
|-----------|-------|
| Lane speed | 200 Gb/s per lane |
| Max pod size | **1,024 accelerators** |
| Protocol | Load/store + remote atomics |
| Memory model | Coherent shared memory |
| Switching | Indirect topologies (leaf-spine within pod) |
| Target BW | Comparable to NVLink (bidirectional) |
| IP licensing | Royalty-free (open standard) |

**Strategic significance:**
- Challenges NVIDIA's NVLink monopoly on high-bandwidth scale-up
- Enables multi-vendor accelerator pods (AMD MI400 + Intel Gaudi + custom ASICs)
- 1,024-accelerator pod is larger than NVL72 (72 GPUs) but requires proof of comparable real-world performance
- First silicon expected 2026u20132027

### 4.4 Scale-Up Comparison

| Fabric | Max Domain | BW per GPU | Latency | Status | Vendor |
|--------|-----------|-----------|---------|--------|--------|
| NVLink 5 + NVSwitch 3 | 72 GPUs | 1,800 GB/s | ~1u20132 u03bcs | Shipping | NVIDIA |
| NVLink 5 + NVSwitch 4 (NVL576) | 576 GPUs (rumored) | 1,800 GB/s | ~2u20135 u03bcs | 2026 (expected) | NVIDIA |
| **UALink 1.0** | **1,024 accelerators** | **~1,800 GB/s (target)** | **~2u20135 u03bcs (target)** | **Spec released; silicon 2026u201327** | **UALink Consortium** |
| PCIe Gen5 + CXL 3.0 | 8u201316 devices | 256 GB/s (u00d716) | ~5 u03bcs | Shipping | PCIe-SIG |
| Infinity Fabric (AMD) | 8 GPUs (MI300X) | 256 GB/s | ~3 u03bcs | Shipping | AMD |

---

## 5. Scale-Out Networking: InfiniBand

### 5.1 Overview

InfiniBand (IB) is the dominant scale-out network for large-scale AI training clusters. Originally developed by Mellanox (acquired by NVIDIA in 2020 for $6.9B), InfiniBand provides lossless, low-latency, high-bandwidth fabric optimized for HPC and AI workloads.

### 5.2 InfiniBand Generations

| Generation | Year | per-Port Speed | Encoding | Max Cable Length (DAC) | Max Cable Length (Optical) |
|-----------|------|---------------|----------|----------------------|--------------------------|
| SDR | 2002 | 10 Gb/s | 8b/10b | u2014 | u2014 |
| DDR | 2005 | 20 Gb/s | 8b/10b | u2014 | u2014 |
| QDR | 2008 | 40 Gb/s | 8b/10b | 5m | 300m |
| FDR | 2011 | 56 Gb/s | 64b/66b | 5m | 300m |
| EDR | 2014 | 100 Gb/s | 64b/66b | 3m | 300m |
| HDR | 2018 | 200 Gb/s | 64b/66b | 3m | 300m |
| **NDR 400** | **2022** | **400 Gb/s** | **64b/66b** | **2m** | **300m** |
| **NDR 800** | **2023** | **800 Gb/s** | **64b/66b** | **2m** | **300m** |
| **XDR** | **2025u20132026** | **800 Gb/s** | **PAM4** | **2m** | **500m (expected)** |

### 5.3 Key InfiniBand Features for AI

| Feature | Description | Benefit for AI |
|---------|-------------|---------------|
| **RDMA (Remote DMA)** | Direct GPU-to-GPU memory transfer, zero-copy | Eliminates CPU overhead; ~1u03bcs additional latency |
| **GPUDirect RDMA** | NVIDIA extension: GPUu2194NIC direct transfer | Bypasses CPU memory entirely for gradient sync |
| **Adaptive Routing** | Packet spraying across multiple paths | Higher utilization, avoids incast congestion |
| **Credit-Based Flow Control** | Lossless fabric (no packet drops) | Predictable performance for collectives |
| **SHARP (Scalable Hierarchical Aggregation)** | In-switch collective reduction | 2u20133u00d7 AllReduce speedup by offloading to switches |
| **PFC + ECN (congestion control)** | Priority-based flow control + congestion notification | Prevents head-of-line blocking |

### 5.4 NVIDIA Quantum & Spectrum Networking Portfolio

| Product | Type | Ports | per-Port Speed | Total BW | SHARP | Target |
|---------|------|-------|---------------|----------|-------|--------|
| Quantum-2 (QM9700) | IB Switch | 64 | 400 Gb/s (NDR) | 51.2 Tb/s | u2705 v2 | H100 clusters |
| **Quantum-X800 (QM9800)** | **IB Switch** | **72** | **800 Gb/s (XDR)** | **115.2 Tb/s** | **u2705 v3** | **B200/B300 clusters** |
| Spectrum-4 | Ethernet Switch | 64 | 400 Gb/s | 51.2 Tb/s | u274c | RoCE clusters |
| **Spectrum-X800** | **Ethernet Switch** | **64** | **800 Gb/s** | **102.4 Tb/s** | **u274c** | **RoCE/AI Ethernet** |
| ConnectX-7 | NIC (IB/Eth) | 1u20132 | 400 Gb/s | u2014 | u2014 | H100 NIC |
| **ConnectX-8** | **NIC (IB/Eth)** | **1u20132** | **800 Gb/s** | **u2014** | **u2014** | **B200/B300 NIC** |
| BlueField-3 DPU | SmartNIC | 2u00d7 400 Gb/s | u2014 | u2014 | Offload | Security, storage |

### 5.5 SHARP: In-Switch Collective Offload

SHARP (Scalable Hierarchical Aggregation and Reduction Protocol) is one of InfiniBand's most powerful differentiators for AI training:

**How SHARP works:**
1. In an AllReduce, each GPU sends gradient fragments to all peers u2192 O(nu00b2) traffic
2. SHARP offloads the reduction (sum/mean) to the network switch ASIC
3. GPUs send gradient data to the switch u2192 switch computes reduction u2192 broadcasts result
4. Reduces AllReduce traffic from O(nu00b2) to O(n) and latency from O(log n) to O(1) hops

**Performance impact:**
- **2u20133u00d7 AllReduce speedup** for common collective sizes (1 MBu2013100 MB)
- Most impactful at scale: 4K+ GPUs where AllReduce traffic is O(nu00b2)
- Requires SHARP-capable switches (Quantum series) and driver support

---

## 6. Scale-Out Networking: RoCE v2 (RDMA over Converged Ethernet)

### 6.1 Overview

RoCE v2 (RDMA over Converged Ethernet version 2) encapsulates RDMA traffic over standard UDP/IP, enabling RDMA semantics on commodity Ethernet fabrics. It provides ~80u201390% of InfiniBand's performance at ~50u201370% of the cost.

### 6.2 RoCE v2 Technical Details

| Parameter | Value |
|-----------|-------|
| Encapsulation | RDMA over UDP over IPv4/IPv6 over Ethernet |
| Transport | InfiniBand transport layer over UDP (port 4791) |
| Lossless mechanism | PFC (Priority Flow Control) + ECN + DCQCN congestion control |
| Max speed | 800 Gb/s (with ConnectX-8 NICs) |
| RDMA operations | Read, Write, Send, Atomic |
| GPUDirect RDMA | Supported (NVIDIA NICs) |
| Standard | IBTA (InfiniBand Trade Association) |

### 6.3 Lossless Ethernet for RoCE

RoCE v2 requires a **lossless Ethernet fabric** u2014 any dropped packet triggers retransmission that kills RDMA performance. Achieving lossless Ethernet requires:

| Mechanism | Purpose | Configuration |
|-----------|---------|--------------|
| **PFC (802.1Qbb)** | Pause traffic on congestion | Enable on RDMA priority (typically priority 3 or 4) |
| **ECN (802.1Qau)** | Signal congestion to senders | Mark packets at switch threshold (~200 KB buffer) |
| **DCQCN** | Rate-based congestion control | Sender throttles on ECN marks; NVIDIA proprietary tuning |
| **Cable length matching** | Prevent incast congestion | Keep all cable lengths within u00b12m for same tier |
| **Buffer management** | Prevent head-of-line blocking | Dedicated buffers per priority; shared pool for bursts |

### 6.4 RoCE v2 Tuning Checklist

Properly tuning a RoCE v2 fabric for AI training is notoriously difficult. A typical checklist:

```bash
# 1. Enable PFC on the RDMA priority
mlnx_qos -i <iface> --pfc 0,0,0,1,0,0,0,0

# 2. Enable ECN marking
sysctl -w net.ipv4.tcp_ecn=1
mlnx_qos -i <iface> --ecn 0,0,0,1,0,0,0,0

# 3. Configure DCQCN parameters
# (via mlxconfig or sysfs u2014 vendor-specific)

# 4. Set MTU to 9000 (jumbo frames)
ip link set <iface> mtu 9000

# 5. NUMA-affinitize NIC interrupts
set_irq_affinity <numa_node> <iface>

# 6. Disable adaptive routing (not supported on Ethernet)
# Use static routing with ECMP for multi-path
```

### 6.5 When RoCE Works Well

- **Cost-sensitive deployments**: Ethernet switches are 30u201350% cheaper than InfiniBand
- **Mixed workloads**: Clusters running both AI training and general cloud workloads
- **Sub-16K GPU clusters**: Where congestion management is manageable
- **Inference serving**: Less sensitive to tail latency than training

---

## 7. InfiniBand vs RoCE v2: Decision Framework

### 7.1 Head-to-Head Comparison

| Dimension | InfiniBand (NDR/XDR) | RoCE v2 (Ethernet) | Winner |
|-----------|----------------------|---------------------|--------|
| **Raw BW per port** | 400u2013800 Gb/s | 400u2013800 Gb/s | Tie |
| **Latency (1 hop)** | 0.5u20130.7 u03bcs | 0.8u20131.2 u03bcs | IB |
| **Lossless guarantee** | Native (credit-based) | Requires PFC tuning | IB |
| **Collective offload (SHARP)** | u2705 Native | u274c Not available | IB |
| **Adaptive routing** | u2705 Packet spraying | u274c ECMP only | IB |
| **Cost (switch per port)** | $3,000u2013$5,000 | $1,500u2013$3,000 | RoCE |
| **Cost (NIC)** | $2,000u2013$4,000 | $1,000u2013$2,500 | RoCE |
| **Management complexity** | Simple (purpose-built) | High (PFC/ECN tuning) | IB |
| **Multi-tenant isolation** | Limited | VLAN/VXISA/VPC | RoCE |
| **Ecosystem breadth** | NVIDIA-only | Multi-vendor | RoCE |
| **Cable reach (DAC)** | 2m | 3m | RoCE |
| **Max cluster size** | 64K+ endpoints | 64K+ endpoints | Tie |
| **Maturity for AI training** | Proven at 100K+ GPUs | Proven at 32K GPUs | IB |

### 7.2 Decision Matrix

| Scenario | Recommendation | Rationale |
|----------|---------------|-----------|
| **>32K GPU training cluster** | InfiniBand | SHARP, adaptive routing, proven at scale |
| **8Ku201332K GPU training** | InfiniBand (preferred) or tuned RoCE | IB reduces tail latency; RoCE viable with expert tuning |
| **<8K GPU training** | RoCE v2 | Cost advantage; manageable congestion |
| **Mixed training + inference** | RoCE v2 | Ethernet flexibility; multi-workload sharing |
| **Multi-tenant cloud** | RoCE v2 | VLAN isolation; no vendor lock-in |
| **Budget-constrained startup** | RoCE v2 | 30u201350% network cost savings |
| **Maximum performance (any cost)** | InfiniBand | SHARP + adaptive routing + lossless guarantee |

### 7.3 Real-World Deployments

| Organization | Fabric | Cluster Size | Notes |
|-------------|--------|-------------|-------|
| xAI (Colossus) | InfiniBand NDR | 100K GPUs (H100) | Largest known IB deployment |
| Meta (RSC u2192 next-gen) | InfiniBand NDR | 35K+ GPUs | Built on NVIDIA Quantum-2 |
| Microsoft (Azure) | InfiniBand + RoCE | Mixed | IB for largest training; RoCE for inference |
| Google (TPU pods) | Custom OCS + Ethernet | 8K+ TPUs per pod | Optical circuit switching |
| CoreWeave | InfiniBand NDR | 16K+ GPUs | Cloud provider, IB-first |
| Lambda Labs | RoCE v2 | 4K+ GPUs | Cost-effective GPU cloud |

---

## 8. Open Fabrics: UALink & Ultra Ethernet Consortium

### 8.1 The Open Challenge to NVIDIA

NVIDIA controls both the dominant scale-up (NVLink) and scale-out (InfiniBand) fabrics for AI. Two open industry consortia have emerged to break this vertical integration:

```
u250cu2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2510
u2502                  AI NETWORKING ECOSYSTEM (2026)                  u2502
u251cu2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2524
u2502                                                                 u2502
u2502  Scale-Up (within rack)         Scale-Out (rack-to-rack)        u2502
u2502  u250cu2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2510           u250cu2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2510       u2502
u2502  u2502  NVIDIA NVLink   u2502           u2502  NVIDIA InfiniBand   u2502       u2502
u2502  u2502  (proprietary)   u2502           u2502  (proprietary)       u2502       u2502
u2502  u2514u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2518           u2514u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2518       u2502
u2502         u2195 vs                           u2195 vs                    u2502
u2502  u250cu2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2510           u250cu2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2510       u2502
u2502  u2502   UALink 1.0     u2502           u2502  Ultra Ethernet 1.0  u2502       u2502
u2502  u2502   (open spec)    u2502           u2502  (open spec)         u2502       u2502
u2502  u2514u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2518           u2514u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2518       u2502
u2502                                                                 u2502
u2502  UALink Consortium:             Ultra Ethernet Consortium:      u2502
u2502  AMD, Broadcom, Google,         AMD, Arista, Broadcom,         u2502
u2502  Intel, Meta, Microsoft,        Cisco, Edgecore, HPE,          u2502
u2502  Cisco, etc.                    Intel, Meta, Microsoft          u2502
u2502                                                                 u2502
u2514u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2518
```

### 8.2 UALink 1.0 Specification

**Published: 2025 | First silicon expected: 2026u20132027**

| Parameter | UALink 1.0 | NVLink 5 (comparison) |
|-----------|-----------|----------------------|
| **Lane speed** | 200 Gb/s per lane | 100 Gb/s per lane |
| **Num lanes per link** | To be determined by implementer | 144 lanes (18 links u00d7 8) |
| **Max domain size** | **1,024 accelerators** | 72 GPUs (NVL72) |
| **Protocol** | Load/store + remote atomics | Load/store + remote atomics |
| **Memory coherency** | Shared virtual memory | Shared virtual memory |
| **Switching** | Required (indirect topology) | NVSwitch ASICs |
| **IP licensing** | Royalty-free | Proprietary (NVIDIA only) |
| **Vendor lock-in** | Multi-vendor | NVIDIA-only |

**Key UALink design goals:**
1. **Scale to 1,024 accelerators** in a single pod u2014 14u00d7 larger than NVL72
2. **Multi-vendor interoperability** u2014 AMD GPUs and Intel accelerators in the same pod
3. **Composable memory** u2014 pool HBM across all accelerators in the pod
4. **Open specification** u2014 royalty-free implementation

**Challenges:**
- No shipping silicon yet; NVLink has 5+ years of production deployment
- Real-world performance parity unproven
- Requires new switch ASIC designs (Broadcom, Cisco committed)
- Software ecosystem (collective libraries, topology awareness) lags NVLink/CUDA

### 8.3 Ultra Ethernet Consortium (UEC 1.0)

**Published: 2025 | First products expected: 2026**

The Ultra Ethernet Consortium (UEC), part of the Linux Foundation, defines an enhanced Ethernet specification optimized for AI and HPC workloads.

| Parameter | UEC 1.0 | Standard Ethernet | InfiniBand (comparison) |
|-----------|---------|-------------------|------------------------|
| **Link speed** | 400Gu2013800G (1.6T roadmap) | 400Gu2013800G | 400u2013800 Gb/s |
| **Lossless delivery** | u2705 Native (credit-based like IB) | Requires PFC | u2705 Native |
| **Multipath routing** | u2705 Packet spraying | ECMP (limited) | u2705 Adaptive routing |
| **Congestion control** | AI-optimized (low tail latency) | DCQCN (RoCE) | Native |
| **Collective offload** | In-switch aggregation (planned) | u274c | SHARP |
| **Telemetry** | In-band, per-packet | SNMP/gRPC (slow) | In-band |
| **Backward compatible** | u2705 With standard Ethernet | u2014 | u274c (separate fabric) |
| **Transport** | Reliable ordered delivery | UDP (RoCE) or TCP | Reliable transport |

**UEC 1.0 Key Innovations:**
1. **Packet spraying** u2014 Every packet can take any path; reordering at the receiver. Eliminates ECMP hash collisions that plague standard Ethernet.
2. **Credit-based flow control** u2014 Native lossless delivery without PFC. Eliminates the "PFC storm" problems of RoCE.
3. **AI-optimized congestion control** u2014 Designed for incast-heavy AllReduce patterns, not general data center traffic.
4. **In-switch telemetry** u2014 Per-packet latency measurement enables real-time routing decisions.

### 8.4 The Open Fabric Timeline

| Year | Milestone |
|------|-----------|
| 2024 | UALink Consortium formed; UEC founded |
| 2025 | UALink 1.0 spec published; UEC 1.0 spec published |
| 2026 | First UEC Ethernet switches (Broadcom, Cisco); first UALink switch tapeouts |
| 2027 | First UALink-connected accelerator pods (AMD MI400); UEC 1.6T |
| 2028 | Open fabrics reach production parity with NVLink/IB for mainstream workloads |

---

## 9. Optical Interconnect Roadmap: 800G u2192 1.6T

### 9.1 Why Optics Matter

AI cluster networking is fundamentally limited by **optical module technology**. Every 800 Gb/s link between racks requires a pair of optical transceivers that convert electrical signals to light and back. These modules are:
- **Expensive**: $3,000u2013$8,000 per 800G module pair
- **Power-hungry**: 15u201325W per module
- **The #1 cost component** of AI cluster networking (50u201360% of fabric cost)

### 9.2 Optical Module Generations

| Generation | Year | Form Factor | Power per Module | Cost per Module | Technology |
|-----------|------|------------|-----------------|----------------|-----------|
| 400G FR4 | 2020 | QSFP-DD | 10u201312W | $1,000u2013$2,000 | EML, 8u00d7 50G lanes |
| 800G SR8 | 2022 | OSFP | 15u201318W | $2,000u2013$4,000 | VCSEL, 8u00d7 100G lanes |
| **800G DR8/LPO** | **2024u20132025** | **OSFP/DD** | **10u201315W (LPO)** | **$3,000u2013$5,000** | **LPO / DSP-based** |
| 1.6T OSFP-XD | 2026 | OSFP-XD | 20u201325W | $5,000u2013$8,000 (est.) | Linear, 8u00d7 200G lanes |
| **1.6T CPO** | **2027u20132028** | **COPACK** | **8u201312W** | **$2,000u2013$4,000 (est.)** | **Co-packaged optics** |
| 3.2T | 2029+ | TBD | TBD | TBD | CPO / LPO 200G/lane |

### 9.3 LPO vs CPO: The Technology Transition

**Linear Pluggable Optics (LPO) u2014 Shipping today:**
- Replaces power-hungry DSP with linear analog amplifier
- Lower power: 10u201315W vs 18u201322W for DSP-based 800G
- Signal integrity relies on host ASIC SerDes quality
- Slightly shorter reach (500m vs 2km for full DSP)
- Dominant for 800G in AI clusters (intra-rack and intra-row)

**Co-Packaged Optics (CPO) u2014 Pilots 2026, volume 2027u20132028:**
- Integrates optical engine directly into switch ASIC package
- Eliminates electrical trace loss (the "copper wall" at >100 Gb/s per lane)
- Dramatically lower power: 8u201312W per 1.6T port vs 30u201340W for pluggable
- Higher reliability (fewer connectors and electrical interfaces)
- Requires new switch architecture; not backward-compatible
- Key players: Broadcom (Bailly), Cisco (Acacia), Ranovus, Ayar Labs

**Near-Packaged Optics (NPO) u2014 Interim step (2026):**
- Optical engine placed on the same PCB as switch ASIC, but not in the package
- Compromise: better signal integrity than pluggable, easier to manufacture than CPO
- Expected to ship in limited volumes for 1.6T before full CPO transition

### 9.4 Optical Cost Impact on AI Clusters

For a 16K-GPU training cluster using a 2-tier leaf-spine topology:

| Component | Count | Unit Cost | Total Cost | % of Network Cost |
|-----------|-------|-----------|-----------|------------------|
| Optical modules (800G) | 6,400 pairs | $4,000/pair | $25.6M | **55%** |
| InfiniBand switches (NDR) | 320 | $40,000 | $12.8M | 28% |
| NICs (ConnectX-7) | 2,000 | $3,000 | $6.0M | 13% |
| Cables (fiber) | 6,400 | $100 | $0.6M | 1% |
| **Total fabric cost** | | | **$46M** | **100%** |

> **Optical modules are the single largest cost component.** A 16K-GPU cluster spends more on transceivers than on switches and NICs combined.

### 9.5 Optical Technology Roadmap

```
2024          2025           2026          2027          2028
 u2502             u2502              u2502             u2502             u2502
 u251cu2500 800G DSP   u251cu2500 800G LPO   u251cu2500 1.6T LPO  u251cu2500 1.6T CPO  u251cu2500 3.2T R&D
 u2502  (volume)   u2502  (volume)   u2502  (early)    u2502  (volume)  u2502
 u2502             u2502              u2502             u2502             u2502
 u2502             u251cu2500 800G LPO   u251cu2500 NPO pilots u251cu2500 CPO 1.6T  u251cu2500 CPO 3.2T
 u2502             u2502  (AI focus) u2502  (1.6T)     u2502  (AI std)  u2502  (pilots)
 u2502             u2502              u2502             u2502             u2502
 u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500
   50G/lane      100G/lane     200G/lane     200G/lane     400G/lane
```

---

## 10. MoE All-to-All Traffic Patterns

### 10.1 Why MoE is a Networking Nightmare

Mixture-of-Experts (MoE) models like DeepSeek-V3, Mixtral, and Grok introduce an **All-to-All communication** pattern that is fundamentally more demanding than the AllReduce used in dense models.

**Dense model training (AllReduce):**
```
Each GPU sends gradient data to all others u2192 O(nu00b2) traffic
BUT: Can be optimized with ring/hierarchical AllReduce u2192 O(n) traffic per GPU
```

**MoE model training (All-to-All):**
```
Each token must be routed to its assigned expert(s)
Tokens are distributed across GPUs u2192 Every GPU sends to every other GPU
This is O(nu00b2) and CANNOT be reduced to O(n) with ring algorithms
```

### 10.2 MoE Communication Pattern

In a typical MoE architecture:

1. **Dispatch phase**: Tokens are routed from the "attention" GPUs to the "expert" GPUs based on the gating network's routing decisions. This is an All-to-All operation where every GPU sends a different subset of tokens to every other GPU.

2. **Expert computation**: Each expert GPU processes its assigned tokens through the expert MLP.

3. **Combine phase**: Expert outputs are routed back to the original token positions. Another All-to-All operation.

```
Step 1: Dispatch (All-to-All)
  GPU 0 u2500u2500tokensu2500u2500u2192 GPU 0, 1, 2, ..., n-1
  GPU 1 u2500u2500tokensu2500u2500u2192 GPU 0, 1, 2, ..., n-1
  ...
  GPU n u2500u2500tokensu2500u2500u2192 GPU 0, 1, 2, ..., n-1

Step 2: Expert Compute (local)

Step 3: Combine (All-to-All, reverse)
  GPU 0 u2190u2500u2500resultsu2500u2500 GPU 0, 1, 2, ..., n-1
  GPU 1 u2190u2500u2500resultsu2500u2500 GPU 0, 1, 2, ..., n-1
  ...
```

### 10.3 MoE Traffic Volume Estimation

For a MoE model with:
- **Hidden dimension**: d = 7,168 (e.g., DeepSeek-V3)
- **Sequence length**: s = 4,096
- **Batch size per GPU**: b = 2
- **Number of experts**: E = 256
- **Expert parallelism**: EP = 64 GPUs
- **Top-K routing**: k = 8

| Parameter | Value |
|-----------|-------|
| Data sent per All-to-All (dispatch) | b u00d7 s u00d7 d u00d7 sizeof(fp16) u00d7 (1 - 1/EP) u2248 224 MB per GPU |
| Data received per All-to-All (dispatch) | ~224 MB per GPU (evenly distributed) |
| Total All-to-All per layer | ~448 MB u00d7 2 (dispatch + combine) = **896 MB per layer** |
| MoE layers in model | ~58 (DeepSeek-V3) |
| **Total All-to-All per training step** | **~52 GB per GPU** |
| Compare: Dense model AllReduce per step | ~2u20135 GB per GPU (for similar model size) |

> **MoE models generate 10u201320u00d7 more network traffic than dense models** of equivalent quality, making the network fabric the primary bottleneck.

### 10.4 MoE Network Requirements

| Requirement | Dense Model | MoE Model | Impact |
|------------|-------------|-----------|--------|
| **BW per GPU** | 400 Gb/s sufficient | **800 Gb/s+ preferred** | MoE needs 2u00d7 BW |
| **Latency sensitivity** | Medium (overlapped with compute) | **High** (pipeline stalls on All-to-All) | MoE cannot overlap |
| **Tail latency** | Moderate | **Critical** (straggler = full step stall) | MoE needs lossless |
| **Optimal topology** | Ring/hierarchical | **Full bisection** | MoE needs all-to-all BW |
| **SHARP benefit** | u2705 2u20133u00d7 AllReduce | u274c No AllReduce to offload | MoE cannot use SHARP |
| **NVLink domain importance** | Medium | **Very High** (expert parallel within rack) | Keep experts local |

### 10.5 MoE Optimization Strategies

1. **Expert parallelism within NVLink domain**: Place all experts for a group of tokens within the NVLink/NVL72 domain to avoid scale-out traffic.
2. **Expert offloading**: Keep hot experts on all GPUs; offload cold experts to CPU/NVMe.
3. **Token dropping / capacity factor**: Limit the number of tokens per expert to bound worst-case All-to-All traffic.
4. **Communication-computation overlap**: Dispatch tokens for layer N+1 while computing layer N (requires careful pipeline design).
5. **All-to-All collective optimization**: Use NCCL's AlltoAllv with topology-aware scheduling.

---

## 11. Network Topologies for AI Clusters

### 11.1 Common Topologies

| Topology | Structure | Bisection BW | Diameter | Use Case |
|----------|-----------|-------------|---------|----------|
| **Fat Tree (Clos)** | k-ary leaf-spine | Full bisection | 2u20133 hops | Most AI clusters |
| **Torus / Mesh** | Direct-connect grid | O(n) | O(u221an) | TPU pods, some HPC |
| **Dragonfly** | Hierarchical groups | High within-group | 2u20133 global hops | Large HPC clusters |
| **Slim Fly** | Optimized diameter-2 | Near-full bisection | 2 hops | Emerging for AI |
| **HyperX** | Multi-dimensional switched | Configurable | 2u20134 hops | Research clusters |

### 11.2 Two-Tier vs Three-Tier Clos (Fat Tree)

**Two-tier (leaf-spine) u2014 Up to ~2,048 endpoints with 64-port 800G switches:**
```
            u250cu2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2510
            u2502         Spine Layer              u2502
            u2502   [S1] [S2] [S3] ... [S32]      u2502
            u2514u2500u2500u252cu2500u2500u2500u2500u2500u252cu2500u2500u2500u2500u2500u252cu2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u252cu2500u2500u2500u2500u2500u2500u2500u2518
               u2502     u2502     u2502          u2502
            u250cu2500u2500u2534u2500u2500u2500u2500u2500u2534u2500u2500u2500u2500u2500u2534u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2534u2500u2500u2500u2500u2500u2500u2500u2510
            u2502         Leaf Layer               u2502
            u2502   [L1] [L2] [L3] ... [L64]      u2502
            u2514u2500u2500u252cu2500u2500u2500u2500u2500u252cu2500u2500u2500u2500u2500u252cu2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u252cu2500u2500u2500u2500u2500u2500u2500u2518
               u2502     u2502     u2502          u2502
            u250cu2500u2500u2534u2500u2500u2500u2500u2500u2534u2500u2500u2500u2500u2500u2534u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2534u2500u2500u2500u2500u2500u2500u2500u2510
            u2502   [GPU nodes]  (8 GPUs/node)     u2502
            u2514u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2518

Scale: 64 leaf switches u00d7 32 downlinks = 2,048 GPU nodes = 16,384 GPUs
Each leaf has 32 uplinks to 32 spine switches
Full bisection bandwidth
```

**Three-tier (leaf-spine-core) u2014 For >16K GPUs:**
```
            u250cu2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2510
            u2502         Core Layer               u2502
            u2502   [C1] [C2] [C3] ... [C64]      u2502
            u2514u2500u2500u252cu2500u2500u2500u2500u2500u252cu2500u2500u2500u2500u2500u252cu2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u252cu2500u2500u2500u2500u2500u2500u2500u2518
               u2502     u2502     u2502          u2502
            u250cu2500u2500u2534u2500u2500u2500u2500u2500u2534u2500u2500u2500u2500u2500u2534u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2534u2500u2500u2500u2500u2500u2500u2500u2510
            u2502         Spine Layer              u2502
            u2502   [S1] [S2] [S3] ... [S128]     u2502
            u2514u2500u2500u252cu2500u2500u2500u2500u2500u252cu2500u2500u2500u2500u2500u252cu2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u252cu2500u2500u2500u2500u2500u2500u2500u2518
               u2502     u2502     u2502          u2502
            u250cu2500u2500u2534u2500u2500u2500u2500u2500u2534u2500u2500u2500u2500u2500u2534u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2534u2500u2500u2500u2500u2500u2500u2500u2510
            u2502         Leaf Layer               u2502
            u2502   [L1] [L2] [L3] ... [L512]     u2502
            u2514u2500u2500u252cu2500u2500u2500u2500u2500u252cu2500u2500u2500u2500u2500u252cu2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u252cu2500u2500u2500u2500u2500u2500u2500u2518
               u2502     u2502     u2502          u2502
            u250cu2500u2500u2534u2500u2500u2500u2500u2500u2534u2500u2500u2500u2500u2500u2534u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2534u2500u2500u2500u2500u2500u2500u2500u2510
            u2502   [GPU nodes]  (8 GPUs/node)     u2502
            u2514u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2518

Scale: 512 leaf u00d7 32 downlinks = 16,384 nodes = 131,072 GPUs
3 hops end-to-end
```

### 11.3 Topology for MoE Models

MoE All-to-All traffic demands **full bisection bandwidth** u2014 every GPU must be able to send to every other GPU simultaneously without contention. This requires:

1. **Fat tree (Clos) topology** with no oversubscription
2. **Equal-cost multipath** across all spine links
3. **Adaptive routing** (InfiniBand) or packet spraying (UEC) to avoid hot spots
4. **Careful placement** of expert-parallel groups within the same rack/NVLink domain

**MoE-optimized placement strategy:**
```
Rack 1 (NVLink domain): Experts 0-7, all attention layers for tokens 0-T
Rack 2 (NVLink domain): Experts 8-15, all attention layers for tokens T-2T
...
All-to-All only crosses racks for tokens routed to remote experts
Minimizes scale-out traffic to only "overflow" expert assignments
```

### 11.4 Network Sizing Calculator

For a training cluster of **N** GPUs with **M** parameters, using tensor parallelism **TP**, pipeline parallelism **PP**, and data parallelism **DP** (where N = TP u00d7 PP u00d7 DP):

| Parameter | Formula | Example (1T param, 64K GPUs) |
|-----------|---------|-------|
| TP size | u2264 NVLink domain size | 72 (NVL72) |
| PP size | Model layers / micro-batch limit | 8u201316 |
| DP size | N / (TP u00d7 PP) | 64K / (72 u00d7 12) u2248 74 |
| Gradient AllReduce volume | 2 u00d7 M u00d7 sizeof(fp16) / PP per step | 2 u00d7 1T u00d7 2B / 12 u2248 333 GB |
| BW per GPU for gradient sync | AllReduce_vol / (DP u00d7 step_time) | 333 GB / (74 u00d7 2s) u2248 2.25 GB/s |
| Required NIC BW per GPU | u2265 2.25 GB/s = 18 Gb/s u2192 400 Gb/s NIC is sufficient | 400 Gb/s u2705 |

> Note: This is a simplified calculation. Real deployments must account for communication overhead, pipeline bubbles, and MoE expert-parallel traffic.

---

## 12. Networking Vendor Landscape

### 12.1 Major Vendors

| Vendor | Key Products | Strengths | AI Cluster Focus |
|--------|-------------|-----------|-----------------|
| **NVIDIA (Mellanox)** | Quantum-X800 IB, Spectrum-X800 Eth, ConnectX-8, NVLink, BlueField-3 | Full stack; SHARP; GPUDirect; dominant market share | **#1 in AI training networks** |
| **Broadcom** | Tomahawk 5 (Ethernet), Jericho3-AI, UEC silicon, SerDes PHY | Switch ASIC leader; merchant silicon for all Ethernet vendors | Enabling UEC and open Ethernet |
| **Cisco** | Nexus 9800 AI, Silicon One, Acacia (optics) | Enterprise installed base; optical expertise | AI Ethernet + UEC |
| **Arista** | 7800R3, 7060X5, AI-optimized EOS | Cloud-scale Ethernet; software-defined | RoCE/AI Ethernet clusters |
| **AMD (Pensando)** | Pensando DPU, UALink chips | SmartNIC + accelerator interconnect | UALink ecosystem |
| **Juniper (HPE)** | QFX5240, PTX10008 | Campus + data center | AI Ethernet |
| **Intel** | Gaudi NICs, UALink, IPU (Infrastructure PU) | Accelerator + networking combo | UALink + open ecosystem |

### 12.2 Optical Module Vendors

| Vendor | Key Products | Focus |
|--------|-------------|-------|
| **II-VI (Coherent)** | 800G/LPO, 1.6T development | Broadest optical portfolio |
| **Innolight** | 800G DR8/SR8, LPO | Cost-competitive, high volume |
| **Hisense Broadband** | 800G LPO, 1.6T | Aggressive pricing, growing share |
| **Cisco (Acacia)** | 800G DSP, CPO (Cortina) | Integrated optics + DSP |
| **Broadcom** | Bailly CPO engine | Co-packaged optics leader |
| **Ayar Labs** | TeraPHY optical I/O | In-package optical interconnect |
| **Ranovus** | CPO engines, 800G modules | CPO for AI switches |

### 12.3 Software & Collective Libraries

| Library | Vendor | Supported Fabrics | Key Feature |
|---------|--------|------------------|-------------|
| **NCCL** | NVIDIA | NVLink, InfiniBand, RoCE | Dominant; optimized for NVIDIA GPUs |
| **RCCL** | AMD | Infinity Fabric, RoCE, IB | AMD GPU equivalent of NCCL |
| **OneCCL** | Intel | Ethernet, IB, CXL | For Intel accelerators (Gaudi) |
| **MSCCLang** | Microsoft Research | Any (programmable) | Custom collective algorithm synthesis |
| **TACCL** | Meta Research | Any (programmable) | Topology-aware collective optimization |
| **cuQuantum** | NVIDIA | NVLink, IB | Quantum simulation communication |

---

## 13. Cost Analysis: Network Fabric TCO

### 13.1 Network Cost per GPU

| Cluster Size | Fabric Type | Network Cost per GPU | % of Total System Cost |
|-------------|-------------|---------------------|----------------------|
| 64 GPUs (8 nodes) | NVLink + RoCE | $2,000u2013$4,000 | 3u20135% |
| 512 GPUs (64 nodes) | InfiniBand NDR | $5,000u2013$8,000 | 5u20138% |
| 4K GPUs (512 nodes) | InfiniBand NDR | $8,000u2013$12,000 | 7u201310% |
| 16K GPUs | InfiniBand NDR/XDR | $12,000u2013$18,000 | 10u201315% |
| 64K GPUs | InfiniBand XDR | $18,000u2013$25,000 | 12u201318% |
| 100K+ GPUs | InfiniBand XDR + optics | $25,000u2013$35,000 | 15u201320% |

> **Network cost scales super-linearly with cluster size** because larger clusters require more spine/core layers and longer optical cable runs.

### 13.2 Total Fabric TCO Breakdown (16K-GPU Cluster, InfiniBand)

| Cost Component | Capital (CAPEX) | Annual Operating (OPEX) | 3-Year TCO |
|---------------|----------------|------------------------|------------|
| InfiniBand switches | $12.8M | $0.5M (power + cooling) | $14.3M |
| NICs (ConnectX-7) | $6.0M | $0.1M | $6.3M |
| Optical modules (800G) | $25.6M | $2.0M (replacements, failures) | $31.6M |
| Fiber cables | $0.6M | $0.2M (maintenance) | $1.2M |
| Network management software | $1.0M | $0.5M (licenses) | $2.5M |
| Network engineering staff | u2014 | $2.0M (4 FTEs) | $6.0M |
| **Total** | **$46.0M** | **$5.3M/yr** | **$61.9M** |
| **Per GPU** | **$2,875** | **$331/yr** | **$3,869** |

### 13.3 InfiniBand vs RoCE TCO Comparison (16K GPUs)

| Component | InfiniBand NDR | RoCE v2 (Ethernet) | Delta |
|-----------|---------------|---------------------|-------|
| Switches | $12.8M | $8.0M | -37% |
| NICs | $6.0M | $4.0M | -33% |
| Optical modules | $25.6M | $25.6M | 0% |
| Cables | $0.6M | $0.5M | -17% |
| Tuning & optimization (one-time) | $0.5M | $2.0M | +300% |
| **Network CAPEX** | **$45.5M** | **$40.1M** | **-12%** |
| Annual OPEX (power + staff) | $3.5M | $4.5M | +29% |
| **3-Year TCO** | **$56.0M** | **$53.6M** | **-4%** |
| **Effective training throughput** | 100% (baseline) | 85u201395% | -5u201315% |

> **Conclusion:** RoCE v2 saves ~12% on CAPEX but may cost 5u201315% in training throughput. The TCO gap narrows to ~4% over 3 years. InfiniBand remains the superior choice for performance-critical training at scale.

---

## 14. Future Outlook 2026u20132028

### 14.1 Technology Roadmap

| Timeline | Scale-Up | Scale-Out | Optical |
|----------|----------|-----------|---------|
| **2026 H1** | NVL72 production; NVL576 announced | XDR 800 Gb/s IB shipping; UEC 1.0 switches | 800G LPO volume; 1.6T LPO samples |
| **2026 H2** | UALink 1.0 first silicon tapeouts | UEC 1.0 in production clusters | NPO pilot deployments |
| **2027** | UALink-connected MI400 pods | UEC + SHARP-equivalent for Ethernet | 1.6T CPO volume production |
| **2028** | NVLink 6 (rumored 3.6 TB/s); UALink 2.0 | 1.6T IB (XXDR?); UEC 1.6T | 3.2T optical R&D; CPO standard |

### 14.2 Key Predictions

1. **Open fabrics will gain 20u201330% market share by 2028**, but NVIDIA will remain dominant (>60%) due to software ecosystem maturity.
2. **CPO will be mandatory for 1.6T+ links** u2014 pluggable optics hit a power wall at 200G/lane. The CPO transition will be the biggest optical disruption since the 100Gu2192400G transition.
3. **MoE will drive network demand disproportionately** u2014 MoE models are growing faster than dense models, and their All-to-All traffic is 10u201320u00d7 more network-intensive.
4. **The NVLink domain will expand to 256u2013576 GPUs** by 2027 (NVSwitch 4 / NVL576), reducing scale-out traffic for models under 1T parameters.
5. **UEC will replace RoCE v2** as the standard AI Ethernet u2014 UEC's native lossless and packet-spraying eliminate the need for PFC tuning.
6. **Signal integrity becomes the next bottleneck** u2014 at 200G/lane and beyond, channel loss, crosstalk, and thermal management dominate optical design.

### 14.3 Emerging Technologies

| Technology | Description | Timeline | Impact |
|-----------|-------------|----------|--------|
| **Co-Packaged Optics (CPO)** | Optical engine inside switch ASIC package | 2027u20132028 volume | 2u20133u00d7 power efficiency; enables 1.6T+ |
| **Silicon Photonics Switching** | Optical switching without O/E/O conversion | 2028+ research | Eliminates electrical bottleneck entirely |
| **Wireless (Free-Space Optics)** | Laser links between racks (no fiber) | 2027+ pilots | Reduces cabling cost and complexity |
| **CXL 3.0 Memory Fabric** | Coherent memory pooling across nodes | 2026u20132027 | Enables disaggregated memory for KV caches |
| **UALink 2.0** | Higher lane speed, larger domains | 2028 spec | Scale-up competitive with NVLink 6 |

---

## 15. Key Takeaways

1. **The network is now the bottleneck.** GPU compute doubles every generation, but interconnect bandwidth only doubles. Communication overhead can consume 30u201350% of training time for large models.

2. **Expand the NVLink domain.** The single highest-impact networking decision is maximizing the NVLink (or UALink) domain size. Moving from 8-GPU to 72-GPU NVLink domains eliminates scale-out traffic for most tensor-parallel operations.

3. **InfiniBand for performance; Ethernet for cost.** InfiniBand's SHARP, adaptive routing, and lossless guarantee make it 5u201315% faster for training at scale. RoCE/UEC is 10u201330% cheaper but requires expert tuning.

4. **MoE changes everything.** MoE models generate 10u201320u00d7 more network traffic than dense models and cannot use SHARP or ring-based optimizations. MoE-heavy clusters need full-bisection-bandwidth fat trees and the fastest available NICs.

5. **Optical modules are the hidden cost.** At $3,000u2013$5,000 per 800G pair, optical transceivers are 50u201360% of the network fabric cost. The CPO transition (2027u20132028) will be critical for cost and power efficiency.

6. **Open fabrics are coming but not here yet.** UALink and UEC will challenge NVIDIA's NVLink/InfiniBand duopoly, but production parity is 2u20133 years away. Plan for a heterogeneous future.

7. **Network cost scales super-linearly.** Going from 16K to 64K GPUs more than doubles the per-GPU network cost due to additional switching tiers and longer cable runs.

---

## References & Further Reading

1. NVIDIA GB200 NVL72 Architecture Whitepaper u2014 NVIDIA, 2024
2. UALink 1.0 Specification u2014 UALink Consortium, 2025
3. Ultra Ethernet Consortium 1.0 Specification u2014 UEC / Linux Foundation, 2025
4. "MoNTA: Enabling Large-Scale Mixture-of-Experts Training via Network-Traffic-Aware Parallelism" u2014 arxiv:2411.00662, 2024
5. NVIDIA SHARP Technology Overview u2014 NVIDIA Developer Documentation
6. "RoCEv2 vs InfiniBand for AI Data Centers" u2014 various vendor whitepapers, 2024u20132025
7. IEEE 802.3df (800G Ethernet) and 802.3dj (1.6T Ethernet) Standards
8. "Co-Packaged Optics: The Next Frontier in Data Center Networking" u2014 LightCounting, 2025
9. NCCL (NVIDIA Collective Communications Library) Documentation u2014 NVIDIA
10. "Optical Interconnect Roadmap for AI Infrastructure" u2014 CIG (Consortium for On-Board Optics), 2025

---

> Navigation: [u2190 AI Infra Overview](ai_infra_overview.md) | [Compute Layer u2192](01_compute_layer.md) | [Storage & Data u2192](03_storage_data.md)
