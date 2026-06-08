"""Public entry points for writing OpenUtau USTX project files."""
from __future__ import annotations

from src.application.conversion_log import LogFn
from src.domain.models.Project import Project
from src.ustx.UstxSerializer import serialize


def export(project: Project, outfile: str, *, log_fn: LogFn | None = None) -> None:
    """Write a domain project to a ``.ustx`` file on disk.

    Args:
        project: Parsed domain project to export.
        outfile: Destination path for the generated USTX file.
        log_fn: Optional sink for progress messages (UI log panel).
    """
    from src.application.conversion_log import emit_log

    with open(outfile, 'w', encoding='utf-8') as file:
        ustx = serialize(project)
        file.write(ustx)
        emit_log(f'Wrote output file to {outfile}', log_fn=log_fn)


def write_to_string(project: Project) -> str:
    """Serialize a domain project to USTX YAML text without writing a file.

    Args:
        project: Parsed domain project to export.

    Returns:
        YAML text for the generated USTX project.
    """
    return serialize(project)
