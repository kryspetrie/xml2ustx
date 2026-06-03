using System.IO;
using System.Text;
using Avalonia.Controls;
using Avalonia.Interactivity;
using OpenUtau.Core.Util;

namespace OpenUtau.App.Views {
    public partial class Xml2UstxConfigWindow : Window {
        readonly string configPath;
        TextBox? configBox;

        public Xml2UstxConfigWindow() {
            InitializeComponent();
            configPath = Xml2UstxPaths.EnsureUserConfig();
            configBox = this.FindControl<TextBox>("ConfigBox");
            if (configBox != null) {
                configBox.Text = File.ReadAllText(configPath, Encoding.UTF8);
            }
        }

        void OnSave(object? sender, RoutedEventArgs e) {
            if (configBox != null) {
                File.WriteAllText(configPath, configBox.Text ?? string.Empty, Encoding.UTF8);
            }
            Close();
        }

        void OnReset(object? sender, RoutedEventArgs e) {
            if (configBox != null && File.Exists(Xml2UstxPaths.ShippedDefaultConfigPath)) {
                configBox.Text = File.ReadAllText(Xml2UstxPaths.ShippedDefaultConfigPath, Encoding.UTF8);
            }
        }

        void OnOpenFolder(object? sender, RoutedEventArgs e) {
            OS.OpenFolder(Xml2UstxPaths.UserConfigDirectory);
        }

        void OnClose(object? sender, RoutedEventArgs e) {
            Close();
        }
    }
}
