// ssot-digest-content.tsx — TypeScript migration of ssot-digest-content.jsx.
//
// ssot-digest-content.jsx — Phase 22 refactor: SsotDigestContent
// extracted from ssot-digest.jsx so the latter drops well under 1000.
// This is the main render component for the SSOT digest pane;
// SsotReviewPane (sibling, ssot-review.jsx) wraps it.
//
// Migration notes (vs ssot-digest-content.jsx):
//   - Proper ES module: no in-browser-babel IIFE wrapper; statements run at
//     module scope (preserving original order so the window.X bridge still
//     executes). The original was wrapped in `(() => { ... })()`.
//   - React hooks are imported (`useMemo`) instead of read off the ambient
//     global `React`; `React.useMemo` becomes the imported `useMemo`.
//   - Cross-file globals OWNED BY OTHER FILES (the ~40 lambda forward-refs,
//     plus sectionFact which is owned by workspace.jsx) live in the sibling
//     ssot-digest-content-globals.tsx and resolve `window.X` at call time.
//   - The per-view render functions live in the sibling
//     ssot-digest-content-renderers.tsx (buildRenderers(ctx)); this file
//     computes the derived `ctx` and dispatches on view.id. Sub-1000 split.
//   - This file's OWN public global (SsotDigestContent) becomes a real export
//     plus a transitional window.* bridge at the bottom for not-yet-migrated
//     .jsx consumers.
import { useMemo } from 'react';
import {
  win,
  type SsotDigestContentProps,
  DigestSourceSections,
  SsotCommandPalette,
  blockField,
  buildReferenceTokens,
  compactDigestItems,
  extractFeatures,
  extractFsms,
  extractModuleContracts,
  extractRegisters,
  extractReviewInterfaces,
  extractReviewPins,
  extractScenarios,
  extractSubmodules,
  listBlocksFromSection,
  mapGroupsFromSection,
  sectionByKey,
  sectionFact,
  sourceSectionsForDigestView,
  ssotTitleFor,
  ssotValuePresent,
} from './ssot-digest-content-globals';
import { buildRenderers } from './ssot-digest-content-renderers';

const SsotDigestContent = ({ view, sections, statusByKey, uiLang = 'ko', content = '', selected = '', onJump, feedbackMode = false }: SsotDigestContentProps) => {
  const t = uiLang === 'en'
    ? { sourceSections: 'Source section review', ports: 'ports', fields: 'fields' }
    : { sourceSections: '원본 섹션 리뷰', ports: 'ports', fields: 'fields' };
  const top = sectionByKey(sections, 'top_module');
  const io = sectionByKey(sections, 'io_list');
  const featuresSection = sectionByKey(sections, 'features');
  const submodsSection = sectionByKey(sections, 'sub_modules');
  const decompSection = sectionByKey(sections, 'decomposition');
  const functionSection = sectionByKey(sections, 'function_model');
  const cycleSection = sectionByKey(sections, 'cycle_model');
  const timingSection = sectionByKey(sections, 'timing');
  const registersSection = sectionByKey(sections, 'registers')
    || sectionByKey(sections, 'memoryMap')
    || sectionByKey(sections, 'memory_map')
    || (sections || []).find((s: any) => /register|memory_?map/i.test(s.key || ''));
  const dataflowSection = sectionByKey(sections, 'dataflow');
  const clockSection = sectionByKey(sections, 'clock_reset_domains')
    || sectionByKey(sections, 'clock_reset')
    || sectionByKey(sections, 'clocks');
  const cdcSection = sectionByKey(sections, 'cdc_requirements');
  const rdcSection = sectionByKey(sections, 'rdc_requirements');
  const memorySection = sectionByKey(sections, 'memory');
  const interruptsSection = sectionByKey(sections, 'interrupts');
  const fsmSection = sectionByKey(sections, 'fsm');
  const errorsSection = sectionByKey(sections, 'errors') || sectionByKey(sections, 'error_handling');
  const parametersSection = sectionByKey(sections, 'parameters')
    || sectionByKey(sections, 'top_module_parameters')
    || sectionByKey(sections, 'module_parameters')
    || sectionByKey(sections, 'parameter_list')
    || sectionByKey(sections, 'default_parameters')
    || (sections || []).find((s: any) => /parameter/i.test(s.key || ''));
  // Extract `parameters` blocks → [{name, default, description}]. SSOT
  // shapes seen in the wild:
  //   • parameters: ─ list of {name, default, description, …}
  //   • top_module: ─ {parameters: [...]}
  //   • parameters: as a flat key=value mapping at section root
  //   • module_parameters / parameter_list / default_parameters
  //   • freeform "NUM_PINS = 32" lines inside a parameters paragraph
  // We try them in order and stop at the first hit so an IP that uses
  // any of these shapes ends up with parameter chips on the diagram.
  const parameters = (() => {
    const collect = (blocks: any) => blocks.map((b: any) => ({
      name: blockField(b, 'name') || blockField(b, 'key') || blockField(b, 'param') || '',
      value: blockField(b, 'default') || blockField(b, 'value') || blockField(b, 'default_value') || blockField(b, 'val') || '',
      description: blockField(b, 'description', 200),
    })).filter((p: any) => p.name);
    // 1) blocks under the standalone `parameters` section
    let rows = collect(listBlocksFromSection(parametersSection));
    // 2) blocks nested under top_module.parameters
    if (!rows.length) rows = collect(listBlocksFromSection(top, 'parameters'));
    // 3) blocks under `top_module.params` (alternative key)
    if (!rows.length) rows = collect(listBlocksFromSection(top, 'params'));
    // 4) flat KEY: VALUE pairs inside the parameters section text — last
    //    ditch effort for IPs that flatten the parameter list instead of
    //    wrapping each entry in its own `- name: …` block. Only catches
    //    SystemVerilog-style identifiers (UPPER_SNAKE_CASE) so we don't
    //    misread random doc paragraphs as parameters.
    if (!rows.length && parametersSection && parametersSection.text) {
      const seen = new Set();
      const flat = [];
      const re = /^[\s-]*([A-Z_][A-Z0-9_]{2,})\s*[:=]\s*([^\n#]+?)\s*$/gm;
      let m;
      while ((m = re.exec(parametersSection.text)) !== null) {
        const name = m[1];
        if (seen.has(name)) continue;
        seen.add(name);
        flat.push({ name, value: m[2].trim().replace(/^["']|["']$/g, ''), description: '' });
      }
      rows = flat;
    }
    return rows;
  })();

  const interfaces = extractReviewInterfaces(sections, io);
  const diagramPins = extractReviewPins(io, interruptsSection);
  const parsedFeatures = extractFeatures(featuresSection);
  const featureSections = (sections || []).filter((section: any) => (
    section !== featuresSection
    && /feature|fifo|fsm|generation|arbitration|ack|interrupt|open_drain|access|bit_control|start_stop/i.test(section.key || '')
  ));
  const features = parsedFeatures.length ? parsedFeatures : featureSections.slice(0, 12).map((section: any) => ({
    name: ssotTitleFor(section.key),
    trigger: sectionFact(section, 'trigger') || sectionFact(section, 'condition') || sectionFact(section, 'source'),
    datapath: sectionFact(section, 'datapath') || sectionFact(section, 'description') || sectionFact(section, 'implementation') || sectionFact(section, 'logic'),
    control: sectionFact(section, 'control') || sectionFact(section, 'response') || sectionFact(section, 'timing'),
    output: sectionFact(section, 'output') || sectionFact(section, 'result') || sectionFact(section, 'description'),
    sourceKey: section.key,
  }));
  const rawSubmods = extractSubmodules(submodsSection);
  const moduleContracts = extractModuleContracts(decompSection);
  const submods = rawSubmods.length ? rawSubmods : moduleContracts.map((contract: any) => ({
    name: contract.module,
    file: '',
    description: contract.implementation,
    implements: contract.owns,
    sourceSections: [],
    interfaces: contract.interfaces,
  }));
  const contractByModule = moduleContracts.reduce((acc: any, contract: any) => {
    if (contract.module) acc[contract.module] = contract;
    return acc;
  }, {});
  const registers = extractRegisters(registersSection);
  const registerConfig = {
    addrWidth: sectionFact(registersSection, 'addr_width') || sectionFact(registersSection, 'address_width'),
    dataWidth: sectionFact(registersSection, 'register_width') || sectionFact(registersSection, 'data_width'),
    byteAddressable: sectionFact(registersSection, 'byte_addressable'),
  };
  const noRegisterPolicy = (() => {
    if (!registersSection) return '';
    const hasPolicy = ['no_registers', 'no_csr', 'no_register_map']
      .some(key => ssotValuePresent(sectionFact(registersSection, key)));
    if (!hasPolicy) return '';
    return sectionFact(registersSection, 'reason', '')
      || sectionFact(registersSection, 'policy', '')
      || sectionFact(registersSection, 'description', '')
      || sectionFact(registersSection, 'access_model', '')
      || 'Explicit no-register policy declared.';
  })();
  const clockDomains = listBlocksFromSection(clockSection, 'domains').map((block: any) => ({
    name: blockField(block, 'name'),
    frequency: blockField(block, 'frequency_mhz'),
    description: blockField(block, 'description', 260),
  }));
  const resets = listBlocksFromSection(io, 'resets').map((block: any) => ({
    name: blockField(block, 'name'),
    polarity: blockField(block, 'polarity'),
    type: blockField(block, 'sync_async') || blockField(block, 'type'),
    description: blockField(block, 'description', 220),
  }));
  const cdcCrossings = listBlocksFromSection(cdcSection, 'crossings').map((block: any) => ({
    name: blockField(block, 'name'),
    from: blockField(block, 'source_domain'),
    to: blockField(block, 'dest_domain'),
    synchronizer: blockField(block, 'synchronizer'),
    description: blockField(block, 'description', 260),
  }));
  const fsmMachines = extractFsms(fsmSection);
  const noFsmPolicy = (() => {
    if (!fsmSection) return '';
    const hasPolicy = ['no_fsm', 'no_state_machine', 'combinational_only']
      .some(key => ssotValuePresent(sectionFact(fsmSection, key)));
    if (!hasPolicy) return '';
    return sectionFact(fsmSection, 'reason', '')
      || sectionFact(fsmSection, 'policy', '')
      || sectionFact(fsmSection, 'description', '')
      || 'Explicit no-FSM policy declared.';
  })();
  const irqs = useMemo(() => {
    const blocks = ([] as any[])
      .concat(listBlocksFromSection(interruptsSection, 'interrupt_list'))
      .concat(listBlocksFromSection(interruptsSection, 'list'))
      .concat(listBlocksFromSection(interruptsSection));
    return blocks
      .map(b => ({
        name: blockField(b, 'name') || blockField(b, 'id') || '',
        polarity: blockField(b, 'polarity'),
        mask: blockField(b, 'mask') || blockField(b, 'enable'),
        description: blockField(b, 'description', 240),
      }))
      .filter(e => e.name);
  }, [interruptsSection]);
  const refTokenMap = useMemo(
    () => buildReferenceTokens({ registers, features, fsmMachines, irqs }),
    [registers, features, fsmMachines, irqs]
  );
  const paletteScenarios = useMemo(() => extractScenarios(sections), [sections]);
  const paletteItems = useMemo(() => {
    const out: any[] = [];
    (registers || []).forEach((reg: any) => {
      out.push({
        kind: 'register',
        label: reg.name || '(reg)',
        detail: [reg.offset && `@ ${reg.offset}`, reg.access].filter(Boolean).join(' · '),
        viewId: 'registers',
      });
      (reg.fields || []).forEach((f: any) => {
        if (!f.name) return;
        out.push({
          kind: 'field',
          label: `${reg.name}.${f.name}`,
          detail: [f.bits && `bits ${f.bits}`, f.access].filter(Boolean).join(' · '),
          viewId: 'registers',
        });
      });
    });
    (features || []).forEach((feat: any) => {
      out.push({
        kind: 'feature',
        label: feat.name || '(feature)',
        detail: String(feat.description || feat.datapath || feat.trigger || '').slice(0, 80),
        viewId: 'features',
      });
    });
    (fsmMachines || []).forEach((m: any) => {
      (m.states || []).forEach((s: any) => {
        const label = String(s).trim();
        if (!label) return;
        out.push({
          kind: 'state',
          label,
          detail: `FSM ${m.name || ''}${String(m.resetState || '').trim() === label ? ' · reset' : ''}`,
          viewId: 'fsm',
        });
      });
    });
    (irqs || []).forEach((irq: any) => {
      out.push({
        kind: 'interrupt',
        label: irq.name,
        detail: String(irq.description || '').slice(0, 80),
        viewId: 'overview',
      });
    });
    (interfaces || []).forEach((iface: any) => {
      out.push({
        kind: 'interface',
        label: iface.name || '(iface)',
        detail: [iface.type, iface.role && `role ${iface.role}`].filter(Boolean).join(' · '),
        viewId: 'interfaces',
      });
    });
    (paletteScenarios || []).forEach((scn: any) => {
      out.push({
        kind: 'scenario',
        label: scn.name,
        detail: String(scn.summary || '').slice(0, 80),
        viewId: 'scenarios',
      });
    });
    return out;
  }, [registers, features, fsmMachines, irqs, interfaces, paletteScenarios]);
  const dataflowGroups = mapGroupsFromSection(dataflowSection).filter((g: any) => g.key !== 'locked_decisions');
  const transactions = listBlocksFromSection(functionSection, 'transactions');
  const stateVars = listBlocksFromSection(functionSection, 'state_variables');
  const latencyGroups = mapGroupsFromSection(cycleSection, 'latency');
  const handshakeRules = listBlocksFromSection(cycleSection, 'handshake_rules');
  const pipeline = listBlocksFromSection(cycleSection, 'pipeline');
  const topName = sectionFact(top, 'name') || sectionFact(top, 'module') || (top && top.value) || 'SSOT';

  const header = (
    <div style={{ marginBottom: 12 }}>
      <div style={{ color: 'var(--magenta)', fontWeight: 900, fontSize: 18, letterSpacing: 0 }}>
        {topName}
      </div>
      <div style={{ color: 'var(--fg)', lineHeight: 1.45, marginTop: 4, maxWidth: 920 }}>
        {sectionFact(top, 'description', 'No top_module.description available yet.')}
      </div>
    </div>
  );

  const featureTokens = (feature: any) => String([
    feature && feature.name,
    feature && feature.sourceKey,
    feature && feature.trigger,
    feature && feature.datapath,
  ].filter(Boolean).join(' '))
    .toLowerCase()
    .split(/[^a-z0-9_]+/)
    .filter(token => token.length > 2 && !['the', 'and', 'with', 'for'].includes(token))
    .slice(0, 8);

  const matchesFeature = (text: any, tokens: any) => {
    const hay = String(text || '').toLowerCase();
    return (tokens || []).some((token: any) => hay.includes(token));
  };

  const namesForFeature = (rows: any, tokens: any, nameOf: any, textOf: any, limit = 5) => (rows || [])
    .filter((row: any) => matchesFeature(textOf(row), tokens))
    .map(nameOf)
    .filter(Boolean)
    .slice(0, limit);

  const semanticSectionNames = (rx: any, limit = 6) => (sections || [])
    .filter((section: any) => rx.test(section.key || ''))
    .map((section: any) => ssotTitleFor(section.key))
    .slice(0, limit);

  const statusForPresence = (present: any) => present ? 'approved' : 'needs_review';
  const coverageRows = [
    { label: 'Top module', status: statusForPresence(!!top), detail: topName },
    { label: 'Feature map', status: statusForPresence(features.length > 0), detail: `${features.length} features` },
    { label: 'Architecture', status: statusForPresence(submods.length > 0 || moduleContracts.length > 0), detail: `${submods.length || moduleContracts.length} modules` },
    { label: 'Interfaces', status: statusForPresence(interfaces.length > 0), detail: `${interfaces.length} interfaces` },
    { label: 'Function model', status: statusForPresence(!!functionSection || semanticSectionNames(/function|fsm|logic|state/i, 1).length > 0), detail: functionSection ? 'function_model' : compactDigestItems(semanticSectionNames(/function|fsm|logic|state/i, 3), 3) },
    { label: 'FSM', status: statusForPresence(fsmMachines.length > 0 || !!noFsmPolicy), detail: fsmMachines.length ? `${fsmMachines.length} machines` : (noFsmPolicy ? 'explicit no-FSM policy' : compactDigestItems(semanticSectionNames(/fsm|state|transition/i, 3), 3)) },
    { label: 'Cycle model', status: statusForPresence(!!cycleSection || !!timingSection || semanticSectionNames(/cycle|timing|latency|scl/i, 1).length > 0), detail: cycleSection ? 'cycle_model' : compactDigestItems(semanticSectionNames(/cycle|timing|latency|scl/i, 3), 3) },
    { label: 'Register map', status: statusForPresence(registers.length > 0 || !!noRegisterPolicy), detail: registers.length ? `${registers.length} registers` : (noRegisterPolicy ? 'explicit no-register policy' : '0 registers') },
    { label: 'Dataflow', status: statusForPresence(dataflowGroups.length > 0 || semanticSectionNames(/dataflow|flow|fifo|buffer|open_drain|access/i, 1).length > 0), detail: dataflowGroups.length ? `${dataflowGroups.length} flows` : compactDigestItems(semanticSectionNames(/dataflow|flow|fifo|buffer|open_drain|access/i, 3), 3) },
  ];

  const sourceSections = sourceSectionsForDigestView(view, sections);
  const scenarios = useMemo(() => extractScenarios(sections), [sections]);

  const renderers = buildRenderers({
    header, sections, statusByKey, t, onJump, selected, content, feedbackMode,
    top, topName, clockSection, functionSection, cycleSection, timingSection,
    fsmSection, rdcSection, decompSection, parameters, submods, moduleContracts,
    contractByModule, features, featureSections, interfaces, diagramPins,
    registers, registerConfig, noRegisterPolicy, noFsmPolicy, fsmMachines,
    dataflowGroups, transactions, stateVars, latencyGroups, handshakeRules,
    pipeline, clockDomains, resets, cdcCrossings, coverageRows, refTokenMap,
    scenarios, featureTokens, matchesFeature, namesForFeature, semanticSectionNames,
  });

  let body;
  if (view.id === 'overview') body = renderers.renderOverview();
  else if (view.id === 'scenarios') body = renderers.renderScenarios();
  else if (view.id === 'features') body = renderers.renderFeatures();
  else if (view.id === 'architecture') body = renderers.renderArchitecture();
  else if (view.id === 'feature_map') body = renderers.renderFeatureMap();
  else if (view.id === 'function_model') body = renderers.renderFunctionModel();
  else if (view.id === 'fsm') body = renderers.renderFsm();
  else if (view.id === 'cycle_model') body = renderers.renderCycleModel();
  else if (view.id === 'interfaces') body = renderers.renderInterfaces();
  else if (view.id === 'registers') body = renderers.renderRegisters();
  else if (view.id === 'dataflow') body = renderers.renderDataflow();
  else if (view.id === 'clocking') body = renderers.renderClocking();
  else if (view.id === 'review_gaps') body = renderers.renderReviewGaps();
  else if (view.id === 'gates') body = renderers.renderGates();
  else if (view.id === 'raw_yaml') body = renderers.renderRawYaml();
  else body = renderers.renderGeneric(view.label, sourceSections);

  return (
    <>
      {body}
      {!['architecture', 'overview', 'scenarios', 'review_gaps', 'raw_yaml', 'gates'].includes(view.id) ? (
        <DigestSourceSections view={view} sections={sections} statusByKey={statusByKey} t={t} />
      ) : null}
      <SsotCommandPalette items={paletteItems} onJump={onJump} />
      <div style={{
        position: 'fixed', right: 16, bottom: 14, zIndex: 50,
        padding: '4px 10px', borderRadius: 999,
        background: 'color-mix(in oklch, var(--bg-2) 70%, transparent)',
        border: '1px solid var(--line)', color: 'var(--fg-mute)',
        fontFamily: 'var(--mono)', fontSize: 10, pointerEvents: 'none',
        backdropFilter: 'blur(2px)',
      }}>
        ⌘K  jump
      </div>
    </>
  );
};

// ── Transitional bridge: register on window for not-yet-migrated .jsx ──
// SsotDigestContent is not (yet) declared on the ambient Window (it lives in
// the local SsotDigestContentWindow cast in ssot-digest-content-globals.tsx),
// so write it through `win` — same pattern as block-diagram.tsx's
// `win.BlockDiagram = BlockDiagram`. Remove once all consumers import
// { SsotDigestContent } directly.
win.SsotDigestContent = SsotDigestContent;

export { SsotDigestContent };
