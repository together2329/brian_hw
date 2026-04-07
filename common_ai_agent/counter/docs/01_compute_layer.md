# Compute Layer u2014 GPU Architecture & Trends

> **Document:** 01 of 09 u00b7 AI Infrastructure Series  
> **Last Updated:** April 2026  
> **Scope:** AI accelerators (GPUs, TPUs, custom ASICs), rack-scale systems, cloud pricing, deployment models  
> **Previous:** [AI Infra Overview](ai_infra_overview.md) u00b7 **Next:** [Networking & Interconnect](02_networking_interconnect.md)

---

## Table of Contents

1. [Compute Layer Overview](#1-compute-layer-overview)
2. [NVIDIA GPU Roadmap](#2-nvidia-gpu-roadmap)
3. [AMD Instinct Accelerator Family](#3-amd-instinct-accelerator-family)
4. [Google TPU (Trillium v6)](#4-google-tpu-trillium-v6)
5. [Custom Silicon u2014 Hyperscaler ASICs](#5-custom-silicon--hyperscaler-asics)
6. [Rack-Scale Systems & AI Factories](#6-rack-scale-systems--ai-factories)
7. [GPU Cloud Pricing Landscape (2026)](#7-gpu-cloud-pricing-landscape-2026)
8. [Deployment Models: Cloud vs. On-Prem vs. Hybrid](#8-deployment-models-cloud-vs-on-prem-vs-hybrid)
9. [Training vs. Inference Compute Economics](#9-training-vs-inference-compute-economics)
10. [Key Trends & Strategic Implications](#10-key-trends--strategic-implications)

---

## 1. Compute Layer Overview

The compute layer is the foundational building block of AI infrastructure. It encompasses all accelerator hardware u2014 GPUs, TPUs, and custom ASICs u2014 responsible for the massively parallel matrix operations that underpin neural network training and inference.

### Why the Compute Layer Matters

| Factor | Detail |
|--------|--------|
| **Dominant cost driver** | GPU/accelerator costs represent 40u201360% of total AI infrastructure TCO |
| **Performance bottleneck** | Compute-bound (training) vs. memory-bound (inference) u2014 hardware choice dictates throughput |
| **Vendor lock-in risk** | NVIDIA CUDA ecosystem dominance (~80%+ AI GPU market share) creates switching costs |
| **Rapid iteration cycle** | New GPU generations every 18u201324 months; 2u20133u00d7 performance jumps per generation |
| **Power-density challenge** | Rack power growing from 120 kW u2192 600 kW (2027) u2192 1 MW (prototype), driven by GPU TDPs |

### Accelerator Landscape (2025u20132026)

| Vendor | Flagship Product | Architecture | Memory | Market Position |
|--------|-----------------|--------------|--------|-----------------|
| **NVIDIA** | B200 / B300 (Blackwell/Ultra) | Blackwell | 192u2013288 GB HBM3e | Dominant (~80%+) |
| **AMD** | MI300X / MI355X | CDNA 3 | 192 GB HBM3 | Challenger (growing) |
| **Google** | TPU v6 (Trillium) | Custom ASIC | Undisclosed (2u00d7 v5e) | Internal + GCP only |
| **Amazon** | Trainium2 / Inferentia3 | Custom ASIC | Undisclosed | AWS-internal |
| **Meta** | MTIA v2 / v3 | Custom ASIC | Undisclosed | Internal inference |
| **Microsoft** | Maia 100 | Custom ASIC | Undisclosed | Azure-internal |
| **Intel** | Gaudi 3 | Habana | 128 GB HBM2e | Challenger (limited) |

---

## 2. NVIDIA GPU Roadmap

### 2.1 NVIDIA Hopper (H100 / H200) u2014 The Incumbent

The Hopper generation was the workhorse of the 2023u20132025 AI buildout. Over 3.5 million H100 GPUs were deployed globally by early 2025.

| Specification | H100 SXM5 | H200 SXM |
|---------------|-----------|----------|
| **Architecture** | Hopper (H100) | Hopper (H200) |
| **GPU Memory** | 80 GB HBM3 | 141 GB HBM3e |
| **Memory Bandwidth** | 3.35 TB/s | 4.8 TB/s |
| **FP8 Dense (TFLOPS)** | 1,979 | ~1,979 |
| **FP16/BF16 Dense (TFLOPS)** | 989 | ~989 |
| **FP32 (TFLOPS)** | 67 | ~67 |
| **TDP** | 700 W | 700 W |
| **NVLink Bandwidth** | 900 GB/s | 900 GB/s |
| **PCIe** | Gen5 u00d716 | Gen5 u00d716 |
| **Production** | 2023u2013present | 2024u2013present |

**Key Innovation u2014 Transformer Engine:** Hopper introduced dedicated hardware for dynamic FP8/FP16 mixed-precision, automatically scaling precision per layer to maximize throughput without accuracy loss.

### 2.2 NVIDIA Blackwell (B200) u2014 Current Flagship

Blackwell represents a generational leap beyond Hopper, with a fundamentally new die architecture (two reticle-sized dies in a single unified GPU).

| Specification | B200 SXM |
|---------------|----------|
| **Architecture** | Blackwell |
| **GPU Memory** | 192 GB HBM3e |
| **Memory Bandwidth** | 8 TB/s |
| **FP4 Dense (PFLOPS)** | 9.0 |
| **FP8 / FP6 Dense (PFLOPS)** | 4.5 |
| **FP16 / BF16 Dense (TFLOPS)** | 2,250 |
| **FP32 (TFLOPS)** | 90 |
| **TDP** | 1,000 W |
| **NVLink Bandwidth** | 1.8 TB/s (NVLink 5) |
| **Form Factor** | SXM (dual-die, single package) |

**Key Innovations:**
- **Dual-die design:** Two GPU dies connected by 10 TB/s die-to-die link, acting as a single CUDA-visible GPU
- **Second-generation Transformer Engine:** Supports FP4 and FP6 precision natively u2014 2u00d7 throughput vs. FP8 for inference
- **5th-gen NVLink:** 1.8 TB/s bidirectional, enabling 72-GPU NVLink domains
- **Confidential computing:** Hardware-level encryption for multi-tenant cloud deployments
- **RAS engine:** Built-in reliability, availability, and serviceability for data center reliability

### 2.3 NVIDIA Blackwell Ultra (B300) u2014 The Push to Limits

Announced at GTC 2025 (March), the B300 is a binned, optimized version of Blackwell u2014 higher clocks, more memory, and improved thermal design. It shipped in January 2026 and represents NVIDIA's most powerful single GPU.

| Specification | B300 SXM | B200 SXM | Delta |
|---------------|----------|----------|-------|
| **Architecture** | Blackwell Ultra | Blackwell | u2014 |
| **GPU Memory** | 288 GB HBM3e | 192 GB HBM3e | +50% |
| **Memory Bandwidth** | 8 TB/s | 8 TB/s | Same |
| **FP4 Dense (PFLOPS)** | 14.0 | 9.0 | +56% |
| **FP8 Dense (PFLOPS)** | 7.0 | 4.5 | +56% |
| **FP16 Dense (TFLOPS)** | 3,500 | 2,250 | +56% |
| **TDP** | ~1,200 W | 1,000 W | +20% |
| **NVLink Bandwidth** | 1.8 TB/s | 1.8 TB/s | Same |

**Key Points:**
- **Target workload:** Reasoning models (DeepSeek R1, OpenAI o-series) that demand more compute per query
- **Form factors:** B300 SXM6, B300 NVL16 server, GB300 NVL72 rack
- **DGX SuperPod:** 8 u00d7 NVL72 racks = 576 B300 GPUs, 300 TB HBM3e, 11.5 EFLOPS FP4
- **Cloud availability:** Major providers listed instances within weeks of January 2026 ship date

### 2.4 NVIDIA GPU Generational Comparison

| Spec | H100 | H200 | B200 | B300 |
|------|------|------|------|------|
| **Memory** | 80 GB | 141 GB | 192 GB | 288 GB |
| **Mem BW** | 3.35 TB/s | 4.8 TB/s | 8 TB/s | 8 TB/s |
| **FP8 (PFLOPS)** | 2.0 | 2.0 | 4.5 | 7.0 |
| **FP4 (PFLOPS)** | N/A | N/A | 9.0 | 14.0 |
| **NVLink** | 900 GB/s | 900 GB/s | 1.8 TB/s | 1.8 TB/s |
| **TDP** | 700 W | 700 W | 1,000 W | ~1,200 W |
| **Shipped** | 2023 | 2024 | 2024 Q4 | 2026 Q1 |

---

## 3. AMD Instinct Accelerator Family

### 3.1 AMD MI300X

The MI300X is AMD's flagship AI accelerator, leveraging a chiplet-based design with CDNA 3 architecture. It was the first GPU to challenge NVIDIA with 192 GB of HBM memory.

| Specification | MI300X |
|---------------|--------|
| **Architecture** | CDNA 3 (chiplet) |
| **GPU Memory** | 192 GB HBM3 |
| **Memory Bandwidth** | 5.3 TB/s |
| **FP8 Dense (TFLOPS)** | 1,302 (without sparsity) |
| **FP16/BF16 Dense (TFLOPS)** | 654 |
| **FP32 (TFLOPS)** | 164 |
| **Compute Units** | 304 CUs |
| **TDP** | 750 W |
| **Interconnect** | Infinity Fabric (256 GB/s GPU-to-GPU) |
| **Form Factor** | OAM |
| **Production** | 2024u2013present |

**Key Innovations:**
- **Chiplet architecture:** Multiple compute dies stacked on a shared memory cache u2014 improves yield and scalability vs. monolithic designs
- **192 GB HBM3:** Largest GPU memory at launch, enabling single-GPU inference for 70B+ models
- **Infinity Fabric:** Proprietary high-speed interconnect for multi-GPU scaling
- **ROCm 6.x:** Open software stack; growing compatibility with PyTorch, JAX, and major ML frameworks

### 3.2 Real-World Performance Gap

A comprehensive study by Celestial AI (arXiv:2510.27583) benchmarked MI300X against H100/H200 for LLM inference:

| Metric | MI300X vs H100 | Notes |
|--------|---------------|-------|
| **Theoretical FP8 compute** | 1.5u00d7 advantage | MI300X has higher peak FLOPS |
| **Realized LLM inference** | 37u201366% of H100/H200 | Significant gap between peak and real-world |
| **Memory bandwidth utilization** | Lower than expected | Software maturity is the key bottleneck |
| **Interconnect efficiency** | Competitive on paper | Infinity Fabric not yet matching NVLink in practice |

**Takeaway:** AMD hardware is competitive on paper but the software ecosystem (ROCm vs. CUDA) remains the primary adoption barrier. The gap is narrowing with each ROCm release.

### 3.3 AMD Future Roadmap

| Product | Expected | Key Improvement |
|---------|----------|-----------------|
| **MI325X** | 2025 H2 | Enhanced CDNA 3, improved memory |
| **MI355X** | 2026 | CDNA 4 architecture, HBM3e |
| **MI400** | 2027 | Next-gen architecture, rack-scale design |

---

## 4. Google TPU (Trillium v6)

Google's Tensor Processing Units represent the most mature custom ASIC program for AI. The sixth-generation Trillium TPU was announced at Google I/O 2024 and is now deployed for Gemini model training and GCP customer workloads.

### 4.1 Trillium TPU v6 Specifications

| Specification | Trillium (TPU v6) | TPU v5e | Delta |
|---------------|-------------------|---------|-------|
| **Peak compute per chip** | 4.7u00d7 TPU v5e | Baseline | +370% |
| **HBM capacity** | 2u00d7 TPU v5e | Baseline | +100% |
| **HBM bandwidth** | 2u00d7 TPU v5e | Baseline | +100% |
| **ICI bandwidth** | 2u00d7 TPU v5e | Baseline | +100% |
| **Energy efficiency** | 67% better | Baseline | -67% energy/OP |
| **Max pod size** | 256 TPUs | 256 TPUs | Same |
| **SparseCore** | 3rd generation | 2nd generation | Enhanced embeddings |

### 4.2 Key Architectural Features

- **Expanded Matrix Multiply Units (MXUs):** Larger systolic arrays for higher throughput per clock
- **Third-generation SparseCore:** Dedicated hardware for processing ultra-large embedding tables u2014 critical for recommendation systems and ranking models
- **Interchip Interconnect (ICI):** Doubled bandwidth enables scaling to tens of thousands of chips across pods; custom optical ICI interconnects and Google Jupiter networking allow building-scale supercomputers
- **Multi-slice technology:** Scales beyond single pods using Titanium Intelligence Processing Units (IPUs)

### 4.3 TPU Generational Trajectory

| Generation | Year | Key Improvement |
|------------|------|-----------------|
| TPU v1 | 2015 | Inference only (AlphaGo era) |
| TPU v2 | 2017 | Training support, 180 TFLOPS |
| TPU v3 | 2018 | Liquid cooling, 2u00d7 v2 |
| TPU v4 | 2020 | Major leap, custom interconnect |
| TPU v5e | 2023 | Cost-efficient inference |
| TPU v5p | 2023 | Peak training performance |
| **TPU v6 (Trillium)** | **2024u20132025** | **4.7u00d7 compute, 2u00d7 memory/bandwidth** |

### 4.4 TPU Availability

TPUs are available exclusively through Google Cloud Platform (Vertex AI) and are used internally for Gemini model training. They are not available for on-premises deployment, which limits adoption to GCP-committed organizations.

---

## 5. Custom Silicon u2014 Hyperscaler ASICs

Hyperscalers are investing billions in custom silicon to reduce dependency on NVIDIA and optimize for their specific workload patterns.

### 5.1 Custom Silicon Comparison

| Vendor | Chip | Purpose | Key Feature | Status |
|--------|------|---------|-------------|--------|
| **Amazon** | Trainium2 | Training | 20+ ExaFLOPS clusters | Production (AWS) |
| **Amazon** | Inferentia3 | Inference | Low-latency, high-throughput | Production (AWS) |
| **Amazon** | Graviton4 | General compute | ARM-based, AI-optimized I/O | Production |
| **Meta** | MTIA v2 | Inference | Recommendation + ranking | Production (internal) |
| **Meta** | MTIA v3 | Training + Inference | Higher memory bandwidth | Sampling |
| **Microsoft** | Maia 100 | Training + Inference | Azure-optimized | Limited deployment |
| **Intel** | Gaudi 3 | Training | 128 GB HBM2e, open software | Limited adoption |
| **SambaNova** | SN40L | Training + Inference | Reconfigurable dataflow architecture | Niche deployment |
| **Cerebras** | WSE-3 | Training | Wafer-scale (4 trillion transistors) | Niche (research) |

### 5.2 The Custom Silicon Rationale

| Motivation | Detail |
|------------|--------|
| **Cost reduction** | Custom ASICs cost 30u201350% less per FLOP than NVIDIA GPUs at volume |
| **Supply independence** | Reduce vulnerability to NVIDIA allocation constraints |
| **Workload specialization** | Optimize for inference patterns, recommendation models, or specific architectures |
| **Power efficiency** | Custom designs achieve 2u20133u00d7 better FLOPS/watt for target workloads |
| **Ecosystem control** | Vertical integration from chip to cloud platform |

### 5.3 Limitations

- **Software ecosystem immaturity:** Custom chips lack CUDA's 15+ year ecosystem advantage
- **Limited flexibility:** ASICs optimized for current workloads may not handle next-gen architectures
- **Scale requirements:** Custom silicon is only cost-effective at hyperscaler volumes (>100K units)
- **Talent scarcity:** Chip design expertise is concentrated among a small number of engineers

---

## 6. Rack-Scale Systems & AI Factories

The industry is shifting from individual GPU servers to integrated rack-scale systems where hundreds of GPUs operate as a single computational unit.

### 6.1 NVIDIA GB200 NVL72

The GB200 NVL72 is NVIDIA's flagship rack-scale system, connecting 36 Grace CPUs and 72 Blackwell GPUs in a single liquid-cooled rack.

| Specification | GB200 NVL72 |
|---------------|-------------|
| **GPUs** | 72 u00d7 NVIDIA Blackwell (B200) |
| **CPUs** | 36 u00d7 NVIDIA Grace (ARM Neoverse V2) |
| **Total GPU Memory** | 13.4 TB HBM3e |
| **Memory Bandwidth** | 576 TB/s (aggregate) |
| **FP4 Compute** | 1.44 EFLOPS |
| **FP8 Compute** | 720 PFLOPS |
| **NVLink Domain** | 72 GPUs (single fabric) |
| **Total NVLink BW** | 130 TB/s (rack-level) |
| **Rack Size** | 48 RU |
| **Cooling** | Direct liquid cooling (DLC) |
| **Networking** | BlueField-3 DPUs, Spectrum-X / Quantum-2 |

**Architecture Highlights:**
- **Grace Blackwell Superchip:** 2 u00d7 B200 GPUs + 1 u00d7 Grace CPU per package, connected by NVLink-C2C at 900 GB/s
- **Unified memory:** All 72 GPUs share a single address space u2014 models up to ~13 TB fit entirely in GPU memory
- **NVLink spine:** Full all-to-all connectivity across 72 GPUs eliminates the PCIe bottleneck
- **Liquid cooling required:** Rack TDP exceeds 120 kW; air cooling is not viable

### 6.2 NVIDIA GB300 NVL72 & DGX SuperPod

The GB300 NVL72 is the Blackwell Ultra variant, featuring B300 GPUs:

| Specification | GB300 NVL72 | DGX SuperPod (8 u00d7 NVL72) |
|---------------|-------------|--------------------------|
| **GPUs** | 72 u00d7 B300 | 576 u00d7 B300 |
| **Total Memory** | ~20 TB HBM3e | ~300 TB HBM3e |
| **FP4 Compute** | ~2.0 EFLOPS | ~11.5 EFLOPS |
| **Grace CPUs** | 36 | 288 |
| **Target** | 200B+ training, 671B inference | Frontier model training |

### 6.3 GB200 NVL72 vs. 8u00d7GPU Server Comparison

| System | GPU Memory | NVLink BW/GPU | Best For | Cloud Price/GPU-hr |
|--------|-----------|---------------|----------|---------------------|
| **8u00d7H100 SXM5** | 640 GB | 900 GB/s | Sub-70B models, cost-sensitive | $2.00u2013$6.88 |
| **8u00d7B200 SXM** | 1.44 TB | 1.8 TB/s | 70Bu2013100B models, FP4 workloads | $4.50u2013$12.00 |
| **GB200 NVL72 rack** | 13.4 TB | 1.8 TB/s (full fabric) | 200B+ training, 671B inference | $10.50u2013$27.00 |
| **GB300 NVL72 rack** | ~20 TB | 1.8 TB/s (full fabric) | Reasoning models, frontier training | Est. $14u2013$30 |

### 6.4 The "AI Factory" Concept

NVIDIA's vision is the **AI Factory** u2014 purpose-built data centers designed around rack-scale systems:

- **Input:** Data + energy
- **Output:** Intelligence (tokens, embeddings, predictions)
- **Metric:** Tokens/watt or FLOPS/dollar, not traditional DC metrics
- **Scale:** 100K+ GPU deployments (e.g., xAI Colossus: 100K GPUs in 122 days; Meta: 350K+ H100 cluster)

---

## 7. GPU Cloud Pricing Landscape (2026)

### 7.1 Pricing by GPU Model (On-Demand, March 2026)

| GPU Model | VRAM | Neo-Cloud ($/GPU-hr) | Hyperscaler ($/GPU-hr) | Spot ($/GPU-hr) |
|-----------|------|-----------------------|------------------------|-----------------|
| **H100 SXM5** | 80 GB | $1.25u2013$3.00 | $6.88u2013$14.90 | $0.50u2013$1.50 |
| **H200 SXM** | 141 GB | $2.50u2013$4.50 | $8.00u2013$16.00 | $1.00u2013$2.50 |
| **B200 SXM** | 192 GB | $4.50u2013$8.00 | $12.00u2013$22.00 | $2.50u2013$5.00 |
| **B300 SXM** | 288 GB | $4.95u2013$10.00 | $15.00u2013$27.00 | $3.00u2013$6.00 |
| **A100 80GB** | 80 GB | $0.80u2013$2.00 | $3.50u2013$6.00 | $0.40u2013$1.00 |
| **RTX 4090** | 24 GB | $0.30u2013$0.60 | N/A (consumer) | $0.15u2013$0.30 |
| **L40S** | 48 GB | $1.00u2013$2.00 | $3.00u2013$5.00 | $0.50u2013$1.00 |

*Sources: Spheron, Verda (DataCrunch), getdeploying.com, AWS/Azure/GCP public pricing, March 2026*

### 7.2 Key Pricing Observations

1. **Hyperscaler premium:** AWS, Azure, GCP charge 3u20136u00d7 more than neo-clouds (CoreWeave, Lambda, Spheron, TensorWave) for the same GPU hardware
2. **Blackwell pricing still maturing:** B200/B300 pricing is higher due to limited supply and high demand; expect 30u201350% price drops by late 2026
3. **Spot pricing enables massive savings:** Spot/preemptible instances offer 50u201375% discounts for fault-tolerant workloads (training with checkpointing)
4. **Reserved pricing:** 1-year commitments typically yield 30u201340% savings vs. on-demand; 3-year commitments yield 50u201360%

### 7.3 Provider Comparison

| Provider | Type | H100 $/hr | B200 $/hr | Strengths |
|----------|------|-----------|-----------|-----------|
| **AWS** | Hyperscaler | ~$6.88 | ~$15.00+ | Largest ecosystem, EFA networking |
| **Azure** | Hyperscaler | ~$12.29 | ~$18.00+ | Enterprise integration, OpenAI |
| **GCP** | Hyperscaler | ~$5.00 | ~$14.00+ | TPU access, A3 Mega instances |
| **CoreWeave** | Neo-cloud | ~$2.50 | ~$6.00 | GPU-first, Slurm-native, fast provisioning |
| **Lambda Labs** | Neo-cloud | ~$1.50 | ~$5.00 | Developer-friendly, simple pricing |
| **Spheron** | Marketplace | ~$2.01 | ~$6.03 | Decentralized, competitive rates |
| **TensorWave** | Neo-cloud | ~$2.50 | ~$6.50 | AMD MI300X specialist |
| **Vast.ai** | Marketplace | ~$1.25 | N/A | Cheapest consumer/community GPUs |
| **RunPod** | Marketplace | ~$1.70 | ~$5.50 | Serverless GPU, easy deployment |

---

## 8. Deployment Models: Cloud vs. On-Prem vs. Hybrid

### 8.1 Model Comparison

| Factor | Cloud (Hyperscaler) | Cloud (Neo-cloud) | On-Premises | Hybrid |
|--------|---------------------|-------------------|-------------|--------|
| **Upfront cost** | $0 | $0 | $5Mu2013$50M+ (GPU cluster) | $2Mu2013$20M |
| **Time to deploy** | Minutesu2013Hours | Minutesu2013Hours | 6u201318 months | 3u201312 months |
| **GPU access** | Shared / Reserved | Shared / Dedicated | Dedicated | Mixed |
| **Networking** | Managed (EFA/IB) | Varies | Self-managed | Self + managed |
| **Data sovereignty** | Limited | Varies | Full control | Partial |
| **Scalability** | Elastic | Semi-elastic | Fixed capacity | Burst to cloud |
| **Software stack** | Managed (SageMaker, Vertex) | Basic (Slurm, K8s) | Full control | Mixed |
| **Best for** | Experimentation, startups, bursty workloads | Cost-sensitive training | Production inference, data-sensitive, sovereign AI | Enterprise production |

### 8.2 Total Cost of Ownership (TCO) Analysis

Based on Lenovo's 2026 TCO analysis for generative AI infrastructure:

| Workload Profile | Cloud (3-yr) | On-Prem (3-yr) | Break-Even |
|------------------|-------------|----------------|------------|
| **Small (8u00d7H100, light use)** | $1.2M | $2.5M | Cloud cheaper (utilization <40%) |
| **Medium (32u00d7H100, moderate)** | $5.0M | $6.0M | ~60% utilization |
| **Large (128u00d7H100, heavy)** | $18M | $12M | On-prem 35% cheaper at >70% utilization |
| **Inference (continuous, 24/7)** | $8M/yr | $4M/yr | On-prem always cheaper |

**Key Insight:** On-premises infrastructure becomes cost-effective when GPU utilization exceeds 60u201370% consistently. For 24/7 inference workloads, on-prem is typically 40u201350% cheaper over a 3-year horizon.

### 8.3 The Hybrid Strategy

Most enterprises are converging on a hybrid approach:

```
u250cu2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2510
u2502                    HYBRID AI INFRA                           u2502
u2502                                                             u2502
u2502  u250cu2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2510  u250cu2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2510  u250cu2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2510      u2502
u2502  u2502   ON-PREM    u2502  u2502   CLOUD      u2502  u2502  NEO-CLOUD   u2502      u2502
u2502  u2502  (Production u2502  u2502  (Burst      u2502  u2502  (Cost-      u2502      u2502
u2502  u2502   inference, u2502  u2502   training,  u2502  u2502   sensitive  u2502      u2502
u2502  u2502   sensitive  u2502  u2502   experiment-u2502  u2502   training,  u2502      u2502
u2502  u2502   data)      u2502  u2502   ation)     u2502  u2502   spot)      u2502      u2502
u2502  u2514u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2518  u2514u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2518  u2514u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2518      u2502
u2502                                                             u2502
u2502  Unified by: Kubernetes u00b7 Ray u00b7 MLflow u00b7 Terraform          u2502
u2514u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2518
```

---

## 9. Training vs. Inference Compute Economics

### 9.1 Compute Requirements by Phase

| Phase | Compute Pattern | Memory Pattern | Network Pattern |
|-------|----------------|----------------|-----------------|
| **Pre-training** | Compute-bound (weeksu2013months) | Model params + optimizer states | AllReduce, heavy collective ops |
| **Post-training (RLHF/RL)** | Mixed compute/memory | Growing (reward models, value heads) | Moderate |
| **Inference (offline batch)** | Memory-bandwidth-bound | KV cache dominates (grows with seq len) | Low |
| **Inference (online serving)** | Latency-critical, memory-bound | KV cache + batching overhead | Moderate (speculative decoding) |

### 9.2 Cost Distribution Shift (2024 u2192 2026+)

| Phase | 2024 Share | 2026+ Share | Trend |
|-------|-----------|------------|-------|
| Pre-training | ~50% | ~20% | u2193 One-time cost, amortized |
| Post-training (RLHF/RL/DPO) | ~10% | ~25% | u2191u2191 RL-based post-training approaching 0.5u00d7 pre-train compute |
| Inference / Serving | ~40% | ~55% | u2191u2191 Dominant u2014 billions of requests daily, agentic AI |

### 9.3 GPU Selection by Workload

| Workload | Recommended GPU | Rationale |
|----------|----------------|-----------|
| **Pre-training 70B+ models** | B200 / B300 (NVLink cluster) | Need maximum FLOPS + NVLink bandwidth for AllReduce |
| **Pre-training < 30B models** | H100 / H200 cluster | Sufficient compute, better availability, lower cost |
| **RLHF / post-training** | H200 / B200 | Large memory for reward model + policy model simultaneously |
| **Batch inference (70B)** | H200 (141 GB) | Model fits in single GPU, maximize bandwidth |
| **Batch inference (200B+)** | B200 / B300 (TP) | Tensor parallelism across 2u20134 GPUs |
| **Online serving (low latency)** | H100 / B200 + speculative decoding | Latency-optimized configurations |
| **Fine-tuning (LoRA)** | A100 / L40S / RTX 4090 | Cost-effective for adapter training |
| **Edge / on-device inference** | Custom ASIC (Apple ANE, Qualcomm NPU) | Power-constrained environments |

### 9.4 Quantization Impact on Hardware Selection

| Precision | Memory Reduction | Throughput Gain | Quality Impact | Hardware Support |
|-----------|-----------------|-----------------|----------------|------------------|
| FP16/BF16 | Baseline | Baseline | None | All GPUs |
| FP8 | 50% | 2u00d7 | Minimal (<1% degradation) | H100+, MI300X |
| INT8 (W8A8) | 50% | 2u00d7 | Small (1u20132%) | H100+, B200 |
| INT4 (AWQ/GPTQ) | 75% | 4u00d7 | Moderate (2u20135%) | All GPUs (software) |
| FP4 | 75% | 4u00d7 | Moderate (2u20135%) | B200, B300 only |

**FP4 Impact:** Blackwell's native FP4 support effectively doubles the addressable model size per GPU u2014 a 70B model in FP4 uses only ~35 GB, fitting on a single H100. A 405B model in FP4 needs ~200 GB, fitting on a single B300.

---

## 10. Key Trends & Strategic Implications

### 10.1 Trends Shaping the Compute Layer (2025u20132028)

| Trend | Impact | Timeline |
|-------|--------|----------|
| **Blackwell Ultra dominance** | B300 becomes default for frontier training; H100/H200 cascade to cost-sensitive workloads | 2026 |
| **Custom ASIC explosion** | Every major hyperscaler ships 2nd/3rd-gen custom silicon; 15u201320% of AI compute on non-NVIDIA by 2028 | 2026u20132028 |
| **AMD software maturation** | ROCm 7+ closes gap with CUDA; AMD captures 10u201315% AI GPU market | 2026u20132027 |
| **Rack-scale standard** | 72+ GPU NVLink domains become minimum for frontier training; individual GPU servers for inference only | 2026u20132027 |
| **Liquid cooling mandatory** | All new GPU deployments >600W per chip require DLC; air cooling phased out for AI data centers | 2026u20132027 |
| **FP4 as default inference precision** | FP4 replaces FP8 as standard inference format; 4u00d7 cost reduction vs. FP16 | 2026u20132027 |
| **Reasoning compute surge** | Chain-of-thought, agentic AI increases inference compute 5u201310u00d7 per query vs. simple completion | 2025u20132028 |
| **GPU-as-a-service commoditization** | Neo-cloud competition drives pricing toward marginal cost; hyperscaler premium narrows | 2026u20132028 |

### 10.2 Strategic Recommendations

| For | Recommendation |
|-----|---------------|
| **Startups** | Use neo-clouds (CoreWeave, Lambda, Spheron) for training; avoid hyperscaler GPU premium |
| **Enterprises** | Invest in on-prem inference clusters (3-yr payback at >60% utilization); use cloud for burst training |
| **Cloud providers** | Build custom silicon roadmap now; NVIDIA dependency is a strategic risk |
| **Governments** | Sovereign AI requires domestic GPU capacity u2014 on-prem or sovereign cloud (Korea: 260K Blackwell GPUs planned) |
| **Researchers** | Optimize for FP8/FP4 quantization now; Blackwell's FP4 Transformer Engine is a paradigm shift |
| **Infrastructure teams** | Plan for liquid cooling in all new deployments; rack power budgets must accommodate 600 kW+ |

### 10.3 The NVIDIA Moat u2014 And How It's Being Challenged

| Moat Layer | Strength | Challenge |
|-----------|----------|-----------|
| **CUDA ecosystem** | Very strong (15+ years, millions of developers) | PyTorch/ROCm abstracting CUDA; OpenAI Triton |
| **NVLink interconnect** | Strong (1.8 TB/s, no open alternative at parity) | UALink (AMD-led consortium) emerging |
| **Full-stack integration** | Strong (GPU + CPU + DPU + networking + software) | Hyperscalers building equivalent stacks internally |
| **Supply chain scale** | Very strong (TSMC priority, HBM supply agreements) | AMD, Google, Amazon all at TSMC |
| **Developer mindshare** | Strong but eroding | PyTorch 2.x + ROCm making AMD more accessible |

---

## Key Statistics Summary

| Metric | Value | Source |
|--------|-------|--------|
| NVIDIA AI GPU market share | ~80%+ | Industry estimates (2025) |
| B300 FP4 compute | 14 PFLOPS per GPU | NVIDIA / Spheron |
| B300 memory | 288 GB HBM3e | NVIDIA |
| GB200 NVL72 unified memory | 13.4 TB | NVIDIA |
| GB200 NVL72 FP4 compute | 1.44 EFLOPS | NVIDIA |
| DGX SuperPod (8u00d7NVL72) FP4 | 11.5 EFLOPS | NVIDIA |
| MI300X real-world vs H100 | 37u201366% of H100 performance | Celestial AI (arXiv:2510.27583) |
| Trillium TPU compute uplift | 4.7u00d7 vs TPU v5e | Google Cloud Blog |
| Cloud H100 price range | $1.25u2013$14.90/GPU-hr | Multi-provider survey |
| Hyperscaler vs neo-cloud premium | 3u20136u00d7 | Spheron analysis |
| On-prem break-even utilization | ~60u201370% | Lenovo TCO 2026 |
| Inference cost share (2026+) | ~55% of lifecycle | FMS 2025 |
| Korea GPU deployment plan | 260,000 Blackwell GPUs | Korea Herald |

---

*Previous: [AI Infra Overview](ai_infra_overview.md) u00b7 **You are here: Compute Layer** u00b7 Next: [Networking & Interconnect u2192](02_networking_interconnect.md)*
