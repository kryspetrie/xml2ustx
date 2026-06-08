// Add to OpenUtau/Views/MainWindow.axaml.cs (inside MainWindow class):

        async Task<bool> EnsureXml2UstxSidecarAsync() {
            if (Xml2UstxPaths.SidecarExists) {
                return true;
            }
            var result = await MessageBox.Show(
                this,
                ThemeManager.GetString("dialogs.xml2ustx.download.message"),
                ThemeManager.GetString("dialogs.xml2ustx.download.caption"),
                MessageBox.MessageBoxButtons.YesNo);
            if (result != MessageBox.MessageBoxResult.Yes) {
                return false;
            }
            try {
                LoadingWindow.BeginLoading(this);
                var progress = new Progress<string>(msg =>
                    DocManager.Inst.ExecuteCmd(new ProgressBarNotification(0, msg)));
                await Xml2UstxInstaller.EnsureSidecarAsync(progress);
                DocManager.Inst.ExecuteCmd(new ProgressBarNotification(0,
                    ThemeManager.GetString("progress.xml2ustx.installed")));
                return Xml2UstxPaths.SidecarExists;
            } finally {
                LoadingWindow.EndLoading();
            }
        }

        async Task<bool> EnsureXml2UstxVoicesValidAsync(string configPath, string? trackConfigId) {
            SingerManager.Inst.SearchAllSingers();
            var validation = Xml2UstxConfig.Validate(configPath, trackConfigId);
            if (validation.IsValid) {
                return true;
            }
            if (Xml2UstxConfig.ListInstalledSingers().Count == 0) {
                _ = await MessageBox.Show(
                    this,
                    ThemeManager.GetString("dialogs.xml2ustx.voiceremap.nosingers.message"),
                    ThemeManager.GetString("dialogs.xml2ustx.voiceremap.nosingers.caption"),
                    MessageBox.MessageBoxButtons.Ok);
                return false;
            }
            var remapDialog = new Xml2UstxVoiceRemapDialog(validation.MissingSingers);
            await remapDialog.ShowDialog(this);
            if (!remapDialog.Confirmed) {
                return false;
            }
            Xml2UstxConfig.ApplyVoiceRemap(configPath, remapDialog.ViewModel.BuildRemap());
            return true;
        }

        async void OnMenuImportMuseScore(object sender, RoutedEventArgs args) {
            if (!await EnsureXml2UstxSidecarAsync()) {
                return;
            }
            var files = await FilePicker.OpenFilesAboutProject(
                this, "menu.file.importmusescore",
                FilePicker.MuseScoreMusicXml);
            if (files == null || files.Length == 0) {
                return;
            }
            try {
                string configPath = Xml2UstxPaths.EnsureUserConfig();
                var trackIds = Xml2Ustx.ListTrackConfigIds(configPath);
                string defaultName = Path.GetFileNameWithoutExtension(files[0]);
                string defaultPreset = Preferences.Default.Xml2UstxTrackConfigId;
                if (string.IsNullOrEmpty(defaultPreset) || !trackIds.Contains(defaultPreset)) {
                    defaultPreset = trackIds.Count > 0 ? trackIds[0] : "default";
                }
                var dialog = new Xml2UstxImportDialog(trackIds, defaultName, defaultPreset);
                await dialog.ShowDialog(this);
                if (!dialog.Confirmed) {
                    return;
                }
                if (!string.IsNullOrEmpty(dialog.ViewModel.SelectedTrackConfigId)) {
                    Preferences.Default.Xml2UstxTrackConfigId = dialog.ViewModel.SelectedTrackConfigId;
                    Preferences.Save();
                }
                if (!await EnsureXml2UstxVoicesValidAsync(
                        configPath, dialog.ViewModel.SelectedTrackConfigId)) {
                    return;
                }
                var loadedProjects = new List<UProject>();
                foreach (var file in files) {
                    var project = await Xml2Ustx.LoadProjectAsync(
                        file,
                        configPath,
                        dialog.ViewModel.SelectedTrackConfigId,
                        dialog.ViewModel.ProjectName);
                    loadedProjects.Add(project);
                }
                bool importTempo = DocManager.Inst.Project.parts.Count == 0;
                if (!importTempo && loadedProjects[0].tempos.Count > 0) {
                    var tempoString = string.Join("\n",
                        loadedProjects[0].tempos
                            .Select(tempo => $"position: {tempo.position}, tempo: {tempo.bpm}")
                        );
                    var tempoResult = await MessageBox.Show(
                        this,
                        ThemeManager.GetString("dialogs.importtracks.importtempo") + "\n" + tempoString,
                        ThemeManager.GetString("dialogs.importtracks.caption"),
                        MessageBox.MessageBoxButtons.YesNo);
                    importTempo = tempoResult == MessageBox.MessageBoxResult.Yes;
                }
                if (DocManager.Inst.Project.parts.Count == 0 && loadedProjects.Count == 1) {
                    DocManager.Inst.ExecuteCmd(new LoadProjectNotification(loadedProjects[0]));
                } else {
                    viewModel.ImportTracks(loadedProjects.ToArray(), importTempo);
                }
            } catch (Exception e) {
                Log.Error(e, "Failed to import MuseScore MusicXML via xml2ustx");
                _ = await MessageBox.ShowError(this,
                    new MessageCustomizableException(
                        "Failed to import MusicXML",
                        "<translate:errors.failed.importfiles>",
                        e));
            }
            ValidateTracksVoiceColor();
        }

        async void OnMenuDownloadXml2Ustx(object sender, RoutedEventArgs args) {
            if (Xml2UstxPaths.SidecarExists) {
                _ = await MessageBox.Show(
                    this,
                    ThemeManager.GetString("dialogs.xml2ustx.alreadyinstalled.message"),
                    ThemeManager.GetString("dialogs.xml2ustx.alreadyinstalled.caption"),
                    MessageBox.MessageBoxButtons.Ok);
                return;
            }
            if (!await EnsureXml2UstxSidecarAsync()) {
                return;
            }
        }

        void OnMenuEditXml2UstxConfig(object sender, RoutedEventArgs args) {
            try {
                Xml2UstxPaths.EnsureUserConfig();
                var window = new Xml2UstxConfigWindow();
                window.ShowDialog(this);
            } catch (Exception e) {
                Log.Error(e, "Failed to open xml2ustx config editor");
                _ = MessageBox.ShowError(this,
                    new MessageCustomizableException(
                        "xml2ustx config",
                        "dialogs.xml2ustx.config.caption",
                        e));
            }
        }
