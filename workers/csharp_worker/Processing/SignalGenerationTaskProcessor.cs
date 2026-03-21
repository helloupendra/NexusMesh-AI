using Microsoft.Extensions.Options;
using NexusMesh.Worker.RabbitMq;

namespace NexusMesh.Worker.Processing;

public sealed class SignalGenerationTaskProcessor : ITaskProcessor
{
    private readonly RabbitMqOptions _options;

    public string TaskType => "signal_generation";

    public SignalGenerationTaskProcessor(IOptions<RabbitMqOptions> options)
    {
        _options = options.Value;
    }

    public async Task<Dictionary<string, object?>> ProcessAsync(TaskMessage message, CancellationToken token)
    {
        await Task.Delay(_options.HeavyComputationDelayMs / 2, token);

        return new Dictionary<string, object?>
        {
            ["summary"] = "Signal generation complete",
            ["request"] = message.Request,
            ["signal"] = "BUY",
            ["confidence"] = 0.62,
            ["indicators"] = new[] { "RSI(14)", "BollingerBands(20,2)" },
            ["engine"] = "csharp-worker",
        };
    }
}
