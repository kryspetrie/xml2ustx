using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using OpenUtau.Core;
using OpenUtau.Core.Ustx;
using Serilog;
using YamlDotNet.Serialization;

namespace OpenUtau.Core.Format {
    /// <summary>
    /// Reads and updates xml2ustx config.yml voice presets against installed OpenUtau singers.
    /// </summary>
    public static class Xml2UstxConfig {
        public sealed class VoiceEntry {
            public string Id { get; set; } = string.Empty;
            public string? Singer { get; set; }
            public string? Phonemizer { get; set; }
            public string? Renderer { get; set; }
        }

        public sealed class InvalidVoice {
            public string VoicePresetId { get; init; } = string.Empty;
            public string ConfiguredSingerId { get; init; } = string.Empty;
        }

        public sealed class ValidationResult {
            public List<InvalidVoice> MissingSingers { get; init; } = new();
            public bool IsValid => MissingSingers.Count == 0;
        }

        static readonly IDeserializer Deserializer = new DeserializerBuilder()
            .IgnoreUnmatchedProperties()
            .Build();

        static readonly ISerializer Serializer = new SerializerBuilder().Build();

        public static ValidationResult Validate(string configPath, string? trackConfigId) {
            var result = new ValidationResult { MissingSingers = new List<InvalidVoice>() };
            if (!File.Exists(configPath)) {
                return result;
            }
            try {
                var voiceIds = GetVoiceIdsForTrackConfig(configPath, trackConfigId);
                var voices = LoadVoiceEntries(configPath);
                var voiceMap = voices.ToDictionary(v => v.Id, StringComparer.OrdinalIgnoreCase);
                foreach (var voiceId in voiceIds) {
                    if (!voiceMap.TryGetValue(voiceId, out var voice)) {
                        result.MissingSingers.Add(new InvalidVoice {
                            VoicePresetId = voiceId,
                            ConfiguredSingerId = "(voice preset missing from config)",
                        });
                        continue;
                    }
                    if (string.IsNullOrWhiteSpace(voice.Singer)) {
                        continue;
                    }
                    var singer = SingerManager.Inst.GetSinger(voice.Singer);
                    if (singer == null || !singer.Found) {
                        result.MissingSingers.Add(new InvalidVoice {
                            VoicePresetId = voice.Id,
                            ConfiguredSingerId = voice.Singer,
                        });
                    }
                }
            } catch (Exception e) {
                Log.Warning(e, "Failed to validate xml2ustx config {Path}", configPath);
            }
            return result;
        }

        public static List<string> GetVoiceIdsForTrackConfig(string configPath, string? trackConfigId) {
            var ids = new List<string>();
            if (!File.Exists(configPath)) {
                return ids;
            }
            var root = LoadRoot(configPath);
            if (root == null || !root.TryGetValue("track_config", out var trackConfigObj)) {
                return ids;
            }
            if (trackConfigObj is not List<object> trackConfigs) {
                return ids;
            }
            string? selectedId = string.IsNullOrWhiteSpace(trackConfigId) ? "default" : trackConfigId;
            Dictionary<object, object>? selected = null;
            foreach (var entry in trackConfigs) {
                if (entry is not Dictionary<object, object> dict) {
                    continue;
                }
                if (dict.TryGetValue("id", out var idObj)
                    && string.Equals(idObj?.ToString(), selectedId, StringComparison.OrdinalIgnoreCase)) {
                    selected = dict;
                    break;
                }
            }
            selected ??= trackConfigs
                .OfType<Dictionary<object, object>>()
                .FirstOrDefault(d => string.Equals(d.TryGetValue("id", out var idObj) ? idObj?.ToString() : null,
                    "default", StringComparison.OrdinalIgnoreCase));
            if (selected == null || !selected.TryGetValue("tracks", out var tracksObj)) {
                return ids;
            }
            if (tracksObj is not List<object> tracks) {
                return ids;
            }
            foreach (var track in tracks) {
                if (track is Dictionary<object, object> trackDict
                    && trackDict.TryGetValue("voice_id", out var voiceIdObj)) {
                    var voiceId = voiceIdObj?.ToString();
                    if (!string.IsNullOrWhiteSpace(voiceId)) {
                        ids.Add(voiceId);
                    }
                }
            }
            return ids.Distinct(StringComparer.OrdinalIgnoreCase).ToList();
        }

        public static List<VoiceEntry> LoadVoiceEntries(string configPath) {
            var root = LoadRoot(configPath);
            var entries = new List<VoiceEntry>();
            if (root == null || !root.TryGetValue("voice_config", out var voiceConfigObj)) {
                return entries;
            }
            if (voiceConfigObj is not List<object> voiceConfigs) {
                return entries;
            }
            foreach (var item in voiceConfigs) {
                if (item is not Dictionary<object, object> dict) {
                    continue;
                }
                entries.Add(new VoiceEntry {
                    Id = dict.TryGetValue("id", out var idObj) ? idObj?.ToString() ?? string.Empty : string.Empty,
                    Singer = dict.TryGetValue("singer", out var singerObj) ? singerObj?.ToString() : null,
                    Phonemizer = dict.TryGetValue("phonemizer", out var phonObj) ? phonObj?.ToString() : null,
                    Renderer = dict.TryGetValue("renderer", out var rendObj) ? rendObj?.ToString() : null,
                });
            }
            return entries;
        }

        public static void ApplyVoiceRemap(string configPath, IReadOnlyDictionary<string, string> voicePresetToSingerId) {
            if (!File.Exists(configPath)) {
                throw new FileNotFoundException("xml2ustx config not found.", configPath);
            }
            var root = LoadRoot(configPath)
                ?? throw new InvalidOperationException("Invalid xml2ustx config YAML.");
            if (!root.TryGetValue("voice_config", out var voiceConfigObj) || voiceConfigObj is not List<object> voiceConfigs) {
                throw new InvalidOperationException("voice_config section missing from xml2ustx config.");
            }
            foreach (var item in voiceConfigs) {
                if (item is not Dictionary<object, object> dict) {
                    continue;
                }
                var voiceId = dict.TryGetValue("id", out var idObj) ? idObj?.ToString() : null;
                if (string.IsNullOrWhiteSpace(voiceId)
                    || !voicePresetToSingerId.TryGetValue(voiceId, out var newSingerId)) {
                    continue;
                }
                var singer = SingerManager.Inst.GetSinger(newSingerId)
                    ?? throw new InvalidOperationException($"Singer not found: {newSingerId}");
                dict["singer"] = newSingerId;
                if (!string.IsNullOrWhiteSpace(singer.DefaultPhonemizer)) {
                    dict["phonemizer"] = singer.DefaultPhonemizer;
                }
                var renderer = RendererFor(singer);
                if (!string.IsNullOrWhiteSpace(renderer)) {
                    dict["renderer"] = renderer;
                }
            }
            var yaml = Serializer.Serialize(root);
            File.WriteAllText(configPath, yaml, Encoding.UTF8);
        }

        public static List<USinger> ListInstalledSingers() {
            return SingerManager.Inst.Singers.Values
                .Where(s => s.Found)
                .OrderBy(s => s.LocalizedName, StringComparer.OrdinalIgnoreCase)
                .ToList();
        }

        static string? RendererFor(USinger singer) {
            return singer.SingerType switch {
                USingerType.DiffSinger => "DIFFSINGER",
                USingerType.Enunu => "ENUNU",
                USingerType.Voicevox => "VOICEVOX",
                _ => null,
            };
        }

        static Dictionary<string, object>? LoadRoot(string configPath) {
            var yaml = File.ReadAllText(configPath, Encoding.UTF8);
            return Deserializer.Deserialize<Dictionary<string, object>>(yaml);
        }
    }
}
