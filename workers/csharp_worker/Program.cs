using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using NexusMesh.Worker.Processing;
using NexusMesh.Worker;
using NexusMesh.Worker.RabbitMq;

var builder = Host.CreateApplicationBuilder(args);

// Dependency Injection (DI) in .NET is a built-in container where you register services
// once and the runtime injects them where needed. This avoids manual object creation
// and makes testing/replacement easier.
//
// - Configure<TOptions> binds configuration (appsettings/env vars) to typed settings.
// - AddSingleton creates exactly one instance for the app lifetime.
// - AddHostedService starts a background worker managed by the Host lifecycle.
builder.Services.Configure<RabbitMqOptions>(
    builder.Configuration.GetSection(RabbitMqOptions.SectionName));

// Singleton connection manager: RabbitMQ TCP connections are expensive.
// Reusing a single connection is safer and faster than creating one per message.
builder.Services.AddSingleton<IRabbitMqConnectionManager, RabbitMqConnectionManager>();

// Multiple ITaskProcessor implementations are registered.
// The worker resolves all of them and routes by task_type.
builder.Services.AddSingleton<ITaskProcessor, BacktestTaskProcessor>();
builder.Services.AddSingleton<ITaskProcessor, SignalGenerationTaskProcessor>();
builder.Services.AddSingleton<ITaskProcessor, RiskEvaluationTaskProcessor>();

builder.Services.AddHostedService<TaskRouterWorker>();

await builder.Build().RunAsync();
