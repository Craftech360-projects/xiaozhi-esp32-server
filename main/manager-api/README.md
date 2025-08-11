本文档是开发类文档，如需部署小智服务端，[点击这里查看部署教程](../../README.md#%E9%83%A8%E7%BD%B2%E6%96%87%E6%A1%A3)

# 项目介绍

manager-api 该项目基于SpringBoot框架开发。

开发使用代码编辑器，导入项目时，选择`manager-api`文件夹作为项目目录

# 开发环境
JDK 21
Maven 3.8+
PostgreSQL 15+ (推荐) 或 MySQL 8.0+ (已弃用)
Redis 5.0+
Vue 3.x

## 数据库支持

### Azure PostgreSQL (默认)
项目已完全迁移至Azure PostgreSQL数据库：
- 开发环境：Azure PostgreSQL Flexible Server
- 生产环境：Azure PostgreSQL Flexible Server
- 版本要求：PostgreSQL 15+

### MySQL (已弃用)
MySQL支持已完全移除。

## Azure PostgreSQL 设置

### 快速设置
使用自动化脚本创建Azure PostgreSQL服务器：
```bash
# 运行Azure PostgreSQL设置脚本
./scripts/setup-azure-postgresql.sh
```

### 手动设置
参考详细指南：
- [Azure PostgreSQL设置指南](../../docs/azure-postgresql-setup.md)
- [数据库迁移指南](../../docs/mysql-to-postgresql-migration-runbook.md)

### 环境变量配置
```bash
export AZURE_POSTGRES_SERVER=your-server-name
export AZURE_POSTGRES_DATABASE=xiaozhi_esp32_server
export AZURE_POSTGRES_USERNAME=your-username
export AZURE_POSTGRES_PASSWORD=your-password
```

# 接口文档
启动后打开：http://localhost:8002/xiaozhi/doc.html

