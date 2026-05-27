import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const here = dirname(fileURLToPath(import.meta.url));
const workspaceSrc = readFileSync(resolve(here, '../workspace.jsx'), 'utf8');
const stylesSrc = readFileSync(resolve(here, '../styles.css'), 'utf8');

describe('terminal transcript rendering hooks', () => {
  it('routes context, compact, and todo slash output to the terminal renderer', () => {
    expect(workspaceSrc).toContain('AtlasTerminalTranscript');
    expect(workspaceSrc).toContain('Compression Summary');
    expect(workspaceSrc).toContain('Full Conversation Context');
    expect(workspaceSrc).toContain('Todo Status');
    expect(workspaceSrc).toContain('_atlasTerminalTranscriptKind');
  });

  it('defines role, token, and separator styles for structured slash output', () => {
    expect(stylesSrc).toContain('.atlas-terminal-transcript');
    expect(stylesSrc).toContain('.att-role-assistant');
    expect(stylesSrc).toContain('.att-chip');
    expect(stylesSrc).toContain('.att-separator');
  });
});
