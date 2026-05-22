// vcd-parser.js — minimal pure-JS VCD parser for ATLAS sim_debug.
//
// Returns {signals, samples, timeRange, scopes} from a raw VCD string.
//   signals = [{ id, ref, scope, name, type, width, isBus }]
//   samples = { id: [[time, value], ...] }   // value is '0'/'1'/'x'/'z'/binary
//   timeRange = [tMin, tMax]
//   scopes = nested {name, type, signals:[ids], children:[scopes]}
//
// Trade-offs:
//  - Single-pass tokenizer — fast, ~10 MB/s on a modest laptop.
//  - Buses are returned as binary strings (e.g. "10110011"); convert at
//    the renderer (HEX/DEC/ENUM) since radix is per-row state in the UI.
//  - Real-value VCD entries (`r1.234`) are kept as-is.
//  - Skips $comment / $version / $date / $timescale (we re-extract
//    timescale via a regex pass — that's all we need).
//
// Reference: IEEE 1364-2005 §18.2 (VCD format).

(function () {
  'use strict';

  function parseVCD(raw) {
    if (!raw || typeof raw !== 'string') {
      return { signals: [], samples: {}, timeRange: [0, 0], scopes: null };
    }

    const signals = [];
    const samples = Object.create(null);
    const idToInfo = Object.create(null);
    let timescale = '1ns';
    let tMin = null;
    let tMax = 0;

    // Build scope tree as we go. Stack = current depth.
    const root = { name: '$root', type: 'root', signals: [], children: [] };
    const scopeStack = [root];

    // --- Header pass: walk $... commands until $enddefinitions. ---
    // VCD is whitespace-tolerant; just split into tokens.
    const tokens = raw.split(/\s+/);
    let i = 0;

    while (i < tokens.length) {
      const t = tokens[i];

      if (t === '$timescale') {
        // $timescale 1 ns $end (or 100ps etc.)
        const ts = [];
        i++;
        while (i < tokens.length && tokens[i] !== '$end') { ts.push(tokens[i]); i++; }
        timescale = ts.join('').trim();
        i++; // skip $end
        continue;
      }

      if (t === '$scope') {
        // $scope module foo $end
        const stype = tokens[i + 1] || 'module';
        const sname = tokens[i + 2] || 'unnamed';
        const node = { name: sname, type: stype, signals: [], children: [] };
        scopeStack[scopeStack.length - 1].children.push(node);
        scopeStack.push(node);
        // advance past $end
        while (i < tokens.length && tokens[i] !== '$end') i++;
        i++;
        continue;
      }

      if (t === '$upscope') {
        scopeStack.pop();
        while (i < tokens.length && tokens[i] !== '$end') i++;
        i++;
        continue;
      }

      if (t === '$var') {
        // $var wire 4 ! bit_cnt [3:0] $end
        // VCD allows the bus range either as a separate token
        // ("cnt [3:0]") or appended to the name ("cnt[3:0]" — no
        // space). Split on the first '[' so the range is normalized
        // either way.
        const stype = tokens[i + 1] || 'wire';
        const width = parseInt(tokens[i + 2] || '1', 10) || 1;
        const id = tokens[i + 3];
        const rawName = tokens[i + 4] || '';
        let baseName = rawName;
        let inlineRange = '';
        const lb = rawName.indexOf('[');
        if (lb > 0 && rawName.endsWith(']')) {
          baseName = rawName.slice(0, lb);
          inlineRange = rawName.slice(lb);
        }
        let suffix = inlineRange;
        let j = i + 5;
        while (j < tokens.length && tokens[j] !== '$end') {
          suffix += (suffix ? ' ' : '') + tokens[j];
          j++;
        }
        const scope = scopeStack[scopeStack.length - 1];
        const sig = {
          id,
          ref: baseName + (suffix ? (' ' + suffix) : ''),
          scope: scopeStack
            .slice(1)            // skip $root
            .map(s => s.name)
            .join('.'),
          name: baseName,
          type: stype,
          width,
          isBus: width > 1,
          range: suffix,           // e.g. "[3:0]"
        };
        // VCD allows the same ID to alias multiple references — keep
        // the first as canonical so samples map cleanly.
        if (!idToInfo[id]) {
          idToInfo[id] = sig;
          signals.push(sig);
          samples[id] = [];
        }
        scope.signals.push(id);
        i = j + 1;
        continue;
      }

      if (t === '$enddefinitions') {
        // skip $end then break into value-change pass
        while (i < tokens.length && tokens[i] !== '$end') i++;
        i++;
        break;
      }

      // Skip $comment / $version / $date / $dumpvars header / unknown
      if (t && t.startsWith('$')) {
        while (i < tokens.length && tokens[i] !== '$end') i++;
        i++;
        continue;
      }

      i++;
    }

    // --- Value-change pass: timestamps + scalar/vector changes. ---
    // Scalar:  0!         (id following the bit char)
    // Vector:  b1011 !    (b<bits> <space> id)
    // Real:    r1.23 !
    let curTime = 0;
    while (i < tokens.length) {
      const tok = tokens[i];
      if (!tok) { i++; continue; }

      if (tok[0] === '#') {
        // timestamp
        const t = parseInt(tok.slice(1), 10);
        if (!isNaN(t)) {
          curTime = t;
          if (tMin === null) tMin = t;
          if (t > tMax) tMax = t;
        }
        i++;
        continue;
      }

      if (tok[0] === 'b' || tok[0] === 'B') {
        // bus value: b<bits> <id>
        const bits = tok.slice(1);
        const id = tokens[i + 1];
        if (id && samples[id]) samples[id].push([curTime, bits]);
        i += 2;
        continue;
      }

      if (tok[0] === 'r' || tok[0] === 'R') {
        // real value: r<number> <id>
        const val = tok.slice(1);
        const id = tokens[i + 1];
        if (id && samples[id]) samples[id].push([curTime, val]);
        i += 2;
        continue;
      }

      // scalar: first char is value, rest is id
      const v = tok[0];
      if (v === '0' || v === '1' || v === 'x' || v === 'X' ||
          v === 'z' || v === 'Z') {
        const id = tok.slice(1);
        if (id && samples[id]) samples[id].push([curTime, v.toLowerCase()]);
      }
      // ignore $dumpall / $dumpoff blocks — they'll re-loop here as
      // scalar/vector and we'll just collect the values.
      i++;
    }

    return {
      signals,
      samples,
      timeRange: [tMin || 0, tMax],
      scopes: root,
      timescale,
    };
  }

  window.parseVCD = parseVCD;
})();
