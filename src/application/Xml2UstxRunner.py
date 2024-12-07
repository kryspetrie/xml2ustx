from src.application.CLIParser import parse as parse_cli
from src.application.JobBuilder import build_cli as build_cli_job, build_ui as build_ui_job
from src.application.models.CommandLineOptions import CommandLineOptions
from src.application.models.UiOptions import UiOptions
from src.domain.ProjectParser import parse as parse_project
from src.domain.models.Job import Job
from src.domain.models.Project import Project
from src.ustx.UstxExport import export as export_ustx_file, write_to_string as to_ustx_string


def run_cli():
    cli_options: CommandLineOptions = parse_cli()
    job: Job = build_cli_job(cli_options)
    project: Project = parse_project(job)
    export_ustx_file(project, job.output_file)


def run_app(ui_options: UiOptions):
    job: Job = build_ui_job(ui_options)
    project: Project = parse_project(job)
    return to_ustx_string(project)
