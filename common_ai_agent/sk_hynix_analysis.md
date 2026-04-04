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
