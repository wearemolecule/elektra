# schema definitions
create_prices = {
  "type": "object",
  "properties": {
    "flow_date": {"type":"string"},
    "ticker": {"type":"string"},
    "node": {"type":"string"},
    "iso": {"type":"string"},
    "block": {"type":"string"},
    "frequency": {"type":"string"},
    "data": {
      "type": "array",
      "properties": {
        "flow_date": {"type":"string"},
        "hour_ending": {"type":"number"},
        "price": {"type":"number"}
      }
    }
  },
  "required": ["flow_date", "ticker", "node", "iso", "block", "frequency", "data"]
}

scrub_prices = {
  "type": "object",
  "properties": {
    "flow_date": {"type":"string"},
    "ticker": {"type":"string"},
    "node": {"type":"string"},
    "iso": {"type":"string"},
    "data": {
      "type": "array",
      "properties": {
        "flow_date": {"type":"string"},
        "hour_ending": {"type":"number"},
        "price": {"type":"number"}
      }
    }
  },
  "required": ["flow_date", "ticker", "node", "iso", "data"]
}