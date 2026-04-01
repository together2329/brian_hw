"""
/skills command handler — separated from main.py for clarity.

Public API:
    handle_skills_command(skill_arg, load_active_skills_fn) -> bool
        Returns True if the command was handled (caller should `continue`).
"""

from lib.display import Color


def handle_skills_command(skill_arg: str, load_fn) -> bool:
    """
    Process a /skills sub-command.

    Args:
        skill_arg: everything after '/skills ' (stripped), or '' for bare /skills
        load_fn:   main.py's load_active_skills function (state stored as attributes)

    Returns:
        True — command handled, caller should continue the loop
    """
    try:
        from core.skill_system import get_skill_registry
        registry = get_skill_registry()
        all_skills = registry.get_skills_by_priority()
        skill_names = [s.name for s in all_skills]

        forced = getattr(load_fn, 'forced_skills', set())
        disabled = getattr(load_fn, 'disabled_skills', set())
        auto_active = getattr(load_fn, 'active_skills', [])

        def _resolve(token: str):
            if token.isdigit():
                idx = int(token) - 1
                return skill_names[idx] if 0 <= idx < len(skill_names) else None
            matches = [n for n in skill_names if token.lower() in n.lower()]
            return matches[0] if len(matches) == 1 else (token if token in skill_names else None)

        def _print_list():
            print(Color.info("\n=== Skills ==="))
            for i, skill in enumerate(all_skills, 1):
                n = skill.name
                if n in forced:
                    status = "\033[32m[ACTIVE]\033[0m"
                elif n in disabled:
                    status = "\033[31m[off]\033[0m   "
                elif n in auto_active:
                    status = "\033[36m[auto]\033[0m  "
                else:
                    status = "\033[2m[off]\033[0m   "
                desc = (skill.description or "")[:60]
                print(f"  {i:2}  {Color.BOLD}{n:<26}{Color.RESET} {status}  \033[2m{desc[:55]}\033[0m")
            print(Color.system(
                "\n  /skills a <name|#>   activate"
                "  /skills d <name|#>   deactivate"
                "\n  /skills all          activate all"
                "  /skills clear        clear all\n"
            ))

        def _ensure_attrs():
            if not hasattr(load_fn, 'forced_skills'):
                load_fn.forced_skills = set()
            if not hasattr(load_fn, 'disabled_skills'):
                load_fn.disabled_skills = set()

        # ── Dispatch ──────────────────────────────────────────────────────────

        if skill_arg == "":
            _print_list()

        elif skill_arg == "clear":
            load_fn.forced_skills = set()
            load_fn.disabled_skills = set()
            load_fn._active_skill = None
            load_fn._cached_key = ""
            load_fn._cached_skill = None
            print(Color.success("✅ All skill overrides cleared (back to auto-detection)"))

        elif skill_arg == "all":
            _ensure_attrs()
            load_fn.forced_skills = set(skill_names)
            load_fn.disabled_skills = set()
            print(Color.success(f"✅ All {len(skill_names)} skills activated"))

        elif skill_arg.startswith(("a ", "add ")):
            token = skill_arg.split(" ", 1)[1].strip()
            resolved = _resolve(token)
            if not resolved:
                print(Color.error(f"❌ Skill not found: '{token}'"))
                _print_list()
                return True
            _ensure_attrs()
            load_fn.forced_skills.add(resolved)
            load_fn.disabled_skills.discard(resolved)
            print(Color.success(f"✅ Skill '{resolved}' activated"))

        elif skill_arg.startswith(("d ", "del ", "disable ")):
            token = skill_arg.split(" ", 1)[1].strip()
            resolved = _resolve(token)
            if not resolved:
                print(Color.error(f"❌ Skill not found: '{token}'"))
                _print_list()
                return True
            _ensure_attrs()
            load_fn.forced_skills.discard(resolved)
            load_fn.disabled_skills.add(resolved)
            load_fn._active_skill = None
            load_fn._cached_key = ""
            print(Color.warning(f"❌ Skill '{resolved}' deactivated"))

        else:
            # Bare name/index → activate directly
            resolved = _resolve(skill_arg)
            if resolved:
                _ensure_attrs()
                load_fn.forced_skills.add(resolved)
                load_fn.disabled_skills.discard(resolved)
                print(Color.success(f"✅ Skill '{resolved}' activated"))
            else:
                _print_list()

    except ImportError:
        print(Color.error("❌ Skill system not available"))
    except Exception as e:
        print(Color.error(f"❌ /skills error: {e}"))

    return True
