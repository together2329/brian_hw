import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { SsotDocPane } from '../ssot-doc';
import {
  buildSsotDocTargetFromElement,
  dispatchSsotDocComment,
  findSsotDocSelectableElement,
  markSsotDocSelection,
} from '../ssot-doc-feedback-dom';

describe('SSOT DOC Feedback Mode target selection', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    window.history.pushState({}, '', '/');
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(() => {
    cleanup();
  });

  it('resolves the nearest rendered DOC component with SSOT mapping attributes', () => {
    const section = document.createElement('section');
    section.setAttribute('data-ssot-section', 'registers');
    section.setAttribute('data-ssot-path', 'registers.register_list.0');
    section.setAttribute('data-ssot-label', 'CTRL');
    section.setAttribute('data-ssot-kind', 'register');
    const child = document.createElement('span');
    section.appendChild(child);

    expect(buildSsotDocTargetFromElement(child)).toEqual({
      section: 'registers',
      path: 'registers.register_list.0',
      label: 'CTRL',
      kind: 'register',
    });
  });

  it('resolves selectable elements from an iframe document realm', () => {
    const iframe = document.createElement('iframe');
    document.body.appendChild(iframe);
    const iframeDoc = iframe.contentDocument;
    if (!iframeDoc) throw new Error('iframe document unavailable');
    iframeDoc.body.innerHTML = [
      '<table>',
      '<tbody>',
      '<tr data-ssot-section="registers" data-ssot-path="registers.register_list.0.fields.0" data-ssot-label="enable" data-ssot-kind="register_field">',
      '<td>enable</td>',
      '</tr>',
      '</tbody>',
      '</table>',
    ].join('');

    const cell = iframeDoc.querySelector('td');
    if (!cell) throw new Error('iframe cell unavailable');
    const selectable = findSsotDocSelectableElement(cell);

    expect(selectable?.getAttribute('data-ssot-path')).toBe('registers.register_list.0.fields.0');
    expect(buildSsotDocTargetFromElement(selectable)).toEqual({
      section: 'registers',
      path: 'registers.register_list.0.fields.0',
      label: 'enable',
      kind: 'register_field',
    });
  });

  it('marks a DOC component without forcing the page to scroll', () => {
    const row = document.createElement('section');
    const scrollIntoView = vi.fn();
    Object.defineProperty(row, 'scrollIntoView', {
      configurable: true,
      value: scrollIntoView,
    });
    document.body.appendChild(row);

    markSsotDocSelection(row);

    expect(row.getAttribute('data-atlas-doc-feedback-selected')).toBe('1');
    expect(scrollIntoView).not.toHaveBeenCalled();
  });

  it('renders source/comment actions disabled until a component is selected', () => {
    render(<SsotDocPane uiLang="en" ip="doc_source_ip" />);

    fireEvent.click(screen.getByRole('button', { name: /Feedback Mode/i }));

    expect(screen.getByRole('button', { name: /Show SSOT/i })).toBeDisabled();
    expect(screen.getByRole('button', { name: /Send to chat/i })).toBeDisabled();
  });

  it('uses chat-style feedback entry instead of an inline value writer', () => {
    render(<SsotDocPane uiLang="en" ip="doc_source_ip" />);

    fireEvent.click(screen.getByRole('button', { name: /Feedback Mode/i }));

    expect(screen.getByPlaceholderText(/chat feedback/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /send to chat/i })).toBeDisabled();
    expect(screen.queryByPlaceholderText(/value to write/i)).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /apply feedback/i })).not.toBeInTheDocument();
  });

  it('renders the DOC export iframe with the active workspace session', () => {
    window.history.pushState({}, '', '/?session=admin%2Fdefault%2Fmctp_axi%2Fsim_debug&ip=mctp_axi');

    render(<SsotDocPane uiLang="en" ip="mctp_axi" />);

    const frame = screen.getByTestId('ssot-doc-frame') as HTMLIFrameElement;
    const url = new URL(frame.src);
    expect(url.pathname).toBe('/api/ssot/export');
    expect(url.searchParams.get('ip')).toBe('mctp_axi');
    expect(url.searchParams.get('session_id')).toBe('admin/default/mctp_axi/sim_debug');
  });

  it('dispatches a structured chat prefill event for the selected DOC source', () => {
    const listener = vi.fn();
    window.addEventListener('atlas-ssot-doc-comment', listener);

    dispatchSsotDocComment({
      ip: 'demo_ip',
      target: {
        section: 'registers',
        path: 'registers.register_list.0.fields.0.description',
        label: 'CTRL.enable.description',
        kind: 'register_field',
      },
      comment: 'Explain why this bit is W1C.',
      selectedText: 'Enable transfer',
      source: {
        ok: true,
        ip: 'demo_ip',
        ssot_path: 'demo_ip/yaml/demo_ip.ssot.yaml',
        section: 'registers',
        path: 'registers.register_list.0.fields.0.description',
        label: 'CTRL.enable.description',
        kind: 'register_field',
        value: 'Enable transfer',
        yaml: 'description: Enable transfer\n',
        feedback: [],
      },
    });

    expect(listener).toHaveBeenCalledTimes(1);
    const event = listener.mock.calls[0][0] as CustomEvent;
    expect(event.detail.text).toContain('/to-ssot demo_ip');
    expect(event.detail.target.path).toBe('registers.register_list.0.fields.0.description');

    window.removeEventListener('atlas-ssot-doc-comment', listener);
  });
});
