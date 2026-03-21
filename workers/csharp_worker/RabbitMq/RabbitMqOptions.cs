namespace NexusMesh.Worker.RabbitMq;

public sealed class RabbitMqOptions
{
    public const string SectionName = "RabbitMq";

    public string Host { get; init; } = "localhost";
    public int Port { get; init; } = 5672;
    public string Username { get; init; } = "guest";
    public string Password { get; init; } = "guest";
    public string VirtualHost { get; init; } = "/";
    public string TaskQueue { get; init; } = "task_queue";
    public string ResultsQueue { get; init; } = "results_queue";
    public string StatusEventsQueue { get; init; } = "status_events_queue";
    public int HeavyComputationDelayMs { get; init; } = 2500;
}
