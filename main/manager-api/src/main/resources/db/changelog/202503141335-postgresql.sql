-- PostgreSQL version of 202503141335.sql
-- System tables creation for PostgreSQL

DROP TABLE IF EXISTS sys_user CASCADE;
DROP TABLE IF EXISTS sys_params CASCADE;
DROP TABLE IF EXISTS sys_user_token CASCADE;
DROP TABLE IF EXISTS sys_dict_type CASCADE;
DROP TABLE IF EXISTS sys_dict_data CASCADE;

-- 系统用户
CREATE TABLE sys_user (
  id bigint NOT NULL,
  username varchar(50) NOT NULL,
  password varchar(100),
  super_admin smallint, -- Changed from tinyint unsigned to smallint
  status smallint, -- Changed from tinyint to smallint
  create_date timestamp, -- Changed from datetime to timestamp
  updater bigint,
  creator bigint,
  update_date timestamp, -- Changed from datetime to timestamp
  PRIMARY KEY (id),
  CONSTRAINT uk_username UNIQUE (username)
);

-- Add comments for PostgreSQL
COMMENT ON TABLE sys_user IS '系统用户';
COMMENT ON COLUMN sys_user.id IS 'id';
COMMENT ON COLUMN sys_user.username IS '用户名';
COMMENT ON COLUMN sys_user.password IS '密码';
COMMENT ON COLUMN sys_user.super_admin IS '超级管理员   0：否   1：是';
COMMENT ON COLUMN sys_user.status IS '状态  0：停用   1：正常';
COMMENT ON COLUMN sys_user.create_date IS '创建时间';
COMMENT ON COLUMN sys_user.updater IS '更新者';
COMMENT ON COLUMN sys_user.creator IS '创建者';
COMMENT ON COLUMN sys_user.update_date IS '更新时间';

-- 系统用户Token
CREATE TABLE sys_user_token (
  id bigint NOT NULL,
  user_id bigint NOT NULL,
  token varchar(100) NOT NULL,
  expire_date timestamp, -- Changed from datetime to timestamp
  update_date timestamp, -- Changed from datetime to timestamp
  create_date timestamp, -- Changed from datetime to timestamp
  PRIMARY KEY (id),
  CONSTRAINT uk_user_id UNIQUE (user_id),
  CONSTRAINT uk_token UNIQUE (token)
);

COMMENT ON TABLE sys_user_token IS '系统用户Token';
COMMENT ON COLUMN sys_user_token.id IS 'id';
COMMENT ON COLUMN sys_user_token.user_id IS '用户id';
COMMENT ON COLUMN sys_user_token.token IS '用户token';
COMMENT ON COLUMN sys_user_token.expire_date IS '过期时间';
COMMENT ON COLUMN sys_user_token.update_date IS '更新时间';
COMMENT ON COLUMN sys_user_token.create_date IS '创建时间';

-- 参数管理
CREATE TABLE sys_params (
  id bigint NOT NULL,
  param_code varchar(32),
  param_value varchar(2000),
  param_type smallint DEFAULT 1, -- Changed from tinyint unsigned to smallint
  remark varchar(200),
  creator bigint,
  create_date timestamp, -- Changed from datetime to timestamp
  updater bigint,
  update_date timestamp, -- Changed from datetime to timestamp
  PRIMARY KEY (id),
  CONSTRAINT uk_param_code UNIQUE (param_code)
);

COMMENT ON TABLE sys_params IS '参数管理';
COMMENT ON COLUMN sys_params.id IS 'id';
COMMENT ON COLUMN sys_params.param_code IS '参数编码';
COMMENT ON COLUMN sys_params.param_value IS '参数值';
COMMENT ON COLUMN sys_params.param_type IS '类型   0：系统参数   1：非系统参数';
COMMENT ON COLUMN sys_params.remark IS '备注';
COMMENT ON COLUMN sys_params.creator IS '创建者';
COMMENT ON COLUMN sys_params.create_date IS '创建时间';
COMMENT ON COLUMN sys_params.updater IS '更新者';
COMMENT ON COLUMN sys_params.update_date IS '更新时间';

-- 字典类型
CREATE TABLE sys_dict_type (
    id bigint NOT NULL,
    dict_type varchar(100) NOT NULL,
    dict_name varchar(255) NOT NULL,
    remark varchar(255),
    sort integer, -- Changed from int unsigned to integer
    creator bigint,
    create_date timestamp, -- Changed from datetime to timestamp
    updater bigint,
    update_date timestamp, -- Changed from datetime to timestamp
    PRIMARY KEY (id),
    CONSTRAINT uk_dict_type UNIQUE (dict_type)
);

COMMENT ON TABLE sys_dict_type IS '字典类型';
COMMENT ON COLUMN sys_dict_type.id IS 'id';
COMMENT ON COLUMN sys_dict_type.dict_type IS '字典类型';
COMMENT ON COLUMN sys_dict_type.dict_name IS '字典名称';
COMMENT ON COLUMN sys_dict_type.remark IS '备注';
COMMENT ON COLUMN sys_dict_type.sort IS '排序';
COMMENT ON COLUMN sys_dict_type.creator IS '创建者';
COMMENT ON COLUMN sys_dict_type.create_date IS '创建时间';
COMMENT ON COLUMN sys_dict_type.updater IS '更新者';
COMMENT ON COLUMN sys_dict_type.update_date IS '更新时间';

-- 字典数据
CREATE TABLE sys_dict_data (
    id bigint NOT NULL,
    dict_type_id bigint NOT NULL,
    dict_label varchar(255) NOT NULL,
    dict_value varchar(255),
    remark varchar(255),
    sort integer, -- Changed from int unsigned to integer
    creator bigint,
    create_date timestamp, -- Changed from datetime to timestamp
    updater bigint,
    update_date timestamp, -- Changed from datetime to timestamp
    PRIMARY KEY (id),
    CONSTRAINT uk_dict_type_value UNIQUE (dict_type_id, dict_value)
);

-- Create index for sort column
CREATE INDEX idx_sort ON sys_dict_data (sort);

COMMENT ON TABLE sys_dict_data IS '字典数据';
COMMENT ON COLUMN sys_dict_data.id IS 'id';
COMMENT ON COLUMN sys_dict_data.dict_type_id IS '字典类型ID';
COMMENT ON COLUMN sys_dict_data.dict_label IS '字典标签';
COMMENT ON COLUMN sys_dict_data.dict_value IS '字典值';
COMMENT ON COLUMN sys_dict_data.remark IS '备注';
COMMENT ON COLUMN sys_dict_data.sort IS '排序';
COMMENT ON COLUMN sys_dict_data.creator IS '创建者';
COMMENT ON COLUMN sys_dict_data.create_date IS '创建时间';
COMMENT ON COLUMN sys_dict_data.updater IS '更新者';
COMMENT ON COLUMN sys_dict_data.update_date IS '更新时间';