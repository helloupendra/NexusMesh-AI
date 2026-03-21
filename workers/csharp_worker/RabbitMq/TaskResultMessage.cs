using System.Text.Json.Serialization;

namespace NexusMesh.Worker.RabbitMq;

public sealed class TaskResultMessage
{
    [JsonPropertyName("task_id")]
    public string TaskId { get; init; } = string.Empty;

    [JsonPropertyName("status")]
    public string Status { get; init; } = "COMPLETED";

    [JsonPropertyName("task_type")]
    public string TaskType { get; init; } = "backtest";

    [JsonPropertyName("result")]
    public Dictionary<string, object?>? Result { get; init; }

    [JsonPropertyName("error")]
    public string? Error { get; init; }
}
