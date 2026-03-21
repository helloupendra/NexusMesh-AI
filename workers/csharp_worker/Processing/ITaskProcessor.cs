using NexusMesh.Worker.RabbitMq;

namespace NexusMesh.Worker.Processing;

public interface ITaskProcessor
{
    string TaskType { get; }

    Task<Dictionary<string, object?>> ProcessAsync(TaskMessage message, CancellationToken token);
}
