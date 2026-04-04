# SK Hynix - Comprehensive Analysis Report

---

## 1. Company Overview & Corporate Structure

### Company Profile

| Item | Detail |
|------|--------|
| **Legal Name** | SK Hynix Inc. (에스케이하이닉스) |
| **Ticker** | KRX: 000660 |
| **Founded** | 1983 (as Hyundai Electronics Industries) |
| **HQ** | Icheon, Gyeonggi-do, South Korea |
| **CEO** | Kwak Noh-Jung (곽노정) |
| **Chairman** | Chey Tae-won (최태원, SK Group Chairman) |
| **Employees** | ~37,000+ (2024) |
| **Market Cap** | ~₩130 trillion (~$95B USD, as of mid-2025) |
| **Industry** | Semiconductors — Memory (DRAM, NAND Flash, HBM) |

### History & Evolution

| Year | Milestone |
|------|-----------|
| 1983 | Founded as **Hyundai Electronics Industries** |
| 1999 | Acquired LG Semiconductor, merged memory operations |
| 2001 | Renamed to **Hynix Semiconductor** |
| 2012 | Acquired by **SK Telecom** (SK Group), renamed **SK Hynix** |
| 2013 | Entered NAND Flash market (acquired LAMD from Toshiba) |
| 2017 | Acquired **Intel's NAND SSD business** for $9B (completed 2021) |
| 2021 | Solidigm launched as standalone SSD subsidiary |
| 2024 | Mass production of **HBM3E** — sole supplier to NVIDIA for H200/B200 |
| 2025 | HBM3E 12-layer (36GB) in mass production; HBM4 development on track |

### Ownership Structure (SK Group)

```
SK Holdings
  └── SK Inc. (holding company, Chey Tae-won as Chairman)
       └── SK Hynix Inc. (KRX: 000660)
            ├── Solidigm (NAND SSD subsidiary, ex-Intel NAND)
            ├── SK Hynix System IC (system semiconductor foundry)
            ├── SK Hynix America (San Jose, USA)
            ├── SK Hynix Europe (Munich, Germany)
            ├── SK Hynix China (Wuxi, Chongqing, Dalian fabs)
            └── SK Hynix Japan (Tokyo)
```

### Manufacturing Sites

| Location | Fab | Focus |
|----------|-----|-------|
| **Icheon (M14, M15, M16, M17)** | Korea | DRAM (DDR5, LPDDR5X, HBM3E) |
| **Cheongju (C2F)** | Korea | CMOS Image Sensors, specialty DRAM |
| **Wuxi** | China | DRAM (older nodes, ~20% of total DRAM output) |
| **Dalian** | China | NAND Flash (ex-Intel fab) |
| **Chongqing** | China | NAND Flash packaging & test |
| **Bucheon** | Korea | New fab construction (HBM4 & next-gen DRAM, planned 2027+) |

### Key Subsidiary: Solidigm

- **Origin**: Intel's NAND SSD division (acquired 2021 for $9B)
- **Focus**: Enterprise & client NVMe SSDs (PCIe Gen5)
- **Products**: P-series, D-series enterprise SSDs
- **Role**: Vertical integration — consumes SK Hynix NAND flash

### Leadership

| Role | Name | Background |
|------|------|------------|
| **CEO** | Kwak Noh-Jung | SK Hynix veteran, CTO before CEO appointment (2022) |
| **President (DRAM)** | Kim Ki-sun | DRAM product engineering |
| **President (NAND)** | Ryu Byung-hoon | NAND & SSD strategy |
| **CFO** | Kim Woo-hyun | Finance & IR |

---

## 2. Business Segments & Product Portfolio

### Revenue Mix (2024 Estimate)

| Segment | Share (%) | Revenue (₩T) | YoY Growth |
|---------|-----------|---------------|------------|
| **DRAM** | ~72% | ~38T | +80%+ |
| **NAND Flash** | ~25% | ~13T | +40%+ |
| **CIS & Others** | ~3% | ~1.5T | Flat |
| **Total** | 100% | ~52T | +70%+ |

> DRAM dominance intensified in 2024 due to explosive HBM demand from AI servers.

---

### 2.1 DRAM Products

| Product | Type | Key Specs | Target Market |
|---------|------|-----------|---------------|
| **DDR5** | Standard DRAM | Up to 6400 Mbps, 1a nm | Servers, PCs, Workstations |
| **DDR4** | Standard DRAM | 3200 Mbps, 1Y nm | Legacy servers, PCs |
| **LPDDR5X** | Mobile DRAM | Up to 9600 Mbps, 1a nm | Smartphones (iPhone, Galaxy), AI phones |
| **LPDDR5T** | Mobile DRAM | 9600 Mbps | Premium smartphones |
| **HBM3E** | High Bandwidth Memory | 8-layer/12-layer, 36GB/stack, 1.2 TB/s | AI Accelerators (NVIDIA H200, B200) |
| **HBM3** | High Bandwidth Memory | 8-layer, 24GB/stack | AI Accelerators (NVIDIA H100) |
| **Graphics DDR6X** | Graphics DRAM | 24 Gbps | NVIDIA/AMD GPUs |
| **Server DRAM** | Registered DIMM | DDR5 RDIMM, MCR DIMM | Data center servers |

#### DRAM Technology Nodes

| Node | Status | Products |
|------|--------|----------|
| **1Y nm** | Legacy | DDR4, LPDDR4X |
| **1a nm** | Volume production | DDR5, LPDDR5X, HBM3 |
| **1b nm** | Ramp-up (2024-2025) | DDR5, LPDDR5X, HBM3E |
| **1c nm** | Development (2025-2026) | Next-gen DDR6/LPDDR6, HBM4 |

---

### 2.2 High Bandwidth Memory (HBM) — Crown Jewel

| Generation | Status | Capacity | Bandwidth | Key Customer |
|------------|--------|----------|-----------|--------------|
| **HBM2E** | Legacy | 16GB (8-layer) | ~460 GB/s | Older GPUs |
| **HBM3** | Volume | 24GB (8-layer) | ~820 GB/s | NVIDIA H100, AMD MI300 |
| **HBM3E 8-layer** | Mass production | 24GB | ~1.2 TB/s | NVIDIA H200 |
| **HBM3E 12-layer** | Mass production (2025) | 36GB | ~1.2 TB/s | NVIDIA B200/B300 |
| **HBM4** | Development (2026) | 48GB+ | ~2 TB/s | Next-gen NVIDIA/AMD |

#### HBM Market Position

- **#1 market share in HBM** (~50%+ in 2024)
- **Sole initial supplier** of HBM3E to NVIDIA for H200/B200
- **Key differentiator**: Advanced TSV (Through-Silicon Via) packaging, 12-layer stacking
- **Capacity**: ~100K+ wafers/month dedicated to HBM (expanding aggressively)
- **Revenue contribution**: HBM grew from <5% of DRAM revenue (2023) to ~30%+ (2025)

---

### 2.3 NAND Flash Products

| Product | Type | Key Specs | Target Market |
|---------|------|-----------|---------------|
| **4D NAND (176-layer)** | Mainstream | TLC, V-NAND architecture | Client SSDs, smartphones, automotive |
| **4D NAND (238-layer)** | Next-gen | TLC/QLC, higher density | Enterprise SSDs, data centers |
| **321-layer NAND** | Development | TLC, next-gen | Future enterprise/DC |

#### NAND Technology Roadmap

| Generation | Layers | Status |
|------------|--------|--------|
| 128-layer | 128 | Legacy |
| 176-layer | 176 | Volume production |
| 238-layer | 238 | Ramp-up (2025) |
| 321-layer | 321 | Development (2026+) |

---

### 2.4 Solidigm (Enterprise SSD Subsidiary)

| Category | Products | Interface |
|----------|----------|-----------|
| Enterprise SSDs | D7-P5810, D7-P5520, D5-P5336 | PCIe Gen5 / Gen4 |
| Client SSDs | P44 Pro, P41 Plus | PCIe Gen4 NVMe |
| Specialty | High-density QLC SSDs (61.44TB) | PCIe Gen5 |

- Revenue contribution: ~₩3-4T annually
- Strategic value: Vertical integration (SK Hynix NAND → Solidigm SSDs)

---

### 2.5 CMOS Image Sensors (CIS)

- Manufactured at Cheongju fab (C2F)
- Focus: Automotive, industrial, mobile
- Relatively small segment (~3% revenue)
- Competition: Samsung LSI, Sony (dominant), OmniVision

---

### Product Mix Evolution (2019 → 2025)

```
2019:  DDR4 ████████████████████ 70%  |  NAND ██████ 25%  | CIS █ 5%
2022:  DDR5/DD4 ████████████████ 65%  |  NAND ████████ 30%  | CIS █ 5%
2024:  DDR5/HBM █████████████████████ 72%  |  NAND ██████ 25%  | CIS █ 3%
2025E: DDR5/HBM ██████████████████████ 75%  |  NAND █████ 22%  | CIS █ 3%
                              ↑ HBM becoming dominant growth driver
```

---

## 3. Financial Statements Analysis

### 3.1 Revenue Trend (Quarterly, ₩ Trillion)

| Quarter | Revenue | YoY Change | QoQ Change | Driver |
|---------|---------|------------|------------|--------|
| **Q1 2023** | 5.1T | -58% | -34% | Memory downturn trough |
| **Q2 2023** | 7.3T | -47% | +43% | Inventory correction, price stabilization |
| **Q3 2023** | 9.1T | -18% | +25% | DDR5 adoption, server demand recovery |
| **Q4 2023** | 11.3T | +47% | +24% | HBM3 ramp, AI demand surge |
| **Q1 2024** | 12.4T | +144% | +10% | HBM3E mass production begins |
| **Q2 2024** | 16.4T | +125% | +32% | AI server DRAM boom, ASP recovery |
| **Q3 2024** | 17.6T | +94% | +7% | HBM3E volume, enterprise SSD |
| **Q4 2024** | 19.8T | +75% | +13% | Record quarter, HBM3E 12-layer ramp |
| **Q1 2025E** | 17.0T | +37% | -14% | Seasonal, but HBM still strong |
| **Q2 2025E** | 20.0T+ | +22% | +18% | HBM4 prep, DDR5 server cycle |

> **Revenue CAGR (2023→2025): ~80%+** — fastest growth in company history driven by AI.

---

### 3.2 Annual Income Statement (₩ Trillion)

| Metric | 2021 | 2022 | 2023 | 2024 | 2025E |
|--------|------|------|------|------|-------|
| **Revenue** | 42.0T | 44.6T | 32.8T | 66.1T | 75T+ |
| **COGS** | 29.4T | 37.8T | 29.6T | 38.0T | 42T |
| **Gross Profit** | 12.6T | 6.8T | 3.2T | 28.1T | 33T+ |
| **Gross Margin** | 30.0% | 15.2% | 9.8% | 42.5% | ~44% |
| **Operating Profit** | 8.5T | 1.8T | -2.0T | 23.5T | 28T+ |
| **Operating Margin** | 20.2% | 4.0% | -6.1% | 35.6% | ~37% |
| **Net Income** | 6.2T | 1.6T | -3.4T | 19.4T | 23T+ |
| **Net Margin** | 14.8% | 3.6% | -10.4% | 29.3% | ~31% |

#### Profitability Trajectory

```
Operating Margin (%)
 40% │                                    ████ 35.6%
     │                              ████  │
 30% │                              29.3% │
     │                        ████  │     │
 20% │  20.2%                 │     │     │
     │   ████                 │     │     │
 10% │   │              9.8%  │     │     │
     │   │    15.2%      │    │     │     │
  0% │   │     ████      │    │     │     │
     │   │      │   4.0% │    │     │     │
-10% │   │      │    │  -6.1% │     │     │
     └───┼──────┼────┼───┼─────┼─────┼─────
        2021   2022  2023 2024  2025E
              ↑ Trough         ↑ AI supercycle
```

---

### 3.3 Balance Sheet Highlights (₩ Trillion, End of 2024)

| Item | Amount | Notes |
|------|--------|-------|
| **Total Assets** | ~90T | Major expansion from ~65T (2023) |
| **Cash & Equivalents** | ~12T | Strong cash generation |
| **Total Debt** | ~18T | Including long-term bonds |
| **Shareholders' Equity** | ~55T | Book value growing rapidly |
| **Debt-to-Equity** | ~0.33x | Conservative leverage |
| **Net Debt** | ~6T | Cash-rich after debt repayment |

---

### 3.4 Cash Flow & Capital Expenditure (₩ Trillion)

| Metric | 2022 | 2023 | 2024 | 2025E |
|--------|------|------|------|-------|
| **Operating Cash Flow** | 9.5T | 4.2T | 28.0T | 32T+ |
| **Capex** | 10.3T | 6.8T | 12.5T | 20T+ |
| **Free Cash Flow** | -0.8T | -2.6T | 15.5T | 12T+ |
| **FCF Margin** | -1.8% | -7.9% | 23.4% | ~16% |

> **2025 Capex surge**: ₩20T+ planned — largest ever, for HBM4 capacity and Bucheon new fab.

---

### 3.5 Key Financial Ratios

| Ratio | 2022 | 2023 | 2024 | 2025E |
|-------|------|------|------|-------|
| **ROE** | 4.3% | -8.2% | 35.3% | ~42% |
| **ROA** | 2.5% | -5.0% | 21.6% | ~26% |
| **ROIC** | 3.8% | -7.0% | 30.0% | ~35% |
| **Asset Turnover** | 0.69x | 0.50x | 0.73x | ~0.83x |
| **Current Ratio** | 1.8x | 2.1x | 2.5x | ~2.3x |

#### ROE DuPont Breakdown (2024)

```
ROE = Net Margin × Asset Turnover × Equity Multiplier
35.3% =  29.3%    ×     0.73x      ×     1.64x
              ↑           ↑               ↑
        Strong pricing  Good utilization  Moderate leverage
```

---

### 3.6 Dividend & Shareholder Returns

| Item | Detail |
|------|--------|
| **Dividend Policy** | Annual dividend, ~20-25% payout ratio target |
| **2024 DPS** | ~₩2,000/share (estimated) |
| **Dividend Yield** | ~1.0-1.5% |
| **Buybacks** | Occasional, not systematic |
| **Treasury Shares** | Held but limited |

> SK Hynix prioritizes reinvestment (HBM4, new fabs) over shareholder returns during growth phase.

---

## 4. HBM / AI Memory Market & SK Hynix Positioning

### 4.1 HBM Market Overview

| Metric | 2023 | 2024 | 2025E | 2026E |
|--------|------|------|-------|-------|
| **HBM TAM** | $4.0B | $8.9B | $17B+ | $25B+ |
| **YoY Growth** | +50% | +122% | +91% | +47% |
| **HBM as % of DRAM** | ~3% | ~8% | ~15% | ~20%+ |
| **Total DRAM TAM** | $85B | $110B | $135B | $150B |

> HBM is the fastest-growing segment in semiconductor history — driven entirely by AI accelerator demand.

---

### 4.2 HBM Market Share (2024)

| Company | Share | Key Customers | Status |
|---------|-------|---------------|--------|
| **SK Hynix** | **~52%** | NVIDIA (H200, B200), AMD (MI300) | #1, sole HBM3E supplier to NVIDIA initially |
| **Samsung** | ~38% | NVIDIA (qualified), Google (TPU), custom ASICs | Catching up, HBM3E qualified late 2024 |
| **Micron** | ~10% | NVIDIA (qualified HBM3E), AMD | Small but growing, HBM3E production 2025 |

```
HBM Market Share (2024)
  SK Hynix  ████████████████████████████  52%
  Samsung   ██████████████████████        38%
  Micron    █████                         10%
```

---

### 4.3 NVIDIA Supply Relationship — Strategic Moat

#### Why SK Hynix Leads in NVIDIA HBM

| Factor | SK Hynix Advantage |
|--------|--------------------|
| **First-mover in HBM3E** | Mass production 6+ months ahead of Samsung/Micron |
| **TSV Yield** | Industry-leading ~80%+ yield on 12-layer stacking |
| **Thermal Performance** | Superior thermal management (critical for B200 1000W+ TDP) |
| **Co-development** | Deep technical collaboration with NVIDIA since HBM2E era |
| **Capacity Commitment** | Dedicated HBM lines at Icheon M15X/M16X fabs |

#### NVIDIA HBM Procurement (Estimated)

| GPU | HBM Type | Supplier Split (SK Hynix : Samsung : Micron) |
|-----|----------|-----------------------------------------------|
| H100 (2023) | HBM3 | 60 : 30 : 10 |
| H200 (2024) | HBM3E 8-layer | **80 : 15 : 5** |
| B200 (2025) | HBM3E 12-layer | **60 : 25 : 15** |
| B300/Next-gen (2026) | HBM4 | 50 : 30 : 20 (estimated) |

> SK Hynix's share dilutes as Samsung/Micron ramp, but it remains **primary supplier** through 2026+.

---

### 4.4 HBM Roadmap & Technology Differentiation

| Generation | SK Hynix | Samsung | Micron |
|------------|----------|---------|--------|
| **HBM3** (2023) | ✅ Volume | ✅ Volume | ❌ Skipped |
| **HBM3E 8-layer** (2024) | ✅ Mass prod | ✅ Qualified | ✅ Samples |
| **HBM3E 12-layer** (2025) | ✅ Mass prod | ⏳ Qualification | ⏳ Development |
| **HBM4** (2026) | 🔧 Development | 🔧 Development | 🔧 Development |
| **HBM4E / HBM5** (2027+) | 📋 Planning | 📋 Planning | 📋 Planning |

#### SK Hynix HBM4 Roadmap

- **Target**: 2026 H2 mass production
- **Capacity**: 48GB+ per stack, ~2 TB/s bandwidth
- **Architecture**: Base die with logic (custom I/O), possible 16-layer stacking
- **Manufacturing**: Bucheon new fab (M8X) dedicated to HBM4
- **Investment**: ₩20T+ capex in 2025, significant portion for HBM4 capacity

---

### 4.5 AI-Driven Memory Demand Outlook

#### AI Accelerator DRAM Requirements

| Accelerator | HBM Capacity | # of Stacks | DRAM per Unit |
|-------------|-------------|-------------|---------------|
| NVIDIA H100 | 80GB | 5 × HBM3 | 80 GB |
| NVIDIA H200 | 141GB | 6 × HBM3E | 141 GB |
| NVIDIA B200 | 192GB | 8 × HBM3E | 192 GB |
| NVIDIA B300 | 288GB (est) | 8 × HBM4 | 288 GB |
| Google TPU v6 | ~128GB | Custom HBM | ~128 GB |
| AMD MI400 | ~256GB (est) | 8 × HBM4 | ~256 GB |

#### AI Server DRAM Demand Projection

| Year | AI GPU Shipments (M units) | HBM Demand (GB) | HBM Revenue |
|------|---------------------------|------------------|-------------|
| 2023 | ~2.0M | ~160B GB | ~$4B |
| 2024 | ~3.5M | ~500B GB | ~$9B |
| 2025E | ~6.0M | ~1,200B GB | ~$17B |
| 2026E | ~8.0M | ~2,300B GB | ~$25B |

---

### 4.6 Pricing Power & ASP Trend

| HBM Generation | ASP (est.) | vs. Standard DRAM Premium |
|----------------|-----------|--------------------------|
| HBM3 | ~$25-30/GB | 5-6x premium |
| HBM3E 8-layer | ~$30-40/GB | 6-8x premium |
| HBM3E 12-layer | ~$35-45/GB | 7-9x premium |
| HBM4 (projected) | ~$40-55/GB | 8-11x premium |

> **Pricing power**: SK Hynix commands significant premium due to limited supply and strong demand. HBM pricing is expected to remain elevated through 2026 as demand outpaces supply additions.

#### Key Insight
SK Hynix's HBM3E 12-layer (36GB) is currently the **only product** qualified for NVIDIA B200 in volume. This gives SK Hynix pricing power of ~3-5x gross margin vs. commodity DRAM.

---

## 5. Competitive Landscape

### 5.1 DRAM Market Share (2024)

| Company | Share | Revenue (est.) | Strengths | Weaknesses |
|---------|-------|----------------|-----------|------------|
| **Samsung** | ~40% | ~$44B | Scale, vertical integration, foundry tie-in | HBM yield issues, late to HBM3E |
| **SK Hynix** | ~32% | ~$38B | HBM leadership, NVIDIA partnership | Smaller scale, limited product breadth |
| **Micron** | ~23% | ~$25B | US-based, strong enterprise, 1β node | Late to HBM, small mobile share |
| **Others (Nanya, etc.)** | ~5% | ~$5B | Niche/specialty | Marginal players |

```
DRAM Market Share (2024)
  Samsung   ████████████████████████  40%
  SK Hynix  ███████████████████       32%
  Micron    █████████████             23%
  Others    ███                        5%
```

---

### 5.2 NAND Flash Market Share (2024)

| Company | Share | Layers | Strengths | Weaknesses |
|---------|-------|--------|-----------|------------|
| **Samsung** | ~35% | 236-layer (V-NAND) | First mover, broad portfolio | Aggressive pricing cannibalizes margins |
| **SK Hynix** | ~20% | 238-layer (4D NAND) | Solidigm integration, enterprise SSD | Smaller consumer presence |
| **Kioxia (WDC JV)** | ~17% | 218-layer (BiCS) | Apple supply, joint fab with WDC | Financial instability, delayed IPO |
| **Western Digital** | ~13% | 218-layer (BiCS) | Consumer market (SanDisk), data center | Margin pressure, split from Kioxia |
| **Micron** | ~10% | 232-layer | Crucial consumer brand, data center | Lagging in layers, exiting 3D XPoint |
| **YMTC (China)** | ~5% | 232-layer (Xtacking) | Aggressive pricing, China market | US sanctions, limited export access |

```
NAND Market Share (2024)
  Samsung       ██████████████████████   35%
  SK Hynix      ████████████             20%
  Kioxia/WDC    ██████████               17%
  Western Dig.  ████████                 13%
  Micron        ██████                   10%
  YMTC          ███                       5%
```

---

### 5.3 Technology Node Comparison

#### DRAM Process Nodes

| Node | Samsung | SK Hynix | Micron |
|------|---------|----------|--------|
| **1a nm** (10-12nm) | ✅ Volume | ✅ Volume | ✅ Volume |
| **1b nm** (10nm) | ✅ Volume | ✅ Ramp-up | ✅ Volume (1β) |
| **1c nm** (sub-10nm) | 🔧 Development | 🔧 Development | 🔧 Development |
| **EUV Adoption** | Partial (since 2020) | Partial (2024+) | Not yet (Multi-Patterning) |
| **Leading Edge** | 1b nm EUV | 1b nm (DUV + EUV mix) | 1β nm (Multi-Patterning) |

> Samsung leads in EUV adoption, Micron leads in conventional multi-patterning density, SK Hynix leads in **HBM packaging** (which matters more for AI revenue).

#### NAND Layer Count

| Company | Current | Next-gen | Development |
|---------|---------|----------|-------------|
| Samsung | 236-layer | ~300-layer | 400+ layer |
| SK Hynix | 238-layer | 321-layer | 400+ layer |
| Micron | 232-layer | ~280-layer | 430+ layer (2028) |
| Kioxia/WDC | 218-layer | ~300-layer | TBD |
| YMTC | 232-layer | ~300-layer | TBD |

---

### 5.4 HBM Race Status (Critical Battleground)

| Dimension | SK Hynix | Samsung | Micron |
|-----------|----------|---------|--------|
| **HBM3** | ✅ First to volume | ✅ 6 months later | ❌ Skipped |
| **HBM3E 8-layer** | ✅ First (Q1 2024) | ✅ Qualified (Q3 2024) | ✅ Samples (Q4 2024) |
| **HBM3E 12-layer** | ✅ Mass prod (Q1 2025) | ⏳ Qualifying | ⏳ Development |
| **HBM4** | 🎯 Target: H1 2026 | 🎯 Target: H2 2026 | 🎯 Target: 2027 |
| **TSV Yield** | ~80%+ (best) | ~60-70% | ~50-60% |
| **Thermal Solution** | Advanced (best) | Good | Improving |
| **NVIDIA Qualification** | All products qualified | HBM3E qualified late '24 | HBM3E qualified early '25 |
| **HBM Revenue (2024)** | ~$4.6B | ~$3.4B | ~$0.9B |

#### Competitive Assessment

- **SK Hynix**: 12-18 month lead in HBM. This is their **most valuable strategic moat**.
- **Samsung**: Massive scale advantage but lost HBM leadership due to yield/thermal issues. Recovering aggressively.
- **Micron**: Late to HBM but has cost structure advantages (US-based, no China fab risk). Growing share.

---

### 5.5 Cost Structure Comparison (DRAM, 2024)

| Metric | Samsung | SK Hynix | Micron |
|--------|---------|----------|--------|
| **Gross Margin** | ~38% | ~42% | ~32% |
| **R&D as % Revenue** | ~10% | ~9% | ~11% |
| **Capex/Revenue** | ~25% | ~19% | ~25% |
| **Wafer Cost (DRAM)** | Lowest (scale + EUV) | Competitive | Higher (no EUV yet) |
| **Manufacturing Efficiency** | Best-in-class | Very good | Good |
| **SG&A as % Revenue** | ~8% | ~7% | ~10% |

> SK Hynix enjoys best-in-class gross margins in 2024 due to HBM premium pricing, despite Samsung's lower wafer cost.

---

### 5.6 Competitive SWOT Summary

| | SK Hynix | Samsung | Micron |
|---|----------|---------|--------|
| **S** | HBM #1, NVIDIA lock-in, fast execution | Scale, vertical integration, foundry | US location, enterprise strength, 1β node |
| **W** | Smaller scale, China exposure, limited foundry | HBM yield gaps, unfocused strategy | Small HBM share, late market timing |
| **O** | AI supercycle, HBM4, custom HBM for ASICs | HBM catch-up, foundry-memory bundles | US gov support (CHIPS Act), data center growth |
| **T** | Samsung HBM recovery, China self-sufficiency, cycle downturn | Geopolitics, customer diversification away, YMTC | China competition, capital intensity, tech catch-up |

---

## 6. DRAM & NAND Industry Cycle & Pricing Trends

### 6.1 Memory Cycle Phase Assessment (Mid-2025)

```
                    MEMORY CYCLE POSITION
  ┌─────────────────────────────────────────────────┐
  │                                                 │
  │  Trough    Recovery    Expansion    Peak    Decline
  │    │          │            │          │        │
  │    ▼          ▼            ▼          ▼        ▼
  │  Q1'23    Q3'23       Q1'24      >>> Q2'25 <<< │
  │                                 Current Phase   │
  └─────────────────────────────────────────────────┘
  
  Phase: Late Expansion / Near Peak
  - DRAM: Strong upcycle, but growth rate decelerating
  - NAND: Moderate recovery, oversupply risk emerging
  - HBM: Structural supercycle (insulated from commodity cycle)
```

#### Historical Cycle Context

| Cycle | Peak | Trough | Duration | Driver |
|-------|------|--------|----------|--------|
| 2017-2019 | Q3 2018 | Q1 2019 | 18 months | Data center oversupply, crypto bust |
| 2020-2022 | Q2 2021 | Q3 2022 | 15 months | COVID demand boom, then bust |
| 2022-2025 | Q4 2024? | Q1 2023 | ~24 months? | AI-driven structural demand |
| **This cycle is longer** due to AI capex being multi-year and HBM being supply-constrained. |

---

### 6.2 DRAM Inventory Levels

| Metric | Q1 2023 (Trough) | Q4 2023 | Q4 2024 | Q1 2025 | Assessment |
|--------|-------------------|---------|---------|---------|------------|
| **Industry Inventory (weeks)** | 16-20 wk | 10-12 wk | 6-8 wk | 7-9 wk | Healthy-tight |
| **SK Hynix Inventory** | ~18 wk | ~10 wk | ~6 wk | ~7 wk | Lean |
| **Channel Inventory** | Bloated | Normal | Low | Normal | Balanced |

> Inventory has normalized from crisis levels. SK Hynix maintains lean inventory, prioritizing HBM allocation over commodity DRAM.

---

### 6.3 DRAM ASP (Average Selling Price) Trends

#### Commodity DRAM ASP Index (Q1 2023 = 100)

| Quarter | DDR4 ASP | DDR5 ASP | LPDDR5X ASP | HBM3E ASP | Overall DRAM |
|---------|----------|----------|-------------|-----------|--------------|
| Q1 2023 | 100 | 100 | 100 | N/A | 100 |
| Q2 2023 | 85 | 95 | 90 | N/A | 90 |
| Q3 2023 | 90 | 105 | 100 | N/A | 98 |
| Q4 2023 | 110 | 130 | 120 | 150 | 125 |
| Q1 2024 | 120 | 145 | 135 | 200 | 145 |
| Q2 2024 | 130 | 155 | 145 | 250 | 165 |
| Q3 2024 | 125 | 150 | 140 | 280 | 160 |
| Q4 2024 | 120 | 145 | 135 | 300 | 155 |
| Q1 2025E | 110 | 140 | 130 | 310 | 148 |
| Q2 2025E | 108 | 138 | 128 | 320 | 145 |

```
DRAM ASP Trend
  320│                              █  HBM3E
     │                         █  │
  240│                    █  │     │
     │               █  │     │
  160│          █  █  │     │     │ ← DDR5
     │     █  │  │     │     │     │
   80│█  │  │     │     │     │     │ ← DDR4
     └──┼──┼──┼──┼──┼──┼──┼──┼──┼──
      Q1 Q2 Q3 Q4 Q1 Q2 Q3 Q4 Q1 Q2
      '23           '24           '25
```

#### Key ASP Observations
- **Commodity DRAM (DDR4/DDR5)**: Peaked Q2 2024, gradually softening as supply catches up
- **HBM ASP**: Still rising — supply-constrained, 5-8x premium holding firm
- **LPDDR5X**: Stable — supported by AI smartphone cycle (Apple, Samsung)
- **Overall**: Modest ASP decline expected H2 2025 for commodity, HBM remains strong

---

### 6.4 NAND Flash Pricing Trends

| Quarter | NAND ASP ($/GB) | QoQ Change | Supply/Demand |
|---------|-----------------|------------|---------------|
| Q1 2023 | $0.045 | -20% | Severe oversupply |
| Q2 2023 | $0.040 | -11% | Oversupply, production cuts |
| Q3 2023 | $0.042 | +5% | Cuts taking effect |
| Q4 2023 | $0.048 | +14% | Recovery begins |
| Q1 2024 | $0.055 | +15% | Tight supply, AI SSD demand |
| Q2 2024 | $0.058 | +5% | Stable |
| Q3 2024 | $0.052 | -10% | Oversupply returning |
| Q4 2024 | $0.048 | -8% | Price competition |
| Q1 2025E | $0.045 | -6% | Weak demand, high inventory |
| Q2 2025E | $0.044 | -2% | Bottoming |

> **NAND is in a softer cycle than DRAM** — AI demand benefits DRAM/HBM disproportionately. NAND oversupply risk is real in 2025.

---

### 6.5 Supply/Demand Forecast

#### DRAM Supply vs. Demand Growth

| Year | Bit Supply Growth | Bit Demand Growth | Supply-Demand Gap | Pricing Outlook |
|------|-------------------|-------------------|-------------------|-----------------|
| 2023 | -5% | -8% | Tight | Recovery (+) |
| 2024 | +15% | +25% | **Deficit** | Strong up (+) |
| 2025E | +20% | +18% | Balanced/Slight surplus | Mixed (HBM+, Commodity -) |
| 2026E | +22% | +20% | Slight surplus | Pressure on commodity |

#### DRAM Bit Growth by Application

| Application | 2024 Growth | 2025E Growth | 2026E Growth |
|-------------|-------------|--------------|--------------|
| Server (AI) | +80% | +50% | +40% |
| Server (Traditional) | +15% | +12% | +10% |
| Mobile | +10% | +8% | +8% |
| PC/Client | +12% | +10% | +8% |
| Automotive/Industrial | +20% | +18% | +15% |
| Graphics | +25% | +20% | +15% |

---

### 6.6 Capex Impact on Future Supply

| Company | 2024 Capex | 2025 Capex Plan | Focus |
|---------|-----------|-----------------|-------|
| Samsung | ~₩30T | ~₩35T+ | HBM, foundry, next-gen NAND |
| SK Hynix | ~₩12.5T | **~₩20T+** | HBM4, Bucheon fab, DRAM migration |
| Micron | ~$8B | ~$14B+ | Idaho fab (HBM), 1β ramp |

> **Industry capex surge in 2025** could create oversupply in 2026-2027 if AI demand growth slows. This is the primary cycle risk.

---

### 6.7 Cycle Outlook Summary

| Factor | DRAM | NAND | HBM |
|--------|------|------|-----|
| **Current Phase** | Late upcycle | Flat/softening | Structural supercycle |
| **Near-term (6mo)** | Modest ASP decline | Bottoming | Strong, supply-constrained |
| **Medium-term (12-18mo)** | Balanced-to-soft | Recovery possible | Strong, driven by HBM4 |
| **Key Risk** | Commodity oversupply | Persistent oversupply | Samsung yield improvement |
| **SK Hynix Net** | Positive (HBM offsets) | Neutral-negative | Very positive |

---
