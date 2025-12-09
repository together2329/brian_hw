# PCI $\geq$ EXPRESS PCI Express ${ }^{\circledR}$ Base Specification Revision 6.3 

December 19, 2024

Copyright© 2002-2024 PCI-SIG
PCI-SIG disclaims all warranties and liability for the use of this document and the information contained herein and assumes no responsibility for any errors that may appear in this document, nor does PCI-SIG make a commitment to update the information contained herein.

This PCI Specification is provided "as is" without any warranties of any kind, including any warranty of merchantability, non-infringement, fitness for any particular purpose, or any warranty otherwise arising out of any proposal, specification, or sample. PCI-SIG disclaims all liability for infringement of proprietary rights, relating to use of information in this specification. This document itself may not be modified in any way, including by removing the copyright notice or references to PCI-SIG. No license, express or implied, by estoppel or otherwise, to any intellectual property rights is granted herein. PCI, PCI Express, PCIe, and PCI-SIG are trademarks or registered trademarks of PCI-SIG. All other product names are trademarks, registered trademarks, or servicemarks of their respective owners.

Page 2

# Table of Contents 

1. Introduction ..... 133
1.1 An Evolving I/O Interconnect ..... 133
1.2 PCI Express Link ..... 134
1.3 PCI Express Fabric Topology ..... 135
1.3.1 Root Complex ..... 136
1.3.2 Endpoints ..... 137
1.3.2.1 Legacy Endpoint Rules ..... 137
1.3.2.2 PCI Express Endpoint Rules ..... 138
1.3.2.3 Root Complex Integrated Endpoint Rules ..... 138
1.3.3 Switch ..... 139
1.3.4 Root Complex Event Collector ..... 140
1.3.5 PCI Express to PCI/PCI-X Bridge ..... 140
1.4 Hardware/Software Model for Discovery, Configuration and Operation ..... 140
1.5 PCI Express Layering Overview ..... 141
1.5.1 Transaction Layer ..... 142
1.5.2 Data Link Layer ..... 142
1.5.3 Physical Layer ..... 142
1.5.4 Layer Functions and Services ..... 143
1.5.4.1 Transaction Layer Services ..... 143
1.5.4.2 Data Link Layer Services ..... 144
1.5.4.3 Physical Layer Services ..... 144
1.5.4.4 Inter-Layer Interfaces ..... 145
1.5.4.4.1 Transaction/Data Link Interface. ..... 145
1.5.4.4.2 Data Link/Physical Interface ..... 145
2. Transaction Layer Specification. ..... 147
2.1 Transaction Layer Overview. ..... 147
2.1.1 Address Spaces, Transaction Types, and Usage. ..... 147
2.1.1.1 Memory Transactions ..... 148
2.1.1.2 I/O Transactions. ..... 148
2.1.1.3 Configuration Transactions ..... 149
2.1.1.4 Message Transactions ..... 149
2.1.2 Packet Format Overview ..... 149
2.2 Transaction Layer Protocol - Packet Definition ..... 151
2.2.1 Common Packet Header Fields ..... 151
2.2.1.1 Common Packet Header Fields for Non-Flit Mode ..... 151
2.2.1.2 Common Packet Header Fields for Flit Mode ..... 154
2.2.2 TLPs with Data Payloads - Rules ..... 177
2.2.3 TLP Digest Rules - Non-Flit Mode Only ..... 180
2.2.4 Routing and Addressing Rules ..... 181
2.2.4.1 Address-Based Routing Rules ..... 181
2.2.4.2 ID Based Routing Rules ..... 184
2.2.5 First/Last DW Byte Enables Rules ..... 188
2.2.5.1 Byte Enable Rules for Non-Flit Mode ..... 188
2.2.5.2 Byte Enable Rules for Flit Mode ..... 191
2.2.6 Transaction Descriptor ..... 191
2.2.6.1 Overview ..... 191

2.2.6.2 Transaction Descriptor - Transaction ID Field ..... 192
2.2.6.3 Transaction Descriptor - Attributes Field ..... 199
2.2.6.4 Relaxed Ordering and ID-Based Ordering Attributes ..... 200
2.2.6.5 No Snoop Attribute ..... 200
2.2.6.6 Transaction Descriptor - Traffic Class Field ..... 201
2.2.7 Memory, I/O, and Configuration Request Rules ..... 201
2.2.7.1 Non-Flit Mode ..... 201
2.2.7.1.1 TPH Rules ..... 205
2.2.7.2 Flit Mode ..... 208
2.2.8 Message Request Rules ..... 210
2.2.8.1 INTx Interrupt Signaling - Rules ..... 212
2.2.8.2 Power Management Messages ..... 216
2.2.8.3 Error Signaling Messages ..... 217
2.2.8.4 Locked Transactions Support ..... 218
2.2.8.5 Slot Power Limit Support ..... 219
2.2.8.6 Vendor-Defined Messages ..... 220
2.2.8.6.1 PCI-SIG Defined VDMs ..... 222
2.2.8.6.2 Device Readiness Status (DRS) Message ..... 223
2.2.8.6.3 Function Readiness Status Message (FRS Message) ..... 224
2.2.8.6.4 Hierarchy ID Message ..... 226
2.2.8.7 Ignored Messages ..... 227
2.2.8.8 Latency Tolerance Reporting (LTR) Message ..... 228
2.2.8.9 Optimized Buffer Flush/Fill (OBFF) Message ..... 229
2.2.8.10 Precision Time Measurement (PTM) Messages ..... 230
2.2.8.11 Integrity and Data Encryption (IDE) Messages ..... 233
2.2.9 Completion Rules ..... 236
2.2.9.1 Completion Rules for Non-Flit Mode ..... 237
2.2.9.2 Completion Rules for Flit Mode ..... 239
2.2.10 TLP Prefix Rules ..... 242
2.2.10.1 TLP Prefix General Rules - Non-Flit Mode ..... 242
2.2.10.2 Local TLP Prefix Processing ..... 242
2.2.10.2.1 Vendor Defined Local TLP Prefix ..... 243
2.2.10.3 Flit Mode Local TLP Prefix ..... 243
2.2.10.4 End-End TLP Prefix Processing - Non-Flit Mode ..... 244
2.2.10.4.1 Vendor Defined End-End TLP Prefix ..... 246
2.2.10.4.2 Root Ports with End-End TLP Prefix Supported ..... 246
2.2.11 OHC-E Rules - Flit Mode ..... 246
2.3 Handling of Received TLPs ..... 248
2.3.1 Request Handling Rules ..... 251
2.3.1.1 Data Return for Non-UIO Read Requests ..... 257
2.3.1.2 UIO Read Completions ..... 262
2.3.1.3 UIO Write Completions ..... 263
2.3.2 Completion Handling Rules ..... 263
2.4 Transaction Ordering ..... 265
2.4.1 Transaction Ordering Rules for TLPs not using UIO or Flow-Through IDE Streams ..... 265
2.4.2 Ordering Rules for UIO ..... 271
2.4.3 Update Ordering and Granularity Observed by a Read Transaction ..... 272
2.4.3.1 Ordering and Granularity for Non-UIO Reads ..... 272
2.4.3.2 Ordering and Granularity for UIO Reads ..... 273
2.4.4 Update Ordering and Granularity Provided by a Write Transaction ..... 273

2.4.4.1 Ordering and Granularity for Non-UIO Writes ..... 273
2.4.4.2 Ordering and Granularity for UIO Writes ..... 274
2.5 Virtual Channel (VC) Mechanism ..... 274
2.5.1 Virtual Channel Identification (VC ID) ..... 278
2.5.2 TC to VC Mapping ..... 278
2.5.3 VC and TC Rules ..... 280
2.6 Ordering and Receive Buffer Flow Control ..... 281
2.6.1 Flow Control (FC) Rules ..... 282
2.6.1.1 FC Information Tracked by Transmitter ..... 290
2.6.1.2 FC Information Tracked by Receiver ..... 296
2.7 End-to-End Data Integrity ..... 303
2.7.1 ECRC Rules ..... 303
2.7.2 Error Forwarding (Data Poisoning) ..... 308
2.7.2.1 Rules For Use of Data Poisoning ..... 309
2.8 Completion Timeout Mechanism ..... 310
2.9 Link Status Dependencies ..... 311
2.9.1 Transaction Layer Behavior in DL_Down Status ..... 311
2.9.2 Transaction Layer Behavior in DL_Up Status ..... 312
2.9.3 Transaction Layer Behavior During Downstream Port Containment ..... 313
3. Data Link Layer Specification ..... 315
3.1 Data Link Layer Overview ..... 315
3.2 Data Link Control and Management State Machine ..... 316
3.2.1 Data Link Control and Management State Machine Rules ..... 317
3.3 Data Link Feature Exchange ..... 320
3.4 Flow Control Initialization Protocol ..... 322
3.4.1 Flow Control Initialization State Machine Rules ..... 322
3.4.2 Scaled Flow Control ..... 330
3.5 Data Link Layer Packets (DLLPs) ..... 330
3.5.1 Data Link Layer Packet Rules ..... 331
3.6 Data Integrity Mechanisms ..... 340
3.6.1 Introduction ..... 340
3.6.2 LCRC, Sequence Number, and Retry Management (TLP Transmitter) ..... 341
3.6.2.1 LCRC and Sequence Number Rules (TLP Transmitter) ..... 341
3.6.2.2 Handling of Received DLLPs (Non-Flit Mode) ..... 349
3.6.2.3 Handling of Received DLLPs (Flit Mode) ..... 350
3.6.3 LCRC and Sequence Number (TLP Receiver) (Non-Flit Mode) ..... 351
3.6.3.1 LCRC and Sequence Number Rules (TLP Receiver) ..... 351
4. Physical Layer Logical Block ..... 357
4.1 Introduction ..... 357
4.2 Logical Sub-block ..... 357
4.2.1 8b/10b Encoding for $2.5 \mathrm{GT} / \mathrm{s}$ and $5.0 \mathrm{GT} / \mathrm{s}$ Data Rates ..... 359
4.2.1.1 Symbol Encoding. ..... 359
4.2.1.1.1 Serialization and De-serialization of Data ..... 360
4.2.1.1.2 Special Symbols for Framing and Link Management (K Codes) ..... 361
4.2.1.1.3 8b/10b Decode Rules ..... 362
4.2.1.2 Framing and Application of Symbols to Lanes ..... 363
4.2.1.2.1 Framing and Application of Symbols to Lanes for TLPs and DLLPs in Non-Flit Mode ..... 363
4.2.1.3 Data Scrambling ..... 366

4.2.2 128b/130b Encoding for 8.0 GT/s, 16.0 GT/s, and 32.0 GT/s Data Rates ..... 367
4.2.2.1 Lane Level Encoding ..... 368
4.2.2.2 Ordered Set Blocks ..... 369
4.2.2.2.1 Block Alignment ..... 369
4.2.2.3 Data Blocks ..... 370
4.2.2.3.1 Framing Tokens in Non-Flit-Mode ..... 370
4.2.2.3.2 Transmitter Framing Requirements in Non-Flit Mode ..... 375
4.2.2.3.3 Receiver Framing Requirements in Non-Flit Mode ..... 376
4.2.2.3.4 Receiver Framing Requirements in Flit Mode ..... 378
4.2.2.3.5 Recovery from Framing Errors in Non-Flit Mode and Flit Mode ..... 379
4.2.2.4 Scrambling in Non-Flit Mode and Flit Mode ..... 379
4.2.2.5 Precoding ..... 385
4.2.2.5.1 Precoding at 32.0 GT/s Data Rate ..... 386
4.2.2.6 Loopback with 128b/130b Code in Non-Flit Mode and Flit Mode ..... 388
4.2.3 Flit Mode Operation ..... 388
4.2.3.1 1b/1b Encoding for 64.0 GT/s and higher Data Rates ..... 388
4.2.3.1.1 PAM4 Signaling ..... 390
4.2.3.1.2 1b/1b Scrambling ..... 391
4.2.3.1.3 Gray Coding at 64.0 GT/s and Higher Data Rates ..... 392
4.2.3.1.4 Precoding at 64.0 GT/s and Higher Data Rates ..... 393
4.2.3.1.5 Ordered Set Blocks at 64.0 GT/s and Higher Data Rates ..... 396
4.2.3.1.6 Alignment at Block/ Flit Level for 1b/1b Encoding. ..... 397
4.2.3.2 Processing of Ordered Sets During Flit Mode Data Stream ..... 398
4.2.3.3 Data Stream in Flit Mode ..... 400
4.2.3.4 Bytes in Flit Layout ..... 406
4.2.3.4.1 TLP Bytes in Flit ..... 406
4.2.3.4.2 DLP Bytes in Flit ..... 409
4.2.3.4.2.1 Flit Sequence Number and Retry Mechanism ..... 414
4.2.3.4.2.1.1 IDLE Flit Handshake Phase ..... 421
4.2.3.4.2.1.2 Sequence Number Handshake Phase ..... 421
4.2.3.4.2.1.3 Normal Flit Exchange Phase ..... 423
4.2.3.4.2.1.4 Received Ack and Nak Processing ..... 424
4.2.3.4.2.1.5 Ack, Nak, and Discard Rules ..... 425
4.2.3.4.2.1.6 Flit Replay Scheduling ..... 432
4.2.3.4.2.1.7 Flit Replay Transmit Rules ..... 433
4.2.3.4.2.2 NOP Flit Payload ..... 438
4.2.3.4.2.2.1 NOP.Empty Flit ..... 438
4.2.3.4.2.2.2 NOP.Debug Flit ..... 439
4.2.3.4.2.2.2.1 PCI-SIG Defined Debug Chunk Opcode Values ..... 442
4.2.3.4.2.2.2.2 Empty Debug Chunk ..... 443
4.2.3.4.2.2.2.3 Start Capture Trigger Debug Chunk ..... 443
4.2.3.4.2.2.2.4 Stop Capture Trigger Debug Chunk ..... 444
4.2.3.4.2.2.2.5 FC Information Tracked by Transmitter Debug Chunk ..... 444
4.2.3.4.2.2.2.6 FC Information Tracked by Receiver Debug Chunk ..... 446
4.2.3.4.2.2.2.7 Flit Mode Transmitter Retry Flags and Counters Debug Chunk ..... 447
4.2.3.4.2.2.2.8 Flit Mode Receiver Retry Flags and Counters Debug Chunk ..... 448
4.2.3.4.2.2.2.9 Buffer Occupancy Debug Chunk ..... 449
4.2.3.4.2.2.2.1 Link Debug Request Debug Chunk ..... 450
4.2.304.2.2.3 NOP.Vendor Flit ..... 451
4.2.3.4.2.3 CRC Bytes in Flit ..... 451

4.2.3.4.2.4 ECC Bytes in Flit ..... 452
4.2.3.4.2.5 Ordered Set insertion in Data Stream in Flit Mode ..... 458
4.2.4 Link Equalization Procedure for 8.0 GT/s and Higher Data Rates ..... 459
4.2.4.1 Rules for Transmitter Coefficients ..... 471
4.2.4.2 Encoding of Presets ..... 472
4.2.5 Link Initialization and Training ..... 473
4.2.5.1 Training Sequences ..... 474
4.2.5.2 Alternate Protocol Negotiation ..... 494
4.2.5.3 Electrical Idle Sequences (EIOS and EIEOS) ..... 497
4.2.5.4 Inferring Electrical Idle ..... 502
4.2.5.5 Lane Polarity Inversion ..... 503
4.2.5.6 Fast Training Sequence (FTS) ..... 504
4.2.5.7 Start of Data Stream Ordered Set (SDS Ordered Set) ..... 506
4.2.5.8 Link Error Recovery ..... 506
4.2.5.9 Reset ..... 507
4.2.5.9.1 Fundamental Reset ..... 507
4.2.5.9.2 Hot Reset. ..... 508
4.2.5.10 Link Data Rate Negotiation ..... 508
4.2.5.11 Link Width and Lane Sequence Negotiation ..... 508
4.2.5.11.1 Required and Optional Port Behavior ..... 508
4.2.5.12 Lane-to-Lane De-skew ..... 509
4.2.5.13 Lane vs. Link Training ..... 510
4.2.6 Link Training and Status State Machine (LTSSM) Descriptions ..... 510
4.2.6.1 Detect Overview ..... 511
4.2.6.2 Polling Overview ..... 511
4.2.6.3 Configuration Overview ..... 511
4.2.6.4 Recovery Overview ..... 511
4.2.6.5 L0 Overview ..... 512
4.2.6.6 L0s Overview. ..... 512
4.2.6.7 L0p Overview ..... 512
4.2.6.7.1 Link Management DLLP ..... 517
4.2.6.8 L1 Overview ..... 520
4.2.6.9 L2 Overview ..... 520
4.2.6.10 Disabled Overview ..... 521
4.2.6.11 Loopback Overview ..... 521
4.2.6.12 Hot Reset Overview ..... 522
4.2.7 Link Training and Status State Rules ..... 522
4.2.7.1 Detect ..... 524
4.2.7.1.1 Detect.Quiet ..... 524
4.2.7.1.2 Detect.Active ..... 525
4.2.7.2 Polling ..... 526
4.2.7.2.1 Polling.Active ..... 526
4.2.7.2.2 Polling.Compliance ..... 528
4.2.7.2.3 Polling.Configuration ..... 533
4.2.7.2.4 Polling.Speed ..... 533
4.2.7.3 Configuration ..... 534
4.2.7.3.1 Configuration.Linkwidth.Start ..... 534
4.2.7.3.1.1 Downstream Lanes ..... 534
4.2.7.3.1.2 Upstream Lanes ..... 536
4.2.7.3.2 Configuration.Linkwidth.Accept ..... 538

4.2.7.3.2.1 Downstream Lanes ..... 538
4.2.7.3.2.2 Upstream Lanes ..... 539
4.2.7.3.3 Configuration.Lanenum.Accept ..... 541
4.2.7.3.3.1 Downstream Lanes ..... 542
4.2.7.3.3.2 Upstream Lanes ..... 543
4.2.7.3.4 Configuration.Lanenum.Wait ..... 544
4.2.7.3.4.1 Downstream Lanes ..... 544
4.2.7.3.4.2 Upstream Lanes ..... 544
4.2.7.3.5 Configuration.Complete ..... 545
4.2.7.3.5.1 Downstream Lanes ..... 545
4.2.7.3.5.2 Upstream Lanes ..... 547
4.2.7.3.6 Configuration.Idle ..... 549
4.2.7.4 Recovery ..... 553
4.2.7.4.1 Recovery.RcvrLock ..... 553
4.2.7.4.2 Recovery.Equalization ..... 559
4.2.7.4.2.1 Downstream Lanes ..... 560
4.2.7.4.2.1.1 Phase 1 of Transmitter Equalization ..... 561
4.2.7.4.2.1.2 Phase 2 of Transmitter Equalization ..... 563
4.2.7.4.2.1.3 Phase 3 of Transmitter Equalization ..... 564
4.2.7.4.2.2 Upstream Lanes ..... 566
4.2.7.4.2.2.1 Phase 0 of Transmitter Equalization ..... 567
4.2.7.4.2.2.2 Phase 1 of Transmitter Equalization ..... 569
4.2.7.4.2.2.3 Phase 2 of Transmitter Equalization ..... 570
4.2.7.4.2.2.4 Phase 3 of Transmitter Equalization ..... 572
4.2.7.4.3 Recovery.Speed ..... 573
4.2.7.4.4 Recovery.RcvrCfg ..... 575
4.2.7.4.5 Recovery.Idle ..... 582
4.2.7.5 L0 ..... 585
4.2.7.6 L0s ..... 587
4.2.7.6.1 Receiver L0s ..... 587
4.2.7.6.1.1 Rx_L0s.Entry ..... 587
4.2.7.6.1.2 Rx_L0s.Idle ..... 587
4.2.7.6.1.3 Rx_L0s.FTS ..... 587
4.2.7.6.2 Transmitter L0s ..... 588
4.2.7.6.2.1 Tx_L0s.Entry ..... 588
4.2.7.6.2.2 Tx_L0s.Idle ..... 588
4.2.7.6.2.3 Tx_L0s.FTS ..... 589
4.2.7.7 L1 ..... 590
4.2.7.7.1 L1.Entry ..... 590
4.2.7.7.2 L1.Idle ..... 590
4.2.7.8 L2 ..... 592
4.2.7.8.1 L2.Idle ..... 592
4.2.7.8.2 L2.TransmitWake ..... 593
4.2.7.9 Disabled ..... 593
4.2.7.10 Loopback ..... 594
4.2.7.10.1 Loopback.Entry ..... 594
4.2.7.10.2 Loopback.Active ..... 598
4.2.7.10.3 Loopback.Exit ..... 600
4.2.7.11 Hot Reset ..... 601
4.2.8 Clock Tolerance Compensation ..... 602

4.2.8.1 SKP Ordered Set for 8b/10b Encoding ..... 603
4.2.8.2 SKP Ordered Set for 128b/130b Encoding ..... 603
4.2.8.3 SKP Ordered Set for 1b/1b Encoding ..... 607
4.2.8.4 Rules for Transmitters ..... 611
4.2.8.5 Rules for Receivers ..... 614
4.2.9 Compliance Pattern in 8b/10b Encoding ..... 615
4.2.10 Modified Compliance Pattern in 8b/10b Encoding ..... 616
4.2.11 Compliance Pattern in 128b/130b Encoding ..... 618
4.2.12 Modified Compliance Pattern in 128b/130b Encoding ..... 620
4.2.13 Jitter Measurement Pattern in 128b/130b ..... 620
4.2.14 Compliance Pattern in 1b/1b Encoding ..... 621
4.2.15 Modified Compliance Pattern in 1b/1b Encoding ..... 622
4.2.16 Jitter Measurement Pattern in 1b/1b Encoding ..... 622
4.2.17 Toggle Patterns in 1b/1b encoding ..... 623
4.2.18 Lane Margining at Receiver ..... 623
4.2.18.1 Receiver Number, Margin Type, Usage Model, and Margin Payload Fields ..... 624
4.2.18.1.1 Step Margin Execution Status ..... 629
4.2.18.1.2 Margin Payload for Step Margin Commands ..... 629
4.2.18.2 Margin Command and Response Flow ..... 630
4.2.18.3 Flit Mode 8.0 GT/s Margining Behavior ..... 633
4.2.18.4 Receiver Margin Testing Requirements ..... 633
4.3 Retimers ..... 638
4.3.1 Retimer Requirements ..... 639
4.3.2 Supported Retimer Topologies ..... 640
4.3.3 Variables ..... 641
4.3.4 Receiver Impedance Propagation Rules ..... 642
4.3.5 Switching Between Modes ..... 642
4.3.6 Forwarding Rules ..... 642
4.3.6.1 Forwarding Type Rules ..... 643
4.3.6.2 Orientation, Lane Numbers, and Data Stream Mode Rules ..... 643
4.3.6.3 Electrical Idle Exit Rules ..... 644
4.3.6.4 Data Rate Change and Determination Rules ..... 647
4.3.6.5 Electrical Idle Entry Rules ..... 647
4.3.6.6 Transmitter Settings Determination Rules ..... 649
4.3.6.7 Ordered Set Modification Rules ..... 651
4.3.6.8 DLLP, TLP, Logical Idle, and Flit Modification Rules ..... 653
4.3.6.9 8b/10b Encoding Rules ..... 653
4.3.6.10 8b/10b Scrambling Rules ..... 654
4.3.6.11 Hot Reset Rules ..... 654
4.3.6.12 Disable Link Rules ..... 655
4.3.6.13 Loopback ..... 655
4.3.6.14 Compliance Receive Rules ..... 657
4.3.6.15 Enter Compliance Rules ..... 658
4.3.7 Execution Mode Rules ..... 660
4.3.7.1 CompLoadBoard Rules ..... 660
4.3.7.1.1 CompLoadBoard.Entry ..... 661
4.3.7.1.2 CompLoadBoard.Pattern ..... 661
4.3.7.1.3 CompLoadBoard.Exit ..... 662
4.3.7.2 Link Equalization Rules ..... 662
4.3.7.2.1 Downstream Lanes ..... 663

4.3.7.2.1.1 Phase 1 ..... 663
4.3.7.2.1.2 Phase 2 ..... 663
4.3.7.2.1.3 Phase 3 Active ..... 663
4.3.7.2.1.4 Phase 3 Passive ..... 664
4.3.7.2.2 Upstream Lanes ..... 664
4.3.7.2.2.1 Phase 0 ..... 664
4.3.7.2.2.2 Phase 1 Active ..... 664
4.3.7.2.2.3 Phase 2 Active ..... 664
4.3.7.2.2.4 Phase 2 Passive ..... 665
4.3.7.2.2.5 Phase 3 ..... 665
4.3.7.2.3 Force Timeout ..... 665
4.3.7.3 Follower Loopback ..... 666
4.3.7.3.1 Follower Loopback. Entry ..... 666
4.3.7.3.2 Follower Loopback.Active ..... 666
4.3.7.3.3 Follower Loopback.Exit ..... 667
4.3.8 Retimer Latency ..... 667
4.3.8.1 Measurement ..... 667
4.3.8.2 Maximum Limit on Retimer Latency ..... 667
4.3.8.3 Impacts on Upstream and Downstream Ports ..... 667
4.3.9 SRIS ..... 668
4.3.10 L1 PM Substates Support ..... 670
4.3.11 Retimer Configuration Parameters ..... 671
4.3.11.1 Global Parameters ..... 672
4.3.11.2 Per Physical Pseudo Port Parameters ..... 672
4.3.12 In Band Register Access ..... 673
5. Power Management ..... 675
5.1 Overview ..... 675
5.2 Link State Power Management ..... 676
5.3 PCI-PM Software Compatible Mechanisms ..... 680
5.3.1 Device Power Management States (D-States) of a Function ..... 680
5.3.1.1 D0 State ..... 681
5.3.1.2 D1 State ..... 681
5.3.1.3 D2 State ..... 681
5.3.1.4 D3 State ..... 682
5.3.1.4.1 D3 ${ }_{\text {Hot }}$ State ..... 683
5.3.1.4.2 D3 ${ }_{\text {Cold }}$ State ..... 684
5.3.2 PM Software Control of the Link Power Management State ..... 685
5.3.2.1 Entry into the L1 State ..... 686
5.3.2.2 Exit from L1 State ..... 688
5.3.2.3 Entry into the L2/L3 Ready State ..... 689
5.3.3 Power Management Event Mechanisms ..... 689
5.3.3.1 Motivation ..... 689
5.3.3.2 Link Wakeup ..... 690
5.3.3.2.1 PME Synchronization ..... 691
5.3.3.3 PM_PME Messages ..... 692
5.3.3.3.1 PM_PME "Backpressure" Deadlock Avoidance ..... 693
5.3.3.4 PME Rules ..... 693
5.3.3.5 PM_PME Delivery State Machine ..... 694
5.4 Native PCI Express Power Management Mechanisms ..... 695

5.4.1 Active State Power Management (ASPM) ..... 695
5.4.1.1 L0s ASPM State ..... 697
5.4.1.1.1 Entry into the L0s State ..... 699
5.4.1.1.2 Exit from the L0s State ..... 699
5.4.1.2 ASPM L0p State ..... 700
5.4.1.3 ASPM L1 State ..... 700
5.4.1.3.1 ASPM Entry into the L1 State ..... 701
5.4.1.3.2 Exit from the L1 State ..... 706
5.4.1.4 ASPM Configuration ..... 708
5.4.1.4.1 Software Flow for Enabling or Disabling ASPM ..... 711
5.5 L1 PM Substates ..... 712
5.5.1 Entry conditions for L1 PM Substates and L1.0 Requirements ..... 716
5.5.2 L1.1 Requirements ..... 717
5.5.2.1 Exit from L1.1 ..... 717
5.5.3 L1.2 Requirements ..... 718
5.5.3.1 L1.2.Entry ..... 719
5.5.3.2 L1.2.Idle. ..... 720
5.5.3.3 L1.2.Exit. ..... 720
5.5.3.3.1 Exit from L1.2 ..... 721
5.5.4 L1 PM Substates Configuration ..... 722
5.5.5 L1 PM Substates Timing Parameters ..... 722
5.5.6 Link Activation ..... 723
5.6 Auxiliary Power Support ..... 724
5.7 Power Management System Messages and DLLPs ..... 725
5.8 PCI Function Power State Transitions ..... 726
5.9 State Transition Recovery Time Requirements ..... 726
5.10 SR-IOV Power Management ..... 726
5.10.1 VF Device Power Management States ..... 727
5.10.2 PF Device Power Management States ..... 727
5.11 PCI Bridges and Power Management ..... 728
5.11.1 Switches and PCI Express to PCI Bridges ..... 729
5.12 Power Management Events ..... 729
6. System Architecture ..... 731
6.1 Interrupt and PME Support ..... 731
6.1.1 Rationale for PCI Express Interrupt Model ..... 731
6.1.2 PCI-compatible INTx Emulation ..... 732
6.1.3 INTx Emulation Software Model ..... 732
6.1.4 MSI and MSI-X Operation ..... 732
6.1.4.1 MSI Configuration ..... 733
6.1.4.2 MSI-X Configuration ..... 734
6.1.4.3 Enabling Operation ..... 735
6.1.4.4 Sending Messages ..... 736
6.1.4.5 Per-vector Masking and Function Masking ..... 736
6.1.4.6 Hardware/Software Synchronization ..... 737
6.1.4.7 Message Transaction Reception and Ordering Requirements ..... 739
6.1.5 PME Support ..... 739
6.1.6 Native PME Software Model ..... 739
6.1.7 Legacy PME Software Model ..... 740
6.1.8 Operating System Power Management Notification ..... 740

6.1.9 PME Routing Between PCI Express and PCI Hierarchies ..... 740
6.2 Error Signaling and Logging ..... 741
6.2.1 Scope ..... 741
6.2.2 Error Classification ..... 741
6.2.2.1 Correctable Errors ..... 742
6.2.2.2 Uncorrectable Errors ..... 743
6.2.2.2.1 Fatal Errors ..... 743
6.2.2.2.2 Non-Fatal Errors ..... 743
6.2.3 Error Signaling ..... 743
6.2.3.1 Completion Status ..... 743
6.2.3.2 Error Messages ..... 743
6.2.3.2.1 Uncorrectable Error Severity Programming (Advanced Error Reporting) ..... 745
6.2.3.2.2 Masking Individual Errors ..... 745
6.2.3.2.3 Error Pollution ..... 745
6.2.3.2.4 Advisory Non-Fatal Error Cases ..... 746
6.2.3.2.4.1 Completer Sending a Completion with UR/CA Status ..... 746
6.2.3.2.4.2 Intermediate Receiver ..... 747
6.2.3.2.4.3 Ultimate PCI Express Receiver of a Poisoned TLP or IDE TLP with PCRC Check Failed ..... 747
6.2.3.2.4.4 Requester with Completion Timeout ..... 748
6.2.3.2.4.5 Receiver of an Unexpected Completion ..... 748
6.2.3.2.5 Requester Receiving a Completion with UR/CA Status ..... 748
6.2.3.3 Error Forwarding (Data Poisoning) ..... 749
6.2.3.4 Optional Error Checking ..... 749
6.2.4 Error Logging ..... 749
6.2.4.1 Root Complex Considerations (Advanced Error Reporting) ..... 750
6.2.4.1.1 Error Source Identification ..... 750
6.2.4.1.2 Interrupt Generation ..... 750
6.2.4.2 Multiple Error Handling (Advanced Error Reporting Extended Capability) ..... 751
6.2.4.2.1 Multiple Error Handling in VFs ..... 753
6.2.4.3 Advisory Non-Fatal Error Logging ..... 754
6.2.4.4 End-End TLP Prefix Logging - Non-Flit Mode ..... 754
6.2.5 Sequence of Device Error Signaling and Logging Operations ..... 755
6.2.6 Error Message Controls ..... 757
6.2.7 Error Listing and Rules ..... 758
6.2.7.1 Conventional PCI Mapping ..... 763
6.2.8 Virtual PCI Bridge Error Handling ..... 763
6.2.8.1 Error Message Forwarding and PCI Mapping for Bridge - Rules ..... 763
6.2.9 SR-IOV Baseline Error Handling ..... 764
6.2.10 Internal Errors ..... 765
6.2.11 Downstream Port Containment (DPC) ..... 766
6.2.11.1 DPC Interrupts ..... 768
6.2.11.2 DPC ERR_COR Signaling ..... 769
6.2.11.3 Root Port Programmed I/O (RP PIO) Error Controls ..... 769
6.2.11.4 Software Triggering of DPC ..... 772
6.2.11.5 DL_Active ERR_COR Signaling ..... 773
6.3 Virtual Channel Support ..... 774
6.3.1 Introduction and Scope ..... 774
6.3.2 TC/VC Mapping and Example Usage ..... 774
6.3.3 VC Arbitration ..... 776
6.3.3.1 Traffic Flow and Switch Arbitration Model ..... 777

6.3.3.2 VC Arbitration - Arbitration Between VCs ..... 778
6.3.3.2.1 Strict Priority Arbitration Model ..... 779
6.3.3.2.2 Round Robin Arbitration Model ..... 779
6.3.3.3 Port Arbitration - Arbitration Within VC ..... 780
6.3.3.4 Multi-Function Devices and Function Arbitration ..... 780
6.3.4 Isochronous Support ..... 783
6.3.4.1 Rules for Software Configuration ..... 783
6.3.4.2 Rules for Requesters ..... 784
6.3.4.3 Rules for Completers ..... 784
6.3.4.4 Rules for Switches and Root Complexes ..... 784
6.3.4.5 Rules for Multi-Function Devices ..... 784
6.3.5 SVC and VC/MFVC Capability Coexistence ..... 785
6.4 Device Synchronization ..... 785
6.5 Locked Transactions ..... 786
6.5.1 Introduction ..... 786
6.5.2 Initiation and Propagation of Locked Transactions - Rules ..... 787
6.5.3 Switches and Lock - Rules ..... 788
6.5.4 PCI Express/PCI Bridges and Lock - Rules ..... 788
6.5.5 Root Complex and Lock - Rules ..... 788
6.5.6 Legacy Endpoints ..... 788
6.5.7 PCI Express Endpoints ..... 789
6.6 PCI Express Reset - Rules ..... 789
6.6.1 Conventional Reset ..... 789
6.6.2 Function Level Reset (FLR) ..... 792
6.7 PCI Express Native Hot-Plug ..... 795
6.7.1 Elements of Hot-Plug ..... 796
6.7.1.1 Indicators ..... 796
6.7.1.1.1 Attention Indicator ..... 797
6.7.1.1.2 Power Indicator ..... 797
6.7.1.2 Manually-operated Retention Latch (MRL) ..... 798
6.7.1.3 MRL Sensor ..... 798
6.7.1.4 Electromechanical Interlock ..... 799
6.7.1.5 Attention Button ..... 799
6.7.1.6 Software User Interface ..... 799
6.7.1.7 Slot Numbering ..... 800
6.7.1.8 Power Controller ..... 800
6.7.2 Registers Grouped by Hot-Plug Element Association ..... 801
6.7.2.1 Attention Button Registers ..... 801
6.7.2.2 Attention Indicator Registers ..... 801
6.7.2.3 Power Indicator Registers ..... 801
6.7.2.4 Power Controller Registers ..... 801
6.7.2.5 Presence Detect Registers ..... 802
6.7.2.6 MRL Sensor Registers ..... 802
6.7.2.7 Electromechanical Interlock Registers ..... 802
6.7.2.8 Command Completed Registers ..... 802
6.7.2.9 Port Capabilities and Slot Information Registers ..... 803
6.7.2.10 Hot-Plug Interrupt Control Register ..... 803
6.7.3 PCI Express Hot-Plug Events ..... 803
6.7.3.1 Slot Events ..... 803
6.7.3.2 Command Completed Events ..... 804

6.7.3.3 Data Link Layer State Changed Events ..... 804
6.7.3.4 Software Notification of Hot-Plug Events ..... 805
6.7.4 System Firmware Intermediary (SFI) Support ..... 806
6.7.4.1 SFI ERR_COR Event Signaling ..... 806
6.7.4.2 SFI Downstream Port Filtering (DPF) ..... 806
6.7.4.3 SFI CAM ..... 807
6.7.4.4 SFI Interactions with Readiness Notifications ..... 808
6.7.4.5 SFI Suppression of Hot-Plug Surprise Functionality ..... 809
6.7.5 Firmware Support for Hot-Plug ..... 810
6.7.6 Async Removal ..... 810
6.8 Power Budgeting Mechanism ..... 811
6.8.1 System Power Budgeting Process Recommendations ..... 812
6.8.2 Device Power Considerations ..... 813
6.8.3 Power Limit Mechanisms ..... 813
6.9 Slot Power Limit Control ..... 814
6.10 Root Complex Topology Discovery ..... 817
6.11 Link Speed Management ..... 819
6.12 Access Control Services (ACS) ..... 819
6.12.1 ACS Component Capability Requirements ..... 820
6.12.1.1 ACS Downstream Ports ..... 820
6.12.1.2 ACS Functions in SR-IOV Capable and Multi-Function Devices ..... 823
6.12.1.3 Functions in Single-Function Devices. ..... 825
6.12.2 Interoperability ..... 825
6.12.3 ACS Peer-to-Peer Control Interactions ..... 825
6.12.4 ACS Enhanced Capability ..... 827
6.12.5 ACS Violation Error Handling ..... 828
6.12.6 ACS Redirection Impacts on Ordering Rules ..... 829
6.12.6.1 Completions Passing Posted Requests ..... 829
6.12.6.2 Requests Passing Posted Requests ..... 830
6.13 Alternative Routing-ID Interpretation (ARI) ..... 831
6.14 Multicast Operations ..... 834
6.14.1 Multicast TLP Processing ..... 834
6.14.2 Multicast Ordering ..... 836
6.14.3 Multicast Capability Structure Field Updates ..... 837
6.14.4 MC Blocked TLP Processing ..... 837
6.14.5 MC_Overlay Mechanism ..... 837
6.15 Atomic Operations (AtomicOps) ..... 840
6.15.1 AtomicOp Use Models and Benefits ..... 841
6.15.2 AtomicOp Transaction Protocol Summary ..... 842
6.15.3 Root Complex Support for AtomicOps ..... 843
6.15.3.1 Root Ports with AtomicOp Completer Capabilities ..... 843
6.15.3.2 Root Ports with AtomicOp Routing Capability ..... 844
6.15.3.3 RCs with AtomicOp Requester Capabilities ..... 844
6.15.4 Switch Support for AtomicOps ..... 845
6.16 Dynamic Power Allocation (DPA) Capability ..... 845
6.16.1 DPA Capability with Multi-Function Devices ..... 846
6.17 TLP Processing Hints (TPH) ..... 846
6.17.1 Processing Hints ..... 846
6.17.2 Steering Tags ..... 847
6.17.3 ST Modes of Operation ..... 847

6.17.4 TPH Capability ..... 848
6.18 Latency Tolerance Reporting (LTR) Mechanism ..... 849
6.19 Optimized Buffer Flush/Fill (OBFF) Mechanism ..... 854
6.20 PASID ..... 857
6.20.1 Managing PASID Usage ..... 857
6.20.2 PASID Information Layout ..... 858
6.20.2.1 PASID TLP Prefix - Non-Flit Mode ..... 858
6.20.2.2 PASID field (Flit Mode and Non-Flit Mode) ..... 859
6.20.2.3 Execute Requested ..... 860
6.20.2.4 Privileged Mode Requested ..... 861
6.21 Precision Time Measurement (PTM) Mechanism ..... 862
6.21.1 Introduction ..... 862
6.21.2 PTM Link Protocol ..... 863
6.21.3 Configuration and Operational Requirements ..... 867
6.21.3.1 PTM Requester Role ..... 868
6.21.3.2 PTM Responder Role ..... 870
6.21.3.3 PTM Time Source Role - Rules Specific to Switches ..... 871
6.22 Readiness Notifications (RN) ..... 872
6.22.1 Device Readiness Status (DRS) ..... 875
6.22.2 Function Readiness Status (FRS) ..... 876
6.22.3 FRS Queuing ..... 876
6.23 Enhanced Allocation ..... 877
6.24 Emergency Power Reduction State ..... 879
6.25 Hierarchy ID Message ..... 882
6.26 Flattening Portal Bridge (FPB) ..... 886
6.26.1 Introduction ..... 886
6.26.2 Hardware and Software Requirements ..... 890
6.27 Vital Product Data (VPD) ..... 897
6.27.1 VPD Format ..... 899
6.27.2 VPD Definitions ..... 900
6.27.2.1 VPD Large and Small Resource Data Tags ..... 900
6.27.2.2 Read-Only Fields ..... 900
6.27.2.3 Read/Write Fields ..... 902
6.27.2.4 VPD Example ..... 902
6.28 Native PCle Enclosure Management ..... 903
6.29 Conventional PCI Advanced Features Operation ..... 908
6.30 Data Object Exchange (DOE) ..... 910
6.30.1 Data Objects and Features ..... 913
6.30.1.1 DOE Discovery Feature ..... 915
6.30.1.2 DOE Async Message ..... 918
6.30.2 Operation ..... 919
6.30.3 Interrupt Generation ..... 921
6.31 Component Measurement and Authentication (CMA-SPDM) ..... 922
6.31.1 Removed ..... 928
6.31.2 Removed ..... 928
6.31.3 CMA-SPDM Rules ..... 928
6.31.4 Secured CMA-SPDM ..... 930
6.32 Deferrable Memory Write ..... 931
6.33 Integrity \& Data Encryption (IDE) ..... 936
6.33.1 IDE Stream and TEE State Machines ..... 940

6.33.2 IDE Stream Establishment ..... 942
6.33.3 IDE Key Management (IDE_KM) ..... 943
6.33.4 IDE TLPs ..... 953
6.33.5 IDE TLP Sub-Streams ..... 970
6.33.6 IDE TLP Aggregation ..... 975
6.33.7 Flow-Through Selective IDE Streams ..... 976
6.33.8 Other IDE Rules ..... 977
6.34 Unordered IO (UIO) ..... 980
6.34.1 UIO Rules ..... 981
6.35 MMIO Register Blocks ..... 981
6.35.1 MMIO Capabilities Register Block (MCAP) ..... 982
6.35.1.1 MCAP Array Register (Offset 00h) ..... 983
6.35.1.2 MCAP Header Register Block (Offset Varies) ..... 985
6.35.1.3 MMIO Mailbox Capability (MMB) (Offset: Varies) ..... 987
6.35.1.3.1 MMB Operation ..... 988
6.35.1.3.2 MMB Registers ..... 989
6.35.1.3.2.1 MMB Capabilities Register (Offset 00h) ..... 989
6.35.1.3.2.2 MMB Control Register (Offset 04h) ..... 991
6.35.1.3.2.3 MMB Command Register (Offset 08h) ..... 992
6.35.1.3.2.4 MMB Status Register (Offset 10h) ..... 993
6.35.1.3.2.4.1 MMB Command Return Codes ..... 994
6.35.1.3.2.5 MMB Payload Registers (Offset 20h) ..... 994
6.35.1.4 Management Message Passthrough (MMPT) Capability (Offset: Varies) ..... 995
6.35.1.4.1 MMPT Registers ..... 995
6.35.1.4.1.1 MMPT Capabilities Register (Offset 00h) ..... 995
6.35.1.4.1.2 MMPT Control Register (Offset 04h) ..... 996
6.35.1.4.1.3 MMPT Receive Message Notification Register (Offset 08h) ..... 997
6.35.2 MMIO Designated Vendor-Specific Register Block (MDVS) ..... 997
6.35.2.1 MDVS Register Block Header Register 1 (Offset 00h) ..... 998
6.35.3 MDVS Register Block Header Register 2 (Offset 04h) ..... 999
6.35.4 MDVS Register Block Header Register 3 (Offset 08h) ..... 999
6.36 MMB Command Interface ..... 1000
6.36.1 Management Message Passthrough (MMPT) ..... 1000
6.36.1.1 MMPT Send Message (Opcode 0100h) ..... 1001
6.36.1.1.1 MMPT Send Message Operation ..... 1002
6.36.1.2 MMPT Receive Message (Opcode 0101h) ..... 1003
6.36.1.2.1 MMPT Receive Message Operation ..... 1004
6.37 Debug Over Link ..... 1004
6.37.1 NOP Flit ..... 1004
7. Software Initialization and Configuration ..... 1007
7.1 Configuration Topology ..... 1007
7.2 PCI Express Configuration Mechanisms ..... 1008
7.2.1 PCI-compatible Configuration Mechanism ..... 1009
7.2.2 PCI Express Enhanced Configuration Access Mechanism (ECAM) ..... 1010
7.2.2.1 Host Bridge Requirements ..... 1013
7.2.2.2 PCI Express Device Requirements ..... 1013
7.2.3 Root Complex Register Block (RCRB) ..... 1014
7.3 Configuration Transaction Rules ..... 1014
7.3.1 Device Number ..... 1014

7.3.2 Configuration Transaction Addressing ..... 1015
7.3.3 Configuration Request Routing Rules ..... 1015
7.3.4 PCI Special Cycles ..... 1017
7.4 Configuration Register Types ..... 1017
7.5 PCI and PCIe Capabilities Required by the Base Spec for all Ports ..... 1019
7.5.1 PCI-Compatible Configuration Registers ..... 1019
7.5.1.1 Type 0/1 Common Configuration Space ..... 1019
7.5.1.1.1 Vendor ID Register (Offset 00h) ..... 1020
7.5.1.1.2 Device ID Register (Offset 02h) ..... 1021
7.5.1.1.3 Command Register (Offset 04h) ..... 1021
7.5.1.1.4 Status Register (Offset 06h) ..... 1024
7.5.1.1.5 Revision ID Register (Offset 08h) ..... 1026
7.5.1.1.6 Class Code Register (Offset 09h) ..... 1026
7.5.1.1.7 Cache Line Size Register (Offset 0Ch) ..... 1027
7.5.1.1.8 Latency Timer Register (Offset 0Dh) ..... 1027
7.5.1.1.9 Header Type Register (Offset 0Eh) ..... 1027
7.5.1.1.10 BIST Register (Offset 0Fh) ..... 1028
7.5.1.1.11 Capabilities Pointer (Offset 34h) ..... 1029
7.5.1.1.12 Interrupt Line Register (Offset 3Ch) ..... 1029
7.5.1.1.13 Interrupt Pin Register (Offset 3Dh) ..... 1030
7.5.1.1.14 Error Registers ..... 1030
7.5.1.2 Type 0 Configuration Space Header ..... 1031
7.5.1.2.1 Base Address Registers (Offset 10h - 24h) ..... 1031
7.5.1.2.2 Cardbus CIS Pointer Register (Offset 28h) ..... 1035
7.5.1.2.3 Subsystem Vendor ID Register/Subsystem ID Register (Offset 2Ch/2Eh) ..... 1035
7.5.1.2.4 Expansion ROM Base Address Register (Offset 30h) ..... 1036
7.5.1.2.5 Min_Gnt Register/Max_Lat Register (Offset 3Eh/3Fh) ..... 1039
7.5.1.3 Type 1 Configuration Space Header ..... 1039
7.5.1.3.1 Type 1 Base Address Registers (Offset 10h-14h) ..... 1041
7.5.1.3.2 Primary Bus Number Register (Offset 18h) ..... 1041
7.5.1.3.3 Secondary Bus Number Register (Offset 19h) ..... 1041
7.5.1.3.4 Subordinate Bus Number Register (Offset 1Ah) ..... 1041
7.5.1.3.5 Secondary Latency Timer (Offset 1Bh) ..... 1041
7.5.1.3.6 I/O Base/I/O Limit Registers(Offset 1Ch/1Dh) ..... 1042
7.5.1.3.7 Secondary Status Register (Offset 1Eh) ..... 1042
7.5.1.3.8 Memory Base Register/Memory Limit Register(Offset 20h/22h) ..... 1044
7.5.1.3.9 64-bit Memory Base/64-bit Memory Limit Registers (Offset 24h/26h) and 64-bit Base Upper 32 Bits/64-bit Limit Upper 32 Bits Registers (Offset 28h/2Ch) ..... 1044
7.5.1.3.10 64-bit Base Upper 32 Bits/64-bit Limit Upper 32 Bits Registers (Offset 28h/2Ch) ..... 1045
7.5.1.3.11 I/O Base Upper 16 Bits/I/O Limit Upper 16 Bits Registers (Offset 30h/32h) ..... 1045
7.5.1.3.12 Expansion ROM Base Address Register (Offset 38h) ..... 1045
7.5.1.3.13 Bridge Control Register (Offset 3Eh) ..... 1046
7.5.2 PCI Power Management Capability Structure ..... 1048
7.5.2.1 Power Management Capabilities Register (Offset 00h) ..... 1049
7.5.2.2 Power Management Control/Status Register (Offset 04h) ..... 1051
7.5.2.3 Power Management Data Register (Offset 07h) ..... 1052
7.5.3 PCI Express Capability Structure ..... 1054
7.5.3.1 PCI Express Capability List Register (Offset 00h) ..... 1055
7.5.3.2 PCI Express Capabilities Register (Offset 02h) ..... 1056
7.5.3.3 Device Capabilities Register (Offset 04h) ..... 1058

7.5.3.4 Device Control Register (Offset 08h) ..... 1062
7.5.3.5 Device Status Register (Offset 0Ah) ..... 1069
7.5.3.6 Link Capabilities Register (Offset 0Ch) ..... 1070
7.5.3.7 Link Control Register (Offset 10h) ..... 1074
7.5.3.8 Link Status Register (Offset 12h) ..... 1081
7.5.3.9 Slot Capabilities Register (Offset 14h) ..... 1084
7.5.3.10 Slot Control Register (Offset 18h) ..... 1086
7.5.3.11 Slot Status Register (Offset 1Ah) ..... 1089
7.5.3.12 Root Control Register (Offset 1Ch) ..... 1091
7.5.3.13 Root Capabilities Register (Offset 1Eh) ..... 1093
7.5.3.14 Root Status Register (Offset 20h) ..... 1093
7.5.3.15 Device Capabilities 2 Register (Offset 24h) ..... 1095
7.5.3.16 Device Control 2 Register (Offset 28h) ..... 1100
7.5.3.17 Device Status 2 Register (Offset 2Ah) ..... 1103
7.5.3.18 Link Capabilities 2 Register (Offset 2Ch) ..... 1104
7.5.3.19 Link Control 2 Register (Offset 30h) ..... 1107
7.5.3.20 Link Status 2 Register (Offset 32h) ..... 1110
7.5.3.21 Slot Capabilities 2 Register (Offset 34h) ..... 1114
7.5.3.22 Slot Control 2 Register (Offset 38h) ..... 1114
7.5.3.23 Slot Status 2 Register (Offset 3Ah) ..... 1114
7.6 PCI Express Extended Capabilities ..... 1114
7.6.1 Extended Capabilities in Configuration Space ..... 1115
7.6.2 Extended Capabilities in the Root Complex Register Block ..... 1115
7.6.3 PCI Express Extended Capability Header ..... 1115
7.7 PCI and PCIe Capabilities Required by the Base Spec in Some Situations ..... 1116
7.7.1 MSI Capability Structures ..... 1116
7.7.1.1 MSI Capability Header (Offset 00h) ..... 1118
7.7.1.2 Message Control Register for MSI (Offset 02h) ..... 1118
7.7.1.3 Message Address Register for MSI (Offset 04h) ..... 1120
7.7.1.4 Message Upper Address Register for MSI (Offset 08h) ..... 1121
7.7.1.5 Message Data Register for MSI (Offset 08h or 0Ch) ..... 1121
7.7.1.6 Extended Message Data Register for MSI (Optional) ..... 1122
7.7.1.7 Mask Bits Register for MSI (Offset 0Ch or 10h ..... 1122
7.7.1.8 Pending Bits Register for MSI (Offset 10h or 14h) ..... 1123
7.7.2 MSI-X Capability and Table Structure ..... 1123
7.7.2.1 MSI-X Capability Header (Offset 00h) ..... 1127
7.7.2.2 Message Control Register for MSI-X (Offset 02h) ..... 1128
7.7.2.3 Table Offset/Table BIR Register for MSI-X (Offset 04h) ..... 1129
7.7.2.4 PBA Offset/PBA BIR Register for MSI-X (Offset 08h) ..... 1129
7.7.2.5 Message Address Register for MSI-X Table Entries ..... 1130
7.7.2.6 Message Upper Address Register for MSI-X Table Entries ..... 1131
7.7.2.7 Message Data Register for MSI-X Table Entries ..... 1131
7.7.2.8 Vector Control Register for MSI-X Table Entries ..... 1131
7.7.2.9 Pending Bits Register for MSI-X PBA Entries ..... 1132
7.7.3 Secondary PCI Express Extended Capability ..... 1133
7.7.3.1 Secondary PCI Express Extended Capability Header (Offset 00h) ..... 1135
7.7.3.2 Link Control 3 Register (Offset 04h) ..... 1135
7.7.3.3 Lane Error Status Register (Offset 08h) ..... 1136
7.7.3.4 Lane Equalization Control Register (Offset 0Ch) ..... 1137
7.7.4 Data Link Feature Extended Capability ..... 1139

7.7.4.1 Data Link Feature Extended Capability Header (Offset 00h) ..... 1140
7.7.4.2 Data Link Feature Capabilities Register (Offset 04h) ..... 1141
7.7.4.3 Data Link Feature Status Register (Offset 08h) ..... 1142
7.7.5 Physical Layer 16.0 GT/s Extended Capability ..... 1143
7.7.5.1 Physical Layer 16.0 GT/s Extended Capability Header (Offset 00h) ..... 1145
7.7.5.2 16.0 GT/s Capabilities Register (Offset 04h) ..... 1145
7.7.5.3 16.0 GT/s Control Register (Offset 08h) ..... 1146
7.7.5.4 16.0 GT/s Status Register (Offset 0Ch) ..... 1146
7.7.5.5 16.0 GT/s Local Data Parity Mismatch Status Register (Offset 10h) ..... 1147
7.7.5.6 16.0 GT/s First Retimer Data Parity Mismatch Status Register (Offset 14h) ..... 1148
7.7.5.7 16.0 GT/s Second Retimer Data Parity Mismatch Status Register (Offset 18h) ..... 1148
7.7.5.8 Physical Layer 16.0 GT/s Reserved (Offset 1Ch) ..... 1149
7.7.5.9 16.0 GT/s Lane Equalization Control Register (Offsets 20h to 3Ch) ..... 1149
7.7.6 Physical Layer 32.0 GT/s Extended Capability ..... 1150
7.7.6.1 Physical Layer 32.0 GT/s Extended Capability Header (Offset 00h) ..... 1152
7.7.6.2 32.0 GT/s Capabilities Register (Offset 04h) ..... 1152
7.7.6.3 32.0 GT/s Control Register (Offset 08h) ..... 1153
7.7.6.4 32.0 GT/s Status Register (Offset 0Ch) ..... 1154
7.7.6.5 Received Modified TS Data 1 Register (Offset 10h) ..... 1155
7.7.6.6 Received Modified TS Data 2 Register (Offset 14h) ..... 1156
7.7.6.7 Transmitted Modified TS Data 1 Register (Offset 18h) ..... 1157
7.7.6.8 Transmitted Modified TS Data 2 Register (Offset 1Ch) ..... 1158
7.7.6.9 32.0 GT/s Lane Equalization Control Register (Offset 20h) ..... 1159
7.7.7 Physical Layer 64.0 GT/s Extended Capability ..... 1161
7.7.7.1 Physical Layer 64.0 GT/s Extended Capability Header (Offset 00h) ..... 1162
7.7.7.2 64.0 GT/s Capabilities Register (Offset 04h) ..... 1162
7.7.7.3 64.0 GT/s Control Register (Offset 08h) ..... 1163
7.7.7.4 64.0 GT/s Status Register (Offset 0Ch) ..... 1163
7.7.7.5 64.0 GT/s Lane Equalization Control Register (Offset 10h) ..... 1164
7.7.8 Flit Logging Extended Capability ..... 1166
7.7.8.1 Flit Logging Extended Capability Header (Offset 00h) ..... 1167
7.7.8.2 Flit Error Log 1 Register (Offset 04h) ..... 1167
7.7.8.3 Flit Error Log 2 Register (Offset 08h) ..... 1170
7.7.8.4 Flit Error Counter Control Register (Offset 0Ch) ..... 1171
7.7.8.5 Flit Error Counter Status Register (Offset 0Eh) ..... 1172
7.7.8.6 FBER Measurement Control Register (Offset 10h) ..... 1173
7.7.8.7 FBER Measurement Status 1 Register (Offset 14h) ..... 1173
7.7.8.8 FBER Measurement Status 2 Register (Offset 18h) ..... 1174
7.7.8.9 FBER Measurement Status 3 Register (Offset 1Ch) ..... 1175
7.7.8.10 FBER Measurement Status 4 Register (Offset 20h) ..... 1175
7.7.8.11 FBER Measurement Status 5 Register (Offset 24h) ..... 1176
7.7.8.12 FBER Measurement Status 6 Register (Offset 28h) ..... 1176
7.7.8.13 FBER Measurement Status 7 Register (Offset 2Ch) ..... 1176
7.7.8.14 FBER Measurement Status 8 Register (Offset 30h) ..... 1177
7.7.8.15 FBER Measurement Status 9 Register (Offset 34h) ..... 1177
7.7.8.16 FBER Measurement Status 10 Register (Offset 38h) ..... 1178
7.7.9 Device 3 Extended Capability Structure ..... 1178
7.7.9.1 Device 3 Extended Capability Header (Offset 00h) ..... 1178
7.7.9.2 Device Capabilities 3 Register (Offset 04h) ..... 1179
7.7.9.3 Device Control 3 Register (Offset 08h) ..... 1181

7.7.9.4 Device Status 3 Register (Offset 0Ch) ..... 1184
7.7.10 Lane Margining at the Receiver Extended Capability ..... 1185
7.7.10.1 Lane Margining at the Receiver Extended Capability Header (Offset 00h) ..... 1187
7.7.10.2 Margining Port Capabilities Register (Offset 04h) ..... 1187
7.7.10.3 Margining Port Status Register (Offset 06h) ..... 1188
7.7.10.4 Margining Lane Control Register (Offset 08h) ..... 1188
7.7.10.5 Margining Lane Status Register (Offset 0Ah) ..... 1189
7.7.11 ACS Extended Capability ..... 1190
7.7.11.1 ACS Extended Capability Header (Offset 00h) ..... 1191
7.7.11.2 ACS Capability Register (Offset 04h) ..... 1192
7.7.11.3 ACS Control Register (Offset 06h) ..... 1193
7.7.11.4 Egress Control Vector Register (Offset 08h) ..... 1195
7.8 Common PCI and PCIe Capabilities. ..... 1197
7.8.1 Power Budgeting Extended Capability ..... 1197
7.8.1.1 Power Budgeting Extended Capability Header (Offset 00h) ..... 1197
7.8.1.2 Power Budgeting Data Select Register (Offset 04h) ..... 1198
7.8.1.3 Power Budgeting Control Register (Offset 06h) ..... 1198
7.8.1.4 Power Budgeting Data Register (Offset 08h) ..... 1200
7.8.1.5 Power Budgeting Capability Register (Offset 0Ch) ..... 1205
7.8.1.6 Power Budgeting Sense Detect Register (Offset 0Dh) ..... 1206
7.8.2 Latency Tolerance Reporting (LTR) Extended Capability ..... 1209
7.8.2.1 LTR Extended Capability Header (Offset 00h) ..... 1210
7.8.2.2 Max Snoop Latency Register (Offset 04h) ..... 1210
7.8.2.3 Max No-Snoop Latency Register (Offset 06h) ..... 1211
7.8.3 L1 PM Substates Extended Capability ..... 1211
7.8.3.1 L1 PM Substates Extended Capability Header (Offset 00h) ..... 1212
7.8.3.2 L1 PM Substates Capabilities Register (Offset 04h) ..... 1213
7.8.3.3 L1 PM Substates Control 1 Register (Offset 08h) ..... 1214
7.8.3.4 L1 PM Substates Control 2 Register (Offset 0Ch) ..... 1216
7.8.3.5 L1 PM Substates Status Register (Offset 10h) ..... 1217
7.8.4 Advanced Error Reporting Extended Capability ..... 1217
7.8.4.1 Advanced Error Reporting Extended Capability Header (Offset 00h) ..... 1220
7.8.4.2 Uncorrectable Error Status Register (Offset 04h) ..... 1220
7.8.4.3 Uncorrectable Error Mask Register (Offset 08h) ..... 1223
7.8.4.4 Uncorrectable Error Severity Register (Offset 0Ch) ..... 1225
7.8.4.5 Correctable Error Status Register (Offset 10h) ..... 1228
7.8.4.6 Correctable Error Mask Register (Offset 14h) ..... 1229
7.8.4.7 Advanced Error Capabilities and Control Register (Offset 18h) ..... 1230
7.8.4.8 Header Log Register (Offset 1Ch) ..... 1232
7.8.4.9 Root Error Command Register (Offset 2Ch) ..... 1233
7.8.4.10 Root Error Status Register (Offset 30h) ..... 1234
7.8.4.11 Error Source Identification Register (Offset 34h) ..... 1236
7.8.4.12 TLP Prefix Log Register (Offset 38h) ..... 1237
7.8.5 Enhanced Allocation Capability Structure (EA) ..... 1238
7.8.5.1 Enhanced Allocation Capability First DW (Offset 00h) ..... 1238
7.8.5.2 Enhanced Allocation Capability Second DW (Offset 04h) [Type 1 Functions Only] ..... 1239
7.8.5.3 Enhanced Allocation Per-Entry Format (Offset 04h or 08h) ..... 1239
7.8.6 Resizable BAR Extended Capability ..... 1244
7.8.6.1 Resizable BAR Extended Capability Header (Offset 00h) ..... 1247

7.8.6.2 Resizable BAR Capability Register ..... 1247
7.8.6.3 Resizable BAR Control Register ..... 1250
7.8.7 VF Resizable BAR Extended Capability ..... 1252
7.8.7.1 VF Resizable BAR Extended Capability Header (Offset 00h) ..... 1254
7.8.7.2 VF Resizable BAR Capability Register (Offset 04h) ..... 1254
7.8.7.3 VF Resizable BAR Control Register (Offset 08h) ..... 1254
7.8.8 ARI Extended Capability ..... 1256
7.8.8.1 ARI Extended Capability Header (Offset 00h) ..... 1256
7.8.8.2 ARI Capability Register (Offset 04h) ..... 1257
7.8.8.3 ARI Control Register (Offset 06h) ..... 1258
7.8.9 PASID Extended Capability Structure ..... 1258
7.8.9.1 PASID Extended Capability Header (Offset 00h) ..... 1259
7.8.9.2 PASID Capability Register (Offset 04h) ..... 1260
7.8.9.3 PASID Control Register (Offset 06h) ..... 1260
7.8.10 FRS Queueing Extended Capability ..... 1262
7.8.10.1 FRS Queueing Extended Capability Header (Offset 00h) ..... 1262
7.8.10.2 FRS Queueing Capability Register (Offset 04h) ..... 1263
7.8.10.3 FRS Queueing Status Register (Offset 08h) ..... 1263
7.8.10.4 FRS Queueing Control Register (Offset 0Ah) ..... 1264
7.8.10.5 FRS Message Queue Register (Offset 0Ch) ..... 1264
7.8.11 Flattening Portal Bridge (FPB) Capability ..... 1265
7.8.11.1 FPB Capability Header (Offset 00h) ..... 1266
7.8.11.2 FPB Capabilities Register (Offset 04h) ..... 1266
7.8.11.3 FPB RID Vector Control 1 Register (Offset 08h) ..... 1268
7.8.11.4 FPB RID Vector Control 2 Register (Offset 0Ch) ..... 1269
7.8.11.5 FPB MEM Low Vector Control Register (Offset 10h) ..... 1270
7.8.11.6 FPB MEM High Vector Control 1 Register (Offset 14h) ..... 1271
7.8.11.7 FPB MEM High Vector Control 2 Register (Offset 18h) ..... 1273
7.8.11.8 FPB Vector Access Control Register (Offset 1Ch) ..... 1274
7.8.11.9 FPB Vector Access Data Register (Offset 20h) ..... 1275
7.8.12 Flit Performance Measurement Extended Capability ..... 1276
7.8.12.1 Flit Performance Measurement Extended Capability Header (Offset 00h) ..... 1276
7.8.12.2 Flit Performance Measurement Capability Register (Offset 04h) ..... 1277
7.8.12.3 Flit Performance Measurement Control Register (Offset 08h) ..... 1278
7.8.12.4 Flit Performance Measurement Status Register (Offset 0Ch) ..... 1280
7.8.12.5 LTSSM Performance Measurement Status Register (Offsets 10h to 20h) ..... 1281
7.8.13 Flit Error Injection Extended Capability ..... 1282
7.8.13.1 Flit Error Injection Extended Capability Header (Offset 00h) ..... 1283
7.8.13.2 Flit Error Injection Capability Register (Offset 04h) ..... 1284
7.8.13.3 Flit Error Injection Control 1 Register (Offset 08h) ..... 1284
7.8.13.4 Flit Error Injection Control 2 Register (Offset 0Ch) ..... 1286
7.8.13.5 Flit Error Injection Status Register (Offset 10h) ..... 1287
7.8.13.6 Ordered Set Error Injection Control 1 Register (Offset 14h) ..... 1288
7.8.13.7 Ordered Set Error Injection Control 2 Register (Offset 18h) ..... 1289
7.8.13.8 Ordered Set Error Tx Injection Status Register (Offset 1Ch) ..... 1290
7.8.13.9 Ordered Set Error Rx Injection Status Register (Offset 20h) ..... 1291
7.8.14 NOP Flit Extended Capability ..... 1292
7.8.14.1 NOP Flit Extended Capability Header ..... 1293
7.8.14.2 NOP Flit Capabilities Register ..... 1294
7.8.14.3 NOP Flit Control 1 Register ..... 1294

7.8.14.4 NOP Flit Control 2 Register ..... 1296
7.8.14.5 NOP Flit Status Register ..... 1297
7.9 Additional PCI and PCIe Capabilities ..... 1298
7.9.1 Virtual Channel Extended Capability ..... 1298
7.9.1.1 Virtual Channel Extended Capability Header (Offset 00h) ..... 1299
7.9.1.2 Port VC Capability Register 1 (Offset 04h) ..... 1299
7.9.1.3 Port VC Capability Register 2 (Offset 08h) ..... 1301
7.9.1.4 Port VC Control Register (Offset 0Ch) ..... 1301
7.9.1.5 Port VC Status Register (Offset 0Eh) ..... 1302
7.9.1.6 VC Resource Capability Register ..... 1303
7.9.1.7 VC Resource Control Register ..... 1304
7.9.1.8 VC Resource Status Register ..... 1307
7.9.1.9 VC Arbitration Table ..... 1308
7.9.1.10 Port Arbitration Table ..... 1308
7.9.2 Multi-Function Virtual Channel Extended Capability ..... 1310
7.9.2.1 MFVC Extended Capability Header (Offset 00h) ..... 1310
7.9.2.2 MFVC Port VC Capability Register 1 (Offset 04h) ..... 1311
7.9.2.3 MFVC Port VC Capability Register 2 (Offset 08h) ..... 1312
7.9.2.4 MFVC Port VC Control Register (Offset 0Ch) ..... 1313
7.9.2.5 MFVC Port VC Status Register (Offset 0Eh) ..... 1314
7.9.2.6 MFVC VC Resource Capability Register ..... 1314
7.9.2.7 MFVC VC Resource Control Register ..... 1315
7.9.2.8 MFVC VC Resource Status Register ..... 1317
7.9.2.9 MFVC VC Arbitration Table ..... 1318
7.9.2.10 Function Arbitration Table ..... 1318
7.9.3 Device Serial Number Extended Capability ..... 1320
7.9.3.1 Device Serial Number Extended Capability Header (Offset 00h) ..... 1320
7.9.3.2 Serial Number Register (Offset 04h) ..... 1321
7.9.4 Vendor-Specific Capability ..... 1322
7.9.5 Vendor-Specific Extended Capability ..... 1322
7.9.5.1 Vendor-Specific Extended Capability Header (Offset 00h) ..... 1323
7.9.5.2 Vendor-Specific Header (Offset 04h) ..... 1324
7.9.6 Designated Vendor-Specific Extended Capability (DVSEC) ..... 1325
7.9.6.1 Designated Vendor-Specific Extended Capability Header (Offset 00h) ..... 1325
7.9.6.2 Designated Vendor-Specific Header 1 (Offset 04h) ..... 1326
7.9.6.3 Designated Vendor-Specific Header 2 (Offset 08h) ..... 1327
7.9.7 RCRB Header Extended Capability ..... 1327
7.9.7.1 RCRB Header Extended Capability Header (Offset 00h) ..... 1328
7.9.7.2 RCRB Vendor ID and Device ID register (Offset 04h) ..... 1328
7.9.7.3 RCRB Capabilities register (Offset 08h) ..... 1329
7.9.7.4 RCRB Control register (Offset 0Ch) ..... 1329
7.9.8 Root Complex Link Declaration Extended Capability ..... 1330
7.9.8.1 Root Complex Link Declaration Extended Capability Header (Offset 00h) ..... 1331
7.9.8.2 Element Self Description Register (Offset 04h) ..... 1332
7.9.8.3 Link Entries ..... 1333
7.9.8.3.1 Link Description Register ..... 1333
7.9.8.3.2 Link Address ..... 1334
7.9.8.3.2.1 Link Address for Link Type 0 ..... 1334
7.9.8.3.2.2 Link Address for Link Type 1 ..... 1334
7.9.9 Root Complex Internal Link Control Extended Capability ..... 1335

7.9.9.1 Root Complex Internal Link Control Extended Capability Header (Offset 00h) ..... 1336
7.9.9.2 Root Complex Link Capabilities Register (Offset 04h) ..... 1336
7.9.9.3 Root Complex Link Control Register (Offset 08h) ..... 1339
7.9.9.4 Root Complex Link Status Register (Offset 0Ah) ..... 1340
7.9.10 Root Complex Event Collector Endpoint Association Extended Capability ..... 1341
7.9.10.1 Root Complex Event Collector Endpoint Association Extended Capability Header (Offset 00h) ..... 1342
7.9.10.2 Association Bitmap for RCIEPs (Offset 04h) ..... 1343
7.9.10.3 RCEC Associated Bus Numbers Register (Offset 08h) ..... 1343
7.9.11 Multicast Extended Capability ..... 1344
7.9.11.1 Multicast Extended Capability Header (Offset 00h) ..... 1345
7.9.11.2 Multicast Capability Register (Offset 04h) ..... 1346
7.9.11.3 Multicast Control Register (Offset 06h) ..... 1347
7.9.11.4 MC_Base_Address Register (Offset 08h) ..... 1347
7.9.11.5 MC_Receive Register (Offset 10h) ..... 1348
7.9.11.6 MC_Block_All Register (Offset 18h) ..... 1348
7.9.11.7 MC_Block_Untranslated Register (Offset 20h) ..... 1349
7.9.11.8 MC_Overlay_BAR Register (Offset 28h) ..... 1349
7.9.12 Dynamic Power Allocation Extended Capability (DPA Capability) ..... 1350
7.9.12.1 DPA Extended Capability Header (Offset 00h) ..... 1351
7.9.12.2 DPA Capability Register (Offset 04h) ..... 1351
7.9.12.3 DPA Latency Indicator Register (Offset 08h) ..... 1352
7.9.12.4 DPA Status Register (Offset 0Ch) ..... 1353
7.9.12.5 DPA Control Register (Offset 0Eh) ..... 1353
7.9.12.6 DPA Power Allocation Array ..... 1354
7.9.13 TPH Requester Extended Capability ..... 1354
7.9.13.1 TPH Requester Extended Capability Header (Offset 00h) ..... 1355
7.9.13.2 TPH Requester Capability Register (Offset 04h) ..... 1355
7.9.13.3 TPH Requester Control Register (Offset 08h) ..... 1356
7.9.13.4 TPH ST Table (Starting from Offset 0Ch) ..... 1357
7.9.14 DPC Extended Capability ..... 1358
7.9.14.1 DPC Extended Capability Header (Offset 00h) ..... 1361
7.9.14.2 DPC Capability Register (Offset 04h) ..... 1361
7.9.14.3 DPC Control Register (Offset 06h) ..... 1363
7.9.14.4 DPC Status Register (Offset 08h) ..... 1365
7.9.14.5 DPC Error Source ID Register (Offset 0Ah) ..... 1366
7.9.14.6 RP PIO Status Register (Offset 0Ch) ..... 1367
7.9.14.7 RP PIO Mask Register (Offset 10h) ..... 1368
7.9.14.8 RP PIO Severity Register (Offset 14h) ..... 1368
7.9.14.9 RP PIO SysError Register (Offset 18h) ..... 1369
7.9.14.10 RP PIO Exception Register (Offset 1Ch) ..... 1370
7.9.14.11 RP PIO Header Log Register (Offset 20h) ..... 1371
7.9.14.12 RP PIO ImpSpec Log Register (Offset 30h) ..... 1372
7.9.14.13 RP PIO TLP Prefix Log Register (Offset 34h) ..... 1372
7.9.15 Precision Time Measurement Extended Capability (PTM Extended Capability) ..... 1373
7.9.15.1 PTM Extended Capability Header (Offset 00h) ..... 1374
7.9.15.2 PTM Capability Register (Offset 04h) ..... 1374
7.9.15.3 PTM Control Register (Offset 08h) ..... 1376
7.9.16 Readiness Time Reporting Extended Capability ..... 1377
7.9.16.1 Readiness Time Reporting Extended Capability Header (Offset 00h) ..... 1378
7.9.16.2 Readiness Time Reporting 1 Register (Offset 04h) ..... 1379

7.9.16.3 Readiness Time Reporting 2 Register (Offset 08h) ..... 1380
7.9.17 Hierarchy ID Extended Capability ..... 1381
7.9.17.1 Hierarchy ID Extended Capability Header (Offset 00h) ..... 1382
7.9.17.2 Hierarchy ID Status Register (Offset 04h) ..... 1383
7.9.17.3 Hierarchy ID Data Register (Offset 08h) ..... 1384
7.9.17.4 Hierarchy ID GUID 1 Register (Offset 0Ch) ..... 1385
7.9.17.5 Hierarchy ID GUID 2 Register (Offset 10h) ..... 1385
7.9.17.6 Hierarchy ID GUID 3 Register (Offset 14h) ..... 1386
7.9.17.7 Hierarchy ID GUID 4 Register (Offset 18h) ..... 1386
7.9.17.8 Hierarchy ID GUID 5 Register (Offset 1Ch) ..... 1387
7.9.18 Vital Product Data Capability (VPD Capability) ..... 1387
7.9.18.1 VPD Address Register ..... 1388
7.9.18.2 VPD Data Register ..... 1389
7.9.19 Native PCIe Enclosure Management Extended Capability (NPEM Extended Capability) ..... 1389
7.9.19.1 NPEM Extended Capability Header (Offset 00h) ..... 1390
7.9.19.2 NPEM Capability Register (Offset 04h) ..... 1390
7.9.19.3 NPEM Control Register (Offset 08h) ..... 1392
7.9.19.4 NPEM Status Register (Offset 0Ch) ..... 1394
7.9.20 Alternate Protocol Extended Capability ..... 1395
7.9.20.1 Alternate Protocol Extended Capability Header (Offset 00h) ..... 1395
7.9.20.2 Alternate Protocol Capabilities Register (Offset 04h) ..... 1396
7.9.20.3 Alternate Protocol Control Register (Offset 08h) ..... 1396
7.9.20.4 Alternate Protocol Data 1 Register (Offset 0Ch) ..... 1397
7.9.20.5 Alternate Protocol Data 2 Register (Offset 10h) ..... 1398
7.9.20.6 Alternate Protocol Selective Enable Mask Register (Offset 14h) ..... 1398
7.9.21 Conventional PCI Advanced Features Capability (AF) ..... 1399
7.9.21.1 Advanced Features Capability Header (Offset 00h) ..... 1399
7.9.21.2 AF Capabilities Register (Offset 03h) ..... 1400
7.9.21.3 Conventional PCI Advanced Features Control Register (Offset 04h) ..... 1400
7.9.21.4 AF Status Register (Offset 05h) ..... 1401
7.9.22 SFI Extended Capability ..... 1401
7.9.22.1 SFI Extended Capability Header (Offset 00h) ..... 1402
7.9.22.2 SFI Capability Register (Offset 04h) ..... 1403
7.9.22.3 SFI Control Register (Offset 06h) ..... 1403
7.9.22.4 SFI Status Register (Offset 08h) ..... 1405
7.9.22.5 SFI CAM Address Register (Offset 0Ch) ..... 1406
7.9.22.6 SFI CAM Data Register (Offset 10h) ..... 1406
7.9.23 Subsystem ID and Subsystem Vendor ID Capability ..... 1406
7.9.23.1 Subsystem ID and Subsystem Vendor ID Capability Header (Offset 00h) ..... 1407
7.9.23.2 Subsystem ID and Subsystem Vendor ID Capability Data (Offset 04h) ..... 1407
7.9.24 Data Object Exchange Extended Capability ..... 1408
7.9.24.1 DOE Extended Capability Header (Offset 00h) ..... 1408
7.9.24.2 DOE Capabilities Register (Offset 04h) ..... 1409
7.9.24.3 DOE Control Register (Offset 08h) ..... 1410
7.9.24.4 DOE Status Register (Offset 0Ch) ..... 1411
7.9.24.5 DOE Write Data Mailbox Register (Offset 10h) ..... 1412
7.9.24.6 DOE Read Data Mailbox Register (Offset 14h) ..... 1412
7.9.25 Shadow Functions Extended Capability ..... 1413
7.9.25.1 Shadow Functions Extended Capability Header (Offset 00h) ..... 1415
7.9.25.2 Shadow Functions Capability Register (Offset 04h) ..... 1416

7.9.25.3 Shadow Functions Control Register (Offset 08h) ..... 1416
7.9.25.4 Shadow Functions Instance Register Entry ..... 1417
7.9.26 IDE Extended Capability ..... 1417
7.9.26.1 IDE Extended Capability Header (Offset 00h) ..... 1418
7.9.26.2 IDE Capability Register (Offset 04h) ..... 1419
7.9.26.3 IDE Control Register (Offset 08h) ..... 1421
7.9.26.4 Link IDE Register Block ..... 1421
7.9.26.4.1 Link IDE Stream Control Register ..... 1421
7.9.26.4.2 Link IDE Stream Status Register ..... 1423
7.9.26.5 Selective IDE Stream Register Block ..... 1424
7.9.26.5.1 Selective IDE Stream Capability Register ..... 1424
7.9.26.5.2 Selective IDE Stream Control Register ..... 1424
7.9.26.5.3 Selective IDE Stream Status Register ..... 1427
7.9.26.5.4 Selective IDE RID Association Register Block ..... 1427
7.9.26.5.4.1 IDE RID Association Register 1 ..... 1428
7.9.26.5.4.2 IDE RID Association Register 2 ..... 1428
7.9.26.5.5 Selective IDE Address Association Register Block. ..... 1429
7.9.26.5.5.1 IDE Address Association Register 1 ..... 1429
7.9.26.5.5.2 IDE Address Association Register 2 ..... 1429
7.9.26.5.5.3 IDE Address Association Register 3 ..... 1430
7.9.27 Null Capability ..... 1430
7.9.28 Null Extended Capability ..... 1431
7.9.29 Streamlined Virtual Channel Extended Capability (SVC) ..... 1431
7.9.29.1 Streamlined Virtual Channel Extended Capability Header (Offset 00h) ..... 1432
7.9.29.2 SVC Port Capability Register 1 (Offset 04h) ..... 1433
7.9.29.3 SVC Port Capability Register 2 (Offset 08h) ..... 1433
7.9.29.4 SVC Port Control Register (Offset 0Ch) ..... 1433
7.9.29.5 SVC Port Status Register (Offset 10h) ..... 1434
7.9.29.6 SVC Resource Capability Register ..... 1435
7.9.29.7 SVC Resource Control Register ..... 1435
7.9.29.8 SVC Resource Status Register ..... 1437
7.9.30 MMIO Register Block Locator Extended Capability (MRBL) ..... 1438
7.9.30.1 MRBL Extended Capability Header (Offset 00h) ..... 1439
7.9.30.2 MRBL Capabilities Register (Offset 04h) ..... 1439
7.9.30.3 MRBL Locator Register (Offset Varies) ..... 1440
8. Electrical Sub-Block ..... 1443
8.1 Electrical Specification Introduction ..... 1443
8.2 Interoperability Criteria ..... 1443
8.2.1 Data Rates ..... 1443
8.2.2 Refclk Architectures ..... 1443
8.3 Transmitter Specification ..... 1444
8.3.1 Measurement Setup for Characterizing Transmitters ..... 1444
8.3.1.1 Breakout and Replica Channels ..... 1445
8.3.2 Voltage Level Definitions ..... 1445
8.3.3 Tx Voltage Parameters ..... 1446
8.3.3.1 2.5 and 5.0 GT/s Transmitter Equalization ..... 1446
8.3.3.2 8.0, 16.0, 32.0, and 64.0 GT/s Transmitter Equalization ..... 1446
8.3.3.3 Tx Equalization Presets for $8.0,16.0,32.0$, and 64.0 GT/s. ..... 1448
8.3.3.4 Measuring Tx Equalization for $2.5 \mathrm{GT} / \mathrm{s}$ and $5.0 \mathrm{GT} / \mathrm{s}$ ..... 1450

8.3.3.5 Measuring Presets at $8.0,16.0,32.0$, and $64.0 \mathrm{GT} / \mathrm{s}$ ..... 1450
8.3.3.6 Method for Measuring $\mathrm{V}_{\text {TX-DIFF-PP }}$ at $2.5 \mathrm{GT} / \mathrm{s}$ and $5.0 \mathrm{GT} / \mathrm{s}$ ..... 1451
8.3.3.7 Method for Measuring $\mathrm{V}_{\text {TX-DIFF-PP }}$ at $8.0,16.0,32.0$, and $64.0 \mathrm{GT} / \mathrm{s}$ ..... 1451
8.3.3.8 Coefficient Range and Tolerance for $8.0,16.0,32.0$, and $64.0 \mathrm{GT} / \mathrm{s}$ ..... 1452
8.3.3.9 EIEOS and $\mathrm{V}_{\text {TX-EIEOS-FS }}$ and $\mathrm{V}_{\text {TX-EIEOS-RS }}$ Limits ..... 1455
8.3.3.10 Reduced Swing Signaling ..... 1456
8.3.3.11 Effective Tx Package Loss at $8.0,16.0,32.0$, and $64.0 \mathrm{GT} / \mathrm{s}$ ..... 1456
8.3.3.12 Linear Fit Pulse Response ..... 1458
8.3.3.13 Transmitter Signal-to Noise and Distortion Ratio (SNDR $_{T X}$ ) for $64.0 \mathrm{GT} / \mathrm{s}$ ..... 1460
8.3.3.14 Transmitter Ratio of Level Mismatch ( $\mathrm{R}_{\mathrm{LM}-\mathrm{Tx}}$ ) for $64.0 \mathrm{GT} / \mathrm{s}$ ..... 1462
8.3.3.14.1 Multi Pulse Response Fit (MPRF) - PAM4 Voltage Variant ..... 1463
8.3.4 Transmitter Margining ..... 1467
8.3.5 Tx Jitter Parameters ..... 1468
8.3.5.1 Post Processing Steps to Extract Jitter ..... 1468
8.3.5.2 Applying CTLE or De-embedding ..... 1468
8.3.5.3 Independent Refclk Measurement and Post Processing ..... 1469
8.3.5.4 Embedded and Non-Embedded Refclk Measurement and Post Processing ..... 1469
8.3.5.5 Behavioral CDR Characteristics. ..... 1470
8.3.5.6 Data Dependent and Uncorrelated Jitter ..... 1475
8.3.5.7 Data Dependent Jitter ..... 1475
8.3.5.8 Uncorrelated Total Jitter and Deterministic Jitter (Dual Dirac Model) ( $\mathrm{T}_{\text {TX-UTJ }}$ and $\mathrm{T}_{\text {TX-UDJDD }}$ ) ..... 1476
8.3.5.9 Random Jitter ( $\mathrm{T}_{\text {TX-RJ }}$ ) (informative) ..... 1476
8.3.5.10 Uncorrelated Total and Deterministic PWJ ( $\mathrm{T}_{\text {TX-UPW-TJ }}$ and $\mathrm{T}_{\text {TX-UPW-DJDD }}$ ) ..... 1476
8.3.6 Data Rate Dependent Parameters ..... 1478
8.3.7 Tx and Rx Return Loss for $2.5,5.0,8.0,16.0$, and $32.0 \mathrm{GT} / \mathrm{s}$ ..... 1481
8.3.8 Tx and Rx Return Loss for $64.0 \mathrm{GT} / \mathrm{s}$ ..... 1483
8.3.9 Transmitter PLL Bandwidth and Peaking ..... 1485
8.3.9.1 $2.5 \mathrm{GT} / \mathrm{s}$ and $5.0 \mathrm{GT} / \mathrm{s}$ Tx PLL Bandwidth and Peaking ..... 1485
8.3.9.2 $8.0 \mathrm{GT} / \mathrm{s}, 16.0 \mathrm{GT} / \mathrm{s}, 32.0 \mathrm{GT} / \mathrm{s}$, and $64.0 \mathrm{GT} / \mathrm{s}$ Tx PLL Bandwidth and Peaking ..... 1485
8.3.9.3 Series Capacitors ..... 1486
8.3.10 Data Rate Independent Tx Parameters ..... 1486
8.4 Receiver Specifications ..... 1487
8.4.1 Receiver Stressed Eye Specification ..... 1487
8.4.1.1 Breakout and Replica Channels ..... 1487
8.4.1.2 Calibration Channel Insertion Loss Characteristics ..... 1488
8.4.1.3 Post Processing Procedures ..... 1497
8.4.1.4 Behavioral Rx Package Models. ..... 1498
8.4.1.5 Behavioral CDR Model ..... 1498
8.4.1.6 No Behavioral Rx Equalization for 2.5 and $5.0 \mathrm{GT} / \mathrm{s}$. ..... 1498
8.4.1.7 Behavioral Rx Equalization for $8.0,16.0,32.0$, and $64.0 \mathrm{GT} / \mathrm{s}$. ..... 1498
8.4.1.8 Behavioral CTLE (8.0 and $16.0 \mathrm{GT} / \mathrm{s}$ ) ..... 1499
8.4.1.9 Behavioral CTLE (32.0 and $64.0 \mathrm{GT} / \mathrm{s}$ ) ..... 1501
8.4.1.10 Behavioral DFE (8.0, 16.0, 32.0, and $64.0 \mathrm{GT} / \mathrm{s}$ Only) ..... 1504
8.4.2 Stressed Eye Test ..... 1506
8.4.2.1 Procedure for Calibrating a Stressed EH/EW Eye ..... 1506
8.4.2.1.1 Post Processing Tool Requirements ..... 1511
8.4.2.2 Procedure for Testing Rx DUT ..... 1512
8.4.2.2.1 Sj Mask ..... 1512
8.4.2.3 Receiver Refclk Modes ..... 1520

8.4.2.3.1 Common Refclk Mode ..... 1520
8.4.2.3.2 Independent Refclk Mode ..... 1521
8.4.3 Common Receiver Parameters ..... 1522
8.4.3.1 5.0 GT/s Exit From Idle Detect (EFI) ..... 1524
8.4.3.2 Receiver Return Loss ..... 1524
8.4.4 Lane Margining at the Receiver - Electrical Requirements ..... 1524
8.4.5 Low Frequency and Miscellaneous Signaling Requirements ..... 1528
8.4.5.1 ESD Standards ..... 1528
8.4.5.2 Channel AC Coupling Capacitors ..... 1528
8.4.5.3 Short Circuit Requirements ..... 1528
8.4.5.4 Transmitter and Receiver Termination ..... 1529
8.4.5.5 Electrical Idle ..... 1529
8.4.5.6 DC Common Mode Voltage ..... 1529
8.4.5.7 Receiver Detection ..... 1530
8.5 Channel Tolerancing ..... 1530
8.5.1 Channel Compliance Testing ..... 1530
8.5.1.1 Behavioral Transmitter and Receiver Package Models ..... 1532
8.5.1.2 Measuring Package Performance (16.0 GT/s only) ..... 1542
8.5.1.3 Simulation Tool Requirements ..... 1542
8.5.1.3.1 Simulation Tool Chain Inputs ..... 1543
8.5.1.3.2 Processing Steps ..... 1543
8.5.1.3.3 Simulation Tool Outputs ..... 1543
8.5.1.3.4 Open Source Simulation Tool ..... 1544
8.5.1.4 Behavioral Transmitter Parameters ..... 1544
8.5.1.4.1 Deriving Voltage and Jitter Parameters ..... 1544
8.5.1.4.2 Optimizing Tx/Rx Equalization (8.0, 16.0, 32.0, and 64.0 GT/s only) ..... 1546
8.5.1.4.3 Pass/Fail Eye Characteristics ..... 1546
8.5.1.4.4 Characterizing Channel Common Mode Noise ..... 1549
8.5.1.4.5 Verifying V ${ }_{\text {CH-IDLE-DET-DIFF-pp }}$ ..... 1550
8.6 Refclk Specifications ..... 1550
8.6.1 Refclk Test Setup ..... 1550
8.6.2 REFCLK AC Specifications ..... 1551
8.6.3 Data Rate Independent Refclk Parameters ..... 1555
8.6.3.1 Low Frequency Refclk Jitter Limits ..... 1556
8.6.4 Refclk Architectures Supported ..... 1556
8.6.5 Filtering Functions Applied to Raw Data ..... 1557
8.6.5.1 PLL Filter Transfer Function Example ..... 1557
8.6.5.2 CDR Transfer Function Examples ..... 1558
8.6.6 Common Refclk Rx Architecture (CC) ..... 1558
8.6.6.1 Determining the Number of PLL BW and peaking Combinations ..... 1559
8.6.6.2 CDR and PLL BW and Peaking Limits for Common Refclk ..... 1560
8.6.7 Jitter Limits for Refclk Architectures ..... 1561
8.6.8 Form Factor Requirements for RefClock Architectures ..... 1562
9. Single Root I/O Virtualization and Sharing ..... 1565
9.1 SR-IOV Architectural Overview ..... 1565
9.2 SR-IOV Initialization and Resource Allocation ..... 1577
9.2.1 SR-IOV Resource Discovery ..... 1577
9.2.1.1 Configuring SR-IOV Capabilities. ..... 1577
9.2.1.1.1 Configuring the VF BAR Mechanisms ..... 1577

9.2.1.2 VF Discovery ..... 1578
9.2.1.3 Function Dependency Lists ..... 1580
9.2.1.4 Interrupt Resource Allocation ..... 1581
9.2.2 SR-IOV Reset Mechanisms ..... 1581
9.2.2.1 SR-IOV Conventional Reset ..... 1581
9.2.2.2 FLR That Targets a VF ..... 1581
9.2.2.3 FLR That Targets a PF ..... 1581
9.2.3 IOV Re-initialization and Reallocation ..... 1581
9.3 Configuration ..... 1582
9.3.1 SR-IOV Configuration Overview ..... 1582
9.3.2 Configuration Space ..... 1582
9.3.3 SR-IOV Extended Capability ..... 1582
9.3.3.1 SR-IOV Extended Capability Header (Offset 00h) ..... 1583
9.3.3.2 SR-IOV Capabilities Register (04h) ..... 1584
9.3.3.2.1 VF Migration Capable ..... 1585
9.3.3.2.2 ARI Capable Hierarchy Preserved ..... 1585
9.3.3.2.3 VF Larger-Tag Requester Support ..... 1585
9.3.3.2.4 VF Migration Interrupt Message Number ..... 1586
9.3.3.3 SR-IOV Control Register (Offset 08h) ..... 1586
9.3.3.3.1 VF Enable ..... 1588
9.3.3.3.2 VF Migration Enable ..... 1589
9.3.3.3.3 VF Migration Interrupt Enable ..... 1589
9.3.3.3.4 VF MSE (Memory Space Enable) ..... 1589
9.3.3.3.5 ARI Capable Hierarchy ..... 1590
9.3.3.4 SR-IOV Status Register (Offset 0Ah) ..... 1590
9.3.3.4.1 VF Migration Status ..... 1591
9.3.3.5 InitialVFs (Offset 0Ch) ..... 1591
9.3.3.6 TotalVFs (Offset 0Eh) ..... 1591
9.3.3.7 NumVFs (Offset 10h) ..... 1591
9.3.3.8 Function Dependency Link (Offset 12h) ..... 1591
9.3.3.9 First VF Offset (Offset 14h) ..... 1593
9.3.3.10 VF Stride (Offset 16h) ..... 1593
9.3.3.11 VF Device ID (Offset 1Ah) ..... 1593
9.3.3.12 Supported Page Sizes (Offset 1Ch) ..... 1594
9.3.3.13 System Page Size (Offset 20h) ..... 1594
9.3.3.14 VF BAR0 (Offset 24h), VF BAR1 (Offset 28h), VF BAR2 (Offset 2Ch), VF BAR3 (Offset 30h), VF BAR4 (Offset 34h), VF BARS (Offset 38h) ..... 1594
9.3.3.15 VF Migration State Array Offset (Deprecated) (Offset 3Ch) ..... 1595
9.3.4 PF/VF Configuration Space Header ..... 1595
9.3.5 PCI Express Capability Changes ..... 1595
9.3.6 PCI Standard Capabilities ..... 1595
9.3.7 PCI Express Extended Capabilities Changes ..... 1596
10. Address Translation Services (ATS) ..... 1601
10.1 ATS Architectural Overview ..... 1601
10.1.1 Address Translation Services (ATS) Overview ..... 1602
10.1.2 Page Request Interface Extension ..... 1606
10.1.3 Process Address Space ID (PASID) ..... 1607
10.1.4 ATS Memory Attributes ..... 1608
10.2 ATS Translation Services ..... 1608

10.2.1 Memory Requests with Address Type ..... 1608
10.2.2 Translation Requests ..... 1610
10.2.2.1 Attribute Field ..... 1611
10.2.2.2 Length Field ..... 1612
10.2.2.3 Tag Field ..... 1612
10.2.2.4 Untranslated Address Field ..... 1612
10.2.2.5 No Write (NW) Flag. ..... 1613
10.2.2.6 PASID on Translation Request ..... 1613
10.2.2.7 CXL Src ..... 1613
10.2.3 Translation Completion ..... 1613
10.2.3.1 Translated Address Field ..... 1617
10.2.3.2 Translation Range Size (S) Field ..... 1617
10.2.3.3 Non-snooped (N) Field ..... 1618
10.2.3.4 Untranslated Access Only (U) Field ..... 1618
10.2.3.5 Read (R) and Write (W) Fields ..... 1618
10.2.3.6 Execute Permitted (Exe) ..... 1619
10.2.3.7 Privileged Mode Access (Priv) ..... 1620
10.2.3.8 Global Mapping (Global) ..... 1621
10.2.3.9 ATS Memory Attributes ..... 1623
10.2.4 Completions with Multiple Translations ..... 1626
10.3 ATS Invalidation ..... 1627
10.3.1 Invalidate Request ..... 1627
10.3.2 Invalidate Completion ..... 1629
10.3.3 Invalidate Completion Semantics ..... 1631
10.3.4 Request Acceptance Rules ..... 1632
10.3.5 Invalidate Flow Control ..... 1632
10.3.6 Invalidate Ordering Semantics ..... 1633
10.3.7 Implicit Invalidation Events ..... 1634
10.3.8 PASID and Global Invalidate ..... 1635
10.4 Page Request Services ..... 1635
10.4.1 Page Request Message ..... 1636
10.4.1.1 PASID Usage ..... 1638
10.4.1.2 Managing PASID Usage on PRG Requests ..... 1638
10.4.1.2.1 Stop Marker Messages ..... 1639
10.4.2 Page Request Group Response Message ..... 1641
10.4.2.1 Response Code Field ..... 1642
10.4.2.2 PASID Usage on PRG Responses ..... 1643
10.5 ATS Configuration ..... 1643
10.5.1 ATS Extended Capability ..... 1643
10.5.1.1 ATS Extended Capability Header (Offset 00h) ..... 1643
10.5.1.2 ATS Capability Register (Offset 04h) ..... 1644
10.5.1.3 ATS Control Register (Offset 06h) ..... 1645
10.5.2 Page Request Extended Capability Structure ..... 1646
10.5.2.1 Page Request Extended Capability Header (Offset 00h) ..... 1647
10.5.2.2 Page Request Control Register (Offset 04h) ..... 1647
10.5.2.3 Page Request Status Register (Offset 06h) ..... 1648
10.5.2.4 Outstanding Page Request Capacity (Offset 08h) ..... 1649
10.5.2.5 Outstanding Page Request Allocation (Offset 0Ch) ..... 1650
11. TEE Device Interface Security Protocol (TDISP) ..... 1651

11.1 Overview of the TEE-I/O Security Model as it Relates to Devices ..... 1653
11.2 TDISP Rules ..... 1658
11.2.1 TDISP TLP Rules ..... 1662
11.2.2 TDISP Message Transport ..... 1663
11.2.3 Requirements for Requesters (TSM) ..... 1664
11.2.4 Requirements for Responders (DSM) ..... 1665
11.2.5 TDISP Timing Requirements ..... 1665
11.2.6 DSM Tracking and Handling of Locked TDI Configurations (Informative) ..... 1665
11.2.7 TVM Acceptance of a TDI ..... 1668
11.3 TDISP Message Formats and processing ..... 1668
11.3.1 TDISP Request Codes ..... 1668
11.3.2 TDISP Response Codes ..... 1669
11.3.3 TDISP Message Format and Protocol Versioning ..... 1670
11.3.4 GET_TDISP_VERSION ..... 1671
11.3.5 TDISP_VERSION ..... 1671
11.3.6 GET_TDISP_CAPABILITIES ..... 1671
11.3.7 TDISP_CAPABILITIES ..... 1672
11.3.8 LOCK_INTERFACE_REQUEST ..... 1672
11.3.9 LOCK_INTERFACE_RESPONSE ..... 1674
11.3.10GET_DEVICE_INTERFACE_REPORT ..... 1675
11.3.11DEVICE_INTERFACE_REPORT ..... 1676
11.3.12GET_DEVICE_INTERFACE_STATE ..... 1679
11.3.13DEVICE_INTERFACE_STATE ..... 1679
11.3.14START_INTERFACE_REQUEST ..... 1679
11.3.15START_INTERFACE_RESPONSE ..... 1680
11.3.16STOP_INTERFACE_REQUEST ..... 1680
11.3.17STOP_INTERFACE_RESPONSE ..... 1680
11.3.18BIND_P2P_STREAM_REQUEST ..... 1680
11.3.19BIND_P2P_STREAM_RESPONSE ..... 1681
11.3.20UNBIND_P2P_STREAM_REQUEST ..... 1682
11.3.21UNBIND_P2P_STREAM_RESPONSE ..... 1682
11.3.22SET_MMIO_ATTRIBUTE_REQUEST ..... 1683
11.3.23SET_MMIO_ATTRIBUTE_RESPONSE ..... 1684
11.3.24TDISP_ERROR ..... 1684
11.3.25VDM_REQUEST ..... 1685
11.3.26VDM_RESPONSE ..... 1686
11.4 Device Security Requirements ..... 1686
11.4.1 Device Identity and Authentication ..... 1686
11.4.2 Firmware and Configuration Measurements ..... 1686
11.4.3 Securing Interconnects ..... 1687
11.4.4 Device Attached Memory ..... 1687
11.4.5 TDI Security ..... 1688
11.4.6 Data Integrity Errors ..... 1689
11.4.7 Debug Modes ..... 1689
11.4.8 Conventional Reset ..... 1689
11.4.9 Function Level Reset ..... 1690
11.4.10Address Translation Services (ATS) and Access Control Services (ACS) ..... 1690
11.5 Requirements Placed on Host Security due to TDI Requirements ..... 1691
11.5.1 Address Translation ..... 1691
11.5.2 MMIO Access Control ..... 1692

11.5.3 DMA Access Control ..... 1692
11.5.4 Device Binding ..... 1692
11.5.5 Securing Interconnects ..... 1692
11.5.6 Data Integrity Errors ..... 1693
11.5.7 TSM Tracking and Handling of Locked Root Port Configurations (Informative) ..... 1693
11.5.8 IDE Extended Capability registers ..... 1696
11.6 Overview of Threat Model and Mitigations ..... 1696
11.6.1 Interconnect Security ..... 1697
11.6.2 Identity and Measurement Reporting ..... 1697
11.6.3 TDI Assignment and Detach ..... 1698
12. Architectural Out-of-Band Management ..... 1701
12.1 Introduction ..... 1701
12.2 Framework for Sidebands ..... 1701
12.3 Sideband Signaling Mechanisms ..... 1702
12.3.1 Discrete Sidebands ..... 1702
12.3.2 Flex I/O Sidebands ..... 1703
12.3.2.1 Flex I/O Default State Guidelines ..... 1703
12.3.2.2 Flex I/O Discovery Phase Guidelines ..... 1704
12.3.2.3 Flex I/O Compatibility Check Guidelines ..... 1704
12.3.2.4 Flex I/O Control Negotiation Guidelines ..... 1705
12.3.2.5 General Flex I/O Control Guidelines ..... 1705
12.3.3 Peripheral Sideband Tunnelling Interface (PESTI) Sidebands ..... 1706
12.3.3.1 PESTI Introduction ..... 1706
12.3.3.2 PESTI Physical Interface ..... 1707
12.3.3.3 PESTI Electrical Circuit ..... 1707
12.3.3.4 PESTI DC Specifications ..... 1709
12.3.3.5 PESTI Target Detection ..... 1709
12.3.3.6 PESTI Protocol Commands ..... 1710
12.3.3.6.1 Discovery Payload Request (DPR) ..... 1710
12.3.3.6.2 PESTI Virtual Wire Exchange (VWE) ..... 1710
12.3.3.6.3 PESTI Fanout MUX Control ..... 1710
12.3.3.7 PESTI Initiator Abort ..... 1711
12.3.3.8 PESTI Broadcast ..... 1711
12.3.3.9 PESTI Initiator Control and Status Registers ..... 1712
12.3.3.10 PESTI AC Specifications ..... 1714
12.3.3.11 PESTI Discovery Phase ..... 1715
12.3.3.12 PESTI Active Phase ..... 1718
12.3.3.13 PESTI Target Reset and Fault Handling ..... 1720
12.3.3.14 PESTI Fan-Out ..... 1720
12.3.3.15 PESTI Security Considerations ..... 1724
12.4 Managed USB 2.0 ..... 1724
12.5 2-Wire Interface ..... 1725
12.5.1 2-Wire Interface Use Cases ..... 1726
12.5.2 2-Wire Addressing ..... 1726
12.5.3 2-wire Bus Sharing ..... 1728
12.5.3.1 2-wire Multi-Drop Topology ..... 1728
12.5.3.2 SMBus MUX Use ..... 1728
12.5.3.3 2-wire Hub Use ..... 1729
12.5.4 [I3C-Basic] Support on Existing SMBus Signals ..... 1730

12.5.4.1 I3C Basic Overview ..... 1730
12.5.4.2 I3C Basic Discovery and Mode Changing. ..... 1731
12.5.4.3 I3C Basic DC and AC Signal Requirements ..... 1734
12.6 Field Replacement Unit (FRU) Information ..... 1736
12.6.1 FRU Information Device Requirements ..... 1736
12.6.1.1 FRU Information Device Requirements Specific to SMBus/I2C Mode ..... 1737
12.6.1.2 [SMBus]/[I2C] Access Protocol ..... 1738
12.6.2 FRU Information Format ..... 1739
12.6.3 Common PCI-SIG MultiRecord Descriptors ..... 1741
12.6.3.1 Connector Subdivision (Group ID 0h, Sub-Type 0h) ..... 1741
12.7 Out-of-Band Control Mechanism ..... 1743
12.8 Retimer Management ..... 1744
12.9 Internal Cable Management ..... 1744
A. Isochronous Applications ..... 1747
A. 1 Introduction ..... 1747
A. 2 Isochronous Contract and Contract Parameters ..... 1748
A.2.1 Isochronous Time Period and Isochronous Virtual Timeslot ..... 1749
A.2.2 Isochronous Payload Size ..... 1749
A.2.3 Isochronous Bandwidth Allocation ..... 1749
A.2.4 Isochronous Transaction Latency ..... 1751
A.2.5 An Example Illustrating Isochronous Parameters ..... 1752
A. 3 Isochronous Transaction Rules ..... 1752
A. 4 Transaction Ordering ..... 1752
A. 5 Isochronous Data Coherency ..... 1752
A. 6 Flow Control ..... 1753
A. 7 Considerations for Bandwidth Allocation ..... 1753
A.7.1 Isochronous Bandwidth of PCI Express Links ..... 1753
A.7.2 Isochronous Bandwidth of Endpoints ..... 1753
A.7.3 Isochronous Bandwidth of Switches ..... 1753
A.7.4 Isochronous Bandwidth of Root Complex ..... 1754
A. 8 Considerations for PCI Express Components ..... 1754
A.8.1 An Endpoint as a Requester ..... 1754
A.8.2 An Endpoint as a Completer ..... 1754
A.8.3 Switches ..... 1754
A.8.4 Root Complex ..... 1755
B. Symbol Encoding ..... 1757
C. Physical Layer Appendix ..... 1767
C. 1 8b/10b Data Scrambling Example ..... 1767
C. 2 128b/130b Data Scrambling Example ..... 1772
D. Request Dependencies ..... 1775
E. ID-Based Ordering Usage ..... 1779
E. 1 Introduction ..... 1779
E. 2 Potential Benefits with IDO Use ..... 1780
E.2.1 Benefits for MFD/RP Direct Connect ..... 1780
E.2.2 Benefits for Switched Environments ..... 1780
E.2.3 Benefits for Integrated Endpoints ..... 1780

E.2.4 IDO Use in Conjunction with RO ..... 1781
E. 3 When to Use IDO ..... 1781
E. 4 When Not to Use IDO ..... 1781
E.4.1 When Not to Use IDO with Endpoints ..... 1781
E.4.2 When Not to Use IDO with Root Ports ..... 1782
E. 5 Software Control of IDO Use ..... 1782
E.5.1 Software Control of Endpoint IDO Use ..... 1782
E.5.2 Software Control of Root Port IDO Use ..... 1783
F. Message Code Usage ..... 1785
G. Protocol Multiplexing ..... 1787
G. 1 Protocol Multiplexing Interactions with PCI Express ..... 1788
G. 2 PMUX Packets ..... 1792
G. 3 PMUX Packet Layout. ..... 1793
G.3.1 PMUX Packet Layout for 8b/10b Encoding ..... 1793
G.3.2 PMUX Packet Layout at 128b/130b Encoding. ..... 1794
G. 4 PMUX Control ..... 1797
G. 5 PMUX Extended Capability ..... 1797
G.5.1 PMUX Extended Capability Header (Offset 00h) ..... 1798
G.5.2 PMUX Capability Register (Offset 04h) ..... 1798
G.5.3 PMUX Control Register (Offset 08h) ..... 1799
G.5.4 PMUX Status Register (Offset 0Ch) ..... 1801
G.5.5 PMUX Protocol Array (Offsets 10h through 48h) ..... 1802
H. Flow Control Update Latency and ACK Update Latency Calculations ..... 1805
H. 1 Flow Control Update Latency ..... 1805
H. 2 Ack Latency ..... 1807
I. Async Hot-Plug Reference Model ..... 1811
I. 1 Async Hot-Plug Initial Configuration ..... 1813
I. 2 Async Removal Configuration and Interrupt Handling ..... 1814
I. 3 Async Hot-Add Configuration and Interrupt Handling ..... 1816
J. Alpha Power and Reverse lookup assignment ..... 1819
J. 1 Alpha Powers ..... 1820
J. 284 Byte to 86 Byte Encoder ..... 1831
J. 3250 Byte to 256 Byte Encoder example ..... 1832
J. 486 Byte to 84 Byte Decoder ..... 1835
J. 5256 Byte to 250 Byte decoder ..... 1839
K. MATLAB created generator matrix for CRC code ..... 1843
K. 1 Generator Matrix output ..... 1844
K. 2 Flit 8 byte LCRC ..... 1877
L. Example IDE TLPs and Test Keys ..... 2127
L. 1 Example NFM IDE TLP Without Partial Header Encryption ..... 2127
L. 2 Example FM IDE TLP Without Partial Header Encryption ..... 2128
L. 3 Example NFM IDE TLP With Partial Header Encryption ..... 2130
L. 4 Example FM IDE TLP With Partial Header Encryption ..... 2132
L. 5 IDE Test Keys ..... 2134

6.3-1.0-PUB - PCI Express ${ }^{\circledR}$ Base Specification Revision 6.3

# List of Figures 

Figure 1 Old Figure: Flit Mode and Non-Flit Mode processing with 8b/10b and 128b/130b encoding on the Transmit side ..... 86
Figure 2 New Figure: Flit Mode and Non-Flit Mode processing with 8b/10b and 128b/130b encoding on the Transmit side ..... 86
Figure 3 Old Figure: Flit Mode and Non-Flit Mode processing with 8b/10b and 128b/130b encoding on the Receive side ..... 86
Figure 4 New Figure: Flit Mode and Non-Flit Mode processing with 8b/10b and 128b/130b encoding on the Receive side ..... 87
Figure 5 Old Figure: Powers of alpha for the check bits for Bytes 0 to 84 ..... 88
Figure 6 New Figure: Powers of alpha for the check bits for Bytes 0 to 84 ..... 88
Figure 1-1 PCI Express Link ..... 134
Figure 1-2 Example PCI Express Topology ..... 136
Figure 1-3 Logical Block Diagram of a Switch ..... 139
Figure 1-4 High-Level Layering Diagram ..... 141
Figure 1-5 Packet Flow Through the Layers ..... 141
Figure 2-1 Layering Diagram Highlighting the Transaction Layer ..... 147
Figure 2-2 Serial View of a TLP ..... 149
Figure 2-3 Generic TLP Format - Non-Flit Mode ..... 150
Figure 2-4 Fields Present in All TLPs ..... 151
Figure 2-5 Fields Present in All Non-Flit Mode TLP Headers ..... 152
Figure 2-6 First DW of Header Base ..... 154
Figure 2-7 OHC-A1 ..... 167
Figure 2-8 OHC-A2 ..... 168
Figure 2-9 OHC-A3 ..... 168
Figure 2-10 OHC-A4 ..... 168
Figure 2-11 OHC-A5 ..... 169
Figure 2-12 OHC-B ..... 169
Figure 2-13 OHC-C ..... 169
Figure 2-14 Example Topology Illustrating Multiple Segments and NFM Subtrees ..... 172
Figure 2-15 Examples of Completer Target Memory Access for FetchAdd ..... 179
Figure 2-16 32-bit Address Routing - Non-Flit Mode ..... 181
Figure 2-17 64-bit Address Routing - Non-Flit Mode ..... 181
Figure 2-18 32-bit Address Routing - Flit Mode ..... 182
Figure 2-19 64-bit Address Routing - Flit Mode ..... 182
Figure 2-20 64-bit Address Routing - Flit Mode - 5 DW ..... 182
Figure 2-21 64-bit Address Routing - Flit Mode - 6 DW ..... 183
Figure 2-22 64-bit Address Routing - Flit Mode - 7 DW ..... 183
Figure 2-23 Non-ARI ID Routing with 4 DW Header - Non-Flit Mode ..... 185
Figure 2-24 ARI ID Routing with 4 DW Header - Non-Flit Mode ..... 186
Figure 2-25 Non-ARI ID Routing with 3 DW Header - Non-Flit Mode ..... 186
Figure 2-26 ARI ID Routing with 3 DW Header - Non-Flit Mode ..... 186
Figure 2-27 ID Routing with 3 DW Header - Flit Mode ..... 186
Figure 2-28 ID Routing with 4 DW Header - Flit Mode ..... 187
Figure 2-29 ID Routing with 5 DW Header - Flit Mode ..... 187
Figure 2-30 ID Routing with 6 DW Header - Flit Mode ..... 187
Figure 2-31 ID Routing with 7 DW Header - Flit Mode ..... 188
Figure 2-32 Location of Byte Enables in TLP Header - Non-Flit Mode ..... 189
Figure 2-33 Transaction Descriptor ..... 192

Figure 2-34 Transaction ID ..... 192
Figure 2-35 Attributes Field of Transaction Descriptor. ..... 200
Figure 2-36 Request Header Format for 64-bit Addressing of Memory ..... 203
Figure 2-37 Request Header Format for 32-bit Addressing of Memory ..... 203
Figure 2-38 Request Header Format for I/O Transactions - Non-Flit Mode ..... 204
Figure 2-39 Request Header Format for Configuration Transactions - Non-Flit Mode ..... 205
Figure 2-40 TPH TLP Prefix ..... 205
Figure 2-41 Location of PH[1:0] in a 4 DW Request Header - Non-Flit Mode ..... 206
Figure 2-42 Location of PH[1:0] in a 3 DW Request Header - Non-Flit Mode ..... 207
Figure 2-43 Location of ST[7:0] in the Memory Write Request Header - Non-Flit Mode ..... 207
Figure 2-44 Location of ST[7:0] in Memory Read, DMWr, and AtomicOp Request Headers - Non-Flit Mode ..... 208
Figure 2-45 Flit Mode Mem64 Request ..... 209
Figure 2-46 Flit Mode Mem32 Request ..... 209
Figure 2-47 Flit Mode IO Request ..... 209
Figure 2-48 Flit Mode Configuration Request ..... 210
Figure 2-49 Message Request Header - Non-Flit Mode ..... 211
Figure 2-50 Message Request Header - Flit Mode ..... 211
Figure 2-51 ERR_COR Message - Non-Flit Mode ..... 218
Figure 2-52 ERR_COR Message - Flit Mode ..... 218
Figure 2-53 Header for Vendor-Defined Messages - Non-Flit Mode ..... 221
Figure 2-54 Header for Vendor-Defined Messages - Flit Mode ..... 221
Figure 2-55 Header for PCI-SIG-Defined VDMs - Non-Flit Mode ..... 222
Figure 2-56 Header for PCI-SIG-Defined VDMs - Flit Mode ..... 222
Figure 2-57 DRS Message - Non-Flit Mode ..... 223
Figure 2-58 DRS Message - Flit Mode ..... 224
Figure 2-59 FRS Message - Non-Flit Mode ..... 225
Figure 2-60 FRS Message - Flit Mode ..... 225
Figure 2-61 Hierarchy ID Message - Non-Flit Mode ..... 227
Figure 2-62 Hierarchy ID Message - Flit Mode ..... 227
Figure 2-63 LTR Message - Non-Flit Mode ..... 229
Figure 2-64 LTR Message - Flit Mode ..... 229
Figure 2-65 OBFF Message - Non-Flit Mode ..... 230
Figure 2-66 OBFF Message - Flit Mode ..... 230
Figure 2-67 PTM Request/Response Message - Non-Flit Mode ..... 231
Figure 2-68 PTM ResponseD Message - Non-Flit Mode ..... 232
Figure 2-69 PTM Request/Response Message - Flit Mode ..... 232
Figure 2-70 PTM ResponseD Message - Flit Mode ..... 232
Figure 2-71 IDE Sync Message for Link IDE Stream - Non-Flit Mode ..... 234
Figure 2-72 IDE Sync Message for Link IDE Stream - Flit Mode ..... 234
Figure 2-73 IDE Sync Message for Selective IDE Stream - Non-Flit Mode ..... 235
Figure 2-74 IDE Sync Message for Selective IDE Stream - Flit Mode ..... 235
Figure 2-75 IDE Fail Message for Link IDE Stream - Non-Flit Mode ..... 235
Figure 2-76 IDE Fail Message for Link IDE Stream - Flit Mode ..... 236
Figure 2-77 IDE Fail Message for Selective IDE Stream - Non-Flit Mode ..... 236
Figure 2-78 IDE Fail Message for Selective IDE Stream - Flit Mode ..... 236
Figure 2-79 Completion Header Format - Non-Flit Mode ..... 237
Figure 2-80 (Non-ARI) Completer ID ..... 238
Figure 2-81 ARI Completer ID ..... 238
Figure 2-82 Completion Header Base Format - Non-UIO Flit Mode ..... 240
Figure 2-83 Completion Header Base Format - UIOWrCpl and UIORdCpl ..... 240
Figure 2-84 Completion Header Base Format - UIORdCplD ..... 240
Figure 2-85 Flit Mode Local TLP Prefix ..... 244

Figure 2-86 OHC-E1 ..... 246
Figure 2-87 OHC-E2 ..... 247
Figure 2-88 OHC-E4 ..... 247
Figure 2-89 Flowchart for Handling of Received TLPs ..... 249
Figure 2-90 Flowchart for Switch Handling of TLPs ..... 251
Figure 2-91 Flowchart for Handling of Received Request ..... 256
Figure 2-92 Example Completion Data when some Byte Enables are 0b ..... 259
Figure 2-93 Deadlock Examples with Intersystem Interconnects ..... 270
Figure 2-94 Virtual Channel Concept - An Illustration ..... 277
Figure 2-95 Virtual Channel Concept - Switch Internals (Upstream Flow) ..... 277
Figure 2-96 An Example of TC/VC Configurations ..... 280
Figure 2-97 Relationship Between Requester and Ultimate Completer ..... 281
Figure 2-98 Credit Block Example ..... 290
Figure 2-99 Calculation of 32-bit ECRC for TLP End to End Data Integrity Protection ..... 307
Figure 3-1 Layering Diagram Highlighting the Data Link Layer ..... 315
Figure 3-2 Data Link Control and Management State Machine. ..... 317
Figure 3-3 VC0 Flow Control Initialization Example with 8b/10b Encoding-based Framing ..... 329
Figure 3-4 DLLP Type and CRC Fields (Non-Flit Mode) ..... 331
Figure 3-5 DLLP Type Field (Flit Mode) ..... 331
Figure 3-6 Data Link Layer Packet Format for Ack and Nak (Non-Flit Mode) ..... 335
Figure 3-7 Data Link Layer Packet Format for NOP ..... 335
Figure 3-8 Data Link Layer Packet Format for NOP2 (Flit Mode) ..... 335
Figure 3-9 Data Link Layer Packet Format for InitFC1 ..... 336
Figure 3-10 Data Link Layer Packet Format for InitFC2 ..... 336
Figure 3-11 Data Link Layer Packet Format for UpdateFC ..... 337
Figure 3-12 Data Link Layer Packet Format for Power Management ..... 337
Figure 3-13 Data Link Layer Packet Format for Vendor-Specific. ..... 337
Figure 3-14 Data Link Layer Packet Format for Data Link Feature DLLP ..... 338
Figure 3-15 Data Link Packet Layer Format for Link Management (Flit Mode) ..... 338
Figure 3-16 Diagram of CRC Calculation for DLLPs ..... 340
Figure 3-17 TLP with LCRC and TLP Sequence Number Applied - Non-Flit Mode. ..... 341
Figure 3-18 TLP Following Application of TLP Sequence Number and 4 Bits ..... 343
Figure 3-19 Calculation of LCRC ..... 345
Figure 3-20 Received DLLP Error Check Flowchart ..... 349
Figure 3-21 Ack/Nak DLLP Processing Flowchart ..... 350
Figure 3-22 Receive Data Link Layer Handling of TLPs Flowchart ..... 353
Figure 4-1 Layering Diagram Highlighting Physical Layer ..... 357
Figure 4-2 Character to Symbol Mapping ..... 360
Figure 4-3 Bit Transmission Order on Physical Lanes - x1 Example ..... 360
Figure 4-4 Bit Transmission Order on Physical Lanes - x4 Example ..... 361
Figure 4-5 TLP with Framing Symbols Applied ..... 364
Figure 4-6 DLLP with Framing Symbols Applied ..... 365
Figure 4-7 Framed TLP on a x1 Link ..... 365
Figure 4-8 Framed TLP on a x2 Link ..... 366
Figure 4-9 Framed TLP on a x4 Link ..... 366
Figure 4-10 LFSR with 8b/10b Scrambling Polynomial ..... 367
Figure 4-11 Example of Bit Transmission Order in a x1 Link Showing 130 Bits of a Block ..... 368
Figure 4-12 Example of Bit Placement in a x4 Link with One Block per Lane ..... 369
Figure 4-13 Layout of Framing Tokens ..... 372
Figure 4-14 TLP and DLLP Layout ..... 374
Figure 4-15 Packet Transmission in a x8 Link ..... 374
Figure 4-16 Nullified TLP Layout in a x8 Link with Other Packets. ..... 374

Figure 4-17 SKP Ordered Set of Length 66-bit in a x8 Link ..... 375
Figure 4-18 LFSR with Scrambling Polynomial in 8.0 GT/s and Above Data Rate. ..... 382
Figure 4-19 Alternate Implementation of the LFSR for Descrambling. ..... 384
Figure 4-20 Precoding working the scrambler/ de-scrambler ..... 386
Figure 4-21 Example of Symbol placement in a x4 Link with 1b/1b encoding. ..... 389
Figure 4-22 Transmit side at $64.0 \mathrm{GT} / \mathrm{s}$ ..... 390
Figure 4-23 Receive side at $64.0 \mathrm{GT} / \mathrm{s}$ ..... 390
Figure 4-24 PAM4 Signaling at UI level: Voltage levels, 2-bit encoding, and their corresponding DC balance values ..... 391
Figure 4-25 The Sequence of Gray Coding, Precoding, and PAM4 voltage translation on an aligned 2-bit boundary on a per Lane ..... 392
Figure 4-26 Processing of Ordered Sets during or at the end of a Data Stream in Flit mode at 64.0 GT/s Data Rate. ..... 400
Figure 4-27 Flit Mode and Non-Flit Mode processing with 8b/10b and 128b/130b encoding on the Transmit side ..... 405
Figure 4-28 Flit Mode and Non-Flit Mode processing with 8b/10b and 128b/130b encoding on the Receive side ..... 406
Figure 4-29 DLP Byte to Bit Number Assignment ..... 410
Figure 4-30 DLP Bit usage ..... 410
Figure 4-31 Optimized_Update_FC ..... 411
Figure 4-32 Flit_Marker ..... 412
Figure 4-33 NOP Flit Common Header ..... 413
Figure 4-34 Flit Ack, Nak, and Discard Rules Flow Chart (Zoom-In to View) ..... 432
Figure 4-35 Flit Ack/Nak/Replay Example ..... 437
Figure 4-36 NOP.Empty Flit Payload. ..... 439
Figure 4-37 NOP.Debug Flit Debug Chunk ..... 439
Figure 4-38 Example Debug Chunk with one DW Debug Chunk Heaader and one DW of Debug Chunk Payload ..... 440
Figure 4-39 Example Debug Chunk with two DW Debug Chunk Heaader and one DW of Debug Chunk Payload ..... 440
Figure 4-40 Example Debug Chunk with four DW Debug Chunk Heaader and one DW of Debug Chunk Payload ..... 441
Figure 4-41 Example NOP.Debug Flit Payload with a single Debug Chunk with a one DW Debug Chunk Header ..... 441
Figure 4-42 Example NOP.Debug Flit Payload with multiple Debug Chunks with one DW Debug Chunk Headers ..... 442
Figure 4-43 Empty Debug Chunk ..... 443
Figure 4-44 Start Capture Trigger Debug Chunk ..... 444
Figure 4-45 Stop Capture Trigger Debug Chunk ..... 444
Figure 4-46 FC Information Tracked by Transmitter Debug Chunk ..... 445
Figure 4-47 FC Information Tracked by Reciever Debug Chunk. ..... 447
Figure 4-48 Flit Mode Transmitter Retry Flags and Counters Debug Chunk ..... 448
Figure 4-49 Flit Mode Receiver Retry Flags and Counters Debug Chunk ..... 449
Figure 4-50 Buffer Occupancy Debug Chunk ..... 450
Figure 4-51 Link Debug Request Debug Chunk ..... 450
Figure 4-52 NOP.Vendor Flit Payload. ..... 451
Figure 4-53 CRC generation/ checking in Flit. ..... 451
Figure 4-54 FEC Table: i to $\mathrm{a}^{\mathrm{i}}$ ..... 453
Figure 4-55 FEC Log Table: $a^{i}$ to $i$ ..... 454
Figure 4-56 H-matrix of the FEC ..... 454
Figure 4-57 Weight of check bits for different Bytes/bits ..... 455
Figure 4-58 ECC Decoder function. ..... 457
Figure 4-59 3-way ECC decode followed by CRC check of flit on the Receive side. ..... 458
Figure 4-60 8.0 GT/s Equalization Flow ..... 469
Figure 4-61 16.0 GT/s Equalization Flow ..... 469
Figure 4-62 64.0 GT/s Equalization Flow ..... 470
Figure 4-63 Equalization Bypass Example ..... 471
Figure 4-64 Alternate Protocol Negotiation and Equalization Bypass LTSSM States ..... 495
Figure 4-65 Electrical Idle Exit Ordered Set for 8.0 GT/s to 32.0 GT/s Data Rates (EIEOS) ..... 500
Figure 4-66 Example of L0p flow in a x16 Link ..... 520

Figure 4-67 Main State Diagram for Link Training and Status State Machine ..... 524
Figure 4-68 Detect Substate Machine ..... 526
Figure 4-69 Polling Substate Machine ..... 534
Figure 4-70 Configuration Substate Machine ..... 552
Figure 4-71 Recovery Substate Machine ..... 585
Figure 4-72 L0s Substate Machine ..... 590
Figure 4-73 L1 Substate Machine ..... 592
Figure 4-74 L2 Substate Machine ..... 593
Figure 4-75 Loopback Substate Machine ..... 601
Figure 4-76 Margin PHY Payload for Control SKP Ordered Set with 1b/1b Encoding ..... 609
Figure 4-77 LFSR PHY Payload for Control SKP Ordered Set with 1b/1b Encoding ..... 610
Figure 4-78 Polling.Compliance PHY Payload for Control SKP Ordered Set with 1b/1b Encoding ..... 610
Figure 4-79 Receiver Number Assignment ..... 626
Figure 4-80 Supported Retimer Topologies ..... 641
Figure 4-81 Retimer CLKREQ\# Connection Topology ..... 671
Figure 5-1 Link Power Management State Flow Diagram ..... 678
Figure 5-2 Entry into the L1 Link State ..... 686
Figure 5-3 Exit from L1 Link State Initiated by Upstream Component ..... 688
Figure 5-4 Conceptual Diagrams Showing Two Example Cases of WAKE\# Routing ..... 691
Figure 5-5 A Conceptual PME Control State Machine ..... 694
Figure 5-6 L1 Transition Sequence Ending with a Rejection (L0s Enabled) ..... 705
Figure 5-7 L1 Successful Transition Sequence ..... 706
Figure 5-8 Example of L1 Exit Latency Computation ..... 707
Figure 5-9 State Diagram for L1 PM Substates ..... 713
Figure 5-10 Downstream Port with a Single PLL ..... 714
Figure 5-11 Multiple Downstream Ports with a shared PLL ..... 715
Figure 5-12 Example: L1.1 Waveforms Illustrating Upstream Port Initiated Exit ..... 717
Figure 5-13 Example: L1.1 Waveforms Illustrating Downstream Port Initiated Exit ..... 718
Figure 5-14 L1.2 Substates ..... 719
Figure 5-15 Example: Illustration of Boundary Condition due to Different Sampling of CLKREQ\# ..... 720
Figure 5-16 Example: L1.2 Waveforms Illustrating Upstream Port Initiated Exit ..... 721
Figure 5-17 Example: L1.2 Waveforms Illustrating Downstream Port Initiated Exit ..... 722
Figure 5-18 Function Power Management State Transitions ..... 726
Figure 5-19 PCI Express Bridge Power Management Diagram ..... 729
Figure 6-1 Error Classification ..... 742
Figure 6-2 Flowchart Showing Sequence of Device Error Signaling and Logging Operations ..... 756
Figure 6-3 Pseudo Logic Diagram for Selected Error Message Control and Status Bits ..... 757
Figure 6-4 TC Filtering Example ..... 775
Figure 6-5 TC to VC Mapping Example ..... 775
Figure 6-6 An Example of Traffic Flow Illustrating Ingress and Egress ..... 776
Figure 6-7 An Example of Differentiated Traffic Flow Through a Switch ..... 777
Figure 6-8 Switch Arbitration Structure ..... 777
Figure 6-9 VC ID and Priority Order - An Example ..... 778
Figure 6-10 Multi-Function Arbitration Model ..... 781
Figure 6-11 Root Complex Represented as a Single Component ..... 818
Figure 6-12 Root Complex Represented as Multiple Components ..... 818
Figure 6-13 Example System Topology with ARI Devices ..... 833
Figure 6-14 Segmentation of the Multicast Address Range ..... 834
Figure 6-15 Latency Fields Format for LTR Messages ..... 849
Figure 6-16 CLKREQ\# and Clock Power Management ..... 853
Figure 6-17 Use of LTR and Clock Power Management ..... 854
Figure 6-18 Codes and Equivalent WAKE\# Patterns ..... 855

Example Platform Topology Showing a Link Where OBFF is Carried by Messages ..... 856
Figure 6-20 PASID TLP Prefix ..... 859
Figure 6-21 Example System Topologies using PTM ..... 863
Figure 6-22 Precision Time Measurement Link Protocol. ..... 864
Figure 6-23 Precision Time Measurement Example ..... 866
Figure 6-24 PTM Requester Operation ..... 869
Figure 6-25 PTM Timestamp Capture Example ..... 872
Figure 6-26 Example Illustrating Application of Enhanced Allocation ..... 878
Figure 6-27 Emergency Power Reduction State: Example Add-in Card ..... 882
Figure 6-28 FPB High Level Diagram and Example Topology ..... 887
Figure 6-29 Example Illustrating "Flattening" of a Switch ..... 888
Figure 6-30 Vector Mechanism for Address Range Decoding ..... 889
Figure 6-31 Relationship between FPB and non-FPB Decode Mechanisms ..... 890
Figure 6-32 Routing IDs (RIDs) and Supported Granularities ..... 892
Figure 6-33 Address in Memory Below 4 GB and Effect of Granularity ..... 894
Figure 6-34 VPD Format ..... 899
Figure 6-35 Example NPEM Configuration using a Downstream Port ..... 904
Figure 6-36 Example NPEM Configuration using an Upstream Port ..... 905
Figure 6-37 NPEM Command Flow ..... 906
Figure 6-38 Stack Diagram Illustration of Multiple Sessions and Connections ..... 912
Figure 6-39 Example Showing Relationships of Software and Hardware Elements ..... 913
Figure 6-40 DOE Data Object Format ..... 914
Figure 6-41 DOE Data Object Header 1 ..... 914
Figure 6-42 DOE Data Object Header 2 ..... 914
Figure 6-43 DOE Discovery Request Data Object Contents (3rd DW) ..... 915
Figure 6-44 DOE Discovery Response Data Object Contents (3rd DW) ..... 916
Figure 6-45 DOE Discovery Response Data Object Contents (4th DW) ..... 916
Figure 6-46 CMA-SPDM as Part of a Layered Architecture ..... 923
Figure 6-47 Example System Showing Multiple Access Mechanisms ..... 925
Figure 6-48 Example Add-In-Card Supporting CMA-SPDM ..... 926
Figure 6-49 Byte Mapping of SPDM Messages Including Example Payload ..... 929
Figure 6-50 Byte Mapping of Secured CMA-SPDM Messages Including Example Payload ..... 930
Figure 6-51 Example DMWr Data Payload Template ..... 935
Figure 6-52 IDE Secures TLPs Between Ports ..... 937
Figure 6-53 IDE Stream State Machine ..... 941
Figure 6-54 IDE Stream State Machine ..... 942
Figure 6-55 IDE Key Management (IDE_KM) and Related Specifications \& Capabilities ..... 944
Figure 6-56 Query (QUERY) Data Object ..... 949
Figure 6-57 Query Response (QUERY_RESP) Data Object ..... 950
Figure 6-58 Key Programming (KEY_PROG) Data Object with Example 256b Key ..... 950
Figure 6-59 Key Programming Acknowledgement (KP_ACK) Data Object ..... 951
Figure 6-60 Key Set Go (K_SET_GO) Data Object ..... 951
Figure 6-61 Key Set Stop (K_SET_STOP) Data Object ..... 951
Figure 6-62 Key Set Go/Stop Acknowledgement (K_GOSTOP_ACK) Data Object ..... 951
Figure 6-63 IDE_KM Example ..... 953
Figure 6-64 IDE TLP Prefix (NFM) ..... 954
Figure 6-65 MAC Layout ..... 955
Figure 6-66 Example of IDE TLP for a Link IDE Stream without Aggregation (Non-Flit Mode) ..... 955
Figure 6-67 IDE TLP - Example Showing Aggregation of Two TLPs for a Link IDE Stream (Non-Flit Mode) ..... 956
Figure 6-68 IDE TLP - Example of IDE TLP for a Selective IDE Stream without Aggregation (Non-Flit Mode) ..... 956
Figure 6-69 IDE TLP - Example Showing Aggregation of Two TLPs for a Selective IDE Stream (Non-Flit Mode) ..... 956
Figure 6-70 Example of IDE TLP for a Link IDE Stream without Aggregation (Flit Mode) ..... 957

Figure 6-71 IDE TLP - Example Showing Aggregation of Two TLPs for a Link IDE Stream (Flit Mode) ..... 957
Figure 6-72 IDE TLP - Example of IDE TLP for a Selective IDE Stream without Aggregation (Flit Mode) ..... 958
Figure 6-73 IDE TLP - Example Showing Aggregation of Two TLPs for a Selective IDE Stream (Flit Mode) ..... 958
Figure 6-74 High Level Flow For Partial Header Encryption ..... 959
Figure 6-75 Partial Header Encryption in NFM with Byte Enables ..... 961
Figure 6-76 Partial Header Encryption in NFM without Byte Enables ..... 962
Figure 6-77 Partial Header Encryption in FM with OHC-A1 ..... 963
Figure 6-78 Partial Header Encryption in FM without OHC-A1 ..... 964
Figure 6-79 Example Illustrating PCRC Application to Two Aggregated IDE TLPs for a Link IDE Stream (NFM) ..... 965
Figure 6-80 Example - Posted Requests Allowed to Bypass Non-Posted Requests ..... 973
Figure 6-81 Example - Non-Posted Requests Never Allowed to Bypass Posted Requests ..... 974
Figure 6-82 Example - Secure Non-Posted Request Reordering Not Allowed Over PCIe Fabric ..... 974
Figure 6-83 MMIO Register Blocks ..... 982
Figure 6-84 MCAP Register Block ..... 983
Figure 6-85 MCAP Array Register Block ..... 984
Figure 6-86 MCAP Array Register 1 ..... 984
Figure 6-87 MCAP Array Register 2 ..... 985
Figure 6-88 MCAP Header Register Block ..... 985
Figure 6-89 MCAP Header Register 1 ..... 985
Figure 6-90 MCAP Header Register 2 ..... 986
Figure 6-91 MCAP Header Register 3 ..... 986
Figure 6-92 MCAP Header Register 4 ..... 987
Figure 6-93 MMB Registers ..... 989
Figure 6-94 MMB Capabilities Register ..... 990
Figure 6-95 MMB Control Register ..... 991
Figure 6-96 MMB Command Register ..... 992
Figure 6-97 MMB Status Register ..... 993
Figure 6-98 MMB Payload Registers ..... 995
Figure 6-99 MMPT Registers ..... 995
Figure 6-100 MMPT Capabilities Register ..... 996
Figure 6-101 MMPT Control Register ..... 996
Figure 6-102 MMPT Receive Message Notification Register ..... 997
Figure 6-103 MDVS Register Block ..... 998
Figure 6-104 MDVS Register Block Header Register 1 ..... 998
Figure 6-105 MDVS Register Block Header Register 2 ..... 999
Figure 6-106 MDVS Register Block Header Register 3 ..... 999
Figure 7-1 PCI Express Root Complex Device Mapping ..... 1007
Figure 7-2 PCI Express Switch Device Mapping ..... 1008
Figure 7-3 PCI Express Configuration Space Layout ..... 1009
Figure 7-4 Common Configuration Space Header ..... 1020
Figure 7-5 Command Register ..... 1021
Figure 7-6 Status Register ..... 1024
Figure 7-7 Class Code Register ..... 1027
Figure 7-8 Header Type Register ..... 1028
Figure 7-9 BIST Register ..... 1029
Figure 7-10 Type 0 Configuration Space Header ..... 1031
Figure 7-11 Base Address Register for Memory ..... 1032
Figure 7-12 Base Address Register for I/O ..... 1032
Figure 7-13 Expansion ROM Base Address Register ..... 1037
Figure 7-14 Type 1 Configuration Space Header ..... 1040
Figure 7-15 Secondary Status Register ..... 1043
Figure 7-16 Bridge Control Register ..... 1046

Figure 7-17 PCI Power Management Capability Structure ..... 1048
Figure 7-18 Power Management Capabilities Register ..... 1049
Figure 7-19 Power Management Control/Status Register ..... 1051
Figure 7-20 Power Management Data Register ..... 1053
Figure 7-21 PCI Express Capability Structure ..... 1055
Figure 7-22 PCI Express Capability List Register ..... 1056
Figure 7-23 PCI Express Capabilities Register ..... 1056
Figure 7-24 Device Capabilities Register ..... 1058
Figure 7-25 Device Control Register ..... 1062
Figure 7-26 Device Status Register ..... 1069
Figure 7-27 Link Capabilities Register ..... 1071
Figure 7-28 Link Control Register ..... 1075
Figure 7-29 Link Status Register ..... 1082
Figure 7-30 Slot Capabilities Register ..... 1084
Figure 7-31 Slot Control Register ..... 1087
Figure 7-32 Slot Status Register ..... 1090
Figure 7-33 Root Control Register ..... 1092
Figure 7-34 Root Capabilities Register ..... 1093
Figure 7-35 Root Status Register ..... 1094
Figure 7-36 Device Capabilities 2 Register ..... 1095
Figure 7-37 Device Control 2 Register ..... 1100
Figure 7-38 Link Capabilities 2 Register ..... 1104
Figure 7-39 Link Control 2 Register ..... 1107
Figure 7-40 Link Status 2 Register ..... 1110
Figure 7-41 Slot Capabilities 2 Register ..... 1114
Figure 7-42 PCI Express Extended Configuration Space Layout ..... 1115
Figure 7-43 PCI Express Extended Capability Header ..... 1115
Figure 7-44 MSI Capability Structure for 32-bit Message Address ..... 1116
Figure 7-45 MSI Capability Structure for 64-bit Message Address ..... 1117
Figure 7-46 MSI Capability Structure for 32-bit Message Address and PVM ..... 1117
Figure 7-47 MSI Capability Structure for 64-bit Message Address and PVM ..... 1117
Figure 7-48 MSI Capability Header ..... 1118
Figure 7-49 Message Control Register for MSI ..... 1119
Figure 7-50 Message Address Register for MSI ..... 1120
Figure 7-51 Message Upper Address Register for MSI ..... 1121
Figure 7-52 Message Data Register for MSI ..... 1121
Figure 7-53 Extended Message Data Register for MSI ..... 1122
Figure 7-54 Mask Bits Register for MSI ..... 1123
Figure 7-55 Pending Bits Register for MSI ..... 1123
Figure 7-56 MSI-X Capability Structure ..... 1124
Figure 7-57 MSI-X Table Structure ..... 1125
Figure 7-58 MSI-X PBA Structure ..... 1125
Figure 7-59 MSI-X Capability Header ..... 1127
Figure 7-60 Message Control Register for MSI-X ..... 1128
Figure 7-61 Table Offset/Table BIR Register for MSI-X ..... 1129
Figure 7-62 PBA Offset/PBA BIR Register for MSI-X ..... 1129
Figure 7-63 Message Address Register for MSI-X Table Entries ..... 1130
Figure 7-64 Message Upper Address Register for MSI-X Table Entries ..... 1131
Figure 7-65 Message Data Register for MSI-X Table Entries ..... 1131
Figure 7-66 Vector Control Register for MSI-X Table Entries ..... 1132
Figure 7-67 Pending Bits Register for MSI-X PBA Entries ..... 1132
Figure 7-68 Secondary PCI Express Extended Capability Structure ..... 1134

Figure 7-69 Secondary PCI Express Extended Capability Header ..... 1135
Figure 7-70 Link Control 3 Register ..... 1135
Figure 7-71 Lane Error Status Register ..... 1136
Figure 7-72 Lane Equalization Control Register ..... 1137
Figure 7-73 Lane Equalization Control Register Entry ..... 1137
Figure 7-74 Data Link Feature Extended Capability ..... 1140
Figure 7-75 Data Link Feature Extended Capability Header ..... 1140
Figure 7-76 Data Link Feature Capabilities Register ..... 1141
Figure 7-77 Data Link Feature Status Register ..... 1142
Figure 7-78 Physical Layer 16.0 GT/s Extended Capability ..... 1144
Figure 7-79 Physical Layer 16.0 GT/s Extended Capability Header ..... 1145
Figure 7-80 16.0 GT/s Capabilities Register ..... 1145
Figure 7-81 16.0 GT/s Control Register ..... 1146
Figure 7-82 16.0 GT/s Status Register ..... 1146
Figure 7-83 16.0 GT/s Local Data Parity Mismatch Status Register ..... 1147
Figure 7-84 16.0 GT/s First Retimer Data Parity Mismatch Status Register ..... 1148
Figure 7-85 16.0 GT/s Second Retimer Data Parity Mismatch Status Register ..... 1148
Figure 7-86 16.0 GT/s Lane Equalization Control Register Entry ..... 1149
Figure 7-87 Physical Layer 32.0 GT/s Extended Capability ..... 1151
Figure 7-88 Physical Layer 32.0 GT/s Extended Capability Header ..... 1152
Figure 7-89 32.0 GT/s Capabilities Register ..... 1152
Figure 7-90 32.0 GT/s Control Register ..... 1153
Figure 7-91 32.0 GT/s Status Register ..... 1154
Figure 7-92 Received Modified TS Data 1 Register ..... 1156
Figure 7-93 Received Modified TS Data 2 Register ..... 1157
Figure 7-94 Transmitted Modified TS Data 1 Register ..... 1158
Figure 7-95 Transmitted Modified TS Data 2 Register ..... 1159
Figure 7-96 32.0 GT/s Lane Equalization Control Register Entry ..... 1160
Figure 7-97 32.0 GT/s Lane Equalization Control Register Entry ..... 1161
Figure 7-98 Physical Layer 64.0 GT/s Extended Capability Header ..... 1162
Figure 7-99 64.0 GT/s Capabilities Register ..... 1162
Figure 7-100 64.0 GT/s Control Register ..... 1163
Figure 7-101 64.0 GT/s Status Register ..... 1163
Figure 7-102 64.0 GT/s Lane Equalization Control Register Entry ..... 1165
Figure 7-103 Flit Logging Extended Capability Structure ..... 1166
Figure 7-104 Flit Logging Extended Capability Header ..... 1167
Figure 7-105 Flit Error Log 1 Register ..... 1168
Figure 7-106 Flit Error Log 2 Register ..... 1170
Figure 7-107 Flit Error Counter Control Register ..... 1171
Figure 7-108 Flit Error Counter Status Register ..... 1172
Figure 7-109 FBER Measurement Control Register ..... 1173
Figure 7-110 FBER Measurement Status 1 Register ..... 1174
Figure 7-111 FBER Measurement Status 2 Register ..... 1174
Figure 7-112 FBER Measurement Status 3 Register ..... 1175
Figure 7-113 FBER Measurement Status 4 Register ..... 1175
Figure 7-114 FBER Measurement Status 5 Register ..... 1176
Figure 7-115 FBER Measurement Status 6 Register ..... 1176
Figure 7-116 FBER Measurement Status 7 Register ..... 1176
Figure 7-117 FBER Measurement Status 8 Register ..... 1177
Figure 7-118 FBER Measurement Status 9 Register ..... 1177
Figure 7-119 FBER Measurement Status 10 Register ..... 1178
Figure 7-120 Device 3 Extended Capability Structure ..... 1178

Figure 7-121 Device 3 Extended Capability Header ..... 1179
Figure 7-122 Device Capabilities 3 Register ..... 1179
Figure 7-123 Device Control 3 Register ..... 1182
Figure 7-124 Device Status 3 Register ..... 1184
Figure 7-125 Lane Margining at the Receiver Extended Capability ..... 1186
Figure 7-126 Lane Margining at the Receiver Extended Capability Header ..... 1187
Figure 7-127 Margining Port Capabilities Register ..... 1187
Figure 7-128 Margining Port Status Register ..... 1188
Figure 7-129 Lane N: Margining Control Register Entry ..... 1189
Figure 7-130 Lane N: Margining Lane Status Register Entry ..... 1190
Figure 7-131 ACS Extended Capability ..... 1191
Figure 7-132 ACS Extended Capability Header ..... 1191
Figure 7-133 ACS Capability Register ..... 1192
Figure 7-134 ACS Control Register ..... 1193
Figure 7-135 Egress Control Vector Register ..... 1196
Figure 7-136 Power Budgeting Extended Capability ..... 1197
Figure 7-137 Power Budgeting Extended Capability Header ..... 1198
Figure 7-138 Power Budgeting Control Register ..... 1199
Figure 7-139 Power Budgeting Data Register ..... 1201
Figure 7-140 Power Budgeting Capability Register ..... 1205
Figure 7-141 Power Budgeting Sense Detect Register ..... 1207
Figure 7-142 LTR Extended Capability Structure ..... 1210
Figure 7-143 LTR Extended Capability Header ..... 1210
Figure 7-144 Max Snoop Latency Register ..... 1210
Figure 7-145 Max No-Snoop Latency Register ..... 1211
Figure 7-146 L1 PM Substates Extended Capability ..... 1212
Figure 7-147 L1 PM Substates Extended Capability Header ..... 1212
Figure 7-148 L1 PM Substates Capabilities Register ..... 1213
Figure 7-149 L1 PM Substates Control 1 Register ..... 1214
Figure 7-150 L1 PM Substates Control 2 Register ..... 1216
Figure 7-151 L1 PM Substates Status Register ..... 1217
Figure 7-152 Advanced Error Reporting Extended Capability - Functions that do not support Flit Mode Structure ..... 1218
Figure 7-153 Advanced Error Reporting Extended Capability - Functions that support Flit Mode Structure ..... 1219
Figure 7-154 Advanced Error Reporting Extended Capability Header ..... 1220
Figure 7-155 Uncorrectable Error Status Register ..... 1221
Figure 7-156 Uncorrectable Error Mask Register ..... 1223
Figure 7-157 Uncorrectable Error Severity Register ..... 1226
Figure 7-158 Correctable Error Status Register ..... 1228
Figure 7-159 Correctable Error Mask Register ..... 1229
Figure 7-160 Advanced Error Capabilities and Control Register ..... 1231
Figure 7-161 Header Log Register ..... 1233
Figure 7-162 Root Error Command Register ..... 1234
Figure 7-163 Root Error Status Register ..... 1235
Figure 7-164 Error Source Identification Register ..... 1236
Figure 7-165 TLP Prefix Log Register ..... 1238
Figure 7-166 First DW of Enhanced Allocation Capability ..... 1238
Figure 7-167 Second DW of Enhanced Allocation Capability ..... 1239
Figure 7-168 First DW of Each Entry for Enhanced Allocation Capability ..... 1240
Figure 7-169 Format of Entry for Enhanced Allocation Capability ..... 1242
Figure 7-170 Example Entry with 64b Base and 64b MaxOffset ..... 1243
Figure 7-171 Example Entry with 64b Base and 32b MaxOffset ..... 1244

Figure 7-172 Example Entry with 32b Base and 64b MaxOffset ..... 1244
Figure 7-173 Example Entry with 32b Base and 32b MaxOffset ..... 1244
Figure 7-174 Resizable BAR Extended Capability ..... 1246
Figure 7-175 Resizable BAR Extended Capability Header ..... 1247
Figure 7-176 Resizable BAR Capability Register ..... 1248
Figure 7-177 Resizable BAR Control Register ..... 1250
Figure 7-178 VF Resizable BAR Extended Capability ..... 1253
Figure 7-179 VF Resizable BAR Extended Capability Header ..... 1254
Figure 7-180 VF Resizable BAR Control Register ..... 1255
Figure 7-181 ARI Extended Capability ..... 1256
Figure 7-182 ARI Extended Capability Header ..... 1256
Figure 7-183 ARI Capability Register ..... 1257
Figure 7-184 ARI Control Register ..... 1258
Figure 7-185 PASID Extended Capability Structure ..... 1259
Figure 7-186 PASID Extended Capability Header ..... 1259
Figure 7-187 PASID Capability Register ..... 1260
Figure 7-188 PASID Control Register ..... 1261
Figure 7-189 FRS Queueing Extended Capability ..... 1262
Figure 7-190 FRS Queueing Extended Capability Header ..... 1262
Figure 7-191 FRS Queueing Capability Register ..... 1263
Figure 7-192 FRS Queueing Status Register ..... 1263
Figure 7-193 FRS Queueing Control Register ..... 1264
Figure 7-194 FRS Message Queue Register ..... 1264
Figure 7-195 FPB Capability Structure ..... 1265
Figure 7-196 FPB Capability Header ..... 1266
Figure 7-197 FPB Capabilities Register ..... 1266
Figure 7-198 FPB RID Vector Control 1 Register ..... 1268
Figure 7-199 FPB RID Vector Control 2 Register ..... 1270
Figure 7-200 FPB MEM Low Vector Control Register ..... 1270
Figure 7-201 FPB MEM High Vector Control 1 Register ..... 1272
Figure 7-202 FPB MEM High Vector Control 2 Register ..... 1273
Figure 7-203 FPB Vector Access Control Register ..... 1274
Figure 7-204 FPB Vector Access Data Register ..... 1275
Figure 7-205 Flit Performance Measurement Extended Capability Structure ..... 1276
Figure 7-206 Flit Performance Measurement Extended Capability Header ..... 1277
Figure 7-207 Flit Performance Measurement Capability Register ..... 1277
Figure 7-208 Flit Performance Measurement Control Register ..... 1278
Figure 7-209 Flit Performance Measurement Status Register ..... 1280
Figure 7-210 LTSSM Performance Measurement Status Register ..... 1281
Figure 7-211 Flit Error Injection Extended Capability Structure ..... 1283
Figure 7-212 Flit Error Injection Extended Capability Header ..... 1283
Figure 7-213 Flit Error Injection Capability Register ..... 1284
Figure 7-214 Flit Error Injection Control 1 Register ..... 1284
Figure 7-215 Flit Error Injection Control 2 Register ..... 1286
Figure 7-216 Flit Error Injection Status Register ..... 1287
Figure 7-217 Ordered Set Error Injection Control 1 Register ..... 1288
Figure 7-218 Ordered Set Error Injection Control 2 Register ..... 1289
Figure 7-219 Ordered Set Tx Error Injection Status Register ..... 1290
Figure 7-220 Ordered Set Rx Error Injection Status Register ..... 1291
Figure 7-221 NOP Flit Extended Capability ..... 1293
Figure 7-222 NOP Flit Extended Capability Header ..... 1293
Figure 7-223 NOP Flit Capabilites Register ..... 1294

Figure 7-224 NOP Flit Control 1 Register ..... 1294
Figure 7-225 NOP Flit Control 2 Register ..... 1296
Figure 7-226 NOP Flit Status Register ..... 1297
Figure 7-227 Virtual Channel Extended Capability Structure. ..... 1298
Figure 7-228 Virtual Channel Extended Capability Header ..... 1299
Figure 7-229 Port VC Capability Register 1 ..... 1300
Figure 7-230 Port VC Capability Register 2 ..... 1301
Figure 7-231 Port VC Control Register ..... 1302
Figure 7-232 Port VC Status Register ..... 1303
Figure 7-233 VC Resource Capability Register ..... 1303
Figure 7-234 VC Resource Control Register ..... 1305
Figure 7-235 VC Resource Status Register ..... 1307
Figure 7-236 Example VC Arbitration Table with 32 Phases ..... 1308
Figure 7-237 Example Port Arbitration Table with 128 Phases and 2-bit Table Entries ..... 1309
Figure 7-238 MFVC Capability Structure ..... 1310
Figure 7-239 MFVC Extended Capability Header ..... 1310
Figure 7-240 MFVC Port VC Capability Register 1 ..... 1311
Figure 7-241 MFVC Port VC Capability Register 2 ..... 1312
Figure 7-242 MFVC Port VC Control Register ..... 1313
Figure 7-243 MFVC Port VC Status Register ..... 1314
Figure 7-244 MFVC VC Resource Capability Register ..... 1314
Figure 7-245 MFVC VC Resource Control Register ..... 1315
Figure 7-246 MFVC VC Resource Status Register ..... 1318
Figure 7-247 Device Serial Number Extended Capability Structure ..... 1320
Figure 7-248 Device Serial Number Extended Capability Header ..... 1321
Figure 7-249 Serial Number Register ..... 1321
Figure 7-250 Vendor-Specific Capability ..... 1322
Figure 7-251 VSEC Capability Structure ..... 1323
Figure 7-252 Vendor-Specific Extended Capability Header ..... 1323
Figure 7-253 Vendor-Specific Header ..... 1324
Figure 7-254 Designated Vendor-Specific Extended Capability ..... 1325
Figure 7-255 Designated Vendor-Specific Extended Capability Header ..... 1325
Figure 7-256 Designated Vendor-Specific Header 1 ..... 1326
Figure 7-257 Designated Vendor-Specific Header 2 ..... 1327
Figure 7-258 RCRB Header Extended Capability Structure ..... 1327
Figure 7-259 RCRB Header Extended Capability Header ..... 1328
Figure 7-260 RCRB Vendor ID and Device ID register ..... 1328
Figure 7-261 RCRB Capabilities register ..... 1329
Figure 7-262 RCRB Control register ..... 1329
Figure 7-263 Root Complex Link Declaration Extended Capability ..... 1331
Figure 7-264 Root Complex Link Declaration Extended Capability Header ..... 1331
Figure 7-265 Element Self Description Register ..... 1332
Figure 7-266 Link Entry ..... 1333
Figure 7-267 Link Description Register ..... 1333
Figure 7-268 Link Address for Link Type 0 ..... 1334
Figure 7-269 Link Address for Link Type 1 ..... 1335
Figure 7-270 Root Complex Internal Link Control Extended Capability ..... 1336
Figure 7-271 Root Complex Internal Link Control Extended Capability Header ..... 1336
Figure 7-272 Root Complex Link Capabilities Register ..... 1337
Figure 7-273 Root Complex Link Control Register ..... 1339
Figure 7-274 Root Complex Link Status Register ..... 1341
Figure 7-275 Root Complex Event Collector Endpoint Association Extended Capability ..... 1342

Figure 7-276 Root Complex Event Collector Endpoint Association Extended Capability Header ..... 1342
Figure 7-277 RCEC Associated Bus Numbers Register ..... 1343
Figure 7-278 Multicast Extended Capability Structure ..... 1345
Figure 7-279 Multicast Extended Capability Header ..... 1345
Figure 7-280 Multicast Capability Register. ..... 1346
Figure 7-281 Multicast Control Register ..... 1347
Figure 7-282 MC_Base_Address Register ..... 1347
Figure 7-283 MC_Receive Register ..... 1348
Figure 7-284 MC_Block_All Register ..... 1348
Figure 7-285 MC_Block_Untranslated Register ..... 1349
Figure 7-286 MC_Overlay_BAR Register ..... 1350
Figure 7-287 Dynamic Power Allocation Extended Capability Structure ..... 1350
Figure 7-288 DPA Extended Capability Header ..... 1351
Figure 7-289 DPA Capability Register ..... 1351
Figure 7-290 DPA Latency Indicator Register ..... 1352
Figure 7-291 DPA Status Register ..... 1353
Figure 7-292 DPA Control Register ..... 1353
Figure 7-293 DPA Power Allocation Array ..... 1354
Figure 7-294 Substate Power Allocation Register ( 0 to Substate_Max) ..... 1354
Figure 7-295 TPH Extended Capability Structure ..... 1355
Figure 7-296 TPH Requester Extended Capability Header ..... 1355
Figure 7-297 TPH Requester Capability Register ..... 1355
Figure 7-298 TPH Requester Control Register ..... 1356
Figure 7-299 TPH ST Table ..... 1357
Figure 7-300 TPH ST Table Entry ..... 1358
Figure 7-301 DPC Extended Capability - Non-Flit Mode ..... 1359
Figure 7-302 DPC Extended Capability - Flit Mode ..... 1360
Figure 7-303 DPC Extended Capability Header ..... 1361
Figure 7-304 DPC Capability Register ..... 1361
Figure 7-305 DPC Control Register ..... 1363
Figure 7-306 DPC Status Register ..... 1365
Figure 7-307 DPC Error Source ID Register ..... 1366
Figure 7-308 RP PIO Status Register ..... 1367
Figure 7-309 RP PIO Mask Register ..... 1368
Figure 7-310 RP PIO Severity Register ..... 1369
Figure 7-311 RP PIO SysError Register ..... 1370
Figure 7-312 RP PIO Exception Register ..... 1371
Figure 7-313 RP PIO Header Log Register ..... 1372
Figure 7-314 RP PIO ImpSpec Log Register ..... 1372
Figure 7-315 RP PIO TLP Prefix Log Register ..... 1373
Figure 7-316 PTM Extended Capability Structure ..... 1374
Figure 7-317 PTM Extended Capability Header ..... 1374
Figure 7-318 PTM Capability Register ..... 1375
Figure 7-319 PTM Control Register ..... 1376
Figure 7-320 Readiness Time Reporting Extended Capability ..... 1378
Figure 7-321 Readiness Time Encoding ..... 1378
Figure 7-322 Readiness Time Reporting Extended Capability Header ..... 1379
Figure 7-323 Readiness Time Reporting 1 Register ..... 1379
Figure 7-324 Readiness Time Reporting 2 Register ..... 1380
Figure 7-325 Hierarchy ID Extended Capability ..... 1382
Figure 7-326 Hierarchy ID Extended Capability Header ..... 1382
Figure 7-327 Hierarchy ID Status Register ..... 1383

Figure 7-328 Hierarchy ID Data Register ..... 1384
Figure 7-329 Hierarchy ID GUID 1 Register ..... 1385
Figure 7-330 Hierarchy ID GUID 2 Register ..... 1385
Figure 7-331 Hierarchy ID GUID 3 Register ..... 1386
Figure 7-332 Hierarchy ID GUID 4 Register ..... 1386
Figure 7-333 Hierarchy ID GUID 5 Register ..... 1387
Figure 7-334 VPD Capability Structure ..... 1388
Figure 7-335 VPD Address Register ..... 1389
Figure 7-336 VPD Data Register ..... 1389
Figure 7-337 NPEM Extended Capability ..... 1390
Figure 7-338 NPEM Extended Capability Header ..... 1390
Figure 7-339 NPEM Capability Register ..... 1391
Figure 7-340 NPEM Control Register ..... 1392
Figure 7-341 NPEM Status Register ..... 1394
Figure 7-342 Alternate Protocol Extended Capability ..... 1395
Figure 7-343 Alternate Protocol Extended Capability Header ..... 1395
Figure 7-344 Alternate Protocol Capabilities Register ..... 1396
Figure 7-345 Alternate Protocol Control Register ..... 1396
Figure 7-346 Alternate Protocol Data 1 Register ..... 1397
Figure 7-347 Alternate Protocol Data 2 Register ..... 1398
Figure 7-348 Alternate Protocol Selective Enable Mask Register ..... 1398
Figure 7-349 Conventional PCI Advanced Features Capability (AF) ..... 1399
Figure 7-350 Advanced Features Capability Header ..... 1399
Figure 7-351 AF Capabilities Register ..... 1400
Figure 7-352 Conventional PCI Advanced Features Control Register ..... 1400
Figure 7-353 AF Status Register ..... 1401
Figure 7-354 SFI Extended Capability ..... 1402
Figure 7-355 SFI Extended Capability Header ..... 1402
Figure 7-356 SFI Capability Register ..... 1403
Figure 7-357 SFI Control Register ..... 1403
Figure 7-358 SFI Status Register ..... 1405
Figure 7-359 SFI CAM Address Register ..... 1406
Figure 7-360 SFI CAM Data Register ..... 1406
Figure 7-361 Subsystem ID and Subsystem Vendor ID Capability ..... 1407
Figure 7-362 Subsystem ID and Subsystem Vendor ID Capability Header ..... 1407
Figure 7-363 Subsystem ID and Subsystem Vendor ID Capability Data ..... 1407
Figure 7-364 Data Object Exchange Extended Capability ..... 1408
Figure 7-365 DOE Extended Capability Header ..... 1408
Figure 7-366 DOE Capabilities Register ..... 1409
Figure 7-367 DOE Control Register ..... 1410
Figure 7-368 DOE Status Register ..... 1411
Figure 7-369 DOE Write Data Mailbox Register ..... 1412
Figure 7-370 DOE Read Data Mailbox Register ..... 1412
Figure 7-371 Shadow Functions Extended Capability Structure ..... 1415
Figure 7-372 Shadow Functions Extended Capability Header ..... 1415
Figure 7-373 Shadow Functions Capability Register ..... 1416
Figure 7-374 Shadow Functions Control Register ..... 1416
Figure 7-375 Shadow Functions Instance Register Entry ..... 1417
Figure 7-376 IDE Extended Capability Structure ..... 1418
Figure 7-377 IDE Extended Capability Header ..... 1418
Figure 7-378 IDE Capability Register ..... 1419
Figure 7-379 IDE Control Register ..... 1421

Figure 7-380 Link IDE Stream Control Register ..... 1421
Figure 7-381 Link IDE Stream Status Register ..... 1423
Figure 7-382 Selective IDE Stream Capability Register ..... 1424
Figure 7-383 Selective IDE Stream Control Register ..... 1424
Figure 7-384 Selective IDE Stream Status Register ..... 1427
Figure 7-385 IDE RID Association Register 1 (Offset +00h) ..... 1428
Figure 7-386 IDE RID Association Register 2 (Offset +04h) ..... 1428
Figure 7-387 IDE Address Association Register 1 (Offset +00h) ..... 1429
Figure 7-388 IDE Address Association Register 2 (Offset +04h) ..... 1429
Figure 7-389 IDE Address Association Register 3 (Offset +04h) ..... 1430
Figure 7-390 Null Capability ..... 1430
Figure 7-391 Null Extended Capability ..... 1431
Figure 7-392 Streamlined Virtual Channel Extended Capability Structure ..... 1432
Figure 7-393 Streamlined Virtual Channel Extended Capability Header ..... 1432
Figure 7-394 SVC Port Capability Register 1 ..... 1433
Figure 7-395 SVC Port Control Register ..... 1434
Figure 7-396 SVC Port Status Register ..... 1434
Figure 7-397 SVC Resource Capability Register ..... 1435
Figure 7-398 SVC Resource Control Register ..... 1436
Figure 7-399 SVC Resource Status Register ..... 1437
Figure 7-400 MRBL Extended Capability ..... 1438
Figure 7-401 MRBL Extended Capability Header ..... 1439
Figure 7-402 MRBL Capabilities Register ..... 1439
Figure 7-403 MRBL Locator Register ..... 1440
Figure 8-1 Tx Test Board for Non-Embedded Refclk ..... 1444
Figure 8-2 Tx Test board for Embedded Refclk ..... 1444
Figure 8-3 Single-ended and Differential Levels ..... 1446
Figure 8-4 Tx Equalization FIR Representation for 8.0, 16.0, and 32.0 GT/s ..... 1447
Figure 8-5 Tx Equalization FIR Representation for 64.0 GT/s ..... 1448
Figure 8-6 Definition of Tx Voltage Levels and Equalization Ratios ..... 1449
Figure 8-7 Methodology for measuring Tx equalization coefficients and presets ..... 1451
Figure 8-8 $\quad V_{\text {TX-DIFF-PP }}$ and $V_{\text {TX-DIFF-PP-LOW }}$ Measurement ..... 1452
Figure 8-9 Transmit Equalization Coefficient Space Triangular Matrix Example for 8.0, 16.0, and 32.0 GT/s ..... 1453
Figure 8-10 Transmit Equalization Coefficient Space Triangular Matrix Example for 64.0 GT/s ..... 1454
Figure 8-11 Measuring $V_{\text {TX-EIEOS-FS }}$ and $V_{\text {TX-EIEOS-RS }}$ at 8.0 GT/s ..... 1456
Figure 8-12 Compliance Pattern and Resulting Package Loss Test Waveform ..... 1457
Figure 8-13 Example of Normalized Four Symbol Linear Pulse Responses ..... 1465
Figure 8-14 Example of Un-normalized Four Symbol Linear Pulse Responses ..... 1466
Figure 8-15 2.5 and 5.0 GT/s Transmitter Margining Voltage Levels and Codes ..... 1467
Figure 8-16 First Order CC Behavioral CDR Transfer Functions. ..... 1471
Figure 8-17 $2^{\text {nd }}$ Order Behavioral SRIS CDR Transfer Functions for 2.5 GT/s and 5.0 GT/s ..... 1472
Figure 8-18 Behavioral SRIS CDR Function for 8.0 GT/s, and SRIS and CC CDR for 16.0 and 32.0 GT/s ..... 1473
Figure 8-19 Behavioral SRIS and CC CDR for 64.0 GT/s ..... 1474
Figure 8-20 Relation Between Data Edge PDFs and Recovered Data Clock. ..... 1476
Figure 8-21 Derivation of $T_{\text {TX-UTJ }}$ and $T_{\text {TX-UDJDD. }}$ ..... 1476
Figure 8-22 PWJ Relative to Consecutive Edges 1 UI Apart ..... 1477
Figure 8-23 Definition of $T_{\text {TX-UPW-DJDD }}$ and $T_{\text {TX-UPW-TJ }}$ Data Rate Dependent Transmitter Parameters ..... 1477
Figure 8-24 Tx, Rx Differential Return Loss Mask with 50 Ohm Reference. ..... 1482
Figure 8-25 Tx, Rx Common Mode Return Loss Mask with 50 Ohm Reference. ..... 1483
Figure 8-26 $64.0 \mathrm{GT} / \mathrm{s}$ Tx, Rx Differential Return Loss Mask with 50 Ohm Reference ..... 1484
Figure 8-27 $64.0 \mathrm{GT} / \mathrm{s}$ Tx, Rx Common Mode Return Loss Mask with 50 Ohm Reference. ..... 1485

Figure 8-28 Rx Test board Topology for 16.0 and 32.0 GT/s ..... 1488
Figure 8-29 Example Calibration Channel IL Mask Excluding Rx Package for 8.0 GT/s. ..... 1489
Figure 8-30 Example 16.0 GT/s Calibration Channel ..... 1493
Figure 8-31 Stackup for Example 16.0 GT/s Calibration Channel ..... 1493
Figure 8-32 CEM Connector Drill Hole Pad Stack ..... 1494
Figure 8-33 Pad Stack for SMA Drill Holes ..... 1495
Figure 8-34 Example 32.0 GT/s Calibration Channel ..... 1497
Figure 8-35 Stack-up for Example 32.0 GT/s Calibration Channel ..... 1497
Figure 8-36 Transfer Function for 8.0 GT/s Behavioral CTLE ..... 1499
Figure 8-37 Loss Curves for 8.0 GT/s Behavioral CTLE ..... 1500
Figure 8-38 Loss Curves for 16.0 GT/s Behavioral CTLE ..... 1500
Figure 8-39 Loss Curves for 32.0 GT/s Behavioral CTLE ..... 1502
Figure 8-40 Loss Curves for 64.0 GT/s Behavioral CTLE ..... 1504
Figure 8-41 Variables Definition and Diagram for 1-tap DFE ..... 1505
Figure 8-42 Diagram for 2-tap DFE ..... 1505
Figure 8-43 Layout for Calibrating the Stressed Jitter Eye at 8.0 GT/s ..... 1509
Figure 8-44 Layout for Calibrating the Stressed Jitter Eye at 16.0, 32.0, and 64.0 GT/s ..... 1510
Figure 8-45 Sj Mask for Receivers Operating in IR mode at 8.0 GT/s ..... 1513
Figure 8-46 Sj Mask for Receivers Operating in SRIS mode at 16.0 GT/s ..... 1514
Figure 8-47 Sj Mask for Receivers Operating in CC mode at 16.0 GT/s ..... 1515
Figure 8-48 Sj Mask for Receivers Operating in SRIS mode at 32.0 GT/s ..... 1516
Figure 8-49 Sj Mask for Receivers Operating in CC mode at 32.0 GT/s ..... 1517
Figure 8-50 Sj Mask for Receivers Operating in SRIS mode at 64.0 GT/s ..... 1518
Figure 8-51 Sj Mask for Receivers Operating in CC mode at 64.0 GT/s ..... 1519
Figure 8-52 Sj Masks for Receivers Operating in CC Mode at 8.0 GT/s ..... 1520
Figure 8-53 Layout for Jitter Testing Common Refclk Rx at 16.0 GT/s ..... 1521
Figure 8-54 Layout for Jitter Testing for Independent Refclk Rx at 16.0 GT/s ..... 1521
Figure 8-55 Exit from Idle Voltage and Time Margins ..... 1524
Figure 8-56 Allowed Ranges for Maximum NRZ Timing and Voltage Margin ..... 1525
Figure 8-57 Allowed Ranges for Maximum PAM4 Timing and Voltage Margins ..... 1526
Figure 8-58 Flow Diagram for Channel Tolerancing at 2.5 and 5.0 GT/s ..... 1531
Figure 8-59 Flow Diagram for Channel Tolerancing at 8.0 and 16.0 GT/s ..... 1531
Figure 8-60 Tx/Rx Behavioral Package Models ..... 1532
Figure 8-61 Behavioral Tx and Rx 5-Port Designation for 8.0 and 16.0 GT/s Packages ..... 1533
Figure 8-62 SDD21 Plots for Root and Non-Root Packages for 16.0 GT/s. ..... 1533
Figure 8-63 Insertion Loss for Root Reference Package for 32.0 GT/s ..... 1534
Figure 8-64 Return Loss for Root Reference Package for 32.0 GT/s ..... 1534
Figure 8-65 NEXT for Root Reference Package (Worst-Case) for 32.0 GT/s ..... 1535
Figure 8-66 FEXT for Root Reference Package (Worst-Case) for 32.0 GT/s ..... 1535
Figure 8-67 Insertion Loss for Non-Root Reference Package for 32.0 GT/s ..... 1536
Figure 8-68 Return Loss for Non-Root Reference Package for 32.0 GT/s ..... 1536
Figure 8-69 NEXT for Non-Root Reference Package (Worst-Case) for 32.0 GT/s ..... 1537
Figure 8-70 FEXT for Non-Root Reference Package (Worst-Case) for 32.0 GT/s ..... 1537
Figure 8-71 Insertion Loss for Root Reference Package for 64.0 GT/s ..... 1538
Figure 8-72 Return Loss for Root Reference Package for 64.0 GT/s ..... 1538
Figure 8-73 NEXT for Root Reference Package (Worst Case) for 64.0 GT/s ..... 1539
Figure 8-74 FEXT for Root Reference Package (Worst Case) for 64.0 GT/s ..... 1539
Figure 8-75 Insertion Loss for Non-Root Reference Package for 64.0 GT/s ..... 1540
Figure 8-76 Return Loss for Non-Root Reference Package for 64.0 GT/s ..... 1540
Figure 8-77 NEXT for Non-Root Reference Package (Worst Case) for 64.0 GT/s ..... 1541
Figure 8-78 FEXT for Non-Root Reference Package (Worst Case) for 64.0 GT/s ..... 1541
Figure 8-79 32.0 and 64.0 GT/s Reference Package Port Connections for Pin to Pin Channel Evaluation. ..... 1542

Figure 8-80 Example Derivation of 8.0 GT/s Jitter Parameters for ..... 1544
Figure 8-81 EH, EW Mask ..... 1547
Figure 8-82 Oscilloscope Refclk Test Setup for All Cases Except Jitter at 32.0 and 64.0 GT/s ..... 1551
Figure 8-83 Single-Ended Measurement Points for Absolute Cross Point and Swing. ..... 1553
Figure 8-84 Single-Ended Measurement Points for Delta Cross Point ..... 1553
Figure 8-85 Single-Ended Measurement Points for Rise and Fall Time Matching ..... 1554
Figure 8-86 Differential Measurement Points for Duty Cycle and Period ..... 1554
Figure 8-87 Differential Measurement Points for Rise and Fall Time ..... 1554
Figure 8-88 Differential Measurement Points for Ringback ..... 1555
Figure 8-89 Limits for phase jitter from the Reference with 5000 ppm SSC ..... 1556
Figure 8-90 5 MHz PLL Transfer Function Example ..... 1558
Figure 8-91 Common Refclk Rx Architecture for all Data Rates Except 32.0 and 64.0 GT/s ..... 1559
Figure 8-92 Common Refclk PLL and CDR Characteristics for 2.5 GT/s ..... 1560
Figure 8-93 Common Refclk PLL and CDR Characteristics for 5.0 GT/s ..... 1560
Figure 8-94 Common Refclk PLL and CDR Characteristics for 8.0 and 16.0 GT/s ..... 1561
Figure 8-95 Common Refclk PLL and CDR Characteristics for 32.0 GT/s ..... 1561
Figure 8-96 Common Refclk PLL and CDR Characteristics for 64.0 GT/s ..... 1561
Figure 9-1 Generic Platform Configuration ..... 1565
Figure 9-2 Generic Platform Configuration with a VI and Multiple SI ..... 1566
Figure 9-3 Generic Platform Configuration with SR-IOV and IOV Enablers ..... 1568
Figure 9-4 Example Multi-Function Device ..... 1570
Figure 9-5 Example SR-IOV Single PF Capable Device ..... 1571
Figure 9-6 Example SR-IOV Multi-PF Capable Device ..... 1573
Figure 9-7 Example SR-IOV Device with Multiple Bus Numbers ..... 1575
Figure 9-8 Example SR-IOV Device with a Mixture of Function Types ..... 1576
Figure 9-9 BAR Space Example for Single BAR Device ..... 1578
Figure 9-10 SR-IOV Extended Capability ..... 1583
Figure 9-11 SR-IOV Extended Capability Header ..... 1583
Figure 9-12 SR-IOV Capabilities Register ..... 1584
Figure 9-13 SR-IOV Control Register ..... 1587
Figure 9-14 SR-IOV Status ..... 1590
Figure 10-1 Example Illustrating a Platform with TA, ATPT, and ATC Elements ..... 1602
Figure 10-2 Example ATS Translation Request/Completion Exchange ..... 1602
Figure 10-3 Example Multi-Function Device with ATC per Function ..... 1604
Figure 10-4 Invalidation Protocol with a Single Invalidate Request and Completion ..... 1605
Figure 10-5 Single Invalidate Request with Multiple Invalidate Completions. ..... 1606
Figure 10-6 Memory Request Header with 64-bit Address Highlighting AT field ..... 1608
Figure 10-7 Memory Request Header with 32-bit Address Highlighting AT field ..... 1609
Figure 10-8 Memory Request Header with 32-bit Address Highlighting AT field - Flit Mode ..... 1609
Figure 10-9 Memory Request Header with 32-bit Address Highlighting AT field - Flit Mode ..... 1609
Figure 10-10 Translation Request with 64-bit Address - Non-Flit Mode ..... 1610
Figure 10-11 Translation Request with 32-bit Address - Non-Flit Mode ..... 1611
Figure 10-12 Translation Request with 64-bit Address - Flit Mode ..... 1611
Figure 10-13 Translation Request with 32-bit Address - Flit Mode ..... 1611
Figure 10-14 Translation Completion Data Entry ..... 1615
Figure 10-15 Example Translation Completion with 1 TLP ..... 1622
Figure 10-16 Example Translation Completion with 2 TLPs. ..... 1623
Figure 10-17 ATS Memory Attributes Example ..... 1625
Figure 10-18 Invalidate Request Message - Non-Flit Mode ..... 1627
Figure 10-19 Invalidate Request Message - Flit Mode. ..... 1627
Figure 10-20 Invalidate Request Message Body ..... 1628
Figure 10-21 Invalidate Completion Message Format - Non-Flit Mode ..... 1629

Figure 10-22 Invalidate Completion Message - Flit Mode ..... 1630
Figure 10-23 Page Request Message - Non-Flit Mode ..... 1637
Figure 10-24 Page Request Message - Flit Mode ..... 1637
Figure 10-25 Stop Marker Message - Non-Flit Mode ..... 1640
Figure 10-26 Stop Marker Message - Flit Mode ..... 1642
Figure 10-27 PRG Response Message - Non-Flit Mode ..... 1643
Figure 10-28 PRG Response Message - Flit Mode ..... 1644
Figure 10-29 ATS Extended Capability Structure ..... 1644
Figure 10-30 ATS Capsability Register (Offset 04h) ..... 1645
Figure 10-31 ATS Control Register ..... 1645
Figure 10-32 Page Request Extended Capability Structure ..... 1647
Figure 10-33 Page Request Extended Capability Header ..... 1647
Figure 10-34 Page Request Control Register ..... 1648
Figure 10-35 Page Request Status Register ..... 1648
Figure 11-1 Conceptual View with Example Host and Device and Logical Communication Paths ..... 1652
Figure 11-2 TDISP Host/Device Reference Architecture ..... 1655
Figure 11-3 Identification of Requests ..... 1658
Figure 11-4 TDI Identifier - INTERFACE_ID ..... 1659
Figure 11-5 TDISP State Machine ..... 1659
Figure 11-6 TDISP Request/Response Encapsulation ..... 1664
Figure 11-7 Example Flow Where DSM is Unable to Return Full Length Report ..... 1678
Figure 12-1 Example PESTI Application ..... 1707
Figure 12-2 UART Data Framing. ..... 1707
Figure 12-3 PESTI Circuit Diagram ..... 1708
Figure 12-4 PESTI Broadcast Command ..... 1712
Figure 12-5 PESTI Protocol Phases. ..... 1714
Figure 12-6 PESTI Discovery Command and Response Format. ..... 1716
Figure 12-7 Single Byte PESTI Virtual Wire Exchange ..... 1718
Figure 12-8 Multi-byte PESTI Virtual Wire Exchange ..... 1718
Figure 12-9 PESTI Fan-out Methods ..... 1722
Figure 12-10 PESTI Mux Switch Control Format ..... 1723
Figure 12-11 [CEM] form factor example circuit for repurposing legacy JTAG to USB 2.0 mode ..... 1725
Figure 12-12 Example of 2-wire, 8-bit addressing for a card carrier with N end form factors in SMBus mode ..... 1728
Figure 12-13 Example of 2-wire Hub Use ..... 1730
Figure 12-14 SMBus to I3C Transition Flow. ..... 1733
Figure 12-15 Component Timing Diagram for Transition to I3C Signaling Voltage ..... 1735
Figure 12-16 SMBus/I2C-based FRU Information Device Writes with Two-Byte Addressing ..... 1738
Figure 12-17 FRU Information Device Reads with Two-Byte Addressing ..... 1738
Figure 12-18 Example Tiers Involving Sidebands ..... 1745
Figure A-1 An Example Showing Endpoint-to-Root-Complex and Peer-to-Peer Communication Models ..... 1747
Figure A-2 Two Basic Bandwidth Resourcing Problems: Over-Subscription and Congestion. ..... 1748
Figure A-3 A Simplified Example Illustrating PCI Express Isochronous Parameters. ..... 1752
Figure C-1 Scrambling Spectrum at $2.5 \mathrm{GT} / \mathrm{s}$ for Data Value of 0 ..... 1772
Figure E-1 Reference Topology for IDO Use ..... 1779
Figure G-1 Device and Processor Connected Using a PMUX Link ..... 1787
Figure G-2 PMUX Link ..... 1787
Figure G-3 PMUX Packet Flow Through the Layers ..... 1788
Figure G-4 PMUX Packet ..... 1792
Figure G-5 TLP and PMUX Packet Framing (8b/10b Encoding) ..... 1793
Figure G-6 TLP and PMUX Packet Framing (128b/130b Encoding) ..... 1795
Figure G-7 PMUX Extended Capability ..... 1798

Figure G-8 PMUX Extended Capability Header ..... 1798
Figure G-9 PMUX Capability Register ..... 1799
Figure G-10 PMUX Control Register ..... 1800
Figure G-11 PMUX Status Register ..... 1801
Figure G-12 PMUX Protocol Array Entry ..... 1802
Figure L-1 Example Memory Write TLP (NFM) ..... 2127
Figure L-2 Example NFM Memory Write IDE TLP ..... 2128
Figure L-3 Example Memory Write TLP (FM) ..... 2129
Figure L-4 Example Memory Write IDE TLP (FM) ..... 2130
Figure L-5 Example Memory Write TLP with Partial Header Encryption (NFM) ..... 2131
Figure L-6 Example NFM Memory Write IDE TLP with Partial Header Encryption ..... 2132
Figure L-7 Example Memory Write TLP with Partial Header Encryption (FM) ..... 2133
Figure L-8 Example Memory Write IDE TLP with Partial Header Encryption (FM) ..... 2134

Page 54

# List of Equations 

Equation 2-1 CREDITS_CONSUMED ..... 291
Equation 2-2 SHARED_CREDITS_CONSUMED ..... 291
Equation 2-3 SUM_SHARED_CREDITS_CONSUMED ..... 292
Equation 2-4 TLP SHARED_CREDITS_CONSUMED_CURRENTLY ..... 292
Equation 2-5 FC SHARED_CREDITS_CONSUMED_CURRENTLY ..... 292
Equation 2-6 SUM_SHARED_CREDIT_LIMIT ..... 293
Equation 2-7 SHARED_CUMULATIVE_CREDITS_REQUIRED ..... 294
Equation 2-8 Shared Transmitter Gate non-[Merged] ..... 294
Equation 2-9 Shared Transmitter Gate [Merged] ..... 294
Equation 2-10 Shared Transmitter Usage Limit Gate non-[Merged] ..... 295
Equation 2-11 Shared Transmitter Usage Limit Gate [Merged] ..... 295
Equation 2-12 CUMULATIVE_CREDITS_REQUIRED ..... 295
Equation 2-13 Transmitter Gate ..... 295
Equation 2-14 CREDITS_ALLOCATED ..... 296
Equation 2-15 CREDITS_RECEIVED ..... 297
Equation 2-16 Receiver Overflow Error Check Non-Flit / Dedicated ..... 298
Equation 2-17 Receiver Overflow Error Check Non-Posted / Not [Merged] ..... 298
Equation 2-18 Receiver Overflow Error Check [Merged] ..... 298
Equation 3-1 Tx SEQ Stall ..... 342
Equation 3-2 Tx SEQ Update ..... 343
Equation 4-1 Parity bytes ..... 452
Equation 4-2 Check bytes ..... 452
Equation 4-3 Retimer Latency with SRIS ..... 669
Equation 6-1 MC_Overlay Transform rules ..... 838
Equation 6-2 PTM Master Time ..... 864
Equation 7-1 MSI-X Starting Address ..... 1127
Equation 7-2 MSI-X PBA QWORD Access ..... 1127
Equation 7-3 MSI-X PBA DWORD Access ..... 1127
Equation 7-4 Egress Control Vector Access ..... 1195
Equation 8-1 VDIFFp-p ..... 1445
Equation 8-2 VTX-AC-CM-PP ..... 1445
Equation 8-3 Y ..... 1458
Equation 8-4 $\mathrm{x}_{\mathrm{f}}$ ..... 1459
Equation 8-5 X ..... 1459
Equation 8-6 P ..... 1459
Equation 8-7 E ..... 1459
Equation 8-8 y ..... 1460
Equation 8-9 XNP ..... 1460
Equation 8-10 P E EO ..... 1460
Equation 8-11 e ..... 1461
Equation 8-12 $\sigma_{L, i}$ ..... 1461
Equation 8-13 $\mu_{\mathrm{L}, \mathrm{i}}$ ..... 1461
Equation 8-14 $\sigma_{\mathrm{L}}$ ..... 1462
Equation 8-15 $\sigma_{\mathrm{n}}$ ..... 1462
Equation 8-16 SNDR ..... 1462
Equation 8-17 RLM ..... 1463

Equation 8-18 $\mathrm{W}_{\text {symo_3 }}$ ..... 1464
Equation 8-19 $\mathrm{X}_{\text {sym }}$ ..... 1464
Equation 8-20 $\mathrm{P}_{\text {sym }}$ ..... 1464
Equation 8-21 $\mathrm{P}_{\text {sym_un_normalized }}$ ..... 1466
Equation 8-22 Behavioral SRIS CDR at $8.0 \mathrm{GT} / \mathrm{s}$ and SRIS and CC Behavioral CDR at $16.0 \mathrm{GT} / \mathrm{s}$ ..... 1473
Equation 8-23 SRIS Behavioral CDR Parameters at $8.0 \mathrm{GT} / \mathrm{s}$ ..... 1473
Equation 8-24 SRIS and CC Behavioral CDR Parameters at $16.0 \mathrm{GT} / \mathrm{s}$ ..... 1474
Equation 8-25 SRIS and CC Behavioral CDR Parameters at 32.0 and $64.0 \mathrm{GT} / \mathrm{s}$ ..... 1475
Equation 8-26 Behavioral CTLE at $32.0 \mathrm{GT} / \mathrm{s}$ ..... 1501
Equation 8-27 Behavioral CTLE at $64.0 \mathrm{GT} / \mathrm{s}$ ..... 1503
Equation 8-28 Relationship between $2^{\text {nd }}$ order PLL natural frequency and 3 dB point ..... 1557
Equation A-1 Isochronous Bandwidth ..... 1748
Equation A-2 Isochronous Payload Size ..... 1749
Equation A-3 $\mathrm{N}_{\text {max }}$ ..... 1749
Equation A-4 BW $_{\text {max }}$ ..... 1750
Equation A-5 BW $_{\text {granularity }}$ ..... 1750
Equation A-6 $\mathrm{N}_{\text {link }}$ ..... 1750
Equation A-7 Max Isochronous Transaction Latency ..... 1751
Equation H-1 Max UpdateFC Latency ..... 1805
Equation H-2 Max Ack Latency ..... 1808

# List of Tables 

Table 1-1 PCIe Signaling Characteristics ..... 135
Table 2-1 Transaction Types for Different Address Spaces ..... 148
Table 2-2 Fmt[2:0] Field Values ..... 152
Table 2-3 Fmt[2:0] and Type[4:0] Field Encodings ..... 152
Table 2-4 Length[9:0] Field Encoding ..... 154
Table 2-5 Flit Mode TLP Header Type Encodings ..... 156
Table 2-6 OHC-A Included Fields for OHC-A1 through OHC-A5 (see through ) ..... 166
Table 2-7 Address Field Mapping ..... 183
Table 2-8 Header Field Locations for non-ARI ID Routing - Non-Flit Mode ..... 185
Table 2-9 Header Field Locations for ARI ID Routing. ..... 185
Table 2-10 Byte Enables Location and Correspondence ..... 190
Table 2-11 Tag Enables, Sizes, and Permitted Ranges for non-UIO Transactions ..... 195
Table 2-12 Ordering Attributes ..... 200
Table 2-13 Cache Coherency Management Attribute ..... 201
Table 2-14 Definition of TC Field Encodings ..... 201
Table 2-15 Length Field Values for AtomicOp Requests ..... 202
Table 2-16 TPH TLP Prefix Bit Mapping ..... 205
Table 2-17 Location of PH[1:0] in TLP Header ..... 207
Table 2-18 Processing Hint Encoding ..... 207
Table 2-19 Location of ST[7:0] in TLP Headers ..... 208
Table 2-20 Message Routing. ..... 212
Table 2-21 INTx Mechanism Messages ..... 213
Table 2-22 Bridge Mapping for INTx Virtual Wires ..... 215
Table 2-23 Power Management Messages ..... 216
Table 2-24 Error Signaling Messages ..... 217
Table 2-25 ERR_COR Subclass (ECS) Field Encodings ..... 218
Table 2-26 Unlock Message ..... 219
Table 2-27 Set_Slot_Power_Limit Message ..... 219
Table 2-28 Vendor-Defined Messages ..... 220
Table 2-29 DRS Message ..... 223
Table 2-30 FRS Message ..... 225
Table 2-31 Hierarchy ID Message ..... 226
Table 2-32 Ignored Messages ..... 228
Table 2-33 LTR Message ..... 228
Table 2-34 OBFF Message ..... 230
Table 2-35 Precision Time Measurement Messages ..... 231
Table 2-36 IDE Messages ..... 234
Table 2-37 Completion Status Field Values ..... 238
Table 2-38 Local TLP Prefix Types ..... 243
Table 2-39 End-End TLP Prefix Types ..... 244
Table 2-40 Calculating Byte Count from Length and Byte Enables ..... 260
Table 2-41 Calculating Lower Address from First DW BE ..... 261
Table 2-42 Ordering Rules Summary ..... 266
Table 2-43 UIO TLP Ordering Rules ..... 271
Table 2-44 UIO Acceptance Dependency Rules - Downstream Ports ..... 272
Table 2-45 UIO Acceptance Dependency Rules - Upstream Ports ..... 272
Table 2-46 Streamlined VC (SVC) TC/VC Default Assignments ..... 275

Table 2-47 TC to VC Mapping Example ..... 279
Table 2-48 Flow Control Credit Types ..... 283
Table 2-49 TLP Flow Control Credit Consumption ..... 283
Table 2-50 Minimum Initial Flow Control Advertisements ..... 285
Table 2-51 [Field Size] Values ..... 288
Table 2-52 Maximum UpdateFC Transmission Latency Guidelines for 2.5 GT/s (Symbol Times) ..... 302
Table 2-53 Maximum UpdateFC Transmission Latency Guidelines for 5.0 GT/s (Symbol Times) ..... 302
Table 2-54 Maximum UpdateFC Transmission Latency Guidelines for 8.0 GT/s and Higher Data Rates (Symbol Times) ..... 303
Table 2-55 Mapping of Bits into ECRC Field ..... 305
Table 3-1 Data Link Feature Supported Bit Definition ..... 321
Table 3-2 InitFC1 / InitFC2 Options - Non-Flit Mode ..... 324
Table 3-3 InitFC1 / InitFC2 Options - Flit Mode ..... 324
Table 3-4 Scaled Flow Control Scaling Factors ..... 330
Table 3-5 DLLP Type Encodings ..... 332
Table 3-6 HdrScale and DataScale Encodings ..... 334
Table 3-7 Mapping of Bits into CRC Field ..... 338
Table 3-8 Mapping of Bits into LCRC Field ..... 343
Table 3-10 Maximum Ack Latency Limits for 2.5 GT/s (Symbol Times) (-0\%/+0\%) ..... 354
Table 3-11 Maximum Ack Latency Limits for 5.0 GT/s (Symbol Times) (-0\%/+0\%) ..... 354
Table 3-12 Maximum Ack Latency Limits for 8.0 GT/s and higher data rates (Symbol Times) ..... 354
Table 4-1 Valid Encoding and Data Stream Mode Combinations ..... 358
Table 4-2 Valid Encoding for Ordered Sets ..... 358
Table 4-3 Special Symbols in 8b/10b Encoding ..... 361
Table 4-4 Framing Token Encoding ..... 371
Table 4-6 Effect of $+/-1$ voltage level error on the wire for various PAM4 voltage levels - at most one bit flips with an error on a UI ..... 393
Table 4-7 Truth Table for Precoding on the Transmit side ..... 393
Table 4-8 Truth Table for Precoding on the Receive side ..... 394
Table 4-9 Example of precoding with an error in the channel and DFE error propagation at the Receiver ..... 395
Table 4-10 Flit Layout in a x16 Link ..... 401
Table 4-11 Flit interleaving in a x8 Link ..... 402
Table 4-12 Flit interleaving in a x4 Link ..... 403
Table 4-13 Flit interleaving in a x2 Link ..... 403
Table 4-14 Flit arrangement in a x1 Link. ..... 404
Table 4-15 Example TLP Placement in Flit Mode on a x16 Link ..... 408
Table 4-16 Flit Types ..... 410
Table 4-17 DLP Bytes in the Flit ..... 410
Table 4-18 Optimized_Update_FC ..... 411
Table 4-19 Flit_Marker ..... 412
Table 4-20 NOP Flit Types ..... 413
Table 4-21 NOP Flit Common Header Fields ..... 413
Table 4-22 NOP.Debug Flit Debug Chunk Fields ..... 439
Table 4-23 PCI-SIG Defined Debug Chunk Opcode Values ..... 442
Table 4-24 FC Information Tracked by Transmitter Encodings. ..... 445
Table 4-25 FC Information Tracked by Receiver Encodings ..... 447
Table 4-26 Flit Mode Transmitter Retry Flags and Counters Fields ..... 448
Table 4-27 Flit Mode Receiver Retry Flags and Counters Fields ..... 449
Table 4-28 Buffer Occupancy Encodings ..... 450
Table 4-30 Ordered Set insertion interval once Data Stream starts in terms of number of Flits. ..... 459
Table 4-31 Equalization Requirements Under Different Conditions ..... 464
Table 4-32 Transmitter Preset Encoding. ..... 472

Table 4-33 Receiver Preset Hint Encoding for 8.0 GT/s ..... 473
Table 4-34 TS1 Ordered Set in 8b/10b and 128b/130b Encoding ..... 477
Table 4-35 TS2 Ordered Set in 8b/10b and 128b/130b Encoding ..... 483
Table 4-36 Modified TS1/TS2 Ordered Set (8b/10b encoding) ..... 486
Table 4-37 TS1/TS2 Ordered Set with 1b/1b Encoding ..... 488
Table 4-38 TS0 Ordered Set ..... 491
Table 4-39 Modified TS Information 1 field in Modified TS1/TS2 Ordered Sets if Modified TS Usage = 010b (Alternate Protocol) ..... 496
Table 4-40 Electrical Idle Ordered Set (EIOS) for 2.5 GT/s and 5.0 GT/s Data Rates ..... 498
Table 4-41 Electrical Idle Ordered Set (EIOS) for 128b/130b Encoding ..... 498
Table 4-42 Electrical Idle Ordered Set (EIOS) for 1b/1b Encoding ..... 498
Table 4-43 Electrical Idle Exit Ordered Set (EIEOS) for 5.0 GT/s Data Rate ..... 498
Table 4-44 Electrical Idle Exit Ordered Set (EIEOS) for 8.0 GT/s Data Rate ..... 499
Table 4-45 Electrical Idle Exit Ordered Set (EIEOS) for 16.0 GT/s Data Rate ..... 499
Table 4-46 Electrical Idle Exit Ordered Set (EIEOS) for 32.0 GT/s Data Rate ..... 499
Table 4-47 Electrical Idle Exit Ordered Set (EIEOS) for 64.0 GT/s Data Rate ..... 499
Table 4-48 Electrical Idle Inference Conditions ..... 503
Table 4-49 FTS for 8.0 GT/s and Above Data Rates ..... 505
Table 4-50 SDS Ordered Set (for 8.0 GT/s and 16.0 GT/s Data Rate) ..... 506
Table 4-51 SDS Ordered Set (for 32.0 GT/s) ..... 506
Table 4-52 SDS Ordered Set (for 64.0 GT/s) ..... 506
Table 4-53 Summary of L0p Transmitter/Receiver Behavior ..... 517
Table 4-54 Link Management DLLP ..... 517
Table 4-58 Link Status Mapped to the LTSSM ..... 522
Table 4-59 Compliance Pattern Settings ..... 529
Table 4-61 Use of TS0 or TS1 Ordered Sets in different phases ..... 560
Table 4-62 Standard SKP Ordered Set with 128b/130b Encoding ..... 605
Table 4-63 Control SKP Ordered Set with 128b/130b Encoding ..... 606
Table 4-64 Control SKP Ordered Set with 1b/1b Encoding ..... 608
Table 4-65 PHY Payload for Control SKP Ordered Set with 1b/1b Encoding ..... 611
Table 4-69 Illustration of Modified Compliance Pattern ..... 617
Table 4-72 Margin Command Related Fields in the Control SKP Ordered Set ..... 624
Table 4-73 Margin Commands and Corresponding Responses ..... 627
Table 4-74 Maximum Retimer Exit Latency ..... 646
Table 4-75 Inferring Electrical Idle ..... 648
Table 4-76 Retimer Latency Limit not SRIS (Symbol times) ..... 667
Table 4-77 Retimer Latency Limit SRIS (Symbol times) ..... 668
Table 5-1 Summary of PCI Express Link Power Management States ..... 679
Table 5-2 Relation Between Power Management States of Link and Components ..... 685
Table 5-3 Encoding of the ASPM Support Field ..... 708
Table 5-4 Description of the Slot Clock Configuration Bit ..... 708
Table 5-5 Description of the Common Clock Configuration Bit ..... 708
Table 5-6 Encoding of the L0s Exit Latency Field ..... 709
Table 5-7 Encoding of the L1 Exit Latency Field ..... 709
Table 5-8 Encoding of the Endpoint L0s Acceptable Latency Field ..... 710
Table 5-9 Encoding of the Endpoint L1 Acceptable Latency Field ..... 710
Table 5-10 Encoding of the ASPM Control Field ..... 710
Table 5-11 L1.2 Timing Parameters. ..... 723
Table 5-12 Aux Power Source and Availability ..... 724
Table 5-13 Power Management System Messages and DLLPs ..... 725
Table 5-14 PCI Function State Transition Delays ..... 726
Table 6-1 Error Messages. ..... 744

Table 6-2 General PCI Express Error List ..... 758
Table 6-3 Physical Layer Error List ..... 758
Table 6-4 Data Link Layer Error List ..... 758
Table 6-5 Transaction Layer Error List ..... 759
Table 6-6 Multi-Function Arbitration Error Model Example ..... 782
Table 6-7 Elements of Hot-Plug ..... 796
Table 6-8 Attention Indicator States ..... 797
Table 6-9 Power Indicator States ..... 798
Table 6-10 Power Budgeting Deployments ..... 811
Table 6-11 ACS P2P Request Redirect and ACS P2P Egress Control Interactions ..... 826
Table 6-12 ECRC Rules for MC_Overlay. ..... 838
Table 6-13 Processing Hint Mapping ..... 847
Table 6-14 ST Modes of Operation ..... 847
Table 6-15 PASID TLP Prefix ..... 859
Table 6-16 Emergency Power Reduction Supported Values. ..... 879
Table 6-17 System GUID Authority ID Encoding ..... 883
Table 6-19 Small Resource Data Type Tag Bit Definitions. ..... 898
Table 6-20 Large Resource Data Type Tag Bit Definitions ..... 898
Table 6-21 Resource Data Type Flags for a Typical VPD ..... 898
Table 6-22 Example of Add-in Serial Card Number ..... 899
Table 6-23 VPD Large and Small Resource Data Tags ..... 900
Table 6-24 VPD Read-Only Fields ..... 900
Table 6-25 VPD Read/Write Fields ..... 902
Table 6-26 VPD Example ..... 902
Table 6-27 NPEM States ..... 907
Table 6-28 DOE Data Object Header 1 ..... 914
Table 6-29 DOE Data Object Header 2 ..... 915
Table 6-30 DOE Discovery Request Data Object Contents (3rd DW) ..... 915
Table 6-31 DOE Discovery Response Data Object Contents (3rd DW) ..... 916
Table 6-32 DOE Discovery Response Data Object Contents (4th DW) ..... 916
Table 6-33 PCI-SIG Defined Data Object Types (Vendor ID = 0001h) ..... 917
Table 6-34 DOE Async Message Data Object Contents (1 DW) ..... 918
Table 6-35 TLP Types for Selective IDE Streams ..... 966
Table 6-36 IDE Revised Ordering Rules for Flow-Through non-UIO IDE Streams - Per Stream ..... 977
Table 6-37 IDE Revised Ordering Rules for Flow-Through UIO IDE Streams - Per Stream ..... 977
Table 6-38 MCAP Array Register 1 ..... 984
Table 6-39 MCAP Array Register 2 ..... 985
Table 6-40 MCAP Header Register 1 ..... 986
Table 6-41 MCAP Header Register 2 ..... 986
Table 6-42 MCAP Header Register 3 ..... 986
Table 6-43 MCAP Header Register 4 ..... 987
Table 6-44 PCI-SIG Defined MCAP Identifiers (MCAP Vendor ID = 0001h) ..... 987
Table 6-45 MMB Capabilities Register ..... 990
Table 6-46 MMB Control Register ..... 991
Table 6-47 MMB Command Register ..... 992
Table 6-48 MMB Status Register ..... 993
Table 6-49 MMB PCI-SIG Defined Command Return Codes (Vendor ID = 0001h) ..... 994
Table 6-50 MMPT Capabilities Register ..... 996
Table 6-51 MMPT Control Register ..... 997
Table 6-52 MMPT Receive Message Notification Register ..... 997
Table 6-53 MDVS Register Block Header Register 1 ..... 998
Table 6-54 MDVS Register Block Header Register 2 ..... 999

Table 6-55 MDVS Register Block Header Register 3 ..... 999
Table 6-56 PCI-SIG Defined MMB Command Opcodes (Vendor ID = 0001h) ..... 1000
Table 6-57 MMPT Send Message Input Payload ..... 1001
Table 6-58 MMPT Send Message Output Payload ..... 1002
Table 6-59 MMPT Receive Message Input Payload ..... 1003
Table 6-60 MMPT Receive Message Output Payload ..... 1003
Table 7-1 Enhanced Configuration Address Mapping ..... 1011
Table 7-2 Register and Register Bit-Field Types ..... 1017
Table 7-3 Special Field Types to Indicate VF Attributes ..... 1019
Table 7-4 Command Register ..... 1022
Table 7-5 Status Register ..... 1024
Table 7-6 Class Code Register ..... 1027
Table 7-7 Header Type Register ..... 1028
Table 7-8 BIST Register ..... 1029
Table 7-9 Memory Base Address Register Bits 2:1 Encoding ..... 1033
Table 7-10 Expansion ROM Base Address Register ..... 1037
Table 7-11 I/O Addressing Capability ..... 1042
Table 7-12 Secondary Status Register ..... 1043
Table 7-13 Bridge Control Register ..... 1046
Table 7-14 Power Management Capabilities Register ..... 1049
Table 7-15 Power Management Control/Status Register ..... 1051
Table 7-16 Power Management Data Register ..... 1053
Table 7-17 Power Consumption/Dissipation Reporting ..... 1053
Table 7-18 PCI Express Capability List Register ..... 1056
Table 7-19 PCI Express Capabilities Register ..... 1056
Table 7-20 Device Capabilities Register ..... 1058
Table 7-21 Device Control Register ..... 1062
Table 7-22 Device Status Register ..... 1069
Table 7-23 Link Capabilities Register ..... 1071
Table 7-24 Link Control Register ..... 1075
Table 7-26 Link Status Register ..... 1082
Table 7-27 Slot Capabilities Register ..... 1084
Table 7-28 Slot Control Register ..... 1087
Table 7-29 Slot Status Register ..... 1090
Table 7-30 Root Control Register ..... 1092
Table 7-31 Root Capabilities Register ..... 1093
Table 7-32 Root Status Register ..... 1094
Table 7-33 Device Capabilities 2 Register ..... 1095
Table 7-34 Device Control 2 Register ..... 1100
Table 7-35 Link Capabilities 2 Register ..... 1104
Table 7-36 Link Control 2 Register ..... 1107
Table 7-37 Link Status 2 Register ..... 1110
Table 7-38 Slot Capabilities 2 Register ..... 1114
Table 7-39 PCI Express Extended Capability Header ..... 1115
Table 7-40 MSI Capability Header ..... 1118
Table 7-41 Message Control Register for MSI ..... 1119
Table 7-42 Message Address Register for MSI ..... 1120
Table 7-43 Message Upper Address Register for MSI ..... 1121
Table 7-44 Message Data Register for MSI ..... 1121
Table 7-45 Extended Message Data Register for MSI ..... 1122
Table 7-46 Mask Bits Register for MSI ..... 1123
Table 7-47 Pending Bits Register for MSI ..... 1123

Table 7-48 MSI-X Capability Header ..... 1128
Table 7-49 Message Control Register for MSI-X ..... 1128
Table 7-50 Table Offset/Table BIR Register for MSI-X ..... 1129
Table 7-51 PBA Offset/PBA BIR Register for MSI-X ..... 1130
Table 7-52 Message Address Register for MSI-X Table Entries ..... 1130
Table 7-53 Message Upper Address Register for MSI-X Table Entries ..... 1131
Table 7-54 Message Data Register for MSI-X Table Entries ..... 1131
Table 7-55 Vector Control Register for MSI-X Table Entries ..... 1132
Table 7-56 Pending Bits Register for MSI-X PBA Entries ..... 1133
Table 7-57 Secondary PCI Express Extended Capability Header ..... 1135
Table 7-58 Link Control 3 Register ..... 1135
Table 7-59 Lane Error Status Register ..... 1137
Table 7-60 Lane Equalization Control Register Entry ..... 1137
Table 7-63 Data Link Feature Extended Capability Header ..... 1140
Table 7-64 Data Link Feature Capabilities Register ..... 1141
Table 7-65 Data Link Feature Status Register ..... 1142
Table 7-66 Physical Layer 16.0 GT/s Extended Capability Header ..... 1145
Table 7-67 16.0 GT/s Capabilities Register ..... 1145
Table 7-68 16.0 GT/s Control Register ..... 1146
Table 7-69 16.0 GT/s Status Register ..... 1146
Table 7-70 16.0 GT/s Local Data Parity Mismatch Status Register ..... 1147
Table 7-71 16.0 GT/s First Retimer Data Parity Mismatch Status Register ..... 1148
Table 7-72 16.0 GT/s Second Retimer Data Parity Mismatch Status Register ..... 1149
Table 7-73 16.0 GT/s Lane Equalization Control Register Entry ..... 1149
Table 7-75 Physical Layer 32.0 GT/s Extended Capability Header ..... 1152
Table 7-76 32.0 GT/s Capabilities Register ..... 1152
Table 7-77 32.0 GT/s Control Register ..... 1153
Table 7-78 32.0 GT/s Status Register ..... 1154
Table 7-79 Received Modified TS Data 1 Register ..... 1156
Table 7-80 Received Modified TS Data 2 Register ..... 1157
Table 7-81 Transmitted Modified TS Data 1 Register ..... 1158
Table 7-82 Transmitted Modified TS Data 2 Register ..... 1159
Table 7-83 32.0 GT/s Lane Equalization Control Register Entry ..... 1160
Table 7-85 Physical Layer 64.0 GT/s Extended Capability Header ..... 1162
Table 7-86 64.0 GT/s Capabilities Register ..... 1162
Table 7-87 64.0 GT/s Control Register ..... 1163
Table 7-88 64.0 GT/s Status Register ..... 1163
Table 7-89 64.0 GT/s Lane Equalization Control Register Entry ..... 1165
Table 7-91 Flit Logging Extended Capability Header ..... 1167
Table 7-92 Flit Error Log Interpretation ..... 1167
Table 7-93 Flit Error Log 1 Register ..... 1168
Table 7-94 Flit Error Log 2 Register ..... 1170
Table 7-95 Flit Error Counter Control Register ..... 1171
Table 7-96 Flit Error Counter Status Register ..... 1172
Table 7-97 FBER Measurement Control Register ..... 1173
Table 7-98 FBER Measurement Status 1 Register ..... 1174
Table 7-99 FBER Measurement Status 2 Register ..... 1174
Table 7-100 FBER Measurement Status 3 Register ..... 1175
Table 7-101 FBER Measurement Status 4 Register ..... 1175
Table 7-102 FBER Measurement Status 5 Register ..... 1176
Table 7-103 FBER Measurement Status 6 Register ..... 1176
Table 7-104 FBER Measurement Status 7 Register ..... 1177

Table 7-105
Table 7-106
Table 7-107
Table 7-108
Table 7-109
Table 7-110
Table 7-111
Table 7-112
Table 7-113
Table 7-114
Table 7-115
Table 7-116
Table 7-117
Table 7-118
Table 7-119
Table 7-120
Table 7-121
Table 7-122
Table 7-123
Table 7-124
Table 7-125
Table 7-126
Table 7-127
Table 7-128
Table 7-129
Table 7-130
Table 7-131
Table 7-132
Table 7-133
Table 7-134
Table 7-135
Table 7-136
Table 7-137
Table 7-138
Table 7-139
Table 7-140
Table 7-141
Table 7-142
Table 7-143
Table 7-144
Table 7-145
Table 7-146
Table 7-147
Table 7-148
Table 7-149
Table 7-151
Table 7-152
Table 7-153
Table 7-154
Table 7-155
Table 7-156

FBER Measurement Status 8 Register ..... 1177
FBER Measurement Status 9 Register ..... 1177
FBER Measurement Status 10 Register ..... 1178
Device 3 Extended Capability Header ..... 1179
Device Capabilities 3 Register ..... 1179
Device Control 3 Register ..... 1182
Device Status 3 Register ..... 1184
Lane Margining at the Receiver Extended Capability Header ..... 1187
Margining Port Capabilities Register ..... 1187
Margining Port Status Register ..... 1188
Lane N: Margining Control Register Entry ..... 1189
Lane N: Margining Lane Status Register Entry ..... 1190
ACS Extended Capability Header ..... 1191
ACS Capability Register ..... 1192
ACS Control Register ..... 1193
Egress Control Vector Register ..... 1196
Power Budgeting Extended Capability Header ..... 1198
Power Budgeting Control Register ..... 1199
Power Budgeting Data Register ..... 1201
Power Budgeting Capability Register ..... 1205
Power Budgeting Sense Detect Register ..... 1207
Power Budgeting Sense Detect Encodings ..... 1207
LTR Extended Capability Header ..... 1210
Max Snoop Latency Register ..... 1211
Max No-Snoop Latency Register ..... 1211
L1 PM Substates Extended Capability Header ..... 1212
L1 PM Substates Capabilities Register ..... 1213
L1 PM Substates Control 1 Register ..... 1214
L1 PM Substates Control 2 Register ..... 1216
L1 PM Substates Status Register ..... 1217
Advanced Error Reporting Extended Capability Header ..... 1220
Uncorrectable Error Status Register ..... 1221
Uncorrectable Error Mask Register ..... 1224
Uncorrectable Error Severity Register ..... 1226
Correctable Error Status Register ..... 1228
Correctable Error Mask Register ..... 1230
Advanced Error Capabilities and Control Register ..... 1231
Header Log Register ..... 1233
Root Error Command Register ..... 1234
Root Error Status Register ..... 1235
Error Source Identification Register ..... 1237
TLP Prefix Log Register ..... 1238
First DW of Enhanced Allocation Capability ..... 1238
Second DW of Enhanced Allocation Capability ..... 1239
First DW of Each Entry for Enhanced Allocation Capability ..... 1240
Enhanced Allocation Entry Field Value Definitions for both the Primary Properties and Secondary Properties Fields ..... 1242
Resizable BAR Extended Capability Header ..... 1247
Resizable BAR Capability Register ..... 1248
Resizable BAR Control Register ..... 1250
VF Resizable BAR Extended Capability Header ..... 1254
VF Resizable BAR Control Register ..... 1255

Table 7-157 ARI Extended Capability Header ..... 1256
Table 7-158 ARI Capability Register ..... 1257
Table 7-159 ARI Control Register ..... 1258
Table 7-160 PASID Extended Capability Header ..... 1259
Table 7-161 PASID Capability Register ..... 1260
Table 7-162 PASID Control Register ..... 1261
Table 7-163 FRS Queueing Extended Capability Header ..... 1262
Table 7-164 FRS Queueing Capability Register ..... 1263
Table 7-165 FRS Queueing Status Register ..... 1264
Table 7-166 FRS Queueing Control Register ..... 1264
Table 7-167 FRS Message Queue Register ..... 1265
Table 7-168 FPB Capabilities Header ..... 1266
Table 7-169 FPB Capabilities Register ..... 1266
Table 7-173 FPB RID Vector Control 1 Register ..... 1268
Table 7-176 FPB RID Vector Control 2 Register ..... 1270
Table 7-177 FPB MEM Low Vector Control Register ..... 1270
Table 7-180 FPB MEM High Vector Control 1 Register ..... 1272
Table 7-183 FPB MEM High Vector Control 2 Register ..... 1273
Table 7-185 FPB Vector Access Control Register ..... 1274
Table 7-187 FPB Vector Access Data Register ..... 1275
Table 7-188 Flit Performance Measurement Extended Capability Header ..... 1277
Table 7-189 Flit Performance Measurement Capability Register ..... 1277
Table 7-190 Flit Performance Measurement Control Register ..... 1278
Table 7-191 Flit Performance Measurement Status Register ..... 1280
Table 7-192 LTSSM Performance Measurement Status Register ..... 1281
Table 7-193 Flit Error Injection Extended Capability Header ..... 1283
Table 7-194 Flit Error Injection Capability Register ..... 1284
Table 7-195 Flit Error Injection Control 1 Register ..... 1284
Table 7-196 Flit Error Injection Control 2 Register ..... 1286
Table 7-197 Flit Error Injection Status Register ..... 1287
Table 7-198 Ordered Set Error Injection Control 1 Register ..... 1288
Table 7-199 Ordered Set Error Injection Control 2 Register ..... 1290
Table 7-200 Ordered Set Tx Error Injection Status Register ..... 1290
Table 7-201 Ordered Set Rx Error Injection Status Register ..... 1291
Table 7-202 NOP Flit Extended Capability Header ..... 1293
Table 7-203 NOP Flit Capabilites Register ..... 1294
Table 7-204 NOP Flit Control 1 Register ..... 1294
Table 7-205 NOP Flit Control 2 Register ..... 1296
Table 7-206 NOP Flit Status Register ..... 1297
Table 7-207 Virtual Channel Extended Capability Header ..... 1299
Table 7-208 Port VC Capability Register 1 ..... 1300
Table 7-209 Port VC Capability Register 2 ..... 1301
Table 7-210 Port VC Control Register ..... 1302
Table 7-211 Port VC Status Register ..... 1303
Table 7-212 VC Resource Capability Register ..... 1303
Table 7-213 VC Resource Control Register ..... 1305
Table 7-214 VC Resource Status Register ..... 1307
Table 7-215 Definition of the 4-bit Entries in the VC Arbitration Table. ..... 1308
Table 7-216 Length of the VC Arbitration Table ..... 1308
Table 7-217 Length of Port Arbitration Table ..... 1309
Table 7-218 MFVC Extended Capability Header ..... 1311
Table 7-219 MFVC Port VC Capability Register 1 ..... 1311

Table 7-220 MFVC Port VC Capability Register 2 ..... 1312
Table 7-221 MFVC Port VC Control Register ..... 1313
Table 7-222 MFVC Port VC Status Register ..... 1314
Table 7-223 MFVC VC Resource Capability Register ..... 1314
Table 7-224 MFVC VC Resource Control Register ..... 1316
Table 7-225 MFVC VC Resource Status Register ..... 1318
Table 7-226 Length of Function Arbitration Table ..... 1319
Table 7-227 Device Serial Number Extended Capability Header ..... 1321
Table 7-228 Serial Number Register ..... 1321
Table 7-229 Vendor-Specific Capability ..... 1322
Table 7-230 Vendor-Specific Extended Capability Header ..... 1323
Table 7-231 Vendor-Specific Header ..... 1324
Table 7-232 Designated Vendor-Specific Extended Capability Header ..... 1326
Table 7-233 Designated Vendor-Specific Header 1 ..... 1326
Table 7-234 Designated Vendor-Specific Header 2 ..... 1327
Table 7-235 RCRB Header Extended Capability Header ..... 1328
Table 7-236 RCRB Vendor ID and Device ID register ..... 1329
Table 7-237 RCRB Capabilities register ..... 1329
Table 7-238 RCRB Control register ..... 1329
Table 7-239 Root Complex Link Declaration Extended Capability Header ..... 1332
Table 7-240 Element Self Description Register ..... 1332
Table 7-241 Link Description Register ..... 1333
Table 7-242 Link Address for Link Type 1 ..... 1335
Table 7-243 Root Complex Internal Link Control Extended Capability Header ..... 1336
Table 7-244 Root Complex Link Capabilities Register ..... 1337
Table 7-245 Root Complex Link Control Register ..... 1340
Table 7-246 Root Complex Link Status Register ..... 1341
Table 7-247 Root Complex Event Collector Endpoint Association Extended Capability Header ..... 1342
Table 7-248 RCEC Associated Bus Numbers Register ..... 1343
Table 7-249 Multicast Extended Capability Header ..... 1345
Table 7-250 Multicast Capability Register ..... 1346
Table 7-251 Multicast Control Register ..... 1347
Table 7-252 MC_Base_Address Register ..... 1347
Table 7-253 MC_Receive Register ..... 1348
Table 7-254 MC_Block_All Register ..... 1349
Table 7-255 MC_Block_Untranslated Register ..... 1349
Table 7-256 MC_Overlay_BAR Register ..... 1350
Table 7-257 DPA Extended Capability Header ..... 1351
Table 7-258 DPA Capability Register ..... 1351
Table 7-259 DPA Latency Indicator Register ..... 1352
Table 7-260 DPA Status Register ..... 1353
Table 7-261 DPA Control Register ..... 1353
Table 7-262 Substate Power Allocation Register (0 to Substate_Max) ..... 1354
Table 7-263 TPH Requester Extended Capability Header ..... 1355
Table 7-264 TPH Requester Capability Register ..... 1356
Table 7-265 TPH Requester Control Register ..... 1357
Table 7-266 TPH ST Table Entry ..... 1358
Table 7-267 DPC Extended Capability Header ..... 1361
Table 7-268 DPC Capability Register ..... 1362
Table 7-269 DPC Control Register ..... 1363
Table 7-270 DPC Status Register ..... 1365
Table 7-271 DPC Error Source ID Register ..... 1367

Table 7-272 RP PIO Status Register ..... 1367
Table 7-273 RP PIO Mask Register ..... 1368
Table 7-274 RP PIO Severity Register ..... 1369
Table 7-275 RP PIO SysError Register ..... 1370
Table 7-276 RP PIO Exception Register ..... 1371
Table 7-277 RP PIO Header Log Register ..... 1372
Table 7-278 RP PIO ImpSpec Log Register ..... 1372
Table 7-279 RP PIO TLP Prefix Log Register ..... 1373
Table 7-280 PTM Extended Capability Header ..... 1374
Table 7-281 PTM Capability Register ..... 1375
Table 7-282 PTM Control Register ..... 1376
Table 7-284 Readiness Time Reporting Extended Capability Header ..... 1379
Table 7-285 Readiness Time Reporting 1 Register ..... 1379
Table 7-286 Readiness Time Reporting 2 Register ..... 1380
Table 7-287 Hierarchy ID Extended Capability Header ..... 1382
Table 7-288 Hierarchy ID Status Register ..... 1383
Table 7-289 Hierarchy ID Data Register ..... 1384
Table 7-290 Hierarchy ID GUID 1 Register ..... 1385
Table 7-291 Hierarchy ID GUID 2 Register ..... 1385
Table 7-292 Hierarchy ID GUID 3 Register ..... 1386
Table 7-293 Hierarchy ID GUID 4 Register ..... 1386
Table 7-294 Hierarchy ID GUID 5 Register ..... 1387
Table 7-295 VPD Address Register ..... 1389
Table 7-296 VPD Data Register ..... 1389
Table 7-297 NPEM Extended Capability Header ..... 1390
Table 7-298 NPEM Capability Register ..... 1391
Table 7-299 NPEM Control Register ..... 1392
Table 7-300 NPEM Status Register ..... 1394
Table 7-301 Alternate Protocol Extended Capability Header ..... 1395
Table 7-302 Alternate Protocol Capabilities Register ..... 1396
Table 7-303 Alternate Protocol Control Register ..... 1397
Table 7-304 Alternate Protocol Data 1 Register ..... 1397
Table 7-305 Alternate Protocol Data 2 Register ..... 1398
Table 7-306 Alternate Protocol Selective Enable Mask Register ..... 1398
Table 7-307 Advanced Features Capability Header ..... 1399
Table 7-308 AF Capabilities Register ..... 1400
Table 7-309 Conventional PCI Advanced Features Control Register ..... 1400
Table 7-310 AF Status Register ..... 1401
Table 7-311 SFI Extended Capability Header ..... 1402
Table 7-312 SFI Capability Register ..... 1403
Table 7-313 SFI Control Register ..... 1403
Table 7-314 SFI Status Register ..... 1405
Table 7-315 SFI CAM Address Register ..... 1406
Table 7-316 SFI CAM Data Register ..... 1406
Table 7-317 Subsystem ID and Subsystem Vendor ID Capability Header ..... 1407
Table 7-318 Subsystem ID and Subsystem Vendor ID Capability Data. ..... 1407
Table 7-319 DOE Extended Capability Header ..... 1408
Table 7-320 DOE Capabilities Register ..... 1409
Table 7-321 DOE Control Register ..... 1410
Table 7-322 DOE Status Register ..... 1411
Table 7-323 DOE Write Data Mailbox Register ..... 1412
Table 7-324 DOE Read Data Mailbox Register ..... 1413

Table 7-325 Shadow Functions Extended Capability Header ..... 1415
Table 7-326 Shadow Functions Capability Register ..... 1416
Table 7-327 Shadow Functions Control Register ..... 1416
Table 7-328 Shadow Functions Instance Register Entry ..... 1417
Table 7-329 IDE Extended Capability Header ..... 1418
Table 7-330 IDE Capability Register ..... 1419
Table 7-331 IDE Control Register ..... 1421
Table 7-332 Link IDE Stream Control Register ..... 1422
Table 7-333 Link IDE Stream Status Register ..... 1423
Table 7-334 Selective IDE Stream Capability Register ..... 1424
Table 7-335 Selective IDE Stream Control Register ..... 1425
Table 7-336 Selective IDE Stream Status Register ..... 1427
Table 7-337 IDE RID Association Register 1 (Offset +00h) ..... 1428
Table 7-338 IDE RID Association Register 2 (Offset +04h) ..... 1428
Table 7-339 IDE Address Association Register 1 (Offset +00h) ..... 1429
Table 7-340 IDE Address Association Register 2 (Offset +04h) ..... 1429
Table 7-341 IDE Address Association Register 3 (Offset +04h) ..... 1430
Table 7-342 Null Capability ..... 1430
Table 7-343 Null Extended Capability ..... 1431
Table 7-344 Streamlined Virtual Channel Extended Capability Header ..... 1432
Table 7-345 SVC Port Capability Register 1 ..... 1433
Table 7-346 SVC Port Control Register ..... 1434
Table 7-347 SVC Port Status Register ..... 1434
Table 7-348 SVC Resource Capability Register ..... 1435
Table 7-349 SVC Resource Control Register ..... 1436
Table 7-350 SVC Resource Status Register ..... 1438
Table 7-351 MRBL Extended Capability Header ..... 1439
Table 7-352 MRBL Capabilities Register ..... 1440
Table 7-353 MRBL Locator Register ..... 1440
Table 8-1 Tx Preset Ratios and Corresponding Coefficient Values for 8.0, 16.0, and 32.0 GT/s ..... 1449
Table 8-2 Tx Preset Ratios and Corresponding Coefficient Values for 64.0 GT/s ..... 1450
Table 8-3 Cases that the Reference Packages and ps21 ${ }_{\text {TX }}$ Parameter are Normative ..... 1457
Table 8-4 Recommended De-embedding Cutoff Frequency ..... 1468
Table 8-5 Tx Measurement and Post Processing For Different Refclks ..... 1470
Table 8-6 Data Rate Dependent Transmitter Parameters ..... 1478
Table 8-7 Data Rate Independent Tx Parameters ..... 1486
Table 8-8 Calibration Channel IL Limits ..... 1489
Table 8-11 Stressed Jitter Eye Parameters ..... 1510
Table 8-12 Common Receiver Parameters ..... 1522
Table 8-13 Lane Margining ..... 1526
Table 8-14 Package Model Capacitance Values ..... 1532
Table 8-15 Jitter/Voltage Parameters for Channel Tolerancing ..... 1544
Table 8-16 Channel Tolerancing Eye Mask Values ..... 1547
Table 8-17 EIEOS Signaling Parameters ..... 1550
Table 8-18 REFCLK DC Specifications and AC Timing Requirements ..... 1551
Table 8-19 Data Rate Independent Refclk Parameters ..... 1555
Table 8-20 Jitter Limits for CC Architecture ..... 1561
Table 8-21 Form Factor Clocking Architecture Requirements ..... 1562
Table 8-22 Form Factor Common Clock Architecture Details ..... 1563
Table 8-23 Form Factor Clocking Architecture Requirements Example ..... 1563
Table 8-24 Form Factor Common Clock Architecture Details Example ..... 1563
Table 9-1 VF Routing ID Algorithm ..... 1579

Table 9-2 SR-IOV Extended Capability Header ..... 1584
Table 9-3 SR-IOV Capabilities Register ..... 1584
Table 9-4 SR-IOV Control Register ..... 1587
Table 9-5 SR-IOV Status ..... 1590
Table 9-8 BAR Offsets ..... 1595
Table 9-9 SR-IOV Usage of PCI Standard Capabilities ..... 1596
Table 9-10 SR-IOV Usage of PCI Express Extended Capabilities. ..... 1596
Table 10-1 Address Type (AT) Field Encodings ..... 1609
Table 10-2 Translation Completion Status Codes ..... 1614
Table 10-3 Translation Completion Data Fields ..... 1615
Table 10-5 Examples of Translation Size Using S Field ..... 1617
Table 10-6 Page Request Message Data Fields ..... 1637
Table 10-7 PRG Response Message Data Fields ..... 1642
Table 10-8 Response Codes ..... 1642
Table 10-9 ATS Extended Capability Header ..... 1644
Table 10-10 ATS Capability Register (Offset 04h) ..... 1644
Table 10-11 ATS Control Register ..... 1645
Table 10-13 Page Request Extended Capability Header ..... 1647
Table 10-14 Page Request Control Register ..... 1648
Table 10-15 Page Request Status Register ..... 1649
Table 11-1 INTERFACE_ID Definition ..... 1659
Table 11-2 Example DSM Tracking and Handling for Architected Registers ..... 1665
Table 11-3 TDISP Request Codes ..... 1668
Table 11-4 TDISP Response Codes ..... 1669
Table 11-5 TDISP Message Format ..... 1670
Table 11-6 Generic Error Response Codes ..... 1670
Table 11-7 TDISP_VERSION ..... 1671
Table 11-8 GET_TDISP_CAPABILITIES ..... 1672
Table 11-9 TDISP_CAPABILITIES ..... 1672
Table 11-10 LOCK_INTERFACE_REQUEST ..... 1674
Table 11-11 LOCK_INTERFACE_RESPONSE ..... 1675
Table 11-12 LOCK_INTERFACE_REQUEST Error Codes ..... 1675
Table 11-13 GET_DEVICE_INTERFACE_REPORT ..... 1675
Table 11-14 DEVICE_INTERFACE_REPORT ..... 1676
Table 11-15 TDI Report Structure ..... 1676
Table 11-16 GET_DEVICE_INTERFACE_REPORT Error Response Codes ..... 1678
Table 11-17 DEVICE_INTERFACE_STATE ..... 1679
Table 11-18 START_INTERFACE_REQUEST ..... 1679
Table 11-19 START_INTERFACE_REQUEST Error Response Codes ..... 1680
Table 11-20 BIND_P2P_STREAM_REQUEST ..... 1681
Table 11-21 BIND_P2P_STREAM_REQUEST Error Response Codes ..... 1681
Table 11-22 UNBIND_P2P_STREAM_REQUEST ..... 1682
Table 11-23 UNBIND_P2P_STREAM_REQUEST Error Response Codes ..... 1683
Table 11-24 SET_MMIO_ATTRIBUTE_REQUEST ..... 1683
Table 11-25 SET_MMIO_ATTRIBUTE_REQUEST Error Response Codes ..... 1684
Table 11-26 TDISP_ERROR ..... 1684
Table 11-27 Error Code and Error Data ..... 1684
Table 11-28 EXTENDED_ERROR_DATA ..... 1685
Table 11-29 VDM_REQUEST ..... 1686
Table 11-30 VDM_RESPONSE ..... 1686
Table 11-31 Example TSM Tracking and Handling for Root Port Configurations ..... 1693
Table 12-1 Relative Comparisons of Typical Architectural Out-of-Band Interfaces ..... 1701

Table 12-2 PESTI DC Specifications ..... 1709
Table 12-3 PESTI Initiator Control and Status Registers ..... 1712
Table 12-4 PESTI Discovery Status State Transitions ..... 1712
Table 12-5 PESTI AC Specifications ..... 1714
Table 12-6 PESTI Discovery Payload ..... 1716
Table 12-7 Example VWIRE_OUT_0 (Initiator to Target) ..... 1719
Table 12-8 Example VWIRE_IN_0 (Target to Initiator) ..... 1719
Table 12-9 MSC_CTRL_VAL (Initiator to PESTI Snooper Target) Data Byte Value = 02h. ..... 1722
Table 12-10 MSC_STAT_VAL (PESTI Snooper Target to Initiator) ..... 1723
Table 12-11 2-wire Interface Example Usages ..... 1726
Table 12-12 Baseline SMBus Recommended Default Target Addresses ..... 1727
Table 12-13 I3C Basic Logic Signaling DC Specification ..... 1734
Table 12-14 I3C Timing Requirements ..... 1734
Table 12-15 PCI-SIG Multilecord ..... 1739
Table 12-17 PCI-SIG MultiRecord Descriptor ..... 1740
Table 12-18 Descriptor Sub-Types for Group ID 0h ..... 1741
Table 12-19 Connector Subdivision Combinations Descriptor ..... 1742
Table 12-20 Connector Subdivision Descriptor ..... 1742
Table A-1 Isochronous Bandwidth Ranges and Granularities ..... 1750
Table B-1 8b/10b Data Symbol Codes ..... 1757
Table B-2 8b/10b Special Character Symbol Codes ..... 1766
Table F-1 Message Code Usage ..... 1785
Table F-2 PCI-SIG-Defined VDM Subtype Usage ..... 1786
Table G-1 PCI Express Attribute Impact on Protocol Multiplexing ..... 1789
Table G-2 PMUX Attribute Impact on PCI Express ..... 1791
Table G-3 PMUX Packet Layout (8b/10b Encoding) ..... 1793
Table G-4 PMUX Packet Layout (128b/130b Encoding) ..... 1795
Table G-5 Symbol 1 Bits [6:3] ..... 1796
Table G-6 PMUX Extended Capability Header ..... 1798
Table G-7 PMUX Capability Register ..... 1799
Table G-8 PMUX Control Register ..... 1800
Table G-9 PMUX Status Register ..... 1801
Table G-10 PMUX Protocol Array Entry ..... 1803
Table H-1 Maximum UpdateFC Transmission Latency Guidelines for 2.5 GT/s Mode Operation by Link Width and Max Payload (Symbol Times) ..... 1806
Table H-2 Maximum UpdateFC Transmission Latency Guidelines for 5.0 GT/s Mode Operation by Link Width and Max Payload (Symbol Times) ..... 1806
Table H-3 Maximum UpdateFC Transmission Latency Guidelines for 8.0 GT/s Operation by Link Width and Max Payload (Symbol Times) ..... 1807
Table H-5 Maximum Ack Latency Limit and AckFactor for 2.5 GT/s (Symbol Times) ..... 1808
Table H-6 Maximum Ack Transmission Latency Limit and AckFactor for 5.0 GT/s (Symbol Times) ..... 1809
Table H-7 Maximum Ack Transmission Latency Limit and AckFactor for 8.0 GT/s (Symbol Times) ..... 1809
Table L-1 Inputs and Outputs for Example IDE TLP ..... 2127
Table L-2 Inputs and Outputs for Example IDE TLP (FM) ..... 2129
Table L-3 Inputs and Outputs for Example IDE TLP with Partial Header Encryption (mode 0100b - Address[41:2] Encrypted) (NFM) ..... 2131
Table L-4 Inputs and Outputs for Example IDE TLP with Partial Header Encryption (mode 0100b - Address[41:2] Encrypted) (FM) ..... 2133
Table L-5 IDE Test Keys ..... 2134

Page 70

# Status of this Document 

This section describes the status of this document at the time of its publication. Other documents may supersede this document. A list of current PCISIG publications and the latest revision of this specification can be found at pcisig.com

This is the PCI Express Base 6.3 Specification. This consists of Base 6.2 plus approved ECNs, errata, and editorial corrections. See Critical Errata and Important Errata and Approved ECNs.

- The NCB-PCI_Express_Base_6.3.pdf is normative (i.e., the official specification). It contains no changebars.
- The CB-PCI_Express_Base_6.3-vs-6.2.pdf is informative. It contains changebars relative to the PCI Express Base 6.2 Specification [PCIe-6.2].


## NOTE: Background on the new Document Process

The new PCISIG document system is a variant of the w3c Respec tool (see https://github.com/w3c/respec/wiki). Respec is a widely used tool written to support the World Wide Web specifications. The PCISIG variant is https://github.com/sglaser/respec. Both Respec and the PCISIG variant are open source (MIT License) Javascript libraries. They operate in the author's browser and provide a rapid edit / review cycle without requiring any special tools be installed.

Respec is built on top of HTML5, the document format for the World Wide Web http://www.w3.org/TR/html5/. HTML is a text-based document format that allows us to deploy tools commonly used for software development (git, continuous integration, build scripts, etc.) to better manage and control the spec development process.

PCISIG enhancements to Respec support document formatting closer to existing PCISIG practice as well as automatic creation of register figures (eliminating about half of the manually drawn figures).

# NOTE: Navigating in changebar documents 

The Base 6.0.1 version introduces a new errata delivery process. Instead of having a separate "change this to that" document, a new version of the specification is produced with the changes integrated into the document. This makes it easier to consume and less likely that errata will be overlooked.

All changes are annotated with the $n$ character. Searching for this character in a PDF reader will step through all changes. There is a $n$ character in the upper right of page 1 that can be copied into the search string.

Inserted text is yellow and underlined. It contains the $r$ character.
Deleted text is red and struck through. It contains the 1 character.
All errata are identified by a "red box" near the first change in a chunk of changes. This box contains one or more triangle characters that can navigate through the changes for the associated errata.

The upward pointing triangle is a link to the associated errata table entry.

The right pointing triangle is a link to the next change associated with this errata. If this is the last change, this triangle is not present.

The left pointing triangle is a link to the previous change associated with this errata. If this is the first chance, this triangle is not present.

Changes that are not marked with a red box are considered editorial in nature and are not associated with an errata.
Where the automated process can't correctly identify changes (e.g., figures and equations), the errata table contains the change description.

This document is governed by the PCI-SIG Specification Development Procedures.

# Revision History 

| Revision | Revision History | Date |
| :--: | :--: | :--: |
| 1.0 | Initial release. | 07/22/2002 |
| $1.0 a$ | Incorporated Errata C1-C66 and E1-E4.17. | 04/15/2003 |
| 1.1 | Incorporated approved Errata and ECNs. | 03/28/2005 |
| 2.0 | Added 5.0 GT/s data rate and incorporated approved Errata and ECNs. | 12/20/2006 |
| 2.1 | Incorporated Errata for the PCI Express Base Specification, Rev. 2.0 (February 27, 2009), and added the following ECNs: <br> - Internal Error Reporting ECN (April 24, 2008) <br> - Multicast ECN (December 14, 2007, approved by PWG May 8, 2008) <br> - Atomic Operations ECN (January 15, 2008, approved by PWG April 17, 2008) <br> - Resizable BAR Capability ECN (January 22, 2008, updated and approved by PWG April 24, 2008) <br> - Dynamic Power Allocation ECN (May 24, 2008) <br> - ID-Based Ordering ECN (January 16, 2008, updated 29 May 2008) <br> - Latency Tolerance Reporting ECN (22 January 2008, updated 14 August 2008) <br> - Alternative Routing-ID Interpretation (ARI) ECN (August 7, 2006, last updated June 4, 2007) <br> - Extended Tag Enable Default ECN (September 5, 2008) <br> - TLP Processing Hints ECN (September 11, 2008) <br> - TLP Prefix ECN (December 15, 2008) | $03 / 04 / 2009$ |
| 3.0 | Added 8.0 GT/s data rate, latest approved Errata, and the following ECNs: <br> - Optimized Buffer Flush/Fill ECN (8 February 2008, updated 30 April 2009) <br> - ASPM Optionality ECN (June 19, 2009, approved by the PWG August 20, 2009) <br> - Incorporated End-End TLP Changes for RCs ECN (26 May 2010) and Protocol Multiplexing ECN (17 June 2010) | $11 / 10 / 2010$ |
| 3.1 | Incorporated feedback from Member Review <br> Incorporated Errata for the PCI Express ${ }^{\circledR}$ Base Specification Revision 3.0 <br> Incorporated M-PCIe Errata (3p1_active_errata_list_mpcie_28Aug2014.doc and 3p1_active_errata_list_mpcie_part2_11Sept2014.doc) <br> Incorporated the following ECNs: <br> - ECN: Downstream Port containment (DPC) <br> - ECN: Separate Refclk Independent SSC (SRIS) Architecture <br> - ECN: Process Address Space ID (PASID) <br> - ECN: Lightweight Notification (LN) Protocol | $10 / 8 / 2014$ |

| Revision | Revision History | Date |
| :--: | :--: | :--: |
| 3.1a | - ECN: Precision Time Measurement <br> - ECN: Enhanced DPC (eDPC) <br> - ECN: 8.0 GT/s Receiver Impedance <br> - ECN: L1 PM Substates with CLKREQ <br> - ECN: Change Root Complex Event Collector Class Code <br> - ECN: M-PCIe <br> - ECN: Readiness Notifications (RN) <br> - ECN: Separate Refclk Independent SSC Architecture (SRIS) JTOL and SSC Profile Requirements | $\begin{aligned} & 12 / 5 / 2015 \\ & 2 / 6 / 2015 \end{aligned}$ |
| 4.0 | Version 0.3: Based on PCI Express ${ }^{\circledR}$ Base Specification Revision 3.1 (October 8, 2014) with some editorial feedback received in December 2013. <br> - Added § Chapter 9., Electrical Sub-block: Added § Chapter 9. (Rev0.3-11-30-13_final.docx) <br> - Changes related to Revision 0.3 release <br> - Incorporated PCIe-relevant material from PCI Bus Power Management Interface Specification (Revision 1.2, dated March 3, 2004). This initial integration of the material will be updated as necessary and will supersede the standalone Power Management Interface specification. <br> Version $0.5(12 / 22 / 14$, minor revisions on 1/26/15, minor corrections $2 / 6 / 15)$ <br> - Added front matter with notes on expected discussions and changes. <br> - Added ECN:Retimer (dated October 6, 2014) <br> - Corrected § Chapter 4. title to, "Physical Layer Logical Block". <br> - Added Encoding subteam feedback on § Chapter 4. <br> - Added Electrical work group changes from PCIe Electrical Specification Rev 0.5 RC1 into § Chapter 9. |  |
|  | Version 0.7: Based on PCI Express ${ }^{\circledR}$ Base Specification Version 4.0 Revision 0.5 (11/23/2015) <br> - Added ECN_DVSEC-2015-08-04 <br> - Applied ECN PASID-ATS dated 2011-03-31 <br> - Applied PCIE Base Spec Errata: PCIe_Base_r3 1_Errata_2015-09-18 except: <br> - B216; RCIE <br> - B256; grammar is not clear <br> - Changes to Chapter 7. Software Initialization and Configuration per PCIe_4.0_regs_0-3F_gord_7.docx <br> - Added Chapter SR-IOV Spec Rev 1.2 (Rev 1.1 dated September 8, 2009 plus: <br> - SR-IOV_11_errata_table.doc | $11 / 24 / 2015$ |

| Revision | Revision History | Date |
| :--: | :--: | :--: |
|  | - DVSEC <br> - 3.1 Base Spec errata <br> - Added Chapter ATS Spec Rev 1.2 (Rev 1.1 dated January 26, 2009 plus: <br> - ECN-PASID-ATS <br> - 3.1 Base Spec errata |  |
|  | 2/18/2016 Changes from the Protocol Working Group <br> - Applied changes from the following documents: <br> - FC Init/Revision | scaled-flow-control-pcie-base40-2016-01-07.pdf (Steve.G) <br> - Register updates for integrated legacy specs | PCle_4.0_regs_0-3F_gord_8.docx (GordC) <br> - Tag Scaling PCle 4_0 Tag Field scaling 2015-11-23 clean.docx (JoeC) <br> - MSI/MSI-X|PCle 4_0 MSI \& MSI-X 2015-12-18 clean.docx (JoeC); register diagrams TBD on next draft. <br> - REPLAY_TIMER/Ack/FC Limits | Ack_FC_Replay_Timers_ver8 (PeterJ) | 2/18/16 |
|  | Chapter 10. SR-IOV related changes: <br> - Incorporated "SR-IOV and Sharing Specification" Revision 1.1 dated January 20, 2010 (sr-iov1_1_20Jan10.pdf) as § Chapter 10., with changes from the following documents <br> - Errata for the PCI Express ${ }^{\circledR}$ Base Specification Revision 3.1, Single Root I/O Virtualization and Sharing Revision 1.1, Address Translation and Sharing Revision 1.1, and M. 2 Specification Revision 1.0: PCle_Base_r3 1_Errata_2015-09-18_clean.pdf <br> - ECN__Integrated_Endpoints_and_IOV_updates__19 Nov 2015_Final.pdf <br> - Changes marked "editorial" only in marked PDF: sr-iov1_1_20Jan10-steve-manning-comments.pdf | 4/26/16 [snapshot] |
|  | Chapter 9. Electrical Sub-Block related changes: <br> Source: WG approved word document from Dan Froelich (FileName: <br> Electrical-PCI_Express_Base_4.0r0.7_April_7_wg_approved_redo_for_figure_corruption.docx) | $\begin{aligned} & 5 / 23 / \\ & 16 \text { [snapshot } \end{aligned}$ |
|  | Version 0.7 continued... <br> Chapter 4. PHY Logical Changes based on: <br> - Chapter4-PCI_Express_Base_4 0r0 7_May3_2016_draft.docx <br> Chapter 7. . PHY Logical Changes based on: <br> - PCI_Express_Base_4 0r0 7_Phy-Logical_Ch7_Delta_28_Apr_2016.docx |  |
|  | Changes incorporated into the August 2016 4.0 r0.7 Draft PDF - ........... <br> June 16 Feedback from PWG on the May 2016 snapshot | 8/30/16 |

| Revision | Revision History | Date |
| :--: | :--: | :--: |
|  | PWG Feedback on 4.0 r0.7 Feb-Apr-May-2016 Drafts <br> *EWG Feedback: <br> -CB-PCI_Express_Base_4.0r0.7_May-2016 (Final).fdf <br> -EWG f/b: <br> Electrical-PCI_Express_Base_4.0r0.7_April_7_wg_approved_redo_for_figure_corruption_Broadco.docx <br> *PWG Feedback: <br> -PWG 0.7 fix list part1 and part 2.docx <br> -PWG 07 fix list part3a.docx <br> -PCI_Express_Base_4.0r0.7_pref_April-2016_chp5_PM_stuff_only_ver3.docx <br> -PCI_Express_Base_4.0r0.7_pref_April-2016_chp5_PM_stuff_only_ver3.docx <br> -scaled-flow-control-pcie-base40-2016-07-07.pdf <br> -ECN_NOP_DLLP-2014-06-11_clean.pdf <br> -ECN_RN_29_Aug_2013.pdf <br> -3p1_active_errata_list_mpcie_28Aug2014.doc <br> -3p1_active_errata_list_mpcie_part2_11Sept2014.doc <br> -lane-margining-capability-snapshot-2016-06-16.pdf <br> -Emergency Power Reduction Mechanism with PWRBRK Signal ECN <br> -PWG 07 fix list part4.docx <br> -ECN_Conventional_Adv_Caps_27Jul06.pdf <br> -10-bit Tag related SR-IOV Updates <br> *Other: <br> -Merged Acknowledgements back pages from SR-IOV and ATS specifications into the main base spec. Acknowledgements page. |  |  |
|  | Changes since August 2016 for the September 2016 4.0 r0.7 Draft PDF- . . . <br> Applied: <br> PWG Feedback/Corrections on August draft <br> ECN_SR-IOV_Table_Updates_16-June-2016.doc | 9/28/16 |
|  | Changes since September 282016 for the October 2016 4.0 r0.7 Draft PDF- . . . <br> EWG: <br> Updates to \$ Chapter 9. - Electrical Sub-block (Sections: 9.4.1.4, 9.6.5.1, 9.6.5.2, 9.6.7) <br> PWG: <br> Updates to Sections: 3.2.1, 3.3, 3.5.1, 7.13, 7.13.3 (Figure: Data Link Status Register) | $10 / 7 / 16$ |
|  | Changes to the October 1320164.0 r0.7 Draft PDF- . . . | $10 / 21 / 16$ |

| Revision | Revision History | Date |
| :--: | :--: | :--: |
|  | EWG: <br> Updates to \$ Chapter 9. - Electrical Sub-block (\$ Section 9.3.3.9 and Figure 9-9 caption) |  |
|  | -....- Changes to the November 320164.0 r0.7 Draft PDF-... <br> \$ Section 2.6.1 Flow Control Rules: Updated Scaled Flow Control sub-bullet under FC initialization bullet (before Table 2-43) | $11 / 3 / 16$ |
|  | -....- Changes to the November 1120164.0 r0.7 Draft PDF-... <br> Added M-PCIe statement to the Open Issues page <br> Updated date to November 11, 2016 | $11 / 11 / 16$ |
| Version 0.9: Based on PCI Express ${ }^{\circledR}$ Base Specification Version 4.0 Revision 0.7 (11/11/2016) |  |  |
| Incorporated the following ECNs: <br> -ECN-Hierarchy_ID-2017-02-23 <br> -ECN_FPB_9_Feb_2017 <br> -ECN Expanded Resizable BARs 2016-04-18 <br> -ECN-VF-Resizable-BARs_6-July-2016 <br> - \$ Chapter 7. reorganized: <br> - New section 7.6 created per a PWG-approved reorganization to move sections $7.5,7.6$, and 7.10 to subsections 7.6 .1 through 7.6 .3 resp. <br> - New section 7.7 created per a PWG-approved reorganization to move sections $7.7,7.8,7.12$, $7.13,7.40,7.41$ and 7.20 to subsections 7.7 .1 through 7.7 .7 resp. <br> - New section 7.9 created per a PWG-approved reorganization to move sections $7.15,7.22,7.16$, $7.23,7.39,7.24,7.17,7.18,7.21,7.25,7.28,7.30,7.33,7.34,7.35,7.38$, and 7.42 to subsections 7.9.1 through 7.9.17 resp. <br> -Removed \$ Chapter 8. : M-PCIe Logical Sub-Block <br> -Updated \$ Chapter 9. (8 now), EWG Updates to \$ Chapter 9. - Electrical Sub-block per: Chapter9-PCI_Express_Base_4 0r09_March_30-2017_approved.docx <br> -Updated \$ Chapter 4. : Physical Layer Logical Block per PCI_Express_Base_4 0_r0 9_Chapter4_Final_Draft.docx <br> -Updated Figures in \$ Chapter 10. : ATS Specification <br> -Removed \$ Appendix H. : M-PCIe timing Diagrams <br> -Removed Appendix I: M-PCIe Compliance Patterns, pursuant to removing the M-PCIe Chapter this 0.9 version of the 4.0 Base Spec. <br> -Added \$ Appendix H. : Flow Control Update Latency and ACK Update Latency Calculations <br> -Added Appendix I: Vital Product Data (VPD) | April 28 2017 |

| Revision | Revision History | Date |
| :--: | :--: | :--: |
|  | -Updated editorial feedback on the Appendix section per: <br> PCI_Express_Base_4.0r0.7_appendixes_November-11-2016_combined-editorial.docx <br> -Deleted references to M-PCIe throughout the document. <br> -Updated § Chapter 9. (8 now), EWG Updates to § Chapter 9. - Electrical Sub-block per: Chapter9-PCI_Express_Base_4 0r09_March_30-2017_approved.docx <br> -Updated § Chapter 4. : Physical Layer Logical Block per PCI_Express_Base_4 0_r0 9_Chapter4_Final_Draft.docx <br> -Updated Figures in § Chapter 10. : ATS Specification <br> -Added § Appendix H. : Flow Control Update Latency and ACK Update Latency Calculations <br> -Following items that were marked deleted in the Change Bar version of the April $28^{\text {th }}$ snapshot have been "accepted" to no longer show up: pp 1070: Lane Equalization Control 2 Register (Offset TBD) <br> Comment: Deleted per: PCI_Express_Base_4 0r0 7_Phy-Logical_Ch7_Delta_28_Apr_2016.docx pp 1074: <br> Physical Layer 16.0 GT/s Margining Extended Capability section Comment: Deleted per: <br> PCI_Express_Base_4 0r0 7_Phy-Logical_Ch7_Delta_28_Apr_2016.docx Comment: Replaced by Section Lane Margining at the Receiver Extended Capability per Fix3a \#83 <br> lane-margining-capability-snapshot-2016-06-16.pdf <br> -Incorporated: PCIe 4_0 Tag Field scaling 2017-03-31.docx <br> -Vital Product Data (VPD) <br> -Added § Section 6.27 <br> -Added § Section 7.9.4 <br> -Incorporated feedback from April $28^{\text {th }}$ snapshot.[source: 3 fdf files] <br> -Completed editorial feedback on the Appendix section per: <br> PCI_Express_Base_4.0r0.7_appendixes_November-11-2016_combined-editorial.docx <br> -Incorporated ECN EMD for MSI 2016-05-10 <br> -Updated per: PWG F2F changes from: <br> PCI_Express_Base_4.0r0.7_pref_November-11-2016-F2F-2017-03-16-2017-03-30-sdg.docx <br> -Updated figures per following lists (Gord Caruk): PCIe_40_fix_drawing_items.doc PCIe_4 0_fix_drawing_items_part2.doc | May 26, <br> 2017 |
|  | Version 0.91 <br> ***Note this version will be used as the base for the PCI Express ${ }^{\circledR}$ Base Specification Revision 5.0*** <br> Item numbers are with reference to PWG CheckList (https://members.pcisig.com/wg/PCIe-Protocol/ document/10642) <br> -Moved Flattening Portal Bridge Section 7.10 to Section 7.8.10. PWG Checklist Items \#12.1 <br> -Fixed misc. feedback that needed clarification from the 0.9 version. Issues fall under the categories of figure updates, broken cross references. Also incorporated feedback received from member review of the 4.0 version rev. 0.9 Base Spec. <br> -Updated to reconcile issues related to incorporating the Extended Message Data for MSI ECN. PWG Checklist Items \#22 | August 17, <br> 2017 |

| Revision | Revision History | Date |
| :--: | :--: | :--: |
|  | -Completed incorporating all resolved editorial items from PWG Checklist Items \#14, 14.1,15.1, 36, 42. TBD: Some minor editorial items from \#13, \#14 and \#15 have been deferred to post 0.91 by reviewers. TBD: Errata and NPEM ECN |  |
|  | ECN: ECN_Native_PCIe_Enclosure_Management_v10August2017.docx <br> Deleted Section 5.11.1 through Section 5.14 <br> Changes tracked by items 34.0134.0234.0434.0534.11 in the PWG checklist <br> Errata: B265, C266, 267, 268, B269, A270, A271, B274, C275, B276, B277, B278, B279, B280, B281, B283, B284, B285, B286, B288, B289, B292, B293, B294, B295, B297, B299, B300, B301 <br> Other minor edits per: NCB-PCI_Express_Base_4.0r0.91_August-17-2017__dh_sdg_Annot_2.fdf | August 28, 2017 |
|  | Applied fixes and corrections captured in NCB-PCI_Express_Base_4.0r1.0_August-28-2017.fdf (Revision 8): <br> https://members.pcisig.com/wg/PCIe-Protocol/document/10770 <br> Updated contributor list in Appendix section. | September 20, 2017 |
|  | Updated contributor list in Appendix section. <br> Inserted correct Figure 6-2. <br> Applied minor fixes and corrections captured in: <br> NCB-PCI_Express_Base_4.0r1.0_September-20-2017 https://members.pcisig.com/wg/PCIe-Protocol/ document/10770 | September 27, 2017 |
|  | "-c" version: Changes to match -b version of the Final NCB PDF approved by PWG and EWG on September 29, 2017. See change bars. Details include: <br> EWG Changes: <br> -Typo in Equation 8-3; changed 1.6.0 GT/s to 16.0 GT/s <br> - § Section 8.4.2.1 ; corrected references from Table 8-11 to Table 8-10 <br> - § Section 8.5.1.3.3 \& § Section 8.5.1.4.3 (Figure 8-47); changed "median" to "mean" <br> PWG Changes: <br> -Sub-Sub-Bullet before Figure 4-27. Added "or higher" after 8.0 GT/s <br> - § Section 5.12 Power Management Events; deleted last two paragraphs and Implementation Note. <br> -Updated Acknowledgements section with additional contacts. | September 29, 2017 |
| 5.0 | Version 0.3 <br> Summary of intended changes for 5.0. This was a short document, referencing the PCI Express Base Specification but not including it. | $2017-06-01$ |
|  | Version 0.5 | 2017-11-02 |

| Revision | Revision History | Date |
| :--: | :--: | :--: |
|  | Further details on intended changes for 5.0. This was a short document, referencing the PCI Express Base Specification but not including it. |  |
|  | Version 0.7 <br> This was the first release of Base 5.0 based on the 4.0 Specification text. The 4.0 specification was converted into HTML format during this process. This conversion process was imperfect but does not impact the new 5.0 material. | 2018-06-07 |
|  | Version 0.9 <br> This includes: <br> - Additional details regarding operating at $32.0 \mathrm{GT} / \mathrm{s}$ <br> - Corrections to match published Base 4.0 <br> - Redrawing of some figures <br> - PCIe_Base_r4_0_Errata_2018-10-04a.pdf <br> - ECN-Thermal-Reporting 2017May18.pdf <br> - ECN-Link-Activation-07-Dec-2017.pdf | 2018-10-18 |
|  | Version 1.0 <br> This includes: <br> - Corrections and clarification for support of the $32.0 \mathrm{GT} / \mathrm{s}$ operation <br> - Editorial Changes: <br> - Rewrite misleading / confusing text <br> - Update terminology for consistency and accuracy <br> - Update grammar for readability <br> - Add many hotlinks / cross references <br> - Implement all 4.0 Errata <br> - Incorporate Expansion ROM Validation ECN Expansion ROM Validation ECN.pdf <br> - Incorporate Enhanced PCIe Precision Time Measurement (ePTM) ECN ECN_ePTM_10_January_2019.pdf <br> - Incorporate Root Complex Event Collector Bus Number Association ECN ECN EventCollector 13Sept2018a.pdf <br> - Incorporate PCIe Link Activation ECN ECN Link Activation 07 Dec 2017.pdf <br> - Incorporate Advanced Capabilities for Conventional PCI ECN (updated for PCIe) ECN_Conventional_Adv_Caps_27Jul06.pdf <br> - Incorporate Async Hot-Plug Updates ECN ECN Async Hot-Plug Updates 2018-11-29.pdf <br> - Incorporate ACS Enhanced Capability ECN ECN_ACS_25_Apr_2019_Clean.pdf | 2019-05-16 |

| Revision | Revision History | Date |
| :--: | :--: | :--: |
|  | - Incorporate the Subsystem ID and Subsystem Vendor ID Capability, from the PCI-to-PCI Bridge Architecture Specification, Revision 1.2 (updated for PCIe) ppb12. pdf |  |
| 6.0 | Version 0.3 | 2019-10-04 |
|  | Initial Release of Base 6.0, Standalone Document |  |
|  | Version 0.5, Standalone Document | 2020-01-30 |
|  | - Add L0p <br> - Add Shared Flow Control <br> - Update Physical Layer / Logical Sublayer meterial <br> - Add Deprecation items: <br> = MR-IOV <br> = Lightweight Notification (LN) <br> - Update new TLP Header material <br> - Update Electrical Layer material |  |
|  | Version 0.7, Integrated Document |  |
|  | First version relative to Base 5.0 Specification text. <br> - Incorporate Base 5.0 Errata Matching Errata document to be published. <br> - Incorporate Approved Base 5.0 ECNs: <br> = ACS Enhanced Capability <br> = ATS Memory Attributes Shadow Functions <br> = CMA <br> = DOE <br> = PTM Byte Order Adaptation <br> = DMWr <br> = PASID for Untranslated Addr <br> - Support Flit Mode changes in Chapter 2 <br> = 14 bit Tag support <br> = Flit Mode TLP Format changes, including translation rules <br> - Support Shared Flow Control, L0p, NULL2 DLLP in Chapter 3 <br> - Integrate Flit Mode material into Chapter 4 <br> - Flit Mode changes to Error Handling in Chapter 6 <br> = TLP Translation Blocked error <br> - Integrate PAM4 Electrical changes into Chapter 8 <br> - Refactor SR-IOV Registers from Chapter 9 into Chapter 7 Moves "VFs do things this way" material next to the original. |  |

- Define Shared Flow Control Supported and Shared Flow Control Enable bits in Chapter 7 (removed in Version 0.9)
- Virtual Channel Extended Capability
- Multi-Function Virtual Channel Extended Capability
- Define new capabilities associated with 64.0 GT/s and Flit Mode in Chapter 7
- Physical Layer 64.0 GT/s Extended Capability
- Flit Logging Extended Capability
- Device 3 Extended Capability Structure
- Flit Performance Measurement Extended Capability
- Flit Error Injection Extended Capability
- Deprecate material:
- MR-IOV
- Lightweight Notification (LN)

Version 0.71, Integrated Document

- Incorporate Combined Power ECN
- Incorporate IDE ECN, plus Partial Header Encryption
- Incorporate Errata: B90a, B90b, B90c, B90d, B90g, B90h, B90j, B90k, B90l, B90m, B90n, B90o, B90w, B90x, B90y, B90z, B113, B114
- LOp updates
- Shared Flow control Updates
- PAM4, 64.0 GT/s electrical updates
- Physical Layer, Logical Sub-block updates
- Rework Flit Ack/Nak protocol
- Training Set changes
- Max Payload Supported changes
- TLP Layout changes
- 14 bit tag updates
- SR-IOV updates
- Data Link Feature DLLP updates
- DRS is MUST@FLIT, explain how software should use
- Specify additional error behavior

Version 0.9, Integrated Document

- Implement Errata B23, B64, B66-67, B74-75, B77, B78, B80-81, B85-88, B89a, B90f, B93-B95, B98-101, B103-105, B107-111, B112, B115-118, B120-121, B123-125, B127-128, B132, B133a-B133c, B133e
- Simplified Shared Flow Control (always on in Flit Mode) and improvements to text
- Numerous Phy Logical updates and issue fixes
- Updated and Improved Flit Mode TLP type earmarking

| Revision | Revision History | Date |
| :--: | :--: | :--: |
|  | - Updated and Improved OHC content <br> - Improve Segment-related content <br> - Improve Max Payload Size content <br> - MUST@FLIT changes, esp for Completion Timeout mechanism <br> - Numerous editorial improvements |  |
|  | Version 1.0, Published Document <br> - Incorporate Relaxed Detect Timing ECN <br> - Numerous editorial improvements <br> - Update errata B117 <br> - Add missing artwork <br> - Fix and add cross references <br> - Electrical section clarifications <br> - Add Remote LOp Supported bit in Device Status 3 <br> - Define Null Capability and Null Extended Capability <br> - Update Reference Documents <br> - Update encoding of Flit Mode Local TLP Prefix (was inconsistent in 0.9) | 2021-12-16 |

# Critical Errata 

| Revision | Errata | Description |
| :--: | :--: | :--: |
| 6.0.1 | A20 | Partial Header Encryption Corrections: <br> - Define Partial Header Encryption Mode field for Like IDE <br> - Correct Partial Header Encryption Algorithm to correct functional issues and to use Byte level granularity instead of bit granularity as required in AES-GCM. <br> - Update $\S$ Figure L-1 to include Attr[2] (a.k.a. A2 or IDO). <br> - Add $\S$ Section L. 2 . |
| 6.0.1 | A27 | Clarify Flit Mode Receiver parsing requirements regarding of the Length field. |
| 6.0.1 | A35 | Shared Flow Control Corrections: <br> - Split Table 3-2 into § Table 3-2 and § Table 3-3 <br> - Correct encoding of Symbol +0 bit 3 in § Figure 3-9, § Figure 3-10, and § Figure 3-11 to match § Table $3-3$ <br> - Remove obsolete "Shared Flow Control Flit_Marker" text from the Recommended Priority of Scheduled Transmissions Implementation Note. |
| 6.0.1 | A35a | Shared Flow Control Usage Limit is RsvdP for Non-Flit Mode components. |

| Revision | Errata | Description |
| :--: | :--: | :--: |
| 6.0.1 | A37 | Corrections to the Flit Sequence Number and Retry Mechanism (see § Section 4.2.3.4.2.1) |
| 6.0.1 | A38 | LOp Corrections: <br> - Preserve LFSR relationship between Lanes on width increase <br> - Update scrambler behavior during LOp width increase <br> - Update Link Managment DLLP Behavior <br> - Update LFSR advancement rules for LOp |
| 6.0.1 | A53 | Define the Flit Error Counter Interrupt Enable bit in the Flit Error Counter Control Register. |
| 6.0.1 | A62 | Clarify OHC rules. |
| 6.0.1 | A67 | Training Set Corrections: <br> - Clarify equalization fields in TS0 Ordered Sets (see § Table 4-38). |
| 6.0.1 | A73 | Modified TS1/TS2 corrections |
| 6.1 | A392 | Clarify End-to-End TLP Prefix Support indications to software. |
| 6.1 | A393 | Corrections to Flow Control rules <br> - To clarify that when [Merged] is used, distinct UpdateFCs are sent for Posted and Completion credits. This provides buffer consumption visibility to the transmitter allowing a vendor-specific Quality of Service (QoS) mechanism to be implemented. <br> - Clarify definition of FC Unit Size <br> - Require consistency across VCs for shared credits - for example, if one VC advertises [Infinite.3], all VCs must also advertise it <br> - Update minimum flow control credit rules. <br> - Clarify scale factor rules when [Zero] or [Merged] are used. <br> - Update § Equation 2-8 <br> - Add § Equation 2-9 <br> - Update § Equation 2-10 <br> - Add § Equation 2-11 <br> - Update § Equation 2-16 <br> - Add § Equation 2-17 and § Equation 2-18 |
| 6.2 | A531 | Correct § Figure 6-64 "IDE TLP Prefix (NFM)" and clarify text. |
| 6.2 | A540 | Corrections to Equalization Phase 1 rules. |
| 6.2 | A544 | Corrections to Flit Ack and Nak rules. |
| 6.2 | A577 | Define EIE pattern for Retimers for 1b/1b encoding. |
| 6.2 | A578 | Required modifications for Retimer timeouts for 64.0 GT/s. |
| 6.2 | A587 | Correct inconsistencies between decimal and binary values listed in § Table 2-5 "Flit Mode TLP Header Type Encodings". |

| Revision | Errata | Description |
| :--: | :--: | :-- |
| 6.3 | A656 | Sending NOP Flits with explicit sequence number set to NEXT_TX_FLIT_SEQ_NUM - 1 during Replay could <br> cause issues at the far end receiver, especially if next Flit has an implicit sequence number. |
| 6.3 | A687 | IMPLICIT_RX_FLIT_SEQ_NUM Rules must ignore invalid Flits. |

# Important Errata and Approved ECNs 

| Revision | Errata / ECN | Description |
| :--: | :--: | :-- |
| 6.0 .1 | B5 | Clarify value of the Alternate Protocol Count field in the Alternate Protocol Capabilities Register. |
| 6.0 .1 | B7 | Incorrect capability name used in the description of the Capability ID field of Lane Margining at the <br> Receiver Extended Capability Header. |
| 6.0 .1 | B8 | Clarify that behavior is undefined when Message Data Register for MSI low bits conflict with the <br> MME setting. |
| 6.0 .1 | B10 | A single PCI Express Function is permitted to contain multiple VSEC structures. |
| 6.0 .1 | B11 | Clarify Retimer Loopback behavior. |
| 6.0 .1 | B12 | Recommend that parity errors in Control SKP OS be checked only when immediately preceded by a <br> Data Block. |
| 6.0 .1 | B13 | Clarify Alternate Protocol Negotiation Status error values. |
| 6.0 .1 | B14 | Define what it means for Scaled Flow Control to be "activated". |
| 6.0 .1 | B15 | Margining Ready applies to speeds above 16.0 GT/s. |
| 6.0 .1 | B16 | Update Link Number encoding in § Table 4-37. |
| 6.0 .1 | B17 | Add Implementation Note: Implementation Note: Delays in Data Link Layer Link Active Reflecting <br> Link Control Operations |
| 6.0 .1 | B18 | Clarify Receiver Impedance Propagation Rules. |
| 6.0 .1 | B21 | Update recommended behavior on transitions from Hot Reset to Detect.Active. |
| 6.0 .1 | B22 | Clarify Flit Mode poison rules. |
| 6.0 .1 | B23 | Shrink figures § Figure 3-9 and § Figure 3-10 so they're not cut off. <br> - Redraw § Figure 4-27 so it's readable. |

![img-0.jpeg](03_Knowledge/Tech/PCIe/00_Contents/img-0.jpeg)

Figure 1 Old Figure: Flit Mode and Non-Flit Mode processing with 8b/10b and 128b/130b encoding on the Transmit side
![img-1.jpeg](03_Knowledge/Tech/PCIe/00_Contents/img-1.jpeg)

Figure 2 New Figure: Flit Mode and Non-Flit Mode processing with 8b/10b and 128b/130b encoding on the Transmit side

- Redraw $\S$ Figure 4-28 so it's readable.
![img-2.jpeg](03_Knowledge/Tech/PCIe/00_Contents/img-2.jpeg)

Figure 3 Old Figure: Flit Mode and Non-Flit Mode processing with 8b/10b and 128b/130b encoding on the Receive side

| Revision | Errata / ECN | Description |
| :--: | :--: | :--: |
|  |  | ![img-3.jpeg](03_Knowledge/Tech/PCIe/00_Contents/img-3.jpeg) |

Figure 4 New Figure: Flit Mode and Non-Flit Mode processing with 8b/10b and 128b/130b encoding on the Receive side

| 6.0.1 | B24 | Lane Margining at the Receiver Corrections |
| :--: | :--: | :-- |
| 6.0.1 | B25 | Define FLIT in Terms and Acronyms |
| 6.0.1 | B26 | Completion Timeout Ranges Supported, Completion Timeout Disable Supported, and Completion Timeout <br> Value only apply to Non-Posted Requests |
| 6.0.1 | B28 | Requester must accept any Segment number in completions. |
| 6.0.1 | B29 | TC field must be 000b in § Figure 2-72, § Figure 2-74, § Figure 2-76, and § Figure 2-78. <br> Type field was incorrect in § Figure 2-74 and § Figure 2-78. |
| 6.0.1 | B30 | Routing field was incorrect in § Table 2-36 IDE Messages. |
| 6.0.1 | B31 | Clarify origins of $T_{r s d}$ value of 1 ms. |
| 6.0.1 | B34 | § Table 4-34 TS1 Ordered Set in 8b/10b and 128b/130b Encoding: Symbol 4, Bit 7 had the wrong <br> LTSSM state for the speed_change usage. |
| 6.0.1 | B40 | Update the exponents of $\alpha$ in § Figure 4-56. $\alpha^{85}$ and $\alpha^{84}$ changed to $\alpha^{84}$ and $\alpha^{83}$ respectively. <br> Update exponents of $\alpha$ in Column $B^{0}$ in § Figure 4-57. $\alpha^{85}$ through $\alpha^{92}$ changed to $\alpha^{84}$ through $\alpha^{81}$ <br> respectively. |

| Revision | Errata / ECN | Description |
| :-- | :-- | :-- |


|  | $B_{0}$ | $\cdots$ | $B_{82}$ | $B_{83}$ | $B_{04}$ | $B_{05}$ |
| :--: | :--: | :--: | :--: | :--: | :--: | :--: |
| 0 | $a^{83}$ | $\cdots$ | $a^{2}$ | $a$ | 1 | $p_{0}$ |
| 1 | $a^{86}$ | $\cdots$ | $a^{3}$ | $a^{2}$ | $a$ | $p_{1}$ |
| 2 | $a^{87}$ | $\cdots$ | $a^{4}$ | $a^{3}$ | $a^{2}$ | $p_{2}$ |
| 3 | $a^{88}$ | $\cdots$ | $a^{5}$ | $a^{4}$ | $a^{3}$ | $p_{3}$ |
| 4 | $a^{89}$ | $\cdots$ | $a^{6}$ | $a^{5}$ | $a^{4}$ | $p_{4}$ |
| 5 | $a^{90}$ | $\cdots$ | $a^{7}$ | $a^{6}$ | $a^{5}$ | $p_{5}$ |
| 6 | $a^{91}$ | $\cdots$ | $a^{8}$ | $a^{7}$ | $a^{6}$ | $p_{6}$ |
| 7 | $a^{92}$ | $\cdots$ | $a^{9}$ | $a^{8}$ | $a^{7}$ | $p_{7}$ |

Figure 5 Old Figure: Powers of alpha for the check bits for Bytes 0 to 84

|  | $B_{0}$ | $\cdots$ | $B_{82}$ | $B_{83}$ | $B_{04}$ | $B_{05}$ |
| :--: | :--: | :--: | :--: | :--: | :--: | :--: |
| 0 | $a^{84}$ | $\cdots$ | $a^{2}$ | $a$ | 1 | $p_{0}$ |
| 1 | $a^{85}$ | $\cdots$ | $a^{3}$ | $a^{2}$ | $a$ | $p_{1}$ |
| 2 | $a^{86}$ | $\cdots$ | $a^{4}$ | $a^{3}$ | $a^{2}$ | $p_{2}$ |
| 3 | $a^{87}$ | $\cdots$ | $a^{5}$ | $a^{4}$ | $a^{3}$ | $p_{3}$ |
| 4 | $a^{88}$ | $\cdots$ | $a^{6}$ | $a^{5}$ | $a^{4}$ | $p_{4}$ |
| 5 | $a^{89}$ | $\cdots$ | $a^{7}$ | $a^{6}$ | $a^{5}$ | $p_{5}$ |
| 6 | $a^{90}$ | $\cdots$ | $a^{8}$ | $a^{7}$ | $a^{6}$ | $p_{6}$ |
| 7 | $a^{91}$ | $\cdots$ | $a^{9}$ | $a^{8}$ | $a^{7}$ | $p_{7}$ |

Figure 6 New Figure: Powers of alpha for the check bits for Bytes 0 to 84

| 6.0 .1 | B44 | Extended Synch is not used for L0s in Flit Mode, but is still relevant for other purposes. |
| :-- | :-- | :-- |
| 6.0 .1 | B45 | Add 64.0 GT/s encoding to Enable SKP OS Generation Vector. |
| 6.0 .1 | B48 | Clarify 1b/1b encoding EIOSQ terminology in Compliance and Modified Compliance Patterns. |
| 6.0 .1 | B49 | Execute Requested is reserved in all Memory Requests other than Untranslated Memory Read <br> Requests. |
| 6.0 .1 | B50 | Typo in units column of $\S$ Table 8-16, Parameter T T X-CH-UPW-RJ-64G |

| Revision | Errata / ECN | Description |
| :--: | :--: | :--: |
| 6.0.1 | B51 | - Typo in units column of § Table 8-18, Parameter Z $\mathrm{Z}_{\text {C-DC }}$ <br> - Locate artwork for § Figure 8-86 |
| 6.0.1 | B54 | Don't send Selective IDE Stream IDE Sync and IDE Fail messages unless the V bit is Set for that RID Base. |
| 6.0.1 | B55 | The "subsequent IDE TLPs" error reporting language applies regardless of how Insecure was reached. |
| 6.0.1 | B56 | Selective IDE Stream Enable and Link IDE Stream Enable are edge triggered. |
| 6.0.1 | B58 | The Selective IDE Stream Control Register, Default Stream field only applied to Selective IDE Streams. |
| 6.0.1 | B59 | Routed to Root Complex is permitted only when the Partner Port is a Root Port, as indicated by the Default Stream bit being Set. |
| 6.0.1 | B60 | Clarify rules for selecting the Selective IDE Stream for a given TLP. |
| 6.0.1 | B64 | Clarify Segment number processing rules in Flit Mode Completer Transaction ID processing. |
| 6.0.1 | B66 | The Data Link Feature Exchange Enable field was renamed to Data Link Feature Exchange Is Enabled. <br> This errata also applies to [PCIE-5.0]. |
| 6.0.1 | B68 | Correct Type field value in § Figure 10-13 (was 0000 0000b should be 0000 0011b). |
| 6.0.1 | B69 | In Shared Flow Control Usage Limit Enable, clarify wording to indicate which Shared Flow Control Usage Limit is affected (duplicate field names in VC Resource Control Register and MFVC VC Resource Control Register). |
| 6.0.1 | B70 | DC Balance correction in 1b/1b encoding of T50, TS1, and TS2 |
| 6.0.1 | B71 | Consolidate description of 1b/1b behavior for SKP Ordered Sets |
| 6.0.1 | B72 | TS2 Symbol 6, operating at 2.5 or $5.0 \mathrm{GT} / \mathrm{s}$ and Requesting equalization $32.0 \mathrm{GT} / \mathrm{s}$ encoding is only for $32.0 \mathrm{GT} / \mathrm{s}$ (was " $32.0 \mathrm{GT} / \mathrm{s}$ or higher") |
| 6.0.1 | B75 | Clarify behavior in CMA-SPDM Rules. |
| 6.0.1 | B77 | Update artwork for § Figure 6-79. |
| 6.0.1 | B79 | In Flit Mode, the 16.0 GT/s Local Data Parity Mismatch Status Register, 16.0 GT/s First Retimer Data Parity Mismatch Status Register, and 16.0 GT/s Second Retimer Data Parity Mismatch Status Register are used at all 128b/130b and 1b/1b data rates. |
| 6.0.1 | B81 | Clarify 128b/130b Control and Standard SKP Alternation Rule interactions with LOp |
| 6.0.1 | B82 | Editorial: SRIS_Mode_Enabled is a variable, not a bit. |
| 6.0.1 | B83 | Define CXL Src bit in ATS Translation Requests. This is bit 3 in byte 15 in § Figure 10-10, § Figure 10-11, § Figure 10-12, and § Figure 10-13. Editorial change in § Table 10-3. |
| 6.0.1 | B85 | Loopback Follower changes |

| Revision | Errata / ECN | Description |
| :--: | :--: | :--: |
| 6.0.1 | B86 | - § Table 4-37 Equalization Byte 0 correction (Symbols 1,9) <br> - § Table 4-35 Symbol 68.0 GT/s should be 8.0 GT/s or higher <br> - § Section 4.2.7.4.4, Width change rule change, change "128b/138b" to "128b/130b or 1b/ 1b" (3 places) |
| 6.0.1 | B87 | Update Recovery.RcvrLock behavior when hardware autonomous equalization is not adopted |
| 6.0.1 | B88 | Define 1b/1b Phy Payload type Alternation Rule |
| 6.0.1 | B89 | - Change name of LOp Supported capability bit (was Receiver LOp Supported) <br> - Clarify Target Link Width behavior <br> - Clarify LOp.Priority behavior |
| 6.0.1 | B90 | Clarify Receiver Framing Requirements (including LOp in Flit Mode) |
| 6.0.1 | B92 | Clarify that the LTSSM must not advertise speeds above $32.0 \mathrm{GT} / \mathrm{s}$ in Polling.Active and Polling.Configuration. During those states, negotiation for greater than $32.0 \mathrm{GT} / \mathrm{s}$ is occuring. |
| 6.0.1 | B93 | Add implementation note "Reject Coefficient Values with TS0 Ordered Sets" in § Section 4.2.7.4.2.2.1. |
| 6.0.1 | B94 | Attr[2] was incorrectly shown as Reserved in § Figure 10-6, § Figure 10-7, § Figure 10-10, and § Figure 10-11. |
| 6.0.1 | B95 | Clarify historical timestam invalidation behavior in § Section 6.21.3.2 . |
| 6.0.1 | B96 | Correct the register width of the Root Capabilities Register, § Table 7-31. Was 32 bits, but the register is actually 16 bits wide. |
| 6.0.1 | B98 | Update § Figure 7-228 and § Table 7-207 to better reflect that the Virtual Channel Extended Capability uses Capability ID 0002h or 0009h. |
| 6.0.1 | B99 | Clarify that intermediate receivers should not check crossing 4 KB boundaries. Implementing this check could invalidate such silicon changes for future TLP Type definitions (e.g., such future TLP Types could be similar to the existing Atomic CAS where the relationship between the TLP Length field and the affected memory range is not 1:1). |
| 6.0.1 | B100 | Clarify that LOp is supported at all data rates. |
| 6.0.1 | B102 | Segment was erroneously left out of IDE RID Association mechanism |
| 6.0.1 | B103 | Clarify IDE TLP Aggregation rules. See § Section 6.33.6 . |
| 6.0.1 | B104 | Add implementation note SKP Ordered Sets in a Data Stream in Flit Mode to § Section 4.2.8.5 . |
| 6.0.1 | B106 | Clarify the FM/NFM rules for PCRC. |
| 6.0.1 | B107 | Clarify that IDE TLPs in FM always have OHC-C. |
| 6.0.1 | B108 | CMA-SPDM state should not be affected by FLR. |
| 6.0.1 | B111 | Clarify Retimer response for Access Retimer Register command. |
| 6.0.1 | B112 | Add implementation note Security Issues Associated with Non-Enabled Bytes. |

| Revision | Errata / ECN | Description |
| :--: | :--: | :--: |
| 6.0.1 | B113 | The following figures incorrectly described reserved bits as RsvdP that should be RsvdZ. some of these were also incorrect in (PCIE-5.0) but were correct in (PCIe-4.0). <br> - § Figure 7-32 - Slot Status Register <br> - § Figure 7-124 - Device Status 3 Register <br> - § Figure 7-381 - Link IDE Stream Status Register <br> - § Figure 7-384 - Selective IDE Stream Status Register |
| 6.0.1 | B114 | Add new § Section 4.2.18.3 describing Lane Margining contents for Flit Mode Control SKP Ordered Sets at $8.0 \mathrm{GT} / \mathrm{s}$. |
| 6.0.1 | B115 | Clarify the Variant bit rules in § Section 2.7.1 . |
| 6.0.1 | B116 | OHC-A1 is also used for Route to Root Complex Messages (e.g., Page Request Messages) and for Translation Requests that Set NW |
| 6.0.1 | B117 | Clarify that "overflow" for the PR Received Counters (NPR/CPL) means the 64b counter itself overflows. |
| 6.0.1 | B118 | Clarify that, with system support for DRS, Devices are permitted to take longer than 1 second to become Configuration-Ready. |
| 6.0.1 | B119 | Clarify text in Segment Captured bit description. |
| 6.0.1 | B120 | When the length of an ATS Request is improper, the result should be undefined, not a Malformed TLP. |
| 6.0.1 | B121 | Clarify TLP Prefix Processing rules for Flit Mode. |
| 6.0.1 | B122 | Clarify completion rules for TLPs with Reserved Type field values. |
| 6.0.1 | B123 | Deprecate Flit Mode TLP Suffixes. They were unused and have latency concerns. |
| 6.0.1 | B124 | Clarify that Equalization Bypass to Highest NRZ Rate Disable is optional. |
| 6.0.1 | B127 | Clarify LOp Framing Error rule. Clarify LOp retimer behavior. |
| 6.0.1 | B128 | Update the Compliance Pattern for 1b/1b operation. |
| 6.0.1 | B130 | Clarify Loopback.Active language. |
| 6.0.1 | B131 | - Deprecate Report Longest Burst vs First Burst <br> - Flit Error Counter does not roll over <br> - Introductory text in § Section 7.7.8.7 describes all FBER Measurement Status Registers (i.e., FBER Measurement Status 1 Register through FBER Measurement Status 10 Register) <br> - Remove Pseudo Port wording in Lane \#0 Correctable Counter (also applies to the rest of the Lane counters). |
| 6.0.1 | B132 | Correct Tag field usage in Messages and Vendor-Defined Messages. <br> - Message byte 6 is Reserved unless specifically defined. <br> - Reserved bits must be copied intact during translation to/from Flit Mode and Non-Flit Mode. |

| Revision | Errata / ECN |                                                                                                                                                                                                                          Description                                                                                                                                                                                                                          |
| :------: | :----------: | :-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------: |
|          |              | - Change wording for byte 6 of Non-Flit Mode Messages $\S$ Figure 2-49. <br> - Change wording for byte 6 of Flit Mode Messages $\S$ Figure 2-50. <br> - Low 7 bits of byte 6 are available for use in Vendor-Defined Messages. <br> - Change wording for byte 6 of Non-Flit Mode Vendor-Defined Messages $\S$ Figure 2-53 <br> - Change wording for byte 6 of Flit Mode Vendor-Defined Messages $\S$ Figure 2-54 <br> This errata also applies to [PCIE-5.0]. |
|   6.1    |     B305     |                                                                                                                                            Clarify flit error counting Behavior <br> - Events to Count field of the Flit Error Counter Control Register <br> - $\S$ Section 4.2.3.4.2 <br> - $\S$ Section 4.2.5.1                                                                                                                                             |
|   6.1    |     B306     |                                                                                                                                                                                                              Electrical Idle exit timing changes                                                                                                                                                                                                              |
|   6.1    |     B308     |                                                                                                                                                                           Clarify implementation note Detection of Improper Reordering in IDE TLP Sub-Streams (\$ Section 6.33.5 )                                                                                                                                                                            |
|   6.1    |     B309     |                                                                                                                                                                                                     Support 64.0 GT/s in Loopback. Entry and Detect.Quiet                                                                                                                                                                                                     |
|   6.1    |     B310     |                                                                                                                                                                                     Clarify Recovery.RcvrLock, Recovery.RcvrCfg, Recovery.Speed, and Recovery.Idle rules                                                                                                                                                                                      |
|   6.1    |     B311     |                                                                                                                                                                                                            Text was misplaced in Recovery.RcvrCfg                                                                                                                                                                                                             |
|   6.1    |     B312     |                                                                                                                                                                                                                           LOp rules                                                                                                                                                                                                                           |
|   6.1    |     B314     |                                                                                                                                                                                                            Lane Numbering matching rules in 1b/1b                                                                                                                                                                                                             |
|   6.1    |     B315     |                                                                                                                                                                                                        Centralize text describing Default Lane numbers                                                                                                                                                                                                        |
|   6.1    |     B316     |                                                                                                                                                                                                           IDE Terminus rules for Switch / Root Port                                                                                                                                                                                                           |
|   6.1    |     B317     |                                                                                                                                                                                               Add implementation note Determination of Slot Number Information                                                                                                                                                                                                |
|   6.1    |     B319     |                                                                                                                                                                     - Update Symbol Time definition for 1b/1b encoding <br> - Update Retimer Latency Limit values for SRIS \$ Table 4-77                                                                                                                                                                      |
|   6.1    |     B320     |                                                                                                                                                                                                    Provide Test Keys for testing IDE in $\S$ Section L. 5                                                                                                                                                                                                     |
|   6.1    |     B322     |                                                                                                                                                                                                    Recovery.RcvrLock to Recovery. Equalization transition                                                                                                                                                                                                     |
|   6.1    |     B323     |                                                                                                                                                                                     SRIS Clocking bit is also meaningful in Flit Mode with 8b/10b and 128b/130b encoding                                                                                                                                                                                      |
|   6.1    |     B325     |                                                                                                                                                                                                                   Recovery.Idle to Loopback                                                                                                                                                                                                                   |
|   6.1    |     B326     |                                                                                                                                                                                                       Configuration.Linkwidth.Start rules for 64.0 GT/s                                                                                                                                                                                                       |
|   6.1    |     B328     |                                                                                                                                                                                                       Clarify Requester Segment field behavior in OHC-C                                                                                                                                                                                                       |
|   6.1    |    B329a     |                                                                                                                                                                                                  Configuration Requests cannot map to the Default IDE Stream                                                                                                                                                                                                  |

| Revision | Errata / ECN | Description |
| :--: | :--: | :--: |
| 6.1 | B330 | Clarify definition of Flit halves |
| 6.1 | B331 | Corrections to EP and Length fields of the following messages: <br> - § Figure 10-22 <br> - § Figure 10-24 <br> - § Figure 10-26 <br> - § Figure 10-28 <br> - § Figure 2-72 <br> - § Figure 2-74 <br> - § Figure 2-76 <br> - § Figure 2-78 |
| 6.1 | B332 | Function Level Reset clarification |
| 6.1 | B335 | Recovery.RcvrLock transmitter equalization coefficients |
| 6.1 | B336 | EIEOS inference behavior only occurs when the LTSSM rules already allow entry to Recovery |
| 6.1 | B338 | Define terms Endpoint Upstream Port and Switch Port. |
| 6.1 | B340 | Clarify rules for where a PASID Extended Capability is permitted and define associated behavior. |
| 6.1 | B341 | Errata against TDISP ECN-Link-Activation-07-Dec-2017 <br> Poisoned TLP rules in TDISP |
| 6.1 | B342 | Returning TC0/VC0 to secure state in Link IDE |
| 6.1 | B344 | TEE rules when not using TDISP |
| 6.1 | B345 | Remove confusing and unnecesary text regarding CMA-SPDM |
| 6.1 | B346 | Remove confusing and unnecesary text regarding CMA-SPDM |
| 6.1 | B347 | Update § Figure 6-63 to recommend setting IDE Enable last when programming keys. Add text to strongly recommend this behavior while permitting otherwise. |
| 6.1 | B348 | Errata against TDISP ECN <br> DOE errors don't usually impact TDISP |
| 6.1 | B349 | ERRATA against TDISP ECN <br> Add examples applicable IDE errors. |
| 6.1 | B353 | Translation Requests always contain OHC-A1 as they always contain the NW bit. |
| 6.1 | B354 | Correct naming of the Recieved IDE Fail Message in Link IDE Stream Status Register and Selective IDE Stream Status Register |
| 6.1 | B355 | Clarify requirements on system software behavior doing IDE enablement. |
| 6.1 | B356 | Update precoding behavior |

| Revision | Errata / ECN | Description |
| :--: | :--: | :--: |
| 6.1 | B357 | Clarify Alternate Protocol Negotiation behavior |
| 6.1 | B358 | Add implmentation note Handling TLPs Spanning Multiple Flits |
| 6.1 | B359 | Clarify wording for Gray coding of DC balance symbol |
| 6.1 | B360 | Clarify K_SET_GO behavior |
| 6.1 | B361 | Errata against TDISP ECN <br> Reword $\S$ Section 11.2.1 to reflect T-Bit behavior required by TDISP |
| 6.1 | B363 | Flit Mode Status has different behavior for Upstream and Downstream Ports |
| 6.1 | B365 | Clarify precoding text for $64.0 \mathrm{GT} / \mathrm{s}$ |
| 6.1 | B367 | Clarify All VCs Enabled wording in the Port VC Control Register and MFVC Port VC Control Register |
| 6.1 | B369 | Add rules in $\S$ Section 6.33 .8 |
| 6.1 | B370 | Clarify Latency Tolerance Rporting behavior when entering and exiting DO |
| 6.1 | B373 | Clarify Retimer rules for Hot Reset |
| 6.1 | B374 | Clarify rules for Loopback.Entry |
| 6.1 | B375 | Clarify rules for Loopback.Entry |
| 6.1 | B376 | Clarify wording in Phase 0 and Phase 1 of Transmitter Equalization |
| 6.1 | B377 | Clarify rules for Loopback.Entry |
| 6.1 | B378 | Clarify Ordered Set Error Injection behavior |
| 6.1 | B381 | Clarify Local TLP Prefix rules in Flit Mode TLP Grammar |
| 6.1 | B382 | Correct uniqueness rules for Transaction IDs |
| 6.1 | B384 | Recovery.Speed corrections |
| 6.1 | B385 | Correct Flit Ack, Nak, and Discard rules |
| 6.1 | B386 | Add $64.0 \mathrm{GT} / \mathrm{s}$ to Recovery.RcvrLock rule |
| 6.1 | B388 | Framing Error in the context of $\S$ Section 4.2.5.8 is only for Non-Flit Mode |
| 6.1 | B394 | Update Configuration Request Routing Rules for IDE |
| 6.1 | B395 | K_SET_GO or K_SET_STOP behavior with an invalid Stream ID |
| 6.1 | B397 | LOp beahvior when an EIEOSQ is scheduled near an SDS Ordered Set |
| 6.1 | B398 | Flit Sequence Number and Retry Mechanism |
| 6.1 | B405 | VF Enable behavior |
| 6.1 | B406 | Clarify rules for Local TLP PRefixes and Lpcal TLPs |
| 6.1 | B407 | Clarify L0 behavior when receiving EIOS behavior (interaciton with LOp) |

| Revision | Errata / ECN | Description |
| :--: | :--: | :--: |
| 6.1 | B408 | Flit Sequence Number rules |
| 6.1 | B409 | In § Section 4.2.7.4.4, the LTSSM must not initiate a width change if speed_change is set to 1b |
| 6.1 | B412 | Errata to TDISP ECN <br> FLR to Functions other than Function 0 do not affect SPDM or IDE streams. |
| 6.1 | B414 | Errata to UIO ECN <br> TC to VC Mapping rules |
| 6.1 | B415 | Behavior for L0s in Flit Mode |
| 6.1 | B416 | Clarify wording around Hot and Warm Reset |
| 6.1 | B418 | Recommend software recovery procedure for use when the page request queue overflows <br> This Errata is part 1 of 10 that constitute ATS 1.2 |
| 6.1 | B419 | U-bit will eventually be deprecated <br> This Errata is part 2 of 10 that constitute ATS 1.2 |
| 6.1 | B420 | Address space overlap clarification <br> This Errata is part 3 of 10 that constitute ATS 1.2 |
| 6.1 | B421 | ITag uniqueness rules <br> This Errata is part 4 of 10 that constitute ATS 1.2 |
| 6.1 | B422 | ATS and PRI interactions with Shadow Functions <br> This Errata is part 5 of 10 that constitute ATS 1.2 |
| 6.1 | B423 | ATS Translation Completion Status updates <br> This Errata is part 6 of 10 that constitute ATS 1.2 |
| 6.1 | B425 | Invalidate Queue Depth, Page Aligned Request, and Global Invalidate Supported updates <br> This Errata is part 7 of 10 that constitute ATS 1.2 |
| 6.1 | B426 | Execute Requested update <br> This Errata is part 8 of 10 that constitute ATS 1.2 |
| 6.1 | B427 | Execute Permission Supported update <br> This Errata is part 9 of 10 that constitute ATS 1.2 |
| 6.1 | B428 | ATS Enable update <br> This Errata is part 10 of 10 that constitute ATS 1.2 |

| Revision | Errata / ECN | Description |
| :--: | :--: | :--: |
| 6.1 | B429 | Scaled Flow Control updates |
| 6.1 | B430 | Data Link Feature is required in Flit Mode |
| 6.1 | B431 | Errata against UIO ECN: <br> Remove the sentence "Because UIO can only be enabled when end-to-end UIO support exists, it is never necessary for the Root Complex to take ownership of UIO Requests." from the Implementation Note Root Complex Support for peer-to-peer Non-Posted Memory Transactions that Traverse Hierarchies. |
| 6.1 | B432 | Mandate capacitor placement on the Transmit end of a Link. |
| 6.1 | B433 | Clarify valid tag values for 14-bit tags. |
| 6.1 | B434 | Clarify rules for Switch FM to NFM translation. |
| 6.1 | B435 | Address Routed Message corrections in Flit Mode. |
| 6.1 | B436 | Clarification of Tag keep-out ranges. |
| 6.2 | B500 | Clarify rules for PASID application. |
| 6.2 | B501 | Clarify rules for Address Routed Messages. |
| 6.2 | B502 | Clarify OHC-A5 requirements for Selective IDE Completions. |
| 6.2 | B503 | Remove needless indirection regarding requirement that VFs must not implement PASID Extended Capability. |
| 6.2 | B506 | Clarify rules for TDI regarding MSI/MSI-X. |
| 6.2 | B507 | Errata B507: Remove Implementation Note "FUTURE TEE EXTENSIONS": TEE extensions for sub-function I/O-virtualization techniques will be covered in a future revision of this specification. |
| 6.2 | B508 | Remove unnecessary restriction on VC1 in SVC. |
| 6.2 | B510 | Correct typo in Recovery.RcvrCfg. |
| 6.2 | B512 | Clarify application of IDE Default Stream to Translation Requests and Untranslated Memory Requests. |
| 6.2 | B513 | Clarify application of ordering rules for Flow-Through Selective IDE. |
| 6.2 | B515 | Clarify Flit Performance Measurement mechanisms. |
| 6.2 | B515a | Clarify Segment rules for Flit Mode Requesters/Completers within an RC. |
| 6.2 | B517 | Correct \$ Figure 6-46 "CMA-SPDM as Part of a Layered Architecture". |
| 6.2 | B518 | Correct use of "Precision Time Measurement". |
| 6.2 | B520 | Clarify Phase 1 of Transmitter Equalization text. |
| 6.2 | B522 | Correct paragraph alignment. |
| 6.2 | B524 | Clarify rules for EQ TS2 Ordered Set use. |
| 6.2 | B525 | Add LOp register cross-references. |

| Revision | Errata / ECN | Description |
| :--: | :--: | :--: |
| 6.2 | B529 | Clarify earmarked TLP handling. |
| 6.2 | B535 | FLIT_REPLAY_NUM clarifications. |
| 6.2 | B536 | Clarify Segment Base programming for certain scenarios. |
| 6.2 | B537 | Clarify rules for Selective IDE for Configuration Requests. |
| 6.2 | B538 | Clarify Privileged Mode Requested and Execute Requested/Execute Permitted rules corrupted during Revision 6.0 development. |
| 6.2 | B541 | Clarify LOp request handling rules. |
| 6.2 | B546 | Clarify figures and text regarding TLP Header Byte 6 for Message Requests. <br> The following NFM Message Request Header figures in § Section 2.2.8 have byte 6 labeled as "Tag". Change the label to "R" or "Reserved" (based on what fits). Note: Figures are automatically generated and these changes are not marked in the document. <br> - § Figure 2-51 <br> - § Figure 2-55 <br> - § Figure 2-63 <br> - § Figure 2-65 <br> - § Figure 2-67 <br> - § Figure 2-68 |
| 6.2 | B547 | Clarify AT field requirements for Messages Routed by Address. |
| 6.2 | B548 | Clarify MMB Capabilities Register language. |
| 6.2 | B549 | Clarify handling of received DMWr Requests. |
| 6.2 | B550 | Clarify and cross-reference existing rules regarding Segment exceptions for Root Ports. |
| 6.2 | B551 | Clarify SKP Ordered Set rules with LOp. |
| 6.2 | B552 | Correct omission of T50 in rules for Phase 1 of Transmitter Equalization. |
| 6.2 | B553 | Clarify text regarding Electrical Idle Sequences on entry to Recovery.RcvrLock. |
| 6.2 | B554 | Clarify Autonomous Change / Selectable De-emphasis for TS1/TS2 Ordered Set with 1b/1b Encoding. |
| 6.2 | B555 | Clarify content of TS2 Ordered Set with 1b/1b Encoding. |
| 6.2 | B556 | Clarify handling of NOP2 DLLP during equalization. |
| 6.2 | B557 | Clarify Flit Replay Transmit rules. |
| 6.2 | B559 | UIO clarifications. |
| 6.2 | B561 | Clarify and cross-reference DMWr capability reporting. |
| 6.2 | B562 | OHC-E clarifications. |
| 6.2 | B564 | Clarify LOp Link width rules. |

| Revision | Errata / ECN | Description |
| :--: | :--: | :--: |
| 6.2 | B565 | Clarify rules for handling an invalid Flit Sequence Number in a received Ack Flit or Nak Flit. |
| 6.2 | B566 | Clarify Retimer data rate change and determination rules. |
| 6.2 | B568 | Correct Bad DLLP entry in § Table 6-4 "Data Link Layer Error List". |
| 6.2 | B569 | Clarify handling of ID Routed Messages targeting a Function that is not implemented. |
| 6.2 | B571 | Correct figures to reduce the Key Sub-Stream field width to 3 bits. This affects: <br> - § Figure 6-57 <br> - § Figure 6-58 <br> - § Figure 6-59 <br> - § Figure 6-60 <br> - § Figure 6-61 |
| 6.2 | B572 | Clarify rules for implementing PTM Extended Capability. |
| 6.2 | B573 | Clarify Data Stream, and rules for chosing Flit Mode vs. Non-Flit Mode. |
| 6.2 | B575 | Clarify Half Scrambling |
| 6.2 | B576 | Add Implementation Note: Forwarding D21.3 Symbol with Incorrect Disparity. |
| 6.2 | B580 | Clarify rules to detect an SDS. |
| 6.2 | B581 | Add Implementation Note Orthogonality of L0p and L1/L2 |
| 6.2 | B583 | Clarify definition of UIO TLPs. |
| 6.2 | B583a | Clarify that Translation Requests are not defined for UIO Memory Reads. |
| 6.2 | B585 | Correct section references. |
| 6.2 | B586 | Clarify definition of Idle Flit, Nop Flit, and Payload Flit. |
| 6.2 | B588 | DPC doesn't invent Completions for UIO Requests. |
| 6.2 | B595 | Clarify Larger Tags rules. |
| 6.2 | B599 | Clarify Precoding negotiaion. |
| 6.3 | B600 | Effect of Detect on Precoding |
| 6.3 | B601 | Population of TS1/TS2 Ordered Set fields during L0p |
| 6.3 | B602 | Retimer changes to Enter Compliance Rules |
| 6.3 | B603 | Correct Flit Layout figures to use Symbol Times instead of UI. With PAM4, UI was no longer accurate. |
| 6.3 | B604 | Add Transmitter Preset rules for Phase 0 of Transmitter Equalization when sending TS0 Ordered Sets |
| 6.3 | B605 | Change label for rightmost block in § Figure 4-22 from "PAM4 voltage Conversion to 2-bit aligned" to "2-bit aligned to PAM-4 voltage Conversion" <br> Update fonts in § Figure 4-22 and § Figure 4-23 |

| Revision | Errata / ECN | Description |
| :--: | :--: | :--: |
| 6.3 | B606 | Clarify TS0 rules for Phase 0 of Transmitter Equalization <br> TS0s don't have the Reject Coefficient Values bit, so references to setting it need to be qualified by TS1 Ordered Sets, and the text needs to say what happens when transmitting TS0s. |
| 6.3 | B607 | Clarify rules for determining behavior for coalesced UIO Completions with mixed Completions Status values |
| 6.3 | B608 | Correction of Electrical Idle time rules in Polling.Compliance |
| 6.3 | B616 | Remove leftover text referring to Receiver Preset Hints (that are only present at 8.0 GT/s). Update text to use correct field names. |
| 6.3 | B617 | Clarify SKP OS behavior in Rules for Transmitters |
| 6.3 | B618 | Define Flit Mode behavior when TPH is used and Byte Enable values do not match the Non-Flit Mode implied values (see § Section 2.2.5.1). |
| 6.3 | B619 | Clarify Alternate Protocol Negotiation when more than one alternate protocol is supported (i.e., PCIe plus two or more alternate protocols). |
| 6.3 | B621 | Defined minimum Receiver rules for detecting Idle Flits. |
| 6.3 | B623 | Clarify behavior when changing VF Enable. Immediate Readiness does not apply to VFs. |
| 6.3 | B624 | Define the terms RefClk, recommended, and strongly recommended |
| 6.3 | B625 | Clarify software rules for interpreting Flit Error Log registers. |
| 6.3 | B626 | Add implementation note Summary of L0p Transmitter/Receiver Behavior. |
| 6.3 | B626a | Clarify LOp Enable rules. <br> Note: This Erratum adds two sentences to the implementation note § Implementation Note: Summary of L0p Transmitter/Receiver Behavior located immediately before § Table 4-53. That change may be marked as part of Erratum B626. |
| 6.3 | B628 | Cleanup terminology regarding Update Flow Control and Optimized_Update_FC |
| 6.3 | B630 | Remove values for fields Frnt and Type in § Figure 10-6 and § Figure 10-7. MRd and MWr are not the only types of Memory Requests. |
| 6.3 | B632 | Flit Latency Tracking Counter unit changed to ns from $\mu \mathrm{s}$. <br> Incomplete integration error of earlier Erratum BS15. This unfortunately creates a situation where a software workaround is needed for Flit Latency Tracking Counter use. |
| 6.3 | B633 | Clarify rules for when N_FTS is meaningful in TS1, TS2, and Modified TS1/TS2 Ordered Sets. |
| 6.3 | B634 | Relax definition of LOp Exit Latency encodings. Indicate that LOp Exit Latency is a hint (e.g., there is no compliance issue if latency is longer). |
| 6.3 | B635 | PASID is permitted on all Memory Requests, including UIO and DMWr. |
| 6.3 | B640 | - Correct § Figure L-4 to match § Table L-2 <br> - Correct § Figure L-8 to match § Table L-4 |

| Revision | Errata / ECN | Description |
| :--: | :--: | :--: |
|  |  | - Update both figures to reflect that Sub-Stream is now a 3 bit field. |
| 6.3 | B641 | Increase Retimer Force Timeout value from 48 ms to 96 ms |
| 6.3 | B642 | In 8b/10b and 128b/130b, the Training Control field is bit encoded (e.g., the Hot Reset bit). In 1b/1b, the Training Control field is encoded. <br> This erratum corrects wording elsewhere in the specification to reflect this difference (e.g., use Hot_Reset_Request which is indicated in two different ways based on data rate). |
| 6.3 | B643 | Correct incorporation error in cross reference (there is no Section 6.99.4). |
| 6.3 | B647 | Add VOL parameter to § Table 12-2 (PESTI DC Specifications) |
| 6.3 | B648 | Add implementation note Rationale for T2wrst to § Section 12.5.4.2. |
| 6.3 | B648a | In § Figure 12-15, update left end of the arrow for timing parameter $T_{13 c 2 s m b}$. |
| 6.3 | B649 | Update caption of § Table 10-2 |
| 6.3 | B650 | Clarify INTx/MSI/MSI-X interrupt wording. |
| 6.3 | B652 | Clarify Precoding behavior in Loopback.Active |
| 6.3 | B653 | Clarify wording for gray coding and precoding of Compliance Pattern in 1b/1b Encoding. |
| 6.3 | B655 | Delete redundant bullet in § Section 4.2.6.7. |
| 6.3 | B657 | Define Flit Mode behavior when receiving TLPs with a Reserved Type encoding. |
| 6.3 | B658 | IDE Fail and IDE Sync messages are not defined in the UIO VC |
| 6.3 | B659 | Clarify Implementation Note TS0 to TS1 Transitions. |
| 6.3 | B661 | NPEM registers are not affected by Function Level Reset |
| 6.3 | B662 | Clarify text indicating that ACS Source Validation does not check Segment Numbers. |
| 6.3 | B665 | PCI-PM is not required for VFs. |
| 6.3 | B666 | Clarify behavior for reserved type encodings in § Table 2-5, Flit Mode TLP Header Type Encodings |
| 6.3 | B667 | Clarify behavior when DOE Object Length is not as expected. |
| 6.3 | B669 | Clarify definition of data payload. |
| 6.3 | B670 | Clarify definition of Physical Function. |
| 6.3 | B671 | Clarify definition of Single-Function Device |
| 6.3 | B672 | Clarify definition of Requester |
| 6.3 | B673 | Clarify software interpretation of the Consecutive Flit Error after the Last Flit Error field. |
| 6.3 | B674 | Refer to tables instead of figures in § Section 2.2.4.2. |
| 6.3 | B675 | Remove outdated text in § Section 6.13 |

| Revision | Errata / ECN | Description |
| :--: | :--: | :--: |
| 6.3 | B676 | Correct Poisoned and Nullified wording in $\S$ Section 4.2.3.4.1 . |
| 6.3 | B677 | Remove PAM4 versions of Lane Margining parameters in § Table 8-13. Move rules into non-PAM4 parameters (i.e., there is only one set of parameters with different behaviors for PAM4 and NRZ). |
| 6.3 | B678 | Clarifications in $\S$ Section 2.2.9.2 - Completion Rules for Flit Mode |
| 6.3 | B679 | In § Section 6.6.2, remove redundant text that explicitly lists Link Equalization Request 16.0 GT/s and 16.0 GT/s Lane Equalization Control Register. Those registers are covered by the subsequent existing text "All registers in the Physical Layer 16.0 GT/s Extended Capability structure". |
| 6.3 | B680 | Correct cross references in $\S$ Section 7.7.3.3 |
| 6.3 | B681 | Define behavior when Extended Synch is Set and LOp is activating Lanes. |
| 6.3 | B682 | Simplify access rules for MMIO Register Blocks in § Section 6.35 . |
| 6.3 | B683 | Clarify Downstream Component Presence behavior. |
| 6.3 | B684 | Clarify Root Complex behavior regarding AtomicOp Requester Enable and AtomicOp Egress Blocking. |
| 6.3 | B685 | Indicate which MSI interrupt vector should be used for Link Equalization Request Interrupt Enable. |
| 6.3 | B686 | Correct inconsistent crosslink behavior between Flit Mode and non-Flit Mode |
| 6.3 | B688 | Clarify Ordered Set modification rules for Retimers. |
| 6.3 | B689 | Correct reference in § Table 7-314 - SFI DRS Received description. |
| 6.3 | B690 | Define term Role-Based Error Reporting. Use it in the definition of the Role-Based Error Reporting bit in the Device Capabilities Register. |
| 6.3 | B691 | Define terms DSP and USP. Global replace DP with DSP and UP with USP. |
| 6.3 | B692 | Update § Figure 2-53 to make symbol 6, bit 7 Reserved. Bits 6:0 remain "(For Vendor Definition)". Only the low 7 bits get copied during translation. This makes it consistent with the existing text: <br> - The low 7 bits of byte 6 is available for vendor definition. Byte 6, bit 7 is Reserved in Non-Flit Mode and is the EP bit in Flit Mode. <br> Update § Figure 2-56 to include the EP bit in symbol 6, bit 7. <br> Update § Figure 2-27 through § Figure 2-31 to define EP in Symbol 6, bit 7 |
| 6.3 | B693 | Use TS0 and TS1 in text that previously only used TS1. |
| 6.3 | B694 | Clarify LOp rules regarding abandoned requests. |
| 6.3 | B695 | UIO Requests always use 14-bit tags. Clarify conflicting text. |
| 6.3 | B696 | Add OHC-C content to § Figure L-3 and § Figure L-7 <br> Update Requester Segment value in § Figure L-8. |
| 6.3 | B697 | Endpoint behavior when recieving an ID Routed Message for an unimplemented Function. |
| 6.3 | B698 | Update pseudocode for RX replay buffer controls in § Section 4.2.3.4.2.1.5 |

| Revision | Errata / ECN | Description |
| :--: | :--: | :--: |
| 6.3 | B699 | Remove text describing what happens when receiving a TS1 in a case where TS1s can't occur. |
| 6.3 | B701 | Clarify Switch and Root Complex rules regarding support for Flow-Through Selective IDE. |
| 6.3 | B704 | Protocol Multiplexing is not supported in Flit Mode. |
| 6.3 | B705 | Clarify Flit Error Counter interrupt behavior. |
| 6.3 | B705a | Clarify Flit Error Counter Enable affects on Flit Error Counter. |
| 6.3 | B706 | Recomend Lane Numbering behavior in the Flit Logging Extended Capability. |
| 6.3 | B707 | Clarify Type 1 Config Request behavior when Selective IDE Stream are in use. |
| 6.3 | B710 | Clarify discard rules for Link IDE. |
| 6.3 | B713 | Clarify Matching Link and Lane Numbers for 1b/1b Encoding behavior for TS2s in Recovery.RcvrCfg. |
| 6.3 | B714 | In § Figure 4-34, replace "MAX_UNACKNOLWEDGED_FLITS" with " 511 " in the two checks so that they read: "(TX_ACKNAK_FLIT_SEQ_NUM - IMPLICIT_RX_FLIT_SEQ_NUM) mod 1023<511". This makes the figure agree with the pseudo code. |
| 6.1 | ECN: TDISP | Incorporate TEE Device Interface Security Protocol (TDISP), Approved July 22, 2022 <br> Minor issues corrected during TDISP incorporation (not individually marked): <br> - Update reserved field width in § Table 11-24 to account for IS_NON_TEE_MEM Range Attribute. <br> - In § Section 11.5.7, table reference corrected to § Table 11-31. <br> - In § Section 11.2 "An example list of architectural configurations registers that should be locked and tracked arespecifiedis shown in § Section 11.2.6." |
| 6.1 | ECN: UIO | Incorporate Unordered IO (UIO), Approved March 16, 2023 |
| 6.1 | ECN: <br> Alt-Protocol-DLLP | Incorporate Alternate Protocol DLLP Reservation, Approved December 14, 2022 <br> Section references in Note 3 of § Figure 3-5 were corrected from the published ECN. |
| 6.1 | ECN: DOE 1.1 | Incorporate Data Object Exchange (DOE), Revision 1.1 Approved September 29, 2022 |
| 6.2 | ECN: 12V-2x6 | Incorporate 12V-2x6 Connector Updates to PCIe Base 6.0 (12V-2x6), Approved August 9, 2023 |
| 6.2 | ECN: MMPT | Incorporate Management Message Passthrough via MMIO Mailbox (MMPT), Approved 2023-09-21 <br> Errata to the ECN since publication are also incorporated: <br> - Added a note that MMB Registers offset 018h-019h are reserved for CXL compatibility. <br> - Added reserved bit definitions to the MMB Capabilities Register, the MMB Control Register, and the MMB Status Register where fields are reserved for CXL compatibility. <br> - Updated the section numbers to align with PCIe Base Spec v6.1. <br> - Updated CXL to [CXL] for notes about legacy compatibility. |
| 6.2 | ECN: <br> Architectural <br> Out-of-Band <br> Management | Incorporate Architectural Out-of-Band Management, Approved 2023-12-12 |

| Revision | Errata / ECN | Description |
| :--: | :--: | :--: |
| 6.2 | ECN: Revised <br> CMA-SPDM | Incorporate Component Measurement and Authentication (CMA-SPDM), Revised December 2022 |
| 6.3 | OHC-E Capability <br> Enumeration | Add a three-bit field OHC-E Support in Device Capabilities 3 Register to indicate to software a Function's level of OHC-E support. |
| 6.3 | Removing <br> Prefetchable <br> Terminology | Through misunderstanding and misuse, "Prefetchable" \& "Non-Prefetchable" have become damaged words - a source of more trouble than good. This ECN reworks the PCle Base Specification to more accurately reflect modern device \& system requirements, with the ultimate goal of significantly reducing industry confusion and correctly focusing development efforts. |
| 6.3 | NOP Flit <br> Extensions | Defines two new standardized NOP Flit types: <br> 1. NOP.Debug (Debug information) <br> 2. NOP.Vendor (Vendor-defined content) <br> Existing NOP Flit definition is renamed as NOP.Empty Flit type. <br> Any NOP Flit type is permitted when a NOP Flit is transmitted. <br> NOP.Debug and NOP.Vendor Flits are not subject to retransmission or flow control. Transmission is on a best effort basis. <br> A NOP Flit Counter mechanism is defined to detect missing NOP Flits (in most cases). A NOP Stream ID indicates the origin of the NOP Flit and enables forwarding use cases of NOP Flits. |
| 6.3 | $\begin{gathered} \text { SNDR }_{\text {TX }}$ and \\ R $_{\text {LM-TX }}$ <br> Measurement \end{gathered}$ | Tx Signal-to-Noise Distortion Ratio (SNDR) and Ratio of Level Mismatch ( $\mathrm{R}_{\mathrm{LM}-\mathrm{TX}}$ ) Measurement Methodologies at $64.0 \mathrm{GT} / \mathrm{s}$ <br> Describes ways to measure Signal-to-Noise Distortion Ratio (SNDR ${ }_{T X}$ ) and Ratio of Level Mismatch ( $\mathrm{R}_{\mathrm{LM}-\mathrm{TX}}$ ) at $64.0 \mathrm{GT} / \mathrm{s}$ using Multi Pulse Response Fit (MPRF)-based methodologies. <br> The new MPRF-based SNDR $_{\text {TX }}$ method mitigates the impact of duty cycle error on the SNDR $_{\text {TX }}$ measurement. <br> The new MPRF-based $R_{L M-T X}$ method replaces the method where the $6 L_{d} U I$ from each consecutive run of 64 or more Uls of the same symbol $\{0,1,2,3\}$, is used to establish a mean voltage for the PAM4 signal levels $\left(V_{0}, V_{1}, V_{2}\right.$, and $\left.V_{3}\right)$ transmitted for PAM4 2-bit symbols for the $R_{L M-T X}$ equation. The new $R_{L M-T X}$ method will be applied on a compliance pattern waveform captured on a real-time oscilloscope. Pulse responses are established based on each PAM4 signal level. The peak of these pulse responses become the input to the $R_{L M-T X}$ expression. <br> The lower data rates are unaffected as SNDR $_{\text {TX }}$ and $R_{\text {LM-TX }}$ are only defined at $64.0 \mathrm{GT} / \mathrm{s}$. |

Page 104

# Objective of the PCI Express ${ }^{\circledR}$ Architecture 

This document defines the "base" specification for the PCI Express architecture, including the electrical, protocol, platform architecture and programming interface elements required to design and build devices and systems. A key goal of the PCI Express architecture is to enable devices from different vendors to inter-operate in an open architecture, spanning multiple market segments including clients, servers, embedded, and communication devices. The architecture provides a flexible framework for product versatility and market differentiation.

This specification describes the PCI Express ${ }^{\circledR}$ architecture, interconnect attributes, fabric management, and the programming interface required to design and build systems and peripherals that are compliant with the PCI Express Specification.

The goal is to enable such devices from different vendors to inter-operate in an open architecture. The specification is intended as an enhancement to the $\mathrm{PCI}^{\text {® }}$ architecture spanning multiple market segments; clients (desktops and mobile), servers (standard and enterprise), and embedded and communication devices. The specification allows system OEMs and peripheral developers adequate room for product versatility and market differentiation without the burden of carrying obsolete interfaces or losing compatibility.

Page 106

# PCI Express Architecture Specification Organization 

The PCI Express specifications are organized as a base specification and a set of companion documents.
The PCI Express Base Specification contains the technical details of the architecture, protocol, Data Link Layer, Physical Layer, and software interface. The PCI Express Base Specification (this document) is applicable to all variants of PCI Express.

The companion specifications define a variety of form factors, including mechanical and electrical chapters covering topics including auxiliary signals, power delivery, and the Adapter interconnect electrical budget.

Page 108

# Documentation Conventions 

## Capitalization

Some terms are capitalized to distinguish their definition in the context of this document from their common English meaning. Words not capitalized have their common English meaning. When terms such as "memory write" or "memory read" appear completely in lower case, they include all transactions of that type.

Register names and the names of fields and bits in registers and headers are presented with the first letter capitalized and a mixture of capitalization for the remainder.

## Numbers and Number Bases

Hexadecimal numbers are written with a lower case " $h$ " suffix, e.g., FFFh and 80h. Hexadecimal numbers larger than four digits are represented with a space dividing each group of four digits, as in 1E FFFF FFFFh. Binary numbers are written with a lower case "b" suffix, e.g., 1001b and 10b. Binary numbers larger than four digits are written with a space dividing each group of four digits, as in 100001010010 b .

All other numbers are decimal.

## Implementation Notes

## IMPLEMENTATION NOTE:

Implementation Notes should not be considered to be part of this specification. They are included for clarification and illustration only.

## Notes

## NOTE

Notes pertain to the specification itself as opposed to implementations of the specification. For example, they are used to describe the document process. They are also used for forward looking information describing anticipated changes for a future version of this specification.

## Issues

## ISSUE 1

Issues are outstanding items in the specification. They indicate things like missing, outdated, or lower quality artwork, anticipated changes that are being deferred to a subsequent version of the specification, potential errata items noticed during the editing process, etc.

PCI-SIG's goal is to resolve all notes before the 1.0 published release of the specification (where "resolving" includes deferring an item to later, or determining that the item is not needed or is incorrect).

Implementation Notes Notes and Issues can also be inline.

Page 110

# Terms and Acronyms 

## 8b/10b

The data encoding scheme ${ }^{1}$ used in the PCI Express Physical Layer for $5.0 \mathrm{GT} / \mathrm{s}$ and below.

## 10-Bit Tags

A Tag's capability that provides a total of 10 bits for the Tag field. See Tag.

## 14-Bit Tags

A Tag's capability that provides a total of 14 bits for the Tag field. See Tag.

## Access Control Services, ACS

A set of capabilities and control registers used to implement access control over routing within a PCI Express component.

## ACS Violation

An error that applies to a Posted or Non-Posted Request when the Completer detects an access control violation.

## Adapter

Used generically to refer to an add-in card or module.

## Advanced Error Reporting, AER

Advanced Error Reporting (see § Section 7.8.4).

## Alternative Routing-ID, ARI

Alternative Routing-ID Interpretation. Applicable to Requester IDs and Completer IDs as well as Routing IDs.

## ARI Device

A Device associated with an Upstream Port, whose Functions each contain an ARI Extended Capability structure.

## ARI Downstream Port

A Switch Downstream Port or Root Port that supports ARI Forwarding.

## ARI Forwarding

Functionality that enables the Downstream Port immediately above an ARI Device to access the Devices extended Functions. Enabling ARI Forwarding ensures the logic that determines when to turn a Type 1 Configuration Request into a Type 0 Configuration Request no longer enforces a restriction on the traditional Device Number field being 0.

## Asserted

The active logical state of a conceptual or actual signal.

## Async Removal

Removal of an adapter or cable from a slot without lock-step synchronization with the operating system (e.g., in an asynchronous manner without button presses).

## Atomic Operation, AtomicOp

One of three architected Atomic Operations where a single PCI Express transaction targeting a location in Memory Space reads the location's value, potentially writes a new value to the location, and returns the original value. This read-modify-write sequence to the location is performed atomically. AtomicOps include FetchAdd, Swap, and CAS.

[^0]
[^0]:    1. IBM Journal of Research and Development, Vol. 27, \#5, September 1983 "A DC-Balanced, Partitioned-Block 8B/10B Transmission Code" by Widmer and Franaszek.

# Attribute 

Transaction handling preferences indicated by specified Packet header bits and fields (e.g., non-snoop).

## Authentication

A process for determining that an entity is what it appears to be (its identity) using defined data objects and digital signatures.

## Base Address Register, BAR

Base Address Registers exist within Configuration Space and are used to determine the amount of system memory space needed by a Function and to provide the base address for a mapping to Function memory space. A Base Address Register may map to memory space or I/O space.

## Beacon

An optional 30 kHz to 500 MHz in-band signal used to exit the L2 Link Power Management state. One of two defined mechanisms for waking up a Link in L2 (see Wakeup).

## Bridge

One of several defined System Elements. A Function that virtually or actually connects a PCI/PCI-X segment or PCI Express Port with an internal component interconnect or with another PCI/PCI-X bus segment or PCI Express Port. A virtual Bridge in a Root Complex or Switch must use the software configuration interface described in this specification.

## by-1, $\times 1$

A Link or Port with one Physical Lane.

## by-8, x8

A Link or Port with eight Physical Lanes.

## by-N, xN

A Link or Port with "N" Physical Lanes.

## Compare and Swap, CAS

An AtomicOp where the value of a target location is compared to a specified value and, if they match, another specified value is written back to the location. Regardless, the original value of the location is returned.

## Character

An 8-bit quantity treated as an atomic entity; a byte.

## Clear

A bit is Clear when its value is 0 b.

## Cold Reset

A Fundamental Reset following the application of main power.

## Completer

The Function that terminates or "completes" a given Request, and generates a Completion if appropriate. Generally, the Function targeted by the Request serves as the Completer. For cases when an uncorrectable error prevents the Request from reaching its targeted Function, the Function that detects and handles the error serves as the Completer.

## Completer Abort, CA

1. A status that applies to a posted or non-posted Request that the Completer is permanently unable to complete successfully, due to a violation of the Completer's programming model or to an unrecoverable error associated with the Completer.
2. A status indication returned with a Completion for a non-posted Request that suffered a Completer Abort at the Completer.

# Completer ID 

The combination of a Completer's Bus Number, Device Number, and Function Number that uniquely identifies the Completer of the Request within a Hierarchy. With an ARI Completer ID, bits traditionally used for the Device Number field are used instead to expand the Function Number field, and the Device Number is implied to be 0.

## Completion

A Packet used to terminate, or to partially terminate, a transaction sequence. A Completion always corresponds to a preceding Request, and, in some cases, includes data.

## component

A physical device (a single package).

## Configuration Software

The component of system software responsible for accessing Configuration Space and configuring the PCI/PCIe bus.

## Configuration Space

One of the four address spaces within the PCI Express architecture. Packets with a Configuration Space address are used to configure Functions.

## Configuration-Ready

A Function is Configuration-Ready when it is guaranteed that the Function will respond to a valid Configuration Request targeting the Function with a Completion indicating Successful Completion status.

## Containment Error Recovery, CER

A general error containment and recovery approach supported by Downstream Port Containment (DPC), where with suitable software/firmware support, many uncorrectable errors can be handled without disrupting applications.

## Conventional PCI

Behaviors or features originally defined in the PCI Local Bus Specification. The PCI Express Base 4.0 and subsequent specifications incorporate the relevant requirements from the PCI Local Bus Specification.

## Conventional Reset

A Hot, Warm, or Cold Reset. Distinct from Function Level Reset (FLR).

## Data Link Layer

The intermediate Layer that is between the Transaction Layer and the Physical Layer.

## Data Link Layer Packet, DLLP

A Packet generated in the Data Link Layer to support Link management functions.

## data payload

Information following the header in some packets that is destined for consumption by the targeted Receiver of the Packet (for example, Write Requests or Read Completions).

## deasserted

The inactive logical state of a conceptual or actual signal.

## Deferrable Memory Write, DMWr

A Memory Write where the Requester attempts to write to a given location in Memory Space using the non-posted DMWr TLP Type. A Completer that supports this TLP Type can accept or decline the Request, indicating this by means of the Completion status returned. See § Section 6.32 .

## Design for Testability, DFT

Design for Testability.

# Device (uppercase 'D') 

A collection of one or more Functions within a single hierarchy identified by common Bus Number and Device Number. An SR-IOV Device may have additional Functions accessed via additional Bus Numbers and/or Device Numbers configured through one or more SR-IOV Extended Capability structures.

## device (lowercase 'd')

1. A physical or logical entity that performs a specific type of I/O.
2. A component on either end of a PCI Express Link.
3. A common imprecise synonym for Function, particularly when a device has a single Function.

## Device Readiness Status, DRS

A mechanism for indicating that a Device is Configuration-Ready (see § Section 6.22.1).

## DLP

In Flit Mode, the Data Link Layer Payload within a Flit.

## Downstream

1. The relative position of an interconnect/System Element (Port/component) that is farther from the Root Complex. The Ports on a Switch that are not the Upstream Port are Downstream Ports. All Ports on a Root Complex are Downstream Ports. The Downstream component on a Link is the component farther from the Root Complex.
2. A direction of information flow where the information is flowing away from the Root Complex.

## Downstream Path

The flow of data through a Retimer from the Upstream Pseudo Port Receiver to the Downstream Pseudo Port Transmitter.

## Downstream Port Containment, DPC

The automatic disabling of the Link below a Downstream Port following an uncorrectable error, which prevents TLPs subsequent to the error from propagating Upstream or Downstream.

## DSP

Downstream Port

## DWORD, DW

Four bytes. Used in the context of a data payload, the 4 bytes of data must be on a naturally aligned 4-byte boundary (the least significant 2 bits of the byte address are 00b).

## Egress Port

The transmitting Port; that is, the Port that sends outgoing traffic.

## Electrical Idle

A Link state used in a variety of defined cases, with specific requirements defined for the Transmitter and Receiver.

## End-End TLP Prefix

A TLP Prefix that is carried along with a TLP from source to destination. See § Section 2.2.10.4 .

## Endpoint

One of several defined System Elements. A Function that has a Type 00h Configuration Space header.

## Endpoint Upstream Port

An Upstream Port that contains Endpoint Functions exclusively.

# error detection 

Mechanisms that determine that an error exists, either by the first agent to discover the error (e.g., Malformed TLP) or by the recipient of a signaled error (e.g., receiver of a poisoned TLP).

## error logging

A detector setting one or more bits in architected registers based on the detection of an error. The detector might be the original discoverer of an error or a recipient of a signaled error.

## error reporting

In a broad context, the general notification of errors. In the context of the Device Control register, sending an error Message. In the context of the Root Error Command register, signaling an interrupt as a result of receiving an error Message.

## error signaling

One agent notifying another agent of an error either by (1) sending an error Message, (2) sending a Completion with UR/CA Status, or (3) poisoning a TLP.

## Extension Device

A component whose purpose is to extend the physical length of a Link.

## Extended Function

Within an ARI Device, a Function whose Function Number is greater than 7. Extended Functions are accessible only after ARI-aware software has enabled ARI Forwarding in the Downstream Port immediately above the ARI Device.

## FetchAdd, Fetch and Add

An AtomicOp where the value of a target location is incremented by a specified value using two's complement arithmetic ignoring any carry or overflow, and the result is written back to the location. The original value of the location is returned.

## Flit

Flow Control Unit

## Flow Control

The method for communicating receive buffer status from a Receiver to a Transmitter to prevent receive buffer overflow and allow Transmitter compliance with ordering rules.

## Flow Control Packet, FCP

A DLLP used to send Flow Control information from the Transaction Layer in one component to the Transaction Layer in another component.

## Flow-Through

Refers to the behavior, by a Switch or Root Complex supporting peer-to-peer, of passing an IDE TLP associated with a Selective IDE Stream from Ingress Port to Egress Port without modification.

## FRU Information

Information used to provide inventory and capability information about a board on which the FRU Information Device is located.

## FRU Information Device

A storage component such as a real or firmware emulated EEPROM, compatible with components such as the AT 24C256 that stores FRU Information.

## Function

Within a Device, an addressable entity in Configuration Space associated with a single Function Number. Used to refer to one Function of a Multi-Function Device, or to the only Function in a Single-Function Device. Specifically included are special types of Functions defined in § Chapter 9. , notably Physical Functions and Virtual Functions.

# Function Group 

Within an ARI Device, a configurable set of Functions that are associated with a single Function Group Number. Function Groups can optionally serve as the basis for VC arbitration or access control between multiple Functions within the ARI Device.

## Function Level Reset, FLR

A mechanism for resetting a specific Endpoint Function (see § Section 6.6.2).

## Function Readiness Status, FRS

A mechanism for indicating that a Function is Configuration-Ready (see § Section 6.22.2)

## Fundamental Reset

A hardware mechanism for setting or returning all Port states to the initial conditions specified in this document (see § Section 6.6 ).

## GT/s

The number of encoded bits transferred in a second on a direction of a Lane. Short for Giga Transfers per Second.

## header

A set of fields that appear at or near the front of a Packet that contain the information required to determine the characteristics and purpose of the Packet.

## Hierarchy

A PCI Express I/O interconnect topology, wherein the Configuration Space addresses, referred to as the tuple of Bus/ Device/Function Numbers (or just Bus/Function Numbers, for ARI cases), are unique. These addresses are used for Configuration Request routing, Completion routing, some Message routing, and for other purposes. In some contexts a Hierarchy is also called a Segment, and in Flit Mode, the Segment number is sometimes also included in the ID of a Function.

## hierarchy domain

The part of a Hierarchy originating from a single Root Port.

## Host Bridge

Part of a Root Complex that connects a host CPU or CPUs to a Hierarchy.

## Hot Reset

A reset propagated in-band across a Link using a Physical Layer mechanism.

## IDE Partner Port

The remote IDE Terminus for an IDE Stream.

## IDE Stream

A Port to Port connection established using the mechanisms defined by Integrity and Data Encryption (IDE) to secure TLP traffic between the two Ports. The connection may be in the form of a Selective IDE Stream, in which case it is possible for IDE TLPs to flow through Switches without affecting their security, or in the form of a Link IDE Stream, in which case the two Ports must be connected without intervening Switches.

## IDE Terminus

A Port acting as the originator or ultimate destination for IDE TLPs associated with one or more IDE Streams.

## IDE TLP

A TLP associated with an IDE Stream and secured using Integrity and Data Encryption (IDE).

## in-band signaling

A method for signaling events and conditions using the Link between two components, as opposed to the use of separate physical (sideband) signals. All mechanisms defined in this document can be implemented using in-band signaling, although in some form factors sideband signaling may be used instead.

# Ingress Port 

Receiving Port; that is, the Port that accepts incoming traffic.

## Internal Error

An error associated with a PCI Express interface that occurs within a component and which may not be attributable to a packet or event on the PCI Express interface itself or on behalf of transactions initiated on PCI Express.

## I/O Space

One of the four address spaces of the PCI Express architecture.

## isochronous

Data associated with time-sensitive applications, such as audio or video applications.

## invariant

A field of a TLP header or TLP Prefix that contains a value that cannot legally be modified as the TLP flows through the PCI Express fabric.

## Lane

A set of differential signal pairs, one pair for transmission and one pair for reception. A by-N Link is composed of N Lanes.

## Layer

A unit of distinction applied to this specification to help clarify the behavior of key elements. The use of the term Layer does not imply a specific implementation.

## Link

The collection of two Ports and their interconnecting Lanes. A Link is a dual-simplex communications path between two components.

## Link IDE Stream

An IDE Stream applied to all TLPs, except those associated with Selective IDE Stream(s), where the two Ports are connected without intervening Switches, although extension devices may be present on the Link.

## Link Segment

The collection of a Port and a Pseudo Port or two Pseudo Ports and their interconnecting Lanes. A Link Segment is a dual simplex communications path between a Component and a Retimer or between two Retimers (two Pseudo Ports).

## Lightweight Notification, LN

This protocol is now deprecated. It was a lightweight protocol that supported notifications to Endpoints via a hardware mechanism when cachelines of interest were updated.

## Local TLP Prefix

A TLP Prefix that is carried along with a TLP on a single Link. See § Section 2.2.10.2 .

## Logical Bus

The logical connection among a collection of Devices that have the same Bus Number in Configuration Space.

## Logical Idle

A period of one or more Symbol Times when no information (TLPs, PMUX Packets, DLLPs, or any special Symbol) is being transmitted or received. Unlike Electrical Idle, during Logical Idle the Idle data Symbol is being transmitted and received.

## LTR

Abbreviation for Latency Tolerance Reporting

# Malformed Packet 

A TLP that violates specific TLP formation rules as defined in this specification.

## Measurement

A process for calculating a cryptographic hash value of firmware or other configuration state, applying a digital signature, and returning this information.

## Memory Space

One of the four address spaces of the PCI Express architecture.

## Message

A TLP used to communicate information outside of the Memory, I/O, and Configuration Spaces.

## Message Signaled Interrupt, MSI/MSI-X

Two similar but separate mechanisms that enable a Function to request service by writing a system-specified DWORD of data to a system-specified address using a Memory Write Request. Compared to MSI, MSI-X supports a larger maximum number of vectors and independent message address and data for each vector.

## Message Space

One of the four address spaces of the PCI Express architecture.

## MMIO

Memory-mapped I/O space. Synonymous with the term Memory Space.

## MPS

Abbreviation for Max_Payload_Size.

## Multicast, MC

A feature and associated mechanisms that enable a single Posted Request TLP sent by a source to be distributed to multiple targets.

## Multicast Group, MCG

A set of Endpoints that are the target of Multicast TLPs in a particular address range.

## Multicast Hit

The determination by a Receiver that a TLP will be handled as a Multicast TLP.

## Multicast TLP

A TLP that is potentially distributed to multiple targets, as controlled by Multicast Capability structures in the components through which the TLP travels.

## Multicast Window

A region of Memory Space where Posted Request TLPs that target it will be handled as Multicast TLPs.

## Multi-Function Device, MFD

A Device that has multiple Functions.

## Multi-Root I/O Virtualization, MR-IOV

A Function that supports the MR-IOV capability. See [MR-IOV] for additional information.

## MUST@FLIT

MUST@FLIT features are mandatory for components that support Flit Mode (Flit Mode Supported is Set). MUST@FLIT features are strongly recommended for all other components.

## naturally aligned

A data payload with a starting address equal to an integer multiple of a power of two, usually a specific power of two. For example, 64-byte naturally aligned means the least significant 6 bits of the byte address are 000000 b.

# NPEM 

Native PCIe Enclosure Management

## OBFF

Optimized Buffer Flush/Fill

## Operating System

Throughout this specification, the terms operating system and system software refer to the combination of power management services, device drivers, user-mode services, and/or kernel mode services.

## orderly removal

A hot-plug removal model where the OS is notified when a user/operator wishes to remove an adapter, and the OS has the opportunity to prepare for the event (e.g., quiescing adapter activity) before granting permission for removal.

## P2P

Peer-to-peer.

## Path

The flow of data through a Retimer, in either the Upstream Path or the Downstream Path.

## Packet

A fundamental unit of information transfer consisting of an optional TLP Prefix, followed by a header and, in some cases, followed by a data payload.

## Parts per Million, ppm

Applied to frequency, the difference, in millionths of a Hertz, between a stated ideal frequency, and the measured long-term average of a frequency.

## PCIe ${ }^{\circledR}$

PCI Express ${ }^{\circledR}$

## PCI Bridge

See Type 1 Function.

## PCI Software Model

The software model necessary to initialize, discover, configure, and use a PCI-compatible device, as specified in [PCI-3.0], [PCI-X], and [Firmware].

## Phantom Function Number, PFN

An unclaimed Function Number that may be used to expand the number of outstanding transaction identifiers by logically combining the PFN with the Tag identifier to create a unique transaction identifier.

## Physical Function, PF

A Function that contains an SR-IOV Extended Capability structure and supports the SR-IOV capabilities defined in § Chapter 9. .

## Physical Lane

See Lane.

## Physical Layer

The Layer that directly interacts with the communication medium between two components.

## Port

1. Logically, an interface between a component and a PCI Express Link.
2. Physically, a group of Transmitters and Receivers located on the same chip that define a Link.

# Power Management 

Software or Hardware mechanisms used to minimize system power consumption, manage system thermal limits, and maximize system battery life. Power management involves tradeoffs among system speed, noise, battery life, and AC power consumption.

## PMUX Channel

A multiplexed channel on a PMUX Link that is configured to transport a specific multiplexed protocol. See § Appendix G.

## PMUX Link

A Link where Protocol Multiplexing is supported and enabled. See § Appendix G.

## PMUX Packet

A non-PCI Express Packet transported over a PCI Express Link. See § Appendix G.

## Precision Time Measurement, PTM

An optional capability for communicating precise timing information between components.

## Process Address Space ID, PASID

The Process Address Space ID, in conjunction with the Requester ID, uniquely identifies the address space associated with a transaction.

## Programmed I/O, PIO

A transaction sequence that's initiated by a host processor, often as the result of executing a single load or store instruction that targets a special address range, but can be generated by other mechanisms such as the PCI-Compatible Configuration Mechanism. Notably, host processor loads or stores targeting an ECAM address range generate Configuration Space transactions. Other memory-mapped ranges typically exist to generate Memory Space and I/O Space transactions.

## Pseudo Port

1. Logically, an interface between a Retimer and a PCI Express Link Segment.
2. Physically, a group of Transmitters and Receivers located on the same Retimer chip that define a Link Segment.

## Quality of Service, QoS

Attributes affecting the bandwidth, latency, jitter, relative priority, etc., for differentiated classes of traffic.

## QWORD, QW

Eight bytes. Used in the context of a data payload, the 8 bytes of data must be on a naturally aligned 8-byte boundary (the least significant 3 bits of the address are 000b).

## RCIEP

Root Complex Integrated Endpoint.

## Read Side Effect

An observable change in system state due to a read. A classic Read Side Effect is a read that returns an element from a FIFO, removing that element from the FIFO. This specification does not define or require the implementation of Read Side Effects.

## recommended

Among several possibilities one is particularly suitable, without mentioning or excluding others; or that a certain course of action is preferred but not necessarily required.

## Receiver, Rx

The component that receives Packet information across a Link.

# Receiving Port 

In the context of a specific TLP, PMUX Packet, or DLLP, the Port that receives the Packet on a given Link.

## Re-driver

A non-protocol aware, software transparent, Extension Device.

## Refclk

An abbreviation for Reference Clock.

## repeater

An imprecise term for Extension Device.

## Reported Error

An error subject to the logging and signaling requirements architecturally defined in this document.

## Request

A Packet used to initiate a transaction sequence. A Request includes operation code and, in some cases, address and length, data, or other information.

## Requester

The Function or system element that first introduces a transaction sequence into the PCI Express domain.

## Requester ID

The combination of a Requester's Bus Number, Device Number, and Function Number that uniquely identifies the Requester within a Hierarchy. With an ARI Requester ID, bits traditionally used for the Device Number field are used instead to expand the Function Number field, and the Device Number is implied to be 0.

## Reserved

The contents, states, or information are not defined at this time. Using any Reserved area (for example, packet header bit-fields, configuration register bits) is not permitted. Reserved register fields must be read only and must return 0 (all 0's for multi-bit fields) when read. Reserved encodings for register and packet fields must not be used. Any implementation dependence on a Reserved field value or encoding will result in an implementation that is not PCI Express-compliant. The functionality of such an implementation cannot be guaranteed in this or any future revision of this specification.

## Retimer

A Physical Layer protocol aware, software transparent, Extension Device that forms two separate electrical Link Segments.

## Role-Based Error Reporting

A set of error handling semantics based on the role of the agent that detects the error, the type of TLP involved in the error, and the error handling settings of the agent. See Implementation Note: Use of ERR_COR, ERR_NONFATAL, and ERR_FATAL.

## Root Complex, $R C$

A defined System Element that includes at least one Host Bridge, Root Port, or Root Complex Integrated Endpoint.

## Root Complex Component

A logical aggregation of Root Ports, Root Complex Register Blocks, Root Complex Integrated Endpoints, and Root Complex Event Collectors.

## Root Port, RP

A PCI Express Port on a Root Complex that maps a portion of a Hierarchy through an associated virtual PCI-PCI Bridge.

## Routing Element

A term referring to a Root Complex, Switch, or Bridge in regard to its ability to route, multicast, or block TLPs.

# Routing ID, RID 

Either the Requester ID or Completer ID that identifies a PCI Express Function.

## RP PIO

Root Port Programmed I/O. See § Section 6.2.11.3.

## Rx_MPS_Limit

The computed data payload size limit for a Function receiving a TLP, which is determined by the Rx_MPS_Fixed bit value and Max_Payload_Size setting in one or more Functions. See § Section 2.2.2 for details.

## Segment

See Hierarchy

## Selective IDE Stream

An IDE Stream applied selectively to TLPs based on ranges of Memory Addresses and RIDs, and where it is possible for secured TLPs to flow through Switches without affecting their security.

## Set

A bit is Set when its value is 1 b .

## Shadow Function

An otherwise unimplemented Function, where its Transaction ID space is used by a Function that implements the Shadow Functions Extended Capability structure.

## sideband signaling

A method for signaling events and conditions using physical signals separate from the signals forming the Link between two components. All mechanisms defined in this document can be implemented using in-band signaling, although in some form factors sideband signaling may be used instead.

## Single-Function Device, SFD

A Device that has a single Function.

## Single Root I/O Virtualization, SR-IOV

A Function that supports the SR-IOV Extended Capability defined in this specification.

## Single Root PCI Manager, SR-PCIM

Software responsible for configuration and management of the SR-IOV Extended Capability and PF/VF as well as dealing with associated error handling. Multiple implementation options exist; therefore, SR-PCIM implementation is outside the scope of this specification.

## SR-IOV Device

A Device containing one or more Functions that have an SR-IOV Extended Capability structure.

## SSD

Solid State Drive

## strongly recommended

This item is not mandatory, but in the absence of compelling reasons, it is the most desired choice.

## Swap, Unconditional Swap

An AtomicOp where a specified value is written to a target location, and the original value of the location is returned.

## Switch

A defined System Element that connects two or more Ports to allow Packets to be routed from one Port to another. To configuration software, a Switch appears as a collection of virtual PCI-to-PCI Bridges [PCI-to-PCI-Bridge].

# Switch Port 

A Port that contains a Switch Downstream Port Function or at least one Switch Upstream Port Function.

## Symbol

A 10-bit quantity when using 8b/10b encoding. An 8-bit quantity when using 128b/130b encoding.

## Symbol Time

The period of time required to place a Symbol on a Lane ( 10 times the Unit Interval when using 8b/10b encoding, 8 times the Unit Interval when using 128b/130b encoding, and 4 times the Unit Interval when using 1b/1b encoding).

## System Element

A defined Device or collection of Devices that operate according to distinct sets of rules. The following System Elements are defined: Root Complex, Endpoint, Switch, and Bridge.

## System Image, SI

A software component running on a virtual system to which specific Functions, PFs, and VFs can be assigned. Specification of the behavior and architecture of an SI is outside the scope of this specification. Examples of SIs include guest operating systems and shared/non-shared protected domain device drivers.

## System Software

Includes System Firmware (BIOS, UEFI), Operating System, VMM, management software, platform vendor's add-on to the Operating System.

## Tag

A number assigned to a given Non-Posted Request to distinguish Completions for that Request from other Requests.

## TEE Device Interface (TDI)

The unit of assignment for an IO-virtualization capable device. For example, a TDI may be an entire Device, a non-IOV Function, a PF (and possibly its subordinate VFs), or a VF.

## TEE-I/O

A conceptual framework for establishing and managing Trusted Execution Environments (TEEs) that include a composition of resources from one or more devices (see § Chapter 11.).

## TLP Prefix

Additional information that may be optionally prepended to a TLP. TLP Prefixes are either Local or End-End. A TLP can have multiple TLP Prefixes. See § Section 2.2.10 .

## TPH

Abbreviation for TLP Processing Hints

## Transaction Descriptor

An element of a Packet header that, in addition to Address, Length, and Type, describes the properties of the Transaction.

## Transaction ID

A component of the Transaction Descriptor including Requester ID and Tag.

## Transaction Layer

The Layer that operates at the level of transactions (for example, read, write).

## Transaction Layer Packet, TLP

A Packet generated in the Transaction Layer to convey a Request or Completion.

## transaction sequence

A single Request and zero or more Completions associated with carrying out a single logical transfer by a Requester.

# Transceiver 

The physical Transmitter and Receiver pair on a single chip.

## Translated Request

A Request using a Translated Memory Address, as indicated by the AT field.

## Transmitter, $T x$

The component sending Packet information across a Link.

## Transmitting Port

In the context of a specific TLP, PMUX Packet, or DLLP, the Port that transmits the Packet on a given Link.

## Trusted Computing Base (TCB)

A combination of hardware, firmware, and software, responsible for enforcing a security policy. Bugs or vulnerabilities occurring inside the TCB might jeopardize the security properties of the entire system. By contrast, parts of a computer system outside the TCB shall not be able to create a condition that would allow any more privileges than are granted to them in accordance with the security policy.

## Trusted Execution Environment,TEE

Refers to an environment, which may include only a portion of a device, the whole of a device, or a composition of multiple devices, within which some level of "trust" is established, such that operations (including code execution) that occur within this environment are considered "trustworthy". It is generally the case that one TEE is isolated from other TEEs that are intended to be distinct, and that all TEEs are isolated from untrusted environments.

## Trusted Execution Environment Virtual Machine (Trusted Execution Environment VM, TVM)

A Trusted Execution Environment Virtual Machine as defined in the TEE Device Interface Security Protocol (TDISP) reference architecture (see § Chapter 11.).

## Tx_MPS_Limit

The computed data payload size limit for a Function transmitting a TLP, which is determined by the Max_Payload_Size setting in one or more Functions. See § Section 2.2.2 for details.

## Type 0 Function

Function with a Type 0 Configuration Space Header (see § Section 7.5.1.2).

## Type 1 Function

Function with a Type 1 Configuration Space Header (see § Section 7.5.1.3).

## Unconditional Swap, Swap

An AtomicOp where a specified value is written to a target location, and the original value of the location is returned.

## Unit Interval, UI

Given a data stream of a repeating pattern of alternating 1 and 0 values, the Unit Interval is the value measured by averaging the time interval between voltage transitions, over a time interval long enough to make all intentional frequency modulation of the source clock negligible (see RX: UI and TX: UI).

## Unordered I/O, UIO

A set of Request/Completion Types used with supporting Virtual Channel(s) to support a Requester-managed ordering model. See § Section 6.34 .

## Unsupported Request, UR

1. A status that applies to a posted or non-posted Request that specifies some action or access to some space that is not supported by the Completer.
2. A status indication returned with a Completion for a non-posted Request that suffered an Unsupported Request at the Completer.

# Upstream 

1. The relative position of an interconnect/System Element (Port/component) that is closer to the Root Complex. The Port on a Switch that is closest topologically to the Root Complex is the Upstream Port. The Port on a component that contains only Endpoint or Bridge Functions is an Upstream Port. The Upstream component on a Link is the component closer to the Root Complex.
2. A direction of information flow where the information is flowing towards the Root Complex.

## Upstream Path

The flow of data through a Retimer from the Downstream Pseudo Port Receiver to the Upstream Pseudo Port Transmitter.

## USP

Upstream Port

## variant

A field of a TLP header that contains a value that is subject to possible modification according to the rules of this specification as the TLP flows through the PCI Express fabric.

## Virtual Function, VF

A Function that is associated with a Physical Function. A VF shares one or more physical resources, such as a Link, with the Physical Function and other VFs that are associated with the same PF.

## Virtualization Intermediary, VI

A software component supporting one or more SIs-colloquially known as a hypervisor or virtual machine monitor. Specification of the behavior and architecture of the VI is outside the scope of this specification.

## wakeup

An optional mechanism used by a component to request the reapplication of main power when in the L2 Link state. Two such mechanisms are defined: Beacon (using in-band signaling) and WAKE\# (using sideband signaling).

## Warm Reset

A Fundamental Reset without cycling main power.

## Zero

The numerical value of zero in a bit, field, or register, of appropriate width for that bit, field, or register.

6.3-1.0-PUB - PCI Express ${ }^{\circledR}$ Base Specification Revision 6.3

# Reference Documents 

## PCI

## PCI-3.0

PCI Local Bus Specification, Revision 3.0

## PCIe

## PCIe-6.3

PCI Express Base Specification, Revision 6.3

## PCIe-6.2

PCI Express Base Specification, Revision 6.2

## PCIe-6.1

PCI Express Base Specification, Revision 6.1

## PCIe-6.0.1

PCI Express Base Specification, Revision 6.0.1

## PCIe-6.0

PCI Express Base Specification, Revision 6.0

## PCIe-5.0

PCI Express Base Specification, Revision 5.0

## PCIe-4.0

PCI Express Base Specification, Revision 4.0

## PCIe-3.1

## PCIe-3.1a

PCI Express Base Specification, Revision 3.1a

## PCIe-3.0

PCI Express Base Specification, Revision 3.0

## PCIE-2.1

PCI Express Base Specification, Revision 2.1

## PCIe-2.0

PCI Express Base Specification, Revision 2.0

## PCIe-1.1

PCI Express Base Specification, Revision 1.1

## PCIe-1.0

## PCIe-1.0a

PCI Express Base Specification, Revision 1.0a
PCI Express Card Electromechanical Specification, Revision 6.0 - Work in Progress

CEM
CEM-5.0
CEM-5.1
PCI Express Card Electromechanical Specification, Revision 5.1 plus PCI Express CEM Specification, Revision 5.1
Errata
CEM-4.0
PCI Express Card Electromechanical Specification, Revision 4.0
CEM-3.0
PCI Express Card Electromechanical Specification, Revision 3.0
CEM-2.0
PCI Express Card Electromechanical Specification, Revision 2.0
PCIe-to-PCI-PCI-X-Bridge
PCI Express to PCI/PCI-X Bridge Specification, Revision 1.0
PCI-to-PCI-Bridge
PCI-to-PCI Bridge Architecture Specification Revision 1.2
PCI-X
PCI-X Addendum to the PCI Local Bus Specification, Revision 2.0a
Mini-Card
PCI Express Mini Card Electromechanical Specification, Revision 2.1
OCuLink
PCI Express OCuLink Specification, Revision 1.1
M. 2
PCI Express M. 2 Specification, Revision 4.0
MR-IOV
MR-IOV Specification, Revision 1.0
U. 2

SFF-8639
PCI Express SFF-8639 Module Specification, Revision 4.0, Version 1.0

# Ext-Cabling 

PCI Express External Cabling Specification, Revision 3.0a

## ExpressModule

PCI Express ExpressModule Electromechanical Specification, Revision 1.0

## PCI-Hot-Plug

## PCI-Hot-Plug-1.1

PCI Hot-Plug Specification, Revision 1.1

## PCI-PM

PCI Bus Power Management Interface Specification, Revision 1.2

## PCI-Code-and-ID

PCI Code and ID Assignment Specification, Revision 1.11 (or later)

## Firmware

PCI Firmware Specification, Revision 3.2

ACPI
Advanced Configuration and Power Interface Specification, Revision 6.2
UEFI
Unified Extensible Firmware Interface (UEFI) Specification, Version 2.8
EUI-48
EUI-64
SMBIOS
https://www.dmtf.org/standards/smbios System Management BIOS (SMBIOS) Reference Specification, Version 3.6.0 or later

Guidelines for Use of Extended Unique Identifier (EUI), Organizationally Unique Identifier (OUI), and Company ID (CID)

# JEDEC-JESD22-C101 

JEDEC JESD22-C101F: Field-Induced Charged-Device Model Test Method for Electrostatic Discharge Withstand Thresholds of Microelectronic Components

## JEDEC-JEP155-JEP157

JEDEC JEP155: Recommended ESD Target Levels for HBM/MM Qualification and JEP157 Recommended ESD-CDM Target Levels

## ESDA-JEDEC-JS-001-2010

ESDA/JEDEC JS-001-2010: Joint JEDEC/ESDA Standard for Electrostatic Discharge Sensitivity Test - Human Body Model (HBM) - Component Level

## ITU-T-Rec-X-667

ITU T-Rec. X.667: Information technology - Procedures for the operation of object identifier registration authorities: Generation of universally unique identifiers and their use in object identifiers

## ISO-IEC-9834-8

ISO/IEC 9834-8: Information technology - Procedures for the operation of object identifier registration authorities Part 8: Generation of universally unique identifiers (UUIDs) and their use in object identifiers

## RFC-4122

IETF RFC-4122: A Universally Unique IDentifier (UUID) URN Namespace

## DNS

RFC-1034
IETF RFC-1034: DOMAIN NAMES - CONCEPTS AND FACILITIES

## PICMG

PICMG

## PLUG-PLAY-ISA-1.0a

Plug and Play ISA Specification, Version 1.0a, May 5, 1994

## PC-Card

PC-Card

## MCTP-VDM

## DSP0238

Management Component Transport Protocol (MCTP) PCIe VDM Transport Binding Specification -
https://www.dmtf.org/dsp/DSP0238.

# SPDM 

## DSP0274

DMTF Security Protocol \& Data Model (SPDM) Specification - https://www.dmtf.org/dsp/DSP0274. IDE_KM requires SPDM Version 1.1 or above. TDISP requires version 1.2 or above.

## SPDM-MCTP <br> DSP0275

Security Protocol and Data Model (SPDM) over MCTP Binding Specification - https://www.dmtf.org/dsp/DSP0275.

## AES-GCM

NIST Special Publication 800-38D Recommendation for Block Cipher Modes of Operation: Galois/Counter Mode (GCM) and GMAC - https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-38d.pdf

## Secured SPDM <br> DSP0277

Secured Messages using SPDM Specification (IDE requires version 1.0 or above) - https://www.dmtf.org/dsp/ DSP0277

## Secured MCTP

DSP0276
Secured Messages using SPDM over MCTP Binding Specification (version 1.0 or above) - https://www.dmtf.org/dsp/ DSP0276

## CXL

CXL-3.0
Compute Express Link Specificaiton - https://www.computeexpresslink.org

## SMBus

SMBus Version 3.2
SMBus Specification - http://smbus.org/specs/

## I2C

I2C Specification - https://www.nxp.com/docs/en/user-guide/UM10204.pdf

## I3C

I3C-Basic
I3C-Basic-1.1.1
MIPI I3C Basic Specification - https://resources.mipi.org/mipi-i3c-basic-download

## I3C-DCR

I3C Device Characteristic Register - https://www.mipi.org/mipi_i3c_device_characteristics_register

## NVMe

NVM-Express
NVM Express Specification - https://nvmexpress.org/specifications

## NVMe-MI

NVM Express Management Interface Specification - https://nvmexpress.org/specification/nvme-mi-specification

## PLDM-Firmware-Update

DSP0267
PLDM for Firmware Update Specification - https://www.dmtf.org/dsp/DSP0267), or

## PLDM-Platform-Monitoring-Control <br> DSP0248

PLDM for Platform Monitoring and Control Specification - https://www.dmtf.org/dsp/DSP0248

MMBI
DSP0282
Memory-Mapped BMC Interface (MMBI) Specification - https://www.dmtf.org/dsp/DSP0282

# IPMI-FRU 

IPMI Platform Management FRU Information Storage Definition - https://www.intel.com/content/dam/www/ public/us/en/documents/specification-updates/
ipmi-platform-mgt-fru-info-storage-def-v1-0-rev-1-3-spec-update.pdf

## CopprLink

CopprLink-Internal
CopprLink Internal Cable Specification for PCI Express 5.0 and 6.0 - Work in Progress: Draft 0.9 is
https://members.pcisig.com/wg/PCI-SIG/document/20254

6.3-1.0-PUB - PCI Express ${ }^{\circledR}$ Base Specification Revision 6.3

