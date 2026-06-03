using System;
using System.IO;
using System.Runtime.InteropServices;
using Serilog;

namespace OpenUtau.Core.Util {
    /// <summary>
    /// Paths for bundled or downloaded xml2ustx sidecar and user config.
    /// </summary>
    public static class Xml2UstxPaths {
        public const string ToolsSubDir = "tools";
        public const string SidecarSubDir = "xml2ustx";
        public const string SidecarExeName = "xml2ustx";
        public const string ShippedDefaultConfigName = "default-config.yml";
        public const string DownloadedSidecarSubDir = "sidecar";

        public static string BundledSidecarDirectory =>
            Path.Combine(PathManager.Inst.RootPath, ToolsSubDir, SidecarSubDir);

        public static string DownloadedSidecarDirectory =>
            Path.Combine(PathManager.Inst.DataPath, SidecarSubDir, DownloadedSidecarSubDir);

        /// <summary>Active sidecar directory (downloaded preferred over bundled).</summary>
        public static string SidecarDirectory {
            get {
                string downloadedExe = GetExecutablePathIn(DownloadedSidecarDirectory);
                if (File.Exists(downloadedExe)) {
                    return DownloadedSidecarDirectory;
                }
                return BundledSidecarDirectory;
            }
        }

        public static string ExecutablePath => GetExecutablePathIn(SidecarDirectory);

        static string GetExecutablePathIn(string directory) {
            string name = RuntimeInformation.IsOSPlatform(OSPlatform.Windows)
                ? SidecarExeName + ".exe"
                : SidecarExeName;
            return Path.Combine(directory, name);
        }

        public static string UserConfigDirectory =>
            Path.Combine(PathManager.Inst.DataPath, SidecarSubDir);

        public static string UserConfigPath =>
            Path.Combine(UserConfigDirectory, "config.yml");

        public static string ShippedDefaultConfigPath {
            get {
                string bundled = Path.Combine(BundledSidecarDirectory, ShippedDefaultConfigName);
                if (File.Exists(bundled)) {
                    return bundled;
                }
                string downloaded = Path.Combine(DownloadedSidecarDirectory, ShippedDefaultConfigName);
                if (File.Exists(downloaded)) {
                    return downloaded;
                }
                return bundled;
            }
        }

        public static bool SidecarExists => File.Exists(ExecutablePath);

        public static string EnsureUserConfig() {
            Directory.CreateDirectory(UserConfigDirectory);
            if (!File.Exists(UserConfigPath)) {
                if (File.Exists(ShippedDefaultConfigPath)) {
                    File.Copy(ShippedDefaultConfigPath, UserConfigPath);
                    Log.Information($"Created xml2ustx config at {UserConfigPath}");
                } else {
                    throw new FileNotFoundException(
                        "xml2ustx default config not found. Use Tools to download the MusicXML converter, or place config.yml in the xml2ustx folder.",
                        ShippedDefaultConfigPath);
                }
            }
            return UserConfigPath;
        }
    }
}
