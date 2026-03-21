using Microsoft.Extensions.Options;
using NexusMesh.Worker.RabbitMq;

namespace NexusMesh.Worker.Processing;

public sealed class RiskEvaluationTaskProcessor : ITaskProcessor
{
    private readonly RabbitMqOptions _options;

    public string TaskType => "risk_evaluation";

    public RiskEvaluationTaskProcessor(IOptions<RabbitMqOptions> options)
    {
        _options = options.Value;
    }

    public async Task<Dictionary<string, object?>> ProcessAsync(TaskMessage message, CancellationToken token)
    {
        await Task.Delay(_options.HeavyComputationDelayMs / 3, token);

        return new Dictionary<string, object?>
        {
            ["summary"] = "Risk evaluation complete",
            ["request"] = message.Request,
            ["risk_score"] = 0.31,
            ["max_drawdown_pct"] = 6.2,
            ["var_95_pct"] = 2.4,
            ["risk_state"] = "acceptable",
            ["engine"] = "csharp-worker",
        };
    }
}
