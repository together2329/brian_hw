// ssot-digest-content-globals.tsx — cross-file global forward-refs for
// ssot-digest-content.tsx (extracted to keep the source under 1000 lines).
//
// These are the ~40 lambda forward-refs to cross-file globals OWNED BY OTHER
// FILES (helpers/components still living in .jsx), plus `sectionFact` which is
// owned by workspace.jsx. Each resolves `window.X` at call time so the exact
// runtime behavior of the original is preserved — they are not (yet) declared
// in types/atlas-window.d.ts, so a narrow `win` cast is used (same pattern as
// block-diagram.tsx).
import { type ReactNode } from 'react';

export interface SsotDigestContentProps {
  view: any;
  sections: any;
  statusByKey?: any;
  uiLang?: string;
  content?: string;
  selected?: string;
  onJump?: any;
  feedbackMode?: boolean;
}

// ── Narrow cast for undeclared cross-file globals ─────────────────────
// types/atlas-window.d.ts does not (yet) declare these helper/component
// globals (owned by other still-.jsx files), so reference them through a
// locally-typed view of window. This preserves the exact runtime reads
// without spraying `any`.
export interface SsotDigestContentWindow {
  AtlasStatusBadge?: (...a: unknown[]) => unknown;
  BlockDiagram?: (...a: unknown[]) => unknown;
  DigestCard?: (...a: unknown[]) => unknown;
  DigestEmpty?: (...a: unknown[]) => unknown;
  DigestKV?: (...a: unknown[]) => unknown;
  DigestList?: (...a: unknown[]) => unknown;
  DigestSourceSections?: (...a: unknown[]) => unknown;
  FeatureCard?: (...a: unknown[]) => unknown;
  FoldablePane?: (...a: unknown[]) => unknown;
  FsmTransitionDiagram?: (...a: unknown[]) => unknown;
  GatesPanel?: (...a: unknown[]) => unknown;
  ModuleTree?: (...a: unknown[]) => unknown;
  PipelineTraceDiagram?: (...a: unknown[]) => unknown;
  RegisterBitFieldView?: (...a: unknown[]) => unknown;
  SsotCommandPalette?: (...a: unknown[]) => unknown;
  SsotScenarioPlayer?: (...a: unknown[]) => unknown;
  _formatWidth?: (...a: unknown[]) => unknown;
  _hasMeaningfulRegisterField?: (...a: unknown[]) => unknown;
  _hasRegisterDetail?: (...a: unknown[]) => unknown;
  blockField?: (...a: unknown[]) => unknown;
  blockListValues?: (...a: unknown[]) => unknown;
  buildReferenceTokens?: (...a: unknown[]) => unknown;
  compactDigestItems?: (...a: unknown[]) => unknown;
  extractFeatures?: (...a: unknown[]) => unknown;
  extractFsms?: (...a: unknown[]) => unknown;
  extractModuleContracts?: (...a: unknown[]) => unknown;
  extractRegisters?: (...a: unknown[]) => unknown;
  extractReviewInterfaces?: (...a: unknown[]) => unknown;
  extractReviewPins?: (...a: unknown[]) => unknown;
  extractScenarios?: (...a: unknown[]) => unknown;
  extractSubmodules?: (...a: unknown[]) => unknown;
  fieldFromText?: (...a: unknown[]) => unknown;
  fsmGraphFromMachine?: (...a: unknown[]) => unknown;
  linkifyReferences?: (...a: unknown[]) => unknown;
  listBlocksFromSection?: (...a: unknown[]) => unknown;
  mapGroupsFromSection?: (...a: unknown[]) => unknown;
  sectionByKey?: (...a: unknown[]) => unknown;
  sectionFact?: (...a: unknown[]) => unknown;
  sourceSectionsForDigestView?: (...a: unknown[]) => unknown;
  ssotTitleFor?: (...a: unknown[]) => unknown;
  ssotValuePresent?: (...a: unknown[]) => unknown;
  trimSsotValue?: (...a: unknown[]) => unknown;
  uniqueFsmStates?: (...a: unknown[]) => unknown;
  SsotDigestContent?: (props: SsotDigestContentProps) => ReactNode;
}

export const win = window as unknown as SsotDigestContentWindow & Window;

// Forward-refs to cross-file globals (resolved at call time):
export const AtlasStatusBadge = (...a: any[]): any => win.AtlasStatusBadge!(...a);
export const BlockDiagram = (...a: any[]): any => win.BlockDiagram!(...a);
export const DigestCard = (...a: any[]): any => win.DigestCard!(...a);
export const DigestEmpty = (...a: any[]): any => win.DigestEmpty!(...a);
export const DigestKV = (...a: any[]): any => win.DigestKV!(...a);
export const DigestList = (...a: any[]): any => win.DigestList!(...a);
export const DigestSourceSections = (...a: any[]): any => win.DigestSourceSections!(...a);
export const FeatureCard = (...a: any[]): any => win.FeatureCard!(...a);
export const FoldablePane = (...a: any[]): any => win.FoldablePane!(...a);
export const FsmTransitionDiagram = (...a: any[]): any => win.FsmTransitionDiagram!(...a);
export const GatesPanel = (...a: any[]): any => win.GatesPanel!(...a);
export const ModuleTree = (...a: any[]): any => win.ModuleTree!(...a);
export const PipelineTraceDiagram = (...a: any[]): any => win.PipelineTraceDiagram!(...a);
export const RegisterBitFieldView = (...a: any[]): any => win.RegisterBitFieldView!(...a);
export const SsotCommandPalette = (...a: any[]): any => win.SsotCommandPalette!(...a);
export const SsotScenarioPlayer = (...a: any[]): any => win.SsotScenarioPlayer!(...a);
export const _formatWidth = (...a: any[]): any => win._formatWidth!(...a);
export const _hasMeaningfulRegisterField = (...a: any[]): any => win._hasMeaningfulRegisterField!(...a);
export const _hasRegisterDetail = (...a: any[]): any => win._hasRegisterDetail!(...a);
export const blockField = (...a: any[]): any => win.blockField!(...a);
export const blockListValues = (...a: any[]): any => win.blockListValues!(...a);
export const buildReferenceTokens = (...a: any[]): any => win.buildReferenceTokens!(...a);
export const compactDigestItems = (...a: any[]): any => win.compactDigestItems!(...a);
export const extractFeatures = (...a: any[]): any => win.extractFeatures!(...a);
export const extractFsms = (...a: any[]): any => win.extractFsms!(...a);
export const extractModuleContracts = (...a: any[]): any => win.extractModuleContracts!(...a);
export const extractRegisters = (...a: any[]): any => win.extractRegisters!(...a);
export const extractReviewInterfaces = (...a: any[]): any => win.extractReviewInterfaces!(...a);
export const extractReviewPins = (...a: any[]): any => win.extractReviewPins!(...a);
export const extractScenarios = (...a: any[]): any => win.extractScenarios!(...a);
export const extractSubmodules = (...a: any[]): any => win.extractSubmodules!(...a);
export const fieldFromText = (...a: any[]): any => win.fieldFromText!(...a);
export const fsmGraphFromMachine = (...a: any[]): any => win.fsmGraphFromMachine!(...a);
export const linkifyReferences = (...a: any[]): any => win.linkifyReferences!(...a);
export const listBlocksFromSection = (...a: any[]): any => win.listBlocksFromSection!(...a);
export const mapGroupsFromSection = (...a: any[]): any => win.mapGroupsFromSection!(...a);
export const sectionByKey = (...a: any[]): any => win.sectionByKey!(...a);
export const sourceSectionsForDigestView = (...a: any[]): any => win.sourceSectionsForDigestView!(...a);
export const ssotTitleFor = (...a: any[]): any => win.ssotTitleFor!(...a);
export const ssotValuePresent = (...a: any[]): any => win.ssotValuePresent!(...a);
export const trimSsotValue = (...a: any[]): any => win.trimSsotValue!(...a);
export const uniqueFsmStates = (...a: any[]): any => win.uniqueFsmStates!(...a);
// sectionFact is owned by workspace.jsx; in the original .jsx it was called
// directly (relying on babel's loose scoping). Keep it as a forward-ref so it
// resolves window.sectionFact at call time — identical runtime behavior.
export const sectionFact = (...a: any[]): any => win.sectionFact!(...a);
