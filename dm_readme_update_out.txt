read 301 lines (crlf=True)
  replace L292-299 (8 lines) with 11 lines
  replace L291-291 (1 lines) with 1 lines
  replace L281-286 (6 lines) with 11 lines
  insert 10 lines before L280
  insert  7 lines before L269
  replace L262-263 (2 lines) with 3 lines
  replace L243-248 (6 lines) with 9 lines
  replace L233-238 (6 lines) with 13 lines
  insert 27 lines before L231
  replace L178-180 (3 lines) with 5 lines
  replace L118-118 (1 lines) with 1 lines
  insert 23 lines before L115
  replace L3-7 (5 lines) with 8 lines
wrote 392 lines / 21894 chars

=== headings now:
  14| ## 1. 到底为什么原来不持续出兵？（源码证据）
  26| ### 根因 A：出兵循环只被"一次性触发"，触发后被永久关闭
  67| ### 根因 B：Hard / Hardest 难度下 AI 从不造房子
  72| ### 根因 C：资源不会补充
  78| ### 根因 D：人口上限不是 8 个"标准值"时（例如 **500**），整个死亡竞赛 AI 直接失效 ← 你这次遇到的就是这个
 118| #### 根因 D 的更正（v2 证据，2026-09-26）
 144| ## 2. v1 补丁内容 A（**已废弃**，当前生效的 v2 见 §2c）：往 `anib_60002` 末尾追加 4 条规则（1725 字节）
 204| ## 2b. v1 补丁内容 B（**已废弃 / v2 已删除**）：常量 catch-all（当时以为能修"根因 D"，改的是 `anib_60027` / `anib_60010`）
 259| ## 2c. v2 补丁（当前生效）：往 `anib_60002` 追加 14 条规则（5295 字节）
 286| ## 3. 改动的文件与验证
 311| ### 3b. v1 的历史数字（**已废弃，仅供对照**）
 315| ## 4. 文件清单（都在 `D:\aoe2_work`）
 344| ## 5. 还原 / 重装 / 调参
 376| ## 6. 注意事项
