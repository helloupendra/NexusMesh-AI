using System.Text.Json.Serialization;

namespace NexusMesh.Worker.RabbitMq;

public sealed class TaskMessage
{
    [JsonPropertyName("task_id")]
    public string TaskId { get; init; } = string.Empty;

    [JsonPropertyName("request")]
    public string Request { get; init; } = string.Empty;

    [JsonPropertyName("task_type")]
    public string? TaskType { get; init; } = "backtest";
}
