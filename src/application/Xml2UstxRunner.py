"""Module for running CLI and UI jobs for XML to USTX conversion."""
from __future__ import annotations

from collections.abc import Callable

from src.Utils import dumps
from src.application.CLIParser import parse as parse_cli
from src.application.JobBuilder import (
    build_cli as build_cli_job,
    build_native as build_native_job,
)
from src.application.conversion_errors import ConversionCancelledError
from src.application.conversion_log import LogFn, emit_log
from src.application.session_log import SessionLogger
from src.application.models.CommandLineOptions import CommandLineOptions
from src.application.models.NativeUiOptions import NativeUiOptions
from src.domain.ProjectParser import parse as parse_project
from src.domain.models.Job import Job
from src.domain.models.Project import Project
from src.ustx.UstxExport import export as export_ustx_file


def run_cli() -> None:
    """Run the CLI job for XML to USTX conversion."""
    cli_options: CommandLineOptions = parse_cli()
    job: Job = build_cli_job(cli_options)
    outputs = run_job(job)
    if cli_options.open_in_openutau:
        from src.application.openutau_launcher import open_in_openutau

        open_in_openutau(outputs, openutau_path=cli_options.openutau_path)


def run_job(
        job: Job,
        *,
        log_fn: LogFn | None = None,
        should_cancel: Callable[[], bool] | None = None,
        progress_fn: Callable[[int, int], None] | None = None) -> list[str]:
    """Run conversion for a built job; returns output file paths.

    Args:
        job: Built conversion job.
        log_fn: Optional sink for progress and debug messages (UI log panel).
        should_cancel: When this returns ``True``, abort before the next file.

    Returns:
        Paths to generated USTX files.

    Raises:
        ConversionCancelledError: When ``should_cancel`` returns ``True``.
    """
    outputs: list[str] = []
    with SessionLogger(log_fn=log_fn, session_name=job.name) as session:
        job_log = session.write
        emit_log(f'Session log: {session.path}', log_fn=job_log)

        if job.debug:
            emit_log(f'Running job with the following config:\n{dumps(job)}\n', log_fn=job_log)

        total = len(job.input_files)
        for index, input_file in enumerate(job.input_files, start=1):
            if should_cancel and should_cancel():
                raise ConversionCancelledError('Conversion cancelled.')

            if progress_fn is not None:
                progress_fn(index, total)

            emit_log(f'Converting file {index}/{total}: {input_file}', log_fn=job_log)
            project: Project = parse_project(
                input_file=input_file,
                project_name=job.name,
                track_configs=job.track_configs,
                default_lyric=job.default_lyric,
                debug=job.debug,
                log_fn=job_log,
                should_cancel=should_cancel,
            )
            output_file = job.output_files[index - 1]
            export_ustx_file(project, output_file, log_fn=job_log)
            outputs.append(output_file)

    return outputs


def run_native(
        native_options: NativeUiOptions,
        *,
        log_fn: LogFn | None = None,
        should_cancel: Callable[[], bool] | None = None,
        progress_fn: Callable[[int, int], None] | None = None) -> list[str]:
    """Run conversion from native UI options."""
    job: Job = build_native_job(native_options)
    return run_job(job, log_fn=log_fn, should_cancel=should_cancel, progress_fn=progress_fn)
