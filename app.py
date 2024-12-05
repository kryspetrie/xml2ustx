import os
import tempfile
import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile

from main import run_and_return_string, PROGRAM_DESCRIPTION, CONFIG_FILE_PATH
from src.ConfigParser import parse

# Yes, we will be parsing this file twice... oh well.
config = parse(CONFIG_FILE_PATH)

st.title('Convert MusicXML or MIDI to .ustx')
st.markdown(PROGRAM_DESCRIPTION)
option = st.radio(label='Track config options:', options=config.track_config_map.keys())

uploaded_file: UploadedFile = st.file_uploader("Choose a file", type=['xml', 'mxl', 'mid', 'musicxml'])

if uploaded_file is not None:
    ext = os.path.splitext(uploaded_file.name)[1]
    with tempfile.NamedTemporaryFile(suffix=ext) as infile, tempfile.NamedTemporaryFile(suffix="ustx", mode="w") as outFile:
        infile.write(uploaded_file.getbuffer())
        infile_path = infile.name

        ustx_string = run_and_return_string(
            input_file=infile_path,
            project_name="OpenUTAU Project",
            config_file=CONFIG_FILE_PATH,
            track_config_id=option,
            voice_config_ids=[],
            volumes=[],
            pans=[],
            tracks=[],
            debug=False)

        outFile.write(ustx_string)
        with open(outFile.name, 'rb') as read_outfile:
            st.download_button('Download USTX file', read_outfile, file_name='outfile.ustx', mime='text/yaml')

        
        
