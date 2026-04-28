// data.jsx — shared mock data for both directions

const WORKSPACES = [
  {
    id: 'req_gen', name: 'req_gen', label: 'Requirements',
    role: 'Iterative requirement gathering with user',
    cmd: '/new-req', alias: 'nr',
    color: 'var(--magenta)',
    glyph: 'REQ',
    phase: 1,
    description: 'Phase 1–9 iterative discovery. Captures user intent, constraints, and acceptance criteria into <ip>_requirements.md.',
    output: 'req/<ip>_requirements.md',
  },
  {
    id: 'mas_gen', name: 'mas_gen', label: 'Micro Arch Spec',
    role: 'Section-by-section MAS authoring',
    cmd: '/new-ip', alias: 'ni',
    color: 'var(--cyan)',
    glyph: 'MAS',
    phase: 2,
    description: 'Authors MAS §1–§9 from requirements. Block diagram, register map, interfaces, FSM, DV plan.',
    output: 'mas/<ip>_mas.md',
  },
  {
    id: 'rtl_gen', name: 'rtl_gen', label: 'RTL Implementation',
    role: 'SystemVerilog RTL from MAS §2–§8',
    cmd: '/new-ip-rtl', alias: 'nir',
    color: 'var(--accent)',
    glyph: 'RTL',
    phase: 3,
    description: 'Generates synthesizable SystemVerilog with /lint built-in. Produces <ip>.sv and filelist.',
    output: 'rtl/<ip>.sv  ·  list/<ip>.f',
  },
  {
    id: 'tb_gen', name: 'tb_gen', label: 'Testbench',
    role: 'TB + test cases from MAS §9 DV Plan',
    cmd: '/new-ip-tb', alias: 'nit',
    color: 'var(--ok)',
    glyph: 'TB ',
    phase: 4,
    description: 'Generates testbench skeleton, drivers, monitors, and per-feature test cases.',
    output: 'tb/tb_<ip>.sv  ·  tc_<ip>.sv',
  },
  {
    id: 'sim', name: 'sim', label: 'Simulation',
    role: 'Compile + simulate + debug loop',
    cmd: '/compile', alias: 'c',
    color: 'var(--warn)',
    glyph: 'SIM',
    phase: 5,
    description: 'Compiles filelist, runs simulation, parses logs, and writes sim_report.txt.',
    output: 'sim/sim_report.txt',
  },
  {
    id: 'lint', name: 'lint', label: 'Lint Check',
    role: 'Verilator lint + fix loop',
    cmd: '/lint-all', alias: 'la',
    color: 'var(--err)',
    glyph: 'LNT',
    phase: 6,
    description: 'Runs Verilator lint over filelist, classifies findings, and proposes fixes.',
    output: 'lint/lint_report.txt',
  },
];

// Main flow: SSOT gen → RTL Gen → Lint → TB Gen (Sim)
const FLOW_STAGES = [
  { id: 'ssot',    label: 'SSOT Gen',         glyph: 'SSOT', cmd: '/new-ssot',    detail: 'SSOT Spec Detail',     color: 'var(--magenta)' },
  { id: 'rtl_gen', label: 'RTL Gen',          glyph: 'RTL',  cmd: '/new-ip-rtl',  detail: 'RTL Implementation Style', color: 'var(--accent)' },
  { id: 'lint',    label: 'Lint',             glyph: 'LNT',  cmd: '/lint-all',    detail: 'Lint Findings',        color: 'var(--err)' },
  { id: 'tb_gen',  label: 'TB Gen (Sim)',     glyph: 'TB',   cmd: '/new-ip-tb',   detail: 'TB Detail',            color: 'var(--ok)' },
];

const ACTIVE_IP = {
  name: 'spi_master',
  status: 'Lint → TB',
  pipeline: [
    { id: 'ssot',    state: 'done',    files: 1, when: '14:02', summary: 'SSOT v3 · 47 specs locked' },
    { id: 'rtl_gen', state: 'done',    files: 2, when: '15:24', summary: 'spi_master.sv · 412 lines' },
    { id: 'lint',    state: 'warn',    files: 1, when: '15:30', summary: '3 warn · 0 err' },
    { id: 'tb_gen',  state: 'active',  files: 2, when: '15:47', summary: 'tb + 12 tc generating…' },
  ],
};

const RECENT_IPS = [
  { name: 'spi_master',  status: 'active',   phase: 'tb_gen',  date: 'Today · 15:47', warn: 3, err: 0 },
  { name: 'apb_uart',    status: 'complete', phase: 'lint',    date: 'Yesterday',     warn: 0, err: 0 },
  { name: 'axi_dma',     status: 'sim_fail', phase: 'sim',     date: 'Apr 26',        warn: 2, err: 1 },
  { name: 'fifo_async',  status: 'complete', phase: 'lint',    date: 'Apr 24',        warn: 0, err: 0 },
  { name: 'i2c_slave',   status: 'paused',   phase: 'mas_gen', date: 'Apr 22',        warn: 0, err: 0 },
  { name: 'pwm_ctrl',    status: 'complete', phase: 'lint',    date: 'Apr 19',        warn: 1, err: 0 },
];

// deps: array of todo ids that must finish before this one can start.
// Used to render the Todo as a DAG.
const TODOS = [
  { id: 1, section: '§1', title: 'Overview & block diagram',     state: 'done',    deps: [],     detail: 'High-level role of spi_master, top-level ports, clock domains.' },
  { id: 2, section: '§2', title: 'Register map',                 state: 'done',    deps: [1],    detail: 'CTRL, STAT, DATA_TX, DATA_RX, BAUD_DIV, IRQ_EN.' },
  { id: 3, section: '§3', title: 'Interfaces (APB, SPI master)', state: 'done',    deps: [1],    detail: 'APB slave 32-bit, SPI master 4-wire (sclk, mosi, miso, ss_n).' },
  { id: 4, section: '§4', title: 'Clocking & reset',             state: 'done',    deps: [3],    detail: 'pclk only, async resetn, internal sclk via BAUD_DIV.' },
  { id: 5, section: '§5', title: 'FSM',                          state: 'active',  deps: [2,4],  detail: 'IDLE → LOAD → SHIFT → COMPLETE → IDLE. CPOL/CPHA matrix.' },
  { id: 6, section: '§6', title: 'Datapath',                     state: 'pending', deps: [5],    detail: 'TX/RX shift registers, FIFO depth, byte-count.' },
  { id: 7, section: '§7', title: 'Interrupts',                   state: 'pending', deps: [5],    detail: 'TX_EMPTY, RX_FULL, TRANSFER_DONE.' },
  { id: 8, section: '§8', title: 'Performance',                  state: 'pending', deps: [6],    detail: 'Max sclk, latency budget, throughput target.' },
  { id: 9, section: '§9', title: 'DV Plan',                      state: 'pending', deps: [6,7],  detail: 'Coverage points, test list, scenarios.' },
];

const FILE_TREE = [
  { type: 'dir',  name: 'spi_master/', expanded: true, depth: 0 },
  { type: 'dir',  name: 'req/',        expanded: true, depth: 1 },
  { type: 'file', name: 'spi_master_requirements.md', depth: 2, ext: 'md', size: '7.2K' },
  { type: 'dir',  name: 'mas/',        expanded: true, depth: 1 },
  { type: 'file', name: 'spi_master_mas.md', depth: 2, ext: 'md', size: '14.8K', active: true },
  { type: 'dir',  name: 'rtl/',        expanded: true, depth: 1 },
  { type: 'file', name: 'spi_master.sv', depth: 2, ext: 'sv', size: '11.4K' },
  { type: 'dir',  name: 'list/',       expanded: false, depth: 1 },
  { type: 'dir',  name: 'tb/',         expanded: true, depth: 1 },
  { type: 'file', name: 'tb_spi_master.sv', depth: 2, ext: 'sv', size: '4.1K', dim: true },
  { type: 'file', name: 'tc_spi_master.sv', depth: 2, ext: 'sv', size: '0.8K', dim: true },
  { type: 'dir',  name: 'sim/',        expanded: false, depth: 1 },
  { type: 'dir',  name: 'lint/',       expanded: true, depth: 1 },
  { type: 'file', name: 'lint_report.txt', depth: 2, ext: 'txt', size: '2.1K' },
];

const REACT_LOG = [
  { kind: 'user', text: '/new-ip-tb spi_master' },
  { kind: 'thought', text: 'User wants TB generation for spi_master. I should read MAS §9 (DV Plan) first to extract coverage points and test scenarios, then scaffold tb_<ip>.sv with clk/reset, BFM hooks, and one tc_<ip>.sv per scenario.' },
  { kind: 'action', tool: 'read_file', args: { path: 'spi_master/mas/spi_master_mas.md', section: '§9' } },
  { kind: 'obs',  text: 'OK · 312 lines read · §9 DV Plan: 12 scenarios, 4 coverage groups, target 95% functional coverage.' },
  { kind: 'thought', text: 'Twelve scenarios: cpol/cpha matrix (4), back-to-back transfers, multi-slave SS, FIFO overflow, baud-rate edge cases, irq assert/deassert, reset mid-transfer, register-access via APB. I\'ll generate tb_spi_master.sv with a class-based environment and one tc per scenario.' },
  { kind: 'action', tool: 'write_file', args: { path: 'spi_master/tb/tb_spi_master.sv', lines: 184 } },
  { kind: 'obs',  text: 'OK · tb_spi_master.sv (184 lines) · APB BFM, SPI slave model, monitor, scoreboard hooks.' },
  { kind: 'action', tool: 'write_file', args: { path: 'spi_master/tb/tc_spi_master.sv', lines: 96 } },
  { kind: 'obs',  text: 'OK · tc_spi_master.sv (96 lines) · 12 test cases registered.' },
  { kind: 'thought', text: 'Generation complete. Recommend running /sim to validate compilation, then iterate on any failing scenarios.' },
];

const SLASH_COMMANDS = [
  { cmd: '/new-ip-tb',    alias: 'nit', desc: 'Generate testbench from MAS §9 DV Plan' },
  { cmd: '/legacy-ip-tb', alias: 'lit', desc: 'Update TB for legacy IP regression' },
  { cmd: '/sim',          alias: 's',   desc: 'Run simulation with current TB' },
  { cmd: '/compile',      alias: 'c',   desc: 'Compile filelist only (no run)' },
  { cmd: '/lint',         alias: 'l',   desc: 'Lint current RTL' },
  { cmd: '/todo',         alias: 't',   desc: 'Show / edit todo list' },
  { cmd: '/plan',         alias: 'p',   desc: 'Show current plan' },
  { cmd: '/workspace',    alias: 'w',   desc: 'Switch workspace (req_gen / mas_gen / …)' },
  { cmd: '/compact',      alias: 'cp',  desc: 'Compact conversation context' },
  { cmd: '/help',         alias: 'h',   desc: 'List all commands' },
];

const DIFF_LINES = [
  { kind: 'ctx', n: 142, t: '  // ── FSM: spi_master transfer cycle ──' },
  { kind: 'ctx', n: 143, t: '  typedef enum logic [1:0] {' },
  { kind: 'del', n: 144, t: '    IDLE, SHIFT, DONE' },
  { kind: 'add', n: 144, t: '    IDLE, LOAD, SHIFT, COMPLETE' },
  { kind: 'ctx', n: 145, t: '  } state_t;' },
  { kind: 'ctx', n: 146, t: '' },
  { kind: 'ctx', n: 147, t: '  state_t cur, nxt;' },
  { kind: 'ctx', n: 148, t: '' },
  { kind: 'ctx', n: 149, t: '  always_ff @(posedge pclk or negedge resetn) begin' },
  { kind: 'del', n: 150, t: '    if (!resetn) cur <= IDLE;' },
  { kind: 'add', n: 150, t: '    if (!resetn) begin' },
  { kind: 'add', n: 151, t: '      cur     <= IDLE;' },
  { kind: 'add', n: 152, t: '      bit_cnt <= \'0;' },
  { kind: 'add', n: 153, t: '    end' },
  { kind: 'ctx', n: 151, t: '    else cur <= nxt;' },
  { kind: 'ctx', n: 152, t: '  end' },
];

const LINT_FINDINGS = [
  { sev: 'warn', code: 'WIDTHEXPAND', file: 'spi_master.sv', line: 87,  msg: 'Operator ASSIGN expects 8 bits on RHS, got 4', fixable: true },
  { sev: 'warn', code: 'UNUSED',      file: 'spi_master.sv', line: 124, msg: 'Signal is not used: \'cpha_sync_d2\'', fixable: true },
  { sev: 'warn', code: 'CASEINCOMPLETE', file: 'spi_master.sv', line: 198, msg: 'Case values not handled: COMPLETE', fixable: false },
  { sev: 'info', code: 'STYLE',       file: 'spi_master.sv', line: 41,  msg: 'Module port list could be one-per-line', fixable: true },
];

const CONTEXT = {
  model: 'claude-sonnet-4',
  tokens: 47218,
  tokensMax: 200000,
  iter: 14,
  iterMax: 100,
  rate: '5s',
  safe: true,
};

// Q&A flows — one per stage. Each has a sequence of questions.
// Question kinds: 'multi' (checkbox), 'single' (radio), 'input' (text), 'submit'
const QA_FLOWS = {
  ssot: {
    stage: 'SSOT Gen',
    stageDetail: 'SSOT Spec Detail',
    title: 'SSOT · spi_master · Step 3 / 7',
    step: 3, total: 7,
    breadcrumbs: ['Overview', 'Use Case', 'Interface', 'Clocking', 'Registers', 'FSM', 'Acceptance'],
    activeBreadcrumb: 2,
    question: 'Which interfaces should be exposed in the SSOT?',
    subtitle: 'Multi-select. Each selection adds a port group to the SSOT and is locked once submitted.',
    kind: 'multi',
    options: [
      { id: 'apb',  label: 'APB slave (32-bit)',     detail: 'pclk, paddr, pwdata, prdata, pready, psel, penable.', selected: true },
      { id: 'ahb',  label: 'AHB-Lite slave',          detail: 'Higher throughput · hclk, haddr, hwdata, hrdata.',     selected: false },
      { id: 'axi',  label: 'AXI4-Lite slave',         detail: 'Full handshake · aw/w/b/ar/r channels.',                selected: false },
      { id: 'spi',  label: 'SPI master 4-wire',       detail: 'sclk, mosi, miso, ss_n[N-1:0]. Required by spec name.', selected: true, locked: true },
      { id: 'irq',  label: 'Interrupt line',          detail: 'irq · level-high · TX_EMPTY | RX_FULL | DONE.',         selected: true },
      { id: 'dma',  label: 'DMA req/ack pair',        detail: 'tx_dreq, rx_dreq, dack — for high-rate streaming.',    selected: false },
    ],
    history: [
      { step: 1, title: 'Overview',  answer: 'SPI master controller · single-master · up to 4 CS' },
      { step: 2, title: 'Use case',  answer: 'Sensor polling · flash config · low-latency burst' },
    ],
    upcoming: [
      { step: 4, title: 'Clocking & reset' },
      { step: 5, title: 'Register map' },
      { step: 6, title: 'FSM / datapath' },
      { step: 7, title: 'Acceptance' },
    ],
  },
  rtl_gen: {
    stage: 'RTL Gen',
    stageDetail: 'RTL Implementation Style',
    title: 'RTL · spi_master · Step 1 / 4',
    step: 1, total: 4,
    breadcrumbs: ['Style', 'Coding rules', 'Power/Reset', 'Confirm'],
    activeBreadcrumb: 0,
    question: 'Pick the RTL implementation style.',
    subtitle: 'Single-select. Drives module decomposition and naming conventions.',
    kind: 'single',
    options: [
      { id: 'monolithic', label: 'Monolithic',              detail: 'Single module · fastest to lint · OK for small IP.', selected: false },
      { id: 'hier',       label: 'Hierarchical',            detail: 'Top + per-feature submodules (datapath / fsm / cfg).', selected: true },
      { id: 'pipelined',  label: 'Pipelined w/ skid',       detail: 'Adds skid buffers for timing closure on >200 MHz.',     selected: false },
      { id: 'param',      label: 'Parameterized template',  detail: 'Width/depth/CS-count exposed as parameters.',           selected: false },
    ],
    history: [],
    upcoming: [
      { step: 2, title: 'Coding rules (always_ff / always_comb)' },
      { step: 3, title: 'Power & reset strategy' },
      { step: 4, title: 'Confirm & generate' },
    ],
  },
  tb_gen: {
    stage: 'TB Gen',
    stageDetail: 'TB Detail',
    title: 'TB · spi_master · Step 2 / 5',
    step: 2, total: 5,
    breadcrumbs: ['Methodology', 'Scenarios', 'Coverage', 'Stimulus', 'Confirm'],
    activeBreadcrumb: 1,
    question: 'Which test scenarios should be generated?',
    subtitle: 'Multi-select. Each generates one tc_<ip>.sv entry.',
    kind: 'multi',
    options: [
      { id: 'cpol_cpha', label: 'CPOL/CPHA matrix (4)',       detail: 'All four mode combinations · sanity transfer each.',      selected: true },
      { id: 'b2b',       label: 'Back-to-back transfers',     detail: 'No-gap consecutive bytes · validate FIFO drain.',         selected: true },
      { id: 'multi_cs',  label: 'Multi-slave CS rotation',     detail: 'Round-robin across ss_n[3:0] · expect mutual exclusion.', selected: true },
      { id: 'fifo_ovr',  label: 'FIFO overflow',               detail: 'Force overflow · expect status bit + IRQ.',                selected: false },
      { id: 'baud',      label: 'Baud-rate edges',             detail: 'Min/max/odd dividers · check sclk integrity.',             selected: true },
      { id: 'reset_mid', label: 'Reset mid-transfer',          detail: 'Async reset during SHIFT · expect clean IDLE.',            selected: false },
      { id: 'apb_reg',   label: 'APB register access',         detail: 'R/W coverage on every CTRL/STAT bit.',                     selected: true },
    ],
    history: [
      { step: 1, title: 'Methodology',  answer: 'Class-based · UVM-lite · scoreboard + monitor' },
    ],
    upcoming: [
      { step: 3, title: 'Coverage groups' },
      { step: 4, title: 'Stimulus generation' },
      { step: 5, title: 'Confirm & generate' },
    ],
  },
};

const QA_FLOW = QA_FLOWS.ssot;
window.QA_FLOWS = QA_FLOWS;

window.QA_FLOW = QA_FLOW;
window.WORKSPACES = WORKSPACES;
window.ACTIVE_IP = ACTIVE_IP;
window.RECENT_IPS = RECENT_IPS;
window.TODOS = TODOS;
window.FILE_TREE = FILE_TREE;
window.REACT_LOG = REACT_LOG;
window.SLASH_COMMANDS = SLASH_COMMANDS;
window.DIFF_LINES = DIFF_LINES;
window.LINT_FINDINGS = LINT_FINDINGS;
window.CONTEXT = CONTEXT;
window.FLOW_STAGES = FLOW_STAGES;
