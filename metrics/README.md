# Metrics stack (opt-in)

```bash
docker compose --profile metrics up -d
```

- Grafana: `:3000` — anonymous read-only for the group; admin password = `GRAFANA_PASSWORD` in `.env`
- Dashboard "ZapeG — Sunucu" is pre-provisioned: online players, playtime, deaths, blocks mined, distance
- Prometheus keeps 180 days — enough for the yearly **ZapeG Ödülleri** (playtime/death totals straight off the dashboard)

**TPS panel (one manual step):** the exporter exposes Forge TPS metrics, but the exact metric name varies by exporter version. After first start run:

```bash
docker compose exec prometheus wget -qO- http://metrics-exporter:9150/metrics | grep -i tps | head
```

then add a panel with that metric in Grafana (it's saved into the provisioned dashboard, `allowUiUpdates` is on).
