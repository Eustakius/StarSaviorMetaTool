using System.Collections.Generic;
using Newtonsoft.Json;

namespace StarSaviorTool.Models
{
    public class CharacterData
    {
        [JsonProperty("meta_version")]
        public string MetaVersion { get; set; } = "";

        [JsonProperty("tag_explanations")]
        public Dictionary<string, string> TagExplanations { get; set; } = new();

        [JsonProperty("characters")]
        public List<Character> Characters { get; set; } = new();
    }

    public class Character
    {
        [JsonProperty("name")]
        public string Name { get; set; } = "";

        [JsonProperty("role")]
        public string Role { get; set; } = "";

        [JsonProperty("tier")]
        public string Tier { get; set; } = "";

        [JsonProperty("element")]
        public string Element { get; set; } = "Unknown";

        [JsonProperty("tags")]
        public List<string> Tags { get; set; } = new();

        [JsonProperty("why_meta")]
        public List<string> WhyMeta { get; set; } = new();

        [JsonProperty("weakness")]
        public List<string> Weakness { get; set; } = new();

        [JsonProperty("source")]
        public List<string> Source { get; set; } = new();
    }

    public class TeamResult
    {
        [JsonProperty("team")]
        public List<TeamMember> Team { get; set; } = new();

        [JsonProperty("meta_score")]
        public MetaScore MetaScore { get; set; } = new();

        [JsonProperty("coverage_report")]
        public List<CoverageItem> CoverageReport { get; set; } = new();

        [JsonProperty("warnings")]
        public List<string> Warnings { get; set; } = new();

        [JsonProperty("auto_suggestions")]
        public List<Suggestion> AutoSuggestions { get; set; } = new();

        [JsonProperty("not_found")]
        public List<string> NotFound { get; set; } = new();

        [JsonProperty("team_analysis")]
        public List<TeamAnalysis> TeamAnalysis { get; set; } = new();

        [JsonProperty("synergies")]
        public List<string> Synergies { get; set; } = new();
    }

    public class TeamMember
    {
        [JsonProperty("name")]
        public string Name { get; set; } = "";

        [JsonProperty("role")]
        public string Role { get; set; } = "";

        [JsonProperty("tier")]
        public string Tier { get; set; } = "";

        [JsonProperty("element")]
        public string Element { get; set; } = "Unknown";

        [JsonProperty("tags")]
        public List<string> Tags { get; set; } = new();
    }

    public class MetaScore
    {
        [JsonProperty("total_score")]
        public int TotalScore { get; set; }

        [JsonProperty("max_score")]
        public int MaxScore { get; set; }

        [JsonProperty("percentage")]
        public double Percentage { get; set; }

        [JsonProperty("rating")]
        public string Rating { get; set; } = "";

        [JsonProperty("breakdown")]
        public List<ScoreBreakdown> Breakdown { get; set; } = new();
    }

    public class ScoreBreakdown
    {
        [JsonProperty("name")]
        public string Name { get; set; } = "";

        [JsonProperty("tier")]
        public string Tier { get; set; } = "";

        [JsonProperty("weight")]
        public int Weight { get; set; }
    }

    public class CoverageItem
    {
        [JsonProperty("category")]
        public string Category { get; set; } = "";

        [JsonProperty("tag")]
        public string Tag { get; set; } = "";

        [JsonProperty("status")]
        public string Status { get; set; } = "";

        [JsonProperty("required")]
        public bool Required { get; set; }
    }

    public class Suggestion
    {
        [JsonProperty("name")]
        public string Name { get; set; } = "";

        [JsonProperty("role")]
        public string Role { get; set; } = "";

        [JsonProperty("tier")]
        public string Tier { get; set; } = "";

        [JsonProperty("reason")]
        public string Reason { get; set; } = "";
    }

    public class TeamAnalysis
    {
        [JsonProperty("name")]
        public string Name { get; set; } = "";

        [JsonProperty("role")]
        public string Role { get; set; } = "";

        [JsonProperty("tier")]
        public string Tier { get; set; } = "";

        [JsonProperty("contributions")]
        public List<string> Contributions { get; set; } = new();

        [JsonProperty("why_meta")]
        public List<string> WhyMeta { get; set; } = new();
    }

    public class EnrichResult
    {
        [JsonProperty("status")]
        public string Status { get; set; } = "";

        [JsonProperty("online")]
        public bool Online { get; set; }

        [JsonProperty("enriched")]
        public int Enriched { get; set; }

        [JsonProperty("message")]
        public string Message { get; set; } = "";
    }
}
