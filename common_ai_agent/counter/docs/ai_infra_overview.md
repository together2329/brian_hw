# AI Infrastructure: Comprehensive Research Overview

> **Last Updated:** April 2026  
> **Scope:** Global AI infrastructure landscape u2014 from silicon to serving  
> **Sources:** Deloitte Tech Trends 2026, McKinsey, IEA, Grand View Research, Built In, FMS 2025, NVIDIA, Korea Herald, and others

---

## Table of Contents

1. [What Is AI Infrastructure?](#1-what-is-ai-infrastructure)
2. [Market Size & Investment Landscape](#2-market-size--investment-landscape)
3. [The 6-Layer AI Infrastructure Stack](#3-the-6-layer-ai-infrastructure-stack)
4. [Key Players & Ecosystem](#4-key-players--ecosystem)
5. [Training vs. Inference Economics](#5-training-vs-inference-economics)
6. [The Shift: From Hyperscaler Dominance to AI Factories](#6-the-shift-from-hyperscaler-dominance-to-ai-factories)
7. [Document Series Roadmap](#7-document-series-roadmap)

---

## 1. What Is AI Infrastructure?

AI infrastructure encompasses the **complete technology stack** needed to develop, train, deploy, and maintain artificial intelligence systems at scale. Unlike traditional software infrastructure, AI systems require specialized components optimized for:

- **Massive parallel computation** u2014 GPU/TPU-accelerated workloads for training and inference
- **High-throughput data processing** u2014 Fast storage and data pipelines for petabyte-scale datasets
- **Model lifecycle management** u2014 MLOps pipelines from experiment tracking to production serving
- **Ultra-low-latency networking** u2014 GPU-to-GPU interconnects for distributed training across thousands of chips

### Why It Matters

| Factor | Impact |
|--------|--------|
| Training time reduction | Right infra: weeks u2192 days (up to 70% cost savings) |
| Enterprise AI complexity | 78% of enterprises struggle with AI infra complexity (Hakia/2025) |
| Cost per workload | Enterprises spend 3u20135u00d7 more on AI infra vs. traditional apps (NVIDIA) |
| GPU demand growth | 350% increase in GPU demand YoY (2024u20132025) |

---

## 2. Market Size & Investment Landscape

### Global Market

| Metric | Value |
|--------|-------|
| **AI Infrastructure Market (2023)** | $35.4 billion |
| **AI Infrastructure Market (2025)** | $135.8 billion |
| **AI Infrastructure Market (2030, projected)** | $223u2013400 billion |
| **CAGR (2024u20132030)** | 30.4% |
| **Global CapEx required by 2030** | $3 trillion |

*Sources: Grand View Research (2023), MarketsandMarkets (2025), JLL (2025)*

### Hyperscaler Capital Expenditure (2025)

| Company | 2025 AI Infra Spend | Key Projects |
|---------|---------------------|--------------|
| **Amazon (AWS)** | ~$75B | $23B Ohio expansion, Annapurna Labs custom silicon |
| **Microsoft (Azure)** | ~$80B | "World's most powerful" data center (Wisconsin), OpenAI partnership |
| **Google (GCP)** | ~$50B | TPU v5/v6, Gemini Ultra infrastructure |
| **Meta** | ~$40B | Custom MTIA chips, 350K+ H100 cluster |
| **xAI (Elon Musk)** | Multi-B | Colossus u2014 100K GPU supercomputer (built in 122 days) |
| **Stargate Project** | $500B (multi-year) | Up to 10 GW AI-ready power (u2248 NYC + San Diego combined) |

**Total 2025 hyperscaler spend: ~$580 billion** (IEA World Energy Outlook 2025)

---

## 3. The 6-Layer AI Infrastructure Stack

```
u250cu2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2510
u2502                    LAYER 6: APPLICATION                         u2502
u2502         AI-powered products, APIs, agents, chatbots             u2502
u251cu2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2524
u2502                    LAYER 5: MLOps & ORCHESTRATION               u2502
u2502   Experiment tracking, model registry, CI/CD, serving (vLLM)   u2502
u251cu2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2524
u2502                    LAYER 4: ML FRAMEWORK                        u2502
u2502   PyTorch, JAX, TensorFlow, CUDA, TensorRT, DeepSpeed          u2502
u251cu2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2524
u2502                    LAYER 3: STORAGE & DATA                      u2502
u2502   Object storage (S3/GCS), NVMe, vector DBs, data pipelines    u2502
u251cu2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2524
u2502                    LAYER 2: NETWORKING & INTERCONNECT           u2502
u2502   NVLink, InfiniBand, RoCE, UALink, Ultra Ethernet, 800G/1.6T  u2502
u251cu2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2524
u2502                    LAYER 1: HARDWARE / COMPUTE                  u2502
u2502   GPUs (NVIDIA H100/B200/GB200), TPUs, CPUs, custom ASICs      u2502
u2514u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2518
```

### Layer 1: Hardware / Compute
- **NVIDIA Blackwell (B200/B300)**: 180 GB HBM3e per GPU, 1.8 TB/s NVLink bandwidth
- **GB200 NVL72**: 72 B200 GPUs + 36 Grace ARM CPUs in one rack u2014 13.4 TB unified memory, 1.44 EFLOPS FP4
- **Custom Silicon**: Google TPU v5/v6, Amazon Trainium2/Inferentia3, Meta MTIA, Microsoft Maia
- **AMD MI300X/MI400**: CDNA architecture, growing adoption

### Layer 2: Networking & Interconnect
- **NVLink 5**: 1.8 TB/s per GPU (7u00d7 PCIe Gen5 bandwidth)
- **InfiniBand NDR/XDR**: 400u2013800 Gb/s for training clusters
- **RoCE v2**: RDMA over Converged Ethernet for cost-sensitive deployments
- **UALink**: Open alternative to NVLink for scale-up (emerging)
- **Ultra Ethernet Consortium (UEC 1.0)**: Open high-performance Ethernet for AI

### Layer 3: Storage & Data
- **Object storage** (S3/GCS) for training datasets and model artifacts
- **NVMe SSD arrays** for high-speed checkpoint I/O
- **Vector databases** (Pinecone, Weaviate, Milvus) for embeddings/RAG
- **Distributed file systems** (Lustre, Weka, DAOS) for parallel training I/O

### Layer 4: ML Framework
- **Training**: PyTorch (dominant), JAX, DeepSpeed, Megatron-LM
- **Inference**: TensorRT-LLM, vLLM, ONNX Runtime, llama.cpp
- **Compilation**: CUDA, Triton, XLA, OpenAI Triton

### Layer 5: MLOps & Orchestration
- **Orchestration**: Kubernetes (K8s), Slurm (HPC), Ray
- **Experiment tracking**: MLflow, Weights & Biases, Neptune
- **Model serving**: Triton Inference Server, vLLM, TensorRT-LLM
- **CI/CD**: GitHub Actions, GitLab CI with ML-specific pipelines

### Layer 6: Application
- AI agents, chatbots, copilots, recommendation systems
- Multimodal interfaces (text, image, video, audio)
- Retrieval-Augmented Generation (RAG) pipelines
- RLHF / DPO alignment pipelines

---

## 4. Key Players & Ecosystem

### Hardware Vendors

| Vendor | Products | Strategy |
|--------|----------|----------|
| **NVIDIA** | H100, H200, B200, B300, GB200 NVL72 | Dominant (~80%+ AI GPU market); full-stack (CUDA, NVLink, networking) |
| **AMD** | MI300X, MI325X, MI400 (upcoming) | Open ROCm ecosystem; growing cloud adoption |
| **Google** | TPU v5p, TPU v6 (Trillium) | Internal + GCP; custom ASIC for training & inference |
| **Amazon** | Trainium2, Inferentia3, Graviton | AWS-optimized custom silicon |
| **Intel** | Gaudi 3, Gaudi 4 | Challenger position; Habana Labs acquisition |
| **Meta** | MTIA v2, v3 | Internal inference chips; reducing NVIDIA dependency |
| **Microsoft** | Maia 100 | Azure-optimized custom AI accelerator |

### Cloud / Hyperscaler Platforms

| Platform | Key Differentiator |
|----------|-------------------|
| **AWS** | Largest cloud; Inferentia/Trainium custom chips; SageMaker MLOps |
| **Azure** | OpenAI partnership; enterprise AI integration; Maia chips |
| **Google Cloud** | TPU access; Vertex AI; DeepMind model integration |
| **Oracle Cloud** | Bare-metal GPU focus; multi-cloud partnerships |
| **CoreWeave** | GPU-first cloud; fast growth; specialized for AI workloads |
| **Lambda Labs** | Cost-effective GPU rental; developer-focused |

### Networking Vendors

| Vendor | Key Products |
|--------|-------------|
| **NVIDIA (Mellanox)** | InfiniBand NDR/XDR, Spectrum-X Ethernet, NVLink |
| **Cisco** | AI-optimized Ethernet switches, Nexus fabric |
| **Arista** | 800G Ethernet, AI cluster spine-leaf architectures |
| **Broadcom** | SerDes PHY, switch ASICs, UEC silicon |

---

## 5. Training vs. Inference Economics

### The OPEX Shift

A critical trend identified in 2025u20132026: **inference + post-training now represents ~80% of the lifecycle cost** for production AI models (FMS 2025).

| Phase | Cost Share (2024) | Cost Share (2026+) | Trend |
|-------|-------------------|---------------------|-------|
| Pre-training | ~50% | ~20% | u2193 Decreasing (one-time cost) |
| Post-training (RLHF, RL) | ~10% | ~25% | u2191 Surging (Grok-4 RL u2248 0.5u00d7 pre-train compute) |
| Inference / Serving | ~40% | ~55% | u2191u2191 Dominant (continuous API calls, agents) |

### Why Inference Dominates

1. **Production models serve billions of requests daily** u2014 cumulative cost overtakes training within 2 years
2. **Agentic AI** u2014 multi-step reasoning, tool use, chain-of-thought increases tokens/request by 5u201310u00d7
3. **MoE models** u2014 routing overhead increases All-to-All network traffic (u226540% of runtime)
4. **Open-weight models** u2014 more deployments = more inference cost across ecosystem

### Inference Cost Reduction Techniques

| Technique | Speedup / Savings | Status |
|-----------|-------------------|--------|
| FP8 Quantization | 2u00d7 throughput, 50% memory | Production-standard (H100/H200) |
| INT4 Quantization (AWQ/GPTQ) | 4u00d7 throughput, 75% memory | 70B models on consumer GPUs |
| Speculative Decoding | 2u20133u00d7 latency reduction | Production (vLLM, TensorRT-LLM) |
| Continuous Batching | 5u00d7 throughput efficiency | Production |
| Distillation to 20B MoE | 10u00d7 cost reduction at near-70B quality | Emerging |
| KV Cache Optimization | 2u20133u00d7 memory efficiency | Production |

---

## 6. The Shift: From Hyperscaler Dominance to AI Factories

### Current State (2025u20132026)

- **Hyperscalers control >98% of AI infrastructure** (Canalys 2024, IDC 2025)
- Centralized mega-clusters: 100K+ GPU deployments
- Massive CapEx: $320B+ in 2025 alone by top 4 hyperscalers

### Emerging Shifts (2026u20132028)

| Trend | Description |
|-------|-------------|
| **Inference Factories** | Purpose-built facilities closer to users for low-latency serving |
| **Sovereign AI** | Nations building domestic GPU capacity (Korea: 260K GPUs, EU, Japan) |
| **Power Constraints** | Rack density: 120 kW u2192 600 kW (2027) u2192 1 MW (prototype); requires liquid cooling |
| **Open Fabrics** | UALink + Ultra Ethernet challenging NVIDIA's closed NVLink/IB ecosystem |
| **Optics Revolution** | 800G LPO (today) u2192 NPO pilots (2026) u2192 1.6T CPO volume (2027u201328) |
| **Edge Inference** | On-device AI (Apple, Qualcomm), reducing cloud dependency |
| **Regulatory Pressure** | Energy caps, carbon reporting, data sovereignty requirements |

### The "Five Pivotal Shifts" (FMS 2025 / 2025u20132028 Outlook)

1. **Network-bound era**: MoE & agents push u226540% of runtime into All-to-All traffic
2. **Inference OPEX rules**: Cumulative serving cost overtakes training within 2 years
3. **Post-training surge**: RL-based post-training approaching 0.5u00d7 pre-train compute
4. **Fabric realignment**: Closed NVLink/IB vs. open UALink + UEC 1.0
5. **Optics roadmap**: 800G LPO u2192 NPO u2192 1.6T CPO u2014 signal integrity as next bottleneck

---

## 7. Document Series Roadmap

This overview is the first in a series of 9 documents:

| # | Document | Status |
|---|----------|--------|
| 0 | **AI Infra Overview (this document)** | u2705 Complete |
| 1 | [Compute Layer u2014 GPU Architecture & Trends](01_compute_layer.md) | u23f3 Pending |
| 2 | [Networking & Interconnect Layer](02_networking_interconnect.md) | u23f3 Pending |
| 3 | [Storage & Data Layer](03_storage_data.md) | u23f3 Pending |
| 4 | [AI Data Center Physical Infrastructure](04_datacenter_physical.md) | u23f3 Pending |
| 5 | [Inference Optimization & Serving](05_inference_optimization.md) | u23f3 Pending |
| 6 | [MLOps & Orchestration Stack](06_mlops_orchestration.md) | u23f3 Pending |
| 7 | [Korea AI Infrastructure Landscape](07_korea_ai_infra.md) | u23f3 Pending |
| 8 | [2025u20132028 Outlook & Strategic Recommendations](08_outlook_recommendations.md) | u23f3 Pending |

---

## Key Statistics Summary

| Metric | Value | Source |
|--------|-------|--------|
| Global AI infra market (2025) | $135.8B | MarketsandMarkets |
| Global AI infra market (2030 proj.) | $223u2013400B | Grand View / MarketsandMarkets |
| Total CapEx required by 2030 | $3 trillion | JLL |
| Hyperscaler spend in 2025 | ~$580B | IEA |
| Enterprise AI infra complexity | 78% struggle | Hakia/2025 survey |
| Cost premium vs. traditional apps | 3u20135u00d7 | NVIDIA |
| Inference % of lifecycle cost | ~80% (2026+) | FMS 2025 |
| GB200 NVL72 unified memory | 13.4 TB | NVIDIA |
| GB200 NVL72 FP4 compute | 1.44 EFLOPS | NVIDIA |
| Rack power density trend | 120 kW u2192 600 kW (2027) u2192 1 MW | Industry |
| Korea GPU deployment plan | 260,000 Blackwell GPUs | Korea Herald |
| Samsung SDS data center investment | 3.7T KRW ($2.8B), 140 MW | Samsung SDS |

---

*Next document u2192 [01_compute_layer.md](01_compute_layer.md)*
