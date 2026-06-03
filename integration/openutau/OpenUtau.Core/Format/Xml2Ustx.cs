using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using OpenUtau.Core.Ustx;
using OpenUtau.Core.Util;
using Serilog;
using YamlDotNet.Serialization;

namespace OpenUtau.Core.Format {
    /// <summary>
    /// Invokes the bundled xml2ustx sidecar to convert MuseScore / MusicXML inputs to USTX.
    /// </summary>
    public static class Xml2Ustx {
        static readonly string[] InputExtensions = { ".xml", ".musicxml", ".mxl", ".mid", ".midi" };

        public static bool IsSupportedInput(string path) {
            if (string.IsNullOrEmpty(path)) {
                return false;
            }
            return InputExtensions.Contains(Path.GetExtension(path).ToLowerInvariant());
        }

        public static List<string> ListTrackConfigIds(string configPath) {
            var ids = new List<string>();
            if (!File.Exists(configPath)) {
                return ids;
            }
            try {
                var yaml = File.ReadAllText(configPath, Encoding.UTF8);
                var deserializer = new DeserializerBuilder().Build();
                var root = deserializer.Deserialize<Dictionary<string, object>>(yaml);
                if (root != null && root.TryGetValue("track_config", out var trackConfigObj)
                    && trackConfigObj is List<object> entries) {
                    foreach (var entry in entries) {
                        if (entry is Dictionary<object, object> dict
                            && dict.TryGetValue("id", out var idObj)) {
                            ids.Add(idObj?.ToString() ?? string.Empty);
                        }
                    }
                }
            } catch (Exception e) {
                Log.Warning(e, "Failed to parse track_config from {Path}", configPath);
            }
            ids.RemoveAll(string.IsNullOrWhiteSpace);
            return ids;
        }

        public static async Task<string> ConvertToUstxAsync(
            string inputFile,
            string configFile,
            string? trackConfigId,
            string projectName) {
            if (!Xml2UstxPaths.SidecarExists) {
                throw new FileNotFoundException(
                    "xml2ustx converter not found. This build may not include the MusicXML sidecar.",
                    Xml2UstxPaths.ExecutablePath);
            }
            if (!File.Exists(inputFile)) {
                throw new FileNotFoundException("Input file not found.", inputFile);
            }
            if (!File.Exists(configFile)) {
                throw new FileNotFoundException("xml2ustx config not found.", configFile);
            }

            string outputFile = Path.Combine(
                Path.GetTempPath(),
                $"xml2ustx-{Guid.NewGuid():N}.ustx");

            var args = new StringBuilder();
            args.Append($"--input_file \"{inputFile}\"");
            args.Append($" --output_file \"{outputFile}\"");
            args.Append($" --config_file \"{configFile}\"");
            args.Append($" --project_name \"{projectName.Replace("\"", "\\\"")}\"");
            if (!string.IsNullOrWhiteSpace(trackConfigId)) {
                args.Append($" --track_config \"{trackConfigId}\"");
            }

            var startInfo = new ProcessStartInfo {
                FileName = Xml2UstxPaths.ExecutablePath,
                Arguments = args.ToString(),
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true,
                WorkingDirectory = Xml2UstxPaths.SidecarDirectory,
            };
            startInfo.Environment["XML2USTX_CONFIG"] = configFile;

            using var process = Process.Start(startInfo)
                ?? throw new InvalidOperationException("Failed to start xml2ustx process.");
            string stderr = await process.StandardError.ReadToEndAsync();
            await process.WaitForExitAsync();

            if (process.ExitCode != 0) {
                var message = string.IsNullOrWhiteSpace(stderr)
                    ? $"xml2ustx exited with code {process.ExitCode}"
                    : stderr.Trim();
                throw new InvalidOperationException(message);
            }
            if (!File.Exists(outputFile)) {
                throw new FileNotFoundException("xml2ustx did not produce an output file.", outputFile);
            }
            return outputFile;
        }

        public static async Task<UProject> LoadProjectAsync(
            string inputFile,
            string configFile,
            string? trackConfigId,
            string projectName) {
            string ustxPath = await ConvertToUstxAsync(
                inputFile, configFile, trackConfigId, projectName);
            try {
                var project = Ustx.Load(ustxPath);
                project.FilePath = string.Empty;
                project.Saved = false;
                return project;
            } finally {
                try {
                    if (File.Exists(ustxPath)) {
                        File.Delete(ustxPath);
                    }
                } catch (Exception e) {
                    Log.Warning(e, "Failed to delete temp ustx {Path}", ustxPath);
                }
            }
        }
    }
}
