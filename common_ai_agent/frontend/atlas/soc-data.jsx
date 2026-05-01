// soc-data.jsx — IP-XACT-lite SoC mock for ATLAS SoC Architect
//
// One cluster-y SoC with submodules. Mirrors IP-XACT semantics
// (component / busInterface / addressBlock / memoryMap) but in a
// flatter YAML-friendly shape. The whole tree is what ssot-gen
// reads/writes; rtl-gen and sim run per-module.
//
// Status legend: 'ok' (green ✓) · 'partial' (◐) · 'pending' (○) · 'err' (✗) · 'run' (◌)

window.SOC = {
  name: 'aurora_soc',
  version: '0.4.2',
  // Bus protocols and their visual treatment
  protocols: {
    AXI4:   { color: 'cyan',    label: 'AXI4',   signals: ['awvalid','awready','awaddr','awlen','awsize','awburst','wvalid','wready','wdata','wstrb','wlast','bvalid','bready','bresp','arvalid','arready','araddr','rvalid','rready','rdata','rresp','rlast'] },
    AXI4L:  { color: 'cyan',    label: 'AXI4-Lite', signals: ['awvalid','awready','awaddr','wvalid','wready','wdata','wstrb','bvalid','bready','bresp','arvalid','arready','araddr','rvalid','rready','rdata','rresp'] },
    AHB:    { color: 'accent',  label: 'AHB',    signals: ['hclk','hresetn','haddr','hburst','hsize','htrans','hwdata','hwrite','hready','hresp','hrdata'] },
    APB:    { color: 'magenta', label: 'APB',    signals: ['psel','penable','pwrite','paddr','pwdata','pready','prdata','pslverr'] },
    ACE:    { color: 'cyan',    label: 'ACE',    signals: ['... AXI4 + cache coherency','arsnoop','awsnoop','acvalid','acready','acaddr','acsnoop','crvalid','crready','crresp','cdvalid','cdready','cddata','cdlast','rack','wack'] },
    AXIS:   { color: 'cyan',    label: 'AXI-Stream', signals: ['tvalid','tready','tdata','tlast','tstrb','tkeep','tuser','tdest','tid'] },
    IRQ:    { color: 'warn',    label: 'IRQ',    signals: ['irq[0]','irq[1]','...'] },
    CLK:    { color: 'fg-dim',  label: 'clk/rst',signals: ['clk','rst_n'] },
    DDRPHY: { color: 'warn',    label: 'DDR-PHY',signals: ['ck_t','ck_c','cs_n','ras_n','cas_n','we_n','dq[63:0]','dqs','dm'] },
    ANALOG: { color: 'warn',    label: 'analog', signals: ['vdd','vss','iref','vbias','...']},
  },

  // Top-level clusters (subsystems). Each cluster has children = modules.
  clusters: [
    {
      id: 'cpu_ss', name: 'cpu_ss', label: 'CPU Subsystem',
      x: 60, y: 80, w: 540, h: 420,
      status: { ssot: 'ok', rtl: 'ok', sim: 'partial' },
      modules: [
        { id: 'cpu0', name: 'cpu0', kind: 'cpu', label: 'Cortex-A55 #0', x: 24, y: 56, w: 180, h: 96,
          params: [{k:'arch',v:'ARMv8.2'},{k:'isa',v:'AArch64'},{k:'l1i',v:'32K'}],
          status: { ssot:'ok', rtl:'ok', sim:'ok' },
          interfaces: [
            { side:'right', name:'M_AXI', proto:'ACE', role:'master', width:128, lanes:'32+32+5', y:0.4 },
            { side:'left',  name:'CLK',   proto:'CLK', role:'slave',  y:0.5 },
            { side:'top',   name:'IRQ',   proto:'IRQ', role:'slave',  width:32, x:0.5 },
          ],
        },
        { id: 'cpu1', name: 'cpu1', kind: 'cpu', label: 'Cortex-A55 #1', x: 24, y: 168, w: 180, h: 96,
          params: [{k:'arch',v:'ARMv8.2'},{k:'isa',v:'AArch64'},{k:'l1i',v:'32K'}],
          status: { ssot:'ok', rtl:'ok', sim:'partial' },
          interfaces: [
            { side:'right', name:'M_AXI', proto:'ACE', role:'master', width:128, y:0.4 },
            { side:'left',  name:'CLK',   proto:'CLK', role:'slave',  y:0.5 },
            { side:'top',   name:'IRQ',   proto:'IRQ', role:'slave',  width:32, x:0.5 },
          ],
        },
        { id: 'l2', name: 'l2_cache', kind: 'mem', label: 'L2 Cache', x: 240, y: 96, w: 180, h: 184,
          params: [{k:'size',v:'512K'},{k:'ways',v:'8'},{k:'line',v:'64B'}],
          status: { ssot:'ok', rtl:'ok', sim:'ok' },
          addr: '0x0000_0000 — internal',
          interfaces: [
            { side:'left',  name:'S_ACE_0', proto:'ACE', role:'slave',  width:128, y:0.3 },
            { side:'left',  name:'S_ACE_1', proto:'ACE', role:'slave',  width:128, y:0.7 },
            { side:'right', name:'M_AXI',   proto:'AXI4',role:'master', width:128, y:0.5 },
          ],
        },
        { id: 'gic', name: 'gic_400', kind: 'periph', label: 'GIC-400', x: 360, y: 296, w: 156, h: 80,
          params: [{k:'spec',v:'GICv2'},{k:'sources',v:'192'}],
          status: { ssot:'ok', rtl:'partial', sim:'pending' },
          addr: '0x0800_0000',
          interfaces: [
            { side:'left',  name:'S_APB', proto:'APB', role:'slave',  width:32, y:0.5 },
            { side:'right', name:'IRQ_M', proto:'IRQ', role:'master', width:64, y:0.5 },
          ],
        },
      ],
    },

    {
      id: 'noc', name: 'noc', label: 'Interconnect (NoC)',
      x: 660, y: 80, w: 380, h: 600,
      status: { ssot: 'ok', rtl: 'ok', sim: 'ok' },
      modules: [
        { id: 'cci', name: 'cci_550', kind: 'bus', label: 'CCI-550', x: 32, y: 64, w: 316, h: 220,
          params: [{k:'masters',v:'4'},{k:'slaves',v:'5'},{k:'data_w',v:'128'}],
          status: { ssot:'ok', rtl:'ok', sim:'ok' },
          interfaces: [
            { side:'left',  name:'S_ACE',  proto:'ACE',  role:'slave',  width:128, y:0.5 },
            { side:'right', name:'M_AXI_0',proto:'AXI4', role:'master', width:128, y:0.2 },
            { side:'right', name:'M_AXI_1',proto:'AXI4', role:'master', width:128, y:0.45 },
            { side:'right', name:'M_AXI_2',proto:'AXI4', role:'master', width:128, y:0.7 },
            { side:'bottom',name:'M_APB',  proto:'APB',  role:'master', width:32,  x:0.5 },
          ],
        },
        { id: 'apb_br', name: 'apb_bridge', kind: 'bus', label: 'AXI→APB bridge', x: 80, y: 320, w: 220, h: 88,
          params: [{k:'data_w',v:'32'},{k:'slaves',v:'8'}],
          status: { ssot:'ok', rtl:'ok', sim:'ok' },
          interfaces: [
            { side:'top',    name:'S_AXI',proto:'AXI4L',role:'slave',  width:32, x:0.5 },
            { side:'bottom', name:'M_APB',proto:'APB',  role:'master', width:32, x:0.5 },
          ],
        },
        { id: 'dmac', name: 'dmac_330', kind: 'periph', label: 'DMA-330', x: 80, y: 440, w: 220, h: 100,
          params: [{k:'channels',v:'8'},{k:'data_w',v:'128'}],
          status: { ssot:'ok', rtl:'partial', sim:'pending' },
          addr: '0x0900_0000',
          interfaces: [
            { side:'top',    name:'S_APB', proto:'APB',  role:'slave',  width:32,  x:0.3 },
            { side:'top',    name:'M_AXI', proto:'AXI4', role:'master', width:128, x:0.7 },
            { side:'right',  name:'IRQ',   proto:'IRQ',  role:'master', width:8,   y:0.5 },
          ],
        },
      ],
    },

    {
      id: 'mem_ss', name: 'mem_ss', label: 'Memory Subsystem',
      x: 1100, y: 80, w: 360, h: 280,
      status: { ssot: 'ok', rtl: 'partial', sim: 'pending' },
      modules: [
        { id: 'ddrc', name: 'ddr_ctrl', kind: 'mem', label: 'DDR4 Controller', x: 24, y: 56, w: 156, h: 100,
          params: [{k:'spec',v:'DDR4-3200'},{k:'data_w',v:'64'},{k:'ranks',v:'2'}],
          status: { ssot:'ok', rtl:'partial', sim:'pending' },
          addr: '0x8000_0000 — 0xFFFF_FFFF (2 GB)',
          interfaces: [
            { side:'left',  name:'S_AXI',  proto:'AXI4',  role:'slave',  width:128, y:0.5 },
            { side:'right', name:'M_PHY',  proto:'DDRPHY',role:'master', width:64,  y:0.5 },
          ],
        },
        { id: 'sram', name: 'sram_64k', kind: 'mem', label: 'On-chip SRAM', x: 200, y: 56, w: 132, h: 100,
          params: [{k:'size',v:'64K'},{k:'ports',v:'1'}],
          status: { ssot:'ok', rtl:'ok', sim:'ok' },
          addr: '0x4000_0000 — 0x4000_FFFF',
          interfaces: [
            { side:'left',  name:'S_AXI', proto:'AXI4L', role:'slave', width:32, y:0.5 },
          ],
        },
        { id: 'rom', name: 'boot_rom', kind: 'mem', label: 'Boot ROM', x: 24, y: 176, w: 156, h: 76,
          params: [{k:'size',v:'32K'}],
          status: { ssot:'ok', rtl:'ok', sim:'ok' },
          addr: '0x0000_0000 — 0x0000_7FFF',
          interfaces: [
            { side:'left',  name:'S_AXI', proto:'AXI4L', role:'slave', width:32, y:0.5 },
          ],
        },
      ],
    },

    {
      id: 'periph_ss', name: 'periph_ss', label: 'Peripherals',
      x: 60, y: 540, w: 540, h: 460,
      status: { ssot: 'partial', rtl: 'partial', sim: 'pending' },
      modules: [
        { id: 'uart', name: 'uart_top', kind: 'periph', label: 'UART (PL011)', x: 24, y: 56, w: 156, h: 76,
          params: [{k:'baud',v:'≤4M'},{k:'fifo',v:'32'}],
          status: { ssot:'ok', rtl:'ok', sim:'ok' },
          addr: '0x4000_1000',
          interfaces: [
            { side:'left',  name:'S_APB', proto:'APB', role:'slave',  width:32, y:0.5 },
            { side:'right', name:'IRQ',   proto:'IRQ', role:'master', width:1,  y:0.5 },
          ],
        },
        { id: 'spi', name: 'spi_master', kind: 'periph', label: 'SPI Master', x: 200, y: 56, w: 156, h: 76,
          params: [{k:'cs',v:'4'},{k:'fifo',v:'16'}],
          status: { ssot:'ok', rtl:'partial', sim:'err' },
          addr: '0x4000_2000',
          interfaces: [
            { side:'left',  name:'S_APB', proto:'APB', role:'slave',  width:32, y:0.5 },
            { side:'right', name:'IRQ',   proto:'IRQ', role:'master', width:1,  y:0.5 },
          ],
        },
        { id: 'i2c', name: 'i2c_master', kind: 'periph', label: 'I²C Master', x: 376, y: 56, w: 140, h: 76,
          params: [{k:'speed',v:'1MHz'}],
          status: { ssot:'ok', rtl:'ok', sim:'ok' },
          addr: '0x4000_3000',
          interfaces: [
            { side:'left',  name:'S_APB', proto:'APB', role:'slave', width:32, y:0.5 },
          ],
        },
        { id: 'gpio', name: 'gpio_top', kind: 'periph', label: 'GPIO ×64', x: 24, y: 156, w: 156, h: 76,
          params: [{k:'pins',v:'64'}],
          status: { ssot:'ok', rtl:'ok', sim:'ok' },
          addr: '0x4000_4000',
          interfaces: [
            { side:'left',  name:'S_APB', proto:'APB', role:'slave', width:32, y:0.5 },
          ],
        },
        { id: 'tmr', name: 'timer_pl1', kind: 'periph', label: 'Timer ×4', x: 200, y: 156, w: 156, h: 76,
          params: [{k:'count',v:'4'},{k:'width',v:'64'}],
          status: { ssot:'ok', rtl:'ok', sim:'partial' },
          addr: '0x4000_5000',
          interfaces: [
            { side:'left',  name:'S_APB', proto:'APB', role:'slave',  width:32, y:0.5 },
            { side:'right', name:'IRQ',   proto:'IRQ', role:'master', width:4,  y:0.5 },
          ],
        },
        { id: 'wdt', name: 'wdt', kind: 'periph', label: 'Watchdog', x: 376, y: 156, w: 140, h: 76,
          params: [{k:'cycles',v:'2^32'}],
          status: { ssot:'ok', rtl:'ok', sim:'ok' },
          addr: '0x4000_6000',
          interfaces: [
            { side:'left', name:'S_APB', proto:'APB', role:'slave', width:32, y:0.5 },
          ],
        },
        { id: 'sec', name: 'sec_engine', kind: 'periph', label: 'Crypto / TRNG', x: 24, y: 256, w: 220, h: 92,
          params: [{k:'algos',v:'AES,SHA,RSA'},{k:'trng',v:'NIST 800-90B'}],
          status: { ssot:'partial', rtl:'pending', sim:'pending' },
          addr: '0x4001_0000',
          interfaces: [
            { side:'left',  name:'S_AXI', proto:'AXI4L',role:'slave',  width:32, y:0.5 },
            { side:'right', name:'IRQ',   proto:'IRQ',  role:'master', width:1,  y:0.5 },
          ],
        },
        { id: 'eth', name: 'eth_mac',  kind: 'periph', label: 'Ethernet MAC', x: 264, y: 256, w: 252, h: 92,
          params: [{k:'spec',v:'GMII'},{k:'speed',v:'1G'}],
          status: { ssot:'ok', rtl:'partial', sim:'pending' },
          addr: '0x4002_0000',
          interfaces: [
            { side:'left',  name:'S_AXI',  proto:'AXI4', role:'slave',  width:32,  y:0.4 },
            { side:'left',  name:'S_AXIS', proto:'AXIS', role:'slave',  width:64,  y:0.7 },
            { side:'right', name:'IRQ',    proto:'IRQ',  role:'master', width:2,   y:0.5 },
          ],
        },
      ],
    },

    {
      id: 'analog_ss', name: 'analog_ss', label: 'Analog / Mixed-Signal',
      x: 1100, y: 400, w: 360, h: 300,
      status: { ssot: 'partial', rtl: 'pending', sim: 'pending' },
      modules: [
        { id: 'pll', name: 'pll_top', kind: 'analog', label: 'PLL (1–2 GHz)', x: 24, y: 56, w: 156, h: 76,
          params: [{k:'fout',v:'1–2 GHz'},{k:'jitter',v:'<2 ps'}],
          status: { ssot:'ok', rtl:'partial', sim:'pending' },
          interfaces: [
            { side:'left',  name:'S_APB', proto:'APB',    role:'slave',  width:32, y:0.5 },
            { side:'right', name:'CLK_O', proto:'CLK',    role:'master', y:0.5 },
            { side:'bottom',name:'IO',    proto:'ANALOG', role:'master', x:0.5 },
          ],
        },
        { id: 'adc', name: 'adc_12b', kind: 'analog', label: 'ADC 12-bit', x: 200, y: 56, w: 132, h: 76,
          params: [{k:'res',v:'12b'},{k:'rate',v:'10MS/s'}],
          status: { ssot:'partial', rtl:'pending', sim:'pending' },
          addr: '0x4003_0000',
          interfaces: [
            { side:'left',  name:'S_APB', proto:'APB',    role:'slave',  width:32, y:0.5 },
            { side:'bottom',name:'AIN',   proto:'ANALOG', role:'slave',  x:0.5 },
          ],
        },
        { id: 'phy', name: 'usb_phy', kind: 'analog', label: 'USB 2.0 PHY', x: 24, y: 176, w: 308, h: 92,
          params: [{k:'spec',v:'UTMI+'},{k:'speed',v:'HS/FS/LS'}],
          status: { ssot:'ok', rtl:'pending', sim:'pending' },
          interfaces: [
            { side:'left',   name:'S_APB',proto:'APB',    role:'slave',  width:32, y:0.4 },
            { side:'left',   name:'UTMI', proto:'AXIS',   role:'slave',  width:8,  y:0.7 },
            { side:'bottom', name:'IO',   proto:'ANALOG', role:'master', x:0.5 },
          ],
        },
      ],
    },
  ],

  // Top-level bus connections — the lines drawn on canvas. Each is one
  // logical bus that gets bundled into a single thick wire on screen.
  // Endpoints reference cluster:module:interface_name.
  busses: [
    { id:'b1', proto:'ACE',   width:128, from:'cpu_ss/cpu0/M_AXI',     to:'cpu_ss/l2/S_ACE_0',     label:'cpu0 → L2', addr:null,            active:true },
    { id:'b2', proto:'ACE',   width:128, from:'cpu_ss/cpu1/M_AXI',     to:'cpu_ss/l2/S_ACE_1',     label:'cpu1 → L2', addr:null,            active:true },
    { id:'b3', proto:'AXI4',  width:128, from:'cpu_ss/l2/M_AXI',       to:'noc/cci/S_ACE',         label:'L2 → CCI',  addr:'0x0—0xFFFF_FFFF', active:true },
    { id:'b4', proto:'AXI4',  width:128, from:'noc/cci/M_AXI_0',       to:'mem_ss/ddrc/S_AXI',     label:'CCI → DDR', addr:'0x8000_0000—0xFFFF_FFFF', active:true },
    { id:'b5', proto:'AXI4',  width:32,  from:'noc/cci/M_AXI_1',       to:'mem_ss/sram/S_AXI',     label:'CCI → SRAM',addr:'0x4000_0000—0x4000_FFFF', active:false },
    { id:'b6', proto:'AXI4',  width:32,  from:'noc/cci/M_AXI_2',       to:'mem_ss/rom/S_AXI',      label:'CCI → ROM', addr:'0x0—0x7FFF',     active:false },
    { id:'b7', proto:'APB',   width:32,  from:'noc/cci/M_APB',         to:'noc/apb_br/S_AXI',      label:'AXI→APB',   addr:'0x4000_*',       active:true },
    { id:'b8', proto:'APB',   width:32,  from:'noc/apb_br/M_APB',      to:'periph_ss/uart/S_APB',  label:'→ UART',    addr:'0x4000_1000',    active:true },
    { id:'b9', proto:'APB',   width:32,  from:'noc/apb_br/M_APB',      to:'periph_ss/spi/S_APB',   label:'→ SPI',     addr:'0x4000_2000',    active:true, status:'err' },
    { id:'b10',proto:'APB',   width:32,  from:'noc/apb_br/M_APB',      to:'periph_ss/i2c/S_APB',   label:'→ I²C',     addr:'0x4000_3000',    active:false },
    { id:'b11',proto:'APB',   width:32,  from:'noc/apb_br/M_APB',      to:'periph_ss/gpio/S_APB',  label:'→ GPIO',    addr:'0x4000_4000',    active:false },
    { id:'b12',proto:'APB',   width:32,  from:'noc/apb_br/M_APB',      to:'periph_ss/tmr/S_APB',   label:'→ TIMER',   addr:'0x4000_5000',    active:false },
    { id:'b13',proto:'APB',   width:32,  from:'noc/apb_br/M_APB',      to:'periph_ss/wdt/S_APB',   label:'→ WDT',     addr:'0x4000_6000',    active:false },
    { id:'b14',proto:'AXI4L', width:32,  from:'noc/cci/M_AXI_2',       to:'periph_ss/sec/S_AXI',   label:'→ Crypto',  addr:'0x4001_0000',    active:false },
    { id:'b15',proto:'AXI4',  width:32,  from:'noc/cci/M_AXI_2',       to:'periph_ss/eth/S_AXI',   label:'→ ETH',     addr:'0x4002_0000',    active:false },
    { id:'b16',proto:'IRQ',   width:64,  from:'periph_ss/uart/IRQ',    to:'cpu_ss/gic/IRQ_M',      label:'IRQs → GIC',addr:null,            active:true, agg:true },
    { id:'b17',proto:'APB',   width:32,  from:'noc/apb_br/M_APB',      to:'analog_ss/pll/S_APB',   label:'→ PLL',     addr:'0x4003_*',       active:false },
    { id:'b18',proto:'APB',   width:32,  from:'noc/apb_br/M_APB',      to:'analog_ss/adc/S_APB',   label:'→ ADC',     addr:'0x4003_0000',    active:false },
    { id:'b19',proto:'CLK',   from:'analog_ss/pll/CLK_O',              to:'cpu_ss/cpu0/CLK',       label:'sysclk',    active:true },
  ],

  // Address map — flattened for the addr-map view
  addrMap: [
    { base: '0x0000_0000', size: '0x0000_8000',   region: 'BOOT_ROM',    target: 'mem_ss/rom' },
    { base: '0x0800_0000', size: '0x0010_0000',   region: 'GIC',         target: 'cpu_ss/gic' },
    { base: '0x0900_0000', size: '0x0001_0000',   region: 'DMAC',        target: 'noc/dmac' },
    { base: '0x4000_0000', size: '0x0001_0000',   region: 'SRAM',        target: 'mem_ss/sram' },
    { base: '0x4000_1000', size: '0x0000_1000',   region: 'UART',        target: 'periph_ss/uart' },
    { base: '0x4000_2000', size: '0x0000_1000',   region: 'SPI',         target: 'periph_ss/spi' },
    { base: '0x4000_3000', size: '0x0000_1000',   region: 'I2C',         target: 'periph_ss/i2c' },
    { base: '0x4000_4000', size: '0x0000_1000',   region: 'GPIO',        target: 'periph_ss/gpio' },
    { base: '0x4000_5000', size: '0x0000_1000',   region: 'TIMER',       target: 'periph_ss/tmr' },
    { base: '0x4000_6000', size: '0x0000_1000',   region: 'WDT',         target: 'periph_ss/wdt' },
    { base: '0x4001_0000', size: '0x0001_0000',   region: 'CRYPTO',      target: 'periph_ss/sec' },
    { base: '0x4002_0000', size: '0x0001_0000',   region: 'ETH_MAC',     target: 'periph_ss/eth' },
    { base: '0x4003_0000', size: '0x0001_0000',   region: 'ADC',         target: 'analog_ss/adc' },
    { base: '0x8000_0000', size: '0x8000_0000',   region: 'DDR',         target: 'mem_ss/ddrc' },
  ],

  // Per-module artifact tracker: ssot / rtl / sim files
  artifacts: {
    'spi_master': {
      ssot: { path: 'rtl/spi_master/spi_master.ssot.yaml', status: 'ok',  size: '1.2 KB', mtime: '2 min ago' },
      rtl:  { path: 'rtl/spi_master/spi_master.sv',        status: 'partial', size: '4.8 KB', mtime: '8 min ago' },
      sim:  { path: 'sim/spi_master/spi.vcd',              status: 'err',  size: '142 KB', mtime: '1 min ago', failures: 3 },
      ipxact:{ path:'rtl/spi_master/spi_master.ipxact.xml',status: 'ok',  size: '6.1 KB', mtime: '2 min ago' },
    },
    'uart_top': {
      ssot: { path: 'rtl/uart_top/uart_top.ssot.yaml', status: 'ok',  size: '0.9 KB', mtime: '1 hr ago' },
      rtl:  { path: 'rtl/uart_top/uart_top.sv',        status: 'ok',  size: '3.2 KB', mtime: '1 hr ago' },
      sim:  { path: 'sim/uart_top/uart.vcd',           status: 'ok',  size: '88 KB',  mtime: '1 hr ago', passing: 24 },
    },
  },

  // Simulated YAML view of a module's ssot.yaml — used in V4 / drill-in
  ssotYamlSpi: `# spi_master.ssot.yaml — IP-XACT-lite
component:
  vendor: atlas.io
  library: peripherals
  name: spi_master
  version: 0.4.2

parameters:
  - { name: NUM_CS,  type: int, default: 4 }
  - { name: FIFO_D,  type: int, default: 16 }
  - { name: DATA_W,  type: int, default: 8  }

ports:
  clk:    { dir: in,  width: 1 }
  rst_n:  { dir: in,  width: 1 }
  sclk:   { dir: out, width: 1 }
  mosi:   { dir: out, width: 1 }
  miso:   { dir: in,  width: 1 }
  cs_n:   { dir: out, width: NUM_CS }
  irq:    { dir: out, width: 1 }

busInterfaces:
  - name: S_APB
    proto: APB
    role: slave
    width: 32
    addressBlocks:
      - { name: regs, base: 0x0, range: 0x1000, usage: register }

memoryMap:
  - register: { name: CTRL,    offset: 0x000, width: 32, access: rw, fields: [EN, MSTR, CPOL, CPHA] }
  - register: { name: STATUS,  offset: 0x004, width: 32, access: ro, fields: [BUSY, TXFULL, RXEMPTY] }
  - register: { name: TXDATA,  offset: 0x008, width: 32, access: wo }
  - register: { name: RXDATA,  offset: 0x00C, width: 32, access: ro }
  - register: { name: BAUDDIV, offset: 0x010, width: 32, access: rw }

knownIssues:
  - id: BUG-007
    sev: high
    sym: "mosi → X at t≈110ns"
    state: investigating
    fix: "reset bit_cnt and shift_reg in COMPLETE state"
`,

  ipxactXmlSpi: `<?xml version="1.0" encoding="UTF-8"?>
<spirit:component xmlns:spirit="http://www.accellera.org/XMLSchema/SPIRIT/1685-2014">
  <spirit:vendor>atlas.io</spirit:vendor>
  <spirit:library>peripherals</spirit:library>
  <spirit:name>spi_master</spirit:name>
  <spirit:version>0.4.2</spirit:version>
  <spirit:busInterfaces>
    <spirit:busInterface>
      <spirit:name>S_APB</spirit:name>
      <spirit:busType spirit:vendor="amba.com" spirit:library="AMBA3" spirit:name="APB" spirit:version="r2p0_0"/>
      <spirit:slave><spirit:memoryMapRef spirit:memoryMapRef="regs_map"/></spirit:slave>
    </spirit:busInterface>
  </spirit:busInterfaces>
  <spirit:memoryMaps>
    <spirit:memoryMap>
      <spirit:name>regs_map</spirit:name>
      <spirit:addressBlock>
        <spirit:name>regs</spirit:name>
        <spirit:baseAddress>0x40002000</spirit:baseAddress>
        <spirit:range>0x1000</spirit:range>
        <spirit:width>32</spirit:width>
      </spirit:addressBlock>
    </spirit:memoryMap>
  </spirit:memoryMaps>
</spirit:component>`,
};

// quick lookup: cluster/module by qualified id → {cluster, module}
window.SOC_LOOKUP = (function () {
  const m = {};
  for (const c of window.SOC.clusters) {
    m[c.id] = { cluster: c, module: null };
    for (const mod of c.modules) {
      m[`${c.id}/${mod.id}`] = { cluster: c, module: mod };
    }
  }
  return m;
})();

// pin coords helper — given "cluster/module/iface", returns absolute
// {x,y,side,proto,role,label} for line drawing in the canvas.
window.pinAt = function pinAt(qualifiedRef) {
  const parts = qualifiedRef.split('/');
  const cluster = window.SOC.clusters.find(c => c.id === parts[0]);
  if (!cluster) return null;
  const mod = cluster.modules.find(m => m.id === parts[1]);
  if (!mod) return null;
  const iface = mod.interfaces.find(i => i.name === parts[2]);
  if (!iface) return null;
  const mAbsX = cluster.x + mod.x;
  const mAbsY = cluster.y + mod.y;
  let x = mAbsX, y = mAbsY;
  if (iface.side === 'left')   { x = mAbsX;          y = mAbsY + mod.h * (iface.y || 0.5); }
  if (iface.side === 'right')  { x = mAbsX + mod.w;  y = mAbsY + mod.h * (iface.y || 0.5); }
  if (iface.side === 'top')    { x = mAbsX + mod.w * (iface.x || 0.5); y = mAbsY; }
  if (iface.side === 'bottom') { x = mAbsX + mod.w * (iface.x || 0.5); y = mAbsY + mod.h; }
  return { x, y, side: iface.side, proto: iface.proto, role: iface.role, label: iface.name, width: iface.width };
};
