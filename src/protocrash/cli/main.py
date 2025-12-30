"""
ProtoCrash CLI - Main Entry Point
"""

import click


@click.group()
@click.version_option(version='1.0.0', prog_name='protocrash')
@click.option('-v', '--verbose', count=True, help='Increase verbosity (can be repeated)')
@click.option('-q', '--quiet', is_flag=True, help='Suppress output')
@click.option('--config', type=click.Path(exists=True), help='Configuration file path')
@click.pass_context
def cli(ctx, verbose, quiet, config):
    """
    ProtoCrash - Coverage-Guided Protocol Fuzzer

    A smart mutation-based fuzzer for finding vulnerabilities in protocol implementations.
    """
    # Store global options in context
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['quiet'] = quiet
    ctx.obj['config'] = config


@cli.command()
@click.option('--target', required=True, help='Target binary or server (e.g., ./target or tcp://localhost:8080)')
@click.option('--protocol', type=click.Choice(['http', 'dns', 'smtp', 'custom']), default='custom',
              help='Protocol type for structure-aware mutations')
@click.option('--corpus', type=click.Path(), default='./corpus',
              help='Corpus directory containing seed inputs')
@click.option('--crashes', type=click.Path(), default='./crashes',
              help='Directory to save discovered crashes')
@click.option('--timeout', type=int, default=5000,
              help='Execution timeout in milliseconds (default: 5000ms)')
@click.option('--workers', type=int, default=1,
              help='Number of parallel workers for distributed fuzzing (default: 1)')
@click.option('--duration', type=int,
              help='Campaign duration in seconds (runs indefinitely if not set)')
@click.option('--max-iterations', type=int,
              help='Maximum number of fuzzing iterations (overrides duration)')
@click.pass_context
def fuzz(ctx, target, protocol, corpus, crashes, timeout, workers, duration, max_iterations):
    """
    Start a fuzzing campaign against the target.

    \b
    EXAMPLES:
      # Basic fuzzing of a local binary
      $ protocrash fuzz --target ./vulnerable_app --corpus ./seeds

      # Distributed fuzzing with 8 workers for 1 hour
      $ protocrash fuzz --target ./app --workers 8 --duration 3600

      # HTTP protocol fuzzing with custom timeout
      $ protocrash fuzz --target tcp://localhost:8080 --protocol http --timeout 10000

      # Quick test run with iteration limit
      $ protocrash fuzz --target ./app --max-iterations 1000

    \b
    TIPS:
      • Start with 1-2 workers and scale up based on CPU usage
      • Use shorter timeouts (1-5s) for faster fuzzing
      • Provide diverse seed inputs in corpus directory
      • Monitor crashes directory for discovered bugs
    """
    from protocrash.cli.fuzz_command import run_fuzz_campaign

    run_fuzz_campaign(
        target=target,
        protocol=protocol,
        corpus_dir=corpus,
        crashes_dir=crashes,
        timeout_ms=timeout,
        num_workers=workers,
        duration=duration,
        max_iterations=max_iterations,
        verbose=ctx.obj['verbose']
    )


@cli.command()
@click.option('--crash-dir', required=True, type=click.Path(exists=True), help='Directory containing crashes')
@click.option('--classify', is_flag=True, help='Classify crashes by exploitability')
@click.option('--dedupe', is_flag=True, help='Deduplicate crashes')
@click.option('--format', type=click.Choice(['text', 'json']), default='text', help='Output format')
@click.pass_context
def analyze(ctx, crash_dir, classify, dedupe, format):
    """
    Analyze discovered crashes.

    Examples:

      # Analyze and classify crashes
      protocrash analyze --crash-dir ./crashes --classify

      # Deduplicate crashes
      protocrash analyze --crash-dir ./crashes --dedupe

      # JSON output
      protocrash analyze --crash-dir ./crashes --format json
    """
    from protocrash.cli.analyze_command import run_crash_analysis

    run_crash_analysis(
        crash_dir=crash_dir,
        classify=classify,
        dedupe=dedupe,
        output_format=format,
        verbose=ctx.obj['verbose']
    )


@cli.command()
@click.option('--campaign', type=click.Path(exists=True), help='Campaign directory (corpus + crashes)')
@click.option('--format', type=click.Choice(['text', 'html', 'json']), default='html', help='Report format')
@click.option('--output', type=click.Path(), required=True, help='Output file path')
@click.pass_context
def report(ctx, campaign, format, output):
    """
    Generate fuzzing campaign report.

    Examples:

      # Generate HTML report
      protocrash report --campaign ./campaign --format html --output report.html

      # Generate text summary
      protocrash report --campaign ./campaign --format text --output summary.txt

      # Generate JSON data
      protocrash report --campaign ./campaign --format json --output data.json
    """
    from protocrash.cli.report_command import generate_report

    generate_report(
        campaign_dir=campaign,
        output_format=format,
        output_path=output,
        verbose=ctx.obj['verbose']
    )


def main():
    """Entry point for CLI"""
    cli(obj={})


if __name__ == '__main__':
    main()
