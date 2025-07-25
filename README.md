# ClassRoll Pro - 课堂点名插件

![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![License](https://img.shields.io/badge/license-AFN--License%202.0-green.svg)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/H2O-ME/ClassRoll-Pro)

## 项目介绍

ClassRoll Pro 是一个在Class Widgets上运行的的课堂随机点名插件，支持自定义学生名单和概率设置。提供用于触发选择的浮动 UI 按钮和用于控制选择可能性的可配置概率系统。

### 主要特性

- 📋 **名单管理**：轻松添加、编辑和删除学生信息
- 🎯 **浮动 UI**：标有“点名”的持久页面浮动按钮，快捷方便
- ⚙️ **概率控制**：为每个学生设置1-5级的被点中概率
- 📅 **时间显示**：当不主动执行点名时，小部件会显示当前时间和日期，使其成为一个两用组件，即使在不需要点名功能时也能提供实用性。

### 项目结构

```
.
├── ClassWidgets/          # 自定义UI组件
│   └── base.py
├── names.txt             # 学生名单配置文件
├── plugin.json           # 插件配置文件
├── main.py               # 主程序入口
├── settings.ui           # 设置界面设计文件
└── README.md             # 项目说明文档
```
<img width="1686" height="324" alt="image" src="https://github.com/user-attachments/assets/5baa59e8-8550-49c7-8dd2-156820eb44dd" />

### 系统架构概述
<img width="1680" height="800" alt="image" src="https://github.com/user-attachments/assets/39037b4d-67ec-4db2-ac8d-c3ce766c6104" />

### 核心组件交互
<img width="1622" height="747" alt="image" src="https://github.com/user-attachments/assets/30f14f03-7a6d-4fad-a470-8996a5e882da" />


## 安装与运行

1. 下载本项目
2. 将文件放置在 Class Widgets 的 plugins 文件夹
3. 在“设置”中启用此插件
4. 重新启动 Class Widgets
5. 在小组件页面添加小组件
6. 开始使用

## 使用教程

### 1. 初始配置设置

#### 配置学生列表

1. 使用文本编辑器打开项目根目录下的 `names.txt` 文件，该文件包含学生姓名和概率级别
2. ClassRoll Pro 以简单的基于文本的格式将学生信息存储在文件中。每个学生条目都遵循逗号分隔的结构，每行遵循格式 StudentName，ProbabilityLevel
   - 例如：`张三,3` 或 `李四,5`（概率等级 3 的张三）（概率等级为 5 的李四 ）
   - 默认情况下，学生被分配概率级别 3（正常）
3. 文件保存于插件根目录下，重启Class Widgets会自动重新加载名单

### 2. 开始点名

1. 类控件启动后，屏幕右下角会出现一个标有“点名”的浮动按钮
2. 点击悬浮按钮触发随机点名，小组件将显示过程
3. 系统会随机选择一名学生并显示选中动画，10 秒后小组件自动返回时间/日期显示


### 3. 进阶使用

#### 自定义特定学生概率

系统支持5个概率等级：
<img width="870" height="283" alt="image" src="https://github.com/user-attachments/assets/9397a1c5-7b5f-4579-adfb-84ea546f0115" />

<img width="1595" height="785" alt="image" src="https://github.com/user-attachments/assets/4076abb4-f0c7-46ad-acc1-44b7c820d9d6" />


#### 设置方法1：

1. 打开设置界面
2. 点击"概率设置"按钮
3. 为每个学生选择适当的概率等级
4. 点击"保存"应用设置

#### 设置方法2

1. 使用文本编辑器打开项目根目录下的 `names.txt` 文件
2. 直接编辑 `names.txt` 文件，修改名字后的概率数字
3. 保存文件后，重启Class Widgets重新加载名单

## 📄 软件许可协议

本项目使用 [AFN-License 2.0](LICENSE) 授权。

---

<div align="center">
    <p>© 2025 THW 版权所有</p>
</div>
