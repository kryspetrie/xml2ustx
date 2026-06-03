using System.Collections.Generic;
using Avalonia.Controls;
using Avalonia.Interactivity;
using OpenUtau.App.ViewModels;

namespace OpenUtau.App.Views {
    public partial class Xml2UstxImportDialog : Window {
        public Xml2UstxImportViewModel ViewModel { get; }
        public bool Confirmed { get; private set; }

        public Xml2UstxImportDialog(
            List<string> trackConfigIds,
            string defaultProjectName,
            string? defaultTrackConfigId = null) {
            InitializeComponent();
            ViewModel = new Xml2UstxImportViewModel(trackConfigIds, defaultProjectName, defaultTrackConfigId);
            DataContext = ViewModel;
        }

        void OnOk(object? sender, RoutedEventArgs e) {
            Confirmed = true;
            Close();
        }

        void OnCancel(object? sender, RoutedEventArgs e) {
            Close();
        }
    }
}
