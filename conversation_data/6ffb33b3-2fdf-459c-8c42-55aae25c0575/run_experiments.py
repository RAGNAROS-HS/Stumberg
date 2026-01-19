#!/usr/bin/env python3
"""
Experiment Runner for EA vs DPLL Comparison

Creates reproducible experiments comparing both solvers.
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime


def create_experiment_config(experiment_name: str, ea_config_file: str, 
                            num_runs: int = 5, seeds: list = None):
    """
    Create experiment configuration
    
    Args:
        experiment_name: Name for this experiment
        ea_config_file: Path to EA configuration JSON
        num_runs: Number of EA runs per puzzle
        seeds: Optional specific seeds to use
    
    Returns:
        dict: Experiment configuration
    """
    if seeds is None:
        import random
        seeds = [random.randint(0, 1000000) for _ in range(num_runs)]
    
    return {
        'name': experiment_name,
        'timestamp': datetime.now().isoformat(),
        'ea_config_file': ea_config_file,
        'num_runs': num_runs,
        'seeds': seeds,
        'solvers': ['dpll', 'ea']
    }


def run_experiment(input_folder: str, output_folder: str, 
                   experiment_config: dict, verbose: bool = True):
    """
    Run a complete experiment
    
    Args:
        input_folder: Folder containing puzzle files
        output_folder: Folder for results
        experiment_config: Experiment configuration dictionary
        verbose: Print progress
    """
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save experiment config
    config_file = output_path / "experiment_config.json"
    with open(config_file, 'w') as f:
        json.dump(experiment_config, f, indent=2)
    
    if verbose:
        print(f"Running experiment: {experiment_config['name']}")
        print(f"Input folder: {input_folder}")
        print(f"Output folder: {output_folder}")
        print(f"EA runs per puzzle: {experiment_config['num_runs']}")
        print(f"Seeds: {experiment_config['seeds']}")
        print()
    
    # Build command
    cmd = [
        sys.executable,
        'runall_extended.py',
        '--input_folder', input_folder,
        '--output_folder', output_folder,
        '--solver', 'both',
        '--ea_config', experiment_config['ea_config_file'],
        '--seeds', ','.join(map(str, experiment_config['seeds']))
    ]
    
    if verbose:
        print(f"Running command: {' '.join(cmd)}")
        print()
    
    # Run experiment
    try:
        result = subprocess.run(cmd, check=True, capture_output=not verbose, text=True)
        
        if verbose:
            print("\nExperiment completed successfully!")
            print(f"Results saved to: {output_folder}")
        
        return True
    
    except subprocess.CalledProcessError as e:
        print(f"Error running experiment: {e}", file=sys.stderr)
        if not verbose and e.stdout:
            print(f"stdout: {e.stdout}", file=sys.stderr)
        if not verbose and e.stderr:
            print(f"stderr: {e.stderr}", file=sys.stderr)
        return False


def run_predefined_experiments(input_folder: str, base_output_folder: str):
    """
    Run a suite of predefined experiments
    
    Args:
        input_folder: Folder containing puzzle files
        base_output_folder: Base folder for all experiment results
    """
    base_path = Path(base_output_folder)
    base_path.mkdir(parents=True, exist_ok=True)
    
    experiments = [
        {
            'name': 'Quick Test',
            'config_file': 'ea_config_fast.json',
            'num_runs': 3,
            'output_suffix': 'quick_test'
        },
        {
            'name': 'Standard Configuration',
            'config_file': 'ea_config.json',
            'num_runs': 5,
            'output_suffix': 'standard'
        },
        {
            'name': 'Thorough Search',
            'config_file': 'ea_config_thorough.json',
            'num_runs': 5,
            'output_suffix': 'thorough'
        }
    ]
    
    results = []
    
    for exp_spec in experiments:
        print(f"\n{'='*60}")
        print(f"Experiment: {exp_spec['name']}")
        print(f"{'='*60}\n")
        
        output_folder = str(base_path / exp_spec['output_suffix'])
        
        exp_config = create_experiment_config(
            exp_spec['name'],
            exp_spec['config_file'],
            exp_spec['num_runs']
        )
        
        success = run_experiment(input_folder, output_folder, exp_config)
        
        results.append({
            'experiment': exp_spec['name'],
            'success': success,
            'output_folder': output_folder
        })
    
    # Summary
    print(f"\n{'='*60}")
    print("Experiment Suite Summary")
    print(f"{'='*60}\n")
    
    for result in results:
        status = "✓ SUCCESS" if result['success'] else "✗ FAILED"
        print(f"{status}: {result['experiment']}")
        if result['success']:
            print(f"  Results: {result['output_folder']}")
    
    return all(r['success'] for r in results)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Run reproducible EA vs DPLL experiments"
    )
    
    parser.add_argument(
        '--input_folder',
        required=True,
        help="Folder containing puzzle files"
    )
    
    parser.add_argument(
        '--output_folder',
        required=True,
        help="Base folder for experiment results"
    )
    
    parser.add_argument(
        '--mode',
        choices=['quick', 'standard', 'thorough', 'all', 'custom'],
        default='standard',
        help="Experiment mode"
    )
    
    parser.add_argument(
        '--ea_config',
        help="EA config file (for custom mode)"
    )
    
    parser.add_argument(
        '--num_runs',
        type=int,
        default=5,
        help="Number of EA runs per puzzle (for custom mode)"
    )
    
    parser.add_argument(
        '--seeds',
        help="Comma-separated seeds (for custom mode)"
    )
    
    args = parser.parse_args()
    
    if args.mode == 'all':
        # Run all predefined experiments
        success = run_predefined_experiments(args.input_folder, args.output_folder)
        sys.exit(0 if success else 1)
    
    elif args.mode == 'custom':
        # Run custom experiment
        if not args.ea_config:
            print("Error: --ea_config required for custom mode", file=sys.stderr)
            sys.exit(1)
        
        seeds = None
        if args.seeds:
            seeds = [int(s.strip()) for s in args.seeds.split(',')]
        
        exp_config = create_experiment_config(
            'Custom Experiment',
            args.ea_config,
            args.num_runs,
            seeds
        )
        
        success = run_experiment(args.input_folder, args.output_folder, exp_config)
        sys.exit(0 if success else 1)
    
    else:
        # Run single predefined experiment
        config_map = {
            'quick': 'ea_config_fast.json',
            'standard': 'ea_config.json',
            'thorough': 'ea_config_thorough.json'
        }
        
        exp_config = create_experiment_config(
            f"{args.mode.title()} Experiment",
            config_map[args.mode],
            args.num_runs if args.mode == 'custom' else 5
        )
        
        success = run_experiment(args.input_folder, args.output_folder, exp_config)
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
