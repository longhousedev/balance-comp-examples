# Submit Run

```
curl -i -X POST http://balance-competition.tabletopgames.ai/api/submit_run 
    -H "Content-Type: application/json" 
    -d '{"game": "Dominion", "params": {"HAND_SIZE": 3}, "api_key": "7079cc2c-2ced-4031-ba9a-6eac68945c22", "run_type":"fast"}'
```

# Check status

```
curl -i -X GET http://balance-competition.tabletopgames.ai/api/query_run?id=13
```

# Retrieve Result

```
curl -i -X GET http://balance-competition.tabletopgames.ai/api/retrieve_result?id=13&api_key=7079cc2c-2ced-4031-ba9a-6eac68945c22
```