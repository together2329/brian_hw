// workspace-feed-terminal.tsx — ATLAS terminal-transcript renderer.
//
// Extracted from workspace-feed-cards.tsx as part of the strangler-fig
// TypeScript migration to keep each module under 1000 lines. This is an
// INERT mirror: the legacy workspace.jsx still serves the live app.
//
// Owns: the terminal-transcript detection + tokenizer + renderer family —
// section regex, transcript-kind sniff, per-line role/kind classification,
// inline token chipping, and the <AtlasTerminalTranscript> component that
// pretty-prints /context, /compact, /todo, and conversation dumps.
//
// Migration notes (house style):
//   - Real ES module. `React.Fragment` -> imported `Fragment` (automatic JSX
//     runtime, so no `import React` for JSX itself).
//   - Cross-module pure helpers (_unwrapAtlasOutputFence, _CHIP_PATH_RE) come
//     from the sibling modules; window-shaped values stay typed `any`.
import { Fragment } from 'react';

import { _unwrapAtlasOutputFence } from './workspace-report-status';
import { _CHIP_PATH_RE } from './workspace-markdown-chips';

export const _ATLAS_TERMINAL_SECTION_RE = /^(?:#+\s*)?(Compression Summary|Context Usage|Full Conversation Context|Full Conversation History|Goals|Completed|Decisions & Conventions|Errors & Fixes|In Progress \/ Next|Key Files & Symbols|User Preferences|Todo Status|Recent Messages|Stats|Memory Rules|Rules|Skills)\b/i;

export const _atlasTerminalTranscriptKind = (text: any) => {
  const body = String(_unwrapAtlasOutputFence(text) || '');
  if (!body.trim()) return '';
  if (/Compression Summary/i.test(body)) return 'compact';
  if (/Context Usage/i.test(body) && /Full Conversation (?:Context|History)/i.test(body)) return 'context';
  if (/Todo Status/i.test(body) || /^\s*── TODO ──/mi.test(body)) return 'todo';
  if (/^\s*\[(?:\d+\]\s+)?(?:SYSTEM|USER|ASSISTANT|TOOL)\b/mi.test(body)) return 'transcript';
  return '';
};

export const _atlasTerminalRole = (line: any) => {
  const trimmed = String(line || '').trim();
  const match = trimmed.match(/^\[(?:\d+\]\s+)?(SYSTEM|USER|ASSISTANT|TOOL)\b/i)
    || trimmed.match(/^\[(SYSTEM|USER|ASSISTANT|TOOL)\]/i);
  return match ? match[1].toLowerCase() : '';
};

export const _atlasTerminalLineKind = (line: any) => {
  const trimmed = String(line || '').trim();
  if (!trimmed) return 'blank';
  if (/^[=\-─]{8,}$/.test(trimmed)) return 'separator';
  const role = _atlasTerminalRole(trimmed);
  if (role) return `role role-${role}`;
  if (_ATLAS_TERMINAL_SECTION_RE.test(trimmed)) return 'section';
  if (/^(?:\/context|\/compact|\/todo|\/memory|-v\/context|\/context\s+-v)\b/i.test(trimmed)) return 'command';
  if (/^\[(?:Todo Status|Ongoing Task|Resume after compression)\]/i.test(trimmed)) return 'callout';
  if (/^\s*[•*-]\s+/.test(line)) return 'bullet';
  return 'text';
};

export const _atlasTerminalTokenClass = (token: any) => {
  const t = String(token || '');
  const bare = t.replace(/^`|`$/g, '').replace(/[),.;:]+$/g, '');
  if (!bare.trim()) return '';
  if (/^`.*`$/.test(t)) return 'att-chip att-code';
  if (/^(?:CLAIMED|VERIFIED|PASSED|FAILED|MISSING|RUNNING|READY)$/i.test(bare)) return 'att-chip att-status';
  if (/^\[(?:approved|pending|in_progress|completed|rejected|review)\]$/i.test(bare)) return 'att-chip att-status';
  if (/^(?:0x[0-9a-f]+|\d+(?:\.\d+)?(?:k|m|%|s|ms|us|bytes?)?)$/i.test(bare)) return 'att-chip att-number';
  if (/[A-Za-z0-9_.-]+\/[A-Za-z0-9_./-]+/.test(bare) || _CHIP_PATH_RE.test(bare)) return 'att-chip att-path';
  if (/^[A-Z][A-Z0-9_]{2,}(?:\[[^\]]+\])?$/.test(bare)) return 'att-chip att-signal';
  if (/^[a-z][a-z0-9_]*_[a-z0-9_]+(?:\[[^\]]+\])?$/i.test(bare)) return 'att-chip att-signal';
  return '';
};

export const _renderAtlasTerminalInline = (line: any, lineKey: any) => {
  const parts = String(line || '').split(/(`[^`]+`|[A-Za-z0-9_.-]+\/[A-Za-z0-9_./-]+|0x[0-9A-Fa-f]+|\[[A-Za-z_ -]+\]|[A-Za-z_][A-Za-z0-9_]*(?:\[[^\]\s]+\])?|\d+(?:\.\d+)?(?:k|m|%|s|ms|us|bytes?)?)/g);
  return parts.map((part, idx) => {
    if (!part) return null;
    const cls = _atlasTerminalTokenClass(part);
    if (!cls) return <Fragment key={`${lineKey}-${idx}`}>{part}</Fragment>;
    const clean = /^`.*`$/.test(part) ? part.slice(1, -1) : part;
    return <span key={`${lineKey}-${idx}`} className={cls}>{clean}</span>;
  });
};

export const AtlasTerminalTranscript = ({ text, kind }: any) => {
  const body = String(_unwrapAtlasOutputFence(text) || '').replace(/\r\n?/g, '\n').trimEnd();
  const lines = body.split('\n');
  return (
    <div className={`atlas-terminal-transcript atlas-terminal-${kind || 'transcript'}`}>
      {lines.map((line, idx) => {
        const lineKind = _atlasTerminalLineKind(line);
        if (lineKind === 'separator') {
          return <div key={idx} className="att-line att-separator" />;
        }
        return (
          <div key={idx} className={`att-line att-${lineKind}`}>
            {line ? _renderAtlasTerminalInline(line, idx) : ' '}
          </div>
        );
      })}
    </div>
  );
};
