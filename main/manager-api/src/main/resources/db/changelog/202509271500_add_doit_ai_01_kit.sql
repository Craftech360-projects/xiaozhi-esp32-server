-- Add doit-ai-01-kit firmware type to dictionary if it doesn't exist
INSERT INTO `sys_dict_data` (`id`, `dict_type_id`, `dict_label`, `dict_value`, `sort`, `remark`, `creator`, `create_date`)
SELECT 101055, 101, 'doit-ai-01-kit', 'doit-ai-01-kit', 1, 'DoIT AI 01 Kit firmware type', NULL, NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM `sys_dict_data` WHERE `dict_type_id` = 101 AND `dict_value` = 'doit-ai-01-kit'
);