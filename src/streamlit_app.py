import tempfile

import streamlit as st

from src.main import create_utau


st.title('Convert .xml to .ustx')
st.markdown('This app need a .xml music file as input and convert it into OpenUtau file project. You can generate it from MuseScore or similar software.')


uploaded_file = st.file_uploader("Choose a .xml music file", type='xml')

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(suffix=".xml") as f:
        f.write(uploaded_file.getbuffer())
        file_path = f.name

        text_ustx = create_utau(file_path)
        with open('output.ustx', 'w') as f:
            f.write(text_ustx)
        with open('output.ustx', 'rb') as f:
            st.download_button('Downloadd output.ustx', f,file_name="output.ustx", mime="text/yaml")
        
        
        
