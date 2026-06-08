using System.Collections.Generic;
using Avalonia.Controls;
using Avalonia.Interactivity;
using OpenUtau.App.ViewModels;
using OpenUtau.Core.Format;

namespace OpenUtau.App.Views {
    public partial class Xml2UstxVoiceRemapDialog : Window {
        public Xml2UstxVoiceRemapViewModel ViewModel { get; }
        public bool Confirmed { get; private set; }

        public Xml2UstxVoiceRemapDialog(IEnumerable<Xml2UstxConfig.InvalidVoice> invalidVoices) {
            InitializeComponent();
            ViewModel = new Xml2UstxVoiceRemapViewModel(invalidVoices);
            DataContext = ViewModel;
        }

        void OnSave(object? sender, RoutedEventArgs e) {
            if (!ViewModel.IsComplete) {
                return;
            }
            Confirmed = true;
            Close();
        }

        void OnCancel(object? sender, RoutedEventArgs e) {
            Close();
        }
    }
}
