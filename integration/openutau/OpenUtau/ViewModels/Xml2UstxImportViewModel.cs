using System.Collections.Generic;
using ReactiveUI;
using ReactiveUI.Fody.Helpers;

namespace OpenUtau.App.ViewModels {
    public class Xml2UstxImportViewModel : ViewModelBase {
        [Reactive] public string ProjectName { get; set; } = "Imported Score";
        [Reactive] public string? SelectedTrackConfigId { get; set; }
        public List<string> TrackConfigIds { get; }

        public Xml2UstxImportViewModel(
            List<string> trackConfigIds,
            string defaultProjectName,
            string? defaultTrackConfigId = null) {
            TrackConfigIds = trackConfigIds;
            ProjectName = defaultProjectName;
            if (!string.IsNullOrEmpty(defaultTrackConfigId)
                && trackConfigIds.Contains(defaultTrackConfigId)) {
                SelectedTrackConfigId = defaultTrackConfigId;
            } else if (trackConfigIds.Count > 0) {
                SelectedTrackConfigId = trackConfigIds[0];
            }
        }
    }
}
