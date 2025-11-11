# CityU 课程数据爬虫与可视化系统

本项目用于爬取香港城市大学（CityU）本科课程专业页面及课程详细页面，输出结构化的 JSON/CSV 数据和关系型 SQLite 数据库，包含课程及其前置课程、互斥课程关系，并支持可视化课程依赖关系图。

## 环境配置（Windows，新手版）

按下面步骤一步一步来，无需懂编程：

### 步骤 0：安装 Python（只做一次）

- 到 <https://www.python.org/downloads/> 下载并安装 Python 3.11 或更高版本
- 安装时勾选 "Add python.exe to PATH"（如果看到了）

安装好后，打开新的 PowerShell 窗口，确认版本：

```powershell
py -3 --version
```

如果提示找不到 py 命令，请改用：

```powershell
python --version
```

### 步骤 1：在 PowerShell 打开本项目文件夹

- 方法 A：在资源管理器地址栏输入 powershell 回车
- 方法 B：在 VS Code 顶部菜单：Terminal → New Terminal（新终端），它会自动在项目目录打开

可用下面命令确认当前目录里能看到 README_CN.md：

```powershell
dir
```

### 步骤 2：安装依赖（只需第一次）

```powershell
py -3 -m pip install -U pip
py -3 -m pip install -r requirements.txt
```

如果上面报错"找不到 py"，把命令里的 py -3 换成 python 即可：

```powershell
python -m pip install -U pip
python -m pip install -r requirements.txt
```

### 常见小问题（立刻能救）

- "py 不是内部或外部命令" → 用 `python` 替换 `py -3`，或重启 PowerShell 再试
- "pip 不是内部或外部命令" → 用 `python -m pip ...` 代替 `pip ...`
- "找不到 requirements.txt" → 先执行 `dir`，确认你在项目根目录
- 网络/证书报错 → 稍后再试或换网络，首次下载页面可能慢一点

### 进阶（可选）：使用虚拟环境，干净不影响系统

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -U pip
pip install -r requirements.txt
python orchestrator.py run-all --verbose
```

退出虚拟环境：

```powershell
deactivate
```

---

## 🚀 傻瓜式快速上手

**完成上面的环境配置后，只需 2 步**就能看到课程依赖图：

### 第一步：在 PowerShell 运行命令

```powershell
py -3 orchestrator.py run-all --verbose
```

### 第二步：查看生成的图片

打开最新生成的目录 `outputs/vNNN/`（如 `v001/`），里面有：

- `dependency_vNNN.png` - 课程依赖关系图
- `roots_vNNN.png` - 根课程图（无前置要求的入门课程）

数据库文件位于 `outputs/courses.db`。

---

### 如果运行失败（404 或网络错误）：修改配置文件

默认 URL 可能已失效，需要手动替换：

**步骤 A：找到有效的课程页面 URL**

1. 打开浏览器访问 CityU 课程目录：<https://www.cityu.edu.hk/catalogue/>
2. 找到你感兴趣的专业（如计算机科学 Computer Science）
3. 复制浏览器地址栏的完整 URL（例如：`https://www.cityu.edu.hk/catalogue/ug/202425/Major/BSC1_CSC-1.htm`）

**步骤 B：编辑配置文件**

1. 右键点击 `config/scraper.toml` → 选择"打开方式" → 记事本（或 VS Code）
2. 找到这几行：

   ```toml
   urls = [
       "https://www.cityu.edu.hk/catalogue/ug/202425/Major/BSC1_CSC-1.htm",
   ]
   ```

3. 把引号里的旧链接**整个删掉**，粘贴你刚才复制的新 URL
4. 保存文件（`Ctrl + S`）
5. 重新运行第一步的命令

---

### 其他常见问题

| 问题 | 快速解决 |
|------|----------|
| "py 不是内部或外部命令" | 用 `python` 替换 `py -3`，或重启 PowerShell |
| 没生成图片 | 检查是否有网络；确认 `outputs/courses.db` 存在；重跑一次 |
| 节点挤成一团 | 打开 `config/visualize_dependency.toml`，把 `max_per_layer` 改小（如改成 3） |
| 前置课程显示不全 | 页面使用 "Precursors" 而非 "Prerequisites"，当前版本暂不支持 |

---

## 架构

---

本项目用于爬取香港城市大学（CityU）本科课程专业页面及课程详细页面，输出结构化的 JSON/CSV 数据和关系型 SQLite 数据库，包含课程及其前置课程、互斥课程关系，并支持可视化课程依赖关系图。

## 环境配置（Windows，新手版）

按下面步骤一步一步来，无需懂编程：

### 步骤 0：安装 Python（只做一次）

- 到 <https://www.python.org/downloads/> 下载并安装 Python 3.11 或更高版本
- 安装时勾选 “Add python.exe to PATH”（如果看到了）

安装好后，打开新的 PowerShell 窗口，确认版本：

```powershell
py -3 --version
```

如果提示找不到 py 命令，请改用：

```powershell
python --version
```

### 步骤 1：在 PowerShell 打开本项目文件夹

- 方法 A：在资源管理器地址栏输入 powershell 回车
- 方法 B：在 VS Code 顶部菜单：Terminal → New Terminal（新终端），它会自动在项目目录打开

可用下面命令确认当前目录里能看到 README_CN.md：

```powershell
dir
```

### 步骤 2：安装依赖（只需第一次）

```powershell
py -3 -m pip install -U pip
py -3 -m pip install -r requirements.txt
```

如果上面报错“找不到 py”，把命令里的 py -3 换成 python 即可：

```powershell
python -m pip install -U pip
python -m pip install -r requirements.txt
```

### 步骤 3：一键运行并生成图片

```powershell
py -3 orchestrator.py run-all --verbose
```

运行成功后，你会在 `outputs/` 里看到一个新版本目录（如 `v043/`），其中包含依赖图 `dependency_v043.png`。数据库文件位于 `outputs/courses.db`。

### 常见小问题（立刻能救）

- “py 不是内部或外部命令” → 用 `python` 替换 `py -3`，或重启 PowerShell 再试
- “pip 不是内部或外部命令” → 用 `python -m pip ...` 代替 `pip ...`
- “找不到 requirements.txt” → 先执行 `dir`，确认你在项目根目录
- 网络/证书报错 → 稍后再试或换网络，首次下载页面可能慢一点
- 看不到图片 → 确认 `outputs/` 里是否生成了最新 `vNNN/`，并检查里面是否有 `dependency_vNNN.png`

### 进阶（可选）：使用虚拟环境，干净不影响系统

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -U pip
pip install -r requirements.txt
python orchestrator.py run-all --verbose
```

退出虚拟环境：

```powershell
deactivate
```

## 架构

```text
core/
  scraper/        # 网络与 HTTP 请求层
    http.py
    major_scraper.py
  dp_build/       # 解析与数据处理层
    models.py
    parsers.py
    db_builder.py
  filter/         # 数据过滤层
    check.py
  vis/            # 可视化层
    common.py
    dependency.py
    roots.py
config/           # 配置文件目录
  scraper.toml    # 爬虫配置（URL、数据库重载开关等）
  visualize_dependency.toml  # 依赖图可视化配置
  visualize_roots.toml       # 根课程可视化配置
orchestrator.py   # 统一 CLI 入口（子命令）
outputs/          # 所有生成的文件（JSON、CSV、DB、图像）
  vNNN/           # 版本化输出目录
README.md         # 英文文档
README_CN.md      # 中文文档
requirements.txt
```

核心组件：

- `core.scraper.http.fetch_html` 处理 HTTP 请求，支持重试、超时、延迟等
- `core.dp_build.parsers.parse_major_page` 解析专业课程页面，可选择性跟随课程链接
- `core.dp_build.parsers.parse_course_page` 解析单个课程详细页面（标题、学分、前置课程、互斥课程、评估方式等）
- `core.dp_build.db_builder.build_course_db` 构建 SQLite 数据库
- `core.vis.dependency.render_dependency_tree` 渲染课程依赖关系图
- `core.vis.roots.render_root_courses` 渲染根课程图（无前置课程的课程）
- `orchestrator.py` 提供统一的 CLI 接口，包含多个子命令

## 安装

建议创建虚拟环境并安装依赖：

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## 使用方法

所有输出默认保存在 `outputs/` 目录。

### 配置文件

#### scraper.toml - 爬虫配置

编辑 `config/scraper.toml` 设置要爬取的 URL 和数据库选项：

```toml
[scraper]
# 主要爬取的URL列表（可添加多个）
urls = [
    "https://www.cityu.edu.hk/catalogue/ug/202425/Major/BSC1_CSC-1.htm",
]

[database]
# 是否在构建数据库前删除现有表（true=重新创建，false=保留现有数据）
reset = true

[cache]
cache_dir = "cache"
use_cache = false  # true则使用缓存，false则每次重新下载
```

### 一键运行完整流程

使用 `run-all` 命令执行完整流程：爬取 → 构建数据库 → 询问是否生成图像 → 交互式课程查询

```powershell
py -3 orchestrator.py run-all --verbose
```

执行后会完成：

1. 读取配置文件 URL
2. 爬取课程页面并提取 semester（学期）信息
3. 生成或更新 `outputs/courses.db`
4. **询问是否生成可视化图像**（输入 yes/y 生成，no/n 跳过）
5. 可选：生成图像到新的版本目录 `outputs/vNNN/`
6. **启动交互式课程查询系统**

再次运行会自动创建下一个版本号目录（例如 v043 → v044）。

### 交互式课程查询功能 🆕

运行 `run-all` 后会自动启动问答系统，你可以：

1. **输入已完成的课程代码**（多个课程用空格或逗号分隔）
   ```
   > CS1315 SDSC1001
   ```

2. **选择要查询的学期**
   ```
   请输入要查询的学期 (A/B，或直接回车查看所有学期):
   > A
   ```
   - 输入 `A` - 只显示 A 学期开设的课程
   - 输入 `B` - 只显示 B 学期开设的课程
   - 直接回车 - 显示所有学期的课程

3. **查看智能推荐**，系统会显示：
   - ✅ **可直接选修的课程** - 所有前置条件已满足
   - 🌱 **无前置要求的课程** - 入门课程
   - ⚠️ **特别要求课程** - 需要特殊批准或条件（如年级要求、CEC 批准）
   - 💼 **实习项目** - 各类实习课程
   - 📖 **相关后续课程** - 部分前置条件已满足，显示还需哪些课程

4. 输入 `q` 退出查询

**示例输出**：
```
✅ 可直接选修的课程 (3 门)
   • SDSC2003     Human Contexts and Ethics in Data Science
   • CS2334       Data Structures for Data Science

🌱 无前置要求的课程 (15 门)
   • CS1315       Introduction to Computer Programming
   • GE1501       Chinese Civilisation - History and Philosophy
   ...

⚠️ 特别要求课程 (2 门)
   • SDSC3026     International Professional Development
     要求 / Requirement: (1) Year 3 completed (2) CEC approval required

💼 实习项目 (6 门)
   • SDSC0001     Internship
   • SDSC0002     Internship
   ...
```

### 单独的子命令

#### 1. 爬取专业页面（导出 JSON）

```powershell
python orchestrator.py scrape-major --url "https://www.cityu.edu.hk/catalogue/ug/2022/course/A_BScDS.htm" --out data_science.json --courses --verbose
```

#### 2. 爬取多个专业页面（从文件读取 URL）

创建 `majors.txt` 文件，每行一个 URL（`#` 开头的行会被忽略）：

```powershell
python orchestrator.py scrape-major --file majors.txt --out majors.csv --format csv --courses --verbose
```

#### 3. 构建课程数据库

```powershell
python orchestrator.py build-db --verbose
```

这会在 `outputs/courses.db` 创建包含以下表的数据库：

- `courses(course_code PRIMARY KEY, course_title, offering_unit, credit_units, ...)`
- `prerequisites(course_code, prereq_code)` - 前置课程关系
- `exclusions(course_code, excluded_code)` - 互斥课程关系

#### 4. 可视化课程关系图

使用预设配置文件渲染图像：

```powershell
# 依赖关系图（自动创建版本化输出目录 outputs/vNNN）
python orchestrator.py visualize --profile dependency --verbose

# 根课程图（无前置课程的课程）
python orchestrator.py visualize --profile roots --verbose
```

或使用自定义配置文件：

```powershell
python orchestrator.py visualize --config config/visualize_dependency.toml --verbose
```

### 可视化配置说明

编辑 `config/visualize_dependency.toml` 或 `config/visualize_roots.toml` 来自定义图像输出：

```toml
[visualize]
db = "outputs/courses.db"                # 数据库路径
bundle_version = true                     # 自动创建版本化目录 vNNN
roots_only = false                        # 是否只显示根课程
highlight_cycles = true                   # 高亮循环依赖（红色）
max_depth = 6                             # 限制显示的层级深度
truncate_title = 28                       # 课程标题截断长度
max_per_layer = 5                         # 每层最多显示多少节点
exclude_isolated = true                   # 排除孤立节点（无前置也无后续课程）
straight_edges = true                     # 使用直线连接（false则使用曲线）
```

### 数据库结构

`courses.db` 包含：

- **courses** 表：课程基本信息
  - `course_code` (主键): 课程代码（如 CS1102）
  - `course_title`: 课程名称
  - `offering_unit`: 开课单位
  - `credit_units`: 学分
  - `duration`: 课程时长
  - `semester`: 开课学期（A、B 或 A, B）🆕
  - `aims`: 课程目标
  - `assessment_json`: 评估方式（JSON格式）
  - `pdf_url`: 课程大纲PDF链接
  - `url`: 课程页面URL

- **prerequisites** 表：前置课程关系
  - `course_code`: 课程代码
  - `prereq_code`: 前置课程代码

- **exclusions** 表：互斥课程关系
  - `course_code`: 课程代码
  - `excluded_code`: 互斥课程代码

- **special_requirements** 表：特别要求课程 🆕
  - `course_code` (主键): 课程代码
  - `requirement_text`: 文字描述的特殊要求（如年级、批准要求等）

### 可视化图像说明

#### 依赖关系图（dependency graph）

- 显示所有课程及其前置关系
- 根节点（无前置课程）位于底部
- 依赖课程位于上方
- 连接线按父节点着色（相同父节点的边使用相同颜色）
- 节点颜色与其出边颜色相同（叶子节点为灰色）
- 支持循环检测（红色边标记）

#### 根课程图（roots only）

- 只显示没有前置课程的课程
- 按开课单位着色
- 适合快速查看入门课程

### 命令行选项

所有命令都支持以下通用选项：

- `--verbose`: 显示详细输出
- `--out-dir`: 覆盖默认输出目录
- `--cache-dir`: 设置HTML缓存目录

可视化命令特有选项：

- `--profile {dependency|roots}`: 使用预设配置
- `--config PATH`: 使用自定义配置文件
- `--bundle-version`: 自动创建版本化目录
- `--db PATH`: 指定数据库路径
- `--focus CODE`: 聚焦显示某个课程的依赖树
- `--max-depth N`: 限制显示深度

### 优先级规则

1. **命令行参数** 优先级最高
2. **配置文件设置** 次之
3. **默认值** 最低

例如：

- 命令行指定 `--reset` → 优先生效，忽略配置文件
- 配置文件 `reset = true` 且命令行未提供 → 使用配置文件值

### 发布到 GitHub 的隐私注意

为避免泄露本地信息：

- 不要提交本地绝对路径（已改为使用 `py -3`）
- 不要保留临时调试输出、个人邮箱、姓名等
- `outputs/` 目录建议在 `.gitignore` 中（除非你要展示样例）
- 如果使用虚拟环境，确保排除 `.venv/`
- 查看 `config/` 中是否有仅自己使用的内部 URL（必要再公开）

迁移到公开仓库前建议执行：

```powershell
git grep -i "users" || echo OK
git grep -i "asus" || echo OK
git status
```

## 数据模型

### Major JSON 格式

```json
{
  "url": "https://.../A_BScDS.htm",
  "program_title": "Data Science",
  "program_code": "BScDS",
  "aims": "...",
  "il_outcomes": ["Outcome 1", "Outcome 2"],
  "structure_tables": [
    {
      "caption": "Year 1",
      "headers": ["Course", "Credit"],
      "rows": [["SDSC1001", "3"], ["CS1102", "3"]]
    }
  ],
  "remarks": "...",
  "courses": [
    {
      "course_code": "SDSC2001",
      "course_title": "Probability and Statistics",
      "offering_unit": "Department of ...",
      "credit_units": "3",
      "duration": "One semester",
      "aims": "...",
      "prerequisites": "MA2510 or equivalent",
      "exclusive_courses": "",
      "assessment": {"Coursework": "40%", "Exam": "60%"},
      "pdf_url": "https://.../syllabus.pdf",
      "url": "https://.../course/SDSC2001.htm"
    }
  ]
}
```

## 注意事项

- 课程代码检测使用正则表达式 `[A-Z]{2,}\d{3,4}`
- 网络礼仪：使用 `--delay` 选项限制请求频率
- 某些页面的 HTML 结构可能不一致，解析器会尽量容错但可能遗漏边缘情况
- 评估方式以 JSON 对象形式存储在 `assessment_json` 列

## 扩展开发

- 在 `core/dp_build/parsers.py` 中添加新的解析规则
- 在 `orchestrator.py` 中添加新的输出格式（如 Parquet、Excel）
- 在 `core/vis/` 中添加新的可视化样式

## 故障排查

### 查看合并后的配置

使用内置的配置查看器检查配置是否正确加载：

```powershell
# 使用预设配置
python orchestrator.py show-config --profile dependency

# 使用自定义配置文件
python orchestrator.py --config config/visualize_dependency.toml show-config
```



### 常见问题

1. **URL 404 错误**
   - 检查 `config/scraper.toml` 中的 URL 是否正确
   - CityU 网站结构可能变化，需要更新 URL

2. **图像为空或节点重叠**
   - 检查数据库是否有数据：`sqlite3 outputs/courses.db "SELECT COUNT(*) FROM courses;"`
   - 调整 `max_per_layer` 参数

3. **缓存问题**
   - 设置 `use_cache = false` 强制重新下载
   - 手动删除 `cache/` 目录

## 许可证

仅供教育和研究使用。大规模爬取前请查阅 CityU 网站使用条款。
