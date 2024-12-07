import os
import tempfile
import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile

from src.application.Strings import PROGRAM_DESCRIPTION
from src.application.models.UiOptions import UiOptions
from src.application.ConfigParser import parse
from src.application.JobBuilder import DEFAULT_CONFIG_FILE
from src.application.Xml2UstxRunner import run_app

# Yes, we will be parsing this file twice... oh well.
config = parse(DEFAULT_CONFIG_FILE)

st.title('Convert MusicXML or MIDI to .ustx')
st.markdown(PROGRAM_DESCRIPTION)
track_config_id = st.radio(label='Track config options:', options=config.track_config_map.keys())

uploaded_file: UploadedFile = st.file_uploader("Choose a file", type=['xml', 'mxl', 'mid', 'musicxml'])

if uploaded_file is not None:
    ext = os.path.splitext(uploaded_file.name)[1]

    # Write the input file to disk as a temp file
    with tempfile.NamedTemporaryFile(suffix=ext) as infile, tempfile.NamedTemporaryFile(suffix="ustx", mode="w") as outFile:
        infile.write(uploaded_file.getbuffer())

        # Generate the USTX output
        ui_options = UiOptions(input_file=infile.name, track_config_id=track_config_id)
        ustx_string: str = run_app(ui_options)

        # Write the output file to disk as a temp file
        outFile.write(ustx_string)
        with open(outFile.name, 'rb') as read_outfile:

            # Populate a download button for the output file
            st.download_button('Download USTX file', read_outfile, file_name='outfile.ustx', mime='text/yaml')
