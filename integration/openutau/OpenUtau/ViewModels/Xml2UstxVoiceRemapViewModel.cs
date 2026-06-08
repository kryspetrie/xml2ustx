using System.Collections.Generic;
using System.Linq;
using OpenUtau.Core.Format;
using OpenUtau.Core.Ustx;
using ReactiveUI;
using ReactiveUI.Fody.Helpers;

namespace OpenUtau.App.ViewModels {
    public class Xml2UstxVoiceRemapRow : ViewModelBase {
        public string VoicePresetId { get; }
        public string MissingSingerId { get; }
        public List<SingerOption> AvailableSingers { get; }

        [Reactive] public SingerOption? SelectedSinger { get; set; }

        public Xml2UstxVoiceRemapRow(
            string voicePresetId,
            string missingSingerId,
            IEnumerable<USinger> installedSingers) {
            VoicePresetId = voicePresetId;
            MissingSingerId = missingSingerId;
            AvailableSingers = installedSingers
                .Select(s => new SingerOption(s))
                .ToList();
            SelectedSinger = AvailableSingers.FirstOrDefault();
        }
    }

    public sealed class SingerOption {
        public USinger Singer { get; }
        public string Id => Singer.Id;
        public string Label => $"{Singer.LocalizedName} ({Singer.Id})";

        public SingerOption(USinger singer) {
            Singer = singer;
        }

        public override string ToString() => Label;
    }

    public class Xml2UstxVoiceRemapViewModel : ViewModelBase {
        public List<Xml2UstxVoiceRemapRow> Rows { get; }

        public Xml2UstxVoiceRemapViewModel(IEnumerable<Xml2UstxConfig.InvalidVoice> invalidVoices) {
            var singers = Xml2UstxConfig.ListInstalledSingers();
            Rows = invalidVoices
                .Select(v => new Xml2UstxVoiceRemapRow(v.VoicePresetId, v.ConfiguredSingerId, singers))
                .ToList();
        }

        public Dictionary<string, string> BuildRemap() {
            return Rows
                .Where(r => r.SelectedSinger != null)
                .ToDictionary(r => r.VoicePresetId, r => r.SelectedSinger!.Id);
        }

        public bool IsComplete => Rows.All(r => r.SelectedSinger != null);
    }
}
