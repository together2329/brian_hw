"""
Agent Configuration System (OpenCode-Inspired)

OpenCode의 장점을 도입:
1. 설정 기반 에이전트 정의 (JSONC/YAML)
2. 세밀한 권한 시스템 (wildcard 패턴)
3. 에이전트별 모델/파라미터 설정
4. 동적 에이전트 생성 (런타임)
"""

import os
import re
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Union
from enum import Enum


# ============================================================
# Permission Types
# ============================================================

class PermissionLevel(Enum):
    """권한 레벨"""
    ALLOW = "allow"   # 자동 허용
    ASK = "ask"       # 사용자 확인 필요
    DENY = "deny"     # 거부


@dataclass
class ToolPermissions:
    """도구 권한 설정"""
    # 파일 편집 권한
    edit: PermissionLevel = PermissionLevel.ALLOW

    # Bash 명령어 권한 (wildcard 패턴 지원)
    # 예: {"git diff*": "allow", "rm -rf*": "deny", "*": "ask"}
    bash: Dict[str, PermissionLevel] = field(default_factory=dict)

    # 스킬 권한 (스킬 이름별)
    skill: Dict[str, PermissionLevel] = field(default_factory=dict)

    # 웹 접근 권한
    webfetch: PermissionLevel = PermissionLevel.ALLOW

    # 외부 디렉토리 접근 권한
    external_directory: PermissionLevel = PermissionLevel.ASK

    # 무한 루프 방지 (doom loop)
    doom_loop: PermissionLevel = PermissionLevel.ASK

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ToolPermissions':
        """딕셔너리에서 ToolPermissions 생성"""
        permissions = cls()

        if 'edit' in data:
            permissions.edit = PermissionLevel(data['edit'])

        if 'bash' in data:
            if isinstance(data['bash'], str):
                # 단일 문자열: 모든 bash에 적용
                permissions.bash = {"*": PermissionLevel(data['bash'])}
            else:
                permissions.bash = {
                    k: PermissionLevel(v) for k, v in data['bash'].items()
                }

        if 'skill' in data:
            if isinstance(data['skill'], str):
                permissions.skill = {"*": PermissionLevel(data['skill'])}
            else:
                permissions.skill = {
                    k: PermissionLevel(v) for k, v in data['skill'].items()
                }

        if 'webfetch' in data:
            permissions.webfetch = PermissionLevel(data['webfetch'])

        if 'external_directory' in data:
            permissions.external_directory = PermissionLevel(data['external_directory'])

        if 'doom_loop' in data:
            permissions.doom_loop = PermissionLevel(data['doom_loop'])

        return permissions

    def check_bash_permission(self, command: str) -> PermissionLevel:
        """
        Bash 명령어 권한 확인 (wildcard 패턴 매칭)

        더 specific한 패턴이 우선:
        - "git diff*" > "git *" > "*"
        """
        # 가장 긴 매치 찾기 (더 specific)
        best_match = None
        best_pattern_len = -1

        for pattern, level in self.bash.items():
            if self._wildcard_match(pattern, command):
                # 패턴 길이 (*, ? 제외)로 우선순위 결정
                pattern_specificity = len(pattern.replace('*', '').replace('?', ''))
                if pattern_specificity > best_pattern_len:
                    best_pattern_len = pattern_specificity
                    best_match = level

        return best_match if best_match else PermissionLevel.ALLOW

    def _wildcard_match(self, pattern: str, text: str) -> bool:
        """Wildcard 패턴 매칭 (* = 모든 문자, ? = 단일 문자)"""
        # 정규식으로 변환
        regex_pattern = pattern.replace('*', '.*').replace('?', '.')
        regex_pattern = f"^{regex_pattern}$"
        return bool(re.match(regex_pattern, text, re.IGNORECASE))


# ============================================================
# Agent Configuration
# ============================================================

@dataclass
class AgentModelConfig:
    """에이전트별 모델 설정"""
    provider_id: str = ""  # anthropic, openai, openrouter, etc.
    model_id: str = ""     # claude-3-opus, gpt-4, etc.

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentModelConfig':
        if isinstance(data, str):
            # "provider/model" 형식 파싱
            parts = data.split('/', 1)
            return cls(
                provider_id=parts[0] if len(parts) > 1 else "",
                model_id=parts[-1]
            )
        return cls(
            provider_id=data.get('provider_id', data.get('providerID', '')),
            model_id=data.get('model_id', data.get('modelID', ''))
        )


@dataclass
class AgentConfig:
    """에이전트 설정"""
    name: str
    description: str = ""

    # 모드: primary (메인), subagent (서브), all (둘 다)
    mode: str = "all"

    # 네이티브 에이전트 여부 (코드로 정의된 기본 에이전트)
    native: bool = False

    # 숨김 에이전트 (내부용)
    hidden: bool = False

    # 기본 에이전트 여부
    default: bool = False

    # 모델 설정 (None = 기본 모델 사용)
    model: Optional[AgentModelConfig] = None

    # LLM 파라미터
    temperature: Optional[float] = None
    top_p: Optional[float] = None

    # 커스텀 시스템 프롬프트
    prompt: Optional[str] = None

    # 허용/비활성화 도구 (True = 허용, False = 비활성화)
    tools: Dict[str, bool] = field(default_factory=dict)

    # 허용된 도구 목록 (ALLOWED_TOOLS 스타일, 레거시 호환)
    allowed_tools: Set[str] = field(default_factory=set)

    # 권한 설정
    permission: ToolPermissions = field(default_factory=ToolPermissions)

    # 추가 옵션
    options: Dict[str, Any] = field(default_factory=dict)

    # 최대 스텝 수
    max_steps: Optional[int] = None

    # UI 색상
    color: Optional[str] = None

    # 비활성화 여부
    disable: bool = False

    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any]) -> 'AgentConfig':
        """딕셔너리에서 AgentConfig 생성"""
        config = cls(name=name)

        config.description = data.get('description', '')
        config.mode = data.get('mode', 'all')
        config.native = data.get('native', False)
        config.hidden = data.get('hidden', False)
        config.default = data.get('default', False)

        # 모델 설정
        if 'model' in data:
            config.model = AgentModelConfig.from_dict(data['model'])

        # LLM 파라미터
        config.temperature = data.get('temperature')
        config.top_p = data.get('top_p', data.get('topP'))

        # 프롬프트
        config.prompt = data.get('prompt')

        # 도구 설정
        if 'tools' in data:
            config.tools = data['tools']

        # 허용 도구 (레거시)
        if 'allowed_tools' in data:
            config.allowed_tools = set(data['allowed_tools'])

        # 권한
        if 'permission' in data:
            config.permission = ToolPermissions.from_dict(data['permission'])

        # 추가 옵션
        for key in data:
            if key not in ['name', 'description', 'mode', 'native', 'hidden',
                          'default', 'model', 'temperature', 'top_p', 'topP',
                          'prompt', 'tools', 'allowed_tools', 'permission',
                          'max_steps', 'maxSteps', 'color', 'disable']:
                config.options[key] = data[key]

        config.max_steps = data.get('max_steps', data.get('maxSteps'))
        config.color = data.get('color')
        config.disable = data.get('disable', False)

        return config

    def get_allowed_tools(self) -> Set[str]:
        """허용된 도구 목록 반환 (tools dict + allowed_tools set 병합)"""
        allowed = set(self.allowed_tools)

        for tool, enabled in self.tools.items():
            if enabled:
                if tool == "*":
                    # 모든 도구 허용
                    return {"*"}
                allowed.add(tool)
            elif tool in allowed:
                allowed.remove(tool)

        return allowed


# ============================================================
# Agent Registry (설정 기반 에이전트 관리)
# ============================================================

class AgentRegistry:
    """
    에이전트 레지스트리 - 설정 파일에서 에이전트 로드 및 관리

    설정 파일 우선순위:
    1. 프로젝트 로컬: .brian_coder/agents.jsonc
    2. 사용자 글로벌: ~/.brian_coder/agents.jsonc
    3. 기본 내장 에이전트
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._agents: Dict[str, AgentConfig] = {}
        self._config_paths: List[Path] = []
        self._initialized = True

        # 기본 에이전트 등록
        self._register_native_agents()

        # 설정 파일에서 로드
        self._load_configs()

    def _register_native_agents(self):
        """네이티브 에이전트 등록 (기본 제공)"""
        # 기본 권한 설정
        default_permission = ToolPermissions(
            edit=PermissionLevel.ALLOW,
            bash={"*": PermissionLevel.ALLOW},
            skill={"*": PermissionLevel.ALLOW},
            webfetch=PermissionLevel.ALLOW,
            doom_loop=PermissionLevel.ASK,
            external_directory=PermissionLevel.ASK
        )

        # Plan 에이전트 권한 (읽기 전용)
        plan_permission = ToolPermissions(
            edit=PermissionLevel.DENY,
            bash={
                "git diff*": PermissionLevel.ALLOW,
                "git log*": PermissionLevel.ALLOW,
                "git show*": PermissionLevel.ALLOW,
                "git status*": PermissionLevel.ALLOW,
                "git branch": PermissionLevel.ALLOW,
                "grep*": PermissionLevel.ALLOW,
                "ls*": PermissionLevel.ALLOW,
                "cat*": PermissionLevel.ALLOW,
                "head*": PermissionLevel.ALLOW,
                "tail*": PermissionLevel.ALLOW,
                "find*": PermissionLevel.ALLOW,
                "tree*": PermissionLevel.ALLOW,
                "rg*": PermissionLevel.ALLOW,
                "pwd*": PermissionLevel.ALLOW,
                "*": PermissionLevel.ASK
            },
            webfetch=PermissionLevel.ALLOW
        )

        # Explore 에이전트
        self._agents["explore"] = AgentConfig(
            name="explore",
            description="Fast agent for codebase exploration. Read-only, finds files and patterns.",
            mode="subagent",
            native=True,
            allowed_tools={
                "read_file", "read_lines", "grep_file", "list_dir",
                "find_files", "rag_search", "rag_explore", "git_status", "git_diff"
            },
            permission=plan_permission
        )

        # Plan 에이전트
        self._agents["plan"] = AgentConfig(
            name="plan",
            description="Planning agent for complex task analysis. Creates execution plans.",
            mode="subagent",
            native=True,
            allowed_tools={
                "read_file", "read_lines", "grep_file", "list_dir",
                "find_files", "rag_search", "create_plan", "get_plan"
            },
            permission=plan_permission
        )

        # Execute 에이전트
        self._agents["execute"] = AgentConfig(
            name="execute",
            description="Execution agent for implementing plans. Full write access.",
            mode="subagent",
            native=True,
            allowed_tools={
                "read_file", "read_lines", "write_file", "replace_in_file",
                "replace_lines", "run_command", "grep_file", "list_dir",
                "find_files", "rag_search", "mark_step_done"
            },
            permission=default_permission
        )

        # Review 에이전트
        self._agents["review"] = AgentConfig(
            name="review",
            description="Code review agent for quality checks and suggestions.",
            mode="subagent",
            native=True,
            allowed_tools={
                "read_file", "read_lines", "grep_file", "list_dir",
                "find_files", "rag_search", "git_diff"
            },
            permission=plan_permission
        )

        # Build 에이전트 (메인 에이전트)
        self._agents["build"] = AgentConfig(
            name="build",
            description="Main agent with full access for development tasks.",
            mode="primary",
            native=True,
            default=True,
            tools={"*": True},  # 모든 도구 허용
            permission=default_permission
        )

    def _load_configs(self):
        """설정 파일에서 에이전트 로드"""
        config_locations = [
            Path.cwd() / '.brian_coder' / 'agents.jsonc',
            Path.cwd() / '.brian_coder' / 'agents.json',
            Path.home() / '.brian_coder' / 'agents.jsonc',
            Path.home() / '.brian_coder' / 'agents.json',
        ]

        for config_path in config_locations:
            if config_path.exists():
                self._config_paths.append(config_path)
                self._load_config_file(config_path)

    def _load_config_file(self, path: Path):
        """단일 설정 파일 로드"""
        try:
            content = path.read_text(encoding='utf-8')

            # JSONC (주석 제거)
            content = self._strip_jsonc_comments(content)

            data = json.loads(content)

            if 'agents' in data:
                agents_data = data['agents']
            else:
                agents_data = data

            for name, agent_data in agents_data.items():
                if isinstance(agent_data, dict):
                    if agent_data.get('disable', False):
                        # 비활성화된 에이전트 제거
                        if name in self._agents:
                            del self._agents[name]
                        continue

                    # 기존 네이티브 에이전트가 있으면 병합
                    if name in self._agents and self._agents[name].native:
                        self._merge_agent_config(name, agent_data)
                    else:
                        self._agents[name] = AgentConfig.from_dict(name, agent_data)

            print(f"[AgentRegistry] Loaded {len(agents_data)} agents from {path}")

        except Exception as e:
            print(f"[AgentRegistry] Failed to load {path}: {e}")

    def _merge_agent_config(self, name: str, data: Dict[str, Any]):
        """기존 에이전트에 설정 병합"""
        agent = self._agents[name]

        # 오버라이드 가능 필드
        if 'model' in data:
            agent.model = AgentModelConfig.from_dict(data['model'])
        if 'temperature' in data:
            agent.temperature = data['temperature']
        if 'top_p' in data or 'topP' in data:
            agent.top_p = data.get('top_p', data.get('topP'))
        if 'prompt' in data:
            agent.prompt = data['prompt']
        if 'tools' in data:
            agent.tools.update(data['tools'])
        if 'permission' in data:
            # 권한 병합
            new_perm = ToolPermissions.from_dict(data['permission'])
            agent.permission.bash.update(new_perm.bash)
            agent.permission.skill.update(new_perm.skill)
            if 'edit' in data['permission']:
                agent.permission.edit = new_perm.edit
            if 'webfetch' in data['permission']:
                agent.permission.webfetch = new_perm.webfetch
        if 'max_steps' in data or 'maxSteps' in data:
            agent.max_steps = data.get('max_steps', data.get('maxSteps'))
        if 'color' in data:
            agent.color = data['color']
        if 'description' in data:
            agent.description = data['description']

    def _strip_jsonc_comments(self, content: str) -> str:
        """JSONC 주석 제거"""
        # 단일행 주석 제거 (// ...)
        content = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)
        # 다중행 주석 제거 (/* ... */)
        content = re.sub(r'/\*[\s\S]*?\*/', '', content)
        return content

    # ============================================================
    # Public API
    # ============================================================

    def get(self, name: str) -> Optional[AgentConfig]:
        """에이전트 설정 조회"""
        return self._agents.get(name)

    def list(self) -> List[AgentConfig]:
        """모든 에이전트 목록"""
        return list(self._agents.values())

    def list_visible(self) -> List[AgentConfig]:
        """표시 가능한 에이전트 목록 (hidden=False)"""
        return [a for a in self._agents.values() if not a.hidden]

    def list_primary(self) -> List[AgentConfig]:
        """Primary 모드 에이전트 목록"""
        return [a for a in self._agents.values()
                if a.mode in ('primary', 'all') and not a.hidden]

    def list_subagents(self) -> List[AgentConfig]:
        """Subagent 모드 에이전트 목록"""
        return [a for a in self._agents.values()
                if a.mode in ('subagent', 'all')]

    def get_default(self) -> Optional[AgentConfig]:
        """기본 에이전트 반환"""
        for agent in self._agents.values():
            if agent.default:
                return agent
        return self._agents.get('build')

    def register(self, config: AgentConfig):
        """에이전트 등록"""
        self._agents[config.name] = config

    def reload(self):
        """설정 리로드"""
        self._agents.clear()
        self._config_paths.clear()
        self._register_native_agents()
        self._load_configs()


# ============================================================
# Permission Checker
# ============================================================

class PermissionChecker:
    """
    권한 검사기 - OpenCode 스타일 세밀한 권한 체크
    """

    def __init__(self, agent_config: AgentConfig):
        self.config = agent_config
        self.permission = agent_config.permission

    def check_tool(self, tool_name: str) -> bool:
        """도구 사용 가능 여부"""
        allowed = self.config.get_allowed_tools()
        if "*" in allowed:
            return True
        return tool_name in allowed

    def check_edit(self, file_path: str) -> PermissionLevel:
        """파일 편집 권한"""
        return self.permission.edit

    def check_bash(self, command: str) -> PermissionLevel:
        """Bash 명령어 권한 (wildcard 매칭)"""
        return self.permission.check_bash_permission(command)

    def check_skill(self, skill_name: str) -> PermissionLevel:
        """스킬 사용 권한"""
        # Specific skill 먼저
        if skill_name in self.permission.skill:
            return self.permission.skill[skill_name]
        # 와일드카드
        if "*" in self.permission.skill:
            return self.permission.skill["*"]
        return PermissionLevel.ALLOW

    def check_webfetch(self, url: str) -> PermissionLevel:
        """웹 접근 권한"""
        return self.permission.webfetch

    def check_external_directory(self, path: str) -> PermissionLevel:
        """외부 디렉토리 접근 권한"""
        # 현재 작업 디렉토리 외부인지 확인
        try:
            cwd = Path.cwd().resolve()
            target = Path(path).resolve()

            if target.is_relative_to(cwd):
                return PermissionLevel.ALLOW
            return self.permission.external_directory
        except:
            return self.permission.external_directory


# ============================================================
# Singleton Accessor
# ============================================================

def get_agent_registry() -> AgentRegistry:
    """AgentRegistry 싱글톤 반환"""
    return AgentRegistry()


def get_agent_config(name: str) -> Optional[AgentConfig]:
    """에이전트 설정 조회"""
    return get_agent_registry().get(name)


def list_agents() -> List[AgentConfig]:
    """모든 에이전트 목록"""
    return get_agent_registry().list()
