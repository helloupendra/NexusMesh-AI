using RabbitMQ.Client;

namespace NexusMesh.Worker.RabbitMq;

public interface IRabbitMqConnectionManager : IDisposable
{
    IModel CreateChannel();
}
