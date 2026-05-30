/* workspace.tsx — THE ES-MODULE ROOT of the migrated ATLAS workspace.
 *
 * This is the thin composer that sits at the apex of the strangler-fig
 * migration of workspace.jsx. It owns nothing itself: every component,
 * hook, and helper now lives in a sibling .tsx module. This file merely:
 *
 *   1. imports the root `Workspace` component (defined in workspace-root.tsx)
 *      plus every symbol that the legacy file published onto `window`, each
 *      from the sibling module that now owns it;
 *   2. re-exports those symbols so ES importers of `./workspace` keep working;
 *   3. reproduces — byte-for-byte in spirit — the `window.X = X` bridge block
 *      from the tail of workspace.jsx (Phase 13a–13g), so the not-yet-migrated
 *      .jsx consumers (preview-pane.jsx, ssot-digest.jsx, ssot-doc.jsx,
 *      ssot-qa-board.jsx, workspace-panels.jsx, workflow-report.jsx, app-shell)
 *      find the same globals they always have.
 *
 * INERT mirror — the live app is still served by workspace.jsx. The gate is:
 * tsc-clean + vitest-green + window.Workspace registered + public exports
 * intact. Do NOT treat this module as the live source of truth, and do NOT
 * modify workspace.jsx (which remains the production bundle entry).
 *
 * Bridge fidelity: the 83 top-level `window.X` assignments below mirror the
 * legacy tail (workspace.jsx L452, L1397, L13177–L13286). `FoldablePane` is a
 * pure passthrough — workspace.jsx reads it from window (L13193) and rebinds
 * it (L13203); we do the same so the global survives this module's evaluation.
 */

// ── Root component (owns Workspace) ───────────────────────────────
import { Workspace } from './workspace-root';

// ── Report / status helpers ───────────────────────────────────────
import {
  WORKFLOW_REPORT_TABS,
  AtlasStatusBadge,
  atlasStatusMeta,
  _limitAtlasLines,
} from './workspace-report-status';

// ── Session routing / health / exec-mode helpers ──────────────────
import {
  ssotIpFromSession,
  isSsotYamlPath,
  normalizeUiSession,
  healthMatchesCurrentUser,
  uiEffectiveHealthSession,
  uiHealthCountersMatchBrowserRoute,
  uiSessionRoute,
  atlasUiExecMode,
} from './workspace-session-routing';

// ── Markdown / chip / clipboard helpers ───────────────────────────
import {
  _copyToClipboard,
  _markdownHtml,
  _normalizeMarkdownImageSrc,
  _postProcessMarkdownNode,
} from './workspace-markdown-chips';

// ── Async resource / preview helpers ──────────────────────────────
import {
  atlasFileTreeMetaForPath,
  atlasFormatBytes,
  atlasImageMimeForExt,
  scheduleAtlasPreviewWork,
  useAtlasAsyncResource,
} from './workspace-async-resource';

// ── Tool / worker-snapshot helpers ────────────────────────────────
import { workspaceFetchWorkerSnapshot } from './workspace-tool-theme';

// ── Feed cards / ask-user block / escaping ────────────────────────
import {
  _escHtml,
  AskUserQuestionBlock,
} from './workspace-feed-cards';

// ── SSOT extraction + section helpers ─────────────────────────────
import {
  SSOT_SECTION_LABELS,
  ssotTitleFor,
  _hasMeaningfulRegisterField,
  _hasRegisterDetail,
  blockField,
  blockListValues,
  buildReferenceTokens,
  digestViewsForSections,
  extractFeatures,
  extractFsms,
  extractModuleContracts,
  extractRegisters,
  extractReviewInterfaces,
  extractReviewPins,
  extractScenarios,
  extractSubmodules,
  fieldFromText,
  linkifyReferences,
  listBlocksFromSection,
  mapGroupsFromSection,
  sectionByKey,
  sectionFact,
  sourceSectionsForDigestView,
  splitSsotSections,
  ssotNeedsAttentionStatus,
  ssotPathOf,
  ssotProgressStatusMap,
  ssotSectionStatus,
  ssotStatusColor,
  ssotStatusGlyph,
  ssotStatusKey,
  ssotValuePresent,
  trimSsotValue,
} from './workspace-ssot-extract';

// ── SSOT FSM / digest primitives + gates ──────────────────────────
import {
  DigestEmpty,
  DigestKV,
  DigestList,
  compactDigestItems,
  FsmTransitionDiagram,
  fsmGraphFromMachine,
  uniqueFsmStates,
  GatesPanel,
} from './workspace-ssot-fsm';

// ── SSOT panels (module tree, registers, features, scenarios) ─────
import {
  DigestSourceSections,
  FeatureCard,
  ModuleTree,
  PipelineTraceDiagram,
  RegisterBitFieldView,
  SsotCommandPalette,
  SsotScenarioPlayer,
  SubmoduleCell,
  chooseSsotFile,
  _formatWidth,
  _ifaceColor,
  _ifaceKind,
  _maxNestingDepth,
} from './workspace-ssot-panels';

// ── Todo graph ────────────────────────────────────────────────────
import { TodoGraph } from './workspace-todo';

// ── Git diff status glyph ─────────────────────────────────────────
import { _statusGlyph } from './workspace-git-diff';

// ── Lint / coverage / YAML fold helpers ───────────────────────────
import {
  _FOLD_KIND_COLOR,
  _buildFoldTree,
  _highlightYamlLine,
} from './workspace-lint-coverage';

// `FoldablePane` is owned by foldable-pane.jsx (not yet migrated). The legacy
// file reads it from window (workspace.jsx L13193) and rebinds it (L13203);
// mirror that passthrough so the global survives this module's evaluation.
const FoldablePane: any = (window as any).FoldablePane;

// ── Re-export the public surface ──────────────────────────────────
// workspace.jsx published no ES exports (classic script). These re-exports
// let ES importers of `./workspace` reach the same symbols the globals expose.
export {
  Workspace,
  WORKFLOW_REPORT_TABS,
  AtlasStatusBadge,
  atlasStatusMeta,
  _limitAtlasLines,
  ssotIpFromSession,
  isSsotYamlPath,
  normalizeUiSession,
  healthMatchesCurrentUser,
  uiEffectiveHealthSession,
  uiHealthCountersMatchBrowserRoute,
  uiSessionRoute,
  atlasUiExecMode,
  _copyToClipboard,
  _markdownHtml,
  _normalizeMarkdownImageSrc,
  _postProcessMarkdownNode,
  atlasFileTreeMetaForPath,
  atlasFormatBytes,
  atlasImageMimeForExt,
  scheduleAtlasPreviewWork,
  useAtlasAsyncResource,
  workspaceFetchWorkerSnapshot,
  _escHtml,
  AskUserQuestionBlock,
  SSOT_SECTION_LABELS,
  ssotTitleFor,
  _hasMeaningfulRegisterField,
  _hasRegisterDetail,
  blockField,
  blockListValues,
  buildReferenceTokens,
  digestViewsForSections,
  extractFeatures,
  extractFsms,
  extractModuleContracts,
  extractRegisters,
  extractReviewInterfaces,
  extractReviewPins,
  extractScenarios,
  extractSubmodules,
  fieldFromText,
  linkifyReferences,
  listBlocksFromSection,
  mapGroupsFromSection,
  sectionByKey,
  sectionFact,
  sourceSectionsForDigestView,
  splitSsotSections,
  ssotNeedsAttentionStatus,
  ssotPathOf,
  ssotProgressStatusMap,
  ssotSectionStatus,
  ssotStatusColor,
  ssotStatusGlyph,
  ssotStatusKey,
  ssotValuePresent,
  trimSsotValue,
  DigestEmpty,
  DigestKV,
  DigestList,
  compactDigestItems,
  FsmTransitionDiagram,
  fsmGraphFromMachine,
  uniqueFsmStates,
  GatesPanel,
  DigestSourceSections,
  FeatureCard,
  ModuleTree,
  PipelineTraceDiagram,
  RegisterBitFieldView,
  SsotCommandPalette,
  SsotScenarioPlayer,
  SubmoduleCell,
  chooseSsotFile,
  _formatWidth,
  _ifaceColor,
  _ifaceKind,
  _maxNestingDepth,
  TodoGraph,
  _statusGlyph,
  _FOLD_KIND_COLOR,
  _buildFoldTree,
  _highlightYamlLine,
};

// ── window bridges ────────────────────────────────────────────────
// Reproduces the legacy workspace.jsx tail so not-yet-migrated .jsx consumers
// keep finding their globals. Grouped + ordered to match the original phases.
const w = window as any;

// app-shell.tsx mounts the workspace by reading window.Workspace.
w.Workspace = Workspace;

// Phase 13a/13b: early single bridges (workspace.jsx L1397 / L452).
w.ssotIpFromSession = ssotIpFromSession; // consumed by ssot-doc.jsx
w.WORKFLOW_REPORT_TABS = WORKFLOW_REPORT_TABS; // consumed by workflow-report.jsx

// Phase 13d: expose preview-pane.jsx deps.
w._FOLD_KIND_COLOR = _FOLD_KIND_COLOR;
w._buildFoldTree = _buildFoldTree;
w._copyToClipboard = _copyToClipboard;
w._escHtml = _escHtml;
w._highlightYamlLine = _highlightYamlLine;
w._markdownHtml = _markdownHtml;
w._normalizeMarkdownImageSrc = _normalizeMarkdownImageSrc;
w._postProcessMarkdownNode = _postProcessMarkdownNode;
w.atlasFileTreeMetaForPath = atlasFileTreeMetaForPath;
w.atlasFormatBytes = atlasFormatBytes;
w.atlasImageMimeForExt = atlasImageMimeForExt;
w.scheduleAtlasPreviewWork = scheduleAtlasPreviewWork;
w.useAtlasAsyncResource = useAtlasAsyncResource;

// Phase 13c: expose ssot-digest.jsx deps.
w.AtlasStatusBadge = AtlasStatusBadge;
w.DigestEmpty = DigestEmpty;
w.DigestKV = DigestKV;
w.DigestList = DigestList;
w.DigestSourceSections = DigestSourceSections;
w.FeatureCard = FeatureCard;
w.FoldablePane = FoldablePane; // passthrough (read from window above)
w.FsmTransitionDiagram = FsmTransitionDiagram;
w.GatesPanel = GatesPanel;
w.ModuleTree = ModuleTree;
w.PipelineTraceDiagram = PipelineTraceDiagram;
w.RegisterBitFieldView = RegisterBitFieldView;
w.SsotCommandPalette = SsotCommandPalette;
w.SsotScenarioPlayer = SsotScenarioPlayer;
w.SubmoduleCell = SubmoduleCell;
w._formatWidth = _formatWidth;
w._hasMeaningfulRegisterField = _hasMeaningfulRegisterField;
w._hasRegisterDetail = _hasRegisterDetail;
w._ifaceColor = _ifaceColor;
w._ifaceKind = _ifaceKind;
w._maxNestingDepth = _maxNestingDepth;
w.blockField = blockField;
w.blockListValues = blockListValues;
w.buildReferenceTokens = buildReferenceTokens;
w.chooseSsotFile = chooseSsotFile;
w.compactDigestItems = compactDigestItems;
w.digestViewsForSections = digestViewsForSections;
w.extractFeatures = extractFeatures;
w.extractFsms = extractFsms;
w.extractModuleContracts = extractModuleContracts;
w.extractRegisters = extractRegisters;
w.extractReviewInterfaces = extractReviewInterfaces;
w.extractReviewPins = extractReviewPins;
w.extractScenarios = extractScenarios;
w.extractSubmodules = extractSubmodules;
w.fieldFromText = fieldFromText;
w.fsmGraphFromMachine = fsmGraphFromMachine;
w.isSsotYamlPath = isSsotYamlPath;
w.linkifyReferences = linkifyReferences;
w.listBlocksFromSection = listBlocksFromSection;
w.mapGroupsFromSection = mapGroupsFromSection;
w.sectionByKey = sectionByKey;
w.sectionFact = sectionFact;
w.sourceSectionsForDigestView = sourceSectionsForDigestView;
w.splitSsotSections = splitSsotSections;
w.ssotNeedsAttentionStatus = ssotNeedsAttentionStatus;
w.ssotPathOf = ssotPathOf;
w.ssotProgressStatusMap = ssotProgressStatusMap;
w.ssotSectionStatus = ssotSectionStatus;
w.ssotStatusColor = ssotStatusColor;
w.ssotStatusGlyph = ssotStatusGlyph;
w.ssotStatusKey = ssotStatusKey;
w.ssotTitleFor = ssotTitleFor;
w.ssotValuePresent = ssotValuePresent;
w.trimSsotValue = trimSsotValue;
w.uniqueFsmStates = uniqueFsmStates;
w.SSOT_SECTION_LABELS = SSOT_SECTION_LABELS;

// Phase 13f: expose ssot-qa-board.jsx deps.
w.AskUserQuestionBlock = AskUserQuestionBlock;
w.atlasStatusMeta = atlasStatusMeta;
w.normalizeUiSession = normalizeUiSession;

// Phase 13g: expose workspace-panels.jsx deps.
w.TodoGraph = TodoGraph;
w._limitAtlasLines = _limitAtlasLines;
w._statusGlyph = _statusGlyph;
w.atlasUiExecMode = atlasUiExecMode;
w.healthMatchesCurrentUser = healthMatchesCurrentUser;
w.uiEffectiveHealthSession = uiEffectiveHealthSession;
w.uiHealthCountersMatchBrowserRoute = uiHealthCountersMatchBrowserRoute;
w.uiSessionRoute = uiSessionRoute;
w.workspaceFetchWorkerSnapshot = workspaceFetchWorkerSnapshot;
