// sim-debug-module-signals.tsx — the RTL module-signal feature extracted from
// the SimDebug root as a self-contained hook (split "by feature", keeping the
// root closure lean). Owns the per-module signal list (ports + internal
// nets/vars elaborated by pyslang via /api/module/signals), the in/out/internal
// filter, the rtl/vcd source toggle, and the click → focus + source-jump
// handler. The root wires it to its source viewer + selection state through the
// callbacks passed in.
//
// Load order: imported by sim-debug.tsx. Owns no window bridge.
import { useState, useCallback, useEffect, useRef } from 'react';
import type { ModuleSignal } from './sim-debug-helpers';
import { normalizeProjectSourcePath } from './sim-debug-helpers';

interface UseModuleSignalsArgs {
  ipName: string;
  rtlTop: string;
  loadSourceFile: (path: string, cursorLine?: number) => void;
  setSelectedSig: (name: string) => void;
  setSelectedSigScope: (scope: string) => void;
}

export interface ModuleSignalsApi {
  moduleSignals: ModuleSignal[];
  moduleSignalsModule: string;
  moduleSignalsScope: string;
  moduleSignalsLoading: boolean;
  moduleSignalsError: string;
  signalFilter: string;
  setSignalFilter: (v: string) => void;
  signalSource: string;
  setSignalSource: (v: string) => void;
  loadModuleSignals: (moduleName: string) => Promise<void> | void;
  onSelectModuleSignal: (sig: ModuleSignal) => void;
}

export const useModuleSignals = ({
  ipName, rtlTop, loadSourceFile, setSelectedSig, setSelectedSigScope,
}: UseModuleSignalsArgs): ModuleSignalsApi => {
  const cacheRef = useRef(new Map<string, { signals: ModuleSignal[]; scope: string; error: string }>());
  const requestSeqRef = useRef(0);
  const [moduleSignals, setModuleSignals] = useState<ModuleSignal[]>([]);
  const [moduleSignalsModule, setModuleSignalsModule] = useState('');
  const [moduleSignalsScope, setModuleSignalsScope] = useState('');
  const [moduleSignalsLoading, setModuleSignalsLoading] = useState(false);
  const [moduleSignalsError, setModuleSignalsError] = useState('');
  const [signalFilter, setSignalFilter] = useState('all');   // all | in | out | internal
  const [signalSource, setSignalSource] = useState('rtl');   // rtl | vcd

  // Reset when the active IP changes — stale signals must not survive a
  // workspace switch.
  useEffect(() => {
    requestSeqRef.current += 1;
    setModuleSignals([]);
    setModuleSignalsModule('');
    setModuleSignalsScope('');
    setModuleSignalsError('');
  }, [ipName]);

  // Elaborate one module's ports + internal nets/vars via pyslang.
  const loadModuleSignals = useCallback(async (moduleName: string) => {
    if (!moduleName || !ipName) {
      setModuleSignals([]);
      setModuleSignalsModule('');
      setModuleSignalsScope('');
      return;
    }
    const top = rtlTop || ipName;
    const key = `${ipName}::${top}::${moduleName}`;
    const cached = cacheRef.current.get(key);
    if (cached) {
      setModuleSignals(cached.signals);
      setModuleSignalsModule(moduleName);
      setModuleSignalsScope(cached.scope);
      setModuleSignalsError(cached.error);
      if (cached.signals.length) setSignalSource('rtl');
      return;
    }
    const seq = ++requestSeqRef.current;
    setModuleSignalsLoading(true);
    setModuleSignalsError('');
    try {
      const r = await fetch('/api/module/signals?module=' + encodeURIComponent(moduleName) +
                            '&top=' + encodeURIComponent(top) +
                            '&ip=' + encodeURIComponent(ipName));
      const d = await r.json();
      if (seq !== requestSeqRef.current) return;
      const sigs: ModuleSignal[] = Array.isArray(d.signals) ? d.signals : [];
      const entry = { signals: sigs, scope: String(d.instance_path || ''), error: sigs.length ? '' : (d.error || '') };
      cacheRef.current.set(key, entry);
      setModuleSignals(sigs);
      setModuleSignalsModule(moduleName);
      setModuleSignalsScope(entry.scope);
      setModuleSignalsError(entry.error);
      if (sigs.length) setSignalSource('rtl');
    } catch (e) {
      if (seq !== requestSeqRef.current) return;
      setModuleSignals([]);
      setModuleSignalsError(String(e));
    } finally {
      if (seq === requestSeqRef.current) setModuleSignalsLoading(false);
    }
  }, [ipName, rtlTop]);

  // Click a module signal → focus it (so Ctrl+W can pin it to the wave) and
  // jump source to its declaration. Preserve the RTL instance scope so common
  // port names like clk/rst/irq do not become ambiguous across the whole VCD.
  const onSelectModuleSignal = useCallback((sig: ModuleSignal) => {
    if (!sig || !sig.name) return;
    setSelectedSig(sig.name);
    setSelectedSigScope(moduleSignalsScope || '');
    const fl = String(sig.file_line || (sig.file && sig.line ? `${sig.file}:${sig.line}` : '')).trim();
    const m = fl.match(/^(.*):(\d+)$/);
    if (m) loadSourceFile(normalizeProjectSourcePath(m[1]), parseInt(m[2], 10));
  }, [loadSourceFile, moduleSignalsScope, setSelectedSig, setSelectedSigScope]);

  return {
    moduleSignals, moduleSignalsModule, moduleSignalsScope, moduleSignalsLoading,
    moduleSignalsError, signalFilter, setSignalFilter, signalSource, setSignalSource,
    loadModuleSignals, onSelectModuleSignal,
  };
};
