[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/nicolalandro/xml2ustx/main/src/streamlit_app.py)

# musicxml to USTX
Transform a music .xml to .ustx for UTAU.

```
PYTHONPATH="$PYTHONPATH:$(pwd)" python3.8 src/main.py data/haendel_hallelujah.xml
# it save test.ustx
```

* streamlit demo

```
PYTHONPATH="$PYTHONPATH:$(pwd)" python3.8 -m streamlit run src/streamlit_app.py
```