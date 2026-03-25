using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.IO;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading.Tasks;
using System.Windows.Input;
using Newtonsoft.Json;
using StarSaviorTool.Models;
using StarSaviorTool.Services;

namespace StarSaviorTool.ViewModels
{
    public class MainViewModel : INotifyPropertyChanged
    {
        private readonly PythonBridge _python = new();
        private CharacterData _characterData = new();

        // ─── Collections ─────────────────────────────
        public ObservableCollection<Character> AllCharacters { get; } = new();
        public ObservableCollection<Character> FilteredCharacters { get; } = new();
        public ObservableCollection<Character> SelectedTeam { get; } = new();
        public ObservableCollection<string> CoverageReport { get; } = new();
        public ObservableCollection<string> Warnings { get; } = new();
        public ObservableCollection<string> TeamAnalysis { get; } = new();
        public ObservableCollection<string> Synergies { get; } = new();

        // ─── Team Builder Options ────────────────────
        private string _selectedTeamFocus = "Balanced";
        public string SelectedTeamFocus
        {
            get => _selectedTeamFocus;
            set { _selectedTeamFocus = value; OnPropertyChanged(); if(SelectedTeam.Count > 0) { _ = AnalyzeTeamAsync(); } }
        }
        public List<string> TeamFocusOptions { get; } = new() { "Balanced", "Hyper Carry", "Stall", "Burst Speed", "Control", "Elemental" };

        // ─── Filters ─────────────────────────────────
        private string _selectedTierFilter = "All";
        public string SelectedTierFilter
        {
            get => _selectedTierFilter;
            set { _selectedTierFilter = value; OnPropertyChanged(); ApplyFilters(); }
        }

        private string _selectedRoleFilter = "All";
        public string SelectedRoleFilter
        {
            get => _selectedRoleFilter;
            set { _selectedRoleFilter = value; OnPropertyChanged(); ApplyFilters(); }
        }

        private string _searchText = "";
        public string SearchText
        {
            get => _searchText;
            set { _searchText = value; OnPropertyChanged(); ApplyFilters(); }
        }

        public List<string> TierFilters { get; } = new() { "All", "T0", "SS", "S", "A", "B" };
        public List<string> RoleFilters { get; } = new() { "All", "Dealer", "Support", "Defender", "Assassin", "Caster" };

        // ─── Selected Character ──────────────────────
        private Character? _selectedCharacter;
        public Character? SelectedCharacter
        {
            get => _selectedCharacter;
            set { _selectedCharacter = value; OnPropertyChanged(); }
        }

        // ─── Status ──────────────────────────────────
        private string _statusText = "Ready";
        public string StatusText
        {
            get => _statusText;
            set { _statusText = value; OnPropertyChanged(); }
        }

        private bool _isOnline;
        public bool IsOnline
        {
            get => _isOnline;
            set { _isOnline = value; OnPropertyChanged(); OnPropertyChanged(nameof(ConnectionStatus)); }
        }

        public string ConnectionStatus => IsOnline ? "🟢 Online" : "🔴 Offline";

        private string _metaScoreText = "—";
        public string MetaScoreText
        {
            get => _metaScoreText;
            set { _metaScoreText = value; OnPropertyChanged(); }
        }

        private string _metaRating = "";
        public string MetaRating
        {
            get => _metaRating;
            set { _metaRating = value; OnPropertyChanged(); }
        }

        private string _metaVersion = "";
        public string MetaVersion
        {
            get => _metaVersion;
            set { _metaVersion = value; OnPropertyChanged(); }
        }

        // ─── Commands ────────────────────────────────
        public ICommand LoadDataCommand => new RelayCommand(async _ => await LoadDataAsync());
        public ICommand AddToTeamCommand => new RelayCommand(async _ => await AddToTeamAsync(), _ => SelectedCharacter != null && SelectedTeam.Count < 4);
        public ICommand RemoveFromTeamCommand => new RelayCommand(async _ => await RemoveFromTeamAsync());
        public ICommand AutoFixTeamCommand => new RelayCommand(async _ => await AutoFixTeamAsync());
        public ICommand ClearTeamCommand => new RelayCommand(async _ => { SelectedTeam.Clear(); ClearTeamResults(); });
        public ICommand EnrichDataCommand => new RelayCommand(async _ => await EnrichDataAsync());
        public ICommand CheckConnCommand => new RelayCommand(async _ => await CheckConnectivityAsync());

        // ─── Init ────────────────────────────────────
        public MainViewModel()
        {
        }

        public async Task InitializeAsync()
        {
            await LoadDataAsync();
            await CheckConnectivityAsync();
        }

        // ─── Data Loading ────────────────────────────

        private async Task LoadDataAsync()
        {
            StatusText = "Loading character data...";
            try
            {
                var json = await _python.GetAllCharactersAsync();
                var result = JsonConvert.DeserializeObject<dynamic>(json);

                // Also load directly from data.json for full data
                var dataPath = FindDataJson();
                if (dataPath != null)
                {
                    var raw = await File.ReadAllTextAsync(dataPath);
                    _characterData = JsonConvert.DeserializeObject<CharacterData>(raw) ?? new();
                }

                AllCharacters.Clear();
                foreach (var c in _characterData.Characters)
                {
                    AllCharacters.Add(c);
                }

                MetaVersion = _characterData.MetaVersion;
                ApplyFilters();
                StatusText = $"Loaded {AllCharacters.Count} characters (v{MetaVersion})";
            }
            catch (Exception ex)
            {
                StatusText = $"Error loading data: {ex.Message}";
            }
        }

        private string? FindDataJson()
        {
            // Try multiple paths
            var candidates = new[]
            {
                Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "..", "..", "..", "..", "data.json"),
                Path.Combine(Directory.GetCurrentDirectory(), "data.json"),
                Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "data.json"),
            };

            foreach (var c in candidates)
            {
                var full = Path.GetFullPath(c);
                if (File.Exists(full)) return full;
            }
            return null;
        }

        // ─── Filtering ──────────────────────────────

        private void ApplyFilters()
        {
            FilteredCharacters.Clear();

            var filtered = AllCharacters.AsEnumerable();

            if (SelectedTierFilter != "All")
                filtered = filtered.Where(c => c.Tier == SelectedTierFilter);

            if (SelectedRoleFilter != "All")
                filtered = filtered.Where(c => c.Role == SelectedRoleFilter);

            if (!string.IsNullOrWhiteSpace(SearchText))
                filtered = filtered.Where(c => c.Name.Contains(SearchText, StringComparison.OrdinalIgnoreCase));

            // Group by tier order
            var tierOrder = new[] { "T0", "SS", "S", "A", "B" };
            var ordered = filtered.OrderBy(c => Array.IndexOf(tierOrder, c.Tier)).ThenBy(c => c.Name);

            foreach (var c in ordered)
                FilteredCharacters.Add(c);
        }

        // ─── Team Builder ────────────────────────────

        private async Task AddToTeamAsync()
        {
            if (SelectedCharacter == null || SelectedTeam.Count >= 4) return;
            if (SelectedTeam.Any(c => c.Name == SelectedCharacter.Name)) return;

            SelectedTeam.Add(SelectedCharacter);
            await AnalyzeTeamAsync();
        }

        private async Task RemoveFromTeamAsync()
        {
            if (SelectedTeam.Count > 0)
            {
                SelectedTeam.RemoveAt(SelectedTeam.Count - 1);
                if (SelectedTeam.Count > 0)
                    await AnalyzeTeamAsync();
                else
                    ClearTeamResults();
            }
        }

        private void ClearTeamResults()
        {
            MetaScoreText = "—";
            MetaRating = "";
            CoverageReport.Clear();
            Warnings.Clear();
            TeamAnalysis.Clear();
            Synergies.Clear();
        }

        private async Task AnalyzeTeamAsync()
        {
            if (SelectedTeam.Count == 0) return;

            StatusText = "Analyzing team...";
            try
            {
                var names = SelectedTeam.Select(c => c.Name).ToArray();
                string focusArg = SelectedTeamFocus.ToLower().Replace(" ", "_");
                var json = await _python.BuildTeamAsync(false, true, focusArg, names);
                var result = JsonConvert.DeserializeObject<TeamResult>(json);

                if (result != null)
                {
                    // Score
                    MetaScoreText = $"{result.MetaScore.TotalScore}/{result.MetaScore.MaxScore} ({result.MetaScore.Percentage}%)";
                    MetaRating = result.MetaScore.Rating;

                    // Coverage
                    CoverageReport.Clear();
                    foreach (var item in result.CoverageReport)
                        CoverageReport.Add($"{item.Status} {item.Category}");

                    // Warnings
                    Warnings.Clear();
                    foreach (var w in result.Warnings)
                        Warnings.Add(w);

                    // Analysis
                    TeamAnalysis.Clear();
                    if (result.TeamAnalysis != null)
                    {
                        foreach (var a in result.TeamAnalysis)
                        {
                            var contribs = string.Join(", ", a.Contributions);
                            var metas = a.WhyMeta.Count > 0 ? string.Join("; ", a.WhyMeta) : "";
                            TeamAnalysis.Add($"🔹 {a.Name} [{a.Tier} {a.Role}]: {contribs}");
                            if (!string.IsNullOrEmpty(metas))
                                TeamAnalysis.Add($"   ↳ {metas}");
                        }
                    }

                    Synergies.Clear();
                    if (result.Synergies != null)
                    {
                        foreach (var s in result.Synergies)
                            Synergies.Add(s);
                    }
                }

                StatusText = "Team analysis complete";
            }
            catch (Exception ex)
            {
                StatusText = $"Analysis error: {ex.Message}";
            }
        }

        private async Task AutoFixTeamAsync()
        {
            StatusText = "Auto-fixing team...";
            try
            {
                var names = SelectedTeam.Select(c => c.Name).ToList();
                if (names.Count == 0) names.Add("Lacy"); // Default start

                string focusArg = SelectedTeamFocus.ToLower().Replace(" ", "_");
                var json = await _python.BuildTeamAsync(true, true, focusArg, names.ToArray());
                var result = JsonConvert.DeserializeObject<TeamResult>(json);

                if (result != null)
                {
                    SelectedTeam.Clear();
                    foreach (var member in result.Team)
                    {
                        var fullChar = AllCharacters.FirstOrDefault(c => c.Name == member.Name);
                        if (fullChar != null) SelectedTeam.Add(fullChar);
                    }

                    // Update score/analysis
                    MetaScoreText = $"{result.MetaScore.TotalScore}/{result.MetaScore.MaxScore} ({result.MetaScore.Percentage}%)";
                    MetaRating = result.MetaScore.Rating;

                    CoverageReport.Clear();
                    foreach (var item in result.CoverageReport)
                        CoverageReport.Add($"{item.Status} {item.Category}");

                    Warnings.Clear();
                    foreach (var w in result.Warnings)
                        Warnings.Add(w);

                    TeamAnalysis.Clear();
                    if (result.TeamAnalysis != null)
                    {
                        foreach (var a in result.TeamAnalysis)
                        {
                            var contribs = string.Join(", ", a.Contributions);
                            TeamAnalysis.Add($"🔹 {a.Name} [{a.Tier} {a.Role}]: {contribs}");
                            if (a.WhyMeta.Count > 0)
                                TeamAnalysis.Add($"   ↳ {string.Join("; ", a.WhyMeta)}");
                        }
                    }

                    // Show suggestions
                    if (result.AutoSuggestions.Count > 0)
                    {
                        TeamAnalysis.Add("");
                        TeamAnalysis.Add("🤖 Auto-Suggestions:");
                        foreach (var s in result.AutoSuggestions)
                            TeamAnalysis.Add($"   → {s.Name} ({s.Tier} {s.Role}): {s.Reason}");
                    }

                    Synergies.Clear();
                    if (result.Synergies != null)
                    {
                        foreach (var s in result.Synergies)
                            Synergies.Add(s);
                    }
                }

                StatusText = "Auto-fix complete";
            }
            catch (Exception ex)
            {
                StatusText = $"Auto-fix error: {ex.Message}";
            }
        }

        // ─── Enrichment ─────────────────────────────

        private async Task EnrichDataAsync()
        {
            StatusText = "Enriching data from web sources...";
            try
            {
                var json = await _python.EnrichDataAsync();
                var result = JsonConvert.DeserializeObject<dynamic>(json);

                if (result != null)
                {
                    string status = (string)(result.status ?? "unknown");
                    string message = (string)(result.message ?? "Unknown result");
                    int enriched = (int)(result.enriched ?? 0);

                    StatusText = message;

                    if (enriched > 0)
                        await LoadDataAsync();
                }
                else
                {
                    StatusText = "❌ Could not parse enrichment result";
                }
            }
            catch (Exception ex)
            {
                StatusText = $"❌ Enrichment failed: {ex.Message}";
            }
        }

        private async Task CheckConnectivityAsync()
        {
            try
            {
                var json = await _python.CheckConnectivityAsync();
                var result = JsonConvert.DeserializeObject<dynamic>(json);
                IsOnline = result?.online == true;
            }
            catch
            {
                IsOnline = false;
            }
        }

        // ─── INotifyPropertyChanged ──────────────────

        public event PropertyChangedEventHandler? PropertyChanged;
        protected void OnPropertyChanged([CallerMemberName] string? name = null)
            => PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
    }

    // ─── RelayCommand ────────────────────────────────

    public class RelayCommand : ICommand
    {
        private readonly Func<object?, Task> _execute;
        private readonly Func<object?, bool>? _canExecute;

        public RelayCommand(Func<object?, Task> execute, Func<object?, bool>? canExecute = null)
        {
            _execute = execute;
            _canExecute = canExecute;
        }

        public bool CanExecute(object? parameter) => _canExecute?.Invoke(parameter) ?? true;
        public async void Execute(object? parameter) => await _execute(parameter);

        public event EventHandler? CanExecuteChanged
        {
            add => CommandManager.RequerySuggested += value;
            remove => CommandManager.RequerySuggested -= value;
        }
    }
}
