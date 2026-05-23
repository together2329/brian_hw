"""
mutmut configuration note — mutmut 3.x

mutmut 3.x reads configuration from setup.cfg [mutmut] section (NOT this file).
This file exists for documentation only.

Effective config is in setup.cfg:
  [mutmut]
  paths_to_mutate = core/atlas_db.py
                    src/atlas_api_jobs.py
  tests_dir = tests/test_atlas_db_orchestrator.py
              tests/test_orchestrator_workers_route.py
              tests/test_orchestrator_dispatch_seed.py
              tests/test_orchestrator_chat_ip_extraction.py
              tests/test_chat_full_multiuser_system.py

To run mutation testing:
  ./scripts/run_tests.sh mutation

To run a scoped baseline (one hardened function, ~30 mutations):
  /Users/brian/Library/Python/3.9/bin/mutmut run \
      'src/atlas_api_jobs.py:_rehydrate_jobs_from_db*'

mutmut 3.x always uses pytest directly (no shell runner).
Install: pip3 install mutmut
"""
