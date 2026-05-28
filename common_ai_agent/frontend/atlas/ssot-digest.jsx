// ssot-digest.jsx — Phase 13c refactor: SSOT digest + review cluster
// extracted from workspace.jsx. Four components moved as a unit (in dep
// order so internal refs stay local consts):
//
//   1. DigestCard         (12 lines)  — leaf primitive
//   2. BlockDiagram      (478 lines)  — module-tree visualization
//   3. SsotDigestContent (950 lines)  — main digest renderer (uses 1+2 + many
//                                       extract*/section* helpers)
//   4. SsotReviewPane    (583 lines)  — review wrapper around 3 + status helpers
//
// Total: ~2023 lines. workspace.jsx shrinks ~2023 lines (-10%).
//
// Load order (index.html): AFTER preview-pane.jsx, BEFORE workspace.jsx.
// Uses the same lambda forward-ref + IIFE wrapper pattern as preview-pane.jsx:
//   - IIFE keeps the forward-ref consts out of the global script scope so
//     they don't collide with workspace.jsx's same-named definitions.
//   - Each `const X = (...a) => window.X(...a)` defers the lookup to call
//     time — workspace.jsx registers all of these via `window.X = X;` at
//     end-of-file during its own load, after the consts are declared.
//   - The 4 components register themselves on window at the bottom of this
//     IIFE; workspace.jsx aliases them back via `const X = window.X;` so
//     existing render sites in workspace.jsx pick up the moved components.

(() => {

// Forward-ref to workspace.jsx helpers (resolved at call time):
// BlockDiagram was extracted to block-diagram.jsx in Phase 18; the
// SsotDigestContent body still uses <BlockDiagram .../> at JSX render
// sites, so we forward-ref it the same way.
const BlockDiagram = (...a) => window.BlockDiagram(...a);
const AtlasStatusBadge = (...a) => window.AtlasStatusBadge(...a);
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
const SubmoduleCell = (...a) => window.SubmoduleCell(...a);
const _formatWidth = (...a) => window._formatWidth(...a);
const _hasMeaningfulRegisterField = (...a) => window._hasMeaningfulRegisterField(...a);
const _hasRegisterDetail = (...a) => window._hasRegisterDetail(...a);
const _ifaceColor = (...a) => window._ifaceColor(...a);
const _ifaceKind = (...a) => window._ifaceKind(...a);
const _maxNestingDepth = (...a) => window._maxNestingDepth(...a);
const blockField = (...a) => window.blockField(...a);
const blockListValues = (...a) => window.blockListValues(...a);
const buildReferenceTokens = (...a) => window.buildReferenceTokens(...a);
const chooseSsotFile = (...a) => window.chooseSsotFile(...a);
const compactDigestItems = (...a) => window.compactDigestItems(...a);
const digestViewsForSections = (...a) => window.digestViewsForSections(...a);
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
const isSsotYamlPath = (...a) => window.isSsotYamlPath(...a);
const linkifyReferences = (...a) => window.linkifyReferences(...a);
const listBlocksFromSection = (...a) => window.listBlocksFromSection(...a);
const mapGroupsFromSection = (...a) => window.mapGroupsFromSection(...a);
const sectionByKey = (...a) => window.sectionByKey(...a);
const sectionFact = (...a) => window.sectionFact(...a);
const sourceSectionsForDigestView = (...a) => window.sourceSectionsForDigestView(...a);
const splitSsotSections = (...a) => window.splitSsotSections(...a);
const ssotNeedsAttentionStatus = (...a) => window.ssotNeedsAttentionStatus(...a);
const ssotPathOf = (...a) => window.ssotPathOf(...a);
const ssotProgressStatusMap = (...a) => window.ssotProgressStatusMap(...a);
const ssotSectionStatus = (...a) => window.ssotSectionStatus(...a);
const ssotStatusColor = (...a) => window.ssotStatusColor(...a);
const ssotStatusGlyph = (...a) => window.ssotStatusGlyph(...a);
const ssotStatusKey = (...a) => window.ssotStatusKey(...a);
const ssotTitleFor = (...a) => window.ssotTitleFor(...a);
const ssotValuePresent = (...a) => window.ssotValuePresent(...a);
const trimSsotValue = (...a) => window.trimSsotValue(...a);
const uniqueFsmStates = (...a) => window.uniqueFsmStates(...a);
const useAtlasAsyncResource = (...a) => window.useAtlasAsyncResource(...a);


const DigestCard = ({ title, meta, children }) => (
  <div style={{
    border: '1px solid var(--line)', borderRadius: 4,
    background: 'var(--bg-2)', padding: '10px 12px', minWidth: 0,
  }}>
    <div style={{ display: 'flex', gap: 8, alignItems: 'baseline', marginBottom: 7 }}>
      <span style={{ color: 'var(--accent)', fontWeight: 800, fontSize: 12 }}>{title}</span>
      {meta ? <span className="mute trunc" style={{ fontSize: 10, fontFamily: 'var(--mono)' }}>{meta}</span> : null}
    </div>
    {children}
  </div>
);



// Phase 13c window exports — workspace.jsx aliases these back.
window.DigestCard = DigestCard;
// BlockDiagram extracted to block-diagram.jsx in Phase 18.
// window.BlockDiagram is registered by that file.
// SsotDigestContent extracted to ssot-digest-content.jsx in Phase 22.
// SsotReviewPane extracted to ssot-review.jsx in Phase 21.

})();
