import sys

import ConfigParser
from models.ApplicationConfig import ApplicationConfig
from src.models.JobConfig import JobConfig
from src.models.Project import Project
from src.models.TrackConfig import TrackConfig
from src.models.Voice import Voice
from src.ustx.UstxExport import export
from src.ProjectParser import parse
from typing import List

CONFIG_FILE_PATH = "./config.yml"

if __name__ == '__main__':
    input_file = sys.argv[1]
    output_file = 'outfile.ustx' if len(sys.argv) < 2 else sys.argv[2]
    project_name = 'My First Project' if len(sys.argv) < 3 else sys.argv[3]

    application_config: ApplicationConfig = ConfigParser.parse(CONFIG_FILE_PATH)

    track_configs: List[TrackConfig] = application_config.track_config_map['ttbb-barbershop']

    job: JobConfig = JobConfig(
        input_file=input_file,
        output_file=output_file,
        name=project_name,
        track_configs=track_configs
    )


    project: Project = parse(job)

    export(project, job.output_file)


