using Microsoft.Extensions.Options;
using RabbitMQ.Client;

namespace NexusMesh.Worker.RabbitMq;

public sealed class RabbitMqConnectionManager : IRabbitMqConnectionManager
{
    private readonly object _syncRoot = new();
    private readonly RabbitMqOptions _options;
    private IConnection? _connection;
    private bool _disposed;

    public RabbitMqConnectionManager(IOptions<RabbitMqOptions> options)
    {
        _options = options.Value;
    }

    public IModel CreateChannel()
    {
        ThrowIfDisposed();
        var connection = GetOrCreateConnection();
        var channel = connection.CreateModel();

        // Backpressure: process one message at a time per worker instance.
        channel.BasicQos(prefetchSize: 0, prefetchCount: 1, global: false);
        return channel;
    }

    private IConnection GetOrCreateConnection()
    {
        lock (_syncRoot)
        {
            ThrowIfDisposed();

            if (_connection is { IsOpen: true })
            {
                return _connection;
            }

            _connection?.Dispose();

            var factory = new ConnectionFactory
            {
                HostName = _options.Host,
                Port = _options.Port,
                UserName = _options.Username,
                Password = _options.Password,
                VirtualHost = _options.VirtualHost,
                DispatchConsumersAsync = true,
                AutomaticRecoveryEnabled = true,
                NetworkRecoveryInterval = TimeSpan.FromSeconds(5),
            };

            _connection = factory.CreateConnection();
            return _connection;
        }
    }

    private void ThrowIfDisposed()
    {
        if (_disposed)
        {
            throw new ObjectDisposedException(nameof(RabbitMqConnectionManager));
        }
    }

    public void Dispose()
    {
        lock (_syncRoot)
        {
            if (_disposed)
            {
                return;
            }

            _disposed = true;

            if (_connection is not null)
            {
                if (_connection.IsOpen)
                {
                    _connection.Close();
                }

                _connection.Dispose();
                _connection = null;
            }
        }
    }
}
