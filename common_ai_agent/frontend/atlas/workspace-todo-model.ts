export const TODO_EDITOR_STATES = ['pending', 'in_progress', 'completed', 'approved', 'rejected'] as const;

export type TodoRecord = {
  readonly id?: string | number;
  readonly title?: string;
  readonly content?: string;
  readonly detail?: string;
  readonly criteria?: string | readonly string[];
  readonly state?: string;
  readonly status?: string;
  readonly priority?: string;
  readonly approvedReason?: string;
  readonly rejectionReason?: string;
  readonly notes?: readonly unknown[];
  readonly deps?: readonly unknown[];
  readonly section?: string;
  readonly command?: unknown;
  readonly onReject?: unknown;
  readonly onSuccess?: unknown;
  readonly onCondition?: readonly unknown[];
  readonly commandLogs?: readonly TodoCommandLog[];
};

export type TodoCommandLog = {
  readonly cmd?: unknown;
  readonly ok?: unknown;
  readonly tail?: unknown;
  readonly log_file?: unknown;
  readonly logFile?: unknown;
  readonly lines?: unknown;
  readonly elapsed?: unknown;
};

export type TodoSaveFields = {
  readonly content: string;
  readonly detail: string;
  readonly criteria: string;
  readonly state: string;
  readonly approved_reason: string;
  readonly rejection_reason: string;
};

export type TodoMutationApi = {
  readonly refreshTodos?: (options?: { readonly force?: boolean }) => unknown;
  readonly addTodo?: (fields: { readonly content: string; readonly detail: string; readonly criteria: string; readonly priority: string }) => Promise<unknown> | unknown;
  readonly updateTodo?: (index: number, fields: TodoSaveFields) => Promise<unknown> | unknown;
  readonly removeTodo?: (index: number) => Promise<unknown> | unknown;
  readonly clearTodos?: () => Promise<unknown> | unknown;
};

export const isTodoRecord = (value: unknown): value is TodoRecord => (
  !!value && typeof value === 'object'
);

export const todoId = (todo: TodoRecord, index: number): string => String(todo.id ?? `todo-${index + 1}`);

export const todoTitle = (todo: TodoRecord): string => {
  const title = String(todo.title ?? todo.content ?? '').trim();
  return title || '(untitled todo)';
};

export const todoState = (todo: TodoRecord): string => (
  String(todo.state ?? todo.status ?? 'pending').trim() || 'pending'
);

export const todoDetail = (todo: TodoRecord): string => String(todo.detail ?? '').trim();

export const todoCriteriaText = (criteria: TodoRecord['criteria']): string => (
  Array.isArray(criteria) ? criteria.map(line => String(line ?? '').trim()).filter(Boolean).join('\n') : String(criteria ?? '').trim()
);

export const todoCriteriaLines = (todo: TodoRecord): readonly string[] => (
  todoCriteriaText(todo.criteria).split(/\n+/).map(line => line.trim()).filter(Boolean)
);

export const todoNotes = (todo: TodoRecord): readonly string[] => (
  Array.isArray(todo.notes) ? todo.notes.map(note => String(note ?? '').trim()).filter(Boolean) : []
);

export const todoDeps = (todo: TodoRecord): readonly string[] => (
  Array.isArray(todo.deps) ? todo.deps.map(dep => String(dep ?? '').trim()).filter(Boolean) : []
);

export const todoCommandText = (todo: TodoRecord): string => {
  const command = todo.command;
  if (!command) return '';
  if (typeof command === 'string') return command.trim();
  const encoded = JSON.stringify(command);
  return typeof encoded === 'string' ? encoded : String(command);
};

export const todoTargetLabel = (value: unknown): string => {
  const target = Number(value);
  return Number.isInteger(target) && target > 0 ? `Task #${target}` : '';
};

export const todoCommandLogs = (todo: TodoRecord): readonly TodoCommandLog[] => (
  Array.isArray(todo.commandLogs) ? todo.commandLogs : []
);
