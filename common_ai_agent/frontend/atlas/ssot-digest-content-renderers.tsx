// ssot-digest-content-renderers.tsx — per-view render functions for
// SsotDigestContent (extracted to keep the source under 1000 lines).
//
// Each render* function was a closure over locals computed inside the
// SsotDigestContent component body. To preserve identical behavior without
// moving that computation, the component now builds a single `ctx` object
// (DigestRenderContext) holding every derived value + helper the renderers
// read, and `buildRenderers(ctx)` returns the render closures bound to it.
// Runtime is unchanged — the same expressions run in the same order, just
// reached through `ctx.X` instead of a lexical binding.
import { type ReactNode } from 'react';
import {
  AtlasStatusBadge,
  BlockDiagram,
  DigestCard,
  DigestEmpty,
  DigestKV,
  DigestList,
  DigestSourceSections,
  FeatureCard,
  FoldablePane,
  FsmTransitionDiagram,
  GatesPanel,
  ModuleTree,
  PipelineTraceDiagram,
  RegisterBitFieldView,
  SsotScenarioPlayer,
  _formatWidth,
  _hasMeaningfulRegisterField,
  _hasRegisterDetail,
  blockField,
  blockListValues,
  compactDigestItems,
  fieldFromText,
  fsmGraphFromMachine,
  linkifyReferences,
  sectionFact,
  ssotTitleFor,
  trimSsotValue,
  uniqueFsmStates,
} from './ssot-digest-content-globals';

// Everything the render closures read off the component scope. Typed `any`
// in the same permissive house style as the source — these are window-sourced
// or loosely-shaped SSOT values.
export interface DigestRenderContext {
  header: ReactNode;
  sections: any;
  statusByKey: any;
  t: any;
  onJump: any;
  selected: string;
  content: string;
  feedbackMode: boolean;
  top: any;
  topName: any;
  clockSection: any;
  functionSection: any;
  cycleSection: any;
  timingSection: any;
  fsmSection: any;
  rdcSection: any;
  decompSection: any;
  parameters: any;
  submods: any;
  moduleContracts: any;
  contractByModule: any;
  features: any;
  featureSections: any;
  interfaces: any;
  diagramPins: any;
  registers: any;
  registerConfig: any;
  noRegisterPolicy: any;
  noFsmPolicy: any;
  fsmMachines: any;
  dataflowGroups: any;
  transactions: any;
  stateVars: any;
  latencyGroups: any;
  handshakeRules: any;
  pipeline: any;
  clockDomains: any;
  resets: any;
  cdcCrossings: any;
  coverageRows: any;
  refTokenMap: any;
  scenarios: any;
  featureTokens: (feature: any) => any;
  matchesFeature: (text: any, tokens: any) => any;
  namesForFeature: (rows: any, tokens: any, nameOf: any, textOf: any, limit?: number) => any;
  semanticSectionNames: (rx: any, limit?: number) => any;
}

export interface DigestRenderers {
  renderOverview: () => ReactNode;
  renderFeatures: () => ReactNode;
  renderFeatureMap: () => ReactNode;
  renderArchitecture: () => ReactNode;
  renderFunctionModel: () => ReactNode;
  renderFsm: () => ReactNode;
  renderCycleModel: () => ReactNode;
  renderInterfaces: () => ReactNode;
  renderRegisters: () => ReactNode;
  renderDataflow: () => ReactNode;
  renderClocking: () => ReactNode;
  renderReviewGaps: () => ReactNode;
  renderRawYaml: () => ReactNode;
  renderGates: () => ReactNode;
  renderGeneric: (title: any, sourceSections: any) => ReactNode;
  renderScenarios: () => ReactNode;
}

export const buildRenderers = (ctx: DigestRenderContext): DigestRenderers => {
  const {
    header, sections, statusByKey, t, onJump, selected, content, feedbackMode,
    top, topName, clockSection, functionSection, cycleSection, fsmSection,
    rdcSection, decompSection, parameters, submods, moduleContracts,
    contractByModule, features, featureSections, interfaces, diagramPins,
    registers, registerConfig, noRegisterPolicy, noFsmPolicy, fsmMachines,
    dataflowGroups, transactions, stateVars, latencyGroups, handshakeRules,
    pipeline, clockDomains, resets, cdcCrossings, coverageRows, refTokenMap,
    scenarios, featureTokens, matchesFeature, namesForFeature, semanticSectionNames,
  } = ctx;

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
              {coverageRows.map((row: any) => (
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
            <DigestList items={moduleContracts.map((contract: any) => `${contract.module}: ${compactDigestItems(contract.owns, 4)}`)} />
          )}
        </DigestCard>
        <div style={{ display: 'grid', gap: 10, gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))' }}>
          <DigestCard title="Features" meta={`${features.length} items`}>
            <DigestList items={features.map((f: any) => `${f.name}${f.datapath ? ` - ${trimSsotValue(f.datapath, 90)}` : ''}`)} limit={6} />
          </DigestCard>
          <DigestCard title="Interfaces" meta={`${interfaces.length} interfaces`}>
            <DigestList items={interfaces.map((iface: any) => `${iface.name}${iface.type ? ` (${iface.type})` : ''}${iface.ports.length ? ` · ${iface.ports.length} ports` : ''}`)} limit={6} />
          </DigestCard>
          <DigestCard title="Registers / Dataflow" meta={`${registers.length} regs`}>
            <DigestKV rows={[
              ['registers', compactDigestItems(registers.map((reg: any) => `${reg.name}${reg.offset ? ` @ ${reg.offset}` : ''}`), 5)],
              ['dataflow', compactDigestItems(dataflowGroups.map((g: any) => ssotTitleFor(g.key)), 5) || compactDigestItems(semanticSectionNames(/dataflow|flow|fifo|buffer|open_drain|access/i, 5), 5)],
              ['function', sectionFact(functionSection, 'purpose') || compactDigestItems(semanticSectionNames(/function|fsm|logic|state/i, 4), 4)],
              ['fsm', compactDigestItems(fsmMachines.map((machine: any) => `${machine.name} (${machine.states.length} states)`), 4)],
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
        {features.length ? features.map((f: any, i: number) => (
          <FeatureCard key={`${f.name}-${i}`} index={i + 1} feature={f} tokenMap={refTokenMap} onJump={onJump} />
        )) : <DigestEmpty />}
      </div>
    </>
  );

  const renderFeatureMap = () => (
    <>
      {header}
      <div style={{ display: 'grid', gap: 10 }}>
        {features.length ? features.map((feature: any, i: number) => {
          const tokens = featureTokens(feature);
          const ownedModules = namesForFeature(
            submods,
            tokens,
            (row: any) => row.name,
            (row: any) => [row.name, row.description, ...(row.implements || []), ...(row.sourceSections || [])].join(' '),
          );
          const contractModules = namesForFeature(
            moduleContracts,
            tokens,
            (row: any) => row.module,
            (row: any) => [row.module, row.implementation, ...(row.owns || []), ...(row.inputs || []), ...(row.outputs || [])].join(' '),
          );
          const relatedRegisters = namesForFeature(
            registers,
            tokens,
            (row: any) => `${row.name}${row.offset ? ` @ ${row.offset}` : ''}`,
            (row: any) => [row.name, row.description, ...(row.fields || []).map((field: any) => `${field.name} ${field.description}`)].join(' '),
          );
          const relatedFlows = namesForFeature(
            dataflowGroups,
            tokens,
            (row: any) => ssotTitleFor(row.key),
            (row: any) => `${row.key} ${row.text}`,
          );
          const relatedFunction = namesForFeature(
            transactions,
            tokens,
            (row: any) => blockField(row, 'id') || blockField(row, 'name'),
            (row: any) => row.text,
          );
          const relatedCycle = namesForFeature(
            [...latencyGroups, ...handshakeRules, ...pipeline],
            tokens,
            (row: any) => row.key || blockField(row, 'signal') || blockField(row, 'stage') || blockField(row, 'name'),
            (row: any) => row.text,
          );
          const modules = compactDigestItems([...new Set([...ownedModules, ...contractModules])], 5);
          return (
            <DigestCard key={`feat-${feature.name || ''}-${i}`} title={feature.name} meta={feature.sourceKey || feature.trigger}>
              <DigestKV rows={[
                ['what', feature.datapath || feature.output || feature.trigger],
                ['implemented by', modules || compactDigestItems(featureSections.filter((section: any) => matchesFeature(section.text, tokens)).map((section: any) => ssotTitleFor(section.key)), 5)],
                ['submodule direction', compactDigestItems(moduleContracts.filter((contract: any) => matchesFeature(contract.implementation, tokens)).map((contract: any) => `${contract.module}: ${trimSsotValue(contract.implementation, 90)}`), 2)],
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
              {submods.map((m: any, i: number) => {
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
              {moduleContracts.map((contract: any, i: number) => (
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
          {transactions.length ? transactions.map((tx: any, i: number) => (
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
              {stateVars.map((v: any, i: number) => <DigestKV key={`sv-${blockField(v, 'name') || i}-${i}`} rows={[[blockField(v, 'name'), `${blockField(v, 'source')} · reset ${blockField(v, 'reset')} · ${blockField(v, 'description')}`]]} />)}
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
          meta={`${fsmMachines.length} machines · ${fsmMachines.reduce((sum: number, m: any) => sum + uniqueFsmStates(m).length, 0)} states · ${fsmMachines.reduce((sum: number, m: any) => sum + m.transitions.length, 0)} transitions`}
        >
          {fsmMachines.length ? (
            <DigestKV rows={[
              ['machines', compactDigestItems(fsmMachines.map((machine: any) => machine.name), 8)],
              ['reset states', compactDigestItems(fsmMachines.map((machine: any) => machine.resetState ? `${machine.name}: ${machine.resetState}` : '').filter(Boolean), 6)],
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
        {fsmMachines.map((machine: any, machineIdx: number) => {
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
                    {graph.states.map((state: any) => (
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
          {latencyGroups.length ? latencyGroups.map((g: any, i: number) => (
            <DigestKV key={`lat-${g.key || ''}-${i}`} rows={[[g.key, `${fieldFromText(g.text, 'min_cycles') || '?'}-${fieldFromText(g.text, 'max_cycles') || '?'} cycles · ${fieldFromText(g.text, 'description')}`]]} />
          )) : <DigestEmpty />}
        </DigestCard>
        <DigestCard title="Handshake / Pipeline" meta={`${handshakeRules.length} rules · ${pipeline.length} stages`}>
          {handshakeRules.slice(0, 8).map((r: any, i: number) => <div key={`hr-${blockField(r, 'signal') || i}-${i}`} style={{ marginBottom: 4 }}><b>{blockField(r, 'signal')}</b> <span className="mute">{blockField(r, 'rule', 320)}</span></div>)}
          {pipeline.length ? <hr style={{ border: 0, borderTop: '1px solid var(--line)', margin: '8px 0' }} /> : null}
          {pipeline.map((p: any, i: number) => <div key={`pl-${blockField(p, 'stage') || i}-${i}`} style={{ marginBottom: 4 }}><b>{blockField(p, 'stage')}</b> <span className="mute">{blockField(p, 'cycle')} · {blockField(p, 'action', 320)}</span></div>)}
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
        {interfaces.length ? interfaces.map((iface: any, i: number) => (
          <DigestCard key={`if-${iface.name || ''}-${i}`} title={iface.name} meta={`${iface.type}${iface.role ? ` · ${iface.role}` : ''} · ${iface.ports.length} ${t.ports}`}>
            <div className="mute" style={{ marginBottom: 8 }}>{iface.description}</div>
            <div style={{ display: 'grid', gap: 4 }}>
              {iface.ports.map((port: any, pi: number) => (
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
              {moduleContracts.map((contract: any, ci: number) => (
                <div key={`mc2-${contract.module || ''}-${ci}`} style={{ borderBottom: '1px solid var(--line)', paddingBottom: 8 }}>
                  <div style={{ fontWeight: 800 }}>{contract.module}</div>
                  <DigestKV rows={[
                    ['inputs', contract.inputs.join('; ')],
                    ['outputs', contract.outputs.join('; ')],
                  ]} />
                  {contract.interfaces.length ? (
                    <div style={{ marginTop: 7, display: 'grid', gap: 6 }}>
                      {contract.interfaces.map((iface: any, ii: number) => (
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
            {registers.map((reg: any, i: number) => {
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
                      {tags.map((tag: any) => (
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
        {dataflowGroups.length ? dataflowGroups.map((g: any, i: number) => (
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
          {clockDomains.length ? clockDomains.map((d: any, i: number) => <DigestKV key={`cd-${d.name || ''}-${i}`} rows={[[d.name, `${d.frequency || '?'} MHz · ${d.description}`]]} />) : <DigestEmpty />}
        </DigestCard>
        <DigestCard title="Reset">
          {resets.length ? resets.map((r: any, i: number) => <DigestKV key={`rs-${r.name || ''}-${i}`} rows={[[r.name, `${r.polarity} · ${r.type} · ${r.description}`]]} />) : <DigestKV rows={[['scheme', sectionFact(clockSection, 'type') || sectionFact(clockSection, 'reset_scheme')]]} />}
        </DigestCard>
        <DigestCard title="CDC / RDC" meta={`${cdcCrossings.length} CDC crossings`}>
          {cdcCrossings.length ? cdcCrossings.map((c: any, i: number) => <DigestKV key={`cdc-${c.name || ''}-${i}`} rows={[[c.name, `${c.from} -> ${c.to} · ${c.synchronizer} · ${c.description}`]]} />) : <DigestEmpty text={sectionFact(rdcSection, 'note') || 'No CDC crossings listed.'} />}
        </DigestCard>
      </div>
    </>
  );

  const renderReviewGaps = () => {
    const explicitGaps = (sections || []).flatMap((section: any) => (
      ((section.summary && section.summary.gaps) || []).map((gap: any) => ({
        key: section.key,
        line: gap.line,
        text: gap.text,
      }))
    ));
    const missing = coverageRows.filter((row: any) => row.status !== 'approved');
    return (
      <>
        {header}
        <div style={{ display: 'grid', gap: 10 }}>
          <DigestCard title="Review Coverage" meta={`${coverageRows.length} anchors`}>
            <div style={{ display: 'grid', gap: 6 }}>
              {coverageRows.map((row: any) => (
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
              <DigestList items={missing.map((row: any) => `${row.label}: ${row.detail || 'not found'}`)} />
            ) : <DigestEmpty text="All core review anchors have structured SSOT coverage." />}
          </DigestCard>
          <DigestCard title="Open Flags" meta={`${explicitGaps.length} flags`}>
            {explicitGaps.length ? (
              <div style={{ display: 'grid', gap: 7 }}>
                {explicitGaps.slice(0, 18).map((gap: any) => (
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

  const renderGeneric = (title: any, sourceSections: any) => (
    <>
      {header}
      {sourceSections.length ? <DigestSourceSections view={{ keys: sourceSections.map((s: any) => s.key) }} sections={sections} statusByKey={statusByKey} t={t} /> : <DigestEmpty />}
    </>
  );

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

  return {
    renderOverview,
    renderFeatures,
    renderFeatureMap,
    renderArchitecture,
    renderFunctionModel,
    renderFsm,
    renderCycleModel,
    renderInterfaces,
    renderRegisters,
    renderDataflow,
    renderClocking,
    renderReviewGaps,
    renderRawYaml,
    renderGates,
    renderGeneric,
    renderScenarios,
  };
};
