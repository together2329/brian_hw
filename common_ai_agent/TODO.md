# Common AI Agent - Project TODO

## Overview
Common AI Agent is an intelligent coding agent with ReAct loop architecture, supporting file operations, Git integration, sub-agents, Verilog analysis, and PCIe/UCIe/NVMe spec navigation.

---

## ✅ Recently Completed (from current_plan.md)

| # | Task | Status |
|---|------|--------|
| 1 | Update TodoItem dataclass with Priority, Tags, Estimate, DueDate | ✅ Done |
| 2 | Add Dependency management (prereqs) to TodoItem | ✅ Done |
| 3 | Implement UndoStack in TodoTracker | ✅ Done |
| 4 | Add time logging (start/stop) | ✅ Done |
| 5 | Create integration helper for Graph Lite | ✅ Done |
| 6 | Add report generator methods | ✅ Done |

---

## 📋 TODO: Feature Enhancements

### High Priority
- [ ] **Error Recovery System** - Improve error handling in ReAct loop
- [ ] **Context Compression Testing** - Verify compression doesn't lose critical context
- [ ] **Session Recovery** - Test rollback on consecutive errors

### Medium Priority  
- [ ] **Verilog Tools Polish** - Enhance Verilog analysis capabilities
- [ ] **Memory System Integration** - Test memory persistence across sessions
- [ ] **Graph Knowledge System** - Verify knowledge extraction and linking
- [ ] **RAG Auto-Indexing** - Test automatic file indexing on startup

### Low Priority
- [ ] **UI/UX Improvements** - Textual UI refinements
- [ ] **Documentation** - Update README and inline docs
- [ ] **Performance Profiling** - Identify bottlenecks

---

## 🔧 TODO: Technical Debt

- [ ] Add unit tests for `lib/todo_tracker.py` new features
- [ ] Refactor large functions in `core/` modules
- [ ] Add type hints to all public functions
- [ ] Remove deprecated code paths
- [ ] Consolidate configuration loading

---

## 📊 TODO: Testing

- [ ] Run full test suite: `pytest tests/ -v`
- [ ] Add integration tests for todo workflow
- [ ] Test sub-agent delegation
- [ ] Verify memory system CRUD operations
- [ ] Test graph knowledge extraction

---

## 📝 Notes

### Key Directories
- `core/` - Core agent logic (ReAct loop, tool dispatch, etc.)
- `lib/` - Utility libraries (display, memory, todo_tracker)
- `src/` - Entry points and configuration
- `tests/` - Test suite
- `rules/` - Project-specific rules (loaded dynamically)
- `skills/` - Domain-specific skill modules

### Configuration
- `.env` / `.config` - Environment variables
- `config.py` - All configurable options with defaults

---

## Quick Commands

```bash
# Run agent
python -m src.main

# Run tests
pytest tests/ -v

# Run specific test
pytest tests/test_todo_workflow.py -v

# Check coverage
pytest --cov=core --cov=lib tests/
```

---

*Last updated: $(date)*
