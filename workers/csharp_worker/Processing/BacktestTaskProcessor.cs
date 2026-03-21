using NexusMesh.Worker.RabbitMq;
using Microsoft.Extensions.Options;

namespace NexusMesh.Worker.Processing;

public sealed class BacktestTaskProcessor : ITaskProcessor
{
    private readonly RabbitMqOptions _options;

    public string TaskType => "backtest";

    public BacktestTaskProcessor(IOptions<RabbitMqOptions> options)
    {
        _options = options.Value;
    }

    public async Task<Dictionary<string, object?>> ProcessAsync(TaskMessage message, CancellationToken token)
    {
        await Task.Delay(_options.HeavyComputationDelayMs, token);

        return new Dictionary<string, object?>
        {
            ["summary"] = "Backtest complete",
            ["request"] = message.Request,
            ["latency_ms"] = _options.HeavyComputationDelayMs,
            ["engine"] = "csharp-worker",
        };
    }
}
