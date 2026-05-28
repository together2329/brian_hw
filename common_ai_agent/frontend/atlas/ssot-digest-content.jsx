// ssot-digest-content.jsx — Phase 22 refactor: SsotDigestContent
// extracted from ssot-digest.jsx so the latter drops well under 1000.
// This is the main render component for the SSOT digest pane;
// SsotReviewPane (sibling, ssot-review.jsx) wraps it.

(() => {

const AtlasStatusBadge = (...a) => window.AtlasStatusBadge(...a);
const BlockDiagram = (...a) => window.BlockDiagram(...a);
const DigestCard = (...a) => window.DigestCard(...a);
const DigestEmpty = (...a) => window.DigestEmpty(...a);
const DigestKV = (...a) => window.DigestKV(...a);
const DigestList = (...a) => window.DigestList(...a);
const DigestSourceSections = (...a) => window.DigestSourceSections(...a);
const FeatureCard = (...a) => window.FeatureCard(...a);
const FoldablePane = (...a) => window.FoldablePane(...a);
const FsmTransitionDiagram = (...a) => window.FsmTransitionDiagram(...a);
const GatesPanel = (...a) => window.GatesPanel(...a);
const ModuleTree = (...a) => window.ModuleTree(...a);
const PipelineTraceDiagram = (...a) => window.PipelineTraceDiagram(...a);
const RegisterBitFieldView = (...a) => window.RegisterBitFieldView(...a);
const SsotCommandPalette = (...a) => window.SsotCommandPalette(...a);
const SsotScenarioPlayer = (...a) => window.SsotScenarioPlayer(...a);
const _formatWidth = (...a) => window._formatWidth(...a);
const _hasMeaningfulRegisterField = (...a) => window._hasMeaningfulRegisterField(...a);
const _hasRegisterDetail = (...a) => window._hasRegisterDetail(...a);
const blockField = (...a) => window.blockField(...a);
const blockListValues = (...a) => window.blockListValues(...a);
const buildReferenceTokens = (...a) => window.buildReferenceTokens(...a);
const compactDigestItems = (...a) => window.compactDigestItems(...a);
const extractFeatures = (...a) => window.extractFeatures(...a);
const extractFsms = (...a) => window.extractFsms(...a);
const extractModuleContracts = (...a) => window.extractModuleContracts(...a);
const extractRegisters = (...a) => window.extractRegisters(...a);
const extractReviewInterfaces = (...a) => window.extractReviewInterfaces(...a);
const extractReviewPins = (...a) => window.extractReviewPins(...a);
const extractScenarios = (...a) => window.extractScenarios(...a);
const extractSubmodules = (...a) => window.extractSubmodules(...a);
const fieldFromText = (...a) => window.fieldFromText(...a);
const fsmGraphFromMachine = (...a) => window.fsmGraphFromMachine(...a);
const linkifyReferences = (...a) => window.linkifyReferences(...a);
const listBlocksFromSection = (...a) => window.listBlocksFromSection(...a);
const mapGroupsFromSection = (...a) => window.mapGroupsFromSection(...a);
const sectionByKey = (...a) => window.sectionByKey(...a);
const sourceSectionsForDigestView = (...a) => window.sourceSectionsForDigestView(...a);
const ssotTitleFor = (...a) => window.ssotTitleFor(...a);
const ssotValuePresent = (...a) => window.ssotValuePresent(...a);
const trimSsotValue = (...a) => window.trimSsotValue(...a);
const uniqueFsmStates = (...a) => window.uniqueFsmStates(...a);


const SsotDigestContent = ({ view, sections, statusByKey, uiLang = 'ko', content = '', selected = '', onJump, feedbackMode = false }) => {
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
    || (sections || []).find(s => /register|memory_?map/i.test(s.key || ''));
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
    || (sections || []).find(s => /parameter/i.test(s.key || ''));
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
    const collect = (blocks) => blocks.map(b => ({
      name: blockField(b, 'name') || blockField(b, 'key') || blockField(b, 'param') || '',
      value: blockField(b, 'default') || blockField(b, 'value') || blockField(b, 'default_value') || blockField(b, 'val') || '',
      description: blockField(b, 'description', 200),
    })).filter(p => p.name);
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
  const featureSections = (sections || []).filter(section => (
    section !== featuresSection
    && /feature|fifo|fsm|generation|arbitration|ack|interrupt|open_drain|access|bit_control|start_stop/i.test(section.key || '')
  ));
  const features = parsedFeatures.length ? parsedFeatures : featureSections.slice(0, 12).map(section => ({
    name: ssotTitleFor(section.key),
    trigger: sectionFact(section, 'trigger') || sectionFact(section, 'condition') || sectionFact(section, 'source'),
    datapath: sectionFact(section, 'datapath') || sectionFact(section, 'description') || sectionFact(section, 'implementation') || sectionFact(section, 'logic'),
    control: sectionFact(section, 'control') || sectionFact(section, 'response') || sectionFact(section, 'timing'),
    output: sectionFact(section, 'output') || sectionFact(section, 'result') || sectionFact(section, 'description'),
    sourceKey: section.key,
  }));
  const rawSubmods = extractSubmodules(submodsSection);
  const moduleContracts = extractModuleContracts(decompSection);
  const submods = rawSubmods.length ? rawSubmods : moduleContracts.map(contract => ({
    name: contract.module,
    file: '',
    description: contract.implementation,
    implements: contract.owns,
    sourceSections: [],
    interfaces: contract.interfaces,
  }));
  const contractByModule = moduleContracts.reduce((acc, contract) => {
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
  const clockDomains = listBlocksFromSection(clockSection, 'domains').map(block => ({
    name: blockField(block, 'name'),
    frequency: blockField(block, 'frequency_mhz'),
    description: blockField(block, 'description', 260),
  }));
  const resets = listBlocksFromSection(io, 'resets').map(block => ({
    name: blockField(block, 'name'),
    polarity: blockField(block, 'polarity'),
    type: blockField(block, 'sync_async') || blockField(block, 'type'),
    description: blockField(block, 'description', 220),
  }));
  const cdcCrossings = listBlocksFromSection(cdcSection, 'crossings').map(block => ({
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
  const irqs = React.useMemo(() => {
    const blocks = []
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
  const refTokenMap = React.useMemo(
    () => buildReferenceTokens({ registers, features, fsmMachines, irqs }),
    [registers, features, fsmMachines, irqs]
  );
  const paletteScenarios = React.useMemo(() => extractScenarios(sections), [sections]);
  const paletteItems = React.useMemo(() => {
    const out = [];
    (registers || []).forEach((reg) => {
      out.push({
        kind: 'register',
        label: reg.name || '(reg)',
        detail: [reg.offset && `@ ${reg.offset}`, reg.access].filter(Boolean).join(' · '),
        viewId: 'registers',
      });
      (reg.fields || []).forEach((f) => {
        if (!f.name) return;
        out.push({
          kind: 'field',
          label: `${reg.name}.${f.name}`,
          detail: [f.bits && `bits ${f.bits}`, f.access].filter(Boolean).join(' · '),
          viewId: 'registers',
        });
      });
    });
    (features || []).forEach((feat) => {
      out.push({
        kind: 'feature',
        label: feat.name || '(feature)',
        detail: String(feat.description || feat.datapath || feat.trigger || '').slice(0, 80),
        viewId: 'features',
      });
    });
    (fsmMachines || []).forEach((m) => {
      (m.states || []).forEach((s) => {
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
    (irqs || []).forEach((irq) => {
      out.push({
        kind: 'interrupt',
        label: irq.name,
        detail: String(irq.description || '').slice(0, 80),
        viewId: 'overview',
      });
    });
    (interfaces || []).forEach((iface) => {
      out.push({
        kind: 'interface',
        label: iface.name || '(iface)',
        detail: [iface.type, iface.role && `role ${iface.role}`].filter(Boolean).join(' · '),
        viewId: 'interfaces',
      });
    });
    (paletteScenarios || []).forEach((scn) => {
      out.push({
        kind: 'scenario',
        label: scn.name,
        detail: String(scn.summary || '').slice(0, 80),
        viewId: 'scenarios',
      });
    });
    return out;
  }, [registers, features, fsmMachines, irqs, interfaces, paletteScenarios]);
  const dataflowGroups = mapGroupsFromSection(dataflowSection).filter(g => g.key !== 'locked_decisions');
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

  const featureTokens = (feature) => String([
    feature && feature.name,
    feature && feature.sourceKey,
    feature && feature.trigger,
    feature && feature.datapath,
  ].filter(Boolean).join(' '))
    .toLowerCase()
    .split(/[^a-z0-9_]+/)
    .filter(token => token.length > 2 && !['the', 'and', 'with', 'for'].includes(token))
    .slice(0, 8);

  const matchesFeature = (text, tokens) => {
    const hay = String(text || '').toLowerCase();
    return (tokens || []).some(token => hay.includes(token));
  };

  const namesForFeature = (rows, tokens, nameOf, textOf, limit = 5) => (rows || [])
    .filter(row => matchesFeature(textOf(row), tokens))
    .map(nameOf)
    .filter(Boolean)
    .slice(0, limit);

  const semanticSectionNames = (rx, limit = 6) => (sections || [])
    .filter(section => rx.test(section.key || ''))
    .map(section => ssotTitleFor(section.key))
    .slice(0, limit);

  const statusForPresence = (present) => present ? 'approved' : 'needs_review';
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

  const renderOverview = () => (
    <>
      {header}
      <div style={{ display: 'grid', gap: 10 }}>
        <div style={{ display: 'grid', gap: 10, gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))' }}>
          <DigestCard title="Top Module" meta={top ? `line ${top.startLine}` : ''}>
            <DigestKV rows={[
              ['name', topName],
              ['type', sectionFact(top, 'type')],
              ['clock', sectionFact(top, 'clock_freq_mhz') ? `${sectionFact(top, 'clock_freq_mhz')} MHz` : sectionFact(clockSection, 'frequency_hz')],
              ['purpose', trimSsotValue(sectionFact(top, 'description', 'No top_module.description available yet.'), 300)],
            ]} />
          </DigestCard>
          <DigestCard title="Review Coverage" meta={`${sections.length} sections`}>
            <div style={{ display: 'grid', gap: 5 }}>
              {coverageRows.map(row => (
                <div key={row.label} style={{ display: 'grid', gridTemplateColumns: '118px minmax(0, 1fr)', gap: 8, alignItems: 'center' }}>
                  <AtlasStatusBadge status={row.status} label={row.label} compact soft />
                  <span className="trunc" style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 10 }}>{row.detail || '-'}</span>
                </div>
              ))}
            </div>
          </DigestCard>
        </div>
        <DigestCard title="Architecture" meta={`${submods.length} submodules`}>
          {submods.length ? <ModuleTree topName={topName} modules={submods.slice(0, 10)} /> : (
            <DigestList items={moduleContracts.map(contract => `${contract.module}: ${compactDigestItems(contract.owns, 4)}`)} />
          )}
        </DigestCard>
        <div style={{ display: 'grid', gap: 10, gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))' }}>
          <DigestCard title="Features" meta={`${features.length} items`}>
            <DigestList items={features.map(f => `${f.name}${f.datapath ? ` - ${trimSsotValue(f.datapath, 90)}` : ''}`)} limit={6} />
          </DigestCard>
          <DigestCard title="Interfaces" meta={`${interfaces.length} interfaces`}>
            <DigestList items={interfaces.map(iface => `${iface.name}${iface.type ? ` (${iface.type})` : ''}${iface.ports.length ? ` · ${iface.ports.length} ports` : ''}`)} limit={6} />
          </DigestCard>
          <DigestCard title="Registers / Dataflow" meta={`${registers.length} regs`}>
            <DigestKV rows={[
              ['registers', compactDigestItems(registers.map(reg => `${reg.name}${reg.offset ? ` @ ${reg.offset}` : ''}`), 5)],
              ['dataflow', compactDigestItems(dataflowGroups.map(g => ssotTitleFor(g.key)), 5) || compactDigestItems(semanticSectionNames(/dataflow|flow|fifo|buffer|open_drain|access/i, 5), 5)],
              ['function', sectionFact(functionSection, 'purpose') || compactDigestItems(semanticSectionNames(/function|fsm|logic|state/i, 4), 4)],
              ['fsm', compactDigestItems(fsmMachines.map(machine => `${machine.name} (${machine.states.length} states)`), 4)],
              ['cycle', sectionFact(cycleSection, 'purpose') || compactDigestItems(semanticSectionNames(/cycle|timing|latency|scl/i, 4), 4)],
            ]} />
          </DigestCard>
        </div>
      </div>
    </>
  );

  const renderFeatures = () => (
    <>
      {header}
      <div style={{ display: 'grid', gap: 14 }}>
        {features.length ? features.map((f, i) => (
          <FeatureCard key={`${f.name}-${i}`} index={i + 1} feature={f} tokenMap={refTokenMap} onJump={onJump} />
        )) : <DigestEmpty />}
      </div>
    </>
  );

  const renderFeatureMap = () => (
    <>
      {header}
      <div style={{ display: 'grid', gap: 10 }}>
        {features.length ? features.map((feature, i) => {
          const tokens = featureTokens(feature);
          const ownedModules = namesForFeature(
            submods,
            tokens,
            row => row.name,
            row => [row.name, row.description, ...(row.implements || []), ...(row.sourceSections || [])].join(' '),
          );
          const contractModules = namesForFeature(
            moduleContracts,
            tokens,
            row => row.module,
            row => [row.module, row.implementation, ...(row.owns || []), ...(row.inputs || []), ...(row.outputs || [])].join(' '),
          );
          const relatedRegisters = namesForFeature(
            registers,
            tokens,
            row => `${row.name}${row.offset ? ` @ ${row.offset}` : ''}`,
            row => [row.name, row.description, ...(row.fields || []).map(field => `${field.name} ${field.description}`)].join(' '),
          );
          const relatedFlows = namesForFeature(
            dataflowGroups,
            tokens,
            row => ssotTitleFor(row.key),
            row => `${row.key} ${row.text}`,
          );
          const relatedFunction = namesForFeature(
            transactions,
            tokens,
            row => blockField(row, 'id') || blockField(row, 'name'),
            row => row.text,
          );
          const relatedCycle = namesForFeature(
            [...latencyGroups, ...handshakeRules, ...pipeline],
            tokens,
            row => row.key || blockField(row, 'signal') || blockField(row, 'stage') || blockField(row, 'name'),
            row => row.text,
          );
          const modules = compactDigestItems([...new Set([...ownedModules, ...contractModules])], 5);
          return (
            <DigestCard key={`feat-${feature.name || ''}-${i}`} title={feature.name} meta={feature.sourceKey || feature.trigger}>
              <DigestKV rows={[
                ['what', feature.datapath || feature.output || feature.trigger],
                ['implemented by', modules || compactDigestItems(featureSections.filter(section => matchesFeature(section.text, tokens)).map(section => ssotTitleFor(section.key)), 5)],
                ['submodule direction', compactDigestItems(moduleContracts.filter(contract => matchesFeature(contract.implementation, tokens)).map(contract => `${contract.module}: ${trimSsotValue(contract.implementation, 90)}`), 2)],
                ['control path', feature.control || compactDigestItems(relatedRegisters, 4)],
                ['function model', compactDigestItems(relatedFunction, 4) || sectionFact(functionSection, 'purpose')],
                ['cycle model', compactDigestItems(relatedCycle, 4) || sectionFact(cycleSection, 'purpose')],
                ['registers', compactDigestItems(relatedRegisters, 5)],
                ['dataflow', compactDigestItems(relatedFlows, 5)],
                ['observable output', feature.output],
              ]} />
            </DigestCard>
          );
        }) : (
          <DigestCard title="Feature Map">
            <DigestEmpty text="No feature-level entries were found. Review Gaps shows which anchors are missing." />
          </DigestCard>
        )}
      </div>
    </>
  );

  const renderArchitecture = () => (
    <>
      {header}
      <div style={{ display: 'grid', gap: 10 }}>
        <DigestCard title="Block Diagram" meta={`${topName} → ${submods.length} submodules · ${diagramPins.length ? `${diagramPins.length} pins` : `${interfaces.length} interfaces`}`}>
          {submods.length ? (
            <BlockDiagram
              topName={topName}
              modules={submods}
              contractByModule={contractByModule}
              interfaces={interfaces}
              diagramPins={diagramPins}
              clockSection={clockSection}
              parameters={parameters}
            />
          ) : <DigestEmpty />}
        </DigestCard>
        <DigestCard title="Module Tree" meta={`${topName} + ${submods.length} submodules`}>
          {submods.length ? (
            <ModuleTree topName={topName} modules={submods} />
          ) : <DigestEmpty />}
        </DigestCard>
        <DigestCard title="Module Split" meta={`${submods.length} submodules`}>
          {submods.length ? (
            <div style={{ display: 'grid', gap: 9 }}>
              {submods.map((m, i) => {
                const contract = contractByModule[m.name] || {};
                const localInputs = (contract.inputs || []).length ? contract.inputs : [];
                const localOutputs = (contract.outputs || []).length ? contract.outputs : [];
                const owns = (contract.owns || []).length ? contract.owns : m.implements;
                return (
                  <div key={`sm-${m.name || ''}-${i}`} style={{ borderBottom: '1px solid var(--line)', paddingBottom: 7 }}>
                    <div><b>{m.name}</b> <span className="mute" style={{ fontFamily: 'var(--mono)', fontSize: 10 }}>{m.file}</span></div>
                    <div className="mute" style={{ marginTop: 2 }}>{m.description}</div>
                    {owns.length ? <div style={{ marginTop: 3, color: 'var(--cyan)', fontFamily: 'var(--mono)', fontSize: 10 }}>direction: {owns.join(', ')}</div> : null}
                    {localInputs.length || localOutputs.length ? (
                      <DigestKV rows={[
                        ['inputs', localInputs.join('; ')],
                        ['outputs', localOutputs.join('; ')],
                      ]} />
                    ) : null}
                  </div>
                );
              })}
            </div>
          ) : <DigestEmpty />}
        </DigestCard>
        {moduleContracts.length ? (
          <DigestCard title="Implementation Direction" meta={`${moduleContracts.length} module contracts`}>
            <div style={{ display: 'grid', gap: 10 }}>
              {moduleContracts.map((contract, i) => (
                <div key={`mc-${contract.module || ''}-${i}`} style={{ borderBottom: '1px solid var(--line)', paddingBottom: 8 }}>
                  <div style={{ fontWeight: 800 }}>{contract.module}</div>
                  {contract.implementation ? <div className="mute" style={{ marginTop: 2 }}>{contract.implementation}</div> : null}
                  <DigestKV rows={[
                    ['owns', contract.owns.join('; ')],
                    ['inputs', contract.inputs.join('; ')],
                    ['outputs', contract.outputs.join('; ')],
                  ]} />
                </div>
              ))}
            </div>
          </DigestCard>
        ) : null}
        {decompSection ? <DigestSourceSections view={{ keys: ['decomposition'] }} sections={sections} statusByKey={statusByKey} t={t} /> : null}
      </div>
    </>
  );

  const renderFunctionModel = () => (
    <>
      {header}
      <div style={{ display: 'grid', gap: 10 }}>
        <DigestCard title="Purpose">
          <div>{sectionFact(functionSection, 'purpose', 'No function model purpose available yet.')}</div>
        </DigestCard>
        <DigestCard title="Transactions" meta={`${transactions.length} transactions`}>
          {transactions.length ? transactions.map((tx, i) => (
            <div key={`tx-${blockField(tx, 'id') || blockField(tx, 'name') || i}-${i}`} style={{ marginBottom: 10, borderBottom: '1px solid var(--line)', paddingBottom: 8 }}>
              <div><b>{blockField(tx, 'id')}</b> {blockField(tx, 'name')}</div>
              <DigestKV rows={[
                ['preconditions', blockListValues(tx, 'preconditions', 4).join('; ')],
                ['inputs', blockListValues(tx, 'inputs', 4).join('; ')],
                ['outputs', blockListValues(tx, 'outputs', 4).join('; ')],
                ['side effects', blockListValues(tx, 'side_effects', 4).join('; ')],
              ]} />
            </div>
          )) : <DigestEmpty />}
        </DigestCard>
        <DigestCard title="State Variables" meta={`${stateVars.length} variables`}>
          {stateVars.length ? (
            <div style={{ display: 'grid', gap: 5 }}>
              {stateVars.map((v, i) => <DigestKV key={`sv-${blockField(v, 'name') || i}-${i}`} rows={[[blockField(v, 'name'), `${blockField(v, 'source')} · reset ${blockField(v, 'reset')} · ${blockField(v, 'description')}`]]} />)}
            </div>
          ) : <DigestEmpty />}
        </DigestCard>
      </div>
    </>
  );

  const renderFsm = () => (
    <>
      {header}
      <div style={{ display: 'grid', gap: 10 }}>
        <DigestCard
          title="FSM Summary"
          meta={`${fsmMachines.length} machines · ${fsmMachines.reduce((sum, m) => sum + uniqueFsmStates(m).length, 0)} states · ${fsmMachines.reduce((sum, m) => sum + m.transitions.length, 0)} transitions`}
        >
          {fsmMachines.length ? (
            <DigestKV rows={[
              ['machines', compactDigestItems(fsmMachines.map(machine => machine.name), 8)],
              ['reset states', compactDigestItems(fsmMachines.map(machine => machine.resetState ? `${machine.name}: ${machine.resetState}` : '').filter(Boolean), 6)],
              ['source', fsmSection ? `fsm section line ${fsmSection.startLine}` : 'No fsm section found'],
            ]} />
          ) : noFsmPolicy ? (
            <DigestKV rows={[
              ['policy', noFsmPolicy],
              ['source', fsmSection ? `fsm section line ${fsmSection.startLine}` : 'No fsm section found'],
            ]} />
          ) : (
            <DigestEmpty text="No structured FSM section found. Add fsm.<machine>.states and fsm.<machine>.transitions to SSOT." />
          )}
        </DigestCard>
        {fsmMachines.map((machine, machineIdx) => {
          const graph = fsmGraphFromMachine(machine);
          return (
            <DigestCard
              key={`fsm-${machine.name || ''}-${machineIdx}`}
              title={machine.name}
              meta={`${graph.states.length} states · ${graph.transitions.length} transitions`}
            >
              <DigestKV rows={[
                ['reset', machine.resetState],
                ['illegal recovery', machine.illegalRecovery],
                ['outputs', machine.outputs.join('; ')],
                ['actions', machine.actions.join('; ')],
                ['note', machine.note],
              ]} />
              {graph.states.length ? (
                <div style={{ marginTop: 10 }}>
                  <div className="mute" style={{ fontFamily: 'var(--mono)', fontSize: 10, marginBottom: 5 }}>states</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {graph.states.map(state => (
                      <span
                        key={`${machine.name}:${state.id}`}
                        style={{
                          border: '1px solid var(--line-2)',
                          borderRadius: 3,
                          padding: '3px 7px',
                          fontFamily: 'var(--mono)',
                          fontSize: 'var(--ui-control-font-size)',
                          color: state.reset ? 'var(--accent)' : 'var(--fg)',
                          background: state.reset
                            ? 'color-mix(in oklch, var(--accent) 14%, transparent)'
                            : 'var(--bg-3)',
                        }}
                      >
                        {state.label}
                      </span>
                    ))}
                  </div>
                </div>
              ) : null}
              <FsmTransitionDiagram machine={machine} index={machineIdx} />
            </DigestCard>
          );
        })}
      </div>
    </>
  );

  const renderCycleModel = () => (
    <>
      {header}
      <div style={{ display: 'grid', gap: 10 }}>
        <DigestCard title="Cycle Contract">
          <DigestKV rows={[
            ['purpose', sectionFact(cycleSection, 'purpose')],
            ['clock', sectionFact(cycleSection, 'clock')],
            ['reset assertion', sectionFact(cycleSection, 'assertion')],
            ['reset deassertion', sectionFact(cycleSection, 'deassertion')],
          ]} />
        </DigestCard>
        <DigestCard title="Latency" meta={`${latencyGroups.length} paths`}>
          {latencyGroups.length ? latencyGroups.map((g, i) => (
            <DigestKV key={`lat-${g.key || ''}-${i}`} rows={[[g.key, `${fieldFromText(g.text, 'min_cycles') || '?'}-${fieldFromText(g.text, 'max_cycles') || '?'} cycles · ${fieldFromText(g.text, 'description')}`]]} />
          )) : <DigestEmpty />}
        </DigestCard>
        <DigestCard title="Handshake / Pipeline" meta={`${handshakeRules.length} rules · ${pipeline.length} stages`}>
          {handshakeRules.slice(0, 8).map((r, i) => <div key={`hr-${blockField(r, 'signal') || i}-${i}`} style={{ marginBottom: 4 }}><b>{blockField(r, 'signal')}</b> <span className="mute">{blockField(r, 'rule', 320)}</span></div>)}
          {pipeline.length ? <hr style={{ border: 0, borderTop: '1px solid var(--line)', margin: '8px 0' }} /> : null}
          {pipeline.map((p, i) => <div key={`pl-${blockField(p, 'stage') || i}-${i}`} style={{ marginBottom: 4 }}><b>{blockField(p, 'stage')}</b> <span className="mute">{blockField(p, 'cycle')} · {blockField(p, 'action', 320)}</span></div>)}
        </DigestCard>
        {pipeline.length ? (
          <DigestCard title="Pipeline trace" meta={`${pipeline.length}-stage staircase · ${Math.min(transactions.length || 1, 4)} ${transactions.length ? 'transactions' : 'flow'}`}>
            <PipelineTraceDiagram pipeline={pipeline} transactions={transactions} />
          </DigestCard>
        ) : null}
      </div>
    </>
  );

  const renderInterfaces = () => (
    <>
      {header}
      <div style={{ display: 'grid', gap: 10 }}>
        <div style={{ color: 'var(--accent)', fontWeight: 800, fontSize: 12 }}>Top Module External Interfaces <span className="mute" style={{ fontFamily: 'var(--mono)', fontSize: 10 }}>{interfaces.length} interfaces</span></div>
        {interfaces.length ? interfaces.map((iface, i) => (
          <DigestCard key={`if-${iface.name || ''}-${i}`} title={iface.name} meta={`${iface.type}${iface.role ? ` · ${iface.role}` : ''} · ${iface.ports.length} ${t.ports}`}>
            <div className="mute" style={{ marginBottom: 8 }}>{iface.description}</div>
            <div style={{ display: 'grid', gap: 4 }}>
              {iface.ports.map((port, pi) => (
                <div key={`port-${port.name || ''}-${pi}`} style={{ display: 'grid', gridTemplateColumns: 'minmax(110px, 0.7fr) 56px minmax(70px, max-content) minmax(0, 1.4fr)', gap: 10, fontFamily: 'var(--mono)', fontSize: 'var(--ui-control-font-size)', alignItems: 'baseline' }}>
                  <span style={{ color: 'var(--fg)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{port.name}</span>
                  <span className="mute">{port.direction}</span>
                  <span className="mute" style={{ whiteSpace: 'nowrap' }}>{_formatWidth(port.width) || '[0]'}</span>
                  <span className="mute" style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>{port.description}</span>
                </div>
              ))}
            </div>
          </DigestCard>
        )) : <DigestEmpty />}
        {moduleContracts.length ? (
          <DigestCard title="Submodule Local Interfaces" meta={`${moduleContracts.length} modules`}>
            <div style={{ display: 'grid', gap: 10 }}>
              {moduleContracts.map((contract, ci) => (
                <div key={`mc2-${contract.module || ''}-${ci}`} style={{ borderBottom: '1px solid var(--line)', paddingBottom: 8 }}>
                  <div style={{ fontWeight: 800 }}>{contract.module}</div>
                  <DigestKV rows={[
                    ['inputs', contract.inputs.join('; ')],
                    ['outputs', contract.outputs.join('; ')],
                  ]} />
                  {contract.interfaces.length ? (
                    <div style={{ marginTop: 7, display: 'grid', gap: 6 }}>
                      {contract.interfaces.map((iface, ii) => (
                        <div key={`cif-${iface.name || ''}-${ii}`}>
                          <b>{iface.name}</b> <span className="mute">{iface.type}{iface.role ? ` · ${iface.role}` : ''}</span>
                          <DigestKV rows={[
                            ['inputs', iface.inputs.join('; ')],
                            ['outputs', iface.outputs.join('; ')],
                            ['description', iface.description],
                          ]} />
                        </div>
                      ))}
                    </div>
                  ) : null}
                </div>
              ))}
            </div>
          </DigestCard>
        ) : null}
      </div>
    </>
  );

  const renderRegisters = () => (
    <>
      {header}
      <DigestCard title="Register Map" meta={`${registers.length} registers`}>
        {registers.length ? (
          <div style={{ display: 'grid', gap: 8 }}>
            <div className="mute" style={{ fontFamily: 'var(--mono)', fontSize: 10 }}>
              {[
                `${registers.length} register${registers.length === 1 ? '' : 's'}`,
                _hasRegisterDetail(registerConfig.addrWidth) ? `addr ${registerConfig.addrWidth}` : '',
                _hasRegisterDetail(registerConfig.dataWidth) ? `data ${registerConfig.dataWidth}` : '',
                _hasRegisterDetail(registerConfig.byteAddressable) ? `byte ${registerConfig.byteAddressable}` : '',
              ].filter(Boolean).join(' · ')}
            </div>
            {registers.map((reg, i) => {
              const meaningfulFields = (reg.fields || []).filter(_hasMeaningfulRegisterField);
              const hasExpandedDetail = meaningfulFields.length > 0;
              const tags = [
                _hasRegisterDetail(reg.access) && `access ${reg.access}`,
                _hasRegisterDetail(reg.reset) && `reset ${reg.reset}`,
                _hasRegisterDetail(reg.width) && `${reg.width}b`,
              ].filter(Boolean);
              return (
              <div key={`reg-${reg.name || ''}-${i}`} style={{
                border: '1px solid var(--line)',
                borderLeft: '3px solid var(--accent)',
                borderRadius: 4,
                background: 'var(--bg-2)',
                padding: hasExpandedDetail ? 10 : '8px 10px',
                minWidth: 0,
              }}>
                <div style={{ display: 'grid', gridTemplateColumns: '76px minmax(0, 1fr)', gap: 10, alignItems: 'center' }}>
                  <div style={{
                    fontFamily: 'var(--mono)',
                    color: 'var(--cyan)',
                    fontWeight: 900,
                    border: '1px solid var(--line-2)',
                    borderRadius: 4,
                    padding: '4px 7px',
                    textAlign: 'center',
                    background: 'var(--bg-1)',
                    whiteSpace: 'nowrap',
                  }}>
                    {_hasRegisterDetail(reg.offset) ? reg.offset : '--'}
                  </div>
                  <div style={{ minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 7, flexWrap: 'wrap' }}>
                      <span style={{ fontWeight: 900, color: 'var(--fg)', fontSize: 14, fontFamily: 'var(--mono)', wordBreak: 'break-word' }}>{reg.name}</span>
                      {tags.map(tag => (
                        <span key={`${reg.name}-${tag}`} className="mute" style={{
                          fontFamily: 'var(--mono)',
                          fontSize: 10,
                          border: '1px solid var(--line)',
                          borderRadius: 3,
                          padding: '2px 6px',
                          background: 'var(--bg-3)',
                          whiteSpace: 'nowrap',
                        }}>{tag}</span>
                      ))}
                    </div>
                    {_hasRegisterDetail(reg.description) ? (
                      <div className="mute" style={{ marginTop: 5, lineHeight: 1.5, wordBreak: 'break-word' }}>{linkifyReferences(reg.description, refTokenMap, onJump)}</div>
                    ) : !hasExpandedDetail ? (
                      <div className="mute" style={{ marginTop: 3, fontFamily: 'var(--mono)', fontSize: 10 }}>details pending</div>
                    ) : null}
                  </div>
                </div>
                {hasExpandedDetail ? (
                  <RegisterBitFieldView
                    width={reg.width || registerConfig.dataWidth || 32}
                    fields={meaningfulFields}
                    tokenMap={refTokenMap}
                    onJump={onJump}
                  />
                ) : null}
              </div>
            );})}
          </div>
        ) : noRegisterPolicy ? (
          <DigestKV rows={[['policy', noRegisterPolicy]]} />
        ) : <DigestEmpty />}
      </DigestCard>
    </>
  );

  const renderDataflow = () => (
    <>
      {header}
      <div style={{ display: 'grid', gap: 10 }}>
        {dataflowGroups.length ? dataflowGroups.map((g, i) => (
          <DigestCard key={`df-${g.key || ''}-${i}`} title={ssotTitleFor(g.key)}>
            <DigestKV rows={[
              ['source', fieldFromText(g.text, 'source')],
              ['sequence', blockListValues(g, 'sequence', 8).join(' -> ')],
              ['buffer', fieldFromText(g.text, 'buffer')],
              ['backpressure', fieldFromText(g.text, 'backpressure', 360)],
              ['description', fieldFromText(g.text, 'description', 360)],
            ]} />
          </DigestCard>
        )) : <DigestEmpty />}
      </div>
    </>
  );

  const renderClocking = () => (
    <>
      {header}
      <div style={{ display: 'grid', gap: 10 }}>
        <DigestCard title="Clock Domains" meta={`${clockDomains.length} domains`}>
          {clockDomains.length ? clockDomains.map((d, i) => <DigestKV key={`cd-${d.name || ''}-${i}`} rows={[[d.name, `${d.frequency || '?'} MHz · ${d.description}`]]} />) : <DigestEmpty />}
        </DigestCard>
        <DigestCard title="Reset">
          {resets.length ? resets.map((r, i) => <DigestKV key={`rs-${r.name || ''}-${i}`} rows={[[r.name, `${r.polarity} · ${r.type} · ${r.description}`]]} />) : <DigestKV rows={[['scheme', sectionFact(clockSection, 'type') || sectionFact(clockSection, 'reset_scheme')]]} />}
        </DigestCard>
        <DigestCard title="CDC / RDC" meta={`${cdcCrossings.length} CDC crossings`}>
          {cdcCrossings.length ? cdcCrossings.map((c, i) => <DigestKV key={`cdc-${c.name || ''}-${i}`} rows={[[c.name, `${c.from} -> ${c.to} · ${c.synchronizer} · ${c.description}`]]} />) : <DigestEmpty text={sectionFact(rdcSection, 'note') || 'No CDC crossings listed.'} />}
        </DigestCard>
      </div>
    </>
  );

  const renderReviewGaps = () => {
    const explicitGaps = (sections || []).flatMap(section => (
      ((section.summary && section.summary.gaps) || []).map(gap => ({
        key: section.key,
        line: gap.line,
        text: gap.text,
      }))
    ));
    const missing = coverageRows.filter(row => row.status !== 'approved');
    return (
      <>
        {header}
        <div style={{ display: 'grid', gap: 10 }}>
          <DigestCard title="Review Coverage" meta={`${coverageRows.length} anchors`}>
            <div style={{ display: 'grid', gap: 6 }}>
              {coverageRows.map(row => (
                <div key={row.label} style={{
                  display: 'grid', gridTemplateColumns: '150px minmax(0, 1fr)',
                  gap: 8, alignItems: 'center', borderBottom: '1px solid var(--line)', paddingBottom: 5,
                }}>
                  <AtlasStatusBadge status={row.status} label={row.label} compact soft />
                  <span style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 'var(--ui-control-font-size)', minWidth: 0, wordBreak: 'break-word' }}>
                    {row.detail || '-'}
                  </span>
                </div>
              ))}
            </div>
          </DigestCard>
          <DigestCard title="Missing Anchors" meta={`${missing.length} missing`}>
            {missing.length ? (
              <DigestList items={missing.map(row => `${row.label}: ${row.detail || 'not found'}`)} />
            ) : <DigestEmpty text="All core review anchors have structured SSOT coverage." />}
          </DigestCard>
          <DigestCard title="Open Flags" meta={`${explicitGaps.length} flags`}>
            {explicitGaps.length ? (
              <div style={{ display: 'grid', gap: 7 }}>
                {explicitGaps.slice(0, 18).map(gap => (
                  <div key={`${gap.key}:${gap.line}:${gap.text}`} style={{ borderLeft: '2px solid var(--warn)', paddingLeft: 8 }}>
                    <div style={{ color: 'var(--warn)', fontFamily: 'var(--mono)', fontSize: 10 }}>{ssotTitleFor(gap.key)} · line {gap.line}</div>
                    <div style={{ marginTop: 2 }}>{gap.text}</div>
                  </div>
                ))}
              </div>
            ) : <DigestEmpty text="No TBD, TODO, placeholder, pending, null, or unspecified markers detected." />}
          </DigestCard>
        </div>
      </>
    );
  };

  const renderRawYaml = () => {
    // Embed FoldablePane directly without the DigestCard wrapper —
    // DigestCard pins height for chip-sized content and clipped the
    // scrollable fold body. Now matches /tmp/ssot_fold_engine.html
    // exactly: a single full-bleed fold pane with the toolbar at top,
    // the chat input is the global ATLAS textarea reached via the
    // atlas-fold-comment custom event.
    const lineCount = (content || '').split('\n').length;
    if (!selected || !content) {
      return (
        <>
          {header}
          <div style={{ padding: 16, color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 12 }}>
            {selected ? 'loading…' : 'no SSOT file selected'}
          </div>
        </>
      );
    }
    return (
      <>
        {header}
        <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column', overflow: 'auto' }}>
          <FoldablePane path={selected} body={content} lang="yaml" lineCount={lineCount} feedbackMode={feedbackMode} />
        </div>
      </>
    );
  };

  const renderGates = () => {
    const ipFromPath = (() => {
      const p = String(selected || '').trim();
      if (!p) return '';
      const seg = p.split('/').filter(Boolean);
      return seg[0] || '';
    })();
    return (
      <>
        {header}
        <div style={{ flex: 1, minHeight: 0, overflow: 'auto', padding: '10px 12px' }}>
          <GatesPanel ip={ipFromPath} />
        </div>
      </>
    );
  };

  const renderGeneric = (title, sourceSections) => (
    <>
      {header}
      {sourceSections.length ? <DigestSourceSections view={{ keys: sourceSections.map(s => s.key) }} sections={sections} statusByKey={statusByKey} t={t} /> : <DigestEmpty />}
    </>
  );

  const sourceSections = sourceSectionsForDigestView(view, sections);
  const scenarios = React.useMemo(() => extractScenarios(sections), [sections]);
  const renderScenarios = () => (
    <>
      {header}
      <DigestCard title="Interactive scenarios" meta={`${scenarios.length} scenarios${scenarios.length && scenarios[0].synthesized ? ' · auto-synthesized from transactions + pipeline' : ''}`}>
        {scenarios.length ? (
          <SsotScenarioPlayer scenarios={scenarios} fsmMachines={fsmMachines} tokenMap={refTokenMap} onJump={onJump} />
        ) : (
          <DigestEmpty text="No cycle_model.scenarios[] declared and no function_model.transactions[] + cycle_model.pipeline[] to synthesize from. Add scenarios under cycle_model: { scenarios: [{ name, summary, steps:[{cycle,action,fl_state,cl_state,signals}] }] } to make this IP self-demonstrating." />
        )}
      </DigestCard>
    </>
  );
  let body;
  if (view.id === 'overview') body = renderOverview();
  else if (view.id === 'scenarios') body = renderScenarios();
  else if (view.id === 'features') body = renderFeatures();
  else if (view.id === 'architecture') body = renderArchitecture();
  else if (view.id === 'feature_map') body = renderFeatureMap();
  else if (view.id === 'function_model') body = renderFunctionModel();
  else if (view.id === 'fsm') body = renderFsm();
  else if (view.id === 'cycle_model') body = renderCycleModel();
  else if (view.id === 'interfaces') body = renderInterfaces();
  else if (view.id === 'registers') body = renderRegisters();
  else if (view.id === 'dataflow') body = renderDataflow();
  else if (view.id === 'clocking') body = renderClocking();
  else if (view.id === 'review_gaps') body = renderReviewGaps();
  else if (view.id === 'gates') body = renderGates();
  else if (view.id === 'raw_yaml') body = renderRawYaml();
  else body = renderGeneric(view.label, sourceSections);

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

window.SsotDigestContent = SsotDigestContent;

})();
