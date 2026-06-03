// Add to OpenUtau/FilePicker.cs after MUSICXML file type:

        public static FilePickerFileType MuseScoreMusicXml { get; } = new("MuseScore / MusicXML") {
            Patterns = new[] { "*.musicxml", "*.mxl", "*.xml", "*.mid", "*.midi" },
        };

// Optionally extend ProjectFiles patterns to include *.mxl and *.xml:
// Patterns = new[] { "*.ustx", "*.vsqx", "*.ust", "*.mid", "*.midi", "*.ufdata", "*.musicxml", "*.mxl", "*.xml" },
