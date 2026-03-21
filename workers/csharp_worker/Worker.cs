using System.Text;
using System.Text.Json;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using NexusMesh.Worker.Processing;
using NexusMesh.Worker.RabbitMq;
using RabbitMQ.Client;
using RabbitMQ.Client.Events;

namespace NexusMesh.Worker;

public sealed class TaskRouterWorker : BackgroundService
{
    private readonly ILogger<TaskRouterWorker> _logger;
    private readonly RabbitMqOptions _options;
    private readonly IReadOnlyDictionary<string, ITaskProcessor> _processors;
    private readonly IRabbitMqConnectionManager _connectionManager;
    private IModel? _channel;

    public TaskRouterWorker(
        ILogger<TaskRouterWorker> logger,
        IOptions<RabbitMqOptions> options,
        IEnumerable<ITaskProcessor> processors,
        IRabbitMqConnectionManager connectionManager)
    {
        _logger = logger;
        _options = options.Value;
        _processors = processors.ToDictionary(
            processor => processor.TaskType,
            processor => processor,
            StringComparer.OrdinalIgnoreCase);
        _connectionManager = connectionManager;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        _channel = _connectionManager.CreateChannel();

        _channel.QueueDeclare(
            queue: _options.TaskQueue,
            durable: true,
            exclusive: false,
            autoDelete: false,
            arguments: null);

        _channel.QueueDeclare(
            queue: _options.ResultsQueue,
            durable: true,
            exclusive: false,
            autoDelete: false,
            arguments: null);

        var consumer = new AsyncEventingBasicConsumer(_channel);

        // Why Task and not void?
        // - async Task lets RabbitMQ/.NET observe completion and exceptions.
        // - async void fire-and-forget handlers can swallow failures and make retries harder.
        // AsyncEventingBasicConsumer specifically supports Task-returning handlers.
        consumer.Received += async (_, eventArgs) =>
            await HandleMessageAsync(eventArgs, stoppingToken);

        _channel.BasicConsume(
            queue: _options.TaskQueue,
            autoAck: false,
            consumer: consumer);

        _logger.LogInformation(
            "Worker consuming queue '{QueueName}' with handlers: {Handlers}",
            _options.TaskQueue,
            string.Join(", ", _processors.Keys));

        while (!stoppingToken.IsCancellationRequested)
        {
            await Task.Delay(TimeSpan.FromSeconds(1), stoppingToken);
        }
    }

    private async Task HandleMessageAsync(BasicDeliverEventArgs eventArgs, CancellationToken token)
    {
        if (_channel is null)
        {
            throw new InvalidOperationException("RabbitMQ channel is not initialized.");
        }

        TaskMessage? taskMessage;

        try
        {
            var json = Encoding.UTF8.GetString(eventArgs.Body.ToArray());
            taskMessage = JsonSerializer.Deserialize<TaskMessage>(json);

            if (taskMessage is null || string.IsNullOrWhiteSpace(taskMessage.TaskId))
            {
                _logger.LogWarning("Invalid message payload received. Dropping message.");
                _channel.BasicAck(eventArgs.DeliveryTag, multiple: false);
                return;
            }
        }
        catch (JsonException ex)
        {
            _logger.LogError(ex, "Failed to deserialize task message.");
            _channel.BasicAck(eventArgs.DeliveryTag, multiple: false);
            return;
        }

        try
        {
            var taskType = NormalizeTaskType(taskMessage.TaskType);
            if (_processors.TryGetValue(taskType, out var processor) is false)
            {
                PublishResult(new TaskResultMessage
                {
                    TaskId = taskMessage.TaskId,
                    TaskType = taskType,
                    Status = "FAILED",
                    Result = null,
                    Error = $"Unsupported task_type '{taskType}'. Supported: {string.Join(", ", _processors.Keys)}",
                }, correlationId: taskMessage.TaskId);

                _channel.BasicAck(eventArgs.DeliveryTag, multiple: false);
                return;
            }

            _logger.LogInformation(
                "Processing task {TaskId} (type: {TaskType}): {Request}",
                taskMessage.TaskId,
                taskType,
                taskMessage.Request);

            var routedResult = await processor.ProcessAsync(taskMessage, token);

            var result = new TaskResultMessage
            {
                TaskId = taskMessage.TaskId,
                TaskType = taskType,
                Status = "COMPLETED",
                Result = routedResult,
                Error = null,
            };

            PublishResult(result, correlationId: taskMessage.TaskId);
            _channel.BasicAck(eventArgs.DeliveryTag, multiple: false);

            _logger.LogInformation("Task {TaskId} completed", taskMessage.TaskId);
        }
        catch (OperationCanceledException)
        {
            _logger.LogWarning("Task {TaskId} cancelled by shutdown", taskMessage.TaskId);
            _channel.BasicNack(eventArgs.DeliveryTag, multiple: false, requeue: true);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Task {TaskId} failed", taskMessage.TaskId);

            var failure = new TaskResultMessage
            {
                TaskId = taskMessage.TaskId,
                TaskType = NormalizeTaskType(taskMessage.TaskType),
                Status = "FAILED",
                Result = null,
                Error = ex.Message,
            };

            PublishResult(failure, correlationId: taskMessage.TaskId);
            _channel.BasicAck(eventArgs.DeliveryTag, multiple: false);
        }
    }

    private void PublishResult(TaskResultMessage result, string correlationId)
    {
        if (_channel is null)
        {
            throw new InvalidOperationException("RabbitMQ channel is not initialized.");
        }

        var body = Encoding.UTF8.GetBytes(JsonSerializer.Serialize(result));
        var props = _channel.CreateBasicProperties();
        props.ContentType = "application/json";
        props.DeliveryMode = 2;
        props.CorrelationId = correlationId;

        _channel.BasicPublish(
            exchange: string.Empty,
            routingKey: _options.ResultsQueue,
            basicProperties: props,
            body: body);
    }

    private static string NormalizeTaskType(string? taskType)
    {
        return string.IsNullOrWhiteSpace(taskType) ? "backtest" : taskType.Trim().ToLowerInvariant();
    }

    public override void Dispose()
    {
        _channel?.Close();
        _channel?.Dispose();
        base.Dispose();
    }
}
