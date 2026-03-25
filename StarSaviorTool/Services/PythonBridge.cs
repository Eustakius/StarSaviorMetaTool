using System;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Threading.Tasks;

namespace StarSaviorTool.Services
{
    /// <summary>
    /// Bridges C# to Python scripts via Process.Start().
    /// Passes arguments, reads JSON from stdout.
    /// </summary>
    public class PythonBridge
    {
        private readonly string _pythonPath;
        private readonly string _scriptsDir;

        public PythonBridge()
        {
            _pythonPath = "python";
            // Scripts are in ../python/ relative to the executable
            var baseDir = AppDomain.CurrentDomain.BaseDirectory;
            _scriptsDir = Path.GetFullPath(Path.Combine(baseDir, "..", "..", "..", "..", "python"));

            // Fallback: check if running from project root
            if (!Directory.Exists(_scriptsDir))
            {
                _scriptsDir = Path.GetFullPath(Path.Combine(baseDir, "python"));
            }
            if (!Directory.Exists(_scriptsDir))
            {
                // Try relative to working directory
                _scriptsDir = Path.GetFullPath(Path.Combine(Directory.GetCurrentDirectory(), "python"));
            }
        }

        public async Task<string> RunScriptAsync(string scriptName, params string[] args)
        {
            var baseName = Path.GetFileNameWithoutExtension(scriptName);
            var exePath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "python_bin", $"{baseName}.exe");
            var scriptPath = Path.Combine(_scriptsDir, scriptName);

            var psi = new ProcessStartInfo
            {
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true,
                StandardOutputEncoding = Encoding.UTF8,
                StandardErrorEncoding = Encoding.UTF8
            };

            var arguments = new StringBuilder();
            
            // If the bundled .exe exists, run that wrapper directly without Python!
            if (File.Exists(exePath))
            {
                psi.FileName = exePath;
                foreach (var arg in args)
                {
                    arguments.Append($" \"{arg}\"");
                }
            }
            else
            {
                // Fallback to running via Python interpreter in dev mode
                if (!File.Exists(scriptPath))
                {
                    return $"{{\"error\": \"Script not found: {scriptPath}\"}}";
                }
                psi.FileName = _pythonPath;
                arguments.Append($"\"{scriptPath}\"");
                foreach (var arg in args)
                {
                    arguments.Append($" \"{arg}\"");
                }
            }

            psi.Arguments = arguments.ToString();

            try
            {
                using var process = Process.Start(psi);
                if (process == null)
                    return "{\"error\": \"Failed to start Python process\"}";

                var output = await process.StandardOutput.ReadToEndAsync();
                var error = await process.StandardError.ReadToEndAsync();

                await process.WaitForExitAsync();

                if (process.ExitCode != 0 && !string.IsNullOrEmpty(error))
                {
                    return $"{{\"error\": \"Python error: {EscapeJson(error)}\"}}";
                }

                return string.IsNullOrWhiteSpace(output)
                    ? "{\"error\": \"Empty output from Python script\"}"
                    : output;
            }
            catch (Exception ex)
            {
                return $"{{\"error\": \"Exception: {EscapeJson(ex.Message)}\"}}";
            }
        }

        public async Task<string> GetAllCharactersAsync()
            => await RunScriptAsync("data_engine.py");

        public async Task<string> FilterCharactersAsync(string? tier = null, string? role = null, string? element = null)
        {
            var args = new System.Collections.Generic.List<string>();
            if (!string.IsNullOrEmpty(tier)) { args.Add("--tier"); args.Add(tier); }
            if (!string.IsNullOrEmpty(role)) { args.Add("--role"); args.Add(role); }
            if (!string.IsNullOrEmpty(element)) { args.Add("--element"); args.Add(element); }
            return await RunScriptAsync("data_engine.py", args.ToArray());
        }

        public Task<string> BuildTeamAsync(bool autoFix, bool analyze, string focus, params string[] characters)
        {
            var args = new List<string>();
            if (autoFix) args.Add("--auto-fix");
            if (analyze) args.Add("--analyze");
            if (!string.IsNullOrEmpty(focus))
            {
                args.Add("--focus");
                args.Add(focus);
            }
            args.AddRange(characters.Select(c => $"\"{c}\""));
            return RunScriptAsync("team_builder.py", args.ToArray());
        }

        public async Task<string> ScoreTeamAsync(params string[] characterNames)
            => await RunScriptAsync("meta_scorer.py", characterNames);

        public async Task<string> CheckConnectivityAsync()
            => await RunScriptAsync("web_enricher.py", "--check");

        public async Task<string> EnrichDataAsync(bool dryRun = false)
        {
            var args = new System.Collections.Generic.List<string>();
            if (dryRun) args.Add("--dry-run");
            return await RunScriptAsync("web_enricher.py", args.ToArray());
        }

        public async Task<string> ValidateDataAsync()
            => await RunScriptAsync("web_enricher.py", "--validate");

        private static string EscapeJson(string s)
            => s.Replace("\\", "\\\\").Replace("\"", "\\\"").Replace("\n", "\\n").Replace("\r", "");
    }
}
