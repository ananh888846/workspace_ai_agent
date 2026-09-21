CREATE TABLE tool_capabilities (
  tool_id UUID NOT NULL,
  capability VARCHAR(100) NOT NULL,
  resource VARCHAR(100),
  action VARCHAR(100),
  requires_account BOOLEAN NOT NULL DEFAULT false,
  PRIMARY KEY (tool_id, capability),
  FOREIGN KEY (tool_id) REFERENCES tools(id) ON DELETE CASCADE
);

CREATE INDEX idx_tool_capabilities_capability_enabled
  ON tool_capabilities (capability, requires_account);
