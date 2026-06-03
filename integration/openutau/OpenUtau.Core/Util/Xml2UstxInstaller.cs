using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Runtime.InteropServices;
using System.Threading.Tasks;
using Newtonsoft.Json;
using Serilog;
using SharpCompress.Archives;
using SharpCompress.Readers;

namespace OpenUtau.Core.Util {
    /// <summary>
    /// Downloads and installs the xml2ustx sidecar when it is not bundled with the app.
    /// </summary>
    public static class Xml2UstxInstaller {
        const string LunaiRepo = "keirokeer/OpenUtau-DiffSinger-Lunai";
        const string Xml2UstxRepo = "kryspetrie/xml2ustx";

        class GithubReleaseAsset {
            public string name = string.Empty;
            public string browser_download_url = string.Empty;
        }

        class GithubRelease {
#pragma warning disable 0649
            public long id;
            public bool draft;
            public bool prerelease;
            public string tag_name = string.Empty;
            public GithubReleaseAsset[] assets = Array.Empty<GithubReleaseAsset>();
#pragma warning restore 0649
        }

        public static string PlatformAssetName {
            get {
                if (RuntimeInformation.IsOSPlatform(OSPlatform.Windows)) {
                    return RuntimeInformation.ProcessArchitecture switch {
                        Architecture.X86 => "xml2ustx-win-x86.zip",
                        Architecture.Arm64 => "xml2ustx-win-arm64.zip",
                        _ => "xml2ustx-win-x64.zip",
                    };
                }
                if (RuntimeInformation.IsOSPlatform(OSPlatform.OSX)) {
                    return RuntimeInformation.ProcessArchitecture == Architecture.Arm64
                        ? "xml2ustx-osx-arm64.zip"
                        : "xml2ustx-osx-x64.zip";
                }
                return RuntimeInformation.ProcessArchitecture == Architecture.Arm64
                    ? "xml2ustx-linux-arm64.zip"
                    : "xml2ustx-linux-x64.zip";
            }
        }

        public static async Task<bool> EnsureSidecarAsync(IProgress<string>? status = null) {
            if (Xml2UstxPaths.SidecarExists) {
                return true;
            }
            status?.Report("Downloading MusicXML converter...");
            try {
                await DownloadAndInstallAsync(status);
                return Xml2UstxPaths.SidecarExists;
            } catch (Exception e) {
                Log.Error(e, "Failed to install xml2ustx sidecar");
                throw;
            }
        }

        public static async Task DownloadAndInstallAsync(IProgress<string>? status = null) {
            string assetName = PlatformAssetName;
            string? url = await ResolveDownloadUrlAsync(LunaiRepo, assetName)
                ?? await ResolveDownloadUrlAsync(Xml2UstxRepo, assetName);
            if (url == null) {
                throw new FileNotFoundException(
                    $"No release asset '{assetName}' found on GitHub. Build the sidecar or install it manually under {Xml2UstxPaths.DownloadedSidecarDirectory}.");
            }
            status?.Report($"Downloading MusicXML converter ({assetName})...");
            byte[] data = await DownloadAsync(url);
            string dest = Xml2UstxPaths.DownloadedSidecarDirectory;
            if (Directory.Exists(dest)) {
                Directory.Delete(dest, true);
            }
            Directory.CreateDirectory(dest);
            status?.Report("Extracting MusicXML converter...");
            await Task.Run(() => ExtractZip(data, dest));
            string exe = Path.Combine(dest, RuntimeInformation.IsOSPlatform(OSPlatform.Windows)
                ? Xml2UstxPaths.SidecarExeName + ".exe"
                : Xml2UstxPaths.SidecarExeName);
            if (File.Exists(exe) && !RuntimeInformation.IsOSPlatform(OSPlatform.Windows)) {
                File.SetUnixFileMode(exe,
                    UnixFileMode.UserRead | UnixFileMode.UserWrite | UnixFileMode.UserExecute |
                    UnixFileMode.GroupRead | UnixFileMode.GroupExecute |
                    UnixFileMode.OtherRead | UnixFileMode.OtherExecute);
            }
            Log.Information("Installed xml2ustx sidecar to {Path}", dest);
        }

        static async Task<string?> ResolveDownloadUrlAsync(string repo, string assetName) {
            using var client = new HttpClient();
            client.DefaultRequestHeaders.Add("Accept", "application/json");
            client.DefaultRequestHeaders.Add("User-Agent", "OpenUtau-xml2ustx");
            client.Timeout = TimeSpan.FromSeconds(30);
            string api = $"https://api.github.com/repos/{repo}/releases";
            using var response = await client.GetAsync(api);
            if (!response.IsSuccessStatusCode) {
                Log.Warning("GitHub releases API failed for {Repo}: {Code}", repo, response.StatusCode);
                return null;
            }
            var releases = JsonConvert.DeserializeObject<List<GithubRelease>>(
                await response.Content.ReadAsStringAsync());
            if (releases == null) {
                return null;
            }
            foreach (var release in releases
                .Where(r => !r.draft)
                .OrderByDescending(r => r.id)) {
                var asset = release.assets?.FirstOrDefault(a =>
                    string.Equals(a.name, assetName, StringComparison.OrdinalIgnoreCase));
                if (asset != null && !string.IsNullOrEmpty(asset.browser_download_url)) {
                    Log.Information("xml2ustx asset {Asset} from {Repo} release {Tag}", assetName, repo, release.tag_name);
                    return asset.browser_download_url;
                }
            }
            return null;
        }

        static async Task<byte[]> DownloadAsync(string url) {
            using var client = new HttpClient();
            client.Timeout = TimeSpan.FromMinutes(10);
            using var response = await client.GetAsync(url, HttpCompletionOption.ResponseHeadersRead);
            response.EnsureSuccessStatusCode();
            return await response.Content.ReadAsByteArrayAsync();
        }

        static void ExtractZip(byte[] data, string destDir) {
            using var stream = new MemoryStream(data);
            using var archive = ArchiveFactory.OpenArchive(stream, new ReaderOptions());
            foreach (var entry in archive.Entries) {
                if (string.IsNullOrEmpty(entry.Key) || entry.Key.Contains("..")) {
                    continue;
                }
                string outPath = Path.Combine(destDir, entry.Key);
                if (entry.IsDirectory) {
                    Directory.CreateDirectory(outPath);
                } else {
                    var dir = Path.GetDirectoryName(outPath);
                    if (!string.IsNullOrEmpty(dir)) {
                        Directory.CreateDirectory(dir);
                    }
                    entry.WriteToFile(outPath, new ExtractionOptions { ExtractFullPath = true, Overwrite = true });
                }
            }
        }
    }
}
