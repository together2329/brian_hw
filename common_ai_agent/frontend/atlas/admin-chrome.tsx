// admin-chrome.tsx — TypeScript migration of the AdminPage tab-row + filter-bar
// chrome, extracted verbatim from admin.jsx (strangler-fig split, sub-1000).
//
// Presentational: the parent (admin.tsx) owns `activeTab`/`filters` state and
// the derived counts/options, and passes them down. JSX is identical to the
// original tab-row and filter-bar blocks; styles come from admin-styles.
//
// Cross-file: owns no window globals. Consumes only the typed props below.
import {
  tabRowStyle, tabStyle, filterBarStyle, filterLabelStyle, selectStyle,
} from './admin-styles';
import type { AdminFilters } from './admin-helpers';

export interface AdminTabCounts {
  users: number;
  ips: number;
  sessions: number;
  workflowStages: number;
  usage: number;
  costContexts: number;
  todoUsage: number;
  todoFlow: number;
  sessionFlowNeedsAttention: number;
  traceEvents: number;
  toolUsage: number;
  rtlRunHistory: number;
  artifactVersions: number;
  runArtifactSets: number;
  interventions: number;
  inputHistory: number;
  memoryRules: number;
  feedbackOpen: number;
  feedbackTotal: number;
}

export interface AdminFilterOptions {
  ips: string[];
  workspaces: string[];
  workflows: string[];
  users: string[];
}

export interface AdminTabRowProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  counts: AdminTabCounts;
}

export function AdminTabRow({ activeTab, setActiveTab, counts }: AdminTabRowProps) {
  return (
    <div style={tabRowStyle}>
      <button style={tabStyle(activeTab === 'overview')} onClick={() => setActiveTab('overview')}>
        Overview
      </button>
      <button style={tabStyle(activeTab === 'users')} onClick={() => setActiveTab('users')}>
        Users ({counts.users})
      </button>
      <button style={tabStyle(activeTab === 'ips')} onClick={() => setActiveTab('ips')}>
        IPs ({counts.ips})
      </button>
      <button style={tabStyle(activeTab === 'sessions')} onClick={() => setActiveTab('sessions')}>
        Sessions ({counts.sessions})
      </button>
      <button style={tabStyle(activeTab === 'stages')} onClick={() => setActiveTab('stages')}>
        Stages ({counts.workflowStages})
      </button>
      <button style={tabStyle(activeTab === 'usage')} onClick={() => setActiveTab('usage')}>
        Usage ({counts.usage})
      </button>
      <button style={tabStyle(activeTab === 'costs')} onClick={() => setActiveTab('costs')}>
        Costs ({counts.costContexts})
      </button>
      <button style={tabStyle(activeTab === 'todos')} onClick={() => setActiveTab('todos')}>
        Todos ({counts.todoUsage})
      </button>
      <button style={tabStyle(activeTab === 'flow')} onClick={() => setActiveTab('flow')}>
        Flow ({counts.todoFlow})
      </button>
      <button style={tabStyle(activeTab === 'session-flow')} onClick={() => setActiveTab('session-flow')}>
        Session Flow ({counts.sessionFlowNeedsAttention})
      </button>
      <button style={tabStyle(activeTab === 'trace')} onClick={() => setActiveTab('trace')}>
        Trace ({counts.traceEvents})
      </button>
      <button style={tabStyle(activeTab === 'tools')} onClick={() => setActiveTab('tools')}>
        Tools ({counts.toolUsage})
      </button>
      <button style={tabStyle(activeTab === 'rtl')} onClick={() => setActiveTab('rtl')}>
        RTL Runs ({counts.rtlRunHistory})
      </button>
      <button style={tabStyle(activeTab === 'versions')} onClick={() => setActiveTab('versions')}>
        Versions ({counts.artifactVersions})
      </button>
      <button style={tabStyle(activeTab === 'run-sets')} onClick={() => setActiveTab('run-sets')}>
        Run Sets ({counts.runArtifactSets})
      </button>
      <button style={tabStyle(activeTab === 'human')} onClick={() => setActiveTab('human')}>
        Human ({counts.interventions})
      </button>
      <button style={tabStyle(activeTab === 'inputs')} onClick={() => setActiveTab('inputs')}>
        Inputs ({counts.inputHistory})
      </button>
      <button style={tabStyle(activeTab === 'memory')} onClick={() => setActiveTab('memory')}>
        Memory ({counts.memoryRules})
      </button>
      <button style={tabStyle(activeTab === 'runtime')} onClick={() => setActiveTab('runtime')}>
        Runtime
      </button>
      <button style={tabStyle(activeTab === 'feedback')} onClick={() => setActiveTab('feedback')}>
        Feedback ({counts.feedbackOpen}/{counts.feedbackTotal})
      </button>
      <button style={tabStyle(activeTab === 'admin-chat')} onClick={() => setActiveTab('admin-chat')}>
        Admin Chat
      </button>
      <button style={tabStyle(activeTab === 'raw-db')} onClick={() => setActiveTab('raw-db')}>
        Raw DB
      </button>
    </div>
  );
}

export interface AdminFilterBarProps {
  filters: AdminFilters;
  setFilter: (key: keyof AdminFilters, value: string) => void;
  clearFilters: () => void;
  filterOptions: AdminFilterOptions;
}

export function AdminFilterBar({ filters, setFilter, clearFilters, filterOptions }: AdminFilterBarProps) {
  return (
    <div style={filterBarStyle}>
      <label style={filterLabelStyle} htmlFor="admin-filter-range">
        Range
        <select
          id="admin-filter-range"
          aria-label="Range"
          style={selectStyle}
          value={filters.range}
          onChange={(e) => setFilter('range', e.target.value)}
        >
          <option value="24h">Last 24h</option>
          <option value="7d">Last 7d</option>
          <option value="30d">Last 30d</option>
          <option value="all">All time</option>
        </select>
      </label>
      <label style={filterLabelStyle} htmlFor="admin-filter-ip">
        IP
        <select
          id="admin-filter-ip"
          aria-label="IP"
          style={selectStyle}
          value={filters.ip}
          onChange={(e) => setFilter('ip', e.target.value)}
        >
          <option value="">All IPs</option>
          {filterOptions.ips.map((value) => <option key={value} value={value}>{value}</option>)}
        </select>
      </label>
      <label style={filterLabelStyle} htmlFor="admin-filter-workspace">
        Workspace
        <select
          id="admin-filter-workspace"
          aria-label="Workspace"
          style={selectStyle}
          value={filters.workspace}
          onChange={(e) => setFilter('workspace', e.target.value)}
        >
          <option value="">All workspaces</option>
          {filterOptions.workspaces.map((value) => <option key={value} value={value}>{value}</option>)}
        </select>
      </label>
      <label style={filterLabelStyle} htmlFor="admin-filter-workflow">
        Workflow
        <select
          id="admin-filter-workflow"
          aria-label="Workflow"
          style={selectStyle}
          value={filters.workflow}
          onChange={(e) => setFilter('workflow', e.target.value)}
        >
          <option value="">All workflows</option>
          {filterOptions.workflows.map((value) => <option key={value} value={value}>{value}</option>)}
        </select>
      </label>
      <label style={filterLabelStyle} htmlFor="admin-filter-user">
        User
        <select
          id="admin-filter-user"
          aria-label="User"
          style={selectStyle}
          value={filters.user}
          onChange={(e) => setFilter('user', e.target.value)}
        >
          <option value="">All users</option>
          {filterOptions.users.map((value) => <option key={value} value={value}>{value}</option>)}
        </select>
      </label>
      <label style={filterLabelStyle}>
        Reset
        <button type="button" style={{ ...selectStyle, cursor: 'pointer', color: '#f0c674' }} onClick={clearFilters}>
          Clear filters
        </button>
      </label>
    </div>
  );
}
