# Platform Support

The hardware-IP workflows under this directory (`syn`, `sta`, `dft`, `pnr`,
`sta-post`, plus the existing `lint`, `sim`, `rtl-gen`, `tb-gen`, `ssot-gen`)
shell out to open-source EDA tools. Tool support varies by host OS.

## Support matrix

| Tool | Linux (Ubuntu/Debian/RHEL) | macOS (Apple Silicon / Intel) | Windows native | WSL2 | Docker |
|---|---|---|---|---|---|
| `yosys` (used by `/syn`) | ✅ apt | ✅ brew | ⚠️ MSYS2/OSS-CAD-Suite | ✅ | ✅ |
| `verilator` / `iverilog` (`/lint`, `/sim`) | ✅ | ✅ | ⚠️ partial | ✅ | ✅ |
| `sta` — OpenSTA (`/sta`, `/sta-post`) | ✅ | ✅ source build | ❌ no official support | ✅ | ✅ |
| `openroad` (`/dft`, `/pnr-*`) | ✅ first-class | ⚠️ source build, dep-heavy | ❌ **CMake fails to configure** | ✅ | ✅ |
| sky130 PDK files (LEF, Liberty, tracks, RCX rules) | ✅ | ✅ | ✅ (just data files) | ✅ | ✅ |
| Workflow shell scripts (`workflow/*/scripts/*.sh`) | ✅ POSIX | ✅ POSIX | ❌ needs bash | ✅ | ✅ |

**Bottom line**: native Windows is not viable for the full chain.
Use **WSL2** or **Docker**.

## Recommended setups

### Linux (primary target)

This is the path of least resistance. Both OpenROAD and OpenSTA are
first-class supported on Ubuntu 22.04+.

```bash
# Tools
sudo apt update
sudo apt install -y yosys verilator iverilog \
                    cmake bison flex swig \
                    libboost-all-dev libreadline-dev libtcl-dev

# OpenROAD (with all transitive deps via the official installer)
git clone --recursive https://github.com/The-OpenROAD-Project/OpenROAD.git
cd OpenROAD
sudo ./etc/DependencyInstaller.sh -all
./etc/Build.sh -threads=$(nproc)
sudo cp build/bin/openroad /usr/local/bin/
```

No keg-only / no manual `OpenMP_ROOT` games. CMake configure passes on the
first try.

### macOS (Apple Silicon supported, this repo's reference)

The full chain has been built and tested on macOS 15 (Sequoia, M-series).
Several deps need explicit cmake hints because Homebrew installs them
keg-only.

```bash
# Brew packages
brew install cmake swig boost eigen pcre tcl-tk@8 libomp spdlog or-tools \
             qt@5 yaml-cpp googletest icu4c@78 zstd bzip2 zlib gettext \
             readline bison flex pkg-config
brew install The-OpenROAD-Project/lemon-graph/lemon-graph

# OpenSTA (CUDD + OpenSTA — separate repo, install to ~/.local)
# (see HW_IP_textual session notes; results in /Users/<you>/.local/bin/sta)

# OpenROAD — direct cmake invocation with all hints (Build.sh's auto-detection
# is fragile on macOS). Reference invocation: see git log for the commit that
# added pdk/sky130/.
```

Reference build that worked on Apple Silicon:
- `OpenMP_ROOT=/opt/homebrew/opt/libomp`
- `Qt5_DIR=/opt/homebrew/opt/qt@5/lib/cmake/Qt5`
- `BISON_EXECUTABLE=/opt/homebrew/opt/bison/bin/bison` (system bison 2.3 doesn't have `%code`)
- `-DCMAKE_CXX_FLAGS="-DBOOST_STACKTRACE_GNU_SOURCE_NOT_REQUIRED"`
- All keg-only `*/lib` paths in `LDFLAGS` + `-Wl,-rpath,...`
- `-DCUDD_LIB=$HOME/.local/lib/libcudd.dylib`
- Tests: `-DENABLE_TESTS=OFF -DBUILD_TESTS=OFF`
- GUI: `-DBUILD_GUI=OFF` (avoids broken Qt5CoreConfigExtras.cmake)

Total build time: ~15 min on M2 8-core (was ~25 min during dependency
debugging, dep resolution dominated).

### Windows — WSL2 (recommended)

Native Windows is not supported. OpenROAD's CMake refuses to configure on
MSVC, and OpenSTA's CUDD dep has long-standing Windows issues.

Use WSL2 with Ubuntu 22.04:

```powershell
# In Windows PowerShell (admin):
wsl --install -d Ubuntu-22.04
```

Then inside the Ubuntu shell, follow the **Linux** setup above. The repo
checks out and the workflows run unchanged — they were authored as POSIX
shell + Python and exercise no Windows-specific paths.

WSL2 quirks to be aware of:
- File I/O across the `/mnt/c/` boundary is slow. Clone the repo inside
  `~/` (i.e. `\\wsl$\Ubuntu\home\<user>`) for fast yosys / openroad runs.
- GUI tools (OpenROAD's `gui` mode, KLayout) need WSLg (Windows 11) or an
  X server (Windows 10). Not needed for our workflows — `/pnr-*` runs
  with `BUILD_GUI=OFF`.

### Windows — Docker (alternative)

If WSL2 isn't an option, use the official OpenROAD Docker image:

```powershell
docker pull openroad/orfs
docker run -it -v "${PWD}:/work" openroad/orfs bash
# inside the container:
cd /work
export SKY130_LIB=/work/pdk/sky130/lib/sky130_fd_sc_hd__ss_100C_1v40.lib
# ...
bash workflow/syn/scripts/auto_syn.sh counter
```

The image bundles yosys + OpenSTA + OpenROAD + sky130hd PDK, so steps that
download `make_tracks.tcl`, `rcx_patterns.rules`, etc. (under
`pdk/sky130/`) can use the image's copies under
`/OpenROAD-flow-scripts/flow/platforms/sky130hd/` instead of fetching from
GitHub.

Drawback: every workflow `run_command` would have to wrap with
`docker exec`. We don't currently provide that wrapper — it'd be a small
shell helper but is out of scope for v1.

## What works on which platform

| Workflow | Linux | macOS | WSL2 | Docker | Tools required |
|---|---|---|---|---|---|
| `/ssot-gen`, `/rtl-gen`, `/tb-gen` | ✅ | ✅ | ✅ | ✅ | LLM only |
| `/lint` | ✅ | ✅ | ✅ | ✅ | verilator |
| `/sim` | ✅ | ✅ | ✅ | ✅ | iverilog or verilator |
| `/syn` | ✅ | ✅ | ✅ | ✅ | yosys + sky130 Liberty |
| `/sta` | ✅ | ✅ | ✅ | ✅ | OpenSTA + sky130 Liberty |
| `/dft` (passthrough) | ✅ | ✅ | ✅ | ✅ | none (just file copy) |
| `/dft` (scan-insert) | ✅ | ✅ | ✅ | ✅ | OpenROAD `insert_dft` pass |
| `/pnr-fp` → `/pnr-route` | ✅ | ✅ | ✅ | ✅ | OpenROAD + LEF + RCX rules |
| `/sta-post` | ✅ | ✅ | ✅ | ✅ | OpenSTA + SPEF |

The `dft` / `pnr-*` workflows that need OpenROAD will fail-fast with
`[<STAGE> TOOL MISSING] openroad not on PATH` (exit 3) on hosts where the
binary is absent — including native Windows, where the message is the
expected and correct stop signal pointing the user to WSL2/Docker.

## Tested combinations

| Host | Tools all present | counter IP through `/sta-post` |
|---|---|---|
| macOS 15 (M2, this repo) | ✅ yosys, OpenSTA, OpenROAD | ✅ PASS, setup_wns +5.43 ns post-route |
| Ubuntu 22.04 (CI / your laptop) | expected ✅ | expected ✅ |
| Windows 11 native | ❌ OpenROAD CMake fails | ❌ |
| WSL2 + Ubuntu 22.04 | expected ✅ | expected ✅ |

If you exercise the chain on a new host, please update this table.
