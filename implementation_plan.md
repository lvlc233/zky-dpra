# DeepPaperResearcher Bug Investigation Report

针对您提出的7点bug和增强需求，我已经对项目的前后端代码进行了初步查阅和根因排查。以下是我的调查结论：

## 1. 搜索用的 API (多数据源轮询与降级机制)
- **需求分析**：目前外部搜索硬编码依赖单一下游（如 arXivAPI），容易被限流或由于网络原因超时。我们需要设计一套支持多API轮询重试和权重降级的高可用架构，并配套管理后台配置功能。
- **增强方案（基于数据库权重的 API 轮询回退）**：
  - **基础层（Base Layer）**：抽象出一个标准的 `SearchAPIClient` 接口，并分别实现多家学术 API 的接入（例如 arXiv, Semantic Scholar, Crossref 等）。
  - **持久层（Database）**：新增存放各 API 配置的数据库表。非常赞同您提议的结构，建议在 `id + key + weight` 的基础上，增加 `api_name` (标识具体使用哪个平台) 和 `is_active` (作为动态开关)。最终字段形如：`id | api_name | api_key | weight | is_active`。
  - **应用层（Application Layer）**：搜索服务处理请求时，从数据库读取所有 `is_active=True` 的 API 配置，并按照 `weight` 降序排序。优先调用高权重的 API，若抛出异常、网络超时或失败，则自动捕获并回退 (Fallback) 给下一优先级的 API，直到成功或全部耗尽。
  - **管理端（Admin UI）**：前端新增管理员配置面板，支持动态管理搜索 API：修改权重（随时切换主用通道）、打开/关闭通道、以及安全地配置各个数据源的 API Key。

## 2. 搜索时的本地搜索和网络搜索
- **问题分析**：在 `search_service.py:search_papers` 中，如果选择了外部搜索（不论是通过旧的 `source=='arxiv'` 还是新的开关 `enable_web_search`），系统会直接跳过本地数据库的搜索，仅返回网络搜索结果。
- **增强方案**：为了实现混合搜索，我们需要在开启全网搜索时，仍然并行或先查本地 DB（并结合基于 Embedding 的向量检索），最后合并去重展示。

## 3. Chunk（切块向量）的不稳定性
- **问题分析**：目前论文文本的解析与向量化（`vectorize` Arq task）高度依赖正确的 Embedding 模型配置。如果用户未配置模型、模型配额不足或服务不稳定，导致 Chunk 无法正确生成，进而使得 `InPaperChatAgent` 的 `search_paper_chunks` 工具搜索不到内容。
- **增强方案**：
  1. **重新切块支持**：如果切块失败，在论文详情/搜索界面提供一个 `重新重试向量化` (Retry Vectorization) 的接口供前端调用。
  2. **Agent 增强**：在 `paper_chat_agent` 的可用 tools 里，补充一个直接**按章节/页码等全文索引阅读**的 Fallback 工具（例如 `read_paper_text`），即使没有向量 Chunk，Agent 依然能兜底通读论文。

## 4. 状态调整同步（上传后一直“解析中”）
- **问题分析**：上传论文后，`PaperService.upload_paper` 会将状态设入数据库的 `PENDING`，随后 `parse_text` 任务执行时将其设为 `PROCESSING`。
如果有任何原因导致 `parse_text` 抛出未捕获的错误或是 Redis 服务器中断，DB里的状态将成为孤儿，永远卡在 `PROCESSING`；而前端的转圈圈则是因为轮询 `get_paper_status` 迟迟等不到 `COMPLETED`。
- **修复方案**：在 `get_paper_status` 针对卡在 `PROCESSING` 的任务增强恢复机制：如果超时且 Redis 无对应的活跃 job，将其置为 `FAILED`；或者前端上传遇到问题能够通过接口重选或终止、取消。

## 5. 论文内容显示 Bug（本地上传，刷新后数据消失）
- **根本原因**：在 `PaperService.upload_paper` (第192行) 中，系统聪明地使用 `PyMuPDFParser` 同步且快速地提取到了标题和作者，存入 DB。因此上传当即前端显示完全正常。
但是，几秒钟后，异步的 `PaperProcessingService.parse_text` 任务开始执行（第770行）。它调用了 `_extract_metadata` 再次去解析，紧接着（第792行）直接覆盖了数据库：`await PaperRepository.update_paper_metadata(..., title=title, ...)`。
如果这次异步抓取返回了空Title或未能正确提取，它会用空字符串或None覆盖掉原有的正确元数据！刷新后，消失的标题就是因此而来。
- **修复方案**：在 `parse_text` 阶段，仅当新的 `title` 和 `authors` 非空且质量更高时，才覆盖存储，或者优先保留已存在的数据。

## 6. Agent 消息刷新功能（需要重新生成摘要和脑图能力）
- **问题分析**：当前摘要和脑图主要是上传后流水线自动触发的任务，缺少独立的由用户侧触发重新运行的端点。
- **增强方案**：
  - 后端需要在 `controller/api/reader/router.py`（或者是 papers router）增加 `/api/v1/papers/{id}/summary/regenerate` 等路由，调用 Arq 客户端将任务重新下发到 Worker。
  - 脑图生成同理，清除原状态后提交。

## 7. 备注功能（前端删除注释 Bug）
- **问题分析**：在阅读器中，前端对高亮/备注 Annotation 删除时卡住且无法删除，大概率是因为调用了 `deleteAnnotation` 接口，而后端缺乏该接口（或者 URL 路径有误报 404）、引发了未捕获的请求失败（Promise Reject），导致 React 组件状态卡死在 `isLoading=true` 且并未从列表中 `.filter` 剔除该条目。
- **修复方案**：后端对齐/修补 `DELETE /api/v1/reader/annotations/{annotation_id}` 接口功能，前端妥善 catch error 并更新 Local State。

以上为不修改代码前提下，对该项目 7 个主要 Bug 的深度排查与报告。您可以随时告诉我，哪几个问题您希望优先得到解决，我们可以开始逐个清理这些 Bug！
