import os
import glob
import re

def create_migration_script():
    print("Creating migration script from local Liquibase files...")

    # Find all SQL files in the changelog directory
    changelog_path = "main/manager-api/src/main/resources/db/changelog"
    sql_files = glob.glob(f"{changelog_path}/*.sql")

    # Sort files by creation date (filename)
    sql_files.sort()

    migration_content = []
    migration_content.append("-- =====================================================")
    migration_content.append("-- Complete Database Migration Script - Railway to Local Docker")
    migration_content.append("-- Generated: 2025-09-19")
    migration_content.append("-- Target Database: manager_api")
    migration_content.append("-- =====================================================\n")

    migration_content.append("SET FOREIGN_KEY_CHECKS = 0;")
    migration_content.append("SET SQL_MODE = 'NO_AUTO_VALUE_ON_ZERO';")
    migration_content.append("SET AUTOCOMMIT = 0;")
    migration_content.append("START TRANSACTION;\n")

    # Process each SQL file
    for sql_file in sql_files:
        print(f"Processing: {sql_file}")
        try:
            with open(sql_file, 'r', encoding='utf-8') as f:
                content = f.read()

                # Translate Chinese comments to English
                content = translate_comments(content)

                migration_content.append(f"-- =====================================================")
                migration_content.append(f"-- From file: {os.path.basename(sql_file)}")
                migration_content.append(f"-- =====================================================")
                migration_content.append(content)
                migration_content.append("\n")

        except Exception as e:
            print(f"Error processing {sql_file}: {e}")

    migration_content.append("-- =====================================================")
    migration_content.append("-- Insert default admin user")
    migration_content.append("-- =====================================================")
    migration_content.append("INSERT INTO `sys_user` (`id`, `username`, `password`, `super_admin`, `status`, `create_date`, `creator`)")
    migration_content.append("VALUES (1, 'admin', '$2a$10$012Kx2ba5jzqr9gLlG4MX.bnQJTjjNEacl5.I1FuqrnqyaOJkWopp', 1, 1, NOW(), 1);")
    migration_content.append("")

    migration_content.append("SET FOREIGN_KEY_CHECKS = 1;")
    migration_content.append("COMMIT;")
    migration_content.append("")
    migration_content.append("SELECT 'Database migration completed successfully!' as message;")

    # Write to migration file
    with open('railway_to_local_migration.sql', 'w', encoding='utf-8') as f:
        f.write('\n'.join(migration_content))

    print("Migration script created: railway_to_local_migration.sql")

def translate_comments(content):
    """Translate Chinese comments to English"""

    # Dictionary for common translations
    translations = {
        # Table comments
        '系统用户': 'System Users',
        '系统用户Token': 'System User Token',
        '参数管理': 'Parameter Management',
        '字典类型': 'Dictionary Type',
        '字典数据': 'Dictionary Data',
        '模型配置表': 'Model Configuration',
        '模型供应器表': 'Model Provider',
        'TTS 音色表': 'TTS Voice',
        '智能体配置模板表': 'AI Agent Template',
        '智能体配置表': 'AI Agent Configuration',
        '设备信息表': 'Device Information',
        '声纹识别表': 'Voiceprint Recognition',
        '对话历史表': 'Chat History',
        '对话信息表': 'Chat Message',

        # Field comments
        '主键': 'Primary key',
        '用户名': 'Username',
        '密码': 'Password',
        '超级管理员': 'Super administrator',
        '状态': 'Status',
        '创建时间': 'Create time',
        '更新时间': 'Update time',
        '创建者': 'Creator',
        '更新者': 'Updater',
        '用户id': 'User ID',
        '用户token': 'User token',
        '过期时间': 'Expire time',
        '参数编码': 'Parameter code',
        '参数值': 'Parameter value',
        '类型': 'Type',
        '系统参数': 'System parameter',
        '非系统参数': 'Non-system parameter',
        '备注': 'Remark',
        '字典类型': 'Dictionary type',
        '字典名称': 'Dictionary name',
        '排序': 'Sort order',
        '字典类型ID': 'Dictionary type ID',
        '字典标签': 'Dictionary label',
        '字典值': 'Dictionary value',
        '模型类型': 'Model type',
        '供应器类型': 'Provider type',
        '供应器名称': 'Provider name',
        '供应器字段列表': 'Provider field list',
        '模型编码': 'Model code',
        '模型名称': 'Model name',
        '是否默认配置': 'Is default configuration',
        '是否启用': 'Is enabled',
        '模型配置': 'Model configuration',
        '官方文档链接': 'Official documentation link',
        '音色名称': 'Voice name',
        '音色编码': 'Voice code',
        '语言': 'Language',
        '音色 Demo': 'Voice demo',
        '智能体唯一标识': 'Agent unique identifier',
        '智能体编码': 'Agent code',
        '智能体名称': 'Agent name',
        '语音识别模型标识': 'ASR model identifier',
        '语音活动检测标识': 'VAD model identifier',
        '大语言模型标识': 'LLM model identifier',
        '语音合成模型标识': 'TTS model identifier',
        '音色标识': 'Voice identifier',
        '记忆模型标识': 'Memory model identifier',
        '意图模型标识': 'Intent model identifier',
        '角色设定参数': 'System prompt',
        '语言编码': 'Language code',
        '交互语种': 'Interaction language',
        '排序权重': 'Sort weight',
        '创建者 ID': 'Creator ID',
        '更新者 ID': 'Updater ID',
        '所属用户 ID': 'User ID',
        '设备唯一标识': 'Device unique identifier',
        '关联用户 ID': 'Associated user ID',
        'MAC 地址': 'MAC address',
        '最后连接时间': 'Last connected time',
        '自动更新开关': 'Auto update switch',
        '设备硬件型号': 'Device hardware model',
        '设备别名': 'Device alias',
        '智能体 ID': 'Agent ID',
        '固件版本号': 'Firmware version',
        '声纹唯一标识': 'Voiceprint unique identifier',
        '声纹名称': 'Voiceprint name',
        '用户 ID（关联用户表）': 'User ID (linked to user table)',
        '关联智能体 ID': 'Associated agent ID',
        '关联智能体编码': 'Associated agent code',
        '关联智能体名称': 'Associated agent name',
        '声纹描述': 'Voiceprint description',
        '声纹特征向量（JSON 数组格式）': 'Voiceprint feature vector (JSON array format)',
        '关联记忆数据': 'Associated memory data',
        '对话编号': 'Chat ID',
        '用户编号': 'User ID',
        '聊天角色': 'Chat role',
        '设备编号': 'Device ID',
        '信息汇总': 'Message count',
        '对话记录唯一标识': 'Chat message unique identifier',
        '用户唯一标识': 'User unique identifier',
        '对话历史 ID': 'Chat history ID',
        '角色（用户或助理）': 'Role (user or assistant)',
        '对话内容': 'Chat content',
        '提示令牌数': 'Prompt tokens',
        '总令牌数': 'Total tokens',
        '完成令牌数': 'Completion tokens',
        '提示耗时（毫秒）': 'Prompt time (milliseconds)',
        '总耗时（毫秒）': 'Total time (milliseconds)',
        '完成耗时（毫秒）': 'Completion time (milliseconds)',

        # Common values
        '否': 'No',
        '是': 'Yes',
        '停用': 'Disabled',
        '正常': 'Normal',
        '关闭': 'Disabled',
        '开启': 'Enabled',
        '中文': 'Chinese',
        '英文': 'English',
        '默认': 'Default'
    }

    # Apply translations
    for chinese, english in translations.items():
        content = content.replace(f"'{chinese}'", f"'{english}'")
        content = content.replace(f'"{chinese}"', f'"{english}"')
        content = re.sub(rf"COMMENT\s*['\"]([^'\"]*){re.escape(chinese)}([^'\"]*)['\"]",
                        rf"COMMENT '\1{english}\2'", content)

    return content

if __name__ == "__main__":
    create_migration_script()