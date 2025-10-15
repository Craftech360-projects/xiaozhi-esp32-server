DROP TABLE IF EXISTS sys_user;
DROP TABLE IF EXISTS sys_params;
DROP TABLE IF EXISTS sys_user_token;
DROP TABLE IF EXISTS sys_dict_type;
DROP TABLE IF EXISTS sys_dict_data;

-- System user
CREATE TABLE sys_user (
  id bigint NOT NULL,
  username varchar(50) NOT NULL,
  password varchar(100),
  super_admin SMALLINT,
  status SMALLINT,
  create_date TIMESTAMP,
  updater bigint,
  creator bigint,
  update_date TIMESTAMP,
  PRIMARY KEY (id),
  CONSTRAINT uk_username UNIQUE (username)
);
COMMENT ON TABLE sys_user IS 'System user';
COMMENT ON COLUMN sys_user.id IS 'id';
COMMENT ON COLUMN sys_user.username IS 'username';
COMMENT ON COLUMN sys_user.password IS 'password';
COMMENT ON COLUMN sys_user.super_admin IS 'Super administrator 0: no 1: yes';
COMMENT ON COLUMN sys_user.status IS 'Status 0: disabled 1: normal';
COMMENT ON COLUMN sys_user.create_date IS 'creation time';
COMMENT ON COLUMN sys_user.updater IS 'updater';
COMMENT ON COLUMN sys_user.creator IS 'creator';
COMMENT ON COLUMN sys_user.update_date IS 'update time';

-- System user token
CREATE TABLE sys_user_token (
  id bigint NOT NULL,
  user_id bigint NOT NULL,
  token varchar(100) NOT NULL,
  expire_date TIMESTAMP,
  update_date TIMESTAMP,
  create_date TIMESTAMP,
  PRIMARY KEY (id),
  CONSTRAINT uk_user_id UNIQUE (user_id),
  CONSTRAINT uk_token UNIQUE (token)
);
COMMENT ON TABLE sys_user_token IS 'System user token';
COMMENT ON COLUMN sys_user_token.id IS 'id';
COMMENT ON COLUMN sys_user_token.user_id IS 'user id';
COMMENT ON COLUMN sys_user_token.token IS 'user token';
COMMENT ON COLUMN sys_user_token.expire_date IS 'expiration time';
COMMENT ON COLUMN sys_user_token.update_date IS 'update time';
COMMENT ON COLUMN sys_user_token.create_date IS 'creation time';

-- Parameter management
create table sys_params
(
  id                   bigint NOT NULL,
  param_code           varchar(32),
  param_value          varchar(2000),
  param_type           SMALLINT default 1,
  remark               varchar(200),
  creator              bigint,
  create_date          TIMESTAMP,
  updater              bigint,
  update_date          TIMESTAMP,
  PRIMARY KEY (id),
  CONSTRAINT uk_param_code UNIQUE (param_code)
);
COMMENT ON TABLE sys_params IS 'Parameter management';
COMMENT ON COLUMN sys_params.id IS 'id';
COMMENT ON COLUMN sys_params.param_code IS 'parameter code';
COMMENT ON COLUMN sys_params.param_value IS 'parameter value';
COMMENT ON COLUMN sys_params.param_type IS 'Type 0: system parameter 1: non-system parameter';
COMMENT ON COLUMN sys_params.remark IS 'remark';
COMMENT ON COLUMN sys_params.creator IS 'creator';
COMMENT ON COLUMN sys_params.create_date IS 'creation time';
COMMENT ON COLUMN sys_params.updater IS 'updater';
COMMENT ON COLUMN sys_params.update_date IS 'update time';

-- Dictionary type
create table sys_dict_type
(
    id                   bigint NOT NULL,
    dict_type            varchar(100) NOT NULL,
    dict_name            varchar(255) NOT NULL,
    remark               varchar(255),
    sort                 INTEGER,
    creator              bigint,
    create_date          TIMESTAMP,
    updater              bigint,
    update_date          TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT uk_dict_type UNIQUE (dict_type)
);
COMMENT ON TABLE sys_dict_type IS 'Dictionary type';
COMMENT ON COLUMN sys_dict_type.id IS 'id';
COMMENT ON COLUMN sys_dict_type.dict_type IS 'dictionary type';
COMMENT ON COLUMN sys_dict_type.dict_name IS 'dictionary name';
COMMENT ON COLUMN sys_dict_type.remark IS 'remark';
COMMENT ON COLUMN sys_dict_type.sort IS 'sort order';
COMMENT ON COLUMN sys_dict_type.creator IS 'creator';
COMMENT ON COLUMN sys_dict_type.create_date IS 'creation time';
COMMENT ON COLUMN sys_dict_type.updater IS 'updater';
COMMENT ON COLUMN sys_dict_type.update_date IS 'update time';

-- Dictionary data
create table sys_dict_data
(
    id                   bigint NOT NULL,
    dict_type_id         bigint NOT NULL,
    dict_label           varchar(255) NOT NULL,
    dict_value           varchar(255),
    remark               varchar(255),
    sort                 INTEGER,
    creator              bigint,
    create_date          TIMESTAMP,
    updater              bigint,
    update_date          TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT uk_dict_type_value UNIQUE (dict_type_id, dict_value)
);
CREATE INDEX idx_sort ON sys_dict_data(sort);
COMMENT ON TABLE sys_dict_data IS 'Dictionary data';
COMMENT ON COLUMN sys_dict_data.id IS 'id';
COMMENT ON COLUMN sys_dict_data.dict_type_id IS 'dictionary type ID';
COMMENT ON COLUMN sys_dict_data.dict_label IS 'dictionary label';
COMMENT ON COLUMN sys_dict_data.dict_value IS 'dictionary value';
COMMENT ON COLUMN sys_dict_data.remark IS 'remark';
COMMENT ON COLUMN sys_dict_data.sort IS 'sort order';
COMMENT ON COLUMN sys_dict_data.creator IS 'creator';
COMMENT ON COLUMN sys_dict_data.create_date IS 'creation time';
COMMENT ON COLUMN sys_dict_data.updater IS 'updater';
COMMENT ON COLUMN sys_dict_data.update_date IS 'update time';
