# Telematics domain → `prod_telematics`
Owner: Connected Vehicle / IoT team. Primary ingestion: **Event Hubs streaming**.
- bronze/ — `stream_telemetry_bronze.py` (Structured Streaming from Event Hubs)
- silver/ — `trip_sessionization.py` (Lakeflow + expectations + quarantine), `dim_driver_scd2.py`
- gold/   — `build_fact_trip.py` (+ fact_telemetry_event, fact_trip_summary_daily, mart_driver_risk_score)
- docs/   — recall letters / vehicle manuals for RAG
