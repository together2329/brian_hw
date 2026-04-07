# Storage & Data Layer

> **Last Updated: April 2026**
> Navigation: [u2190 AI Infra Overview](ai_infra_overview.md) | [Networking & Interconnect u2190](02_networking_interconnect.md) | [Data Center Physical u2192](04_datacenter_physical.md)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Storage Hierarchy for AI](#2-the-storage-hierarchy-for-ai)
3. [Object Storage: S3, GCS, Azure Blob](#3-object-storage-s3-gcs-azure-blob)
4. [NVMe SSD Arrays & High-Speed Local Storage](#4-nvme-ssd-arrays--high-speed-local-storage)
5. [Distributed File Systems for AI Training](#5-distributed-file-systems-for-ai-training)
6. [Vector Databases & RAG Infrastructure](#6-vector-databases--rag-infrastructure)
7. [Data Pipeline for Training Datasets](#7-data-pipeline-for-training-datasets)
8. [Checkpoint I/O: The Hidden Bottleneck](#8-checkpoint-io-the-hidden-bottleneck)
9. [Storage Tiers & Data Lifecycle](#9-storage-tiers--data-lifecycle)
10. [Storage Vendor Landscape](#10-storage-vendor-landscape)
11. [Cost Analysis: Storage TCO for AI](#11-cost-analysis-storage-tco-for-ai)
12. [Future Outlook 2026u20132028](#12-future-outlook-20262028)
13. [Key Takeaways](#13-key-takeaways)

---

## 1. Executive Summary

Storage is the **silent backbone** of AI infrastructure. While GPUs and networks dominate performance discussions, the data pipeline u2014 from petabyte-scale training datasets to millisecond-latency checkpoint saves u2014 determines whether a training cluster operates at 30% or 90% utilization.

**Key facts at a glance:**

| Metric | 2024 | 2026 | Trend |
|--------|------|------|-------|
| Typical training dataset size | 1u201310 TB (text) | 10u2013100 TB (multimodal) | 10u00d7 growth |
| Checkpoint size (frontier model) | 1u20132 TB (100B params) | 5u201315 TB (1T+ params) | 5u201310u00d7 growth |
| NVMe Gen5 SSD throughput | 14 GB/s per drive | 28 GB/s (Gen6 sampling) | 2u00d7 |
| Vector DB scale (production) | 1u201310B vectors | 100B+ vectors | 10u2013100u00d7 |
| Object storage egress cost | $0.05u20130.12/GB | $0.05u20130.12/GB (flat) | No improvement |

This document covers the full storage stack for AI infrastructure u2014 from object storage and distributed file systems to NVMe arrays, vector databases, data pipelines, and the critical checkpoint I/O bottleneck.

---

## 2. The Storage Hierarchy for AI

### 2.1 The Complete Data Access Hierarchy

AI workloads access data through a strict hierarchy, with each level offering different bandwidth, latency, capacity, and cost characteristics:

| Tier | Technology | Bandwidth | Latency | Capacity per Node | $/GB/month | Role in AI |
|------|-----------|-----------|---------|-------------------|-----------|-----------|
| **T0** | GPU Register File | ~40 TB/s | ~0.3 ns | ~256 KB | u2014 | Immediate compute |
| **T1** | GPU L2 Cache | ~20 TB/s | ~1 ns | ~40u201360 MB | u2014 | Hot tensor data |
| **T2** | HBM3e (GPU Memory) | 4.8u20138.0 TB/s | ~100 ns | 180u2013288 GB | u2014 | Model weights, KV cache |
| **T3** | DDR5 (Host CPU Memory) | 150u2013300 GB/s | ~80u2013100 ns | 256 GBu20132 TB | $10u201320 | Staging, OS buffers |
| **T4** | CXL-Attached Memory | 64 GB/s per link | ~150u2013200 ns | 1u20134 TB (expanding) | $5u201310 | Extended memory pool |
| **T5** | Local NVMe Gen5 SSD | 14 GB/s per drive | ~15u201360 u03bcs | 15u201360 TB | $0.50u20131.00 | Checkpoint, data cache |
| **T6** | Distributed File System | 100u2013500 GB/s (cluster) | 0.5u20132 ms | 100 TBu201310 PB | $0.30u20130.80 | Training data, shared state |
| **T7** | Object Storage (S3/GCS) | 10u2013120 GB/s (bucket) | 10u2013200 ms | Unlimited | $0.02u20130.16 | Archive, raw datasets |

### 2.2 Data Flow During Training

```
u250cu2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2510
u2502                    AI TRAINING DATA FLOW                            u2502
u2502                                                                     u2502
u2502  [T7: Object Storage]     Raw datasets (PB-scale)                  u2502
u2502     u2502 e.g., S3, GCS                                                 u2502
u2502     u2502 100-200 ms latency, 10-120 GB/s                               u2502
u2502     u25bc                                                               u2502
u2502  [T6: Distributed FS]     Staged training data                      u2502
u2502     u2502 e.g., Lustre, Weka, DAOS                                      u2502
u2502     u2502 0.5-2 ms latency, 100-500 GB/s                                u2502
u2502     u25bc                                                               u2502
u2502  [T5: Local NVMe]         Tokenized, cached batches                 u2502
u2502     u2502 e.g., PCIe Gen5 NVMe RAID                                     u2502
u2502     u2502 15-60 u03bcs latency, 50-200 GB/s                                 u2502
u2502     u25bc                                                               u2502
u2502  [T3: CPU DDR5]           DataLoader prefetch buffers               u2502
u2502     u2502 80-100 ns latency, 150-300 GB/s                               u2502
u2502     u25bc                                                               u2502
u2502  [T2: GPU HBM]            Training tensors, model weights           u2502
u2502        4.8-8 TB/s, ~100 ns latency                                  u2502
u2502                                                                     u2502
u2502  Checkpoint path: T2 u2192 T5 (NVMe) u2192 T7 (Object Storage)             u2502
u2514u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2518
```

### 2.3 Key Principle: Keep the Pipeline Full

GPU utilization depends on feeding data fast enough. A B200 GPU consuming 2,250 TFLOPS of FP16 data needs:
- **Training data input**: ~2u20134 GB/s per GPU (tokenized text/images)
- **Gradient checkpoint save**: ~1u201310 GB/s per GPU (periodic)
- **Model checkpoint save**: ~100 GBu201310 TB every N minutes

If any tier in the hierarchy can't keep up, GPUs stall u2014 burning $2u20134/hour per GPU while waiting for data.

---

## 3. Object Storage: S3, GCS, Azure Blob

### 3.1 Role in AI Infrastructure

Object storage is the **foundation tier** for AI data u2014 storing raw training datasets, preprocessed corpora, model artifacts, logs, and checkpoints. It provides virtually unlimited capacity with high durability (99.999999999% / "11 nines") at the lowest cost per GB.

### 3.2 Major Providers Comparison

| Parameter | Amazon S3 | Google Cloud Storage | Azure Blob Storage |
|-----------|-----------|---------------------|-------------------|
| **Hot tier** | S3 Standard ($0.023/GB/mo) | Standard ($0.026/GB/mo) | Hot ($0.018/GB/mo) |
| **Warm tier** | S3 Infrequent Access ($0.0125) | Nearline ($0.010) | Cool ($0.012) |
| **Cold tier** | S3 Glacier Deep Archive ($0.00099) | Archive ($0.0012) | Archive ($0.00099) |
| **Low-latency tier** | S3 Express One Zone ($0.16/GB/mo) | u2014 | u2014 |
| **Max single object** | 5 TB | 5 TB | 190.7 TB |
| **Throughput (per bucket)** | 100 GB/s+ | 120 GB/s+ | 90 GB/s+ |
| **Latency (hot)** | 100u2013200 ms | 100u2013200 ms | 100u2013200 ms |
| **Latency (Express)** | 10u201315 ms | u2014 | u2014 |
| **Durability** | 99.999999999% | 99.999999999% | 99.999999999% |
| **Egress cost** | $0.05u20130.12/GB | $0.08u20130.12/GB | $0.05u20130.12/GB |

### 3.3 S3 Express One Zone: Purpose-Built for AI

S3 Express One Zone (launched 2024) is the first object storage tier designed specifically for AI/ML workloads requiring low-latency access:

- **10u201315 ms latency** (vs. 100u2013200 ms for standard S3)
- **100 GB/s+ throughput** per bucket
- **Single Availability Zone** (lower durability, lower latency)
- **$0.16/GB/month** (~7u00d7 standard S3)
- **Use cases**: Training data staging, frequent checkpoint read/write, feature store access

### 3.4 Egress Cost: The Hidden Expense

Object storage egress (data transfer out) costs are often the **largest ongoing expense** for AI data:

| Scenario | Monthly Egress | S3 Cost | GCS Cost | Azure Cost |
|----------|---------------|---------|----------|-----------|
| 1 PB dataset read once | 1 PB | $50,000u2013$120,000 | $80,000u2013$120,000 | $50,000u2013$120,000 |
| 100 TB weekly training reload | 400 TB/mo | $20,000u2013$48,000 | $32,000u2013$48,000 | $20,000u2013$48,000 |
| 10 TB daily checkpoint sync | 300 TB/mo | $15,000u2013$36,000 | $24,000u2013$36,000 | $15,000u2013$36,000 |

> **Strategy**: Keep hot training data on local/distributed storage; use object storage for cold archive and initial ingestion only. Minimize egress with cloud-local processing.

### 3.5 Object Storage Optimization for AI

| Technique | Description | Impact |
|-----------|-------------|--------|
| **Multipart upload** | Parallel upload of large objects in 5u201310 GB parts | 5u201310u00d7 upload throughput |
| **S3 Transfer Acceleration** | Route through CloudFront edge locations | 2u20135u00d7 cross-region transfer |
| **Prefix distribution** | Spread objects across many key prefixes | Avoids S3 request rate limits (5,500 GET/s per prefix) |
| **S3 Select / Glacier Select** | Server-side filtering (SQL subset retrieval) | Up to 80% less data transfer |
| **Lifecycle policies** | Auto-transition cold data to cheaper tiers | 50u201380% cost reduction for archival |
| **Point-in-time recovery** | Versioning + replication for data protection | Prevents catastrophic data loss |

---

## 4. NVMe SSD Arrays & High-Speed Local Storage

### 4.1 Why NVMe Matters for AI

Local NVMe SSDs are the **fast storage tier** directly attached to GPU nodes, serving two critical functions:
1. **Training data cache**: Tokenized datasets pre-staged for high-throughput DataLoader access
2. **Checkpoint I/O**: Fast save/load of model checkpoints (critical for training efficiency)

### 4.2 Current-Generation NVMe SSDs

| Drive | Interface | Capacity | Seq. Read | Seq. Write | Random Read IOPS | Latency | Form Factor |
|-------|-----------|----------|-----------|------------|-----------------|---------|-------------|
| **Samsung PM1743** | PCIe Gen5 u00d74 | 3.84u201315.36 TB | 13.5 GB/s | 6.6 GB/s | 2,500K | ~15 u03bcs | U.2 / EDSFF |
| **Micron 9400** | PCIe Gen5 u00d74 | 3.2u201315.36 TB | 14 GB/s | 10 GB/s | 2,000K | ~20 u03bcs | U.2 / EDSFF |
| **Solidigm D7-P5810** | PCIe Gen5 u00d74 | 3.2u201312.8 TB | 14 GB/s | 6.8 GB/s | 2,100K | ~15 u03bcs | U.2 / EDSFF |
| **Samsung PM9C1a** | PCIe Gen5 u00d74 | 256 GBu20132 TB | 12 GB/s | 6.5 GB/s | 1,500K | ~20 u03bcs | M.2 |
| **Kioxia CM7** | PCIe Gen5 u00d74 | 3.2u201312.8 TB | 14 GB/s | 6.2 GB/s | 2,300K | ~18 u03bcs | EDSFF |

### 4.3 NVMe Array Configurations for AI Nodes

**Single-node NVMe configuration (typical GPU server):**

| Configuration | Drives | Total Capacity | Aggregate BW | Use Case |
|--------------|--------|---------------|-------------|----------|
| 4u00d7 Gen5 NVMe (U.2) | 4 u00d7 15.36 TB | 61.4 TB | ~56 GB/s read | Checkpoint + data cache |
| 8u00d7 Gen5 NVMe (U.2) | 8 u00d7 15.36 TB | 122.9 TB | ~112 GB/s read | Large model training |
| 16u00d7 Gen5 NVMe (EDSFF) | 16 u00d7 7.68 TB | 122.9 TB | ~200 GB/s+ read | Maximum throughput |

### 4.4 NVMe Performance for Checkpoint I/O

For a 1-trillion-parameter model in FP16:

| Parameter | Value |
|-----------|-------|
| Model parameter memory | 2 TB (1T u00d7 2 bytes) |
| Optimizer state (AdamW) | +8 TB (4u00d7 model: m, v, gradients, params in FP32) |
| **Total checkpoint size** | **~10 TB** |
| Save time (single Gen5 NVMe @ 14 GB/s) | ~714 seconds (~12 min) |
| Save time (8u00d7 Gen5 RAID @ 100 GB/s) | ~100 seconds (~1.7 min) |
| Save time (8u00d7 Gen5 RAID + async streaming) | ~50 seconds (overlap with training) |

### 4.5 NVMe vs HDD vs Object Storage for Checkpoints

| Storage | Write BW | Save Time (10 TB checkpoint) | $/TB/month | Suitable For |
|---------|---------|----------------------------|-----------|-------------|
| 8u00d7 Gen5 NVMe RAID | 100 GB/s | ~100s | $0.50u20131.00 | Hot checkpoints, active training |
| Single Gen5 NVMe | 14 GB/s | ~714s | $0.50u20131.00 | Single-GPU checkpoints |
| Network file system | 5u201320 GB/s | 500u20132,000s | $0.30u20130.80 | Shared checkpoint storage |
| HDD array (RAID-6) | 1u20133 GB/s | 3,300u201310,000s | $0.05u20130.10 | Archive only |
| S3 Standard | 5u201310 GB/s (upload) | 1,000u20132,000s | $0.02u20130.03 | Long-term archive |

> **Best practice**: Save checkpoints to local NVMe first (fast), then asynchronously replicate to object storage (durable). This decouples checkpoint latency from network/durable storage speed.

---

## 5. Distributed File Systems for AI Training

### 5.1 Why Distributed File Systems?

When training across dozens or hundreds of nodes, all workers need concurrent access to the same training data. Distributed file systems provide:
- **Shared namespace** across all nodes
- **Parallel I/O** (aggregate bandwidth across many storage servers)
- **Posix compatibility** (existing tools work without modification)
- **Fault tolerance** (data replicated across storage servers)

### 5.2 Major Distributed File Systems

#### Lustre

| Parameter | Value |
|-----------|-------|
| **Architecture** | Metadata servers (MDS) + Object Storage Servers (OSS) |
| **Max throughput** | 1u20132+ TB/s aggregate |
| **Metadata ops** | 50,000+ ops/sec |
| **Max nodes** | 16,000+ |
| **Protocol** | Custom (Lustre protocol over LNET) |
| ** posix** | Full POSIX compliance |
| **License** | GPL (open source) |
| **Use case** | HPC training clusters, national labs |
| **Key users** | Meta, CERN, national supercomputing centers |

**Strengths**: Highest raw throughput at scale; proven at exabyte deployments; no licensing cost.
**Weaknesses**: Complex management; requires dedicated storage servers; not cloud-native; metadata performance bottleneck for small-file workloads.

#### WekaIO (WekaFS)

| Parameter | Value |
|-----------|-------|
| **Architecture** | Software-defined, container-native |
| **Max throughput** | 200+ GB/s per cluster |
| **Latency** | <200 u03bcs (NVMe-backed) |
| **Max nodes** | 1,000+ |
| **Protocol** | NFS, SMB, S3, POSIX |
| **Deployment** | On-prem or cloud (AWS, GCP) |
| **License** | Commercial ($2,500/TB/year) |
| **Use case** | AI cloud clusters, enterprise AI |

**Strengths**: Cloud-native; integrates NVMe + object storage in single namespace; simple management.
**Weaknesses**: Commercial license cost; lower max throughput than Lustre at extreme scale.

#### DAOS (Distributed Asynchronous Object Storage)

| Parameter | Value |
|-----------|-------|
| **Developer** | Intel |
| **Architecture** | User-space, PMEM/NVMe-optimized |
| **Max throughput** | 500+ GB/s per cluster |
| **Latency** | <100 u03bcs (PMEM-backed) |
| **Protocol** | Custom API + POSIX (DFS) |
| **License** | Apache 2.0 (open source) |
| **Use case** | Aurora supercomputer, Intel-based AI clusters |

**Strengths**: Lowest latency; optimized for NVMe/PMEM; designed for AI checkpoint patterns.
**Weaknesses**: Tied to Intel ecosystem; limited third-party support; PMEM (Optane) discontinued.

#### BeeGFS

| Parameter | Value |
|-----------|-------|
| **Architecture** | Client-server, metadata + storage separation |
| **Max throughput** | 500+ GB/s aggregate |
| **Max nodes** | 10,000+ |
| **Protocol** | Custom (BeeGFS protocol) |
| **License** | Community (free) + Enterprise (commercial) |
| **Use case** | University clusters, mid-size AI training |
| **TCO** | ~$0.42/GB/month (most cost-effective) |

**Strengths**: Easy to deploy; excellent price/performance; active community.
**Weaknesses**: Less proven at extreme scale (>10K nodes); fewer enterprise features.

#### IBM Storage Scale (formerly GPFS / Spectrum Scale)

| Parameter | Value |
|-----------|-------|
| **Architecture** | Shared-nothing cluster |
| **Max throughput** | 1+ TB/s |
| **Max capacity** | Exabyte-scale |
| **Protocol** | POSIX, NFS, S3 |
| **License** | Commercial |
| **Use case** | Enterprise AI, financial services, healthcare |

**Strengths**: Battle-tested (25+ years); massive scale; enterprise features (tiering, encryption).
**Weaknesses**: Expensive licensing; complex configuration; not optimized for cloud-native deployments.

### 5.3 Distributed FS Decision Matrix

| Scenario | Recommended FS | Rationale |
|----------|---------------|-----------|
| **>1,000-node training cluster** | Lustre | Highest aggregate throughput; proven at exabyte scale |
| **Cloud-native AI (AWS/GCP)** | WekaIO | Seamless cloud deployment; NVMe + S3 tiering |
| **Intel-optimized cluster** | DAOS | Lowest latency with PMEM/NVMe; Intel ecosystem |
| **Mid-size cluster (50u2013500 nodes)** | BeeGFS | Best price/performance; easy deployment |
| **Enterprise / regulated industry** | IBM Storage Scale | Compliance features; audit trail; encryption |
| **Multi-tenant AI cloud** | WekaIO or Ceph | Multi-tenancy; QoS; S3-compatible |

### 5.4 Performance Comparison

| File System | Seq. Read BW | Seq. Write BW | Metadata Ops | Latency | Cost/GB/mo |
|------------|-------------|--------------|-------------|---------|-----------|
| Lustre | 1u20132 TB/s | 1u20132 TB/s | 50K ops/s | 0.5u20132 ms | $0.56 |
| WekaIO | 200 GB/s | 200 GB/s | 200K ops/s | <0.2 ms | $0.80 |
| DAOS | 500 GB/s | 500 GB/s | 300K ops/s | <0.1 ms | $0.70 |
| BeeGFS | 500 GB/s | 500 GB/s | 100K ops/s | 0.3u20131 ms | $0.42 |
| IBM Storage Scale | 1 TB/s | 1 TB/s | 150K ops/s | 0.5u20132 ms | $0.90 |
| Ceph | 200 GB/s | 200 GB/s | 50K ops/s | 1u20135 ms | $0.35 |

> Note: Performance figures are per-cluster aggregate with typical NVMe-backed storage servers. Actual performance depends heavily on cluster size, network fabric, and workload pattern.

---

## 6. Vector Databases & RAG Infrastructure

### 6.1 Why Vector Databases Matter

Retrieval-Augmented Generation (RAG) has become the dominant pattern for enterprise AI deployment, requiring vector databases to store and retrieve embeddings at scale. Over 40% of enterprise AI deployments now use RAG.

### 6.2 Major Vector Databases

| Database | Type | Max Scale | Query Latency | Dimension Support | License |
|----------|------|-----------|---------------|-------------------|---------|
| **Pinecone** | Managed cloud | 10B+ vectors | 10u201350 ms | Up to 20,000 | Commercial (managed) |
| **Milvus** | Self-hosted / managed | 10B+ vectors | 15u201360 ms | Up to 32,768 | Apache 2.0 (open source) |
| **Weaviate** | Self-hosted / managed | 10B+ vectors | 20u201380 ms | Up to 65,535 | BSD-3 (open source) |
| **Qdrant** | Self-hosted | 1B+ vectors | 5u201330 ms | Up to 65,535 | Apache 2.0 (open source) |
| **Chroma** | Self-hosted / embedded | 100M+ vectors | 10u201350 ms | Up to 1,000+ | Apache 2.0 (open source) |
| **pgvector** | PostgreSQL extension | 100M+ vectors | 20u2013100 ms | Up to 2,000 | Apache 2.0 (open source) |
| **Elasticsearch** | Search engine + vector | 1B+ vectors | 20u2013100 ms | Up to 4,096 | SSPL / Elastic License |

### 6.3 Indexing Methods

| Method | Build Time | Query Latency | Recall | Memory Usage | Best For |
|--------|-----------|--------------|--------|-------------|----------|
| **Flat (brute-force)** | None | O(n) | 100% | High | Small datasets (<1M) |
| **IVF (Inverted File)** | Fast | Medium | 90u201399% | Medium | General purpose |
| **HNSW** | Medium | Fast (5u201330 ms) | 95u201399.5% | High | Low-latency production |
| **PQ (Product Quantization)** | Fast | Fast | 80u201395% | Low (8u201332u00d7 compression) | Memory-constrained |
| **IVF + PQ** | Fast | Fast | 85u201395% | Very Low | Billion-scale, cost-sensitive |
| **ScaNN (Google)** | Medium | Very Fast | 95u201399% | Medium | High-throughput |
| **FAISS** | Fast | Fast | 90u201399% | Medium | GPU-accelerated search |

### 6.4 RAG Pipeline Architecture

```
u250cu2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2510
u2502                    RAG PIPELINE ARCHITECTURE                          u2502
u2502                                                                      u2502
u2502  1. INGESTION                                                        u2502
u2502  [Documents] u2192 Chunking u2192 Embedding Model u2192 Vector Database          u2502
u2502     u2502              u2502           u2502              u2502                       u2502
u2502     u2502         256-1024    e5-large,       Pinecone/                   u2502
u2502     u2502         tokens     text-embedding   Milvus/                     u2502
u2502     u2502                    -3-large        Qdrant                       u2502
u2502                                                                      u2502
u2502  2. QUERY                                                            u2502
u2502  [User Query] u2192 Embedding u2192 ANN Search u2192 Top-K Chunks u2192 LLM         u2502
u2502                      u2502           u2502            u2502           u2502           u2502
u2502                 same model    HNSW/IVF    5-50 chunks   GPT-4/       u2502
u2502                 as ingest     recall@10   context       Claude/      u2502
u2502                                           window       Llama         u2502
u2502                                                                      u2502
u2502  3. TYPICAL PERFORMANCE TARGETS                                      u2502
u2502  Embedding latency: 10-50 ms/query                                   u2502
u2502  Vector search latency: 5-50 ms/query                                u2502
u2502  Total RAG latency: 100-500 ms (incl. LLM generation)                u2502
u2502  Throughput: 100-1,000 queries/sec per replica                       u2502
u2514u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2518
```

### 6.5 Vector Database Sizing

| Scale | Vectors | Dimensions | Index Size (HNSW) | RAM Required | Storage |
|-------|---------|-----------|-------------------|-------------|---------|
| Small | 10M | 1,536 (OpenAI) | ~60 GB | 80 GB | 100 GB SSD |
| Medium | 100M | 1,536 | ~600 GB | 800 GB | 1 TB NVMe |
| Large | 1B | 1,536 | ~6 TB | 8 TB | 10 TB NVMe |
| Enterprise | 10B | 1,536 | ~60 TB | 80 TB | 100 TB distributed |
| Frontier | 100B | 1,536 | ~600 TB | Distributed cluster | Petabyte-scale |

### 6.6 Choosing a Vector Database

| Priority | Recommendation | Why |
|----------|---------------|-----|
| **Fastest queries** | Qdrant | Rust-native, <30ms at scale |
| **Easiest operations** | Pinecone | Fully managed, zero admin |
| **Largest scale** | Milvus | Proven at 10B+ vectors, distributed |
| **Tightest integration** | pgvector | Leverages existing PostgreSQL |
| **Best hybrid search** | Weaviate | Built-in BM25 + vector + filtering |
| **Smallest footprint** | Chroma | Embedded mode, prototyping |
| **GPU acceleration** | FAISS (library) | GPU-native, custom pipelines |

---

## 7. Data Pipeline for Training Datasets

### 7.1 The ML Data Lifecycle

```
u250cu2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2510    u250cu2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2510    u250cu2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2510    u250cu2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2510    u250cu2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2510
u2502  INGEST  u2502 u2192  u2502  CLEAN   u2502 u2192  u2502 TRANSFORMu2502 u2192  u2502  TOKENIZEu2502 u2192  u2502  TRAIN   u2502
u2502          u2502    u2502          u2502    u2502          u2502    u2502          u2502    u2502          u2502
u2502 Web crawlu2502    u2502 Dedup    u2502    u2502 Filter   u2502    u2502 BPE/     u2502    u2502 DataLoaderu2502
u2502 APIs     u2502    u2502 PII      u2502    u2502 Quality  u2502    u2502 Sentence u2502    u2502 streaming u2502
u2502 Internal u2502    u2502 Language  u2502    u2502 Augment  u2502    u2502 Piece    u2502    u2502 sharding  u2502
u2502 datasets u2502    u2502 detect   u2502    u2502 Resample u2502    u2502 vocab    u2502    u2502 prefetch  u2502
u2514u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2518    u2514u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2518    u2514u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2518    u2514u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2518    u2514u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2518
     u2193               u2193               u2193               u2193               u2193
  S3/GCS        Spark/Ray        Ray Data       HuggingFace      WebDataset/
  (raw)         (cleaned)        (transformed)  tokenizers       TFRecord/
                                                                MDS format
```

### 7.2 Data Ingestion

| Source | Typical Volume | Format | Tools |
|--------|---------------|--------|-------|
| Common Crawl | 100+ TB (raw HTML) | WARC | cc-net, warcio |
| The Stack (code) | 10+ TB | Per-file | GitHub API, snapshot |
| Academic papers | 1u201310 TB | PDF, LaTeX | S2ORC, arXiv dump |
| Books | 100 GBu20131 TB | Text, EPUB | Books3, Project Gutenberg |
| Internal enterprise data | 1u2013100 TB | Various | Custom ETL pipelines |
| Synthetic data | 1u201310 TB | JSON/parquet | LLM-generated, filtered |

### 7.3 Data Preprocessing Pipeline

**Typical preprocessing steps for LLM training:**

| Step | Purpose | Tools | Compute Cost |
|------|---------|-------|-------------|
| **Language detection** | Filter by target language | fastText, langdetect | Low (CPU) |
| **Quality filtering** | Remove low-quality content | classifiers, perplexity filters | Medium |
| **Deduplication** | Exact + fuzzy dedup | MinHash, Bloom filters, deduplicate-text-datasets | High (CPU + RAM) |
| **PII removal** | Strip personally identifiable info | Presidio, regex, NER models | Medium |
| **Toxic content filtering** | Remove harmful content | classifiers, keyword lists | Lowu2013Medium |
| **Format normalization** | Clean HTML, markdown, whitespace | BeautifulSoup, custom parsers | Low |
| **Data mixing / resampling** | Balance domains/languages | sampling weights, mixing ratios | Low |

**Compute requirements for preprocessing 10 TB of text:**

| Step | CPU Time | RAM | Storage (intermediate) |
|------|---------|-----|----------------------|
| Full pipeline | 5,000u201320,000 CPU-hours | 256 GBu20131 TB | 2u20135u00d7 input size |
| Deduplication (most expensive) | 5,000u201310,000 CPU-hours | 512 GBu20132 TB | 3u00d7 input size |
| Tokenization | 1,000u20135,000 CPU-hours | 64 GB | 1.5u00d7 input size |

### 7.4 Data Formats for Training

| Format | Description | Pros | Cons | Used By |
|--------|-------------|------|------|---------|
| **WebDataset (.tar)** | POSIX tar with paired files | Streaming-friendly, no random access needed | Requires pre-shuffling | HuggingFace, LAION |
| **TFRecord** | Protobuf-based sequential | Efficient, proven at scale | TensorFlow ecosystem | Google, TensorFlow |
| **MDS (Mosaic Data Silo)** | Columnar, memory-mapped | Fast random access, GPU-direct | MosaicML ecosystem | MosaicML / Databricks |
| **Parquet** | Columnar, compressed | Good compression, interop | Not ideal for streaming | General data engineering |
| **JSONL** | Line-delimited JSON | Simple, human-readable | Large, slow to parse | Prototyping, small data |
| **HDF5** | Hierarchical data format | Random access, chunking | Single-writer bottleneck | Scientific data |
| **LLM Dataset (LLM-DS)** | Emerging standard | Optimized for training | Early stage | Research |

### 7.5 DataLoader Performance: Feeding the GPU

PyTorch DataLoader is the bridge between storage and GPU training. Efficient data loading is critical:

**Key parameters:**

```python
from torch.utils.data import DataLoader

loader = DataLoader(
    dataset,
    batch_size=64,
    num_workers=8,          # Parallel data loading processes
    pin_memory=True,        # Page-locked memory for faster GPU transfer
    prefetch_factor=4,      # Prefetch batches ahead
    persistent_workers=True, # Keep workers alive between epochs
    collate_fn=custom_collate
)
```

**Throughput requirements:**

| Model Size | Tokens/second/GPU | Data Rate | DataLoader Workers |
|-----------|-------------------|-----------|-------------------|
| 7B params | ~50K tokens/s | ~100 MB/s | 4u20138 |
| 70B params | ~10K tokens/s | ~20 MB/s | 4u20138 |
| 400B params | ~5K tokens/s | ~10 MB/s | 4u20138 |

> Note: Larger models have lower tokens/second because each token requires more compute. Data loading is rarely the bottleneck for very large models u2014 compute dominates. For small models (7B), data loading can be the bottleneck.

### 7.6 Streaming Data from Object Storage

For very large datasets, streaming directly from object storage avoids the need to stage everything on local NVMe:

| Tool | Description | Throughput | Use Case |
|------|-------------|-----------|----------|
| **WebDataset** | Iterate over tar archives in S3/GCS | 500 MB/su20132 GB/s/node | LLM training at scale |
| **LitData** | Lightning-optimized streaming | 1u20135 GB/s/node | Lightning AI ecosystem |
| **TensorFlow Datasets** | Stream TFRecords from GCS | 500 MB/su20131 GB/s/node | TF-native workflows |
| **streaming (MosaicML)** | MDS format, cloud-native | 1u20133 GB/s/node | MosaicML platform |

---

## 8. Checkpoint I/O: The Hidden Bottleneck

### 8.1 Why Checkpoints Matter

Model checkpoints are periodic snapshots of training state saved for:
1. **Fault tolerance**: Resume training after node failure (GPU failure rate ~1u20135% per day in large clusters)
2. **Evaluation**: Test model at specific training steps
3. **Rollback**: Revert to a better checkpoint if training diverges

### 8.2 Checkpoint Sizes

| Model | Parameters | FP16 Weights | Optimizer State (AdamW, FP32) | **Total Checkpoint** |
|-------|-----------|-------------|-------------------------------|---------------------|
| Llama 2 7B | 7B | 14 GB | 56 GB | **70 GB** |
| Llama 2 70B | 70B | 140 GB | 560 GB | **700 GB** |
| Llama 3 405B | 405B | 810 GB | 3.24 TB | **4.05 TB** |
| DeepSeek-V3 671B (MoE) | 671B | 1,342 GB | 5.37 TB | **6.71 TB** |
| Frontier 1T+ | 1T+ | 2,000 GB | 8,000 GB | **10 TB** |
| Frontier 10T (future) | 10T | 20,000 GB | 80,000 GB | **100 TB** |

### 8.3 Checkpoint Time Impact

The time to save a checkpoint is **dead time** u2014 GPUs sit idle while state is written to storage.

**Checkpoint time by storage tier:**

| Checkpoint Size | 8u00d7 Gen5 NVMe (100 GB/s) | Distributed FS (20 GB/s) | S3 (10 GB/s upload) |
|----------------|------------------------|--------------------------|---------------------|
| 70 GB (7B model) | 0.7s | 3.5s | 7s |
| 700 GB (70B model) | 7s | 35s | 70s |
| 4 TB (405B model) | 40s | 200s (3.3 min) | 400s (6.7 min) |
| 10 TB (1T model) | 100s (1.7 min) | 500s (8.3 min) | 1,000s (16.7 min) |
| 100 TB (10T model) | 1,000s (16.7 min) | 5,000s (83 min) | 10,000s (167 min) |

**Impact on training efficiency:**

If checkpoints are saved every 1,000 steps (every ~30 minutes for a large model), and each checkpoint takes 10 minutes on distributed FS:
- **Training efficiency loss**: 10 / (30 + 10) = **25% wasted GPU time**
- At $3/GPU-hr u00d7 16K GPUs u00d7 25% waste = **$12,000/hour in wasted compute**

### 8.4 Checkpoint Strategies

| Strategy | Description | Save Time | GPU Downtime | Complexity |
|----------|-------------|-----------|-------------|-----------|
| **Synchronous** | Block training, save all state | Full (10u2013100s of seconds) | 100% | Low |
| **Asynchronous** | Copy to host RAM, train continues | Apparent: 1u20135s | ~5% | Medium |
| **Forked checkpoint** | Fork process, save from fork | Apparent: <1s | ~1% | High (OS-level) |
| **Incremental** | Save only changed parameters | 10u201350% of full | 10u201350% | High |
| **Distributed (FSDP/ZeRO)** | Each rank saves its shard | ~1/N of full | Moderate | Medium |
| **In-memory + background** | Save to RAM, async flush to disk | Apparent: <1s | ~0% | High |

### 8.5 PyTorch Distributed Checkpoint (DCP)

PyTorch's native distributed checkpoint (introduced in PyTorch 2.x) provides:

```python
import torch.distributed.checkpoint as dcp

# Save (each rank saves its own shard)
dcp.save(
    state_dict={"model": model, "optimizer": optimizer},
    checkpoint_id="/mnt/checkpoint/step_1000/",
    storage_reader=...,
)

# Load (reshard automatically for different parallelism configs)
dcp.load(
    state_dict={"model": model, "optimizer": optimizer},
    checkpoint_id="/mnt/checkpoint/step_1000/",
)
```

**Key features:**
- **Sharded save**: Each rank saves only its local shard u2192 Nu00d7 faster than gathering to one rank
- **Reshard on load**: Save with TP=8, load with TP=16 u2192 automatic resharding
- **Async save support**: Save in background while training continues
- **Single-file-per-rank**: Avoids filesystem metadata bottleneck

### 8.6 DeepSpeed ZeRO Checkpoint Behavior

| ZeRO Stage | What's Sharded | Checkpoint per Rank | Total Checkpoint I/O |
|-----------|---------------|--------------------|--------------------|
| ZeRO-1 | Optimizer states | ~model_size / N + optimizer / N | Parallel across ranks |
| ZeRO-2 | Optimizer + gradients | ~(model + optimizer) / N | Parallel across ranks |
| ZeRO-3 | Everything (params + grad + optimizer) | ~total_state / N | Parallel across ranks |

> With ZeRO-3 across 1,024 GPUs, a 10 TB checkpoint becomes ~10 GB per rank u2014 saving to local NVMe in <1 second.

### 8.7 Checkpoint Best Practices

1. **Save to local NVMe first**: Fastest possible save; async replicate to shared storage.
2. **Use sharded checkpoints**: Each GPU rank saves only its shard in parallel.
3. **Async checkpointing**: Don't block training u2014 fork a process or copy to host RAM first.
4. **Checkpoint every 1u20132 hours**: Balance between fault tolerance and overhead.
5. **Keep 2u20133 recent checkpoints**: Older ones on object storage for long-term retention.
6. **Validate checkpoint integrity**: Periodically load and verify (corrupted checkpoints waste days of training).
7. **Pre-plan resharding**: Save in a format that supports different parallelism configurations on load.

---

## 9. Storage Tiers & Data Lifecycle

### 9.1 The 5-Tier AI Data Model

```
u250cu2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2510
u2502               AI DATA LIFECYCLE & STORAGE TIERS              u2502
u2502                                                              u2502
u2502  u250cu2500u2500u2500u2500u2500u2500u2500u2500u2500u2510   HOT TIER (GPU HBM)                          u2502
u2502  u2502   T2    u2502   180-288 GB per GPU, 4.8-8 TB/s              u2502
u2502  u2502         u2502   Active model weights, KV cache, activations  u2502
u2502  u2514u2500u2500u2500u2500u252cu2500u2500u2500u2500u2518                                                   u2502
u2502       u2502                                                       u2502
u2502  u250cu2500u2500u2500u2500u2534u2500u2500u2500u2500u2510   WARM TIER (Local NVMe)                       u2502
u2502  u2502   T5    u2502   15-120 TB per node, 14-200 GB/s              u2502
u2502  u2502         u2502   Checkpoints, tokenized data cache, logits     u2502
u2502  u2514u2500u2500u2500u2500u252cu2500u2500u2500u2500u2518                                                   u2502
u2502       u2502                                                       u2502
u2502  u250cu2500u2500u2500u2500u2534u2500u2500u2500u2500u2510   SHARED TIER (Distributed FS)                 u2502
u2502  u2502   T6    u2502   100 TB-10 PB, 100-500 GB/s                   u2502
u2502  u2502         u2502   Training datasets, shared checkpoints         u2502
u2502  u2514u2500u2500u2500u2500u252cu2500u2500u2500u2500u2518                                                   u2502
u2502       u2502                                                       u2502
u2502  u250cu2500u2500u2500u2500u2534u2500u2500u2500u2500u2510   COLD TIER (Object Storage Standard)          u2502
u2502  u2502   T7    u2502   Unlimited, 10-120 GB/s                        u2502
u2502  u2502         u2502   Raw datasets, model artifacts, audit logs     u2502
u2502  u2514u2500u2500u2500u2500u252cu2500u2500u2500u2500u2518                                                   u2502
u2502       u2502                                                       u2502
u2502  u250cu2500u2500u2500u2500u2534u2500u2500u2500u2500u2510   ARCHIVE TIER (Glacier/Archive)               u2502
u2502  u2502   T8    u2502   Unlimited, hours to retrieve                  u2502
u2502  u2502         u2502   Compliance, historical data, old experiments  u2502
u2502  u2514u2500u2500u2500u2500u2500u2500u2500u2500u2500u2518                                                   u2502
u2514u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2518
```

### 9.2 Data Lifecycle by ML Phase

| Phase | Hot Data | Warm Data | Cold Data |
|-------|----------|-----------|-----------|
| **Data collection** | u2014 | Ingestion buffers | Raw web crawl, documents |
| **Preprocessing** | Working shards | Cleaned datasets | Original raw data |
| **Training** | Tokenized batches (GPU HBM) | Training data cache (NVMe) | Full dataset (object storage) |
| **Checkpointing** | Active checkpoint (NVMe) | Recent checkpoints (FS) | Historical checkpoints (S3) |
| **Evaluation** | Model weights (GPU) | Eval datasets (NVMe/FS) | Benchmark results (S3) |
| **Deployment** | Model weights (GPU serving) | Model registry (FS) | Model versions (S3) |
| **RAG serving** | Embeddings cache (RAM) | Vector index (NVMe) | Source documents (S3) |

### 9.3 Data Movement Patterns

| Pattern | Source u2192 Destination | Frequency | Trigger |
|---------|---------------------|-----------|---------|
| **Ingestion** | Internet/Crawler u2192 Object Storage | Continuous | Data collection pipeline |
| **Staging** | Object Storage u2192 Distributed FS | Per-training-run | Training job start |
| **Caching** | Distributed FS u2192 Local NVMe | Per-node | Data prefetch |
| **Training feed** | Local NVMe u2192 GPU HBM | Every iteration | DataLoader |
| **Checkpoint save** | GPU HBM u2192 Local NVMe | Every 1u20132 hours | PyTorch checkpoint |
| **Checkpoint replicate** | Local NVMe u2192 Distributed FS / S3 | Async after save | Durability |
| **Model deploy** | S3/FS u2192 Serving GPU HBM | Per-deployment | CI/CD pipeline |
| **Vector index build** | Documents u2192 Vector DB | Daily/weekly | Document update |

---

## 10. Storage Vendor Landscape

### 10.1 Storage System Vendors

| Vendor | Key Products | Target Market | Notable Feature |
|--------|-------------|--------------|----------------|
| **NetApp** | ONTAP AI, AFF A900 | Enterprise AI | Data management, cloning |
| **Pure Storage** | FlashBlade//S, FlashArray//XL | AI data pipelines | 100+ GB/s per blade, Evergreen |
| **DDN** | AI400X2, EXAScaler (Lustre) | HPC + AI | NVIDIA DGX-certified, 200+ GB/s |
| **IBM** | Storage Scale (GPFS), FlashSystem | Enterprise, financial | Compliance, encryption |
| **WekaIO** | WekaFS | Cloud-native AI | NVMe + S3 in single namespace |
| **VAST Data** | VAST Data Platform | Enterprise AI | Disaggregated shared-everything |
| **HPE** | Cray ClusterStor (Lustre) | HPC / AI | Cray EX integration |
| **Dell** | PowerScale (Isilon), PowerVault | Enterprise AI | Multi-protocol, scale-out |
| **Hitachi Vantara** | VSP One | Enterprise | Data resilience |

### 10.2 NVMe SSD Vendors

| Vendor | Key Products | Capacity | Interface |
|--------|-------------|----------|-----------|
| **Samsung** | PM1743, PM9C1a | Up to 15.36 TB | PCIe Gen5 |
| **Micron** | 9400, 6500 ION | Up to 15.36 TB | PCIe Gen5 |
| **Solidigm (SK hynix)** | D7-P5810, D5-P5336 | Up to 61.44 TB (QLC) | PCIe Gen5 |
| **Kioxia** | CM7, CD8P | Up to 12.8 TB | PCIe Gen5 |
| **Western Digital** | Ultrastar DC SN861 | Up to 12.8 TB | PCIe Gen5 |

### 10.3 Vector Database Vendors

| Vendor | Product | Deployment | Pricing Model |
|--------|---------|-----------|--------------|
| **Pinecone** | Pinecone | Managed cloud | Per-vector + query ($0.096/GB/mo storage) |
| **Zilliz** | Milvus (managed) | Managed cloud | Per-node ($0.50u20132.00/hr) |
| **Weaviate** | Weaviate DB | Self-hosted / managed | Per-node (enterprise) |
| **Qdrant** | Qdrant Cloud | Managed cloud | Per-node ($0.05u20130.50/hr) |
| **Chroma** | Chroma DB | Self-hosted | Free (open source) |

---

## 11. Cost Analysis: Storage TCO for AI

### 11.1 Storage Cost for a 10 PB AI Training Cluster

| Component | Capacity | $/TB/month | Monthly Cost | Notes |
|-----------|----------|-----------|-------------|-------|
| NVMe Gen5 array (local) | 2 PB | $500 | $1,000,000 | 4u00d7 per GPU node |
| Distributed FS (Lustre) | 5 PB | $350 | $1,750,000 | Shared training data |
| Object Storage (S3 Standard) | 10 PB | $23 | $230,000 | Raw + archive |
| Object Storage (Glacier) | 20 PB | $4 | $80,000 | Long-term archive |
| Vector DB cluster | 500 TB | $800 | $400,000 | RAG infrastructure |
| Data pipeline compute | u2014 | u2014 | $200,000 | Preprocessing CPUs |
| **Total** | **~37.5 PB** | u2014 | **$3,660,000/mo** | |

### 11.2 Storage Cost Breakdown by Phase

| ML Phase | Storage Type | Data Volume | Monthly Cost | % of Total |
|----------|-------------|------------|-------------|-----------|
| Data ingestion | S3 Standard | 5u201320 PB | $115Ku2013$460K | 10u201315% |
| Preprocessing | Distributed FS + CPU | 5u201310 PB | $500Ku2013$1M | 20u201325% |
| Training | NVMe + Distributed FS | 1u20135 PB | $2Mu2013$5M | 50u201360% |
| Serving | NVMe + Vector DB | 100 TBu20131 PB | $200Ku2013$800K | 10u201315% |
| Archive | S3 Glacier | 20u2013100 PB | $80Ku2013$400K | 3u20135% |

### 11.3 Cost Optimization Strategies

| Strategy | Savings | Implementation |
|----------|---------|---------------|
| **Tier data aggressively** | 40u201360% | Auto-lifecycle policies: NVMe u2192 FS u2192 S3 u2192 Glacier |
| **Compress training data** | 30u201350% | zstd compression on tokenized datasets (2:1 ratio) |
| **Use spot/preemptible for preprocessing** | 60u201380% | Data pipelines don't need SLA-guaranteed compute |
| **Minimize egress** | 20u201350% | Keep data in same cloud/region as compute |
| **Deduplicate before storage** | 40u201360% | Remove duplicate documents before staging |
| **Shared checkpoint pool** | 30u201340% | Use distributed FS instead of per-node NVMe for checkpoints |
| **Snapshot-based checkpoint** | 50u201370% | Copy-on-write snapshots instead of full copy |

---

## 12. Future Outlook 2026u20132028

### 12.1 Emerging Storage Technologies

| Technology | Description | Timeline | Impact |
|-----------|-------------|----------|--------|
| **CXL 3.0 Memory Expansion** | Disaggregated memory pool via CXL fabric | 2026u20132027 | GPU nodes share terabytes of remote memory; reduces data movement |
| **CXL-attached persistent memory** | Persistent memory accessible via CXL | 2027 | Checkpoint to CXL memory at DRAM speeds (~100 GB/s) |
| **Computational Storage** | NVMe SSDs with embedded processors | 2026 | Offload compression, filtering, and preprocessing to storage |
| **Storage-Class Memory (SCM)** | Byte-addressable persistent memory | 2027+ | Bridges gap between DRAM and NVMe |
| **Direct Data Placement (DPP)** | GPU-direct storage access (RDMA) | 2026 | Bypasses CPU; data flows directly from NVMe u2192 GPU HBM |
| **KV-cache offload to CXL** | Serve KV-cache from CXL-attached memory | 2026u20132027 | 10u00d7 larger context windows without GPU memory expansion |

### 12.2 Checkpoint I/O Evolution

| Generation | Checkpoint Approach | Save Time (10 TB) | GPU Downtime |
|-----------|---------------------|-------------------|-------------|
| **2024: Synchronous** | Save to local NVMe | 100s (1.7 min) | 100% |
| **2025: Async + sharded** | Parallel sharded save + async replication | ~10s apparent | ~5% |
| **2026: Forked checkpoint** | OS-level process fork, save from snapshot | <1s apparent | ~1% |
| **2027: CXL-attached** | Copy to persistent CXL memory | <0.1s | ~0% |
| **2028: Distributed snapshot** | Coordinated distributed memory snapshot | Near-zero | ~0% |

### 12.3 Key Predictions

1. **Checkpoint I/O will be solved by CXL** u2014 Co-packaged CXL memory will allow near-instant checkpoints, eliminating the #1 storage bottleneck in training.

2. **Vector databases will consolidate to 3u20134 players** u2014 Currently fragmented market will consolidate around Pinecone (managed), Milvus (open source), Qdrant (performance), and pgvector (lightweight).

3. **Data preprocessing will move to GPUs** u2014 Tokenization, filtering, and deduplication are increasingly GPU-accelerated (e.g., NVIDIA DALI, RAPIDS cuDF), reducing preprocessing time by 10u201350u00d7.

4. **Multimodal data will dominate storage** u2014 Video training data (Sora, Gemini) is 100u20131000u00d7 larger per sample than text. Storage systems must adapt to streaming multi-GB video files.

5. **Object storage egress costs will face regulatory pressure** u2014 Governments will push for zero-egress-fee cloud storage, reducing AI data transfer costs by 50u201380%.

6. **Disaggregated storage will be standard for AI clouds** u2014 Storage nodes separate from compute nodes, connected via CXL or high-speed fabric, enabling independent scaling.

---

## 13. Key Takeaways

1. **Storage is the silent killer of GPU utilization.** Poor checkpoint I/O alone can waste 15u201330% of GPU time on large training runs. Use local NVMe + async saves.

2. **The storage hierarchy matters.** Keep hot data close to the GPU (NVMe), warm data on distributed FS, and cold data on object storage. Each tier is 3u201310u00d7 cheaper but 10u2013100u00d7 slower.

3. **Egress costs dominate object storage TCO.** Reading 1 PB from S3 costs more in egress ($50Ku2013$120K) than in storage ($23K/month). Keep data local to compute.

4. **Distributed file systems are essential for multi-node training.** Lustre for the largest clusters; BeeGFS for cost-effectiveness; WekaIO for cloud-native deployments.

5. **Vector databases are now core infrastructure.** With 40%+ of enterprise AI using RAG, vector DB selection (Pinecone, Milvus, Qdrant) is a first-class infrastructure decision.

6. **Checkpoint sizes are growing faster than storage bandwidth.** 10 TB checkpoints are here today; 100 TB checkpoints are coming. Sharded + async checkpointing is mandatory.

7. **CXL will transform the storage-memory boundary.** CXL-attached memory and persistent memory will bridge the gap between DRAM and NVMe, enabling near-instant checkpoints.

---

## References & Further Reading

1. PyTorch Distributed Checkpoint Documentation u2014 PyTorch, 2025
2. DeepSpeed ZeRO: Memory Optimizations Toward Training Trillion Parameter Models u2014 Rajbhandari et al., SC 2020
3. "The Pile: An 800GB Dataset of Diverse Text for Language Modeling" u2014 Gao et al., 2020
4. NVIDIA DALI: Data Loading Library Documentation u2014 NVIDIA, 2025
5. "Deduplicating Training Data Makes Language Models Better" u2014 Lee et al., ACL 2022
6. Lustre File System Architecture Guide u2014 OpenSFS, 2024
7. WekaIO Architecture Whitepaper u2014 WekaIO, 2025
8. FAISS: A Library for Efficient Similarity Search u2014 Facebook Research, 2024
9. Milvus Architecture Documentation u2014 Zilliz, 2025
10. "Scaling Laws for Neural Language Models" u2014 Kaplan et al., 2020

---

> Navigation: [u2190 AI Infra Overview](ai_infra_overview.md) | [Networking & Interconnect u2190](02_networking_interconnect.md) | [Data Center Physical u2192](04_datacenter_physical.md)
