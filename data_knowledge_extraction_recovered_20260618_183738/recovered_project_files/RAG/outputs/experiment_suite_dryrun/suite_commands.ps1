# Generated RAG experiment suite commands

# status
D:\ryb\python.exe experiments/experiment_status.py --output-dir outputs\experiment_suite_dryrun\status

# research_plan
D:\ryb\python.exe experiments/build_experiment_research_plan.py --output-dir outputs\experiment_suite_dryrun\research_plan

# prompt_diagnostic
D:\ryb\python.exe experiments/prompt_atom_decomposition_experiment.py --output-dir outputs\experiment_suite_dryrun\prompt_atom_decomposition

# atom_result_dry_run
D:\ryb\python.exe experiments/run_atom_decomposition_result_experiment.py --dry-run --output-root outputs\experiment_suite_dryrun\atom_decomposition_result_dryrun
