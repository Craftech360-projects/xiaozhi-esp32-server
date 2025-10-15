-- Add server.ota for configuring OTA address

delete from sys_params where id = 100;
delete from sys_params where id = 101;

delete from sys_params where id = 106;
INSERT INTO sys_params (id, param_code, param_value, value_type, param_type, remark) VALUES (106, 'server.websocket', 'null', 'string', 1, 'WebSocket address, multiple separated by semicolon');

delete from sys_params where id = 107;
INSERT INTO sys_params (id, param_code, param_value, value_type, param_type, remark) VALUES (107, 'server.ota', 'null', 'string', 1, 'OTA address');


-- Add firmware information table
CREATE TABLE IF NOT EXISTS ai_ota (
  id varchar(32) NOT NULL,
  firmware_name varchar(100) DEFAULT NULL,
  type varchar(50) DEFAULT NULL,
  version varchar(50) DEFAULT NULL,
  size bigint DEFAULT NULL,
  remark varchar(500) DEFAULT NULL,
  firmware_path varchar(255) DEFAULT NULL,
  sort INTEGER DEFAULT 0,
  updater bigint DEFAULT NULL,
  update_date TIMESTAMP DEFAULT NULL,
  creator bigint DEFAULT NULL,
  create_date TIMESTAMP DEFAULT NULL,
  PRIMARY KEY (id)
);
COMMENT ON TABLE ai_ota IS 'Firmware information table';
COMMENT ON COLUMN ai_ota.id IS 'ID';
COMMENT ON COLUMN ai_ota.firmware_name IS 'Firmware name';
COMMENT ON COLUMN ai_ota.type IS 'Firmware type';
COMMENT ON COLUMN ai_ota.version IS 'Version number';
COMMENT ON COLUMN ai_ota.size IS 'File size (bytes)';
COMMENT ON COLUMN ai_ota.remark IS 'Remark/description';
COMMENT ON COLUMN ai_ota.firmware_path IS 'Firmware path';
COMMENT ON COLUMN ai_ota.sort IS 'sort order';
COMMENT ON COLUMN ai_ota.updater IS 'updater';
COMMENT ON COLUMN ai_ota.update_date IS 'update time';
COMMENT ON COLUMN ai_ota.creator IS 'creator';
COMMENT ON COLUMN ai_ota.create_date IS 'creation time';

update ai_device set auto_update = 1;
