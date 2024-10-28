# AZDNS
> 一个基于Python Flask开发的二级域名分发系统

### 1.安装
#### 1.1 下载源代码
通过git工具或在GitHub下载源代码
#### 1.2 安装依赖库
`pip install -r requirements.txt`
> 执行命令前，请先部署好Python环境（版本>=3.6)
#### 1.3 创建数据表
在项目目录下执行：`flask init-db`

稍等片刻，数据表将被自动创建
####  1.4 安装完毕
此刻，您可访问 localhost:5000 查看服务运行状态

### 2.配置
#### 2.1 创建管理员账号
在项目目录下执行：`flask create-admin`

然后按提示输入信息即可
